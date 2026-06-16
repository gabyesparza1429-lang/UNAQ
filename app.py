import streamlit as st
import pandas as pd
import io
import json

# Configuración inicial de la interfaz web (Igual a tu app original)
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

# Inicializar los contenedores de memoria interna de la app
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Estructura Original con Inyección y Soporte de Respaldos.")
st.write("---")

# BARRA LATERAL
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    # Si ya hay grupos en la memoria, mostrar el selector clásico de Óscar
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)

# PANTALLA DE CONTROL: SI NO HAY GRUPOS ACTIVOS, MOSTRAR PANEL DE INYECCIÓN
if not st.session_state.base_datos_grupos:
    st.header("📂 Panel de Recuperación e Inyección de Listas")
    st.info("Para activar la cuadrícula de notas de Óscar, pega el texto de las listas o sube un archivo de respaldo.")
    
    pestana_pegar, pestana_archivo = st.tabs(["📋 Método 1: Pegar Texto de la Lista", "📁 Método 2: Subir Respaldo (.csv o .json)"])
    
    with pestana_pegar:
        texto_pegado = st.text_area("Pega aquí el contenido de tus listas de la UNAQ:", height=250)
        
        if st.button("✨ Procesar Texto y Activar Tablas", type="primary", use_container_width=True):
            if texto_pegado.strip():
                # Separar el texto por líneas limpias
                lineas = [l.strip() for l in texto_pegado.split('\n') if l.strip()]
                
                # Crear un grupo por defecto por si el texto no trae cabecera clara
                grupo_actual = "GRUPO_A1.40"
                alumnos_por_grupo = {grupo_actual: []}
                
                for linea in lineas:
                    # Detectar si la línea contiene un código de grupo de la UNAQ
                    if "-" in linea and ("IAM" in linea or "IDMA" in linea or "IECSA" in linea or "MA-" in linea):
                        # Limpiar el nombre del maestro si viene en la misma línea
                        potencial_grupo = linea.replace("HERNANDEZ FLORES OSCAR", "").strip()
                        # Extraer solo el código del grupo corto para que no quede una pestaña enorme
                        partes = potencial_grupo.split()
                        grupo_actual = partes[0] if partes else potencial_grupo
                        if grupo_actual not in alumnos_por_grupo:
                            alumnos_por_grupo[grupo_actual] = []
                        continue
                    
                    # Detectar renglón de alumno (si empieza con número de lista seguido de matrícula)
                    partes_linea = linea.split()
                    if len(partes_linea) >= 3 and partes_linea[0].isdigit() and partes_linea[1].isdigit():
                        # Excluir palabras de cabecera que se puedan colar
                        if any(x in linea.lower() for x in ["universidad", "lista", "docente", "matricula"]):
                            continue
                        
                        matricula = partes_linea[1]
                        # El resto de la línea es el nombre del alumno, quitando el plan de estudios del final si existe
                        resto = " ".join(partes_linea[2:])
                        if partes_linea[-1].isalnum() and len(partes_linea[-1]) >= 7: # Posible plan como IAM2024
                            nombre_alumno = " ".join(partes_linea[2:-1]).upper()
                        else:
                            nombre_alumno = resto.upper()
                            
                        alumnos_por_grupo[grupo_actual].append(nombre_alumno)
                
                # Convertir las listas en los DataFrames con el formato exacto de tu app anterior
                for grupo, lista_nombres in alumnos_por_grupo.items():
                    # Eliminar duplicados manteniendo el orden
                    lista_limpia = sorted(list(set(lista_nombres)))
                    if lista_limpia:
                        df_init = pd.DataFrame({'Alumno': lista_limpia})
                        # Columnas originales de captura de Óscar
                        df_init['Quiz 1'] = 0.0
                        df_init['Quiz 2'] = 0.0
                        df_init['Quiz 3'] = 0.0
                        df_init['Quiz 4'] = 0.0
                        df_init['TOTAL QUIZ'] = 0.0
                        df_init['Proyecto 1'] = 0.0
                        df_init['Proyecto 2'] = 0.0
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
        archivo_subido = st.file_uploader("Sube un archivo de respaldo previo (.csv):", type=["csv"])
        if archivo_subido is not None:
            try:
                df_excel = pd.read_csv(archivo_subido)
                nombre_g = archivo_subido.name.split('.')[0].replace('Respaldo_Notas_', '')
                st.session_state.base_datos_grupos[nombre_g] = df_excel
                st.success("🎉 ¡Respaldo cargado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

# SI YA HAY GRUPOS CARGADOS: MOSTRAR LA INTERFAZ ORIGINAL DE ÓSCAR (DATAEDITOR CELDA POR CELDA)
else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    
    st.success(f"📋 Mostrando lista para el Grupo: {grupo_seleccionado}")
    
    # 💾 EL BOTÓN DE MEJORA: Descarga el respaldo inmediato a la PC
    csv_buffer = io.StringIO()
    df_grupo.to_csv(csv_buffer, index=False)
    st.download_button(
        label="💾 GUARDAR RESPALDO DE SEGURIDAD EN TU COMPUTADORA (EXCEL/CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"Respaldo_Notas_{grupo_seleccionado}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.write("---")
    st.write("💡 *Instrucciones para Óscar: Puedes dar doble clic directo en cualquier celda para cambiar las calificaciones, asistencias o firmas.*")
    
    # El editor interactivo clásico celda por celda que le gusta a Óscar
    df_editado = st.data_editor(df_grupo, use_container_width=True, hide_index=True)
    
    # Recalcular automáticamente si Óscar cambia datos en la tabla en tiempo real
    if not df_editado.equals(df_grupo):
        for idx in df_editado.index:
            # Captura de datos numéricos desde las celdas editadas
            q1 = float(df_editado.at[idx, "Quiz 1"])
            q2 = float(df_editado.at[idx, "Quiz 2"])
            q3 = float(df_editado.at[idx, "Quiz 3"])
            q4 = float(df_editado.at[idx, "Quiz 4"])
            p1 = float(df_editado.at[idx, "Proyecto 1"])
            p2 = float(df_editado.at[idx, "Proyecto 2"])
            dias = int(df_editado.at[idx, "Días Asistidos"])
            firmas = int(df_editado.at[idx, "Firmas Registradas"])
            ser = float(df_editado.at[idx, "Ser"])
            
            # Cálculos automáticos matemáticos de los rubros
            t_quiz = round((q1 + q2 + q3 + q4) / 4.0, 2)
            t_proj = round((p1 + p2) / 2.0, 2)
            t_asist = round((min(dias, 32) / 32.0) * 10.0, 2)
            t_firmas = round((min(firmas, 15) / 15.0) * 10.0, 2)
            
            df_editado.at[idx, "TOTAL QUIZ"] = t_quiz
            df_editado.at[idx, "TOTAL PROYECTO"] = t_proj
            df_editado.at[idx, "Asistencia"] = t_asist
            df_editado.at[idx, "TOTAL FIRMAS"] = t_firmas
            
            # Nota final base 10 (Quizes 30%, Proyectos 30%, Asistencia 15%, Firmas 15%, SER 10%)
            nota_b10 = (t_quiz * 0.3) + (t_proj * 0.3) + (t_asist * 0.15) + (t_firmas * 0.15) + (ser * 0.1)
            df_editado.at[idx, "NOTA BASE 10"] = round(nota_b10, 1)
            df_editado.at[idx, "PUNTAJE 30%"] = round(nota_b10 * 0.3, 2)
            
        st.session_state.base_datos_grupos[grupo_seleccionado] = df_editado
        st.rerun()

    # Botón de emergencia para cerrar sesión o cambiar todo el bloque de texto
    if st.button("🔄 Cerrar este grupo y cargar otra lista de texto"):
        st.session_state.base_datos_grupos = {}
        st.rerun()
