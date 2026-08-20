"""
Base Service Class for API Integrations
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from ahos.utils.logger import logger
from ahos.utils.decorators import retry, timing
from ahos.infrastructure.config.settings import settings
import requests

class BaseService(ABC):
    def __init__(self, name: str, base_url: str = "", api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key or self._get_api_key_from_settings()
        self.session = self._create_session()

    def _get_api_key_from_settings(self) -> Optional[str]:
        key_name = f"{self.name.upper()}_API_KEY"
        return getattr(settings, key_name, None)

    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "AHOS/2.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        if self.api_key:
            session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        return session

    @retry()
    @timing
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"{self.name} GET request failed for {url}: {str(e)}")
            raise

    @retry()
    @timing
    def _post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        try:
            response = self.session.post(url, data=data, json=json, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"{self.name} POST request failed for {url}: {str(e)}")
            raise

    @abstractmethod
    def get_token_data(self, token_id: str) -> Dict[str, Any]:
        pass

    def close(self):
        if self.session:
            self.session.close()
