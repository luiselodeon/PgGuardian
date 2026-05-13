FROM node:20-alpine
WORKDIR /app

# Instalar dependencias
COPY package*.json ./ 
RUN npm install

# Copiar código fuente
COPY . .

# Exponer puerto de Vite dev server
EXPOSE 5173

# Ejecutar en modo desarrollo con host habilitado para Docker
CMD ["npm", "run", "dev", "--", "--host"]
