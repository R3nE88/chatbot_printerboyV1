import os

BASE_PATH = '/tmp'  # Mismo que usas en storage.py

archivos = ['usuarios.json', 'conversaciones.json', 'bot_estado.json']

for archivo in archivos:
    ruta = os.path.join(BASE_PATH, archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
        print(f"✅ Archivo {archivo} eliminado.")
    else:
        print(f"ℹ️ Archivo {archivo} no encontrado.")
