FROM node:18-alpine

WORKDIR /app

# Install build dependencies for Alpine Linux
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Serve the application with disabled host check
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000", "--strictPort"]
