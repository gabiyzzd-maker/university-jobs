import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from db import conectar


TABLAS_RESUMEN = ("carreras", "profesores", "cursos", "estudiantes", "matriculas", "usuarios")

REPORTES_EXCEL = {
    "Carreras": (
        ["ID", "Nombre", "Descripcion"],
        """
        SELECT id, nombre, COALESCE(descripcion, '')
        FROM carreras
        ORDER BY id
        """,
    ),
    "Profesores": (
        ["ID", "Nombre", "Email"],
        """
        SELECT id, nombre, COALESCE(email, '')
        FROM profesores
        ORDER BY id
        """,
    ),
    "Cursos": (
        ["ID", "Nombre", "Creditos", "Carrera", "Profesor"],
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
        """,
    ),
    "Estudiantes": (
        ["ID", "Nombre", "Email", "Carrera"],
        """
        SELECT e.id,
               e.nombre,
               COALESCE(e.email, ''),
               COALESCE(c.nombre, 'Sin carrera')
        FROM estudiantes e
        LEFT JOIN carreras c ON c.id = e.carrera_id
        ORDER BY e.id
        """,
    ),
    "Matriculas": (
        ["ID", "Estudiante", "Curso", "Fecha"],
        """
        SELECT m.id,
               COALESCE(e.nombre, 'Sin estudiante'),
               COALESCE(cu.nombre, 'Sin curso'),
               m.fecha
        FROM matriculas m
        LEFT JOIN estudiantes e ON e.id = m.estudiante_id
        LEFT JOIN cursos cu ON cu.id = m.curso_id
        ORDER BY m.id
        """,
    ),
    "Usuarios": (
        ["ID", "Usuario", "Rol"],
        """
        SELECT id, username, rol
        FROM usuarios
        ORDER BY id
        """,
    ),
}


def cargar_resumen(labels):
    try:
        conn = conectar()
        cur = conn.cursor()

        for tabla, label in labels.items():
            cur.execute(f"SELECT COUNT(*) FROM {tabla}")
            total = cur.fetchone()[0]
            label.config(text=f"{tabla.capitalize()}: {total}")

        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el resumen:\n{e}")


def cargar_matriculas(tabla):
    for row in tabla.get_children():
        tabla.delete(row)

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute(REPORTES_EXCEL["Matriculas"][1])
        for fila in cur.fetchall():
            tabla.insert("", "end", values=fila)
        cur.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el reporte:\n{e}")


def ajustar_columnas(hoja):
    for columna in hoja.columns:
        max_largo = 0
        letra = columna[0].column_letter

        for celda in columna:
            valor = "" if celda.value is None else str(celda.value)
            max_largo = max(max_largo, len(valor))

        hoja.column_dimensions[letra].width = min(max_largo + 2, 45)


def exportar_excel():
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        messagebox.showerror(
            "Error",
            "Falta instalar openpyxl.\n\nEjecute: pip install openpyxl",
        )
        return

    ruta = filedialog.asksaveasfilename(
        title="Guardar reporte",
        defaultextension=".xlsx",
        filetypes=[("Archivo Excel", "*.xlsx")],
        initialfile="reporte_academia.xlsx",
    )

    if not ruta:
        return

    try:
        conn = conectar()
        cur = conn.cursor()
        libro = Workbook()
        libro.remove(libro.active)

        for nombre_hoja, (encabezados, consulta) in REPORTES_EXCEL.items():
            hoja = libro.create_sheet(nombre_hoja)
            hoja.append(encabezados)

            for celda in hoja[1]:
                celda.font = Font(bold=True)

            cur.execute(consulta)
            for fila in cur.fetchall():
                hoja.append(list(fila))

            ajustar_columnas(hoja)

        libro.save(ruta)
        cur.close()
        conn.close()
        messagebox.showinfo("Excel", f"Reporte exportado correctamente:\n{ruta}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar a Excel:\n{e}")


def ventana_reportes(parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("Reportes")
    win.geometry("760x500")
    win.resizable(False, False)

    tk.Label(win, text="Reportes", font=("Arial", 15, "bold")).pack(pady=12)

    panel = tk.Frame(win)
    panel.pack(pady=4)

    labels = {}
    for tabla_nombre in TABLAS_RESUMEN:
        label = tk.Label(panel, text=f"{tabla_nombre.capitalize()}: 0", width=18, anchor="w")
        label.pack(side="left", padx=2)
        labels[tabla_nombre] = label

    tabla = ttk.Treeview(
        win,
        columns=("ID", "Estudiante", "Curso", "Fecha"),
        show="headings",
    )
    for col in ("ID", "Estudiante", "Curso", "Fecha"):
        tabla.heading(col, text=col)
    tabla.column("ID", width=70, anchor="center")
    tabla.column("Estudiante", width=240)
    tabla.column("Curso", width=270)
    tabla.column("Fecha", width=120, anchor="center")
    tabla.pack(padx=10, pady=12, fill="both", expand=True)

    botones = tk.Frame(win)
    botones.pack(pady=8)

    tk.Button(
        botones,
        text="Actualizar",
        width=16,
        command=lambda: [cargar_resumen(labels), cargar_matriculas(tabla)],
    ).pack(side="left", padx=5)

    tk.Button(
        botones,
        text="Exportar Excel",
        width=16,
        command=exportar_excel,
    ).pack(side="left", padx=5)

    cargar_resumen(labels)
    cargar_matriculas(tabla)

    if parent is None:
        win.mainloop()
