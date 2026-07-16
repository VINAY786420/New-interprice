# frontend/Dockerfile (update)
# 1) Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Copy only package.json; use npm install so it works without package-lock.json
COPY package.json ./
RUN npm install --silent

COPY . .
RUN npm run build

# 2) Production stage
FROM nginx:stable-alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
