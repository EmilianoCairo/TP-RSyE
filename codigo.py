import networkx as nx
import pandas as pd
import itertools 
import numpy as np
from collections import Counter
from matplotlib.ticker import LogLocator, NullLocator
from matplotlib import font_manager, pyplot as plt
import random
import base64

font_path = 'static/InstrumentSerif-Regular.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Instrument Serif'

def apply_plot_style(ax, fig):
    ax.set_facecolor('#faf9f5')
    fig.set_facecolor('#faf9f5')
    ax.spines['left'].set_color('#cc7c5e')
    ax.spines['bottom'].set_color('#cc7c5e')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', color='#cc7c5e')

def image_to_base64(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

def es_afiliacion_dc(filiacion_texto): #esto funciona muy mal.
    if not isinstance(filiacion_texto, str):
        return False
    texto = filiacion_texto.lower()

    keywords_dc = ('computación', 'computation', 'computer', 'comp', 'computacion', 'computation', 'computacin')
    keywords_institucion = ('exactas y naturales', 'fcen', 'fceyn', 'buenos aires', 'uba', 'universidad de buenos aires', 'facultad de ciencias exactas y naturales')

    dc = any(keyword in texto for keyword in keywords_dc)
    institucion = any(keyword in texto for keyword in keywords_institucion)

    return dc and institucion

def cargar_datos(ruta_archivo):
    df = pd.read_csv(ruta_archivo, sep=';', usecols=['Título', 'Autor', 'Filiación']).drop_duplicates('Título')
    df['is_dc'] = df['Filiación'].apply(es_afiliacion_dc)

    autores_dc = set(
        df[df['is_dc']]
        .dropna(subset=['Autor'])['Autor']
        .str.split(';')
        .explode()
        .str.strip()
    )

    colaboraciones = []
    todos_los_autores = set()
    
    for row in df.itertuples(index=False):
        if pd.isna(row.Autor):
            continue
            
        autores_raw = [autor.strip() for autor in row.Autor.split(';')]
        autores = [autor for autor in autores_raw if autor.lower() != 'et al.']
        
        todos_los_autores.update(autores)
        
        if len(autores) > 1:
            for autor1, autor2 in itertools.combinations(autores, 2):
                colaboraciones.append((autor1, autor2, {'title': getattr(row, 'Título', 'Sin Título')}))

    atributos_autores = {autor: {'dc_collaborator': autor in autores_dc} for autor in todos_los_autores}

    return colaboraciones, atributos_autores

def crear_grafo(colaboraciones, atributos):
    g = nx.MultiGraph()
    g.add_edges_from(colaboraciones)
    nx.set_node_attributes(g, atributos)
    
    w = nx.Graph()
    for u, v, data in g.edges(data=True):
        if w.has_edge(u, v):
            w[u][v]['weight'] += 1
        else:
            w.add_edge(u, v, weight=1)
    
    nx.set_node_attributes(w, atributos)

    return g, w

def conectividad(G):
    if not nx.is_connected(G):
        componentes = list(nx.connected_components(G))
        max_comp = max(componentes, key=len)
        g_max = G.subgraph(max_comp).copy()
        return g_max, len(componentes), len(max_comp)
    return G, 1, G.number_of_nodes()

def get_path_info(full_multigraph, simple_graph, start_author, end_author): 
    #esto se puede hacer mejor.
    #podría ser un grafo? con los ejes con los titulos y los nodos con los autores??
    if start_author not in simple_graph:
        return {"error": f"El autor '{start_author}' no se encuentra en la red."}
    if end_author not in simple_graph:
        return {"error": f"El autor '{end_author}' no se encuentra en la red."}

    try:
        path = nx.shortest_path(simple_graph, source=start_author, target=end_author)
    except nx.NetworkXNoPath:
        return {"error": f"No existe un camino de colaboración entre {start_author} y {end_author}."}

    path_info = []
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        
        paper_title = "Colaboración sin título específico"
        if full_multigraph.has_edge(u, v):
            paper_title = full_multigraph.get_edge_data(u, v)[0].get('title', 'Sin Título')

        path_info.append({
            "from": u,
            "to": v,
            "paper": paper_title
        })

    return {"path": path_info}

def visualize_tie_strength_vs_overlap(graph_simple, graph_weighted, num_bins=30):
    #esto hay que revisar
    edge_data = []
    for u, v in graph_simple.edges():
        edge_attrs = graph_weighted.get_edge_data(u, v, default={'weight': 1})
        strength = edge_attrs.get('weight', 1)
        
        neighbors_u = set(graph_simple.neighbors(u))
        neighbors_v = set(graph_simple.neighbors(v))
        intersection_size = len(neighbors_u.intersection(neighbors_v))
        union_size = len(neighbors_u.union(neighbors_v))
        
        if union_size == 0:
            overlap = 0
        else:
            overlap = intersection_size / union_size
            
        edge_data.append({'strength': strength, 'overlap': overlap})

    df = pd.DataFrame(edge_data)
    df_sorted = df.sort_values(by='strength').reset_index(drop=True)
    df_sorted['percentile'] = (df_sorted.index + 1) / len(df_sorted)
    df_sorted['bin'] = pd.cut(df_sorted['percentile'], bins=num_bins, labels=False)
    binned_data = df_sorted.groupby('bin').agg(
        avg_percentile=('percentile', 'mean'),
        avg_overlap=('overlap', 'mean')
    ).dropna()

    fig, ax = plt.subplots(figsize=(10, 6))
    apply_plot_style(ax, fig)

    ax.plot(binned_data['avg_percentile'], binned_data['avg_overlap'], marker='o', linestyle='-', color='#cc7c5e')
    
    ax.set_xlabel("$P_{cum}$")
    ax.set_ylabel("$<O>_w$")
    ax.set_xlim(0, 1)
    ax.set_ylim(bottom=0)

    return fig

def visualize_path_distribution(graph, samples=1000):
    plt.close('all')
    all_path_lengths = []
    
    node_list = list(graph.nodes())
    nodes_to_sample = random.sample(node_list, min(samples, len(node_list)))

    for source_node in nodes_to_sample:
        path_lengths = nx.single_source_shortest_path_length(graph, source_node)
        all_path_lengths.extend(path_lengths.values())

    path_counts = Counter(length for length in all_path_lengths if length > 0)

    total_paths = sum(path_counts.values())
    lengths = sorted(path_counts.keys())
    probabilities = [path_counts[length] / total_paths for length in lengths]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    apply_plot_style(ax, fig)

    ax.plot(lengths, probabilities, marker='o', linestyle='-', color='#cc7c5e')
    ax.set_yscale('log')
    
    ax.set_xlabel("Longitud del camino", color='#000000')
    ax.set_ylabel("Probabilidad", color='#000000')
    ax.yaxis.set_major_locator(LogLocator(base=10.0))
    ax.yaxis.set_minor_locator(NullLocator())

    return fig
"""
esto fue una idea pero no la use al final. todo esto termino en el visualizador de caminos entre autores
def visualize_ego_network_handdrawn(graph, central_author, distances):

    nodes_by_distance = {}
    for node, dist in distances.items():
        if dist not in nodes_by_distance:
            nodes_by_distance[dist] = []
        nodes_by_distance[dist].append(node)

    nodes_to_plot = {central_author}
    
    target_distance = 3
    if target_distance in nodes_by_distance and len(nodes_by_distance[target_distance]) > 0:
        endpoints = random.sample(nodes_by_distance[target_distance], 10)
        for endpoint in endpoints:
            try:
                path = nx.shortest_path(graph, source=central_author, target=endpoint)
                nodes_to_plot.update(path)
            except nx.NetworkXNoPath:
                continue

    subgraph = graph.subgraph(nodes_to_plot)

    # Create figure and axes
    fig = plt.figure(facecolor='#faf9f5')
    
    ax = fig.add_subplot(1, 1, 1)

    ax.set_facecolor('#faf9f5') 
    
    pos = nx.nx_agraph.graphviz_layout(subgraph, prog='neato', args='-Gsplines=true -Goverlap=scale')

    nx.draw_networkx(
        subgraph,
        pos=pos,
        ax=ax,
        with_labels=True,
        font_size=4,
        node_shape="s",
        node_color="none",
        edge_color = '#ccc6ba',
        bbox=dict(facecolor='#faf9f5' ,edgecolor = '#faf9f5',boxstyle="round,pad=0.1")
    )
    nx.draw_networkx(
            subgraph.subgraph([central_author]),
            pos=pos,
            ax=ax,
            with_labels=True,
            node_shape="s",
            font_size=6,
            node_color="none",
            bbox=dict(facecolor='#cc7c5e',edgecolor = '#cc7c5e', boxstyle="round,pad=0.2")
    )
  
    ax.axis('equal')
    ax.axis('off')
    
    fig.tight_layout()

    return fig
"""