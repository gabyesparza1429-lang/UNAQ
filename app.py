import streamlit as st
import pandas as pd
import io
import re

# 1. Configuración inicial de la interfaz web
st.set_page_config(page_title="GEM UNAQ - Control de Notas", layout="wide")

# Inicializar los contenedores de memoria temporal dentro de la app
if 'base_datos_grupos' not in st.session_state:
    st.session_state.base_datos_grupos = {}
if 'configuraciones_grupos' not in st.session_state:
    st.session_state.configuraciones_grupos = {}

st.title("✈️ Generador de Interfaces GEM - UNAQ")
st.write("Estructura Unificada de Control de Notas y Rescate de Alumnos.")
st.write("---")

# 2. BARRA LATERAL IZQUIERDA
with st.sidebar:
    st.header("📋 Datos del Curso")
    cuatrimestre = st.text_input("Cuatrimestre actual:", "MAYO-AGOSTO 2026")
    
    # Si ya procesamos listas, mostrar los grupos en un menú desplegable
    if st.session_state.base_datos_grupos:
        lista_de_grupos = list(st.session_state.base_datos_grupos.keys())
        grupo_seleccionado = st.selectbox("📂 Seleccione el Grupo para Trabajar:", lista_de_grupos)
        
        # Configuración de rubros por defecto para el grupo
        cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
            'w_quiz': 30, 'w_proyecto': 30, 'w_asistencia': 15, 'w_firmas': 15, 'w_ser': 10
        })

