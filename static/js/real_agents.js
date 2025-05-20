// MCP Multi-Agent Hub - Real Agents JavaScript

// DOM elements
const realAgentForm = document.getElementById('real-agent-form');
const realQuestionInput = document.getElementById('real-question-input');
const useMockAgentsCheckbox = document.getElementById('use-mock-agents');
const realQuestionsList = document.getElementById('real-questions-list');
const realContextContainer = document.getElementById('real-context-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorAlert = document.getElementById('error-alert');
const errorMessage = document.getElementById('error-message');
const refreshButton = document.getElementById('refresh-button');
const processingProgress = document.getElementById('processing-progress');
const progressBar = document.getElementById('progress-bar');

// Global state
let currentQuestionId = null;
let pollingInterval = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Load questions list on start
    loadQuestionsList();
    
    // Set up event listeners
    setupEventListeners();
});

// Set up event listeners
function setupEventListeners() {
    // Real agent form submission
    realAgentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = realQuestionInput.value.trim();
        const useMockAgents = useMockAgentsCheckbox.checked;
        
        if (question) {
            await submitRealAgentQuestion(question, !useMockAgents);
            realQuestionInput.value = '';
        }
    });
    
    // Refresh button
    refreshButton.addEventListener('click', () => {
        if (currentQuestionId) {
            loadQuestionContext(currentQuestionId);
        } else {
            loadQuestionsList();
        }
    });
}

// Load the list of questions from the server
async function loadQuestionsList() {
    showLoading(true);
    try {
        const response = await fetch('/questions');
        if (!response.ok) throw new Error('Failed to load questions');
        
        const questions = await response.json();
        renderQuestionsList(questions);
        showLoading(false);
    } catch (error) {
        showError('Error loading questions: ' + error.message);
        showLoading(false);
    }
}

// Render the list of questions
function renderQuestionsList(questions) {
    realQuestionsList.innerHTML = '';
    
    if (Object.keys(questions).length === 0) {
        realQuestionsList.innerHTML = `
            <div class="alert alert-info">
                No questions yet. Submit a question to get started.
            </div>
        `;
        return;
    }
    
    // Sort questions by timestamp (newest first)
    const sortedQuestions = Object.entries(questions)
        .map(([id, q]) => ({ id, ...q }))
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    sortedQuestions.forEach(question => {
        const questionElement = document.createElement('div');
        questionElement.className = 'card mb-3 fade-in';
        questionElement.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${escapeHtml(question.text)}</h5>
                <p class="card-text text-muted">
                    <small>Created: ${formatDateTime(question.timestamp)}</small>
                </p>
                <div class="d-flex justify-content-between">
                    <button class="btn btn-primary btn-sm view-btn" data-id="${question.id}">
                        View Context
                    </button>
                    <button class="btn btn-outline-danger btn-sm delete-btn" data-id="${question.id}">
                        Delete
                    </button>
                </div>
            </div>
        `;
        
        realQuestionsList.appendChild(questionElement);
        
        // Add event listeners to the buttons
        questionElement.querySelector('.view-btn').addEventListener('click', () => {
            loadQuestionContext(question.id);
        });
        
        questionElement.querySelector('.delete-btn').addEventListener('click', () => {
            deleteQuestion(question.id);
        });
    });
}

// Submit a new question to real agents
async function submitRealAgentQuestion(questionText, useRealAgents) {
    showLoading(true);
    try {
        const response = await fetch('/api/real-agents/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                question: questionText,
                use_real_agents: useRealAgents
            }),
        });
        
        if (!response.ok) throw new Error('Failed to submit question to real agents');
        
        const result = await response.json();
        showMessage(`Question submitted to ${useRealAgents ? 'real' : 'mock'} AI agents!`, 'success');
        
        // Load the new question context
        currentQuestionId = result.question_id;
        showProgressIndicator();
        startProgressPolling(result.question_id);
        
    } catch (error) {
        showError('Error submitting question: ' + error.message);
        showLoading(false);
    }
}

// Show the progress indicator
function showProgressIndicator() {
    // Hide the welcome content and show the progress indicator
    realContextContainer.querySelector('.text-center').style.display = 'none';
    processingProgress.style.display = 'block';
    updateProgress(0);
}

// Update the progress bar
function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    progressBar.textContent = `${percent}%`;
}

// Start polling for progress updates
function startProgressPolling(questionId) {
    // Clear any existing polling interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Set up polling to check progress every 2 seconds
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/real-agents/status/${questionId}`);
            if (!response.ok) throw new Error('Failed to check progress');
            
            const status = await response.json();
            
            // Update progress based on status
            updateProgress(status.progress);
            
            // If processing is complete, load the context and stop polling
            if (status.status === 'complete') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                loadQuestionContext(questionId);
            }
        } catch (error) {
            console.error('Error checking progress:', error);
        }
    }, 2000);
}

