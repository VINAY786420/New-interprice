# frontend/Dockerfile (quick fix): allow build without package-lock.json
# Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Copy package.json only and use npm install to work without package-lock.json
COPY package.json ./
RUN npm install --silent

# Copy the rest of the source
COPY . .

# Accept REACT_APP_API_URL as a build-arg and export it as an ENV so react-scripts can read it at build time
ARG REACT_APP_API_URL=""
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Build the production bundle
RUN npm run build

# Production stage: serve with nginx
FROM nginx:stable-alpine

# Remove default nginx static content and replace with React build
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
