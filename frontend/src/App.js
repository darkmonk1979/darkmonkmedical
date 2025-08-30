import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { Search, Pill, ExternalLink, Clock, Database, Globe, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("unified");
  const [apiHealth, setApiHealth] = useState(null);

  // Check API health on component mount
  useEffect(() => {
    checkApiHealth();
    fetchSearchHistory();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API}/health`);
      setApiHealth(response.data);
    } catch (error) {
      console.error("API health check failed:", error);
      setApiHealth({ status: "error", services: {} });
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const response = await axios.get(`${API}/search/history`);
      setSearchHistory(response.data.slice(0, 5)); // Show last 5 searches
    } catch (error) {
      console.error("Failed to fetch search history:", error);
    }
  };

  const performSearch = async (searchType = "unified") => {
    if (!searchQuery.trim()) {
      setError("Please enter a medication name to search");
      return;
    }

    // For Google search, we don't make API calls since we're using the embed
    if (searchType === "google") {
      setActiveTab("google");
      return;
    }

    setLoading(true);
    setError(null);
    setSearchResults(null);

    try {
      const endpoint = searchType === "unified" ? "/search/unified" : "/search/pbs";
      const response = await axios.post(`${API}${endpoint}`, {
        query: searchQuery,
        search_type: searchType
      });
      setSearchResults(response.data);
      fetchSearchHistory(); // Refresh history
    } catch (error) {
      console.error("Search failed:", error);
      setError(error.response?.data?.detail || "Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const renderPBSResults = (results) => {
    if (!results || !Array.isArray(results) || results.length === 0) {
      return (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>No PBS Results</AlertTitle>
          <AlertDescription>No medications found in the PBS database.</AlertDescription>
        </Alert>
      );
    }

    return (
      <div className="space-y-4">
        {results.map((med, index) => (
          <Card key={index} className="border-blue-200 hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-semibold text-blue-800">
                  {med.drug_name}
                </CardTitle>
                {med.pbs_code && (
                  <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                    PBS: {med.pbs_code}
                  </Badge>
                )}
              </div>
              {med.active_ingredient && (
                <CardDescription className="text-gray-600">
                  Active Ingredient: {med.active_ingredient}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent className="space-y-2">
              {med.form_strength && (
                <p><span className="font-medium">Form &amp; Strength:</span> {med.form_strength}</p>
              )}
              {med.manufacturer && (
                <p><span className="font-medium">Manufacturer:</span> {med.manufacturer}</p>
              )}
              {med.atc_code && (
                <p><span className="font-medium">ATC Code:</span> {med.atc_code}</p>
              )}
              {med.prescriber_type && (
                <p><span className="font-medium">Prescriber Type:</span> {med.prescriber_type}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  // Google CSE Embed with explicit render on tab activation
  const GoogleSearchEmbed = () => {
    const renderedRef = useRef(false);

    useEffect(() => {
      // Try to render when the tab is active
      if (!renderedRef.current && typeof window !== 'undefined') {
        const tryRender = () => {
          try {
            if (window.google && window.google.search && window.google.search.cse && window.google.search.cse.element) {
              window.google.search.cse.element.render({ div: 'gcse-container', tag: 'search' });
              renderedRef.current = true;
              return true;
            }
            if (window.__gcse && typeof window.__gcse.parsetags === 'function') {
              window.__gcse.parsetags();
              renderedRef.current = true;
              return true;
            }
          } catch (e) {
            console.warn('CSE render attempt failed:', e);
          }
          return false;
        };

        // Attempt immediately, then retry a few times if needed
        if (!tryRender()) {
          const retries = [300, 700, 1500];
          let cleared = false;
          const timers = retries.map((ms) => setTimeout(() => {
            if (!renderedRef.current) {
              tryRender();
            }
          }, ms));
          return () => {
            if (!cleared) {
              timers.forEach(clearTimeout);
              cleared = true;
            }
          };
        }
      }
    }, []);

    return (
      <div className="space-y-4">
        <Alert className="border-green-200 bg-green-50">
          <Globe className="h-4 w-4" />
          <AlertTitle className="text-green-800">Google Custom Search</AlertTitle>
          <AlertDescription className="text-green-700">
            Search Australian medical websites including TGA, NPS Medicine Finder, PBS, and Health.gov.au using Google's search engine.
          </AlertDescription>
        </Alert>

        <Card className="border-green-200">
          <CardContent className="p-6">
            {/* Container that we render CSE into */}
            <div id="gcse-container" className="w-full">
              {/* Fallback: If script auto-parses, this also works */}
              <div className="gcse-search"></div>
            </div>
          </CardContent>
        </Card>

        <div className="text-sm text-gray-600 space-y-2">
          <p><strong>Covered Australian Medical Websites:</strong></p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-green-300 text-green-700">TGA</Badge>
              <span>Therapeutic Goods Administration</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-blue-300 text-blue-700">NPS</Badge>
              <span>NPS Medicine Finder</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-purple-300 text-purple-700">PBS</Badge>
              <span>Pharmaceutical Benefits Scheme</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-orange-300 text-orange-700">Health.gov.au</Badge>
              <span>Department of Health</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-blue-600 rounded-full">
              <Pill className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900">
              Australian Medical Search
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Search Australian government medical databases including PBS, TGA, and NPS Medicine Finder 
            for comprehensive medication information
          </p>
          {/* API Health Status */}
          {apiHealth && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <div className="flex items-center gap-2">
                {apiHealth.status === "healthy" ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-600" />
                )}
                <span className="text-sm text-gray-600">
                  API Status: {apiHealth.status}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Search Section */}
        <Card className="mb-8 shadow-lg border-0">
          <CardContent className="p-6">
            <div className="flex gap-4 mb-4">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Enter medication name (e.g., Paracetamol, Aspirin, Insulin)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && performSearch(activeTab)}
                  className="text-lg h-12 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <Button 
                onClick={() => performSearch(activeTab)} 
                disabled={loading}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white px-8"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>

            {/* Search Type Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 bg-gray-100">
                <TabsTrigger value="unified" className="flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Unified Search
                </TabsTrigger>
                <TabsTrigger value="pbs" className="flex items-center gap-2">
                  <Pill className="w-4 h-4" />
                  PBS Only
                </TabsTrigger>
                <TabsTrigger value="google" className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Web Search
                </TabsTrigger>
              </TabsList>

              <div className="mt-4 text-sm text-gray-600">
                <TabsContent value="unified">
                  Search PBS database and get info about web search options
                </TabsContent>
                <TabsContent value="pbs">
                  Search only the Pharmaceutical Benefits Scheme database
                </TabsContent>
                <TabsContent value="google">
                  Search Australian medical websites using Google Custom Search Engine
                </TabsContent>
              </div>
            </Tabs>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Search Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Always show Google CSE when the Web Search tab is active */}
        {activeTab === 'google' && (
          <div className="mb-8">
            <GoogleSearchEmbed />
          </div>
        )}

        {/* Search Results for PBS/Unified searches */}
        {searchResults && activeTab !== 'google' && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Search Results for "{searchQuery}"
            </h2>

            {activeTab === "unified" ? (
              <Tabs defaultValue="pbs" className="w-full">
                <TabsList className="bg-gray-100 mb-6">
                  <TabsTrigger value="pbs" className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    PBS Results ({searchResults.pbs_results?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="google-info" className="flex items-center gap-2">
                    <Globe className="w-4 h-4" />
                    Web Search Info
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="pbs">
                  {renderPBSResults(searchResults.pbs_results)}
                </TabsContent>

                <TabsContent value="google-info">
                  <Alert className="border-blue-200 bg-blue-50">
                    <Globe className="h-4 w-4" />
                    <AlertTitle className="text-blue-800">Web Search Available</AlertTitle>
                    <AlertDescription className="text-blue-700">
                      Switch to the "Web Search" tab above to search Australian medical websites with Google Custom Search.
                    </AlertDescription>
                  </Alert>
                </TabsContent>
              </Tabs>
            ) : (
              renderPBSResults(searchResults)
            )}
          </div>
        )}

        {/* Search History */}
        {searchHistory.length > 0 && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Recent Searches
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {searchHistory.map((search, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSearchQuery(search.query);
                      setActiveTab(search.search_type);
                    }}
                    className="text-blue-600 border-blue-300 hover:bg-blue-50"
                  >
                    {search.query}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>
            Searching official Australian medical databases: PBS, TGA, NPS Medicine Finder
          </p>
          <p className="mt-1">
            Always consult with healthcare professionals for medical advice
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;