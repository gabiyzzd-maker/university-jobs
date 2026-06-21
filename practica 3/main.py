from fastapi import FastAPI, HTTPException, Header, Depends
from db import conectar
from models import EstudianteCreate, EstudianteUpdate, LoginRequest
from auth import crear_token, verificar_token

app = FastAPI(title="API Academia")

# ── DEPENDENCIA DE AUTENTICACIÓN ───────────────────
def obtener_usuario_actual(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido o formato incorrecto")
    
    token = authorization.split(" ")[1]
    payload = verificar_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")
    
    return payload  # Retorna los datos del usuario (sub, rol, etc.)

# ── AUTH ───────────────────────────────────────────
@app.post("/login")
def login(datos: LoginRequest):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT rol FROM usuarios WHERE username=%s AND password=%s",
                    (datos.username, datos.password))
        resultado = cur.fetchone()
    finally:
        conn.close()

    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
    token = crear_token({"sub": datos.username, "rol": resultado[0]})
    return {"access_token": token, "token_type": "bearer"}

# ── ESTUDIANTES ────────────────────────────────────
@app.get("/estudiantes")
def listar_estudiantes(usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, email FROM estudiantes ORDER BY id")
        filas = cur.fetchall()
    finally:
        conn.close()
        
    return [{"id": f[0], "nombre": f[1], "email": f[2]} for f in filas]

@app.get("/estudiantes/{id}")
def obtener_estudiante(id: int, usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, email FROM estudiantes WHERE id=%s", (id,))
        f = cur.fetchone()
    finally:
        conn.close()
        
    if not f:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"id": f[0], "nombre": f[1], "email": f[2]}

@app.post("/estudiantes", status_code=201)
def crear_estudiante(est: EstudianteCreate, usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO estudiantes (nombre, email) VALUES (%s, %s) RETURNING id",
                    (est.nombre, est.email))
        nuevo_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
        
    return {"id": nuevo_id, "nombre": est.nombre, "email": est.email}

@app.put("/estudiantes/{id}")
def actualizar_estudiante(id: int, est: EstudianteUpdate, usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE estudiantes SET nombre=%s, email=%s WHERE id=%s",
                    (est.nombre, est.email, id))
        conn.commit()
    finally:
        conn.close()
        
    return {"mensaje": "Estudiante actualizado"}

@app.delete("/estudiantes/{id}")
def eliminar_estudiante(id: int, usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM estudiantes WHERE id=%s", (id,))
        conn.commit()
    finally:
        conn.close()
        
    return {"mensaje": "Estudiante eliminado"}

# ── CURSOS ─────────────────────────────────────────
@app.get("/cursos")
def listar_cursos(usuario: dict = Depends(obtener_usuario_actual)):
    conn = conectar()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, creditos FROM cursos ORDER BY id")
        filas = cur.fetchall()
    finally:
        conn.close()
        
    return [{"id": f[0], "nombre": f[1], "creditos": f[2]} for f in filas]