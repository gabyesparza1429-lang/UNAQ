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
        "configuraciones_grupos": st.session_state.configuraciones_grupos
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

if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = cargar_datos_permanentes()

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Configuración adaptativa de Evaluación Continua (30% Global). Extractor optimizado Multi-Nivel.")
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
            if os.path.exists(ARCHIVO_BD):
                os.remove(ARCHIVO_BD)
            st.rerun()

# VISTA DE CARGA INICIAL CON PARSER INTELIGENTE MEJORADO
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
            carrera_actual = ""
            nivel_actual = ""
            
            for linea in lineas:
                linea_limpia = linea.replace('"', '').replace(',', '').replace('\'', '').strip()
                if not linea_limpia or len(linea_limpia) < 3:
                    continue
                
                # 1. EXTRACTOR FLEXIBLE DE NIVEL: Busca cualquier número con punto decimal (ej: 1.4, 2.2)
                match_nivel = re.search(r'(?:A|B|FR)?-?(\d\.\d)', linea_limpia, re.IGNORECASE)
                if match_nivel:
                    nivel_actual = f"A{match_nivel.group(1)}"
                
                # 2. EXTRACTOR FLEXIBLE DE CARRERA: Busca códigos de planes (ej: IDMA, IAMAM, IALUM)
                match_carrera = re.search(r'\b([A-Z]{3,5})\d{4}\b', linea_limpia, re.IGNORECASE)
                if match_carrera:
                    carrera_actual = match_carrera.group(1).upper()
                elif "IDMA" in linea_limpia.upper():
                    carrera_actual = "IDMA"
                elif "IAMAM" in linea_limpia.upper():
                    carrera_actual = "IAMAM"

                # Si no se ha detectado carrera pero sí nivel, o viceversa, se asumen valores base para no perder datos
                if carrera_actual == "": 
                    carrera_temp = "CARRERA"
                else: 
                    carrera_temp = carrera_actual
                    
                if nivel_actual == "": 
                    nivel_temp = "NIVEL"
                else: 
                    nivel_temp = nivel_actual
                
                grupo_compuesto = f"{carrera_temp} {nivel_temp}"
                
                if any(bloqueo in linea_limpia.lower() for bloqueo in palabras_bloqueadas):
                    continue
                
                # Limpieza estricta de códigos del renglón del estudiante
                linea_limpia = re.sub(r'\b[A-Z]+\d{4}\b', '', linea_limpia, flags=re.IGNORECASE).strip()
                linea_limpia = re.sub(r'\b\d+\b', '', linea_limpia).strip()
                linea_limpia = re.sub(r'A?-?FR-?\d\.\d', '', linea_limpia, flags=re.IGNORECASE).strip()
                
                if len(linea_limpia.split()) >= 2 and not "INGLES" in linea_limpia.upper():
                    if grupo_compuesto not in diccionario_grupos:
                        diccionario_grupos[grupo_compuesto] = []
                    diccionario_grupos[grupo_compuesto].append(linea_limpia.upper())
            
            # Formatear y empaquetar los grupos procesados
            for grupo, lista_alumnos in diccionario_grupos.items():
                lista_final_alumnos = sorted(list(set(lista_alumnos)))
                if lista_final_alumnos:
                    df_init = pd.DataFrame({'Alumno': lista_final_alumnos})
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
            
            if st.session_state.base_datos_grupos:
                guardar_datos_permanentes()
                st.success("🎉 ¡Listas analizadas con éxito! Revisa la barra izquierda para cambiar de salón.")
                st.rerun()

