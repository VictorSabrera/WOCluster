import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import distance_matrix
import plotly.express as px

# Función para convertir distancia en metros a acres
def distancia_a_acres(distancia):
    radio_metros = distancia / 2
    area_metros_cuadrados = np.pi * (radio_metros**2)
    area_acres = area_metros_cuadrados / 4046.86
    return area_acres

# Función para clasificar pozos según el espaciamiento en acres
def clasificar_espaciamiento(acres, x1, x2, x3, x4, x5):
    if acres <= x1:
        return f'menor a {x1} acres'
    elif x1 < acres <= x2:
        return f'{x1 + 0.01} a {x2} acres'
    elif x2 < acres <= x3:
        return f'{x2 + 0.01} a {x3} acres'
    elif x3 < acres <= x4:
        return f'{x3 + 0.01} a {x4} acres'
    else:
        return f'mayor a {x5} acres'

# Función para clasificar pozos según el volumen acumulado
def clasificar_volumen(cum, y1, y2, y3):
    if cum <= y1:
        return f'Cum <= {y1}'
    elif y1 < cum <= y2:
        return f'{y1 + 0.01} < Cum <= {y2}'
    else:
        return f'Cum > {y3}'

# Cargar el archivo CSV
st.image("OLYMPIC.jpeg", width=200)
st.title("Well Clustering for Workover Candidate Selection")

uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

# Si no se carga un archivo, usar el archivo predeterminado
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("dfvii.csv")

# Inputs para clasificación
st.sidebar.header("Parámetros de Clasificación Segun Acreaje")

# Clasificación por acreaje
x1 = st.sidebar.number_input("Menor que (acres)", min_value=0.0, value=4.0, step=0.1)

col1, col2 = st.sidebar.columns(2)
x2_1 = col1.number_input("Desde", min_value=x1, value=4.01, step=0.1)
x2_2 = col2.number_input("Hasta", min_value=x2_1, value=6.0, step=0.1)

col3, col4 = st.sidebar.columns(2)
x3_1 = col3.number_input("Desde", min_value=x2_2, value=6.01, step=0.1)
x3_2 = col4.number_input("Hasta", min_value=x3_1, value=8.0, step=0.1)

col5, col6 = st.sidebar.columns(2)
x4_1 = col5.number_input("Desde", min_value=x3_2, value=8.01, step=0.1)
x4_2 = col6.number_input("Hasta", min_value=x4_1, value=10.0, step=0.1)

x5 = st.sidebar.number_input("Mayor que (acres)", min_value=x4_2, value=10.01, step=0.1)

# Clasificación por volumen acumulado
st.sidebar.header("Parámetros de Clasificación por Volumen de Petróleo Acumulado (Np)")

y1 = st.sidebar.number_input("Npmenor que", min_value=0.0, value=10.0, step=0.1)

col7, col8 = st.sidebar.columns(2)
y2_1 = col7.number_input("Np desde", min_value=y1, value=10.01, step=0.1)
y2_2 = col8.number_input("Np hasta", min_value=y2_1, value=20.0, step=0.1)

y3 = st.sidebar.number_input("Np mayor que", min_value=y2_2, value=20.01, step=0.1)

# Filtrar por cada 'Zone Name' y calcular distancias euclidianas
zonas = df['Zone Name'].unique()
dataframes_zonas = {}

for zona in zonas:
    # Filtrar los datos por zona
    df_zona = df[df['Zone Name'] == zona].copy()
    
    # Calcular la matriz de distancias euclidianas
    coords = df_zona[['X', 'Y']].values
    dist_matrix = distance_matrix(coords, coords)
    
    # Crear un DataFrame de la matriz de distancias usando el índice del DataFrame
    dist_df = pd.DataFrame(dist_matrix, index=df_zona.index, columns=df_zona.index)
    
    # Reemplazar ceros (distancia a sí mismo) por inf para calcular la distancia mínima a otros pozos
    dist_df.replace(0, np.inf, inplace=True)
    
    # Calcular la distancia mínima a cualquier otro pozo
    df_zona['distancia_min'] = dist_df.min(axis=1)
    
    # Convertir la distancia mínima a acres
    df_zona['espaciamiento_acres'] = df_zona['distancia_min'].apply(distancia_a_acres)
    
    # Clasificar los pozos según el espaciamiento en acres
    df_zona['grupo_espaciamiento'] = df_zona['espaciamiento_acres'].apply(
        lambda x: clasificar_espaciamiento(x, x1, x2_2, x3_2, x4_2, x5)
    )
    
    # Clasificar los pozos según el volumen acumulado
    df_zona['grupo_volumen'] = df_zona['Cum'].apply(
        lambda x: clasificar_volumen(x, y1, y2_2, y3)
    )
    
    # Combinar ambos criterios en un solo grupo
    df_zona['grupo_combined'] = df_zona['grupo_espaciamiento'] + ' & ' + df_zona['grupo_volumen']
    
    # Almacenar el DataFrame filtrado por zona en un diccionario
    dataframes_zonas[zona] = df_zona

# Mostrar clusters por zona
zona_seleccionada = st.selectbox("Selecciona una Zona", zonas)
if zona_seleccionada:
    df_zona = dataframes_zonas[zona_seleccionada]
    
    fig = px.scatter(df_zona, x='X', y='Y', color='grupo_combined', title=f'Clusters de espaciamiento y volumen para {zona_seleccionada}')
    st.plotly_chart(fig)

    # Seleccionar cluster específico
    cluster_seleccionado = st.selectbox("Selecciona un Cluster", df_zona['grupo_combined'].unique())
    if cluster_seleccionado:
        df_filtrado = df_zona[df_zona['grupo_combined'] == cluster_seleccionado]
        st.write(df_filtrado)

# Exportar los resultados
if st.button("Exportar Resultados"):
    for zona, df_zona in dataframes_zonas.items():
        df_zona.to_csv(f'{zona}_clusters.csv', index=False)
    st.success("Resultados exportados exitosamente.")

