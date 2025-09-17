import aiohttp
import logging
from datetime import datetime, timezone

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

    async def get_item_by_gtin(self, community_id: str, location_id: str, gtin: str):
        url = f"{self._base_url}/stock/{community_id}/{location_id}/{gtin}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    _LOGGER.warning("GTIN %s nicht gefunden in Lagerort %s", gtin, location_id)
                    return None
                else:
                    _LOGGER.error("Fehler beim Abrufen des Artikels: %s – URL: %s", resp.status, url)
                    return None

    async def update_stock(self, community_id: str, location_id: str, items: list):
        url = f"{self._base_url}/stock/{community_id}/{location_id}"
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self._headers(), json=items) as resp:
                if resp.status == 200:
                    _LOGGER.info("Lagerbestand erfolgreich aktualisiert für %s", location_id)
                    return await resp.json()
                _LOGGER.error("Fehler beim Aktualisieren des Lagerbestands: %s – URL: %s", resp.status, url)
                return None

    # NEU: Artikel hinzufügen / aktualisieren
    async def add_item(self, community_id: str, location_id: str, gtin: str, count: int, best_before: str, description: str = ""):
        """
        Fügt einen Artikel hinzu oder aktualisiert ihn.
        best_before: ISO-Datum string z.B. '2025-09-17'
        """
        # Timestamp aus ISO-Datum
        try:
            dt = datetime.fromisoformat(best_before).replace(tzinfo=timezone.utc)
            ts = int(dt.timestamp() * 1000)  # Millisekunden
        except Exception:
            ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

        payload = {
            "gtin": gtin,
            "description": description,
            "attributes": [
                {
                    "count": count,
                    "bestBeforeDate": {
                        "ts": ts
                    }
                }
            ]
        }

        url = f"{self._base_url}/stock/{community_id}/{location_id}"
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self._headers(), json=payload) as resp:
                text = await resp.text()
                if resp.status == 200:
                    _LOGGER.info("Artikel erfolgreich hinzugefügt: %s (%s Stück) in %s", gtin, count, location_id)
                    return await resp.json()
                _LOGGER.error("Fehler beim Hinzufügen des Artikels: %s – %s", resp.status, text)
                raise Exception(f"Fehler beim Hinzufügen des Artikels: {resp.status} {text}")
