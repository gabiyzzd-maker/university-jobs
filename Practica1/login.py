import tkinter as tk
from tkinter import messagebox

from cursos import ventana_cursos
from db import conectar, inicializar_bd
from estudiantes import ventana_estudiantes
from reportes import ventana_reportes


def validar_usuario(username, password):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "SELECT rol FROM usuarios WHERE username=%s AND password=%s",
        (username, password),
    )
    usuario = cur.fetchone()
    cur.close()
    conn.close()
    return usuario


def abrir_menu(usuario, rol):
    menu = tk.Tk()
    menu.title("Sistema Academia")
    menu.geometry("340x285")
    menu.resizable(False, False)

    tk.Label(menu, text="Sistema Academia", font=("Arial", 16, "bold")).pack(pady=14)
    tk.Label(menu, text=f"Usuario: {usuario} ({rol})").pack(pady=2)

    tk.Button(
        menu,
        text="Estudiantes",
        width=24,
        command=lambda: ventana_estudiantes(menu),
    ).pack(pady=6)

    tk.Button(
        menu,
        text="Cursos",
        width=24,
        command=lambda: ventana_cursos(menu),
    ).pack(pady=6)

    tk.Button(
        menu,
        text="Reportes",
        width=24,
        command=lambda: ventana_reportes(menu),
    ).pack(pady=6)

    tk.Button(menu, text="Salir", width=24, command=menu.destroy).pack(pady=14)
    menu.mainloop()


def abrir_login():
    login = tk.Tk()
    login.title("Login")
    login.geometry("310x220")
    login.resizable(False, False)

    tk.Label(login, text="Inicio de sesion", font=("Arial", 14, "bold")).pack(pady=12)

    tk.Label(login, text="Usuario:").pack()
    usuario = tk.Entry(login, width=30)
    usuario.pack(pady=3)

    tk.Label(login, text="Contrasena:").pack()
    clave = tk.Entry(login, width=30, show="*")
    clave.pack(pady=3)

    def validar():
        username = usuario.get().strip()
        password = clave.get().strip()

        if not username or not password:
            messagebox.showwarning("Aviso", "Digite usuario y contrasena")
            return

        try:
            inicializar_bd()
            resultado = validar_usuario(username, password)
        except Exception as e:
            messagebox.showerror(
                "Error de base de datos",
                "No se pudo conectar con la base academia.\n\n"
                "Revise PostgreSQL, la base de datos, el usuario y la clave.\n\n"
                f"Detalle: {e}",
            )
            return

        if resultado is None:
            messagebox.showerror("Error", "Usuario o contrasena incorrectos")
            return

        login.destroy()
        abrir_menu(username, resultado[0])

    tk.Button(login, text="Entrar", width=18, command=validar).pack(pady=16)
    login.bind("<Return>", lambda _event: validar())
    login.mainloop()
