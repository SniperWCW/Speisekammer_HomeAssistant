import aiohttp

class SpeisekammerAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.speisekammer.app"

    async def get_communities(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/communities", headers=self._headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def get_storage_locations(self, community_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/communities/{community_id}/storage-locations", headers=self._headers()) as resp:
                return await resp.json()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
