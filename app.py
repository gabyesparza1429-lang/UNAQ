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
st.set_page_config(page_title="UNAQ - Control de Notas", layout="wide")

# Nombre del archivo persistente en disco para la memoria permanente
ARCHIVO_BD = "base_datos_alumnos.json"

def guardar_datos_permanentes():
    datos_exportar = {}
    for grupo, df in st.session_state.base_datos_grupos.items():
        datos_exportar[grupo] = df.to_dict(orient="records")
    with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
        json.dump(datos_exportar, f, ensure_ascii=False, indent=4)

def cargar_datos_permanentes():
    if os.path.exists(ARCHIVO_BD):
        try:
            with open(ARCHIVO_BD, "r", encoding="utf-8") as f:
                datos_importados = json.load(f)
            diccionario_final = {}
            for grupo, lista_filas in datos_importados.items():
                diccionario_final[grupo] = pd.DataFrame(lista_filas)
            return diccionario_final
        except:
            return {}
    return {}

# Inicialización de datos
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Herramienta con memoria permanente y extractor optimizado para listas de la UNAQ.")
st.write("---")

# BARRA LATERAL OPTIMIZADA: Ocupa mínimo espacio
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    # Si ya existen grupos, el selector global aparece aquí a la izquierda
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        # Selector Único de Grupo que controla TODA la app automáticamente
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        st.write("---")
        # Sección expandible oculta para que no estorbe ni quite espacio de notas
        with st.expander("🎯 Configurar Porcentajes de Evaluación"):
            st.caption("Escriba los valores numéricos (Deben sumar 100%)")
            v_quiz = st.number_input("Total QUIZ (%)", 0, 100, 20)
            v_proy = st.number_input("Total PROYECTO (%)", 0, 100, 20)
            st.markdown("**Competencias:**")
            v_co = st.number_input("Comprensión Oral (%)", 0, 100, 10)
            v_ce = st.number_input("Comprensión Escrita (%)", 0, 100, 10)
            v_po = st.number_input("Producción Oral (%)", 0, 100, 10)
            v_pe = st.number_input("Producción Escrita (%)", 0, 100, 10)
            st.markdown("**Formación:**")
            v_as = st.number_input("Asistencia (%)", 0, 100, 5)
            v_fi = st.number_input("Firmas / Tareas (%)", 0, 100, 10)
            v_se = st.number_input("SER (%)", 0, 100, 5)
            
            suma_total = v_quiz + v_proy + v_co + v_ce + v_po + v_pe + v_as + v_fi + v_se
            if suma_total != 100:
                st.error(f"Suma actual: {suma_total}%. Debe ser 100%.")
            else:
                st.success("Porcentajes válidos.")
                st.session_state.config_evaluacion = {
                    'quiz': v_quiz / 100, 'proyecto': v_proy / 100,
                    'comp_oral': v_co / 100, 'comp_esc': v_ce / 100,
                    'prod_oral': v_po / 100, 'prod_esc': v_pe / 100,
                    'asistencia': v_as / 100, 'firmas': v_fi / 100, 'ser': v_se / 100
                }
        
        st.write("---")
        if st.button("🚨 BORRAR TODO / NUEVO PDF", use_container_width=True, type="secondary"):
            st.session_state.base_datos_grupos = {}
            if os.path.exists(ARCHIVO_BD):
                os.remove(ARCHIVO_BD)
            st.rerun()

# Si los porcentajes no se han movido en el expander, se asegura un respaldo por defecto para evitar errores
if 'config_evaluacion' not in st.session_state or not st.session_state.config_evaluacion:
    st.session_state.config_evaluacion = {
        'quiz': 0.20, 'proyecto': 0.20, 'comp_oral': 0.10, 'comp_esc': 0.10,
        'prod_oral': 0.10, 'prod_esc': 0.10, 'asistencia': 0.05, 'firmas': 0.10, 'ser': 0.05
    }

