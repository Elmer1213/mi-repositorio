# Etapa de construcción
FROM node:18 AS build
WORKDIR /app

COPY package*.json ./
RUN npm install -g @angular/cli
RUN npm install
COPY . .
RUN ng build --configuration docker

# Etapa de ejecución
FROM node:18
WORKDIR /app
COPY --from=build /app/dist/frontend ./dist/frontend
RUN npm install -g http-server
EXPOSE 4200
CMD ["http-server", "dist/frontend", "-p", "4200", "-a", "0.0.0.0"]
