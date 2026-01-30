// Background service worker for Vectors in Orbit extension

const API_BASE = 'http://localhost:8000';

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
    console.log('Vectors in Orbit extension installed');

    // Create context menu for image search
    chrome.contextMenus.create({
        id: 'search-similar-image',
        title: 'Find Similar Products',
        contexts: ['image']
    });

    // Initialize storage
    chrome.storage.local.set({
        session_history: [],
        current_page_context: ''
    });
});

// Context menu handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'search-similar-image' && info.srcUrl) {
        // Store image URL for popup to process
        chrome.storage.local.set({
            pending_visual_search: info.srcUrl
        });

        // Show badge
        chrome.action.setBadgeText({ text: '1' });
        chrome.action.setBadgeBackgroundColor({ color: '#818cf8' });

        // Open popup
        chrome.action.openPopup();
    }
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'PRODUCT_VISITED') {
        handleProductVisit(message.productId);
    }

    if (message.type === 'CONTEXT_EXTRACTED') {
        handleContextExtraction(message.context);
    }

    if (message.type === 'PRODUCT_PAGE_DETECTED') {
        handleProductPageDetected(message.productInfo, message.enhancedQuery);
    }

    if (message.type === 'FIND_SIMILAR') {
        // User clicked "Find Similar" button on product page
        chrome.storage.local.set({
            current_page_context: message.query
        });
        chrome.action.openPopup();
    }

    sendResponse({ success: true });
});

// Handle product visit
async function handleProductVisit(productId) {
    try {
        const result = await chrome.storage.local.get(['session_history']);
        let history = result.session_history || [];

        // Add to history if not already present
        if (!history.includes(productId)) {
            history.push(productId);

            // Keep last 20 products
            if (history.length > 20) {
                history = history.slice(-20);
            }

            await chrome.storage.local.set({ session_history: history });
        }
    } catch (err) {
        console.error('Failed to update session history:', err);
    }
}

// Handle context extraction
async function handleContextExtraction(context) {
    try {
        await chrome.storage.local.set({ current_page_context: context });
    } catch (err) {
        console.error('Failed to save context:', err);
    }
}

// Handle product page detection
async function handleProductPageDetected(productInfo, enhancedQuery) {
    try {
        // Store detected product info
        await chrome.storage.local.set({
            detected_product: productInfo,
            current_page_context: enhancedQuery
        });

        // Show badge
        chrome.action.setBadgeText({ text: '🛍️' });
        chrome.action.setBadgeBackgroundColor({ color: '#10b981' });

        console.log('Product page detected:', productInfo);
    } catch (err) {
        console.error('Failed to handle product detection:', err);
    }
}

// Handle area capture
async function handleCaptureArea(area, tab) {
    try {
        // Capture full screenshot
        const screenshotUrl = await chrome.tabs.captureVisibleTab(tab.windowId, {
            format: 'png'
        });

        // Crop to selected area
        const croppedBlob = await cropScreenshot(screenshotUrl, area);

        // Send to API
        const formData = new FormData();
        formData.append('image', croppedBlob, 'cropped-screenshot.png');

        const response = await fetch('http://localhost:8000/recommend/by-image', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();

            // Store results for popup
            await chrome.storage.local.set({
                screenshot_results: data.matches || [],
                screenshot_search_active: true
            });

            // Show badge
            chrome.action.setBadgeText({ text: String(data.matches?.length || 0) });
            chrome.action.setBadgeBackgroundColor({ color: '#10b981' });

            // Open popup to show results
            chrome.action.openPopup();
        }
    } catch (err) {
        console.error('Failed to process screenshot:', err);
    }
}

// Crop screenshot to selected area
async function cropScreenshot(screenshotUrl, area) {
    return new Promise((resolve, reject) => {
        const img = new Image();

        img.onload = () => {
            const canvas = new OffscreenCanvas(
                area.width * area.devicePixelRatio,
                area.height * area.devicePixelRatio
            );
            const ctx = canvas.getContext('2d');

            // Draw cropped portion
            ctx.drawImage(
                img,
                area.x * area.devicePixelRatio,
                area.y * area.devicePixelRatio,
                area.width * area.devicePixelRatio,
                area.height * area.devicePixelRatio,
                0,
                0,
                area.width * area.devicePixelRatio,
                area.height * area.devicePixelRatio
            );

            // Convert to blob
            canvas.convertToBlob({ type: 'image/png' })
                .then(resolve)
                .catch(reject);
        };

        img.onerror = reject;
        img.src = screenshotUrl;
    });
}

// Track page views for analytics (optional)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        // Clear badge when navigating to new page
        chrome.action.setBadgeText({ text: '' });
    }
});
