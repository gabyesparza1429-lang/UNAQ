import streamlit as st
import pandas as pd
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración inicial de la página web
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

# Inicialización de la base de datos de grupos y alumnos en la sesión de la app
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = {} # Estructura: {'GRUPO_1': DataFrame, 'GRUPO_2': DataFrame}
if 'config_evaluacion' not in st.session_state:
    st.session_state.config_evaluacion = {}

st.title("✈️ Generador de Interfaces GEM - UNAQ (Múltiples Grupos)")
st.write("Extractor inteligente multiclase especializado en sábanas y listas de asistencia de la UNAQ.")
st.write("---")

# BARRA LATERAL: Configuración de Criterios y Ponderaciones
with st.sidebar:
    st.header("📋 Configuración de Evaluación")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    st.write("---")
    st.subheader("🎯 Porcentajes de Notas")
    st.caption("Asegúrate de que la suma de todos los rubros dé exactamente 100%")
    
    w_quiz = st.slider("Porcentaje Total QUIZ (%)", 0, 100, 20)
    w_proyecto = st.slider("Porcentaje Total PROYECTO (%)", 0, 100, 20)
    
    st.markdown("**Competencias Lingüísticas:**")
    w_comp_oral = st.slider("Comprensión Oral (%)", 0, 100, 10)
    w_comp_esc = st.slider("Comprensión Escrita (%)", 0, 100, 10)
    w_prod_oral = st.slider("Producción Oral (%)", 0, 100, 10)
    w_prod_esc = st.slider("Producción Escrita (%)", 0, 100, 10)
    
    st.markdown("**Formación Integral:**")
    w_asistencia = st.slider("Porcentaje ASISTENCIA (%)", 0, 100, 5)
    w_firmas = st.slider("Porcentaje FIRMAS (%)", 0, 100, 10)
    w_ser = st.slider("Porcentaje SER (%)", 0, 100, 5)
    
    suma_total = (w_quiz + w_proyecto + w_comp_oral + w_comp_esc + 
                  w_prod_oral + w_prod_esc + w_asistencia + w_firmas + w_ser)
                  
    if suma_total != 100:
        st.error(f"La suma actual es {suma_total}%. Debe ser exactamente 100%.")
    else:
        st.success("Configuración de porcentajes válida (100%).")
        st.session_state.config_evaluacion = {
            'quiz': w_quiz / 100, 'proyecto': w_proyecto / 100,
            'comp_oral': w_comp_oral / 100, 'comp_esc': w_comp_esc / 100,
            'prod_oral': w_prod_oral / 100, 'prod_esc': w_prod_esc / 100,
            'asistencia': w_asistencia / 100, 'firmas': w_firmas / 100, 'ser': w_ser / 100
        }

