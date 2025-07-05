import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import codigo as cod 


st.set_page_config(layout="wide")

st.title('Análisis de la red de colaboraciones de la FCEyN')


@st.cache_data
def cargarYProcesar(ruta_archivo):
    listaCoautorias = cod.cargarDatos(ruta_archivo)
    g, weighted = cod.crear_grafo(listaCoautorias)
    return g,  weighted

@st.cache_data
def calcular_comunidades_aprox(_graph, _centrality, k):
    communities_generator = cod.girvan_newman_aprox(_graph, _centrality)
    for _ in range(k - 1):
        communities = next(communities_generator)
    return communities

@st.cache_data
def centralidadAprox(_graph, k_samples):
    return cod.betweennessAprox(_graph, k_samples)


g,  weighted = cargarYProcesar('articles.csv')
gMax, numComp, tamComp = cod.conectividad(g)     

st.sidebar.header("Métricas Generales")
st.sidebar.metric("Total de Autores", g.number_of_nodes())
st.sidebar.metric("Colaboraciones Únicas", g.number_of_edges())
st.sidebar.metric("Componentes Conexas", numComp)
st.sidebar.metric("Tamaño Componente Gigante", tamComp)
st.sidebar.header("Métricas de la Componente Gigante")

diametro = nx.diameter(gMax)
clusterCoeff = nx.average_clustering(gMax)

st.sidebar.metric("Diámetro", diametro) 
st.sidebar.metric("Coeficiente de Clustering", f"{clusterCoeff:.2f}") #los hardcodee porque tarda mucho en calcularlos y no tiene sentido para debuggear.


k = st.slider("Precisión de Centralidad (k muestras)", 25, 500, step = 25)
centralidadAproxDict = centralidadAprox(gMax, k)
nodosOrdenadosCentralidad = sorted(centralidadAproxDict.items(), key=lambda x: x[1], reverse=True)




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
col1, col2 = st.columns(2)

with col1:
    st.subheader("Nodos más Centrales")
    dfCentralidad = pd.DataFrame(nodosOrdenadosCentralidad, columns=['Autor', 'Centralidad Aprox.'])
    st.dataframe(dfCentralidad.head(10))
    
    st.subheader("Puentes en la Red")
    puentes = list(nx.bridges(gMax))
    if puentes:
        st.write(f"Se encontraron {len(puentes)} puentes.")
        st.write(puentes)
    else:
        st.write("No se encontraron puentes en el componente gigante.")
with col2:
    st.subheader("El neo Erdös")
    neoErdos = cod.neoErdos(gMax, centralidadAproxDict)
    st.write(f"El autor más central es: **{neoErdos}**.")
    distancias = nx.shortest_path_length(gMax, source=neoErdos)
    df_distancias = pd.DataFrame(distancias.items(), columns=['Autor', 'Distancia a ' + neoErdos])
    st.dataframe(df_distancias.sort_values(by='Distancia a ' + neoErdos).head(20))

#with tab3:
#    st.header("Detección de Comunidades (Aproximación de Girvan-Newman)")
#    st.write("Este algoritmo utiliza el estimador de centralidad de nodos para encontrar comunidades de forma eficiente.")
#    
#    k = st.slider("Selecciona el número de comunidades a generar:", 2, 5, 10, 20)
#    if st.button("Detectar Comunidades"):
#        with st.spinner("Ejecutando algoritmo de comunidades aproximado..."):
#            comunidadesMostrar = calcular_comunidades_aprox(gMax, tuple(centralidadAproxDict.items()), k)
#            fig_comm = cod.visualize_communities(gMax, comunidadesMostrar)
#            st.pyplot(fig_comm)






