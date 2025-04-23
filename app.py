from flask import Flask, request
import requests
import json
import threading
import httpx
from collections import defaultdict, deque

from config import rol, OPENROUTER_API_KEY, VERIFY_TOKEN, PAGE_ACCESS_TOKEN
from embeddings import buscar_contexto

app = Flask(__name__)
deque_max = 16
conversaciones = defaultdict(lambda: deque(maxlen=deque_max))

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
        mensaje = evento['message']['text']
        print(f"\n📝 Mensaje de {sender_id}: {mensaje}")

        conversaciones[sender_id].append({"role": "user", "content": mensaje})

        contexto = buscar_contexto(mensaje)

        historial = [
            {"role": "system", "content": rol},
            {"role": "system", "content": f"Información relevante:\n{contexto}"},
            *conversaciones[sender_id]
        ]

        respuesta = responder_con_openrouter(historial)
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
        return "Lo siento, hubo un error al generar la respuesta."

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

if __name__ == '__main__':
    app.run(port=5000)