# CUERPO PRINCIPAL: Extracción y separación por grupos
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga Masiva de PDFs (Detección de Múltiples Grupos)")
    st.info("💡 **Instrucciones:** Abre tu PDF completo de la UNAQ (el que tiene todas las materias y grupos juntos), presiona **Ctrl + A** para seleccionar todo, luego **Ctrl + C** para copiar, y pégalo aquí abajo. El sistema detectará los diferentes grupos y acomodará a cada alumno automáticamente.")
    
    texto_pegado = st.text_area("📋 Pega aquí todo el contenido de tus listas de la UNAQ:", height=400, placeholder="Pega el texto aquí...")
    
    if st.button("✨ Procesar, Separar y Crear Grupos", type="primary", use_container_width=True):
        if texto_pegado.strip() == "":
            st.warning("El cuadro de texto está vacío.")
        else:
            lineas = texto_pegado.split("\n")
            
            # Palabras institucionales que no son nombres de alumnos
            palabras_bloqueadas = [
                "universidad", "aeronáutica", "querétaro", "departamento", "servicios", "escolares",
                "lista", "asistencia", "clave", "materia", "cuatrimestre", "docente",
                "carrera", "ciclo", "matricula", "nombre", "plan", "estudios", "asistencias",
                "inglés", "ingenierías", "oscar", "hernandez", "flores", "page", "clases", "unq"
            ]
            
            diccionario_grupos = {}
            grupo_actual = "GRUPO NO ESPECIFICADO"
            
            for linea in lineas:
                linea_limpia = linea.replace('"', '').replace(',', '').replace('\'', '').strip()
                
                if not linea_limpia or len(linea_limpia) < 3:
                    continue
                
                # DETECCIÓN DE NUEVO GRUPO (Busca patrones como 26MA-6IDMA, 26MA-3IECSA, etc.)
                match_grupo = re.search(r'\b\d{2}MA-\d[A-Z]+\b', linea_limpia)
                if match_grupo:
                    grupo_actual = match_grupo.group(0)
                    if grupo_actual not in diccionario_grupos:
                        diccionario_grupos[grupo_actual] = []
                    continue
                
                # Saltar líneas informativas o basura de formato
                if any(bloqueo in linea_limpia.lower() for bloqueo in palabras_bloqueadas):
                    continue
                
                # Quitar números sueltos (matrículas o número de lista)
                linea_limpia = re.sub(r'\b\d+\b', '', linea_limpia).strip()
                
                # Verificar que cumpla características de un nombre real de alumno
                if len(linea_limpia.split()) >= 2 and not linea_limpia.startswith("A-FR-") and not "INGLES" in linea_limpia.upper():
                    if grupo_actual not in diccionario_grupos:
                        diccionario_grupos[grupo_actual] = []
                    diccionario_grupos[grupo_actual].append(linea_limpia.upper())
            
            # Limpiar listas, remover duplicados por grupo y guardarlo en la sesión
            grupos_creados = 0
            for grupo, lista_alumnos in diccionario_grupos.items():
                lista_final_alumnos = sorted(list(set(lista_alumnos)))
                if lista_final_alumnos:
                    # Crear el DataFrame estructurado de notas para cada grupo detectado
                    st.session_state.base_datos_grupos[grupo] = pd.DataFrame({
                        'Alumno': lista_final_alumnos,
                        '1er Quiz': [0.0]*len(lista_final_alumnos), '2do Quiz': [0.0]*len(lista_final_alumnos),
                        '3er Quiz': [0.0]*len(lista_final_alumnos), '4to Quiz': [0.0]*len(lista_final_alumnos),
                        'TOTAL QUIZ': [0.0]*len(lista_final_alumnos),
                        '1er Proyecto': [0.0]*len(lista_final_alumnos), 'TOTAL PROYECTO': [0.0]*len(lista_final_alumnos),
                        'Comprensión Oral': [0.0]*len(lista_final_alumnos), 'Comprensión Escrita': [0.0]*len(lista_final_alumnos),
                        'Producción Oral': [0.0]*len(lista_alumnos_filt := lista_final_alumnos), 'Producción Escrita': [0.0]*len(lista_final_alumnos),
                        'Asistencia': [0.0]*len(lista_final_alumnos), 'Firmas': [0.0]*len(lista_final_alumnos),
                        'Ser': [0.0]*len(lista_final_alumnos), 'TOTAL FINAL': [0.0]*len(lista_final_alumnos)
                    })
                    grupos_creados += 1
            
            if grupos_creados > 0:
                st.success(f"🎉 ¡Éxito! El sistema detectó y configuró automáticamente {grupos_creados} grupos separados con sus respectivos alumnos.")
                st.rerun()
            else:
                st.error("No se detectaron grupos válidos en el texto pegado. Asegúrate de copiar el PDF completo.")

