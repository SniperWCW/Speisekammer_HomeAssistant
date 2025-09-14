import logging
import requests
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SpeisekammerAPI:
    def __init__(self, token: str, base_url: str = "https://api.speisekammer.app"):
        self._token = token
        self._base_url = base_url.rstrip('/')
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _get(self, path: str, params: dict = None):
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            resp = requests.get(url, headers=self._headers, params=params if params else {})
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            return None

    def get_communities(self):
        return self._get("communities")

    def get_items(self, community_id: str):
        return self._get("items", params={"communityId": community_id})
