const API_BASE = 'http://localhost:8000';
let userId = null;
let currentPreferences = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Get user ID
    const result = await chrome.storage.local.get(['userId', 'screenshot_results', 'screenshot_search_active']);
    userId = result.userId || 'user_' + Math.random().toString(36).substr(2, 9);
    await chrome.storage.local.set({ userId });

    // Check for screenshot results
    if (result.screenshot_search_active && result.screenshot_results) {
        renderRecommendations(result.screenshot_results);
        await chrome.storage.local.remove(['screenshot_search_active']);
        chrome.action.setBadgeText({ text: '' });
        return;
    }

    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const activeTab = document.querySelector('.tab.active').dataset.tab;
        if (activeTab === 'recommendations') loadRecommendations();
        if (activeTab === 'wishlist') loadWishlist();
    });

    // Search
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();

        if (query.length === 0) {
            loadRecommendations();
            return;
        }

        if (query.length < 2) return;

        searchTimeout = setTimeout(() => searchProducts(query), 400);
    });

    // Image upload
    document.getElementById('image-upload-input').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        showLoading('recommendations-list', 'Analyzing image...');

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch(`${API_BASE}/recommend/by-image`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                renderRecommendations(data.matches || []);
            } else {
                showError('recommendations-list', 'Image search failed');
            }
        } catch (err) {
            showError('recommendations-list', 'Could not process image');
        }
    });

    // Screenshot capture with area selection
    document.getElementById('screenshot-btn').addEventListener('click', async () => {
        try {
            // Get active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

            // Send message to content script to start selection
            await chrome.tabs.sendMessage(tab.id, {
                type: 'START_SCREENSHOT_SELECTION'
            });

            // Close popup to let user select area
            window.close();
        } catch (err) {
            console.error('Screenshot error:', err);
            showError('recommendations-list', 'Could not start screenshot capture');
        }
    });

    // Preferences
    setupPreferences();

    // Load initial data
    await checkForProductPageDetection();
    loadPreferences();
});

// ====================
// PRODUCT PAGE DETECTION
// ====================

async function checkForProductPageDetection() {
    console.log('🔍 Starting product page detection...');

    try {
        // Get the active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        console.log('📑 Active tab:', tab?.url);

        // Skip if on extension pages or chrome:// pages
        if (!tab || !tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
            console.log('⏭️ Skipping: Not a regular webpage');
            loadRecommendations();
            return;
        }

        // Request page HTML from content script
        console.log('📨 Requesting page HTML from content script...');
        let response;

        try {
            response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_HTML' });
        } catch (msgError) {
            console.error('❌ Content script not responding:', msgError);
            console.log('💡 This usually means the page needs to be refreshed after installing the extension');
            loadRecommendations();
            return;
        }

        if (!response || !response.html) {
            console.log('⚠️ No HTML received from content script');
            loadRecommendations();
            return;
        }

        console.log('✅ Got page HTML, length:', response.html.length);

        // Try backend detection first
        let productInfo = null;
        let enhancedQuery = null;

        try {
            console.log('🌐 Trying backend detection...');
            const detectionResponse = await fetch(`${API_BASE}/detect-product-page`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    html: response.html,
                    url: response.url
                })
            });

            if (detectionResponse.ok) {
                const detectionData = await detectionResponse.json();
                console.log('📥 Backend response:', detectionData);

                if (detectionData.detection && detectionData.detection.is_product_page && detectionData.product_info) {
                    productInfo = detectionData.product_info;
                    enhancedQuery = detectionData.enhanced_query;
                    console.log('✅ Backend detected product:', productInfo.name);
                }
            } else {
                console.log('⚠️ Backend returned error:', detectionResponse.status);
            }
        } catch (backendError) {
            console.log('⚠️ Backend detection failed, using client-side fallback:', backendError.message);
        }

        // If backend failed, try client-side extraction
        if (!productInfo) {
            console.log('🔧 Trying client-side extraction...');
            productInfo = extractProductInfoClientSide(response.html, response.url);

            if (productInfo) {
                console.log('✅ Client-side detected product:', productInfo);
            } else {
                console.log('❌ Client-side detection found no product');
            }
        }

        if (productInfo && productInfo.name) {
            // Product detected (either from backend or client-side)!
            console.log('🎉 Product detected! Displaying:', productInfo.name);
            displayDetectedProduct(productInfo, enhancedQuery);
        } else {
            // Not a product page, load normal recommendations
            console.log('📋 Not a product page, loading normal recommendations');
            loadRecommendations();
        }
    } catch (error) {
        console.error('❌ Product detection error:', error);
        // Fallback to normal recommendations
        loadRecommendations();
    }
}

