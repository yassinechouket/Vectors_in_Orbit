# 🔧 Backend Errors - Diagnosis & Fixes

## Current Issues

You're seeing two errors:

### 1. POST /tracking/search - 422 Unprocessable Content
**Cause**: The frontend is sending search tracking events but missing required fields.

**Missing Fields**:
- `results_count` (required)
- `session_id` (required)

**Fix**: The frontend needs to send a proper `SearchEvent` with all required fields.

### 2. POST /search - 500 Internal Server Error
**Cause**: This is the critical error. The `/search` endpoint is calling the recommendation pipeline, which is likely failing.

**Possible Reasons**:
1. Product IDs are integers in database but expected as strings
2. Async method being called incorrectly
3. Missing session_context handling
4. Response formatting issue

## 🔍 How to See the Full Error

To see the exact error, check your backend terminal where you ran `python main.py`. You should see the full stack trace there.

Alternatively, run this:

```bash
# Get last 50 lines of erro from terminal
cd backend
python -c "import requests; r = requests.post('http://localhost:8000/search', json={'query': 'laptop'}, timeout=30); print(r.text)"
```

## 🛠️ Quick Fixes

### Fix 1: Check Backend Logs

Look at your backend terminal for the full error message. It will show something like:

```
Traceback (most recent call last):
  File "...", line X, in get_recommendations
    ...
AttributeError: 'int' object has no attribute '...'
```

### Fix 2: Test with Simpler Endpoint

Try the health endpoint first:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

If this works, the issue is specifically in the recommendation pipeline.

### Fix 3: Test Qdrant Directly

```bash
cd backend
python -c "from services.qdrant.client import QdrantManager; qm = QdrantManager(); info = qm.get_collection_info(); print(info)"
```

This will verify Qdrant has the data.

## 📝 What I Need from You

Please share:

1. **Full error from backend terminal** - The complete stack trace
2. **Frontend request** - What exactly is the frontend sending to `/search`?
3. **Health check result** - Does `GET /health` work?

Once I see the exact error, I can provide the precise fix!

## 🎯 Temporary Workaround

While we debug, you can test the API directly with curl:

```bash
# PowerShell
$body = @{
    query = "laptop"
    user_id = "test"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:8000/recommend" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

If this works, the issue is in how the frontend is calling the API.

## 🔄 Restart Backend

Sometimes errors get cached. Try restarting:

1. Stop the backend (Ctrl+C)
2. Restart: `python main.py`
3. Try again

