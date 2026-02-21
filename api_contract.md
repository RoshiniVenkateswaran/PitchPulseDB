# PitchPulse API Contract (Unified)

*Version:* 2.0 (Merged — Roshini's Backend + Keerthi's AI Endpoints)  
*Purpose:* Single source of truth for JSON shapes across Flutter (Prithvi), FastAPI (Roshini), and AI Layer (Keerthi).

---

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

---

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
**Response:** Workspace object (status: `"pending"`)

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

---

## AI Feature Endpoints

### `GET /players/{id}/similar_cases?k=5`
Retrieves similar historical player-weeks from Actian VectorAI DB.  
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
Calls Gemini with similar cases + playbook docs via RAG.  
**Response (Strict JSON from AI Layer):**
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
**Response (Strict JSON from AI Layer):**
```json
{
  "mechanical_risk_band": "MED",
  "flags": ["Slight knee valgus on descent"],
  "coaching_cues": ["Drive knees out over toes"],
  "confidence": 0.85
}
```

### `POST /players/{id}/presage_checkin`
Submits selfie-captured vitals (physical + emotional) for readiness adjustment.  
**Request Body:**
```json
{
  "vitals": {
    "pulse_rate": 74,
    "hrv_ms": 42,
    "breathing_rate": 18,
    "stress_level": "High",
    "focus": "Low",
    "valence": "Negative",
    "confidence": 0.88
  }
}
```
**Response (Strict JSON from AI Layer):**
```json
{
  "readiness_delta": -15,
  "readiness_flag": "ALERT",
  "emotional_state": "Stressed",
  "contributing_factors": [
    "Resting HR elevated +20bpm above baseline.",
    "HRV suppressed at 52% of baseline.",
    "High psychological stress detected in facial scan."
  ],
  "recommendation": "Reduce training load and prioritize mental recovery."
}
```

### `POST /workspaces/{id}/suggested-xi`
Generates an AI-recommended tactical formation and Starting XI.  
**Request Body:**
```json
{
  "opponent": "Bayern Munich",
  "match_context": "Away, Champions League Semi-Final",
  "available_squad": [
    {"id": "uuid", "name": "Vinícius Jr", "position": "FW", "readiness": 95, "form": "Excellent"},
    {"id": "uuid", "name": "Bellingham", "position": "MID", "readiness": 88, "form": "Good"}
  ]
}
```
**Response (Strict JSON from AI Layer):**
```json
{
  "best_formation": "4-3-3",
  "tactical_analysis": "4-3-3 selected to stretch Bayern's high line with pace on both flanks.",
  "starting_xi_ids": ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11"],
  "bench_ids": ["p12", "p13", "p14", "p15"],
  "player_rationales": {
    "p1": "Vini is highly recommended to start. At 95% readiness with low ACWR."
  }
}
```

---

## Internal / Sync Routes (Can use `?use_demo=true`)

### `POST /sync/workspace/{id}/initial`
**Response:** `{"status": "success", "players_synced": 25, "fixtures_synced": 5}`

### `POST /sync/fixtures/poll_once`
**Response:** `{"status": "success", "fixtures_processed": 1, "stats_ingested": 14}`