function extractProductInfoClientSide(html, url) {
    // Parse HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    const productInfo = {
        name: null,
        price: null,
        image: null,
        brand: null,
        category: null,
        sku: null
    };

    // Extract product name (try multiple strategies)
    productInfo.name =
        doc.querySelector('[itemprop="name"]')?.textContent?.trim() ||
        doc.querySelector('h1[class*="product"]')?.textContent?.trim() ||
        doc.querySelector('h1[class*="title"]')?.textContent?.trim() ||
        doc.querySelector('.product-title')?.textContent?.trim() ||
        doc.querySelector('#productTitle')?.textContent?.trim() || // Amazon
        doc.querySelector('h1')?.textContent?.trim();

    // Extract price
    const priceText =
        doc.querySelector('[itemprop="price"]')?.getAttribute('content') ||
        doc.querySelector('[itemprop="price"]')?.textContent?.trim() ||
        doc.querySelector('.price')?.textContent?.trim() ||
        doc.querySelector('[class*="price"]')?.textContent?.trim() ||
        doc.querySelector('#priceblock_ourprice')?.textContent?.trim(); // Amazon

    if (priceText) {
        const priceMatch = priceText.match(/[\d,]+\.?\d*/);
        if (priceMatch) {
            productInfo.price = parseFloat(priceMatch[0].replace(',', ''));
        }
    }

    // Extract image
    productInfo.image =
        doc.querySelector('[itemprop="image"]')?.getAttribute('src') ||
        doc.querySelector('[itemprop="image"]')?.getAttribute('content') ||
        doc.querySelector('.product-image img')?.getAttribute('src') ||
        doc.querySelector('#landingImage')?.getAttribute('src') || // Amazon
        doc.querySelector('img[class*="product"]')?.getAttribute('src') ||
        doc.querySelector('meta[property="og:image"]')?.getAttribute('content');

    // Extract brand
    productInfo.brand =
        doc.querySelector('[itemprop="brand"]')?.textContent?.trim() ||
        doc.querySelector('[itemprop="brand"] [itemprop="name"]')?.textContent?.trim() ||
        doc.querySelector('.brand')?.textContent?.trim() ||
        doc.querySelector('#bylineInfo')?.textContent?.trim(); // Amazon

    // Extract category
    productInfo.category =
        doc.querySelector('[itemprop="category"]')?.textContent?.trim() ||
        doc.querySelector('.breadcrumb')?.textContent?.trim();

    // Check if this looks like a product page
    const hasProductIndicators =
        doc.querySelector('[itemtype*="Product"]') ||
        doc.querySelector('[class*="product"]') ||
        doc.querySelector('[id*="product"]') ||
        (productInfo.name && productInfo.price);

    // Only return if we have reasonable confidence this is a product page
    if (hasProductIndicators && productInfo.name) {
        return productInfo;
    }

    return null;
}

