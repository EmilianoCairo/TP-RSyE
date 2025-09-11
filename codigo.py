import networkx as nx
import pandas as pd
import itertools 
from collections import Counter, defaultdict
from matplotlib.ticker import LogLocator, NullLocator, PercentFormatter
from matplotlib import font_manager, pyplot as plt
import random
import base64
from typing import List
from pyvis.network import Network
import math
import pickle
import os

cache_dir = '.cache'
font_path = 'static/InstrumentSerif-Regular.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Instrument Serif'

def smooth(scalars: list[float], weight: float) -> List[float]: 
    last = scalars[0]  
    smoothed = list()
    for point in scalars:
        smoothed_val = last * weight + (1 - weight) * point 
        smoothed.append(smoothed_val)                        
        last = smoothed_val                                  
        
    return smoothed


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
    df = pd.read_csv(ruta_archivo, sep=';', usecols=['Título', 'Autor', 'Filiación', 'Año']).drop_duplicates('Título')
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
                colaboraciones.append((autor1, autor2, {'title': getattr(row, 'Título', 'Sin Título'), 'year': getattr(row, 'Año', None)}))
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

def get_path_info(G_multi, simple_graph, start_author, end_author):
    try:
        path = nx.shortest_path(simple_graph, source=start_author, target=end_author)
    except (nx.NodeNotFound, nx.NetworkXNoPath) as e:
        return {"error": str(e)}
    
    path_info = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        
        all_titles = []
        if G_multi.has_edge(u, v):
            edge_data_dict = G_multi.get_edge_data(u, v)
            if edge_data_dict:
                all_titles = [d.get('title', 'Sin Título') for d in edge_data_dict.values()]
        
        path_info.append({"from": u, "to": v, "papers": all_titles})
        
    return {"path": path_info}

# def get_path_info(G, simple_graph, start_author, end_author):
#     if start_author not in simple_graph:
#         return {"error": f"El autor '{start_author}' no se encuentra en la red."}
#     if end_author not in simple_graph:
#         return {"error": f"El autor '{end_author}' no se encuentra en la red."}
#     try:
#         path = nx.shortest_path(simple_graph, source=start_author, target=end_author)
#     except nx.NetworkXNoPath:
#         return {"error": f"No existe un camino de colaboración entre {start_author} y {end_author}."}
#     path_info = []
#     for i in range(len(path) - 1):
#         u, v = path[i], path[i+1]
#         paper_title = "Colaboración sin título específico"
#         if G.has_edge(u, v):
#             paper_title = G.get_edge_data(u, v)[0].get('title', 'Sin Título')
#         path_info.append({"from": u, "to": v, "paper": paper_title})
#     return {"path": path_info}

def analizar_cierre_focal(G, window_size=5):
    all_years = [d['year'] for u, v, d in G.edges(data=True) if 'year' in d]
    min_year, max_year = min(all_years), max(all_years)

    triad_counts = defaultdict(lambda: {'open': 0, 'closed': 0})

    for year_t in range(int(min_year), int(max_year) - window_size + 1):
        year_t_plus_window = year_t + window_size

        edges_at_t = [e for e in G.edges(data=True) if e[2].get('year') <= year_t]
        graph_at_t = nx.Graph(edges_at_t)
        
        if not graph_at_t.nodes():
            continue

        edges_at_t_plus_window = [e for e in G.edges(data=True) if e[2].get('year') <= year_t_plus_window]
        graph_at_t_plus_window = nx.Graph(edges_at_t_plus_window)

        for node in graph_at_t.nodes():
            neighbors = list(graph_at_t.neighbors(node))
            if len(neighbors) >= 2:
                for b, c in itertools.combinations(neighbors, 2):
                    if not graph_at_t.has_edge(b, c):
                        k = len(list(nx.common_neighbors(graph_at_t, b, c)))
                        
                        triad_counts[k]['open'] += 1
                        if graph_at_t_plus_window.has_edge(b, c):
                            triad_counts[k]['closed'] += 1
    
    results = []
    for k, counts in sorted(triad_counts.items()):
        if counts['open'] > 0:
            probability = counts['closed'] / counts['open']
            results.append({'common_neighbours': k, 'probability': probability, 'open_triads': counts['open']})
            
    return pd.DataFrame(results, columns=['common_neighbours', 'probability', 'open_triads'])

def visualize_triadic_closure_prob(df_results):
    max_k = df_results[df_results['probability'] > 0]['common_neighbours'].max()
    plot_df = df_results[df_results['common_neighbours'] <= max_k]

    fig, ax = plt.subplots(figsize=(10, 6))
    apply_plot_style(ax, fig)

    ax.set_xlabel("Coautores en Común")
    ax.set_ylabel("Probabilidad de Cierre Triádico")
    
    ax.plot(plot_df['common_neighbours'], plot_df['probability'], color='#cc7c5e', linestyle='-', marker='.')
    
    ax.set_xlim(0, right= max_k + 1)
    ax.set_xticks(range(int(max_k) + 1))

    smoothed_probs = smooth(plot_df['probability'].tolist(), 0.8)
    
    ax.plot(plot_df['common_neighbours'], smoothed_probs, color='#B8B2A8', linestyle='--')

    return fig

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

def get_papers_between_authors(G_multi, author1, author2):
    papers = []
    if G_multi.has_edge(author1, author2):
        edge_data_dict = G_multi.get_edge_data(author1, author2)
        for key, data in edge_data_dict.items():
            papers.append({
                'Título': data.get('title', 'Sin Título'),
                'Año': data.get('year', 'N/A')
            })
    return papers

