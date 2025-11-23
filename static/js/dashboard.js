(function () {
    const DPR = window.devicePixelRatio || 1;

    /* ---------------------------------------------------
     * CANVAS SETUP HELPERS
     * --------------------------------------------------- */
    function setupCanvas(canvas) {
        const rect = canvas.getBoundingClientRect();
        const ctx = canvas.getContext("2d");
        canvas.width = rect.width * DPR;
        canvas.height = rect.height * DPR;
        ctx.scale(DPR, DPR);
        return { ctx, width: rect.width, height: rect.height };
    }

    function drawEmptyState(ctx, width, height, message) {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.font = '16px "Inter", sans-serif';
        ctx.textAlign = "center";
        ctx.fillText(message, width / 2, height / 2);
    }

    /* ---------------------------------------------------
     * BAR CHART (PULSE)
     * --------------------------------------------------- */
    function renderBarChart(id, dataset) {
        const canvas = document.getElementById(id);
        if (!canvas) return;

        const { ctx, width, height } = setupCanvas(canvas);

        if (!dataset || !dataset.length) {
            drawEmptyState(ctx, width, height, "Aún no hay datos históricos.");
            return;
        }

        ctx.clearRect(0, 0, width, height);

        const padding = 32;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        const step = chartWidth / dataset.length;
        const maxValue = Math.max(...dataset.map(d => d.avgPulse), 1);

        // base line
        ctx.strokeStyle = "rgba(255,255,255,0.2)";
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
            gradient.addColorStop(0, "#00d7c1");
            gradient.addColorStop(1, "#007bff");

            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // label spacing
            const labelFrequency = Math.max(1, Math.ceil(dataset.length / 6));
            if (index % labelFrequency === 0) {
                ctx.fillStyle = "rgba(255,255,255,0.7)";
                ctx.font = '12px "Inter", sans-serif';
                ctx.save();
                ctx.translate(x + barWidth / 2, height - padding + 16);
                ctx.rotate(-Math.PI / 6);
                ctx.fillText(point.label, 0, 0);
                ctx.restore();
            }
        });
    }

    /* ---------------------------------------------------
     * LINE CHART (HUMIDITY)
     * --------------------------------------------------- */
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
            drawEmptyState(ctx, width, height, "Carga registros para ver la tendencia.");
            return;
        }

        const padding = 32;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        const values = dataset.map(p => p.value);
        const smoothed = movingAverage(values, 3);

        const maxValue = Math.max(...smoothed, 1);
        const minValue = Math.min(...smoothed, 0);
        const range = maxValue - minValue || 1;

        ctx.clearRect(0, 0, width, height);

        // baseline
        ctx.strokeStyle = "rgba(255,255,255,0.15)";
        ctx.setLineDash([4, 8]);
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        ctx.setLineDash([]);

        // plot line
        ctx.beginPath();
        smoothed.forEach((value, index) => {
            const x = padding + (chartWidth / (smoothed.length - 1)) * index;
            const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
        gradient.addColorStop(0, "#ffb347");
        gradient.addColorStop(1, "#ffd56f");
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3;
        ctx.stroke();

        // dots & labels
        smoothed.forEach((value, index) => {
            const x = padding + (chartWidth / (smoothed.length - 1)) * index;
            const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;

            ctx.fillStyle = "#ffb347";
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();

            const labelFreq = Math.max(1, Math.ceil(dataset.length / 4));
            if (index % labelFreq === 0 || index === smoothed.length - 1) {
                ctx.fillStyle = "rgba(255,255,255,0.7)";
                ctx.font = '12px "Inter", sans-serif';
                ctx.fillText(dataset[index].label, x - 20, height - 4);
            }
        });
    }

    /* ---------------------------------------------------
     * REALTIME REDIS METRICS
     * --------------------------------------------------- */
    function renderRedisMetrics(data) {
        console.log("LIVE DATA:", data);

        document.getElementById("live-total").textContent =
            data.total_readings ?? 0;

        document.getElementById("live-humidity").textContent =
            (data.humidity_avg ?? 0).toFixed(1);

        document.getElementById("live-tilt").textContent =
            data.inclination_events ?? 0;

        document.getElementById("live-hit").textContent =
            data.hit_events ?? 0;

        document.getElementById("live-last-ts").textContent =
            data.last_timestamp || "--";

        const seqEl = document.getElementById("live-last-seq");
        if (seqEl) seqEl.textContent = data.last_seq || "--";
    }

    function setStatus(el, text, status) {
        el.textContent = text;
        el.classList.remove("is-ok", "is-error", "is-connecting");
        el.classList.add(status === "ok" ? "is-ok" :
                        status === "error" ? "is-error" : "is-connecting");
    }

    function initRealtimeStream() {
        const statusEl = document.getElementById("live-status");

        function fetchRedisData() {
            fetch("/realtime-redis/")
                .then(r => r.json())
                .then(data => {
                    setStatus(statusEl, "Conectado a Redis", "ok");
                    renderRedisMetrics(data);
                })
                .catch(err => {
                    console.error("Redis ERROR:", err);
                    setStatus(statusEl, "Error Redis", "error");
                });
        }

        fetchRedisData();
        setInterval(fetchRedisData, 5000);
    }

    /* ---------------------------------------------------
     * INIT
     * --------------------------------------------------- */
    document.addEventListener("DOMContentLoaded", () => {
        const data = window.dashboardData || {};
        renderBarChart("pulseChart", data.monthlyPulse || []);
        renderLineChart("humidityChart", data.humidityTrend || []);
        document.getElementById("refresh-btn").addEventListener("click", (e) => {
            e.preventDefault();  // evita que el form GET se envíe
            location.reload();   // recarga TODA la página
        });
        
        initRealtimeStream(); // <<< IMPORTANTE
    });

})();
