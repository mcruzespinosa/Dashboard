import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime

st.set_page_config(page_title="Incident App", layout="wide")

# Sidebar con menú tipo hamburger
with st.sidebar:
    selected = option_menu(
        menu_title="☰ Menú",  # título del menú
        options=["Inicio", "Registro de horas", "Reporte de Incidencia", "Historial"],
        icons=["house", "clipboard-check", "clock-history"],
        default_index=0
    )

# Inicio
if selected == "Inicio":
    st.title("📌 DASHBOARD")
    st.markdown("RECUERDA REGISTRAR TUS HORAS")

# Formulario
elif selected == "Reporte de Incidencia":
    st.title("📝 Reporte de Incidencia")

    with st.form("incident_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Responsable")
            department = st.text_input("Área o Departamento")
            phone = st.text_input("Cantidad Dañadas")
            date = st.date_input("Fecha")
        
        with col2:
            time = st.time_input("Hora")
            location = st.text_input("Codigo de pieza")
            police = st.selectbox("Destino de Pieza", ["Retrabajo", "Scrap"])
        
        incident_details = st.text_area("Descripción del incidente", height=150)
        actions = st.text_area("Acciones correctivas", height=100)
        image = st.file_uploader("Imagen de la incidencia", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Generar Reporte")

    if submitted:
        st.success("✅ Reporte registrado")
        st.write(f"**Nombre:** {name}")
        st.write(f"**Fecha:** {date}")
        st.write(f"**Hora:** {time}")
        if image:
            st.image(image, width=300)

# Historial (simulado)
elif selected == "Historial":
    st.title("📚 Historial de Reportes")
    st.info("Aquí se podrían listar todos los reportes generados.")
