function drawLineChart(canvas, points, opts={}){
  if(!canvas) return; const ctx = canvas.getContext('2d');
  const W = canvas.width = canvas.clientWidth; const H = canvas.height = canvas.clientHeight;
  ctx.clearRect(0,0,W,H);
  if(!points || points.length===0){ ctx.fillStyle='#94a3b8'; ctx.fillText('Sin datos',8,16); return; }
  const xs = points.map(p=>p.t), ys = points.map(p=>p.v);
  const minX=Math.min(...xs), maxX=Math.max(...xs); const minY=Math.min(...ys), maxY=Math.max(...ys);
  const pad=8; const toX = x=> pad + (W-2*pad)*((x-minX)/(maxX-minX||1));
  const toY = y=> H-pad - (H-2*pad)*((y-minY)/(maxY-minY||1));
  // grid
  ctx.strokeStyle='rgba(148,163,184,.35)'; ctx.lineWidth=1;
  ctx.beginPath(); for(let i=0;i<5;i++){ const y=pad+i*(H-2*pad)/4; ctx.moveTo(pad,y); ctx.lineTo(W-pad,y);} ctx.stroke();
  // line
  ctx.strokeStyle=opts.color||'#0ea5e9'; ctx.lineWidth=2; ctx.beginPath();
  points.forEach((p,i)=>{ const x=toX(p.t), y=toY(p.v); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke();
}

function drawBinaryChart(canvas, points, opts={}){
  if(!canvas) return; const ctx = canvas.getContext('2d');
  const W = canvas.width = canvas.clientWidth; const H = canvas.height = canvas.clientHeight;
  ctx.clearRect(0,0,W,H);
  const xs = points.map(p=>p.t); const minX=Math.min(...xs)||0, maxX=Math.max(...xs)||1; const pad=8;
  const toX = x=> pad + (W-2*pad)*((x-minX)/(maxX-minX||1));
  // baseline
  ctx.fillStyle='rgba(148,163,184,.25)'; ctx.fillRect(pad,H/2-2,W-2*pad,4);
  // segments
  ctx.fillStyle = (opts.color||'#ef4444');
  for(let i=1;i<points.length;i++){
    if(points[i-1].v===1){ const x1=toX(points[i-1].t), x2=toX(points[i].t); ctx.fillRect(x1, pad, Math.max(2,x2-x1), H-2*pad); }
  }
}

window.IGPCharts = { drawLineChart, drawBinaryChart };

