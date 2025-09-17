import streamlit as st
import codigo as cod 
import pandas as pd
import dill as pickle
import networkx as nx
import os
import html
import streamlit.components.v1 as components


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

@st.cache_resource
def load_all_graphs():

    g_pkl = os.path.join(cache_dir, 'multigrafo_completo.pkl')
    w_pkl = os.path.join(cache_dir, 'weighted_Graph_completo.pkl')

    if os.path.exists(g_pkl) and os.path.exists(w_pkl):
        g = pickle.load(open(g_pkl, 'rb'))
        w = pickle.load(open(w_pkl, 'rb'))
    else:
        # Si los archivos no existen, los crea desde el CSV
        colaboraciones, atributos = cod.cargar_datos('articles.csv')
        g, w = cod.crear_grafo(colaboraciones, atributos)
        pickle.dump(g, open(g_pkl, 'wb'))
        pickle.dump(w, open(w_pkl, 'wb'))
        
    return g, w



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

def add_highlight_js(html_content, highlight_node):
    if not highlight_node:
        return html_content

    highlight_script = f"""
        // --- Injected Javascript for Highlighting and Zooming ---
        var highlightId = '{html.escape(highlight_node, quote=True)}';
        if (network.body.nodes[highlightId]) {{
          network.selectNodes([highlightId]);
          network.body.data.nodes.update([{{
            id: highlightId, 
            color: {{
                background: '#CCC6BA', 
                border: '#cc7c5e', 
                highlight: {{
                    background: '#CCC6BA', 
                    border: '#cc7c5e'}}}}}}]);
          var nodePosition = network.getPositions([highlightId])[highlightId];
          network.moveTo({{
            position: nodePosition,
            scale: 0.15, 
            animation: {{
              duration: 1000,
              easingFunction: "easeInOutQuad"
            }}
          }});
        }}
    """
    
    injection_point = "network = new vis.Network(container, data, options);"
    
    final_html = html_content.replace(
        injection_point,
        injection_point + highlight_script
    )
    
    return final_html

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

def calcular_y_visualizar_repeticion(w):
    repeat_pkl = os.path.join(cache_dir, 'repeated_coauthors.pkl')

    if not os.path.exists(repeat_pkl):
        pickle.dump(cod.visualize_coauthor_repetition(w), open(repeat_pkl, 'wb'))
    return pickle.load(open(repeat_pkl), 'rb')

def make_bg_transparent(html_content):
    head_end = html_content.find("</head>")
    if head_end == -1:
        return html_content # Fallback if no head tag is found
    
    style_injection = """
    <style>
      html, body {
        background-color: transparent !important;
        padding: 0;
        margin: -1px;
        overflow: hidden;
      }
      #mynetwork {
        border: none;
        margin: -1px;
        padding: 0;
      }
    </style>
    """
    
    return html_content[:head_end] + style_injection + html_content[head_end:]

g_multi, g_weighted = load_all_graphs()
g_giant, numComp2, tamComp2 = cod.conectividad(g_weighted)



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
st.sidebar.metric("Coeficiente de Clustering", 0.81) 
#los hardcodee porque tarda mucho en calcularlos y no tiene sentido para debuggear. 

st.write(""" 
         Este trabajo presenta un análisis de la red de colaboraciones científicas de la Facultad de Ciencias Exactas y Naturales (FCEyN).
         Utilizando los metadatos de publicaciones de la biblioteca digital de la universidad, 
         se construyó y analizó un grafo de coautorías para caracterizar su estructura topológica y social.""")

tab1, tab2, tab3, tab4= st.tabs(["Análisis de Colaboración", "Análisis de Centralidad", "Análisis de Comunidades", "Conclusiones y Trabajo Futuro"])

all_centralities = calcular_centralidad_aprox(g)
all_centralities2 = calcular_centralidad_aprox(g_giant)