# INTERFAZ DE OPERACIÓN DIARIA
else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos[grupo_seleccionado]
    
    tab_tabla, tab_captura, tab_reportes, tab_admin = st.tabs([
        "📊 Cuadrícula del Grupo", "📝 Captura de Calificaciones", "🖨️ Reportes PDF", "🛠️ Administrar Salón"
    ])
    
    with tab_tabla:
        st.header(f"📊 Concentrado General - {grupo_seleccionado}")
        st.caption(f"Cuatrimestre: {cuatrimestre} | Equivalente al 30% de la Calificación del Cuatrimestre")
        
        cols_mostrar = ['Alumno']
        if cfg['w_quiz'] > 0:
            for q in range(1, cfg['num_quizes'] + 1): cols_mostrar.append(f"Quiz {q}")
            cols_mostrar.append('TOTAL QUIZ')
        if cfg['w_proyecto'] > 0:
            for p in range(1, cfg['num_proyectos'] + 1): cols_mostrar.append(f"Proyecto {p}")
            cols_mostrar.append('TOTAL PROYECTO')
        if cfg['w_asistencia'] > 0:
            cols_mostrar.extend(['Días Asistidos', 'Asistencia'])
        if cfg['w_firmas'] > 0:
            cols_mostrar.extend(['Firmas Registradas', 'TOTAL FIRMAS'])
        if cfg['w_ser'] > 0:
            cols_mostrar.append('Ser')
        cols_mostrar.extend(['NOTA BASE 10', 'PUNTAJE 30%'])
        
        cols_finales = [c for c in cols_mostrar if c in df_grupo.columns]
        st.dataframe(df_grupo[cols_finales], use_container_width=True, hide_index=True)

    with tab_captura:
        st.subheader(f"✍️ Captura de Notas - Grupo Actual: {grupo_seleccionado}")
        if not df_grupo.empty:
            alumno_seleccionado = st.selectbox("👤 Selecciona al alumno:", df_grupo['Alumno'].tolist(), key=f"sel_al_{grupo_seleccionado}")
            idx = df_grupo[df_grupo['Alumno'] == alumno_seleccionado].index[0]
            
            col1, col2, col3 = st.columns(3)
            
            valores_quizes = []
            with col1:
                if cfg['w_quiz'] > 0:
                    st.markdown(f"### 📝 {cfg['n_quiz']} ({cfg['w_quiz']}% )")
                    for q_idx in range(1, cfg['num_quizes'] + 1):
                        col_q_name = f"Quiz {q_idx}"
                        val_def = float(df_grupo.at[idx, col_q_name]) if col_q_name in df_grupo.columns else 0.0
                        v_q = st.number_input(f"{col_q_name} (0-10)", 0.0, 10.0, val_def, 0.1, key=f"inp_q{q_idx}_{idx}")
                        valores_quizes.append((col_q_name, v_q))
                else:
                    st.caption("Quizes desactivados.")
                
            valores_proyectos = []
            dias_del_alumno = 0
            with col2:
                if cfg['w_proyecto'] > 0 or cfg['w_asistencia'] > 0:
                    st.markdown("### 🏗️ Entregables y Asistencias")
                    if cfg['w_proyecto'] > 0:
                        for p_idx in range(1, cfg['num_proyectos'] + 1):
                            col_p_name = f"Proyecto {p_idx}"
                            val_def = float(df_grupo.at[idx, col_p_name]) if col_p_name in df_grupo.columns else 0.0
                            v_p = st.number_input(f"{col_p_name} (0-10)", 0.0, 10.0, val_def, 0.1, key=f"inp_p{p_idx}_{idx}")
                            valores_proyectos.append((col_p_name, v_p))
                    if cfg['w_asistencia'] > 0:
                        st.markdown(f"**Días totales del cuatrimestre: {cfg['dias_asistencia']}**")
                        val_as_def = int(df_grupo.at[idx, 'Días Asistidos']) if 'Días Asistidos' in df_grupo.columns else int(cfg['dias_asistencia'])
                        dias_del_alumno = st.number_input("Días que asistió el alumno:", 0, int(cfg['dias_asistencia']), val_as_def, 1, key=f"as_{idx}")
                else:
                    st.caption("Entregables y asistencias desactivados.")
                        
            firmas_alumno = 0
            ser = 0.0
            with col3:
                if cfg['w_firmas'] > 0 or cfg['w_ser'] > 0:
                    st.markdown("### 📋 Firmas y Actitud")
                    if cfg['w_firmas'] > 0:
                        st.markdown(f"**Total de firmas programadas: {cfg['num_firmas']}**")
                        val_fi_def = int(df_grupo.at[idx, 'Firmas Registradas']) if 'Firmas Registradas' in df_grupo.columns else int(cfg['num_firmas'])
                        firmas_alumno = st.number_input("Firmas obtenidas por el alumno:", 0, int(cfg['num_firmas']), val_fi_def, 1, key=f"fi_{idx}")
                    if cfg['w_ser'] > 0:
                        val_ser = float(df_grupo.at[idx, 'Ser']) if 'Ser' in df_grupo.columns else 0.0
                        ser = st.number_input(f"Nota de {cfg['n_ser']} (0-10)", 0.0, 10.0, val_ser, 0.1, key=f"se_{idx}")
                else:
                    st.caption("Firmas y rasgos de actitud desactivados.")
                        
            if st.button("💾 Guardar y Calcular Proporción Parcial", type="primary", use_container_width=True):
                t_quiz = 0.0
                if cfg['w_quiz'] > 0 and valores_quizes:
                    suma_quizes = 0.0
                    for col_q, val_q in valores_quizes:
                        df_grupo.at[idx, col_q] = val_q
                        suma_quizes += val_q
                    t_quiz = suma_quizes / cfg['num_quizes']
                    df_grupo.at[idx, 'TOTAL QUIZ'] = round(t_quiz, 2)
                
                t_proyecto = 0.0
                if cfg['w_proyecto'] > 0 and valores_proyectos:
                    suma_proy = 0.0
                    for col_p, val_p in valores_proyectos:
                        df_grupo.at[idx, col_p] = val_p
                        suma_proy += val_p
                    t_proyecto = suma_proy / cfg['num_proyectos']
                    df_grupo.at[idx, 'TOTAL PROYECTO'] = round(t_proyecto, 2)
                
                nota_asistencia = 0.0
                if cfg['w_asistencia'] > 0:
                    df_grupo.at[idx, 'Días Asistidos'] = dias_del_alumno
                    nota_asistencia = (dias_del_alumno / cfg['dias_asistencia']) * 10.0
                    df_grupo.at[idx, 'Asistencia'] = round(nota_asistencia, 2)
                
                nota_firmas = 0.0
                if cfg['w_firmas'] > 0:
                    df_grupo.at[idx, 'Firmas Registradas'] = firmas_alumno
                    nota_firmas = (firmas_alumno / cfg['num_firmas']) * 10.0
                    df_grupo.at[idx, 'TOTAL FIRMAS'] = round(nota_firmas, 2)
                
                if cfg['w_ser'] > 0: df_grupo.at[idx, 'Ser'] = ser
                
                p_quiz = (t_quiz * (cfg['w_quiz'] / 100)) if cfg['w_quiz'] > 0 else 0.0
                p_proy = (t_proyecto * (cfg['w_proyecto'] / 100)) if cfg['w_proyecto'] > 0 else 0.0
                p_asist = (nota_asistencia * (cfg['w_asistencia'] / 100)) if cfg['w_asistencia'] > 0 else 0.0
                p_firmas = (nota_firmas * (cfg['w_firmas'] / 100)) if cfg['w_firmas'] > 0 else 0.0
                p_ser = (ser * (cfg['w_ser'] / 100)) if cfg['w_ser'] > 0 else 0.0
                
                nota_base_10 = p_quiz + p_proy + p_asist + p_firmas + p_ser
                df_grupo.at[idx, 'NOTA BASE 10'] = round(nota_base_10, 2)
                
                puntaje_30 = nota_base_10 * 0.3
                df_grupo.at[idx, 'PUNTAJE 30%'] = round(puntaje_30, 2)
                
                st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
                guardar_datos_permanentes()
                st.success(f"💾 Guardado. Nota base 10: {round(nota_base_10,2)} | Puntaje Parcial Escalado al 30%: {round(puntaje_30, 2)} / 3.0")
                st.rerun()
        else:
            st.warning("Este grupo no tiene alumnos registrados.")

    with tab_reportes:
        st.header(f"🖨️ Reporte Imprimible PDF ({grupo_seleccionado})")
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
            if c['w_quiz'] > 0: headers.append(c['n_quiz'][:6])
            if c['w_proyecto'] > 0: headers.append(c['n_proyecto'][:6])
            if c['w_asistencia'] > 0: headers.append("Asist.")
            if c['w_firmas'] > 0: headers.append("Firmas")
            headers.extend(["Nota /10", "Puntaje (30%)"])
            
            data = [headers]
            for _, row in df.iterrows():
                fila = [row['Alumno'][:20]]
                if c['w_quiz'] > 0: fila.append(str(row['TOTAL QUIZ']))
                if c['w_proyecto'] > 0: fila.append(str(row['TOTAL PROYECTO']))
                if c['w_asistencia'] > 0: fila.append(str(row['Asistencia']))
                if c['w_firmas'] > 0: fila.append(str(row['TOTAL FIRMAS']))
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
        st.header("🛠️ Panel de Control - Administrar Salón y Listas")
        
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
