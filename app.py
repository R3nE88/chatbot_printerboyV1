from flask import Flask, request, render_template
import requests
import json
import threading
import httpx
from collections import defaultdict, deque
import os
from config import rol
from embeddings import buscar_contexto
from storage import StorageManager
from datetime import datetime, timezone
import pytz
import threading

# Si existe un archivo .env, lo carga (para entorno local)
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

app = Flask(__name__)

storage = StorageManager()
deque_max = 16
# Cargar datos guardados
usuarios_info = storage.cargar_usuarios()
conversaciones = storage.cargar_conversaciones(deque_max=deque_max)
bot_activo = storage.cargar_estado_bot()  # ← Nuevo: estado global del bot
message_timers = {}


@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Token incorrecto", 403

@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    try:
        data = request.get_json(force=True)
        print("\n✅ POST recibido:")
        print(json.dumps(data, indent=2))

        if 'entry' in data:
            for entry in data['entry']:
                for messaging_event in entry.get('messaging', []):
                    if 'message' in messaging_event and 'text' in messaging_event['message']:
                        threading.Thread(target=procesar_mensaje, args=(messaging_event,)).start()
        return "ok", 200
    except Exception as e:
        print("❌ Error en webhook:", e)
        return "error", 500

def procesar_mensaje(evento):
    if not bot_activo:
        return

    sender_id = evento['sender']['id']
    mensaje = evento['message']['text'].strip()

    # Inicializar usuario la primera vez
    now = datetime.now(pytz.timezone('America/Phoenix'))
    user = usuarios_info.setdefault(sender_id, {
        "nombre": obtener_nombre_usuario(sender_id),
        "activo": True,
        "message_buffer": []
    })

    if not user["activo"]:
        return

    # 1) Acumula
    user["message_buffer"].append(mensaje)
    user["last_message_time"] = now
    storage.guardar_usuarios(usuarios_info)

    # 2) Cancela timer previo (si existe)
    if sender_id in message_timers:
        message_timers[sender_id].cancel()

    # 3) Arranca un nuevo timer de 5 seg
    def on_timeout():
        buffer = user.get("message_buffer", [])
        if not buffer:
            return
        mensaje_completo = "\n".join(buffer)
        user["message_buffer"] = []
        _procesar_buffer(sender_id, mensaje_completo)

    t = threading.Timer(5, on_timeout)
    message_timers[sender_id] = t
    t.start()

def _procesar_buffer(sender_id, mensaje_completo):
    try:
        # Guardar en historial
        conversaciones[sender_id].append({"role":"user","content":mensaje_completo})
        storage.guardar_conversaciones(conversaciones)

        mst = pytz.timezone('America/Phoenix')
        ahora = datetime.now(mst)
        hora_str = ahora.strftime("%H:%M, %d/%m/%Y")

        contexto = buscar_contexto(mensaje_completo)
        historial = [
            {"role":"system","content": rol},
            {"role":"system","content": f"Información relevante:\n{contexto}"},
            {"role": "system", "content": f"La hora actual es: {hora_str}."},
            *conversaciones[sender_id]
        ]

        respuesta = responder_con_openrouter(historial)
        if respuesta:
            conversaciones[sender_id].append({"role":"assistant","content":respuesta})
            storage.guardar_conversaciones(conversaciones)
            enviar_mensaje(sender_id, respuesta)
    except Exception as e:
        print("❌ Error en _procesar_buffer:", e)

def responder_con_openrouter(historial):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://theprinterboy.com",
            "Content-Type": "application/json"
        }
        data = {
            "model": 'openai/gpt-4.1-nano', #'microsoft/mai-ds-r1:free',#"openai/gpt-3.5-turbo",
            "messages": historial
        }
        response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        respuesta_json = response.json()
        print("🧾 Respuesta JSON:", response.json())
        if "choices" in respuesta_json and len(respuesta_json["choices"]) > 0:
            return respuesta_json["choices"][0]["message"]["content"].strip()
        else:
            print("⚠️ Respuesta inesperada:", respuesta_json)
            return "Lo siento, no pude generar una respuesta en este momento."
    except Exception as e:
        print("❌ Error con OpenRouter:", e)
        return None

def enviar_mensaje(sender_id, mensaje):
    url = "https://graph.facebook.com/v17.0/me/messages"
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": mensaje}
    }
    requests.post(url, params=params, json=payload)

def obtener_nombre_usuario(user_id):
    url = f"https://graph.facebook.com/{user_id}"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "first_name,last_name"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return f"{data.get('first_name', '')} {data.get('last_name', '')}"
    return "Desconocido"

@app.route('/admin')
def panel_admin():
    return render_template("admin.html", usuarios_json=usuarios_info)  # ✅


@app.route('/toggle/<user_id>', methods=['POST'])
def toggle_usuario(user_id):
    if user_id in usuarios_info:
        usuarios_info[user_id]["activo"] = not usuarios_info[user_id]["activo"]
        estado = "activado" if usuarios_info[user_id]["activo"] else "desactivado"
        storage.guardar_usuarios(usuarios_info)
        print(f"🔁 Usuario {usuarios_info[user_id]['nombre']} ha sido {estado}")
    else:
        print(f"⚠️ Usuario con ID {user_id} no encontrado.")
    return "", 204  # No Content

@app.route('/api/usuarios')
def obtener_usuarios():
    return {
        uid: {"nombre": info["nombre"], "activo": info["activo"]}
        for uid, info in usuarios_info.items()
    }

@app.route('/bot/on', methods=['POST'])
def activar_bot():
    global bot_activo
    bot_activo = True
    storage.guardar_estado_bot(bot_activo)
    print("✅ Bot ACTIVADO globalmente.")
    return "", 204

@app.route('/bot/off', methods=['POST'])
def desactivar_bot():
    global bot_activo
    bot_activo = False
    storage.guardar_estado_bot(bot_activo)
    print("⛔ Bot DESACTIVADO globalmente.")
    return "", 204

@app.route('/api/bot_estado')
def estado_bot():
    return {"activo": bot_activo}

port = int(os.environ.get("PORT", 5000))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)