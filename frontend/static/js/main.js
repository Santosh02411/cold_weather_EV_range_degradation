/* ═══ main.js — Cold Weather EV Modeler ═══ */

// ═══ Theme Toggle ═══
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = next === 'light' ? '🌙' : '☀️';
}

(function() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    document.addEventListener('DOMContentLoaded', function() {
        const btn = document.getElementById('themeToggle');
        if (btn) btn.textContent = saved === 'light' ? '🌙' : '☀️';
    });
})();

// ═══ Mobile Sidebar ═══
function toggleSidebar() {
    document.querySelector('.sidebar')?.classList.toggle('open');
}

// ═══ Fetch helper ═══
async function apiFetch(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    // Get CSRF token
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        defaults.headers['X-CSRFToken'] = csrfMeta.content;
    }
    const resp = await fetch(url, { ...defaults, ...options });
    if (!resp.ok) {
        let errorMsg = 'Request failed';
        try {
            const err = await resp.json();
            errorMsg = err.error || err.message || errorMsg;
        } catch(e) {
            errorMsg = `Server Error: ${resp.status} ${resp.statusText}`;
        }
        console.error(`API Error [${url}]:`, errorMsg);
        throw new Error(errorMsg);
    }
    return resp.json();
}

// ═══ Flash Messages Auto-dismiss ═══
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function() { alert.remove(); }, 300);
        }, 5000);
    });
});

// ═══ Dashboard Charts ═══
async function loadDashboardCharts() {
    try {
        // Stats
        const stats = await apiFetch('/dashboard/api/stats');
        setTextSafe('statPredictions', stats.total_predictions);
        setTextSafe('statVehicles', stats.total_vehicles);
        setTextSafe('statDegradation', stats.avg_degradation + '%');

        if (stats.recent_weather) {
            setTextSafe('statTemperature', stats.recent_weather.temperature_c + '°C');
        }

        // Temp vs Range chart
        const tempData = await apiFetch('/dashboard/api/charts/temp-vs-range');
        if (tempData.temperatures.length > 0) {
            renderTempRangeChart(tempData);
        }

        // Efficiency chart
        const effData = await apiFetch('/dashboard/api/charts/efficiency');
        if (effData.labels.length > 0) {
            renderEfficiencyChart(effData);
        }

        // Seasonal chart
        const seasonal = await apiFetch('/dashboard/api/charts/seasonal');
        renderSeasonalChart(seasonal);

        // Smart Alerts (Module 15)
        renderSmartAlerts(stats);

    } catch (e) {
        console.log('Dashboard data loading:', e.message);
    }
}

function setTextSafe(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function renderTempRangeChart(data) {
    const ctx = document.getElementById('tempRangeChart');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Temperature vs Predicted Range',
                data: data.temperatures.map((t, i) => ({ x: t, y: data.ranges[i] })),
                backgroundColor: 'rgba(99, 140, 255, 0.6)',
                borderColor: '#638cff',
                pointRadius: 5,
                pointHoverRadius: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#8892a8' } } },
            scales: {
                x: { title: { display: true, text: 'Temperature (°C)', color: '#8892a8' },
                     ticks: { color: '#8892a8' }, grid: { color: 'rgba(99,140,255,0.08)' } },
                y: { title: { display: true, text: 'Predicted Range (km)', color: '#8892a8' },
                     ticks: { color: '#8892a8' }, grid: { color: 'rgba(99,140,255,0.08)' } }
            }
        }
    });
}

