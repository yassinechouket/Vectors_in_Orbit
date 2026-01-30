// Screenshot crop overlay
// Injected when user wants to capture a specific area

let isSelecting = false;
let startX = 0;
let startY = 0;
let overlay = null;
let selectionBox = null;

// Create overlay
function createCropOverlay() {
    // Remove existing overlay if any
    removeCropOverlay();

    // Create dark overlay
    overlay = document.createElement('div');
    overlay.id = 'vio-screenshot-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 999999;
        cursor: crosshair;
    `;

    // Create selection box
    selectionBox = document.createElement('div');
    selectionBox.style.cssText = `
        position: fixed;
        border: 2px solid #818cf8;
        background: rgba(129, 140, 248, 0.1);
        display: none;
        z-index: 1000000;
        box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
    `;

    // Add instructions
    const instructions = document.createElement('div');
    instructions.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 16px;
        text-align: center;
        z-index: 1000001;
        pointer-events: none;
    `;
    instructions.innerHTML = `
        <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">📸 Select Area to Search</div>
        <div style="opacity: 0.8;">Click and drag to select a region</div>
        <div style="opacity: 0.6; font-size: 14px; margin-top: 8px;">Press ESC to cancel</div>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(selectionBox);
    document.body.appendChild(instructions);

    // Mouse events
    overlay.addEventListener('mousedown', handleMouseDown);
    overlay.addEventListener('mousemove', handleMouseMove);
    overlay.addEventListener('mouseup', handleMouseUp);

    // Keyboard event (ESC to cancel)
    document.addEventListener('keydown', handleKeyDown);

    // Hide instructions after 2 seconds
    setTimeout(() => {
        if (instructions.parentNode) {
            instructions.style.transition = 'opacity 0.3s';
            instructions.style.opacity = '0';
            setTimeout(() => instructions.remove(), 300);
        }
    }, 2000);
}

function handleMouseDown(e) {
    isSelecting = true;
    startX = e.clientX;
    startY = e.clientY;

    selectionBox.style.left = startX + 'px';
    selectionBox.style.top = startY + 'px';
    selectionBox.style.width = '0px';
    selectionBox.style.height = '0px';
    selectionBox.style.display = 'block';
}

function handleMouseMove(e) {
    if (!isSelecting) return;

    const currentX = e.clientX;
    const currentY = e.clientY;

    const width = Math.abs(currentX - startX);
    const height = Math.abs(currentY - startY);
    const left = Math.min(currentX, startX);
    const top = Math.min(currentY, startY);

    selectionBox.style.left = left + 'px';
    selectionBox.style.top = top + 'px';
    selectionBox.style.width = width + 'px';
    selectionBox.style.height = height + 'px';
}

async function handleMouseUp(e) {
    if (!isSelecting) return;

    isSelecting = false;

    const rect = selectionBox.getBoundingClientRect();

    // Check if selection is valid (at least 20x20 pixels)
    if (rect.width < 20 || rect.height < 20) {
        removeCropOverlay();
        return;
    }

    // Capture the selected area
    await captureSelectedArea(rect);

    removeCropOverlay();
}

function handleKeyDown(e) {
    if (e.key === 'Escape') {
        removeCropOverlay();
        chrome.runtime.sendMessage({
            type: 'SCREENSHOT_CANCELLED'
        });
    }
}

function removeCropOverlay() {
    if (overlay) {
        overlay.remove();
        overlay = null;
    }
    if (selectionBox) {
        selectionBox.remove();
        selectionBox = null;
    }
    document.removeEventListener('keydown', handleKeyDown);
}

async function captureSelectedArea(rect) {
    try {
        // Send message to background to capture screenshot
        chrome.runtime.sendMessage({
            type: 'CAPTURE_AREA',
            area: {
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                devicePixelRatio: window.devicePixelRatio || 1
            }
        });
    } catch (err) {
        console.error('Failed to capture area:', err);
    }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'START_SCREENSHOT_SELECTION') {
        createCropOverlay();
        sendResponse({ success: true });
    }
});