@st.cache_data
def get_interactive_graph_html(_graph_simple, _graph_weighted, _centrality, _partition, highlight_node=None):
    cache_key = f"graph_html_{len(_graph_simple.nodes())}_{highlight_node}"
    html_cache_file = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    if os.path.exists(html_cache_file):
        with open(html_cache_file, 'rb') as f:
            return pickle.load(f)
    
    file_name = cod.create_interactive_graph(_graph_simple, _graph_weighted, _centrality, _partition, highlight_node)
    with open(file_name, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Cache the HTML content
    with open(html_cache_file, 'wb') as f:
        pickle.dump(html_content, f)
    
    return html_content

def search_author(search_term, nodes):
    if not search_term:
        return None
    
    exact_matches = [node for node in nodes if node.lower() == search_term.lower()]
    if exact_matches:
        return exact_matches[0]
    
    partial_matches = [node for node in nodes if search_term.lower() in node.lower()]
    if partial_matches:
        return partial_matches[0]
    
    return None

@st.fragment
def collaboration_tab():
    st.header("Visualización Interactiva de la Red")

    with st.expander("Cómo interactuar con el grafo"):
        st.markdown("""
        * **Zoom**: Usar la rueda del mouse para acercar o alejar.
        * **Mover**: Hacer clic en el fondo y arrastra para moverte por el grafo.
        * **Seleccionar**: Hacer clic en un autor para seleccionarlo. Sus conexiones directas se resaltarán.
        * **Multiselección**: Mantén presionada la tecla Crtl/Cmd y haz clic en varios autores para seleccionarlos.
        * **Información**: Pasa el mouse sobre un autor para ver su información de centralidad y grado.
        * **Highlight**: Usa el menú desplegable para seleccionar un autor y resaltarlo en el grafo.
        """)

    num_nodes_to_display = st.slider(
            "Número de autores a visualizar:", 
            min_value=100, max_value=len(g.nodes()), value=100, step=100
        )

    opciones = list(g.nodes())
    search_term = st.selectbox(
        "Seleccionar autor:",
        options=opciones, index=opciones.index("Feuerstein, E.") if "Feuerstein, E." in opciones else 0
    )

    centrality_for_viz = all_centralities2[1000]
    top_nodes = sorted(centrality_for_viz, key=centrality_for_viz.get, reverse=True)[:num_nodes_to_display]
    
    highlight_node = None
    if search_term:
        highlight_node = search_term
        if highlight_node not in top_nodes:
            top_nodes.append(highlight_node)
    
    g_visual = g_giant.subgraph(top_nodes)


    if 'last_node_count' not in st.session_state or st.session_state.last_node_count != num_nodes_to_display:
        
        num_nodes = g_visual.number_of_nodes()
        cache_file = os.path.join(cache_dir, f'base_html_{num_nodes}_nodes.pkl')

        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                base_html = pickle.load(f)
        else:
            communities = list(nx.community.greedy_modularity_communities(g_visual, cutoff=9, best_n=9))
            
            cod.compute_and_cache_layout(g_visual, g_visual, communities)
            file_name = cod.create_interactive_graph(g_visual, g_visual, centrality_for_viz, communities)
            with open(file_name, 'r', encoding='utf-8') as f:
                base_html = f.read()
            with open(cache_file, 'wb') as f:
                pickle.dump(base_html, f)

        st.session_state.current_base_html = base_html
        st.session_state.last_node_count = num_nodes_to_display
    
    base_graph_html = st.session_state.get('current_base_html', '<p>Por favor, seleccione un número de nodos para visualizar.</p>')

    transparent_html = make_bg_transparent(base_graph_html)
    
    final_graph_html = add_highlight_js(transparent_html, highlight_node)
    
    components.html(final_graph_html, height=810)

with tab1:
    collaboration_tab()

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
        st.dataframe(dfCentralidad_sorted, height = 240)
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
    #st.divider() 
    
    # @st.fragment
    # def path_finder_fragment():
    #     st.subheader("Encontrar Camino de Colaboración")
    #     opciones = list(g.nodes)
        
    #     autor_origen = st.selectbox("Autor de Origen:", options=opciones, index=opciones.index("Feuerstein, E."))
    #     autor_destino = st.selectbox("Autor de Destino:", options=opciones, index=opciones.index(autor_principal))

    #     if st.button("Trazar Camino"):
    #         if autor_origen and autor_destino:
    #             origen = search_author(autor_origen, g.nodes())
    #             destino = search_author(autor_destino, g.nodes())
                
    #             if origen and destino:
    #                 with st.spinner("Buscando el camino de colaboración..."):
    #                     path_data = cod.get_path_info(gMax, g, origen, destino)
    #                     if "error" in path_data:
    #                         st.error(path_data["error"])
    #                     else:
    #                         path_list = path_data["path"]
    #                         st.write("---") 
    #                         for i, step in enumerate(path_list):
    #                             st.markdown(f"**{i+1}:** **{step['from']}** colabora con **{step['to']}** en el paper: *{step['paper']}*")
    #             else:
    #                 st.error("Autor de origen o destino no encontrado en la red.")
    #         else:
    #             st.warning("Por favor, ingrese un autor de origen y uno de destino.")
    
    # path_finder_fragment()
    
    st.divider()
    @st.fragment
    def path_finder_fragment2():
        st.subheader("Encontrar Camino de Colaboración")
        opciones = list(g.nodes)
        
        autor_origen = st.selectbox("Autor de Origen:", options=opciones, index=opciones.index("Feuerstein, E."))
        autor_destino = st.selectbox("Autor de Destino:", options=opciones, index=opciones.index(autor_principal))
        if st.button("Trazar Camino"):
            if autor_origen and autor_destino:
                origen = search_author(autor_origen, g_giant.nodes())
                destino = search_author(autor_destino, g_giant.nodes())

                if origen and destino:
                    with st.spinner("Buscando el camino de colaboración..."):
                        path_data = cod.get_path_info(g_multi, g_giant, origen, destino)

                        if "error" in path_data:
                            st.error(path_data["error"])
                        else:
                            path_list = path_data["path"]
                            st.write("---")
                            for i, step in enumerate(path_list):
                                papers = step['papers']
                                md_string = f"**{i+1}:** **{step['from']}** colabora con **{step['to']}**"

                                if not papers:
                                    md_string += " (colaboración sin título específico)."
                                elif len(papers) == 1:
                                    md_string += f" en el paper: *{papers[0]}*."
                                else:
                                    md_string += f" en **{len(papers)} papers**:"
                                    for paper in papers:
                                        md_string += f"\n* *{paper}*"

                                st.markdown(md_string)
                else:
                    st.error("Autor de origen o destino no encontrado en la red.")
            else:
                st.warning("Por favor, ingrese un autor de origen y uno de destino.")

    path_finder_fragment2()
    st.divider() 
    fig_overlap = cod.visualize_tie_strength_vs_overlap(gMax, g)
    st.subheader("Relación entre la *tie strength* y la estructura de la red")
    with st.expander("Metodología y Resultados Esperados"):
        st.markdown("" \
        "Este análisis mide cómo la *tie strength* se relaciona con la estructura local de la red. " \
        "Primero, se calcula la *tie strength* para cada par de colaboradores como el número total de publicaciones conjuntas. " \
        "A la vez, se calcula el  *neighborhood overlap* para ese mismo lazo. " \
        "Finalmente, todas las colaboraciones (aristas) de la red se ordenan por su fuerza, se agrupan en percentiles, y se calcula el overlap promedio para cada percentil.  " \
        "\n La teoría de la fuerza de los lazos de Granovetter predice una correlación monótona positiva: " \
        "los lazos fuertes (colaboraciones frecuentes) deberían ocurrir dentro de grupos cohesivos y, por lo tanto, mostrar un alto overlap, mientras que los lazos débiles actúan como puentes entre grupos y deberían tener un overlap bajo")
    st.pyplot(fig_overlap)
    st.markdown("#### Resultados")
    st.write("En el gráfico, sobre la relación entre el número de coautorías (tie strength) y la superposición de vecinos, se observa un comportamiento errático con fluctuaciones significativas, destacando un pico pronunciado cerca del percentil 55, seguido de una caída abrupta. Esta discrepancia con la teoría, que sugiriá una correlación motonoma positiva, sugiere que la estructura de la colaboración académica posee particularidades no capturadas por el modelo simple. Una hipótesis es que los lazos muy fuertes en esta red no siempre corresponden a pares de investigadores en un grupo denso, sino que pueden representar la relación entre un investigador senior (o director de laboratorio) y sus múltiples colaboradores junior, quienes no necesariamente colaboran entre sí. Este tipo de estructura, centralizada en un nodo hub, generaría lazos de alta fortaleza pero con un overlap bajo, explicando así la desviación del comportamiento esperado. Adicionalmente, las inconsistencias en los datos de autores podrían introducir ruido que afecta esta medición.")

with tab3:
    st.subheader("Patrones de Colaboración por Autor")
    with st.expander("Metodología y Resultados Esperados"):
        st.markdown("" \
             "Para explorar los patrones de colaboración individuales, se analizó a cada autor de la red. " \
             "Para cada uno, se calcularon dos métricas: " \
             "1) su número total de coautores únicos (el grado) y " \
             "2) el porcentaje de esos coautores con los que ha colaborado más de una vez. " \
             "Los autores fueron agrupados por su número total de coautores para visualizar la tendencia. " \
             "Se espera observar una correlación positiva. " \
             "A medida que un investigador se vuelve más prolífico y su red de contactos crece, es razonable suponer que consolida relaciones de trabajo a largo plazo, lo que se traduciría en una mayor proporción de colaboraciones recurrentes en lugar de lazos esporádicos.")
    fig_repetition = cod.visualize_coauthor_repetition(g)
    st.pyplot(fig_repetition)
    st.markdown("#### Resultados")
    st.write("Este gráfico ilustra la relación entre la cantidad total de colaboradores que tiene un autor y el porcentaje de esos colaboradores con quienes ha trabajado más de una vez. La tendencia observada es una correlación positiva y fuerte: a medida que un investigador amplía su red y colabora con más personas, también aumenta la proporción de sus lazos recurrentes. Esto sugiere que los investigadores, a medida que se vuelven más prolíficos, desarrollan un núcleo estable de colaboradores frecuentes, mientras continúan estableciendo nuevas colaboraciones débiles en la periferia de su red. En otras palabras, los autores con pocas colaboraciones tienden a tener lazos esporádicos, pero aquellos con redes extensas han consolidado relaciones de trabajo a largo plazo, lo que indica la formación de grupos de investigación estables y productivos")
    st.divider()

    st.subheader("Distribución de distancias")
    with st.expander("Metodología y Resultados Esperados"):
        st.markdown("" \
            "Para caracterizar la conectividad global de la red, se midió la distribución de las distancias de los caminos más cortos entre los investigadores. " \
            "Dado el gran tamaño de la red, calcular la distancia entre todos los pares de nodos es computacionalmente inviable. " \
            "Por ello, se utilizó un método de muestreo: se seleccionó una muestra aleatoria de 1000 autores y se calculó la distancia desde cada uno de ellos a todos los demás nodos de la componente gigante usando BFS. " \
            "Los resultados de todas las búsquedas se agregaron para estimar la distribución de distancias global. " \
            "La teoría de redes sociales, en particular el fenómeno del mundo pequeño, predice que en redes de gran escala como esta, la distancia promedio será sorprendentemente corta, con una distribución de probabilidad que decae rápidamente después de un pico en un valor bajo")
    fig = distribucionDeDistancias(gMax)
    st.pyplot(fig, clear_figure=True)
    st.markdown("#### Resultados")
    st.write("" \
        " Este gráfico muestra que la distancia más probable entre dos investigadores cualesquiera de la facultad es de aproximadamente seis grados de separación." \
        "Este resultado es una clara evidencia de que la red de coautorías de la FCEyN exhibe la propiedad de mundo pequeño. " \
        "A pesar del gran tamaño de la institución, cualquier investigador está, en promedio, a solo unas pocas coautorías de cualquier otro. ")
    st.divider()
    st.subheader("Análisis de Cierre Triádico")
    with st.expander("Metodología y Resultados Esperados"):
        st.markdown("" \
        "Para analizar el cierre triádico, se implementó un método temporal que recorre la red a lo largo de los años. " \
        "Para cada período, se identifican las tríadas abiertas: conjuntos de tres autores (A, B, C) donde A colabora con B y con C, pero B y C aún no colaboran entre sí. "
        "Luego, se mide la probabilidad de que B y C formen un lazo (publiquen un trabajo juntos) en un período de tiempo posterior. " \
        "Este cálculo se agrupa según la cantidad de coautores que B y C ya tenían en común." \
        "\n Teóricamente, según el principio de cierre triádico, se esperaría una correlación positiva: cuanto mayor sea el número de coautores en común, más alta debería ser la probabilidad de que terminen colaborando, ya que su entorno social compartido genera más oportunidades y confianza para iniciar un nuevo trabajo.")
    
    years = sorted([d['year'] for u, v, d in gMax.edges(data=True) if d.get('year') is not None and pd.notna(d['year'])])
    min_year, max_year = int(years[0]), int(years[-1])
    start_year, end_year = st.slider(
        "Seleccione el rango de años para el análisis:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year + 1, max_year - 1)
    )
    if st.button("Calcular Probabilidad de Cierre"):
        resultado_df = cod.analizar_cierre_focal(gMax, 5)
        fig_cierre = cod.visualize_triadic_closure_prob(resultado_df)
        st.pyplot(fig_cierre)
    st.markdown("#### Resultados")
    st.write("" \
    "La observación contraintuitiva de que una mayor cantidad de coautores compartidos podría disminuir la probabilidad de una futura colaboración directa puede explicarse a través de dos hipótesis complementarias. " \
    "La primera, de naturaleza metodológica, apunta a la calidad y consistencia de los datos. " \
    "Inconsistencias en los nombres de los autores pueden fragmentar la identidad de un investigador en múltiples nodos, distorsionando así el cálculo de vecinos en común. " \
    "Ademas, es posible que haya artículos publicados no presentes en la base de datos. " \
    "Esto se observo en casos particulares con *papers* del ICC que aparecen en la pagina propia del Instituto, pero no en la biblioteca. " \
    "La segunda hipótesis, de carácter estructural, se fundamenta en la teoría de redes. Un investigador central puede actuar como un puente entre grupos de conocimiento distintos y no superpuestos. " \
    "En este escenario, el autor central está llenando un agujero estructural en la red, y la alta cantidad de vecinos en común no es un predictor de cierre triádico, sino un indicador de la diversidad de las conexiones del nodo central.")

with tab4:
    st.header("Conclusiones ")
    st.write("""
             Este análisis de la red de coautorías de la FCEyN ha permitido caracterizar la estructura social subyacente de la colaboración científica en la institución. 
             Los resultados confirman que la red exhibe propiedades claras de "mundo pequeño", 
             indicando un entorno altamente interconectado. 
             La corta distancia promedio entre investigadores demuestra que, a pesar del tamaño de la facultad, 
             la comunidad científica se encuentra sorprendentemente cerca a través de cadenas de colaboración.
             Es importante notar que la estructura de esta red académica desafía los modelos teóricos estándar; 
             las desviaciones encontradas en los análisis de *tie strength* y cierre triádico sugieren que la cohesión local no es el único motor de colaboración. 
             En su lugar, la organización jerárquica de los grupos de investigación parecería ser un factor a tener en cuenta. 
             Los investigadores senior a menudo actúan como *hubs*, generando conexiones con múltiples colaboradores junior que no necesariamente trabajan entre sí. 
             Este patrón, centrado en nodos clave, explicaría porque no siempre se correlaciona con una alta densidad en su entorno inmediato. 
             El análisis de centralidad fue exitoso en identificar a estos actores que funcionan como puentes, vitales para la transferencia de conocimiento entre distintas áreas.
             Es importante notar que hay organizaciones que forman parte de la red como autores cuando no lo son. Por ejemplo, IEEE Computer Society. 
             Esto se debe a inconsistencias en los datos originales y afecta algunas métricas, pero no obstante, las conclusiones generales se mantienen válidas.""")
    st.header("Trabajo Futuro")
    st.write("""
             Mirando hacia el futuro, la principal limitación de este estudio es la calidad de los datos. 
             Un paso importante sería implementar técnicas avanzadas de desambiguación de autores para mejorar la precisión de las métricas. 
             Además, un análisis dinámico completo permitiría modelar la evolución de las comunidades a lo largo del tiempo, 
             ofreciendo una visión más profunda de la formación y disolución de grupos de investigación. 
             Finalmente, la incorporación de redes de citaciones y el análisis de tópicos mediante procesamiento de lenguaje natural podrían mejorar el estudio, 
             creando un mapa que no solo muestre quién colabora con quién, sino también sobre qué temas y con qué impacto.)
             """)
