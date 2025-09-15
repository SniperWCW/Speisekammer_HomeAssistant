import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class SpeisekammerAPI:
    def __init__(self, token: str):
        self._token = token
        self._base_url = "https://api.speisekammer.app"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json"
        }

    async def get_communities(self):
        url = f"{self._base_url}/communities"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.error("Fehler beim Abrufen der Communities: %s", resp.status)
                return []

    async def get_storage_locations(self, community_id: str):
        url = f"{self._base_url}/communities/{community_id}/storage-locations"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.error("Fehler beim Abrufen der Lagerorte: %s", resp.status)
                return []

    async def get_items(self, community_id: str, storage_location_id: str):
        url = f"{self._base_url}/stock/{community_id}/{storage_location_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.error(
                    "Fehler beim Abrufen der Artikel: %s – URL: %s",
                    resp.status,
                    url
                )
                return []
