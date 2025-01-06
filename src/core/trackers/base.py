from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class BaseTracker(ABC):
    """Base class for manga trackers"""

    @abstractmethod
    def search_manga(self, query: str, limit: int = 100, offset: int = 0) -> Dict:
        """Search for manga by title"""
        pass

    @abstractmethod
    def add_manga(self, manga_id: int, status: str = "plan_to_read") -> Dict:
        """Add a manga to user's list"""
        pass

    @abstractmethod
    def update_manga_list_status(self, manga_id: int, **kwargs) -> Dict:
        """Update the user's manga list status"""
        pass

    @abstractmethod
    def delete_manga_list_item(self, manga_id: int) -> bool:
        """Remove a manga from user's list"""
        pass

    @abstractmethod
    def get_user_manga_list(self, **kwargs) -> Dict:
        """Get a user's manga list"""
        pass