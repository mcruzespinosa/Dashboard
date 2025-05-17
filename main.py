import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
import requests
import io
import os
from database import verify_user, obtener_ultimo_registro, get_connection, add_user, insertar_registro, \
obtener_proyectos, actualizar_registro, add_incident, get_incidents, create_tables, add_exam,obtener_numero_proyecto
import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
# --- CONFIGURACIÓN ---
BACKGROUND_IMG = "registro_incidencias_fondo.jpg"
LOGO_URL = "https://vimexelectronics.mx/wp-content/uploads/2023/07/icon_vimex.png"
# ---------------------

def mostrar_alerta_cierre():
    if "ultima_fecha_alerta" not in st.session_state or st.session_state.ultima_fecha_alerta != datetime.now().date():
        st.session_state.alerta_mostrada_hoy = False
        st.session_state.ultima_fecha_alerta = datetime.now().date()

    ahora = datetime.now().strftime("%H:%M")
    if ahora == "17:50" and not st.session_state.alerta_mostrada_hoy:
        with st.modal("Recordatorio de Cierre"):
            st.warning("🔔 Recuerda cerrar tus actividades antes de salir.")
            st.button("Cerrar", on_click=lambda: setattr(st.session_state, "alerta_mostrada_hoy", True))

# Llamar a la función al inicio
mostrar_alerta_cierre()




