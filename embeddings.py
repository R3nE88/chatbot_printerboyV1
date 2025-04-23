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
    texto = f"Sucursal: {row['Sucursal']}, Ciudad: {row['Ciudad']}, Horario: {row['Horario']}, Telefono: {row['Telefono']}$"
    base_conocimiento.append(texto)

for _, row in politicas_df.iterrows():
    texto = f"Política sobre {row['Tema']}: {row['Detalle']}"
    base_conocimiento.append(texto)

for _, row in calculos_df.iterrows():
    texto = f"Cálculo relacionado con '{row['Pregunta']}': {row['Explicacion']}"
    base_conocimiento.append(texto)

vectores = modelo.encode(base_conocimiento)

def buscar_contexto(mensaje, top_n=4):
    emb_mensaje = modelo.encode([mensaje])
    similitudes = cosine_similarity(emb_mensaje, vectores)[0]
    top_indices = np.argsort(similitudes)[-top_n:][::-1]
    contexto = "\n".join([base_conocimiento[i] for i in top_indices])
    return contexto
