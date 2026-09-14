"""
Search History and Saved Searches System
Provides functionality for tracking search history and saving searches for later use
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class SearchHistoryManager:
    """Manages search history and saved searches"""
    
    MAX_HISTORY_ITEMS = 50
    MAX_SAVED_SEARCHES = 100
    
    def __init__(self):
        """Initialize the search history manager"""
        # Use path_utils for correct path when installed (AppData)
        from utils.path_utils import get_data_dir
        self.data_dir = get_data_dir()
        
        self.history_file = self.data_dir / "search_history.json"
        self.saved_searches_file = self.data_dir / "saved_searches.json"
        
        self.history: List[Dict] = []
        self.saved_searches: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """Load history and saved searches from files"""
        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading search history: {e}")
                self.history = []
        
        # Load saved searches
        if self.saved_searches_file.exists():
            try:
                with open(self.saved_searches_file, 'r', encoding='utf-8') as f:
                    self.saved_searches = json.load(f)
            except Exception as e:
                logger.error(f"Error loading saved searches: {e}")
                self.saved_searches = []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving search history: {e}")
    
    def _save_saved_searches(self):
        """Save saved searches to file"""
        try:
            with open(self.saved_searches_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_searches, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error saving saved searches: {e}")
    
    # ==================== History Operations ====================
    
    def add_to_history(self, search_term: str, table_name: str, 
                       conditions: Optional[Dict] = None, result_count: int = 0):
        """Add a search to history"""
        if not search_term and not conditions:
            return
        
        entry = {
            'id': len(self.history) + 1,
            'search_term': search_term,
            'table_name': table_name,
            'conditions': conditions,
            'result_count': result_count,
            'timestamp': datetime.now().isoformat(),
            'type': 'advanced' if conditions else 'simple'
        }
        
        # Remove duplicate if exists
        self.history = [h for h in self.history 
                       if not (h.get('search_term') == search_term 
                              and h.get('table_name') == table_name
                              and h.get('conditions') == conditions)]
        
        # Add to beginning of list
        self.history.insert(0, entry)
        
        # Limit history size
        if len(self.history) > self.MAX_HISTORY_ITEMS:
            self.history = self.history[:self.MAX_HISTORY_ITEMS]
        
        self._save_history()
    
    def get_history(self, table_name: Optional[str] = None, 
                   limit: int = 20) -> List[Dict]:
        """Get search history, optionally filtered by table name"""
        if table_name:
            filtered = [h for h in self.history if h.get('table_name') == table_name]
            return filtered[:limit]
        return self.history[:limit]
    
    def get_recent_searches(self, table_name: str, limit: int = 10) -> List[str]:
        """Get recent simple search terms for autocomplete"""
        recent = []
        for h in self.history:
            if h.get('table_name') == table_name and h.get('type') == 'simple':
                term = h.get('search_term')
                if term and term not in recent:
                    recent.append(term)
                    if len(recent) >= limit:
                        break
        return recent
    
    def clear_history(self, table_name: Optional[str] = None):
        """Clear search history"""
        if table_name:
            self.history = [h for h in self.history if h.get('table_name') != table_name]
        else:
            self.history = []
        self._save_history()
    
    def remove_from_history(self, entry_id: int):
        """Remove specific entry from history"""
        self.history = [h for h in self.history if h.get('id') != entry_id]
        self._save_history()
    
    # ==================== Saved Searches Operations ====================
    
    def save_search(self, name: str, table_name: str, 
                   search_term: Optional[str] = None,
                   conditions: Optional[Dict] = None,
                   description: str = "") -> bool:
        """Save a search for later use"""
        if not name:
            return False
        
        # Check if name already exists
        existing = next((s for s in self.saved_searches 
                        if s.get('name') == name and s.get('table_name') == table_name), None)
        
        entry = {
            'id': existing['id'] if existing else len(self.saved_searches) + 1,
            'name': name,
            'table_name': table_name,
            'search_term': search_term,
            'conditions': conditions,
            'description': description,
            'created_at': existing.get('created_at') if existing else datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'use_count': existing.get('use_count', 0) if existing else 0
        }
        
        if existing:
            # Update existing
            idx = self.saved_searches.index(existing)
            self.saved_searches[idx] = entry
        else:
            # Add new
            if len(self.saved_searches) >= self.MAX_SAVED_SEARCHES:
                return False
            self.saved_searches.append(entry)
        
        self._save_saved_searches()
        return True
    
    def get_saved_searches(self, table_name: Optional[str] = None) -> List[Dict]:
        """Get saved searches, optionally filtered by table name"""
        if table_name:
            return [s for s in self.saved_searches if s.get('table_name') == table_name]
        return self.saved_searches
    
    def get_saved_search(self, search_id: int) -> Optional[Dict]:
        """Get a specific saved search by ID"""
        return next((s for s in self.saved_searches if s.get('id') == search_id), None)
    
    def get_saved_search_by_name(self, name: str, table_name: str) -> Optional[Dict]:
        """Get a saved search by name and table"""
        return next((s for s in self.saved_searches 
                    if s.get('name') == name and s.get('table_name') == table_name), None)
    
    def delete_saved_search(self, search_id: int) -> bool:
        """Delete a saved search"""
        original_len = len(self.saved_searches)
        self.saved_searches = [s for s in self.saved_searches if s.get('id') != search_id]
        if len(self.saved_searches) < original_len:
            self._save_saved_searches()
            return True
        return False
    
    def increment_use_count(self, search_id: int):
        """Increment the use count for a saved search"""
        for search in self.saved_searches:
            if search.get('id') == search_id:
                search['use_count'] = search.get('use_count', 0) + 1
                search['last_used'] = datetime.now().isoformat()
                self._save_saved_searches()
                break
    
    def get_frequently_used(self, table_name: Optional[str] = None, 
                           limit: int = 5) -> List[Dict]:
        """Get most frequently used saved searches"""
        searches = self.get_saved_searches(table_name)
        sorted_searches = sorted(searches, 
                                key=lambda x: x.get('use_count', 0), 
                                reverse=True)
        return sorted_searches[:limit]


# Global instance
_search_history_manager: Optional[SearchHistoryManager] = None


def get_search_history_manager() -> SearchHistoryManager:
    """Get the global search history manager instance"""
    global _search_history_manager
    if _search_history_manager is None:
        _search_history_manager = SearchHistoryManager()
    return _search_history_manager
