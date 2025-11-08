# Base
FROM node:18
WORKDIR /app

# Instalar Angular CLI y http-server (opcional)
RUN npm install -g @angular/cli
RUN npm install -g http-server

# Copiar todo el código del frontend
COPY . .

# Instalar dependencias
RUN npm install

# Exponer puerto 4200
EXPOSE 4200

# Comando para desarrollo en caliente
CMD ["ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--disable-host-check"]
