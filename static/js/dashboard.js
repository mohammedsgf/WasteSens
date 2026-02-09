/**
 * Dashboard controller: WebSocket client, device table, device info panel, sign-out.
 * Depends on map.js being loaded first (window.mapManager).
 */
(function () {
    "use strict";

    // ---- State ----
    const devices = {};          // device_id -> device object
    let selectedDeviceId = null;
    let ws = null;
    let wsReconnectTimer = null;
    const WS_RECONNECT_DELAY = 3000;

    // ---- DOM refs ----
    const tableBody = document.getElementById("device-table-body");
    const filterInput = document.getElementById("device-filter");
    const deviceCountEl = document.getElementById("device-count");
    const infoContent = document.getElementById("device-info-content");
    const mqttStatusDot = document.querySelector("#mqtt-status .status-dot");
    const mqttStatusText = document.querySelector("#mqtt-status .status-text");
    const signoutBtn = document.getElementById("signout-btn");

    // ---- Sign Out ----
    if (signoutBtn) {
        signoutBtn.addEventListener("click", async function (e) {
            e.preventDefault();
            try {
                await fetch("/api/auth/signout", { method: "POST" });
            } catch (_) { /* ignore */ }
            window.location.href = "/signin";
        });
    }

    // ---- WebSocket ----
    function connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        ws = new WebSocket(wsUrl);

        ws.onopen = function () {
            console.log("WebSocket connected");
            setMqttStatus(true, "Connected");
        };

        ws.onmessage = function (evt) {
            try {
                const msg = JSON.parse(evt.data);
                handleDeviceEvent(msg);
            } catch (e) {
                console.error("Failed to parse WS message:", e);
            }
        };

        ws.onclose = function () {
            console.log("WebSocket closed, reconnecting...");
            setMqttStatus(false, "Disconnected - reconnecting...");
            scheduleReconnect();
        };

        ws.onerror = function () {
            setMqttStatus(false, "Connection error");
        };

        // Keep-alive ping every 30 seconds
        setInterval(function () {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send("ping");
            }
        }, 30000);
    }

    function scheduleReconnect() {
        if (wsReconnectTimer) clearTimeout(wsReconnectTimer);
        wsReconnectTimer = setTimeout(connectWebSocket, WS_RECONNECT_DELAY);
    }

    function setMqttStatus(connected, text) {
        if (mqttStatusDot) {
            mqttStatusDot.className = "status-dot " + (connected ? "connected" : "disconnected");
        }
        if (mqttStatusText) {
            mqttStatusText.textContent = text;
        }
    }

    // ---- Device Events ----
    function handleDeviceEvent(msg) {
        const { event, device } = msg;
        if (!device || !device.device_id) return;

        devices[device.device_id] = device;

        switch (event) {
            case "device_added":
                if (window.mapManager) window.mapManager.addDevice(device);
                break;
            case "device_updated":
                if (window.mapManager) window.mapManager.updateDevice(device);
                break;
            case "device_disconnected":
                if (window.mapManager) window.mapManager.markDisconnected(device.device_id);
                break;
        }

        renderTable();
        updateDeviceCount();

        // Update info panel if this device is selected
        if (selectedDeviceId === device.device_id) {
            renderDeviceInfo(device);
        }
    }

    // ---- Device Table ----
    function renderTable() {
        const filterText = (filterInput ? filterInput.value : "").toLowerCase();
        const sortedIds = Object.keys(devices).sort();

        tableBody.innerHTML = "";

        for (const id of sortedIds) {
            const d = devices[id];
            if (filterText && !id.toLowerCase().includes(filterText)) continue;

            const tr = document.createElement("tr");
            if (id === selectedDeviceId) tr.classList.add("selected");

            tr.innerHTML = `
                <td>${escapeHtml(d.device_id)}</td>
                <td><span class="badge ${d.connected ? 'badge-connected' : 'badge-disconnected'}">${d.connected ? 'Online' : 'Offline'}</span></td>
                <td><span class="${batteryClass(d.battery_level)}">${d.battery_level}%</span></td>
                <td><span class="${fillClass(d.fill_level)}">${d.fill_level}%</span></td>
                <td>${formatLocation(d.location)}</td>
            `;

            tr.addEventListener("click", function () {
                selectDevice(d.device_id);
            });

            tableBody.appendChild(tr);
        }
    }

    function updateDeviceCount() {
        if (deviceCountEl) {
            deviceCountEl.textContent = Object.keys(devices).length;
        }
    }

    // ---- Device Selection ----
    function selectDevice(deviceId) {
        selectedDeviceId = deviceId;
        const device = devices[deviceId];

        // Highlight table row
        renderTable();

        // Show info panel
        if (device) {
            renderDeviceInfo(device);
        }

        // Center and highlight on map
        if (window.mapManager) {
            window.mapManager.centerOnDevice(deviceId);
            if (device) {
                window.mapManager.highlightDevice(device);
            }
        }
    }

    // ---- Device Info Panel ----
    function renderDeviceInfo(device) {
        if (!device) {
            infoContent.innerHTML = '<p class="no-selection">Select a device to view details.</p>';
            return;
        }

        const loc = device.location;
        const lastUpdate = device.last_update ? new Date(device.last_update) : null;
        const timeSince = lastUpdate ? formatTimeSince(lastUpdate) : "N/A";

        const statusColor = device.connected ? "var(--color-success)" : "var(--color-danger)";
        const statusText = device.connected ? "Connected" : "Disconnected";
        const batteryColor = device.battery_level < 20 ? "var(--color-danger)" : device.battery_level < 50 ? "var(--color-warning)" : "var(--color-success)";
        const fillColor = device.fill_level > 80 ? "var(--color-danger)" : device.fill_level > 50 ? "var(--color-warning)" : "var(--color-success)";

        let batteryStatus, fillStatus;
        if (device.battery_level < 20) batteryStatus = "Critical - Battery very low";
        else if (device.battery_level < 50) batteryStatus = "Low - Needs attention";
        else batteryStatus = "Good - Acceptable level";

        if (device.fill_level > 80) fillStatus = "Full - Needs collection";
        else if (device.fill_level > 50) fillStatus = "Moderate - Filling up";
        else fillStatus = "Good - Has space";

        infoContent.innerHTML = `
            <div class="info-device-title">${escapeHtml(device.device_id)}</div>
            <div class="info-grid">
                <span class="info-label">Status:</span>
                <span class="info-value" style="color:${statusColor};font-weight:600;">${statusText}</span>

                <span class="info-label">Battery:</span>
                <span class="info-value" style="color:${batteryColor};font-weight:600;">${device.battery_level}%</span>

                <span class="info-label">Fill Level:</span>
                <span class="info-value" style="color:${fillColor};font-weight:600;">${device.fill_level}%</span>

                <span class="info-label">Latitude:</span>
                <span class="info-value">${loc && loc.latitude != null ? loc.latitude.toFixed(6) : 'N/A'}</span>

                <span class="info-label">Longitude:</span>
                <span class="info-value">${loc && loc.longitude != null ? loc.longitude.toFixed(6) : 'N/A'}</span>

                <span class="info-label">Last Update:</span>
                <span class="info-value">${timeSince}</span>

                <span class="info-label">Update Time:</span>
                <span class="info-value">${lastUpdate ? lastUpdate.toLocaleString() : 'N/A'}</span>

                <div class="info-divider"></div>
                <span class="info-section-title">Status Indicators</span>

                <span class="info-label">Battery:</span>
                <span class="info-value">${batteryStatus}</span>

                <span class="info-label">Fill:</span>
                <span class="info-value">${fillStatus}</span>
            </div>
        `;
    }

    // ---- Filter ----
    if (filterInput) {
        filterInput.addEventListener("input", renderTable);
    }

    // ---- Helpers ----
    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function batteryClass(level) {
        if (level < 20) return "badge-battery-low";
        if (level < 50) return "badge-battery-medium";
        return "badge-battery-good";
    }

    function fillClass(level) {
        if (level > 80) return "badge-fill-high";
        if (level > 50) return "badge-fill-medium";
        return "badge-fill-low";
    }

    function formatLocation(loc) {
        if (!loc || loc.latitude == null || loc.longitude == null) return "N/A";
        return loc.latitude.toFixed(4) + ", " + loc.longitude.toFixed(4);
    }

    function formatTimeSince(date) {
        const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
        if (seconds < 60) return seconds + "s ago";
        if (seconds < 3600) return Math.floor(seconds / 60) + "m ago";
        return Math.floor(seconds / 3600) + "h ago";
    }

    // ---- Init ----
    connectWebSocket();
})();
