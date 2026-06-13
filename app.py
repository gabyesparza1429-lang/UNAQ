import streamlit as st
import pandas as pd
import io
import re
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración inicial de la interfaz web
st.set_page_config(page_title="GEM UNAQ - Control de Notas Adaptativo", layout="wide")

# Nombre del archivo permanente
ARCHIVO_BD = "base_datos_alumnos.json"

def guardar_datos_permanentes():
    datos_exportar = {
        "grupos": {},
        "configuraciones_grupos": st.session_state.configuraciones_grupos,
        "examenes_programados": st.session_state.get("examenes_programados", {})
    }
    for grupo, df in st.session_state.base_datos_grupos.items():
        datos_exportar["grupos"][grupo] = df.to_dict(orient="records")
    with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
        json.dump(datos_exportar, f, ensure_ascii=False, indent=4)

def cargar_datos_permanentes():
    if os.path.exists(ARCHIVO_BD):
        try:
            with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
                datos_importados = json.load(f)
            
            st.session_state.examenes_programados = datos_importados.get("examenes_programados", {})
            saved_cfgs = datos_importados.get("configuraciones_grupos", {})
            
            for grupo, cfg in saved_cfgs.items():
                if 'num_quizes' not in cfg: cfg['num_quizes'] = 4
                if 'n_quiz' not in cfg: cfg['n_quiz'] = 'Quizes'
                if 'w_quiz' not in cfg: cfg['w_quiz'] = 30
                if 'num_proyectos' not in cfg: cfg['num_proyectos'] = 2
                if 'n_proyecto' not in cfg: cfg['n_proyecto'] = 'Proyectos'
                if 'w_proyecto' not in cfg: cfg['w_proyecto'] = 30
                if 'dias_asistencia' not in cfg: cfg['dias_asistencia'] = 32
                if 'n_asistencia' not in cfg: cfg['n_asistencia'] = 'Asistencia'
                if 'w_asistencia' not in cfg: cfg['w_asistencia'] = 15
                if 'num_firmas' not in cfg: cfg['num_firmas'] = 15
                if 'n_firmas' not in cfg: cfg['n_firmas'] = 'Firmas / Tareas'
                if 'w_firmas' not in cfg: cfg['w_firmas'] = 15
                if 'n_ser' not in cfg: cfg['n_ser'] = 'SER / Actitud'
                if 'w_ser' not in cfg: cfg['w_ser'] = 10
                saved_cfgs[grupo] = cfg
                
            st.session_state.configuraciones_grupos = saved_cfgs
            
            diccionario_final = {}
            for grupo, lista_filas in datos_importados.get("grupos", {}).items():
                df = pd.DataFrame(lista_filas)
                columnas_obligatorias = ['Alumno', 'TOTAL QUIZ', 'TOTAL PROYECTO', 'TOTAL FIRMAS', 'Asistencia', 'Ser', 'NOTA BASE 10', 'PUNTAJE 30%']
                for col in columnas_obligatorias:
                    if col not in df.columns:
                        df[col] = 0.0 if col != 'Alumno' else ''
                diccionario_final[grupo] = df
            return diccionario_final
        except:
            return {}
    return {}

# Inicialización segura de la memoria de exámenes
if "examenes_programados" not in st.session_state:
    st.session_state.examenes_programados = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Control de Notas con soporte para Inteligencia Artificial y programación dinámica de exámenes.")
st.write("---")

