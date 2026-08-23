const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

let activeBatch = 0;
let floor = 0.06;
let requestToken = 0;

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function relevance(value) {
  return Number(value || 0).toFixed(2);
}

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function assignmentRow(row) {
  const grade = Number(row.draft_relevance ?? 0);
  return `
    <div class="assignment">
      <div>
        <div class="assignment-intent">
          <span class="intent-pill">${row.intent}</span>
          <span class="assignment-meta">→ ${row.responder}</span>
        </div>
        <p>${row.query}</p>
        <div class="assignment-meta">lexical similarity ${Number(row.similarity).toFixed(3)}</div>
      </div>
      <div class="grade g${grade}" title="Draft human relevance grade">${grade}/3</div>
    </div>`;
}

function renderMethod(method, prefix) {
  $(`#${prefix}Metrics`).innerHTML = [
    metric('Coverage', pct(method.coverage)),
    metric('Mean relevance', relevance(method.mean_draft_relevance)),
    metric('Total relevance', method.total_draft_relevance),
  ].join('');

  const container = $(`#${prefix}Assignments`);
  if (!method.assignments?.length) {
    container.innerHTML = '<div class="assignment-empty">No assignment cleared the current topic floor.</div>';
    return;
  }
  container.innerHTML = method.assignments.map(assignmentRow).join('');
}

function renderSummary(greedy, globalMethod) {
  const coverageDelta = globalMethod.coverage - greedy.coverage;
  const relevanceDelta = globalMethod.mean_draft_relevance - greedy.mean_draft_relevance;
  const totalDelta = globalMethod.total_draft_relevance - greedy.total_draft_relevance;

  let title;
  let explanation;
  let className = 'mixed';

  if (coverageDelta > 0 && relevanceDelta >= 0) {
    title = 'Global allocation improves coverage without reducing average draft relevance in this batch.';
    explanation = 'This is the strongest case for batch-level allocation, but it is still a development benchmark until labels are reviewed and frozen.';
    className = 'positive';
  } else if (coverageDelta > 0 && relevanceDelta < 0) {
    title = 'Global allocation serves more requests, but the extra coverage costs some average match quality.';
    explanation = 'This is the tradeoff NIYET must manage. Raising the topic floor can remove weak candidate edges before optimization.';
  } else if (coverageDelta === 0 && relevanceDelta > 0) {
    title = 'Coverage is unchanged, but global allocation improves the average match quality in this batch.';
    explanation = 'The optimizer is using the same responder capacity differently rather than simply increasing the number of assignments.';
    className = 'positive';
  } else {
    title = 'Global allocation is not better on every batch. This case stays visible on purpose.';
    explanation = 'The lab is designed to expose failure cases and threshold sensitivity instead of selecting only examples where NIYET wins.';
  }

  $('#summaryTitle').textContent = title;
  $('#summaryText').textContent = explanation;

  const sign = totalDelta > 0 ? '+' : '';
  const tradeoff = $('#tradeoff');
  tradeoff.className = `tradeoff ${className}`;
  tradeoff.innerHTML = `<strong>${sign}${totalDelta}</strong><span>draft relevance points vs greedy</span>`;
}

function render(data) {
  const [greedy, globalMethod] = data.methods;
  renderMethod(greedy, 'greedy');
  renderMethod(globalMethod, 'global');
  renderSummary(greedy, globalMethod);

  const status = $('#labApiStatus');
  status.textContent = `live API · ${data.review_status}`;
  status.className = 'pipeline-state ok';
  document.title = `NIYET Allocation Lab · Batch ${data.batch_index + 1}`;
}

function renderError(message) {
  $('#summaryTitle').textContent = 'The experiment API is unavailable.';
  $('#summaryText').textContent = 'No fallback metrics are shown. Reload after the live backend is available.';
  $('#tradeoff').innerHTML = '<strong>—</strong><span>no synthetic fallback</span>';
  ['greedyMetrics', 'globalMetrics'].forEach((id) => {
    $(`#${id}`).innerHTML = metric('Status', 'offline');
  });
  ['greedyAssignments', 'globalAssignments'].forEach((id) => {
    $(`#${id}`).innerHTML = `<div class="assignment-empty">${message}</div>`;
  });
  const status = $('#labApiStatus');
  status.textContent = 'API unavailable';
  status.className = 'pipeline-state error';
}

async function runExperiment() {
  const token = ++requestToken;
  $('.lab-shell').classList.add('loading');
  const url = `/api/experiment?batch=${activeBatch}&floor=${floor.toFixed(2)}`;

  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (token !== requestToken) return;
    render(data);
  } catch (error) {
    if (token !== requestToken) return;
    renderError(error instanceof Error ? error.message : 'Unknown API error');
  } finally {
    if (token === requestToken) $('.lab-shell').classList.remove('loading');
  }
}

$$('#batchTabs button').forEach((button) => {
  button.addEventListener('click', () => {
    activeBatch = Number(button.dataset.batch);
    $$('#batchTabs button').forEach((item) => item.classList.toggle('active', item === button));
    runExperiment();
  });
});

const floorRange = $('#floorRange');
let floorTimer;
floorRange.addEventListener('input', () => {
  floor = Number(floorRange.value);
  $('#floorValue').textContent = floor.toFixed(2);
  clearTimeout(floorTimer);
  floorTimer = setTimeout(runExperiment, 120);
});

runExperiment();
