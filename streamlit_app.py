import streamlit as st
import codigo as cod 
import pandas as pd
import dill as pickle
import networkx as nx
import os
import matplotlib.pyplot as plt
import itertools
import html

st.set_page_config(layout="wide")

st.title('Análisis de la red de colaboraciones de la FCEyN')
cache_dir = '.cache'
os.makedirs(cache_dir, exist_ok=True) 

biografias = {
        "Gros, E.G.": {
            "imagen_url": "images/gros_transparency.png",
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
            "imagen_url": "images/estrin_transp.png",
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
            "imagen_url": "images/pietrasanta_transparency.png",
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
df_raw = pd.read_csv('articles.csv', sep=';', usecols=['Título', 'Autor', 'Filiación']).drop_duplicates('Título')

@st.cache_data
def cargarYProcesar(ruta_archivo):
    g_pkl = os.path.join(cache_dir, 'multigrafo_completo.pkl') #grafo_completo
    connect_pkl = os.path.join(cache_dir, 'multiconectividad.pkl') #conectivad
    w_pkl = os.path.join(cache_dir, 'weighted_Graph_completo.pkl') #grafo_completo

    if os.path.exists(g_pkl) and os.path.exists(connect_pkl):
        g = pickle.load(open(g_pkl, 'rb'))
        wMax, numComp, tamComp = pickle.load(open(connect_pkl, 'rb'))

    else:
        colaboraciones, atributos_autores = cod.cargar_datos(ruta_archivo)
        g, w = cod.crear_grafo(colaboraciones, atributos_autores)
        pickle.dump(g, open(g_pkl, 'wb'))
        pickle.dump(w, open(w_pkl, 'wb'))
        pickle.dump(cod.conectividad(w), open(connect_pkl, 'wb'))
        wMax, numComp, tamComp = pickle.load(open(connect_pkl, 'rb'))

    return g, wMax, numComp, tamComp

@st.cache_data
def calcular_comunidades_aprox(_graph, _centrality, k):
    communities_generator = cod.girvan_newman_aprox(_graph, _centrality)
    for _ in range(k - 1):
        communities = next(communities_generator)
    return communities

@st.cache_data
def centralidadAprox(_graph, k_samples):
    return cod.betweennessAprox(_graph, k_samples)

def distribucionDeDistancias(_graph):
    graph_pkl = os.path.join(cache_dir, 'distancesGraph.pkl')
    if not os.path.exists(graph_pkl):
        pickle.dump(cod.visualize_path_distribution(_graph), open(graph_pkl, 'wb'))
    return pickle.load(open(graph_pkl, 'rb'))

def calcular_ego_network(_gMax, autor_principal, distancias):
    ego_pkl = os.path.join(cache_dir, 'ego_network.pkl')
    if not os.path.exists(ego_pkl):
        pickle.dump(cod.visualize_ego_network_handdrawn(_gMax, autor_principal, distancias), open(ego_pkl, 'wb'))
    return pickle.load(open(ego_pkl, 'rb'))

def calcular_centralidad_aprox(_graph):
    central_pkl = os.path.join(cache_dir, 'centrality_cache.pkl')

    if os.path.exists(central_pkl):
        centrality_dict = pickle.load(open(central_pkl, 'rb'))

    else:
        centrality_dict = {}
        for k in range(100, 1001, 100):
            centrality_dict[k] = nx.betweenness_centrality(_graph, k, seed=42)
        pickle.dump(centrality_dict, open(central_pkl, 'wb'))
        
    return centrality_dict


gMax, g, numComp, tamComp  = cargarYProcesar('articles.csv')

st.sidebar.header("Métricas Generales")
st.sidebar.metric("Total de Autores", gMax.number_of_nodes())
st.sidebar.metric("Colaboraciones", gMax.number_of_edges())
st.sidebar.metric("Componentes Conexas", numComp)
st.sidebar.metric("Tamaño Componente Gigante", tamComp)
st.sidebar.header("Métricas de la Componente Gigante")

#diametro = nx.diameter(gMax)
#clusterCoeff = nx.average_clustering(gMax)

st.sidebar.metric("Diámetro", 17) 
st.sidebar.metric("Coeficiente de Clustering", 0.81) #los hardcodee porque tarda mucho en calcularlos y no tiene sentido para debuggear.

tab1, tab2, tab3 = st.tabs(["Análisis de Colaboración (Aristas)", "Análisis de Centralidad (Nodos)", "Análisis de Comunidades"])

all_centralities = calcular_centralidad_aprox(g)

with tab1:
    st.header("Análisis de Colaboración por Tipo de Arista")
    
    #st.write("Este análisis clasifica cada colaboración (arista) para entender cómo interactúa el DC con otros departamentos.")
    #
    #col1, col2 = st.columns(2)
    #with col1:
    #    st.subheader("Distribución de Tipos de Colaboración")
    #    df_tipos = cod.analizar_tipos_de_arista(gMax)
    #    st.dataframe(df_tipos)
    #    st.bar_chart(df_tipos)
    #with col2:
    #    st.subheader("Fuerza Promedio del Lazo por Tipo")
    #    df_fuerza = cod.analizar_fuerza_por_tipo(weighted.subgraph(gMax.nodes()))
    #    st.dataframe(df_fuerza)
    #    st.bar_chart(df_fuerza)
    #
    #st.divider()
    #st.subheader("Embajadores del DC")
    #st.write("Autores del DC con el mayor número de colaboraciones interdepartamentales, actuando como puentes.")
    #df_embajadores = cod.encontrar_embajadores_dc(gMax)
    #st.dataframe(df_embajadores)   

with tab2:

    k_seleccionado = st.slider("Precisión de Centralidad (k muestras)", min_value=100, max_value=1000, value=500, step=100)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Autores más Centrales")
        centralidad_aprox = all_centralities[k_seleccionado]
        nodosOrdenadosCentralidad = sorted(centralidad_aprox.items(), key=lambda x: x[1], reverse=True)

        dfCentralidad = pd.DataFrame(centralidad_aprox.items(), columns=['Autor', 'Centralidad'])
        dfCentralidad_sorted = dfCentralidad.sort_values(by='Centralidad', ascending=False).reset_index(drop=True)

        autor_principal = nodosOrdenadosCentralidad[0][0]
        st.dataframe(dfCentralidad_sorted)
    bio = biografias.get(autor_principal)
    with col2:
        #suele quedar un poquito de lugar abajo de los autores, 
        #capaz poner los papers más citados de c/uno? de google scholar se pude sacar ya sea manual o con un script. 
        st.subheader(f"Biografía de {autor_principal}")
        image_data_url = cod.image_to_base64(bio["imagen_url"] )
        st.markdown(f"""
            <div style="overflow: auto;">
                <img src="{image_data_url}" alt="biography picture"
                     style="
                        float: left;
                        width: 180px;
                        shape-outside: url('{image_data_url}');
                        shape-margin: 10px;
                        border-radius: 10px;
                        margin-right: 200px;
                     ">                
                <p style="text-align: justify; font-size: 0.9em; color: #31333f;">
                    {html.escape(bio["texto"].replace('\n', ' '))}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
    distancias = nx.shortest_path_length(g, source=autor_principal)
    df_distancias = pd.DataFrame(distancias.items(), columns=['Autor', 'Distancia a ' + autor_principal])
    autor_origen = st.text_input("Autor de Origen:", value="Feuerstein, E.")
    autor_destino = st.text_input("Autor de Destino:", value=autor_principal)
    if st.button("Trazar Camino"):
        if autor_origen and autor_destino:
            with st.spinner("Buscando el camino de colaboración..."):
                path_data = cod.get_path_info(gMax, g, autor_origen, autor_destino)
                if "error" in path_data:
                    st.error(path_data["error"])
                else:
                    st.success("Camino encontrado:")
                    path_list = path_data["path"]
                    for i, step in enumerate(path_list):
                        st.markdown(f"**Paso {i+1}:**")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{step['from']}** colabora con **{step['to']}**")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*En el paper: {step['paper']}*")
        else:
            st.warning("Por favor, ingrese un autor de origen y uno de destino.") 
    fig_overlap = cod.visualize_tie_strength_vs_overlap(gMax, g)
    st.subheader("Relación entre Fuerza de Lazo y Estructura de Red")

    st.pyplot(fig_overlap)


with tab3:
    st.header("Análisis Estructural de la Red")
    #st.header("Detección de Comunidades (Girvan-Newman Aproximado)")
    #k_comunidades_slider = st.slider("Selecciona el número de comunidades a visualizar:", 2, 20, 5)
    #@st.fragment
    #def mostrar_comunidades(k_comunidades, k_aprox):
    #    def most_valuable_edge_aprox(G):
    #        edge_betweenness = nx.edge_betweenness_centrality(G, k=k_aprox, seed=42)
    #        return max(edge_betweenness, key=edge_betweenness.get) if edge_betweenness else None
    #    
    #    st.write(f"Calculando partición para **{k_comunidades}** comunidades...")
    #    communities_generator = nx.community.girvan_newman(gMax, most_valuable_edge=most_valuable_edge_aprox)
    #    partition = next(itertools.islice(communities_generator, k_comunidades - 2, k_comunidades -1))
    #    fig_comm = cod.visualize_communities(gMax, partition)
    #    st.pyplot(fig_comm)
    #mostrar_comunidades(k_comunidades_slider, k_seleccionado)
    fig = distribucionDeDistancias(gMax)
    st.pyplot(fig, clear_figure=True)






