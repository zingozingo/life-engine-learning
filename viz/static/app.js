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

        // Build history label
        let historyHtml = '';
        if (queryIndex === 0) {
            historyHtml = '<div class="query-history">First message (no history)</div>';
        } else if (historyTokens > 0) {
            historyHtml = `<div class="history-note">Carrying ${historyTokens.toLocaleString()} tokens of conversation history</div>`;
        } else {
            historyHtml = `<div class="query-history">Query ${queryIndex + 1} in conversation</div>`;
        }

        // Build token summary - prefer new format with input/output split
        const totalInput = session.total_input_tokens || 0;
        const totalOutput = session.total_output_tokens || 0;
        const totalCalls = session.total_api_calls || 0;
        const totalTokens = totalInput + totalOutput;

        let tokenSummary;
        if (totalCalls > 0) {
            tokenSummary = `${totalTokens.toLocaleString()} tokens (${totalCalls} call${totalCalls > 1 ? 's' : ''}: ${totalInput.toLocaleString()} in + ${totalOutput.toLocaleString()} out)`;
        } else {
            // Legacy format fallback
            const actualTokens = computeActualTokens(session.events);
            tokenSummary = `${actualTokens.toLocaleString()} tokens`;
        }

        return `
            <div class="query-section" data-query-index="${queryIndex}">
                <div class="query-header" onclick="toggleQuery(${queryIndex})">
                    <div class="query-info">
                        <div class="query-number">Query ${queryIndex + 1}</div>
                        <div class="query-text">${escapeHtml(session.query_text)}</div>
                        ${historyHtml}
                    </div>
                    <div class="query-stats">
                        <span class="query-token-badge">${tokenSummary}</span>
                        <span class="expand-icon">&#9660;</span>
                    </div>
                </div>
                <div class="query-timeline">
                    ${renderNarrativeTimeline(session.events, session)}
                </div>
            </div>
        `;
    }).join('');
}

