import networkx as nx
import pandas as pd
import itertools 
import numpy as np
import matplotlib.pyplot as plt
import random


def getBiography():
 
    biografias = {
        "Gros, E.G.": {
            "imagen_url": "https://www.fundacionkonex.org/custom/web/data/imagenes/repositorio/2010/6/1/1261/2016031611120728e209b61a52482a0ae1cb9f5959c792.jpg",
            "texto": """
            Nació el 16/04/1931. Premio Konex de Platino 1983. Doctor en Química (Universidad de Buenos Aires). 
            Fue becario posdoctoral en la Universidad de Minnesota (EE.UU.) e Investigador Superior del CONICET (PK). 
            Entre 1967 y 1993, ocupó diversos cargos docentes y dirigió el Departamento de Química Orgánica en la Facultad de Ciencias Exactas, UBA. 
            En 1978 fundó la Unidad de Microanálisis y Métodos Físicos Aplicados a Química Orgánica (UMYMFOR), donde desarrolló servicios para empresas nacionales y extranjeras. 
            Presidió la Academia Nacional de Ciencias Exactas, Físicas y Naturales (1998-2002) e integró la Academia de Ciencias de América Latina. 
            Publicó más de 200 trabajos de investigación en revistas internacionales. Fue el Director del LANAIS-EMAR desde 1992. 
            Recibió, entre otros, el Premio de la Asociación Argentina de Biología Médica Nuclear en 1983. Falleció el 12/06/2001.
            """
        },
        "Estrin, D.A.":{
            "imagen_url": "https://www.fundacionkonex.org/custom/web/data/imagenes/repositorio/2013/4/30/3169/2016031612411001259a0cb2431834302abe2df60a1327.jpg",
            "texto": """
            Nació el 25/04/1962. Licenciado y Doctor en Ciencias Químicas (UBA 1986, UNLP 1989). 
            Profesor titular de la Facultad de Ciencias Exactas y Naturales de la UBA. Investigador Principal de CONICET. 
            Es coordinador del área Ciencias Químicas de la Agencia Nacional de Promoción Científica y Tecnológica. 
            Autor de más de 130 publicaciones en el área de simulación computacional de sistemas químicos.
            Dictó numerosas conferencias en foros nacionales e internacionales. Dirigió 12 tesis doctorales y varias de licenciatura. 
            Fue miembro asociado del International Center for Theoretical Physics entre 1998 y 2005. Fue becario Guggenheim en 2007. 
            Recibió el premio Ranwell Caputo de la Academia Nacional de Ciencias de Córdoba en 2001, y el premio Houssay de la Secretaría de Ciencia  y Técnica en 2003.
            """
        },
        "Pietrasanta, L.I.":{
            "imagen_url": "https://chanzuckerberg.com/wp-content/uploads/2021/11/LIA-PIETRASANTA3-Lia-Pietrasanta.jpg",
            "texto": """
            Doctora en Bioquímica por la Universidad Nacional del Sur (UNS). 
            Realizó sus estudios posdoctorales en Estados Unidos, Alemania y Argentina, donde instaló y formó un grupo de investigación en la Universidad de Buenos Aires. 
            Su investigación se centra en los aspectos biofísicos de la mecanotransducción celular. 
            Coordinadora del Centro de Microscopía Avanzada de la Facultad de Ciencias Exactas y Naturales de la Universidad de Buenos Aires (2002-presente). 
            Coordinadora del Sistema Nacional de Microscopía (SNM, 2011-presente). Presidenta (2017-2018) y expresidenta (2018-presente) de la Sociedad Argentina de Biofísica (SAB).
            Miembra de la Sociedad Argentina de Microscopía (SAMIC, 2008-presente). Miembra de la Sociedad Argentina de Bioquímica y Biología Molecular (SAIB, 2007-presente).
            Miembra del Consejo Científico del Centro Universitario Argentino-Alemán (CUAA-DAHZ, 2018-presente). Miembra del Comité Ejecutivo de Bioimagen Latinoamericana (LABI, 2021-presente).
            """
        }
    }
    return biografias


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

#
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




