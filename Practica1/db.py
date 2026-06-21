try:
    import psycopg2
except ImportError:
    psycopg2 = None


DB_CONFIG = {
    "host": "localhost",
    "database": "Academia",
    "user": "postgres",
    "password": "admin",
}


def conectar():
    if psycopg2 is None:
        raise RuntimeError("Falta instalar psycopg2. Ejecute: pip install psycopg2-binary")

    errores = []
    for database in ("Academia", "academia"):
        config = DB_CONFIG.copy()
        config["database"] = database

        try:
            conn = psycopg2.connect(**config)
            conn.set_client_encoding("UTF8")
            return conn
        except Exception as e:
            errores.append(f"{database}: {e}")

    raise RuntimeError(
        "No se pudo conectar a PostgreSQL. Revise que exista la base "
        "'Academia' o 'academia', que PostgreSQL este encendido y que "
        "el usuario postgres tenga la clave admin.\n\n"
        + "\n".join(errores)
    )


def inicializar_bd():
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carreras (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS profesores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cursos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            creditos INT,
            carrera_id INT REFERENCES carreras(id),
            profesor_id INT REFERENCES profesores(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS estudiantes (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            carrera_id INT REFERENCES carreras(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matriculas (
            id SERIAL PRIMARY KEY,
            estudiante_id INT REFERENCES estudiantes(id),
            curso_id INT REFERENCES cursos(id),
            fecha DATE DEFAULT CURRENT_DATE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            rol VARCHAR(20) DEFAULT 'alumno'
        )
        """
    )
    cur.execute(
        """
        INSERT INTO usuarios (username, password, rol)
        VALUES ('admin', 'admin', 'admin')
        ON CONFLICT (username) DO NOTHING
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def obtener_opciones(tabla):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(f"SELECT id, nombre FROM {tabla} ORDER BY nombre")
    opciones = cur.fetchall()
    cur.close()
    conn.close()
    return opciones


def extraer_id_combo(valor):
    if not valor:
        return None
    return int(valor.split(" - ", 1)[0])


def verificar_conexion():
    conexion = None
    try:
        print("Intentando conectar a la base de datos...")
        conexion = conectar()

        cursor = conexion.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print("\nConexion exitosa.")
        print(f"Version de PostgreSQL: {version[0]}")
        cursor.close()

    except Exception as e:
        print("\nError de conexion. Revisa lo siguiente:")
        print(f"Detalle del error: {e}")
        print("\nPosibles causas:")
        print("- Falta instalar psycopg2-binary.")
        print("- El servidor de PostgreSQL no esta encendido.")
        print("- El usuario o la contrasena de PostgreSQL son incorrectos.")
        print("- No existe la base de datos llamada 'Academia' o 'academia'.")

    finally:
        if conexion is not None:
            conexion.close()
            print("Conexion cerrada limpiamente.")
