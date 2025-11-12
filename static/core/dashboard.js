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
        <div class="mini-charts">
          <canvas class="mini-chart" id="chart-h-${r.sensor}"></canvas>
          <canvas class="mini-chart binary" id="chart-t-${r.sensor}"></canvas>
          <canvas class="mini-chart binary" id="chart-v-${r.sensor}"></canvas>
        </div>
      </div>
      <div class="card-foot">${formatDate(r.recorded_at)}</div>
    `;
    grid.appendChild(card);
  });
}

function updateStatus(rows){
  const pill = document.getElementById('status-pill');
  const last = document.getElementById('last-updated');
  if (!pill || !last) return;
  if (!rows.length){
    pill.className = 'badge ok';
    pill.textContent = 'OK';
    last.textContent = 'Sin datos';
    return;
  }
  const anyWarn = rows.some(r => (r.humidity_pct < 10 || r.humidity_pct > 90) || r.tilt || r.vibration);
  pill.className = `badge ${anyWarn ? 'warn' : 'ok'}`;
  pill.textContent = anyWarn ? 'Alerta' : 'OK';
  const latest = rows.reduce((acc, r) => {
    const t = new Date(r.recorded_at).getTime();
    return isNaN(t) ? acc : Math.max(acc, t);
  }, 0);
  last.textContent = latest ? `Última actualización: ${new Date(latest).toLocaleString()}` : 'Sin datos';
}

async function fetchLatest() {
  try {
    const res = await fetch('/api/latest-readings/', { credentials: 'same-origin' });
    if (!res.ok) return;
    const data = await res.json();
    const rows = data.results || [];
    updateCards(rows);
    updateTable(rows);
    updateStatus(rows);
    // fetch history for each sensor (last 3 hours)
    const since = new Date(Date.now() - 3*60*60*1000).toISOString();
    rows.forEach(async r => {
      try{
        const hr = await fetch(`/api/history/?sensor=${encodeURIComponent(r.sensor)}&from=${encodeURIComponent(since)}`);
        if(!hr.ok) return; const h = await hr.json();
        const hum = h.results.map(it=>({t: new Date(it.recorded_at).getTime(), v: it.humidity_pct})).reverse();
        const tilt = h.results.map(it=>({t: new Date(it.recorded_at).getTime(), v: it.tilt})).reverse();
        const vib = h.results.map(it=>({t: new Date(it.recorded_at).getTime(), v: it.vibration})).reverse();
        IGPCharts.drawLineChart(document.getElementById(`chart-h-${r.sensor}`), hum, {color:'#0ea5e9'});
        IGPCharts.drawBinaryChart(document.getElementById(`chart-t-${r.sensor}`), tilt, {color:'#f59e0b'});
        IGPCharts.drawBinaryChart(document.getElementById(`chart-v-${r.sensor}`), vib, {color:'#ef4444'});
      }catch(e){ /* ignore */ }
    });
  } catch (e) { /* no-op */ }
}

fetchLatest();
setInterval(fetchLatest, 2000);
