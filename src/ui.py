"""Interface moderna em janela usando Flask + pyvis + pywebview."""

from __future__ import annotations

import json
import re
import socket
import threading
import time
import urllib.request
from typing import Any, Iterable

from flask import Flask, jsonify, render_template_string, request
from pyvis.network import Network

from .graph import Graph

try:
    import webview  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - depende do ambiente local
    webview = None


INDEX_HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Grafos</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: rgba(17, 24, 39, 0.88);
      --panel-strong: #111827;
      --panel-soft: #172033;
      --border: rgba(148, 163, 184, 0.18);
      --text: #e5eefc;
      --muted: #98a7c2;
      --accent: #4f9cff;
      --accent-2: #22c55e;
      --danger: #ef4444;
      --warning: #f59e0b;
      --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
      --radius: 18px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(79, 156, 255, 0.14), transparent 28%),
        radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 24%),
        linear-gradient(180deg, #09101c, #0f172a 48%, #0b1020);
      color: var(--text);
      min-height: 100vh;
    }

    .app {
      padding: 24px;
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 20px;
      min-height: 100vh;
    }

    .sidebar, .content {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      overflow: hidden;
    }

    .card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px 0;
    }

    .card-body {
      padding: 18px;
    }

    h1, h2, h3, p { margin: 0; }

    h1 {
      font-size: 28px;
      letter-spacing: -0.02em;
    }

    h2 {
      font-size: 15px;
      color: var(--muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .hero {
      padding: 22px;
      background: linear-gradient(135deg, rgba(79, 156, 255, 0.18), rgba(34, 197, 94, 0.12));
    }

    .hero p {
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.5;
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }

    .chip {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(15, 23, 42, 0.85);
      color: var(--text);
      font-size: 13px;
    }

    form {
      display: grid;
      gap: 10px;
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    input, select, button, textarea {
      width: 100%;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(15, 23, 42, 0.92);
      color: var(--text);
      border-radius: 12px;
      padding: 11px 12px;
      font: inherit;
      outline: none;
    }

    input:focus, select:focus {
      border-color: rgba(79, 156, 255, 0.65);
      box-shadow: 0 0 0 3px rgba(79, 156, 255, 0.18);
    }

    button {
      cursor: pointer;
      font-weight: 600;
      transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
    }

    button:hover {
      transform: translateY(-1px);
      border-color: rgba(79, 156, 255, 0.48);
    }

    .primary { background: linear-gradient(135deg, #2563eb, #3b82f6); }
    .success { background: linear-gradient(135deg, #15803d, #22c55e); }
    .danger { background: linear-gradient(135deg, #b91c1c, #ef4444); }
    .ghost { background: rgba(15, 23, 42, 0.92); }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .toolbar button {
      width: auto;
      min-width: 132px;
    }

    .status {
      padding: 14px 16px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 14px;
      min-height: 52px;
      display: flex;
      align-items: center;
    }

    .visual-frame {
      width: 100%;
      height: 540px;
      border: 0;
      background: #0f172a;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    }

    th {
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .matrix-wrap {
      overflow: auto;
      border-radius: 14px;
      border: 1px solid rgba(148, 163, 184, 0.12);
      background: rgba(15, 23, 42, 0.72);
      max-height: 280px;
    }

    .result {
      min-height: 68px;
      border-radius: 14px;
      padding: 14px 16px;
      background: rgba(15, 23, 42, 0.74);
      border: 1px solid rgba(148, 163, 184, 0.12);
      color: var(--text);
      line-height: 1.5;
    }

    .muted { color: var(--muted); }

    @media (max-width: 1180px) {
      .app { grid-template-columns: 1fr; }
      .grid-2, .grid-3, .row { grid-template-columns: 1fr; }
      .visual-frame { height: 420px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <section class="card hero">
        <h1>Grafos</h1>
        <p>Interface em janela com CRUD, matrizes e árvore geradora mínima, usando a lógica Python do projeto e visualização interativa com pyvis.</p>
        <div class="chips">
          <div class="chip" id="chip-name">Nome: -</div>
          <div class="chip" id="chip-type">Tipo: -</div>
          <div class="chip" id="chip-counts">0 vértices / 0 arestas</div>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Novo Grafo</h2></div>
        <div class="card-body">
          <form id="graph-form">
            <label>Nome
              <input id="graph-name" placeholder="Grafo Principal">
            </label>
            <label>Tipo
              <select id="graph-directed">
                <option value="false">Não dirigido</option>
                <option value="true">Dirigido</option>
              </select>
            </label>
            <button class="primary" type="submit">Criar / Reiniciar grafo</button>
          </form>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Vértices</h2></div>
        <div class="card-body">
          <form id="vertex-add-form">
            <label>Próximo id automático
              <input id="vertex-next-id" readonly>
            </label>
            <button class="success" type="submit">Adicionar vértice</button>
          </form>
          <form id="vertex-remove-form" style="margin-top:12px">
            <label>Remover vértice
              <input id="vertex-remove-id" placeholder="Ex.: A">
            </label>
            <button class="danger" type="submit">Remover vértice</button>
          </form>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Arestas / Arcos</h2></div>
        <div class="card-body">
          <form id="edge-add-form">
            <div class="row">
              <label>Próximo id automático
                <input id="edge-next-id" readonly>
              </label>
              <label>Valor
                <input id="edge-value" type="number" step="any" value="1">
              </label>
            </div>
            <div class="row">
              <label>Origem
                <input id="edge-v" placeholder="A">
              </label>
              <label>Destino
                <input id="edge-w" placeholder="B">
              </label>
            </div>
            <button class="success" type="submit">Adicionar ligação</button>
          </form>
          <form id="edge-remove-form" style="margin-top:12px">
            <label>Remover por id
              <input id="edge-remove-id" placeholder="e1">
            </label>
            <button class="danger" type="submit">Remover ligação</button>
          </form>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Consultas</h2></div>
        <div class="card-body">
          <form id="adjacency-form">
            <div class="row">
              <label>Vértice 1
                <input id="adj-v" placeholder="A">
              </label>
              <label>Vértice 2
                <input id="adj-w" placeholder="B">
              </label>
            </div>
            <button class="ghost" type="submit">Verificar adjacência</button>
          </form>
          <form id="edge-query-form" style="margin-top:12px">
            <label>Id da aresta
              <input id="edge-query-id" placeholder="e1">
            </label>
            <div class="row">
              <button class="ghost" id="btn-edge-value" type="button">Consultar valor</button>
              <button class="ghost" id="btn-edge-extremities" type="button">Consultar extremidades</button>
            </div>
          </form>
        </div>
      </section>
    </aside>

    <main class="content">
      <section class="card">
        <div class="card-head">
          <div>
            <h2>Visualização</h2>
            <p class="muted">Arraste os nós, use zoom e alterne entre o grafo e a MST.</p>
          </div>
          <div class="toolbar">
            <button class="ghost" id="btn-view-graph" type="button">Ver grafo</button>
            <button class="ghost" id="btn-view-mst" type="button">Ver MST (Prim)</button>
            <button class="primary" id="btn-refresh" type="button">Atualizar</button>
          </div>
        </div>
        <div class="card-body" style="padding-top:14px">
          <iframe id="graph-frame" class="visual-frame" title="Grafo"></iframe>
        </div>
        <div class="status" id="status-bar">Carregando aplicação...</div>
      </section>

      <section class="grid-3">
        <section class="card">
          <div class="card-head"><h2>Resultado</h2></div>
          <div class="card-body"><div class="result" id="result-box">Nenhuma consulta executada.</div></div>
        </section>
        <section class="card">
          <div class="card-head"><h2>Vértices</h2></div>
          <div class="card-body"><div id="vertices-box" class="result"></div></div>
        </section>
        <section class="card">
          <div class="card-head"><h2>MST</h2></div>
          <div class="card-body"><div id="mst-box" class="result"></div></div>
        </section>
      </section>

      <section class="grid-2">
        <section class="card">
          <div class="card-head"><h2>Arestas / Arcos</h2></div>
          <div class="card-body">
            <div class="matrix-wrap">
              <table id="edges-table"></table>
            </div>
          </div>
        </section>
        <section class="card">
          <div class="card-head"><h2>Lista de Adjacência</h2></div>
          <div class="card-body">
            <div class="matrix-wrap">
              <table id="adjacency-list-table"></table>
            </div>
          </div>
        </section>
      </section>

      <section class="grid-2">
        <section class="card">
          <div class="card-head"><h2>Matriz de Adjacência</h2></div>
          <div class="card-body">
            <div class="matrix-wrap">
              <table id="adj-matrix-table"></table>
            </div>
          </div>
        </section>
        <section class="card">
          <div class="card-head"><h2>Matriz de Incidência</h2></div>
          <div class="card-body">
            <div class="matrix-wrap">
              <table id="inc-matrix-table"></table>
            </div>
          </div>
        </section>
      </section>
    </main>
  </div>

  <script>
    let currentView = "graph";

    async function api(path, method = "GET", body = null) {
      const options = { method, headers: {} };
      if (body !== null) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
      }
      const response = await fetch(path, options);
      return response.json();
    }

    function setStatus(message) {
      document.getElementById("status-bar").textContent = message || "Pronto.";
    }

    function renderSimpleList(targetId, values, emptyText) {
      const el = document.getElementById(targetId);
      if (!values.length) {
        el.textContent = emptyText;
        return;
      }
      el.innerHTML = values.map((value) => `<div>${value}</div>`).join("");
    }

    function renderTable(targetId, headers, rows, emptyText) {
      const table = document.getElementById(targetId);
      if (!rows.length) {
        table.innerHTML = `<tr><td>${emptyText}</td></tr>`;
        return;
      }
      const head = `<thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>`;
      const body = `<tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>`;
      table.innerHTML = head + body;
    }

    function renderMatrix(targetId, matrix) {
      const table = document.getElementById(targetId);
      const columns = matrix.columns || [];
      const rows = matrix.rows || [];
      const values = matrix.values || [];

      if (!rows.length || !columns.length) {
        table.innerHTML = `<tr><td>Nenhum dado para exibir.</td></tr>`;
        return;
      }

      let html = "<thead><tr><th></th>";
      html += columns.map((column) => `<th>${column}</th>`).join("");
      html += "</tr></thead><tbody>";

      rows.forEach((rowName, rowIndex) => {
        html += `<tr><th>${rowName}</th>`;
        html += values[rowIndex].map((value) => `<td>${value}</td>`).join("");
        html += "</tr>";
      });

      html += "</tbody>";
      table.innerHTML = html;
    }

    function renderState(payload) {
      const state = payload.state;
      const graph = state.graph;

      document.getElementById("chip-name").textContent = `Nome: ${graph.name}`;
      document.getElementById("chip-type").textContent = `Tipo: ${graph.directed ? "Dirigido" : "Não dirigido"}`;
      document.getElementById("chip-counts").textContent = `${graph.vertices.length} vértices / ${graph.edges.length} arestas`;
      document.getElementById("graph-name").value = graph.name;
      document.getElementById("graph-directed").value = String(graph.directed);
      document.getElementById("vertex-next-id").value = state.next_ids.vertex;
      document.getElementById("edge-next-id").value = state.next_ids.edge;
      setStatus(payload.message || "Pronto.");

      renderSimpleList("vertices-box", graph.vertices, "Nenhum vértice cadastrado.");

      const mstText = state.mst
        ? `MST disponível com ${state.mst.vertices.length} vértices e ${state.mst.edges.length} arestas.`
        : "MST indisponível para o estado atual.";
      document.getElementById("mst-box").textContent = mstText;

      renderTable(
        "edges-table",
        ["Id", "Origem", "Destino", "Valor"],
        graph.edges.map((edge) => [edge.id, edge.source_vertex_id, edge.target_vertex_id, edge.value]),
        "Nenhuma aresta cadastrada."
      );

      renderTable(
        "adjacency-list-table",
        ["Vértice", "Conexões"],
        graph.adjacency.map((item) => [item.vertex, item.neighbors.length ? item.neighbors.join(", ") : "[]"]),
        "Lista de adjacência vazia."
      );

      renderMatrix("adj-matrix-table", state.adjacency_matrix);
      renderMatrix("inc-matrix-table", state.incidence_matrix);
    }

    function refreshGraphFrame() {
      document.getElementById("graph-frame").src = `/graph/frame?view=${currentView}&t=${Date.now()}`;
    }

    async function refreshState() {
      const payload = await api("/api/state");
      renderState(payload);
      refreshGraphFrame();
    }

    async function submitJson(path, body) {
      const payload = await api(path, "POST", body);
      if (payload.result) {
        document.getElementById("result-box").textContent = payload.result;
      }
      await refreshState();
    }

    document.getElementById("graph-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      currentView = "graph";
      await submitJson("/api/graph/reset", {
        name: document.getElementById("graph-name").value,
        directed: document.getElementById("graph-directed").value === "true",
      });
    });

    document.getElementById("vertex-add-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitJson("/api/vertex/add", {});
    });

    document.getElementById("vertex-remove-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitJson("/api/vertex/remove", { vertex: document.getElementById("vertex-remove-id").value });
      document.getElementById("vertex-remove-id").value = "";
    });

    document.getElementById("edge-add-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitJson("/api/edge/add", {
        v: document.getElementById("edge-v").value,
        w: document.getElementById("edge-w").value,
        value: document.getElementById("edge-value").value,
      });
      document.getElementById("edge-v").value = "";
      document.getElementById("edge-w").value = "";
    });

    document.getElementById("edge-remove-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      await submitJson("/api/edge/remove", { edge_id: document.getElementById("edge-remove-id").value });
      document.getElementById("edge-remove-id").value = "";
    });

    document.getElementById("adjacency-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const payload = await api("/api/query/adjacent", "POST", {
        v: document.getElementById("adj-v").value,
        w: document.getElementById("adj-w").value,
      });
      document.getElementById("result-box").textContent = payload.result;
      await refreshState();
    });

    document.getElementById("btn-edge-value").addEventListener("click", async () => {
      const edgeId = document.getElementById("edge-query-id").value;
      const payload = await api(`/api/query/edge/${encodeURIComponent(edgeId)}/value`);
      document.getElementById("result-box").textContent = payload.result;
      await refreshState();
    });

    document.getElementById("btn-edge-extremities").addEventListener("click", async () => {
      const edgeId = document.getElementById("edge-query-id").value;
      const payload = await api(`/api/query/edge/${encodeURIComponent(edgeId)}/extremities`);
      document.getElementById("result-box").textContent = payload.result;
      await refreshState();
    });

    document.getElementById("btn-view-graph").addEventListener("click", async () => {
      currentView = "graph";
      refreshGraphFrame();
      setStatus("Mostrando o grafo atual.");
    });

    document.getElementById("btn-view-mst").addEventListener("click", async () => {
      currentView = "mst";
      refreshGraphFrame();
      setStatus("Mostrando a árvore geradora mínima quando disponível.");
    });

    document.getElementById("btn-refresh").addEventListener("click", refreshState);

    refreshState();
  </script>
</body>
</html>
"""


class GraphApp:
    """Controla o estado da aplicação e as operações sobre o grafo."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.graph = Graph(directed=False, name="Grafo Principal")
        self.message = "Aplicação carregada."

    def _set_message(self, message: str) -> None:
        self.message = message

    @staticmethod
    def _next_id(existing_ids: Iterable[str], prefix: str) -> str:
        highest = 0
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
        for item in existing_ids:
            match = pattern.match(item)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"{prefix}{highest + 1}"

    def next_vertex_id(self) -> str:
        return self._next_id(self.graph.vertices, "v")

    def next_edge_id(self) -> str:
        return self._next_id(self.graph.edges.keys(), "e")

    def reset_graph(self, name: str, directed: bool) -> str:
        with self._lock:
            self.graph = Graph(directed=directed, name=name or "Grafo Principal")
            self._set_message("Novo grafo criado com sucesso.")
            return self.message

    def add_vertex(self, vertex: str = "") -> str:
        with self._lock:
            vertex = vertex.strip()
            if not vertex:
                vertex = self.next_vertex_id()
            if self.graph.add_vertex(vertex):
                self._set_message(f"Vértice '{vertex}' adicionado.")
            else:
                generated = self.next_vertex_id()
                if generated != vertex and self.graph.add_vertex(generated):
                    self._set_message(f"Vértice '{generated}' adicionado.")
                else:
                    self._set_message(f"Vértice '{vertex}' já existe.")
            return self.message

    def remove_vertex(self, vertex: str) -> str:
        with self._lock:
            vertex = vertex.strip()
            if not vertex:
                self._set_message("Informe um identificador de vértice.")
            elif self.graph.remove_vertex(vertex):
                self._set_message(f"Vértice '{vertex}' removido.")
            else:
                self._set_message(f"Vértice '{vertex}' não encontrado.")
            return self.message

    def add_edge(self, edge_id: str, v: str, w: str, value: Any) -> str:
        with self._lock:
            edge_id = edge_id.strip()
            v = v.strip()
            w = w.strip()
            try:
                weight = float(value)
            except (TypeError, ValueError):
                self._set_message("O valor da aresta deve ser numérico.")
                return self.message

            if not edge_id:
                edge_id = self.next_edge_id()

            if not v or not w:
                self._set_message("Preencha origem e destino da aresta.")
            elif self.graph.add_edge(edge_id, v, w, weight):
                self._set_message(f"Ligação '{edge_id}' adicionada entre '{v}' e '{w}'.")
            else:
                generated = self.next_edge_id()
                if generated != edge_id and self.graph.add_edge(generated, v, w, weight):
                    self._set_message(f"Ligação '{generated}' adicionada entre '{v}' e '{w}'.")
                else:
                    self._set_message("Não foi possível adicionar a ligação. Verifique os vértices.")
            return self.message

    def remove_edge(self, edge_id: str) -> str:
        with self._lock:
            edge_id = edge_id.strip()
            if not edge_id:
                self._set_message("Informe o id da aresta.")
            elif self.graph.remove_edge(edge_id):
                self._set_message(f"Ligação '{edge_id}' removida.")
            else:
                self._set_message(f"Ligação '{edge_id}' não encontrada.")
            return self.message

    def query_adjacent(self, v: str, w: str) -> str:
        with self._lock:
            v = v.strip()
            w = w.strip()
            if not v or not w:
                self._set_message("Informe dois vértices para verificar adjacência.")
            else:
                result = self.graph.are_adjacent(v, w)
                self._set_message(f"Adjacência entre '{v}' e '{w}': {result}.")
            return self.message

    def query_edge_value(self, edge_id: str) -> str:
        with self._lock:
            edge_id = edge_id.strip()
            if not edge_id:
                self._set_message("Informe o id da aresta.")
            else:
                value = self.graph.get_edge_value(edge_id)
                if value is None:
                    self._set_message(f"Aresta '{edge_id}' não encontrada.")
                else:
                    self._set_message(f"Valor da aresta '{edge_id}': {value}.")
            return self.message

    def query_edge_extremities(self, edge_id: str) -> str:
        with self._lock:
            edge_id = edge_id.strip()
            if not edge_id:
                self._set_message("Informe o id da aresta.")
            else:
                extremities = self.graph.get_edge_extremities(edge_id)
                if extremities is None:
                    self._set_message(f"Aresta '{edge_id}' não encontrada.")
                else:
                    self._set_message(
                        f"Extremidades da aresta '{edge_id}': ({extremities[0]}, {extremities[1]})."
                    )
            return self.message

    def _serialize_graph(self, graph: Graph | None) -> dict[str, Any] | None:
        if graph is None:
            return None

        adjacency = graph.get_adjacency_list()
        return {
            "name": graph.name,
            "directed": graph.directed,
            "vertices": sorted(graph.vertices),
            "edges": [
                {
                    "id": edge.id,
                    "source_vertex_id": edge.source_vertex_id,
                    "target_vertex_id": edge.target_vertex_id,
                    "value": edge.value,
                }
                for edge in sorted(graph.edges.values(), key=lambda item: item.id)
            ],
            "adjacency": [
                {
                    "vertex": vertex,
                    "neighbors": [
                        f"{neighbor} [{edge_id}, {weight}]"
                        for neighbor, edge_id, weight in adjacency[vertex]
                    ],
                }
                for vertex in sorted(adjacency)
            ],
        }

    def _adjacency_matrix_payload(self) -> dict[str, Any]:
        vertices = self.graph.adjacency_matrix_vertices()
        return {
            "rows": vertices,
            "columns": vertices,
            "values": self.graph.adjacency_matrix(),
        }

    def _incidence_matrix_payload(self) -> dict[str, Any]:
        return {
            "rows": self.graph.incidence_matrix_vertices(),
            "columns": self.graph.incidence_matrix_edges(),
            "values": self.graph.incidence_matrix(),
        }

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            mst = self.graph.prim_mst()
            return {
                "graph": self._serialize_graph(self.graph),
                "adjacency_matrix": self._adjacency_matrix_payload(),
                "incidence_matrix": self._incidence_matrix_payload(),
                "mst": self._serialize_graph(mst),
                "next_ids": {
                    "vertex": self.next_vertex_id(),
                    "edge": self.next_edge_id(),
                },
            }

    def render_graph_html(self, view: str) -> str:
        with self._lock:
            graph = self.graph if view == "graph" else self.graph.prim_mst()
            title = self.graph.name if view == "graph" else f"MST de {self.graph.name}"

            if graph is None:
                return self._empty_graph_html(
                    "MST indisponível",
                    "A árvore geradora mínima só existe para grafos não dirigidos e conexos.",
                )

            if not graph.vertices:
                return self._empty_graph_html(
                    title,
                    "Adicione vértices e arestas para começar a visualizar o grafo.",
                )

            network = Network(
                height="100%",
                width="100%",
                directed=graph.directed,
                notebook=False,
                bgcolor="#0f172a",
                cdn_resources="in_line",
            )
            network.barnes_hut(gravity=-32000, central_gravity=0.16, spring_length=190, damping=0.85)

            adjacency = graph.get_adjacency_list()
            for vertex in sorted(graph.vertices):
                degree = len(adjacency.get(vertex, []))
                network.add_node(
                    vertex,
                    label=vertex,
                    title=f"Vértice: {vertex}<br>Conexões: {degree}",
                    shape="dot",
                    size=24 + degree * 2,
                    color="#4f9cff",
                )

            for edge in sorted(graph.edges.values(), key=lambda item: item.id):
                arrows = "to" if graph.directed else ""
                network.add_edge(
                    edge.source_vertex_id,
                    edge.target_vertex_id,
                    label=f"{edge.id} ({edge.value:g})",
                    title=(
                        f"Id: {edge.id}<br>"
                        f"Valor: {edge.value:g}<br>"
                        f"Extremidades: {edge.source_vertex_id} {'→' if graph.directed else '↔'} {edge.target_vertex_id}"
                    ),
                    arrows=arrows,
                    color="#93c5fd" if view == "graph" else "#22c55e",
                    width=2.2,
                )

            network.set_options(
                json.dumps(
                    {
                        "nodes": {
                            "borderWidth": 2,
                            "font": {"size": 18, "color": "#eff6ff", "face": "Segoe UI"},
                        },
                        "edges": {
                            "font": {"color": "#dbeafe", "size": 14, "strokeWidth": 0},
                            "smooth": {"enabled": True, "type": "dynamic"},
                        },
                        "interaction": {
                            "hover": True,
                            "navigationButtons": True,
                            "keyboard": True,
                        },
                        "physics": {
                            "stabilization": {"iterations": 180},
                            "barnesHut": {
                                "gravitationalConstant": -32000,
                                "springLength": 180,
                                "damping": 0.85,
                            },
                        },
                    }
                )
            )
            return network.generate_html()

    @staticmethod
    def _empty_graph_html(title: str, message: str) -> str:
        return f"""
        <!doctype html>
        <html lang="pt-BR">
        <head>
          <meta charset="utf-8">
          <style>
            body {{
              margin: 0;
              min-height: 100vh;
              display: grid;
              place-items: center;
              background: radial-gradient(circle at top, rgba(79,156,255,.18), transparent 30%), #0f172a;
              color: #e5eefc;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            .box {{
              max-width: 520px;
              text-align: center;
              padding: 32px;
              border-radius: 24px;
              background: rgba(15, 23, 42, 0.92);
              border: 1px solid rgba(148, 163, 184, 0.18);
            }}
            h1 {{ margin: 0 0 8px; font-size: 26px; }}
            p {{ margin: 0; color: #9fb0cb; line-height: 1.6; }}
          </style>
        </head>
        <body>
          <div class="box">
            <h1>{title}</h1>
            <p>{message}</p>
          </div>
        </body>
        </html>
        """


def create_app(graph_app: GraphApp) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template_string(INDEX_HTML)

    @app.get("/api/state")
    def api_state() -> Any:
        return jsonify({"message": graph_app.message, "state": graph_app.get_state()})

    @app.post("/api/graph/reset")
    def api_graph_reset() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.reset_graph(payload.get("name", ""), bool(payload.get("directed", False)))
        return jsonify({"message": graph_app.message, "result": result, "state": graph_app.get_state()})

    @app.post("/api/vertex/add")
    def api_vertex_add() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.add_vertex(payload.get("vertex", ""))
        return jsonify({"message": graph_app.message, "result": result, "state": graph_app.get_state()})

    @app.post("/api/vertex/remove")
    def api_vertex_remove() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.remove_vertex(payload.get("vertex", ""))
        return jsonify({"message": graph_app.message, "result": result, "state": graph_app.get_state()})

    @app.post("/api/edge/add")
    def api_edge_add() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.add_edge(
            payload.get("edge_id", ""),
            payload.get("v", ""),
            payload.get("w", ""),
            payload.get("value", 0),
        )
        return jsonify({"message": graph_app.message, "result": result, "state": graph_app.get_state()})

    @app.post("/api/edge/remove")
    def api_edge_remove() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.remove_edge(payload.get("edge_id", ""))
        return jsonify({"message": graph_app.message, "result": result, "state": graph_app.get_state()})

    @app.post("/api/query/adjacent")
    def api_query_adjacent() -> Any:
        payload = request.get_json(silent=True) or {}
        result = graph_app.query_adjacent(payload.get("v", ""), payload.get("w", ""))
        return jsonify({"message": graph_app.message, "result": result})

    @app.get("/api/query/edge/<edge_id>/value")
    def api_query_edge_value(edge_id: str) -> Any:
        result = graph_app.query_edge_value(edge_id)
        return jsonify({"message": graph_app.message, "result": result})

    @app.get("/api/query/edge/<edge_id>/extremities")
    def api_query_edge_extremities(edge_id: str) -> Any:
        result = graph_app.query_edge_extremities(edge_id)
        return jsonify({"message": graph_app.message, "result": result})

    @app.get("/graph/frame")
    def graph_frame() -> str:
        view = request.args.get("view", "graph")
        return graph_app.render_graph_html(view)

    return app


def _pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, attempts: int = 60) -> None:
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("Não foi possível iniciar o servidor local da interface.")


def main() -> None:
    if webview is None:
        raise RuntimeError(
            "A dependência 'pywebview' não está instalada. Rode `uv sync` antes de abrir a aplicação."
        )

    graph_app = GraphApp()
    flask_app = create_app(graph_app)
    port = _pick_port()
    url = f"http://127.0.0.1:{port}"

    server = threading.Thread(
        target=flask_app.run,
        kwargs={"host": "127.0.0.1", "port": port, "debug": False, "use_reloader": False},
        daemon=True,
    )
    server.start()
    _wait_for_server(url)

    webview.create_window("Grafos", url, width=1500, height=980, min_size=(1100, 760))
    webview.start(gui=None, debug=False)


if __name__ == "__main__":
    main()