def visualize_coauthor_repetition(weighted_graph):
    author_data = []
    for node in weighted_graph.nodes():
        unique_coauthors = 0
        repeated_coauthor = 0
        for neighbor in weighted_graph.neighbors(node):
            if weighted_graph[node][neighbor].get('weight', 1) > 1:
                repeated_coauthor += 1
            unique_coauthors += 1
        
        if unique_coauthors > 0:
            author_data.append({
                'unique': unique_coauthors,
                'repeated': repeated_coauthor + 1
            })
    
    df = pd.DataFrame(author_data)
    
    avg_df = df.groupby('unique')['repeated'].mean().reset_index()
    smoothed_repeated = smooth(avg_df['repeated'].tolist(), 0.9)

    fig, ax = plt.subplots(figsize=(10, 8))
    apply_plot_style(ax, fig)
    
    ax.plot(avg_df['unique'], smoothed_repeated, color='#cc7c5e', marker='none', linestyle='-')
    #ax.plot(avg_df['unique'], color='#cc7c5e', marker='.', linestyle='none')
    #ax.plot([0, 1], [0, 1], transform=ax.transAxes, color = 'grey', linestyle ='--')
    ax.yaxis.set_major_formatter(PercentFormatter())


    
    ax.set_xlabel("Cantidad de coautores")
    ax.set_ylabel("Promedio de coautores repetidos")
    
    return fig

def compute_and_cache_layout(G, W, community_partition, cache_file='graph_layout.pkl'):

    node_positions = {}
    node_colors = {}
    community_nodes = defaultdict(list)
    
    for i, community in enumerate(community_partition):
        for node in community:
            community_nodes[i].append(node)
    
    grid_size = math.ceil(math.sqrt(len(community_nodes)))
    
    spacing, radius =  67000, 20000  
  
  
    
    community_colors = [
        '#cc7c5e', '#7195C2', '#CBCADA', '#7C8B62', '#B86B85',
        '#C0D0CA', '#A67C5D', '#8B8FA6', '#9BA78E',
    ]
    
    # Compute positions and colors
    for community_id, nodes in community_nodes.items():
        for node_idx, node in enumerate(nodes):
            angle = (2 * math.pi * node_idx) / len(nodes) + random.uniform(-0.3, 0.3)
            actual_radius = radius * random.uniform(0.1, 1.4)
            
            local_x = actual_radius * math.cos(angle)
            local_y = actual_radius * math.sin(angle)
            
            offset_x = random.uniform(-200, 200)
            offset_y = random.uniform(-200, 200)
            
            row = community_id // grid_size
            col = community_id % grid_size
            base_x = (col - grid_size/2) * spacing
            base_y = (row - grid_size/2) * spacing
            
            node_positions[node] = {
                'x': base_x + local_x + offset_x,
                'y': base_y + local_y + offset_y
            }
            node_colors[node] = community_colors[community_id % len(community_colors)]
    
    # Cache the computed layout
    layout_data = {
        'positions': node_positions,
        'colors': node_colors
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(layout_data, f)
    
    return layout_data

def create_interactive_graph(G, W, centrality_map, community_partition=None, highlight_node=None):

    cache_file = 'graph_layout.pkl'
    pkl_file = os.path.join(cache_dir, cache_file)

    if not os.path.exists(pkl_file) or community_partition is None:
        layout_data = compute_and_cache_layout(G, W, community_partition, cache_file)
    else:
        with open(pkl_file, 'rb') as f:
            layout_data = pickle.load(f)
    
    net = Network(height='800px', width='100%', bgcolor='#faf9f5', 
                 font_color='#333333', notebook=False)
    
    for node in W.nodes():
        if node in layout_data['positions']:
            pos = layout_data['positions'][node]
            color = layout_data['colors'][node]
            size = 150
            border_width = 10 if node == highlight_node else 1
            
            net.add_node(
                n_id=node,
                label=node,
                x=pos['x'],
                y=pos['y'],
                physics=False,
                size=size,
                value=centrality_map.get(node, 0),
                color=color,
                borderWidth=border_width,
                font={
                    "size": 12, 
                    "color": "#000000",
                    "face": "arial",
                    "strokeWidth": 0,
                    "align": "center"
                },
                shape="box"
            )
    
    for u, v in W.edges():
        weight = W[u][v].get('weight', 1)
        net.add_edge(
            u, v, 
            value=weight,
            title=f"Colaboraciones: {weight}"
        )
    
    net.set_options("""
    const options = {
        "physics": {"enabled": false},
        "nodes": {
            "shape": "box",
            "margin": 10,
            "font": {
                "size": 300,
                "color": "#000000",
                "face": "Instrument Serif",
                "align": "center",
                "strokeWidth": 0
            },
            "scaling": {"min": 150, "max": 550}
        },
        "edges": {
            "smooth": false,
            "color": {
                "inherit": false,
                "color": "#E1DACD", 
                "highlight": "#cc7c5e"
            },
            "width": 1.0,
            "hoverWidth": 250.0,
            "selectionWidth": 250.0,
            "opacity": 0.5
        },
        "interaction": {
            "hover": false,
            "tooltipDelay": 200,
            "hoverConnectedEdges": false,
            "selectConnectedEdges": true,
            "hideEdgesOnDrag": false,
            "hideEdgesOnZoom": true,
            "multiselect": true
        }
    }
    """)
    
    file_name = "interactive_graph.html"
    net.write_html(file_name)    
    return file_name