# 3. PANTALLA PRINCIPAL: SI NO HAY LISTAS CARGADAS, MOSTRAR PANEL DE INICIO
if not st.session_state.base_datos_grupos:
    st.header("📂 Carga Inicial o Restauración de Listas")
    st.info("Pega aquí el bloque de texto de tus listas institucionales o sube un respaldo previo.")
    
    pestana_pegar, pestana_archivo = st.tabs(["📋 Método 1: Pegar Texto de la Lista", "📁 Método 2: Subir Respaldo Guardado (.csv)"])
    
    with pestana_pegar:
        texto_pegado = st.text_area("Pega aquí el contenido de tus listas de la UNAQ (puedes pegar todas juntas):", height=300)
        
        if st.button("✨ Procesar Texto y Crear Grupos", type="primary", use_container_width=True):
            if texto_pegado.strip():
                lineas = [l.strip() for l in texto_pegado.split('\n') if l.strip()]
                diccionario_grupos = {}
                grupo_actual = "GENERAL"
                
                i = 0
                while i < len(lineas):
                    linea = lineas[i]
                    
                    # Identificar cambio de grupo
                    if "GRUPO DOCENTE" in linea or linea == "GRUPO" or "INGLESING" in linea:
                        if i + 1 < len(lineas):
                            # Buscar la línea que tiene el formato del código del grupo (contiene números y guiones)
                            for offset in range(1, 4):
                                if i + offset < len(lineas) and "-" in lineas[i + offset]:
                                    potencial_grupo = lineas[i + offset].replace("HERNANDEZ FLORES OSCAR", "").strip()
                                    if potencial_grupo:
                                        grupo_actual = potencial_grupo
                                        break
                        if grupo_actual not in diccionario_grupos:
                            diccionario_grupos[grupo_actual] = []
                    
                    # Identificar renglón de alumno por patrón: Número Matrícula Resto
                    match_alumno = re.match(r'^(\d+)\s+(\d+)\s+(.+)$', linea)
                    if match_alumno:
                        matricula = match_alumno.group(2)
                        resto = match_alumno.group(3)
                        
                        # Revisar si el plan viene al final
                        match_plan = re.search(r'\s+([A-Z\d]{4,10})$', resto)
                        if match_plan:
                            plan = match_plan.group(1)
                            nombre = resto[:match_plan.start()].strip()
                        else:
                            nombre = resto
                            plan = "UNAQ"
                            # Si no tiene plan, checar si el nombre sigue en la línea de abajo
                            if i + 1 < len(lineas) and not re.match(r'^\d+', lineas[i + 1]) and "DEPARTAMENTO" not in lineas[i + 1]:
                                i += 1
                                match_plan_sig = re.search(r'\s+([A-Z\d]{4,10})$', lineas[i])
                                if match_plan_sig:
                                    plan = match_plan_sig.group(1)
                                    nombre = f"{nombre} {lineas[i][:match_plan_sig.start()].strip()}"
                                else:
                                    nombre = f"{nombre} {lineas[i]}"
                        
                        # Limpiar el nombre
                        nombre_limpio = re.sub(r'\s+', ' ', nombre).replace("PLAN ESTUDIOS", "").strip().upper()
                        
                        if grupo_actual not in diccionario_grupos:
                            diccionario_grupos[grupo_actual] = []
                            
                        diccionario_grupos[grupo_actual].append({
                            "Matrícula": matricula,
                            "Alumno": nombre_limpio,
                            "Plan": plan
                        })
                    i += 1
                
                # Convertir los datos extraídos en DataFrames listos con columnas de notas
                for grupo, alumnos in diccionario_grupos.items():
                    if alumnos:
                        df_init = pd.DataFrame(alumnos)
                        # Agregar las columnas para calificaciones en blanco
                        df_init["Quiz 1"] = 0.0
                        df_init["Quiz 2"] = 0.0
                        df_init["Quiz 3"] = 0.0
                        df_init["Quiz 4"] = 0.0
                        df_init["TOTAL QUIZ"] = 0.0
                        df_init["Proyecto 1"] = 0.0
                        df_init["Proyecto 2"] = 0.0
                        df_init["TOTAL PROYECTO"] = 0.0
                        df_init["Días Asistidos"] = 32
                        df_init["Asistencia"] = 10.0
                        df_init["Firmas Registradas"] = 15
                        df_init["TOTAL FIRMAS"] = 10.0
                        df_init["Ser"] = 0.0
                        df_init["NOTA BASE 10"] = 0.0
                        df_init["PUNTAJE 30%"] = 0.0
                        
                        st.session_state.base_datos_grupos[grupo] = df_init
                st.rerun()

    with pestana_archivo:
        archivo_subido = st.file_uploader("Arrastra aquí el archivo .csv de respaldo que descargaste previamente:", type=["csv"])
        if archivo_subido is not None:
            try:
                df_recuperado = pd.read_csv(archivo_subido)
                nombre_g = archivo_subido.name.replace("Respaldo_Notas_", "").replace(".csv", "")
                st.session_state.base_datos_grupos[nombre_g] = df_recuperado
                st.success(f"🎉 ¡Grupo '{nombre_g}' restaurado con éxito desde tu archivo local!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo de respaldo: {e}")

