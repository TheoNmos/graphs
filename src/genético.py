import random

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

def build_edge_map(connections: list[tuple[str, str, float]]) -> dict[frozenset[str], float]:
    """Retorna um mapa de pares de nós para peso da aresta."""
    edge_map: dict[frozenset[str], float] = {}
    for origin, destination, cost in connections:
        edge_map[frozenset({origin, destination})] = float(cost)
    return edge_map


def score_route(route: list[str], edge_map: dict[frozenset[str], float]) -> tuple[float, float, int, int]:
    """Avalia uma rota calculando distância e penalidades."""
    distance = 0.0
    invalid_edges = 0
    node_counts: dict[str, int] = {}
    for node in route:
        node_counts[node] = node_counts.get(node, 0) + 1
    repeated_nodes = sum(count - 1 for count in node_counts.values() if count > 1)

    route_length = len(route)
    if route_length < 1:
        return 0.0, 0.0, 0, 0

    for index in range(route_length):
        current_node = route[index]
        next_node = route[(index + 1) % route_length]
        edge_key = frozenset({current_node, next_node})
        weight = edge_map.get(edge_key)
        if weight is None:
            invalid_edges += 1
        else:
            distance += weight

    total_score = distance + 10000 * repeated_nodes + 10000 * invalid_edges
    return total_score, distance, repeated_nodes, invalid_edges


def random_route(nodes: list[str]) -> list[str]:
    """Gera uma rota aleatória que passa por todos os nós em ordem randômica."""
    route = nodes.copy()
    random.shuffle(route)
    return route


def two_point_ox(parent_a: list[str], parent_b: list[str]) -> list[str]:
    """Realiza crossover OX de dois pontos entre duas rotas de cidades."""
    length = len(parent_a)
    if length != len(parent_b):
        raise ValueError("Os pais devem ter o mesmo tamanho para OX.")
    if length < 2:
        return parent_a.copy()

    left = random.randrange(length)
    right = random.randrange(length)
    if left > right:
        left, right = right, left

    child: list[str | None] = [None] * length
    child[left:right] = parent_a[left:right]

    current_index = right % length
    for gene in parent_b[right:] + parent_b[:right]:
        if gene not in child:
            child[current_index] = gene
            current_index = (current_index + 1) % length

    return [cast_gene for cast_gene in child if cast_gene is not None]


def mutate_route(route: list[str], mutation_rate: float = 0.05) -> list[str]:
    """Aplica mutação por troca de duas posições com pequena probabilidade."""
    new_route = route.copy()
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(new_route)), 2)
        new_route[i], new_route[j] = new_route[j], new_route[i]
    return new_route


def rank_population(population: list[list[str]], edge_map: dict[frozenset[str], float]) -> list[tuple[list[str], float, float, int, int]]:
    """Classifica a população pelo score ascendente."""
    evaluated = [(*score_route(individual, edge_map), individual) for individual in population]
    evaluated.sort(key=lambda item: item[0])
    return [(route, score, distance, repeats, invalids) for score, distance, repeats, invalids, route in evaluated]


def build_ticket_pool(sorted_population: list[tuple[list[str], float, float, int, int]]) -> list[list[str]]:
    """Cria uma lista de genes repetidos por quantidade de tickets para seleção ponderada."""
    ticketed: list[list[str]] = []
    for rank, (route, *_rest) in enumerate(sorted_population):
        tickets = max(50 - rank, 0)
        ticketed.extend([route] * tickets)
    if not ticketed:
        ticketed = [route for route, *_rest in sorted_population]
    return ticketed


def select_two_parents(ticket_pool: list[list[str]]) -> tuple[list[str], list[str]]:
    """Seleciona dois pais com reposição usando pool de tickets."""
    if len(ticket_pool) < 2:
        return ticket_pool[0], ticket_pool[0]
    return random.choice(ticket_pool), random.choice(ticket_pool)


def evolve_generation(
    current_population: list[list[str]],
    edge_map: dict[frozenset[str], float],
    elite_count: int,
    population_size: int,
    mutation_rate: float,
) -> list[list[str]]:
    """Gera a próxima população mantendo os melhores e criando filhos por crossover."""
    sorted_population = rank_population(current_population, edge_map)
    elites = [route for route, *_ in sorted_population[:elite_count]]
    ticket_pool = build_ticket_pool(sorted_population)

    children: list[list[str]] = []
    while len(children) < population_size - elite_count:
        parent_a, parent_b = select_two_parents(ticket_pool)
        child = two_point_ox(parent_a, parent_b)
        child = mutate_route(child, mutation_rate=mutation_rate)
        children.append(child)

    return elites + children


def print_generation_report(
    generation_index: int,
    ranked_population: list[tuple[list[str], float, float, int, int]],
    report_size: int = 10,
) -> None:
    print(f"Geração {generation_index + 1}")
    print("Melhores rotas:")
    for position, (route, score, distance, repeats, invalids) in enumerate(ranked_population[:report_size], start=1):
        route_str = " -> ".join(route + [route[0]])
        print(
            f"{position:2d}. score={score:.1f}, distancia={distance:.1f}, "
            f"repetidos={repeats}, invalidas={invalids}, rota=[{route_str}]"
        )
    print()


def run_genetic_algorithm(
    nodes: list[str],
    edge_map: dict[frozenset[str], float],
    population_size: int = 100,
    elite_count: int = 50,
    num_generations: int = 50,
    mutation_rate: float = 0.05,
) -> None:
    population = [random_route(nodes) for _ in range(population_size)]
    for generation in range(num_generations):
        ranked = rank_population(population, edge_map)
        print_generation_report(generation, ranked)
        population = evolve_generation(population, edge_map, elite_count, population_size, mutation_rate)

    final_ranked = rank_population(population, edge_map)
    print("Geração final (melhores 10):")
    print_generation_report(num_generations, final_ranked)


def main() -> None:
    edge_map = build_edge_map(caxeiro_connections)
    population_size = 100
    elite_count = 50
    num_generations = 50
    mutation_rate = 0.05

    print("Iniciando o algoritmo genético para o problema do caixeiro viajante.")
    print(f"Nós: {len(nodos)}, conexões: {len(caxeiro_connections)}")
    print(f"População: {population_size}, elitismo: {elite_count}, gerações: {num_generations}")
    run_genetic_algorithm(
        nodes=nodos,
        edge_map=edge_map,
        population_size=population_size,
        elite_count=elite_count,
        num_generations=num_generations,
        mutation_rate=mutation_rate,
    )


if __name__ == "__main__":
    main()