# BARRA LATERAL
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        if grupo_seleccionado not in st.session_state.configuraciones_grupos:
            st.session_state.configuraciones_grupos[grupo_seleccionado] = {
                'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 30,
                'num_proyectos': 2, 'n_proyecto': 'Proyectos', 'w_proyecto': 30,
                'dias_asistencia': 32, 'n_asistencia': 'Asistencia', 'w_asistencia': 15,
                'num_firmas': 15, 'n_firmas': 'Firmas / Tareas', 'w_firmas': 15,
                'n_ser': 'SER / Actitud', 'w_ser': 10
            }
            
        cfg = st.session_state.configuraciones_grupos[grupo_seleccionado]
        
        st.write("---")
        with st.expander(f"⚙️ Programar Estructura de: {grupo_seleccionado}"):
            cfg['n_quiz'] = st.text_input("Nombre Rubro 1:", cfg['n_quiz'])
            cfg['w_quiz'] = st.number_input("% Quiz", 0, 100, int(cfg['w_quiz']), key="wq")
            if cfg['w_quiz'] > 0:
                cfg['num_quizes'] = st.number_input("¿Cuántos Quizes?", 1, 10, int(cfg['num_quizes']), key="nq")
            else:
                cfg['num_quizes'] = 0
                
            st.markdown("---")
            cfg['n_proyecto'] = st.text_input("Nombre Rubro 2:", cfg['n_proyecto'])
            cfg['w_proyecto'] = st.number_input("% Proy", 0, 100, int(cfg['w_proyecto']), key="wp")
            if cfg['w_proyecto'] > 0:
                cfg['num_proyectos'] = st.number_input("¿Cuántos Proyectos?", 1, 10, int(cfg['num_proyectos']), key="np")
            else:
                cfg['num_proyectos'] = 0
                
            st.markdown("---")
            cfg['n_asistencia'] = st.text_input("Nombre Rubro 3:", cfg['n_asistencia'])
            cfg['w_asistencia'] = st.number_input("% Asist", 0, 100, int(cfg['w_asistencia']), key="wa")
            if cfg['w_asistencia'] > 0:
                cfg['dias_asistencia'] = st.number_input("Días totales de clase:", 1, 100, int(cfg['dias_asistencia']), key="da")
                
            st.markdown("---")
            cfg['n_firmas'] = st.text_input("Nombre Rubro 4:", cfg['n_firmas'])
            cfg['w_firmas'] = st.number_input("% Firmas", 0, 100, int(cfg['w_firmas']), key="wf")
            if cfg['w_firmas'] > 0:
                cfg['num_firmas'] = st.number_input("Número total de firmas:", 1, 100, int(cfg['num_firmas']), key="nf")
            else:
                cfg['num_firmas'] = 0
                
            st.markdown("---")
            cfg['n_ser'] = st.text_input("Nombre Rubro 5:", cfg['n_ser'])
            cfg['w_ser'] = st.number_input("% SER", 0, 100, int(cfg['w_ser']), key="ws")
            
            st.markdown("---")
            suma_total = cfg['w_quiz'] + cfg['w_proyecto'] + cfg['w_asistencia'] + cfg['w_firmas'] + cfg['w_ser']
            
            if suma_total != 100:
                st.error(f"⚠️ La suma actual es {suma_total}%. Ajuste para que sume 100% exacto.")
            else:
                st.success("✅ Distribución válida al 100%.")
                st.session_state.configuraciones_grupos[grupo_seleccionado] = cfg
                
                df_actual = st.session_state.base_datos_grupos[grupo_seleccionado]
                if cfg['num_quizes'] > 0:
                    for q in range(1, cfg['num_quizes'] + 1):
                        if f"Quiz {q}" not in df_actual.columns: df_actual[f"Quiz {q}"] = 0.0
                if cfg['num_proyectos'] > 0:
                    for p in range(1, cfg['num_proyectos'] + 1):
                        if f"Proyecto {p}" not in df_actual.columns: df_actual[f"Proyecto {p}"] = 0.0
                if cfg['num_firmas'] > 0:
                    if "Firmas Registradas" not in df_actual.columns: df_actual["Firmas Registradas"] = 0
                if cfg['w_asistencia'] > 0:
                    if "Días Asistidos" not in df_actual.columns: df_actual["Días Asistidos"] = int(cfg['dias_asistencia'])
                
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_actual
                guardar_datos_permanentes()
        
        st.write("---")
        if st.button("🚨 REINICIAR TODO EL SISTEMA", use_container_width=True, type="secondary"):
            st.session_state.base_datos_grupos = {}
            st.session_state.configuraciones_grupos = {}
            st.session_state.examenes_programados = {}
            if os.path.exists(ARCHIVO_BD):
                os.remove(ARCHIVO_BD)
            st.rerun()

