FROM node:18

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar Angular CLI globalmente
RUN npm install -g @angular/cli@15

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY src ./src
COPY angular.json tsconfig.json tsconfig.app.json ./

# Exponer puerto
EXPOSE 4200

# Comando para desarrollo
CMD ["ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--disable-host-check", "--poll", "2000"]