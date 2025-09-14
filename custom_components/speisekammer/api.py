"""Async API Wrapper für Speisekammer"""

import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class SpeisekammerAPI:
    """API-Wrapper für die Speisekammer."""

    def __init__(self, token: str):
        self._token = token
        self._headers = {"Authorization": f"Bearer {self._token}"}
        self._base_url = "https://api.speisekammer.app/"

    async def _get(self, endpoint: str, params: dict = None):
        """Interner GET-Aufruf."""
        url = self._base_url + endpoint
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self._headers, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    _LOGGER.debug("API Response from %s: %s", endpoint, data)
                    return data
            except aiohttp.ClientResponseError as e:
                _LOGGER.error("HTTP Error %s for %s", e.status, url)
                raise
            except Exception as e:
                _LOGGER.exception("Unexpected error while calling %s: %s", url, e)
                raise

    async def get_communities(self):
        """Gibt alle Communities zurück."""
        return await self._get("communities")

    async def get_storage_locations(self, community_id: str):
        """Gibt alle Lagerorte einer Community zurück."""
        return await self._get(f"communities/{community_id}/storage-locations")

    async def get_items(self, community_id: str):
        """Holt alle Artikel für eine Community aus allen Lagerorten."""
        try:
            locations = await self.get_storage_locations(community_id)
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Lagerorte: %s", e)
            return []

        all_items = []
        for loc in locations:
            loc_id = loc.get("id")
            if not loc_id:
                continue
            try:
                items = await self._get(f"stock/{community_id}/{loc_id}")
                # Lagerort-Name für spätere Zuordnung anfügen
                for i in items:
                    i["location"] = loc.get("name", "Unbekannt")
                all_items.extend(items)
            except Exception as e:
                _LOGGER.error("Fehler beim Abrufen der Items für Lagerort %s: %s", loc_id, e)
                continue

        return all_items
