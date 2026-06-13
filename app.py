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

# Configuración inicial de la página web
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

# Nombre del archivo persistente en disco para la memoria permanente
ARCHIVO_BD = "base_datos_alumnos.json"

def guardar_datos_permanentes():
    """Serializa la base de datos de grupos y configuraciones a un archivo JSON."""
    datos_exportar = {
        "grupos": {},
        "configuraciones_grupos": st.session_state.configuraciones_grupos
    }
    for grupo, df in st.session_state.base_datos_grupos.items():
        datos_exportar["grupos"][grupo] = df.to_dict(orient="records")
    with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
        json.dump(datos_exportar, f, ensure_ascii=False, indent=4)

def cargar_datos_permanentes():
    """Recupera los datos estructurados y configuraciones específicas desde el disco."""
    if os.path.exists(ARCHIVO_BD):
        try:
            with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
                datos_importados = json.load(f)
            
            st.session_state.configuraciones_grupos = datos_importados.get("configuraciones_grupos", {})
            diccionario_final = {}
            for grupo, lista_filas in datos_importados.get("grupos", {}).items():
                diccionario_final[grupo] = pd.DataFrame(lista_filas)
            return diccionario_final
        except:
            return {}
    return {}

# Inicialización segura de los estados de Streamlit
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Evaluación Continua (30% del Cuatrimestre) con rasgos y número de quizes configurables por grupo.")
st.write("---")

# BARRA LATERAL: Control de Entorno y Variables de Curso
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        # Inicializar configuración específica de este grupo si no existe
        if grupo_seleccionado not in st.session_state.configuraciones_grupos:
            st.session_state.configuraciones_grupos[grupo_seleccionado] = {
                'num_quizes': 4, 'n_quiz': 'Quizes', 'w_quiz': 40,
                'n_proyecto': 'Proyecto', 'w_proyecto': 30,
                'n_asistencia': 'Asistencia', 'w_asistencia': 10,
                'n_firmas': 'Firmas / Tareas', 'w_firmas': 10,
                'n_ser': 'SER / Actitud', 'w_ser': 10
            }
            
        cfg = st.session_state.configuraciones_grupos[grupo_seleccionado]
        
        st.write("---")
        # EXPANSIÓN DE CONFIGURACIÓN DINÁMICA POR GRUPO
        with st.expander(f"⚙️ Configurar Rasgos de: {grupo_seleccionado}"):
            st.caption("Define el número de quizes y el peso de cada rasgo. Asigna 0% para desactivar un rubro.")
            
            # Control interactivo del número de quizes
            cfg['num_quizes'] = st.number_input("Número de Quizes a programar:", min_value=1, max_value=10, value=int(cfg['num_quizes']))
            
            st.markdown("**Pesos e Identificadores (Suma total debe ser 100%):**")
            
            col_n1, col_p1 = st.columns([2, 1])
            with col_n1: cfg['n_quiz'] = st.text_input("Nombre Rasgo 1:", cfg['n_quiz'])
            with col_p1: cfg['w_quiz'] = st.number_input("Quiz %", 0, 100, int(cfg['w_quiz']), key="wq")
            
            col_n2, col_p2 = st.columns([2, 1])
            with col_n2: cfg['n_proyecto'] = st.text_input("Nombre Rasgo 2:", cfg['n_proyecto'])
            with col_p2: cfg['w_proyecto'] = st.number_input("Proy %", 0, 100, int(cfg['w_proyecto']), key="wp")
            
            col_n3, col_p3 = st.columns([2, 1])
            with col_n3: cfg['n_asistencia'] = st.text_input("Nombre Rasgo 3:", cfg['n_asistencia'])
            with col_p3: cfg['w_asistencia'] = st.number_input("Asist %", 0, 100, int(cfg['w_asistencia']), key="wa")
            
            col_n4, col_p4 = st.columns([2, 1])
            with col_n4: cfg['n_firmas'] = st.text_input("Nombre Rasgo 4:", cfg['n_firmas'])
            with col_p4: cfg['w_firmas'] = st.number_input("Firmas %", 0, 100, int(cfg['w_firmas']), key="wf")
            
            col_n5, col_p5 = st.columns([2, 1])
            with col_n5: cfg['n_ser'] = st.text_input("Nombre Rasgo 5:", cfg['n_ser'])
            with col_p5: cfg['w_ser'] = st.number_input("SER %", 0, 100, int(cfg['w_ser']), key="ws")
            
            suma_total = cfg['w_quiz'] + cfg['w_proyecto'] + cfg['w_asistencia'] + cfg['w_firmas'] + cfg['w_ser']
            if suma_total != 100:
                st.error(f"La suma actual es {suma_total}%. Ajuste para que dé 100%.")
            else:
                st.success("Distribución válida de rasgos.")
                st.session_state.configuraciones_grupos[grupo_seleccionado] = cfg
                # Ajustar dinámicamente las columnas del dataframe si aumentó el número de quizes
                df_actual = st.session_state.base_datos_grupos[grupo_seleccionado]
                for q_idx in range(1, cfg['num_quizes'] + 1):
                    col_q = f"Quiz {q_idx}"
                    if col_q not in df_actual.columns:
                        df_actual[col_q] = 0.0
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_actual
                guardar_datos_permanentes()
        
        st.write("---")
        if st.button("🚨 BORRAR TODO / NUEVO PDF", use_container_width=True, type="secondary"):
            st.session_state.base_datos_grupos = {}
            st.session_state.configuraciones_grupos = {}
            if os.path.exists(ARCHIVO_BD):
                os.remove(ARCHIVO_BD)
            st.rerun()

