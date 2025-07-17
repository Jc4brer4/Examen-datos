from duckdb import df
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import pygwalker as pyg
import streamlit.components.v1 as components
from io import BytesIO
from unidecode import unidecode
import xlsxwriter

st.set_page_config(page_title="Dashboard Matriculados", layout="wide")

st.title("🎓 Dashboard Interactivo: Matrículas Educación Superior (2007 - 2024)")
st.markdown("""
Este dashboard permite explorar las matrículas en educación superior en Chile entre 2007 y 2024. 
Puedes filtrar por año, región, institución, carrera, área de conocimiento, y visualizar los datos de forma interactiva.
""")
# ----------------------------# CARGA DEL DATASET LOCAL
# ----------------------------
# Intentar leer dataset_Matriculas_2007_2024.csv con separador ;
try:
    df_historico = pd.read_csv("dataset_Matriculas_2007_2024.csv", sep=",", encoding="latin1")
except pd.errors.ParserError:
    df_historico = pd.read_csv("dataset_Matriculas_2007_2024.csv", sep=";", encoding="latin1", low_memory=False)

# Intentar leer Libro_CódigosADM2025_ArchivoMatricula.csv con separador ;

df_codigos = pd.read_csv("Libro_CódigosADM2025_ArchivoMatricula.csv", sep = ';', encoding = 'latin-1', low_memory = False, on_bad_lines = 'skip')

# Archivo principal normal
df_matriculas = pd.read_csv("ArchivoMatr_Adm2025.csv", sep = ';', encoding = 'utf-8-sig', low_memory = False, on_bad_lines = 'skip')

# ----------------------------  
# Limpieza de los DataFrames

df_historico_limpio = df_historico[['AÑO', 'MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA' ,'TOTAL MATRICULADOS','CLASIFICACIÓN INSTITUCIÓN NIVEL 1','CLASIFICACIÓN INSTITUCIÓN NIVEL 2' ,'CLASIFICACIÓN INSTITUCIÓN NIVEL 3' ,'NOMBRE CARRERA' , "NOMBRE INSTITUCIÓN", 'TOTAL MATRICULADOS PRIMER AÑO', 'MATRICULADOS MUJERES PRIMER AÑO', 'MATRICULADOS HOMBRES PRIMER AÑO' ,"ÁREA DEL CONOCIMIENTO", "CINE-F 1997 ÁREA", "CINE-F 1997 SUBAREA", "CINE-F 2013 ÁREA", "CINE-F 2013 SUBAREA",  "REGIÓN" ]].copy()
df_historico_limpio['MATRICULADOS MUJERES POR PROGRAMA'] = df_historico_limpio['MATRICULADOS MUJERES POR PROGRAMA'].fillna(0).astype(int)
df_historico_limpio['MATRICULADOS HOMBRES POR PROGRAMA'] = df_historico_limpio['MATRICULADOS HOMBRES POR PROGRAMA'].fillna(0).astype(int)

df_historico_limpio['TOTAL MATRICULADOS PRIMER AÑO'] = df_historico_limpio['TOTAL MATRICULADOS PRIMER AÑO'].fillna(0).astype(int)
df_historico_limpio['MATRICULADOS MUJERES PRIMER AÑO'] = df_historico_limpio['MATRICULADOS MUJERES PRIMER AÑO'].fillna(0).astype(int)
df_historico_limpio['MATRICULADOS HOMBRES PRIMER AÑO'] = df_historico_limpio['MATRICULADOS HOMBRES PRIMER AÑO'].fillna(0).astype(int)

df_historico_limpio['AÑO'] = df_historico_limpio['AÑO'].apply(str)
df_historico_limpio['AÑO'] = df_historico_limpio['AÑO'].str.split('_', expand=True)[1]
df_historico_limpio['AÑO'] = pd.to_datetime(df_historico_limpio['AÑO'], format='%Y').dt.year    

df_historico_limpio.fillna(0, inplace=True)



# Limpieza de los códigos
# Seleccionar las columnas relevantes y renombrarlas
df_codigos_limpio = df_codigos[["ï»¿CODIGO_CARRERA","NOMBRE_CARRERA","NOMBRE_UNIVERSIDAD","UNI_CODIGO"]].copy()
df_codigos_limpio = df_codigos_limpio.rename(columns={'ï»¿CODIGO_CARRERA': 'Codigo carrera'})
df_codigos_limpio = df_codigos_limpio.rename(columns={'NOMBRE_CARRERA': 'Carrera'})
df_codigos_limpio = df_codigos_limpio.rename(columns={'NOMBRE_UNIVERSIDAD': 'Universidad'})
df_codigos_limpio = df_codigos_limpio.rename(columns={'UNI_CODIGO': 'Codigo Universidad'})
df_codigos_limpio['Carrera'] = df_codigos_limpio['Carrera'].apply(unidecode)
def remove(text):
  if not isinstance(text, str):
    return text  # Return as is if not a string
  new_text = ""
  prev_char = ""
  for char in text:
    if char.lower() == 'a' and prev_char.lower() == 'a':
      continue
    new_text += char
    prev_char = char
  return new_text

df_codigos_limpio['Carrera'] = df_codigos_limpio['Carrera'].apply(remove)

df_matriculas_limpio = df_matriculas[["CODIGO","CODIGO_UNIV"]].copy()
df_matriculas_limpio = df_matriculas_limpio.rename(columns={'CODIGO': 'Codigo carrera'})
df_matriculas_limpio = df_matriculas_limpio.rename(columns={'CODIGO_UNIV': 'Codigo Universidad'})




df2025 = df_codigos_limpio.copy()
df2025 = df2025.merge(df_matriculas_limpio.groupby(['Codigo carrera', 'Codigo Universidad']).size().reset_index(name='Matriculados'),
                on=['Codigo carrera', 'Codigo Universidad'],
                how='left')
