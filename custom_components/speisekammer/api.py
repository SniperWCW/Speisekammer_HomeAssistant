import aiohttp

class SpeisekammerAPI:
    def __init__(self, token: str):
        self._headers = {"Authorization": f"Bearer {token}"}
        self._base_url = "https://app.speisekammer.app/api/v1/"

    async def _get(self, endpoint: str, params: dict = None):
        url = self._base_url + endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._headers, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_communities(self):
        return await self._get("communities")

    async def get_items(self, community_id: str):
        return await self._get(f"communities/{community_id}/items")