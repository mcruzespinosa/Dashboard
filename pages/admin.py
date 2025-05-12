import streamlit as st
from database import verify_user, add_user, eliminar_ingeniero,obtener_proyectos_con_horas,load_db_path, add_incident, get_incidents, create_tables, get_exam,obtener_ingenieros,asignar_proyecto
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import io
import os

if "user" not in st.session_state or st.session_state.user.lower() != "martin cruz":
    st.error("No tienes acceso a esta página.")
    st.stop()

menu = st.selectbox(
    "Selecciona una sección:",
    ["Resumen", "Registros de usuarios", "Reportes de incidencias", "Resultados Psicometricos", "Dar de baja usuario","Asignar proyecto",]
)

# 🎯 Mostrar contenido según la opción elegida
if menu == "Resumen":
    st.subheader("📊 Resumen general")
    menu = st.selectbox(
    "Selecciona un empleado:",
    ["Luis Avena", "Andrea Tapia", "martin cruz"]
    )
    if menu=="Luis Avena":
        usuario = "Luis Avena"

     # Conectar a la base de datos y consultar los datos
        import sqlite3
        import pandas as pd

        DB_PATH = load_db_path()  # Asegúrate de tener el path correcto o usar load_db_path()

        # Consultar horas trabajadas por proyecto
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT proyecto, SUM(duracion) as total_duracion
            FROM registros
            WHERE usuario = ?
            GROUP BY proyecto
            ORDER BY total_duracion DESC
        """
        df = pd.read_sql_query(query, conn, params=(usuario,))
        conn.close()

        # Verificar si los datos existen
        if df.empty:
            st.info("No hay registros de tiempo para mostrar.")
        else:
            # Función para convertir la duración de formato 'HH:MM:SS' a horas flotantes
            def time_to_hours(time_str):
                # Verificar si el valor es una cadena
                if isinstance(time_str, str):
                    try:
                        h, m, s = map(int, time_str.split(":"))
                        return h + m / 60 + s / 3600
                    except ValueError:
                        st.error(f"El valor de duración '{time_str}' no es válido.")
                    return 0
                elif isinstance(time_str, float):
                    # Si ya es un número flotante, lo devolvemos tal cual
                    return time_str
                else:
                    # Para otros casos, devolvemos 0 (o podrías manejarlo de otra forma)
                    return 0

            # Asegurarnos de que la columna 'total_duracion' esté en el formato correcto
            df['total_duracion'] = df['total_duracion'].apply(time_to_hours)

            # Mostrar los datos en una tabla antes de graficar
            st.write("**Horas trabajadas por proyecto:**")
            st.write(df)


elif menu == "Registros de usuarios":
    st.subheader("👥 Lista de usuarios")
    with st.form("register_form"):
            new_user = st.text_input("Nuevo usuario")
            new_pass = st.text_input("Contraseña", type="password")
            confirm = st.text_input("Confirmar contraseña", type="password")
            reg_submit = st.form_submit_button("Registrar")
            if reg_submit:
                if new_pass != confirm:
                    st.warning("⚠️ Las contraseñas no coinciden.")
                else:
                    db_path = load_db_path()
                    if add_user(new_user, new_pass):  # ✅ solo dos argumentos
                        st.success("✅ Usuario registrado con éxito.")
                    else:
                        st.error("❌ No se pudo registrar el usuario.")

elif menu == "Reportes de incidencias":
    st.subheader("📝 Reportes de incidencias")
    menu = st.selectbox(
    "Selecciona un empleado:",
    ["Luis Avena", "Andrea Tapia", "martin cruz"]
    )

    if menu == "Luis Avena":
        records = get_incidents("Luis Avena")
        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["id", "area", "cantidad", "fecha", "hora", "codigo_pieza", "destino", "created_at"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Reporte #{rec['id']} - {rec['created_at'][:19]}"):
                    st.write(f"**Área:** {rec['area']}")
                    st.write(f"**Cantidad Dañadas:** {rec['cantidad']}")
                    st.write(f"**Fecha / Hora:** {rec['fecha']} {rec['hora']}")
                    st.write(f"**Código de Pieza:** {rec['codigo_pieza']}")
                    st.write(f"**Destino:** {rec['destino']}")
                    st.write(f"**Descripción:** {rec['descripcion']}")
                    st.write(f"**Acciones Correctivas:** {rec['acciones']}")
        
    elif menu == "Andrea Tapia":
        records = get_incidents("Andrea Tapia")
        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["id", "area", "cantidad", "fecha", "hora", "codigo_pieza", "destino", "created_at"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Reporte #{rec['id']} - {rec['created_at'][:19]}"):
                    st.write(f"**Área:** {rec['area']}")
                    st.write(f"**Cantidad Dañadas:** {rec['cantidad']}")
                    st.write(f"**Fecha / Hora:** {rec['fecha']} {rec['hora']}")
                    st.write(f"**Código de Pieza:** {rec['codigo_pieza']}")
                    st.write(f"**Destino:** {rec['destino']}")
                    st.write(f"**Descripción:** {rec['descripcion']}")
                    st.write(f"**Acciones Correctivas:** {rec['acciones']}")

    elif menu == "martin cruz":
        records = get_incidents("martin cruz")
        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["id", "area", "cantidad", "fecha", "hora", "codigo_pieza", "destino", "created_at"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Reporte #{rec['id']} - {rec['created_at'][:19]}"):
                    st.write(f"**Área:** {rec['area']}")
                    st.write(f"**Cantidad Dañadas:** {rec['cantidad']}")
                    st.write(f"**Fecha / Hora:** {rec['fecha']} {rec['hora']}")
                    st.write(f"**Código de Pieza:** {rec['codigo_pieza']}")
                    st.write(f"**Destino:** {rec['destino']}")
                    st.write(f"**Descripción:** {rec['descripcion']}")
                    st.write(f"**Acciones Correctivas:** {rec['acciones']}")
                

elif menu == "Examen psicometrico":
    userexam = st.radio("A quien quieres hacerle el Examen ", ['Ramon Fausto', 'Noel Ramirez', 'Andrea Tapia'])
    activate=True

elif menu =="Resultados Psicometricos":
    st.title("📚 Historial de Examenes")
    st.info("Aquí se podrían los resultados de los Examenes generados anteriormente.")
    # Obtener los examenes del usuario logueado
    menu = st.selectbox(
    "Selecciona un empleado:",
    ["Luis Avena", "Andrea Tapia", "martin cruz"]
    )
    if menu == "Luis Avena":
        records = get_exam("Luis Avena")

        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["nombre", "fecha", "puntaje_tecnico", "responsabilidad", "adaptabilidad", 
                    "trabajo_equipo", "manejo_estres", "flexibilidad"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Nombre #{rec['nombre']}"):
                    st.write(f"**Puntaje tecnico:** {rec['puntaje_tecnico']}")
                    st.write(f"**Responsabilidad:** {rec['responsabilidad']}")
                    st.write(f"**Adaptabilidad:** {rec['adaptabilidad']}")
                    st.write(f"**Trabajo_equipo:** {rec['trabajo_equipo']}")
                    st.write(f"**Manejo_estres:** {rec['manejo_estres']}")
                    st.write(f"**Flexibilidad:** {rec['flexibilidad']}")
                
    elif menu == "Andrea Tapia":
        records = get_exam("Andrea Tapia")

        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["nombre", "fecha", "puntaje_tecnico", "responsabilidad", "adaptabilidad", 
                    "trabajo_equipo", "manejo_estres", "flexibilidad"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Nombre #{rec['nombre']}"):
                    st.write(f"**Puntaje tecnico:** {rec['puntaje_tecnico']}")
                    st.write(f"**Responsabilidad:** {rec['responsabilidad']}")
                    st.write(f"**Adaptabilidad:** {rec['adaptabilidad']}")
                    st.write(f"**Trabajo_equipo:** {rec['trabajo_equipo']}")
                    st.write(f"**Manejo_estres:** {rec['manejo_estres']}")
                    st.write(f"**Flexibilidad:** {rec['flexibilidad']}")


    elif menu == "martin cruz":
        records = get_exam("martin cruz")

        if not records:
            st.info("No hay reportes registrados aún.")
        else:
            # Mostrar tabla de reportes
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df[["nombre", "fecha", "puntaje_tecnico", "responsabilidad", "adaptabilidad", 
                    "trabajo_equipo", "manejo_estres", "flexibilidad"]])

            # Mostrar detalles del reporte
            for rec in records:
                with st.expander(f"Nombre #{rec['nombre']}"):
                    st.write(f"**Puntaje tecnico:** {rec['puntaje_tecnico']}")
                    st.write(f"**Responsabilidad:** {rec['responsabilidad']}")
                    st.write(f"**Adaptabilidad:** {rec['adaptabilidad']}")
                    st.write(f"**Trabajo_equipo:** {rec['trabajo_equipo']}")
                    st.write(f"**Manejo_estres:** {rec['manejo_estres']}")
                    st.write(f"**Flexibilidad:** {rec['flexibilidad']}")
               
elif menu =="Dar de baja usuario":
     
     st.subheader("Dar de baja usuario")
     ingenieros = obtener_ingenieros()
     if ingenieros:
        ingeniero_eliminar = st.selectbox("Selecciona un Ingeniero para Eliminar", ingenieros)
        if st.button("Eliminar Ingeniero") and ingeniero_eliminar:
            eliminar_ingeniero(ingeniero_eliminar)
            st.success(f"Ingeniero '{ingeniero_eliminar}' eliminado")
            ingenieros.remove(ingeniero_eliminar)

elif menu=="Asignar proyecto":
    st.subheader("Asignar Proyectos")
    ingenieros = obtener_ingenieros()
    if ingenieros:
        ingeniero = st.selectbox("Selecciona un Ingeniero", ingenieros)
        numero_proyecto = st.text_input("Número de Proyecto")
        nombre_proyecto = st.text_input("Nombre del Proyecto")
        horas_cotizadas = st.number_input("Horas Cotizadas", min_value=1, step=1)
        
        if st.button("Asignar Proyecto") and ingeniero and nombre_proyecto:
            asignar_proyecto(ingeniero, numero_proyecto, nombre_proyecto, horas_cotizadas)
            st.success(f"Proyecto '{nombre_proyecto}' asignado a {ingeniero}")