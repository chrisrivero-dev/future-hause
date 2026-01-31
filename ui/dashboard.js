/* ============================================================================
   FUTURE HAUSE DASHBOARD — v0.1 Read-Only Intelligence Dashboard
   Fetches and renders data from /outputs/*.json files
   Read-only: No mutations, no writes, display only
   ============================================================================ */

// Configuration
const CONFIG = {
  outputsPath: '/outputs',
  maxItemsPerColumn: 5,
  files: {
    intelEvents: 'intel_events.json',
    kbOpportunities: 'kb_opportunities.json',
    projects: 'projects.json',
    actionLog: 'action_log.json'
  }
};

// State for loaded data and metadata
const state = {
  intelEvents: null,
  kbOpportunities: null,
  projects: null,
  actionLog: null,
  loadStatus: {
    intelEvents: 'pending',
    kbOpportunities: 'pending',
    projects: 'pending',
    actionLog: 'pending'
  },
  metadata: {
    schemaVersions: {},
    generatedTimestamps: {}
  }
};

/* ----------------------------------------------------------------------------
   UTILITY FUNCTIONS
   ---------------------------------------------------------------------------- */

/**
 * Format ISO timestamp to human-readable format
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Formatted date/time string
 */
function formatTimestamp(isoString) {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return '—';
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return '—';
  }
}

/**
 * Truncate string to max length with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
function truncate(str, maxLength = 50) {
  if (!str || typeof str !== 'string') return '';
  return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
}

/**
 * Safely get nested property
 * @param {object} obj - Source object
 * @param {string} path - Dot-notation path
 * @param {*} defaultValue - Default if not found
 * @returns {*} Value or default
 */
