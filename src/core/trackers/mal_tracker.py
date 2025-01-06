import requests
from typing import Dict, Optional, List
from .base import BaseTracker

class MALMangaTracker(BaseTracker):
    BASE_URL = "https://api.myanimelist.net/v2"

    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }

    def search_manga(self, query: str, limit: int = 100, offset: int = 0, fields: str = None) -> Dict:
        """Search for manga by title"""
        params = {
            "q": query,
            "limit": min(limit, 15),
            "offset": offset
        }
        if fields:
            params["fields"] = fields

        response = requests.get(
            f"{self.BASE_URL}/manga",
            headers=self.headers,
            params=params
        )

        return response.json()

    def add_manga(self, manga_id, status="plan_to_read"):
        """Add a manga to user's list"""
        url = f"{self.BASE_URL}/manga/{manga_id}/my_list_status"
        data = {
            "status": status
        }

        response = requests.patch(url, headers=self.headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to add manga: {response.text}")

    def get_manga_details(self, manga_id):
        """Get detailed information for a specific manga"""
        url = f"https://api.myanimelist.net/v2/manga/{manga_id}?fields=id,title,synopsis,num_chapters,status,mean,media_type,start_date,end_date,main_picture"
        headers = self.headers

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_manga_ranking(self, ranking_type: str, limit: int = 100,
                         offset: int = 0, fields: str = None) -> Dict:
        """Get manga rankings by different criteria"""
        params = {
            "ranking_type": ranking_type,
            "limit": min(limit, 500),
            "offset": offset
        }
        if fields:
            params["fields"] = fields

        response = requests.get(
            f"{self.BASE_URL}/manga/ranking",
            headers=self.headers,
            params=params
        )
        return response.json()

    def update_manga_list_status(self, manga_id: int,
                               status: Optional[str] = None,
                               score: Optional[int] = None,
                               num_volumes_read: Optional[int] = None,
                               num_chapters_read: Optional[int] = None,
                               comments: Optional[str] = None) -> Dict:
        """Update the user's manga list status"""
        data = {}
        if status:
            data["status"] = status
        if score:
            data["score"] = score
        if num_volumes_read is not None:
            data["num_volumes_read"] = num_volumes_read
        if num_chapters_read is not None:
            data["num_chapters_read"] = num_chapters_read
        if comments:
            data["comments"] = comments

        response = requests.patch(
            f"{self.BASE_URL}/manga/{manga_id}/my_list_status",
            headers=self.headers,
            data=data
        )
        return response.json()

    def delete_manga_list_item(self, manga_id: int) -> bool:
        """Remove a manga from user's list"""
        response = requests.delete(
            f"{self.BASE_URL}/manga/{manga_id}/my_list_status",
            headers=self.headers
        )
        return response.status_code == 200

    def get_user_manga_list(self, username: str = "@me", status: Optional[str] = None,
                           sort: Optional[str] = None, limit: int = 100,
                           offset: int = 0) -> Dict:
        """Get a user's manga list"""
        params = {
            "limit": min(limit, 1000),
            "offset": offset
        }
        if status:
            params["status"] = status
        if sort:
            params["sort"] = sort

        response = requests.get(
            f"{self.BASE_URL}/users/{username}/mangalist",
            headers=self.headers,
            params=params
        )
        return response.json()