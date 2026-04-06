/**
 * Electronic Voting System JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    initVoteForm();
    initCreateVoteForm();
    initResultsForm();
    initAddOptionButton();
});

/**
 * Vote form handling
 */
function initVoteForm() {
    const form = document.getElementById('vote-form');
    if (!form) return;

    // This handler is now disabled - voting is handled by inline script in vote.html
    // which has the correct N1/N2 code handling and rating vote support
    console.log('scripts.js initVoteForm: Using inline handler from vote.html instead');
}

/**
 * Create vote form handling
 */
function initCreateVoteForm() {
    const form = document.getElementById('create-vote-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        const options = [];
        form.querySelectorAll('input[name="options[]"]').forEach(input => {
            if (input.value.trim()) {
                options.push(input.value.trim());
            }
        });

        const data = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            options: options,
            creator_email: document.getElementById('creator-email').value.trim(),
            start_date: document.getElementById('start-date').value || null,
            end_date: document.getElementById('end-date').value || null
        };

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';

        try {
            const response = await fetch('/api/votes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                // Show success message
                form.classList.add('hidden');
                document.getElementById('create-result').classList.remove('hidden');
                document.getElementById('result-vote-id').textContent = result.vote_id;
                document.getElementById('result-creator-code').textContent = result.creator_code;
                document.getElementById('result-private-key').value = result.private_key;
            } else {
                alert(result.error || 'Failed to create vote');
            }
        } catch (error) {
            alert('Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Vote';
        }
    });
}

/**
 * Results form handling
 */
function initResultsForm() {
    const form = document.getElementById('results-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const voteId = form.dataset.voteId;
        const creatorCode = document.getElementById('creator-code').value.trim();
        const privateKey = document.getElementById('private-key').value.trim();

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Decrypting...';

        try {
            const response = await fetch(`/api/votes/${voteId}/results`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    creator_code: creatorCode,
                    private_key: privateKey
                })
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data);
                document.getElementById('results-form-container').classList.add('hidden');
                document.getElementById('results-display').classList.remove('hidden');
            } else {
                alert(data.error || 'Failed to get results');
            }
        } catch (error) {
            alert('Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Decrypt & View Results';
        }
    });
}

/**
 * Display vote results
 */
function displayResults(data) {
    document.getElementById('total-votes').textContent = data.total_votes;

    const chartContainer = document.getElementById('results-chart');
    chartContainer.innerHTML = '';

    const results = data.results;
    const maxVotes = Math.max(...Object.values(results));

    for (const [option, count] of Object.entries(results)) {
        const percentage = maxVotes > 0 ? (count / maxVotes) * 100 : 0;

        const bar = document.createElement('div');
        bar.className = 'result-bar';
        bar.innerHTML = `
            <div class="result-label">${option}</div>
            <div class="result-bar-bg">
                <div class="result-bar-fill" style="width: ${percentage}%">
                    ${count > 0 ? `<span class="result-count">${count}</span>` : ''}
                </div>
            </div>
        `;
        chartContainer.appendChild(bar);
    }
}

/**
 * Add option button in create vote form
 */
function initAddOptionButton() {
    const addBtn = document.getElementById('add-option');
    if (!addBtn) return;

    addBtn.addEventListener('click', function() {
        const container = document.getElementById('options-container');
        const optionCount = container.children.length + 1;

        if (optionCount > 10) {
            alert('Maximum 10 options allowed');
            return;
        }

        const optionDiv = document.createElement('div');
        optionDiv.className = 'option-input';
        optionDiv.innerHTML = `
            <input type="text" name="options[]" required placeholder="Option ${optionCount}">
            <button type="button" class="remove-option" onclick="removeOption(this)">×</button>
        `;
        container.appendChild(optionDiv);
    });
}

/**
 * Remove option button handler
 */
function removeOption(btn) {
    const container = document.getElementById('options-container');
    if (container.children.length <= 2) {
        alert('Minimum 2 options required');
        return;
    }
    btn.parentElement.remove();
}

/**
 * Copy private key to clipboard
 */
function copyPrivateKey() {
    const textarea = document.getElementById('result-private-key');
    textarea.select();
    document.execCommand('copy');
    alert('Private key copied to clipboard!');
}

/**
 * Fetch and display votes dynamically
 */
async function loadVotes() {
    try {
        const response = await fetch('/api/votes');
        const votes = await response.json();

        const grid = document.getElementById('vote-grid');
        if (!grid) return;

        if (votes.length === 0) {
            grid.innerHTML = `
                <div class="no-votes">
                    <p>No active votes at the moment.</p>
                    <a href="/create-vote" class="btn btn-primary">Create a Vote</a>
                </div>
            `;
            return;
        }

        grid.innerHTML = votes.map(vote => `
            <div class="vote-card" data-vote-id="${vote.id}">
                <div class="vote-card-header">
                    <h3>${vote.title}</h3>
                    <span class="vote-status ${vote.is_active ? 'active' : 'ended'}">
                        ${vote.is_active ? 'Active' : 'Ended'}
                    </span>
                </div>
                <div class="vote-card-body">
                    <p class="vote-description">${vote.description || ''}</p>
                    <div class="vote-dates">
                        <small>Starts: ${vote.start_date ? new Date(vote.start_date).toLocaleString() : 'N/A'}</small>
                        <small>Ends: ${vote.end_date ? new Date(vote.end_date).toLocaleString() : 'N/A'}</small>
                    </div>
                </div>
                <div class="vote-card-footer">
                    <a href="/vote/${vote.id}" class="btn btn-primary">Vote Now</a>
                    <a href="/results/${vote.id}" class="btn btn-secondary">View Results</a>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load votes:', error);
    }
}

// Load votes on page load if on index page
if (document.getElementById('vote-grid')) {
    loadVotes();
}
