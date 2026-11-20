# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the code and build the app
COPY . .
RUN npm run build

# Production image
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]