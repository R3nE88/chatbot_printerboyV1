from flask import Flask, request, render_template
import requests
import json
import threading
import httpx
from collections import defaultdict, deque
import os

from config import rol
#from env import OPENROUTER_API_KEY, VERIFY_TOKEN, PAGE_ACCESS_TOKEN
from embeddings import buscar_contexto
import os

# Si existe un archivo .env, lo carga (para entorno local)
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

app = Flask(__name__)
deque_max = 16
conversaciones = defaultdict(lambda: deque(maxlen=deque_max))
usuarios_info = {}  # key = sender_id, value = {"nombre": "Juan Pérez", "activo": True}

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
    try:
        sender_id = evento['sender']['id']
        mensaje = evento['message'].get('text', '').strip()

        if sender_id not in usuarios_info:
            nombre = obtener_nombre_usuario(sender_id)
            usuarios_info[sender_id] = {"nombre": nombre, "activo": True}
            print(f"📝 Usuario {usuarios_info[sender_id]['nombre']} guardado con estado 'activo'!")
        else:
            print(f"🔍 Usuario {usuarios_info[sender_id]['nombre']} ya existe. Estado actual: {usuarios_info[sender_id]['activo']}")


        if not usuarios_info[sender_id]["activo"]:
            print(f"⛔ Usuario {usuarios_info[sender_id]['nombre']} está inactivo. No se responderá.")
            return

        print(f"\n📝 Mensaje de {sender_id}: {mensaje}")

        conversaciones[sender_id].append({"role": "user", "content": mensaje})

        contexto = buscar_contexto(mensaje)

        historial = [
            {"role": "system", "content": rol},
            {"role": "system", "content": f"Información relevante:\n{contexto}"},
            *conversaciones[sender_id]
        ]

        respuesta = responder_con_openrouter(historial)
        if not respuesta:
            print("⚠️ Respuesta vacía o con error. No se enviará nada.")
            return
        conversaciones[sender_id].append({"role": "assistant", "content": respuesta})

        enviar_mensaje(sender_id, respuesta)

    except Exception as e:
        print("❌ Error al procesar mensaje:", e)

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


port = int(os.environ.get("PORT", 5000))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)