import networkx as nx
import pandas as pd
import itertools 

def cargarDatos(ruta_archivo):
    df = pd.read_csv(ruta_archivo, sep=';', usecols=['Título', 'Autor']).drop_duplicates('Título')
    coautorias = []
    
    for _, row in df.iterrows():
        if pd.isna(row['Autor']):
            continue
            
        autores = [autor.strip() for autor in row['Autor'].split(';')]
        
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

def neoErdos(G):
    return  max(betweenness(G))

def betweenness(G):
    betweennessNodos = nx.betweenness_centrality(G)
    nodos = sorted(betweennessNodos.items(), key=lambda item: item[1], reverse=True)
    return nodos

def tieStrength(weighted):
    print("hay que hacerlo")

def conectividad(G):
    if not nx.is_connected(G):
        componentes = list(nx.connected_components(G))
        maxComp = max(componentes, key=len)
        gMax = G.subgraph(maxComp).copy()
        return gMax, len(componentes), len(maxComp)
    return G, 1, G.number_of_nodes()

def create_community_node_colors(graph, communities):
    number_of_colors = len(communities)
    colors = ["#D4FCB1", "#CDC5FC", "#FFC2C4", "#F2D140", "#BCC6C8"][:number_of_colors]
    node_colors = []
    for node in graph:
        current_community_index = 0
        for community in communities:
            if node in community:
                node_colors.append(colors[current_community_index])
                break
            current_community_index += 1
    return node_colors

def visualize_communities(g, communities):
    modularity = round(nx.community.modularity(g, communities), 4)
    fig_comm, ax_comm = plt.subplots(figsize=(16, 12))
    
    node_colors = cod.create_community_node_colors(g, communities)
    pos = nx.spring_layout(g, k=0.3, iterations=50, seed=42)
    
    nx.draw(g, pos, node_size=200, node_color=node_colors, with_labels=False, width=0.5, ax=ax_comm)
    nx.draw_networkx_labels(g, pos, font_size=8, ax=ax_comm)
    return modularity, fig_comm




