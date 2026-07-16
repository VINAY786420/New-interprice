# frontend/Dockerfile (quick fix): allow build without package-lock.json
# Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Copy package.json only and use npm install to work without package-lock.json
COPY package.json ./
RUN npm install --silent

# Copy the rest of the source and build
COPY . .
RUN npm run build

# Production stage: serve with nginx
FROM nginx:stable-alpine

# Remove default nginx static content and replace with React build
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
