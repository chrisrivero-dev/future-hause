let selectedJobId = null;

async function fetchJobs() {
  const r = await fetch('/api/jobs');
  const data = await r.json();
  return data.jobs || [];
}

function renderJobs(jobs) {
  const el = document.getElementById('jobs');
  el.innerHTML = '';

  jobs
    .sort((a, b) => b.attempt - a.attempt)
    .forEach((j) => {
      const div = document.createElement('div');
      div.className = 'job';
      div.onclick = () => selectJob(j.id);
      div.innerHTML = `
        <b>${j.status}</b> <small>attempt ${j.attempt}</small><br/>
        <small>${j.id}</small><br/>
        <small>files: ${j.files}</small><br/>
        <div>${escapeHtml(j.prompt).slice(0, 120)}${j.prompt.length > 120 ? '…' : ''}</div>
      `;
      el.appendChild(div);
    });
}

function escapeHtml(s) {
  return s
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

async function selectJob(jobId) {
  selectedJobId = jobId;
  const jobs = await fetchJobs();
  const job = jobs.find((j) => j.id === jobId);
  if (!job) return;

  document.getElementById('meta').textContent =
    `status=${job.status} | attempt=${job.attempt} | files=${job.files}`;

  document.getElementById('patch').textContent = job.patch || '';
  document.getElementById('error').textContent = job.last_error || '';

  const canReview = job.status === 'needs_review';
  document.getElementById('apply').disabled = !canReview;
  document.getElementById('reject').disabled = !canReview;
}

async function refreshLoop() {
  const jobs = await fetchJobs();
  renderJobs(jobs);

  if (selectedJobId) {
    await selectJob(selectedJobId);
  }
  setTimeout(refreshLoop, 1000);
}

document.getElementById('run').onclick = async () => {
  const prompt = document.getElementById('prompt').value.trim();
  const files = document.getElementById('files').value.trim();

  const r = await fetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, files }),
  });

  if (!r.ok) {
    const err = await r.text();
    alert(err);
    return;
  }

  const data = await r.json();
  selectedJobId = data.id;
};

document.getElementById('apply').onclick = async () => {
  if (!selectedJobId) return;
  const r = await fetch(`/api/jobs/${selectedJobId}/apply`, { method: 'POST' });
  if (!r.ok) alert(await r.text());
};

document.getElementById('reject').onclick = async () => {
  if (!selectedJobId) return;
  const r = await fetch(`/api/jobs/${selectedJobId}/reject`, {
    method: 'POST',
  });
  if (!r.ok) alert(await r.text());
};

refreshLoop();
