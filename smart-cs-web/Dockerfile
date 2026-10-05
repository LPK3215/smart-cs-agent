# smart-cs-web — Vue3 frontend (build stage + nginx serve)
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Build with vite directly (skip strict vue-tsc type-check so the image always builds;
# type-check is enforced separately in CI via `npm run build`).
RUN npx vite build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# SPA fallback so client-side routes work behind nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
