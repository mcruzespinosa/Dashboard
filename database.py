import psycopg2
import os
import pandas as pd
from datetime import datetime

# Database connection string (IMPORTANT:  Do NOT hardcode passwords in production!)
DB_CONN_STRING = "postgresql://postgres.rwqsenhhhhqglpiihqat:Martin171094@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def get_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Error connecting to the database: {e}")

def create_tables():
    """Creates the necessary tables in the PostgreSQL database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            proyecto TEXT NOT NULL,
            inicio TIMESTAMP NOT NULL,
            fin TIMESTAMP,
            duracion INTERVAL,
            FOREIGN KEY(usuario) REFERENCES usuarios(nombre)
        )
    """)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id SERIAL PRIMARY KEY,
            ingeniero TEXT,
            numero_proyecto TEXT,
            nombre_proyecto TEXT,
            horas_cotizadas INTEGER
        )
    ''')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidencias (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            area TEXT NOT NULL,
            cantidad_danada TEXT NOT NULL,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            codigo_pieza TEXT NOT NULL,
            destino TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            acciones_correctivas TEXT NOT NULL,
            pdf_file TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_examenes (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            fecha TIMESTAMP,
            puntaje_tecnico INTEGER,
            responsabilidad INTEGER,
            adaptabilidad INTEGER,
            trabajo_equipo INTEGER,
            manejo_estres INTEGER,
            flexibilidad INTEGER
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def add_user(nombre, contrasena):
    """Adds a new user to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, contrasena) VALUES (%s, %s)", (nombre, contrasena))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()  # Rollback to avoid leaving the connection in a bad state
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user(nombre, contrasena):
    """Verifies user credentials against the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre=%s AND contrasena=%s", (nombre, contrasena))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

def insert_registro(usuario, proyecto, inicio, fin=None, duracion=None):
    """Inserts a time tracking record into the database."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registros (usuario, proyecto, inicio, fin, duracion)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario, proyecto, inicio, fin, duracion))
    conn.commit()
    cursor.close()
    conn.close()

def get_registros(usuario, proyecto_filtro=""):
    """Retrieves time tracking records for a user, optionally filtered by project."""

    conn = get_connection()
    cursor = conn.cursor()
    if proyecto_filtro:
        cursor.execute("""
            SELECT proyecto, inicio, fin, duracion FROM registros
            WHERE usuario = %s AND proyecto LIKE %s
            ORDER BY inicio DESC
        """, (usuario, f"%{proyecto_filtro}%"))
    else:
        cursor.execute("""
            SELECT proyecto, inicio, fin, duracion FROM registros
            WHERE usuario = %s
            ORDER BY inicio DESC
        """, (usuario,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_total_tiempo_por_proyecto(usuario):
    """Calculates the total time spent on each project for a user."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT proyecto, duracion FROM registros
        WHERE usuario = %s
    """, (usuario,))
    registros = cursor.fetchall()
    total_por_proyecto = {}

    for proyecto, duracion in registros:
        if proyecto not in total_por_proyecto:
            total_por_proyecto[proyecto] = duracion  # Already an interval
        else:
            total_por_proyecto[proyecto] += duracion

    result = [(proy, str(total_por_proyecto[proy])) for proy in total_por_proyecto]
    cursor.close()
    conn.close()
    return result

def exportar_registros_a_excel(usuario, ruta_archivo, proyecto_filtro=""):
    """Exports time tracking records to an Excel file."""

    registros = get_registros(usuario, proyecto_filtro)
    df = pd.DataFrame(registros, columns=["Proyecto", "Inicio", "Fin", "Duración"])
    df.to_excel(ruta_archivo, index=False)
    return ruta_archivo

def add_incident(usuario, area, cantidad, fecha, hora, codigo, destino,
                 descripcion, acciones, pdf_file):
    """Adds an incident report to the database."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidencias
          (usuario, area, cantidad_danada, fecha, hora, codigo_pieza,
           destino, descripcion, acciones_correctivas, pdf_file, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        usuario, area, cantidad, fecha, hora, codigo,
        destino, descripcion, acciones, pdf_file,
        datetime.now()
    ))
    conn.commit()
    cursor.close()
    conn.close()

def get_incidents(usuario):
    """Retrieves incident reports for a specific user."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, area, cantidad_danada, fecha, hora, codigo_pieza,
               destino, descripcion, acciones_correctivas, pdf_file, created_at
        FROM incidencias
        WHERE usuario = %s
        ORDER BY created_at DESC
    """, (usuario,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    columns = ["id", "area", "cantidad", "fecha", "hora", "codigo_pieza",
               "destino", "descripcion", "acciones", "pdf_file", "created_at"]
    return [dict(zip(columns, row)) for row in rows]

def add_exam(nombre, fecha, Score, responsabilidad, adaptabilidad, trabajo_equipo, manejo_estres, flexibilidad):
    """Adds exam results to the database."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial_examenes 
          (nombre, fecha, puntaje_tecnico, responsabilidad, adaptabilidad, trabajo_equipo, manejo_estres, flexibilidad) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (nombre, fecha, Score, responsabilidad, adaptabilidad, trabajo_equipo, manejo_estres, flexibilidad))
    conn.commit()
    cursor.close()
    conn.close()

def get_exam(nombre):
    """Retrieves exam results for a specific user."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre, fecha, puntaje_tecnico, responsabilidad, adaptabilidad, 
                trabajo_equipo, manejo_estres, flexibilidad
        FROM historial_examenes
        WHERE nombre = %s
        ORDER BY fecha DESC
    """, (nombre,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    columns = ["nombre", "fecha", "puntaje_tecnico", "responsabilidad", "adaptabilidad",
                "trabajo_equipo", "manejo_estres", "flexibilidad"]
    return [dict(zip(columns, row)) for row in rows]

def obtener_ingenieros():
    """Retrieves a list of engineers from the database."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM usuarios")
    ingenieros = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return ingenieros

def eliminar_ingeniero(nombre):
    """Deletes an engineer and related data from the database."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE nombre=%s", (nombre,))
    cursor.execute("DELETE FROM historial_examenes WHERE nombre=%s", (nombre,))
    cursor.execute("DELETE FROM registros WHERE usuario=%s", (nombre,))
    cursor.execute("DELETE FROM incidencias WHERE usuario=%s", (nombre,))
    conn.commit()
    cursor.close()
    conn.close()

def asignar_proyecto(ingeniero, numero_proyecto, nombre_proyecto, horas_cotizadas):
    """Assigns a project to an engineer."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO proyectos (ingeniero, numero_proyecto, nombre_proyecto, horas_cotizadas)
        VALUES (%s, %s, %s, %s)
    ''', (ingeniero, numero_proyecto, nombre_proyecto, horas_cotizadas))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_proyectos(ingeniero):
    """Retrieves projects assigned to a specific engineer."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_proyecto FROM proyectos WHERE ingeniero=%s", (ingeniero,))
    proyectos = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return proyectos

def obtener_numero_proyecto(proyecto):
    """obtiene el numero de proyecto por ingeniero."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT numero_proyecto FROM proyectos WHERE ingeniero=%s", (proyectos,))
    proyectos = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return numero_proyecto

