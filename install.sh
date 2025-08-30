#!/bin/bash

# Australian Medical Search Application Installation Script
# For darkmonk.biz - Medical Database Search Application
# Author: Emergent AI Assistant

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Australian Medical Search"
APP_DIR="medical-search-app"
REPO_URL=""  # Will be set by user
DOMAIN="darkmonk.biz"
PORT_FRONTEND=3000
PORT_BACKEND=8001

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get user input with default
get_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        echo "${input:-$default}"
    else
        read -p "$prompt: " input
        echo "$input"
    fi
}

# Function to setup GitHub authentication
setup_github_auth() {
    print_status "Setting up GitHub authentication for private repository..."
    
    echo "Choose authentication method:"
    echo "1. SSH Key (recommended)"
    echo "2. Personal Access Token"
    echo "3. Username/Password (deprecated)"
    
    read -p "Enter choice (1-3): " auth_choice
    
    case $auth_choice in
        1)
            print_status "Using SSH Key authentication"
            REPO_URL=$(get_input "Enter your private repository SSH URL (git@github.com:username/repo.git)")
            
            if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
                print_warning "No SSH key found. Please ensure you have SSH key set up with GitHub."
                echo "Generate SSH key with: ssh-keygen -t ed25519 -C \"your_email@example.com\""
                echo "Add public key to GitHub: https://github.com/settings/keys"
                read -p "Press Enter after setting up SSH key..."
            fi
            ;;
        2)
            print_status "Using Personal Access Token"
            USERNAME=$(get_input "Enter your GitHub username")
            TOKEN=$(get_input "Enter your Personal Access Token")
            REPO_NAME=$(get_input "Enter repository name (username/repo-name)")
            REPO_URL="https://${USERNAME}:${TOKEN}@github.com/${REPO_NAME}.git"
            ;;
        3)
            print_warning "Username/Password authentication is deprecated. Consider using Personal Access Token."
            USERNAME=$(get_input "Enter your GitHub username")
            PASSWORD=$(get_input "Enter your GitHub password")
            REPO_NAME=$(get_input "Enter repository name (username/repo-name)")
            REPO_URL="https://${USERNAME}:${PASSWORD}@github.com/${REPO_NAME}.git"
            ;;
        *)
            print_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        print_error "Cannot detect OS. Please install dependencies manually."
        exit 1
    fi
    
    case $OS in
        "Ubuntu"*)
            sudo apt update
            sudo apt install -y curl wget git build-essential
            ;;
        "CentOS"*|"Red Hat"*)
            sudo yum update -y
            sudo yum install -y curl wget git gcc gcc-c++ make
            ;;
        "Debian"*)
            sudo apt update
            sudo apt install -y curl wget git build-essential
            ;;
        *)
            print_warning "Unknown OS: $OS. Please install curl, wget, git, and build tools manually."
            ;;
    esac
}

# Function to install Node.js
install_nodejs() {
    print_status "Installing Node.js..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js already installed: $NODE_VERSION"
        return
    fi
    
    # Install Node.js via NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    
    case $OS in
        "Ubuntu"*|"Debian"*)
            sudo apt-get install -y nodejs
            ;;
        "CentOS"*|"Red Hat"*)
            sudo yum install -y nodejs npm
            ;;
    esac
    
    # Install Yarn
    npm install -g yarn
    
    print_success "Node.js and Yarn installed successfully"
}

# Function to install Python
install_python() {
    print_status "Installing Python..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python already installed: $PYTHON_VERSION"
        return
    fi
    
    case $OS in
        "Ubuntu"*|"Debian"*)
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        "CentOS"*|"Red Hat"*)
            sudo yum install -y python3 python3-pip
            ;;
    esac
    
    print_success "Python installed successfully"
}

# Function to install MongoDB
install_mongodb() {
    print_status "Installing MongoDB..."
    
    if command_exists mongod; then
        print_success "MongoDB already installed"
        return
    fi
    
    case $OS in
        "Ubuntu"*)
            # Import MongoDB GPG key
            wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
            
            # Add MongoDB repository
            echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
            
            sudo apt update
            sudo apt install -y mongodb-org
            ;;
        "CentOS"*|"Red Hat"*)
            # Add MongoDB repository
            cat > /etc/yum.repos.d/mongodb-org-7.0.repo << 'EOF'
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF
            sudo yum install -y mongodb-org
            ;;
    esac
    
    # Start and enable MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    print_success "MongoDB installed and started"
}

# Function to clone repository
clone_repository() {
    print_status "Cloning repository..."
    
    if [ -d "$APP_DIR" ]; then
        print_warning "Directory $APP_DIR already exists"
        read -p "Do you want to update existing installation? (y/N): " update_choice
        
        if [[ $update_choice =~ ^[Yy]$ ]]; then
            print_status "Updating existing installation..."
            cd "$APP_DIR"
            git pull
            cd ..
        else
            print_status "Using existing directory..."
        fi
    else
        git clone "$REPO_URL" "$APP_DIR"
        print_success "Repository cloned successfully"
    fi
}

# Function to setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    cd "$APP_DIR"
    
    # Backend environment
    if [ ! -f "backend/.env" ]; then
        print_status "Creating backend/.env file..."
        
        GOOGLE_API_KEY=$(get_input "Enter your Google API Key" "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")
        GOOGLE_CSE_ID=$(get_input "Enter your Google CSE ID" "010783511027097431382:jphdjk7zock")
        
        cat > backend/.env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medical_search_db"