df2025['Matriculados'] = df2025['Matriculados'].fillna(0).astype(int)


# Filtros interactivos para el DataFrame df_historico_limpio
st.sidebar.title("Filtros de Análisis(hasta 2024)")

st.sidebar.header("Filtros del Panel")
with st.sidebar:
    # Selección de año(s)
    anios = sorted(df_historico_limpio['AÑO'].unique(), reverse=True)
    anio_sel = st.sidebar.selectbox("Selecciona año", anios)

    # Selección de región
    region_sel = st.sidebar.multiselect("Región", options=sorted(df_historico_limpio["REGIÓN"].dropna().unique()), default=None)

    

    area_conocimiento_sel = st.sidebar.multiselect("Área del Conocimiento", options=sorted(df_historico_limpio["ÁREA DEL CONOCIMIENTO"].dropna().unique()), default=None)

    # Filtro de selección para la carrera
    carreras = sorted(df_historico_limpio["NOMBRE CARRERA"].dropna().unique())
    carrera_sel = st.sidebar.multiselect("Carrera", options=carreras, default=None)

    # Selección de institución
    inst_sel = st.sidebar.multiselect("Institución", options=sorted(df_historico_limpio["NOMBRE INSTITUCIÓN"].dropna().unique()), default=None)

    # Filtro para seleccionar un rango de matriculados (usando slider)
    matriculados_range = st.sidebar.slider("Rango de Matrículas", min_value=int(df_historico_limpio["TOTAL MATRICULADOS"].min()), max_value=int(df_historico_limpio["TOTAL MATRICULADOS"].max()), value=(int(df_historico_limpio["TOTAL MATRICULADOS"].min()), int(df_historico_limpio["TOTAL MATRICULADOS"].max())))
    # Filtro checkbox para mostrar solo el primer año
    solo_primero = st.sidebar.checkbox("Solo Primer Año", value=False)
    # ---------------------------- FILTROS DE MUJERES Y HOMBRES ----------------------------
    # Filtro para mostrar solo mujeres matriculadas
    solo_mujeres = st.sidebar.checkbox("Solo Matriculadas Mujeres", value=False)

    # Filtro para mostrar solo hombres matriculados
    solo_hombres = st.sidebar.checkbox("Solo Matriculados Hombres", value=False)

     # ---------------------------- APLICAR FILTROS ----------------------------
    df_filtrado = df_historico_limpio[df_historico_limpio["AÑO"] == anio_sel]
    if region_sel:
        df_filtrado = df_filtrado[df_filtrado["REGIÓN"].isin(region_sel)]
    if inst_sel:
        df_filtrado = df_filtrado[df_filtrado["NOMBRE INSTITUCIÓN"].isin(inst_sel)]
    if carrera_sel:
        df_filtrado = df_filtrado[df_filtrado["NOMBRE CARRERA"].isin(carrera_sel)]
    if area_conocimiento_sel:
        df_filtrado = df_filtrado[df_filtrado["ÁREA DEL CONOCIMIENTO"].isin(area_conocimiento_sel)]
    if solo_primero and "TOTAL PRIMER AÑO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["TOTAL PRIMER AÑO"] > 0]
    df_filtrado = df_filtrado[df_filtrado["TOTAL MATRICULADOS"].between(matriculados_range[0], matriculados_range[1])]

    # Aplicar filtro de mujeres
    if solo_mujeres:
        df_filtrado = df_filtrado[df_filtrado["MATRICULADOS MUJERES POR PROGRAMA"] > 0]

    # Aplicar filtro de hombres
    if solo_hombres:
        df_filtrado = df_filtrado[df_filtrado["MATRICULADOS HOMBRES POR PROGRAMA"] > 0]




    # Filtros para df2025
    st.sidebar.header("Filtros para 2025")
    # Selección de institución
    inst_sel = st.sidebar.multiselect("Institución 2025", options=sorted(df2025["Universidad"].dropna().unique()), default=None)
    # Filtro de selección para la carrera
    carreras2025 = sorted(df2025["Carrera"].dropna().unique())
    carrera_sel25 = st.sidebar.multiselect("Carrera", options=carreras2025, default=None)

    # Filtro para seleccionar un rango de matriculados (usando slider)
    matriculados_range25 = st.sidebar.slider("Rango de Matrículas 2025", min_value=int(df2025["Matriculados"].min()), max_value=int(df2025["Matriculados"].max()), value=(int(df2025["Matriculados"].min()), int(df2025["Matriculados"].max())))
    #Aplicar filtros para df2025
    df2025_filtrado = df2025[df2025["Universidad"].isin(inst_sel)]
    if carrera_sel25:
        df2025_filtrado = df2025_filtrado[df2025_filtrado["Carrera"].isin(carrera_sel25)]
    df2025_filtrado = df2025_filtrado[df2025_filtrado["Matriculados"].between(matriculados_range25[0], matriculados_range25[1])]


# Descargar Excel
    def convertir_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()




#primera sección del dashboard
#graficos
primer_df = df_historico_limpio[['AÑO', 'MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA' ,'TOTAL MATRICULADOS', "CLASIFICACIÓN INSTITUCIÓN NIVEL 1",'CLASIFICACIÓN INSTITUCIÓN NIVEL 2' ,'CLASIFICACIÓN INSTITUCIÓN NIVEL 3', "NOMBRE CARRERA" ]].copy()
# Filtrar por el rango de años deseado
primer_df['AÑO'] = pd.to_numeric(primer_df['AÑO'])
df_filtrado = primer_df[(primer_df['AÑO'] >= 2017) & (primer_df['AÑO'] <= 2024)].copy()
# Agrupar por año y sumar el total de matriculados
df_agrupado_año = df_filtrado.groupby('AÑO')['TOTAL MATRICULADOS'].sum().reset_index()
# Ordenar por año para el gráfico
df_agrupado_año = df_agrupado_año.sort_values('AÑO')
# Graficar la evolución del total de matriculados por año