function renderEfficiencyChart(data) {
    const ctx = document.getElementById('efficiencyChart');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels.reverse(),
            datasets: [{
                label: 'Energy (Wh/km)',
                data: data.energy.reverse(),
                borderColor: '#22d3ee',
                backgroundColor: 'rgba(34, 211, 238, 0.1)',
                fill: true,
                tension: 0.4,
            }, {
                label: 'Degradation %',
                data: data.degradation.reverse(),
                borderColor: '#f87171',
                backgroundColor: 'rgba(248, 113, 113, 0.1)',
                fill: true,
                tension: 0.4,
                yAxisID: 'y1',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#8892a8' } } },
            scales: {
                x: { ticks: { color: '#8892a8', maxTicksLimit: 10 }, grid: { color: 'rgba(99,140,255,0.08)' } },
                y: { ticks: { color: '#8892a8' }, grid: { color: 'rgba(99,140,255,0.08)' },
                     title: { display: true, text: 'Wh/km', color: '#8892a8' } },
                y1: { position: 'right', ticks: { color: '#f87171' }, grid: { drawOnChartArea: false },
                      title: { display: true, text: 'Degradation %', color: '#f87171' } }
            }
        }
    });
}

function renderSeasonalChart(data) {
    const ctx = document.getElementById('seasonalChart');
    if (!ctx) return;
    const labels = Object.keys(data);
    const values = labels.map(k => data[k].avg_degradation);
    const colors = ['#f87171', '#fbbf24', '#22d3ee', '#34d399', '#f87171'];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Range Degradation %',
                data: values,
                backgroundColor: colors.map(c => c + '40'),
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#8892a8' } } },
            scales: {
                x: { ticks: { color: '#8892a8', maxRotation: 45 }, grid: { display: false } },
                y: { ticks: { color: '#8892a8' }, grid: { color: 'rgba(99,140,255,0.08)' },
                     title: { display: true, text: 'Degradation %', color: '#8892a8' } }
            }
        }
    });
}

function renderSmartAlerts(stats) {
    const container = document.getElementById('dashboardAlerts');
    if (!container) return;
    
    let alerts = [];
    const temp = stats.recent_weather ? stats.recent_weather.temperature_c : -10;
    
    if (temp < -15) {
        alerts.push({ type: 'danger', icon: '🥶', title: 'Severe Cold Warning', desc: 'Extreme range loss (>40%) expected. Battery preconditioning is critical.' });
    } else if (temp < 0) {
        alerts.push({ type: 'warning', icon: '❄️', title: 'Freezing Conditions', desc: 'Significant range reduction (15-25%) detected. Expect slower DC charging.' });
    }
    
    if (stats.avg_degradation > 25) {
        alerts.push({ type: 'info', icon: '🔋', title: 'Efficiency Alert', desc: 'Average range loss is higher than normal. Check tire pressure and HVAC settings.' });
    }

    if (alerts.length === 0) return;

    container.innerHTML = alerts.map(a => `
        <div class="alert alert-${a.type}" style="padding:10px;margin-bottom:0;display:flex;gap:10px;align-items:start;">
            <span style="font-size:18px">${a.icon}</span>
            <div>
                <div style="font-weight:700;font-size:13px">${a.title}</div>
                <div style="font-size:11px;opacity:0.9">${a.desc}</div>
            </div>
        </div>
    `).join('');
}

