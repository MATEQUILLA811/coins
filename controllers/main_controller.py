from flask import Flask, render_template, request,jsonify,url_for,redirect,send_from_directory,Blueprint
from models.blockchain import load_json,get_sender_balance,verificar_claves,obtener_balance,cargar_blockchain,obtener_ultimo_bloque,calcular_hash_bloque,guardar_bloque,tiempo_relativo
import ecdsa
import base64
import time
import hashlib
import os
import json


# 📌 Crear un Blueprint para manejar rutas
#app = Blueprint("routes", __name__, template_folder="../templates")

app = Flask(__name__, template_folder="../templates")  # 📌 Indica la ruta de las plantillas

#pasar es al controller
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "../static", "blockchain.json")


@app.route('/storage/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, "../static/storage"), filename)



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home", methods=["POST"])
def check_sender():
    sender = request.form.get("sender")

    if not sender:
        return render_template("home.html", result="⚠️ Debes ingresar una clave", public="", balance=0, 
                               sent_transactions=[], received_transactions=[])

    balance = get_sender_balance(sender)
    data = load_json()

    # Obtener historial de transacciones
    '''sent_transactions = [ {**entry, "time": tiempo_relativo(entry["timenow"])}
    for entry in data if entry["sender"] == sender]
    received_transactions = [ {**entry, "time": tiempo_relativo(entry["timenow"])}
    for entry in data if entry["recipient"] == sender]
    # tiempo = [entry for entry in data if entry["timenow"] == sender]'''

    transactions = [
    {**entry, "time": tiempo_relativo(entry["timenow"]), 
     "type": "enviado" if entry["sender"] == sender else "recibido"}
    for entry in data if entry["sender"] == sender or entry["recipient"] == sender]



    result = "✅ Clave válida" if balance > 0 else "❌ Clave no encontrada"
    
    return render_template("home.html", result=result, public=sender, balance=balance,transactions=transactions)



@app.route('/transfer', methods=['POST'])
def transfer():
    public_key = request.form.get('public_key')
    if public_key:
        #return jsonify({"message": "Transferencia realizada", "public_key": public_key})
        return render_template("transfer.html",public=public_key)
    return jsonify({"error": "Clave pública no encontrada"}), 400


@app.route('/bien')
def bien():
    #return redirect(url_for("/"))
    return render_template("index.html")

@app.route('/cuenta')
def cuenta():
    return render_template("cuenta.html")








DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
KEYS_DIR = os.path.join(DOWNLOADS_DIR, "crypto_SOL_keys")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.abspath(os.path.join(BASE_DIR, "../static", "blockchain.json"))

ARCHIVO_BLOCKCHAIN = JSON_PATH
print(f"📁 Ruta blockchain.json: {ARCHIVO_BLOCKCHAIN}")

# 📌 Crear claves si no existen
def generar_claves():
    if not os.path.exists(KEYS_DIR):
        os.makedirs(KEYS_DIR)
    
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        print("✅ Claves ya existen.")
        return leer_claves()
    
    print("🔑 Generando claves nuevas...")
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_key.to_pem())
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_key.to_pem())
    
    print("✅ Claves generadas correctamente.")
    return private_key, public_key

# 📌 Leer claves existentes
def leer_claves():
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            private_key = ecdsa.SigningKey.from_pem(f.read())
        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key = ecdsa.VerifyingKey.from_pem(f.read())
        return private_key, public_key
    except Exception as e:
        print(f"❌ Error al leer claves: {e}")
        return None, None

# 📌 Obtener clave pública en HEX
def obtener_clave_publica():
    _, public_key = leer_claves()
    if public_key:
        return public_key.to_string().hex()
    print("❌ No se pudo obtener la clave pública.")
    return None

# 📌 Cargar blockchain
def cargar_blockchain():
    if not os.path.exists(ARCHIVO_BLOCKCHAIN):
        print("📄 No existe blockchain.json, iniciando una nueva blockchain.")
        return []
    try:
        with open(ARCHIVO_BLOCKCHAIN, "r") as f:
            data = json.load(f)
        print(f"✅ Blockchain cargada ({len(data)} bloques).")
        return data
    except json.JSONDecodeError:
        print("❌ Error: blockchain.json tiene formato inválido.")
        return []

# 📌 Verificar si el sender ya tiene un bloque
def sender_existe(sender, blockchain):
    existe = any(bloque["sender"] == sender for bloque in blockchain)
    if existe:
        print(f"⚠️ Sender {sender} ya tiene un bloque.")
    return existe

