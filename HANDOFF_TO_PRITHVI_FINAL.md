# 🏟️ PitchPulse — FINAL Backend Sync for Prithvi's Agent

**To the AI Agent assisting Prithvi (Flutter Frontend):**
We have executed a major architecture pivot on the PitchPulse Python backend. The previous instructions you received are now outdated and causing bugs in the Flutter UI. Please read the following instructions carefully and execute the necessary fixes in `PitchPulseUI`.

**Backend Base URL (ngrok):** `https://ferreous-semisaline-sean.ngrok-free.dev`
**All endpoints are prefixed with nothing** — the paths below are used directly after the base URL (e.g., `GET /workspaces/{id}/home`).

> **Note on "Connection closed before full header was received":** This is a transient ngrok blip (not a server crash). If this happens, simply retry the request. The server is running. If it happens repeatedly, ask Roshini to confirm the server is up.

---

## 🚨 1. REMOVE "Similar Cases" — Endpoint Deleted (All vector AI DB related features and files (RAG and so on) are deleted)

The `GET /players/{id}/similar_cases` endpoint has been **permanently removed** from the backend. Calling it will return a `404`.

**Action:**
- In `lib/providers/player_provider.dart`, delete the function that calls `/players/{id}/similar_cases`.
- Remove the "Similar Cases" UI section from `PlayerDetailScreen`.
- Remove any Dart model classes related to similar cases.

---

## 📸 2. Add Player Photos

The backend now returns `photo_url` for every player from API-Football.

**Example player JSON from `GET /workspaces/{id}/home` → `squad[]`:**
```json
{
  "player": {
    "id": "abc-123",
    "name": "Jude Bellingham",
    "position": "Midfielder",
    "jersey": 5,
    "photo_url": "https://media.api-sports.io/football/players/1100.png"
  },
  "readiness_score": 72.5,
  "risk_score": 27.5,
  "risk_band": "MED"
}
```

**Action:**
- Add `final String? photoUrl;` to your Player Dart model.
- Parse it from `json['photo_url']`.
- Use `Image.network(player.photoUrl!)` with a fallback (initials circle or icon) if `photoUrl` is null.
- Update every widget that shows a player avatar: `PlayerTile`, `PlayerDetailScreen` header, etc.

---

## 🩺 3. Presage Selfie Check-In — Full Specification

**Endpoint:** `POST /players/{player_id}/presage_checkin`

**Request body — what Prithvi's app MUST send:**
```json
{
  "vitals": {
    "face_detected": true,
    "pulse_rate": 60,
    "hrv_ms": 70,
    "breathing_rate": 14,
    "stress_level": "Normal",
    "focus": "High",
    "valence": "Positive",
    "confidence": 0.9
  }
}
```

### Scenario A: No Face Detected
If the Presage SDK or camera fails to detect a face, send:
```json
{ "vitals": { "face_detected": false } }
```
**Backend response:**
```json
{
  "readiness_delta": 0,
  "readiness_flag": "ALERT",
  "emotional_state": "No face detected",
  "contributing_factors": ["Scan failed to detect a human face."],
  "recommendation": "Please ensure you are in a well-lit area and retake the scan."
}
```
**UI Action:** Show a clear error card: "No Face Detected — Please retake the scan." Do NOT update the readiness gauge.

### Scenario B: Happy / Active (Positive Energy)
Send vitals with: `"valence": "Positive"`, `"focus": "High"`, `"stress_level": "Normal"`, low pulse/high HRV.
**Backend response example:**
```json
{
  "readiness_delta": 10,
  "readiness_flag": "OK",
  "emotional_state": "Active",
  "contributing_factors": ["High focus and positive valence detected. Optimal state."],
  "recommendation": "Player is clear for full training load. State is optimal."
}
```
**UI Action:** Show a GREEN result card. Display `emotional_state` ("Active" or "Happy"). Animate the readiness score going UP by the delta.

### Scenario C: Sad / Dull / Stressed (Negative Energy)
Send vitals with: `"valence": "Negative"`, `"focus": "Low"`, `"stress_level": "High"`, high pulse/low HRV.
**Backend response example:**
```json
{
  "readiness_delta": -10,
  "readiness_flag": "CAUTION",
  "emotional_state": "Dull",
  "contributing_factors": ["Low focus and negative valence detected. Reduced cognitive readiness."],
  "recommendation": "Consider reducing training intensity today to allow for mental and physical recovery."
}
```
**UI Action:** Show a RED or AMBER result card. Display `emotional_state` ("Sad", "Dull", or "Stressed"). Animate the readiness score going DOWN by the delta.

### Scenario D: Empty / Missing Vitals
If `vitals` is `{}` or missing entirely, the backend auto-fills healthy defaults and returns an **OK** result. No special handling needed.

