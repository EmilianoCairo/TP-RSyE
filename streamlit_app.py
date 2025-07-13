import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import codigo as cod 
import dill as pickle
import os
import itertools

st.set_page_config(layout="wide")

st.title('Análisis de la red de colaboraciones de la FCEyN')


@st.cache_data
def cargarYProcesar(ruta_archivo):
    if os.path.exists('/.cache/grafo.pkl') and os.path.exists('/.cache/conectividad.pkl'):
        g = pickle.load(open('/.cache/grafo.pkl', 'rb'))
        gMax, numComp, tamComp = pickle.load(open('/.cache/conectividad.pkl', 'rb'))

    else:
        listaCoautorias = cod.cargarDatos(ruta_archivo)
        g, _ = cod.crear_grafo(listaCoautorias)
        pickle.dump(g, open('/.cache/grafo.pkl', 'wb'))
        pickle.dump(cod.conectividad(g), open('/.cache/conectividad.pkl', 'wb'))
        gMax, numComp, tamComp = pickle.load(open('/.cache/conectividad.pkl', 'rb'))


    return gMax, numComp, tamComp

@st.cache_data
def calcular_comunidades_aprox(_graph, _centrality, k):
    communities_generator = cod.girvan_newman_aprox(_graph, _centrality)
    for _ in range(k - 1):
        communities = next(communities_generator)
    return communities

@st.cache_data
def centralidadAprox(_graph, k_samples):
    return cod.betweennessAprox(_graph, k_samples)


gMax, numComp, tamComp  = cargarYProcesar('articles.csv')

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
    if os.path.exists('/.cache/centrality_cache.pkl'):
        centrality_dict = pickle.load(open('/.cache/centrality_cache.pkl', 'rb'))

    else:
        centrality_dict = {}
        for k in range(100, 1001, 100):
            centrality_dict[k] = nx.betweenness_centrality(_graph, k, seed=42)
        pickle.dump(centrality_dict, open('/.cache/centrality_cache.pkl', 'wb'))
        
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
        bio = cod.getBiography().get(autor_principal)
        st.markdown(f"![{autor_principal}]({bio["imagen_url"]})")            
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






