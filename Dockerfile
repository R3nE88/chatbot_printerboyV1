# Usa una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de tu proyecto al contenedor
COPY . .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto que usa Flask (por default 8080 en Cloud Run)
ENV PORT 8080

# Comando para correr la app
CMD ["python", "app.py"]