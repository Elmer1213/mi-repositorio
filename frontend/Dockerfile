# Etapa de build
FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Compilar app en modo producción
RUN npm run build -- --configuration production

# Ejecutar Angular en modo servidor de desarrollo
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0"]