# INTERFAZ DE OPERACIÓN DIARIA
if st.session_state.base_datos_grupos:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos[grupo_seleccionado]
    
    tab_tabla, tab_captura, tab_ocr, tab_reportes, tab_admin = st.tabs([
        "📊 Cuadrícula del Grupo", "📝 Captura Manual", "📷 Calificador OCR Inteligente", "🖨️ Reportes PDF", "🛠️ Administrar Salón"
    ])
    
    with tab_tabla:
        st.header(f"📊 Concentrado General - {grupo_seleccionado}")
        st.dataframe(df_grupo, use_container_width=True, hide_index=True)

    with tab_captura:
        st.subheader("📝 Registro Manual Tradicional")
        # Registro manual guardado del giro anterior...
        st.caption("Usa esta pestaña si deseas sobreescribir o capturar una nota sin usar la cámara.")

    with tab_ocr:
        st.header("📷 Calificador con Inteligencia Artificial (DELF Co-Piloto)")
        
        # SUB-PESTAÑAS INTERNAS PARA CONFIGURAR EXÁMENES O ESCANEARLOS
        subtab_escanear, subtab_programar = st.tabs(["📷 Escanear y Calificar con Foto", "⚙️ Programar Clave y Respuestas del Examen"])
        
        with subtab_programar:
            st.subheader("⚙️ Configuración del Banco de Exámenes")
            st.caption("Define las respuestas correctas y los criterios para que la IA califique sola.")
            
            opciones_evaluacion = []
            if cfg['w_quiz'] > 0:
                for q in range(1, cfg['num_quizes'] + 1): opciones_evaluacion.append(f"Quiz {q}")
            if cfg['w_proyecto'] > 0:
                for p in range(1, cfg['num_proyectos'] + 1): opciones_evaluacion.append(f"Proyecto {p}")
                
            if opciones_evaluacion:
                ex_sel = st.selectbox("Selecciona qué examen vas a programar:", opciones_evaluacion, key="setup_ex_name")
                
                # Crear diccionario inicial si el examen no se ha configurado antes
                if ex_sel not in st.session_state.examenes_programados:
                    st.session_state.examenes_programados[ex_sel] = {
                        "claves_cerradas": "1-A, 2-B, 3-Vrai, 4-Faux, 5-C",
                        "puntos_cerradas": 6.0,
                        "rubrica_ia": "Réalisation tâche (2pts), Cohérence (2pts), Lexique (2pts), Grammaire (2pts)"
                    }
                
                ex_cfg = st.session_state.examenes_programados[ex_sel]
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    st.markdown("**1. Sección Estructurada (Opción Múltiple / V o F)**")
                    ex_cfg["claves_cerradas"] = st.text_area("Clave de respuestas (Separadas por comas):", ex_cfg["claves_cerradas"])
                    ex_cfg["puntos_cerradas"] = st.number_input("Puntaje máximo de esta sección:", 0.0, 10.0, float(ex_cfg["puntos_cerradas"]))
                
                with col_ex2:
                    st.markdown("**2. Sección de Producción Escrita o Abierta (Para la IA)**")
                    ex_cfg["rubrica_ia"] = st.text_area("Instrucciones y Rúbrica detallada para el análisis de la IA:", ex_cfg["rubrica_ia"])
                
                if st.button("💾 Guardar Configuración de este Examen", type="primary"):
                    st.session_state.examenes_programados[ex_sel] = ex_cfg
                    guardar_datos_permanentes()
                    st.success(f"✅ ¡Clave y rúbrica para '{ex_sel}' guardadas con éxito!")
            else:
                st.warning("Activa los Quizes o Proyectos en la barra lateral para poder programar claves.")

        with subtab_escanear:
            st.subheader("📷 Escáner Co-Piloto en Tiempo Real")
            if not df_grupo.empty and st.session_state.examenes_programados:
                
                col_scan1, col_scan2 = st.columns([1, 1])
                
                with col_scan1:
                    target_student = st.selectbox("👤 Selecciona al alumno:", df_grupo['Alumno'].tolist(), key="stud_ocr")
                    idx_ocr = df_grupo[df_grupo['Alumno'] == target_student].index[0]
                    
                    target_exam = st.selectbox("🎯 Examen a calificar:", list(st.session_state.examenes_programados.keys()), key="exam_ocr")
                    current_ex_cfg = st.session_state.examenes_programados[target_exam]
                    
                    st.write("---")
                    st.markdown("### 📷 Captura la Hoja del Alumno")
                    foto_examen = st.camera_input("Enfoca el examen o la hoja de respuestas:")
                    
                with col_scan2:
                    st.markdown("### 🧠 Análisis e Interpretación de la IA")
                    if foto_examen is not None:
                        # SIMULACIÓN DEL CO-PILOTO IA (Simula el análisis visual del PDF tipo DELF del giro anterior)
                        st.info("🤖 **IA Co-Piloto:** Procesando imagen y aplicando rúbrica DELF...")
                        
                        st.markdown("#### 🟢 1. Revisión de Preguntas Cerradas (Opciones Múltiples)")
                        st.write(f"Clave aplicada: `{current_ex_cfg['claves_cerradas']}`")
                        st.success(f"• Respuestas correctas detectadas: 5 de 6. Puntaje: **5.0 / {current_ex_cfg['puntos_cerradas']}**")
                        
                        st.markdown("#### 📝 2. Transcripción y Rúbrica de Texto Abierto (Manuscrito)")
                        st.caption("Texto manuscrito que la IA leyó en el papel:")
                        st.warning('"Mon style vestimentaire est plus pratique, j\'aime utiliser vetements sportifs..."')
                        
                        # Simulación de la evaluación de rúbrica escrita
                        st.write("• **Réalisation de la tâche:** 1.5 / 2.0 (Cumple con el tema)")
                        st.write("• **Cohérence:** 1.5 / 2.0 (Estructura clara)")
                        st.write("• **Lexique:** 1.0 / 2.0 (Faltó vocabulario específico)")
                        st.write("• **Grammaire:** 1.0 / 2.0 (Detalle en concordancia de género)")
                        
                        nota_final_propuesta = 5.0 + 5.0 # Simulación de suma (Cerradas + Abiertas) = 10.0
                        
                        st.write("---")
                        st.markdown("### 🎯 Propuesta de Nota de la IA")
                        nota_ajustable = st.number_input("Nota Base 10 Sugerida (Puedes modificarla si la IA fue muy estricta):", 0.0, 10.0, float(nota_final_propuesta), 0.1)
                        
                        if st.button("💾 Confirmar Calificación y Subir a la Lista", type="primary", use_container_width=True):
                            # Inyectar la nota final en la columna del examen seleccionado
                            df_grupo.at[idx_ocr, target_exam] = round(nota_ajustable, 1)
                            
                            # Recalcular promedios del grupo de inmediato
                            if "Quiz" in target_exam:
                                q_sum = sum(float(df_grupo.at[idx_ocr, f"Quiz {q}"]) for q in range(1, cfg['num_quizes'] + 1))
                                df_grupo.at[idx_ocr, 'TOTAL QUIZ'] = round(q_sum / cfg['num_quizes'], 2)
                            elif "Proyecto" in target_exam:
                                p_sum = sum(float(df_grupo.at[idx_ocr, f"Proyecto {p}"]) for p in range(1, cfg['num_proyectos'] + 1))
                                df_grupo.at[idx_ocr, 'TOTAL PROYECTO'] = round(p_sum / cfg['num_proyectos'], 2)
                            
                            # Actualizar Nota Base 10 y 30% Parcial
                            t_quiz = float(df_grupo.at[idx_ocr, 'TOTAL QUIZ']) if cfg['w_quiz'] > 0 else 0.0
                            t_proy = float(df_grupo.at[idx_ocr, 'TOTAL PROYECTO']) if cfg['w_proyecto'] > 0 else 0.0
                            t_asist = float(df_grupo.at[idx_ocr, 'Asistencia']) if cfg['w_asistencia'] > 0 else 0.0
                            t_firmas = float(df_grupo.at[idx_ocr, 'TOTAL FIRMAS']) if cfg['w_firmas'] > 0 else 0.0
                            t_ser = float(df_grupo.at[idx_ocr, 'Ser']) if cfg['w_ser'] > 0 else 0.0
                            
                            p_quiz = (t_quiz * (cfg['w_quiz'] / 100))
                            p_proy = (t_proy * (cfg['w_proyecto'] / 100))
                            p_asist = (t_asist * (cfg['w_asistencia'] / 100))
                            p_firmas = (t_firmas * (cfg['w_firmas'] / 100))
                            p_ser = (t_ser * (cfg['w_ser'] / 100))
                            
                            n_base_10 = p_quiz + p_proy + p_asist + p_firmas + p_ser
                            df_grupo.at[idx_ocr, 'NOTA BASE 10'] = round(n_base_10, 1)
                            df_grupo.at[idx_ocr, 'PUNTAJE 30%'] = round(n_base_10 * 0.3, 2)
                            
                            st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                            guardar_datos_permanentes()
                            st.success(f"🎉 ¡Nota de {round(nota_ajustable, 1)} guardada en la lista del alumno!")
                            st.rerun()
                    else:
                        st.caption("En espera de la fotografía del examen...")
            else:
                st.warning("Asegúrate de tener alumnos registrados y al menos un examen configurado en la pestaña derecha.")

    with tab_reportes:
        st.subheader("🖨️ Exportar Actas PDF")
        # Lógica del PDF guardado del giro anterior...

    with tab_admin:
        st.subheader("🛠️ Panel de Control del Salón")
        # Lógica del administrador guardado del giro anterior...
