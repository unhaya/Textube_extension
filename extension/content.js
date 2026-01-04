// Textube Chrome Extension - Content Script

function getVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}

function getVideoTitle() {
  const titleEl = document.querySelector('h1.ytd-video-primary-info-renderer yt-formatted-string') ||
                  document.querySelector('h1.ytd-watch-metadata yt-formatted-string') ||
                  document.querySelector('h1 yt-formatted-string');
  return titleEl ? titleEl.textContent.trim() : '';
}

function getChannelName() {
  const channelEl = document.querySelector('#channel-name a') ||
                    document.querySelector('ytd-channel-name a');
  return channelEl ? channelEl.textContent.trim() : '';
}

function getVideoInfo() {
  return {
    videoId: getVideoId(),
    title: getVideoTitle(),
    channelName: getChannelName(),
    url: window.location.href
  };
}

// Message listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getVideoInfo') {
    sendResponse(getVideoInfo());
    return true;
  }

  if (request.action === 'ping') {
    sendResponse({ status: 'ok' });
    return true;
  }
});
