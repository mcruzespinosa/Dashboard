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
    try:
        conn = get_connection()  # Use your PostgreSQL connection function
        cursor = conn.cursor()
        query = """
        SELECT proyecto, SUM(duracion) as total_duracion
        FROM registros
        WHERE usuario = %s
        GROUP BY proyecto
        """
        cursor.execute(query, (usuario,))  # Pass parameters as a tuple
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['proyecto', 'duracion'])  # Create DataFrame
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        df = pd.DataFrame()  # Return an empty DataFrame in case of error
    finally:
        if conn:
            conn.close()

    if df.empty:
        st.info("No hay registros de tiempo para mostrar.")
    else:
        # Función para convertir HH:MM:SS a horas flotantes
        def time_to_hours(time_str):
            try:
                if isinstance(time_str, str):
                    h, m, s = map(int, time_str.strip().split(":"))
                    return h + m / 60 + s / 3600
            except Exception as e:
                st.warning(f"Error en duración '{time_str}': {e}")
            return 0

        # Aplicar la conversión
        df['duracion_horas'] = df['duracion'].apply(time_to_hours)

        # Agrupar por proyecto
        resumen = df.groupby('proyecto')['duracion_horas'].sum().reset_index()
        # Redondear a 2 decimales para visualización
        resumen['horas_redondeadas'] = resumen['duracion_horas'].round(2)
        # Mostrar

        st.write("**Horas trabajadas por proyecto:**")
        st.dataframe(resumen[['proyecto', 'horas_redondeadas']])

        # Gráfico
        st.bar_chart(resumen.set_index('proyecto')['duracion_horas'])
        # ➕ Mostrar total acumulado en HH:MM:SS
        total_horas = resumen['duracion_horas'].sum()
        total_segundos = int(total_horas * 3600)
        total_legible = str(timedelta(seconds=total_segundos))
        st.markdown(f"**Total acumulado:** `{total_legible}` (≈ {round(total_horas, 2)} horas)")

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

   