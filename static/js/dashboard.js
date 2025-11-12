// Dashboard JavaScript para actualización en tiempo real
let humidityChart = null;
let historicalData = [];

// Inicializar gráfico
function initChart() {
    const ctx = document.getElementById('humidityChart');
    if (!ctx) return;

    humidityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humedad (%)',
                data: [],
                borderColor: '#1E3A8A',
                backgroundColor: 'rgba(30, 58, 138, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Humedad (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tiempo'
                    }
                }
            }
        }
    });
}

// Cargar datos históricos
async function loadHistoricalData() {
    try {
        const response = await fetch('/api/historical/?limit=100');
        const result = await response.json();
        
        if (result.data && result.data.length > 0) {
            historicalData = result.data; // Ya viene ordenado
            
            // Actualizar gráfico
            if (humidityChart) {
                const labels = historicalData.map(item => {
                    const date = new Date(item.timestamp);
                    return date.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
                });
                
                const humidityValues = historicalData.map(item => item.humidity);
                
                humidityChart.data.labels = labels;
                humidityChart.data.datasets[0].data = humidityValues;
                humidityChart.update('none'); // Sin animación para actualización rápida
            }
        }
    } catch (error) {
        console.error('Error cargando datos históricos:', error);
    }
}

// Actualizar datos en tiempo real
async function updateRealtimeData() {
    try {
        const response = await fetch('/api/realtime/');
        const result = await response.json();
        
        if (result) {
            // Actualizar valores de humedad
            document.getElementById('current-humidity').textContent = result.humidity.toFixed(1);
            document.getElementById('avg-humidity').textContent = result.stats.avg_humidity_today.toFixed(1);
            document.getElementById('alert-percentage').textContent = result.stats.alert_percentage_today.toFixed(1);
            
            // Actualizar timestamp
            const timestamp = new Date(result.timestamp);
            document.getElementById('last-timestamp').textContent = 
                timestamp.toLocaleString('es-PE', { 
                    year: 'numeric', 
                    month: '2-digit', 
                    day: '2-digit', 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                });
            
            // Actualizar indicadores de inclinación
            const inclinationIndicator = document.getElementById('inclination-indicator');
            const inclinationText = document.getElementById('inclination-text');
            
            if (result.inclination === 1) {
                inclinationIndicator.className = 'status-indicator status-alert';
                inclinationText.textContent = 'ALERTA - Inclinación Detectada';
                inclinationText.style.color = '#DC2626';
            } else {
                inclinationIndicator.className = 'status-indicator status-ok';
                inclinationText.textContent = 'Estable';
                inclinationText.style.color = '#059669';
            }
            
            // Actualizar indicadores de vibración
            const vibrationIndicator = document.getElementById('vibration-indicator');
            const vibrationText = document.getElementById('vibration-text');
            
            if (result.vibration === 1) {
                vibrationIndicator.className = 'status-indicator status-alert';
                vibrationText.textContent = 'MOVIMIENTO Detectado';
                vibrationText.style.color = '#DC2626';
            } else {
                vibrationIndicator.className = 'status-indicator status-ok';
                vibrationText.textContent = 'Sin Movimiento';
                vibrationText.style.color = '#059669';
            }
            
            // Agregar nuevo punto al gráfico si hay cambio significativo
            if (historicalData.length === 0 || 
                Math.abs(historicalData[historicalData.length - 1].humidity - result.humidity) > 0.5) {
                
                historicalData.push({
                    timestamp: result.timestamp,
                    humidity: result.humidity
                });
                
                // Mantener solo los últimos 100 puntos
                if (historicalData.length > 100) {
                    historicalData.shift();
                }
                
                // Actualizar gráfico
                if (humidityChart) {
                    const labels = historicalData.map(item => {
                        const date = new Date(item.timestamp);
                        return date.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
                    });
                    
                    const humidityValues = historicalData.map(item => item.humidity);
                    
                    humidityChart.data.labels = labels;
                    humidityChart.data.datasets[0].data = humidityValues;
                    humidityChart.update('none');
                }
            }
        }
    } catch (error) {
        console.error('Error actualizando datos en tiempo real:', error);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Esperar a que Chart.js esté disponible
    function initializeDashboard() {
        if (typeof Chart !== 'undefined') {
            initChart();
            loadHistoricalData();
            // Actualizar cada 3 segundos
            setInterval(updateRealtimeData, 3000);
            // Primera actualización inmediata
            updateRealtimeData();
        } else {
            // Reintentar después de un breve delay
            setTimeout(initializeDashboard, 100);
        }
    }
    
    initializeDashboard();
});

