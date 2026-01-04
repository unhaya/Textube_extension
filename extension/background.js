// Textube Chrome Extension - Background Service Worker

const SERVER_URL = 'http://localhost:5000';

// Install event
chrome.runtime.onInstalled.addListener(() => {
  console.log('Textube Extension installed');

  // Default settings
  chrome.storage.local.get(['language', 'subtitleType', 'includeTimestamp'], (result) => {
    if (!result.language) {
      chrome.storage.local.set({
        language: 'ja',
        subtitleType: 'any',
        includeTimestamp: false
      });
    }
  });
});

// Message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractSubtitle') {
    extractSubtitle(request.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'checkServer') {
    checkServerHealth()
      .then(status => sendResponse({ online: status }))
      .catch(() => sendResponse({ online: false }));
    return true;
  }
});

// Extract subtitle via local server
async function extractSubtitle(data) {
  const response = await fetch(`${SERVER_URL}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to extract subtitles');
  }

  return await response.json();
}

// Server health check
async function checkServerHealth() {
  try {
    const response = await fetch(`${SERVER_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    return response.ok;
  } catch {
    return false;
  }
}
