function formatDate(iso){
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function pill(value){
  return `<span class="pill ${value ? 'warn' : 'ok'}">${value ? '1' : '0'}</span>`;
}

function humidityBar(h){
  const cl = (h < 10 || h > 90) ? 'warn' : 'ok';
  const width = Math.max(0, Math.min(100, h));
  return `
  <div class="meter ${cl}">
    <div class="fill" style="width:${width}%"></div>
    <div class="value">${h.toFixed(1)}%</div>
  </div>`;
}

function updateTable(rows) {
  const tbody = document.querySelector('#readings-table tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.sensor}</td>
      <td>${r.name || ''}</td>
      <td>${humidityBar(r.humidity_pct)}</td>
      <td>${pill(r.tilt)}</td>
      <td>${pill(r.vibration)}</td>
      <td>${formatDate(r.recorded_at)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function updateCards(rows){
  const grid = document.getElementById('sensor-grid');
  if (!grid) return;
  grid.innerHTML = '';
  rows.forEach(r => {
    const warn = (r.humidity_pct < 10 || r.humidity_pct > 90) || r.tilt || r.vibration;
    const card = document.createElement('div');
    card.className = `card ${warn ? 'card-warn' : 'card-ok'}`;
    card.innerHTML = `
      <div class="card-head">
        <h4>${r.name || r.sensor}</h4>
        <span class="badge ${warn ? 'warn' : 'ok'}">${warn ? 'ALERTA' : 'OK'}</span>
      </div>
      <div class="card-body">
        <div class="kpi">
          <span class="kpi-label">Humedad</span>
          ${humidityBar(r.humidity_pct)}
        </div>
        <div class="kpi">
          <span class="kpi-label">Inclinación</span>
          ${pill(r.tilt)}
        </div>
        <div class="kpi">
          <span class="kpi-label">Vibración</span>
          ${pill(r.vibration)}
        </div>
      </div>
      <div class="card-foot">${formatDate(r.recorded_at)}</div>
    `;
    grid.appendChild(card);
  });
}

async function fetchLatest() {
  try {
    const res = await fetch('/api/latest-readings/', { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    const rows = data.results || [];
    updateCards(rows);
    updateTable(rows);
  } catch (e) { /* no-op */ }
}

fetchLatest();
setInterval(fetchLatest, 2000);
