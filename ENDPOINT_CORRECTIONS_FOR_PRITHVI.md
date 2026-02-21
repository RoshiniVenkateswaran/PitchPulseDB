# 🏟️ PitchPulse Backend — Endpoint Correction Guide for Prithvi's Agent

**Author:** Roshini (Backend)  
**Date:** Feb 21, 2026  
**Purpose:** Prithvi's Flutter app is calling some endpoints that do not exist or have incorrect paths. This document lists every endpoint the Flutter code currently calls, flags the incorrect ones, and provides the correct replacement.

---

## 🔧 Step 0: Update the Base URL First

In `lib/core/constants.dart`, the `defaultValue` is hardcoded to `localhost`. Change it to the live ngrok URL:

```dart
// ❌ CURRENT (will only work on Roshini's machine):
static const String baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'http://localhost:8000',
);

// ✅ CORRECT (use ngrok public URL):
static const String baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'https://ferreous-semisaline-sean.ngrok-free.dev',
);
```

**Note:** The ngrok URL changes every time the server restarts. Roshini will share the updated URL each session.

---

## ✅ Correct Endpoints (No Changes Needed)

These are already using the correct paths — leave them alone!

| Flutter Code (provider) | Method | Endpoint | Status |
|---|---|---|---|
| `auth_provider.dart:40` | GET | `/me` | ✅ Correct |
| `workspace_provider.dart:50` | GET | `/clubs/search?q={query}` | ✅ Correct |
| `workspace_provider.dart:67` | POST | `/workspaces/request_access` | ✅ Correct |
| `workspace_provider.dart:95` | GET | `/me` | ✅ Correct |
| `workspace_provider.dart:130` | GET | `/workspaces/{id}/home` | ✅ Correct |
| `workspace_provider.dart:183` | POST | `/workspaces/{id}/suggested-xi` | ✅ Correct |
| `workspace_provider.dart:198` | GET | `/admin/workspaces/pending` | ✅ Correct |
| `workspace_provider.dart:231` | POST | `/admin/workspaces/{id}/approve` | ✅ Correct |
| `workspace_provider.dart:242` | POST | `/sync/fixtures/poll_once` | ✅ Correct |
| `player_provider.dart:51` | GET | `/players/{id}/detail?weeks=6` | ✅ Correct |
| `player_provider.dart:78` | GET | `/players/{id}/similar_cases?k=5` | ✅ Correct |
| `player_provider.dart:109` | POST | `/players/{id}/action_plan` | ✅ Correct |
| `api_client.dart:86` | POST | `/sync/workspace/{id}/initial?use_demo=true` | ✅ Correct |

---

## ❌ Broken Endpoints — MUST FIX

### Fix 1: Selfie Check-In (Vitals)

**File:** `lib/views/check_in/player_check_in_screen.dart` — Line 178

```dart
// ❌ CURRENT (404 Not Found — this endpoint does not exist):
Uri.parse('$baseUrl/players/${widget.player.id}/checkin/selfie');

// ✅ CORRECT:
Uri.parse('$baseUrl/players/${widget.player.id}/presage_checkin');
```

**Also note:** The current code sends the video as a `multipart/form-data` upload, but the `presage_checkin` endpoint accepts a **JSON body** with `{ "vitals": { ... } }`, not a video file. Here's how to call it:

```dart
// Instead of MultipartRequest, use a normal POST with JSON body:
final response = await http.post(
  Uri.parse('$baseUrl/players/${widget.player.id}/presage_checkin'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    "vitals": {
      "pulse_rate": 74,         // optional, from Presage SDK
      "hrv_ms": 42,             // optional
      "breathing_rate": 18,     // optional
      "stress_level": "High",   // optional: "Low" / "Normal" / "High"
      "focus": "Low",           // optional: "Low" / "Normal" / "High"
      "valence": "Negative",    // optional: "Positive" / "Neutral" / "Negative"
      "confidence": 0.88        // optional
    }
  }),
);
```

**Response shape (unchanged — Prithvi's UI code is already correct):**
```json
{
  "readiness_delta": -15,
  "readiness_flag": "ALERT",
  "emotional_state": "Stressed",
  "contributing_factors": ["Resting HR elevated +20bpm above baseline."],
  "recommendation": "Reduce training load."
}
```

---

### Fix 2: Movement Analysis (Biomechanics)

**File:** `lib/views/check_in/player_check_in_screen.dart` — Line 272

```dart
// ❌ CURRENT (404 Not Found — this endpoint does not exist):
Uri.parse('$baseUrl/players/${widget.player.id}/checkin/movement');

// ✅ CORRECT:
Uri.parse('$baseUrl/players/${widget.player.id}/movement_analysis');
```

**Good news:** The method of sending the video as `multipart/form-data` with the field named `video` is **correct!** Just fix the URL path.

**Response shape (Prithvi's UI code is already correct):**
```json
{
  "mechanical_risk_band": "MED",
  "flags": ["Slight knee valgus on descent"],
  "coaching_cues": ["Drive knees out over toes"],
  "confidence": 0.85
}
```

---

### Fix 3: Workspace Reports (Non-Existent Endpoint)

**File:** `lib/providers/workspace_provider.dart` — Line 166

```dart
// ❌ CURRENT (404 Not Found — this endpoint does not exist in the backend):
await _api.get('/workspaces/$workspaceId/reports');
```

**There is no `/reports` endpoint.** The closest equivalent data comes from the home endpoint.

**✅ OPTION A (Quick Fix):** Remove this call entirely and pull match report data from the home endpoint instead.

**✅ OPTION B (Full Fix):** Replace with the fixture detail endpoint to get match reports per fixture:
```dart
await _api.get('/fixtures/{fixture_id}/detail');
```

---

## 📦 Complete Correct Endpoint Reference

| Screen | Method | Correct URL |
|---|---|---|
| Login | GET | `/me` |
| Search Club | GET | `/clubs/search?q={query}` |
| Request Workspace | POST | `/workspaces/request_access` |
| Home Dashboard | GET | `/workspaces/{id}/home` |
| Player Detail | GET | `/players/{id}/detail?weeks=6` |
| Why is this score? | GET | `/players/{id}/why` |
| Similar Cases (RAG) | GET | `/players/{id}/similar_cases?k=5` |
| Action Plan (AI) | POST | `/players/{id}/action_plan` |
| Vitals Check-In ⚠️ | POST | `/players/{id}/presage_checkin` (JSON body, no video) |
| Movement Analysis ⚠️ | POST | `/players/{id}/movement_analysis` (multipart/form-data with `video` field) |
| Suggested XI (AI) | POST | `/workspaces/{id}/suggested-xi` |
| Admin: Pending | GET | `/admin/workspaces/pending` |
| Admin: Approve | POST | `/admin/workspaces/{id}/approve` |
| Initial Sync | POST | `/sync/workspace/{id}/initial?use_demo=true` |
| Poll FT Matches | POST | `/sync/fixtures/poll_once` |
