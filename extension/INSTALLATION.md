# Extension Installation Guide

## 🚀 Quick Installation

### Step 1: Prepare the Extension
1. Make sure you're in the `extension` folder
2. All files should be present:
   - `manifest.json`
   - `popup.html`
   - `popup.js`
   - `content.js`
   - `background.js`
   - `icons/icon.svg`

### Step 2: Load in Chrome/Edge

1. **Open Chrome/Edge Browser**
2. **Go to Extensions Page**:
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
3. **Enable Developer Mode**:
   - Toggle the "Developer mode" switch in the top-right corner
4. **Load the Extension**:
   - Click "Load unpacked"
   - Navigate to the `extension` folder
   - Select the folder and click "Select Folder"

### Step 3: Verify Installation

1. You should see the extension icon in your browser toolbar
2. Click the icon to open the popup
3. You should see the "For You" interface

## ⚙️ Setup Requirements

### Backend Must Be Running
The extension requires the backend server to be running:
```bash
cd backend
python main.py
```
Server should be on: `http://localhost:8000`

### Webapp Should Be Running
For the best experience, have the webapp running:
```bash
cd webapp
npm run dev
```
Webapp should be on: `http://localhost:3000`

## 🎯 First Use

1. **Visit the Webapp**: Go to `http://localhost:3000`
2. **Browse Products**: Click on 2-3 products that interest you
3. **Open Extension**: Click the extension icon in your browser
4. **See Recommendations**: View your personalized recommendations!

## 🔧 Troubleshooting

### Extension Icon Not Showing
- Make sure `icons/icon.svg` exists
- Try reloading the extension (click the refresh icon on the extensions page)
- Check browser console for errors

### "Connection Error" Message
- Verify backend is running: `curl http://localhost:8000/health`
- Check that backend is on port 8000
- Make sure no firewall is blocking localhost connections

### No Recommendations
- Make sure you've clicked on at least 2-3 products on the webapp
- Check browser console (F12) for errors
- Verify the extension has "storage" permission

### Products Not Being Tracked
- Make sure products have `data-product-id` attribute
- Check that content script is loaded (F12 → Console should show "Vectors in Orbit extension loaded")
- Try refreshing the webapp page

## 📝 Icon Setup (Optional)

If you want to use PNG icons instead of SVG:

1. Convert `icons/icon.svg` to PNG at different sizes:
   - 16x16 pixels → `icon16.png`
   - 48x48 pixels → `icon48.png`
   - 128x128 pixels → `icon128.png`

2. Update `manifest.json`:
```json
"default_icon": {
  "16": "icons/icon16.png",
  "48": "icons/icon48.png",
  "128": "icons/icon128.png"
}
```

You can use online tools like:
- https://cloudconvert.com/svg-to-png
- https://convertio.co/svg-png/

## ✅ Verification Checklist

- [ ] Extension loads without errors
- [ ] Extension icon appears in toolbar
- [ ] Popup opens when clicking icon
- [ ] Backend is running on port 8000
- [ ] Webapp is running on port 3000
- [ ] Can browse products on webapp
- [ ] Extension tracks product clicks
- [ ] Recommendations appear in popup
- [ ] "Why?" button generates explanations
- [ ] "Visual" button performs visual search

## 🎉 You're Ready!

Once installed and verified, the extension will:
- ✅ Track products you view
- ✅ Show personalized recommendations
- ✅ Provide AI explanations
- ✅ Support visual search
- ✅ Learn your preferences over time

Enjoy your personalized shopping assistant! 🛍️✨

