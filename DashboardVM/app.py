import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
import requests
import io
import os
from database import verify_user, add_user, load_db_path, add_incident, get_incidents, create_tables
from datetime import datetime





# --- CONFIGURACIÓN ---
BACKGROUND_IMG = "registro_incidencias_fondo.jpg"
LOGO_URL = "https://vimexelectronics.mx/wp-content/uploads/2023/07/icon_vimex.png"
# ---------------------

# Función: Inicio de sesión y registro
def login_register():
    st.title("🔐 Ingreso al sistema")
    tab1, tab2 = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab1:
        with st.form("login_form"):
            nombre = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")
            if submitted:
                db_path = load_db_path()
                create_tables()
                if verify_user(nombre, contrasena):  # ✅ solo dos argumentos
                    st.session_state.logged_in = True
                    st.session_state.user = nombre
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")

    with tab2:
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

# Función: Generación de PDF
def generate_pdf(data, incident_img_bytes=None):
    filename = f"{data['Responsable'].replace(' ', '_')}_{data['Fecha']}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    if os.path.exists(BACKGROUND_IMG):
        c.drawImage(BACKGROUND_IMG, 0, 0, width=width, height=height)
    else:
        c.setFillColorRGB(0.6, 0.85, 0.92)
        c.rect(0, 0, width, height, fill=1)

    try:
        resp = requests.get(LOGO_URL, stream=True, timeout=5)
        logo = ImageReader(io.BytesIO(resp.content))
        c.drawImage(logo, 30, height - 80, width=120, height=40, mask="auto")
    except:
        pass

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.white)
    c.drawString(160, height - 60, "Incident Report")

    c.setFont("Helvetica", 10)
    y = height - 100
    line_h = 14
    x = 50

    def write_line(label, val, bold=False, indent=0):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(x + indent, y, f"{label}: {val}")
        y -= line_h

    for k in ["Responsable", "Área", "Cantidad Dañadas", "Fecha", "Hora", "Código de Pieza", "Destino"]:
        write_line(k, data.get(k, ""))

    write_line("Descripción", "", bold=True)
    for ln in data["Descripción"].splitlines():
        write_line("", ln, indent=10)

    write_line("Acciones Correctivas", "", bold=True)
    for ln in data["Acciones Correctivas"].splitlines():
        write_line("", ln, indent=10)

    if incident_img_bytes:
        try:
            img = Image.open(io.BytesIO(incident_img_bytes))
            img.thumbnail((200, 200))
            bio = io.BytesIO()
            img.save(bio, format="JPEG")
            bio.seek(0)
            c.drawImage(ImageReader(bio), width - 240, 80, width=200, height=150, mask="auto")
        except:
            pass

    c.save()
    return filename

# Estado de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Pantalla de login si no ha iniciado sesión
if not st.session_state.logged_in:
    login_register()
    st.stop()

# App principal
st.set_page_config(page_title="Incident App", layout="wide")
st.sidebar.write(f"👤 Usuario: {st.session_state.user}")

with st.sidebar:
    selected = option_menu(
        menu_title="☰ Menú",
        options=["Inicio", "Registro de horas", "Reporte de Incidencia", "Historial"],
        icons=["house", "clock", "clipboard-check", "clock-history"],
        default_index=0
    )


if selected == "Inicio":
    db_path = load_db_path()
    st.title(f"👤 Bienvenido {st.session_state.user} ")
    st.info("Usa el menú para navegar por el sistema.")
     # Verificar si el usuario está logueado
    if "user" not in st.session_state:
        st.error("Por favor, inicie sesión para ver esta sección.")
        st.stop()

    usuario = st.session_state.user

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

        # Graficar la duración por proyecto
        st.bar_chart(df.set_index('proyecto')['total_duracion'])

elif selected == "Registro de horas":
    with:
        name = st.text_input("Responsable")
        department = st.text_input("Área")
        cantidad = st.text_input("Cantidad Dañadas")
        date = st.date_input("Fecha")

elif selected == "Reporte de Incidencia":
    st.title("📝 Reporte de Incidencia")
    
    with st.form("incident_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Responsable")
            department = st.text_input("Área")
            cantidad = st.text_input("Cantidad Dañadas")
            date = st.date_input("Fecha")
        with col2:
            time = st.time_input("Hora")
            codigo_pieza = st.text_input("Código de Pieza")
            destino = st.selectbox("Destino", ["Retrabajo", "Scrap"])
        descripcion = st.text_area("Descripción del incidente", height=150)
        acciones = st.text_area("Acciones correctivas", height=100)
        incident_img_file = st.file_uploader("Imagen del incidente", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Generar Reporte")

    if submitted:
        #empacar datos
        datos = {
            "Responsable": name,
            "Área": department,
            "Cantidad Dañadas": cantidad,
            "Fecha": date.strftime("%Y-%m-%d"),
            "Hora": time.strftime("%H:%M"),
            "Código de Pieza": codigo_pieza,
            "Destino": destino,
            "Descripción": descripcion,
            "Acciones Correctivas": acciones
        }
        img_bytes = incident_img_file.read() if incident_img_file else None
        pdf_file = generate_pdf(datos, img_bytes)

        # Guardar en base de datos
        add_incident(
            usuario=st.session_state.user,
            area=datos["Área"],
            cantidad=datos["Cantidad Dañadas"],
            fecha=datos["Fecha"],
            hora=datos["Hora"],
            codigo=datos["Código de Pieza"],
            destino=datos["Destino"],
            descripcion=datos["Descripción"],
            acciones=datos["Acciones Correctivas"],
            pdf_file=pdf_file
        )

        st.success(f"✅ PDF generado: **{pdf_file}**")
        st.write(f"**Nombre:** {name}")
        st.write(f"**Fecha:** {date}")
        st.write(f"**Hora:** {time}")
        if incident_img_file:
            st.image(incident_img_file, width=300)

        with open(pdf_file, "rb") as f:
            st.download_button("🔽 Descargar PDF", f, file_name=pdf_file, mime="application/pdf")

elif selected == "Historial":
    st.title("📚 Historial de Reportes")
    st.info("Aquí se podrían listar los reportes generados anteriormente.")
   
 # Obtener los reportes del usuario logueado
    records = get_incidents(st.session_state.user)
    
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
                
                # Opción para descargar el PDF
                with open(rec['pdf_file'], "rb") as f:
                    st.download_button(
                        label="🔽 Descargar PDF",
                        data=f,
                        file_name=os.path.basename(rec['pdf_file']),
                        mime="application/pdf"
                    )
                st.write("---")