function getNestedValue(obj, path, defaultValue = null) {
  if (!obj || !path) return defaultValue;
  return path.split('.').reduce((acc, part) =>
    acc && acc[part] !== undefined ? acc[part] : defaultValue, obj);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  if (!str || typeof str !== 'string') return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/* ----------------------------------------------------------------------------
   DATA FETCHING
   ---------------------------------------------------------------------------- */

/**
 * Fetch JSON file with graceful error handling
 * @param {string} filename - Name of file in /outputs/
 * @returns {Promise<object|null>} Parsed JSON or null on error
 */
async function fetchOutputFile(filename) {
  const url = `${CONFIG.outputsPath}/${filename}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      console.warn(`Failed to fetch ${filename}: ${response.status}`);
      return null;
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.warn(`Error fetching ${filename}:`, error.message);
    return null;
  }
}

/**
 * Load all output files
 */
async function loadAllData() {
  const results = await Promise.all([
    fetchOutputFile(CONFIG.files.intelEvents),
    fetchOutputFile(CONFIG.files.kbOpportunities),
    fetchOutputFile(CONFIG.files.projects),
    fetchOutputFile(CONFIG.files.actionLog)
  ]);

  // Store results and update load status
  state.intelEvents = results[0];
  state.loadStatus.intelEvents = results[0] ? 'success' : 'error';
  if (results[0]) {
    state.metadata.schemaVersions.intelEvents = results[0].schema_version;
    state.metadata.generatedTimestamps.intelEvents = results[0].generated_at;
  }

  state.kbOpportunities = results[1];
  state.loadStatus.kbOpportunities = results[1] ? 'success' : 'error';
  if (results[1]) {
    state.metadata.schemaVersions.kbOpportunities = results[1].schema_version;
    state.metadata.generatedTimestamps.kbOpportunities = results[1].generated_at;
  }

  state.projects = results[2];
  state.loadStatus.projects = results[2] ? 'success' : 'error';
  if (results[2]) {
    state.metadata.schemaVersions.projects = results[2].schema_version;
    state.metadata.generatedTimestamps.projects = results[2].generated_at;
  }

  state.actionLog = results[3];
  state.loadStatus.actionLog = results[3] ? 'success' : 'error';
  if (results[3]) {
    state.metadata.schemaVersions.actionLog = results[3].schema_version;
  }

  // Render all sections
  renderIntelEvents();
  renderKbOpportunities();
  renderProjects();
  renderRecentRecommendations();
  renderActionLogTable();
  renderSystemMetadata();
}

/* ----------------------------------------------------------------------------
   RENDERING — INTEL EVENTS COLUMN
   ---------------------------------------------------------------------------- */

function renderIntelEvents() {
  const container = document.getElementById('intel-events-content');
  const countEl = document.getElementById('intel-events-count');

  if (!container) return;

  const events = getNestedValue(state.intelEvents, 'events', []);
  const displayEvents = events.slice(0, CONFIG.maxItemsPerColumn);

  countEl.textContent = `${events.length} total`;

  if (displayEvents.length === 0) {
    container.innerHTML = renderEmptyState('No intel events yet');
    return;
  }

  container.innerHTML = displayEvents.map((event, index) => renderCard({
    columnId: 'intel',
    index,
    title: event.title || event.type || 'Event',
    meta: formatTimestamp(event.detected_at || event.timestamp),
    detailsHtml: `
      ${event.id ? renderDetailRow('ID', event.id) : ''}
      ${event.type ? renderDetailRow('Type', event.type) : ''}
      ${event.source ? renderDetailRow('Source', event.source) : ''}
      ${event.description ? renderDetailRow('Description', event.description) : ''}
      ${event.url ? renderDetailRow('URL', event.url) : ''}
    `
  })).join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — KB OPPORTUNITIES COLUMN
   ---------------------------------------------------------------------------- */

function renderKbOpportunities() {
  const container = document.getElementById('kb-opportunities-content');
  const countEl = document.getElementById('kb-opportunities-count');

  if (!container) return;

  const opportunities = getNestedValue(state.kbOpportunities, 'opportunities', []);
  const displayOpportunities = opportunities.slice(0, CONFIG.maxItemsPerColumn);

  countEl.textContent = `${opportunities.length} total`;

  if (displayOpportunities.length === 0) {
    container.innerHTML = renderEmptyState('No KB opportunities yet');
    return;
  }

  container.innerHTML = displayOpportunities.map((opp, index) => renderCard({
    columnId: 'kb',
    index,
    title: opp.title || opp.topic || 'Opportunity',
    meta: escapeHtml(opp.status || opp.priority || ''),
    detailsHtml: `
      ${opp.id ? renderDetailRow('ID', opp.id) : ''}
      ${opp.gap_type ? renderDetailRow('Gap Type', opp.gap_type) : ''}
      ${opp.suggested_action ? renderDetailRow('Suggested', opp.suggested_action) : ''}
      ${opp.source_signals ? renderDetailRow('Signals', opp.source_signals) : ''}
      ${opp.created_at ? renderDetailRow('Created', formatTimestamp(opp.created_at)) : ''}
    `
  })).join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — PROJECTS COLUMN
   ---------------------------------------------------------------------------- */

function renderProjects() {
  const container = document.getElementById('projects-content');
  const countEl = document.getElementById('projects-count');

  if (!container) return;

  const projects = getNestedValue(state.projects, 'projects', []);
  const displayProjects = projects.slice(0, CONFIG.maxItemsPerColumn);

  countEl.textContent = `${projects.length} total`;

  if (displayProjects.length === 0) {
    container.innerHTML = renderEmptyState('No projects yet');
    return;
  }

  container.innerHTML = displayProjects.map((project, index) => renderCard({
    columnId: 'projects',
    index,
    title: project.name || project.title || 'Project',
    meta: escapeHtml(project.status || ''),
    detailsHtml: `
      ${project.id ? renderDetailRow('ID', project.id) : ''}
      ${project.status ? renderDetailRow('Status', project.status) : ''}
      ${project.deliverables ? renderDetailRow('Deliverables', Array.isArray(project.deliverables) ? project.deliverables.join(', ') : project.deliverables) : ''}
      ${project.created_at ? renderDetailRow('Created', formatTimestamp(project.created_at)) : ''}
      ${project.updated_at ? renderDetailRow('Updated', formatTimestamp(project.updated_at)) : ''}
    `
  })).join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — RECENT RECOMMENDATIONS COLUMN
   ---------------------------------------------------------------------------- */

function renderRecentRecommendations() {
  const container = document.getElementById('recommendations-content');
  const countEl = document.getElementById('recommendations-count');

  if (!container) return;

  const actions = getNestedValue(state.actionLog, 'actions', []);
  const displayActions = actions.slice(0, CONFIG.maxItemsPerColumn);

  countEl.textContent = `${actions.length} total`;

  if (displayActions.length === 0) {
    container.innerHTML = renderEmptyState('No recommendations yet');
    return;
  }

  container.innerHTML = displayActions.map((action, index) => renderCard({
    columnId: 'recommendations',
    index,
    title: action.action || action.recommendation || 'Action',
    meta: formatTimestamp(action.timestamp || action.created_at),
    detailsHtml: `
      ${action.id ? renderDetailRow('ID', action.id) : ''}
      ${action.rationale ? renderDetailRow('Rationale', action.rationale) : ''}
      ${action.status ? renderDetailRow('Status', action.status) : ''}
      ${action.source ? renderDetailRow('Source', action.source) : ''}
    `
  })).join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — ACTION LOG TABLE (FULL LIST)
   ---------------------------------------------------------------------------- */

function renderActionLogTable() {
  const container = document.getElementById('action-log-table-body');

  if (!container) return;

  const actions = getNestedValue(state.actionLog, 'actions', []);

  if (actions.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="4" class="intel-empty">
          <div class="intel-empty-text">No actions logged yet</div>
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = actions.map(action => `
    <tr>
      <td class="col-time">${formatTimestamp(action.timestamp || action.created_at)}</td>
      <td class="col-id">${escapeHtml(action.id || '—')}</td>
      <td class="col-action">${escapeHtml(action.action || action.recommendation || '—')}</td>
      <td class="col-rationale">${escapeHtml(action.rationale || '—')}</td>
    </tr>
  `).join('');
}

/* ----------------------------------------------------------------------------
   RENDERING — SYSTEM METADATA
   ---------------------------------------------------------------------------- */

function renderSystemMetadata() {
  const container = document.getElementById('metadata-content');

  if (!container) return;

  const { schemaVersions, generatedTimestamps } = state.metadata;
  const { loadStatus } = state;

  container.innerHTML = `
    <div class="metadata-grid">
      <div class="metadata-card">
        <div class="metadata-card-title">Schema Versions</div>
        <div class="metadata-card-value">
          ${renderSchemaVersions(schemaVersions)}
        </div>
      </div>

      <div class="metadata-card">
        <div class="metadata-card-title">Generated Timestamps</div>
        <div class="metadata-card-value">
          ${renderGeneratedTimestamps(generatedTimestamps)}
        </div>
      </div>

      <div class="metadata-card">
        <div class="metadata-card-title">Output File Status</div>
        <div class="metadata-card-value">
          ${renderLoadStatus(loadStatus)}
        </div>
      </div>
    </div>
  `;
}

function renderSchemaVersions(versions) {
  const files = ['intelEvents', 'kbOpportunities', 'projects', 'actionLog'];
  const labels = {
    intelEvents: 'intel_events.json',
    kbOpportunities: 'kb_opportunities.json',
    projects: 'projects.json',
    actionLog: 'action_log.json'
  };

  return files.map(file => {
    const version = versions[file] || '—';
    return `<div>${labels[file]}: ${escapeHtml(version)}</div>`;
  }).join('');
}

function renderGeneratedTimestamps(timestamps) {
  const files = ['intelEvents', 'kbOpportunities', 'projects'];
  const labels = {
    intelEvents: 'intel_events',
    kbOpportunities: 'kb_opportunities',
    projects: 'projects'
  };

  return files.map(file => {
    const ts = timestamps[file];
    const formatted = ts ? formatTimestamp(ts) : '—';
    return `<div>${labels[file]}: ${formatted}</div>`;
  }).join('');
}

function renderLoadStatus(loadStatus) {
  const files = ['intelEvents', 'kbOpportunities', 'projects', 'actionLog'];
  const labels = {
    intelEvents: 'intel_events.json',
    kbOpportunities: 'kb_opportunities.json',
    projects: 'projects.json',
    actionLog: 'action_log.json'
  };

  return files.map(file => {
    const status = loadStatus[file];
    const dotClass = status === 'success' ? 'success' : status === 'error' ? 'error' : 'pending';
    const statusText = status === 'success' ? 'Loaded' : status === 'error' ? 'Failed' : 'Pending';
    return `
      <div class="metadata-status">
        <span class="metadata-status-dot ${dotClass}"></span>
        <span>${labels[file]}: ${statusText}</span>
      </div>
    `;
  }).join('');
}

/* ----------------------------------------------------------------------------
   HELPER RENDERERS
   ---------------------------------------------------------------------------- */

function renderEmptyState(message) {
  return `
    <div class="intel-empty">
      <div class="intel-empty-icon">—</div>
      <div class="intel-empty-text">${escapeHtml(message)}</div>
    </div>
  `;
}

function renderDetailRow(label, value) {
  if (!value) return '';
  return `
    <div class="intel-detail-row">
      <span class="intel-detail-label">${escapeHtml(label)}:</span>
      <span class="intel-detail-value">${escapeHtml(String(value))}</span>
    </div>
  `;
}

/* ----------------------------------------------------------------------------
   EXPAND/COLLAPSE CONTRACT (v0.1)

   BEHAVIORAL RULES:
   - Only ONE card per column may be expanded at a time
   - Expanding a card auto-collapses any other expanded card in same column
   - Links inside expanded content do NOT collapse the card
   - Focus remains on card after toggle

   ACCESSIBILITY:
   - Card header: role="button", tabindex="0", aria-expanded, aria-controls
   - Details region: role="region", aria-labelledby
   - Enter/Space toggles expand/collapse

   INTERACTION:
   - Click on card header toggles state
   - Keyboard: Enter or Space triggers toggle
   ---------------------------------------------------------------------------- */

/**
 * Generate unique card ID for ARIA relationships
 * @param {string} columnId - Column identifier
 * @param {number} index - Card index within column
 * @returns {object} Object with headerId and detailsId
 */
function generateCardIds(columnId, index) {
  return {
    headerId: `card-header-${columnId}-${index}`,
    detailsId: `card-details-${columnId}-${index}`
  };
}

/**
 * Render a card with proper ARIA attributes
 * @param {object} params - Card parameters
 * @returns {string} HTML string
 */
function renderCard({ columnId, index, title, meta, detailsHtml }) {
  const { headerId, detailsId } = generateCardIds(columnId, index);

  return `
    <div class="intel-card" data-index="${index}">
      <div
        class="intel-card-header"
        id="${headerId}"
        tabindex="0"
        role="button"
        aria-expanded="false"
        aria-controls="${detailsId}"
      >
        <div class="intel-card-summary">
          <div class="intel-card-title">${escapeHtml(title)}</div>
          <div class="intel-card-meta">${meta}</div>
        </div>
        <span class="intel-card-toggle" aria-hidden="true">▼</span>
      </div>
      <div
        class="intel-card-details"
        id="${detailsId}"
        role="region"
        aria-labelledby="${headerId}"
      >
        ${detailsHtml}
      </div>
    </div>
  `;
}

/**
 * Attach expand/collapse handlers to cards in a container
 * @param {HTMLElement} container - The column content container
 */
function attachExpandHandlers(container) {
  const headers = container.querySelectorAll('.intel-card-header');

  headers.forEach(header => {
    // Click handler
    header.addEventListener('click', handleCardToggle);

    // Keyboard handler (Enter/Space)
    header.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleCardToggle.call(header, e);
      }
    });
  });

  // Prevent link clicks inside details from collapsing the card
  const links = container.querySelectorAll('.intel-card-details a');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.stopPropagation();
    });
  });
}

/**
 * Handle card expand/collapse toggle
 * Enforces single-card-per-column rule
 * @param {Event} event - Click or keyboard event
 */
function handleCardToggle(event) {
  const header = this;
  const card = header.closest('.intel-card');
  if (!card) return;

  const column = card.closest('.intel-column-content');
  if (!column) return;

  const isExpanded = card.classList.contains('expanded');

  // If expanding, collapse any other expanded card in this column first
  if (!isExpanded) {
    const expandedCards = column.querySelectorAll('.intel-card.expanded');
    expandedCards.forEach(expandedCard => {
      if (expandedCard !== card) {
        collapseCard(expandedCard);
      }
    });
  }

  // Toggle this card
  if (isExpanded) {
    collapseCard(card);
  } else {
    expandCard(card);
  }

  // Ensure focus remains on the header after toggle
  header.focus();
}

/**
 * Expand a card and update ARIA state
 * @param {HTMLElement} card - The card element
 */
function expandCard(card) {
  card.classList.add('expanded');
  const header = card.querySelector('.intel-card-header');
  if (header) {
    header.setAttribute('aria-expanded', 'true');
  }
}

/**
 * Collapse a card and update ARIA state
 * @param {HTMLElement} card - The card element
 */
function collapseCard(card) {
  card.classList.remove('expanded');
  const header = card.querySelector('.intel-card-header');
  if (header) {
    header.setAttribute('aria-expanded', 'false');
  }
}

/* ----------------------------------------------------------------------------
   ICON STATE MANAGEMENT
   ---------------------------------------------------------------------------- */

/**
 * Update dashboard icon state
 * @param {string} iconState - One of: idle, processing, success, error
 */
function setIconState(iconState) {
  const iconWrapper = document.getElementById('dashboard-icon');
  if (iconWrapper) {
    iconWrapper.setAttribute('data-state', iconState);
  }
}

/* ----------------------------------------------------------------------------
   INITIALIZATION
   ---------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  // Set processing state while loading
  setIconState('processing');

  loadAllData().then(() => {
    // Determine final state based on load results
    const hasErrors = Object.values(state.loadStatus).some(s => s === 'error');
    const allSuccess = Object.values(state.loadStatus).every(s => s === 'success');

    if (hasErrors) {
      setIconState('error');
    } else if (allSuccess) {
      setIconState('success');
      // Return to idle after brief success indication
      setTimeout(() => setIconState('idle'), 2000);
    } else {
      setIconState('idle');
    }
  });
});