// Load the context for a specific question
async function loadQuestionContext(questionId) {
    showLoading(true);
    currentQuestionId = questionId;
    
    // Clear any existing polling interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    
    try {
        const response = await fetch(`/context/${questionId}`);
        if (!response.ok) throw new Error('Failed to load context');
        
        const context = await response.json();
        renderQuestionContext(context);
        
        showLoading(false);
    } catch (error) {
        showError('Error loading context: ' + error.message);
        showLoading(false);
    }
}

// Delete a question
async function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to delete this question?')) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(`/question/${questionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete question');
        
        showMessage('Question deleted successfully!', 'success');
        
        // If we're viewing the deleted question, go back to the list
        if (currentQuestionId === questionId) {
            currentQuestionId = null;
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }
        
        loadQuestionsList();
    } catch (error) {
        showError('Error deleting question: ' + error.message);
        showLoading(false);
    }
}

// Render the context for a question
function renderQuestionContext(context) {
    realContextContainer.innerHTML = '';
    processingProgress.style.display = 'none';
    
    // Question header
    const questionHeader = document.createElement('div');
    questionHeader.className = 'mb-4';
    questionHeader.innerHTML = `
        <h2 class="mb-3">Question</h2>
        <div class="card">
            <div class="card-body">
                <h3 class="card-title">${escapeHtml(context.question_text)}</h3>
                <p class="text-muted">
                    <small>ID: ${context.question_id}</small><br>
                    <small>Created: ${formatDateTime(context.timestamp)}</small>
                </p>
                <button id="back-button" class="btn btn-secondary">
                    <i class="bi bi-arrow-left"></i> Back to Questions
                </button>
            </div>
        </div>
    `;
    
    realContextContainer.appendChild(questionHeader);
    
    // Add event listener to back button
    document.getElementById('back-button').addEventListener('click', () => {
        currentQuestionId = null;
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        loadQuestionsList();
    });
    
    // Responses section
    if (Object.keys(context.responses).length > 0) {
        renderStageSection('Responses', context.responses, 'info');
    }
    
    // Critiques section
    if (Object.keys(context.critiques).length > 0) {
        renderStageSection('Critiques', context.critiques, 'warning');
    }
    
    // Research section
    if (Object.keys(context.research).length > 0) {
        renderStageSection('Research', context.research, 'success');
    }
    
    // Conclusions section
    if (Object.keys(context.conclusions).length > 0) {
        renderStageSection('Conclusions', context.conclusions, 'danger');
    }
}

// Render a section for a specific stage (responses, critiques, etc.)
function renderStageSection(title, items, colorClass) {
    const section = document.createElement('div');
    section.className = 'mb-4 fade-in';
    
    let sectionHTML = `
        <h2 class="mb-3">${title}</h2>
        <div class="timeline">
    `;
    
    Object.entries(items).forEach(([agentId, data]) => {
        // Different rendering for critiques which have a nested structure
        if (title === 'Critiques') {
            if (typeof data === 'object' && data !== null) {
                Object.entries(data).forEach(([targetId, critique]) => {
                    const agentInitial = agentId.split('-')[1]?.charAt(0).toUpperCase() || 'A';
                    const agentClass = `agent-${agentId.split('-')[1] || 'default'}`;
                    
                    sectionHTML += renderCritiqueCard(agentInitial, agentClass, colorClass, critique, data.agent_name || agentId);
                });
            }
        } else {
            // Rendering for responses, research, conclusions
            const agentInitial = agentId.split('-')[1]?.charAt(0).toUpperCase() || 'A';
            const agentClass = `agent-${agentId.split('-')[1] || 'default'}`;
            
            sectionHTML += renderAgentCard(title, agentInitial, agentClass, colorClass, data, data.agent_name || agentId);
        }
    });
    
    sectionHTML += `</div>`;
    section.innerHTML = sectionHTML;
    realContextContainer.appendChild(section);
}

