/* ============================================================================
   FUTURE HAUSE DASHBOARD — v0.1 Read-Only Intelligence Dashboard
   Fetches and renders data from /outputs/*.json files
   Read-only: No mutations, no writes, display only

   LLM ROUTING CONTRACT: docs/llm-routing.md (authoritative)
   ROUTER IMPLEMENTATION: ui/llmRouter.js
   ============================================================================ */

/* ============================================================================
   SECTION SEMANTICS (CANONICAL DEFINITIONS)
   ============================================================================

   New Intel (intel_events.json)
   → Raw, unclassified signals detected by the system
   → No human action has been taken
   → Source of truth for what the system observed

   KB Opportunities (kb_opportunities.json)
   → Evidence-backed documentation gaps
   → Derived from intel analysis (future: v0.3+)
   → Suggests where knowledge base could improve

   Projects (projects.json)
   → Human-approved initiatives derived from intelligence
   → NOT auto-generated; requires explicit human promotion
   → Tracks deliverables and milestones

   Recent Recommendations (future)
   → Advisory suggestions not yet acted on
   → System-generated, human-reviewed
   → May be promoted to Projects or dismissed

   Action Log (action_log.json)
   → Immutable audit trail explaining state changes
   → Every promote, dismiss, accept action MUST be logged here
   → Provides transparency and accountability

   System Metadata
   → Health + trust indicators for the system
   → Schema versions, timestamps, load status
   → No business logic, pure observability

   STATE MUTATION RULES:
   - Dashboard is READ-ONLY; no implicit state changes
   - No auto-promotion between sections
   - All state transitions require explicit engine action
   - All actions must be logged to action_log.json
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
/* ... existing header ... */

// LLM routing rules are defined in docs/llm-routing.md
// Code must conform to that contract. No implicit actions.

/* ----------------------------------------------------------------------------
   SECTION EXPLANATIONS — Plain-Language Intelligence Context
   Purpose: Help users understand what each section represents
   ---------------------------------------------------------------------------- */

