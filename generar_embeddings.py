import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# Cargar modelo (solo local)
modelo = SentenceTransformer('all-MiniLM-L6-v2')

# Cargar Excel
excel_data = pd.read_excel("datos_bot.xlsx", sheet_name=None)

# Cargar hojas
productos_df = excel_data["Productos"]
sucursales_df = excel_data["Sucursales"]
politicas_df = excel_data["Politicas"]
calculos_df = excel_data["Calculos"]

# Construir base de conocimiento
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

# Generar embeddings
vectores = modelo.encode(base_conocimiento)

# Guardar vectores
np.save("vectores.npy", vectores)

# Guardar base_conocimiento
with open("base_conocimiento.pkl", "wb") as f:
    pickle.dump(base_conocimiento, f)

print("✅ Embeddings y base de conocimiento guardados exitosamente.")
