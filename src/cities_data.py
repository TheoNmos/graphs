"""Dados das cidades do Paraná com coordenadas aproximadas."""

# Coordenadas aproximadas (em unidades relativas para distância de Manhattan)
PARANA_CITIES = {
    "Cascavel": (-24.955, -53.455),
    "Toledo": (-24.728, -53.741),
    "Foz do Iguaçu": (-25.518, -54.588),
    "Francisco Beltrão": (-26.096, -53.062),
    "São Mateus do Sul": (-25.866, -50.580),
    "Londrina": (-23.304, -51.169),
    "Curitiba": (-25.428, -49.273),
    "Ponta Grossa": (-25.094, -50.162),
    "Guarapuava": (-25.386, -51.462),
    "Paranaguá": (-25.516, -48.523),
    "Maringá": (-23.424, -51.938),
    "Umuarama": (-23.757, -53.319),
}

# Conexões entre cidades (distâncias reais do mapa)
# Formato: (cidade1, cidade2, distância)
PARANA_CONNECTIONS = [
    ("Cascavel", "Toledo", 50),
    ("Cascavel", "Foz do Iguaçu", 143),
    ("Cascavel", "Francisco Beltrão", 186),
    ("Cascavel", "Guarapuava", 250),
    ("Toledo", "Umuarama", 126),
    ("Foz do Iguaçu", "Cascavel", 143),
    ("Francisco Beltrão", "São Mateus do Sul", 354),
    ("São Mateus do Sul", "Curitiba", 157),
    ("Paranaguá", "Curitiba", 90),
    ("Guarapuava", "Ponta Grossa", 165),
    ("Londrina", "Maringá", 114),
    ("Londrina", "Ponta Grossa", 273),
    ("Ponta Grossa", "Curitiba", 114),
    ("Ponta Grossa", "Guarapuava", 165),
    ("Ponta Grossa", "Maringá", 314),
    ("Maringá", "Umuarama", 190),
    ("Umuarama", "Maringá", 190),
]
