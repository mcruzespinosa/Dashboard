import streamlit as st
from database import verify_user,get_connection, add_user, eliminar_ingeniero, obtener_proyectos_con_horas, add_incident, get_incidents, create_tables, get_exam, obtener_ingenieros, asignar_proyecto
import pandas as pd
import psycopg2
from datetime import timedelta

if "user" not in st.session_state or st.session_state.user.lower() != "martin cruz":
    st.error("No tienes acceso a esta página.")
    st.stop()

menu = st.selectbox(
    "Selecciona una sección:",
    ["Resumen", "Registros de usuarios", "Reportes de incidencias", "Resultados Psicometricos", "Dar de baja usuario", "Asignar proyecto"]
)

if menu == "Resumen":
    st.subheader("\U0001F4CA Resumen general")
    usuario = st.selectbox("Selecciona un USUARIO:", ["Luis Avena", "Andrea Tapia", "martin cruz"])
    # Conectar a la base de datos y consultar los datos
    # import sqlite3  # Remove sqlite3 import

    # DB_PATH = load_db_path()  # Remove these lines
    # import pandas as pd

    # Conectar a la base de datos y obtener los datos sin agregarlos

    try:
        # Conexión a la base de datos
        conn = get_connection()
        cursor = conn.cursor()

        # Consulta optimizada
        query = """
        SELECT proyecto, SUM(duracion) as total_duracion
        FROM registros
        WHERE usuario = %s
        GROUP BY proyecto
        """
        cursor.execute(query, (usuario,))
        rows = cursor.fetchall()

        # Verificación rápida de datos vacíos
        if not rows:
            st.info("No hay registros de tiempo para mostrar.")
        else:

            # Crear DataFrame directamente
            df = pd.DataFrame(rows, columns=['proyecto', 'total_duracion'])

            # Convertir intervalos a horas flotantes
            df['duracion_horas'] = df['total_duracion'].apply(lambda x: x.total_seconds() / 3600)

            # Redondear para visualización
            df['horas_redondeadas'] = df['duracion_horas'].round(2)

            # Mostrar tabla
            st.write("*Horas trabajadas por proyecto:*")
            st.dataframe(df[['proyecto', 'horas_redondeadas']])

            # Gráfico de barras
            st.bar_chart(df.set_index('proyecto')['duracion_horas'])

            # Mostrar total acumulado
            total_horas = df['duracion_horas'].sum()
            total_legible = str(timedelta(seconds=int(total_horas * 3600)))
            st.markdown(f"*Total acumulado:* {total_legible} (≈ {round(total_horas, 2)} horas)")

    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        df = pd.DataFrame()  # DataFrame vacío si ocurre un error

    finally:
        # Asegurarse de cerrar la conexión
        if 'conn' in locals() and conn is not None:
            conn.close()

elif menu == "Registros de usuarios":
    st.subheader("\U0001F465 Lista de usuarios")
    with st.form("register_form"):
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Contraseña", type="password")
        confirm = st.text_input("Confirmar contraseña", type="password")
        reg_submit = st.form_submit_button("Registrar")
        if reg_submit:
            if new_pass != confirm:
                st.warning("⚠️ Las contraseñas no coinciden.")
            else:
                if add_user(new_user, new_pass):
                    st.success("✅ Usuario registrado con éxito.")
                else:
                    st.error("❌ No se pudo registrar el usuario.")

elif menu == "Reportes de incidencias":
    st.subheader("\U0001F4DD Reportes de incidencias")
    empleado = st.selectbox("Selecciona un empleado:", ["Luis Avena", "Andrea Tapia", "martin cruz"])
    records = get_incidents(empleado)
    if not records:
        st.info("No hay reportes registrados aún.")
    else:
        df = pd.DataFrame(records)
        st.dataframe(df[["id", "area", "cantidad", "fecha", "hora", "codigo_pieza", "destino", "created_at"]])
        for rec in records:
            with st.expander(f"Reporte #{rec['id']} - {rec['created_at'][:19]}"):
                st.write(f"**Área:** {rec['area']}")
                st.write(f"**Cantidad Dañadas:** {rec['cantidad']}")
                st.write(f"**Fecha / Hora:** {rec['fecha']} {rec['hora']}")
                st.write(f"**Código de Pieza:** {rec['codigo_pieza']}")
                st.write(f"**Destino:** {rec['destino']}")
                st.write(f"**Descripción:** {rec['descripcion']}")
                st.write(f"**Acciones Correctivas:** {rec['acciones']}")

elif menu == "Resultados Psicometricos":
    st.title("\U0001F4DA Historial de Examenes")
    st.info("Aquí se podrían los resultados de los Examenes generados anteriormente.")
    empleado = st.selectbox("Selecciona un empleado:", ["Luis Avena", "Andrea Tapia", "martin cruz"])
    records = get_exam(empleado)
    if not records:
        st.info("No hay reportes registrados aún.")
    else:
        df = pd.DataFrame(records)
        st.dataframe(df[["nombre", "fecha", "puntaje_tecnico", "responsabilidad", "adaptabilidad", "trabajo_equipo", "manejo_estres", "flexibilidad"]])
        for rec in records:
            with st.expander(f"Nombre #{rec['nombre']}"):
                st.write(f"**Puntaje tecnico:** {rec['puntaje_tecnico']}")
                st.write(f"**Responsabilidad:** {rec['responsabilidad']}")
                st.write(f"**Adaptabilidad:** {rec['adaptabilidad']}")
                st.write(f"**Trabajo_equipo:** {rec['trabajo_equipo']}")
                st.write(f"**Manejo_estres:** {rec['manejo_estres']}")
                st.write(f"**Flexibilidad:** {rec['flexibilidad']}")

elif menu == "Dar de baja usuario":
    st.subheader("Dar de baja usuario")
    ingenieros = obtener_ingenieros()
    if ingenieros:
        ingeniero_eliminar = st.selectbox("Selecciona un Ingeniero para Eliminar", ingenieros)
        if st.button("Eliminar Ingeniero") and ingeniero_eliminar:
            eliminar_ingeniero(ingeniero_eliminar)
            st.success(f"Ingeniero '{ingeniero_eliminar}' eliminado")

elif menu == "Asignar proyecto":
    st.subheader("Asignar Proyectos")
    ingenieros = obtener_ingenieros()
    if ingenieros:
        ingeniero = st.selectbox("Selecciona un Ingeniero", ingenieros, key="selectbox_ingeniero")
        numero_proyecto = st.text_input("Número de Proyecto")
        nombre_proyecto = st.text_input("Nombre del Proyecto")
        horas_cotizadas = st.number_input("Horas Cotizadas", min_value=1, step=1)
        if st.button("Asignar Proyecto") and ingeniero and nombre_proyecto:
            asignar_proyecto(ingeniero, numero_proyecto, nombre_proyecto, horas_cotizadas)
            st.success(f"Proyecto '{nombre_proyecto}' asignado a {ingeniero}")

   
