FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev deps for build)
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Output in /app/dist (will be copied to /out by docker-compose command)
CMD ["echo", "Frontend build complete"]