const SECTION_EXPLANATIONS = {
  'intel-events': {
    title: 'What is New Intel?',
    text: 'Signals, observations, or ideas the system has noticed. This is raw, uncommitted intelligence — nothing here has been acted upon yet.',
    examples: [
      'New FutureBit firmware updates or announcements',
      'Reddit community discussions or support questions',
      'Documentation gaps or user confusion patterns',
      'Suggestions tied to current projects'
    ]
  },
  'kb-opportunities': {
    title: 'What are KB Opportunities?',
    text: 'Places where documentation or canned responses could improve. These are evidence-backed suggestions derived from intel analysis.',
    examples: [
      'Frequently asked questions without clear answers',
      'Common support issues that could be documented',
      'Feature explanations that users struggle to find',
      'Gaps between product capabilities and documentation'
    ]
  },
  'projects': {
    title: 'What are Projects?',
    text: 'Human-approved initiatives you are actively working on. Projects are promoted from intel or recommendations — they represent committed work.',
    examples: [
      'Documentation improvements in progress',
      'Support workflow optimizations',
      'Knowledge base article drafts',
      'Process improvements based on intel patterns'
    ]
  },
  'recommendations': {
    title: 'What are Recommendations?',
    text: 'Actionable suggestions derived from intel and context. These are advisory only — a human must decide whether to act on them.',
    examples: [
      'Suggested KB articles based on support patterns',
      'Proposed canned responses for common questions',
      'Workflow improvements based on observed friction',
      'Priority suggestions based on signal frequency'
    ]
  },
  'action-log': {
    title: 'What is the Action Log?',
    text: 'An immutable audit trail of decisions and actions. Every promote, dismiss, or accept action is recorded here with timestamps and rationale.',
    examples: [
      'Intel promoted to project (with reason)',
      'Recommendation accepted or dismissed',
      'KB article published from opportunity',
      'System state changes and their triggers'
    ]
  },
  'metadata': {
    title: 'What is System Metadata?',
    text: 'Health and trust indicators for the system. This shows schema versions, load status, and timestamps — pure observability, no business logic.',
    examples: [
      'Schema version compatibility checks',
      'Data freshness timestamps',
      'Load status for each data source',
      'System configuration state'
    ]
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
    // Meaningful placeholder explaining what will appear here
    container.innerHTML = `
      <tr>
        <td colspan="4" class="action-log-empty">
          <div class="action-log-empty-content">
            <div class="action-log-empty-title">No actions recorded yet</div>
            <div class="action-log-empty-text">
              When you promote intel to projects, accept recommendations, or dismiss items,
              those decisions will appear here with timestamps and rationale.
            </div>
            <div class="action-log-empty-hint">
              This is your audit trail — every decision is logged for transparency.
            </div>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  // Render actual action log entries
  container.innerHTML = actions.map(action => `
    <tr class="action-log-row" data-action-id="${escapeHtml(action.id || '')}">
      <td class="col-time">${formatTimestamp(action.timestamp || action.created_at)}</td>
      <td class="col-id">${escapeHtml(action.id || '—')}</td>
      <td class="col-action">
        <span class="action-type">${escapeHtml(action.action || action.type || '—')}</span>
        ${action.target ? `<span class="action-target">→ ${escapeHtml(action.target)}</span>` : ''}
      </td>
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
   ICON EVENT WIRING — Interactive State Triggers

   States and Triggers:
   - idle:       Default, restored after interactions
   - processing: Hover, or call mockProcessing()
   - success:    Click (brief), or call mockThinking() completion
   - error:      Reserved for actual errors

   To disable: Set ICON_EVENTS_ENABLED = false
   ---------------------------------------------------------------------------- */

const ICON_EVENTS_ENABLED = true;

/**
 * Wire up icon hover and click events
 * Called once on DOMContentLoaded
 */
function wireIconEvents() {
  if (!ICON_EVENTS_ENABLED) return;

  const iconWrapper = document.getElementById('dashboard-icon');
  if (!iconWrapper) return;

  // Hover: Show processing state
  iconWrapper.addEventListener('mouseenter', () => {
    setIconState('processing');
  });

  // Mouseleave: Always return to idle
  iconWrapper.addEventListener('mouseleave', () => {
    setIconState('idle');
  });

  // Click: Brief success flash, then idle
  iconWrapper.addEventListener('click', () => {
    setIconState('success');
    setTimeout(() => setIconState('idle'), 600);
  });
}

// Safety guard: Maximum processing duration (10 seconds)
const MAX_PROCESSING_MS = 10000;

/**
 * Mock processing state (for testing)
 * @param {number} durationMs - Duration in milliseconds (default 2000, max 10000)
 * @returns {Promise} Resolves when complete
 */
function mockProcessing(durationMs = 2000) {
  const safeDuration = Math.min(durationMs, MAX_PROCESSING_MS);
  setIconState('processing');
  return new Promise(resolve => {
    setTimeout(() => {
      setIconState('idle');
      resolve();
    }, safeDuration);
  });
}

/**
 * Mock thinking state (processing → success → idle)
 * @param {number} thinkMs - Thinking duration (default 1500, max 10000)
 * @returns {Promise} Resolves when complete
 */
function mockThinking(thinkMs = 1500) {
  const safeDuration = Math.min(thinkMs, MAX_PROCESSING_MS);
  setIconState('processing');
  return new Promise(resolve => {
    setTimeout(() => {
      setIconState('success');
      setTimeout(() => {
        setIconState('idle');
        resolve();
      }, 500);
    }, safeDuration);
  });
}

// Expose mock functions for console testing
window.mockProcessing = mockProcessing;
window.mockThinking = mockThinking;
window.setIconState = setIconState;

/* ----------------------------------------------------------------------------
   EXPLANATION PANELS — Inline Expandable Intelligence Context
   Purpose: Help users understand what each section represents
   Triggered: Click on section header
   ---------------------------------------------------------------------------- */

/**
 * Create explanation panel HTML
 * @param {string} sectionKey - Key from SECTION_EXPLANATIONS
 * @returns {string} HTML string
 */
function createExplanationPanel(sectionKey) {
  const explanation = SECTION_EXPLANATIONS[sectionKey];
  if (!explanation) return '';

  const examplesList = explanation.examples
    .map(ex => `<li>${ex}</li>`)
    .join('');

  return `
    <div class="explanation-panel" data-panel="${sectionKey}">
      <div class="explanation-panel-title">${explanation.title}</div>
      <div class="explanation-panel-text">${explanation.text}</div>
      <ul class="explanation-panel-examples">${examplesList}</ul>
    </div>
  `;
}

/**
 * Toggle explanation panel visibility
 * @param {string} sectionKey - Key from SECTION_EXPLANATIONS
 */
function toggleExplanationPanel(sectionKey) {
  const panel = document.querySelector(`[data-panel="${sectionKey}"]`);
  if (panel) {
    panel.classList.toggle('expanded');
  }
}

/**
 * Wire up explanation panel click handlers
 * Called once on DOMContentLoaded
 */
function wireExplanationPanels() {
  // Wire up intel columns
  document.querySelectorAll('.intel-column[data-section]').forEach(column => {
    const sectionKey = column.getAttribute('data-section');
    const header = column.querySelector('.intel-column-header');
    const content = column.querySelector('.intel-column-content');

    if (header && content && SECTION_EXPLANATIONS[sectionKey]) {
      // Insert explanation panel after header
      header.insertAdjacentHTML('afterend', createExplanationPanel(sectionKey));

      // Add click handler to header
      header.addEventListener('click', (e) => {
        // Don't trigger if clicking on count or other interactive elements
        if (e.target.closest('.intel-column-count')) return;
        toggleExplanationPanel(sectionKey);
      });
    }
  });

  // Wire up secondary sections
  document.querySelectorAll('.secondary-section[data-section]').forEach(section => {
    const sectionKey = section.getAttribute('data-section');
    const header = section.querySelector('.secondary-section-header');
    const content = section.querySelector('.secondary-section-content');

    if (header && content && SECTION_EXPLANATIONS[sectionKey]) {
      // Insert explanation panel after header
      header.insertAdjacentHTML('afterend', createExplanationPanel(sectionKey));

      // Add click handler to header
      header.addEventListener('click', () => {
        toggleExplanationPanel(sectionKey);
      });
    }
  });
}

/* ----------------------------------------------------------------------------
   THEME TOGGLE — Dark/Light Mode
   - Persists to localStorage (theme preference only)
   - Dark mode is default
   ---------------------------------------------------------------------------- */

const THEME_STORAGE_KEY = 'future-hause-theme';

/**
 * Get current theme from localStorage or default to 'dark'
 * @returns {'dark' | 'light'}
 */
function getStoredTheme() {
  return localStorage.getItem(THEME_STORAGE_KEY) || 'dark';
}

/**
 * Apply theme to document and update toggle button text
 * @param {'dark' | 'light'} theme
 */
function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }

  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.textContent = theme === 'dark' ? 'Dark' : 'Light';
  }
}

