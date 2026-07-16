# Multi-stage build: build React app and serve with nginx

# 1) Build stage
FROM node:18-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

# 2) Production stage
FROM nginx:stable-alpine

# Remove default nginx static content and replace with React build
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
