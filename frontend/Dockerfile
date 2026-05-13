FROM node:20-alpine
WORKDIR /app

# Instalar dependencias (cache mount para acelerar builds repetidos)
COPY package*.json ./ 
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

# Copiar código fuente
COPY . .

# Exponer puerto de Vite dev server
EXPOSE 5173

# Ejecutar en modo desarrollo con host habilitado para Docker
CMD ["npm", "run", "dev", "--", "--host"]
