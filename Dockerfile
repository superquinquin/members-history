# Multi-stage build for Members History application
# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install all dependencies (including dev) for build
RUN npm ci --legacy-peer-deps

# Copy frontend source
COPY frontend/ ./

# Set API URL to empty string for production (uses relative URLs)
ENV VITE_API_URL=""

# Build frontend (creates /app/frontend/dist)
RUN npm run build

# Stage 2: Setup Python backend and serve frontend
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose port
EXPOSE 5001

# Set environment variables
ENV FLASK_ENV=production
ENV FLASK_PORT=5001

# Run the Flask application
CMD ["python", "app.py"]
