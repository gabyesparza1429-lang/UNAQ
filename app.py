import streamlit as st
import pandas as pd
import io
import re
import json

# Configuración inicial de la interfaz web
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if "examenes_programados" not in st.session_state:
    st.session_state.examenes_programados = {}

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Estructura de Control de Notas Unificada y Antiborrados.")
st.write("---")

# BARRA LATERAL
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
            'num_quizes': 4, 'w_quiz': 30, 'num_proyectos': 2, 'w_proyecto': 30,
            'dias_asistencia': 32, 'w_asistencia': 15, 'num_firmas': 15, 'w_firmas': 15, 'w_ser': 10
        })

# SI NO HAY DATOS EN MEMORIA, MOSTRAR PANEL DE CARGA LIMPIO
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga Inicial o Restauración de Listas")
    st.info("El servidor se ha optimizado. Para activar tus grupos, puedes arrastrar un archivo Excel/CSV o pegar la lista de alumnos.")
    
    pestana_pegar, pestana_archivo = st.tabs(["📋 Método 1: Pegar Texto de la Lista", "📁 Método 2: Subir un Excel de Respaldo"])
    
    with pestana_pegar:
        texto_pegado = st.text_area("Pega aquí el contenido de tus listas de la UNAQ:", height=250)
        if st.button("✨ Procesar Texto y Crear Grupo", type="primary"):
            if texto_pegado.strip():
                lineas = texto_pegado.split("\n")
                diccionario_grupos = {}
                carrera_actual, nivel_actual = "", ""
                
                for linea in lineas:
                    linea_limpia = linea.strip()
                    if not linea_limpia or len(linea_limpia) < 3: continue
                    
                    match_nivel = re.search(r'(?:A|B|FR)?-?(\d\.\d)', linea_limpia, re.IGNORECASE)
                    if match_nivel: nivel_actual = f"A{match_nivel.group(1)}"
                    
                    match_carrera = re.search(r'\b([A-Z]{3,5})\d{4}\b', linea_limpia, re.IGNORECASE)
                    if match_carrera: carrera_actual = match_carrera.group(1).upper()
                    
                    grupo_compuesto = f"{carrera_actual if carrera_actual else 'CARRERA'} {nivel_actual if nivel_actual else 'NIVEL'}"
                    
                    if any(b in linea_limpia.lower() for b in ["universidad", "aeronáutica", "lista", "matricula", "nombre"]): continue
                    
                    linea_limpia = re.sub(r'\b[A-Z]+\d{4}\b', '', linea_limpia, flags=re.IGNORECASE).strip()
                    linea_limpia = re.sub(r'\b\d+\b', '', linea_limpia).strip()
                    
                    if len(linea_limpia.split()) >= 2:
                        if grupo_compuesto not in diccionario_grupos: diccionario_grupos[grupo_compuesto] = []
                        diccionario_grupos[grupo_compuesto].append(linea_limpia.upper())
                
                for grupo, lista_alumnos in diccionario_grupos.items():
                    lista_final = sorted(list(set(lista_alumnos)))
                    if lista_final:
                        df_init = pd.DataFrame({'Alumno': lista_final})
                        for q in range(1, 5): df_init[f"Quiz {q}"] = 0.0
                        for p in range(1, 3): df_init[f"Proyecto {p}"] = 0.0
                        df_init['TOTAL QUIZ'] = 0.0
                        df_init['TOTAL PROYECTO'] = 0.0
                        df_init['Días Asistidos'] = 32
                        df_init['Asistencia'] = 10.0
                        df_init['Firmas Registradas'] = 15
                        df_init['TOTAL FIRMAS'] = 10.0
                        df_init['Ser'] = 0.0
                        df_init['NOTA BASE 10'] = 0.0
                        df_init['PUNTAJE 30%'] = 0.0
                        st.session_state.base_datos_grupos[grupo] = df_init
                st.rerun()

    with pestana_archivo:
        archivo_subido = st.file_uploader("Sube un archivo Excel (.xlsx) o CSV:", type=["xlsx", "csv"])
        if archivo_subido is not None:
            try:
                if archivo_subido.name.endswith('.xlsx'):
                    df_excel = pd.read_excel(archivo_subido)
                else:
                    df_excel = pd.read_csv(archivo_subido)
                
                # Intentamos registrar el nombre del grupo basado en el archivo
                nombre_g = archivo_subido.name.split('.')[0].replace('_', ' ')
                st.session_state.base_datos_grupos[nombre_g] = df_excel
                st.success("🎉 ¡Archivo Excel cargado con éxito en la aplicación!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

else:
    # Si ya hay datos en memoria, mostrar la interfaz tradicional sin bloqueos
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
        'num_quizes': 4, 'w_quiz': 30, 'num_proyectos': 2, 'w_proyecto': 30,
        'dias_asistencia': 32, 'w_asistencia': 15, 'num_firmas': 15, 'w_firmas': 15, 'w_ser': 10
    })
    
    st.success(f"📋 Trabajando en el Grupo: {grupo_seleccionado}")
    
    # Botón para descargar el avance actual y no perder nada nunca
    csv_buffer = io.StringIO()
    df_grupo.to_csv(csv_buffer, index=False)
    st.download_button(
        label="💾 GUARDAR RESPALDO DE SEGURIDAD (EXCEL/CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"Respaldo_Notas_{grupo_seleccionado}.csv",
        mime="text/csv"
    )
    
    st.write("---")
    st.dataframe(df_grupo, use_container_width=True, hide_index=True)
    
    # Botón de reinicio maestro por si quieren cambiar de grupo
    if st.button("🔄 Cerrar este grupo y cargar otra lista"):
        st.session_state.base_datos_grupos = {}
        st.rerun()