# Calcular la suma total de matriculados en df2025
total_matriculados_2025 = df2025['Matriculados'].sum().copy()
# Crear una nueva fila para df_agrupado_año
nueva_fila = pd.DataFrame({'AÑO': [2025], 'TOTAL MATRICULADOS': [total_matriculados_2025]})
# Concatenar la nueva fila al DataFrame df_agrupado_año
df_agrupado_año = pd.concat([df_agrupado_año, nueva_fila], ignore_index=True)

  # Agrupar por año y sumar el total de matriculados por género
df_genero_año = df_filtrado.groupby('AÑO')[['MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA']].sum().reset_index()
# Derretir el dataframe para facilitar la graficación con seaborn
df_genero_año = df_genero_año.melt(id_vars='AÑO', var_name='Género', value_name='Total Matriculados')
# Renombrar las columnas para mayor claridad
df_genero_año['Género'] = df_genero_año['Género'].replace({
    'MATRICULADOS MUJERES POR PROGRAMA': 'Mujeres',
    'MATRICULADOS HOMBRES POR PROGRAMA': 'Hombres'
})


primer_df['CLASIFICACIÓN INSTITUCIÓN NIVEL 1'] = primer_df['CLASIFICACIÓN INSTITUCIÓN NIVEL 1'].astype(str).str.strip()
# Agrupar por tipo de institución y sumar el total de matriculados
df_distribucion_institucion = primer_df.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 1')['TOTAL MATRICULADOS'].sum().reset_index()
# Ordenar para mejor visualización
df_distribucion_institucion = df_distribucion_institucion.sort_values('TOTAL MATRICULADOS', ascending=False)
#Distribución de matrículas por tipo de institución

df_distribucion_nivel1 = primer_df.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 1')['TOTAL MATRICULADOS'].sum().reset_index()
df_distribucion_nivel1 = df_distribucion_nivel1.sort_values('TOTAL MATRICULADOS', ascending=False)

df_distribucion_nivel2 = primer_df.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 2')['TOTAL MATRICULADOS'].sum().reset_index()
df_distribucion_nivel2 = df_distribucion_nivel2.sort_values('TOTAL MATRICULADOS', ascending=False)

df_distribucion_nivel3 = primer_df.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 3')['TOTAL MATRICULADOS'].sum().reset_index()
df_distribucion_nivel3 = df_distribucion_nivel3.sort_values('TOTAL MATRICULADOS', ascending=False)


# ----------------------------
#segunda sección del dashboard
# Calcular la matrícula total por área del conocimiento para cada año
df_area_año = df_historico_limpio.groupby(['AÑO', 'ÁREA DEL CONOCIMIENTO'])['TOTAL MATRICULADOS'].sum().reset_index()
# Calcular la matrícula en el año inicial y final para cada área
año_inicial = df_area_año['AÑO'].min()
año_final = df_area_año['AÑO'].max()
matricula_inicial = df_area_año[df_area_año['AÑO'] == año_inicial].set_index('ÁREA DEL CONOCIMIENTO')['TOTAL MATRICULADOS']
matricula_final = df_area_año[df_area_año['AÑO'] == año_final].set_index('ÁREA DEL CONOCIMIENTO')['TOTAL MATRICULADOS']
# Calcular el crecimiento absoluto y porcentual
# Usar fill_value=0 para áreas que no existen en ambos años
crecimiento_absoluto = matricula_final.sub(matricula_inicial, fill_value=0)
crecimiento_porcentual = ((matricula_final.sub(matricula_inicial, fill_value=0)) / matricula_inicial.replace(0, np.nan)).fillna(0) * 100 # Evitar división por cero
# Crear un DataFrame con los resultados
df_crecimiento_areas = pd.DataFrame({
    'Matrícula Inicial': matricula_inicial,
    'Matrícula Final': matricula_final,
    'Crecimiento Absoluto': crecimiento_absoluto,
    'Crecimiento Porcentual': crecimiento_porcentual
}).fillna(0) # Rellenar NaN con 0 si un área solo aparece en un año
# Ordenar por crecimiento absoluto y porcentual
df_crecimiento_absoluto_sorted = df_crecimiento_areas.sort_values('Crecimiento Absoluto', ascending=False)
df_crecimiento_porcentual_sorted = df_crecimiento_areas.sort_values('Crecimiento Porcentual', ascending=False)

top_n = 10

# Visualizar el crecimiento porcentual de las top N áreas (considerando áreas con matrícula inicial > 0)
df_crecimiento_porcentual_filtered = df_crecimiento_areas[df_crecimiento_areas['Matrícula Inicial'] > 0].sort_values('Crecimiento Porcentual', ascending=False)

# Agrupar por área del conocimiento y sumar el total de matriculados
df_distribucion_areas = df_historico_limpio.groupby('ÁREA DEL CONOCIMIENTO')['TOTAL MATRICULADOS'].sum().reset_index()
# Ordenar para mejor visualización
df_distribucion_areas = df_distribucion_areas.sort_values('TOTAL MATRICULADOS', ascending=False)
#Distribución de matrículas por Área del Conocimiento

# Agrupar por Área del Conocimiento y Subárea, y sumar el total de matriculados
df_subareas_demanda = df_historico_limpio.groupby(['ÁREA DEL CONOCIMIENTO', 'CINE-F 2013 SUBAREA'])['TOTAL MATRICULADOS'].sum().reset_index()
df_subareas_demanda = df_subareas_demanda[df_subareas_demanda['CINE-F 2013 SUBAREA'].str.lower() != 'nan'].copy()
df_subareas_demanda = df_subareas_demanda[df_subareas_demanda['ÁREA DEL CONOCIMIENTO'].str.lower() != 'nan'].copy()
# Encontrar la subárea más demandada dentro de cada área
# Para cada área, ordenar las subáreas por el total de matriculados y tomar la primera
top_subareas_por_area = df_subareas_demanda.loc[df_subareas_demanda.groupby('ÁREA DEL CONOCIMIENTO')['TOTAL MATRICULADOS'].idxmax()]
# Ordenar el resultado por el total de matriculados descendente
top_subareas_por_area = top_subareas_por_area.sort_values('TOTAL MATRICULADOS', ascending=False)

