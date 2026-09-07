/**
 * Recoll Modern UI - Interactive Client Scripts
 * Vanilla JavaScript (Zero External Dependencies)
 */

document.addEventListener('DOMContentLoaded', () => {
    // Form submission loading fade
    const searchForms = document.querySelectorAll('form');
    const fadeOverlay = document.getElementById('fade');

    searchForms.forEach(form => {
        form.addEventListener('submit', () => {
            const inputs = form.querySelectorAll('input');
            inputs.forEach(input => input.blur());
            if (fadeOverlay) {
                fadeOverlay.style.display = 'block';
                fadeOverlay.style.opacity = '1';
            }
        });
    });

    // Keyboard navigation shortcuts
    document.addEventListener('keydown', (e) => {
        // Press '/' to focus search box when not typing in an input
        if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            const queryInput = document.querySelector('input[name="query"]');
            if (queryInput) {
                queryInput.focus();
                queryInput.select();
            }
        }
        // Press 'Escape' to blur active input
        if (e.key === 'Escape' && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            document.activeElement.blur();
        }
    });
});

/**
 * Interactive Mouse-Tracking Radial Card Glow
 * @param {MouseEvent} event
 * @param {HTMLElement} card
 */
function updateGlow(event, card) {
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    card.style.setProperty('--x', `${x}px`);
    card.style.setProperty('--y', `${y}px`);
}

/**
 * Add OpenSearch Provider to Browser
 */
function addOpenSearch() {
    if (window.external && 'AddSearchProvider' in window.external) {
        const url = window.location.origin + '/osd.xml';
        window.external.AddSearchProvider(url);
    } else {
        alert('OpenSearch plugins can be added automatically from your browser address bar.');
    }
}
