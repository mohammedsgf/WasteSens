/**
 * Leaflet map manager for the dashboard.
 * Exposes window.mapManager for use by dashboard.js.
 *
 * Marker logic reused from the original PyQt5 map_widget.py inline JS.
 */
(function () {
    "use strict";

    const config = window.APP_CONFIG || {
        mapCenterLat: 40.7128,
        mapCenterLng: -74.006,
        mapZoom: 13,
    };

    // Initialize Leaflet map
    const map = L.map("map").setView(
        [config.mapCenterLat, config.mapCenterLng],
        config.mapZoom
    );

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
    }).addTo(map);

    // Internal state
    const markers = {};       // device_id -> L.marker
    const deviceData = {};    // device_id -> {battery, fill, connected}
    let selectedDevice = null;

    // ---- Marker Icon Helpers ----

    function getBatteryColor(battery, connected) {
        if (!connected) return "gray";
        if (battery < 20) return "#dc2626";
        if (battery < 50) return "#ea580c";
        return "#16a34a";
    }

    function getFillColor(fill, connected) {
        if (!connected) return "gray";
        if (fill > 80) return "#dc2626";
        if (fill > 50) return "#ea580c";
        return "#16a34a";
    }

    function createMarkerIcon(battery, fill, connected, size) {
        size = size || 24;
        const batteryColor = getBatteryColor(battery, connected);
        const fillColor = getFillColor(fill, connected);
        const opacity = connected ? 1.0 : 0.6;
        const innerSize = Math.round(size * 0.42);

        return L.divIcon({
            className: "device-marker",
            html:
                '<div style="position:relative;width:' + size + "px;height:" + size + 'px;">' +
                '<div style="position:absolute;width:' + size + "px;height:" + size + "px;border-radius:50%;border:3px solid " + batteryColor + ";background:" + fillColor + ";box-shadow:0 2px 4px rgba(0,0,0,0.3);opacity:" + opacity + ';"></div>' +
                '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:' + innerSize + "px;height:" + innerSize + "px;border-radius:50%;background:#fff;border:1px solid " + batteryColor + ';"></div>' +
                "</div>",
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2],
        });
    }

    function createHighlightIcon(battery, fill, connected) {
        const size = 36;
        const batteryColor = getBatteryColor(battery, connected);
        const fillColor = getFillColor(fill, connected);
        const opacity = connected ? 1.0 : 0.6;

        return L.divIcon({
            className: "device-marker-selected",
            html:
                '<div style="position:relative;width:' + size + "px;height:" + size + 'px;">' +
                '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:' + size + "px;height:" + size + "px;border-radius:50%;background:" + batteryColor + ";opacity:0.3;box-shadow:0 0 15px " + batteryColor + ';"></div>' +
                '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:32px;height:32px;border-radius:50%;border:4px solid ' + batteryColor + ";background:" + fillColor + ";box-shadow:0 0 10px rgba(0,0,0,0.5),0 0 20px " + batteryColor + ";opacity:" + opacity + ';"></div>' +
                '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid ' + batteryColor + ';box-shadow:0 0 5px rgba(0,0,0,0.3);"></div>' +
                "</div>",
            iconSize: [size, size],
            iconAnchor: [size / 2, size / 2],
        });
    }

    function buildPopup(device) {
        const d = device;
        const loc = d.location || {};
        const statusHtml = d.connected
            ? ""
            : '<span style="color:#dc2626;font-weight:600;">[DISCONNECTED]</span><br>';
        const batColor = d.battery_level < 20 ? "#dc2626" : d.battery_level < 50 ? "#ea580c" : "#16a34a";
        const fillColor = d.fill_level > 80 ? "#dc2626" : d.fill_level > 50 ? "#ea580c" : "#16a34a";
        const lat = loc.latitude != null ? loc.latitude.toFixed(4) : "?";
        const lng = loc.longitude != null ? loc.longitude.toFixed(4) : "?";

        return (
            "<b>Device: " + d.device_id + "</b><br>" +
            statusHtml +
            '<b>Battery:</b> <span style="color:' + batColor + ';">' + d.battery_level + "%</span><br>" +
            '<b>Fill Level:</b> <span style="color:' + fillColor + ';">' + d.fill_level + "%</span><br>" +
            "Location: " + lat + ", " + lng
        );
    }

    // ---- Public API ----

    window.mapManager = {
        addDevice: function (device) {
            const loc = device.location;
            if (!loc || loc.latitude == null || loc.longitude == null) return;

            // Remove existing if any
            if (markers[device.device_id]) {
                map.removeLayer(markers[device.device_id]);
            }

            const marker = L.marker([loc.latitude, loc.longitude], {
                icon: createMarkerIcon(device.battery_level, device.fill_level, device.connected),
            }).addTo(map);

            marker.bindPopup(buildPopup(device));
            markers[device.device_id] = marker;
            deviceData[device.device_id] = {
                battery: device.battery_level,
                fill: device.fill_level,
                connected: device.connected,
            };

            // Auto fit bounds on first device
            if (Object.keys(markers).length === 1) {
                map.setView([loc.latitude, loc.longitude], 13);
            }
        },

        updateDevice: function (device) {
            const loc = device.location;
            if (!loc || loc.latitude == null || loc.longitude == null) return;

            if (!markers[device.device_id]) {
                this.addDevice(device);
                return;
            }

            const marker = markers[device.device_id];
            marker.setLatLng([loc.latitude, loc.longitude]);
            marker.setIcon(
                selectedDevice === device.device_id
                    ? createHighlightIcon(device.battery_level, device.fill_level, device.connected)
                    : createMarkerIcon(device.battery_level, device.fill_level, device.connected)
            );
            marker.setPopupContent(buildPopup(device));

            deviceData[device.device_id] = {
                battery: device.battery_level,
                fill: device.fill_level,
                connected: device.connected,
            };
        },

        markDisconnected: function (deviceId) {
            if (!markers[deviceId]) return;
            const marker = markers[deviceId];
            marker.setIcon(createMarkerIcon(0, 0, false));
            if (deviceData[deviceId]) deviceData[deviceId].connected = false;
        },

        centerOnDevice: function (deviceId) {
            if (markers[deviceId]) {
                map.setView(markers[deviceId].getLatLng(), 15);
            }
        },

        highlightDevice: function (device) {
            // Unhighlight previous
            if (selectedDevice && markers[selectedDevice] && selectedDevice !== device.device_id) {
                const prev = deviceData[selectedDevice];
                if (prev) {
                    markers[selectedDevice].setIcon(
                        createMarkerIcon(prev.battery, prev.fill, prev.connected)
                    );
                }
            }

            selectedDevice = device.device_id;

            if (markers[device.device_id]) {
                markers[device.device_id].setIcon(
                    createHighlightIcon(device.battery_level, device.fill_level, device.connected)
                );
                markers[device.device_id].openPopup();
            }
        },

        fitBounds: function () {
            const latLngs = Object.values(markers).map(function (m) {
                return m.getLatLng();
            });
            if (latLngs.length > 0) {
                map.fitBounds(latLngs, { padding: [50, 50] });
            }
        },
    };
})();