top_n_areas_for_plot = 5
top_areas_list = top_subareas_por_area['ÁREA DEL CONOCIMIENTO'].unique()[:top_n_areas_for_plot]

# Agrupar por Área del Conocimiento y Subárea, y sumar el total de matriculados
df_subareas_demanda = df_historico_limpio.groupby(['ÁREA DEL CONOCIMIENTO', 'CINE-F 2013 SUBAREA'])['TOTAL MATRICULADOS'].sum().reset_index()
df_subareas_demanda = df_subareas_demanda[df_subareas_demanda['CINE-F 2013 SUBAREA'].str.lower() != 'nan'].copy()
df_subareas_demanda = df_subareas_demanda[df_subareas_demanda['ÁREA DEL CONOCIMIENTO'].str.lower() != 'nan'].copy()
# Encontrar la subárea más demandada dentro de cada área
# Para cada área, ordenar las subáreas por el total de matriculados y tomar la primera
top_subareas_por_area = df_subareas_demanda.loc[df_subareas_demanda.groupby('ÁREA DEL CONOCIMIENTO')['TOTAL MATRICULADOS'].idxmax()]
# Ordenar el resultado por el total de matriculados descendente
top_subareas_por_area = top_subareas_por_area.sort_values('TOTAL MATRICULADOS', ascending=False)

top_n_areas_for_plot = 5
top_areas_list = top_subareas_por_area['ÁREA DEL CONOCIMIENTO'].unique()[:top_n_areas_for_plot]

# ----------------------------

# Tercera sección del dashboard
# Filtrar el DataFrame para incluir solo las carreras del área "Administración y Comercio"
df_admin_comercio = df_historico_limpio[df_historico_limpio['ÁREA DEL CONOCIMIENTO'] == 'Administración y Comercio'].copy()
# Obtener la lista única de nombres de carrera en esta área
carreras_admin_comercio = df_admin_comercio['NOMBRE CARRERA'].unique()
# Crear un nuevo DataFrame con la lista de carreras
df_carreras_admin_comercio = pd.DataFrame({'Carreras en Administración y Comercio': carreras_admin_comercio})
# Agrupar por año y sumar el total de matriculados para el área de Administración y Comercio
df_matriculados_admin_comercio_año = df_admin_comercio.groupby('AÑO')['TOTAL MATRICULADOS'].sum().reset_index()
# Ordenar por año
df_matriculados_admin_comercio_año = df_matriculados_admin_comercio_año.sort_values('AÑO')

carreras_filtradas = df2025[df2025['Carrera'].str.contains('ges|gestion|informacion', case=False, na=False)].copy()
carreras_filtradas.head()


# Agrupar por 'Carrera' en el DataFrame filtrado y sumar los 'Matriculados'
df_carreras_filtradas_agrupadas = carreras_filtradas.groupby('Carrera')['Matriculados'].sum().reset_index()
# Ordenar las carreras filtradas por el total de matriculados en orden descendente
df_carreras_filtradas_agrupadas = df_carreras_filtradas_agrupadas.sort_values('Matriculados', ascending=False)

# Filtrar el DataFrame original para incluir solo el área "Administración y Comercio"
df_admin_comercio = df_historico_limpio[df_historico_limpio['ÁREA DEL CONOCIMIENTO'] == 'Administración y Comercio'].copy()
# Agrupar por Año y Subárea, y sumar el total de matriculados
df_admin_comercio_por_anio_subarea = df_admin_comercio.groupby(['AÑO', 'CINE-F 2013 SUBAREA'])['TOTAL MATRICULADOS'].sum().reset_index()

# Filtrar el DataFrame para el área de "Administración y Comercio"
df_admin_comercio = df_historico_limpio[df_historico_limpio['ÁREA DEL CONOCIMIENTO'] == 'Administración y Comercio'].copy()
# Agrupar por año y sumar el total de matriculados por género
df_genero_admin_comercio = df_admin_comercio.groupby('AÑO')[['MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA']].sum().reset_index()
df_genero_admin_comercio = df_genero_admin_comercio.melt(id_vars='AÑO', var_name='Género', value_name='Total Matriculados')
# Renombrar las columnas para mayor claridad
df_genero_admin_comercio['Género'] = df_genero_admin_comercio['Género'].replace({'MATRICULADOS MUJERES POR PROGRAMA': 'Mujeres','MATRICULADOS HOMBRES POR PROGRAMA': 'Hombres'})

# Calcular el total de hombres y mujeres para el área de Administración y Comercio (sumando sobre todos los años)
total_genero_admin_comercio = df_admin_comercio[['MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA']].sum().reset_index()
# Preparar los datos para el gráfico de barras
total_genero_admin_comercio.columns = ['Género', 'Total Matriculados']

# Filtrar el DataFrame para el área de "Administración y Comercio"
df_admin_comercio = df_historico_limpio[df_historico_limpio['ÁREA DEL CONOCIMIENTO'] == 'Administración y Comercio'].copy()
# Agrupar por tipo de institución en los tres niveles y sumar el total de matriculados
df_institucion_admin_nivel1 = df_admin_comercio.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 1')['TOTAL MATRICULADOS'].sum().reset_index()
df_institucion_admin_nivel2 = df_admin_comercio.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 2')['TOTAL MATRICULADOS'].sum().reset_index()
df_institucion_admin_nivel3 = df_admin_comercio.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 3')['TOTAL MATRICULADOS'].sum().reset_index()
# Calcular la proporción para cada nivel
total_matriculados_admin = df_admin_comercio['TOTAL MATRICULADOS'].sum()

