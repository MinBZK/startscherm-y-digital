# Use Node.js as the base image
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Change ownership of the app directory to the node user (which has UID 1000)
RUN chown -R node:node /app

# Switch to non-root user
USER node

# Expose port for development
EXPOSE 3000

# Start the development server
CMD ["npm", "run", "dev"]