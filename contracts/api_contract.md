# PitchPulse API Contract

## Core Structures

### Workspace
```json
{
  "id": "uuid",
  "provider_team_id": 123,
  "team_name": "Real Madrid",
  "status": "approved",
  "created_at": "2023-10-27T10:00:00Z"
}
```

### Player
```json
{
  "id": "uuid",
  "name": "Jude Bellingham",
  "position": "Midfielder",
  "jersey": 5
}
```

### Fixture
```json
{
  "id": "uuid",
  "provider_fixture_id": 456,
  "kickoff": "2023-10-28T14:00:00Z",
  "opponent_name": "Barcelona",
  "home_away": "away",
  "status": "FT",
  "score_home": 1,
  "score_away": 2
}
```

## Public Routes (Requires Bearer Token)

### `GET /me`
Returns current user profile and workspaces.
**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "coach@madrid.com",
    "role": "manager"
  },
  "workspaces": [ /* Workspace objects */ ]
}
```

### `GET /clubs/search?q={query}`
**Response:**
```json
{
  "teams": [
    {
      "provider_team_id": 123,
      "name": "Real Madrid",
      "logo_url": "https://..."
    }
  ]
}
```

### `POST /workspaces/request_access`
**Body:** `{"provider_team_id": 123}`
**Response:** Workspace object (status: "pending")

### `GET /workspaces/{id}/home`
**Response:**
```json
{
  "workspace": { /* Workspace object */ },
  "next_fixture": { /* Fixture object OR null */ },
  "recent_fixtures": [ /* Array of Fixtures */ ],
  "squad": [
    {
      "player": { /* Player Object */ },
      "readiness_score": 85,
      "risk_score": 20,
      "risk_band": "LOW",
      "top_drivers": ["Optimal ACWR", "Normal match load"]
    }
  ]
}
```

### `GET /players/{id}/detail?weeks=6`
**Response:**
```json
{
  "player": { /* Player object */ },
  "current_status": {
      "readiness_score": 85,
      "risk_score": 20,
      "risk_band": "LOW",
      "acute_load": 400,
      "chronic_load": 350,
      "acwr": 1.14
  },
  "weekly_history": [
    {
      "week_start": "2023-10-20T00:00:00Z",
      "risk_score": 15,
      "readiness_score": 90,
      "acute_load": 300,
      "acwr": 0.95
    }
  ]
}
```

### `GET /players/{id}/why`
**Response:**
```json
{
  "drivers": [
    {"factor": "Acute Load Spike", "value": "600", "threshold": "500", "impact": "negative"},
    {"factor": "Days Since Match", "value": "2", "threshold": "3", "impact": "negative"}
  ]
}
```

### `GET /players/{id}/similar_cases?k=5`
**Response:**
```json
{
  "cases": [
    {
       "player_name": "Vinicius Jr",
       "week_date": "2023-09-15T00:00:00Z",
       "similarity_score": 0.92,
       "context": "High ACWR (1.6) combined with 3 matches in 7 days.",
       "action_taken": "Rested for 1 match, load reduced by 30%."
    }
  ]
}
```

### `POST /players/{id}/action_plan`
Calls Gemini with similar cases + playbook docs.
**Response (Strict JSON from Keerthi's Prompt):**
```json
{
  "summary": "Player is at high risk due to acute load spike.",
  "why": [
    "ACWR is 1.6 (Dangerous Zone)",
    "Played 270 minutes in 7 days"
  ],
  "recommendations": [
    "Rest for the upcoming cup fixture.",
    "Limit training to recovery protocols only."
  ],
  "caution": "Do not clear for high-speed running drills until day 4."
}
```

### `POST /players/{id}/movement_analysis`
Accepts a video upload (`multipart/form-data` with `video` field).
**Response (Strict JSON from Keerthi's Prompt):**
```json
{
  "mechanical_risk_band": "MED",
  "flags": ["Slight knee valgus on descent"],
  "coaching_cues": ["Drive knees out over toes"],
  "confidence": 0.85
}
```

## Internal / Sync Routes (Can use `?use_demo=true`)

### `POST /sync/workspace/{id}/initial`
**Response:** `{"status": "success", "players_synced": 25, "fixtures_synced": 5}`

### `POST /sync/fixtures/poll_once`
**Response:** `{"status": "success", "fixtures_processed": 1, "stats_ingested": 14}`