# 📌 Obtener último bloque
def obtener_ultimo_bloque(blockchain):
    if not blockchain:
        return 0, "0"
    return blockchain[-1]["version"], blockchain[-1]["hash"]

# 📌 Calcular hash del bloque
def calcular_hash_bloque(bloque):
    bloque_str = json.dumps(bloque, sort_keys=True).encode()
    return hashlib.sha256(bloque_str).hexdigest()

# 📌 Crear nuevo bloque
def crear_bloque(amount):
    print(f"⚙️ Creando bloque con amount: {amount}")
    
    sender = obtener_clave_publica()
    if sender is None:
        return None, "❌ ERROR: No se pudo obtener la clave pública."

    blockchain = cargar_blockchain()
    
    if sender_existe(sender, blockchain):
        return None, "❌ ERROR: Ya existe un bloque con este sender."
    
    ultima_version, previous_hash = obtener_ultimo_bloque(blockchain)
    
    bloque = {
        "version": ultima_version + 1,
        "hash": "",
        "amount": amount,
        "sender": sender,
        "recipient": None,
        "timenow": int(time.time()),
        "previous_hash": previous_hash
    }
    bloque["hash"] = calcular_hash_bloque(bloque)
    print(f"✅ Bloque creado: {bloque}")
    return bloque, "✅ Bloque creado exitosamente."

# 📌 Guardar bloque
def guardar_bloque(bloque):
    if not bloque:
        return
    blockchain = cargar_blockchain()
    blockchain.append(bloque)
    with open(ARCHIVO_BLOCKCHAIN, "w") as f:
        json.dump(blockchain, f, indent=4)
    print(f"💾 Bloque guardado ({len(blockchain)} bloques en total).")

@app.route("/new", methods=["POST"])
def new():
    claves = generar_claves()
    if claves[0] is None:
        return jsonify({"error": "No se pudo generar claves"}), 500
    return jsonify({
        "message": "Cuenta creada exitosamente",
        "private_key": claves[0].to_string().hex(),
        "public_key": claves[1].to_string().hex()
    }), 200

@app.route("/create_block")
def create_block():
    '''data = request.get_json()
    if not data or "amount" not in data:
        print("❌ Error: Datos inválidos en la petición.")
        return jsonify({"error": "Datos inválidos"}), 400
    
    amount = data.get("amount", 1)
    print(f"📩 Recibida petición para crear bloque con amount: {amount}")'''

    bloque, mensaje = crear_bloque(100)
    if bloque:
        guardar_bloque(bloque)
        return jsonify({"message": mensaje, "block": bloque}), 200
    #return jsonify({"error": mensaje}), 400
    return jsonify("Ya se a creado Cuenta Cripto SOL")
'''@app.route("/new",methods=["POST"])
def new():
     return jsonify({"message": "Cuenta creada exitosamente"}), 200
'''




@app.route('/finalizar', methods=['POST'])
def finalizar_transferencia():
    private_key = request.form.get('private_key')
    public_key = request.form.get('public_key')
    recipient = request.form.get('recipient')
    amount = request.form.get('amount')
    
    if not all([private_key, public_key, recipient, amount]):
        return jsonify({"error": "Todos los campos son obligatorios"}), 400
    
    try:
        amount = int(amount)
        if amount <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
    except ValueError:
        return jsonify({"error": "Cantidad inválida"}), 400
    
    if not verificar_claves(private_key, public_key):
        return render_template("llave.html")
        #return jsonify({"error": "Claves incorrectas"}), 400
    
    balance_sender = obtener_balance(public_key)
    if balance_sender < amount:
        #return jsonify({"error": "Saldo insuficiente"}), 400
        return render_template("vacio.html")
    
    
    blockchain = cargar_blockchain()
    ultima_version, previous_hash = obtener_ultimo_bloque(blockchain)
    nueva_version = ultima_version + 1
    timenow = int(time.time())
    
    bloque = {
        "version": nueva_version,
        "hash": "",
        "amount": amount,
        "sender": public_key,
        "recipient": recipient,
        "timenow": timenow,
        "previous_hash": previous_hash
    }
    
    bloque["hash"] = calcular_hash_bloque(bloque)
    guardar_bloque(bloque)

    return render_template("bien.html",public=public_key)
    
