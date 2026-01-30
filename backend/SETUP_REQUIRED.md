# 🔧 Backend Setup Required

## ❌ Current Issue

The backend cannot start because it's missing the **DeepSeek API key**.

Error:
```
ProviderError: DEEPSEEK_API_KEY environment variable not set
```

## ✅ Solution

You need to create a `.env` file in the `backend` folder with your DeepSeek API key.

### Step 1: Get DeepSeek API Key

1. Visit: https://platform.deepseek.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### Step 2: Create `.env` File

Create a file `backend/.env` with this content:

```env
# DeepSeek API Key (required)
DEEPSEEK_API_KEY=sk-your-actual-api-key-here

# Qdrant Configuration (already running)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

**Replace `sk-your-actual-api-key-here` with your real API key!**

### Step 3: Start the Backend

```bash
cd backend
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 📋 Quick Commands

**Create .env file (PowerShell):**
```powershell
cd backend
@"
DEEPSEEK_API_KEY=sk-your-actual-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
"@ | Out-File -FilePath .env -Encoding UTF8
```

**Then edit the file to add your real API key!**

---

## 🎯 What's Already Working

✅ Qdrant vector database is running  
✅ Database populated with 234 products  
✅ All product embeddings generated  
✅ Frontend files ready  

❌ Backend needs API key to start  

---

## 🔄 After Setup

Once you add the API key and start the backend:

1. **Test it works:**
   ```bash
   python test_recommendation.py
   ```

2. **Try the web app:**
   - Open the webapp at http://localhost:3000
   - Or use the Chrome extension

3. **Test a query:**
   ```bash
   python test_api.py
   ```

---

## 💰 Cost Info

DeepSeek is very affordable:
- Input: $0.14 per 1M tokens
- Output: $0.28 per 1M tokens

For testing, you'll spend less than $0.01 per query.

---

## 🔐 Security Note

**NEVER commit your `.env` file to git!**

The `.gitignore` should already exclude it, but double-check:
```bash
# Make sure .env is in .gitignore
echo ".env" >> ../.gitignore
```

---

## 🐛 Still Having Issues?

If you get other errors after adding the API key:

1. **Check the key is valid:**
   - Go to DeepSeek platform
   - Verify the key exists and is active

2. **Check the .env file location:**
   - Must be in `backend/.env`
   - Not in the project root

3. **Restart the backend:**
   - Stop with Ctrl+C
   - Start again with `python main.py`

4. **Check logs:**
   - Look for `[INFO]` and `[ERROR]` messages
   - They'll tell you what's wrong
