from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional
import math
import heapq


@dataclass
class Edge:
    """Aresta/Arco com identificador e valor numérico."""

    id: str
    source_vertex_id: str
    target_vertex_id: str
    value: float


@dataclass
class GuidedSearchResult:
    """Estrutura de dados para armazenar o resultado de uma busca guiada (BFS/DFS) com árvore implícita e caminho."""

    source: str
    target: str
    found: bool
    # lista de arestas que formam a árvore de busca, ou seja, as arestas que foram visitadas para chegar ao destino
    tree_edges: list[tuple[str, str, str]]
    path: list[str]


class Graph:
    """
    Grafo G = (V, A) representado por lista de adjacência.

    - V: conjunto de vértices (cada um com identificador)
    - A: conjunto de arestas/arcos (cada um com id e valor)
    - directed: True = grafo dirigido (arcos), False = não dirigido (arestas)
    """

    def __init__(self, directed: bool = False, name: str = "Grafo"):
        self.directed = directed
        self.name = name
        self._vertices: set[str] = set()
        self._edges: dict[str, Edge] = {}
        self._adjacency: dict[str, list[tuple[str, str, float]]] = {}  # lista de adjacência do grafo
        self._coordinates: dict[str, tuple[float, float]] = {}  # coordenadas (x, y) dos vértices

    def add_vertex(self, vertex_id: str) -> bool:
        """Insere um novo vértice isolado."""
        if vertex_id in self._vertices:
            return False
        # caso o vértice não exista, adiciona ele na lista de vértices e cria uma lista de adjacência vazia pra ele
        self._vertices.add(vertex_id)
        self._adjacency[vertex_id] = []
        return True

    def add_edge(
        self,
        edge_id: str,
        source_vertex_id: str,
        target_vertex_id: str,
        value: float = 1.0,
    ) -> bool:
        """Insere aresta/arco ligando dois vértices, com identificador e valor."""
        # ve se a edge já existe e se os vértices já existem
        if edge_id in self._edges:
            return False
        if source_vertex_id not in self._vertices or target_vertex_id not in self._vertices:
            return False
        edge = Edge(
            id=edge_id,
            source_vertex_id=source_vertex_id,
            target_vertex_id=target_vertex_id,
            value=value,
        )
        # adiciona a nova edge e atualiza lista de adjacência
        self._edges[edge_id] = edge
        self._adjacency[source_vertex_id].append((target_vertex_id, edge_id, value))
        # caso seja não dirigido, tem que criar adjacencia no target também (um aponta por outro)
        if not self.directed:
            self._adjacency[target_vertex_id].append((source_vertex_id, edge_id, value))
        return True

    def remove_vertex(self, vertex_id: str) -> bool:
        """Remove um vértice e suas arestas/arcos incidentes."""
        if vertex_id not in self._vertices:
            return False
        # verifica a lista de edges e seleciona as que possuem o vértice como origem ou destino
        edges_to_remove = [
            edge_id
            for edge_id, edge in self._edges.items()
            if edge.source_vertex_id == vertex_id or edge.target_vertex_id == vertex_id
        ]
        for edge_id in edges_to_remove:
            del self._edges[edge_id]
        # remove a lista de adjacência do vértice
        del self._adjacency[vertex_id]
        # remove o vértice da lista de vértices
        self._vertices.discard(vertex_id)
        # percorre a lista de adjacência e remove as arestas que possuem o vértice como origem ou destino
        for adjacent_vertex_id in self._adjacency:
            self._adjacency[adjacent_vertex_id] = [
                (neighbor_vertex_id, adjacent_edge_id, edge_value)
                for neighbor_vertex_id, adjacent_edge_id, edge_value in self._adjacency[adjacent_vertex_id]
                if neighbor_vertex_id != vertex_id and adjacent_edge_id in self._edges
            ]
        return True

    def remove_edge(self, edge_id: str) -> bool:
        """Remove a aresta/arco a pelo identificador."""
        if edge_id not in self._edges:
            return False
        # recupera a aresta pra saber de quais listas de adjacência ela precisa ser removida
        edge = self._edges[edge_id]
        source_vertex_id = edge.source_vertex_id
        target_vertex_id = edge.target_vertex_id
        # remove a aresta da lista de adjacência do vértice de origem
        self._adjacency[source_vertex_id] = [
            (neighbor_vertex_id, adjacent_edge_id, edge_value)
            for neighbor_vertex_id, adjacent_edge_id, edge_value in self._adjacency[source_vertex_id]
            if adjacent_edge_id != edge_id
        ]
        # se o grafo não for dirigido, remove também da lista do vértice de destino
        if not self.directed:
            self._adjacency[target_vertex_id] = [
                (neighbor_vertex_id, adjacent_edge_id, edge_value)
                for neighbor_vertex_id, adjacent_edge_id, edge_value in self._adjacency[target_vertex_id]
                if adjacent_edge_id != edge_id
            ]
        # por fim remove a aresta da estrutura principal de arestas
        del self._edges[edge_id]
        return True

    def are_adjacent(self, first_vertex_id: str, second_vertex_id: str) -> bool:
        """Verifica se dois vértices são adjacentes."""
        if first_vertex_id not in self._adjacency:
            return False
        # percorre os vizinhos do primeiro vértice procurando o segundo
        return any(
            neighbor_vertex_id == second_vertex_id for neighbor_vertex_id, _, _ in self._adjacency[first_vertex_id]
        )

    def get_edge_value(self, edge_id: str) -> Optional[float]:
        """Retorna o valor da aresta/arco a."""
        # busca a aresta pelo id e devolve o peso dela, se existir
        edge = self._edges.get(edge_id)
        return edge.value if edge else None

    def get_edge_value_by_vertices(
        self,
        source_vertex_id: str,
        target_vertex_id: str,
    ) -> Optional[float]:
        """Retorna o valor da aresta entre dois vértices (primeira encontrada)."""
        # percorre os vizinhos do vértice de origem até encontrar o destino
        for neighbor_vertex_id, _, edge_value in self._adjacency.get(source_vertex_id, []):
            if neighbor_vertex_id == target_vertex_id:
                return edge_value
        return None

    def get_edge_extremities(self, edge_id: str) -> Optional[tuple[str, str]]:
        """Retorna as extremidades (v, w) da aresta/arco a."""
        # retorna origem e destino da aresta a partir do id informado
        edge = self._edges.get(edge_id)
        return (edge.source_vertex_id, edge.target_vertex_id) if edge else None

    def get_edge_by_vertices(
        self,
        source_vertex_id: str,
        target_vertex_id: str,
    ) -> Optional[str]:
        """Retorna o id da primeira aresta entre dois vértices."""
        # procura na adjacência da origem qual aresta leva até o destino
        for neighbor_vertex_id, edge_id, _ in self._adjacency.get(source_vertex_id, []):
            if neighbor_vertex_id == target_vertex_id:
                return edge_id
        return None

    def adjacency_matrix(self) -> list[list[float]]:
        """Retorna a matriz de adjacência (valores são pesos; 0 se não adjacente)."""
        # ordena os vértices pra manter uma ordem fixa nas linhas e colunas da matriz
        vertex_ids = sorted(self._vertices)
        vertex_count = len(vertex_ids)
        vertex_index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        adjacency_matrix = [[0.0] * vertex_count for _ in range(vertex_count)]
        # preenche a matriz com o peso da aresta entre cada par de vértices adjacentes
        for vertex_id in vertex_ids:
            for neighbor_vertex_id, _, edge_value in self._adjacency[vertex_id]:
                adjacency_matrix[vertex_index_by_id[vertex_id]][vertex_index_by_id[neighbor_vertex_id]] = edge_value
        return adjacency_matrix

    def adjacency_matrix_vertices(self) -> list[str]:
        """Retorna ordem dos vértices usada na matriz de adjacência."""
        return sorted(self._vertices)

    def incidence_matrix(self) -> list[list[int]]:
        """
        Retorna a matriz de incidência.
        Linhas = vértices (ordem alfabética), Colunas = arestas (ordem dos ids).
        Para aresta (v,w): +1 em v, -1 em w (dirigido) ou +1 em ambos (não dirigido).
        """
        # define a ordem dos vértices e das arestas pra montar a matriz de forma consistente
        vertex_ids = sorted(self._vertices)
        edges_with_ids = sorted(self._edges.items(), key=lambda item: item[0])
        vertex_count = len(vertex_ids)
        edge_count = len(edges_with_ids)
        vertex_index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        incidence_matrix = [[0] * edge_count for _ in range(vertex_count)]
        # marca a incidência de cada aresta nas linhas correspondentes aos vértices dela
        for edge_index, (_, edge) in enumerate(edges_with_ids):
            source_index = vertex_index_by_id[edge.source_vertex_id]
            target_index = vertex_index_by_id[edge.target_vertex_id]
            if self.directed:
                incidence_matrix[source_index][edge_index] = 1
                incidence_matrix[target_index][edge_index] = -1
            else:
                incidence_matrix[source_index][edge_index] = 1
                incidence_matrix[target_index][edge_index] = 1
        return incidence_matrix

    def incidence_matrix_vertices(self) -> list[str]:
        """Ordem dos vértices na matriz de incidência."""
        return sorted(self._vertices)

    def incidence_matrix_edges(self) -> list[str]:
        """Ordem das arestas na matriz de incidência."""
        return sorted(self._edges.keys())

    def display_ascii(self) -> str:
        """Retorna representação textual do grafo (vértices e arestas)."""
        # começa montando o cabeçalho com nome, tipo e lista de vértices
        lines = [f"=== {self.name} ({'Dirigido' if self.directed else 'Não Dirigido'}) ==="]
        lines.append(f"Vértices: {sorted(self._vertices)}")
        lines.append("Arestas/Arcos:")
        # adiciona uma linha para cada aresta/arco com origem, destino e peso
        for edge_id, edge in sorted(self._edges.items(), key=lambda item: item[0]):
            arrow = " -> " if self.directed else " <-> "
            lines.append(f"  {edge_id}: {edge.source_vertex_id}{arrow}{edge.target_vertex_id} (valor={edge.value})")
        lines.append("\nLista de Adjacência:")
        # depois monta uma visão textual da lista de adjacência de cada vértice
        for vertex_id in sorted(self._vertices):
            adjacency_entries = self._adjacency[vertex_id]
            if adjacency_entries:
                adjacency_description = ", ".join(
                    f"{neighbor_vertex_id}({edge_id}, {edge_value})"
                    for neighbor_vertex_id, edge_id, edge_value in adjacency_entries
                )
                lines.append(f"  {vertex_id}: [{adjacency_description}]")
            else:
                lines.append(f"  {vertex_id}: []")
        return "\n".join(lines)

    def total_edge_weight(self) -> float:
        """Soma dos pesos de todas as arestas/arcos."""
        # soma o peso de todas as arestas atualmente armazenadas no grafo
        return sum(edge.value for edge in self._edges.values())

    def reachability_matrix_roy(self) -> tuple[list[list[bool]], list[str]]:
        """
        Fecho transitivo (alcançabilidade) via Roy-Warshall sobre o grafo.
        Retorna a matriz booleana R e a ordem das linhas/colunas (vértices ordenados).
        """
        # ordena os vértices e prepara a estrutura base da matriz de alcançabilidade
        vertex_ids = sorted(self._vertices)
        n = len(vertex_ids)
        if n == 0:
            return [], []
        index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        reachability = [[False] * n for _ in range(n)]
        # todo vértice alcança a si mesmo
        for index in range(n):
            reachability[index][index] = True
        # marca as alcançabilidades diretas com base na lista de adjacência
        for vertex_id in vertex_ids:
            for neighbor_id, _, _ in self._adjacency.get(vertex_id, []):
                reachability[index_by_id[vertex_id]][index_by_id[neighbor_id]] = True
        # aplica o fechamento transitivo usando vértices intermediários
        for bridge_vertex in range(n):
            for source_vertex in range(n):
                if not reachability[source_vertex][bridge_vertex]:
                    continue
                row_bridge = reachability[bridge_vertex]
                row_source = reachability[source_vertex]
                for target_vertex in range(n):
                    if row_bridge[target_vertex]:
                        row_source[target_vertex] = True
        return reachability, vertex_ids

    def components_roy(self) -> list[list[str]]:
        """
        Componentes usando a matriz de alcançabilidade (Roy):
        - não dirigido: componentes conexas;
        - dirigido: componentes fortemente conexas (via R[u,v] e R[v,u]).
        """
        # primeiro calcula a matriz de alcançabilidade entre todos os vértices
        reachability, vertex_ids = self.reachability_matrix_roy()
        if not vertex_ids:
            return []
        index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        visited: set[str] = set()
        components: list[list[str]] = []
        if self.directed:
            # em grafos dirigidos, um componente exige alcançabilidade nos dois sentidos
            for vertex_id in vertex_ids:
                if vertex_id in visited:
                    continue
                source_index = index_by_id[vertex_id]
                component = [
                    other_id
                    for other_id in vertex_ids
                    if reachability[source_index][index_by_id[other_id]]
                    and reachability[index_by_id[other_id]][source_index]
                ]
                for member_id in component:
                    visited.add(member_id)
                components.append(sorted(component))
        else:
            # em grafos não dirigidos, basta alcançar os outros vértices do mesmo grupo
            for vertex_id in vertex_ids:
                if vertex_id in visited:
                    continue
                source_index = index_by_id[vertex_id]
                component = [other_id for other_id in vertex_ids if reachability[source_index][index_by_id[other_id]]]
                for member_id in component:
                    visited.add(member_id)
                components.append(sorted(component))
        return components

    def bfs_guided(self, source: str, target: str) -> GuidedSearchResult:
        """Busca em largura guiada: interrompe ao desenfileirar o destino; monta a árvore de BFS."""
        # se origem ou destino não existirem, não tem como executar a busca
        if source not in self._vertices or target not in self._vertices:
            return GuidedSearchResult(source, target, False, [], [])
        # se origem e destino forem o mesmo vértice, o caminho já está resolvido
        if source == target:
            return GuidedSearchResult(source, target, True, [], [source])

        # parent_by_vertex guarda de qual vértice cada vértice foi alcançado na busca
        parent_by_vertex: dict[str, Optional[str]] = {source: None}
        # edge_to_child guarda qual aresta foi usada para chegar em cada vértice
        edge_to_child: dict[str, str] = {}
        queue: deque[str] = deque([source])
        target_reached = False

        # bfs percorre em camadas até encontrar o destino ou esgotar os vértices alcançáveis
        while queue:
            current_vertex = queue.popleft()
            if current_vertex == target:
                target_reached = True
                break
            for neighbor_id, edge_id, _ in self._adjacency.get(current_vertex, []):
                if neighbor_id not in parent_by_vertex:
                    parent_by_vertex[neighbor_id] = current_vertex
                    edge_to_child[neighbor_id] = edge_id
                    queue.append(neighbor_id)

        # reconstrói a árvore de busca usando o mapa de pais criado durante a bfs
        tree_edges: list[tuple[str, str, str]] = []
        for vertex_id, parent_vertex in parent_by_vertex.items():
            if parent_vertex is not None:
                tree_edges.append((parent_vertex, vertex_id, edge_to_child[vertex_id]))

        # se o destino foi encontrado, remonta o caminho voltando pelos pais até a origem
        path: list[str] = []
        if target_reached:
            step_vertex: str | None = target
            while step_vertex is not None:
                path.append(step_vertex)
                step_vertex = parent_by_vertex[step_vertex]
            path.reverse()

        return GuidedSearchResult(source, target, target_reached, tree_edges, path)

    def dfs_guided(self, source: str, target: str) -> GuidedSearchResult:
        """Busca em profundidade guiada; prioriza expandir o vizinho igual ao destino."""
        # se origem ou destino não existirem, não tem como executar a busca
        if source not in self._vertices or target not in self._vertices:
            return GuidedSearchResult(source, target, False, [], [])
        # se origem e destino forem o mesmo vértice, o caminho já está resolvido
        if source == target:
            return GuidedSearchResult(source, target, True, [], [source])

        # estruturas equivalentes às da bfs, mas agora usadas na busca em profundidade
        parent_by_vertex: dict[str, Optional[str]] = {source: None}
        edge_to_child: dict[str, str] = {}
        found = False

        def ordered_neighbors(vertex_id: str) -> list[tuple[str, str, float]]:
            # prioriza o destino se ele já aparecer entre os vizinhos
            neighbors = list(self._adjacency.get(vertex_id, []))
            neighbors.sort(key=lambda item: (0 if item[0] == target else 1, item[0]))
            return neighbors

        def visit(vertex_id: str) -> None:
            nonlocal found
            # interrompe chamadas recursivas extras quando o destino já foi encontrado
            if found:
                return
            if vertex_id == target:
                found = True
                return
            for neighbor_id, edge_id, _ in ordered_neighbors(vertex_id):
                if neighbor_id not in parent_by_vertex:
                    parent_by_vertex[neighbor_id] = vertex_id
                    edge_to_child[neighbor_id] = edge_id
                    visit(neighbor_id)
                    if found:
                        return

        # inicia a dfs a partir da origem
        visit(source)

        # monta a árvore gerada pela dfs com base no mapa de pais
        tree_edges = [
            (parent_vertex, vertex_id, edge_to_child[vertex_id])
            for vertex_id, parent_vertex in parent_by_vertex.items()
            if parent_vertex is not None
        ]

        # se encontrou o destino, remonta o caminho final voltando pelos pais
        path: list[str] = []
        if found:
            step_vertex: str | None = target
            while step_vertex is not None:
                path.append(step_vertex)
                step_vertex = parent_by_vertex[step_vertex]
            path.reverse()

        return GuidedSearchResult(source, target, found, tree_edges, path)

    def build_search_tree_graph(self, result: GuidedSearchResult, name: str | None = None) -> Graph:
        """Monta um grafo apenas com as arestas da árvore de busca (mesmos ids e pesos que no grafo atual)."""
        # cria um novo grafo só com os vértices e arestas que fizeram parte da árvore da busca
        display_name = name or f"Árvore ({result.source} → {result.target})"
        tree_graph = Graph(directed=self.directed, name=display_name)
        vertices_in_tree: set[str] = set()
        if result.source in self._vertices:
            vertices_in_tree.add(result.source)
        # coleta todos os vértices que aparecem nas arestas da árvore de busca
        for parent_vertex, child_vertex, _ in result.tree_edges:
            if parent_vertex in self._vertices:
                vertices_in_tree.add(parent_vertex)
            if child_vertex in self._vertices:
                vertices_in_tree.add(child_vertex)
        # adiciona os vértices ao novo grafo antes de inserir as arestas
        for vertex_id in sorted(vertices_in_tree):
            tree_graph.add_vertex(vertex_id)
        # recria as arestas da árvore usando os mesmos ids e pesos do grafo original
        for parent_vertex, child_vertex, edge_id in result.tree_edges:
            if parent_vertex not in self._vertices or child_vertex not in self._vertices:
                continue
            weight = self.get_edge_value(edge_id)
            if weight is None:
                weight = 1.0
            tree_graph.add_edge(edge_id, parent_vertex, child_vertex, weight)
        return tree_graph

    def prim_mst(self) -> Optional["Graph"]:
        """
        Algoritmo de Prim: retorna a árvore geradora mínima.
        Retorna None se o grafo não for conexo ou for dirigido (Prim não aplica a dirigidos).
        """
        # prim só faz sentido em grafos não dirigidos e com pelo menos um vértice
        if self.directed or not self._vertices:
            return None
        # caso trivial: um grafo com um único vértice já é sua própria árvore mínima
        if len(self._vertices) == 1:
            mst = Graph(directed=False, name=f"MST de {self.name}")
            mst.add_vertex(next(iter(self._vertices)))
            return mst

        # começa a árvore pelo menor id de vértice, só pra ter um ponto de partida fixo
        vertices_in_mst: set[str] = set()
        start_vertex_id = min(self._vertices)
        vertices_in_mst.add(start_vertex_id)
        minimum_spanning_tree = Graph(directed=False, name=f"MST de {self.name}")
        # a mst final terá os mesmos vértices do grafo original
        for vertex_id in self._vertices:
            minimum_spanning_tree.add_vertex(vertex_id)

        # a cada passo, escolhe a menor aresta que liga a árvore atual a um vértice fora dela
        while len(vertices_in_mst) < len(self._vertices):
            best_source_vertex_id = None
            best_target_vertex_id = None
            best_edge_id = None
            best_edge_value = float("inf")
            for vertex_id in vertices_in_mst:
                for neighbor_vertex_id, edge_id, edge_value in self._adjacency[vertex_id]:
                    if neighbor_vertex_id not in vertices_in_mst and edge_value < best_edge_value:
                        best_source_vertex_id = vertex_id
                        best_target_vertex_id = neighbor_vertex_id
                        best_edge_id = edge_id
                        best_edge_value = edge_value
            # se não encontrou uma aresta válida, o grafo não é conexo
            if best_source_vertex_id is None or best_target_vertex_id is None or best_edge_id is None:
                return None
            # adiciona o novo vértice e a melhor aresta encontrada na mst
            vertices_in_mst.add(best_target_vertex_id)
            minimum_spanning_tree.add_edge(
                best_edge_id,
                best_source_vertex_id,
                best_target_vertex_id,
                best_edge_value,
            )

        return minimum_spanning_tree

    @property
    def vertices(self) -> set[str]:
        # devolve uma cópia pra evitar alteração externa direta no conjunto interno
        return self._vertices.copy()

    def add_vertex_with_coords(self, vertex_id: str, x: float, y: float) -> bool:
        """Insere um vértice com coordenadas (x, y)."""
        if not self.add_vertex(vertex_id):
            return False
        self._coordinates[vertex_id] = (x, y)
        return True

    def get_vertex_coords(self, vertex_id: str) -> Optional[tuple[float, float]]:
        #Retorna as coordenadas (x, y) de um vértice
        return self._coordinates.get(vertex_id)

    def manhattan_distance(self, v1: str, v2: str) -> Optional[float]:
        #Calcula distância de Manhattan entre dois vértices.
        # Interpreta as coordenadas como (latitude, longitude) em graus.
        # Converte diferenças em graus para quilômetros aproximados:
        #  - 1 grau latitude ≈ 111.32 km
        #  - 1 grau longitude ≈ 111.32 * cos(mean_latitude) km
        coords1 = self._coordinates.get(v1)
        coords2 = self._coordinates.get(v2)
        if coords1 is None or coords2 is None:
            return None
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        try:

            dlat = abs(float(lat1) - float(lat2))
            dlon = abs(float(lon1) - float(lon2))
            mean_lat_rad = math.radians((float(lat1) + float(lat2)) / 2.0)
            km_per_deg_lat = 111.32
            km_per_deg_lon = 111.32 * math.cos(mean_lat_rad)
            return dlat * km_per_deg_lat + dlon * km_per_deg_lon
        except Exception:
            # Se ocorrer algum problema na conversão, retorna None para indicar impossibilidade
            return None

    def dsatur_coloring(self) -> dict[str, int]:
        """
        Algoritmo DSATUR para coloração de grafo.
        Retorna dicionário {vertex_id: color} onde colors são inteiros começando de 0.
        """
        coloring: dict[str, int] = {}
        
        if not self._vertices:
            return coloring

        # Ordena vértices por grau decrescente (começa com o vértice de maior grau)
        vertex_degrees = [(v, len(self._adjacency.get(v, []))) for v in self._vertices]
        vertex_degrees.sort(key=lambda x: x[1], reverse=True)

        # Colore o vértice com maior grau com cor 0
        first_vertex = vertex_degrees[0][0]
        coloring[first_vertex] = 0

        # Processa vértices restantes em ordem de DSAT
        while len(coloring) < len(self._vertices):
            # Calcula DSAT (grau de saturação) para cada vértice não colorido
            best_vertex = None
            best_dsat = -1
            best_degree = -1

            for vertex in self._vertices:
                if vertex in coloring:
                    continue

                # DSAT = número de cores diferentes adjacentes ao vértice
                neighbor_colors: set[int] = set()
                for neighbor, _, _ in self._adjacency.get(vertex, []):
                    if neighbor in coloring:
                        neighbor_colors.add(coloring[neighbor])

                dsat = len(neighbor_colors)
                degree = len(self._adjacency.get(vertex, []))

                # Seleciona vértice com maior DSAT (desempate por grau)
                if dsat > best_dsat or (dsat == best_dsat and degree > best_degree):
                    best_vertex = vertex
                    best_dsat = dsat
                    best_degree = degree

            if best_vertex is None:
                break

            # Encontra a menor cor disponível para best_vertex
            used_colors: set[int] = set()
            for neighbor, _, _ in self._adjacency.get(best_vertex, []):
                if neighbor in coloring:
                    used_colors.add(coloring[neighbor])

            # Atribui a menor cor não usada
            color = 0
            while color in used_colors:
                color += 1
            coloring[best_vertex] = color

        return coloring

    def a_star(self, source: str, target: str) -> tuple[Optional[list[str]], Optional[float], dict[str, float]]:
        """
        Algoritmo A* para encontrar o caminho mínimo.
        Usa distância de Manhattan como heurística.
        Retorna (caminho, distância_total, h_table).
        """
        

        if source not in self._vertices or target not in self._vertices:
            return None, None, {}

        if source == target:
            h_table = {
                vertex_id: self.manhattan_distance(vertex_id, target) or 0.0
                for vertex_id in sorted(self._vertices)
            }
            return [source], 0.0, h_table

        # Verifica se todos os vértices têm coordenadas
        if any(self.get_vertex_coords(vertex_id) is None for vertex_id in self._vertices):
            return None, None, {}

        # Estruturas para A*
        open_set: list[tuple[float, str]] = [(0, source)]  # (f_score, vertex)
        came_from: dict[str, str] = {}
        g_score: dict[str, float] = {source: 0.0}
        f_score: dict[str, float] = {source: self.manhattan_distance(source, target) or 0.0}

        closed_set: set[str] = set()

        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current in closed_set:
                continue

            if current == target:
                # Reconstrói o caminho
                path = [current]
                step = current
                while step in came_from:
                    step = came_from[step]
                    path.append(step)
                path.reverse()
                h_table = {
                    vertex_id: self.manhattan_distance(vertex_id, target) or 0.0
                    for vertex_id in sorted(self._vertices)
                }
                return path, g_score[target], h_table

            closed_set.add(current)

            # Examina vizinhos
            for neighbor, edge_id, edge_weight in self._adjacency.get(current, []):
                if neighbor in closed_set:
                    continue

                tentative_g = g_score[current] + edge_weight

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_score = self.manhattan_distance(neighbor, target) or 0.0
                    f_score[neighbor] = tentative_g + h_score
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None, None, {}



    @property
    def edges(self) -> dict[str, Edge]:
        # devolve uma cópia pra evitar alteração externa direta no dicionário interno
        return self._edges.copy()

    def get_adjacency_list(self) -> dict[str, list[tuple[str, str, float]]]:
        """Retorna cópia da lista de adjacência (vértice -> [(vizinho, edge_id, peso), ...])."""
        # cria uma cópia superficial da estrutura de adjacência pra leitura externa
        return {vertex_id: list(adjacency_entries) for vertex_id, adjacency_entries in self._adjacency.items()}
