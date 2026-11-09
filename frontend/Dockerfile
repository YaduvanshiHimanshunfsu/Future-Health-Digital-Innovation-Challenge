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
# The app runs with `node server.js` alone. The npm and yarn tools that ship with the base image are
# never used at run time, and they carried every known vulnerability Trivy found in this image.
RUN adduser -D -u 10001 samvid \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx \
              /opt/yarn-* /usr/local/bin/yarn /usr/local/bin/yarnpkg
COPY --from=build /src/.next/standalone ./
COPY --from=build /src/.next/static ./.next/static
USER 10001
EXPOSE 3000
CMD ["node", "server.js"]
