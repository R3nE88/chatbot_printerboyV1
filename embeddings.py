import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

modelo = SentenceTransformer('all-MiniLM-L6-v2')
excel_data = pd.read_excel("datos_bot.xlsx", sheet_name=None)

productos_df = excel_data["Productos"]
sucursales_df = excel_data["Sucursales"]
politicas_df = excel_data["Politicas"]
calculos_df = excel_data["Calculos"]

base_conocimiento = []

for _, row in productos_df.iterrows():
    texto = f"Producto: {row['Nombre']}, Descripción: {row['Descripcion']}, Precio: {row['Precio']}$"
    base_conocimiento.append(texto)

for _, row in sucursales_df.iterrows():
    texto = (
        f"La sucursal llamada '{row['Sucursal']}' está ubicada en {row['Ubicacion']}, "
        f"{row['Ciudad']}. Su horario de atención es: {row['Horario']}. "
        f"Puedes comunicarte al teléfono {row['Telefono']}."
    )
    base_conocimiento.append(texto)

for _, row in politicas_df.iterrows():
    texto = f"Política sobre {row['Tema']}: {row['Detalle']}"
    base_conocimiento.append(texto)

for _, row in calculos_df.iterrows():
    texto = f"Cálculo relacionado con '{row['Pregunta']}': {row['Explicacion']}"
    base_conocimiento.append(texto)

vectores = modelo.encode(base_conocimiento)

def buscar_contexto(mensaje, top_n=8):
    emb_mensaje = modelo.encode([mensaje])
    similitudes = cosine_similarity(emb_mensaje, vectores)[0]
    top_indices = np.argsort(similitudes)[-top_n:][::-1]
    contexto = "\n".join([base_conocimiento[i] for i in top_indices])

    # Palabras clave que indican que se quiere información de sucursales
    palabras_clave_sucursales = ["ubicación", "ubicaciones", "dirección", "direccion", "direcciones", "dónde", "sucursal", "sucursales", "local", "ubican"]

    if any(palabra in mensaje.lower() for palabra in palabras_clave_sucursales):
        sucursales_contexto = "\n".join([
            f"Sucursal: {row['Sucursal']}, Ciudad: {row['Ciudad']}, Dirección: {row['Ubicacion']}, Teléfono: {row['Telefono']}, Horario: {row['Horario']}"
            for _, row in sucursales_df.iterrows()
        ])
        contexto += "\n" + sucursales_contexto

    return contexto