# PANTALLA DE CARGA: Si no hay datos guardados
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
                    st.session_state.base_datos_grupos[grupo] = pd.DataFrame({
                        'Alumno': lista_final_alumnos,
                        '1er Quiz': [0.0]*len(lista_final_alumnos), '2do Quiz': [0.0]*len(lista_final_alumnos),
                        '3er Quiz': [0.0]*len(lista_final_alumnos), '4to Quiz': [0.0]*len(lista_final_alumnos),
                        'TOTAL QUIZ': [0.0]*len(lista_final_alumnos),
                        '1er Proyecto': [0.0]*len(lista_final_alumnos), 'TOTAL PROYECTO': [0.0]*len(lista_final_alumnos),
                        'Comprensión Oral': [0.0]*len(lista_final_alumnos), 'Comprensión Escrita': [0.0]*len(lista_final_alumnos),
                        'Producción Oral': [0.0]*len(lista_final_alumnos), 'Producción Escrita': [0.0]*len(lista_final_alumnos),
                        'Asistencia': [0.0]*len(lista_final_alumnos), 'Firmas': [0.0]*len(lista_final_alumnos),
                        'Ser': [0.0]*len(lista_final_alumnos), 'TOTAL FINAL': [0.0]*len(lista_final_alumnos)
                    })
            
            if st.session_state.base_datos_grupos:
                guardar_datos_permanentes()
                st.success("🎉 ¡Grupos creados con éxito!")
                st.rerun()

