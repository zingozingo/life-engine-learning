/**
 * Travel Concierge Dashboard - Frontend Logic
 */

const API_BASE = '';

// State
let conversations = [];
let currentConversation = null;
let currentSessions = [];

// DOM Elements
const conversationList = document.getElementById('conversation-list');
const levelFilter = document.getElementById('level-filter');
const refreshBtn = document.getElementById('refresh-btn');
const emptyState = document.getElementById('empty-state');
const conversationContainer = document.getElementById('conversation-container');
const queriesContainer = document.getElementById('queries-container');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConversations();

    refreshBtn.addEventListener('click', loadConversations);
    levelFilter.addEventListener('change', renderConversationList);
});

// Load conversations from API
async function loadConversations() {
    conversationList.innerHTML = '<div class="loading">Loading conversations...</div>';

    try {
        const response = await fetch(`${API_BASE}/api/conversations`);
        conversations = await response.json();
        renderConversationList();
    } catch (error) {
        conversationList.innerHTML = '<div class="loading">Failed to load conversations</div>';
        console.error('Failed to load conversations:', error);
    }
}

// Render conversation list in sidebar
function renderConversationList() {
    const filterLevel = levelFilter.value;
    const filtered = filterLevel === 'all'
        ? conversations
        : conversations.filter(c => c.level.toString() === filterLevel);

    if (filtered.length === 0) {
        conversationList.innerHTML = '<div class="loading">No conversations found</div>';
        return;
    }

    conversationList.innerHTML = filtered.map(conv => `
        <div class="conversation-item ${currentConversation?.conversation_id === conv.conversation_id ? 'active' : ''}"
             data-id="${conv.conversation_id}">
            <div class="title">${escapeHtml(conv.queries[0] || 'Empty conversation')}</div>
            <div class="meta">
                <span class="level-badge">L${conv.level}</span>
                <span>${conv.query_count} ${conv.query_count === 1 ? 'query' : 'queries'}</span>
                <span>${conv.total_tokens.toLocaleString()} tokens</span>
            </div>
        </div>
    `).join('');

    // Add click handlers
    conversationList.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', () => loadConversation(item.dataset.id));
    });
}

