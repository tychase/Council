// MCP Multi-Agent Hub - Frontend JavaScript

// DOM elements
const questionForm = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const questionsList = document.getElementById('questions-list');
const contextContainer = document.getElementById('context-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorAlert = document.getElementById('error-alert');
const errorMessage = document.getElementById('error-message');
const refreshButton = document.getElementById('refresh-button');
const simulateButton = document.getElementById('simulate-button');

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
    // Question form submission
    questionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        
        if (question) {
            await submitQuestion(question);
            questionInput.value = '';
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
    
    // Simulate button
    simulateButton.addEventListener('click', async () => {
        showLoading(true);
        try {
            showMessage('Simulation has started. This may take a few moments...', 'info');
            
            // The actual simulation runs on the backend through agent_simulator.py
            // Here we just wait a moment and then refresh the questions list
            setTimeout(() => {
                loadQuestionsList();
                showLoading(false);
                showMessage('Simulation completed! Check the questions list for the new question.', 'success');
            }, 3000);
        } catch (error) {
            showError('Failed to start simulation: ' + error.message);
            showLoading(false);
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
    questionsList.innerHTML = '';
    
    if (Object.keys(questions).length === 0) {
        questionsList.innerHTML = `
            <div class="alert alert-info">
                No questions yet. Submit a question or run a simulation to get started.
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
        
        questionsList.appendChild(questionElement);
        
        // Add event listeners to the buttons
        questionElement.querySelector('.view-btn').addEventListener('click', () => {
            loadQuestionContext(question.id);
        });
        
        questionElement.querySelector('.delete-btn').addEventListener('click', () => {
            deleteQuestion(question.id);
        });
    });
}

// Submit a new question
async function submitQuestion(questionText) {
    showLoading(true);
    try {
        const response = await fetch('/question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ question_text: questionText }),
        });
        
        if (!response.ok) throw new Error('Failed to submit question');
        
        const result = await response.json();
        showMessage('Question submitted successfully!', 'success');
        
        // Load the new question context
        loadQuestionContext(result.question_id);
    } catch (error) {
        showError('Error submitting question: ' + error.message);
        showLoading(false);
    }
}

// Load the context for a specific question
async function loadQuestionContext(questionId) {
    showLoading(true);
    currentQuestionId = questionId;
    
    // Clear any existing polling interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    try {
        const response = await fetch(`/context/${questionId}`);
        if (!response.ok) throw new Error('Failed to load context');
        
        const context = await response.json();
        renderQuestionContext(context);
        
        // Set up polling to refresh the context every 5 seconds
        pollingInterval = setInterval(() => {
            refreshQuestionContext(questionId);
        }, 5000);
        
        showLoading(false);
    } catch (error) {
        showError('Error loading context: ' + error.message);
        showLoading(false);
    }
}

// Refresh the context for the current question
async function refreshQuestionContext(questionId) {
    try {
        const response = await fetch(`/context/${questionId}`);
        if (!response.ok) throw new Error('Failed to refresh context');
        
        const context = await response.json();
        renderQuestionContext(context, false); // Don't show loading spinner for refresh
    } catch (error) {
        console.error('Error refreshing context:', error);
        // Don't show error for background refresh
    }
}

// Render the context for a question
function renderQuestionContext(context, showLoadingSpinner = true) {
    if (showLoadingSpinner) {
        showLoading(true);
    }
    
    contextContainer.innerHTML = '';
    
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
    
    contextContainer.appendChild(questionHeader);
    
    // Add event listener to back button
    document.getElementById('back-button').addEventListener('click', () => {
        currentQuestionId = null;
        if (pollingInterval) {
            clearInterval(pollingInterval);
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
    
    if (showLoadingSpinner) {
        showLoading(false);
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
        const agentInitial = agentId.split('-')[1]?.charAt(0).toUpperCase() || 'A';
        const agentClass = `agent-${agentId.split('-')[1] || 'default'}`;
        
        sectionHTML += `
            <div class="timeline-item">
                <div class="card agent-card ${agentClass}">
                    <div class="card-header d-flex align-items-center">
                        <div class="agent-avatar bg-${colorClass}">${agentInitial}</div>
                        <span class="fw-bold">${data.agent_name || agentId}</span>
                        <span class="badge bg-${colorClass} ms-auto">${title.slice(0, -1)}</span>
                    </div>
                    <div class="card-body">
        `;
        
        // Different rendering based on stage
        if (title === 'Responses') {
            sectionHTML += `
                <p>${escapeHtml(data.content)}</p>
                <hr>
                <div class="d-flex justify-content-between">
                    <small class="text-muted">Confidence: ${(data.confidence * 100).toFixed(1)}%</small>
                    <small class="text-muted">Reasoning: ${escapeHtml(data.reasoning)}</small>
                </div>
            `;
        } else if (title === 'Critiques') {
            sectionHTML += `
                <p><strong>Target Agent:</strong> ${data.target_agent}</p>
                <p>${escapeHtml(data.critique)}</p>
                <p><strong>Agreement Level:</strong> ${(data.agreement_level * 100).toFixed(1)}%</p>
                <div class="mt-2">
                    <strong>Key Points:</strong>
                    <ul>
                        ${data.key_points.map(point => `<li>${escapeHtml(point)}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else if (title === 'Research') {
            sectionHTML += `
                <p>${escapeHtml(data.findings)}</p>
                <hr>
                <strong>Sources:</strong>
                <ul>
                    ${data.sources.map(source => 
                        `<li>${escapeHtml(source.title)} (${source.year}) - Relevance: ${(source.relevance * 100).toFixed(1)}%</li>`
                    ).join('')}
                </ul>
                <p><small class="text-muted">Confidence: ${(data.confidence * 100).toFixed(1)}%</small></p>
            `;
        } else if (title === 'Conclusions') {
            sectionHTML += `
                <p>${escapeHtml(data.summary)}</p>
                <hr>
                <div>
                    <strong>Key Takeaways:</strong>
                    <ul>
                        ${data.key_takeaways.map(takeaway => `<li>${escapeHtml(takeaway)}</li>`).join('')}
                    </ul>
                </div>
                <p>
                    <small class="text-muted">Confidence: ${(data.confidence * 100).toFixed(1)}%</small><br>
                    <small class="text-muted">Final Position: ${data.final_position}</small>
                </p>
            `;
        }
        
        sectionHTML += `
                    </div>
                </div>
            </div>
        `;
    });
    
    sectionHTML += `</div>`;
    section.innerHTML = sectionHTML;
    contextContainer.appendChild(section);
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
            }
        }
        
        loadQuestionsList();
    } catch (error) {
        showError('Error deleting question: ' + error.message);
        showLoading(false);
    }
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
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