/**
 * Toggle between dark and light themes
 */
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  applyTheme(newTheme);
  localStorage.setItem(THEME_STORAGE_KEY, newTheme);
}

/**
 * Initialize theme toggle button
 */
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleTheme);
  }

  // Apply stored theme on load
  applyTheme(getStoredTheme());
}

/* ----------------------------------------------------------------------------
   PHASE 1 — NOTES SUBMISSION + LLM RESPONSE

   HARD CONSTRAINTS (NON-NEGOTIABLE):
   - No side effects
   - No data persistence
   - No action log entries
   - No intel promotion
   - No automatic UI or data changes
   - This is a read-only, explanatory loop

   GLOBAL GUARDRAILS:
   - No Excel writes
   - No API calls (except LLM)
   - No persistence
   - No assumptions about work performed or time spent
   - No changes outside the visible UI
   ---------------------------------------------------------------------------- */

// Presence states: idle | thinking | observing
const PRESENCE_STATES = {
  IDLE: 'idle',
  THINKING: 'thinking',
  OBSERVING: 'observing'
};

// Presence state copy (exact strings, verbatim)
const PRESENCE_COPY = {
  [PRESENCE_STATES.IDLE]: 'Waiting for input. No analysis in progress.',
  [PRESENCE_STATES.THINKING]: 'Interpreting your message and preparing a draft response. No actions are being taken.',
  [PRESENCE_STATES.OBSERVING]: 'Draft prepared. Awaiting your review or next instruction.'
};

