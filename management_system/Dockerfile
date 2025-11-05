# 1. Usa una imagen oficial de Python como base
# Usar "slim" ahorra espacio
FROM python:3.14-slim

# 2. Configura variables de entorno
# Previene que Python guarde archivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Asegura que los logs se vean inmediatamente
ENV PYTHONUNBUFFERED 1

# 3. Crea un directorio de trabajo dentro del contenedor
WORKDIR /management-system

# 4. Copia e instala las dependencias
# Se copia solo requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. Copia todo el código de tu proyecto al contenedor
COPY . .

# 6. Expone el puerto que usará Django
EXPOSE 8000

# 7. El comando para ejecutar la app (para desarrollo)
# "0.0.0.0" es crucial para que sea accesible desde fuera del contenedor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]