// ═══ Prediction Form ═══
async function submitPrediction(event) {
    event.preventDefault();
    const form = event.target;
    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;"></span> Predicting...';

    const data = {
        vehicle_id: parseInt(form.vehicle_id?.value || 0),
        temperature_c: parseFloat(form.temperature_c?.value || 0),
        humidity: parseFloat(form.humidity?.value || 50),
        wind_speed_kmh: parseFloat(form.wind_speed_kmh?.value || 10),
        precipitation: form.precipitation?.value || 'none',
        battery_percentage: parseFloat(form.battery_percentage?.value || 100),
        vehicle_speed_kmh: parseFloat(form.vehicle_speed_kmh?.value || 60),
        hvac_usage: form.hvac_usage?.checked ?? true,
        terrain_type: form.terrain_type?.value || 'flat',
        battery_age_years: parseFloat(form.battery_age_years?.value || 0),
        ml_model: form.ml_model?.value || 'random_forest',
    };

    if (!data.vehicle_id) {
        showAlert('warning', 'Please select a vehicle.');
        btn.disabled = false;
        btn.innerHTML = '⚡ Predict Range Degradation';
        return;
    }

    try {
        const result = await apiFetch('/predictions/api/predict', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        displayPredictionResult(result);
        loadRecommendations(data);
    } catch (e) {
        showAlert('danger', e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '⚡ Predict Range Degradation';
    }
}

function displayPredictionResult(result) {
    const container = document.getElementById('predictionResult');
    if (!container) return;

    const p = result.prediction;
    const v = result.vehicle;
    container.innerHTML = `
        <div class="animate-slide">
            <div class="stats-grid" style="margin-bottom:16px">
                <div class="stat-card">
                    <div class="stat-icon red">📉</div>
                    <div><div class="stat-value">${p.range_degradation_pct}%</div><div class="stat-label">Range Degradation</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon blue">🛣️</div>
                    <div><div class="stat-value">${p.predicted_range_km} km</div><div class="stat-label">Predicted Range</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon amber">⚡</div>
                    <div><div class="stat-value">${p.energy_consumption_wh_km} Wh/km</div><div class="stat-label">Energy Consumption</div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon cyan">🔌</div>
                    <div><div class="stat-value">${p.charging_slowdown_pct}%</div><div class="stat-label">Charging Slowdown</div></div>
                </div>
            </div>
            ${result.explanation ? renderExplanation(result.explanation) : ''}
        </div>
    `;
}

function renderExplanation(explanation) {
    if (!explanation || !explanation.explanations) return '';
    let html = '<div class="card" style="margin-top:16px"><div class="card-header"><h3 class="card-title">🧠 AI Explanation</h3></div>';
    html += `<p style="color:var(--text-secondary);font-size:14px;margin-bottom:14px">${explanation.summary}</p>`;
    explanation.explanations.forEach(e => {
        const isPos = e.impact === 'positive';
        html += `<div class="xai-card ${isPos ? 'positive' : ''}">
            <div class="xai-factor">${e.factor}</div>
            <div class="xai-detail">${e.detail}</div>
        </div>`;
    });
    html += '</div>';
    return html;
}

// ═══ Recommendations ═══
async function loadRecommendations(data) {
    try {
        const result = await apiFetch('/recommendations/api/get', {
            method: 'POST', body: JSON.stringify(data),
        });
        const container = document.getElementById('recommendationsContainer');
        if (!container || !result.recommendations) return;
        container.innerHTML = result.recommendations.map(r => `
            <div class="rec-card animate-slide">
                <div class="rec-icon">${r.icon}</div>
                <div>
                    <div class="rec-title">${r.title}</div>
                    <div class="rec-desc">${r.description}</div>
                    <div class="rec-impact">💡 ${r.impact}</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.log('Recommendations:', e.message);
    }
}

// ═══ Trip Simulation ═══
async function submitTrip(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        vehicle_id: parseInt(form.vehicle_id.value),
        source: form.source.value,
        destination: form.destination.value,
        distance_km: parseFloat(form.distance_km.value),
        temperature_c: parseFloat(form.temperature_c.value),
        speed_kmh: parseFloat(form.speed_kmh.value),
        heater_usage: form.heater_usage?.checked ?? true,
        num_passengers: parseInt(form.num_passengers?.value || 1),
        battery_percentage: parseFloat(form.battery_percentage?.value || 100),
    };

    try {
        const result = await apiFetch('/trip/api/simulate', {
            method: 'POST', body: JSON.stringify(data),
        });
        const t = result.trip;
        const container = document.getElementById('tripResult');
        if (container) {
            container.innerHTML = `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon amber">🔋</div>
                        <div><div class="stat-value">${t.estimated_battery_usage_pct}%</div><div class="stat-label">Battery Usage</div></div></div>
                    <div class="stat-card"><div class="stat-icon blue">🛣️</div>
                        <div><div class="stat-value">${t.predicted_remaining_range_km} km</div><div class="stat-label">Remaining Range</div></div></div>
                    <div class="stat-card"><div class="stat-icon cyan">🔌</div>
                        <div><div class="stat-value">${t.charging_stops_required}</div><div class="stat-label">Charging Stops</div></div></div>
                    <div class="stat-card"><div class="stat-icon green">✅</div>
                        <div><div class="stat-value">${t.estimated_arrival_battery_pct}%</div><div class="stat-label">Arrival Battery</div></div></div>
                </div>`;
        }
    } catch (e) {
        showAlert('danger', e.message);
    }
}

// ═══ Charging Analysis ═══
async function submitCharging(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        vehicle_id: parseInt(form.vehicle_id.value),
        temperature_c: parseFloat(form.temperature_c.value),
        current_pct: parseFloat(form.current_pct.value),
        target_pct: parseFloat(form.target_pct.value),
        fast_charging: form.fast_charging?.checked ?? true,
    };

    try {
        const result = await apiFetch('/charging/api/predict', {
            method: 'POST', body: JSON.stringify(data),
        });
        const container = document.getElementById('chargingResult');
        if (container) {
            container.innerHTML = `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon blue">⏱️</div>
                        <div><div class="stat-value">${result.charging_time_minutes} min</div><div class="stat-label">Charging Time</div></div></div>
                    <div class="stat-card"><div class="stat-icon amber">⚡</div>
                        <div><div class="stat-value">${result.effective_power_kw} kW</div><div class="stat-label">Effective Power</div></div></div>
                    <div class="stat-card"><div class="stat-icon green">📊</div>
                        <div><div class="stat-value">${result.efficiency_pct}%</div><div class="stat-label">Charging Efficiency</div></div></div>
                    <div class="stat-card"><div class="stat-icon red">📉</div>
                        <div><div class="stat-value">${result.slowdown_pct}%</div><div class="stat-label">Cold Slowdown</div></div></div>
                </div>`;
        }
        // Load temperature comparison chart
        loadChargingComparison(data.vehicle_id, data.fast_charging);
    } catch (e) {
        showAlert('danger', e.message);
    }
}

async function loadChargingComparison(vehicleId, fastCharging) {
    try {
        const result = await apiFetch('/charging/api/compare', {
            method: 'POST', body: JSON.stringify({ vehicle_id: vehicleId, fast_charging: fastCharging }),
        });
        const ctx = document.getElementById('chargingChart');
        if (!ctx) return;
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: result.comparisons.map(c => c.label),
                datasets: [{
                    label: 'Charging Time (min)',
                    data: result.comparisons.map(c => c.charging_time_minutes),
                    backgroundColor: result.comparisons.map(c =>
                        c.charging_time_minutes > 60 ? 'rgba(248,113,113,0.6)' :
                        c.charging_time_minutes > 40 ? 'rgba(251,191,36,0.6)' : 'rgba(52,211,153,0.6)'),
                    borderRadius: 8,
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8892a8' } } },
                scales: {
                    x: { ticks: { color: '#8892a8' }, grid: { display: false } },
                    y: { ticks: { color: '#8892a8' }, grid: { color: 'rgba(99,140,255,0.08)' } }
                }
            }
        });
    } catch (e) { console.log(e); }
}

// ═══ Compare Vehicles ═══
async function submitComparison(event) {
    event.preventDefault();
    const checkboxes = document.querySelectorAll('input[name="vehicle_ids"]:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
    const temp = parseFloat(document.getElementById('compareTemp')?.value || -10);

    if (ids.length < 2) {
        showAlert('warning', 'Please select at least 2 vehicles to compare.');
        return;
    }

    try {
        const result = await apiFetch('/compare/api/compare', {
            method: 'POST', body: JSON.stringify({ vehicle_ids: ids, temperature_c: temp }),
        });
        displayComparison(result);
    } catch (e) {
        showAlert('danger', e.message);
    }
}

function displayComparison(result) {
    const container = document.getElementById('comparisonResult');
    if (!container) return;

    let html = '<div class="table-container animate-slide"><table><thead><tr>';
    html += '<th>Vehicle</th><th>Battery</th><th>EPA Range</th><th>Degradation %</th><th>Predicted Range</th><th>Energy Wh/km</th><th>Charging Slow%</th>';
    html += '</tr></thead><tbody>';

    result.comparisons.forEach(c => {
        const v = c.vehicle;
        const p = c.prediction;
        html += `<tr>
            <td><strong>${v.manufacturer}</strong> ${v.model_name}</td>
            <td>${v.battery_capacity_kwh} kWh (${v.battery_chemistry})</td>
            <td>${v.epa_range_km} km</td>
            <td><span class="badge ${p.range_degradation_pct > 20 ? 'badge-red' : 'badge-green'}">${p.range_degradation_pct}%</span></td>
            <td>${p.predicted_range_km} km</td>
            <td>${p.energy_consumption_wh_km}</td>
            <td>${p.charging_slowdown_pct}%</td>
        </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// ═══ Weather ═══
async function fetchWeather() {
    const city = document.getElementById('weatherCity')?.value || 'New York';
    try {
        const weather = await apiFetch(`/weather/api/current?city=${encodeURIComponent(city)}`);
        const container = document.getElementById('weatherResult');
        if (container) {
            const isLive = weather.data_source === 'live';
            const sourceBadge = `<div class="alert ${isLive ? 'alert-success' : 'alert-warning'}" style="margin-bottom:1rem;">
                ${isLive ? '🟢 Live data from OpenWeatherMap' : '🟡 Demo/fallback data' + (weather.note ? ' — ' + weather.note : ' — set OPENWEATHERMAP_API_KEY in .env for real conditions')}
            </div>`;
            container.innerHTML = sourceBadge + `
                <div class="animate-slide stats-grid">
                    <div class="stat-card"><div class="stat-icon blue">🌡️</div>
                        <div><div class="stat-value">${weather.temperature_c}°C</div><div class="stat-label">Temperature (Feels ${weather.feels_like_c}°C)</div></div></div>
                    <div class="stat-card"><div class="stat-icon cyan">💧</div>
                        <div><div class="stat-value">${weather.humidity}%</div><div class="stat-label">Humidity</div></div></div>
                    <div class="stat-card"><div class="stat-icon amber">💨</div>
                        <div><div class="stat-value">${weather.wind_speed_kmh?.toFixed(1)} km/h</div><div class="stat-label">Wind Speed</div></div></div>
                    <div class="stat-card"><div class="stat-icon ${weather.severity === 'extreme' ? 'red' : 'green'}">
                        ${weather.severity === 'extreme' ? '🥶' : weather.severity === 'severe' ? '❄️' : '🌤️'}</div>
                        <div><div class="stat-value">${weather.severity?.toUpperCase()}</div><div class="stat-label">Severity for EVs</div></div></div>
                </div>`;
        }
    } catch (e) {
        showAlert('danger', e.message);
    }
}

// ═══ Utility ═══
function showAlert(type, message) {
    const icons = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };
    const container = document.getElementById('alertContainer') || document.querySelector('.page-content');
    if (!container) return;
    const div = document.createElement('div');
    div.className = `alert alert-${type} animate-slide`;
    div.innerHTML = `${icons[type] || ''} ${message}`;
    container.prepend(div);
    setTimeout(() => { div.style.opacity = '0'; setTimeout(() => div.remove(), 300); }, 5000);
}

// ═══ Dataset Upload ═══
async function uploadDataset(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const headers = {};
        if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.content;

        const resp = await fetch('/datasets/api/upload', {
            method: 'POST', body: formData, headers: headers,
        });
        const result = await resp.json();
        if (resp.ok) {
            showAlert('success', 'Dataset uploaded successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showAlert('danger', result.error);
        }
    } catch (e) {
        showAlert('danger', e.message);
    }
}
