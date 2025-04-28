# storage.py
import json
import os
from datetime import datetime
from collections import defaultdict, deque

# Usaremos temp en local y /tmp en Render
BASE_PATH = '/tmp'
os.makedirs(BASE_PATH, exist_ok=True)

class StorageManager:
    def __init__(self):
        self.usuarios_file = os.path.join(BASE_PATH, 'usuarios.json')
        self.conversaciones_file = os.path.join(BASE_PATH, 'conversaciones.json')
        self.estado_bot_file = os.path.join(BASE_PATH, 'bot_estado.json')

    def guardar_json(self, data, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Guardado en {filepath}")
        except Exception as e:
            print(f"❌ Error guardando {filepath}: {e}")

    def cargar_json(self, filepath, default):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error cargando {filepath}: {e}")
        return default

    def guardar_usuarios(self, usuarios_info):
        serializable = {}
        for uid, info in usuarios_info.items():
            info_serializable = info.copy()
            if isinstance(info_serializable.get("last_message_time"), datetime):
                info_serializable["last_message_time"] = info_serializable["last_message_time"].isoformat()
            serializable[uid] = info_serializable
        self.guardar_json(serializable, self.usuarios_file)

    def cargar_usuarios(self):
        data = self.cargar_json(self.usuarios_file, {})
        for uid, info in data.items():
            if "last_message_time" in info and isinstance(info["last_message_time"], str):
                try:
                    info["last_message_time"] = datetime.fromisoformat(info["last_message_time"])
                except ValueError:
                    info["last_message_time"] = datetime.utcnow()
        return data

    def guardar_conversaciones(self, conversaciones):
        serializable = {uid: list(deque_obj) for uid, deque_obj in conversaciones.items()}
        self.guardar_json(serializable, self.conversaciones_file)

    def cargar_conversaciones(self, deque_max=16):
        data = self.cargar_json(self.conversaciones_file, {})
        conversaciones = defaultdict(lambda: deque(maxlen=deque_max))
        for uid, mensajes in data.items():
            conversaciones[uid].extend(mensajes)
        return conversaciones

    def guardar_estado_bot(self, estado):
        self.guardar_json({"activo": estado}, self.estado_bot_file)

    def cargar_estado_bot(self):
        data = self.cargar_json(self.estado_bot_file, {"activo": True})
        return data.get("activo", True)