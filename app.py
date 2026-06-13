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

if "examenes_programados" not in st.session_state:
    st.session_state.examenes_programados = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Estructura de Control de Notas Unificada. Doble método de captura seguro.")
st.write("---")

# BARRA LATERAL
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
            'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 30,
            'num_proyectos': 2, 'n_proyecto': 'Proyectos', 'w_proyecto': 30,
            'dias_asistencia': 32, 'n_asistencia': 'Asistencia', 'w_asistencia': 15,
            'num_firmas': 15, 'n_firmas': 'Firmas / Tareas', 'w_firmas': 15,
            'n_ser': 'SER / Actitud', 'w_ser': 10
        })
        
        st.write("---")
        with st.expander(f"⚙️ Programar Estructura de: {grupo_seleccionado}"):
            cfg['n_quiz'] = st.text_input("Nombre Rubro 1:", cfg.get('n_quiz', 'Quizes'))
            cfg['w_quiz'] = st.number_input("% Quiz", 0, 100, int(cfg.get('w_quiz', 30)), key="wq")
            cfg['num_quizes'] = st.number_input("¿Cuántos Quizes?", 0, 10, int(cfg.get('num_quizes', 4)), key="nq") if cfg['w_quiz'] > 0 else 0
                
            st.markdown("---")
            cfg['n_proyecto'] = st.text_input("Nombre Rubro 2:", cfg.get('n_proyecto', 'Proyectos'))
            cfg['w_proyecto'] = st.number_input("% Proy", 0, 100, int(cfg.get('w_proyecto', 30)), key="wp")
            cfg['num_proyectos'] = st.number_input("¿Cuántos Proyectos?", 0, 10, int(cfg.get('num_proyectos', 2)), key="np") if cfg['w_proyecto'] > 0 else 0
                
            st.markdown("---")
            cfg['n_asistencia'] = st.text_input("Nombre Rubro 3:", cfg.get('n_asistencia', 'Asistencia'))
            cfg['w_asistencia'] = st.number_input("% Asist", 0, 100, int(cfg.get('w_asistencia', 15)), key="wa")
            if cfg['w_asistencia'] > 0:
                cfg['dias_asistencia'] = st.number_input("Días totales de clase:", 1, 100, int(cfg.get('dias_asistencia', 32)), key="da")
                
            st.markdown("---")
            cfg['n_firmas'] = st.text_input("Nombre Rubro 4:", cfg.get('n_firmas', 'Firmas / Tareas'))
            cfg['w_firmas'] = st.number_input("% Firmas", 0, 100, int(cfg.get('w_firmas', 15)), key="wf")
            cfg['num_firmas'] = st.number_input("Número total de firmas:", 0, 100, int(cfg.get('num_firmas', 15)), key="nf") if cfg['w_firmas'] > 0 else 0
                
            st.markdown("---")
            cfg['n_ser'] = st.text_input("Nombre Rubro 5:", cfg.get('n_ser', 'SER / Actitud'))
            cfg['w_ser'] = st.number_input("% SER", 0, 100, int(cfg.get('w_ser', 10)), key="ws")
            
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
                if cfg['w_firmas'] > 0 and "Firmas Registradas" not in df_actual.columns:
                    df_actual["Firmas Registradas"] = int(cfg['num_firmas'])
                if cfg['w_asistencia'] > 0 and "Días Asistidos" not in df_actual.columns:
                    df_actual["Días Asistidos"] = int(cfg['dias_asistencia'])
                
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_actual
                guardar_datos_permanentes()

# VISTA DE CARGA INICIAL
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga Inicial de Listas (Detección Multigrupo)")
    texto_pegado = st.text_area("📋 Pega aquí todo el contenido de tus listas de la UNAQ:", height=300)
    
    if st.button("✨ Procesar, Separar y Crear Grupos", type="primary", use_container_width=True):
        if texto_pegado.strip() != "":
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
                
                if any(b in linea_limpia.lower() for b in ["universidad", "aeronáutica", "lista", "matricula", "nombre", "oscar"]): continue
                
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
            guardar_datos_permanentes()
            st.rerun()

