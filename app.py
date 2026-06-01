import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración inicial de la página web
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

# Inicialización de variables globales en la sesión de la app
if 'alumnos_db' not in st.session_state:
    st.session_state.alumnos_db = None
if 'config_evaluacion' not in st.session_state:
    st.session_state.config_evaluacion = {}

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Herramienta simplificada de captura de calificaciones bimestrales para profesores.")
st.write("---")

# BARRA LATERAL: Configuración Inicial del Cuatrimestre y Criterios
with st.sidebar:
    st.header("📋 Configuración del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "ENERO-ABRIL 2026")
    grupo_nombre = st.text_input("Grupo / Clase:", "IAM A2.1")
    
    st.write("---")
    st.subheader("🎯 Porcentajes de Evaluación")
    st.caption("Define los rubros y sus valores (Asegúrate que sumen 100%)")
    
    # Configuración dinámica de criterios solicitados
    w_quiz = st.slider("Porcentaje Total QUIZ (%)", 0, 100, 40)
    w_proyecto = st.slider("Porcentaje Total PROYECTO (%)", 0, 100, 30)
    w_asistencia = st.slider("Porcentaje ASISTENCIA (%)", 0, 100, 10)
    w_firmas = st.slider("Porcentaje FIRMAS (%)", 0, 100, 10)
    w_ser = st.slider("Porcentaje SER (%)", 0, 100, 10)
    
    suma_total = w_quiz + w_proyecto + w_asistencia + w_firmas + w_ser
    if suma_total != 100:
        st.error(f"La suma actual es {suma_total}%. Debe ser exactamente 100%.")
    else:
        st.success("Configuración de porcentajes válida (100%).")
        st.session_state.config_evaluacion = {
            'quiz': w_quiz / 100, 'proyecto': w_proyecto / 100,
            'asistencia': w_asistencia / 100, 'firmas': w_firmas / 100, 'ser': w_ser / 100
        }

    st.write("---")
    st.subheader("📂 Carga de Alumnos")
    archivo = st.file_uploader("Arrastra aquí el Excel con la lista de alumnos:", type=["xlsx", "csv"])
    
    if archivo is not None and st.button("Cargar y Procesar Lista"):
        try:
            # Procesar el archivo detectando la estructura compartida
            df_raw = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
            
            # Buscar la fila donde se encuentra la palabra "nombre" para limpiar el archivo de la UNAQ
            fila_encabezado = 0
            for r_idx in range(min(5, len(df_raw))):
                if 'nombre' in [str(c).lower() for c in df_raw.iloc[r_idx].values]:
                    fila_encabezado = r_idx + 1
                    break
            
            df_clean = pd.read_csv(archivo, skiprows=fila_encabezado) if archivo.name.endswith('.csv') else pd.read_excel(archivo, skiprows=fila_encabezado)
            df_clean.columns = [str(c).strip().lower() for c in df_clean.columns]
            
            # Extraer nombres válidos
            col_nombre = [c for c in df_clean.columns if 'nombre' in c][0]
            lista_alumnos = df_clean[col_nombre].dropna().astype(str).tolist()
            lista_alumnos = [a.strip() for a in lista_alumnos if a.strip() != '' and 'nombre' not in a.lower()]
            
            # Crear base de datos interna limpia de calificaciones inicializadas en 0
            st.session_state.alumnos_db = pd.DataFrame({
                'Alumno': lista_alumnos,
                '1er Quiz': [0.0]*len(lista_alumnos), '2do Quiz': [0.0]*len(lista_alumnos),
                '3er Quiz': [0.0]*len(lista_alumnos), '4to Quiz': [0.0]*len(lista_alumnos),
                'TOTAL QUIZ': [0.0]*len(lista_alumnos),
                '1er Proyecto': [0.0]*len(lista_alumnos), 'TOTAL PROYECTO': [0.0]*len(lista_alumnos),
                'Asistencia': [0.0]*len(lista_alumnos), 'Firmas': [0.0]*len(lista_alumnos),
                'Ser': [0.0]*len(lista_alumnos), 'TOTAL FINAL': [0.0]*len(lista_alumnos)
            })
            st.success(f"¡Se registraron {len(lista_alumnos)} alumnos exitosamente!")
        except Exception as e:
            st.error(f"Error procesando el formato del archivo: {e}")

# INTERFAZ DE USUARIO PRINCIPAL (PANEL AMIGABLE)
if st.session_state.alumnos_db is not None:
    tab_captura, tab_tabla, tab_reportes = st.tabs(["📝 Captura Paso a Paso", "📊 Cuadrícula General", "🖨️ Generar PDFs"])
    
    with tab_captura:
        st.header("✍️ Registro de Notas por Alumno")
        st.info("Selecciona el alumno y actualiza sus notas. Los promedios se calculan solos.")
        
        # Selector gigante para evitar perderse entre filas
        alumno_seleccionado = st.selectbox("👤 Selecciona al alumno a evaluar:", st.session_state.alumnos_db['Alumno'].tolist())
        idx = st.session_state.alumnos_db[st.session_state.alumnos_db['Alumno'] == alumno_seleccionado].index[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📝 Quizes (Escala 0-10)")
            q1 = st.number_input("1er Quiz", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, '1er Quiz']), 0.1)
            q2 = st.number_input("2do Quiz", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, '2do Quiz']), 0.1)
            q3 = st.number_input("3er Quiz", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, '3er Quiz']), 0.1)
            q4 = st.number_input("4to Quiz", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, '4to Quiz']), 0.1)
            
        with col2:
            st.markdown("### 🏗️ Proyectos (Escala 0-10)")
            p1 = st.number_input("1er Proyecto Nota", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, '1er Proyecto']), 0.1)
            
        with col3:
            st.markdown("### 📋 Formación y Asistencia")
            asist = st.number_input("Asistencia (0-10)", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, 'Asistencia']), 0.1)
            firmas = st.number_input("Firmas / Tareas (0-10)", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, 'Firmas']), 0.1)
            ser = st.number_input("Nota del SER (0-10)", 0.0, 10.0, float(st.session_state.alumnos_db.at[idx, 'Ser']), 0.1)
            
        if st.button("💾 Guardar y Calcular Calificación", type="primary", use_container_width=True):
            # Guardado seguro en memoria
            st.session_state.alumnos_db.at[idx, '1er Quiz'] = q1
            st.session_state.alumnos_db.at[idx, '2do Quiz'] = q2
            st.session_state.alumnos_db.at[idx, '3er Quiz'] = q3
            st.session_state.alumnos_db.at[idx, '4to Quiz'] = q4
            st.session_state.alumnos_db.at[idx, '1er Proyecto'] = p1
            
            # Procesar Matemáticas Ocultas
            t_quiz = (q1 + q2 + q3 + q4) / 4
            st.session_state.alumnos_db.at[idx, 'TOTAL QUIZ'] = round(t_quiz, 2)
            st.session_state.alumnos_db.at[idx, 'TOTAL PROYECTO'] = p1
            
            st.session_state.alumnos_db.at[idx, 'Asistencia'] = asist
            st.session_state.alumnos_db.at[idx, 'Firmas'] = firmas
            st.session_state.alumnos_db.at[idx, 'Ser'] = ser
            
            # Aplicar pesos configurados
            cfg = st.session_state.config_evaluacion
            nota_final = (t_quiz * cfg['quiz']) + (p1 * cfg['proyecto']) + (asist * cfg['asistencia']) + (firmas * cfg['firmas']) + (ser * cfg['ser'])
            st.session_state.alumnos_db.at[idx, 'TOTAL FINAL'] = round(nota_final, 2)
            
            st.success(f"¡Notas guardadas para {alumno_seleccionado}! Promedio calculado: {round(nota_final, 2)} / 10")

    with tab_tabla:
        st.header(f"📊 Concentrado General del Grupo {grupo_nombre}")
        st.write(f"Cuatrimestre: {cuatrimestre}")
        st.dataframe(st.session_state.alumnos_db, use_container_width=True, hide_index=True)

    with tab_reportes:
        st.header("🖨️ Impresión de Reportes Oficiales en PDF")
        
        # Función para construir PDFs de forma programática con ReportLab
        def generar_pdf_grupo(df, g_name, cuatri):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#0B3C5D"), alignment=1)
            meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=11, leading=14, alignment=1)
            
            story.append(Paragraph(f"UNIVERSIDAD AERONÁUTICA EN QUERÉTARO", title_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"REPORTE BIMESTRAL DE CALIFICACIONES - GRUPO: {g_name} | {cuatri}", meta_style))
            story.append(Spacer(1, 20))
            
            # Preparar tabla para el PDF
            data = [["Alumno", "Tot Quiz", "Proyecto", "Asist.", "Ser", "Final"]]
            for _, row in df.iterrows():
                data.append([row['Alumno'][:30], str(row['TOTAL QUIZ']), str(row['TOTAL PROYECTO']), str(row['Asistencia']), str(row['Ser']), str(row['TOTAL FINAL'])])
                
            t = Table(data, colWidths=[200, 60, 60, 50, 50, 60])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B3C5D")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F7FA")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            story.append(t)
            doc.build(story)
            buffer.seek(0)
            return buffer

        pdf_data = generar_pdf_grupo(st.session_state.alumnos_db, grupo_nombre, cuatrimestre)
        
        st.info("Haz clic en el botón inferior para generar una hoja limpia en formato PDF con los resultados de todo el grupo.")
        st.download_button(
            label="📥 DESCARGAR REPORTE EN PDF",
            data=pdf_data,
            file_name=f"Reporte_{grupo_nombre}_{cuatrimestre.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
else:
    st.warning("⚠️ No hay datos cargados todavía.")
    st.info("Usa el menú de la izquierda para configurar los porcentajes de evaluación y cargar el archivo Excel de este bimestre.")
