# Sistema de Grafos - T2: DSATUR e A*

## O que foi implementado?

### ✅ Algoritmos
1. **DSATUR** - Coloração de grafo com número mínimo de cores
2. **A*** - Caminho mínimo com distância de Manhattan como heurística

### ✅ Funcionalidades
- Carregamento automático do mapa do Paraná (12 cidades, 33 conexões)
- Cálculo de distância de Manhattan entre cidades
- Interface web interativa
- Visualização gráfica dos resultados

---

## Como Usar

### 1. Instalar dependências
```bash
pip install flask pyvis pywebview
```

### 2. Testar os algoritmos
```bash
python test_algorithms.py
```

### 3. Executar a interface web
```bash
python main.py
```

A aplicação abrirá em `http://127.0.0.1:<PORT>` automaticamente.

---

## Estrutura do Código

```
src/
├── graph.py           # Classe Graph com DSATUR e A*
├── cities_data.py     # Dados das cidades do Paraná
├── ui.py              # Interface web (Flask + PyVis)
└── __init__.py

test_algorithms.py     # Script de demonstração
EXPLICACAO_ALGORITMOS.md  # Documentação detalhada
```

---

## APIs Disponíveis

### Carregar mapa do Paraná
```
POST /api/graph/load_cities
Retorna: grafo com 12 cidades pré-carregadas
```

### Executar DSATUR
```
POST /api/algorithm/dsatur
Retorna: 
  {
    "coloring": {vertex: color},
    "num_colors": número_de_cores,
    "vertices_by_color": {color: [vértices]}
  }
```

### Executar A*
```
POST /api/algorithm/astar
Body: {"source": "Cascavel", "target": "Curitiba"}
Retorna:
  {
    "path": [lista de cidades],
    "distance": distância_total,
    "path_edges": [(v1, v2), ...]
  }
```

---

## Exemplos de Uso

### Python direto
```python
from src.graph import Graph
from src.cities_data import PARANA_CITIES, PARANA_CONNECTIONS

# Carregar grafo
g = Graph(directed=False, name="Paraná")
for city, coords in PARANA_CITIES.items():
    g.add_vertex_with_coords(city, coords[0], coords[1])

for city1, city2, distance in PARANA_CONNECTIONS:
    g.add_edge(f"{city1}-{city2}", city1, city2, distance)

# Executar DSATUR
coloring = g.dsatur_coloring()
print(f"Cores usadas: {max(coloring.values()) + 1}")

# Executar A*
path, distance = g.a_star("Cascavel", "Curitiba")
print(f"Caminho: {' → '.join(path)}")
print(f"Distância: {distance:.2f}")
```

### HTTP (via interface)
1. Clique em "Carregar Paraná" para pré-carregar as cidades
2. Clique em "DSATUR" para colorir o grafo
3. Selecione origem/destino e clique em "A*" para encontrar caminho

---

## Resultados Esperados

### DSATUR
- Grafo com 12 cidades colorido com ~3-4 cores
- Cada cor representa um grupo de vértices não adjacentes

### A* (exemplos)
```
Cascavel → Curitiba:  Cascavel → São Mateus → Curitiba (351 km)
Toledo → Maringá:     Toledo → Umuarama → Maringá (343 km)
Londrina → Paranaguá: Londrina → Toledo → ... → Paranaguá (705 km)
```

---

## Modificações Feitas

### `src/graph.py`
- Adicionado atributo `_coordinates` para armazenar (x, y) dos vértices
- Método `add_vertex_with_coords(vertex_id, x, y)`
- Método `manhattan_distance(v1, v2)`
- Método `dsatur_coloring()` - algoritmo completo
- Método `a_star(source, target)` - algoritmo completo com heapq

### `src/ui.py`
- Método `load_parana_cities()` - carrega dados pré-definidos
- Método `run_dsatur_coloring()` - executa e retorna coloração
- Método `run_a_star(source, target)` - executa e retorna caminho
- Endpoints POST: `/api/graph/load_cities`, `/api/algorithm/dsatur`, `/api/algorithm/astar`

### Novos arquivos
- `src/cities_data.py` - Coordenadas e conexões das cidades
- `test_algorithms.py` - Script de teste e demonstração
- `EXPLICACAO_ALGORITMOS.md` - Documentação técnica dos algoritmos

---

## Performance

Para o grafo do Paraná (12 cidades, 33 arestas):
- **DSATUR**: < 1ms
- **A***: < 5ms
- **Visualização**: ~100ms (renderização do grafo)

---

## Limitações

1. Coordenadas são aproximadas (não usa lat/lon reais)
2. DSATUR não garante solução ótima (é guloso), mas é eficiente
3. A* requer que vértices tenham coordenadas definidas
4. Distância de Manhattan é uma heurística (Euclidiana seria mais precisa)

---

## Como expandir

Para adicionar mais cidades:
```python
# Em cities_data.py
PARANA_CITIES.update({
    "Nova Cidade": (x, y),
})

PARANA_CONNECTIONS.extend([
    ("Nova Cidade", "Cascavel", 100),
    ("Nova Cidade", "Toledo", 150),
])
```

Para usar diferentes heurísticas em A*:
- Modificar `a_star()` para usar `self.euclidean_distance()` em vez de `self.manhattan_distance()`

---

## Referências

- **DSATUR**: Brélaz, D. (1979). "New methods to color the vertices of a graph"
- **A***: Hart, P., Nilsson, N., Raphael, B. (1968). "A Formal Basis for the Heuristic Determination of Minimum Cost Paths"

---

**Desenvolvido para:** Universidade Univali - Ciência da Computação  
**Disciplina:** Grafos - T2  
**Professor:** Fernanda Cunha  
**Data:** Maio de 2026
