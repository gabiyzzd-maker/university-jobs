import io
import os
from functools import wraps

import openpyxl
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from openpyxl.styles import Font

from db import conectar, inicializar_bd


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_123")


def login_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def ejecutar_consulta(consulta, parametros=None, fetch=False):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(consulta, parametros or ())
    datos = cur.fetchall() if fetch else None
    conn.commit()
    cur.close()
    conn.close()
    return datos


def obtener_opciones(tabla):
    return ejecutar_consulta(f"SELECT id, nombre FROM {tabla} ORDER BY nombre", fetch=True)


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    try:
        inicializar_bd()
    except Exception as e:
        error = f"No se pudo conectar a la base de datos: {e}"

    if request.method == "POST" and error is None:
        user = request.form.get("username", "").strip()
        pwd = request.form.get("password", "").strip()

        resultado = ejecutar_consulta(
            "SELECT rol FROM usuarios WHERE username=%s AND password=%s",
            (user, pwd),
            fetch=True,
        )

        if resultado:
            session["usuario"] = user
            session["rol"] = resultado[0][0]
            return redirect(url_for("index"))

        error = "Credenciales incorrectas"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/index")
@login_requerido
def index():
    conteos = {}
    for tabla in ("carreras", "profesores", "cursos", "estudiantes", "matriculas", "usuarios"):
        conteos[tabla] = ejecutar_consulta(f"SELECT COUNT(*) FROM {tabla}", fetch=True)[0][0]
    return render_template("index.html", conteos=conteos)


@app.route("/carreras")
@login_requerido
def carreras():
    lista = ejecutar_consulta(
        "SELECT id, nombre, COALESCE(descripcion, '') FROM carreras ORDER BY id",
        fetch=True,
    )
    return render_template("carreras.html", carreras=lista)


@app.route("/carreras/agregar", methods=["POST"])
@login_requerido
def agregar_carrera():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    if nombre:
        ejecutar_consulta(
            "INSERT INTO carreras (nombre, descripcion) VALUES (%s, %s)",
            (nombre, descripcion),
        )
    return redirect(url_for("carreras"))


@app.route("/carreras/eliminar/<int:id>")
@login_requerido
def eliminar_carrera(id):
    ejecutar_consulta("DELETE FROM carreras WHERE id=%s", (id,))
    return redirect(url_for("carreras"))


@app.route("/profesores")
@login_requerido
def profesores():
    lista = ejecutar_consulta(
        "SELECT id, nombre, COALESCE(email, '') FROM profesores ORDER BY id",
        fetch=True,
    )
    return render_template("profesores.html", profesores=lista)


@app.route("/profesores/agregar", methods=["POST"])
@login_requerido
def agregar_profesor():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    if nombre:
        ejecutar_consulta(
            "INSERT INTO profesores (nombre, email) VALUES (%s, %s)",
            (nombre, email or None),
        )
    return redirect(url_for("profesores"))


@app.route("/profesores/eliminar/<int:id>")
@login_requerido
def eliminar_profesor(id):
    ejecutar_consulta("DELETE FROM profesores WHERE id=%s", (id,))
    return redirect(url_for("profesores"))


@app.route("/estudiantes")
@login_requerido
def estudiantes():
    lista = ejecutar_consulta(
        """
        SELECT e.id, e.nombre, COALESCE(e.email, ''), COALESCE(c.nombre, 'Sin carrera')
        FROM estudiantes e
        LEFT JOIN carreras c ON c.id = e.carrera_id
        ORDER BY e.id
        """,
        fetch=True,
    )
    return render_template("estudiantes.html", estudiantes=lista, carreras=obtener_opciones("carreras"))


@app.route("/estudiantes/agregar", methods=["POST"])
@login_requerido
def agregar_estudiante():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    carrera_id = request.form.get("carrera_id") or None
    if nombre and email:
        ejecutar_consulta(
            "INSERT INTO estudiantes (nombre, email, carrera_id) VALUES (%s, %s, %s)",
            (nombre, email, carrera_id),
        )
    return redirect(url_for("estudiantes"))


@app.route("/estudiantes/eliminar/<int:id>")
@login_requerido
def eliminar_estudiante(id):
    ejecutar_consulta("DELETE FROM estudiantes WHERE id=%s", (id,))
    return redirect(url_for("estudiantes"))


