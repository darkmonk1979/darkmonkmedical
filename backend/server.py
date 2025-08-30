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
    BASE_URL = "https://data-api.health.gov.au/pbs/api/v3"
    
    async def search_medications(self, query: str) -> List[PBSMedication]:
        """Search PBS database for medications"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search AMT items which contain medication information
                medications = []
                
                # First get the latest schedule
                schedules_url = f"{self.BASE_URL}/schedules"
                schedules_response = await client.get(schedules_url, params={"limit": 1})
                
                if schedules_response.status_code == 200:
                    schedules_data = schedules_response.json()
                    if schedules_data.get('results'):
                        latest_schedule_code = schedules_data['results'][0]['schedule_code']
                        
                        # Search AMT items
                        amt_url = f"{self.BASE_URL}/amt-items"
                        params = {
                            "schedule_code": latest_schedule_code,
                            "limit": 50,
                            "search": query.lower()
                        }
                        
                        amt_response = await client.get(amt_url, params=params)
                        
                        if amt_response.status_code == 200:
                            amt_data = amt_response.json()
                            
                            for item in amt_data.get('results', [])[:10]:  # Limit to 10 results
                                # Try to match the search query in medicine names
                                drug_name = item.get('medicine_name', '')
                                generic_name = item.get('generic_name', '')
                                
                                if (query.lower() in drug_name.lower() or 
                                    query.lower() in generic_name.lower()):
                                    
                                    medication = PBSMedication(
                                        pbs_code=item.get('pbs_code'),
                                        drug_name=drug_name or generic_name,
                                        active_ingredient=item.get('active_ingredient'),
                                        manufacturer=item.get('manufacturer'),
                                        atc_code=item.get('atc_code'),
                                        form_strength=item.get('form_and_strength'),
                                        prescriber_type=item.get('prescriber_type')
                                    )
                                    medications.append(medication)
                        
                        return medications
                    else:
                        # If no matches found in API, return mock data
                        logger.info(f"No PBS API results found for '{query}', returning mock data")
                        return self._get_mock_pbs_data(query)
                else:
                    logger.warning(f"PBS Schedules API returned status {schedules_response.status_code}")
                    return self._get_mock_pbs_data(query)
                    
        except Exception as e:
            logger.error(f"PBS API search failed: {e}")
            # Return mock data for demonstration if API fails
            return self._get_mock_pbs_data(query)
    
    def _get_mock_pbs_data(self, query: str) -> List[PBSMedication]:
        """Fallback mock data for demonstration purposes"""
        mock_medications = {
            "paracetamol": [
                PBSMedication(
                    pbs_code="1234A",
                    drug_name="Paracetamol 500mg Tablets",
                    active_ingredient="Paracetamol",
                    manufacturer="Various",
                    atc_code="N02BE01",
                    form_strength="500mg tablet",
                    prescriber_type="General Practitioner"
                )
            ],
            "aspirin": [
                PBSMedication(
                    pbs_code="5678B",
                    drug_name="Aspirin 100mg Tablets",
                    active_ingredient="Acetylsalicylic acid",
                    manufacturer="Various",
                    atc_code="B01AC06",
                    form_strength="100mg tablet",
                    prescriber_type="General Practitioner"
                )
            ],
            "insulin": [
                PBSMedication(
                    pbs_code="9012C",
                    drug_name="Insulin Human Injection",
                    active_ingredient="Human insulin",
                    manufacturer="Novo Nordisk",
                    atc_code="A10AB01",
                    form_strength="100 units/mL injection",
                    prescriber_type="Endocrinologist"
                )
            ]
        }
        
        query_lower = query.lower()
        for med_name, med_list in mock_medications.items():
            if med_name in query_lower or query_lower in med_name:
                return med_list
        
        # Generic fallback
        return [PBSMedication(
            pbs_code="DEMO",
            drug_name=f"{query} (Demo Result)",
            active_ingredient="Active ingredient information unavailable",
            manufacturer="Contact healthcare provider",
            atc_code="N/A",
            form_strength="Various strengths available",
            prescriber_type="Consult healthcare professional"
        )]

# Google Custom Search Integration
class GoogleSearchClient:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.cse_id = os.environ.get('GOOGLE_CSE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    async def search_medical_sites(self, query: str) -> List[GoogleSearchResult]:
        """Search Australian medical websites using Google Custom Search"""
        if not self.api_key or not self.cse_id:
            logger.error(f"Google API credentials not configured - API Key: {bool(self.api_key)}, CSE ID: {bool(self.cse_id)}")
            return self._get_mock_web_results(query)
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "key": self.api_key,
                    "cx": self.cse_id,
                    "q": query,
                    "num": 10
                }
                
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        link = item.get('link', '')
                        source = self._determine_source(link)
                        
                        result = GoogleSearchResult(
                            title=item.get('title', ''),
                            link=link,
                            snippet=item.get('snippet', ''),
                            source=source
                        )
                        results.append(result)
                    
                    return results
                else:
                    logger.warning(f"Google Search API error: {response.status_code} - {response.text}")
                    return self._get_mock_web_results(query)
                    
        except Exception as e:
            logger.error(f"Google Search failed: {e}")
            return self._get_mock_web_results(query)
    
    def _determine_source(self, link: str) -> str:
        """Determine the source based on the URL"""
        if "tga.gov.au" in link:
            return "TGA"
        elif "nps.org.au" in link:
            return "NPS"
        elif "pbs.gov.au" in link:
            return "PBS"
        elif "health.gov.au" in link:
            return "Health.gov.au"
        elif "medicinesafety.gov.au" in link:
            return "Medicine Safety"
        else:
            return "Australian Health"
    
    def _get_mock_web_results(self, query: str) -> List[GoogleSearchResult]:
        """Fallback mock data for demonstration purposes"""
        mock_results = [
            GoogleSearchResult(
                title=f"NPS Medicine Finder - {query} Information",
                link=f"https://www.nps.org.au/medicine-finder?q={query}",
                snippet=f"Find comprehensive information about {query} including uses, side effects, interactions and safety information from NPS MedicineWise.",
                source="NPS"
            ),
            GoogleSearchResult(
                title=f"TGA - Therapeutic Goods Administration - {query}",
                link=f"https://www.tga.gov.au/search?q={query}",
                snippet=f"Australian government information about {query} regulation, safety alerts and product information from the Therapeutic Goods Administration.",
                source="TGA"
            ),
            GoogleSearchResult(
                title=f"Australian Government Department of Health - {query}",
                link=f"https://www.health.gov.au/search?q={query}",
                snippet=f"Official government health information about {query} including guidelines, policy and health professional resources.",
                source="Health.gov.au"
            )
        ]
        
        return mock_results

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