/* ============================================================================
   FUTURE HAUSE DASHBOARD — MINIMAL STATE TOGGLING
   ONLY for demo purposes — real state comes from backend
   ============================================================================ */

// Status language mapping (Phase 7)
const statusLanguage = {
  'pulse-slow': {
    headline: 'System Ready',
    description: 'All systems operational. Waiting for instructions.',
    action: 'Start Task',
    footerStatus: 'Operational'
  },
  'spin': {
    headline: 'Processing Request',
    description: 'Collecting and validating inputs. Please wait...',
    action: 'Cancel',
    footerStatus: 'Processing'
  },
  'glow': {
    headline: 'Task Complete',
    description: 'Operation completed successfully. Results are ready.',
    action: 'View Results',
    footerStatus: 'Success'
  },
  'shake': {
    headline: 'Attention Required',
    description: 'An issue needs your review. Please check the details.',
    action: 'Review Issue',
    footerStatus: 'Error'
  },
  'slide-in': {
    headline: 'New Information',
    description: 'Fresh data has arrived and is ready for processing.',
    action: 'View Details',
    footerStatus: 'Updated'
  },
  'dim': {
    headline: 'System Idle',
    description: 'No activity detected. System in low-power mode.',
    action: 'Wake Up',
    footerStatus: 'Inactive'
  }
};

// Get DOM elements
const body = document.body;
const icon = document.getElementById('assistant-icon');
const headlineEl = document.getElementById('status-headline');
const descriptionEl = document.getElementById('status-description');
const actionEl = document.getElementById('status-action');
const footerStatusEl = document.getElementById('footer-status');

// Update status language based on state
function updateStatusLanguage(state) {
  const language = statusLanguage[state];
  
  if (language) {
    headlineEl.textContent = language.headline;
    descriptionEl.textContent = language.description;
    actionEl.textContent = language.action;
    footerStatusEl.textContent = language.footerStatus;
  }
}

// Toggle state (for demo only)
function setState(newState) {
  // Remove all state classes from body
  body.className = `state-${newState}`;
  
  // Update icon state class
  icon.className = `future-hause-icon state-${newState}`;
  
  // Update status language
  updateStatusLanguage(newState);
  
  console.log(`State changed to: ${newState}`);
}

// Demo controls event listeners
const demoButtons = document.querySelectorAll('.demo-btn');
demoButtons.forEach(button => {
  button.addEventListener('click', () => {
    const state = button.dataset.state;
    setState(state);
  });
});

// Initialize with default state
updateStatusLanguage('pulse-slow');

/* ============================================================================
   FUTURE: Backend Integration Points
   ============================================================================
   
   Replace manual setState() calls with:
   
   1. Poll engine/state.json every 500ms:
      async function fetchState() {
        const response = await fetch('engine/state.json');
        const data = await response.json();
        setState(data.current_animation);
      }
      setInterval(fetchState, 500);
   
   2. WebSocket connection for real-time updates:
      const ws = new WebSocket('ws://localhost:8080/state');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setState(data.current_animation);
      };
   
   3. Server-sent events (SSE):
      const eventSource = new EventSource('/state-stream');
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setState(data.current_animation);
      };
   
   ============================================================================ */
