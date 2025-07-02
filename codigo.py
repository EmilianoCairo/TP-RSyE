import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import itertools 

def cargarDatos(ruta_archivo):
    df = pd.read_csv(ruta_archivo, sep=',').drop_duplicates('Título')
    coautorias = []
    
    for _, row in df.iterrows():
        if pd.isna(row['Autor']):
            continue
            
        autores = [autor.strip() for autor in row['Autor'].split(';')]
        
        if len(autores) > 1:
            pares_de_autores = itertools.combinations(autores, 2)
            coautorias.extend(list(pares_de_autores))
            
        # me acabo de dar cuenta que en el csv las filiaciones están sin separador porque en la pagina eran un newline y quedaron juntas
        filiaciones = [filiacion.strip() for filiacion in row['Filiación'].split(';')]
        
        #hay un par que tienen Computatión, habría que ver si hay más typos
        #habría que definir la pertenencia al dc porque filiaciones no es por autor, es en general del articulo. 
        #otra opción es la más facil  (if (departamento de computación in filiacines[autor]) then dc.add(autor) else continue) y decir que es uan deficiencia del dataset

    return coautorias

def crear_grafo(coautorias, atributos):
    g = nx.Graph()
    g.add_edges_from(coautorias)
    nx.set_node_attributes(g, atributos)

    weighted = nx.Graph()
    for autor1, autor2 in coautorias:
        if weighted.has_edge(autor1, autor2):
            weighted[autor1][autor2]['weight'] += 1
        else:
            weighted.add_edge(autor1, autor2, weight=1)
    nx.set_node_attributes(weighted, atributos)
    
    return g, weighted

#devuelve el grafo entero o la componente conexa más grande
def analizar_conectividad(G):
    if not nx.is_connected(G):
        componentes = list(nx.connected_components(G))
        maxComp = max(componentes, key=len)
        G = (G.subgraph(maxComp).copy())
    return G

def erdosDC(G):

    investigadoresDC = [n for n, attr in G.nodes(data=True) if attr.get('dpto') == 'DC']
    G_dc = G.subgraph(investigadoresDC).copy()
    centralidadDC = nx.betweenness_centrality(G_dc)
    erdos = max(centralidadDC, key=centralidadDC.get)
    return erdos

def betweenness(G):
    betweennessNodos = nx.betweenness_centrality(G)
    nodos = sorted(betweennessNodos.items(), key=lambda item: item[1], reverse=True)
    return nodos

def tieStrength(weighted):
    print("hay que hacerlo")

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

def visualize_communities(graph, communities, i):
    node_colors = create_community_node_colors(graph, communities)
    modularity = round(nx.community.modularity(graph, communities), 6)
    title = f"Community Visualization of {len(communities)} communities with modularity of {modularity}"
    pos = nx.spring_layout(graph, k=0.3, iterations=50, seed=2)
    plt.subplot(3, 1, i)
    plt.title(title)
    nx.draw(
        graph,
        pos=pos,
        node_size=1000,
        node_color=node_colors,
        with_labels=True,
        font_size=20,
        font_color="black",
    )

if __name__ == "__main__":

    listaCoautorias, afiliaciones = cargarDatos('articles.csv')
 
    g, weighted = crear_grafo(listaCoautorias, afiliaciones)
            
    maxComp = analizar_conectividad(g) #puede ser G entero

    distPromedio = nx.average_short_path_length(maxComp)
    diametro = nx.diameter(maxComp) 
    
    
    clusterCoeff = nx.average_clustering(G)
    puentes = list(nx.bridges((maxComp)))
    nodosOrdenadosCentralidad = betweenness(maxComp)
    tieStrength(weighted.subgraph(maxComp.nodes())) #no está hecho
    homofiliaDpto = nx.attribute_assortativity_coefficient(maxComp, 'dpto')
    #https://networkx.org/documentation/stable/auto_examples/algorithms/plot_girvan_newman.html
    communities = list(nx.community.girvan_newman(maxComp)) 
    modularity_df = pd.DataFrame(
    [
        [k + 1, nx.community.modularity(maxComp, communities[k])] 
        for k in range(len(communities))
    ],
    columns=["k", "modularity"],
    )
    fig, ax = plt.subplots(3, figsize=(15, 20)) #3 es la cantidad de filas)
    modularity_df.plot.bar(
        x="k",
        ax=ax[2],
        color="#F2D140",
        title="Modularity Trend for Girvan-Newman Community Detection",
    )
    #habría que ver que y cuantas comunidades visualizar
    


