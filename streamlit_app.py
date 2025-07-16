import streamlit as st
import codigo as cod 
import pandas as pd
import dill as pickle
import networkx as nx
import os
import html

st.set_page_config(layout="wide")

st.title('Análisis de la red de colaboraciones de la FCEyN')
cache_dir = '.cache'
images_dir = 'images'
os.makedirs(cache_dir, exist_ok=True) 
biografias = {
        "Gros, E.G.": {
            "imagen_url": os.path.join(images_dir, 'gros_transparency.png'),
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
            "imagen_url": os.path.join(images_dir, 'estrin_transp.png'),
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
            "imagen_url": os.path.join(images_dir, 'pietrasanta_transparency.png'),
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


gMax, g,numComp, tamComp  = cargarYProcesar('articles.csv')

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



@st.fragment
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


all_centralities = calcular_centralidad_aprox(gMax)


#with tab1:
#    st.header("Visualización del Componente Gigante")
#    st.write("Nodos azules representan autores del DC, nodos rojos representan autores de otros departamentos.")
#    
#    fig, ax = plt.subplots(figsize=(16, 12))
#    pos = nx.spring_layout(gMax, k=0.3, iterations=50, seed=42)
#    node_colors = ['#0077b6' if gMax.nodes[node].get('dpto') == 'DC' else '#d62828' for node in gMax.nodes()]
#    
#    nx.draw_networkx_nodes(gMax, pos, node_size=100, node_color=node_colors, alpha=0.9, ax=ax)
#    nx.draw_networkx_edges(gMax, pos, width=0.5, alpha=0.3, ax=ax)
#    
#    ax.set_title("Componente Gigante de la Red de Coautorías")
#    plt.axis('off')
#    st.pyplot(fig)


st.header("Análisis de Centralidad y Puentes")
k_seleccionado = st.slider("Precisión de Centralidad (k muestras)", min_value=100, max_value=1000, value=500, step=100)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Autores más Centrales")

    centralidad_aprox = all_centralities[k_seleccionado]
    nodosOrdenadosCentralidad = sorted(centralidad_aprox.items(), key=lambda x: x[1], reverse=True)

    dfCentralidad = pd.DataFrame(centralidad_aprox.items(), columns=['Autor', 'Centralidad Aprox.'])
    dfCentralidad_sorted = dfCentralidad.sort_values(by='Centralidad Aprox.', ascending=False).reset_index(drop=True)
    
    st.dataframe(dfCentralidad_sorted.head(10))
    

with col2:
    if nodosOrdenadosCentralidad:
        autor_principal = nodosOrdenadosCentralidad[0][0]
        bio = biografias.get(autor_principal)
        st.markdown(f"![{autor_principal}]")            
        st.markdown(bio["texto"])
#with tab3:
#    st.header("Detección de Comunidades (Aproximación de Girvan-Newman)")
#    st.write("Este algoritmo utiliza el estimador de centralidad de nodos para encontrar comunidades de forma eficiente.")
#    
#   
#
#
#    k = st.slider("Selecciona el número de comunidades a generar:", 2, 5, 10, 20)
#    if st.button("Detectar Comunidades"):
#        with st.spinner("Ejecutando algoritmo de comunidades aproximado..."):

#            comunidadesMostrar = calcular_comunidades_aprox(gMax, tuple(centralidadAproxDict.items()), k)
#            fig_comm = cod.visualize_communities(gMax, comunidadesMostrar)
#            st.pyplot(fig_comm)






