// Industry News Scanner Frontend
const API_BASE_URL = '';  // Use relative path for deployment compatibility
// #region agent log
fetch('http://127.0.0.1:7245/ingest/1bd910ba-ebaa-4b1e-9bd3-de653771c99d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:2',message:'API_BASE_URL initialized',data:{apiBaseUrl:API_BASE_URL},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
// #endregion

// DOM Elements
const scanButton = document.getElementById('scanButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const reportContainer = document.getElementById('reportContainer');
const emptyState = document.getElementById('emptyState');
const reportContent = document.getElementById('reportContent');
const scanTimestamp = document.getElementById('scanTimestamp');
const totalItems = document.getElementById('totalItems');
const highCount = document.getElementById('highCount');
const mediumCount = document.getElementById('mediumCount');
const lowCount = document.getElementById('lowCount');
const copyJsonButton = document.getElementById('copyJsonButton');

let currentReport = null;

// Event Listeners
scanButton.addEventListener('click', startScan);
copyJsonButton.addEventListener('click', copyJsonToClipboard);

// Start scan workflow
async function startScan() {
    // Reset UI
    hideError();
    hideReport();
    showLoading();
    disableButton();

    // Get selected search source
    const searchSource = document.querySelector('input[name="searchSource"]:checked').value;
    const requestUrl = `${API_BASE_URL}/api/scan`;
    // #region agent log
    fetch('http://127.0.0.1:7245/ingest/1bd910ba-ebaa-4b1e-9bd3-de653771c99d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:33',message:'Before fetch request',data:{apiBaseUrl:API_BASE_URL,requestUrl:requestUrl,searchSource:searchSource},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion

    try {
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/1bd910ba-ebaa-4b1e-9bd3-de653771c99d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:38',message:'Fetch attempt started',data:{requestUrl:requestUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        const response = await fetch(requestUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_source: searchSource
            }),
        });
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/1bd910ba-ebaa-4b1e-9bd3-de653771c99d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:46',message:'Fetch response received',data:{status:response.status,statusText:response.statusText,ok:response.ok,headers:Object.fromEntries(response.headers.entries())},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
        // #endregion

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const report = await response.json();
        currentReport = report;
        displayReport(report);
    } catch (error) {
        console.error('Scan error:', error);
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/1bd910ba-ebaa-4b1e-9bd3-de653771c99d',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:57',message:'Fetch error caught',data:{errorName:error.name,errorMessage:error.message,errorStack:error.stack,errorType:typeof error},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        showError(`Scan failed: ${error.message}. Make sure the backend server is running at ${API_BASE_URL}`);
    } finally {
        hideLoading();
        enableButton();
    }
}

// Display scan report
function displayReport(report) {
    // Update summary
    scanTimestamp.textContent = `Scanned at: ${formatTimestamp(report.scan_timestamp)}`;
    totalItems.textContent = `Total: ${report.total_items} items`;
    highCount.textContent = report.high_importance_count;
    mediumCount.textContent = report.medium_importance_count;
    lowCount.textContent = report.low_importance_count;

    // Group items by importance
    const groupedItems = {
        high: [],
        medium: [],
        low: []
    };

    report.items.forEach(item => {
        groupedItems[item.importance].push(item);
    });

    // Render report content
    reportContent.innerHTML = '';

    // Render each importance group
    ['high', 'medium', 'low'].forEach(importance => {
        if (groupedItems[importance].length === 0) return;

        const groupDiv = document.createElement('div');
        groupDiv.className = 'importance-group';

        const groupHeader = document.createElement('div');
        groupHeader.className = `group-header ${importance}`;
        groupHeader.textContent = `${importance.toUpperCase()} Importance (${groupedItems[importance].length})`;
        groupDiv.appendChild(groupHeader);

        groupedItems[importance].forEach((item, index) => {
            const itemDiv = createReportItem(item, index);
            groupDiv.appendChild(itemDiv);
        });

        reportContent.appendChild(groupDiv);
    });

    showReport();
}