# VISTA DE CARGA INICIAL
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga Inicial de Listas (Detección Multigrupo)")
    st.info("💡 **Instrucciones:** Copia el texto completo de tus PDFs de asistencia de la UNAQ y pégalo aquí abajo.")
    
    texto_pegado = st.text_area("📋 Pega aquí todo el contenido de tus listas de la UNAQ:", height=400)
    
    if st.button("✨ Procesar, Separar y Crear Grupos", type="primary", use_container_width=True):
        if texto_pegado.strip() != "":
            lineas = texto_pegado.split("\n")
            palabras_bloqueadas = [
                "universidad", "aeronáutica", "querétaro", "departamento", "servicios", "escolares",
                "lista", "asistencia", "clave", "materia", "cuatrimestre", "docente",
                "carrera", "ciclo", "matricula", "nombre", "plan", "estudios", "asistencias",
                "inglés", "ingenierías", "oscar", "hernandez", "flores", "page", "clases", "unq"
            ]
            
            diccionario_grupos = {}
            carrera_detectada = ""
            nivel_detectado = ""
            grupo_actual = "GRUPO NO ESPECIFICADO"
            
            for linea in lineas:
                linea_limpia = linea.replace('"', '').replace(',', '').replace('\'', '').strip()
                if not linea_limpia or len(linea_limpia) < 3:
                    continue
                
                match_frn = re.search(r'A?-?FR-?A?(\d\.\d)', linea_limpia, re.IGNORECASE)
                if match_frn:
                    nivel_detectado = f"A{match_frn.group(1)}"
                
                match_plan = re.search(r'\b([A-Z]+)\d{4}\b', linea_limpia, re.IGNORECASE)
                if match_plan:
                    carrera_detectada = match_plan.group(1).upper()
                    if carrera_detectada and nivel_detectado:
                        grupo_actual = f"{carrera_detectada} {nivel_detectado}"
                        if grupo_actual not in diccionario_grupos:
                            diccionario_grupos[grupo_actual] = []
                
                if any(bloqueo in linea_limpia.lower() for bloqueo in palabras_bloqueadas):
                    continue
                
                linea_limpia = re.sub(r'\b[A-Z]+\d{4}\b', '', linea_limpia, flags=re.IGNORECASE).strip()
                linea_limpia = re.sub(r'\b\d+\b', '', linea_limpia).strip()
                
                if len(linea_limpia.split()) >= 2 and not linea_limpia.startswith("A-FR-") and not "INGLES" in linea_limpia.upper():
                    if grupo_actual not in diccionario_grupos:
                        diccionario_grupos[grupo_actual] = []
                    diccionario_grupos[grupo_actual].append(linea_limpia.upper())
            
            for grupo, lista_alumnos in diccionario_grupos.items():
                lista_final_alumnos = sorted(list(set(lista_alumnos)))
                if lista_final_alumnos and grupo != "GRUPO NO ESPECIFICADO":
                    df_init = pd.DataFrame({'Alumno': lista_final_alumnos})
                    for q in range(1, 5):
                        df_init[f"Quiz {q}"] = 0.0
                    df_init['TOTAL QUIZ'] = 0.0
                    df_init['Proyecto'] = 0.0
                    df_init['Asistencia'] = 0.0
                    df_init['Firmas'] = 0.0
                    df_init['Ser'] = 0.0
                    df_init['NOTA BASE 10'] = 0.0
                    df_init['PUNTAJE 30%'] = 0.0
                    st.session_state.base_datos_grupos[grupo] = df_init
            
            if st.session_state.base_datos_grupos:
                guardar_datos_permanentes()
                st.success("🎉 ¡Grupos e interfaz creados con éxito!")
                st.rerun()