// Presence state labels (short form for UI)
const PRESENCE_LABELS = {
  [PRESENCE_STATES.IDLE]: 'Idle',
  [PRESENCE_STATES.THINKING]: 'Thinking',
  [PRESENCE_STATES.OBSERVING]: 'Observing'
};

/**
 * Update presence state (icon + status text)
 * @param {string} presenceState - One of PRESENCE_STATES
 */
function setPresenceState(presenceState) {
  // Update icon animation state
  const iconWrapper = document.getElementById('dashboard-icon');
  if (iconWrapper) {
    iconWrapper.setAttribute('data-state', presenceState);
  }

  // Update status text (short label)
  const statusText = document.querySelector('.presence-status-text');
  if (statusText) {
    statusText.textContent = PRESENCE_LABELS[presenceState] || 'Idle';
  }
}

/**
 * Purpose disclosure — explains Future Hause's role when asked
 * Returns response in mandatory schema format
 * @param {string} userInput - User's input text
 * @returns {string|null} Disclosure text if triggered, null otherwise
 */
function checkPurposeDisclosure(userInput) {
  const lowered = userInput.toLowerCase();
  const purposeTriggers = [
    'what is your purpose',
    'what do you do',
    'what are you',
    'who are you',
    'what is future hause',
    'explain yourself',
    'what can you do',
    'your role',
    'your purpose'
  ];

  const triggered = purposeTriggers.some(trigger => lowered.includes(trigger));

  if (triggered) {
    return formatResponse({
      presenceState: PRESENCE_STATES.OBSERVING,
      summary: 'You asked about my purpose and capabilities.',
      whatIDid: [
        'Explained my role: to serve, assist, and support you',
        'Clarified that I provide drafts, explanations, and recommendations',
        'Confirmed all decisions remain under your control'
      ],
      whatIDidNot: [
        'No data was persisted',
        'No external systems were contacted',
        'No actions were executed'
      ],
      nextStep: 'Share observations or context you would like me to consider.'
    });
  }

  return null;
}

/* --------------------------------------
   RESPONSE SCHEMA CONTRACT (LOCKED)

   Required sections (always present):
   - Status (Presence State, Mode, Side Effects)
   - Summary
   - What I did
   - What I did NOT do

   Optional sections:
   - Next suggested step

   Forbidden:
   - Extra sections
   - Free-form prose outside schema
   - Missing "What I did NOT do"
   -------------------------------------- */

// Minimum guardrails that MUST appear in "What I did NOT do"
const MANDATORY_GUARDRAILS = [
  'No data was persisted',
  'No external systems were modified'
];

/**
 * Validate response parameters against schema contract
 * @param {object} params - Response parameters
 * @throws {Error} If required fields are missing or invalid
 */
