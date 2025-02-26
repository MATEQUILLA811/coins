import json
import os
from datetime import datetime
import ecdsa
import base64
import time
import hashlib

from datetime import datetime


# 📌 Obtener la ruta del JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "../static", "blockchain.json")

def load_json():
    """Carga los datos del archivo JSON"""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    

#time
def tiempo_relativo(timestamp):
    ahora = int(time.time())
    diferencia = ahora - timestamp  # Diferencia en segundos

    if diferencia < 0:
        return "En el futuro"

    unidades = [
        (31536000, "año"),  # 365 días
        (2592000, "mes"),   # 30 días
        (604800, "sem"),    # 7 días
        (86400, "d"),       # 24 horas
        (3600, "h"),        # 60 minutos
        (60, "min"),        # 60 segundos
        (1, "s")            # 1 segundo
    ]

    for segundos, unidad in unidades:
        valor = diferencia // segundos
        if valor >= 1:
            return f"hace {valor} {unidad}" if valor == 1 else f"hace {valor} {unidad}"

    return "ahora"

# 🚀 Pruebas con timestamps de ejemplo
timestamps = [
    int(time.time()) - 10,       # Hace 10s
    int(time.time()) - 3600,     # Hace 1h
    int(time.time()) - 86400,    # Hace 1d
    int(time.time()) - 604800,   # Hace 1 semana
    int(time.time()) - 2592000,  # Hace 1 mes
    int(time.time()) - 31536000  # Hace 1 año
]

for ts in timestamps:
    print(tiempo_relativo(ts))

# Prueba con el timestamp dado
#print(tiempo_relativo(1740530383))  # Salida: "5mes" o "1año" (depende de la fecha actual)




#login

def check_sender_exists(sender):
    """Verifica si el sender está en la blockchain"""
    data = load_json()
    return any(entry.get("sender") == sender for entry in data)


#saldo
def get_sender_balance(user):
    """Calcula el saldo total del usuario en la blockchain (resta envíos y suma recepciones)."""
    data = load_json()
    balance = 0  
    
    for entry in data:
        if entry.get("sender") == user:   # Si el usuario es el que envía, resta el monto
            balance -= entry.get("amount")  
        if entry.get("recipient") == user:  # Si el usuario es el que recibe, suma el monto
            balance += entry.get("amount")  
    
    return balance  # Devuelve el saldo neto


#historial


def add_transaction(sender, recipient, amount):
    """Añade una nueva transacción a la blockchain con fecha y hora."""
    data = load_json()
    transaction = {
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Formato: Año-Mes-Día Hora:Min:Seg
    }
    data.append(transaction)

    # Guardar los datos actualizados
    with open(JSON_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


#verificar y transaferir confirmando
def verificar_claves(private_pem, public_pem):
    try:
        # 📌 Agregar encabezados si faltan
        private_pem = f"-----BEGIN EC PRIVATE KEY-----\n{private_pem.strip()}\n-----END EC PRIVATE KEY-----"
        public_pem = f"-----BEGIN PUBLIC KEY-----\n{public_pem.strip()}\n-----END PUBLIC KEY-----"

        # 📌 Cargar claves correctamente
        clave_privada = ecdsa.SigningKey.from_pem(private_pem.encode())
        clave_publica = ecdsa.VerifyingKey.from_pem(public_pem.encode())

        # 📌 Mensaje de prueba
        mensaje = b"Prueba de autenticidad"

        # 📌 Firmar el mensaje con la clave privada
        firma = clave_privada.sign(mensaje)

        # 📌 Verificar la firma con la clave pública
        return clave_publica.verify(firma, mensaje)

    except Exception as e:
        print(f"❌ Error en la verificación de claves: {e}")
        return False


def cargar_blockchain():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def obtener_balance(sender):
    blockchain = cargar_blockchain()
    balance = 0
    for bloque in blockchain:
        if bloque["sender"] == sender:
            balance -= bloque["amount"]
        if bloque["recipient"] == sender:
            balance += bloque["amount"]
    return balance

def obtener_ultimo_bloque(blockchain):
    if not blockchain:
        return 0, "0"
    ultimo_bloque = blockchain[-1]
    return ultimo_bloque["version"], ultimo_bloque["hash"]

def calcular_hash_bloque(bloque):
    bloque_str = json.dumps(bloque, sort_keys=True).encode()
    return hashlib.sha256(bloque_str).hexdigest()

def guardar_bloque(bloque):
    blockchain = cargar_blockchain()
    blockchain.append(bloque)
    with open(JSON_PATH, "w") as f:
        json.dump(blockchain, f, indent=4)