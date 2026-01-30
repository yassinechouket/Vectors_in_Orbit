console.log("Vectors in Orbit extension loaded");

const API_BASE = 'http://localhost:8000';
let userId = null;
let sessionId = null;

// Initialize user session
async function initializeSession() {
    const result = await chrome.storage.local.get(['userId', 'sessionId']);

    if (!result.userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        await chrome.storage.local.set({ userId });
    } else {
        userId = result.userId;
    }

    // Create new session ID
    sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    await chrome.storage.local.set({ sessionId });
}

// Auto-detect if current page is a product page
async function detectProductPage() {
    const pageHTML = document.documentElement.outerHTML;
    const pageURL = window.location.href;

    try {
        const response = await fetch(`${API_BASE}/detect-product-page`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                html: pageHTML,
                url: pageURL
            })
        });

        if (response.ok) {
            const data = await response.json();

            if (data.detection.is_product_page) {
                console.log('✅ Product page detected!', data);

                // Notify popup
                chrome.runtime.sendMessage({
                    type: 'PRODUCT_PAGE_DETECTED',
                    productInfo: data.product_info,
                    enhancedQuery: data.enhanced_query
                });

                // Show "Find Similar" overlay
                showFindSimilarButton(data.product_info);

                // Track page view
                trackProductView(data.product_info);
            }
        }
    } catch (err) {
        console.log('Product detection failed:', err);
    }
}

// Show floating "Find Similar" button on product pages
function showFindSimilarButton(productInfo) {
    // Remove existing button
    const existing = document.getElementById('vio-find-similar-btn');
    if (existing) existing.remove();

    const button = document.createElement('div');
    button.id = 'vio-find-similar-btn';
    button.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
        </svg>
        <span>Find Similar</span>
    `;
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 30px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        cursor: pointer;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px;
        font-weight: 500;
        transition: transform 0.2s, box-shadow 0.2s;
    `;

    button.addEventListener('mouseenter', () => {
        button.style.transform = 'translateY(-2px)';
        button.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.5)';
    });

    button.addEventListener('mouseleave', () => {
        button.style.transform = '';
        button.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
    });

    button.addEventListener('click', () => {
        // Open extension popup with enhanced query
        chrome.runtime.sendMessage({
            type: 'FIND_SIMILAR',
            query: `Similar to ${productInfo.name}`,
            productInfo: productInfo
        });
    });

    document.body.appendChild(button);
}

// Track product view
async function trackProductView(productInfo) {
    if (!productInfo || !userId) return;

    try {
        await fetch(`${API_BASE}/tracking/view`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: productInfo.sku || productInfo.name,
                duration_seconds: 0, // Will be updated on page unload
                timestamp: new Date().toISOString()
            })
        });
    } catch (err) {
        console.log('View tracking failed:', err);
    }
}

// Track clicks on products
document.addEventListener('click', async (event) => {
    const productElement = event.target.closest('[data-product-id], a[href*="/product/"], .product-card, [itemtype*="Product"]');

    if (productElement) {
        const productId = productElement.getAttribute('data-product-id') ||
            productElement.getAttribute('data-id') ||
            'unknown_product';

        console.log('Product clicked:', productId);

        // Track click
        if (userId && sessionId) {
            try {
                await fetch(`${API_BASE}/tracking/click`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        product_id: productId,
                        position: 0,
                        source: 'page_browse',
                        context: {
                            url: window.location.href,
                            timestamp: new Date().toISOString()
                        },
                        session_id: sessionId
                    })
                });
            } catch (err) {
                console.log('Click tracking failed:', err);
            }
        }

        // Send message to background script
        chrome.runtime.sendMessage({
            type: 'PRODUCT_VISITED',
            productId: productId
        }).catch(err => {
            console.error('Failed to send product visit message:', err);
        });

        // Visual feedback
        productElement.style.transition = 'transform 0.1s';
        productElement.style.transform = 'scale(0.98)';
        setTimeout(() => {
            productElement.style.transform = '';
        }, 100);
    }
});

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'ADD_TO_WISHLIST') {
        // Track wishlist add
        fetch(`${API_BASE}/wishlist/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: message.productId,
                collection: message.collection || 'default',
                current_price: message.price,
                original_price: message.price
            })
        }).then(() => {
            sendResponse({ success: true });
        }).catch(() => {
            sendResponse({ success: false });
        });
        return true;
    }

    if (message.type === 'GET_PAGE_HTML') {
        // Send page HTML to popup for product detection
        sendResponse({
            html: document.documentElement.outerHTML,
            url: window.location.href
        });
        return true;
    }

    if (message.type === 'GET_PAGE_IMAGES') {
        // Extract all product images from the page
        const images = Array.from(document.querySelectorAll('img[src*="product"], img[alt*="product"], [itemtype*="Product"] img'))
            .map(img => img.src)
            .filter(src => src && !src.includes('placeholder'));

        sendResponse({ images: images.slice(0, 5) });
    }
});

// Mark tracked products with a subtle indicator
function markTrackedProducts() {
    const products = document.querySelectorAll('[data-product-id]:not([data-extension-tracked])');

    products.forEach(card => {
        card.setAttribute('data-extension-tracked', 'true');

        // Add subtle visual indicator
        if (!card.querySelector('.extension-indicator')) {
            const badge = document.createElement('div');
            badge.className = 'extension-indicator';
            badge.style.cssText = `
                position: absolute;
                top: 8px;
                left: 8px;
                width: 6px;
                height: 6px;
                background: #6366f1;
                border-radius: 50%;
                border: 1.5px solid rgba(255,255,255,0.8);
                z-index: 1000;
                box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
                pointer-events: none;
                opacity: 0.7;
            `;

            // Ensure parent has relative positioning
            const computedStyle = window.getComputedStyle(card);
            if (computedStyle.position === 'static') {
                card.style.position = 'relative';
            }

            card.appendChild(badge);
        }
    });
}

// Run periodically to handle dynamically loaded content
let markInterval = setInterval(markTrackedProducts, 1000);

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (markInterval) {
        clearInterval(markInterval);
    }
});

// Cross-site Context Extraction
function extractPageContext() {
    // Only extract if not on the local webapp
    if (window.location.hostname === 'localhost' && window.location.port === '3000') return;

    const pageTitle = document.title;
    const metaDesc = document.querySelector('meta[name="description"]')?.getAttribute('content') || "";
    const h1 = document.querySelector('h1')?.innerText || "";

    const context = `${pageTitle} ${h1} ${metaDesc}`.trim();

    if (context.length > 20) {
        console.log('Context extracted:', context);
        chrome.runtime.sendMessage({
            type: 'CONTEXT_EXTRACTED',
            context: context
        }).catch(err => {
            console.error('Failed to send context message:', err);
        });
    }
}

// Initialize on page load
(async function init() {
    await initializeSession();

    // Run context extraction
    if (document.readyState === 'complete') {
        extractPageContext();
        // Detect product page after a short delay to ensure page is fully loaded
        setTimeout(detectProductPage, 1000);
    } else {
        window.addEventListener('load', () => {
            extractPageContext();
            setTimeout(detectProductPage, 1000);
        });
    }

    // Initial mark
    markTrackedProducts();
})();