function validateResponseSchema(params) {
  const { presenceState, summary, whatIDid, whatIDidNot } = params;

  // Required: presenceState must be valid
  if (!presenceState || !Object.values(PRESENCE_STATES).includes(presenceState)) {
    throw new Error('Schema violation: Invalid or missing presenceState');
  }

  // Required: summary must be non-empty string
  if (!summary || typeof summary !== 'string' || summary.trim() === '') {
    throw new Error('Schema violation: Missing or empty summary');
  }

  // Required: whatIDid must be non-empty array
  if (!Array.isArray(whatIDid) || whatIDid.length === 0) {
    throw new Error('Schema violation: "What I did" must be non-empty array');
  }

  // Required: whatIDidNot must be non-empty array
  if (!Array.isArray(whatIDidNot) || whatIDidNot.length === 0) {
    throw new Error('Schema violation: "What I did NOT do" must be non-empty array');
  }
}

/**
 * Format response according to mandatory schema
 * Enforces contract: all required sections present, no extra content
 *
 * Routing contract: docs/llm-routing.md
 *
 * @param {object} params - Response parameters
 * @param {object} params.routingDecision - Result from routeLLM() (optional)
 * @returns {string} Formatted response
 */
function formatResponse({ presenceState, summary, whatIDid, whatIDidNot, nextStep, routingDecision }) {
  // Validate schema compliance
  validateResponseSchema({ presenceState, summary, whatIDid, whatIDidNot });

  // Ensure mandatory guardrails are included in "What I did NOT do"
  const guardrails = [...whatIDidNot];
  MANDATORY_GUARDRAILS.forEach(guardrail => {
    const alreadyIncluded = guardrails.some(item =>
      item.toLowerCase().includes(guardrail.toLowerCase().replace('no ', ''))
    );
    if (!alreadyIncluded) {
      guardrails.push(guardrail);
    }
  });

  // Build response in strict schema order
  const lines = [
    'Status:',
    `• Presence State: ${PRESENCE_LABELS[presenceState]}`,
    '• Mode: Draft / Advisory',
    '• Side Effects: None'
  ];

  // Include routing decision if provided
  if (routingDecision && typeof window.formatRoutingDecision === 'function') {
    lines.push(`• Routed To: ${window.formatRoutingDecision(routingDecision)}`);
  }

  lines.push(
    '',
    'Summary:',
    `• ${summary}`,
    '',
    'What I did:',
    ...whatIDid.map(item => `• ${item}`),
    '',
    'What I did NOT do:',
    ...guardrails.map(item => `• ${item}`)
  );

  // Optional: Next step (only if provided)
  if (nextStep && typeof nextStep === 'string' && nextStep.trim() !== '') {
    lines.push('', 'Next suggested step (optional):', `• ${nextStep}`);
  }

  return lines.join('\n');
}

/**
 * Send notes to LLM and get response
 *
 * Routing contract: docs/llm-routing.md
 * Router implementation: ui/llmRouter.js
 *
 * @param {string} notes - User's notes
 * @returns {Promise<string>} LLM response in mandatory schema format
 */
async function sendToLLM(notes) {
  // Check for purpose disclosure first
  const disclosure = checkPurposeDisclosure(notes);
  if (disclosure) {
    return disclosure;
  }

  // Route input to appropriate LLM stage (no network call)
  // See: docs/llm-routing.md for contract
  const routingDecision = typeof window.routeLLM === 'function'
    ? window.routeLLM(notes)
    : null;

  // TODO: Replace with actual LLM endpoint based on routingDecision.provider
  // For now, simulate a thoughtful response
  // In production: POST /api/llm with { prompt: notes, stage: routingDecision.stage }

  return new Promise((resolve) => {
    // Simulate LLM processing time
    setTimeout(() => {
      resolve(formatResponse({
        presenceState: PRESENCE_STATES.OBSERVING,
        summary: 'Received and interpreted your observations.',
        routingDecision: routingDecision,
        whatIDid: [
          'Analyzed input for routing keywords',
          `Determined routing: Stage ${routingDecision?.stage || '?'} (${routingDecision?.provider || 'unknown'})`,
          'Prepared routing decision for review'
        ],
        whatIDidNot: [
          'No model was called (routing only)',
          'No data was saved or persisted',
          'No Excel or Freshdesk writes',
          'No API calls to external systems',
          'No action log entries created'
        ],
        nextStep: routingDecision
          ? `Ready to forward to ${routingDecision.provider} when enabled.`
          : 'Router not available — check llmRouter.js is loaded.'
      }));
    }, 800); // Shorter delay since no actual LLM call
  });
}

