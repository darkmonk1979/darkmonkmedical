#!/bin/bash

# Australian Medical Search Application Update Script
# For darkmonk.biz - Quick update from GitHub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="medical-search-app"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory '$APP_DIR' not found!"
    print_error "Please run the full installation script first: ./install.sh"
    exit 1
fi

print_status "Updating Australian Medical Search Application..."

# Stop services
print_status "Stopping services..."
sudo systemctl stop medical-search-backend || true
sudo systemctl stop medical-search-frontend || true

# Backup current .env files
print_status "Backing up environment files..."
cp "$APP_DIR/backend/.env" "$APP_DIR/backend/.env.backup" 2>/dev/null || true
cp "$APP_DIR/frontend/.env" "$APP_DIR/frontend/.env.backup" 2>/dev/null || true

# Pull latest changes
print_status "Pulling latest changes from repository..."
cd "$APP_DIR"
git pull

# Update backend dependencies
print_status "Updating backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Update frontend dependencies
print_status "Updating frontend dependencies..."
cd frontend
yarn install
cd ..

# Restore .env files if they were overwritten
print_status "Restoring environment files..."
if [ -f "backend/.env.backup" ]; then
    if [ -f "backend/.env" ] && ! diff -q "backend/.env" "backend/.env.backup" > /dev/null 2>&1; then
        print_warning "Backend .env file was changed in the update."
        read -p "Do you want to keep your existing configuration? (Y/n): " keep_config
        if [[ ! $keep_config =~ ^[Nn]$ ]]; then
            mv "backend/.env.backup" "backend/.env"
            print_success "Restored existing backend configuration"
        else
            print_warning "Using new backend configuration from repository"
        fi
    fi
fi

if [ -f "frontend/.env.backup" ]; then
    if [ -f "frontend/.env" ] && ! diff -q "frontend/.env" "frontend/.env.backup" > /dev/null 2>&1; then
        print_warning "Frontend .env file was changed in the update."
        read -p "Do you want to keep your existing configuration? (Y/n): " keep_config
        if [[ ! $keep_config =~ ^[Nn]$ ]]; then
            mv "frontend/.env.backup" "frontend/.env"
            print_success "Restored existing frontend configuration"
        else
            print_warning "Using new frontend configuration from repository"
        fi
    fi
fi

cd ..

# Restart services
print_status "Starting services..."
sudo systemctl start medical-search-backend
sudo systemctl start medical-search-frontend

# Wait a moment for services to start
sleep 3

# Check service status
print_status "Checking service status..."
if sudo systemctl is-active --quiet medical-search-backend; then
    print_success "Backend service is running"
else
    print_error "Backend service failed to start"
    print_error "Check logs with: sudo journalctl -u medical-search-backend -n 20"
fi

if sudo systemctl is-active --quiet medical-search-frontend; then
    print_success "Frontend service is running"
else
    print_error "Frontend service failed to start"
    print_error "Check logs with: sudo journalctl -u medical-search-frontend -n 20"
fi

print_success "🏥 Australian Medical Search Application updated successfully!"
echo
echo "🌐 Your application should be available at:"
echo "   • Local: http://localhost:3000"
echo "   • API: http://localhost:8001"
echo
echo "📊 Check service status:"
echo "   • Backend: sudo systemctl status medical-search-backend"
echo "   • Frontend: sudo systemctl status medical-search-frontend"
echo
echo "📝 View logs:"
echo "   • Backend logs: sudo journalctl -u medical-search-backend -f"
echo "   • Frontend logs: sudo journalctl -u medical-search-frontend -f"