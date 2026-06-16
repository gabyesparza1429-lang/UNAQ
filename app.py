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

# Configuración de la interfaz de usuario de Streamlit
st.set_page_config(page_title="GEM UNAQ - Control de Notas de Francés", layout="wide")

# Archivo de persistencia de datos local en el servidor
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
            
            if isinstance(datos_importados, dict) and "grupos" in datos_importados:
                st.session_state.examenes_programados = datos_importados.get("examenes_programados", {})
                st.session_state.configuraciones_grupos = datos_importados.get("configuraciones_grupos", {})
                bloque_grupos = datos_importados.get("grupos", {})
            else:
                bloque_grupos = datos_importados if isinstance(datos_importados, dict) else {}
                st.session_state.examenes_programados = {}
                st.session_state.configuraciones_grupos = {}
            
            diccionario_final = {}
            for grupo, lista_filas in bloque_grupos.items():
                df = pd.DataFrame(lista_filas)
                columnas_obligatorias = ['Matrícula', 'Alumno', 'Plan', 'TOTAL QUIZ', 'TOTAL PROYECTO', 'TOTAL FIRMAS', 'Asistencia', 'Ser', 'NOTA BASE 10', 'PUNTAJE 30%']
                for col in columnas_obligatorias:
                    if col not in df.columns:
                        df[col] = 0.0 if col not in ['Matrícula', 'Alumno', 'Plan'] else ''
                diccionario_final[grupo] = df
            return diccionario_final
        except:
            return {}
    return {}

# Inicialización segura del estado de la sesión
if "examenes_programados" not in st.session_state:
    st.session_state.examenes_programados = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Estructura de Control de Notas de Francés - Clasificación por Carrera y Nivel Adaptado.")
st.write("---")

# BARRA LATERAL
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    if st.session_state.base_datos_grupos:
        lista_de_grupos = sorted(list(st.session_state.base_datos_grupos.keys()))
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
            'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 30,
            'num_proyectos': 2, 'n_proyecto': 'Proyectos', 'w_proyecto': 30,
            'dias_asistencia': 32, 'n_asistencia': 'Asistencia', 'w_asistencia': 15,
            'num_firmas': 15, 'n_firmas': 'Firmas / Tareas', 'w_firmas': 15,
            'n_ser': 'SER / Actitud', 'w_ser': 10
        })
        
        st.write("---")
        with st.expander("⚙️ Ajustar Ponderaciones"):
            cfg['w_quiz'] = st.number_input("% Quizes", 0, 100, int(cfg.get('w_quiz', 30)))
            cfg['num_quizes'] = st.number_input("¿Cuántos Quizes?", 1, 10, int(cfg.get('num_quizes', 4))) if cfg['w_quiz'] > 0 else 0
            cfg['w_proyecto'] = st.number_input("% Proyectos", 0, 100, int(cfg.get('w_proyecto', 30)))
            cfg['num_proyectos'] = st.number_input("¿Cuántos Proyectos?", 1, 10, int(cfg.get('num_proyectos', 2))) if cfg['w_proyecto'] > 0 else 0
            cfg['w_asistencia'] = st.number_input("% Asistencia", 0, 100, int(cfg.get('w_asistencia', 15)))
            cfg['w_firmas'] = st.number_input("% Firmas", 0, 100, int(cfg.get('w_firmas', 15)))
            cfg['w_ser'] = st.number_input("% SER (Actitud)", 0, 100, int(cfg.get('w_ser', 10)))
            
            suma = cfg['w_quiz'] + cfg['w_proyecto'] + cfg['w_asistencia'] + cfg['w_firmas'] + cfg['w_ser']
            if suma == 100:
                st.session_state.configuraciones_grupos[grupo_seleccionado] = cfg
                guardar_datos_permanentes()
            else:
                st.error(f"La suma actual es {suma}%. Debe ser 100% exacto.")