# INTERFAZ DE USUARIO DINÁMICA DE CAPTURA Y REPORTES
else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos[grupo_seleccionado]
    
    tab_tabla, tab_captura, tab_reportes, tab_admin = st.tabs([
        "📊 Cuadrícula del Grupo", "📝 Captura Paso a Paso", "🖨️ Reportes PDF", "🛠️ Administrar Grupo Seleccionado"
    ])
    
    with tab_tabla:
        st.header(f"📊 Concentrado de Calificaciones - {grupo_seleccionado}")
        st.write(f"Cuatrimestre: {cuatrimestre} | Evaluación Continua (Máximo 3.0 Puntos)")
        
        cols_mostrar = ['Alumno']
        for q_idx in range(1, cfg['num_quizes'] + 1):
            cols_mostrar.append(f"Quiz {q_idx}")
            
        if cfg['w_quiz'] > 0: cols_mostrar.append('TOTAL QUIZ')
        if cfg['w_proyecto'] > 0: cols_mostrar.append('Proyecto')
        if cfg['w_asistencia'] > 0: cols_mostrar.append('Asistencia')
        if cfg['w_firmas'] > 0: cols_mostrar.append('Firmas')
        if cfg['w_ser'] > 0: cols_mostrar.append('Ser')
        cols_mostrar.extend(['NOTA BASE 10', 'PUNTAJE 30%'])
        
        cols_finales = [c for c in cols_mostrar if c in df_grupo.columns]
        st.dataframe(df_grupo[cols_finales], use_container_width=True, hide_index=True)

    with tab_captura:
        st.subheader(f"✍️ Anotación de Evaluaciones - Grupo: {grupo_seleccionado}")
        if not df_grupo.empty:
            alumno_seleccionado = st.selectbox("👤 Selecciona al alumno:", df_grupo['Alumno'].tolist(), key=f"sel_al_{grupo_seleccionado}")
            idx = df_grupo[df_grupo['Alumno'] == alumno_seleccionado].index[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                valores_quizes = []
                if cfg['w_quiz'] > 0:
                    st.markdown(f"### 📝 {cfg['n_quiz']}")
                    for q_idx in range(1, cfg['num_quizes'] + 1):
                        col_q_name = f"Quiz {q_idx}"
                        val_def = float(df_grupo.at[idx, col_q_name]) if col_q_name in df_grupo.columns else 0.0
                        v_q = st.number_input(f"{col_q_name} (0-10)", 0.0, 10.0, val_def, 0.1, key=f"inp_q{q_idx}_{idx}")
                        valores_quizes.append((col_q_name, v_q))
                
            with col2:
                p1 = 0.0
                asist = 0.0
                if cfg['w_proyecto'] > 0 or cfg['w_asistencia'] > 0:
                    st.markdown("### 🏗️ Entregables")
                    if cfg['w_proyecto'] > 0:
                        p1 = st.number_input(f"Nota de {cfg['n_proyecto']}", 0.0, 10.0, float(df_grupo.at[idx, 'Proyecto']), 0.1, key=f"p1_{idx}")
                    if cfg['w_asistencia'] > 0:
                        asist = st.number_input(f"Nota de {cfg['n_asistencia']}", 0.0, 10.0, float(df_grupo.at[idx, 'Asistencia']), 0.1, key=f"as_{idx}")
                        
            with col3:
                firmas = 0.0
                ser = 0.0
                if cfg['w_firmas'] > 0 or cfg['w_ser'] > 0:
                    st.markdown("### 📋 Formación")
                    if cfg['w_firmas'] > 0:
                        firmas = st.number_input(f"Nota de {cfg['n_firmas']}", 0.0, 10.0, float(df_grupo.at[idx, 'Firmas']), 0.1, key=f"fi_{idx}")
                    if cfg['w_ser'] > 0:
                        ser = st.number_input(f"Nota de {cfg['n_ser']}", 0.0, 10.0, float(df_grupo.at[idx, 'Ser']), 0.1, key=f"se_{idx}")
                        
            if st.button("💾 Guardar y Calcular Calificación", type="primary", use_container_width=True):
                suma_quizes = 0.0
                for col_q, val_q in valores_quizes:
                    df_grupo.at[idx, col_q] = val_q
                    suma_quizes += val_q
                
                t_quiz = (suma_quizes / cfg['num_quizes']) if cfg['num_quizes'] > 0 else 0.0
                df_grupo.at[idx, 'TOTAL QUIZ'] = round(t_quiz, 2)
                
                if cfg['w_proyecto'] > 0: df_grupo.at[idx, 'Proyecto'] = p1
                if cfg['w_asistencia'] > 0: df_grupo.at[idx, 'Asistencia'] = asist
                if cfg['w_firmas'] > 0: df_grupo.at[idx, 'Firmas'] = firmas
                if cfg['w_ser'] > 0: df_grupo.at[idx, 'Ser'] = ser
                
                p_quiz = (t_quiz * (cfg['w_quiz'] / 100)) if cfg['w_quiz'] > 0 else 0.0
                p_proy = (p1 * (cfg['w_proyecto'] / 100)) if cfg['w_proyecto'] > 0 else 0.0
                p_asist = (asist * (cfg['w_asistencia'] / 100)) if cfg['w_asistencia'] > 0 else 0.0
                p_firmas = (firmas * (cfg['w_firmas'] / 100)) if cfg['w_firmas'] > 0 else 0.0
                p_ser = (ser * (cfg['w_ser'] / 100)) if cfg['w_ser'] > 0 else 0.0
                
                nota_base_10 = p_quiz + p_proy + p_asist + p_firmas + p_ser
                df_grupo.at[idx, 'NOTA BASE 10'] = round(nota_base_10, 2)
                
                puntaje_30 = nota_base_10 * 0.3
                df_grupo.at[idx, 'PUNTAJE 30%'] = round(puntaje_30, 2)
                
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                guardar_datos_permanentes()
                st.success(f"¡Calificación guardada! Nota Continua: {round(nota_base_10, 2)}/10 | Puntaje Parcial (30%): {round(puntaje_30, 2)} / 3.0")
                st.rerun()
        else:
            st.warning("Este grupo no tiene alumnos.")

    with tab_reportes:
        st.header(f"🖨️ Reporte Imprimible PDF ({grupo_seleccionado})")
        def generar_pdf_grupo(df, g_name, cuatri, c):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#0B3C5D"), alignment=1)
            meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=12, alignment=1)
            story.append(Paragraph(f"UNIVERSIDAD AERONÁUTICA EN QUERÉTARO", title_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"ACTA DE EVALUACIÓN CONTINUA (30%) - GRUPO: {g_name} | {cuatri}", meta_style))
            story.append(Spacer(1, 15))
            
            data = [["Alumno", c['n_quiz'][:8], c['n_proyecto'][:8], "Asist.", "Base 10", "Puntaje (30%)"]]
            for _, row in df.iterrows():
                data.append([row['Alumno'][:22], str(row['TOTAL QUIZ']), str(row['Proyecto']), str(row['Asistencia']), str(row['NOTA BASE 10']), str(row['PUNTAJE 30%'])])
            t = Table(data, colWidths=[180, 60, 60, 60, 60, 100])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (0,0), (0,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 6), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F7FA")), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        if not df_grupo.empty:
            pdf_data = generar_pdf_grupo(df_grupo, grupo_seleccionado, cuatrimestre, cfg)
            st.download_button(label=f"📥 DESCARGAR REPORTE AL 30% EN PDF", data=pdf_data, file_name=f"Acta_30_{grupo_seleccionado}.pdf", mime="application/pdf", use_container_width=True)

    with tab_admin:
        st.header(f"🛠️ Panel de Control - Administrando: {grupo_seleccionado}")
        st.subheader("✏️ 1. Cambiar Nombre a este Grupo")
        nuevo_nombre_grupo = st.text_input("Escriba el nuevo nombre:", grupo_seleccionado, key=f"txt_gname_{grupo_seleccionado}")
        if st.button("💾 Guardar Nuevo Nombre del Grupo", key=f"btn_gname_{grupo_seleccionado}"):
            nuevo_nombre_grupo = nuevo_nombre_grupo.strip().upper()
            
            # CORRECCIÓN AQUÍ: Se cambió "group_selected" por "grupo_seleccionado"
            if nuevo_nombre_grupo != "" and nuevo_nombre_grupo != grupo_seleccionado:
                st.session_state.base_datos_grupos[nuevo_nombre_grupo] = st.session_state.base_datos_grupos.pop(grupo_seleccionado)
                if grupo_seleccionado in st.session_state.configuraciones_grupos:
                    st.session_state.configuraciones_grupos[nuevo_nombre_grupo] = st.session_state.configuraciones_grupos.pop(grupo_seleccionado)
                guardar_datos_permanentes()
                st.success("¡Grupo renombrado exitosamente!")
                st.rerun()

        st.write("---")
        st.subheader("👤 2. Corregir Nombre de un Alumno de este Grupo")
        if not df_grupo.empty:
            alumno_a_editar = st.selectbox("Seleccione al alumno con error:", df_grupo['Alumno'].tolist(), key=f"sel_ed_al_{grupo_seleccionado}")
            nuevo_nombre_alumno = st.text_input("Corrija el nombre:", alumno_a_editar, key=f"txt_ed_al_{grupo_seleccionado}").strip().upper()
            if st.button("💾 Guardar Corrección del Nombre", key=f"btn_ed_al_{grupo_seleccionado}"):
                if nuevo_nombre_alumno != "":
                    idx_al = df_grupo[df_grupo['Alumno'] == alumno_a_editar].index[0]
                    df_grupo.at[idx_al, 'Alumno'] = nuevo_nombre_alumno
                    st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo.sort_values(by="Alumno").reset_index(drop=True)
                    guardar_datos_permanentes()
                    st.success("¡Nombre del alumno corregido!")
                    st.rerun()

        st.write("---")
        st.subheader("🏃 3. Mover Alumno de este Grupo a Otro Salón")
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
                    st.success(f"¡Alumno transferido exitosamente a {grupo_destino}!")
                    st.rerun()
            else:
                st.warning("No tienes otros grupos creados para poder transferir alumnos.")
