# 🏟️ PitchPulse — Flutter Integration Guide for Prithvi

**From:** Roshini (Backend)  
**Date:** Feb 21, 2026  
**Status:** ✅ Backend Live on ngrok

---

## Step 1: Set Your Base URL

In `lib/core/constants.dart`, change the `defaultValue` to the live ngrok URL:

```dart
static const String baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'https://ferreous-semisaline-sean.ngrok-free.dev', // ← USE THIS
);
```

> **⚠️ Important:** This URL changes every time Roshini restarts her server. She'll message the new URL when that happens.

---

## Step 2: How Club Selection Works (Auto-Approval)

**Nothing needs to change here — it already works.** Here's the full flow:

1. Manager opens app → hits `ClubSelectScreen`
2. Types a club name → calls `GET /clubs/search?q={query}` → returns matching clubs
3. Manager picks a club and taps "Request Access" → calls `POST /workspaces/request_access`
4. Backend **instantly** creates an approved workspace and syncs the squad + fixtures in the background
5. `GET /me` returns the workspace with `"status": "approved"` — no waiting, no admin

**There is no admin approval step anymore.**

---

## Step 3: Fix These 3 Broken Endpoints (Critical)

### Fix 1 — Vitals Check-In (Selfie)
**File:** `lib/views/check_in/player_check_in_screen.dart` line 178

```dart
// ❌ WRONG — this URL doesn't exist:
Uri.parse('$baseUrl/players/${widget.player.id}/checkin/selfie');

// ✅ CORRECT URL:
Uri.parse('$baseUrl/players/${widget.player.id}/presage_checkin');
```

**Also fix the request type** — this endpoint takes a **JSON body**, NOT a multipart video upload:

```dart
// Replace the MultipartRequest with a simple POST:
final response = await http.post(
  Uri.parse('$baseUrl/players/${widget.player.id}/presage_checkin'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    "vitals": {
      "stress_level": "High",    // from Presage SDK
      "focus": "Low",            // from Presage SDK
      "valence": "Negative",     // from Presage SDK
      "pulse_rate": 74,          // optional
      "hrv_ms": 42,              // optional
    }
  }),
);
```

**Response (your UI code is already correct for this):**
```json
{
  "readiness_delta": -15,
  "readiness_flag": "ALERT",
  "emotional_state": "Stressed",
  "contributing_factors": ["Resting HR elevated..."],
  "recommendation": "Reduce training load."
}
```

---

### Fix 2 — Movement Analysis
**File:** `lib/views/check_in/player_check_in_screen.dart` line 272

```dart
// ❌ WRONG:
Uri.parse('$baseUrl/players/${widget.player.id}/checkin/movement');

// ✅ CORRECT:
Uri.parse('$baseUrl/players/${widget.player.id}/movement_analysis');
```

The multipart video upload (field name `video`) is correct — **only the URL path needs to change.**

---

### Fix 3 — Workspace Reports
**File:** `lib/providers/workspace_provider.dart` line 166

```dart
// ❌ WRONG — this endpoint does not exist:
await _api.get('/workspaces/$workspaceId/reports');
```

**Remove this call** or replace it with the home endpoint which returns recent fixtures:
```dart
// ✅ Use home endpoint instead — it returns recent_fixtures:
await _api.get('/workspaces/$workspaceId/home');
```

---

## Step 4: Complete Correct Endpoint Reference

| Screen / Feature | Method | URL |
|---|---|---|
| Login / Profile | `GET` | `/me` |
| Find a Club | `GET` | `/clubs/search?q={query}` |
| Select Club (creates workspace + syncs squad) | `POST` | `/workspaces/request_access` — body: `{"provider_team_id": 541}` |
| Home Dashboard | `GET` | `/workspaces/{id}/home` |
| Player Detail | `GET` | `/players/{id}/detail?weeks=6` |
| Why this score? | `GET` | `/players/{id}/why` |
| Similar Cases (RAG) | `GET` | `/players/{id}/similar_cases?k=5` |
| AI Action Plan | `POST` | `/players/{id}/action_plan` |
| Vitals Check-In ⚠️ | `POST` | `/players/{id}/presage_checkin` — JSON body with `{ "vitals": {...} }` |
| Movement Analysis ⚠️ | `POST` | `/players/{id}/movement_analysis` — multipart with `video` field |
| Suggested XI (AI) | `POST` | `/workspaces/{id}/suggested-xi` |
| Trigger FT Match Poll | `POST` | `/sync/fixtures/poll_once` |
| Manual Squad Re-Sync | `POST` | `/sync/workspace/{id}/initial?use_demo=true` |
| Admin: Pending Requests | `GET` | `/admin/workspaces/pending` |
| Admin: Approve | `POST` | `/admin/workspaces/{id}/approve` |

---

## Step 5: Authentication

Every request **must** include a Firebase ID token in the header:

```dart
'Authorization': 'Bearer <firebaseUser.getIdToken()>'
```

Your `ApiClient` already does this — **no changes needed here**.

For testing without a Firebase account, the backend accepts the test token:
```
Authorization: Bearer test-token-admin
```

---

## Step 6: First-Run Flow (What to call and when)

```
User signs up via Firebase
    ↓
GET /me               → check if user has a workspace
    ↓ (no workspace)
GET /clubs/search     → show club picker UI
    ↓
POST /workspaces/request_access  → workspace created + squad/fixtures synced automatically
    ↓
GET /me               → workspace now shows status: "approved"
    ↓
GET /workspaces/{id}/home   → show home screen with squad readiness tiles
```

---

## Step 7: Demo IDs (for hardcoded testing)

| What | Value |
|---|---|
| Demo Workspace ID | `test-workspace-1` |
| Demo Club | Real Madrid (`provider_team_id: 541`) |
| Demo Fixture ID | `demo-fixture-001` |

---

## Swagger Docs (Test All Endpoints Interactively)

**`https://ferreous-semisaline-sean.ngrok-free.dev/docs`**

Open this in a browser and hit any endpoint directly with the Swagger UI.
