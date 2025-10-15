FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev deps for build)
# Use npm install if package-lock.json doesn't exist, otherwise npm ci
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source
COPY . .

# Build
RUN npm run build

# Output in /app/dist (will be copied to /out by docker-compose command)
CMD ["echo", "Frontend build complete"]
