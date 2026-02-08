/**
 * Travel Concierge Dashboard - Frontend Logic
 */

const API_BASE = '';

// State
let sessions = [];
let currentSession = null;

// DOM Elements
const sessionList = document.getElementById('session-list');
const levelFilter = document.getElementById('level-filter');
const refreshBtn = document.getElementById('refresh-btn');
const emptyState = document.getElementById('empty-state');
const timelineContainer = document.getElementById('timeline-container');
const timeline = document.getElementById('timeline');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();

    refreshBtn.addEventListener('click', loadSessions);
    levelFilter.addEventListener('change', renderSessionList);
});

// Load sessions from API
async function loadSessions() {
    sessionList.innerHTML = '<div class="loading">Loading sessions...</div>';

    try {
        const response = await fetch(`${API_BASE}/api/sessions`);
        sessions = await response.json();
        sessions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
        renderSessionList();
    } catch (error) {
        sessionList.innerHTML = '<div class="loading">Failed to load sessions</div>';
        console.error('Failed to load sessions:', error);
    }
}

// Render session list
function renderSessionList() {
    const filterLevel = levelFilter.value;
    const filtered = filterLevel === 'all'
        ? sessions
        : sessions.filter(s => s.level.toString() === filterLevel);

    if (filtered.length === 0) {
        sessionList.innerHTML = '<div class="loading">No sessions found</div>';
        return;
    }

    sessionList.innerHTML = filtered.map(session => `
        <div class="session-item ${currentSession?.query_id === session.query_id ? 'active' : ''}"
             data-id="${session.query_id}">
            <div class="query">${escapeHtml(session.query_text)}</div>
            <div class="meta">
                <span class="level-badge">L${session.level}</span>
                <span>${session.total_tokens.toLocaleString()} tokens</span>
                <span>${session.event_count} events</span>
            </div>
        </div>
    `).join('');

    // Add click handlers
    sessionList.querySelectorAll('.session-item').forEach(item => {
        item.addEventListener('click', () => loadSession(item.dataset.id));
    });
}

// Load a specific session
async function loadSession(queryId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${queryId}?annotated=true`);
        currentSession = await response.json();
        renderTimeline();
        renderSessionList(); // Update active state
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

// Render the event timeline
function renderTimeline() {
    if (!currentSession) return;

    emptyState.style.display = 'none';
    timelineContainer.style.display = 'block';

    // Update header
    document.getElementById('session-level').textContent = `L${currentSession.level}`;
    document.getElementById('session-query').textContent = currentSession.query_text;
    document.getElementById('session-tokens').textContent = currentSession.total_tokens.toLocaleString();
    document.getElementById('session-events').textContent = currentSession.events.length;

    const startTime = new Date(currentSession.started_at);
    const endTime = currentSession.ended_at ? new Date(currentSession.ended_at) : null;
    const duration = endTime ? Math.round((endTime - startTime) / 1000) : null;
    document.getElementById('session-time').textContent = duration ? `${duration}s total` : '';

    // Render events
    let runningTokens = 0;
    timeline.innerHTML = currentSession.events.map((event, index) => {
        const annotation = event.annotation || {};
        const decisionMaker = annotation.decision_maker || event.decision_by || 'code';

        if (event.token_count) {
            runningTokens += event.token_count;
        }

        return `
            <div class="event-node" data-index="${index}">
                <div class="event-dot ${decisionMaker}"></div>
                <div class="event-card">
                    <div class="event-header" onclick="toggleEvent(${index})">
                        <div class="event-info">
                            <div class="event-title">${annotation.title || formatEventType(event.event_type)}</div>
                            <div class="event-what">${annotation.what || ''}</div>
                        </div>
                        <div class="event-stats">
                            ${event.token_count ? `<span class="token-badge">+${event.token_count.toLocaleString()}</span>` : ''}
                            ${event.duration_ms ? `<span class="duration-badge">${event.duration_ms}ms</span>` : ''}
                            ${runningTokens > 0 ? `<span class="running-total">Σ ${runningTokens.toLocaleString()}</span>` : ''}
                            <span class="expand-icon">▼</span>
                        </div>
                    </div>
                    <div class="event-detail">
                        ${renderEventDetail(event, annotation)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Render event detail section
function renderEventDetail(event, annotation) {
    let html = '';

    // Why section
    if (annotation.why) {
        html += `
            <div class="detail-section">
                <h4>Why This Happens</h4>
                <p>${annotation.why}</p>
            </div>
        `;
    }

    // Four Questions
    if (annotation.q1_who_decides) {
        html += `
            <div class="detail-section">
                <h4>Four Questions</h4>
                <div class="four-questions">
                    <div class="question-card q1">
                        <h5>Q1: Who Decides?</h5>
                        <p>${annotation.q1_who_decides}</p>
                    </div>
                    <div class="question-card q2">
                        <h5>Q2: What Does It See?</h5>
                        <p>${annotation.q2_what_visible}</p>
                    </div>
                    <div class="question-card q3">
                        <h5>Q3: What Can Go Wrong?</h5>
                        <p>${annotation.q3_blast_radius}</p>
                    </div>
                    <div class="question-card q4">
                        <h5>Q4: Where's the Human?</h5>
                        <p>${annotation.q4_human_involved}</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Level Insight
    if (annotation.level_insight) {
        html += `
            <div class="detail-section">
                <div class="level-insight">
                    <h5>💡 How This Changes at Other Levels</h5>
                    <p>${annotation.level_insight}</p>
                </div>
            </div>
        `;
    }

    // Raw data
    if (event.data && Object.keys(event.data).length > 0) {
        html += `
            <details class="raw-data">
                <summary>View Raw Event Data</summary>
                <pre>${escapeHtml(JSON.stringify(event.data, null, 2))}</pre>
            </details>
        `;
    }

    return html;
}

// Toggle event expansion
function toggleEvent(index) {
    const node = document.querySelector(`.event-node[data-index="${index}"]`);
    node.classList.toggle('expanded');
}

// Format event type to title case
function formatEventType(type) {
    return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
