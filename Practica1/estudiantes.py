import tkinter as tk
from tkinter import ttk, messagebox

from db import conectar, extraer_id_combo, obtener_opciones


def cargar_estudiantes(tabla):
    for row in tabla.get_children():
        tabla.delete(row)

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.id, e.nombre, e.email, COALESCE(c.nombre, 'Sin carrera')
            FROM estudiantes e
            LEFT JOIN carreras c ON c.id = e.carrera_id
            ORDER BY e.id
            """
        )
        for fila in cur.fetchall():
            tabla.insert("", "end", values=fila)
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar estudiantes:\n{e}")


def agregar_estudiante(nombre, email, carrera, tabla):
    nombre = nombre.strip()
    email = email.strip()
    carrera_id = extraer_id_combo(carrera)

    if not nombre or not email:
        messagebox.showwarning("Aviso", "Nombre y email son obligatorios")
        return

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO estudiantes (nombre, email, carrera_id) VALUES (%s, %s, %s)",
            (nombre, email, carrera_id),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo agregar el estudiante:\n{e}")
        return

    cargar_estudiantes(tabla)


def eliminar_estudiante(tabla):
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Selecciona un estudiante")
        return

    id_est = tabla.item(seleccion[0])["values"][0]

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM estudiantes WHERE id=%s", (id_est,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror(
            "Error",
            "No se pudo eliminar el estudiante.\n"
            "Si tiene matriculas registradas, elimine esas matriculas primero.\n\n"
            f"Detalle: {e}",
        )
        return

    cargar_estudiantes(tabla)


def ventana_estudiantes(parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("Estudiantes")
    win.geometry("720x455")
    win.resizable(False, False)

    tk.Label(win, text="Nombre:").pack()
    nombre = tk.Entry(win, width=50)
    nombre.pack(pady=3)

    tk.Label(win, text="Email:").pack()
    email = tk.Entry(win, width=50)
    email.pack(pady=3)

    tk.Label(win, text="Carrera:").pack()
    carrera = ttk.Combobox(win, width=47, state="readonly")
    try:
        carreras = obtener_opciones("carreras")
        carrera["values"] = [f"{id_carrera} - {nombre_carrera}" for id_carrera, nombre_carrera in carreras]
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar carreras:\n{e}")
    carrera.pack(pady=3)

    tabla = ttk.Treeview(win, columns=("ID", "Nombre", "Email", "Carrera"), show="headings")
    for col in ("ID", "Nombre", "Email", "Carrera"):
        tabla.heading(col, text=col)
    tabla.column("ID", width=70, anchor="center")
    tabla.column("Nombre", width=210)
    tabla.column("Email", width=250)
    tabla.column("Carrera", width=170)
    tabla.pack(padx=10, pady=10, fill="both", expand=True)

    botones = tk.Frame(win)
    botones.pack(pady=8)

    tk.Button(
        botones,
        text="Agregar",
        width=14,
        command=lambda: agregar_estudiante(nombre.get(), email.get(), carrera.get(), tabla),
    ).pack(side="left", padx=5)

    tk.Button(
        botones,
        text="Eliminar",
        width=14,
        command=lambda: eliminar_estudiante(tabla),
    ).pack(side="left", padx=5)

    cargar_estudiantes(tabla)

    if parent is None:
        win.mainloop()