# 4. PANTALLA PRINCIPAL: SI YA HAY UN GRUPO ACTIVO, MOSTRAR CUADRÍCULA Y CAPTURA
else:
    df_grupo = st.session_state.base_datos_grupos[grupo_seleccionado]
    cfg = st.session_state.configuraciones_grupos.get(grupo_seleccionado, {
        'w_quiz': 30, 'w_proyecto': 30, 'w_asistencia': 15, 'w_firmas': 15, 'w_ser': 10
    })
    
    st.success(f"📋 Grupo actual: {grupo_seleccionado}")
    
    # 💾 BOTÓN MAESTRO DE RESPALDO LOCAL DE SEGURIDAD
    csv_buffer = io.StringIO()
    df_grupo.to_csv(csv_buffer, index=False)
    st.download_button(
        label="💾 DESCARGAR RESPALDO DE SEGURIDAD ACTUAL (GUARDAR EN TU PC)",
        data=csv_buffer.getvalue(),
        file_name=f"Respaldo_Notas_{grupo_seleccionado}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.write("---")
    
    # Pestañas de control internas
    tab_tabla, tab_captura_manual, tab_cambiar = st.tabs(["📊 Ver Calificaciones", "📝 Capturar Notas Celda por Celda", "🔄 Salir / Cargar Otro Texto"])
    
    with tab_tabla:
        st.subheader("Cuadrícula General de Evaluaciones")
        st.dataframe(df_grupo, use_container_width=True, hide_index=True)
        
    with tab_captura_manual:
        st.subheader("Formulario de Captura Rápida")
        alumno_sel = st.selectbox("👤 Selecciona al Estudiante:", df_grupo['Alumno'].tolist())
        idx = df_grupo[df_grupo['Alumno'] == alumno_sel].index[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 📝 Quizes")
            q1 = st.number_input("Quiz 1:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 1"]))
            q2 = st.number_input("Quiz 2:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 2"]))
            q3 = st.number_input("Quiz 3:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 3"]))
            q4 = st.number_input("Quiz 4:", 0.0, 10.0, float(df_grupo.at[idx, "Quiz 4"]))
        with c2:
            st.markdown("### 🏗️ Proyectos")
            p1 = st.number_input("Proyecto 1:", 0.0, 10.0, float(df_grupo.at[idx, "Proyecto 1"]))
            p2 = st.number_input("Proyecto 2:", 0.0, 10.0, float(df_grupo.at[idx, "Proyecto 2"]))
        with c3:
            st.markdown("### 📋 Asistencia y Rasgos")
            d_asist = st.number_input("Días Asistidos (Max 32):", 0, 32, int(df_grupo.at[idx, "Días Asistidos"]))
            f_firmas = st.number_input("Firmas / Tareas (Max 15):", 0, 15, int(df_grupo.at[idx, "Firmas Registradas"]))
            v_ser = st.number_input("Nota SER / Actitud:", 0.0, 10.0, float(df_grupo.at[idx, "Ser"]))
            
        if st.button("💾 Guardar y Calcular Notas de este Alumno", type="primary", use_container_width=True):
            # Inyectar valores manuales
            df_grupo.at[idx, "Quiz 1"] = q1
            df_grupo.at[idx, "Quiz 2"] = q2
            df_grupo.at[idx, "Quiz 3"] = q3
            df_grupo.at[idx, "Quiz 4"] = q4
            df_grupo.at[idx, "Proyecto 1"] = p1
            df_grupo.at[idx, "Proyecto 2"] = p2
            df_grupo.at[idx, "Días Asistidos"] = d_asist
            df_grupo.at[idx, "Firmas Registradas"] = f_firmas
            df_grupo.at[idx, "Ser"] = v_ser
            
            # Realizar operaciones matemáticas automáticas
            t_q = round((q1 + q2 + q3 + q4) / 4.0, 2)
            t_p = round((p1 + p2) / 2.0, 2)
            t_as = round((d_asist / 32.0) * 10.0, 2)
            t_fi = round((f_firmas / 15.0) * 10.0, 2)
            
            df_grupo.at[idx, "TOTAL QUIZ"] = t_q
            df_grupo.at[idx, "TOTAL PROYECTO"] = t_p
            df_grupo.at[idx, "Asistencia"] = t_as
            df_grupo.at[idx, "TOTAL FIRMAS"] = t_fi
            
            # Ponderación Base 10: Quizes 30%, Proyectos 30%, Asistencia 15%, Firmas 15%, SER 10%
            n_b10 = (t_q * 0.3) + (t_p * 0.3) + (t_as * 0.15) + (t_fi * 0.15) + (v_ser * 0.1)
            df_grupo.at[idx, "NOTA BASE 10"] = round(n_b10, 1)
            df_grupo.at[idx, "PUNTAJE 30%"] = round(n_b10 * 0.3, 2)
            
            st.session_state.base_datos_grupos[grupo_seleccionado] = df_grupo
            st.success(f"🎉 Notas de {alumno_sel} calculadas e inyectadas correctamente.")
            st.rerun()
            
    with tab_cambiar:
        if st.button("⚠️ Volver al inicio (Borrar tablas temporales de la pantalla)", type="destructive"):
            st.session_state.base_datos_grupos = {}
            st.rerun()
