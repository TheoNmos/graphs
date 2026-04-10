from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Optional


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
        self._adjacency: dict[str, list[tuple[str, str, float]]] = {} # lista de adjacência do grafo

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
        edge = self._edges[edge_id]
        source_vertex_id = edge.source_vertex_id
        target_vertex_id = edge.target_vertex_id
        self._adjacency[source_vertex_id] = [
            (neighbor_vertex_id, adjacent_edge_id, edge_value)
            for neighbor_vertex_id, adjacent_edge_id, edge_value in self._adjacency[source_vertex_id]
            if adjacent_edge_id != edge_id
        ]
        if not self.directed:
            self._adjacency[target_vertex_id] = [
                (neighbor_vertex_id, adjacent_edge_id, edge_value)
                for neighbor_vertex_id, adjacent_edge_id, edge_value in self._adjacency[target_vertex_id]
                if adjacent_edge_id != edge_id
            ]
        del self._edges[edge_id]
        return True

    def are_adjacent(self, first_vertex_id: str, second_vertex_id: str) -> bool:
        """Verifica se dois vértices são adjacentes."""
        if first_vertex_id not in self._adjacency:
            return False
        return any(
            neighbor_vertex_id == second_vertex_id for neighbor_vertex_id, _, _ in self._adjacency[first_vertex_id]
        )

    def get_edge_value(self, edge_id: str) -> Optional[float]:
        """Retorna o valor da aresta/arco a."""
        edge = self._edges.get(edge_id)
        return edge.value if edge else None

    def get_edge_value_by_vertices(
        self,
        source_vertex_id: str,
        target_vertex_id: str,
    ) -> Optional[float]:
        """Retorna o valor da aresta entre dois vértices (primeira encontrada)."""
        for neighbor_vertex_id, _, edge_value in self._adjacency.get(source_vertex_id, []):
            if neighbor_vertex_id == target_vertex_id:
                return edge_value
        return None

    def get_edge_extremities(self, edge_id: str) -> Optional[tuple[str, str]]:
        """Retorna as extremidades (v, w) da aresta/arco a."""
        edge = self._edges.get(edge_id)
        return (edge.source_vertex_id, edge.target_vertex_id) if edge else None

    def get_edge_by_vertices(
        self,
        source_vertex_id: str,
        target_vertex_id: str,
    ) -> Optional[str]:
        """Retorna o id da primeira aresta entre dois vértices."""
        for neighbor_vertex_id, edge_id, _ in self._adjacency.get(source_vertex_id, []):
            if neighbor_vertex_id == target_vertex_id:
                return edge_id
        return None

    def adjacency_matrix(self) -> list[list[float]]:
        """Retorna a matriz de adjacência (valores são pesos; 0 se não adjacente)."""
        vertex_ids = sorted(self._vertices)
        vertex_count = len(vertex_ids)
        vertex_index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        adjacency_matrix = [[0.0] * vertex_count for _ in range(vertex_count)]
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
        vertex_ids = sorted(self._vertices)
        edges_with_ids = sorted(self._edges.items(), key=lambda item: item[0])
        vertex_count = len(vertex_ids)
        edge_count = len(edges_with_ids)
        vertex_index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        incidence_matrix = [[0] * edge_count for _ in range(vertex_count)]
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
        lines = [f"=== {self.name} ({'Dirigido' if self.directed else 'Não Dirigido'}) ==="]
        lines.append(f"Vértices: {sorted(self._vertices)}")
        lines.append("Arestas/Arcos:")
        for edge_id, edge in sorted(self._edges.items(), key=lambda item: item[0]):
            arrow = " -> " if self.directed else " <-> "
            lines.append(f"  {edge_id}: {edge.source_vertex_id}{arrow}{edge.target_vertex_id} (valor={edge.value})")
        lines.append("\nLista de Adjacência:")
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
        return sum(edge.value for edge in self._edges.values())

    def reachability_matrix_roy(self) -> tuple[list[list[bool]], list[str]]:
        """
        Fecho transitivo (alcançabilidade) via Roy–Warshall sobre o grafo.
        Retorna a matriz booleana R e a ordem das linhas/colunas (vértices ordenados).
        """
        vertex_ids = sorted(self._vertices)
        n = len(vertex_ids)
        if n == 0:
            return [], []
        index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        reachability = [[False] * n for _ in range(n)]
        for index in range(n):
            reachability[index][index] = True
        for vertex_id in vertex_ids:
            for neighbor_id, _, _ in self._adjacency.get(vertex_id, []):
                reachability[index_by_id[vertex_id]][index_by_id[neighbor_id]] = True
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
        reachability, vertex_ids = self.reachability_matrix_roy()
        if not vertex_ids:
            return []
        index_by_id = {vertex_id: index for index, vertex_id in enumerate(vertex_ids)}
        visited: set[str] = set()
        components: list[list[str]] = []
        if self.directed:
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
        if source not in self._vertices or target not in self._vertices:
            return GuidedSearchResult(source, target, False, [], [])
        if source == target:
            return GuidedSearchResult(source, target, True, [], [source])

        parent_by_vertex: dict[str, Optional[str]] = {source: None}
        edge_to_child: dict[str, str] = {}
        queue: deque[str] = deque([source])
        target_reached = False

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

        tree_edges: list[tuple[str, str, str]] = []
        for vertex_id, parent_vertex in parent_by_vertex.items():
            if parent_vertex is not None:
                tree_edges.append((parent_vertex, vertex_id, edge_to_child[vertex_id]))

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
        if source not in self._vertices or target not in self._vertices:
            return GuidedSearchResult(source, target, False, [], [])
        if source == target:
            return GuidedSearchResult(source, target, True, [], [source])

        parent_by_vertex: dict[str, Optional[str]] = {source: None}
        edge_to_child: dict[str, str] = {}
        found = False

        def ordered_neighbors(vertex_id: str) -> list[tuple[str, str, float]]:
            neighbors = list(self._adjacency.get(vertex_id, []))
            neighbors.sort(key=lambda item: (0 if item[0] == target else 1, item[0]))
            return neighbors

        def visit(vertex_id: str) -> None:
            nonlocal found
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

        visit(source)

        tree_edges = [
            (parent_vertex, vertex_id, edge_to_child[vertex_id])
            for vertex_id, parent_vertex in parent_by_vertex.items()
            if parent_vertex is not None
        ]

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
        display_name = name or f"Árvore ({result.source} → {result.target})"
        tree_graph = Graph(directed=self.directed, name=display_name)
        vertices_in_tree: set[str] = set()
        if result.source in self._vertices:
            vertices_in_tree.add(result.source)
        for parent_vertex, child_vertex, _ in result.tree_edges:
            if parent_vertex in self._vertices:
                vertices_in_tree.add(parent_vertex)
            if child_vertex in self._vertices:
                vertices_in_tree.add(child_vertex)
        for vertex_id in sorted(vertices_in_tree):
            tree_graph.add_vertex(vertex_id)
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
        if self.directed or not self._vertices:
            return None
        if len(self._vertices) == 1:
            mst = Graph(directed=False, name=f"MST de {self.name}")
            mst.add_vertex(next(iter(self._vertices)))
            return mst

        vertices_in_mst: set[str] = set()
        start_vertex_id = min(self._vertices)
        vertices_in_mst.add(start_vertex_id)
        minimum_spanning_tree = Graph(directed=False, name=f"MST de {self.name}")
        for vertex_id in self._vertices:
            minimum_spanning_tree.add_vertex(vertex_id)

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
            if best_source_vertex_id is None or best_target_vertex_id is None or best_edge_id is None:
                return None
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
        return self._vertices.copy()

    @property
    def edges(self) -> dict[str, Edge]:
        return self._edges.copy()

    def get_adjacency_list(self) -> dict[str, list[tuple[str, str, float]]]:
        """Retorna cópia da lista de adjacência (vértice -> [(vizinho, edge_id, peso), ...])."""
        return {vertex_id: list(adjacency_entries) for vertex_id, adjacency_entries in self._adjacency.items()}