/**
 * Handle notes form submission
 */
async function handleNotesSubmit() {
  const textarea = document.getElementById('notes-textarea');
  const submitBtn = document.getElementById('notes-submit');
  const responsePanel = document.getElementById('notes-response-panel');
  const responseContent = document.getElementById('notes-response-content');

  if (!textarea || !submitBtn || !responsePanel || !responseContent) {
    console.warn('Notes form elements not found');
    return;
  }

  const notes = textarea.value.trim();

  if (!notes) {
    return; // Don't submit empty notes
  }

  // Disable submit button during processing
  submitBtn.disabled = true;
  submitBtn.textContent = 'Thinking...';

  // Update presence: Idle → Thinking
  setPresenceState(PRESENCE_STATES.THINKING);

  try {
    // Send to LLM
    const response = await sendToLLM(notes);

    // Update presence: Thinking → Observing
    setPresenceState(PRESENCE_STATES.OBSERVING);

    // Display response
    responseContent.textContent = response;
    responsePanel.hidden = false;

    // After a moment, return to idle
    setTimeout(() => {
      setPresenceState(PRESENCE_STATES.IDLE);
    }, 3000);

  } catch (error) {
    console.error('Error sending notes to LLM:', error);
    responseContent.textContent = 'An error occurred. Please try again.';
    responsePanel.hidden = false;
    setPresenceState(PRESENCE_STATES.IDLE);
  } finally {
    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit to Future Hause';
  }
}

/**
 * Wire up notes form submission handler
 */
function wireNotesSubmit() {
  const submitBtn = document.getElementById('notes-submit');
  if (submitBtn) {
    submitBtn.addEventListener('click', handleNotesSubmit);
  }

  // Also handle Enter+Cmd/Ctrl in textarea
  const textarea = document.getElementById('notes-textarea');
  if (textarea) {
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        handleNotesSubmit();
      }
    });
  }

  // Wire up collapsible response panel
  const responseHeader = document.getElementById('notes-response-header');
  if (responseHeader) {
    responseHeader.addEventListener('click', toggleResponsePanel);
    responseHeader.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleResponsePanel();
      }
    });
  }
}

/**
 * Toggle response panel expand/collapse
 */
function toggleResponsePanel() {
  const header = document.getElementById('notes-response-header');
  const body = document.getElementById('notes-response-body');

  if (!header || !body) return;

  const isExpanded = body.classList.contains('expanded');

  if (isExpanded) {
    body.classList.remove('expanded');
    header.setAttribute('aria-expanded', 'false');
  } else {
    body.classList.add('expanded');
    header.setAttribute('aria-expanded', 'true');
  }
}

// Expose for testing
window.setPresenceState = setPresenceState;
window.PRESENCE_STATES = PRESENCE_STATES;

/* ----------------------------------------------------------------------------
   INITIALIZATION
   ---------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize theme from localStorage
  initThemeToggle();

  // Ensure icon starts in idle state
  setIconState('idle');
  setPresenceState(PRESENCE_STATES.IDLE);

  // Wire up icon interactive events
  wireIconEvents();

  // Wire up explanation panels for section headers
  wireExplanationPanels();

  // Wire up notes submission (Phase 1 interaction)
  wireNotesSubmit();

  // State only changes via hover, click, or explicit function calls

  loadAllData().then(() => {
    // Data loaded silently — icon remains idle unless error
    const hasErrors = Object.values(state.loadStatus).some(s => s === 'error');

    if (hasErrors) {
      setIconState('error');
      // Return to idle after showing error briefly
      setTimeout(() => setIconState('idle'), 3000);
    }
    // Success is silent — icon stays idle
  });
});