function displayDetectedProduct(productInfo, enhancedQuery) {
    // Show product info panel
    const panel = document.getElementById('product-info-panel');
    panel.style.display = 'block';

    // Fill in product details
    const nameEl = document.getElementById('detected-product-name');
    const metaEl = document.getElementById('detected-product-meta');
    const imageEl = document.getElementById('detected-product-image');

    nameEl.textContent = productInfo.name || 'Product';

    let metaText = '';
    if (productInfo.price) metaText += `$${productInfo.price}`;
    if (productInfo.brand) metaText += (metaText ? ' • ' : '') + productInfo.brand;
    if (productInfo.category) metaText += (metaText ? ' • ' : '') + productInfo.category;

    metaEl.textContent = metaText || 'Viewing product';

    // Show product image if available
    if (productInfo.image) {
        imageEl.src = productInfo.image;
        imageEl.style.display = 'block';
        imageEl.onerror = () => {
            imageEl.style.display = 'none';
        };
    } else {
        imageEl.style.display = 'none';
    }

    // Setup "Find Similar" button
    const findSimilarBtn = document.getElementById('find-similar-btn');
    findSimilarBtn.onclick = () => {
        const query = enhancedQuery || `Similar to ${productInfo.name}`;
        searchProducts(query);
    };

    // Auto-trigger similar product search
    setTimeout(() => {
        const query = enhancedQuery || `Similar to ${productInfo.name}`;
        searchProducts(query);
    }, 300);
}

// Tab Management
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load data
    if (tabName === 'wishlist') loadWishlist();
    if (tabName === 'preferences') loadPreferences();
}

// ====================
// RECOMMENDATIONS TAB
// ====================

async function loadRecommendations() {
    showLoading('recommendations-list');

    try {
        const result = await chrome.storage.local.get(['session_history']);
        const history = result.session_history || [];

        const response = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_items: history,
                limit: 10
            })
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        renderRecommendations(data.recommendations || []);
    } catch (error) {
        showError('recommendations-list', 'Backend unavailable');
    }
}

async function searchProducts(query) {
    showLoading('recommendations-list', `Searching for "${query}"...`);

    try {
        // Track search
        await fetch(`${API_BASE}/tracking/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                query: query,
                results_count: 0,
                timestamp: new Date().toISOString()
            })
        }).catch(() => { });

        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit: 10 })
        });

        const data = await response.json();
        renderRecommendations(data.recommendations || []);
    } catch (err) {
        showError('recommendations-list', 'Search failed');
    }
}

function renderRecommendations(items) {
    const container = document.getElementById('recommendations-list');

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="loading-state">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity: 0.5;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                </svg>
                <p style="font-size: 0.85rem;">No recommendations yet<br><small style="opacity: 0.6;">Browse products to get started</small></p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    items.forEach(item => {
        const product = item.product || item.payload || item;
        const card = createProductCard(product, item.reason);
        container.appendChild(card);
    });
}

function createProductCard(product, reason) {
    const card = document.createElement('div');
    card.className = 'card';

    const productId = product.id || product.product_id || product.sku;
    const productName = product.title || product.product_name || product.name;
    const productPrice = product.price || 0;
    const productCategory = product.category || 'Product';
    const productImage = product.image_url || 'https://via.placeholder.com/60';

    card.innerHTML = `
        <div class="card-main" data-id="${productId}">
            <div class="img-container">
                <img src="${productImage}" alt="${productName}" onerror="this.src='https://via.placeholder.com/60'">
            </div>
            <div class="card-info">
                <div class="card-title" title="${productName}">${productName}</div>
                <div class="card-meta">
                    <span class="price">$${productPrice}</span>
                    <span>•</span>
                    <span>${productCategory}</span>
                </div>
                ${reason ? `<div class="badge">✨ ${reason}</div>` : ''}
            </div>
        </div>
        <div class="card-actions">
            <button class="btn wishlist-btn" data-id="${productId}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
                Save
            </button>
            <button class="btn explain-btn" data-id="${productId}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                Why?
            </button>
            <button class="btn btn-primary similar-btn" data-id="${productId}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                </svg>
                Similar
            </button>
        </div>
        <div class="explanation" id="explain-${productId}"></div>
    `;

    // Click to view
    card.querySelector('.card-main').addEventListener('click', () => {
        // Track click
        fetch(`${API_BASE}/tracking/click`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: productId,
                position: 0,
                source: 'extension_recommendations'
            })
        }).catch(() => { });

        window.open(`http://localhost:3000/product/${productId}`, '_blank');
    });

    // Wishlist button
    card.querySelector('.wishlist-btn').addEventListener('click', async () => {
        await addToWishlist(productId, productName, productPrice);
    });

    // Explain button
    card.querySelector('.explain-btn').addEventListener('click', async () => {
        const explainBox = card.querySelector('.explanation');
        if (explainBox.style.display === 'block') {
            explainBox.style.display = 'none';
            return;
        }

        explainBox.innerHTML = 'Analyzing...';
        explainBox.style.display = 'block';

        try {
            const response = await fetch(`${API_BASE}/explain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: productId,
                    user_history_titles: []
                })
            });

            const data = await response.json();
            explainBox.innerHTML = `<strong>AI Insight:</strong> ${data.explanation}`;
        } catch {
            explainBox.innerHTML = 'Could not generate explanation';
        }
    });

    // Similar button
    card.querySelector('.similar-btn').addEventListener('click', async () => {
        showLoading('recommendations-list', 'Finding similar products...');

        try {
            const response = await fetch(`${API_BASE}/recommend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_items: [productId],
                    limit: 5
                })
            });

            const data = await response.json();
            renderRecommendations(data.recommendations || []);
        } catch {
            showError('recommendations-list', 'Could not find similar items');
        }
    });

    return card;
}