df_institucion_admin_nivel1['Proporción'] = (df_institucion_admin_nivel1['TOTAL MATRICULADOS'] / total_matriculados_admin) * 100
df_institucion_admin_nivel2['Proporción'] = (df_institucion_admin_nivel2['TOTAL MATRICULADOS'] / total_matriculados_admin) * 100
df_institucion_admin_nivel3['Proporción'] = (df_institucion_admin_nivel3['TOTAL MATRICULADOS'] / total_matriculados_admin) * 100
# ----------------------------
#cuarta sección de dashboard
# Sumar el total de matriculados para estas carreras afines en 2025
total_matriculados_carreras_gestion_2025 = carreras_filtradas['Matriculados'].sum()
# Nos basaremos en el área "Administración y Comercio" como punto de partida, ya que el análisis previo se centró allí.
df_gestion_historico = df_historico_limpio[
    (df_historico_limpio['ÁREA DEL CONOCIMIENTO'] == 'Administración y Comercio') &
    (df_historico_limpio['NOMBRE CARRERA'].str.contains('gesti|gestion|control|informacion', case=False, na=False))
].copy()
# Sumar el total de matriculados en estas carreras históricas
total_matriculados_carreras_gestion_historico = df_gestion_historico['TOTAL MATRICULADOS'].sum()
#Carreras afines a Ingeniería en Control de Gestión identificadas (basado en filtros para 2025)
carreras_filtradas['Carrera'].unique()
#Carreras afines a Ingeniería en Control de Gestión identificadas (basado en filtros para 2007-2024 en Administración y Comercio)
df_gestion_historico['NOMBRE CARRERA'].unique()

# Usamos el dataframe filtrado df_gestion_historico creado en la pregunta anterior
# Agrupar por año y sumar el total de matriculados para estas carreras específicas
df_evolucion_gestion_historico = df_gestion_historico.groupby('AÑO')['TOTAL MATRICULADOS'].sum().reset_index()
# Ordenar por año
df_evolucion_gestion_historico = df_evolucion_gestion_historico.sort_values('AÑO')

# Creamos una nueva fila para el año 2025 con el total de matriculados de carreras_filtradas
nueva_fila_2025_gestion = pd.DataFrame({'AÑO': [2025], 'TOTAL MATRICULADOS': [total_matriculados_carreras_gestion_2025]})

# Concatenar la nueva fila al DataFrame histórico
df_evolucion_gestion_con_2025 = pd.concat([df_evolucion_gestion_historico, nueva_fila_2025_gestion], ignore_index=True)
# Filtrar el DataFrame histórico de carreras afines a Gestión para incluir las columnas de clasificación
df_gestion_institucion = df_gestion_historico[[
    'AÑO',
    'TOTAL MATRICULADOS',
    'CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
    'CLASIFICACIÓN INSTITUCIÓN NIVEL 2',
    'CLASIFICACIÓN INSTITUCIÓN NIVEL 3',
    'NOMBRE INSTITUCIÓN' # Incluir nombre para análisis más granular si es necesario
]].copy()

# Agrupar por tipo de institución (Nivel 1) y sumar el total de matriculados en estas carreras
df_distribucion_gestion_nivel1 = df_gestion_institucion.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 1')['TOTAL MATRICULADOS'].sum().reset_index()

# Calcular la proporción
total_matriculados_gestion_historico = df_gestion_institucion['TOTAL MATRICULADOS'].sum()
df_distribucion_gestion_nivel1['Proporción'] = (df_distribucion_gestion_nivel1['TOTAL MATRICULADOS'] / total_matriculados_gestion_historico) * 100

# Análisis por Nivel 2
df_distribucion_gestion_nivel2 = df_gestion_institucion.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 2')['TOTAL MATRICULADOS'].sum().reset_index()
df_distribucion_gestion_nivel2['Proporción'] = (df_distribucion_gestion_nivel2['TOTAL MATRICULADOS'] / total_matriculados_gestion_historico) * 100
df_distribucion_gestion_nivel2 = df_distribucion_gestion_nivel2.sort_values('TOTAL MATRICULADOS', ascending=False)

# Análisis por Nivel 3
df_distribucion_gestion_nivel3 = df_gestion_institucion.groupby('CLASIFICACIÓN INSTITUCIÓN NIVEL 3')['TOTAL MATRICULADOS'].sum().reset_index()
df_distribucion_gestion_nivel3['Proporción'] = (df_distribucion_gestion_nivel3['TOTAL MATRICULADOS'] / total_matriculados_gestion_historico) * 100
df_distribucion_gestion_nivel3 = df_distribucion_gestion_nivel3.sort_values('TOTAL MATRICULADOS', ascending=False)

# Usamos el dataframe df_gestion_historico creado previamente
df_genero_gestion_historico = df_gestion_historico.groupby('AÑO')[['MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA']].sum().reset_index()
# Derretir el dataframe para facilitar la graficación con seaborn
df_genero_gestion_historico = df_genero_gestion_historico.melt(id_vars='AÑO', var_name='Género', value_name='Total Matriculados')

total_genero_gestion_historico = df_gestion_historico[['MATRICULADOS MUJERES POR PROGRAMA', 'MATRICULADOS HOMBRES POR PROGRAMA']].sum().reset_index()
total_genero_gestion_historico.columns = ['Género', 'Total Matriculados']


# Menú de navegación en la parte superior
st.markdown("---")
st.subheader("Menú de Navegación")
st.write("Selecciona una opción en el menú principal para visualizar los datos.")

menu = st.selectbox(
    "Menú Principal",
    ("Análisis general de las matrículas en educación superior (2017–2024)+(2025)", "Datos Históricos", "Datos 2025",
     "Enfoque específico en las carreras del área económica",
     "Enfoque específico en carreras similares a Ingeniería en Control de Gestión","interactive")
)


