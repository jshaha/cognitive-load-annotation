/**
 * ReadingTracker - Tracks user reading behavior metrics
 */
class ReadingTracker {
    constructor() {
        this.startTime = Date.now();
        this.activeTime = 0;
        this.lastActiveTimestamp = Date.now();
        this.isActive = true;
        this.maxScrollDepth = 0;
        this.scrollBackCount = 0;
        this.lastScrollPosition = 0;
        this.pauseCount = 0;
        this.lastInteractionTime = Date.now();
        this.mouseDistance = 0;
        this.lastMousePosition = { x: 0, y: 0 };
        this.pauseTimer = null;
        this.PAUSE_THRESHOLD = 5000; // 5 seconds

        this.initListeners();
    }

    initListeners() {
        // Page visibility tracking
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());

        // Scroll tracking
        window.addEventListener('scroll', () => this.handleScroll(), { passive: true });

        // Mouse movement tracking
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e), { passive: true });

        // Interaction tracking for pause detection
        ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => this.handleInteraction(), { passive: true });
        });

        // Start pause detection
        this.startPauseDetection();
    }

    handleVisibilityChange() {
        if (document.hidden) {
            // Tab became inactive - save active time
            this.activeTime += Date.now() - this.lastActiveTimestamp;
            this.isActive = false;
        } else {
            // Tab became active
            this.lastActiveTimestamp = Date.now();
            this.isActive = true;
        }
    }

    handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const currentDepth = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;

        // Update max scroll depth
        if (currentDepth > this.maxScrollDepth) {
            this.maxScrollDepth = currentDepth;
        }

        // Detect scroll back (scrolling up more than 50px)
        if (scrollTop < this.lastScrollPosition - 50) {
            this.scrollBackCount++;
        }

        this.lastScrollPosition = scrollTop;
    }

    handleMouseMove(e) {
        const dx = e.clientX - this.lastMousePosition.x;
        const dy = e.clientY - this.lastMousePosition.y;
        this.mouseDistance += Math.sqrt(dx * dx + dy * dy);
        this.lastMousePosition = { x: e.clientX, y: e.clientY };
    }

    handleInteraction() {
        this.lastInteractionTime = Date.now();
    }

    startPauseDetection() {
        this.pauseTimer = setInterval(() => {
            const timeSinceInteraction = Date.now() - this.lastInteractionTime;
            if (timeSinceInteraction >= this.PAUSE_THRESHOLD && this.isActive) {
                this.pauseCount++;
                // Reset interaction time to avoid counting the same pause multiple times
                this.lastInteractionTime = Date.now();
            }
        }, this.PAUSE_THRESHOLD);
    }

    calculateMouseScore() {
        // Normalize mouse distance by time spent (pixels per second)
        const timeSpent = (Date.now() - this.startTime) / 1000;
        return timeSpent > 0 ? this.mouseDistance / timeSpent : 0;
    }

    getMetrics() {
        // Update active time if currently active
        let totalActiveTime = this.activeTime;
        if (this.isActive) {
            totalActiveTime += Date.now() - this.lastActiveTimestamp;
        }

        return {
            time_spent_seconds: (Date.now() - this.startTime) / 1000,
            active_time_seconds: totalActiveTime / 1000,
            scroll_depth_percent: Math.min(100, this.maxScrollDepth),
            scroll_back_count: this.scrollBackCount,
            pause_count: this.pauseCount,
            mouse_activity_score: Math.round(this.calculateMouseScore() * 100) / 100
        };
    }

    destroy() {
        if (this.pauseTimer) {
            clearInterval(this.pauseTimer);
        }
    }
}

/**
 * DifficultPassageTracker - Handles text highlighting for difficult passages
 */
class DifficultPassageTracker {
    constructor(articleElement) {
        this.articleElement = articleElement;
        this.passages = [];
        this.popup = document.getElementById('highlight-popup');
        this.markBtn = document.getElementById('mark-difficult-btn');
        this.passagesList = document.getElementById('difficult-passages-list');
        this.passagesUl = document.getElementById('passages-ul');
        this.currentSelection = null;

        this.initListeners();
    }

    initListeners() {
        // Show popup on text selection
        this.articleElement.addEventListener('mouseup', (e) => this.handleTextSelection(e));

        // Hide popup when clicking elsewhere
        document.addEventListener('mousedown', (e) => {
            if (!this.popup.contains(e.target) && e.target !== this.popup) {
                this.hidePopup();
            }
        });

        // Mark as difficult button
        this.markBtn.addEventListener('click', () => this.markDifficult());
    }

    handleTextSelection(e) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();