// Create a report item element
function createReportItem(item, index) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'report-item';
    itemDiv.id = `item-${index}`;

    // Header (clickable to expand/collapse)
    const header = document.createElement('div');
    header.className = 'item-header';
    header.addEventListener('click', () => toggleItemDetails(index));

    const titleDiv = document.createElement('div');
    titleDiv.className = 'item-title';
    titleDiv.textContent = item.title;
    header.appendChild(titleDiv);

    const metaDiv = document.createElement('div');
    metaDiv.className = 'item-meta';

    // Importance badge
    const importanceBadge = document.createElement('span');
    importanceBadge.className = `importance-badge ${item.importance}`;
    importanceBadge.textContent = item.importance;
    metaDiv.appendChild(importanceBadge);

    // Confidence badge
    const confidenceBadge = document.createElement('span');
    confidenceBadge.className = 'confidence-badge';
    confidenceBadge.textContent = `Confidence: ${(item.confidence * 100).toFixed(0)}%`;
    metaDiv.appendChild(confidenceBadge);

    // Source link
    const sourceLink = document.createElement('a');
    sourceLink.className = 'source-link';
    sourceLink.href = item.url;
    sourceLink.target = '_blank';
    sourceLink.textContent = item.source;
    metaDiv.appendChild(sourceLink);

    // Expand icon
    const expandIcon = document.createElement('span');
    expandIcon.className = 'expand-icon';
    expandIcon.textContent = '▼';
    metaDiv.appendChild(expandIcon);

    header.appendChild(metaDiv);
    itemDiv.appendChild(header);

    // Details (collapsible)
    const details = document.createElement('div');
    details.className = 'item-details';
    details.id = `details-${index}`;

    // Why it matters
    if (item.why_it_matters && item.why_it_matters.length > 0) {
        const whySection = createDetailSection('Why It Matters', item.why_it_matters);
        details.appendChild(whySection);
    }

    // Evidence
    if (item.evidence) {
        const evidenceSection = createDetailSection('Evidence', [item.evidence]);
        details.appendChild(evidenceSection);
    }

    // Recommended actions
    if (item.recommended_actions && item.recommended_actions.length > 0) {
        const actionsSection = createDetailSection('Recommended Actions', item.recommended_actions);
        details.appendChild(actionsSection);
    }

    // Second order impacts
    if (item.second_order_impacts) {
        const impactsSection = createDetailSection('Second Order Impacts', [item.second_order_impacts]);
        details.appendChild(impactsSection);
    }

    // Category
    if (item.category) {
        const categorySection = createDetailSection('Category', [item.category]);
        details.appendChild(categorySection);
    }

    // Dedupe note
    if (item.dedupe_note) {
        const dedupeSection = createDetailSection('Dedupe Note', [item.dedupe_note]);
        details.appendChild(dedupeSection);
    }

    itemDiv.appendChild(details);

    return itemDiv;
}

// Create a detail section
function createDetailSection(label, content) {
    const section = document.createElement('div');
    section.className = 'detail-section';

    const labelDiv = document.createElement('div');
    labelDiv.className = 'detail-label';
    labelDiv.textContent = label;
    section.appendChild(labelDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'detail-content';

    if (Array.isArray(content)) {
        const list = document.createElement('ul');
        list.className = 'detail-list';
        content.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
        contentDiv.appendChild(list);
    } else {
        contentDiv.textContent = content;
    }

    section.appendChild(contentDiv);
    return section;
}

// Toggle item details
function toggleItemDetails(index) {
    const details = document.getElementById(`details-${index}`);
    const item = document.getElementById(`item-${index}`);
    const expandIcon = item.querySelector('.expand-icon');

    if (details.classList.contains('expanded')) {
        details.classList.remove('expanded');
        expandIcon.classList.remove('expanded');
    } else {
        details.classList.add('expanded');
        expandIcon.classList.add('expanded');
    }
}

// Copy JSON to clipboard
async function copyJsonToClipboard() {
    if (!currentReport) return;

    try {
        const jsonString = JSON.stringify(currentReport, null, 2);
        await navigator.clipboard.writeText(jsonString);
        
        // Show feedback
        const originalText = copyJsonButton.textContent;
        copyJsonButton.textContent = 'Copied!';
        copyJsonButton.style.background = '#4caf50';
        
        setTimeout(() => {
            copyJsonButton.textContent = originalText;
            copyJsonButton.style.background = '#667eea';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy JSON to clipboard');
    }
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// UI Helper Functions
function showLoading() {
    loadingIndicator.classList.remove('hidden');
    emptyState.classList.add('hidden');
}

function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    emptyState.classList.add('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function showReport() {
    reportContainer.classList.remove('hidden');
    emptyState.classList.add('hidden');
}

function hideReport() {
    reportContainer.classList.add('hidden');
}

function disableButton() {
    scanButton.disabled = true;
    scanButton.querySelector('.button-text').textContent = 'Scanning...';
}

function enableButton() {
    scanButton.disabled = false;
    scanButton.querySelector('.button-text').textContent = 'Start Scan';
}

