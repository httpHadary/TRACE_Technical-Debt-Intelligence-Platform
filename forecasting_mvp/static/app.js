'use strict';
const api = '/api/mvp/v1';
const el = id => document.getElementById(id);
let bundles = [], serial = 0;
const text = (tag, value, cls) => { const node = document.createElement(tag); node.textContent = value; if (cls) node.className = cls; return node; };
const fmt = value => value === null || value === undefined ? 'Unavailable' : Number(value).toLocaleString(undefined, {maximumFractionDigits: 2});
const signed = value => value === null || value === undefined ? 'Incomparable' : `${value > 0 ? '+' : ''}${fmt(value)}`;
async function get(path) { const response = await fetch(api + path); const data = await response.json(); if (!response.ok) throw Error(data.error || 'Evidence unavailable'); return data; }
function options(node, items) { node.replaceChildren(); for (const [value, label] of items) { const option = text('option', label); option.value = value; node.append(option); } }
function error(exc) { el('status').textContent = exc.message; el('status').className = 'error'; }
function card(label, value, detail) { const node = text('article', '', 'metric'); node.append(text('p', label), text('strong', value), text('small', detail)); return node; }
async function selectBundle() {
  serial++;
  const identity = el('bundle').value;
  el('metrics').replaceChildren(); el('forecast').replaceChildren(); el('history').replaceChildren();
  const bundle = bundles.find(b => b.bundle_id === identity);
  const meta = bundle.metadata;
  const source = meta.source || meta.registration;
  el('provenance').replaceChildren(text('h2', meta.evidence || 'Unvalidated evidence'), text('p', JSON.stringify(source, null, 2), 'source'));
  const units = bundle.kind === 'HISTORICAL_PRINCIPAL' ? {revision_step: [3,4,12]} : null;
  const repos = await get(`/bundles/${identity}/repositories`);
  options(el('repository'), repos.map(r => [r, r]));
  // Current source may register either or both clocks. Probe only registered contracts through API.
  let available = [];
  for (const [unit, values] of Object.entries(units || {revision_step:[3,4,12],elapsed_day:[30,60,90]})) {
    const rows = await get(`/bundles/${identity}/repositories/${encodeURIComponent(repos[0])}/forecasts?horizon_unit=${unit}&horizon=${values[0]}`);
    if (Array.isArray(rows)) available.push(...values.map(h => [`${unit}:${h}`, `${h} ${unit === 'revision_step' ? 'revision steps' : 'elapsed days'}`]));
  }
  options(el('horizon'), available);
  await refresh();
}
async function refresh() {
  const token = ++serial;
  const identity = el('bundle').value, repo = el('repository').value;
  const [unit, h] = el('horizon').value.split(':');
  const base = `/bundles/${identity}/repositories/${encodeURIComponent(repo)}`;
  const query = `?model=persistence&horizon_unit=${unit}&horizon=${h}`;
  el('status').textContent = 'Verifying evidence…';
  const [history, forecasts, evaluations, summaries] = await Promise.all([get(base+'/history'), get(base+'/forecasts'+query), get(base+'/evaluations'+query), get(base+'/evaluations'+query+'&summary=true')]);
  if (token !== serial) return;
  const f = forecasts[forecasts.length-1], e = evaluations.find(r => r.forecast_id === f.forecast_id), origin = history.find(r => r.observation_id === f.origin_observation_id) || history.find(r => r.revision === f.origin_revision);
  el('metrics').replaceChildren(card('Origin stock', fmt(f.origin_stock_minutes), 'estimated minutes'), card('Measured change', signed(origin?.measured_change_minutes), origin?.change_status || 'Unavailable'), card('Projected change', signed(f.predicted_change_minutes), 'persistence · estimated minutes'), card('Actual / absolute error', e.status === 'PENDING' ? 'Pending' : `${fmt(e.actual_minutes)} / ${fmt(e.absolute_error_minutes)}`, e.status));
  const summary = summaries[0];
  el('summary').replaceChildren(text('h2', 'Bundle evaluation coverage'), text('p', `${summary.measured_actuals} measured / ${summary.available_forecasts} available forecasts · ${summary.pending} pending · ${summary.unavailable} unavailable. Current accuracy unvalidated.`));
  for (const [name, report] of Object.entries(summary.subsets)) el('summary').append(text('p', `${name}: ${report.count} endpoints · repository macro MAE / RMSE ${fmt(report.macro_mae_minutes)} / ${fmt(report.macro_rmse_minutes)} min · pooled MAE / RMSE ${fmt(report.pooled_mae_minutes)} / ${fmt(report.pooled_rmse_minutes)} min`));
  el('forecast').replaceChildren();
  for (const row of forecasts) { const ev = evaluations.find(e => e.forecast_id === row.forecast_id); const line = text('div', '', 'forecast-row'); line.append(text('span', row.origin_utc || row.origin_commit_date), text('strong', `${fmt(row.origin_stock_minutes)} → ${fmt(row.prediction_minutes)} min`), text('span', `${row.horizon} ${row.horizon_unit} · ${row.unavailable_reason || ev.status}`), text('small', `Actual ${fmt(ev.actual_minutes)} · signed error ${ev.error_minutes === null ? 'Pending' : signed(ev.error_minutes)} · ${row.endpoint_utc || ev.endpoint_commit_date || ev.observed_utc || 'revision endpoint pending'}${ev.elapsed_commit_date_days === undefined ? '' : ` · ${ev.elapsed_commit_date_days} elapsed commit-date days`}`)); el('forecast').append(line); }
  el('history').replaceChildren();
  for (const row of history) { const tr = document.createElement('tr'); const values = [`${row.revision.slice(0,12)} / ${row.observed_utc || row.commit_date}`, ...['maintainability','reliability','security'].map(k => fmt(row.components?.[k])), fmt(row.stock_minutes), signed(row.measured_change_minutes), row.change_status]; values.forEach(value => tr.append(text('td', value))); el('history').append(tr); }
  el('status').className = ''; el('status').textContent = `${forecasts.length} verified persistence endpoint(s) · ${unit === 'revision_step' ? 'Revision steps are not calendar days' : 'Exact elapsed UTC days'} · Current accuracy unvalidated`;
}
el('bundle').addEventListener('change', () => selectBundle().catch(error));
for (const id of ['repository','horizon']) el(id).addEventListener('change', () => refresh().catch(error));
get('/bundles').then(async data => { bundles = data; options(el('bundle'), data.map(b => [b.bundle_id, `${b.kind} · ${b.bundle_id.slice(0,12)}`])); if (!data.length) throw Error('No complete bundles in this registry'); await selectBundle(); }).catch(error);
