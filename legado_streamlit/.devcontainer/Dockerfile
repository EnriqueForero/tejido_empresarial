# Configurar Python
FROM python:3.11.0

# Establecer un directorio de trabajo dentro del contenedor
WORKDIR /app  

# Copiar el archivo de requerimientos
COPY requirements.txt .  

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt  

# Copiar todos los archivos de la aplicación al contenedor
COPY . .  

# Exponer el puerto 8501 (predeterminado de Streamlit)
EXPOSE 8501  

# Ejecutar Streamlit cuando el contenedor se inicie
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