if menu == "Análisis general de las matrículas en educación superior (2017–2024)+(2025)":
    st.header("Bienvenido al Dashboard de Análisis de Matriculados")
    st.write("Bienvenido al panel principal. ")
    st.subheader(f"📊 Resumen para el Año {anio_sel}")
    total = df_filtrado["TOTAL MATRICULADOS"].sum()
    mujeres = df_filtrado["MATRICULADOS MUJERES POR PROGRAMA"].sum()
    hombres = df_filtrado["MATRICULADOS HOMBRES POR PROGRAMA"].sum()
    porc_mujeres = round((mujeres / total) * 100, 2) if total > 0 else 0
    porc_hombres = round((hombres / total) * 100, 2) if total > 0 else 0
    total_gestion_2025 = df_evolucion_gestion_con_2025["TOTAL MATRICULADOS"].sum()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("👥 Total Matriculados", total)
    col2.metric("👩 Mujeres", mujeres)
    col3.metric("👨 Hombres", hombres)
    col4.metric("% Mujeres", f"{porc_mujeres}%")
    col5.metric("% Hombres", f"{porc_hombres}%")
    col6.metric("📈 Total Gestión 2025", total_gestion_2025)

    st.subheader("Muestras Visualizaciones Principales")

    # Gráfico de barras para mostrar el total de matriculados por área del conocimiento
    
    fig_area_conocimiento = px.bar(df_historico_limpio.groupby("ÁREA DEL CONOCIMIENTO")["TOTAL MATRICULADOS"].sum().reset_index(),
                                    y="ÁREA DEL CONOCIMIENTO", x="TOTAL MATRICULADOS", color="TOTAL MATRICULADOS",
                                    color_continuous_scale="RdPu",  # Degradado rosado
                                    orientation="h",
                                    title="Total de Matrículas por Área del Conocimiento")
    fig_area_conocimiento.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_area_conocimiento, use_container_width=True)

   



    regiones_sum = df_historico_limpio.groupby("REGIÓN")["TOTAL MATRICULADOS"].sum().reset_index()
    fig_region = px.bar(
        regiones_sum,
        y="REGIÓN",
        x="TOTAL MATRICULADOS",
        color="TOTAL MATRICULADOS",
        orientation="h",
        title="Total de Matrículas por Región",
        color_continuous_scale="Teal"
    )
    fig_region.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_region, use_container_width=True) 

   
    st.subheader("¿Cómo ha evolucionado el total de matriculados en educación superior desde 2017 hasta 2024+2025?")
    # Gráfico de líneas por año usando Plotly
    st.subheader("Evolución de Matriculados  (2017-2025)")
    # Gráfico solo del total de matriculados (2017-2025), sin desagregar por género
    df_total = df_filtrado.groupby('AÑO')['TOTAL MATRICULADOS'].sum().reset_index()
    df_total = df_total.sort_values('AÑO')
    # Agregar 2025
    df_total_2025 = pd.DataFrame({'AÑO': [2025], 'TOTAL MATRICULADOS': [total_matriculados_2025]})
    df_total = pd.concat([df_total, df_total_2025], ignore_index=True)

    fig_total = px.line(
        df_total,
        x='AÑO',
        y='TOTAL MATRICULADOS',
        markers=True,
        title='Evolución del Total de Matriculados (2017-2025)'
    )
    fig_total.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_total, use_container_width=True)

    st.subheader("¿Cuál ha sido la evolución por género (mujeres, hombres) en este período?")

    # Evolución por género (2017-2024) en Plotly
    df_genero_plotly = df_genero_año.copy()
    fig_genero = px.line(
        df_genero_plotly,
        x='AÑO',
        y='Total Matriculados',
        color='Género',
        markers=True,
        title='Comparación de Matriculados entre Hombres y Mujeres por Año (2017-2024)'
    )
    fig_genero.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_genero, use_container_width=True)

    
    st.subheader("¿Cómo se distribuyen las matrículas por tipo de institución (Universidades CRUCH, Universidades Privadas, Institutos Profesionales, Centros de Formación Técnica)?")
    
    # Gráfico de barras de distribución de matrículas por tipo de institución usando Plotly
    fig_nivel1 = px.bar(
        df_distribucion_nivel1,
        x='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        y='TOTAL MATRICULADOS',
        color='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        title='Distribución de Matriculados por Clasificación Institución Nivel 1 (2007-2024)',
        labels={'CLASIFICACIÓN INSTITUCIÓN NIVEL 1': 'Clasificación Institución Nivel 1', 'TOTAL MATRICULADOS': 'Total de Matriculados'}
    )
    fig_nivel1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_nivel1, use_container_width=True)



    st.header("Tendencias en áreas del conocimiento y subáreas (general)")
    st.subheader("¿Qué áreas del conocimiento han experimentado mayor crecimiento en matrícula durante el período analizado?")
    
    # Gráfico de barras del top N áreas con mayor crecimiento absoluto usando Plotly
    fig_crecimiento_absoluto = px.bar(
        df_crecimiento_absoluto_sorted.head(top_n).reset_index(),
        x='ÁREA DEL CONOCIMIENTO',
        y='Crecimiento Absoluto',
        title=f'Top {top_n} Áreas del Conocimiento con Mayor Crecimiento Absoluto de Matrícula ({año_inicial}-{año_final})',
        labels={'ÁREA DEL CONOCIMIENTO': 'Área del Conocimiento', 'Crecimiento Absoluto': 'Crecimiento Absoluto de Matriculados'},
        color='Crecimiento Absoluto',
        color_continuous_scale='viridis'
    )
    fig_crecimiento_absoluto.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_crecimiento_absoluto, use_container_width=True)

    


    st.subheader("¿Cómo se distribuye la matrícula en las áreas de ciencias sociales, ciencias de la salud, tecnología, etc.?")

    # Gráfico de barras de distribución de matrículas por área del conocimiento usando Plotly
    fig_distribucion_areas = px.bar(
        df_distribucion_areas,
        x='ÁREA DEL CONOCIMIENTO',
        y='TOTAL MATRICULADOS',
        color='ÁREA DEL CONOCIMIENTO',
        title='Distribución de Matriculados por Área del Conocimiento (2007-2024)',
        labels={'ÁREA DEL CONOCIMIENTO': 'Área del Conocimiento', 'TOTAL MATRICULADOS': 'Total de Matriculados'}
    )
    fig_distribucion_areas.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_distribucion_areas, use_container_width=True)

  
