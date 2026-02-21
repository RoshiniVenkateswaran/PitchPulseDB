# Handoff to Prithvi (Flutter Frontend integration)

Hey Prithvi, here is the exact status of the Backend and exactly how you can start hitting my endpoints.

## 1. My Status: 100% Complete 🚀
* **Database (Supabase):** The backend is live and storing all real player stats, ACWR scores, and fixtures in a cloud PostgreSQL database.
* **Authentication (Firebase):** I successfully linked my backend to your Firebase `serviceAccountKey.json`. 
* **AI Engine:** Keerthi’s Gemini Action Plans, RAG Playbook, and Video Movement Analysis are completely wired to my API endpoints.

## 2. API Contract & Swagger
You have everything you need to start building the UI screens.
* **The Blueprint:** Please check the [api_contract.md](contracts/api_contract.md) file in my repo. It has every single Endpoint URL and the exact JSON payload you will receive (e.g., `GET /players/{id}/detail`).
* **Swagger UI:** I have started the server on my laptop. To view the interactive documentation, go to: `http://localhost:8000/docs`.

## 3. How You Connect to Me
Since we are at a Hackathon, you are going to connect your Flutter app directly to my Macbook's IP Address!

### Step 1: The Base URL
Change the base URL in your Flutter HTTP client to my IP address:
```dart
// Example: Ask me for my laptop IP address (e.g., 192.168.1.55)
const String BASE_URL = "http://[MY_LAPTOP_IP]:8000"; 
```

### Step 2: The Auth Token
For **every single API request** you make to my backend, you *must* pass the Firebase ID token in the Header so I know who is logged in. 
```dart
final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();

final response = await http.get(
  Uri.parse("$BASE_URL/players/123/detail"),
  headers: {
    "Authorization": "Bearer $idToken",
    "Content-Type": "application/json",
  },
);
```
*(Hackathon Shortcut: If your Firebase login screen is broken, you can literally just pass `"Bearer test-token-admin"` and my backend will let you through safely so you aren't blocked!)*

### Step 3: Trigger the First Sync!
Once you successfully hit my server, the very first thing you need to do is trigger the initial data sync. Hit this endpoint to fill the database with the Real Madrid squad:
* **`POST /sync/workspace/test-workspace-1/initial?use_demo=true`**

Once that returns `status: success`, your app will be loaded with full ACWR charts, risk flags, and Gemini Action Plans. Let's build this!
