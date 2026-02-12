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
    actionLog: 'action_log.json',
  },
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
      'Suggestions tied to current projects',
    ],
  },
  'kb-opportunities': {
    title: 'What are KB Opportunities?',
    text: 'Places where documentation or canned responses could improve. These are evidence-backed suggestions derived from intel analysis.',
    examples: [
      'Frequently asked questions without clear answers',
      'Common support issues that could be documented',
      'Feature explanations that users struggle to find',
      'Gaps between product capabilities and documentation',
    ],
  },
  projects: {
    title: 'What are Projects?',
    text: 'Human-approved initiatives you are actively working on. Projects are promoted from intel or recommendations — they represent committed work.',
    examples: [
      'Documentation improvements in progress',
      'Support workflow optimizations',
      'Knowledge base article drafts',
      'Process improvements based on intel patterns',
    ],
  },
  recommendations: {
    title: 'What are Recommendations?',
    text: 'Actionable suggestions derived from intel and context. These are advisory only — a human must decide whether to act on them.',
    examples: [
      'Suggested KB articles based on support patterns',
      'Proposed canned responses for common questions',
      'Workflow improvements based on observed friction',
      'Priority suggestions based on signal frequency',
    ],
  },
  'action-log': {
    title: 'What is the Action Log?',
    text: 'An immutable audit trail of decisions and actions. Every promote, dismiss, or accept action is recorded here with timestamps and rationale.',
    examples: [
      'Intel promoted to project (with reason)',
      'Recommendation accepted or dismissed',
      'KB article published from opportunity',
      'System state changes and their triggers',
    ],
  },
  metadata: {
    title: 'What is System Metadata?',
    text: 'Health and trust indicators for the system. This shows schema versions, load status, and timestamps — pure observability, no business logic.',
    examples: [
      'Schema version compatibility checks',
      'Data freshness timestamps',
      'Load status for each data source',
      'System configuration state',
    ],
  },
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
    actionLog: 'pending',
  },
  metadata: {
    schemaVersions: {},
    generatedTimestamps: {},
  },
  currentDraftId: null,
};

/* ----------------------------------------------------------------------------
   UTILITY FUNCTIONS
   ---------------------------------------------------------------------------- */

/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

/**
 * Format ISO timestamp to human-readable format
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Formatted date/time string
 */
/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

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
      minute: '2-digit',
    });
  } catch (e) {
    return '—';
  }
}
/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

/**
 * Truncate string to max length with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

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
/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

function getNestedValue(obj, path, defaultValue = null) {
  if (!obj || !path) return defaultValue;
  return path
    .split('.')
    .reduce(
      (acc, part) =>
        acc && acc[part] !== undefined ? acc[part] : defaultValue,
      obj
    );
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
    fetch("/api/intel").then(res => res.json()).catch(() => null),
    fetchOutputFile(CONFIG.files.kbOpportunities),
    fetchOutputFile(CONFIG.files.projects),
    fetchOutputFile(CONFIG.files.actionLog),
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
    state.metadata.generatedTimestamps.kbOpportunities =
      results[1].generated_at;
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
  /* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
---------------------------------------------------------------------------- */

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

  if (!container || !countEl) return;

  container.innerHTML = '';

  const events = state.intelEvents?.intel_events || [];
  countEl.textContent = events.length;

  if (events.length === 0) {
    container.innerHTML =
      '<div class="intel-empty"><div class="intel-empty-text">No intel events yet</div></div>';
    return;
  }

  events.forEach((evt) => {
    const row = document.createElement('div');
    row.className = 'intel-row';
    row.innerHTML = `
      <strong>${escapeHtml(evt.title || 'Event')}</strong>
      <div class="meta">${escapeHtml(evt.source || '')} • ${escapeHtml(evt.priority || '')}</div>
      <div class="desc">${escapeHtml(evt.description || '')}</div>
    `;
    container.appendChild(row);
  });
}

/* ----------------------------------------------------------------------------
   RENDERING — KB OPPORTUNITIES COLUMN
   ---------------------------------------------------------------------------- */
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
---------------------------------------------------------------------------- */

