import networkx as nx
import pandas as pd
import itertools 
import numpy as np
import matplotlib.pyplot as plt
import random


def cargarDatos(ruta_archivo):
    df = pd.read_csv(ruta_archivo, sep=';', usecols=['Título', 'Autor']).drop_duplicates('Título')
    coautorias = []
    
    for _, row in df.iterrows():
        if pd.isna(row['Autor']):
            continue
            
        autores = [autor.strip() for autor in row['Autor'].split(';')]
        if 'et al.' in autores: autores.remove('et al.') 
        if len(autores) > 1:
            pares_de_autores = itertools.combinations(autores, 2)
            coautorias.extend(list(pares_de_autores))

    return coautorias

def crear_grafo(coautorias):
    g = nx.Graph()
    g.add_edges_from(coautorias)

    weighted = nx.Graph()
    for autor1, autor2 in coautorias:
        if weighted.has_edge(autor1, autor2):
            weighted[autor1][autor2]['weight'] += 1
        else:
            weighted.add_edge(autor1, autor2, weight=1)
    
    return g, weighted


def conectividad(G):
    if not nx.is_connected(G):
        componentes = list(nx.connected_components(G))
        maxComp = max(componentes, key=len)
        gMax = G.subgraph(maxComp).copy()
        return gMax, len(componentes), len(maxComp)
    return G, 1, G.number_of_nodes()

def neoErdos(G, centralidad_nodos):
    return max(centralidad_nodos, key=centralidad_nodos.get)

def betweennessAprox(G, k_samples):
    centrality = nx.betweenness_centrality(G, k=k_samples, seed=42)
    return centrality

def estimate_edge_betweenness(G, node_betweenness):
    edge_bw = {}
    for u, v in G.edges():
        edge_bw[(u, v)] = node_betweenness.get(u, 0) * node_betweenness.get(v, 0)
    return edge_bw

def girvan_newman_aprox(G, node_betweenness):
    gCopy = G.copy()
    
    for _ in range(gCopy.number_of_edges()):
        edge_bw = estimate_edge_betweenness(gCopy, node_betweenness)
        if not edge_bw: break # No quedan aristas
        
        edge_to_remove = max(edge_bw, key=edge_bw.get)
        gCopy.remove_edge(*edge_to_remove)
        
        yield tuple(c for c in nx.connected_components(gCopy))

def create_community_node_colors(graph, communities):
    number_of_colors = len(communities)
    colors = ["#D4FCB1", "#CDC5FC", "#FFC2C4", "#F2D140", "#BCC6C8", "#F4A261", "#2A9D8F", "#E9C46A", "#E76F51", "#264653"]
    colors = (colors * (number_of_colors // len(colors) + 1))[:number_of_colors]
    node_colors = {}
    for i, community in enumerate(communities):
        for node in community:
            node_colors[node] = colors[i]
    return [node_colors.get(node, "#808080") for node in graph.nodes()]

def visualize_communities(graph, communities):
    modularity = round(nx.community.modularity(graph, communities), 4)
    fig, ax = plt.subplots(figsize=(16, 12))
    
    node_colors = create_community_node_colors(graph, communities)
    pos = nx.spring_layout(graph, k=0.3, iterations=50, seed=42)
    
    nx.draw(graph, pos, node_size=200, node_color=node_colors, with_labels=False, width=0.5, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=8, ax=ax)
    ax.set_title(f"Visualización con {len(communities)} comunidades (Modularidad: {modularity})")
    
    return fig




