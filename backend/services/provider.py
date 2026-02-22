from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json
import os
import logging

logger = logging.getLogger(__name__)

# Map of position codes from API-Football to readable strings
POSITION_MAP = {
    "G": "Goalkeeper",
    "D": "Defender",
    "M": "Midfielder",
    "F": "Forward",
    "A": "Forward",  # Attacker alias
}


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

    @abstractmethod
    def get_player_season_stats(self, player_id: int, season: int = 2024) -> Dict[str, Any]:
        pass


class LiveFootballProvider(ProviderAdapter):
    """
    Live provider that calls the API-Football v3 API.
    Uses PROVIDER_API_KEY from settings.
    """
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-apisports-key": api_key,
        }

    def _get(self, endpoint: str, params: dict = None) -> dict:
        import requests
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API-Football request failed [{endpoint}]: {e}")
            return {}

    def search_clubs(self, query: str) -> List[Dict[str, Any]]:
        data = self._get("teams", {"search": query})
        results = []
        for item in data.get("response", []):
            team = item.get("team", {})
            results.append({
                "provider_team_id": team.get("id"),
                "name": team.get("name"),
                "logo_url": team.get("logo"),
                "country": item.get("venue", {}).get("country"),
                "founded": team.get("founded"),
            })
        return results

    def get_squad(self, team_id: int) -> List[Dict[str, Any]]:
        data = self._get("players/squads", {"team": team_id})
        players = []
        for item in data.get("response", []):
            for p in item.get("players", []):
                # API-Football returns full position strings like "Goalkeeper", "Defender", etc.
                position = p.get("position") or p.get("pos") or "Unknown"
                players.append({
                    "provider_player_id": p.get("id"),
                    "name": p.get("name"),
                    "position": position,
                    "jersey": p.get("number"),
                    "photo_url": p.get("photo"),
                })
        logger.info(f"Fetched {len(players)} players for team {team_id} from API-Football")
        return players


    def get_fixtures(self, team_id: int, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        data = self._get("fixtures", {
            "team": team_id,
            "from": from_date,
            "to": to_date,
        })
        fixtures = []
        for item in data.get("response", []):
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})
            is_home = str(home_team.get("id")) == str(team_id)
            opponent = away_team.get("name") if is_home else home_team.get("name")
            fixtures.append({
                "provider_fixture_id": fixture.get("id"),
                "kickoff": fixture.get("date"),
                "opponent_name": opponent,
                "home_away": "home" if is_home else "away",
                "status": fixture.get("status", {}).get("short", "NS"),
                "score_home": goals.get("home"),
                "score_away": goals.get("away"),
            })
        return fixtures

    def get_fixture_player_stats(self, fixture_id: int) -> List[Dict[str, Any]]:
        data = self._get("fixtures/players", {"fixture": fixture_id})
        result = []
        for team_data in data.get("response", []):
            for p in team_data.get("players", []):
                player = p.get("player", {})
                stats_list = p.get("statistics", [{}])
                stats = stats_list[0] if stats_list else {}
                games = stats.get("games", {})
                minutes = games.get("minutes") or 0
                result.append({
                    "provider_player_id": player.get("id"),
                    "minutes": minutes,
                    "stats_json": {
                        "rating": games.get("rating"),
                        "goals": stats.get("goals", {}).get("total") or 0,
                        "assists": stats.get("goals", {}).get("assists") or 0,
                        "passes": stats.get("passes", {}).get("total") or 0,
                    }
                })
        return result

    def get_player_season_stats(self, player_id: int, season: int = 2024) -> Dict[str, Any]:
        """Fetch a player's season statistics from API-Football."""
        data = self._get("players", {"id": player_id, "season": season})
        stats_out = {
            "total_minutes": 0, "appearances": 0,
            "avg_rating": None, "goals": 0, "assists": 0
        }
        try:
            resp = data.get("response", [])
            if not resp:
                return stats_out
            stats_list = resp[0].get("statistics", [])
            if not stats_list:
                return stats_out
            # Aggregate across all competition entries
            total_rating = 0.0
            rating_count = 0
            for s in stats_list:
                games = s.get("games", {})
                goals_data = s.get("goals", {})
                apps = games.get("appearences") or 0  # API-Football typo is intentional
                mins = games.get("minutes") or 0
                rating_str = games.get("rating")
                stats_out["appearances"] += apps
                stats_out["total_minutes"] += mins
                stats_out["goals"] += goals_data.get("total") or 0
                stats_out["assists"] += goals_data.get("assists") or 0
                if rating_str:
                    try:
                        total_rating += float(rating_str)
                        rating_count += 1
                    except (ValueError, TypeError):
                        pass
            if rating_count > 0:
                stats_out["avg_rating"] = round(total_rating / rating_count, 2)
        except Exception as e:
            logger.warning(f"Failed to parse season stats for player {player_id}: {e}")
        return stats_out


class MockFootballProvider(ProviderAdapter):
    """
    Fallback mock provider that reads from local JSON files in backend/demo_data/
    Used when no PROVIDER_API_KEY is set.
    """
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data")

    def _load_json(self, filename: str) -> Any:
        try:
            with open(os.path.join(self.data_dir, filename), "r") as f:
                return json.load(f)
        except Exception:
            return []

    def search_clubs(self, query: str) -> List[Dict[str, Any]]:
        return [
            {
                "provider_team_id": 541,
                "name": "Real Madrid",
                "logo_url": "https://media.api-sports.io/football/teams/541.png",
                "country": "Spain",
                "founded": 1902,
            }
        ]

    def get_squad(self, team_id: int) -> List[Dict[str, Any]]:
        return self._load_json("squad.json")

    def get_fixtures(self, team_id: int, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        return self._load_json("fixtures.json")

    def get_fixture_player_stats(self, fixture_id: int) -> List[Dict[str, Any]]:
        return self._load_json(f"stats_{fixture_id}.json")

    def get_player_season_stats(self, player_id: int, season: int = 2024) -> Dict[str, Any]:
        """Mock: return varied stats based on player_id for demo variety."""
        import random
        rng = random.Random(player_id)  # deterministic per player
        apps = rng.randint(5, 38)
        mins = apps * rng.randint(55, 90)
        rating = round(rng.uniform(6.2, 8.0), 2)
        goals = rng.randint(0, 15)
        assists = rng.randint(0, 10)
        return {
            "total_minutes": mins,
            "appearances": apps,
            "avg_rating": rating,
            "goals": goals,
            "assists": assists,
        }


def _build_provider() -> ProviderAdapter:
    """Return the live API-Football provider if key is available, else fall back to mock."""
    try:
        from backend.core.config import settings
        if settings.PROVIDER_API_KEY and settings.PROVIDER_API_KEY not in ("demo-key", ""):
            logger.info("Using Live API-Football provider")
            return LiveFootballProvider(api_key=settings.PROVIDER_API_KEY)
    except Exception as e:
        logger.warning(f"Could not load settings for provider: {e}")
    logger.info("Using MockFootballProvider (no live API key)")
    return MockFootballProvider()


# Singleton — used by all endpoints
provider = _build_provider()