function renderKbOpportunities() {
  const container = document.getElementById('kb-opportunities-content');
  const countEl = document.getElementById('kb-opportunities-count');

  if (!container) return;

  const opportunities = getNestedValue(
    state.kbOpportunities,
    'opportunities',
    []
  );
  const displayOpportunities = opportunities.slice(0, CONFIG.maxItemsPerColumn);

  countEl.textContent = `${opportunities.length} total`;

  if (displayOpportunities.length === 0) {
    container.innerHTML = renderEmptyState('No KB opportunities yet');
    return;
  }

  container.innerHTML = displayOpportunities
    .map((opp, index) =>
      renderCard({
        columnId: 'kb',
        index,
        title: opp.title || opp.topic || 'Opportunity',
        meta: escapeHtml(opp.status || ''),
        urgency: opp.priority || opp.urgency || null,
        detailsHtml: `
      ${opp.id ? renderDetailRow('ID', opp.id) : ''}
      ${opp.gap_type ? renderDetailRow('Gap Type', opp.gap_type) : ''}
      ${opp.suggested_action ? renderDetailRow('Suggested', opp.suggested_action) : ''}
      ${opp.source_signals ? renderDetailRow('Signals', opp.source_signals) : ''}
      ${opp.created_at ? renderDetailRow('Created', formatTimestamp(opp.created_at)) : ''}
    `,
      })
    )
    .join('');

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

  container.innerHTML = displayProjects
    .map((project, index) =>
      renderCard({
        columnId: 'projects',
        index,
        title: project.name || project.title || 'Project',
        meta: escapeHtml(project.status || ''),
        urgency: project.priority || project.urgency || null,
        detailsHtml: `
      ${project.id ? renderDetailRow('ID', project.id) : ''}
      ${project.status ? renderDetailRow('Status', project.status) : ''}
      ${project.deliverables ? renderDetailRow('Deliverables', Array.isArray(project.deliverables) ? project.deliverables.join(', ') : project.deliverables) : ''}
      ${project.created_at ? renderDetailRow('Created', formatTimestamp(project.created_at)) : ''}
      ${project.updated_at ? renderDetailRow('Updated', formatTimestamp(project.updated_at)) : ''}
    `,
      })
    )
    .join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — RECENT RECOMMENDATIONS COLUMN
   ---------------------------------------------------------------------------- */
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
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

  container.innerHTML = displayActions
    .map((action, index) =>
      renderCard({
        columnId: 'recommendations',
        index,
        title: action.action || action.recommendation || 'Action',
        meta: formatTimestamp(action.timestamp || action.created_at),
        urgency: action.priority || action.urgency || null,
        showActions: true,
        detailsHtml: `
      ${action.id ? renderDetailRow('ID', action.id) : ''}
      ${action.rationale ? renderDetailRow('Rationale', action.rationale) : ''}
      ${action.status ? renderDetailRow('Status', action.status) : ''}
      ${action.source ? renderDetailRow('Source', action.source) : ''}
    `,
      })
    )
    .join('');

  attachExpandHandlers(container);
}

/* ----------------------------------------------------------------------------
   RENDERING — ACTION LOG TABLE (FULL LIST)
   ---------------------------------------------------------------------------- */
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
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
  container.innerHTML = actions
    .map(
      (action) => `
    <tr class="action-log-row" data-action-id="${escapeHtml(action.id || '')}">
      <td class="col-time">${formatTimestamp(action.timestamp || action.created_at)}</td>
      <td class="col-id">${escapeHtml(action.id || '—')}</td>
      <td class="col-action">
        <span class="action-type">${escapeHtml(action.action || action.type || '—')}</span>
        ${action.target ? `<span class="action-target">→ ${escapeHtml(action.target)}</span>` : ''}
      </td>
      <td class="col-rationale">${escapeHtml(action.rationale || '—')}</td>
    </tr>
  `
    )
    .join('');
}

/* ----------------------------------------------------------------------------
   RENDERING — SYSTEM METADATA
   ---------------------------------------------------------------------------- */
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
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
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
---------------------------------------------------------------------------- */

function renderSchemaVersions(versions) {
  const files = ['intelEvents', 'kbOpportunities', 'projects', 'actionLog'];
  const labels = {
    intelEvents: 'intel_events.json',
    kbOpportunities: 'kb_opportunities.json',
    projects: 'projects.json',
    actionLog: 'action_log.json',
  };

  return files
    .map((file) => {
      const version = versions[file] || '—';
      return `<div>${labels[file]}: ${escapeHtml(version)}</div>`;
    })
    .join('');
}
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
---------------------------------------------------------------------------- */

function renderGeneratedTimestamps(timestamps) {
  const files = ['intelEvents', 'kbOpportunities', 'projects'];
  const labels = {
    intelEvents: 'intel_events',
    kbOpportunities: 'kb_opportunities',
    projects: 'projects',
  };

  return files
    .map((file) => {
      const ts = timestamps[file];
      const formatted = ts ? formatTimestamp(ts) : '—';
      return `<div>${labels[file]}: ${formatted}</div>`;
    })
    .join('');
}
/* ----------------------------------------------------------------------------
   UI HELPERS — DOM Rendering & UI State
   (No event listeners here)
---------------------------------------------------------------------------- */

function renderLoadStatus(loadStatus) {
  const files = ['intelEvents', 'kbOpportunities', 'projects', 'actionLog'];
  const labels = {
    intelEvents: 'intel_events.json',
    kbOpportunities: 'kb_opportunities.json',
    projects: 'projects.json',
    actionLog: 'action_log.json',
  };

  return files
    .map((file) => {
      const status = loadStatus[file];
      const dotClass =
        status === 'success'
          ? 'success'
          : status === 'error'
            ? 'error'
            : 'pending';
      const statusText =
        status === 'success'
          ? 'Loaded'
          : status === 'error'
            ? 'Failed'
            : 'Pending';
      return `
      <div class="metadata-status">
        <span class="metadata-status-dot ${dotClass}"></span>
        <span>${labels[file]}: ${statusText}</span>
      </div>
    `;
    })
    .join('');
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
    detailsId: `card-details-${columnId}-${index}`,
  };
}

