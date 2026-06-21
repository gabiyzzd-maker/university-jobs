import tkinter as tk
from tkinter import ttk, messagebox

from db import conectar, extraer_id_combo, obtener_opciones


def cargar_cursos(tabla):
    for row in tabla.get_children():
        tabla.delete(row)

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT cu.id,
                   cu.nombre,
                   COALESCE(cu.creditos, 0),
                   COALESCE(ca.nombre, 'Sin carrera'),
                   COALESCE(p.nombre, 'Sin profesor')
            FROM cursos cu
            LEFT JOIN carreras ca ON ca.id = cu.carrera_id
            LEFT JOIN profesores p ON p.id = cu.profesor_id
            ORDER BY cu.id
            """
        )
        for fila in cur.fetchall():
            tabla.insert("", "end", values=fila)
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar cursos:\n{e}")


def agregar_curso(nombre, creditos, carrera, profesor, tabla):
    nombre = nombre.strip()
    creditos = creditos.strip()
    carrera_id = extraer_id_combo(carrera)
    profesor_id = extraer_id_combo(profesor)

    if not nombre:
        messagebox.showwarning("Aviso", "El nombre del curso es obligatorio")
        return

    if creditos and not creditos.isdigit():
        messagebox.showwarning("Aviso", "Los creditos deben ser un numero entero")
        return

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cursos (nombre, creditos, carrera_id, profesor_id)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, int(creditos) if creditos else None, carrera_id, profesor_id),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo agregar el curso:\n{e}")
        return

    cargar_cursos(tabla)


def eliminar_curso(tabla):
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona un curso")
        return

    id_curso = tabla.item(seleccion[0])["values"][0]

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM cursos WHERE id=%s", (id_curso,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror(
            "Error",
            "No se pudo eliminar el curso.\n"
            "Si tiene matriculas registradas, elimine esas matriculas primero.\n\n"
            f"Detalle: {e}",
        )
        return

    cargar_cursos(tabla)


def ventana_cursos(parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("Cursos")
    win.geometry("820x505")
    win.resizable(False, False)

    tk.Label(win, text="Nombre del curso:").pack()
    nombre = tk.Entry(win, width=55)
    nombre.pack(pady=3)

    tk.Label(win, text="Creditos:").pack()
    creditos = tk.Entry(win, width=55)
    creditos.pack(pady=3)

    tk.Label(win, text="Carrera:").pack()
    carrera = ttk.Combobox(win, width=52, state="readonly")
    carrera.pack(pady=3)

    try:
        carreras = obtener_opciones("carreras")
        profesores = obtener_opciones("profesores")
        carrera["values"] = [f"{id_carrera} - {nombre_carrera}" for id_carrera, nombre_carrera in carreras]
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar carreras o profesores:\n{e}")

    tk.Label(win, text="Profesor:").pack()
    profesor = ttk.Combobox(win, width=52, state="readonly")
    try:
        profesor["values"] = [f"{id_profesor} - {nombre_profesor}" for id_profesor, nombre_profesor in profesores]
    except UnboundLocalError:
        profesor["values"] = []
    profesor.pack(pady=3)

    tabla = ttk.Treeview(
        win,
        columns=("ID", "Nombre", "Creditos", "Carrera", "Profesor"),
        show="headings",
    )
    for col in ("ID", "Nombre", "Creditos", "Carrera", "Profesor"):
        tabla.heading(col, text=col)
    tabla.column("ID", width=60, anchor="center")
    tabla.column("Nombre", width=220)
    tabla.column("Creditos", width=80, anchor="center")
    tabla.column("Carrera", width=210)
    tabla.column("Profesor", width=210)
    tabla.pack(padx=10, pady=10, fill="both", expand=True)

    botones = tk.Frame(win)
    botones.pack(pady=8)

    tk.Button(
        botones,
        text="Agregar",
        width=14,
        command=lambda: agregar_curso(
            nombre.get(),
            creditos.get(),
            carrera.get(),
            profesor.get(),
            tabla,
        ),
    ).pack(side="left", padx=5)

    tk.Button(
        botones,
        text="Eliminar",
        width=14,
        command=lambda: eliminar_curso(tabla),
    ).pack(side="left", padx=5)

    cargar_cursos(tabla)

    if parent is None:
        win.mainloop()
