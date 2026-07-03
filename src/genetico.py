"""Algoritmo genético para o Problema do Caixeiro Viajante (PCV)."""

import math
import random
import tempfile
import webbrowser
from collections.abc import Sequence
from pathlib import Path

from pyvis.network import Network

# ---------------------------------------------------------------------------
# Grafo do exercício
# ---------------------------------------------------------------------------

nodos = ["c", "e", "f", "g", "h", "k", "l", "n"]

caxeiro_connections = [
    ("c", "e", 10),
    ("c", "f", 20),
    ("c", "n", 47),
    ("c", "l", 10),
    ("c", "k", 70),
    ("c", "h", 30),
    ("f", "n", 30),
    ("f", "g", 55),
    ("f", "l", 10),
    ("n", "k", 60),
    ("l", "e", 5),
    ("l", "h", 40),
    ("k", "h", 73),
    ("k", "e", 10),
    ("k", "g", 90),
    ("h", "e", 60),
    ("h", "g", 80),
    ("e", "g", 40),
]

INFINITO = float("inf")

# Parâmetros do algoritmo (conforme especificação da atividade)
TAMANHO_POPULACAO = 100
TAXA_CROSSOVER = 0.70  # entre 60% e 80%
TAXA_MUTACAO = 0.005  # entre 0,5% e 1%
NUM_GERACOES = 50  # mínimo de 50
NUM_ELITOS = 5  # melhores indivíduos preservados a cada geração


def construir_mapa_arestas(conexoes: Sequence[tuple[str, str, float]]) -> dict[frozenset[str], float]:
    """Monta um dicionário que associa cada par de cidades ao peso da aresta."""
    mapa: dict[frozenset[str], float] = {}
    for origem, destino, peso in conexoes:
        mapa[frozenset({origem, destino})] = peso
    return mapa


def custo_rota(rota: list[str], mapa: dict[frozenset[str], float]) -> float:
    """
    Calcula o custo total de uma rota fechada (volta à cidade inicial).
    Retorna infinito se alguma ligação não existir no grafo.
    """
    total = 0.0
    for i in range(len(rota)):
        cidade_atual = rota[i]
        proxima = rota[(i + 1) % len(rota)]
        peso = mapa.get(frozenset({cidade_atual, proxima}))
        if peso is None:
            return INFINITO
        total += peso
    return total


def rota_aleatoria(cidades: list[str], cidade_inicial: str) -> list[str]:
    """Gera uma permutação aleatória começando pela cidade escolhida."""
    restantes = [c for c in cidades if c != cidade_inicial]
    random.shuffle(restantes)
    return [cidade_inicial] + restantes


def crossover_ox(pai_a: list[str], pai_b: list[str]) -> list[str]:
    """Crossover OX de dois pontos entre duas rotas."""
    tamanho = len(pai_a)
    ponto_1, ponto_2 = sorted(random.sample(range(tamanho), 2))

    filho: list[str | None] = [None] * tamanho
    filho[ponto_1:ponto_2] = pai_a[ponto_1:ponto_2]

    posicao = ponto_2 % tamanho
    for cidade in pai_b[ponto_2:] + pai_b[:ponto_2]:
        if cidade not in filho:
            filho[posicao] = cidade
            posicao = (posicao + 1) % tamanho

    return [cidade for cidade in filho if cidade is not None]


def mutar(rota: list[str], taxa: float) -> list[str]:
    """Troca duas posições aleatórias com a probabilidade informada."""
    nova = rota.copy()
    if random.random() < taxa:
        i, j = random.sample(range(len(nova)), 2)
        nova[i], nova[j] = nova[j], nova[i]
    return nova


def avaliar_populacao(populacao: list[list[str]], mapa: dict[frozenset[str], float]) -> list[tuple[list[str], float]]:
    """Retorna a população ordenada do menor para o maior custo."""
    avaliados = [(rota, custo_rota(rota, mapa)) for rota in populacao]
    avaliados.sort(key=lambda item: item[1])
    return avaliados


def selecionar_pai(avaliados: list[tuple[list[str], float]]) -> list[str]:
    """Seleção por roleta inversa: indivíduos melhores têm mais chances."""
    # Quanto menor o custo, mais tickets o indivíduo recebe.
    pool: list[list[str]] = []
    for posicao, (rota, custo) in enumerate(avaliados):
        if custo == INFINITO:
            tickets = 1
        else:
            tickets = max(50 - posicao, 1)
        pool.extend([rota] * tickets)
    return random.choice(pool)


def nova_geracao(
    avaliados: list[tuple[list[str], float]],
    tamanho: int,
    num_elitos: int,
    taxa_crossover: float,
    taxa_mutacao: float,
) -> list[list[str]]:
    """Monta a próxima geração preservando os melhores (elitismo)."""
    elitos = [rota for rota, _ in avaliados[:num_elitos]]
    filhos: list[list[str]] = []

    while len(filhos) < tamanho - num_elitos:
        pai = selecionar_pai(avaliados)

        if random.random() < taxa_crossover:
            outro_pai = selecionar_pai(avaliados)
            filho = crossover_ox(pai, outro_pai)
        else:
            filho = pai.copy()

        filhos.append(mutar(filho, taxa_mutacao))

    return elitos + filhos