// Load a specific conversation
async function loadConversation(conversationId) {
    try {
        const response = await fetch(`${API_BASE}/api/conversations/${conversationId}?annotated=true`);
        currentSessions = await response.json();

        // Find conversation metadata
        currentConversation = conversations.find(c => c.conversation_id === conversationId);

        renderConversation();
        renderConversationList(); // Update active state
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}

// Render the conversation with all queries
function renderConversation() {
    if (!currentConversation || !currentSessions.length) return;

    emptyState.style.display = 'none';
    conversationContainer.style.display = 'block';

    // Update header
    document.getElementById('conversation-level').textContent = `L${currentConversation.level}`;
    document.getElementById('conversation-title').textContent = 'Conversation';
    document.getElementById('conversation-queries').textContent = currentConversation.query_count;
    document.getElementById('conversation-tokens').textContent = currentConversation.total_tokens.toLocaleString();

    const startTime = new Date(currentConversation.started_at);
    const endTime = currentConversation.ended_at ? new Date(currentConversation.ended_at) : null;
    const duration = endTime ? Math.round((endTime - startTime) / 1000) : null;
    document.getElementById('conversation-time').textContent = duration ? `${duration}s total` : '';

    // Render each query section
    queriesContainer.innerHTML = currentSessions.map((session, queryIndex) => {
        const historyTokens = session.conversation_history_tokens || 0;
        const historyLabel = queryIndex === 0
            ? 'First message (no history)'
            : `Conversation history: ~${historyTokens.toLocaleString()} tokens`;

        return `
            <div class="query-section" data-query-index="${queryIndex}">
                <div class="query-header" onclick="toggleQuery(${queryIndex})">
                    <div class="query-info">
                        <div class="query-number">Query ${queryIndex + 1}</div>
                        <div class="query-text">${escapeHtml(session.query_text)}</div>
                        <div class="query-history">${historyLabel}</div>
                    </div>
                    <div class="query-stats">
                        <span class="query-token-badge">${session.total_tokens.toLocaleString()} tokens</span>
                        <span class="expand-icon">&#9660;</span>
                    </div>
                </div>
                <div class="query-timeline">
                    ${renderTimeline(session.events)}
                </div>
            </div>
        `;
    }).join('');
}

// Render the event timeline for a query
function renderTimeline(events) {
    let runningTokens = 0;

    return `
        <div class="timeline">
            ${events.map((event, index) => {
                const annotation = event.annotation || {};
                const decisionMaker = annotation.decision_maker || event.decision_by || 'code';

                if (event.token_count) {
                    runningTokens += event.token_count;
                }

                // Get specific title and description for tool events
                const { title, what } = getEventDisplay(event, annotation);

                return `
                    <div class="event-node" data-event-index="${index}">
                        <div class="event-dot ${decisionMaker}"></div>
                        <div class="event-card">
                            <div class="event-header" onclick="toggleEvent(this)">
                                <div class="event-info">
                                    <div class="event-title">${title}</div>
                                    <div class="event-what">${what}</div>
                                </div>
                                <div class="event-stats">
                                    ${event.token_count ? `<span class="token-badge">+${event.token_count.toLocaleString()}</span>` : ''}
                                    ${event.duration_ms ? `<span class="duration-badge">${event.duration_ms}ms</span>` : ''}
                                    ${runningTokens > 0 ? `<span class="running-total">S ${runningTokens.toLocaleString()}</span>` : ''}
                                    <span class="expand-icon">&#9660;</span>
                                </div>
                            </div>
                            <div class="event-detail">
                                ${renderEventDetail(event, annotation)}
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Get display title and description for an event, with specifics for tool events
function getEventDisplay(event, annotation) {
    const eventType = event.event_type;
    const data = event.data || {};

    // Tool registered - show which tool
    if (eventType === 'tool_registered') {
        const toolName = data.tool_name || 'unknown';
        return {
            title: `Tool Registered: ${toolName}`,
            what: `${toolName} is now available for the LLM to call during this query.`
        };
    }

    // Tool called - show which tool and what it did
    if (eventType === 'tool_called') {
        const toolName = data.tool_name || 'unknown';
        let what = `The LLM called ${toolName}`;

        // Add parameter details
        if (data.parameters) {
            if (data.parameters.url) {
                // Extract domain from URL
                try {
                    const url = new URL(data.parameters.url);
                    what += ` to fetch data from ${url.hostname}`;
                } catch {
                    what += ` with URL: ${data.parameters.url.substring(0, 50)}...`;
                }
            } else if (data.parameters.endpoint) {
                what += ` (${data.parameters.endpoint})`;
            }
        }

        // Add result preview if available
        if (data.result_summary) {
            const preview = data.result_summary.substring(0, 80);
            what += `. Result: "${preview}${data.result_summary.length > 80 ? '...' : ''}"`;
        }

        return {
            title: `Tool Executed: ${toolName}`,
            what: what
        };
    }

    // Prompt composed - show skills included
    if (eventType === 'prompt_composed' && data.skills_included) {
        const skills = data.skills_included.join(', ');
        return {
            title: annotation.title || 'System Prompt Built',
            what: `Loaded skills: ${skills}. ${data.prompt_length?.toLocaleString() || '?'} characters.`
        };
    }

    // Default: use annotation or format event type
    return {
        title: annotation.title || formatEventType(eventType),
        what: annotation.what || ''
    };
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
                    <h5>How This Changes at Other Levels</h5>
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

// Toggle query expansion
function toggleQuery(queryIndex) {
    const section = document.querySelector(`.query-section[data-query-index="${queryIndex}"]`);
    section.classList.toggle('expanded');
}

// Toggle event expansion
function toggleEvent(header) {
    const node = header.closest('.event-node');
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