# INTERFAZ DE CAPTURA Y REPORTES CUANDO YA HAY GRUPOS ACTIVOS
else:
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        # Selector de grupos detectados en el PDF
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo que desea calificar actualmente:", lista_de_grupos)
    with col_g2:
        st.write(" ")
        st.write(" ")
        if st.button("🔄 Cargar otro PDF / Resetear", use_container_width=True):
            st.session_state.base_datos_grupos = {}
            st.rerun()
            
    # Trabajar con el dataframe del grupo elegido
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    
    tab_captura, tab_tabla, tab_reportes = st.tabs(["📝 Captura Paso a Paso", "📊 Cuadrícula del Grupo", "🖨️ Reportes PDF"])
    
    with tab_captura:
        st.subheader(f"✍️ Evaluando Grupo: {grupo_seleccionado}")
        
        alumno_seleccionado = st.selectbox("👤 Selecciona al alumno a evaluar:", df_grupo['Alumno'].tolist())
        idx = df_grupo[df_grupo['Alumno'] == alumno_seleccionado].index[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📝 Quizes y Proyectos (0-10)")
            q1 = st.number_input("1er Quiz", 0.0, 10.0, float(df_grupo.at[idx, '1er Quiz']), 0.1, key=f"q1_{idx}")
            q2 = st.number_input("2do Quiz", 0.0, 10.0, float(df_grupo.at[idx, '2do Quiz']), 0.1, key=f"q2_{idx}")
            q3 = st.number_input("3er Quiz", 0.0, 10.0, float(df_grupo.at[idx, '3er Quiz']), 0.1, key=f"q3_{idx}")
            q4 = st.number_input("4to Quiz", 0.0, 10.0, float(df_grupo.at[idx, '4to Quiz']), 0.1, key=f"q4_{idx}")
            p1 = st.number_input("Nota del Proyecto", 0.0, 10.0, float(df_grupo.at[idx, '1er Proyecto']), 0.1, key=f"p1_{idx}")
            
        with col2:
            st.markdown("### 🗣️ Competencias (0-10)")
            c_oral = st.number_input("Comprensión Oral", 0.0, 10.0, float(df_grupo.at[idx, 'Comprensión Oral']), 0.1, key=f"co_{idx}")
            c_esc = st.number_input("Comprensión Escrita", 0.0, 10.0, float(df_grupo.at[idx, 'Comprensión Escrita']), 0.1, key=f"ce_{idx}")
            p_oral = st.number_input("Producción Oral", 0.0, 10.0, float(df_grupo.at[idx, 'Producción Oral']), 0.1, key=f"po_{idx}")
            p_esc = st.number_input("Producción Escrita", 0.0, 10.0, float(df_grupo.at[idx, 'Producción Escrita']), 0.1, key=f"pe_{idx}")
            
        with col3:
            st.markdown("### 📋 Formación Integral (0-10)")
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
            if cfg:
                nota_final = ((t_quiz * cfg['quiz']) + (p1 * cfg['proyecto']) + 
                              (c_oral * cfg['comp_oral']) + (c_esc * cfg['comp_esc']) + 
                              (p_oral * cfg['prod_oral']) + (p_esc * cfg['prod_esc']) + 
                              (asist * cfg['asistencia']) + (firmas * cfg['firmas']) + (ser * cfg['ser']))
            else:
                nota_final = (t_quiz + p1 + c_oral + c_esc + p_oral + p_esc + asist + firmas + ser) / 9
                              
            df_grupo.at[idx, 'TOTAL FINAL'] = round(nota_final, 2)
            st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
            st.success(f"¡Guardado! {alumno_seleccionado} tiene un promedio final de: {round(nota_final, 2)} / 10")

    with tab_tabla:
        st.header(f"📊 Concentrado de Calificaciones - {grupo_seleccionado}")
        st.dataframe(df_grupo, use_container_width=True, hide_index=True)

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
                data.append([
                    row['Alumno'][:20], str(row['TOTAL QUIZ']), str(row['TOTAL PROYECTO']),
                    str(row['Comprensión Oral']), str(row['Comprensión Escrita']),
                    str(row['Producción Oral']), str(row['Producción Escrita']), str(row['TOTAL FINAL'])
                ])
                
            t = Table(data, colWidths=[150, 45, 45, 45, 45, 45, 45, 50])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F7FA")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_data = generar_pdf_grupo(df_grupo, grupo_seleccionado, cuatrimestre)
        
        st.download_button(
            label=f"📥 DESCARGAR REPORTE DEL GRUPO {grupo_seleccionado} EN PDF",
            data=pdf_data,
            file_name=f"Reporte_Idiomas_{grupo_seleccionado}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