// Compute total tokens from 'actual' events (api_call, or legacy llm_request/llm_response)
function computeActualTokens(events) {
    let total = 0;
    for (const event of events) {
        if (event.event_type === 'api_call') {
            // New format: tokens in data object
            total += (event.data?.input_tokens || 0) + (event.data?.output_tokens || 0);
        } else if (event.token_role === 'actual' && event.token_count) {
            // Legacy format: tokens in token_count field
            total += event.token_count;
        }
    }
    return total;
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
                const isApiCall = event.event_type === 'api_call';

                // Compute token badge and running total
                let tokenBadge = '';
                let runningTotalDisplay = '';

                if (isApiCall) {
                    // New format: api_call events
                    const inputTokens = event.data?.input_tokens || 0;
                    const outputTokens = event.data?.output_tokens || 0;
                    const roundTokens = inputTokens + outputTokens;
                    runningTokens += roundTokens;

                    tokenBadge = `<span class="token-badge api-call-badge">+${inputTokens.toLocaleString()} in / +${outputTokens.toLocaleString()} out</span>`;
                    runningTotalDisplay = `<span class="running-total">${runningTokens.toLocaleString()}</span>`;
                } else if (event.token_count && isActual) {
                    // Legacy format: llm_request/llm_response
                    runningTokens += event.token_count;
                    tokenBadge = `<span class="token-badge">+${event.token_count.toLocaleString()}</span>`;
                    runningTotalDisplay = `<span class="running-total">${runningTokens.toLocaleString()}</span>`;
                }

                // Get specific title and description for this event
                // Pass all events so llm_request can build breakdown from preceding composition events
                const { title, oneLiner } = getEventDisplay(event, annotation, events, index);

                // Determine event node classes
                const nodeClasses = [
                    'event-node',
                    isComposition ? 'composition' : '',
                    isApiCall ? 'api-call' : ''
                ].filter(Boolean).join(' ');

                return `
                    <div class="${nodeClasses}" data-event-index="${index}" data-event-type="${event.event_type}">
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

        case 'api_call': {
            const round = data.round_number;
            const total = data.total_rounds || '?';
            const input = data.input_tokens || 0;
            const output = data.output_tokens || 0;
            const type = data.response_type;
            const tools = data.tool_calls?.join(', ') || '';

            let title, oneLiner;
            if (total === 1 && type === 'text') {
                // Simple query, no tools — don't overcomplicate
                title = 'API Call';
                oneLiner = `${input.toLocaleString()} in + ${output.toLocaleString()} out`;
            } else {
                title = `API Round ${round} of ${total}`;
                if (type === 'tool_call') {
                    oneLiner = `${input.toLocaleString()} in + ${output.toLocaleString()} out · calls ${tools}`;
                } else {
                    oneLiner = `${input.toLocaleString()} in + ${output.toLocaleString()} out · final response`;
                }
            }
            return { title, oneLiner };
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
        case 'api_call':
            return renderAPICallData(event);
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

// Render API_CALL event data - the suitcase visualization
function renderAPICallData(event) {
    const d = event.data || {};
    const round = d.round_number || 1;
    const total = d.total_rounds || '?';
    const inputTokens = d.input_tokens || 0;
    const outputTokens = d.output_tokens || 0;
    const totalTokens = inputTokens + outputTokens;
    const breakdown = d.input_breakdown || [];
    const responseType = d.response_type || 'text';
    const preview = d.response_preview || '';
    const tools = d.tool_calls || [];
    const model = d.model || 'unknown';

    let html = '<div class="api-call-detail">';

    // Header with round info and model
    html += `<div class="api-call-header">`;
    html += `<span class="round-label">Round ${round} of ${total}</span>`;
    html += `<span class="model-label">${escapeHtml(model)}</span>`;
    html += `</div>`;

    // === INPUT SECTION (the suitcase) ===
    html += `<div class="suitcase">`;
    html += `<div class="suitcase-header">`;
    html += `<span class="suitcase-title">Packed into this call</span>`;
    html += `<span class="suitcase-total">${inputTokens.toLocaleString()} tokens</span>`;
    html += `</div>`;

    // Breakdown items
    html += `<div class="suitcase-contents">`;
    for (const item of breakdown) {
        if (item.is_real) {
            // This is the "ACTUAL TOTAL" line — render as the verified total
            html += `<div class="suitcase-item suitcase-actual-total">`;
            html += `<span class="item-label">${escapeHtml(item.label)}</span>`;
            html += `<span class="item-tokens real">${item.tokens.toLocaleString()}</span>`;
            html += `</div>`;
        } else {
            const tokStr = item.tokens_est != null
                ? `~${item.tokens_est.toLocaleString()}`
                : '';
            html += `<div class="suitcase-item">`;
            html += `<span class="item-label">${escapeHtml(item.label)}</span>`;
            html += `<span class="item-tokens est">${tokStr}</span>`;
            if (item.note) {
                html += `<span class="item-note">${escapeHtml(item.note)}</span>`;
            }
            html += `</div>`;
        }
    }
    html += `</div>`; // suitcase-contents
    html += `</div>`; // suitcase

    // === OUTPUT SECTION (what came back) ===
    html += `<div class="api-response-section">`;
    html += `<div class="response-header">`;
    if (responseType === 'tool_call') {
        html += `<span class="response-title">LLM decided to use tools</span>`;
        html += `<span class="response-tokens">${outputTokens.toLocaleString()} tokens</span>`;
    } else {
        html += `<span class="response-title">LLM responded</span>`;
        html += `<span class="response-tokens">${outputTokens.toLocaleString()} tokens</span>`;
    }
    html += `</div>`;

    // Tool calls list
    if (tools.length > 0) {
        html += `<div class="tool-call-list">`;
        tools.forEach(t => {
            html += `<span class="tool-call-chip">${escapeHtml(t)}</span>`;
        });
        html += `</div>`;
    }

    // Response preview
    if (preview) {
        html += `<div class="response-preview">${escapeHtml(preview)}</div>`;
    }
    html += `</div>`; // api-response-section

    // === COST SUMMARY for this round ===
    html += `<div class="round-cost-summary">`;
    html += `<div class="cost-row">`;
    html += `<span class="cost-label">This round</span>`;
    html += `<span class="cost-value">${inputTokens.toLocaleString()} in + ${outputTokens.toLocaleString()} out = <strong>${totalTokens.toLocaleString()}</strong></span>`;
    html += `</div>`;
    html += `</div>`;

    html += `</div>`; // api-call-detail
    return html;
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

// ============================================================
// NARRATIVE TIMELINE - Step-by-step view with explanations
// ============================================================

// Render narrative timeline (new format) or fall back to legacy
function renderNarrativeTimeline(events, session) {
    const hasApiCalls = events.some(e => e.event_type === 'api_call');
    if (!hasApiCalls) {
        // Fall back to legacy rendering for old log files
        return renderTimeline(events);
    }

    const steps = groupEventsIntoSteps(events);
    let html = '<div class="narrative-timeline">';

    for (const step of steps) {
        html += renderNarrativeStep(step, session);
    }

    html += '</div>';
    return html;
}

// Group flat events into narrative steps
function groupEventsIntoSteps(events) {
    const steps = [];

    // Gather preparation events
    const prepEvents = events.filter(e =>
        ['prompt_composed', 'tool_registered', 'skill_loaded'].includes(e.event_type)
    );

    // Gather API calls in order
    const apiCalls = events.filter(e => e.event_type === 'api_call')
        .sort((a, b) => (a.data.round_number || 0) - (b.data.round_number || 0));

    // Gather tool executions in order
    const toolExecs = events.filter(e => e.event_type === 'tool_called');

    // STEP 1: Preparation (always first)
    if (prepEvents.length > 0) {
        const promptEvent = prepEvents.find(e => e.event_type === 'prompt_composed');
        const toolRegs = prepEvents.filter(e => e.event_type === 'tool_registered');
        const skillLoads = prepEvents.filter(e => e.event_type === 'skill_loaded');

        steps.push({
            type: 'preparation',
            stepNumber: 1,
            events: prepEvents,
            promptEvent,
            toolRegs,
            skillLoads,
        });
    }

    // Interleave API calls and tool executions
    let toolExecIndex = 0;
    let stepNumber = 2;
    let prevInputTokens = null;

    for (let i = 0; i < apiCalls.length; i++) {
        const apiCall = apiCalls[i];
        const isLast = (i === apiCalls.length - 1);
        const isFirst = (i === 0);
        const inputGrowth = prevInputTokens ? (apiCall.data.input_tokens - prevInputTokens) : null;

        // API Call step
        steps.push({
            type: 'api_call',
            stepNumber: stepNumber++,
            event: apiCall,
            roundNumber: apiCall.data.round_number,
            totalRounds: apiCall.data.total_rounds,
            isFirst,
            isLast,
            inputGrowth,
            prevInputTokens,
        });

        prevInputTokens = apiCall.data.input_tokens;

        // If this API call triggered tools (not the last round), add tool execution step
        if (!isLast && apiCall.data.response_type === 'tool_call') {
            const toolNames = apiCall.data.tool_calls || [];
            const matchedTools = [];
            for (const name of toolNames) {
                if (toolExecIndex < toolExecs.length) {
                    matchedTools.push(toolExecs[toolExecIndex]);
                    toolExecIndex++;
                }
            }

            steps.push({
                type: 'tool_execution',
                stepNumber: stepNumber++,
                events: matchedTools,
                toolNames: toolNames,
                resultTokensEst: matchedTools.reduce((sum, t) =>
                    sum + (t.data?.result_tokens || 0), 0),
            });
        }
    }

    // FINAL: Total cost summary
    const totalInput = apiCalls.reduce((sum, e) => sum + (e.data.input_tokens || 0), 0);
    const totalOutput = apiCalls.reduce((sum, e) => sum + (e.data.output_tokens || 0), 0);
    const totalCalls = apiCalls.length;

    steps.push({
        type: 'total_cost',
        stepNumber: stepNumber,
        totalInput,
        totalOutput,
        totalCalls,
        totalTokens: totalInput + totalOutput,
    });

    return steps;
}

// Dispatch to step-specific renderer
function renderNarrativeStep(step, session) {
    switch (step.type) {
        case 'preparation': return renderPreparationStep(step, session);
        case 'api_call': return renderApiCallStep(step);
        case 'tool_execution': return renderToolExecutionStep(step);
        case 'total_cost': return renderTotalCostStep(step);
        default: return '';
    }
}

// STEP: Preparation - what was packed into the suitcase
function renderPreparationStep(step, session) {
    const prompt = step.promptEvent;
    const skills = prompt?.data?.skills_included || [];
    const skillCount = skills.length;
    const skillList = skills.join(', ');
    const promptTokens = prompt?.token_count || 0;
    const toolRegs = step.toolRegs || [];
    const toolNames = toolRegs.map(t => t.data?.tool_name).filter(Boolean);
    const toolTokens = toolRegs.reduce((sum, t) => sum + (t.token_count || 0), 0);
    const historyTokens = session?.conversation_history_tokens || 0;
    const isFirstQuery = (session?.sequence || 1) === 1;

    let html = '<div class="narrative-step preparation-step">';
    html += `<div class="step-header">`;
    html += `<span class="step-number">STEP ${step.stepNumber}</span>`;
    html += `<span class="step-title">Preparation</span>`;
    html += `</div>`;

    html += `<div class="step-explanation">`;
    html += `<p>Your code packed a suitcase with everything Claude might need:</p>`;
    html += `<div class="pack-list">`;

    // Skills
    html += `<div class="pack-item">`;
    html += `<span class="pack-icon">📚</span>`;
    html += `<div class="pack-detail">`;
    html += `<span class="pack-label">${skillCount} skill instruction${skillCount !== 1 ? 's' : ''}</span>`;
    html += `<span class="pack-desc">${skillList}</span>`;
    html += `<span class="pack-tokens">~${promptTokens.toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `</div>`;

    // Tools
    if (toolNames.length > 0) {
        html += `<div class="pack-item">`;
        html += `<span class="pack-icon">🔧</span>`;
        html += `<div class="pack-detail">`;
        html += `<span class="pack-label">${toolNames.length} tool definition${toolNames.length > 1 ? 's' : ''}</span>`;
        html += `<span class="pack-desc">${toolNames.join(', ')}</span>`;
        html += `<span class="pack-tokens">~${toolTokens.toLocaleString()} tokens</span>`;
        html += `</div>`;
        html += `</div>`;
    }

    // Conversation history (if Query 2+)
    if (!isFirstQuery && historyTokens > 0) {
        html += `<div class="pack-item history-item">`;
        html += `<span class="pack-icon">📜</span>`;
        html += `<div class="pack-detail">`;
        html += `<span class="pack-label">Conversation history</span>`;
        html += `<span class="pack-desc">Everything from earlier queries gets re-sent every time</span>`;
        html += `<span class="pack-tokens">~${historyTokens.toLocaleString()} tokens</span>`;
        html += `</div>`;
        html += `</div>`;
    }

    // User's question
    html += `<div class="pack-item">`;
    html += `<span class="pack-icon">💬</span>`;
    html += `<div class="pack-detail">`;
    html += `<span class="pack-label">Your question</span>`;
    html += `<span class="pack-desc">"${escapeHtml((session?.query_text || '').substring(0, 80))}${(session?.query_text?.length || 0) > 80 ? '...' : ''}"</span>`;
    html += `</div>`;
    html += `</div>`;

    html += `</div>`; // pack-list

    // Monolith tax callout
    html += `<div class="insight-callout">`;
    html += `<strong>Level 1 monolith tax:</strong> All ${skillCount} skills are loaded into every query, even if only one is needed. `;
    html += `Level 2 will improve this — loading only relevant skills on demand.`;
    html += `</div>`;

    html += `</div>`; // step-explanation
    html += `</div>`; // narrative-step

    return html;
}

// STEP: API Call - one round-trip to Claude
function renderApiCallStep(step) {
    const d = step.event.data;
    const inputTokens = d.input_tokens || 0;
    const outputTokens = d.output_tokens || 0;
    const totalRounds = d.total_rounds || 1;
    const isToolCall = d.response_type === 'tool_call';
    const tools = d.tool_calls || [];
    const preview = d.response_preview || '';
    const duration = step.event.duration_ms;

    // Determine the narrative
    let stepTitle, explanation;

    if (totalRounds === 1) {
        stepTitle = 'Sent to Claude';
        explanation = `Claude received the suitcase (${inputTokens.toLocaleString()} tokens), read everything, and responded directly.`;
    } else if (step.isFirst && isToolCall) {
        stepTitle = `Sent to Claude (Round ${step.roundNumber} of ${totalRounds})`;
        explanation = `Claude received the suitcase (${inputTokens.toLocaleString()} tokens), read everything, and decided it needs more data before answering.`;
    } else if (!step.isLast && isToolCall) {
        stepTitle = `Sent to Claude again (Round ${step.roundNumber} of ${totalRounds})`;
        let growthNote = '';
        if (step.inputGrowth) {
            growthNote = ` Input grew from ${step.prevInputTokens.toLocaleString()} → ${inputTokens.toLocaleString()} (+${step.inputGrowth.toLocaleString()}) because the tool result was added.`;
        }
        explanation = `Claude received the updated suitcase with previous tool results.${growthNote} Claude decided it needs even more data.`;
    } else {
        stepTitle = totalRounds > 1
            ? `Sent to Claude again (Round ${step.roundNumber} of ${totalRounds})`
            : 'Sent to Claude';
        let growthNote = '';
        if (step.inputGrowth) {
            growthNote = ` Input grew from ${step.prevInputTokens.toLocaleString()} → ${inputTokens.toLocaleString()} (+${step.inputGrowth.toLocaleString()}) because tool results were added.`;
        }
        explanation = `Claude received the final suitcase with all tool results.${growthNote} Claude wrote the response.`;
    }

    let html = '<div class="narrative-step api-call-step">';
    html += `<div class="step-header">`;
    html += `<span class="step-number">STEP ${step.stepNumber}</span>`;
    html += `<span class="step-title">${stepTitle}</span>`;
    if (duration) {
        html += `<span class="step-duration">${(duration / 1000).toFixed(1)}s</span>`;
    }
    html += `</div>`;

    html += `<div class="step-explanation">`;
    html += `<p>${explanation}</p>`;

    // Cost box
    html += `<div class="cost-box">`;
    html += `<div class="cost-line">`;
    html += `<span class="cost-direction">Sent to Claude</span>`;
    html += `<span class="cost-amount">${inputTokens.toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `<div class="cost-line">`;
    html += `<span class="cost-direction">${isToolCall ? "Claude's decision" : "Claude's response"}</span>`;
    html += `<span class="cost-amount">${outputTokens.toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `<div class="cost-line cost-subtotal">`;
    html += `<span class="cost-direction">Round subtotal</span>`;
    html += `<span class="cost-amount">${(inputTokens + outputTokens).toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `</div>`; // cost-box

    // What Claude did
    if (isToolCall && tools.length > 0) {
        html += `<div class="claude-action tool-action">`;
        html += `<strong>Claude decided:</strong> "I need to call `;
        html += tools.map(t => `<code>${escapeHtml(t)}</code>`).join(' and ');
        html += ` to get the data I need."`;
        html += `</div>`;
    } else if (preview) {
        html += `<div class="claude-action text-action">`;
        html += `<strong>Claude responded:</strong>`;
        html += `<div class="claude-preview">${escapeHtml(preview.substring(0, 300))}${preview.length > 300 ? '...' : ''}</div>`;
        html += `</div>`;
    }

    // Expandable: raw suitcase breakdown
    const breakdown = d.input_breakdown || [];
    if (breakdown.length > 0) {
        html += `<details class="breakdown-details">`;
        html += `<summary>View suitcase contents breakdown</summary>`;
        html += `<div class="suitcase-contents">`;
        for (const item of breakdown) {
            if (item.is_real) {
                html += `<div class="suitcase-item suitcase-actual-total">`;
                html += `<span class="item-label">✓ Verified total from API</span>`;
                html += `<span class="item-tokens real">${item.tokens.toLocaleString()}</span>`;
                html += `</div>`;
            } else {
                const tokStr = item.tokens_est != null ? `~${item.tokens_est.toLocaleString()}` : '—';
                html += `<div class="suitcase-item">`;
                html += `<span class="item-label">${escapeHtml(item.label)}</span>`;
                html += `<span class="item-tokens est">${tokStr}</span>`;
                html += `</div>`;
            }
        }
        html += `</div>`;
        html += `</details>`;
    }

    html += `</div>`; // step-explanation
    html += `</div>`; // narrative-step

    return html;
}

// STEP: Tool Execution - your code ran the tool
function renderToolExecutionStep(step) {
    const events = step.events || [];

    let html = '<div class="narrative-step tool-step">';
    html += `<div class="step-header">`;
    html += `<span class="step-number">STEP ${step.stepNumber}</span>`;
    html += `<span class="step-title">Your code ran the tool</span>`;
    html += `</div>`;

    html += `<div class="step-explanation">`;
    html += `<p>Claude can't fetch data itself — it asks your code to do it. Your code executed the tool and got results back.</p>`;

    for (const toolEvent of events) {
        const td = toolEvent.data || {};
        const name = td.tool_name || 'unknown';
        const params = td.parameters || {};
        const result = td.result_summary || '';
        const resultTokens = td.result_tokens;
        const dur = toolEvent.duration_ms;

        html += `<div class="tool-exec-card">`;
        html += `<div class="tool-exec-name"><code>${escapeHtml(name)}</code>`;
        if (dur != null) html += `<span class="tool-exec-duration">${dur}ms</span>`;
        html += `</div>`;

        // Parameters
        if (Object.keys(params).length > 0) {
            html += `<div class="tool-exec-params">`;
            for (const [key, val] of Object.entries(params)) {
                html += `<span class="param-pair"><em>${escapeHtml(key)}:</em> ${escapeHtml(String(val).substring(0, 80))}</span>`;
            }
            html += `</div>`;
        }

        // Result preview
        if (result) {
            html += `<div class="tool-exec-result">`;
            html += `<span class="result-label">Returned:</span> ${escapeHtml(result.substring(0, 200))}`;
            html += `</div>`;
        }

        // Token impact
        if (resultTokens) {
            html += `<div class="tool-token-impact">`;
            html += `This result adds ~${resultTokens.toLocaleString()} tokens to the next suitcase.`;
            html += `</div>`;
        }

        html += `</div>`; // tool-exec-card
    }

    html += `</div>`; // step-explanation
    html += `</div>`; // narrative-step

    return html;
}

// STEP: Total Cost Summary
function renderTotalCostStep(step) {
    let html = '<div class="narrative-step total-cost-step">';
    html += `<div class="step-header">`;
    html += `<span class="step-title">Total Cost</span>`;
    html += `</div>`;

    html += `<div class="total-cost-box">`;
    html += `<div class="total-cost-main">`;
    html += `<span class="total-number">${step.totalTokens.toLocaleString()}</span>`;
    html += `<span class="total-label">tokens</span>`;
    html += `</div>`;

    html += `<div class="total-cost-breakdown">`;
    html += `<div class="total-line">`;
    html += `<span>${step.totalCalls} API call${step.totalCalls > 1 ? 's' : ''}</span>`;
    html += `</div>`;
    html += `<div class="total-line">`;
    html += `<span>Sent to Claude: ${step.totalInput.toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `<div class="total-line">`;
    html += `<span>Claude's responses: ${step.totalOutput.toLocaleString()} tokens</span>`;
    html += `</div>`;
    html += `</div>`;

    // Insight about where cost lives
    if (step.totalInput > 0 && step.totalOutput > 0) {
        const inputPct = Math.round((step.totalInput / step.totalTokens) * 100);
        html += `<div class="insight-callout">`;
        html += `<strong>${inputPct}% of the cost</strong> is sending data TO Claude, not Claude's response. `;
        if (step.totalCalls > 1) {
            html += `With ${step.totalCalls} rounds, the system prompt and history were re-sent ${step.totalCalls} times.`;
        }
        html += `</div>`;
    }

    html += `</div>`; // total-cost-box
    html += `</div>`; // narrative-step

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
