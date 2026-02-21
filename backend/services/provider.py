from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os

class ProviderAdapter(ABC):
    @abstractmethod
    def search_clubs(self, query: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_squad(self, team_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fixtures(self, team_id: int, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fixture_player_stats(self, fixture_id: int) -> List[Dict[str, Any]]:
        pass

class MockFootballProvider(ProviderAdapter):
    """
    Mock provider that reads from local JSON files in backend/demo_data/
    """
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data")

    def _load_json(self, filename: str) -> Any:
        try:
            with open(os.path.join(self.data_dir, filename), "r") as f:
                return json.load(f)
        except Exception as e:
            return []

    def search_clubs(self, query: str) -> List[Dict[str, Any]]:
        # For hackathon, just return Real Madrid if queried
        return [
            {
                "provider_team_id": 541,
                "name": "Real Madrid",
                "logo_url": "https://media.api-sports.io/football/teams/541.png"
            }
        ]

    def get_squad(self, team_id: int) -> List[Dict[str, Any]]:
        return self._load_json("squad.json")

    def get_fixtures(self, team_id: int, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        return self._load_json("fixtures.json")

    def get_fixture_player_stats(self, fixture_id: int) -> List[Dict[str, Any]]:
        return self._load_json(f"stats_{fixture_id}.json")

# In a real app we'd load this via dependency injection based on config
provider = MockFootballProvider()