@app.route("/cursos")
@login_requerido
def cursos():
    lista = ejecutar_consulta(
        """
        SELECT cu.id, cu.nombre, COALESCE(cu.creditos, 0),
               COALESCE(ca.nombre, 'Sin carrera'),
               COALESCE(p.nombre, 'Sin profesor')
        FROM cursos cu
        LEFT JOIN carreras ca ON ca.id = cu.carrera_id
        LEFT JOIN profesores p ON p.id = cu.profesor_id
        ORDER BY cu.id
        """,
        fetch=True,
    )
    return render_template(
        "cursos.html",
        cursos=lista,
        carreras=obtener_opciones("carreras"),
        profesores=obtener_opciones("profesores"),
    )


@app.route("/cursos/agregar", methods=["POST"])
@login_requerido
def agregar_curso():
    nombre = request.form.get("nombre", "").strip()
    creditos = request.form.get("creditos", "").strip()
    carrera_id = request.form.get("carrera_id") or None
    profesor_id = request.form.get("profesor_id") or None

    if nombre:
        ejecutar_consulta(
            """
            INSERT INTO cursos (nombre, creditos, carrera_id, profesor_id)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, int(creditos) if creditos else None, carrera_id, profesor_id),
        )
    return redirect(url_for("cursos"))


@app.route("/cursos/eliminar/<int:id>")
@login_requerido
def eliminar_curso(id):
    ejecutar_consulta("DELETE FROM cursos WHERE id=%s", (id,))
    return redirect(url_for("cursos"))


def agregar_hoja_excel(libro, nombre, encabezados, consulta):
    hoja = libro.create_sheet(nombre)
    hoja.append(encabezados)
    for celda in hoja[1]:
        celda.font = Font(bold=True)

    filas = ejecutar_consulta(consulta, fetch=True)
    for fila in filas:
        hoja.append(list(fila))

    for columna in hoja.columns:
        letra = columna[0].column_letter
        ancho = max(len(str(celda.value or "")) for celda in columna) + 2
        hoja.column_dimensions[letra].width = min(ancho, 45)


@app.route("/reporte")
@login_requerido
def reporte():
    libro = openpyxl.Workbook()
    libro.remove(libro.active)

    agregar_hoja_excel(libro, "Carreras", ["ID", "Nombre", "Descripcion"], "SELECT id, nombre, COALESCE(descripcion, '') FROM carreras ORDER BY id")
    agregar_hoja_excel(libro, "Profesores", ["ID", "Nombre", "Email"], "SELECT id, nombre, COALESCE(email, '') FROM profesores ORDER BY id")
    agregar_hoja_excel(
        libro,
        "Cursos",
        ["ID", "Nombre", "Creditos", "Carrera", "Profesor"],
        """
        SELECT cu.id, cu.nombre, COALESCE(cu.creditos, 0),
               COALESCE(ca.nombre, 'Sin carrera'),
               COALESCE(p.nombre, 'Sin profesor')
        FROM cursos cu
        LEFT JOIN carreras ca ON ca.id = cu.carrera_id
        LEFT JOIN profesores p ON p.id = cu.profesor_id
        ORDER BY cu.id
        """,
    )
    agregar_hoja_excel(
        libro,
        "Estudiantes",
        ["ID", "Nombre", "Email", "Carrera"],
        """
        SELECT e.id, e.nombre, COALESCE(e.email, ''),
               COALESCE(c.nombre, 'Sin carrera')
        FROM estudiantes e
        LEFT JOIN carreras c ON c.id = e.carrera_id
        ORDER BY e.id
        """,
    )
    agregar_hoja_excel(
        libro,
        "Matriculas",
        ["ID", "Estudiante", "Curso", "Fecha"],
        """
        SELECT m.id, COALESCE(e.nombre, 'Sin estudiante'),
               COALESCE(cu.nombre, 'Sin curso'), m.fecha
        FROM matriculas m
        LEFT JOIN estudiantes e ON e.id = m.estudiante_id
        LEFT JOIN cursos cu ON cu.id = m.curso_id
        ORDER BY m.id
        """,
    )

    output = io.BytesIO()
    libro.save(output)
    output.seek(0)
    return send_file(output, download_name="reporte_academia.xlsx", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
