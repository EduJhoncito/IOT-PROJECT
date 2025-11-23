(function () {
    const DPR = window.devicePixelRatio || 1;

    function setupCanvas(canvas) {
        const rect = canvas.getBoundingClientRect();
        const ctx = canvas.getContext('2d');
        canvas.width = rect.width * DPR;
        canvas.height = rect.height * DPR;
        ctx.scale(DPR, DPR);
        return { ctx, width: rect.width, height: rect.height };
    }

    function drawEmptyState(ctx, width, height, message) {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.font = '16px "Inter", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(message, width / 2, height / 2);
    }

    function renderBarChart(id, dataset) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const { ctx, width, height } = setupCanvas(canvas);
        if (!dataset || !dataset.length) {
            drawEmptyState(ctx, width, height, 'Aún no hay datos históricos.');
            return;
        }
        ctx.clearRect(0, 0, width, height);
        const padding = 32;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        const step = chartWidth / dataset.length;
        const maxValue = Math.max(...dataset.map(d => d.avgPulse), 1);

        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        dataset.forEach((point, index) => {
            const barHeight = (point.avgPulse / maxValue) * chartHeight;
            const x = padding + index * step + step * 0.2;
            const y = height - padding - barHeight;
            const barWidth = step * 0.6;
            const gradient = ctx.createLinearGradient(0, y, 0, height - padding);
            gradient.addColorStop(0, '#00d7c1');
            gradient.addColorStop(1, '#007bff');
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            const labelFrequency = Math.max(1, Math.ceil(dataset.length / 6));
            if (index % labelFrequency === 0) {
                ctx.fillStyle = 'rgba(255,255,255,0.7)';
                ctx.font = '12px "Inter", sans-serif';
                ctx.save();
                ctx.translate(x + barWidth / 2, height - padding + 16);
                ctx.rotate(-Math.PI / 6);
                ctx.fillText(point.label, 0, 0);
                ctx.restore();
            }
        });
    }

    function movingAverage(values, windowSize) {
        if (values.length < windowSize) return values;
        return values.map((_, idx, arr) => {
            const start = Math.max(0, idx - windowSize + 1);
            const subset = arr.slice(start, idx + 1);
            const avg = subset.reduce((acc, val) => acc + val, 0) / subset.length;
            return Number(avg.toFixed(2));
        });
    }

    function renderLineChart(id, dataset) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const { ctx, width, height } = setupCanvas(canvas);
        if (!dataset || !dataset.length) {
            drawEmptyState(ctx, width, height, 'Carga registros para ver la tendencia.');
            return;
        }

        const padding = 32;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        const values = dataset.map(point => point.value);
        const smoothed = movingAverage(values, 3);
        const maxValue = Math.max(...smoothed, 1);
        const minValue = Math.min(...smoothed, 0);
        const valueRange = maxValue - minValue || 1;

        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.setLineDash([4, 8]);
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.beginPath();
        smoothed.forEach((value, index) => {
            const x = padding + (chartWidth / (smoothed.length - 1 || 1)) * index;
            const y = padding + chartHeight - ((value - minValue) / valueRange) * chartHeight;
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
        gradient.addColorStop(0, '#ffb347');
        gradient.addColorStop(1, '#ffd56f');
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3;
        ctx.stroke();

        smoothed.forEach((value, index) => {
            const x = padding + (chartWidth / (smoothed.length - 1 || 1)) * index;
            const y = padding + chartHeight - ((value - minValue) / valueRange) * chartHeight;
            ctx.fillStyle = '#ffb347';
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
            const labelFrequency = Math.max(1, Math.ceil(dataset.length / 4));
            if (index % labelFrequency === 0 || index === smoothed.length - 1) {
                ctx.fillStyle = 'rgba(255,255,255,0.7)';
                ctx.font = '12px "Inter", sans-serif';
                ctx.fillText(dataset[index].label, x - 20, height - 4);
            }
        });
    }

    const liveState = {
        totalSamples: 0,
        humiditySum: 0,
        tiltEvents: 0,
        hitEvents: 0,
        currentDay: null,
        lastTimestamp: '--',
        lastSeq: '--',
    };

    function initRealtimeStream() {
        const endpoint = window.streamEndpoint;
        const statusEl = document.getElementById('live-status');
        if (!window.simStreamEnabled) {
            if (statusEl) {
                setStatus(statusEl, 'Simulación deshabilitada', 'error');
            }
            return;
        }
        if (!endpoint || !statusEl || typeof EventSource === 'undefined') {
            if (statusEl) {
                statusEl.textContent = 'No soportado';
                statusEl.classList.add('is-error');
            }
            return;
        }
        const source = new EventSource(endpoint);
        setStatus(statusEl, 'Conectando…', 'connecting');

        source.onopen = () => setStatus(statusEl, 'Conectado', 'ok');
        source.onerror = () => setStatus(statusEl, 'Reintentando…', 'error');
        source.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                handleLivePayload(payload);
            } catch (err) {
                console.error('Error procesando el stream', err);
                setStatus(statusEl, 'Error de datos', 'error');
            }
        };
    }

    function setStatus(el, text, status) {
        el.textContent = text;
        el.classList.remove('is-ok', 'is-error', 'is-connecting');
        if (status === 'ok') {
            el.classList.add('is-ok');
        } else if (status === 'error') {
            el.classList.add('is-error');
        } else {
            el.classList.add('is-connecting');
        }
    }

    function handleLivePayload(payload) {
        if (!payload || !Array.isArray(payload.samples)) {
            return;
        }
        const day = (payload.ts || '').split(' ')[0];
        if (liveState.currentDay !== day) {
            resetDailyCounters(day);
        }
        const sampleCount = payload.samples.length;
        const humiditySum = payload.samples.reduce((acc, sample) => acc + Number(sample?.soil?.pct || 0), 0);
        const tiltCount = payload.samples.filter(sample => Number(sample?.tilt || 0)).length;
        const hitCount = payload.samples.filter(sample => Number(sample?.vib?.hit || 0)).length;

        liveState.totalSamples += sampleCount;
        liveState.humiditySum += humiditySum;
        liveState.tiltEvents += tiltCount;
        liveState.hitEvents += hitCount;
        liveState.lastTimestamp = payload.ts;
        liveState.lastSeq = payload.seq;

        renderLiveMetrics(payload);
    }

    function resetDailyCounters(day) {
        liveState.currentDay = day;
        liveState.totalSamples = 0;
        liveState.humiditySum = 0;
        liveState.tiltEvents = 0;
        liveState.hitEvents = 0;
    }

    function renderLiveMetrics(payload) {
        const totalEl = document.getElementById('live-total');
        const humidityEl = document.getElementById('live-humidity');
        const tiltEl = document.getElementById('live-tilt');
        const hitEl = document.getElementById('live-hit');
        const lastTsEl = document.getElementById('live-last-ts');
        const lastSeqEl = document.getElementById('live-last-seq');
        const jsonEl = document.getElementById('live-json');

        if (totalEl) totalEl.textContent = liveState.totalSamples.toString();
        if (humidityEl) {
            const valueSpan = humidityEl.querySelector('.value');
            if (valueSpan) {
                const avg = liveState.totalSamples ? (liveState.humiditySum / liveState.totalSamples).toFixed(1) : '0.0';
                valueSpan.textContent = avg;
            }
        }
        if (tiltEl) tiltEl.textContent = liveState.tiltEvents.toString();
        if (hitEl) hitEl.textContent = liveState.hitEvents.toString();
        if (lastTsEl) lastTsEl.textContent = liveState.lastTimestamp || '--';
        if (lastSeqEl) lastSeqEl.textContent = liveState.lastSeq || '--';
        if (jsonEl) jsonEl.textContent = JSON.stringify(payload, null, 2);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const data = window.dashboardData || {};
        renderBarChart('pulseChart', data.monthlyPulse || []);
        renderLineChart('humidityChart', data.humidityTrend || []);
        initRealtimeStream();
    });
})();
