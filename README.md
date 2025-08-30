# 🏥 Australian Medical Search Application

A comprehensive medication lookup website for darkmonk.biz that searches Australian government medical databases including PBS, TGA, and NPS Medicine Finder.

## 🌟 Features

- **PBS Database Search**: Search Pharmaceutical Benefits Scheme for medication information
- **Australian Medical Sites**: Google Custom Search integration for TGA, NPS Medicine Finder, Health.gov.au
- **Professional Interface**: Clean, healthcare-themed UI optimized for medical information
- **Search History**: Track and quickly access recent medication searches
- **Unified Search**: Combined results from multiple Australian medical databases
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🚀 Quick Installation

### Prerequisites
- Ubuntu/Debian/CentOS/RedHat server
- Domain name configured (darkmonk.biz)
- Google API Key and Custom Search Engine ID
- GitHub Personal Access Token for private repository

### One-Command Install
```bash
wget https://raw.githubusercontent.com/[YOUR-USERNAME]/[YOUR-REPO]/main/install.sh
chmod +x install.sh
./install.sh
```

### Manual Installation
1. Clone this repository
2. Install system dependencies (Node.js, Python, MongoDB)
3. Configure environment variables
4. Install application dependencies
5. Start services

## 🔧 Configuration

### Backend Environment (.env)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medical_search_db"
CORS_ORIGINS="*"
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_CSE_ID="your-cse-id"
```

### Frontend Environment (.env)
```env
REACT_APP_BACKEND_URL="http://localhost:8001"
WDS_SOCKET_PORT=443
```

## 🛠️ Development

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8001
```

### Frontend (React + Node.js)
```bash
cd frontend
yarn install
yarn start
```

### Database (MongoDB)
```bash
# Install and start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

## 🌐 Production Deployment

The application includes:
- **Systemd Services**: Auto-start on server boot
- **Nginx Configuration**: Reverse proxy for domain access
- **SSL Ready**: Easy Let's Encrypt integration
- **Process Management**: Automatic restart on failure

## 📊 API Endpoints

- `GET /api/health` - API health check
- `POST /api/search/pbs` - Search PBS database
- `POST /api/search/unified` - Combined search results
- `GET /api/search/history` - Recent searches
- `GET /api/search/google-info` - Google CSE information

## 🔍 Usage

1. **PBS Search**: Enter medication name to get detailed PBS information
2. **Web Search**: Use Google Custom Search for Australian medical websites  
3. **Unified Search**: Get both PBS data and web search guidance
4. **Search History**: Click recent searches for quick access

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│  FastAPI Backend │────│   MongoDB       │
│   Port 3000     │    │   Port 8001     │    │   Port 27017    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Google CSE API │
                    │  Medical Sites  │
                    └─────────────────┘
```

## 📱 Supported Medical Databases

- **PBS**: Pharmaceutical Benefits Scheme
- **TGA**: Therapeutic Goods Administration  
- **NPS**: NPS Medicine Finder
- **Health.gov.au**: Department of Health
- **Medicine Safety**: Medicinesafety.gov.au

## 🔄 Updates

To update the application:
```bash
./update.sh
```

## 📞 Support

This application was built for darkmonk.biz medical database search requirements. 

## 📝 License

Private repository for darkmonk.biz deployment.

---

**🏥 Australian Medical Search - Professional medication database lookup for healthcare information**