def exibir_populacao(avaliados: list[tuple[list[str], float]], limite: int = 10) -> None:
    """Mostra os melhores indivíduos da geração atual."""
    print(f"\n  Top {limite} indivíduos:")
    for pos, (rota, custo) in enumerate(avaliados[:limite], start=1):
        rota_str = " -> ".join(rota + [rota[0]])
        custo_str = "infinito" if custo == INFINITO else f"{custo:.0f}"
        print(f"  {pos:2d}. custo={custo_str:>8s}  [{rota_str}]")
    print()


def exibir_rota_grafica(
    rota: list[str],
    custo: float,
    conexoes: Sequence[tuple[str, str, float]],
) -> None:
    """Abre no navegador um grafo destacando a melhor rota encontrada."""
    arestas_rota = {frozenset({rota[i], rota[(i + 1) % len(rota)]}) for i in range(len(rota))}

    # Posiciona os nós em círculo para facilitar a leitura visual.
    posicoes: dict[str, tuple[int, int]] = {}
    raio = 250
    for i, cidade in enumerate(nodos):
        angulo = 2 * math.pi * i / len(nodos)
        posicoes[cidade] = (int(raio * math.cos(angulo)), int(raio * math.sin(angulo)))

    rede = Network(
        height="600px",
        width="100%",
        directed=False,
        bgcolor="#0f172a",
        font_color="#e5eefc",
    )
    rede.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120)

    for cidade in nodos:
        x, y = posicoes[cidade]
        na_rota = cidade in rota
        rede.add_node(
            cidade,
            label=cidade.upper(),
            x=x,
            y=y,
            physics=False,
            color="#22c55e" if na_rota else "#4f9cff",
            size=30 if na_rota else 22,
        )

    for origem, destino, peso in conexoes:
        chave = frozenset({origem, destino})
        na_rota = chave in arestas_rota
        rede.add_edge(
            origem,
            destino,
            label=str(peso),
            color="#22c55e" if na_rota else "#475569",
            width=4 if na_rota else 1,
        )

    caminho_html = Path(tempfile.gettempdir()) / "pcv_melhor_rota.html"
    rede.write_html(str(caminho_html), notebook=False)
    print(f"\nVisualização salva em: {caminho_html}")
    webbrowser.open(caminho_html.as_uri())


def executar_algoritmo_genetico(cidade_inicial: str) -> None:
    """Executa o AG completo e exibe o melhor resultado ao final."""
    mapa = construir_mapa_arestas(caxeiro_connections)

    populacao = [rota_aleatoria(nodos, cidade_inicial) for _ in range(TAMANHO_POPULACAO)]

    melhor_rota: list[str] = []
    melhor_custo = INFINITO

    print("\nAlgoritmo Genético — PCV")
    print(f"Cidade inicial: {cidade_inicial.upper()}")
    print(f"População: {TAMANHO_POPULACAO} | Gerações: {NUM_GERACOES}")
    print(f"Crossover: {TAXA_CROSSOVER:.0%} | Mutação: {TAXA_MUTACAO:.1%} | Elitismo: {NUM_ELITOS}")
    print("-" * 60)

    for geracao in range(NUM_GERACOES):
        avaliados = avaliar_populacao(populacao, mapa)

        custo_atual = avaliados[0][1]
        if custo_atual < melhor_custo:
            melhor_custo = custo_atual
            melhor_rota = avaliados[0][0].copy()

        custo_str = "infinito" if custo_atual == INFINITO else f"{custo_atual:.0f}"
        print(f"Geração {geracao + 1:3d}/{NUM_GERACOES} — melhor custo: {custo_str}")
        exibir_populacao(avaliados)

        populacao = nova_geracao(
            avaliados,
            TAMANHO_POPULACAO,
            NUM_ELITOS,
            TAXA_CROSSOVER,
            TAXA_MUTACAO,
        )

    # Resultado final
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    rota_str = " -> ".join(melhor_rota + [melhor_rota[0]])
    print(f"Melhor rota : {rota_str}")
    print(f"Custo total : {melhor_custo:.0f}")
    print("=" * 60)

    if melhor_custo < INFINITO:
        exibir_rota_grafica(melhor_rota, melhor_custo, caxeiro_connections)
    else:
        print("\nNenhuma rota válida encontrada — visualização não disponível.")


def main() -> None:
    print("Problema do Caixeiro Viajante — Algoritmo Genético")
    print(f"Cidades disponíveis: {', '.join(c.upper() for c in nodos)}")

    while True:
        escolha = input("\nEscolha a cidade inicial: ").strip().lower()
        if escolha in nodos:
            break
        print("Cidade inválida. Tente novamente.")

    executar_algoritmo_genetico(escolha)


if __name__ == "__main__":
    main()
