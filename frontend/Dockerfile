# Build stage
FROM node:20-slim as builder

WORKDIR /app

ARG VITE_API_URL
ARG VITE_CONTACT_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_CONTACT_URL=$VITE_CONTACT_URL

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# Runtime stage (nginx)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