# CARGA INICIAL: PARSEADOR DE TEXTO PARA GRUPOS DE FRANCÉS (Ej: IDMAA1.4)
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga de Listas Institucionales de Francés")
    st.write("Pega el texto crudo de Servicios Escolares. El sistema estructurará los grupos bajo el formato Carrera + Nivel.")
    
    texto_pegado = st.text_area("Entrada de texto de las listas:", height=300)
    
    if st.button("✨ Procesar y Estructurar Grupos de Francés", type="primary", use_container_width=True):
        if texto_pegado.strip():
            # Unir cortes de línea físicos en los códigos institucionales
            texto_normalizado = re.sub(r'(\d+MA-[^\n]*)-\n\s*', r'\1-', texto_pegado)
            lineas = [l.strip() for l in texto_normalizado.split('\n') if l.strip()]
            
            diccionario_grupos = {}
            carrera_detectada = "CARRERA"
            nivel_detectado = "A1.4"
            
            i = 0
            while i < len(lineas):
                linea = lineas[i]
                
                # A. Analizar líneas de código institucional para extraer Carrera y Nivel de Idioma
                if "26MA-" in linea or "FR-" in linea or "FRNA" in linea:
                    # Extraer Carrera (ej: IDMA, IAM, IECSA)
                    match_carrera = re.search(r'\b(IAM|IDMA|IECSA)\b', linea, re.IGNORECASE)
                    if match_carrera:
                        carrera_detectada = match_carrera.group(1).upper()
                    
                    # Extraer Nivel (ej: transforma A1.40 o A2.20 en A1.4 o A2.2)
                    match_nivel = re.search(r'FR-?A?(\d)\.(\d)', linea, re.IGNORECASE)
                    if not match_nivel:
                        match_nivel = re.search(r'FRN-?A?(\d)\.(\d)', linea, re.IGNORECASE)
                    
                    if match_nivel:
                        nivel_detectado = f"A{match_nivel.group(1)}.{match_nivel.group(2)}"
                    
                    # Formar identificador de grupo exacto solicitado: Carrera + Nivel
                    grupo_actual = f"{carrera_detectada}{nivel_detectado}"
                    if grupo_actual not in diccionario_grupos:
                        diccionario_grupos[grupo_actual] = []
                
                # B. Parsear filas de Alumnos
                match_alumno = re.match(r'^(\d+)\s+(\d{4,6})\s+(.+)$', linea)
                if match_alumno:
                    matricula = match_alumno.group(2)
                    resto = match_alumno.group(3)
                    
                    # Extraer Plan de Estudios al final de la línea
                    match_plan = re.search(r'\s+([A-Z\d]{4,10})$', resto)
                    if match_plan:
                        plan = match_plan.group(1)
                        nombre = resto[:match_plan.start()].strip()
                    else:
                        nombre = resto
                        plan = "UNAQ"
                        # Soporte para nombres divididos en el renglón inferior
                        if i + 1 < len(lineas):
                            linea_sig = lineas[i + 1]
                            if not re.match(r'^\d+', linea_sig) and "DEPARTAMENTO" not in linea_sig and "INGLES" not in linea_sig:
                                i += 1
                                match_plan_sig = re.search(r'\s+([A-Z\d]{4,10})$', linea_sig)
                                if match_plan_sig:
                                    plan = match_plan_sig.group(1)
                                    nombre = f"{nombre} {linea_sig[:match_plan_sig.start()].strip()}"
                                else:
                                    nombre = f"{nombre} {linea_sig}"
                    
                    nombre_limpio = re.sub(r'\s+', ' ', nombre).replace("PLAN ESTUDIOS", "").strip().upper()
                    
                    # Seguridad por si no se ha inicializado una cabecera
                    grupo_verificado = f"{carrera_detectada}{nivel_detectado}"
                    if grupo_verificado not in diccionario_grupos:
                        diccionario_grupos[grupo_verificado] = []
                        
                    diccionario_grupos[grupo_verificado].append({
                        "Matrícula": matricula,
                        "Alumno": nombre_limpio,
                        "Plan": plan
                    })
                i += 1
            
            # Crear matrices DataFrames con columnas en blanco para el calificador
            for grupo, alumnos in diccionario_grupos.items():
                if alumnos:
                    df_init = pd.DataFrame(alumnos)
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

