from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey123"
ALGORITHM  = "HS256"

def crear_token(data: dict):
    datos = data.copy()
    datos["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None