elif menu == "Datos Históricos":
    st.header("Vista de Datos Históricos")
    st.dataframe(df_historico_limpio)
    st.subheader("Datos Históricos Filtrados")
    

    st.download_button(
        "⬇ Descargar Excel", 
        data=convertir_excel(df_historico_limpio), 
        file_name="matriculas_filtrado.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    
elif menu == "Datos 2025":
    st.header("Vista de Datos 2025")
    st.dataframe(df2025)
    st.subheader("Datos 2025 Filtrados")

    st.download_button(
        "⬇ Descargar Excel", 
        data=convertir_excel(df2025), 
        file_name="matriculas_2025.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





    

    


    
elif menu == "Enfoque específico en las carreras del área económica":
    st.header("Enfoque específico en las carreras del área económica")
    st.subheader("¿Qué áreas del conocimiento han experimentado mayor crecimiento en matrícula durante el período analizado?")

    # Gráfico de distribución de matrícula por género en Administración y Comercio usando Plotly
    fig_genero_admin_comercio = px.line(
        df_genero_admin_comercio,
        x='AÑO',
        y='Total Matriculados',
        color='Género',
        markers=True,
        title='Distribución de Matrícula por Género en Administración y Comercio (2007-2024)',
        labels={'AÑO': 'Año', 'Total Matriculados': 'Total de Matriculados', 'Género': 'Género'}
    )
    fig_genero_admin_comercio.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_genero_admin_comercio, use_container_width=True)
    
   


    # Gráfico de barras horizontal con Plotly para las carreras filtradas en 2025 (ejes invertidos)
    fig_carreras_filtradas_horizontal = px.bar(
        df_carreras_filtradas_agrupadas.head(20),
        y='Carrera',
        x='Matriculados',
        color_continuous_scale="RdPu",
        orientation='h',
        title='Distribución de Matriculados por Carrera Filtrada (Gestión, Información, etc.) en 2025 (Ejes Invertidos)',
        labels={'Carrera': 'Carrera', 'Matriculados': 'Total de Matriculados (2025)'}
    )
    fig_carreras_filtradas_horizontal.update_layout(yaxis_tickangle=0)
    st.plotly_chart(fig_carreras_filtradas_horizontal, use_container_width=True)

    st.subheader("¿Qué subáreas dentro del área económica han mostrado un mayor crecimiento?")

    
    # Gráfico de evolución por subárea dentro de Administración y Comercio usando Plotly
    fig_subarea_admin_comercio = px.line(
        df_admin_comercio_por_anio_subarea,
        x='AÑO',
        y='TOTAL MATRICULADOS',
        color='CINE-F 2013 SUBAREA',
        markers=True,
        title='Evolución de Matriculados por Subárea en Administración y Comercio (2007-2024)',
        labels={'AÑO': 'Año', 'TOTAL MATRICULADOS': 'Total de Matriculados', 'CINE-F 2013 SUBAREA': 'Subárea'}
    )
    fig_subarea_admin_comercio.update_layout(xaxis=dict(dtick=1), legend_title_text='Subárea')
    st.plotly_chart(fig_subarea_admin_comercio, use_container_width=True)

    st.subheader("¿Cuál es la distribución de matrícula por género en las carreras económicas?")


    
    # Gráfico de barras de distribución de matriculados por Clasificación Institución Nivel 1 usando Plotly
    fig_admin_nivel1_bar = px.bar(
        df_institucion_admin_nivel1,
        y='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        x='TOTAL MATRICULADOS',
        color='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        orientation='h',
        title='Distribución de Matriculados en Administración y Comercio por Clasificación Institución Nivel 1 (2007-2024)',
        labels={'CLASIFICACIÓN INSTITUCIÓN NIVEL 1': 'Clasificación Institución Nivel 1', 'TOTAL MATRICULADOS': 'Total de Matriculados'}
    )
    fig_admin_nivel1_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_admin_nivel1_bar, use_container_width=True)
    

