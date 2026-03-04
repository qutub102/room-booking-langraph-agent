# Stage 1: Build the Vite React App
FROM node:18-alpine as build

WORKDIR /app

# Copy package configurations
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app for production
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine

# Copy custom Nginx configuration to add reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built React app to Nginx's web root
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