/**
 * Render a card with proper ARIA attributes
 * @param {object} params - Card parameters
 * @param {string} params.urgency - Optional urgency level (low, medium, high)
 * @param {boolean} params.showActions - Whether to show action affordances
 * @returns {string} HTML string
 */
function renderCard({
  columnId,
  index,
  title,
  meta,
  detailsHtml,
  urgency,
  showActions,
}) {
  const { headerId, detailsId } = generateCardIds(columnId, index);

  // Urgency badge HTML (if provided)
  const urgencyBadge = urgency
    ? `<span class="urgency-badge ${urgency}">${urgency}</span>`
    : '';

  // Action affordances (placeholder, disabled)
  const actionsHtml = showActions
    ? `<div class="card-actions">
        <button type="button" class="card-action-btn approve" disabled title="Approve (coming soon)">✓ Approve</button>
        <button type="button" class="card-action-btn dismiss" disabled title="Dismiss (coming soon)">✕ Dismiss</button>
      </div>`
    : '';

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
          <div class="intel-card-title">${escapeHtml(title)}${urgencyBadge}</div>
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
        ${actionsHtml}
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

  headers.forEach((header) => {
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
  links.forEach((link) => {
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
    expandedCards.forEach((expandedCard) => {
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

  // Hover should NOT change state (no accidental rotation)
  // Removed: mouseenter/mouseleave state changes

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
  return new Promise((resolve) => {
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
  return new Promise((resolve) => {
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
    .map((ex) => `<li>${ex}</li>`)
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
  document.querySelectorAll('.intel-column[data-section]').forEach((column) => {
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
  document
    .querySelectorAll('.secondary-section[data-section]')
    .forEach((section) => {
      const sectionKey = section.getAttribute('data-section');
      const header = section.querySelector('.secondary-section-header');
      const content = section.querySelector('.secondary-section-content');

      if (header && content && SECTION_EXPLANATIONS[sectionKey]) {
        // Insert explanation panel after header
        header.insertAdjacentHTML(
          'afterend',
          createExplanationPanel(sectionKey)
        );

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
  const current = getStoredTheme();
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_STORAGE_KEY, next);
  applyTheme(next);
}

/**
 * Initialize theme toggle button
 */
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', toggleTheme);
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
// Presence states: idle | thinking | observing | observed
const PRESENCE_STATES = {
  IDLE: 'idle',
  THINKING: 'thinking',
  OBSERVING: 'observing',
  OBSERVED: 'observed',
};

// Detect file:// protocol (local demo mode)
const IS_FILE_PROTOCOL = window.location.protocol === 'file:';

// Presence state copy (exact strings, verbatim)
const PRESENCE_COPY = {
  [PRESENCE_STATES.IDLE]: 'Waiting for input. No analysis in progress.',
  [PRESENCE_STATES.THINKING]:
    'Interpreting your message and preparing a draft response. No actions are being taken.',
  [PRESENCE_STATES.OBSERVING]:
    'Draft prepared. Awaiting your review or next instruction.',
  [PRESENCE_STATES.OBSERVED]:
    'Data loaded from manual ingest. Review dashboard for updates.',
};

// Presence state labels (short form for UI)
const PRESENCE_LABELS = {
  [PRESENCE_STATES.IDLE]: 'Idle',
  [PRESENCE_STATES.THINKING]: 'Thinking',
  [PRESENCE_STATES.OBSERVING]: 'Observing',
  [PRESENCE_STATES.OBSERVED]: 'Observed (manual)',
};

/* ----------------------------------------------------------------------------
   ACTIVE PROJECT FOCUS — Mock State (Local Only)
   ---------------------------------------------------------------------------- */

/**
 * Canonical ActiveProject (authoritative dashboard state)
 *
 * This is the ONLY shape the dashboard is allowed to render.
 * All legacy data, mock data, ReviewAgent output, or agent output
 * MUST be normalized into this form before reaching the UI.
 *
 * No inference happens here.
 *
 * @typedef {Object} ActiveProjectCanonical
 * @property {string} project_id - Stable project identifier
 * @property {string} title - Human-readable project name
 * @property {"build"|"research"|"ops"|"personal"} category - Project domain
 * @property {"active"|"paused"|"blocked"|"review"} status - Current lifecycle state
 * @property {number} confidence - 0.0–1.0 confidence score (agent-owned later)
 * @property {string} current_focus - What is being worked on right now
 * @property {string} next_action - Next concrete step
 * @property {string[]} risks - Explicit risks or blockers
 * @property {string} last_updated - ISO-8601 timestamp
 * @property {"manual"|"review_agent"|"agent"} source - Origin of this state
 */
/**
 * ReviewAgent output (read-only, non-authoritative)
 *
 * This represents an evaluation of a project, not ownership.
 * It may override confidence, risks, or status,
 * but never mutates project identity or structure.
 *
 * @typedef {Object} ReviewAgentAssessment
 * @property {number} confidence - 0.0–1.0 confidence score
 * @property {string[]} risks - Explicit risks or concerns
 * @property {"active"|"paused"|"blocked"|"review"} status
 * @property {string} rationale - Human-readable reasoning
 */

/** @type {ActiveProject} */
const mockActiveProject = {
  id: 'proj-freshdesk-ai-001',
  name: 'Freshdesk AI Support',
  domain: 'freshdesk-ai',
  status: 'active',
  description:
    'Intelligent support assistant for FutureBit customer tickets. Drafts responses, identifies KB gaps, and tracks recurring issues.',
  lastActivity: new Date().toISOString(),
  openItems: 3,
};
/**
 * Normalize legacy/mock project data into canonical ActiveProject.
 * No inference. Explicit defaults only.
 *
 * @param {Object} raw
 * @returns {ActiveProjectCanonical}
 */
function normalizeActiveProject(raw) {
  return {
    project_id: raw.id,
    title: raw.name,
    category: 'build',
    status: raw.status || 'active',
    confidence: 0.8, // stub — ReviewAgent will own later
    current_focus: raw.description || 'No focus defined',
    next_action: 'Pending ReviewAgent input',
    risks: [],
    last_updated: raw.lastActivity || new Date().toISOString(),
    source: 'manual',
  };
}

/**
 * Normalize ActiveProject to canonical form
 * @param {ActiveProject} project - Raw project object
 * @returns {ActiveProject} Normalized project
 */
function normalizeActiveProject(project) {
  return {
    id: project.id || '',
    name: project.name || 'Untitled Project',
    domain: project.domain || 'unknown',
    status: project.status || 'active',
    description: project.description || '',
    lastActivity: project.lastActivity || new Date().toISOString(),
    openItems: typeof project.openItems === 'number' ? project.openItems : 0,
  };
}

/**
 * Mock ReviewAgent assessment (read-only, advisory)
 * Follows ReviewAgent output contract from docs/review_agent_contract_v1.md
 */

/**
 * Apply ReviewAgent assessment to project (read-only merge)
 * Does NOT modify original project or assessment
 * @param {ActiveProject} project - Normalized project
 * @param {object} assessment - ReviewAgent assessment
 * @returns {ActiveProject} Project with review metadata attached
 */
function applyReviewAssessment(project, assessment) {
  return {
    ...project,
    _review: {
      recommendation: assessment.recommendation,
      totalFindings: assessment.summary.total_findings,
      highSeverity: assessment.summary.high_severity,
      disclaimer: assessment.disclaimer,
    },
  };
}

/**
 * Render the Active Project Focus panel
 * @param {ActiveProject|null} project - Project to display (null = empty state)
 */
function renderActiveProject(project) {
  const panel = document.getElementById('active-project-panel');
  if (!panel) return;

  if (!project) {
    panel.innerHTML = `
      <div class="active-project-empty">
        <div class="intel-empty-text">No project selected</div>
      </div>
    `;
    return;
  }
  /**
   * Apply ReviewAgent assessment to a canonical ActiveProject.
   * No inference. No mutation of identity fields.
   *
   * @param {ActiveProjectCanonical} project
   * @param {ReviewAgentAssessment} assessment
   * @returns {ActiveProjectCanonical}
   */
  function applyReviewAssessment(project, assessment) {
    return {
      ...project,
      confidence: assessment.confidence,
      risks: assessment.risks,
      status: assessment.status,
      source: 'review_agent',
    };
  }

  const statusClass =
    project.status === 'active'
      ? ''
      : project.status === 'paused'
        ? 'warning'
        : 'inactive';

  panel.innerHTML = `
    <div class="active-project-card">
      <div class="active-project-field">
        <span class="active-project-label">Project</span>
        <span class="active-project-value project-name">${escapeHtml(project.name)}</span>
      </div>
      <div class="active-project-field">
        <span class="active-project-label">Domain</span>
        <span class="active-project-value">${escapeHtml(project.domain)}</span>
      </div>
      <div class="active-project-field">
        <span class="active-project-label">Status</span>
        <span class="active-project-value project-status">
          <span class="status-dot ${statusClass}"></span>
          ${escapeHtml(project.status)}
        </span>
      </div>
      <div class="active-project-field">
        <span class="active-project-label">Open Items</span>
        <span class="active-project-value">${project.openItems}</span>
      </div>
      <div class="active-project-field active-project-description">
        <span class="active-project-label">Description</span>
        <span class="active-project-value">${escapeHtml(project.description)}</span>
      </div>
    </div>
  `;
}

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
    'your purpose',
  ];

  const triggered = purposeTriggers.some((trigger) =>
    lowered.includes(trigger)
  );

  if (triggered) {
    return formatResponse({
      presenceState: PRESENCE_STATES.OBSERVING,
      summary: 'You asked about my purpose and capabilities.',
      whatIDid: [
        'Explained my role: to serve, assist, and support you',
        'Clarified that I provide drafts, explanations, and recommendations',
        'Confirmed all decisions remain under your control',
      ],
      whatIDidNot: [
        'No data was persisted',
        'No external systems were contacted',
        'No actions were executed',
      ],
      nextStep: 'Share observations or context you would like me to consider.',
    });
  }

  return null;
} // ✅ CLOSE validateResponseSchema — CRITICAL

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
  'No external systems were modified',
];

/**
 * Validate response parameters against schema contract
 * @param {object} params - Response parameters
 * @throws {Error} If required fields are missing or invalid
 */

/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */
/**
 * Format a standardized Future Hause response
 * @param {object} payload
 * @returns {string}
 */
function formatResponse(payload) {
  return JSON.stringify(payload, null, 2);
}

function validateResponseSchema(params) {
  const { presenceState, summary, whatIDid, whatIDidNot } = params;

  // Required: presenceState must be valid
  if (
    !presenceState ||
    !Object.values(PRESENCE_STATES).includes(presenceState)
  ) {
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
    throw new Error(
      'Schema violation: "What I did NOT do" must be non-empty array'
    );
  } // ✅ end validateResponseSchema (must NOT wrap the rest of the file)

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
  /* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
  ---------------------------------------------------------------------------- */

  function formatResponse({
    presenceState,
    summary,
    whatIDid,
    whatIDidNot,
    nextStep,
    routingDecision,
  }) {
    // Validate schema compliance
    validateResponseSchema({ presenceState, summary, whatIDid, whatIDidNot });

    // Ensure mandatory guardrails are included in "What I did NOT do"
    const guardrails = [...whatIDidNot];
    MANDATORY_GUARDRAILS.forEach((guardrail) => {
      const alreadyIncluded = guardrails.some((item) =>
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
      '• Side Effects: None',
    ];

    // Include routing decision if provided
    if (routingDecision && typeof window.formatRoutingDecision === 'function') {
      lines.push(
        `• Routed To: ${window.formatRoutingDecision(routingDecision)}`
      );
    }

    lines.push(
      '',
      'Summary:',
      `• ${summary}`,
      '',
      'What I did:',
      ...whatIDid.map((item) => `• ${item}`),
      '',
      'What I did NOT do:',
      ...guardrails.map((item) => `• ${item}`)
    );

    // Optional: Next step (only if provided)
    if (nextStep && typeof nextStep === 'string' && nextStep.trim() !== '') {
      lines.push('', 'Next suggested step (optional):', `• ${nextStep}`);
    }

    return lines.join('\n');
  }
} // ✅ CRITICAL: close the unintended wrapper that was swallowing everything below (e.g., validateResponseSchema)

/* =============================================================================
   LLM + MESSAGE PANEL WIRING (TOP-LEVEL, GLOBAL)
   ============================================================================= */

/**
 * Call Ollama for draft generation (ONLY when allow_draft === true)
 * @param {string} prompt - The user's draft request
 * @returns {Promise<string>} Draft content from Ollama
 */
/* ----------------------------------------------------------------------------
   BUSINESS / ORCHESTRATION LOGIC
   (Decision-making, routing, coordination)
---------------------------------------------------------------------------- */

async function callOllama(prompt) {
  try {
    const res = await fetch('http://127.0.0.1:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'mistral:latest',
        prompt: prompt,
        stream: false,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const data = await res.json();

    // Ollama returns { response: "...", done: true }
    if (typeof data.response === 'string') {
      return data.response.trim();
    }

    throw new Error('Unexpected Ollama response format');
  } catch (err) {
    console.error('Ollama call failed:', err);
    return `[Ollama error: ${err.message}]`;
  }
}

/**
 * Render draft content to the Draft Work section
 * @param {Object|string} draft - Draft object or legacy string
 * @param {string} draft.draft_id - Unique draft identifier
 * @param {string} draft.body - Draft content
 * @param {string} draft.status - Draft status (drafted|reviewing|flagged|reviewed|approved|rejected)
 * @param {string[]} [draft.tags] - Optional tags
 */
function renderDraftWork(draft) {
  const entriesContainer = document.getElementById('draft-worklog-entries');
  if (!entriesContainer) return;

  // Handle legacy string input for backwards compatibility
  if (typeof draft === 'string') {
    draft = { body: draft, status: 'drafted' };
  }

  const timestamp = new Date().toLocaleTimeString();
  const status = draft.status || 'drafted';
  const statusClass = `draft-status-${status}`;
  const tagsHtml = draft.tags?.length
    ? `<div class="draft-entry-tags">${draft.tags.map(t => `<span class="draft-tag">${escapeHtml(t)}</span>`).join('')}</div>`
    : '';

  const entryHtml = `
    <div class="draft-worklog-entry" data-draft-id="${escapeHtml(draft.draft_id || '')}">
      <div class="draft-entry-header">
        <span class="draft-entry-time">${timestamp}</span>
        <span class="draft-badge">DRAFT</span>
        <span class="draft-status-badge ${statusClass}">${escapeHtml(status)}</span>
      </div>
      ${tagsHtml}
      <div class="draft-entry-content">${(draft.body || '').replace(/\n/g, '<br>')}</div>
    </div>
  `;

  // Store current draft_id for review operations
  if (draft.draft_id) {
    state.currentDraftId = draft.draft_id;
  }

  // Clear empty state and add entry
  entriesContainer.innerHTML = entryHtml;

  // Enable action buttons
  const copyBtn = document.getElementById('copy-draft-btn');
  const exportBtn = document.getElementById('export-draft-btn');
  if (copyBtn) copyBtn.disabled = false;
  if (exportBtn) exportBtn.disabled = false;
}

/**
 * Fetch draft by ID from authoritative store
 * @param {string} draftId - Draft ID to fetch
 * @returns {Promise<Object>} Draft object with { draft_id, body, status, tags }
 */
async function fetchDraftById(draftId) {
  const res = await fetch(`/api/draft/${draftId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch draft: ${res.status}`);
  }
  return res.json();
}

/**
 * Send message to /api/send and return draft_id
 * @param {string} text - User message
 * @returns {Promise<Object>} Response with { draft_id, response }
 */
async function sendToApi(text) {
  const res = await fetch('/api/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text }),
  });
  if (!res.ok) {
    throw new Error(`Send failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Send message to LLM and get response
 *
 * Routing contract: docs/llm-routing.md
 * Router implementation: ui/llmRouter.js
 *
 * Intent handling:
 * - draft_request: Call Ollama → render in Draft Work
 * - question: Explanatory response (no Draft Work)
 * - meta: Static explanation of FutureHause
 * - action: Refusal + explanation of boundaries
 * - observation: Acknowledgement only
 *
 * @param {string} message - User's message
 * @returns {Promise<string>} Response in mandatory schema format
 */
async function sendToLLM(message) {
  // Check for purpose disclosure first
  const disclosure = checkPurposeDisclosure(message);
  if (disclosure) {
    return disclosure;
  }

  // Route input to determine intent
  const routingDecision =
    typeof window.routeLLM === 'function' ? window.routeLLM(message) : null;

  if (!routingDecision) {
    return formatResponse({
      presenceState: PRESENCE_STATES.IDLE,
      summary: 'Router unavailable.',
      whatIDid: ['Attempted to classify intent'],
      whatIDidNot: ['Could not route — llmRouter.js not loaded'],
      nextStep: 'Check that llmRouter.js is loaded correctly.',
    });
  }

  const { intent, allow_draft, must_answer_directly } = routingDecision;

  // ═══════════════════════════════════════════════════════════════
  // INTENT: draft_request — Call Ollama, render in Draft Work
  // ═══════════════════════════════════════════════════════════════
  if (intent === 'draft_request' && allow_draft) {
    const ollamaResponse = await callOllama(message);
    renderDraftWork(ollamaResponse);
    // Draft renders ONLY to Draft Work — return null to skip Future Hause Response
    return null;
  }

  // ═══════════════════════════════════════════════════════════════
  // INTENT: question — Explanatory response (no Draft Work)
  // ═══════════════════════════════════════════════════════════════
  if (intent === 'question') {
    return formatResponse({
      presenceState: PRESENCE_STATES.OBSERVING,
      summary: 'This appears to be a question.',
      whatIDid: [
        'Classified intent as question',
        'Prepared explanatory response',
      ],
      whatIDidNot: [
        "No Ollama call (questions don't generate drafts)",
        'No data persistence',
        'No action log entries',
      ],
      nextStep:
        'For questions about FutureHause, ask "What is Future Hause?". For draft requests, try "Draft a work entry for..."',
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // INTENT: meta — Static explanation of FutureHause
  // ═══════════════════════════════════════════════════════════════
  if (intent === 'meta') {
    return formatResponse({
      presenceState: PRESENCE_STATES.OBSERVING,
      summary: 'Future Hause is a local support intelligence assistant.',
      whatIDid: [
        'Recognized meta/identity question',
        'Provided system explanation',
      ],
      whatIDidNot: ['No Ollama call needed', 'No data persistence'],
      nextStep:
        'Future Hause observes signals, drafts work entries, and helps organize intelligence. It never takes autonomous action.',
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // INTENT: action — Refusal + explanation of boundaries
  // ═══════════════════════════════════════════════════════════════
  if (intent === 'action') {
    return formatResponse({
      presenceState: PRESENCE_STATES.IDLE,
      summary: 'Action requests require explicit human approval.',
      whatIDid: [
        'Classified intent as action request',
        'Declined autonomous execution',
      ],
      whatIDidNot: [
        'Did NOT execute the requested action',
        'No commits, pushes, or file writes',
        'No API calls or external changes',
        'No state mutations',
      ],
      nextStep:
        'Future Hause is an analyst, not an actor. It can draft content for your review, but actions must be taken by you.',
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // INTENT: observation — Acknowledgement only
  // ═══════════════════════════════════════════════════════════════
  return formatResponse({
    presenceState: PRESENCE_STATES.OBSERVING,
    summary: 'Observation received and noted.',
    whatIDid: ['Classified intent as observation', 'Acknowledged your input'],
    whatIDidNot: [
      "No Ollama call (observations don't generate drafts)",
      'No data saved or persisted',
      'No action log entries',
      'No auto-promotion to KB or Projects',
    ],
    nextStep:
      'To generate a draft, try: "Draft a work entry for [task description]"',
  });
}

// Update presence: Idle → Thinking
function renderFutureHauseResponse(response) {
  const panel = document.getElementById('future-hause-response');
  if (!panel) {
    console.error('[Future Hause] Response panel missing from DOM');
    return;
  }

  const content = panel.querySelector('.future-hause-response-content');
  if (!content) return;

  // Coach Mode — render with coach styling
  if (response?.mode === 'coach') {
    content.innerHTML = `
      <div class="coach-response">
        <div class="coach-response-label">Coach Feedback</div>
        <div class="coach-response-text">${escapeHtml(response.content || '')}</div>
      </div>
    `;
  }
  // Everything else — plain text or JSON fallback
  else {
    content.textContent =
      typeof response === 'string' ? response : JSON.stringify(response, null, 2);
  }

  panel.hidden = false;
}

async function handleUserSubmission(text) {
  // 1) Presence: Idle → Thinking
  setPresenceState?.(PRESENCE_STATES?.THINKING || 'thinking');

  try {
    // 2) Send to /api/send
    const sendResult = await sendToApi(text);

    // 3) Fetch authoritative draft state and render to Draft Work
    if (sendResult.draft_id) {
      const draft = await fetchDraftById(sendResult.draft_id);
      renderDraftWork(draft);
    }

    // 4) Render non-draft response to Future Hause Response if present
    if (sendResult.response) {
      renderFutureHauseResponse(sendResult.response);
    }
  } catch (err) {
    console.error('[Future Hause] handleUserSubmission failed:', err);
    renderFutureHauseResponse(`Error: ${err?.message || err}`);
  }

  // 5) Presence: Thinking → Observing
  setPresenceState?.(PRESENCE_STATES?.OBSERVING || 'observing');
}

/**
 * Wire up notes form submission handler
 */
/* ----------------------------------------------------------------------------
   WIRING — Event Listeners Only
   (No logic, no rendering)
---------------------------------------------------------------------------- */

function wireNotesSubmit() {
  // Support both legacy IDs and current class-based selectors
  const textarea =
    document.getElementById('notes-textarea') ||
    document.querySelector('.notes-textarea');
  const submitBtn =
    document.getElementById('notes-submit') ||
    document.getElementById('submit-btn');

  if (!textarea || !submitBtn) return;

  submitBtn.addEventListener('click', async () => {
    const text = textarea.value.trim();
    if (!text) return;

    // 1) Action log (append into schema-shaped actionLog.actions array)
    if (!state.actionLog || typeof state.actionLog !== 'object') {
      state.actionLog = { schema_version: '1.0', actions: [] };
    }
    if (!Array.isArray(state.actionLog.actions)) {
      state.actionLog.actions = [];
    }

    state.actionLog.actions.push({
      id: `manual-${Date.now()}`,
      type: 'manual',
      content: text,
      timestamp: new Date().toISOString(),
    });

    state.loadStatus.actionLog = 'success';
    renderActionLogTable();

    // 2) Drive orchestration + response
    await handleUserSubmission(text);

    // 3) Clear input
    textarea.value = '';
  });
}

/**
 * Coach Mode — Direct, practical writing coach
 * Manual trigger only. POSTs to /api/review.
 * After review completes, re-fetches authoritative draft state.
 */
const COACH_PROMPT = `You are a direct, practical writing coach for support and documentation work.

When given draft text:
1. Identify the single biggest improvement opportunity
2. Explain why it matters (1 sentence)
3. Show a concrete rewrite of the weakest section
4. Stop. Do not pad with praise or caveats.

Be brief. Be specific. Be useful.`;

function wireCoachMode() {
  const coachBtn = document.getElementById('coach-btn');
  const textarea = document.getElementById('notes-textarea');
  const responsePanel = document.getElementById('notes-response-panel');
  const responseContent = document.getElementById('notes-response-content');

  if (!coachBtn || !textarea) return;

  coachBtn.addEventListener('click', async () => {
    // Use current draft_id if available, otherwise use textarea content
    const draftId = state.currentDraftId;
    const draftText = textarea.value.trim();

    if (!draftId && !draftText) return;

    // Show loading state
    coachBtn.disabled = true;
    coachBtn.textContent = 'Reviewing...';

    try {
      const response = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          draft_id: draftId || `draft-${Date.now()}`,
          draft_text: draftText,
          system_prompt: COACH_PROMPT,
        }),
      });

      if (!response.ok) {
        throw new Error(`Review API error: ${response.status}`);
      }

      const data = await response.json();
      const reviewResponse =
        data.response || data.content || 'No response received.';

      // Render review response in Future Hause Response panel
      renderFutureHauseResponse({
        mode: 'coach',
        content: reviewResponse,
      });

      // Re-fetch authoritative draft state and re-render Draft Work
      if (draftId) {
        const updatedDraft = await fetchDraftById(draftId);
        renderDraftWork(updatedDraft);
      }

      // Show panel if hidden
      if (responsePanel) {
        responsePanel.hidden = false;
      }
    } catch (err) {
      console.error('[Review Mode]', err);
      if (responseContent) {
        responseContent.innerHTML = `
          <div class="coach-response coach-error">
            <div class="coach-response-label">Review Error</div>
            <div class="coach-response-text">${escapeHtml(err.message)}</div>
          </div>
        `;
      }
      if (responsePanel) {
        responsePanel.hidden = false;
      }
    } finally {
      coachBtn.disabled = false;
      coachBtn.textContent = 'Coach';
    }
  });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
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
   COMMAND CHIPS — Quick Action Buttons (UI-only)
   ---------------------------------------------------------------------------- */

/**
 * Wire up command chip click handlers
 * Populates textarea with chip command text
 */
function wireCommandChips() {
  const chips = document.querySelectorAll('.command-chip');
  const textarea = document.getElementById('notes-textarea');

  if (!textarea) return;

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const command = chip.getAttribute('data-command');
      if (command) {
        textarea.value = command;
        textarea.focus();
      }
    });
  });
}

/* ----------------------------------------------------------------------------
   RELATIVE TIME FORMATTING — UI Helper
   ---------------------------------------------------------------------------- */
/* ----------------------------------------------------------------------------
   PURE HELPERS — No DOM, No State
   Safe everywhere
---------------------------------------------------------------------------- */

function formatRelativeTime(date) {
  const now = new Date();
  const then = date instanceof Date ? date : new Date(date);
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin} min${diffMin > 1 ? 's' : ''} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  return formatTimestamp(then.toISOString());
}

function updateLastUpdatedTime() {
  const el = document.getElementById('last-updated-time');
  if (el) {
    el.textContent = `Last updated: ${formatRelativeTime(new Date())}`;
  }
}

/* ----------------------------------------------------------------------------
   INGEST DRY-RUN — Manual, User-Initiated Demo
   ---------------------------------------------------------------------------- */

function generateMockIntelEvents() {
  const ingestNow = new Date().toISOString();
  return {
    schema_version: '1.0',
    generated_at: ingestNow,
    events: [
      {
        id: 'evt-001',
        type: 'community_discussion',
        title: 'Apollo BTC mining setup questions',
        source: 'Reddit r/FutureBit',
        detected_at: ingestNow,
        description: 'User asking about optimal settings for Apollo BTC miner',
        priority: 'medium',
      },
    ],
  };
}

function generateMockKbOpportunities() {
  const metadataNow = new Date().toISOString();
  return {
    schema_version: '1.0',
    generated_at: metadataNow,
    opportunities: [
      {
        id: 'kb-001',
        title: 'PSU Requirements Guide',
        topic: 'Hardware Setup',
        created_at: metadataNow,
        priority: 'medium',
      },
    ],
  };
}

function generateMockProjects() {
  const projectsNow = new Date().toISOString();
  return {
    schema_version: '1.0',
    generated_at: projectsNow,
    projects: [
      {
        id: 'proj-001',
        name: 'Freshdesk AI Support',
        status: 'active',
        created_at: projectsNow,
        updated_at: projectsNow,
        priority: 'high',
      },
    ],
  };
}

function generateMockActionLog() {
  return {
    schema_version: '1.0',
    actions: [],
  };
}

async function runIngestDryRun() {
  const intelEvents = generateMockIntelEvents();
  const kbOpportunities = generateMockKbOpportunities();
  const mockProjects = generateMockProjects();
  const actionLog = generateMockActionLog();

  state.intelEvents = intelEvents;
  state.loadStatus.intelEvents = 'success';
  state.metadata.schemaVersions.intelEvents = intelEvents.schema_version;
  state.metadata.generatedTimestamps.intelEvents = intelEvents.generated_at;

  state.kbOpportunities = kbOpportunities;
  state.loadStatus.kbOpportunities = 'success';
  state.metadata.schemaVersions.kbOpportunities =
    kbOpportunities.schema_version;
  state.metadata.generatedTimestamps.kbOpportunities =
    kbOpportunities.generated_at;

  state.projects = mockProjects;
  state.loadStatus.projects = 'success';
  state.metadata.schemaVersions.projects = mockProjects.schema_version;
  state.metadata.generatedTimestamps.projects = mockProjects.generated_at;

  state.actionLog = actionLog;
  state.loadStatus.actionLog = 'success';
  state.metadata.schemaVersions.actionLog = actionLog.schema_version;

  renderIntelEvents();
  renderKbOpportunities();
  renderProjects();
  renderRecentRecommendations();
  renderActionLogTable();
  renderSystemMetadata();

  updateLastUpdatedTime();
  setPresenceState(PRESENCE_STATES.OBSERVED);
}

function wireIngestDryRun() {
  const btn = document.getElementById('ingest-dry-run-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = 'Running...';

    try {
      await runIngestDryRun();
    } finally {
      btn.disabled = false;
      btn.innerHTML = `Run ingest (dry-run)<span class="ingest-btn-hint">Manual · Non-persistent · Safe</span>`;
    }
  });
}

/* ----------------------------------------------------------------------------
   INITIALIZATION
   ---------------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle?.();

  setIconState?.('idle');
  setPresenceState?.(PRESENCE_STATES?.IDLE || 'idle');

  wireIconEvents?.();
  wireExplanationPanels?.();
  wireNotesSubmit?.();
  wireCoachMode?.();
  wireCommandChips?.();
  wireIngestDryRun?.();

  updateLastUpdatedTime?.();

  if (IS_FILE_PROTOCOL) {
    console.warn(
      '[Future Hause] file:// detected — auto-load disabled; running ingest demo'
    );
    runIngestDryRun?.();
    return;
  }

  loadAllData?.().then(() => {
    const hasErrors = Object.values(state?.loadStatus || {}).some(
      (s) => s === 'error'
    );
    if (hasErrors) {
      setIconState?.('error');
      setTimeout(() => setIconState?.('idle'), 3000);
    }
  });
});