CORS_ORIGINS="*"
GOOGLE_API_KEY="$GOOGLE_API_KEY"
GOOGLE_CSE_ID="$GOOGLE_CSE_ID"
EOF
        print_success "Backend .env file created"
    else
        print_success "Backend .env file already exists"
    fi
    
    # Frontend environment
    if [ ! -f "frontend/.env" ]; then
        print_status "Creating frontend/.env file..."
        
        BACKEND_URL=$(get_input "Enter backend URL" "http://localhost:$PORT_BACKEND")
        
        cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
WDS_SOCKET_PORT=443
EOF
        print_success "Frontend .env file created"
    else
        print_success "Frontend .env file already exists"
    fi
    
    cd ..
}

# Function to install application dependencies
install_app_dependencies() {
    print_status "Installing application dependencies..."
    
    cd "$APP_DIR"
    
    # Install backend dependencies
    print_status "Installing Python backend dependencies..."
    cd backend
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
    
    cd ..
    
    # Install frontend dependencies
    print_status "Installing Node.js frontend dependencies..."
    cd frontend
    yarn install
    cd ..
    
    cd ..
    print_success "All dependencies installed successfully"
}

# Function to create systemd services
create_services() {
    print_status "Creating systemd services..."
    
    APP_PATH="$(pwd)/$APP_DIR"
    
    # Backend service
    sudo tee /etc/systemd/system/medical-search-backend.service > /dev/null << EOF
[Unit]
Description=Medical Search Backend API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_PATH/backend
Environment=PATH=$APP_PATH/backend/venv/bin
ExecStart=$APP_PATH/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT_BACKEND
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    sudo tee /etc/systemd/system/medical-search-frontend.service > /dev/null << EOF
[Unit]
Description=Medical Search Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_PATH/frontend
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
ExecStart=/usr/bin/yarn start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload
    
    print_success "Systemd services created"
}

# Function to setup nginx (optional)
setup_nginx() {
    read -p "Do you want to setup Nginx reverse proxy? (y/N): " nginx_choice
    
    if [[ $nginx_choice =~ ^[Yy]$ ]]; then
        print_status "Installing and configuring Nginx..."
        
        case $OS in
            "Ubuntu"*|"Debian"*)
                sudo apt install -y nginx
                ;;
            "CentOS"*|"Red Hat"*)
                sudo yum install -y nginx
                ;;
        esac
        
        # Create Nginx config
        sudo tee /etc/nginx/sites-available/medical-search > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Frontend
    location / {
        proxy_pass http://localhost:$PORT_FRONTEND;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:$PORT_BACKEND;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

        sudo ln -sf /etc/nginx/sites-available/medical-search /etc/nginx/sites-enabled/
        sudo nginx -t
        sudo systemctl restart nginx
        sudo systemctl enable nginx
        
        print_success "Nginx configured successfully"
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Start and enable services
    sudo systemctl start medical-search-backend
    sudo systemctl enable medical-search-backend
    
    sudo systemctl start medical-search-frontend
    sudo systemctl enable medical-search-frontend
    
    print_success "Services started and enabled"
}

# Function to display final information
display_info() {
    print_success "🏥 Australian Medical Search Application installed successfully!"
    echo
    echo "📍 Installation Details:"
    echo "   • Application directory: $(pwd)/$APP_DIR"
    echo "   • Frontend: http://localhost:$PORT_FRONTEND"
    echo "   • Backend API: http://localhost:$PORT_BACKEND"
    echo "   • Domain: $DOMAIN"
    echo
    echo "🔧 Useful Commands:"
    echo "   • Check backend status: sudo systemctl status medical-search-backend"
    echo "   • Check frontend status: sudo systemctl status medical-search-frontend"
    echo "   • View backend logs: sudo journalctl -u medical-search-backend -f"
    echo "   • View frontend logs: sudo journalctl -u medical-search-frontend -f"
    echo "   • Restart services: sudo systemctl restart medical-search-backend medical-search-frontend"
    echo
    echo "🌐 Access your application:"
    echo "   • Local: http://localhost:$PORT_FRONTEND"
    if [[ $nginx_choice =~ ^[Yy]$ ]]; then
        echo "   • Domain: http://$DOMAIN"
    fi
    echo
    echo "📚 Features Available:"
    echo "   • PBS medication database search"
    echo "   • Australian medical website search (TGA, NPS, Health.gov.au)"
    echo "   • Search history tracking"
    echo "   • Professional medical interface"
    echo
    print_warning "Remember to:"
    echo "   • Configure your firewall to allow ports $PORT_FRONTEND and $PORT_BACKEND"
    echo "   • Set up SSL certificate for production use"
    echo "   • Configure your router/DDNS to forward traffic to this server"
    echo "   • Update Google API keys if needed in backend/.env"
}

# Main installation function
main() {
    print_status "Starting installation of $APP_NAME"
    echo
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please don't run this script as root"
        exit 1
    fi
    
    # Setup GitHub authentication
    setup_github_auth
    
    # Install system dependencies
    install_system_deps
    
    # Install required software
    install_nodejs
    install_python
    install_mongodb
    
    # Clone repository
    clone_repository
    
    # Setup environment
    setup_environment
    
    # Install app dependencies
    install_app_dependencies
    
    # Create services
    create_services
    
    # Setup nginx (optional)
    setup_nginx
    
    # Start services
    start_services
    
    # Display final information
    display_info
}

# Run main function
main "$@"