"""
NLP Service Layer for Telegram Bot
- Intent extraction
- Project name extraction with fuzzy matching
- Project list caching from Master Sheet
"""
import os
import time
import re
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

# Try to use rapidfuzz for better performance, fallback to difflib
try:
    from rapidfuzz import fuzz
    FUZZY_LIB = "rapidfuzz"
except ImportError:
    FUZZY_LIB = "difflib"

import gsheets_service as gs

# Database integration for DirOps
try:
    import sys
    sys.path.insert(0, '.')
    from dirops_service.database import create_app
    from dirops_service.models import Project
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# =============================================================================
# Configuration
# =============================================================================

MASTER_SHEET_ID = os.getenv('MASTER_SHEET_ID', '')
MASTER_SHEET_NAME = os.getenv('MASTER_SHEET_NAME', 'Projects')
PROJECT_LIST_CACHE_TTL = 3600  # 1 hour

# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NLPResult:
    """Result from NLP processing"""
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    intent: Optional[str] = None
    confidence: float = 0.0
    raw_text: str = ""
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
    
    def to_dict(self) -> Dict:
        return {
            "project": self.project_name,
            "project_id": self.project_id,
            "intent": self.intent,
            "confidence": round(self.confidence, 2),
            "raw_text": self.raw_text,
            "suggestions": self.suggestions
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

# =============================================================================
# Intent Patterns
# =============================================================================

INTENT_PATTERNS = {
    "query_data": [
        r"(buka|cari|search|find|tampilkan|lihat|cek|ambil|get)",
        r"(apa|siapa|dimana|berapa|jumlah|total)",
        r"(data|file|sheet|project|proyek)"
    ],
    "calculate": [
        r"(hitung|total|sum|avg|rata|hitung|calculat)",
        r"(jumlahkan|totalkan)"
    ],
    "statistic": [
        r"(statistik|stats|analyze|analisis)",
        r"(rerata|median|maks|min|max|min)"
    ],
    "navigate": [
        r"(kembali|back|ke menu|menu awal)",
        r"(buka file|pilih file)"
    ],
    "help": [
        r"(help|bantu|tolong|guid|guide)",
        r"(cara pak|cara pakai|cara gun)"
    ]
}

INTENT_KEYWORDS = {
    "query_data": ["buka", "cari", "search", "find", "tampilkan", "lihat", "cek", "apa", "siapa", "dimana", "berapa", "jumlah", "data", "file", "sheet", "project", "proyek"],
    "calculate": ["hitung", "total", "sum", "avg", "rata", "calculat", "jumlahkan"],
    "statistic": ["statistik", "stats", "analyze", "analisis", "rerata", "median", "maks", "min"],
    "navigate": ["kembali", "back", "ke menu", "menu awal", "buka file", "pilih file"],
    "help": ["help", "bantu", "tolong", "guid", "cara"]
}

# =============================================================================
# Project Cache
# =============================================================================

class ProjectCache:
    """Cache for project list from Master Sheet"""
    
    def __init__(self, ttl: int = PROJECT_LIST_CACHE_TTL):
        self._cache: Dict[str, Dict] = {}  # project_name_lower -> {name, id, sheet_id}
        self._sheet_id_map: Dict[str, str] = {}  # project_name_lower -> sheet_id
        self._last_update: float = 0
        self._ttl = ttl
        self._is_loaded: bool = False
    
    def _is_expired(self) -> bool:
        return time.time() - self._last_update > self._ttl
    
    def load_from_master_sheet(self, sheet_id: str, sheet_name: str) -> bool:
        """Load project list from Master Sheet"""
        if not sheet_id:
            print("[NLP] No MASTER_SHEET_ID configured")
            return False
        
        if not self._is_expired() and self._is_loaded:
            print(f"[NLP] Using cached project list (loaded {time.time() - self._last_update:.0f}s ago)")
            return True
        
        print(f"[NLP] Loading project list from Master Sheet: {sheet_id}/{sheet_name}")
        
        try:
            data = gs.get_sheet_data(sheet_id, sheet_name)
            if not data:
                print("[NLP] No data returned from Master Sheet")
                return False
            
            # Parse project data
            # Expected format: [ProjectName, SheetID, ...] or header row followed by data
            self._cache.clear()
            self._sheet_id_map.clear()
            
            start_row = 0
            # Skip header row if present
            if data and len(data) > 0:
                first_row = [str(c).lower() for c in data[0]]
                if 'name' in first_row or 'project' in first_row or 'sheet' in first_row:
                    start_row = 1
            
            for row in data[start_row:]:
                if not row or len(row) < 2:
                    continue
                
                project_name = str(row[0]).strip()
                sheet_id_val = str(row[1]).strip() if len(row) > 1 else ""
                
                if project_name and sheet_id_val:
                    key = project_name.lower()
                    self._cache[key] = {
                        "name": project_name,
                        "sheet_id": sheet_id_val,
                        "search_terms": self._generate_search_terms(project_name)
                    }
                    self._sheet_id_map[key] = sheet_id_val
            
            self._last_update = time.time()
            self._is_loaded = True
            print(f"[NLP] Loaded {len(self._cache)} projects from Master Sheet")
            return True
            
        except Exception as e:
            print(f"[NLP] Error loading from Master Sheet: {e}")
            return False

    def load_from_database(self) -> bool:
        """Load project list from DirOps database"""
        if not DB_AVAILABLE:
            print("[NLP] Database not available")
            return False
        
        if not self._is_expired() and self._is_loaded:
            print(f"[NLP] Using cached project list (loaded {time.time() - self._last_update:.0f}s ago)")
            return True
        
        print("[NLP] Loading project list from DirOps database")
        
        try:
            app = create_app()
            with app.app_context():
                projects = Project.query.all()
                
                self._cache.clear()
                self._sheet_id_map.clear()
                
                for p in projects:
                    key = p.project_code.lower()
                    self._cache[key] = {
                        "name": f"{p.project_code} - {p.project_name}",
                        "project_code": p.project_code,
                        "project_name": p.project_name,
                        "sheet_id": "",  # Local files don't have sheet_id
                        "search_terms": self._generate_search_terms(p.project_name)
                    }
                    self._sheet_id_map[key] = p.project_code
                
                self._last_update = time.time()
                self._is_loaded = True
                print(f"[NLP] Loaded {len(self._cache)} projects from database")
                return True
                
        except Exception as e:
            print(f"[NLP] Error loading from database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_search_terms(self, name: str) -> List[str]:
        """Generate searchable terms from project name"""
        # Remove common prefixes/suffixes
        name = re.sub(r'^(1LC|1LD|1UP|2LC|2LD|2UP)-\d+[A-Z]?\s*-\s*', '', name, flags=re.IGNORECASE)
        terms = re.findall(r'\b\w{3,}\b', name.lower())
        return terms
    
    def get_all_projects(self) -> List[Dict]:
        """Get all cached projects"""
        result = []
        for v in self._cache.values():
            result.append({
                "name": v["name"],
                "sheet_id": v["sheet_id"],
                "project_code": v.get("project_code", ""),
                "project_name": v.get("project_name", ""),
                "search_terms": v.get("search_terms", [])
            })
        return result
    
    def find_project(self, query: str, threshold: float = 0.6) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """
        Find project using fuzzy matching.
        Returns: (project_name, sheet_id, confidence, suggestions)
        """
        if not self._is_loaded:
            return None, None, 0.0, []
        
        query_lower = query.lower()
        query_clean = re.sub(r'^(1LC|1LD|1UP|2LC|2LD|2UP)-\d+[A-Z]?\s*-\s*', '', query_lower, flags=re.IGNORECASE).strip()
        
        best_match = None
        best_score = 0.0
        best_sheet_id = None
        suggestions = []
        
        for key, data in self._cache.items():
            name = data["name"]
            sheet_id = data["sheet_id"]
            
            # Calculate fuzzy scores
            if FUZZY_LIB == "rapidfuzz":
                # RapidFuzz
                score1 = fuzz.ratio(query_lower, key) / 100.0
                score2 = fuzz.ratio(query_clean, name.lower()) / 100.0
                score3 = fuzz.partial_ratio(query_lower, key) / 100.0
                score4 = fuzz.token_sort_ratio(query_lower, key) / 100.0
            else:
                # difflib fallback
                score1 = SequenceMatcher(None, query_lower, key).ratio()
                score2 = SequenceMatcher(None, query_clean, name.lower()).ratio()
                score3 = SequenceMatcher(None, query_lower, name.lower()).ratio()
                score4 = SequenceMatcher(None, query_clean, key).ratio()
            
            # Take best score
            best_score_candidate = max(score1, score2, score3, score4)
            
            # Check search terms for partial matches
            term_match = False
            for term in data.get("search_terms", []):
                if term in query_clean or query_clean in term:
                    term_match = True
                    break
            
            if term_match:
                best_score_candidate = max(best_score_candidate, 0.7)
            
            if best_score_candidate > best_score:
                best_score = best_score_candidate
                best_match = name
                best_sheet_id = sheet_id
            
            # Collect suggestions (top 5 closest)
            if best_score_candidate > 0.4:
                suggestions.append((name, best_score_candidate))
        
        # Sort suggestions by score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = [s[0] for s in suggestions[:5]]
        
        # Apply threshold
        if best_score >= threshold:
            return best_match, best_sheet_id, best_score, suggestions
        else:
            return None, None, 0.0, suggestions
    
    def refresh(self):
        """Force refresh cache"""
        self._last_update = 0
        self._is_loaded = False


# Global project cache instance
project_cache = ProjectCache()

# =============================================================================
# Intent Extractor
# =============================================================================

class IntentExtractor:
    """Extract intent from user message"""
    
    def __init__(self):
        self._intent_cache: Dict[str, Tuple[str, float]] = {}
    
    def extract(self, text: str) -> Tuple[str, float]:
        """
        Extract intent from text.
        Returns: (intent_name, confidence)
        """
        text_lower = text.lower()
        
        # Check cache
        if text_lower in self._intent_cache:
            return self._intent_cache[text_lower]
        
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, keywords in INTENT_KEYWORDS.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matches += 1
            
            if matches > 0:
                # Normalize by number of keywords
                normalized_score = min(score / max(len(keywords) * 0.3, 1), 1.0)
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_intent = intent
        
        # Apply minimum threshold
        if best_score < 0.2:
            best_intent = "unknown"
            best_score = 0.0
        
        result = (best_intent, best_score)
        self._intent_cache[text_lower] = result
        return result
    
    def clear_cache(self):
        """Clear intent cache"""
        self._intent_cache.clear()


# Global intent extractor
intent_extractor = IntentExtractor()

# =============================================================================
# Project Name Extractor
# =============================================================================

class ProjectNameExtractor:
    """Extract project name from user message"""
    
    def __init__(self, cache: ProjectCache):
        self.cache = cache
    
    def extract(self, text: str) -> Tuple[Optional[str], Optional[str], float, List[str]]:
        """
        Extract project name from text using fuzzy matching.
        Returns: (project_name, sheet_id, confidence, suggestions)
        """
        return self.cache.find_project(text)


# Global project name extractor
project_extractor = ProjectNameExtractor(project_cache)

# =============================================================================
# Main NLP Service
# =============================================================================

class NLPService:
    """
    Main NLP Service that orchestrates intent extraction and project name matching.
    """
    
    def __init__(self):
        self.intent_extractor = intent_extractor
        self.project_extractor = project_extractor
        self.cache = project_cache
    
    def initialize(self, master_sheet_id: str = None, master_sheet_name: str = None) -> bool:
        """Initialize NLP service by loading project list"""
        # Prefer database over Google Sheets for DirOps
        if DB_AVAILABLE:
            print("[NLP] Using DirOps database for project list")
            return self.cache.load_from_database()
        
        sheet_id = master_sheet_id or MASTER_SHEET_ID
        sheet_name = master_sheet_name or MASTER_SHEET_NAME
        
        if not sheet_id:
            print("[NLP] Warning: MASTER_SHEET_ID not set. NLP will work with limited functionality.")
            return False
        
        return self.cache.load_from_master_sheet(sheet_id, sheet_name)
    
    def process(self, text: str, threshold: float = 0.6) -> NLPResult:
        """
        Process user message through NLP pipeline.
        
        Args:
            text: User message
            threshold: Fuzzy matching threshold (0.0 - 1.0)
        
        Returns:
            NLPResult with extracted project, intent, and confidence
        """
        result = NLPResult(raw_text=text)
        
        # Extract intent
        intent, intent_confidence = self.intent_extractor.extract(text)
        result.intent = intent
        
        # Extract project name
        project_name, sheet_id, project_confidence, suggestions = self.project_extractor.extract(text)
        result.project_name = project_name
        result.project_id = sheet_id
        result.confidence = project_confidence
        result.suggestions = suggestions
        
        # If intent confidence is lower, blend it
        if intent_confidence > 0 and project_confidence > 0:
            result.confidence = (result.confidence + intent_confidence) / 2
        
        return result
    
    def refresh_cache(self):
        """Force refresh the project cache"""
        self.cache.refresh()
        # Prefer database over Google Sheets for DirOps
        if DB_AVAILABLE:
            self.cache.load_from_database()
        elif MASTER_SHEET_ID:
            self.cache.load_from_master_sheet(MASTER_SHEET_ID, MASTER_SHEET_NAME)
    
    def get_cached_projects(self) -> List[Dict]:
        """Get list of all cached projects"""
        return self.cache.get_all_projects()


# Global NLP service instance
nlp_service = NLPService()

# =============================================================================
# Convenience Functions
# =============================================================================

def initialize_nlp(master_sheet_id: str = None, master_sheet_name: str = None) -> bool:
    """Initialize the global NLP service"""
    return nlp_service.initialize(master_sheet_id, master_sheet_name)

def process_message(text: str, threshold: float = 0.6) -> NLPResult:
    """Process a message and return NLP result"""
    return nlp_service.process(text, threshold)

def get_projects() -> List[Dict]:
    """Get cached project list"""
    return nlp_service.get_cached_projects()

def refresh_projects():
    """Force refresh project cache"""
    nlp_service.refresh_cache()
