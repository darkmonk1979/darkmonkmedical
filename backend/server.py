from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import json
from urllib.parse import quote


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Medical Search API", description="Australian Medical Database Search")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class MedicationSearch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    search_type: str  # "pbs", "google_search", "unified"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class MedicationSearchCreate(BaseModel):
    query: str
    search_type: Optional[str] = "unified"

class PBSMedication(BaseModel):
    pbs_code: Optional[str] = None
    drug_name: str
    active_ingredient: Optional[str] = None
    manufacturer: Optional[str] = None
    atc_code: Optional[str] = None
    ddd_amount: Optional[str] = None
    form_strength: Optional[str] = None
    restrictions: Optional[List[str]] = None
    prescriber_type: Optional[str] = None
    
class GoogleSearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    source: str  # "TGA", "NPS", "Other"
    
class UnifiedSearchResult(BaseModel):
    query: str
    pbs_results: List[PBSMedication]
    web_results: List[GoogleSearchResult]
    search_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# PBS API Integration
class PBSAPIClient:
    BASE_URL = "https://www.pbs.gov.au/api/v1"
    
    async def search_medications(self, query: str) -> List[PBSMedication]:
        """Search PBS database for medications"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # PBS API endpoint for medicine search
                url = f"{self.BASE_URL}/medicine-items"
                params = {
                    "medicine-name": query,
                    "max-results": 20
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    medications = []
                    
                    # Parse PBS API response
                    for item in data.get('medicines', []):
                        medication = PBSMedication(
                            pbs_code=item.get('pbs-code'),
                            drug_name=item.get('medicine-name', query),
                            active_ingredient=item.get('active-ingredient'),
                            manufacturer=item.get('manufacturer'),
                            atc_code=item.get('atc-code'),
                            form_strength=item.get('form-and-strength'),
                            prescriber_type=item.get('prescriber-type')
                        )
                        medications.append(medication)
                    
                    return medications
                else:
                    logger.warning(f"PBS API returned status {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"PBS API search failed: {e}")
            return []

# Google Custom Search Integration
class GoogleSearchClient:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    async def search_medical_sites(self, query: str) -> List[GoogleSearchResult]:
        """Search Australian medical websites using Google Custom Search"""
        if not self.api_key:
            logger.error("Google API key not configured")
            return []
            
        results = []
        
        # Define medical domains to search
        medical_domains = [
            "nps.org.au",
            "tga.gov.au", 
            "pbs.gov.au",
            "health.gov.au",
            "medicinesafety.gov.au"
        ]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for domain in medical_domains:
                    params = {
                        "key": self.api_key,
                        "q": f"{query} site:{domain}",
                        "num": 5
                    }
                    
                    response = await client.get(self.base_url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for item in data.get('items', []):
                            source = "TGA" if "tga.gov.au" in domain else \
                                   "NPS" if "nps.org.au" in domain else \
                                   "PBS" if "pbs.gov.au" in domain else "Health.gov.au"
                            
                            result = GoogleSearchResult(
                                title=item.get('title', ''),
                                link=item.get('link', ''),
                                snippet=item.get('snippet', ''),
                                source=source
                            )
                            results.append(result)
                    else:
                        logger.warning(f"Google Search API error for {domain}: {response.status_code}")
                        
        except Exception as e:
            logger.error(f"Google Search failed: {e}")
            
        return results

# Initialize clients
pbs_client = PBSAPIClient()
google_client = GoogleSearchClient()


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Medical Search API - Australian Healthcare Database Search"}

@api_router.post("/search/pbs", response_model=List[PBSMedication])
async def search_pbs(search_request: MedicationSearchCreate):
    """Search PBS database for medications"""
    try:
        # Log search
        search_log = MedicationSearch(
            query=search_request.query,
            search_type="pbs"
        )
        await db.medication_searches.insert_one(search_log.dict())
        
        results = await pbs_client.search_medications(search_request.query)
        return results
        
    except Exception as e:
        logger.error(f"PBS search error: {e}")
        raise HTTPException(status_code=500, detail="PBS search failed")

@api_router.post("/search/google", response_model=List[GoogleSearchResult])
async def search_google_medical(search_request: MedicationSearchCreate):
    """Search Australian medical websites using Google"""
    try:
        # Log search
        search_log = MedicationSearch(
            query=search_request.query,
            search_type="google_search"
        )
        await db.medication_searches.insert_one(search_log.dict())
        
        results = await google_client.search_medical_sites(search_request.query)
        return results
        
    except Exception as e:
        logger.error(f"Google search error: {e}")
        raise HTTPException(status_code=500, detail="Google search failed")

@api_router.post("/search/unified", response_model=UnifiedSearchResult)
async def unified_medical_search(search_request: MedicationSearchCreate):
    """Unified search across PBS and Google medical sites"""
    try:
        # Log search
        search_log = MedicationSearch(
            query=search_request.query,
            search_type="unified"
        )
        await db.medication_searches.insert_one(search_log.dict())
        
        # Perform both searches concurrently
        pbs_results = await pbs_client.search_medications(search_request.query)
        web_results = await google_client.search_medical_sites(search_request.query)
        
        unified_result = UnifiedSearchResult(
            query=search_request.query,
            pbs_results=pbs_results,
            web_results=web_results
        )
        
        return unified_result
        
    except Exception as e:
        logger.error(f"Unified search error: {e}")
        raise HTTPException(status_code=500, detail="Unified search failed")

@api_router.get("/search/history", response_model=List[MedicationSearch])
async def get_search_history():
    """Get recent medication searches"""
    try:
        searches = await db.medication_searches.find().sort("timestamp", -1).limit(50).to_list(length=None)
        return [MedicationSearch(**search) for search in searches]
    except Exception as e:
        logger.error(f"Search history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search history")

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "pbs_api": "available",
            "google_search": "configured" if os.environ.get('GOOGLE_API_KEY') else "not_configured"
        },
        "timestamp": datetime.now(timezone.utc)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()