else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
        'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 30,
        'num_proyectos': 2, 'n_proyecto': 'Proyectos', 'w_proyecto': 30,
        'dias_asistencia': 32, 'n_asistencia': 'Asistencia', 'w_asistencia': 15,
        'num_firmas': 15, 'n_firmas': 'Firmas / Tareas', 'w_firmas': 15,
        'n_ser': 'SER / Actitud', 'w_ser': 10
    })
    
    tab_tabla, tab_captura_manual, tab_calificador_ocr, tab_reportes, tab_admin = st.tabs([
        "📊 Cuadrícula General", "📝 Método 1: Captura Tradicional Celda por Celda", "📷 Método 2: Calificador Rápido / OCR", "🖨️ Reportes PDF", "🛠️ Administrar Salón"
    ])
    
    with tab_tabla:
        st.header(f"📊 Concentrado General - {grupo_seleccionado}")
        cols_mostrar = ['Alumno']
        if cfg.get('w_quiz', 30) > 0:
            for q in range(1, cfg.get('num_quizes', 4) + 1): cols_mostrar.append(f"Quiz {q}")
            cols_mostrar.append('TOTAL QUIZ')
        if cfg.get('w_proyecto', 30) > 0:
            for p in range(1, cfg.get('num_proyectos', 2) + 1): cols_mostrar.append(f"Proyecto {p}")
            cols_mostrar.append('TOTAL PROYECTO')
        if cfg.get('w_asistencia', 15) > 0: cols_mostrar.extend(['Días Asistidos', 'Asistencia'])
        if cfg.get('w_firmas', 15) > 0: cols_mostrar.extend(['Firmas Registradas', 'TOTAL FIRMAS'])
        if cfg.get('w_ser', 10) > 0: cols_mostrar.append('Ser')
        cols_mostrar.extend(['NOTA BASE 10', 'PUNTAJE 30%'])
        
        cols_finales = [c for c in cols_mostrar if c in df_grupo.columns]
        st.dataframe(df_grupo[cols_finales], use_container_width=True, hide_index=True)

    with tab_captura_manual:
        st.subheader("📝 Captura e Inyección Tradicional de Notas")
        if not df_grupo.empty:
            alumno_manual = st.selectbox("👤 Selecciona al alumno:", df_grupo['Alumno'].tolist(), key="al_man")
            idx_m = df_grupo[df_grupo['Alumno'] == alumno_manual].index[0]
            
            col1, col2, col3 = st.columns(3)
            valores_q = []
            with col1:
                if cfg.get('w_quiz', 0) > 0:
                    st.markdown(f"### 📝 {cfg.get('n_quiz', 'Quizes')}")
                    for q in range(1, cfg.get('num_quizes', 4) + 1):
                        col_n = f"Quiz {q}"
                        v_def = float(df_grupo.at[idx_m, col_n]) if col_n in df_grupo.columns else 0.0
                        valores_q.append((col_n, st.number_input(f"{col_n} (0-10)", 0.0, 10.0, v_def, key=f"mq_{q}")))
            
            valores_p = []
            with col2:
                if cfg.get('w_proyecto', 0) > 0:
                    st.markdown(f"### 🏗️ {cfg.get('n_proyecto', 'Proyectos')}")
                    for p in range(1, cfg.get('num_proyectos', 2) + 1):
                        col_n = f"Proyecto {p}"
                        v_def = float(df_grupo.at[idx_m, col_n]) if col_n in df_grupo.columns else 0.0
                        valores_p.append((col_n, st.number_input(f"{col_n} (0-10)", 0.0, 10.0, v_def, key=f"mp_{p}")))
            
            with col3:
                st.markdown("### 📋 Asistencia, Firmas y Rasgos")
                d_asist = st.number_input("Días asistidos:", 0, int(cfg.get('dias_asistencia', 32)), int(df_grupo.at[idx_m, 'Días Asistidos'])) if cfg.get('w_asistencia', 0) > 0 else 32
                f_regist = st.number_input("Firmas obtenidas:", 0, int(cfg.get('num_firmas', 15)), int(df_grupo.at[idx_m, 'Firmas Registradas'])) if cfg.get('w_firmas', 0) > 0 else 15
                v_ser = st.number_input("Nota SER:", 0.0, 10.0, float(df_grupo.at[idx_m, 'Ser'])) if cfg.get('w_ser', 0) > 0 else 0.0
                
            if st.button("💾 Guardar Cambios Tradicionales", type="primary", use_container_width=True):
                for col_n, val in valores_q: df_grupo.at[idx_m, col_n] = val
                for col_n, val in valores_p: df_grupo.at[idx_m, col_n] = val
                
                t_q = (sum(v for _, v in valores_q) / cfg.get('num_quizes', 4)) if valores_q else 0.0
                t_p = (sum(v for _, v in valores_p) / cfg.get('num_proyectos', 2)) if valores_p else 0.0
                
                df_grupo.at[idx_m, 'TOTAL QUIZ'] = round(t_q, 2)
                df_grupo.at[idx_m, 'TOTAL PROYECTO'] = round(t_p, 2)
                df_grupo.at[idx_m, 'Días Asistidos'] = d_asist
                df_grupo.at[idx_m, 'Asistencia'] = round((d_asist / cfg.get('dias_asistencia', 32)) * 10.0, 2)
                df_grupo.at[idx_m, 'Firmas Registradas'] = f_regist
                df_grupo.at[idx_m, 'TOTAL FIRMAS'] = round((f_regist / cfg.get('num_firmas', 15)) * 10.0, 2)
                df_grupo.at[idx_m, 'Ser'] = v_ser
                
                n_b10 = (t_q * (cfg.get('w_quiz', 0)/100)) + (t_p * (cfg.get('w_proyecto', 0)/100)) + (df_grupo.at[idx_m, 'Asistencia'] * (cfg.get('w_asistencia', 0)/100)) + (df_grupo.at[idx_m, 'TOTAL FIRMAS'] * (cfg.get('w_firmas', 0)/100)) + (v_ser * (cfg.get('w_ser', 0)/100))
                df_grupo.at[idx_m, 'NOTA BASE 10'] = round(n_b10, 1)
                df_grupo.at[idx_m, 'PUNTAJE 30%'] = round(n_b10 * 0.3, 2)
                
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                guardar_datos_permanentes()
                st.success("🎉 Datos guardados tradicionalmente.")
                st.rerun()

    with tab_calificador_ocr:
        st.header("📷 Método 2: Asistente de Rúbricas e Integración OCR")
        sub_c1, sub_c2 = st.tabs(["📷 Procesar Evaluación con Foto / Prompt", "⚙️ Configurar Parámetros del Examen"])
        
        with sub_c2:
            opciones_ev = [f"Quiz {q}" for q in range(1, cfg.get('num_quizes', 4) + 1)] + [f"Proyecto {p}" for p in range(1, cfg.get('num_proyectos', 2) + 1)]
            if opciones_ev:
                ex_sel = st.selectbox("Selecciona la evaluación a parametrizar:", opciones_ev)
                
                # Inicialización defensiva para evitar KeyError de claves anteriores
                if ex_sel not in st.session_state.examenes_programados:
                    st.session_state.examenes_programados[ex_sel] = {"claves": "1-F, 2-D, 3-B", "max_c": 6.0, "rubrica": "Criterios"}
                
                # Uso del método seguro .get() para que nunca vuelva a tronar la app
                txt_claves = st.session_state.examenes_programados[ex_sel].get("claves", "1-F, 2-D, 3-B")
                val_max_c = float(st.session_state.examenes_programados[ex_sel].get("max_c", 6.0))
                txt_rubrica = st.session_state.examenes_programados[ex_sel].get("rubrica", "Criterios")
                
                st.session_state.examenes_programados[ex_sel]["claves"] = st.text_area("Clave de respuestas cerradas:", txt_claves)
                st.session_state.examenes_programados[ex_sel]["max_c"] = st.number_input("Puntaje máximo sección cerrada:", 0.0, 10.0, val_max_c)
                st.session_state.examenes_programados[ex_sel]["rubrica"] = st.text_area("Descripción de Rúbrica Abierta:", txt_rubrica)
                
                if st.button("¼️ Guardar Configuración del Examen"):
                    guardar_datos_permanentes()
                    st.success("✅ Examen parametrizado con éxito de forma segura.")
            else:
                st.caption("No hay Quizes o Proyectos programados en la barra lateral.")

        with sub_c1:
            if not df_grupo.empty and st.session_state.examenes_programados:
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    al_ocr = st.selectbox("Alumno a evaluar con Asistente:", df_grupo['Alumno'].tolist())
                    idx_o = df_grupo[df_grupo['Alumno'] == al_ocr].index[0]
                    ex_ocr = st.selectbox("Destino de la nota generada:", list(st.session_state.examenes_programados.keys()))
                    
                    st.markdown("### 📊 Calculadora de Rasgos Directa (DELF)")
                    pts_c = st.number_input("Aciertos de Comprensión Oral/Escrita (Max 20):", 0, 20, 16)
                    r1 = st.slider("Réalisation de la tâche (Max 3.0):", 0.0, 3.0, 2.0, 0.5)
                    r2 = st.slider("Cohérence et cohésion (Max 2.0):", 0.0, 2.0, 1.5, 0.5)
                    r3 = st.slider("Lexique (Max 2.0):", 0.0, 2.0, 1.5, 0.5)
                    r4 = st.slider("Morphosyntaxe (Max 3.0):", 0.0, 3.0, 2.0, 0.5)
                    
                    p_totales = pts_c + r1 + r2 + r3 + r4 
                    nota_c_10 = (p_totales / 30.0) * 10.0
                    st.metric("Nota Calculada (Base 10)", f"{round(nota_c_10, 1)} / 10")
                    
                with col_o2:
                    st.markdown("### 📷 Captura Co-Piloto")
                    f_cam = st.camera_input("Enfoca el examen del alumno:")
                    if f_cam: st.success("Imagen cargada en el búfer de visión artificial.")
                    
                    if st.button("💾 Validar e Inyectar Nota del Asistente", type="primary", use_container_width=True):
                        df_grupo.at[idx_o, ex_ocr] = round(nota_c_10, 1)
                        
                        if "Quiz" in ex_ocr:
                            q_sum = sum(float(df_grupo.at[idx_o, f"Quiz {q}"]) for q in range(1, cfg.get('num_quizes', 4) + 1))
                            df_grupo.at[idx_o, 'TOTAL QUIZ'] = round(q_sum / cfg.get('num_quizes', 4), 2)
                        elif "Proyecto" in ex_ocr:
                            p_sum = sum(float(df_grupo.at[idx_o, f"Proyecto {p}"]) for p in range(1, cfg.get('num_proyectos', 2) + 1))
                            df_grupo.at[idx_o, 'TOTAL PROYECTO'] = round(p_sum / cfg.get('num_proyectos', 2), 2)
                        
                        t_q = float(df_grupo.at[idx_o, 'TOTAL QUIZ'])
                        t_p = float(df_grupo.at[idx_o, 'TOTAL PROYECTO'])
                        t_as = float(df_grupo.at[idx_o, 'Asistencia'])
                        t_fi = float(df_grupo.at[idx_o, 'TOTAL FIRMAS'])
                        t_se = float(df_grupo.at[idx_o, 'Ser'])
                        
                        n_b10 = (t_q * (cfg.get('w_quiz', 0)/100)) + (t_p * (cfg.get('w_proyecto', 0)/100)) + (t_as * (cfg.get('w_asistencia', 0)/100)) + (t_fi * (cfg.get('w_firmas', 0)/100)) + (t_se * (cfg.get('w_ser', 0)/100))
                        df_grupo.at[idx_o, 'NOTA BASE 10'] = round(n_b10, 1)
                        df_grupo.at[idx_o, 'PUNTAJE 30%'] = round(n_b10 * 0.3, 2)
                        
                        st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                        guardar_datos_permanentes()
                        st.success("🎉 Nota del asistente inyectada con éxito.")
                        st.rerun()

    with tab_reportes:
        st.subheader("🖨️ Exportar Actas PDF")
        def generar_pdf_grupo(df, g_name, cuatri, c):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, leading=18, textColor=colors.HexColor("#0B3C5D"), alignment=1)
            meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=12, alignment=1)
            story.append(Paragraph(f"UNIVERSIDAD AERONÁUTICA EN QUERÉTARO", title_style))
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"ACTA DE EVALUACIÓN CONTINUA (30%) - GRUPO: {g_name} | {cuatri}", meta_style))
            story.append(Spacer(1, 15))
            
            headers = ["Alumno"]
            if c.get('w_quiz', 0) > 0: headers.append(c.get('n_quiz', 'Quiz')[:6])
            if c.get('w_proyecto', 0) > 0: headers.append(c.get('n_proyecto', 'Proy')[:6])
            if c.get('w_asistencia', 0) > 0: headers.append("Asist.")
            if c.get('w_firmas', 0) > 0: headers.append("Firmas")
            headers.extend(["Nota /10", "Puntaje (30%)"])
            
            data = [headers]
            for _, row in df.iterrows():
                fila = [row['Alumno'][:20]]
                if c.get('w_quiz', 0) > 0: fila.append(str(row['TOTAL QUIZ']))
                if c.get('w_proyecto', 0) > 0: fila.append(str(row['TOTAL PROYECTO']))
                if c.get('w_asistencia', 0) > 0: fila.append(str(row['Asistencia']))
                if c.get('w_firmas', 0) > 0: fila.append(str(row['TOTAL FIRMAS']))
                fila.extend([str(row['NOTA BASE 10']), str(row['PUNTAJE 30%'])])
                data.append(fila)
                
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F7FA")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8)
            ]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        if not df_grupo.empty:
            pdf_data = generar_pdf_grupo(df_grupo, grupo_seleccionado, cuatrimestre, cfg)
            st.download_button(label=f"📥 DESCARGAR REPORTE AL 30% EN PDF", data=pdf_data, file_name=f"Acta_30_{grupo_seleccionado}.pdf", mime="application/pdf", use_container_width=True)

    with tab_admin:
        st.header("🛠️ Panel de Control - Administrar Salón")
        
        st.subheader("📂 1. Crear Nuevo Grupo Manualmente")
        nombre_grupo_nuevo = st.text_input("Nombre del Nuevo Grupo (Ej: IDMA A1.4):", key="txt_add_manual_g").strip().upper()
        
        if st.button("💾 Crear Grupo Vacío", key="btn_add_manual_g"):
            if nombre_grupo_nuevo == "":
                st.error("⚠️ Especifica un identificador de grupo no vacío.")
            elif nombre_grupo_nuevo in st.session_state.base_datos_grupos:
                st.warning("⚠️ Este grupo ya existe en la base de datos.")
            else:
                df_nuevo_g = pd.DataFrame(columns=['Alumno', 'TOTAL QUIZ', 'TOTAL PROYECTO', 'TOTAL FIRMAS', 'Asistencia', 'Ser', 'NOTA BASE 10', 'PUNTAJE 30%'])
                st.session_state.base_datos_grupos[nombre_grupo_nuevo] = df_nuevo_g
                st.session_state.configuraciones_grupos[nombre_grupo_nuevo] = {
                    'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 30,
                    'num_proyectos': 2, 'n_proyecto': 'Proyectos', 'w_proyecto': 30,
                    'dias_asistencia': 32, 'n_asistencia': 'Asistencia', 'w_asistencia': 15,
                    'num_firmas': 15, 'n_firmas': 'Firmas / Tareas', 'w_firmas': 15,
                    'n_ser': 'SER / Actitud', 'w_ser': 10
                }
                guardar_datos_permanentes()
                st.success(f"🎉 ¡El grupo {nombre_grupo_nuevo} fue creado!")
                st.rerun()
        
        st.write("---")
        st.subheader(f"➕ 2. Registrar Alumno en el Grupo {grupo_seleccionado}")
        nombre_nuevo_alumno = st.text_input("Escriba los apellidos y nombres completos del nuevo estudiante:", key=f"add_manual_al_{grupo_seleccionado}")
        
        if st.button("➕ Añadir Alumno", key=f"btn_add_manual_{grupo_seleccionado}"):
            nombre_limpio = nombre_nuevo_alumno.strip().upper()
            if nombre_limpio == "":
                st.error("⚠️ Por favor escribe un nombre válido antes de guardar.")
            elif not df_grupo.empty and nombre_limpio in df_grupo['Alumno'].tolist():
                st.warning("⚠️ Este alumno ya se encuentra registrado.")
            else:
                nueva_fila = {}
                for col in df_grupo.columns:
                    if col == 'Alumno': nueva_fila[col] = nombre_limpio
                    elif 'Días Asistidos' in col: nueva_fila[col] = int(cfg.get('dias_asistencia', 32))
                    elif 'Firmas Registradas' in col: nueva_fila[col] = int(cfg.get('num_firmas', 15))
                    elif col in ['Asistencia', 'TOTAL FIRMAS']: nueva_fila[col] = 10.0
                    else: nueva_fila[col] = 0.0
                
                df_nuevo_registro = pd.DataFrame([nueva_fila])
                st.session_state.base_datos_grupos[grupo_seleccionado] = pd.concat([df_grupo, df_nuevo_registro]).sort_values(by="Alumno").reset_index(drop=True)
                guardar_datos_permanentes()
                st.success(f"🎉 ¡{nombre_limpio} fue agregado con éxito!")
                st.rerun()

        st.write("---")
        st.subheader(f"🗑️ 3. Eliminar Alumno Definitivamente de {grupo_seleccionado}")
        if not df_grupo.empty:
            alumno_a_eliminar = st.selectbox("Selecciona al alumno que deseas dar de baja:", df_grupo['Alumno'].tolist(), key=f"sel_del_al_{grupo_seleccionado}")
            if st.button("🗑️ Confirmar Baja Definitiva", key=f"btn_del_al_{grupo_seleccionado}", type="primary"):
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo[df_grupo['Alumno'] != alumno_a_eliminar].reset_index(drop=True)
                guardar_datos_permanentes()
                st.success(f"💥 {alumno_a_eliminar} ha sido eliminado.")
                st.rerun()

        st.write("---")
        st.subheader("✏️ 4. Cambiar Nombre a este Grupo")
        nuevo_nombre_grupo = st.text_input("Escriba el nuevo nombre:", grupo_seleccionado, key=f"txt_gname_{grupo_seleccionado}")
        if st.button("💾 Guardar Nuevo Nombre del Grupo", key=f"btn_gname_{grupo_seleccionado}"):
            nuevo_nombre_grupo = nuevo_nombre_grupo.strip().upper()
            if nuevo_nombre_grupo != "" and nuevo_nombre_grupo != grupo_seleccionado:
                st.session_state.base_datos_grupos[nuevo_nombre_grupo] = st.session_state.base_datos_grupos.pop(grupo_seleccionado)
                if grupo_seleccionado in st.session_state.configuraciones_grupos:
                    st.session_state.configuraciones_grupos[nuevo_nombre_grupo] = st.session_state.configuraciones_grupos.pop(grupo_seleccionado)
                guardar_datos_permanentes()
                st.success("¡Grupo renombrado!")
                st.rerun()

        st.write("---")
        st.subheader("👤 5. Corregir Nombre de un Alumno de este Grupo")
        if not df_grupo.empty:
            alumno_a_editar = st.selectbox("Seleccione al alumno con error:", df_grupo['Alumno'].tolist(), key=f"sel_ed_al_{grupo_seleccionado}")
            nuevo_nombre_alumno = st.text_input("Corrija el nombre:", alumno_a_editar, key=f"txt_ed_al_{grupo_seleccionado}").strip().upper()
            if st.button("💾 Guardar Corrección del Nombre", key=f"btn_ed_al_{grupo_seleccionado}"):
                if nuevo_nombre_alumno != "":
                    idx_al = df_grupo[df_grupo['Alumno'] == alumno_a_editar].index[0]
                    df_grupo.at[idx_al, 'Alumno'] = nuevo_nombre_alumno
                    st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo.sort_values(by="Alumno").reset_index(drop=True)
                    guardar_datos_permanentes()
                    st.success("¡Nombre corregido!")
                    st.rerun()

        st.write("---")
        st.subheader("🏃 6. Mover Alumno de este Grupo a Otro Salón")
        if not df_grupo.empty:
            alumno_a_mover = st.selectbox("Seleccione al alumno a transferir:", df_grupo['Alumno'].tolist(), key=f"mover_al_{grupo_seleccionado}")
            lista_destinos = [g for g in list(st.session_state.base_datos_grupos.keys()) if g != grupo_seleccionado]
            if lista_destinos:
                grupo_destino = st.selectbox("Seleccione el grupo destino:", lista_destinos, key=f"sel_dest_{grupo_seleccionado}")
                if st.button("🔀 Confirmar Transferencia", key=f"btn_mov_{grupo_seleccionado}"):
                    fila_alumno = df_grupo[df_grupo['Alumno'] == alumno_a_mover]
                    st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo[df_grupo['Alumno'] != alumno_a_mover]
                    df_destino = st.session_state.base_datos_grupos[grupo_destino]
                    st.session_state.base_datos_grupos[grupo_destino] = pd.concat([df_destino, fila_alumno]).sort_values(by="Alumno").reset_index(drop=True)
                    guardar_datos_permanentes()
                    st.success("¡Alumno transferido exitosamente!")
                    st.rerun()
