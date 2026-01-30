/* ============================================================================
   FUTURE HAUSE DASHBOARD — ENGINE → UI CONTRACT
   UI is a pure renderer. No state logic. No language maps. No timers.
   ============================================================================ */

/**
 * Global rendering function called by engine/backend
 * @param {Object} payload - Status payload from engine
 * @param {string} payload.state - State name (pulse-slow|spin|glow|shake|slide-in|dim)
 * @param {string} payload.headline - Status headline text
 * @param {string} payload.message - Status description text
 * @param {string} payload.footer - Footer status text
 * @param {Object} payload.action - Action button configuration
 * @param {string} payload.action.label - Button text
 * @param {boolean} payload.action.enabled - Button enabled state
 */
window.renderStatus = function(payload) {
  // Apply state class to body
  document.body.className = `state-${payload.state}`;
  
  // Apply state class to icon
  const icon = document.getElementById('assistant-icon');
  if (icon) {
    icon.className = `future-hause-icon state-${payload.state}`;
  }
  
  // Render headline
  const headlineEl = document.getElementById('status-headline');
  if (headlineEl) {
    headlineEl.textContent = payload.headline;
  }
  
  // Render message
  const descriptionEl = document.getElementById('status-description');
  if (descriptionEl) {
    descriptionEl.textContent = payload.message;
  }
  
  // Render footer status
  const footerStatusEl = document.getElementById('footer-status');
  if (footerStatusEl) {
    footerStatusEl.textContent = payload.footer;
  }
  
  // Render action button
  const actionEl = document.getElementById('status-action');
  if (actionEl && payload.action) {
    actionEl.textContent = payload.action.label;
    actionEl.disabled = !payload.action.enabled;
  }
};

/* ============================================================================
   DEMO CONTROLS (Optional — for manual testing only)
   Remove this section in production
   ============================================================================ */

const demoButtons = document.querySelectorAll('.demo-btn');
demoButtons.forEach(button => {
  button.addEventListener('click', () => {
    const state = button.dataset.state;
    
    // Simulate engine payload
    const demoPayloads = {
      'pulse-slow': {
        state: 'pulse-slow',
        headline: 'System Ready',
        message: 'All systems operational. Waiting for instructions.',
        footer: 'Operational',
        action: { label: 'Start Task', enabled: false }
      },
      'spin': {
        state: 'spin',
        headline: 'Processing Request',
        message: 'Collecting and validating inputs. Please wait...',
        footer: 'Processing',
        action: { label: 'Cancel', enabled: false }
      },
      'glow': {
        state: 'glow',
        headline: 'Task Complete',
        message: 'Operation completed successfully. Results are ready.',
        footer: 'Success',
        action: { label: 'View Results', enabled: false }
      },
      'shake': {
        state: 'shake',
        headline: 'Attention Required',
        message: 'An issue needs your review. Please check the details.',
        footer: 'Error',
        action: { label: 'Review Issue', enabled: false }
      },
      'slide-in': {
        state: 'slide-in',
        headline: 'New Information',
        message: 'Fresh data has arrived and is ready for processing.',
        footer: 'Updated',
        action: { label: 'View Details', enabled: false }
      },
      'dim': {
        state: 'dim',
        headline: 'System Idle',
        message: 'No activity detected. System in low-power mode.',
        footer: 'Inactive',
        action: { label: 'Wake Up', enabled: false }
      }
    };
    
    window.renderStatus(demoPayloads[state]);
  });
});

// Initialize with default payload
window.renderStatus({
  state: 'pulse-slow',
  headline: 'System Ready',
  message: 'All systems operational. Waiting for instructions.',
  footer: 'Operational',
  action: { label: 'Start Task', enabled: false }
});

/* ============================================================================
   ENGINE INTEGRATION EXAMPLES
   ============================================================================
   
   Example 1: Polling engine/state.json
   
   async function pollEngine() {
     try {
       const response = await fetch('engine/state.json');
       const payload = await response.json();
       window.renderStatus(payload);
     } catch (error) {
       console.error('Failed to fetch state:', error);
     }
   }
   setInterval(pollEngine, 500);
   
   --------------------------------------------------------------------------
   
   Example 2: WebSocket real-time updates
   
   const ws = new WebSocket('ws://localhost:8080/state');
   ws.onmessage = (event) => {
     const payload = JSON.parse(event.data);
     window.renderStatus(payload);
   };
   
   --------------------------------------------------------------------------
   
   Example 3: Server-sent events (SSE)
   
   const eventSource = new EventSource('/state-stream');
   eventSource.onmessage = (event) => {
     const payload = JSON.parse(event.data);
     window.renderStatus(payload);
   };
   
   --------------------------------------------------------------------------
   
   Example 4: Direct call from parent window/iframe
   
   window.parent.postMessage({ type: 'status', payload: {...} }, '*');
   window.addEventListener('message', (event) => {
     if (event.data.type === 'status') {
       window.renderStatus(event.data.payload);
     }
   });
   
   ============================================================================ */