// ====================
// WISHLIST TAB
// ====================

async function loadWishlist() {
    showLoading('wishlist-list');

    try {
        const response = await fetch(`${API_BASE}/wishlist/${userId}`);

        if (!response.ok) throw new Error('Failed');

        const data = await response.json();
        renderWishlist(data.items || []);
    } catch {
        showError('wishlist-list', 'Could not load wishlist');
    }
}

function renderWishlist(items) {
    const container = document.getElementById('wishlist-list');

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="loading-state">
                <p style="font-size: 0.85rem;">Wishlist is empty<br><small style="opacity: 0.6;">Save products from recommendations</small></p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    items.forEach(item => {
        const card = createWishlistCard(item);
        container.appendChild(card);
    });
}

function createWishlistCard(item) {
    const card = document.createElement('div');
    card.className = 'card';

    const priceDrop = item.original_price > item.current_price;
    const dropPercent = priceDrop ? ((item.original_price - item.current_price) / item.original_price * 100).toFixed(0) : 0;

    card.innerHTML = `
        <div class="card-main">
            <div class="card-info">
                <div class="card-title">${item.product_name || item.product_id}</div>
                <div class="card-meta">
                    <span class="price">$${item.current_price}</span>
                    ${priceDrop ? `<span style="color: #10b981;">↓ ${dropPercent}%</span>` : ''}
                </div>
                <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 4px;">
                    ${item.collection || 'default'}
                </div>
            </div>
        </div>
        <div class="card-actions">
            <button class="btn remove-btn" data-id="${item.product_id}">Remove</button>
        </div>
    `;

    card.querySelector('.remove-btn').addEventListener('click', async () => {
        await removeFromWishlist(item.product_id);
    });

    return card;
}

