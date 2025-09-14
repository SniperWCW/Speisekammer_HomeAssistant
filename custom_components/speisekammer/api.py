import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class SpeisekammerAPI:
    def __init__(self, token: str):
        self._token = token
        self._headers = {"Authorization": f"Bearer {self._token}"}
        self._base_url = "https://api.speisekammer.app/"

    async def _get(self, endpoint: str, params: dict = None):
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
        return await self._get("communities")

    async def get_items(self, community_id: str):
        return await self._get(f"communities/{community_id}/items")
