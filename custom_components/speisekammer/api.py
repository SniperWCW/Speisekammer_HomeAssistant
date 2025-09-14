"""Async API Wrapper für Speisekammer"""

import aiohttp
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class SpeisekammerAPI:
    def __init__(self, token: str, session: Optional[aiohttp.ClientSession] = None):
        self._token = token
        self._headers = {"Authorization": f"Bearer {self._token}"}
        self._base_url = "https://api.speisekammer.app/"
        self._session = session

    async def _get(self, endpoint: str, params: dict = None):
        """Führt einen GET-Request gegen die API aus."""
        url = self._base_url + endpoint
        session = self._session or aiohttp.ClientSession()

        try:
            async with session.get(
                url, headers=self._headers, params=params, timeout=15
            ) as resp:
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
        finally:
            if self._session is None:
                await session.close()

    async def get_communities(self):
        """Alle Communities abrufen."""
        return await self._get("communities")

    async def get_items(self, community_id: str):
        """Alle Items einer Community abrufen."""
        return await self._get(f"communities/{community_id}/items")