def iniciar_proyecto(usuario, proyecto):
    conn = get_connection()
    cursor = conn.cursor()
    inicio = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO registros (usuario, proyecto, inicio, activo)
        VALUES (?, ?, ?, 1)
    """, (usuario, proyecto, inicio))
    conn.commit()
    conn.close()





def terminar_proyecto(registro_id):
    conn = get_connection()
    cursor = conn.cursor()
    fin = datetime.now().isoformat()
    
    # Calcular la duración
    cursor.execute("""
        SELECT inicio FROM registros WHERE id = ?
    """, (registro_id,))
    inicio = cursor.fetchone()[0]
    duracion = datetime.fromisoformat(fin) - datetime.fromisoformat(inicio)
    duracion_str = str(duracion)

    cursor.execute("""
        UPDATE registros 
        SET fin = ?, duracion = ?, activo = 0
        WHERE id = ?
    """, (fin, duracion_str, registro_id))
    conn.commit()
    conn.close()


# Función: Inicio de sesión y registro
def login_register():
    st.title("🔐 Ingreso al sistema")
    
    with st.form("login_form"):
        nombre = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")
        if submitted:
           # db_path = load_db_path()
            create_tables()
            if verify_user(nombre, contrasena):  # ✅ solo dos argumentos
                st.session_state.logged_in = True
                st.session_state.user = nombre
                if verify_user(nombre, contrasena):
                    st.session_state.user = nombre
                    # Verifica si es el administrador
                if st.session_state.user == "martin cruz":
                    st.switch_page("pages/admin.py")  # Cambia a la página admin
                else:
                    st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")

   

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
        options=["Inicio", "Registro de horas", "Reporte de Incidencia","Historial","Examen Psicometrico"],
        icons=["house", "clock", "clipboard-check", "clock-history","clipboard-check" ],
        default_index=0
    )


if selected == "Inicio":
    # db_path = load_db_path()  # Remove this line
    st.title(f"👤 Bienvenido {st.session_state.user} ")
    st.info("Usa el menú para navegar por el sistema.")
    create_tables()  # This will now use the PostgreSQL connection
    # Verificar si el usuario está logueado
    if "user" not in st.session_state:
        st.error("Por favor, inicie sesión para ver esta sección.")
        st.stop()

    usuario = st.session_state.user

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














elif selected == "Registro de horas":
     
     proyectos=obtener_proyectos(st.session_state.user)
     st.subheader("Controla el tiempo de tus proyectos fácilmente")
     if proyectos:
        proyecto_seleccionado=st.selectbox("Selecciona tu proyecto",proyectos)
        #st.write(f"🔄 Estado del botón: *{proyecto_seleccionado}*")
        #st.write(f"🔄 Estado del botón: *{st.session_state.user}*")
        # Inicializar estados
        
        usuario = st.session_state.get("user", "default_user")  # Asegúrate de que el usuario esté autenticado
        proyecto_activo = proyecto_activo(usuario)

      if proyecto_activo:
          registro_id, proyecto, inicio = proyecto_activo
      if st.button("Terminar Proyecto"):
          terminar_proyecto(registro_id)
          st.success(f"Proyecto '{proyecto}' terminado con éxito.")
      else:
         proyecto_seleccionado = st.text_input("Nombre del Proyecto")
      if proyecto_seleccionado and st.button("Iniciar Proyecto"):
         iniciar_proyecto(usuario, proyecto_seleccionado)
         st.success(f"Proyecto '{proyecto_seleccionado}' iniciado.")
        
        
        
        
        
        
        
        
        numero_proyecto = obtener_numero_proyecto(proyecto_seleccionado)
        st.write(f"NUMERO DE PROYECTO:*{numero_proyecto}*")
        #if "boton_texto" not in st.session_state:
            #st.session_state.boton_texto = "Iniciar"
        #if "proyecto_activo" not in st.session_state:
            #st.session_state.proyecto_activo = False
        #if "inicio_proyecto" not in st.session_state:
            #st.session_state.inicio_proyecto = None
        #if "id_registro" not in st.session_state:
            #st.session_state.id_registro = None

        # Manejar el clic del botón
        #def cambiar_estado():
            #if not st.session_state.user or not proyecto_seleccionado:
                #st.error("Por favor, ingresa tu nombre y el número del proyecto.")
                #return
    
            #if st.session_state.proyecto_activo:
                # Terminar proyecto
               # from datetime import datetime

                #fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #inicio = st.session_state.inicio_proyecto

                # Asegúrate de que 'inicio' sea una cadena
                #if isinstance(inicio, datetime):
                   #inicio = inicio.strftime("%Y-%m-%d %H:%M:%S")
                #elif not isinstance(inicio, str):
                   #st.error(f"El valor de 'inicio_proyecto' no es válido: {inicio} ({type(inicio)})")
                   #return

                #duracion = str(datetime.strptime(fin, "%Y-%m-%d %H:%M:%S") - datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S"))
                #actualizar_registro(st.session_state.id_registro, fin, duracion)
            # Restablecer estados
                #st.session_state.boton_texto = "Iniciar"
                #st.session_state.proyecto_activo = False
                #st.session_state.inicio_proyecto = None
                #st.session_state.id_registro = None
                #st.success(f"✅ Proyecto '{proyecto_seleccionado}' terminado correctamente.")
            #else:
                # Iniciar proyecto
                #inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #insertar_registro(st.session_state.user, proyecto_seleccionado, inicio)
                # Guardar ID del registro y estado de sesión
                #ultimo_registro = obtener_ultimo_registro(st.session_state.user, proyecto_seleccionado)
                #if ultimo_registro:
                    #st.session_state.id_registro = ultimo_registro[0]
                    #st.session_state.inicio_proyecto = ultimo_registro[1]
                    #st.session_state.boton_texto = "Terminar"
                    #st.session_state.proyecto_activo = True
                    #st.success(f"🚀 Proyecto '{proyecto_seleccionado}' iniciado correctamente.")

        

        # Mostrar el botón
        #st.button(st.session_state.boton_texto, on_click=cambiar_estado, key="cambiar_estado_btn", help="Haz clic para iniciar o terminar un proyecto.")

        # Mostrar el estado actual del botón
        #st.write(f"🔄 Estado del botón: *{st.session_state.boton_texto}*")

            
        

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
            with st.expander(f"Reporte #{rec['id']} - {rec['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"):
            #with st.expander(f"Reporte #{rec['id']} - {rec['created_at'][:19]}"):
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

elif selected == "Examen Psicometrico":
    st.title("Examen Psicométrico Laboral – Diseñador Mecánico")

    st.info("*Instrucciones:* Responde todas las secciones. Tiempo estimado: 30 minutos.")
    nombre = st.session_state.user
    if nombre.strip() == "":
        st.warning("Por favor, ingresa tu nombre antes de comenzar el examen.")
        nombre = st.text_input("Nombre del participante:")
    else:    
        # Preguntas técnicas (respuestas correctas)
        correct_answers = {
            "q1": "200",
            "q2": "1.75 mm",
            "q3": "No",
            "q4": "Rebajar el material 0.2 mm a esa velocidad",
            "q5": "Se aplican tolerancias medias según norma ISO"
         }

        # Sección 1: Técnicas
        st.header("Sección 1: Razonamiento Técnico")
        q1 = st.radio("1. ¿Cuántas vueltas da una pieza a 1200 rpm en 10 segundos?", ['100', '120', '200', '20'])
        q2 = st.radio("2. ¿Cuánto se expande una barra de 3.5 m a 0.5 mm/m?", ['0.75 mm', '1.5 mm', '1.75 mm', '2 mm'])
        q3 = st.radio("3. ¿La tuerca fallará con 150 N si resiste 300 N?", ['Sí', 'No', 'No se puede determinar', 'Solo si se excede el tiempo de aplicación'])

        #Sección 2: Comunicación Técnica
        st.header("Sección 2: Comunicación Técnica")
        q4 = st.radio("4. ¿Qué implica: desbaste a 0.2 mm a 1200 rpm?", 
                ['Lijar superficialmente', 
                'Rebajar el material 0.2 mm a esa velocidad', 
                'Detener el husillo a 0.2 mm', 
                'Cortar con tolerancia de ±0.2 mm'])
        q5 = st.radio("5. ¿Qué significa 'Tolerancia general ISO 2768-m'?", 
                ['La pieza debe ser exacta', 
                'Se permite un error mínimo de montaje', 
                'Se aplican tolerancias medias según norma ISO', 
                'Las medidas están en pulgadas'])

        # Sección 3: Personalidad
        st.header("Sección 3: Personalidad Laboral")

        q6 = st.selectbox("6. Verifico mis diseños antes de entregarlos.", ['Siempre', 'A menudo', 'A veces', 'Nunca'])
        q7 = st.selectbox("7. Prefiero instrucciones claras.", ['Siempre', 'A menudo', 'A veces', 'Nunca'])
        q8 = st.selectbox("8. Me adapto fácilmente a nuevas herramientas de diseño.", ['Siempre', 'A menudo', 'A veces', 'Nunca'])
        q9 = st.selectbox("9. Trabajo bien bajo presión.", ['Siempre', 'A menudo', 'A veces', 'Nunca'])
        q10 = st.selectbox("10. Me molestan los cambios en medio del proyecto.", ['Nunca', 'A veces', 'A menudo', 'Siempre'])  # invertido

        # Sección 4: Ética
        st.header("Sección 4: Ética y Situaciones")
        q11 = st.radio("11. ¿Qué haces si detectas un error ya enviado?", 
                ['Nada, ya no está en tus manos', 
                    'Informar de inmediato y proponer solución', 
                    'Esperar a ver si lo detectan', 
                    'Modificar el plano sin avisar'])

        q12 = st.radio("12. Si te asignan una herramienta nueva...", 
                ['Me frustro y lo delego', 
                    'Busco tutoriales y aprendo rápido', 
                    'Lo intento sin garantizar resultados', 
                    'Me niego hasta recibir capacitación'])

        if st.button("Evaluar y Mostrar Perfil"):
           
            
            # Evaluación técnica
            score = 0
            user_answers = {
            "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
            "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10,
            "q11": q11, "q12": q12
            }
            

            for key in correct_answers:
                if user_answers[key] == correct_answers[key]:
                    score += 1

            st.success(f"Puntaje técnico: {score} de 5")

            # Perfil psicológico (0 a 5)
            def val(res):
                scale = {"Nunca": 1, "A veces": 2, "A menudo": 3, "Siempre": 4}
                return scale.get(res, 0)
            
             # Guardar en la base de datos
            responsabilidad = val(q6)
            trabajo_equipo = 5 - val(q7)  # inverso
            adaptabilidad = val(q8)
            manejo_estres = val(q9)
            flexibilidad = val(q10)  # ya está invertido

            add_exam(
                nombre=st.session_state.user,
                fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                Score=score,
                responsabilidad=responsabilidad,
                adaptabilidad=adaptabilidad,
                trabajo_equipo=trabajo_equipo,
                manejo_estres=manejo_estres,
                flexibilidad=flexibilidad
            )

            radar_labels = ['Responsabilidad', 'Adaptabilidad', 'Trabajo en equipo', 'Gestión del estrés', 'Flexibilidad']
            radar_values = [responsabilidad, adaptabilidad, trabajo_equipo, manejo_estres, flexibilidad]

            # Radar chart
            angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
            radar_values += radar_values[:1]
            angles += angles[:1]
            st.success("Examen guardado correctamente.")

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.plot(angles, radar_values, color='blue', linewidth=2)
            ax.fill(angles, radar_values, color='skyblue', alpha=0.4)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(radar_labels)
            ax.set_yticks([1, 2, 3, 4])
            ax.set_yticklabels(['1', '2', '3', '4'])
            ax.set_title("Perfil Psicológico Laboral", size=15)
            st.pyplot(fig)

            # Exportación
            df = pd.DataFrame([user_answers])
            df["Puntaje_Tecnico"] = score
            df["Responsabilidad"] = responsabilidad
            df["Adaptabilidad"] = adaptabilidad
            df["Trabajo_en_Equipo"] = trabajo_equipo
            df["Manejo_Estres"] = manejo_estres
            df["Flexibilidad"] = flexibilidad

            file_name = "resultado_examen_mecanico.xlsx"
            df.to_excel(file_name, index=False)

            with open(file_name, "rb") as f:
                st.download_button("Descargar Resultados en Excel", f, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
