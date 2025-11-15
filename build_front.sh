#!/bin/bash

# Build script for wplace-alerter frontend
# This script builds the Angular frontend and deploys it to data/frontend_build

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Angular frontend...${NC}"

# Navigate to frontend directory
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found!${NC}"
    exit 1
fi

cd frontend

# Build the frontend
echo -e "${YELLOW}Running ng build...${NC}"
if ng build; then
    echo -e "${GREEN}Frontend build completed successfully!${NC}"
else
    echo -e "${RED}Error: Build failed!${NC}"
    exit 1
fi

# Return to root directory
cd ..

# Clean the deployment directory
echo -e "${YELLOW}Cleaning data/frontend_build directory...${NC}"
if [ -d "data/frontend_build" ]; then
    rm -rf data/frontend_build/*
else
    mkdir -p data/frontend_build
fi

# Move built files to deployment directory
echo -e "${YELLOW}Deploying build files...${NC}"
if [ -d "frontend/dist/wplace-alerter" ]; then
    mv frontend/dist/wplace-alerter/* data/frontend_build/
    echo -e "${GREEN}Frontend deployed successfully to data/frontend_build/${NC}"
    echo -e "${GREEN}Build process completed!${NC}"
else
    echo -e "${RED}Error: Build output directory frontend/dist/wplace-alerter not found!${NC}"
    exit 1
fi
