import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Cargar modelo solo para codificar mensajes nuevos
modelo = SentenceTransformer('all-MiniLM-L6-v2')

# Cargar vectores y base de conocimiento ya procesados
vectores = np.load("vectores.npy")
with open("base_conocimiento.pkl", "rb") as f:
    base_conocimiento = pickle.load(f)

# (Opcional) Cargar también datos de sucursales, si quieres mantener respuestas especiales
import pandas as pd
if "datos_bot.xlsx" in os.listdir():
    excel_data = pd.read_excel("datos_bot.xlsx", sheet_name="Sucursales")
    sucursales_df = excel_data
else:
    sucursales_df = None  # Evitar error si no existe en producción

def buscar_contexto(mensaje, top_n=8):
    # Codificar el mensaje
    emb_mensaje = modelo.encode([mensaje])

    # Calcular similitudes
    similitudes = cosine_similarity(emb_mensaje, vectores)[0]
    top_indices = np.argsort(similitudes)[-top_n:][::-1]
    contexto = "\n".join([base_conocimiento[i] for i in top_indices])

    # Agregar información de sucursales si el mensaje lo pide
    palabras_clave_sucursales = ["ubicación", "ubicaciones", "dirección", "direccion", "direcciones", "dónde", "sucursal", "sucursales", "local", "ubican"]

    if sucursales_df is not None and any(palabra in mensaje.lower() for palabra in palabras_clave_sucursales):
        sucursales_contexto = "\n".join([
            f"Sucursal: {row['Sucursal']}, Ciudad: {row['Ciudad']}, Dirección: {row['Ubicacion']}, Teléfono: {row['Telefono']}, Horario: {row['Horario']}"
            for _, row in sucursales_df.iterrows()
        ])
        contexto += "\n" + sucursales_contexto

    return contexto