# INTERFAZ SINCRONIZADA AUTOMÁTICAMENTE
else:
    # Extraemos el DataFrame correspondiente al grupo seleccionado a la izquierda
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    
    tab_tabla, tab_captura, tab_reportes, tab_admin = st.tabs([
        "📊 Cuadrícula del Grupo", "📝 Captura Paso a Paso", "🖨️ Reportes PDF", "🛠️ Administrar Grupo Seleccionado"
    ])
    
    # Pestaña 1: Vista General Sincronizada
    with tab_tabla:
        st.header(f"📊 Concentrado de Calificaciones - {grupo_seleccionado}")
        st.write(f"Periodo: {cuatrimestre}")
        st.dataframe(df_grupo, use_container_width=True, hide_index=True)

    # Pestaña 2: Captura Automática Filtrada por la Barra Izquierda
    with tab_captura:
        st.subheader(f"✍️ Registro de Notas - Grupo Actual: {grupo_seleccionado}")
        if not df_grupo.empty:
            alumno_seleccionado = st.selectbox("👤 Selecciona al alumno de este grupo:", df_grupo['Alumno'].tolist(), key=f"sel_al_{grupo_seleccionado}")
            idx = df_grupo[df_grupo['Alumno'] == alumno_seleccionado].index[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### 📝 Quizes y Proyectos")
                q1 = st.number_input("1er Quiz", 0.0, 10.0, float(df_grupo.at[idx, '1er Quiz']), 0.1, key=f"q1_{idx}")
                q2 = st.number_input("2do Quiz", 0.0, 10.0, float(df_grupo.at[idx, '2do Quiz']), 0.1, key=f"q2_{idx}")
                q3 = st.number_input("3er Quiz", 0.0, 10.0, float(df_grupo.at[idx, '3er Quiz']), 0.1, key=f"q3_{idx}")
                q4 = st.number_input("4to Quiz", 0.0, 10.0, float(df_grupo.at[idx, '4to Quiz']), 0.1, key=f"q4_{idx}")
                p1 = st.number_input("Nota del Proyecto", 0.0, 10.0, float(df_grupo.at[idx, '1er Proyecto']), 0.1, key=f"p1_{idx}")
            with col2:
                st.markdown("### 🗣️ Competencias")
                c_oral = st.number_input("Comprensión Oral", 0.0, 10.0, float(df_grupo.at[idx, 'Comprensión Oral']), 0.1, key=f"co_{idx}")
                c_esc = st.number_input("Comprensión Escrita", 0.0, 10.0, float(df_grupo.at[idx, 'Comprensión Escrita']), 0.1, key=f"ce_{idx}")
                p_oral = st.number_input("Producción Oral", 0.0, 10.0, float(df_grupo.at[idx, 'Producción Oral']), 0.1, key=f"po_{idx}")
                p_esc = st.number_input("Producción Escrita", 0.0, 10.0, float(df_grupo.at[idx, 'Producción Escrita']), 0.1, key=f"pe_{idx}")
            with col3:
                st.markdown("### 📋 Formación Integral")
                asist = st.number_input("Asistencia", 0.0, 10.0, float(df_grupo.at[idx, 'Asistencia']), 0.1, key=f"as_{idx}")
                firmas = st.number_input("Firmas / Tareas", 0.0, 10.0, float(df_grupo.at[idx, 'Firmas']), 0.1, key=f"fi_{idx}")
                ser = st.number_input("Nota del SER", 0.0, 10.0, float(df_grupo.at[idx, 'Ser']), 0.1, key=f"se_{idx}")
                
            if st.button("💾 Guardar y Calcular Calificación", type="primary", use_container_width=True):
                df_grupo.at[idx, '1er Quiz'] = q1
                df_grupo.at[idx, '2do Quiz'] = q2
                df_grupo.at[idx, '3er Quiz'] = q3
                df_grupo.at[idx, '4to Quiz'] = q4
                df_grupo.at[idx, '1er Proyecto'] = p1
                df_grupo.at[idx, 'Comprensión Oral'] = c_oral
                df_grupo.at[idx, 'Comprensión Escrita'] = c_esc
                df_grupo.at[idx, 'Producción Oral'] = p_oral
                df_grupo.at[idx, 'Producción Escrita'] = p_esc
                df_grupo.at[idx, 'Asistencia'] = asist
                df_grupo.at[idx, 'Firmas'] = firmas
                df_grupo.at[idx, 'Ser'] = ser
                
                t_quiz = (q1 + q2 + q3 + q4) / 4
                df_grupo.at[idx, 'TOTAL QUIZ'] = round(t_quiz, 2)
                df_grupo.at[idx, 'TOTAL PROYECTO'] = p1
                
                cfg = st.session_state.config_evaluacion
                nota_final = ((t_quiz * cfg['quiz']) + (p1 * cfg['proyecto']) + 
                              (c_oral * cfg['comp_oral']) + (c_esc * cfg['comp_esc']) + 
                              (p_oral * cfg['prod_oral']) + (p_esc * cfg['prod_esc']) + 
                              (asist * cfg['asistencia']) + (firmas * cfg['firmas']) + (ser * cfg['ser']))
                                  
                df_grupo.at[idx, 'TOTAL FINAL'] = round(nota_final, 2)
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                guardar_datos_permanentes()
                st.success(f"¡Calificación Guardada para {alumno_seleccionado}!")
                st.rerun()
        else:
            st.warning("Este grupo no tiene alumnos.")

    # Pestaña 3: Reportes Sincronizados
    with tab_reportes:
        st.header(f"🖨️ Imprimir Acta de Evaluación ({grupo_seleccionado})")
        def generar_pdf_grupo(df, g_name, cuatri):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor("#0B3C5D"), alignment=1)
            meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=12, alignment=1)
            story.append(Paragraph(f"UNIVERSIDAD AERONÁUTICA EN QUERÉTARO", title_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"ACTA DE EVALUACIÓN DE IDIOMAS - GRUPO: {g_name} | {cuatri}", meta_style))
            story.append(Spacer(1, 15))
            data = [["Alumno", "Quiz", "Proy.", "C.Oral", "C.Esc", "P.Oral", "P.Esc", "Final"]]
            for _, row in df.iterrows():
                data.append([row['Alumno'][:20], str(row['TOTAL QUIZ']), str(row['TOTAL PROYECTO']), str(row['Comprensión Oral']), str(row['Comprensión Escrita']), str(row['Producción Oral']), str(row['Producción Escrita']), str(row['TOTAL FINAL'])])
            t = Table(data, colWidths=[150, 45, 45, 45, 45, 45, 45, 50])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (0,0), (0,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 6), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F7FA")), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        if not df_grupo.empty:
            pdf_data = generar_pdf_grupo(df_grupo, grupo_seleccionado, cuatrimestre)
            st.download_button(label=f"📥 DESCARGAR REPORTE EN PDF ({grupo_seleccionado})", data=pdf_data, file_name=f"Reporte_{grupo_seleccionado}.pdf", mime="application/pdf", use_container_width=True)

    # Pestaña 4: ADMINISTRACIÓN COMPLETAMENTE AUTOSINCRONIZADA CON LA IZQUIERDA
    with tab_admin:
        st.header(f"🛠️ Panel de Control - Administrando: {grupo_seleccionado}")
        
        # Corrección de Nombre de Grupo
        st.subheader("✏️ 1. Cambiar Nombre a este Grupo")
        nuevo_nombre_grupo = st.text_input("Escriba el nuevo nombre:", grupo_seleccionado, key=f"txt_gname_{grupo_seleccionado}")
        if st.button("💾 Guardar Nuevo Nombre del Grupo", key=f"btn_gname_{grupo_seleccionado}"):
            nuevo_nombre_grupo = nuevo_nombre_grupo.strip().upper()
            if nuevo_nombre_grupo != "" and nuevo_nombre_grupo != grupo_seleccionado:
                st.session_state.base_datos_grupos[nuevo_nombre_grupo] = st.session_state.base_datos_grupos.pop(grupo_seleccionado)
                guardar_datos_permanentes()
                st.success("¡Grupo renombrado exitosamente!")
                st.rerun()

        st.write("---")
        # Corrección de Nombre de Alumno Sincronizado
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
        # Transferencia de Alumno Sincronizada
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