async function addToWishlist(productId, productName, price) {
    try {
        const response = await fetch(`${API_BASE}/wishlist/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                product_id: productId,
                product_name: productName,
                collection: 'default',
                current_price: price,
                original_price: price
            })
        });

        if (response.ok) {
            showNotification('✓ Added to wishlist');
        }
    } catch {
        showNotification('✗ Failed to add');
    }
}

async function removeFromWishlist(productId) {
    try {
        await fetch(`${API_BASE}/wishlist/remove/${productId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        loadWishlist();
        showNotification('✓ Removed from wishlist');
    } catch {
        showNotification('✗ Failed to remove');
    }
}

// ====================
// PREFERENCES TAB
// ====================

function setupPreferences() {
    // Ethical toggles
    document.querySelectorAll('#ethical-toggles .toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
        });
    });

    // Priority toggles (single select)
    document.querySelectorAll('#priority-toggles .toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#priority-toggles .toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Boycott management
    document.getElementById('add-boycott-btn').addEventListener('click', async () => {
        const brand = document.getElementById('boycott-brand').value.trim();
        const reason = document.getElementById('boycott-reason').value.trim();

        if (!brand) return;

        try {
            await fetch(`${API_BASE}/preferences/boycott/${userId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    brand,
                    reason: reason || 'No reason provided',
                    active: true
                })
            });

            document.getElementById('boycott-brand').value = '';
            document.getElementById('boycott-reason').value = '';
            loadPreferences();
            showNotification('✓ Boycott added');
        } catch {
            showNotification('✗ Failed to add boycott');
        }
    });

    // Save preferences
    document.getElementById('save-preferences-btn').addEventListener('click', saveAllPreferences);
}

async function loadPreferences() {
    try {
        const response = await fetch(`${API_BASE}/preferences/${userId}`);
        const data = await response.json();
        currentPreferences = data;

        // Load financial data
        if (data.financial_info) {
            document.getElementById('monthly-income').value = data.financial_info.monthly_income || '';
        }

        // Load ethical preferences
        if (data.ethical_preferences) {
            Object.keys(data.ethical_preferences).forEach(key => {
                const btn = document.querySelector(`#ethical-toggles [data-pref="${key}"]`);
                if (btn && data.ethical_preferences[key]) {
                    btn.classList.add('active');
                }
            });
        }

        // Load priority
        if (data.priority) {
            document.querySelectorAll('#priority-toggles .toggle-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.priority === data.priority.focus) {
                    btn.classList.add('active');
                }
            });
        }

        // Load boycotts
        renderBoycotts(data.brand_boycotts || []);
    } catch {
        console.log('Could not load preferences');
    }
}

function renderBoycotts(boycotts) {
    const container = document.getElementById('boycott-list');
    container.innerHTML = '';

    boycotts.forEach(boycott => {
        if (!boycott.active) return;

        const item = document.createElement('div');
        item.className = 'boycott-item';
        item.innerHTML = `
            <div>
                <div style="font-weight: 600; font-size: 0.8rem;">${boycott.brand}</div>
                <div style="font-size: 0.7rem; color: var(--text-dim);">${boycott.reason}</div>
            </div>
            <button class="remove-btn" data-brand="${boycott.brand}">Remove</button>
        `;

        item.querySelector('.remove-btn').addEventListener('click', async () => {
            await removeBoycott(boycott.brand);
        });

        container.appendChild(item);
    });
}

async function removeBoycott(brand) {
    try {
        await fetch(`${API_BASE}/preferences/boycott/${userId}/${encodeURIComponent(brand)}`, {
            method: 'DELETE'
        });
        loadPreferences();
        showNotification('✓ Boycott removed');
    } catch {
        showNotification('✗ Failed to remove');
    }
}

async function saveAllPreferences() {
    const monthlyIncome = parseFloat(document.getElementById('monthly-income').value) || 0;

    // Get ethical preferences
    const ethical = {};
    document.querySelectorAll('#ethical-toggles .toggle-btn').forEach(btn => {
        ethical[btn.dataset.pref] = btn.classList.contains('active');
    });

    // Get priority
    const priorityBtn = document.querySelector('#priority-toggles .toggle-btn.active');
    const priority = priorityBtn ? priorityBtn.dataset.priority : 'price';

    try {
        // Save financial
        if (monthlyIncome > 0) {
            await fetch(`${API_BASE}/preferences/financial/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    monthly_income: monthlyIncome,
                    budget_categories: {},
                    savings_goal: 0
                })
            });
        }

        // Save ethical
        await fetch(`${API_BASE}/preferences/ethical/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ethical)
        });

        // Save priority
        await fetch(`${API_BASE}/preferences/priority/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                focus: priority,
                weights: {}
            })
        });

        showNotification('✓ Preferences saved');
    } catch {
        showNotification('✗ Failed to save');
    }
}

// ====================
// HELPERS
// ====================

function showLoading(containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="loading-state">
            <div class="loader"></div>
            <p style="font-size: 0.85rem;">${message}</p>
        </div>
    `;
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="loading-state">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p style="font-size: 0.85rem; color: #ef4444;">${message}</p>
        </div>
    `;
}

function showNotification(message) {
    // Create temporary notification at bottom of popup
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.8rem;
        z-index: 999999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 2000);
}
