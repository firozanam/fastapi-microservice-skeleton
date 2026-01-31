#!/bin/bash
# Start script for FastAPI application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="${APP_NAME:-microservice-api}"
APP_VERSION="${APP_VERSION:-1.0.0}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
WORKERS="${WORKERS:-4}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ${APP_NAME} v${APP_VERSION}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and configure your environment.${NC}"
    echo ""
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to handle shutdown
shutdown() {
    echo -e "${YELLOW}Shutting down ${APP_NAME}...${NC}"
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Start application
echo -e "${GREEN}Starting ${APP_NAME}...${NC}"
echo -e "Host: ${HOST}"
echo -e "Port: ${PORT}"
echo -e "Workers: ${WORKERS}"
echo -e "Log Level: ${LOG_LEVEL}"
echo ""

# Run with gunicorn in production, uvicorn in development
if [ "${DEBUG:-false}" = "true" ]; then
    echo -e "${YELLOW}Running in development mode with uvicorn...${NC}"
    uvicorn app.main:app \
        --host ${HOST} \
        --port ${PORT} \
        --reload \
        --log-level ${LOG_LEVEL}
else
    echo -e "${GREEN}Running in production mode with gunicorn...${NC}"
    gunicorn app.main:app \
        --bind ${HOST}:${PORT} \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --worker-tmp-dir /dev/shm \
        --timeout 120 \
        --keepalive 5 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile - \
        --error-logfile - \
        --log-level ${LOG_LEVEL}
fi
