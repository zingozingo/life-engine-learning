/**
 * Travel Concierge Dashboard - Frontend Logic
 * Two-level expansion: Data first, Education second
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

    // Compute total actual tokens across all sessions
    const totalActualTokens = currentSessions.reduce((sum, session) => {
        return sum + computeActualTokens(session.events);
    }, 0);

    // Update header
    document.getElementById('conversation-level').textContent = `L${currentConversation.level}`;
    document.getElementById('conversation-title').textContent = 'Conversation';
    document.getElementById('conversation-queries').textContent = currentConversation.query_count;
    document.getElementById('conversation-tokens').textContent = totalActualTokens.toLocaleString();

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

        // Compute actual tokens (only from token_role === 'actual' events)
        const actualTokens = computeActualTokens(session.events);

        return `
            <div class="query-section" data-query-index="${queryIndex}">
                <div class="query-header" onclick="toggleQuery(${queryIndex})">
                    <div class="query-info">
                        <div class="query-number">Query ${queryIndex + 1}</div>
                        <div class="query-text">${escapeHtml(session.query_text)}</div>
                        <div class="query-history">${historyLabel}</div>
                    </div>
                    <div class="query-stats">
                        <span class="query-token-badge">${actualTokens.toLocaleString()} tokens</span>
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

// Compute total tokens from only 'actual' events (llm_request, llm_response)
function computeActualTokens(events) {
    return events.reduce((sum, event) => {
        const role = event.token_role || 'actual';  // Legacy events default to 'actual'
        if (role === 'actual' && event.token_count) {
            return sum + event.token_count;
        }
        return sum;
    }, 0);
}

// Render the event timeline for a query
function renderTimeline(events) {
    let runningTokens = 0;

    return `
        <div class="timeline">
            ${events.map((event, index) => {
                const annotation = event.annotation || {};
                const decisionMaker = annotation.decision_maker || event.decision_by || 'code';
                const tokenRole = event.token_role || 'actual';  // Default for legacy events
                const isComposition = tokenRole === 'composition';
                const isActual = tokenRole === 'actual';

                // Only sum 'actual' events (real API usage)
                if (event.token_count && isActual) {
                    runningTokens += event.token_count;
                }

                // Get specific title and description for this event
                // Pass all events so llm_request can build breakdown from preceding composition events
                const { title, oneLiner } = getEventDisplay(event, annotation, events, index);

                // Token badge ONLY for actual events - composition events show tokens in description
                const tokenBadge = (event.token_count && isActual)
                    ? `<span class="token-badge">+${event.token_count.toLocaleString()}</span>`
                    : '';

                // Running total ONLY shown on actual events
                const runningTotalDisplay = (isActual && runningTokens > 0)
                    ? `<span class="running-total">Σ ${runningTokens.toLocaleString()}</span>`
                    : '';

                return `
                    <div class="event-node ${isComposition ? 'composition' : ''}" data-event-index="${index}">
                        <div class="event-dot ${decisionMaker}"></div>
                        <div class="event-card">
                            <div class="event-header" onclick="toggleEvent(this)">
                                <div class="event-info">
                                    <div class="event-title">${title}</div>
                                    <div class="event-what">${oneLiner}</div>
                                </div>
                                <div class="event-stats">
                                    ${tokenBadge}
                                    ${event.duration_ms ? `<span class="duration-badge">${event.duration_ms}ms</span>` : ''}
                                    ${runningTotalDisplay}
                                    <span class="expand-icon">&#9660;</span>
                                </div>
                            </div>
                            <div class="event-detail">
                                ${renderEventData(event)}
                                ${renderLearnSection(event, annotation)}
                                ${renderRawData(event)}
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Get display title and one-liner description built from actual event data
// events and currentIndex are passed so llm_request can build breakdown from preceding composition events
function getEventDisplay(event, annotation, events = [], currentIndex = 0) {
    const eventType = event.event_type;
    const data = event.data || {};

    switch (eventType) {
        case 'prompt_composed': {
            const skills = data.skills_included || [];
            const chars = data.prompt_length || 0;
            const tokens = event.token_count || Math.round(chars / 4);
            return {
                title: 'System Prompt Built',
                oneLiner: `Loaded ${skills.length} skills: ${skills.join(', ')}. ${chars.toLocaleString()} chars (~${tokens.toLocaleString()} tokens of LLM input).`
            };
        }

        case 'tool_registered': {
            const toolName = data.tool_name || 'unknown';
            const tokens = event.token_count || 0;
            return {
                title: `Tool Registered: ${toolName}`,
                oneLiner: `${toolName} available. ~${tokens} tokens of LLM input.`
            };
        }

        case 'skill_loaded': {
            const skillName = data.skill_name || 'unknown';
            const tokens = event.token_count || 0;
            return {
                title: `Skill Loaded: ${skillName}`,
                oneLiner: `${skillName} loaded. ~${tokens} tokens of LLM input.`
            };
        }

        case 'llm_request': {
            const model = data.model || 'unknown';
            const totalTokens = event.token_count || 0;

            // Build breakdown from preceding composition events
            const breakdown = buildTokenBreakdown(events, currentIndex, totalTokens);

            return {
                title: 'Request Sent to LLM',
                oneLiner: `Sent to ${model}. ~${totalTokens.toLocaleString()} input tokens ${breakdown}.`
            };
        }

        case 'tool_called': {
            const toolName = data.tool_name || 'unknown';
            const duration = event.duration_ms || 0;
            let target = '';
            if (data.parameters?.url) {
                try {
                    const url = new URL(data.parameters.url);
                    target = url.hostname + url.pathname.substring(0, 30);
                } catch {
                    target = data.parameters.url.substring(0, 40);
                }
            } else if (data.parameters?.endpoint) {
                target = data.parameters.endpoint;
            }
            return {
                title: `Tool Executed: ${toolName}`,
                oneLiner: target ? `Called ${toolName}: ${target} - ${duration}ms` : `Called ${toolName} - ${duration}ms`
            };
        }

        case 'llm_response': {
            const tokens = event.token_count || 0;
            const duration = event.duration_ms || 0;
            const length = data.response_length || 0;
            return {
                title: 'Response Generated',
                oneLiner: `Generated ${tokens.toLocaleString()}-token response (${length.toLocaleString()} chars) in ${duration.toLocaleString()}ms.`
            };
        }

        case 'error': {
            const msg = data.error_message || 'Unknown error';
            return {
                title: 'Error Occurred',
                oneLiner: msg.substring(0, 100)
            };
        }

        default:
            return {
                title: annotation.title || formatEventType(eventType),
                oneLiner: annotation.what || ''
            };
    }
}

// Build a token breakdown string for llm_request by analyzing preceding composition events
function buildTokenBreakdown(events, llmRequestIndex, totalTokens) {
    let promptTokens = 0;
    let toolTokens = 0;
    let skillTokens = 0;

    // Look at all events before this llm_request
    for (let i = 0; i < llmRequestIndex; i++) {
        const e = events[i];
        const role = e.token_role || 'actual';
        if (role !== 'composition') continue;

        const tokens = e.token_count || 0;
        switch (e.event_type) {
            case 'prompt_composed':
                promptTokens += tokens;
                break;
            case 'tool_registered':
                toolTokens += tokens;
                break;
            case 'skill_loaded':
                skillTokens += tokens;
                break;
        }
    }

    const compositionTotal = promptTokens + toolTokens + skillTokens;
    const messageTokens = Math.max(0, totalTokens - compositionTotal);

    // Build breakdown parts
    const parts = [];
    if (promptTokens > 0) parts.push(`prompt: ${promptTokens.toLocaleString()}`);
    if (toolTokens > 0) parts.push(`tools: ${toolTokens.toLocaleString()}`);
    if (skillTokens > 0) parts.push(`skills: ${skillTokens.toLocaleString()}`);
    if (messageTokens > 0) parts.push(`message: ~${messageTokens.toLocaleString()}`);

    if (parts.length === 0) return '';
    return `(${parts.join(' + ')})`;
}

// Render the DATA section (Level 1 expansion) - what actually happened
function renderEventData(event) {
    const eventType = event.event_type;
    const data = event.data || {};

    switch (eventType) {
        case 'prompt_composed':
            return renderPromptData(event, data);
        case 'tool_registered':
            return renderToolRegisteredData(event, data);
        case 'llm_request':
            return renderLLMRequestData(event, data);
        case 'tool_called':
            return renderToolCalledData(event, data);
        case 'llm_response':
            return renderLLMResponseData(event, data);
        case 'error':
            return renderErrorData(event, data);
        default:
            return '';
    }
}

function renderPromptData(event, data) {
    const skills = data.skills_included || [];
    const promptPreview = data.prompt_preview || '';
    const promptLength = data.prompt_length || 0;

    return `
        <div class="data-section">
            <div class="data-row">
                <span class="data-label">Skills Loaded:</span>
                <div class="skill-tags">
                    ${skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
                </div>
            </div>
            <div class="data-row">
                <span class="data-label">Size:</span>
                <span class="data-value">${promptLength.toLocaleString()} characters (~${(event.token_count || Math.round(promptLength/4)).toLocaleString()} tokens)</span>
            </div>
            ${promptPreview ? `
                <details class="data-expandable">
                    <summary>View Prompt Preview</summary>
                    <pre class="data-code">${escapeHtml(promptPreview)}</pre>
                </details>
            ` : ''}
        </div>
    `;
}

function renderToolRegisteredData(event, data) {
    const toolName = data.tool_name || 'unknown';
    return `
        <div class="data-section">
            <div class="data-row">
                <span class="data-label">Tool:</span>
                <span class="data-value mono">${escapeHtml(toolName)}</span>
            </div>
            <div class="data-row">
                <span class="data-label">Token Cost:</span>
                <span class="data-value">~${event.token_count || 0} tokens for tool definition</span>
            </div>
        </div>
    `;
}

function renderLLMRequestData(event, data) {
    const model = data.model || 'unknown';
    return `
        <div class="data-section">
            <div class="data-row">
                <span class="data-label">Model:</span>
                <span class="data-value mono">${escapeHtml(model)}</span>
            </div>
            <div class="data-row">
                <span class="data-label">Input Tokens:</span>
                <span class="data-value">~${(event.token_count || 0).toLocaleString()} tokens</span>
            </div>
        </div>
    `;
}

function renderToolCalledData(event, data) {
    const toolName = data.tool_name || 'unknown';
    const params = data.parameters || {};
    const result = data.result_summary || '';
    const duration = event.duration_ms || 0;

    return `
        <div class="data-section">
            <div class="data-row">
                <span class="data-label">Tool:</span>
                <span class="data-value mono">${escapeHtml(toolName)}</span>
            </div>
            <div class="data-row">
                <span class="data-label">Duration:</span>
                <span class="data-value">${duration}ms</span>
            </div>
            <div class="data-block">
                <span class="data-label">Parameters Sent:</span>
                <pre class="data-code">${escapeHtml(JSON.stringify(params, null, 2))}</pre>
            </div>
            ${result ? `
                <div class="data-block">
                    <span class="data-label">Result Received:</span>
                    <div class="result-preview">
                        <pre class="data-code">${escapeHtml(result.length > 500 ? result.substring(0, 500) : result)}</pre>
                        ${result.length > 500 ? `
                            <details class="show-more-inline">
                                <summary>Show full result (${result.length.toLocaleString()} chars)</summary>
                                <pre class="data-code">${escapeHtml(result)}</pre>
                            </details>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function renderLLMResponseData(event, data) {
    const responsePreview = data.response_preview || '';
    const responseLength = data.response_length || 0;
    const duration = event.duration_ms || 0;
    const tokens = event.token_count || 0;

    return `
        <div class="data-section">
            <div class="data-row">
                <span class="data-label">Output:</span>
                <span class="data-value">${tokens.toLocaleString()} tokens (${responseLength.toLocaleString()} chars) in ${duration.toLocaleString()}ms</span>
            </div>
            <div class="response-block">
                <span class="data-label">Response Text:</span>
                <div class="response-text">${escapeHtml(responsePreview)}</div>
            </div>
        </div>
    `;
}

function renderErrorData(event, data) {
    const errorMsg = data.error_message || 'Unknown error';
    const detail = data.detail || {};

    return `
        <div class="data-section error-data">
            <div class="data-block">
                <span class="data-label">Error:</span>
                <div class="error-message">${escapeHtml(errorMsg)}</div>
            </div>
            ${Object.keys(detail).length > 0 ? `
                <div class="data-block">
                    <span class="data-label">Details:</span>
                    <pre class="data-code">${escapeHtml(JSON.stringify(detail, null, 2))}</pre>
                </div>
            ` : ''}
        </div>
    `;
}

// Render the LEARN section (Level 2 expansion) - education content
function renderLearnSection(event, annotation) {
    if (!annotation.why && !annotation.q1_who_decides) {
        return '';
    }

    return `
        <details class="learn-section">
            <summary class="learn-toggle">Learn: Why does this happen?</summary>
            <div class="learn-content">
                ${annotation.why ? `
                    <div class="learn-why">
                        <p>${annotation.why}</p>
                    </div>
                ` : ''}

                ${annotation.q1_who_decides ? `
                    <div class="four-questions-compact">
                        <div class="q-row q1" onclick="toggleQRow(this)">
                            <span class="q-label">Q1 WHO DECIDES:</span>
                            <span class="q-preview">${truncate(annotation.q1_who_decides, 80)}</span>
                            <div class="q-full">${annotation.q1_who_decides}</div>
                        </div>
                        <div class="q-row q2" onclick="toggleQRow(this)">
                            <span class="q-label">Q2 WHAT VISIBLE:</span>
                            <span class="q-preview">${truncate(annotation.q2_what_visible, 80)}</span>
                            <div class="q-full">${annotation.q2_what_visible}</div>
                        </div>
                        <div class="q-row q3" onclick="toggleQRow(this)">
                            <span class="q-label">Q3 BLAST RADIUS:</span>
                            <span class="q-preview">${truncate(annotation.q3_blast_radius, 80)}</span>
                            <div class="q-full">${annotation.q3_blast_radius}</div>
                        </div>
                        <div class="q-row q4" onclick="toggleQRow(this)">
                            <span class="q-label">Q4 HUMAN:</span>
                            <span class="q-preview">${truncate(annotation.q4_human_involved, 80)}</span>
                            <div class="q-full">${annotation.q4_human_involved}</div>
                        </div>
                    </div>
                ` : ''}

                ${annotation.level_insight ? `
                    <div class="level-insight">
                        <h5>How This Changes at Other Levels</h5>
                        <p>${annotation.level_insight}</p>
                    </div>
                ` : ''}
            </div>
        </details>
    `;
}

// Render raw data section
function renderRawData(event) {
    if (!event.data || Object.keys(event.data).length === 0) {
        return '';
    }

    return `
        <details class="raw-data">
            <summary>View Raw Event Data</summary>
            <pre>${escapeHtml(JSON.stringify(event.data, null, 2))}</pre>
        </details>
    `;
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

// Toggle Q row expansion in compact Four Questions
function toggleQRow(row) {
    row.classList.toggle('expanded');
    event.stopPropagation();
}

// Truncate text with ellipsis
function truncate(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return escapeHtml(text);
    return escapeHtml(text.substring(0, maxLength)) + '...';
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
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}
