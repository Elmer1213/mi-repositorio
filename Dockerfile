FROM python:3.11-slim

# Variables de entorno corregidas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY ./app /app

# Crear usuario sin privilegios
RUN adduser --disabled-password appuser

ENV PATH="/home/appuser/.local/bin:/usr/local/bin:${PATH}"

USER appuser

# Healthcheck para verificar si la API responde
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Ejecutar el script al iniciar el contenedor
CMD ["python", "-m",  "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