def obtener_proyectos_con_horas():
    """Retrieves all projects with their allocated hours."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ingeniero, nombre_proyecto, horas_cotizadas FROM proyectos")
    proyectos = cursor.fetchall()
    cursor.close()
    conn.close()
    return proyectos

def insertar_registro(usuario, proyecto, inicio):
    """Inserts a new time tracking entry."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registros(usuario, proyecto, inicio, fin, duracion)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario, proyecto, inicio, None, None))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_registro(id_registro, fin, duracion):
    """Updates a time tracking entry with finish time and duration."""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE registros
        SET fin = %s, duracion = %s
        WHERE id = %s
    """, (fin, duracion, id_registro))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_ultimo_registro(usuario, proyecto):
    """Retrieves the last started time tracking entry for a user and project."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, inicio FROM registros
            WHERE usuario = %s AND proyecto = %s AND fin IS NULL
            ORDER BY inicio DESC LIMIT 1
        """, (usuario, proyecto))
        registro = cursor.fetchone()
    except Exception as e:
        print(f"Error al obtener el último registro: {e}")
        registro = None
    finally:
        cursor.close()
        conn.close()

    # Verificar si se obtuvo un registro
    if registro is None:
        return None

    # Retornar el ID y la fecha de inicio como cadena
    return registro[0], registro[1].strftime("%Y-%m-%d %H:%M:%S") if isinstance(registro[1], datetime) else registro[1]