# INTERFAZ DE TRABAJO ACTIVA
else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    
    st.success(f"📋 Grupo de Francés activo: {grupo_seleccionado}")
    
    # Respaldo local preventivo anticandados
    csv_buffer = io.StringIO()
    df_grupo.to_csv(csv_buffer, index=False)
    st.download_button(
        label="💾 DESCARGAR RESPALDO LOCAL DE ESTE GRUPO (.CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"Respaldo_{grupo_seleccionado}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    tab_tabla, tab_captura, tab_delf, tab_pdf, tab_admin = st.tabs([
        "📊 Cuadrícula General", "📝 Captura Rápida", "📷 Asistente de Rúbricas DELF", "🖨️ Exportar Acta PDF", "🛠️ Administrar Salón"
    ])
    
    with tab_tabla:
        st.subheader("Concentrado General de Evaluaciones")
        st.dataframe(df_grupo, use_container_width=True, hide_index=True)
        
    with tab_captura:
        st.subheader("📝 Formulario de Registro")
        alumno_sel = st.selectbox("👤 Selecciona al Estudiante:", df_grupo['Alumno'].tolist())
        idx = df_grupo[df_grupo['Alumno'] == alumno_sel].index[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"### 📝 {cfg.get('n_quiz', 'Quizes')}")
            q1 = st.number_input("Quiz 1:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 1"]), key="q1")
            q2 = st.number_input("Quiz 2:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 2"]), key="q2")
            q3 = st.number_input("Quiz 3:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 3"]), key="q3")
            q4 = st.number_input("Quiz 4:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 4"]), key="q4")
        with c2:
            st.markdown(f"### 🏗️ {cfg.get('n_proyecto', 'Proyectos')}")
            p1 = st.number_input("Proyecto 1:", 0.0, 10.0, float(df_grupo.at[idx, "Proyecto 1"]), key="p1")
            p2 = st.number_input("Proyecto 2:", 0.0, 10.0, float(df_grupo.at[idx, "Proyecto 2"]), key="p2")
        with c3:
            st.markdown("### 📋 Parámetros de Control")
            d_asist = st.number_input("Días Asistidos (Máx 32):", 0, 32, int(df_grupo.at[idx, "Días Asistidos"]), key="da")
            f_firmas = st.number_input("Firmas Obtenidas (Máx 15):", 0, 15, int(df_grupo.at[idx, "Firmas Registradas"]), key="fr")
            v_ser = st.number_input("Nota SER (Actitud):", 0.0, 10.0, float(df_grupo.at[idx, "Ser"]), key="sr")
            
        if st.button("💾 Guardar y Calcular Calificaciones", type="primary", use_container_width=True):
            df_grupo.at[idx, "Quiz 1"] = q1
            df_grupo.at[idx, "Quiz 2"] = q2
            df_grupo.at[idx, "Quiz 3"] = q3
            df_grupo.at[idx, "Quiz 4"] = q4
            df_grupo.at[idx, "Proyecto 1"] = p1
            df_grupo.at[idx, "Proyecto 2"] = p2
            df_grupo.at[idx, "Días Asistidos"] = d_asist
            df_grupo.at[idx, "Firmas Registradas"] = f_firmas
            df_grupo.at[idx, "Ser"] = v_ser
            
            t_q = round((q1 + q2 + q3 + q4) / 4.0, 2)
            t_p = round((p1 + p2) / 2.0, 2)
            t_as = round((d_asist / 32.0) * 10.0, 2)
            t_fi = round((f_firmas / 15.0) * 10.0, 2)
            
            df_grupo.at[idx, "TOTAL QUIZ"] = t_q
            df_grupo.at[idx, "TOTAL PROYECTO"] = t_p
            df_grupo.at[idx, "Asistencia"] = t_as
            df_grupo.at[idx, "TOTAL FIRMAS"] = t_fi
            
            nota_b10 = (t_q * (cfg['w_quiz']/100)) + (t_p * (cfg['w_proyecto']/100)) + (t_as * (cfg['w_asistencia']/100)) + (t_fi * (cfg['w_firmas']/100)) + (v_ser * (cfg['w_ser']/100))
            df_grupo.at[idx, "NOTA BASE 10"] = round(nota_b10, 1)
            df_grupo.at[idx, "PUNTAJE 30%"] = round(nota_b10 * 0.3, 2)
            
            st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
            guardar_datos_permanentes()
            st.success(f"🎉 Calificaciones recalculadas para {alumno_sel}.")
            st.rerun()

    with tab_delf:
        st.subheader("📷 Co-Piloto de Rúbricas Oficiales DELF")
        al_ocr = st.selectbox("Alumno para evaluar:", df_grupo['Alumno'].tolist(), key="delf_al")
        idx_o = df_grupo[df_grupo['Alumno'] == al_ocr].index[0]
        ex_ocr = st.selectbox("Asignar evaluación a:", ["Quiz 1", "Quiz 2", "Quiz 3", "Quiz 4", "Proyecto 1", "Proyecto 2"])
        
        co1, co2 = st.columns(2)
        with co1:
            comp = st.number_input("Aciertos Grilla Comprensión (Máx 20):", 0, 20, 15)
            r1 = st.slider("Réalisation de la tâche (0-3):", 0.0, 3.0, 2.5, 0.5)
            r2 = st.slider("Cohérence et cohésion (0-2):", 0.0, 2.0, 1.5, 0.5)
            r3 = st.slider("Lexique (0-2):", 0.0, 2.0, 1.5, 0.5)
            r4 = st.slider("Morphosyntaxe (0-3):", 0.0, 3.0, 2.0, 0.5)
            
            calculada = round(((comp + r1 + r2 + r3 + r4) / 30.0) * 10.0, 1)
            st.metric("Nota sobre 10:", f"{calculada} / 10.0")
        with co2:
            st.camera_input("Capturar examen físico:")
            if st.button("✨ Cargar Nota DELF en Formulario", use_container_width=True):
                df_grupo.at[idx_o, ex_ocr] = calculada
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                guardar_datos_permanentes()
                st.success("Nota asignada temporalmente. Guarda en 'Captura Rápida' para asentar promedios.")

    with tab_pdf:
        st.subheader("🖨️ Exportación de Actas de Evaluación Continua")
        def generar_pdf_binario(df, name, cuat):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            title = ParagraphStyle('T', parent=styles['Heading1'], fontSize=13, leading=15, textColor=colors.HexColor("#0B3C5D"), alignment=1)
            meta = ParagraphStyle('M', parent=styles['Normal'], fontSize=9, leading=11, alignment=1)
            story.append(Paragraph("UNIVERSIDAD AERONÁUTICA EN QUERÉTARO", title))
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"ACTA DE EVALUACIÓN CONTINUA FRANCÉS (30%) - {name} | {cuat}", meta))
            story.append(Spacer(1, 15))
            
            headers = ["Matrícula", "Nombre del Alumno", "Plan", "Nota /10", "30%"]
            data = [headers]
            for _, r in df.iterrows():
                data.append([str(r['Matrícula']), r['Alumno'][:22], str(r['Plan']), str(r['NOTA BASE 10']), str(r['PUNTAJE 30%'])])
                
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (1,1), (1,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8)
            ]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        if st.button("📥 Descargar Acta de Evaluación Continua en PDF", use_container_width=True):
            pdf_data = generar_pdf_binario(df_grupo, grupo_seleccionado, cuatrimestre)
            st.download_button("Guardar PDF", pdf_data, file_name=f"Acta_Francet_{grupo_seleccionado}.pdf", mime="application/pdf")

    with tab_admin:
        st.subheader("🛠️ Panel de Control de Estructura")
        if st.button("⚠️ LIMPIAR TODAS LAS TABLAS Y VOLVER A PANTALLA DE CARGA", type="destructive", use_container_width=True):
            st.session_state.base_datos_grupos = {}
            if os.path.exists(ARCHIVO_BD):
                os.remove(ARCHIVO_BD)
            st.rerun()
