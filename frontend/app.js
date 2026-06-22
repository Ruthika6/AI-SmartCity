// AURA Dashboard Interactivity Module

document.addEventListener("DOMContentLoaded", () => {
    // Current application state
    let wardsList = [];
    let selectedWardId = 1;
    let map = null;
    let forecastChart = null;
    let attributionChart = null;
    let simChart = null;
    
    // UI Selectors
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");
    const liveTimeEl = document.getElementById("live-time");
    
    // Initialize Time Display
    function updateTime() {
        const now = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
        liveTimeEl.innerHTML = `<i class="fa-regular fa-clock"></i> ${now.toLocaleDateString('en-IN', options)}`;
    }
    updateTime();
    setInterval(updateTime, 1000);

    // Tab Navigation Switcher
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(n => n.classList.remove("active"));
            sections.forEach(s => s.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            
            // Re-render maps or charts if they are sized inside hidden containers
            if (targetTab === "map-section" && map) {
                setTimeout(() => map.invalidateSize(), 150);
            }
        });
    });

    // ---------------------------------------------------------
    // 1. MAP & GEOSPATIAL COMPONENT
    // ---------------------------------------------------------
    
    function initMap() {
        // Center around Bengaluru
        map = L.map('map').setView([12.96, 77.62], 11);
        
        // CartoDB Positron Dark theme tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);
    }
    
    function getAqiColor(aqi) {
        if (aqi <= 50) return "#10b981"; // Good - Green
        if (aqi <= 100) return "#f59e0b"; // Moderate - Orange
        if (aqi <= 150) return "#ef4444"; // Poor - Red
        return "#8b5cf6"; // Severe - Purple
    }

    function loadWardsMap() {
        fetch("/api/wards")
            .then(res => res.json())
            .then(data => {
                wardsList = data;
                
                // Clear any existing polygons if needed, but since it's initial load:
                wardsList.forEach(ward => {
                    const color = getAqiColor(ward.current_aqi);
                    
                    // Create ward polygon boundary
                    const polygon = L.polygon(ward.coordinates, {
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.25,
                        weight: 2,
                        opacity: 0.8
                    }).addTo(map);
                    
                    // Hover states
                    polygon.on('mouseover', function () {
                        this.setStyle({ fillOpacity: 0.5, weight: 3 });
                    });
                    polygon.on('mouseout', function () {
                        this.setStyle({ fillOpacity: 0.25, weight: 2 });
                    });
                    
                    // Click handler loads details
                    polygon.on('click', () => {
                        selectedWardId = ward.id;
                        updateWardPane(ward);
                        loadForecast(ward.id);
                        loadAttribution(ward.id);
                    });
                    
                    // Tooltip
                    polygon.bindTooltip(`<strong>${ward.name}</strong><br>AQI: ${ward.current_aqi} (${ward.status})`, {
                        sticky: true
                    });
                });
                
                // Default load first ward
                if (wardsList.length > 0) {
                    const defaultWard = wardsList[0];
                    updateWardPane(defaultWard);
                    loadForecast(defaultWard.id);
                    loadAttribution(defaultWard.id);
                    populateAdvisoryDropdown();
                }
                
                // Update Top bar average
                let sumAqi = 0;
                wardsList.forEach(w => sumAqi += w.current_aqi);
                const avgAqi = Math.round(sumAqi / wardsList.length);
                const topStatusText = document.getElementById("top-status-text");
                const topStatusDot = document.querySelector(".top-bar .indicator-dot");
                
                topStatusText.textContent = `City Avg AQI: ${avgAqi}`;
                
                if (avgAqi <= 100) {
                    topStatusDot.className = "indicator-dot active";
                } else if (avgAqi <= 150) {
                    topStatusDot.className = "indicator-dot warning";
                } else {
                    topStatusDot.className = "indicator-dot critical";
                }
            })
            .catch(err => console.error("Error loading wards:", err));
    }

    function updateWardPane(ward) {
        document.getElementById("selected-ward-name").innerHTML = `
            <i class="fa-solid fa-location-crosshairs text-indigo-400"></i> ${ward.name}
        `;
        document.getElementById("selected-ward-aqi").textContent = ward.current_aqi;
        
        const badge = document.getElementById("selected-ward-status");
        badge.textContent = ward.status;
        badge.style.backgroundColor = getAqiColor(ward.current_aqi) + "30";
        badge.style.color = getAqiColor(ward.current_aqi);
        badge.style.borderColor = getAqiColor(ward.current_aqi) + "60";
        
        document.getElementById("stat-traffic").textContent = ward.traffic_congestion + "/10";
        document.getElementById("stat-construction").textContent = ward.active_construction;
        document.getElementById("stat-industry").textContent = ward.industrial_stacks;
    }

    // ---------------------------------------------------------
    // 2. ANALYTICS CHARTS (Chart.js)
    // ---------------------------------------------------------
    
    function loadForecast(wardId) {
        fetch(`/api/wards/${wardId}/forecast`)
            .then(res => res.json())
            .then(data => {
                const labels = data.forecast.map(f => `+${f.hour}h`);
                const values = data.forecast.map(f => f.aqi);
                const lowers = data.forecast.map(f => f.confidence_lower);
                const uppers = data.forecast.map(f => f.confidence_upper);
                
                if (forecastChart) {
                    forecastChart.destroy();
                }
                
                const ctx = document.getElementById("forecastChart").getContext("2d");
                forecastChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Predicted AQI',
                                data: values,
                                borderColor: '#00f2fe',
                                backgroundColor: 'rgba(0, 242, 254, 0.05)',
                                borderWidth: 2.5,
                                tension: 0.4,
                                fill: false,
                            },
                            {
                                label: 'Lower Limit',
                                data: lowers,
                                borderColor: 'rgba(255, 255, 255, 0.05)',
                                borderWidth: 0,
                                pointRadius: 0,
                                fill: '+1', // Fill down to upper limit (sandwich)
                                tension: 0.4,
                            },
                            {
                                label: 'Confidence Band',
                                data: uppers,
                                borderColor: 'rgba(255, 255, 255, 0.05)',
                                backgroundColor: 'rgba(0, 242, 254, 0.03)',
                                borderWidth: 0,
                                pointRadius: 0,
                                fill: false,
                                tension: 0.4,
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                                ticks: { color: '#9ca3af' }
                            },
                            y: {
                                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                                ticks: { color: '#9ca3af' }
                            }
                        }
                    }
                });
            });
    }

    function loadAttribution(wardId) {
        fetch(`/api/wards/${wardId}/attribution`)
            .then(res => res.json())
            .then(data => {
                const sources = Object.keys(data.attribution);
                const values = Object.values(data.attribution);
                
                if (attributionChart) {
                    attributionChart.destroy();
                }
                
                const ctx = document.getElementById("attributionChart").getContext("2d");
                attributionChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: sources,
                        datasets: [{
                            data: values,
                            backgroundColor: [
                                '#ef4444', // Traffic Red
                                '#f59e0b', // Construction Orange
                                '#8b5cf6', // Industrial Purple
                                '#3b82f6', // Waste Blue
                                '#10b981'  // Background Green
                            ],
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: '#9ca3af',
                                    font: { size: 10 },
                                    boxWidth: 10
                                }
                            }
                        }
                    }
                });
            });
    }

    // ---------------------------------------------------------
    // 3. ENFORCEMENT COMPONENT
    // ---------------------------------------------------------
    let currentHotspots = [];
    
    function loadEnforcement() {
        fetch("/api/enforcement/hotspots")
            .then(res => res.json())
            .then(data => {
                currentHotspots = data;
                const tbody = document.getElementById("hotspot-list");
                tbody.innerHTML = "";
                
                currentHotspots.forEach(hotspot => {
                    const row = document.createElement("tr");
                    row.style.cursor = "pointer";
                    
                    const scoreClass = hotspot.hotspot_score >= 50.0 ? "priority-high" : "priority-med";
                    
                    row.innerHTML = `
                        <td style="font-weight:600;">${hotspot.ward_name}</td>
                        <td>${hotspot.current_aqi}</td>
                        <td><span class="priority-badge ${scoreClass}">${hotspot.hotspot_score}</span></td>
                        <td>${hotspot.primary_source}</td>
                        <td><button class="action-btn">Dossier</button></td>
                    `;
                    
                    row.addEventListener("click", () => {
                        loadDossier(hotspot);
                    });
                    
                    tbody.appendChild(row);
                });
            });
    }

    function loadDossier(hotspot) {
        const detailsPanel = document.getElementById("enforce-details");
        const actionsBar = document.getElementById("dossier-actions-bar");
        
        detailsPanel.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <h3 style="font-size:1.2rem; color:#fff;">${hotspot.ward_name}</h3>
                <span class="priority-badge ${hotspot.hotspot_score >= 50.0 ? 'priority-high' : 'priority-med'}">Priority: ${hotspot.hotspot_score}</span>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
                <div style="background:rgba(255,255,255,0.02); padding:10px; border-radius:8px;">
                    <div class="text-secondary" style="font-size:0.75rem; text-transform:uppercase;">Primary Culprit</div>
                    <div style="font-weight:700; color:var(--aqi-poor); margin-top:4px;">${hotspot.primary_source}</div>
                </div>
                <div style="background:rgba(255,255,255,0.02); padding:10px; border-radius:8px;">
                    <div class="text-secondary" style="font-size:0.75rem; text-transform:uppercase;">Assigned Officer</div>
                    <div style="font-weight:700; color:#fff; margin-top:4px;">${hotspot.assigned_officer}</div>
                </div>
            </div>
            
            <div style="margin-bottom:12px;">
                <h4 style="font-size:0.85rem; text-transform:uppercase; color:var(--text-secondary); margin-bottom:6px;">Evidence File</h4>
                <div class="evidence-box">${hotspot.evidence}</div>
            </div>
            
            <div>
                <h4 style="font-size:0.85rem; text-transform:uppercase; color:var(--text-secondary); margin-bottom:6px;">Mandated Intervention Action</h4>
                <div class="evidence-box" style="border-color:rgba(0, 242, 254, 0.2); background:rgba(0, 242, 254, 0.01); color:#fff;">
                    ${hotspot.recommended_action}
                </div>
            </div>
        `;
        
        actionsBar.style.display = "flex";
        
        // Wire dispatch button
        document.getElementById("dispatch-officer-btn").onclick = () => {
            alert(`Operational command issued: Officer dispatch notification triggered for ${hotspot.assigned_officer}. Status shifted to DISPATCHED.`);
        };
    }
    
    // Load enforcement whenever user opens the tab
    document.querySelector('[data-tab="enforce-section"]').addEventListener("click", loadEnforcement);

    // ---------------------------------------------------------
    // 4. POLICY SIMULATOR COMPONENT
    // ---------------------------------------------------------
    
    const trafficSlider = document.getElementById("sim-traffic");
    const trafficLabel = document.getElementById("label-traffic-cut");
    
    trafficSlider.addEventListener("input", (e) => {
        trafficLabel.textContent = `${e.target.value}% Cut`;
    });
    
    function runSimulation() {
        const payload = {
            traffic_reduction: parseFloat(trafficSlider.value),
            construction_ban: document.getElementById("sim-construction").checked,
            industrial_halt: document.getElementById("sim-industry").checked,
            mist_spraying: document.getElementById("sim-spraying").checked
        };
        
        fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                // Update metrics
                document.getElementById("sim-aqi-metric").textContent = `${data.average_aqi_reduction}%`;
                document.getElementById("sim-carbon-metric").textContent = `${data.carbon_offset_co2_kg.toLocaleString()} kg CO₂`;
                
                // Draw bar comparisons
                const labels = data.ward_reductions.map(w => w.ward_name);
                const befores = data.ward_reductions.map(w => w.before_aqi);
                const afters = data.ward_reductions.map(w => w.after_aqi);
                
                if (simChart) {
                    simChart.destroy();
                }
                
                const ctx = document.getElementById("simChart").getContext("2d");
                simChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Before Policy',
                                data: befores,
                                backgroundColor: 'rgba(239, 68, 68, 0.4)',
                                borderColor: '#ef4444',
                                borderWidth: 1
                            },
                            {
                                label: 'Forecasted After Policy',
                                data: afters,
                                backgroundColor: 'rgba(16, 185, 129, 0.4)',
                                borderColor: '#10b981',
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#9ca3af' }
                            }
                        },
                        scales: {
                            x: {
                                ticks: { color: '#9ca3af' }
                            },
                            y: {
                                ticks: { color: '#9ca3af' },
                                max: 250
                            }
                        }
                    }
                });
            });
    }
    
    document.getElementById("run-simulation-btn").addEventListener("click", runSimulation);
    document.querySelector('[data-tab="sim-section"]').addEventListener("click", () => {
        setTimeout(runSimulation, 150); // Delay briefly so container expands first
    });

    // ---------------------------------------------------------
    // 5. CITIZEN ADVISORY COMPONENT
    // ---------------------------------------------------------
    
    let advisoryRole = "GENERAL";
    let advisoryLang = "EN";
    
    function populateAdvisoryDropdown() {
        const select = document.getElementById("advisory-ward-select");
        select.innerHTML = "";
        
        wardsList.forEach(w => {
            const opt = document.createElement("option");
            opt.value = w.id;
            opt.textContent = `${w.name} (Zone: ${w.zone_name})`;
            select.appendChild(opt);
        });
        
        select.onchange = loadAdvisory;
        loadAdvisory();
    }
    
    // Wire button arrays
    const roleBtns = document.querySelectorAll("#advisory-role-grid .btn-select");
    roleBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            roleBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            advisoryRole = btn.getAttribute("data-role");
            loadAdvisory();
        });
    });
    
    const langBtns = document.querySelectorAll("#advisory-lang-grid .btn-select");
    langBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            langBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            advisoryLang = btn.getAttribute("data-lang");
            loadAdvisory();
        });
    });
    
    function loadAdvisory() {
        const wardId = document.getElementById("advisory-ward-select").value;
        if (!wardId) return;
        
        fetch(`/api/advisory?ward_id=${wardId}&role=${advisoryRole}&language=${advisoryLang}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById("advisory-output-content").textContent = data.advisory;
            })
            .catch(err => {
                document.getElementById("advisory-output-content").textContent = "Error gathering advisory message.";
            });
    }

    // ---------------------------------------------------------
    // 6. AI COPILOT CHAT COMPONENT
    // ---------------------------------------------------------
    
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-user-input");
    const chatSendBtn = document.getElementById("chat-send-btn");
    
    function appendMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    function handleSend() {
        const queryText = chatInput.value.trim();
        if (!queryText) return;
        
        appendMessage(queryText, "user");
        chatInput.value = "";
        
        fetch("/api/copilot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: queryText })
        })
            .then(res => res.json())
            .then(data => {
                appendMessage(data.answer, "bot");
                
                // If the copilot suggests action keywords, display them in the console
                if (data.context && data.context.suggested_actions && data.context.suggested_actions.length > 0) {
                    const actionContainer = document.createElement("div");
                    actionContainer.style.marginTop = "8px";
                    actionContainer.style.display = "flex";
                    actionContainer.style.gap = "8px";
                    
                    data.context.suggested_actions.forEach(act => {
                        const actBadge = document.createElement("span");
                        actBadge.className = "priority-badge";
                        actBadge.style.backgroundColor = "rgba(0, 242, 254, 0.15)";
                        actBadge.style.color = "var(--accent-blue)";
                        actBadge.style.borderColor = "var(--accent-blue)";
                        actBadge.style.border = "1px solid";
                        actBadge.style.cursor = "pointer";
                        actBadge.textContent = `✓ ${act}`;
                        actBadge.onclick = () => alert(`Action Logged: ${act}`);
                        actionContainer.appendChild(actBadge);
                    });
                    chatBox.appendChild(actionContainer);
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            })
            .catch(err => {
                appendMessage("Sorry, I encountered an issue reaching the copilot servers.", "bot");
            });
    }
    
    chatSendBtn.addEventListener("click", handleSend);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSend();
    });
    
    // Suggestion pills binding
    document.querySelectorAll(".suggestion-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            chatInput.value = pill.textContent;
            handleSend();
        });
    });

    // ---------------------------------------------------------
    // BOOTSTRAP INITIALIZATION
    // ---------------------------------------------------------
    initMap();
    loadWardsMap();
});