### Key Implementation Notes:
- `readiness_delta` is an **integer**. Positive = readiness goes up. Negative = readiness goes down.
- `readiness_flag` is one of: `"OK"` (green), `"CAUTION"` (amber), `"ALERT"` (red).
- `emotional_state` is one of: `"Active"`, `"Happy"`, `"Calm"`, `"Sad"`, `"Dull"`, `"Stressed"`, `"No face detected"`.
- The backend **saves the delta to the database automatically**. After a check-in, `GET /players/{id}/detail` will return the updated score.

---

## 🏋️ 4. Movement Analysis — Risk Band Saved

**Endpoint:** `POST /players/{player_id}/movement_analysis` (multipart file upload)

No changes to the request format. But the backend now **persists the returned `mechanical_risk_band` to the database**. So after a movement analysis, calling `GET /players/{id}/detail` will reflect the updated risk band.

---

## 🛠️ 6. Fix Wrong Endpoint Paths in workspace_provider.dart

Three API paths in your `workspace_provider.dart` are **wrong**. Fix them immediately:

| Feature | ❌ Wrong path (current) | ✅ Correct path |
|---|---|---|
| Club Search | `GET /clubs/search?q=...` | **Does not exist as a separate endpoint.** See below. |
| Admin pending list | `GET /admin/workspaces/pending` | `GET /admin/requests` |
| Admin approve | `POST /admin/workspaces/{id}/approve` | `POST /admin/workspaces/{id}/approve` ✅ (this one is correct) |

### Club Search — How It Actually Works
There is **no `/clubs/search` endpoint**. The club search is handled on the Flutter side only. Your existing `demoResults()` fallback is the correct approach. Remove the `await _api.get('/clubs/search?...')` call and instead just filter `ClubSearchResult.demoResults()` directly without making any network call. The user selects a club, and when they tap Join, you call `POST /workspaces/request_access` with `{"provider_team_id": <int>}`.

**Fix in `workspace_provider.dart`, `searchClubs()` method:**
```dart
Future<List<ClubSearchResult>> searchClubs(String query) async {
  // No backend endpoint — filter local demo results
  await Future.delayed(const Duration(milliseconds: 300));
  return ClubSearchResult.demoResults()
      .where((c) => c.name.toLowerCase().contains(query.toLowerCase()))
      .toList();
}
```

### Admin Requests — Fix the path:
```dart
// ❌ Change this:
final data = await _api.get('/admin/workspaces/pending') as List<dynamic>;
// ✅ To this:
final data = await _api.get('/admin/requests') as List<dynamic>;
```


**Endpoint:** `POST /players/{player_id}/action_plan`

This still works the same way — no request body needed. The backend now uses pure Gemini AI (no Vector DB / RAG). The response JSON structure is unchanged:
```json
{
  "summary": "...",
  "why": ["...", "..."],
  "recommendations": ["...", "..."],
  "caution": "..."
}
```

---

## � 6. Complete Endpoint Reference

| Screen / Feature | Method | Path | Notes |
|---|---|---|---|
| Login / Auth | GET | `/me` | Returns current user + workspaces |
| Club Search | local only | n/a | Filter `demoResults()` — no backend call needed |
| Request Workspace | POST | `/workspaces/request_access` | Body: `{"provider_team_id": 541}` |
| Home Screen | GET | `/workspaces/{id}/home` | Squad, fixtures, scores |
| Suggested XI | POST | `/workspaces/{id}/suggested-xi` | Body: `{"opponent": "...", "match_context": "..."}` |
| Player Detail | GET | `/players/{id}/detail?weeks=6` | Current status + weekly history |
| Player Why | GET | `/players/{id}/why` | Risk drivers |
| Action Plan | POST | `/players/{id}/action_plan` | AI-generated plan, no body needed |
| Selfie Check-In | POST | `/players/{id}/presage_checkin` | Body: `{"vitals": {...}}` |
| Movement Video | POST | `/players/{id}/movement_analysis` | Multipart file upload |
| Fixture Detail | GET | `/fixtures/{id}/detail` | Match stats |
| Sync (manual) | POST | `/sync/workspace/{id}/initial` | Re-syncs squad + fixtures |
| Admin list | GET | `/admin/requests` | ⚠️ NOT `/admin/workspaces/pending` |
| Admin approve | POST | `/admin/workspaces/{id}/approve` | ✅ This path is correct |
| ~~Similar Cases~~ | ~~GET~~ | ~~`/players/{id}/similar_cases`~~ | **DELETED — DO NOT CALL** |


---

## ⚠️ Summary of Required Code Changes

1. **Delete** all `similar_cases` code (provider method, UI section, model).
2. **Add** `photo_url` parsing to Player model and display images.
3. **Implement** full presage check-in result handling: "No face detected" error state, green/red cards based on `readiness_flag`, display `emotional_state` text.
4. **Ensure** the presage request body includes `face_detected` boolean.
5. **Fix `searchClubs()`** — remove the `GET /clubs/search` network call, filter `demoResults()` locally instead.
6. **Fix admin pending path** — change `GET /admin/workspaces/pending` → `GET /admin/requests`.
7. **No other endpoint URLs have changed.** All other calls to `/workspaces/...`, `/players/.../detail`, `/players/.../action_plan`, etc. remain the same.

