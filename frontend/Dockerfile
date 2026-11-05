FROM node:22-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /srv
RUN adduser -D -u 10001 samvid
COPY --from=build /src/.next/standalone ./
COPY --from=build /src/.next/static ./.next/static
USER 10001
EXPOSE 3000
CMD ["node", "server.js"]