// Render a card for agent responses, research, or conclusions
function renderAgentCard(title, agentInitial, agentClass, colorClass, data, agentName) {
    let cardHTML = `
        <div class="timeline-item">
            <div class="card agent-card ${agentClass}">
                <div class="card-header d-flex align-items-center">
                    <div class="agent-avatar bg-${colorClass}">${agentInitial}</div>
                    <span class="fw-bold">${agentName}</span>
                    <span class="badge bg-${colorClass} ms-auto">${title.slice(0, -1)}</span>
                </div>
                <div class="card-body">
    `;
    
    // Different rendering based on stage
    if (title === 'Responses') {
        cardHTML += `
            <p class="mb-2"><strong>Model:</strong> ${data.model || 'Unknown'}</p>
            <p>${escapeHtml(data.content || '')}</p>
            <hr>
            <div class="d-flex justify-content-between">
                <small class="text-muted">Confidence: ${data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A'}</small>
                <small class="text-muted">Reasoning: ${escapeHtml(data.reasoning || '')}</small>
            </div>
        `;
    } else if (title === 'Research') {
        cardHTML += `
            <p class="mb-2"><strong>Model:</strong> ${data.model || 'Unknown'}</p>
            <p>${escapeHtml(data.findings || '')}</p>
            <hr>
            <strong>Sources:</strong>
            <ul>
                ${(data.sources || []).map(source => 
                    `<li>${escapeHtml(source.title)} (${source.year}) - Relevance: ${(source.relevance * 100).toFixed(1)}%</li>`
                ).join('')}
            </ul>
            <p><small class="text-muted">Confidence: ${data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A'}</small></p>
        `;
    } else if (title === 'Conclusions') {
        cardHTML += `
            <p class="mb-2"><strong>Model:</strong> ${data.model || 'Unknown'}</p>
            <p>${escapeHtml(data.summary || '')}</p>
            <hr>
            <div>
                <strong>Key Takeaways:</strong>
                <ul>
                    ${(data.key_takeaways || []).map(takeaway => `<li>${escapeHtml(takeaway)}</li>`).join('')}
                </ul>
            </div>
            <p>
                <small class="text-muted">Confidence: ${data.confidence ? (data.confidence * 100).toFixed(1) + '%' : 'N/A'}</small><br>
                <small class="text-muted">Final Position: ${data.final_position || 'N/A'}</small>
            </p>
        `;
    }
    
    cardHTML += `
                </div>
            </div>
        </div>
    `;
    
    return cardHTML;
}

// Render a card for agent critiques
function renderCritiqueCard(agentInitial, agentClass, colorClass, data, agentName) {
    return `
        <div class="timeline-item">
            <div class="card agent-card ${agentClass}">
                <div class="card-header d-flex align-items-center">
                    <div class="agent-avatar bg-${colorClass}">${agentInitial}</div>
                    <span class="fw-bold">${agentName}</span>
                    <span class="badge bg-${colorClass} ms-auto">Critique</span>
                </div>
                <div class="card-body">
                    <p class="mb-2"><strong>Model:</strong> ${data.model || 'Unknown'}</p>
                    <p><strong>Target Agent:</strong> ${data.target_agent || 'Unknown'}</p>
                    <p>${escapeHtml(data.critique || '')}</p>
                    <p><strong>Agreement Level:</strong> ${data.agreement_level ? (data.agreement_level * 100).toFixed(1) + '%' : 'N/A'}</p>
                    <div class="mt-2">
                        <strong>Key Points:</strong>
                        <ul>
                            ${(data.key_points || []).map(point => `<li>${escapeHtml(point)}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Show loading spinner
function showLoading(show) {
    loadingSpinner.style.display = show ? 'block' : 'none';
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorAlert.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorAlert.style.display = 'none';
    }, 5000);
}

// Show message alert
function showMessage(message, type = 'info') {
    // Create or update message alert
    let messageAlert = document.getElementById('message-alert');
    if (!messageAlert) {
        messageAlert = document.createElement('div');
        messageAlert.id = 'message-alert';
        messageAlert.className = `alert alert-${type} alert-dismissible fade show`;
        messageAlert.setAttribute('role', 'alert');
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        
        messageAlert.appendChild(document.createTextNode(message));
        messageAlert.appendChild(closeButton);
        
        // Insert after error alert
        errorAlert.parentNode.insertBefore(messageAlert, errorAlert.nextSibling);
    } else {
        messageAlert.className = `alert alert-${type} alert-dismissible fade show`;
        messageAlert.textContent = message;
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        messageAlert.appendChild(closeButton);
    }
    
    // Hide after 5 seconds
    setTimeout(() => {
        messageAlert.style.display = 'none';
    }, 5000);
}

// Helper function to format datetime
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}