import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import codigo as cod 
import itertools


st.set_page_config(layout="wide")

st.title('Análisis de la red de colaboraciones de la FCEyN')


@st.cache_datas
def cargarYProcesar(ruta_archivo):
    listaCoautorias, afiliaciones = cod.cargarDatos(ruta_archivo)
    g, weighted = cod.crear_grafo(listaCoautorias, afiliaciones)
    maxComp, num_comp, tam_comp = cod.analizar_conectividad(g)
    return g, maxComp, weighted, num_comp, tam_comp

g, maxComp, weighted, num_comp, tam_comp = cargarYProcesar('articulos.csv')

st.sidebar.header("Métricas Generales")
st.sidebar.metric("Total de Autores", g.number_of_nodes())
st.sidebar.metric("Colaboraciones Únicas", g.number_of_edges())
st.sidebar.metric("Componentes Conexas", num_comp)
st.sidebar.metric("Tamaño Componente Gigante", tam_comp)

st.sidebar.header("Métricas de la Componente Gigante")
distPromedio = nx.average_short_path_length(maxComp)
diametro = nx.diameter(maxComp)
clusterCoeff = nx.average_clustering(maxComp)

st.sidebar.metric("Distancia Promedio", f"{distPromedio:.2f}")
st.sidebar.metric("Diámetro", diametro)
st.sidebar.metric("Coeficiente de Clustering", f"{clusterCoeff:.2f}")

tab1, tab2, tab3 = st.tabs(["Visualización de la Red", "Análisis de Centralidad", "Análisis de Comunidades"])

with tab1:
    st.header("Visualización")
    #con filiacioens podriamos hacer que los nodos del dc tengan un colorcito distinto
    fig, ax = plt.subplots(figsize=(16, 12))
    pos = nx.spring_layout(maxComp, k=0.3, iterations=50)
    nx.draw_networkx_nodes(maxComp, pos, node_size=100 , alpha=0.9)
    nx.draw_networkx_edges(maxComp, pos, width=0.5, alpha=0.3)
        
    ax.set_title("Componente Gigante de la Red de Coautorías")
    plt.axis('off')
    st.pyplot(fig)
    
with tab2:
    st.header("Análisis de Centralidad y Puentes")
    col1, col2 = st.columns(2)
        
with col1:
    st.subheader("Nodos más Centrales (Betweenness)")
    nodosOrdenadosCentralidad = cod.betweenness(maxComp)
    dfCentralidad = pd.DataFrame(nodosOrdenadosCentralidad, columns=['Autor', 'Centralidad'])
    st.dataframe(dfCentralidad.head(10))
    st.subheader("Puentes en la Red") #me pareció interesante ver si había puentes. 
    puentes = list(nx.bridges(maxComp))
    if puentes:
            st.write(f"Se encontraron {len(puentes)} puentes.")
            st.write(puentes)
    else:
            st.write("No se encontraron puentes en el componente gigante.")

with col2:
    st.subheader("Número de Erdös del DC")
    erdos_dc, G_dc = cod.erdosDC(maxComp)
    st.write(f"El autor más central dentro del DC es: **{erdos_dc}**.")
    distancias = nx.shortest_path_length(G_dc, source=erdos_dc)
    df_distancias = pd.DataFrame(distancias.items(), columns=['Autor', 'Distancia a ' + erdos_dc])
    st.dataframe(df_distancias.sort_values(by='Distancia a ' + erdos_dc).head(20)) #20 es arbitrario, hay que ver si queda bien

    
with tab3:
    st.header("Detección de Comunidades (Girvan-Newman)")
    with st.spinner("Corriendo g-n (ojo que tarda bastante)"):
            k = 12 #habría que ver cuantas tomar bien. elegí 12 porque es la cantidad de dptos
            comms = nx.community.girvan_newman(maxComp)
            primerasK = itertools.takewhile(lambda c: len(c) <= k, comms)

    fig, mod = cod.visualize_communities(primerasK)
    st.write(f"Visualizando la partición en **{len(primerasK)}** comunidades. Modularidad: **{mod}**")
    st.pyplot(fig)
     
        
            