elif menu == "Enfoque específico en carreras similares a Ingeniería en Control de Gestión":
    st.header("Enfoque específico en carreras similares a Ingeniería en Control de Gestión")
    st.subheader("¿Cuántos estudiantes se matriculan en carreras afines a Ingeniería en Control de Gestión?")
    st.write(f"Total de estudiantes matriculados en carreras afines a Ingeniería en Control de Gestión (2007-2024) dentro del área de Administración y Comercio: {total_matriculados_carreras_gestion_historico}")

    st.subheader("¿Cómo ha evolucionado la matrícula en estas carreras específicas a lo largo de los años?")
    # Gráfico de evolución de matrícula en carreras afines a Ingeniería en Control de Gestión usando Plotly

    fig_evolucion_gestion_plotly = px.line(
        df_evolucion_gestion_historico,
        x='AÑO',
        y='TOTAL MATRICULADOS',
        markers=True,
        title='Evolución de la Matrícula en Carreras Afines a Ingeniería en Control de Gestión (2007-2024)'
    )
    fig_evolucion_gestion_plotly.update_layout(
        xaxis=dict(dtick=1),
        xaxis_title='Año',
        yaxis_title='Total de Matriculados',
        showlegend=False
    )
    st.plotly_chart(fig_evolucion_gestion_plotly, use_container_width=True)

    st.subheader("¿Cuál es la participación de las Universidades CRUCH, privadas y otros tipos de instituciones en estas carreras?")
    # Gráfico de barras de distribución de matriculados por Clasificación Institución Nivel 1 en carreras afines a Gestión usando Plotly
    fig_distribucion_gestion_nivel1_bar = px.bar(
        df_distribucion_gestion_nivel1,
        y='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        x='TOTAL MATRICULADOS',
        orientation='h',
        color='CLASIFICACIÓN INSTITUCIÓN NIVEL 1',
        title='Distribución de Matriculados en Carreras Afines a Gestión por Clasificación Institución Nivel 1 (2007-2024)',
        labels={'CLASIFICACIÓN INSTITUCIÓN NIVEL 1': 'Clasificación Institución Nivel 1', 'TOTAL MATRICULADOS': 'Total de Matriculados'}
    )
    fig_distribucion_gestion_nivel1_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_distribucion_gestion_nivel1_bar, use_container_width=True)

    

    st.subheader("¿Cómo se distribuye la matrícula por género en las carreras relacionadas con Control de Gestión?")
    
    # Gráfico de evolución por género en carreras afines a Control de Gestión usando Plotly
    fig_genero_gestion = px.line(
        df_genero_gestion_historico,
        x='AÑO',
        y='Total Matriculados',
        color='Género',
        markers=True,
        title='Distribución de Matrícula por Género en Carreras Afines a Control de Gestión (2007-2024)',
        labels={'AÑO': 'Año', 'Total Matriculados': 'Total de Matriculados', 'Género': 'Género'}
    )
    fig_genero_gestion.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_genero_gestion, use_container_width=True)

    # Gráfico de barras de distribución total por género en carreras afines a Control de Gestión usando Plotly

    fig_total_genero_gestion = px.bar(
        total_genero_gestion_historico,
        y='Género',
        x='Total Matriculados',
        color='Género',
        orientation='h',
        title='Total de Matriculados por Género en Carreras Afines a Control de Gestión (2007-2024)',
        labels={'Género': 'Género', 'Total Matriculados': 'Total de Matriculados'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_total_genero_gestion, use_container_width=True)


    df_info_control = df_historico_limpio[df_historico_limpio["NOMBRE CARRERA"] == "INGENIERIA EN INFORMACION Y CONTROL DE GESTION"]

    if df_info_control.empty:
        st.warning("No hay datos disponibles para la carrera 'Ingeniería en Información y Control de Gestión'.")
    else:
        # Gráfico de evolución de matrículas con puntos
        fig5 = px.line(df_info_control.groupby("AÑO")["TOTAL MATRICULADOS"].sum().reset_index(),
                       x="AÑO", y="TOTAL MATRICULADOS", 
                       title="Evolución de Matrículas en Ingeniería en Información y Control de Gestión",
                       line_shape="linear", line_dash_sequence=["solid"], 
                       markers=True)  # Añadir puntos en la línea
        fig5.update_traces(line_color="purple")
        fig5.update_layout(xaxis=dict(tickmode="array", tickvals=list(range(2007, 2025))))  # Asegurar que todos los años aparezcan
        st.plotly_chart(fig5, use_container_width=True)

    df_info_control2 = df_historico[df_historico["NOMBRE CARRERA"] == "INGENIERIA EN INFORMACION Y CONTROL DE GESTION"]
    fig_modalidad_info_control = px.bar(df_info_control2.groupby("MODALIDAD")["TOTAL MATRICULADOS"].sum().reset_index(),
                                                x="TOTAL MATRICULADOS", y="MODALIDAD", color="MODALIDAD",
                                                title="Distribución de Matrículas por Modalidad en Ingeniería en Información y Control de Gestión",
                                                color_discrete_map={
                                                    'Presencial': "#034e83", 
                                                    'Semipresencial': "#33e9d7",  
                                                    'No Presencial': "#E32A4F"  
                                                })
    fig_modalidad_info_control.update_layout(xaxis_tickangle=0, margin={"b": 150}, xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig_modalidad_info_control, use_container_width=True, key="fig_modalidad_info_control")


    fig_institucion_info_control = px.bar(df_info_control.groupby("NOMBRE INSTITUCIÓN")["TOTAL MATRICULADOS"].sum().reset_index(),
                                          y="NOMBRE INSTITUCIÓN", x="TOTAL MATRICULADOS", color="TOTAL MATRICULADOS",
                                          orientation="h",
                                          title="Matrículas en Ingeniería en Información y Control de Gestión por Institución",
                                          color_continuous_scale="dense")  
    fig_institucion_info_control.update_layout(
                xaxis_tickangle=-45,  # Alineación de texto en el eje X
                margin={"b": 200},  # Márgenes para evitar que los nombres se corten
                xaxis={'categoryorder': 'total descending'}  # Ordena las categorías por total matriculados
    )
    st.plotly_chart(fig_institucion_info_control, use_container_width=True, key="fig_institucion_info_control")


    fig_heatmap = px.density_heatmap(df_info_control, x="AÑO", y="REGIÓN", z="TOTAL MATRICULADOS", 
                                    color_continuous_scale="RdPu",
                                    title="Mapa de Calor de Matrículas por Año y Región (Ingeniería en Información y Control de Gestión)",
                                    text_auto=True)  # Mostrar los valores dentro de las celdas
    st.plotly_chart(fig_heatmap, use_container_width=True, key="fig_heatmap")


elif menu == "interactive":
    st.header("Interactive Dashboard")
    # ---------------------------- VISUALIZACIONES INTERACTIVAS ----------------------------
    st.markdown("## 📌 Visualizaciones Interactivas")

    st.markdown("## 🔍 Exploración Libre con PyGWalker")
    html = pyg.to_html(df_historico_limpio, return_html=True, dark='light')
    components.html(html, height=800, scrolling=True)









    