        if (selectedText.length > 0) {
            // Check if selection is within article
            const range = selection.getRangeAt(0);
            if (this.articleElement.contains(range.commonAncestorContainer)) {
                this.currentSelection = {
                    text: selectedText,
                    range: range.cloneRange()
                };

                // Position popup near selection
                const rect = range.getBoundingClientRect();
                this.popup.style.top = (rect.bottom + window.scrollY + 5) + 'px';
                this.popup.style.left = (rect.left + window.scrollX) + 'px';
                this.popup.classList.remove('hidden');
            }
        } else {
            this.hidePopup();
        }
    }

    hidePopup() {
        this.popup.classList.add('hidden');
        this.currentSelection = null;
    }

    markDifficult() {
        if (!this.currentSelection) return;

        const { text, range } = this.currentSelection;

        // Calculate offsets relative to article text
        const articleText = this.articleElement.textContent;
        const startOffset = this.getTextOffset(range.startContainer, range.startOffset);
        const endOffset = startOffset + text.length;

        // Add to passages array
        const passage = {
            text_content: text,
            start_offset: startOffset,
            end_offset: endOffset
        };
        this.passages.push(passage);

        // Highlight the text
        this.highlightRange(range);

        // Update UI
        this.updatePassagesList();

        // Hide popup and clear selection
        this.hidePopup();
        window.getSelection().removeAllRanges();
    }

    getTextOffset(node, offset) {
        // Calculate the text offset from the start of the article
        const walker = document.createTreeWalker(
            this.articleElement,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let totalOffset = 0;
        let currentNode;

        while (currentNode = walker.nextNode()) {
            if (currentNode === node) {
                return totalOffset + offset;
            }
            totalOffset += currentNode.textContent.length;
        }

        return totalOffset + offset;
    }

    highlightRange(range) {
        const span = document.createElement('span');
        span.className = 'difficult-text';
        range.surroundContents(span);
    }

    updatePassagesList() {
        if (this.passages.length === 0) {
            this.passagesList.classList.add('hidden');
            return;
        }

        this.passagesList.classList.remove('hidden');
        this.passagesUl.innerHTML = '';

        this.passages.forEach((passage, index) => {
            const li = document.createElement('li');
            const textSpan = document.createElement('span');
            textSpan.textContent = passage.text_content.length > 50
                ? passage.text_content.substring(0, 50) + '...'
                : passage.text_content;

            const removeBtn = document.createElement('span');
            removeBtn.className = 'remove-passage';
            removeBtn.textContent = '\u00d7';
            removeBtn.onclick = () => this.removePassage(index);

            li.appendChild(textSpan);
            li.appendChild(removeBtn);
            this.passagesUl.appendChild(li);
        });
    }

    removePassage(index) {
        this.passages.splice(index, 1);
        this.updatePassagesList();
        // Note: We don't remove the visual highlight as it would be complex
        // Users can see in the list which passages are still tracked
    }

    getPassages() {
        return this.passages;
    }
}

/**
 * RatingForm - Handles the rating form logic
 */
class RatingForm {
    constructor(formElement, tracker, passageTracker) {
        this.form = formElement;
        this.tracker = tracker;
        this.passageTracker = passageTracker;
        this.submitBtn = document.getElementById('submit-btn');
        this.submitHint = document.getElementById('submit-hint');
        this.sliders = this.form.querySelectorAll('.slider');
        this.touchedCount = 0;

        this.initSliders();
        this.initSubmit();
    }

    initSliders() {
        this.sliders.forEach(slider => {
            const valueDisplay = document.getElementById(slider.id + '_value');

            // Update value display
            slider.addEventListener('input', () => {
                valueDisplay.textContent = slider.value;

                // Mark as touched
                if (slider.dataset.touched !== 'true') {
                    slider.dataset.touched = 'true';
                    this.touchedCount++;
                    this.checkSubmitEnabled();
                }
            });
        });
    }

    checkSubmitEnabled() {
        const allTouched = this.touchedCount >= this.sliders.length;
        this.submitBtn.disabled = !allTouched;

        if (allTouched) {
            this.submitHint.classList.add('hidden');
        }
    }

    initSubmit() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (this.submitBtn.disabled) return;

            this.submitBtn.disabled = true;
            this.submitBtn.textContent = 'Submitting...';

            const metrics = this.tracker.getMetrics();
            const passages = this.passageTracker.getPassages();

            const data = {
                mental_effort_score: parseInt(document.getElementById('mental_effort').value),
                background_knowledge_score: parseInt(document.getElementById('background_knowledge').value),
                emotional_drain_score: parseInt(document.getElementById('emotional_drain').value),
                clarity_score: parseInt(document.getElementById('clarity').value),
                optional_comments: document.getElementById('comments').value,
                ...metrics,
                difficult_passages: passages
            };

            try {
                const response = await fetch(submitUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    window.location.href = result.redirect;
                } else {
                    alert('Error: ' + (result.error || 'Unknown error'));
                    this.submitBtn.disabled = false;
                    this.submitBtn.textContent = 'Submit Rating';
                }
            } catch (error) {
                console.error('Submit error:', error);
                alert('An error occurred while submitting. Please try again.');
                this.submitBtn.disabled = false;
                this.submitBtn.textContent = 'Submit Rating';
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const articleElement = document.getElementById('article-text');
    const formElement = document.getElementById('rating-form');

    if (articleElement && formElement) {
        const tracker = new ReadingTracker();
        const passageTracker = new DifficultPassageTracker(articleElement);
        const ratingForm = new RatingForm(formElement, tracker, passageTracker);

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            tracker.destroy();
        });
    }
});
