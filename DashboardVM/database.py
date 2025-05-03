import sqlite3
import os
import pandas as pd
import json
from datetime import datetime


CONFIG_FILE = "config.json"
_db_path = None

def save_db_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"db_path": path}, f)

def load_db_path():
    global _db_path
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            _db_path = config.get("db_path")
    return _db_path

def set_db_path(path):
    global _db_path
    _db_path = path

def get_connection():
    if not _db_path:
        raise Exception("La ruta de la base de datos no ha sido establecida.")
    return sqlite3.connect(_db_path)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            proyecto TEXT NOT NULL,
            inicio TEXT NOT NULL,
            fin TEXT NOT NULL,
            duracion TEXT NOT NULL,
            FOREIGN KEY(usuario) REFERENCES usuarios(nombre)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            area TEXT NOT NULL,
            cantidad_danada TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            codigo_pieza TEXT NOT NULL,
            destino TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            acciones_correctivas TEXT NOT NULL,
            pdf_file TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_user(nombre, contrasena):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, contrasena) VALUES (?, ?)", (nombre, contrasena))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(nombre, contrasena):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre=? AND contrasena=?", (nombre, contrasena))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def insert_registro(usuario, proyecto, inicio, fin, duracion):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registros (usuario, proyecto, inicio, fin, duracion)
        VALUES (?, ?, ?, ?, ?)
    """, (usuario, proyecto, inicio, fin, duracion))
    conn.commit()
    conn.close()

def get_registros(usuario, proyecto_filtro=""):
    conn = get_connection()
    cursor = conn.cursor()
    if proyecto_filtro:
        cursor.execute("""
            SELECT proyecto, inicio, fin, duracion FROM registros
            WHERE usuario = ? AND proyecto LIKE ?
            ORDER BY inicio DESC
        """, (usuario, f"%{proyecto_filtro}%"))
    else:
        cursor.execute("""
            SELECT proyecto, inicio, fin, duracion FROM registros
            WHERE usuario = ?
            ORDER BY inicio DESC
        """, (usuario,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_tiempo_por_proyecto(usuario):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT proyecto, duracion FROM registros
        WHERE usuario = ?
    """, (usuario,))
    registros = cursor.fetchall()
    total_por_proyecto = {}

    from datetime import timedelta

    for proyecto, duracion in registros:
        h, m, s = map(int, duracion.split(":"))
        tiempo = timedelta(hours=h, minutes=m, seconds=s)
        if proyecto not in total_por_proyecto:
            total_por_proyecto[proyecto] = tiempo
        else:
            total_por_proyecto[proyecto] += tiempo

    result = [(proy, str(total_por_proyecto[proy])) for proy in total_por_proyecto]
    conn.close()
    return result

def exportar_registros_a_excel(usuario, ruta_archivo, proyecto_filtro=""):
    registros = get_registros(usuario, proyecto_filtro)
    df = pd.DataFrame(registros, columns=["Proyecto", "Inicio", "Fin", "Duración"])
    df.to_excel(ruta_archivo, index=False)
    return ruta_archivo

def create_incidents_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            area TEXT NOT NULL,
            cantidad_danada TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            codigo_pieza TEXT NOT NULL,
            destino TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            acciones_correctivas TEXT NOT NULL,
            pdf_file TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_incident(usuario, area, cantidad, fecha, hora, codigo, destino,
                 descripcion, acciones, pdf_file):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidencias
          (usuario, area, cantidad_danada, fecha, hora, codigo_pieza,
           destino, descripcion, acciones_correctivas, pdf_file, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        usuario, area, cantidad, fecha, hora, codigo,
        destino, descripcion, acciones, pdf_file,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_incidents(usuario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, area, cantidad_danada, fecha, hora, codigo_pieza,
               destino, descripcion, acciones_correctivas, pdf_file, created_at
        FROM incidencias
        WHERE usuario = ?
        ORDER BY created_at DESC
    """, (usuario,))
    rows = cur.fetchall()
    conn.close()
    # devolver lista de dicts
    columns = ["id","area","cantidad","fecha","hora","codigo_pieza",
               "destino","descripcion","acciones","pdf_file","created_at"]
    return [dict(zip(columns, r)) for r in rows]

def add_incident(usuario, area, cantidad, fecha, hora, codigo, destino,
                 descripcion, acciones, pdf_file):
    # Insertar un reporte de incidencia en la base de datos
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidencias
          (usuario, area, cantidad_danada, fecha, hora, codigo_pieza,
           destino, descripcion, acciones_correctivas, pdf_file, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        usuario, area, cantidad, fecha, hora, codigo,
        destino, descripcion, acciones, pdf_file,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_incidents(usuario):
    # Obtener los reportes de incidencias de un usuario
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, area, cantidad_danada, fecha, hora, codigo_pieza,
               destino, descripcion, acciones_correctivas, pdf_file, created_at
        FROM incidencias
        WHERE usuario = ?
        ORDER BY created_at DESC
    """, (usuario,))
    rows = cur.fetchall()
    conn.close()
    columns = ["id", "area", "cantidad", "fecha", "hora", "codigo_pieza",
               "destino", "descripcion", "acciones", "pdf_file", "created_at"]
    return [dict(zip(columns, r)) for r in rows]