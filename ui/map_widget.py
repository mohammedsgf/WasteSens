"""
Map Widget for displaying devices on a geographic map
"""
import logging
from typing import Optional, Dict
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, QPointF
from models.device import Device
import config

logger = logging.getLogger(__name__)


class MapWidget(QWidget):
    """Widget displaying devices on a Leaflet map"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.web_view = QWebEngineView(self)
        self.devices: Dict[str, Device] = {}
        self.map_ready = False
        self.pending_devices = []  # Devices waiting to be added
        self._setup_ui()
        self._load_map()
    
    def _setup_ui(self):
        """Setup the UI layout"""
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
    
    def _load_map(self):
        """Load the Leaflet map HTML"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialize map
        var map = L.map('map').setView([{config.DEFAULT_MAP_CENTER[0]}, {config.DEFAULT_MAP_CENTER[1]}], {config.DEFAULT_ZOOM_LEVEL});
        window.map = map;
        window.markers = {{}};
        window.selectedDevice = null;
        window.deviceData = {{}};
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);
        
        // Set up JavaScript bridge functions
        window.qtMapWidget = {{
            addMarker: function(deviceId, lat, lng, battery, fill, isConnected) {{
                if (window.map) {{
                    // Remove existing marker if present
                    if (window.markers && window.markers[deviceId]) {{
                        window.map.removeLayer(window.markers[deviceId]);
                    }}
                    
                    // Determine colors based on connection status, battery, and fill level
                    var batteryColor;
                    var fillColor;
                    var opacity = 1.0;
                    
                    if (isConnected === false) {{
                        batteryColor = 'gray';
                        fillColor = 'gray';
                        opacity = 0.6;
                    }} else {{
                        // Battery level color (outer ring)
                        batteryColor = battery < 20 ? 'red' : (battery < 50 ? 'orange' : 'green');
                        // Fill level color (inner circle) - inverse logic (high fill = bad)
                        fillColor = fill > 80 ? 'red' : (fill > 50 ? 'orange' : 'green');
                    }}
                    
                    // Create marker with dual indicators: outer ring (battery) and inner circle (fill)
                    var marker = L.marker([lat, lng], {{
                        icon: L.divIcon({{
                            className: 'device-marker',
                            html: '<div style="position: relative; width: 24px; height: 24px;">' +
                                  '<div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 3px solid ' + batteryColor + '; background-color: ' + fillColor + '; box-shadow: 0 2px 4px rgba(0,0,0,0.3); opacity: ' + opacity + ';"></div>' +
                                  '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background-color: white; border: 1px solid ' + batteryColor + ';"></div>' +
                                  '</div>',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        }})
                    }}).addTo(window.map);
                    
                    var statusText = isConnected === false ? '<span style="color: red;">[DISCONNECTED]</span><br>' : '';
                    var batteryColorText = battery < 20 ? 'red' : (battery < 50 ? 'orange' : 'green');
                    var fillColorText = fill > 80 ? 'red' : (fill > 50 ? 'orange' : 'green');
                    var popupContent = '<b>Device: ' + deviceId + '</b><br>' +
                                      statusText +
                                      '<b>Battery:</b> <span style="color: ' + batteryColorText + ';">' + battery + '%</span> (Ring color)<br>' +
                                      '<b>Fill Level:</b> <span style="color: ' + fillColorText + ';">' + fill + '%</span> (Circle color)<br>' +
                                      'Location: ' + lat.toFixed(4) + ', ' + lng.toFixed(4);
                    marker.bindPopup(popupContent);
                    
                    if (!window.markers) window.markers = {{}};
                    if (!window.deviceData) window.deviceData = {{}};
                    window.markers[deviceId] = marker;
                    window.deviceData[deviceId] = {{battery: battery, fill: fill, connected: isConnected}};
                    console.log('Marker added for device: ' + deviceId + ' (connected: ' + isConnected + ')');
                }} else {{
                    console.error('Map not initialized when trying to add marker for: ' + deviceId);
                }}
            }},
            updateMarker: function(deviceId, lat, lng, battery, fill, isConnected) {{
                if (window.markers && window.markers[deviceId]) {{
                    var marker = window.markers[deviceId];
                    marker.setLatLng([lat, lng]);
                    
                    // Determine colors based on connection status, battery, and fill level
                    var batteryColor;
                    var fillColor;
                    var opacity = 1.0;
                    
                    if (isConnected === false) {{
                        batteryColor = 'gray';
                        fillColor = 'gray';
                        opacity = 0.6;
                    }} else {{
                        // Battery level color (outer ring)
                        batteryColor = battery < 20 ? 'red' : (battery < 50 ? 'orange' : 'green');
                        // Fill level color (inner circle) - inverse logic (high fill = bad)
                        fillColor = fill > 80 ? 'red' : (fill > 50 ? 'orange' : 'green');
                    }}
                    
                    marker.setIcon(L.divIcon({{
                        className: 'device-marker',
                        html: '<div style="position: relative; width: 24px; height: 24px;">' +
                              '<div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 3px solid ' + batteryColor + '; background-color: ' + fillColor + '; box-shadow: 0 2px 4px rgba(0,0,0,0.3); opacity: ' + opacity + ';"></div>' +
                              '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background-color: white; border: 1px solid ' + batteryColor + ';"></div>' +
                              '</div>',
                        iconSize: [24, 24],
                        iconAnchor: [12, 12]
                    }}));
                    
                    var statusText = isConnected === false ? '<span style="color: red;">[DISCONNECTED]</span><br>' : '';
                    var batteryColorText = battery < 20 ? 'red' : (battery < 50 ? 'orange' : 'green');
                    var fillColorText = fill > 80 ? 'red' : (fill > 50 ? 'orange' : 'green');
                    var popupContent = '<b>Device: ' + deviceId + '</b><br>' +
                                      statusText +
                                      '<b>Battery:</b> <span style="color: ' + batteryColorText + ';">' + battery + '%</span> (Ring color)<br>' +
                                      '<b>Fill Level:</b> <span style="color: ' + fillColorText + ';">' + fill + '%</span> (Circle color)<br>' +
                                      'Location: ' + lat.toFixed(4) + ', ' + lng.toFixed(4);
                    marker.setPopupContent(popupContent);
                    // Update device data
                    if (!window.deviceData) window.deviceData = {{}};
                    window.deviceData[deviceId] = {{battery: battery, fill: fill, connected: isConnected}};
                    // If this is the selected device, update highlight
                    if (window.selectedDevice === deviceId) {{
                        window.qtMapWidget.highlightDevice(deviceId, battery, fill, isConnected);
                    }}
                    console.log('Marker updated for device: ' + deviceId + ' (connected: ' + isConnected + ')');
                }} else {{
                    console.warn('Marker not found for device: ' + deviceId + ', adding new marker');
                    // If marker doesn't exist, add it
                    if (window.map && window.qtMapWidget) {{
                        window.qtMapWidget.addMarker(deviceId, lat, lng, battery, fill, isConnected);
                    }}
                }}
            }},
            markDisconnected: function(deviceId) {{
                if (window.markers && window.markers[deviceId]) {{
                    var marker = window.markers[deviceId];
                    var latlng = marker.getLatLng();
                    // Update marker to show disconnected status
                    marker.setIcon(L.divIcon({{
                        className: 'device-marker',
                        html: '<div style="position: relative; width: 24px; height: 24px;">' +
                              '<div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 3px solid gray; background-color: gray; box-shadow: 0 2px 4px rgba(0,0,0,0.3); opacity: 0.6;"></div>' +
                              '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background-color: white; border: 1px solid gray;"></div>' +
                              '</div>',
                        iconSize: [24, 24],
                        iconAnchor: [12, 12]
                    }}));
                    // Update popup to show disconnected status
                    var popup = marker.getPopup();
                    if (popup) {{
                        var content = popup.getContent();
                        if (content && !content.includes('DISCONNECTED')) {{
                            popup.setContent('<span style="color: red;">[DISCONNECTED]</span><br>' + content);
                        }}
                    }}
                    console.log('Device marked as disconnected: ' + deviceId);
                }}
            }},
            removeMarker: function(deviceId) {{
                if (window.markers && window.markers[deviceId]) {{
                    window.map.removeLayer(window.markers[deviceId]);
                    delete window.markers[deviceId];
                    console.log('Marker removed for device: ' + deviceId);
                }}
            }},
            fitBounds: function() {{
                if (window.map && window.markers) {{
                    var bounds = [];
                    for (var deviceId in window.markers) {{
                        bounds.push(window.markers[deviceId].getLatLng());
                    }}
                    if (bounds.length > 0) {{
                        window.map.fitBounds(bounds, {{padding: [50, 50]}});
                        console.log('Map bounds fitted to ' + bounds.length + ' markers');
                    }}
                }}
            }},
            centerOnDevice: function(deviceId) {{
                if (window.markers && window.markers[deviceId]) {{
                    window.map.setView(window.markers[deviceId].getLatLng(), 15);
                    console.log('Map centered on device: ' + deviceId);
                }}
            }},
            highlightDevice: function(deviceId, battery, fill, isConnected) {{
                // Unhighlight previous selection
                if (window.selectedDevice && window.markers && window.markers[window.selectedDevice]) {{
                    var prevMarker = window.markers[window.selectedDevice];
                    var prevDevice = window.deviceData ? window.deviceData[window.selectedDevice] : null;
                    if (prevDevice) {{
                        // Restore normal size
                        var batteryColor = prevDevice.battery < 20 ? 'red' : (prevDevice.battery < 50 ? 'orange' : 'green');
                        var fillColor = prevDevice.fill > 80 ? 'red' : (prevDevice.fill > 50 ? 'orange' : 'green');
                        var opacity = prevDevice.connected ? 1.0 : 0.6;
                        if (!prevDevice.connected) {{
                            batteryColor = 'gray';
                            fillColor = 'gray';
                        }}
                        prevMarker.setIcon(L.divIcon({{
                            className: 'device-marker',
                            html: '<div style="position: relative; width: 24px; height: 24px;">' +
                                  '<div style="position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 3px solid ' + batteryColor + '; background-color: ' + fillColor + '; box-shadow: 0 2px 4px rgba(0,0,0,0.3); opacity: ' + opacity + ';"></div>' +
                                  '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background-color: white; border: 1px solid ' + batteryColor + ';"></div>' +
                                  '</div>',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        }}));
                    }}
                }}
                
                // Highlight new selection
                if (window.markers && window.markers[deviceId]) {{
                    window.selectedDevice = deviceId;
                    var marker = window.markers[deviceId];
                    
                    // Determine colors
                    var batteryColor;
                    var fillColor;
                    var opacity = 1.0;
                    if (isConnected === false) {{
                        batteryColor = 'gray';
                        fillColor = 'gray';
                        opacity = 0.6;
                    }} else {{
                        batteryColor = battery < 20 ? 'red' : (battery < 50 ? 'orange' : 'green');
                        fillColor = fill > 80 ? 'red' : (fill > 50 ? 'orange' : 'green');
                    }}
                    
                    // Make marker bigger with glow effect
                    marker.setIcon(L.divIcon({{
                        className: 'device-marker-selected',
                        html: '<div style="position: relative; width: 36px; height: 36px;">' +
                              '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 36px; height: 36px; border-radius: 50%; background-color: ' + batteryColor + '; opacity: 0.3; box-shadow: 0 0 15px ' + batteryColor + ';"></div>' +
                              '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; border-radius: 50%; border: 4px solid ' + batteryColor + '; background-color: ' + fillColor + '; box-shadow: 0 0 10px rgba(0,0,0,0.5), 0 0 20px ' + batteryColor + '; opacity: ' + opacity + ';"></div>' +
                              '<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 14px; height: 14px; border-radius: 50%; background-color: white; border: 2px solid ' + batteryColor + '; box-shadow: 0 0 5px rgba(0,0,0,0.3);"></div>' +
                              '</div>',
                        iconSize: [36, 36],
                        iconAnchor: [18, 18]
                    }}));
                    
                    // Open popup automatically
                    marker.openPopup();
                    
                    console.log('Device highlighted: ' + deviceId);
                }}
            }},
            unhighlightDevice: function() {{
                if (window.selectedDevice) {{
                    window.selectedDevice = null;
                }}
            }}
        }};
        
        // Signal that map is ready
        console.log('Map initialized and ready');
    </script>
</body>
</html>
"""
        self.web_view.setHtml(html_content)
        
        # Wait for page to load, then mark as ready
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self._on_map_ready)
    
    def _on_map_ready(self):
        """Callback when map is ready"""
        self.map_ready = True
        logger.info("Map widget ready")
        # Process any pending devices
        for device in self.pending_devices:
            self.add_device(device)
        self.pending_devices.clear()
    
    def add_device(self, device: Device):
        """
        Add a device marker to the map
        
        Args:
            device: Device instance to add
        """
        if device.location is None:
            logger.warning(f"Device {device.device_id} has no location, skipping map marker")
            return
        
        # If device already exists, update it instead
        if device.device_id in self.devices:
            self.update_device(device)
            return
        
        lat, lng = device.location
        self.devices[device.device_id] = device
        
        logger.info(f"Adding device {device.device_id} to map at ({lat}, {lng})")
        
        # If map not ready, queue the device
        if not self.map_ready:
            logger.info(f"Map not ready, queuing device {device.device_id}")
            self.pending_devices.append(device)
            return
        
        # Add marker via JavaScript - ensure map is ready
        device_id_escaped = device.device_id.replace("'", "\\'")
        js_code = f"""
        (function() {{
            if (window.map && window.qtMapWidget) {{
                try {{
                    window.qtMapWidget.addMarker(
                        '{device_id_escaped}',
                        {lat},
                        {lng},
                        {device.battery_level},
                        {device.fill_level},
                        {str(device.connected).lower()}
                    );
                    console.log('Successfully added marker for device: {device_id_escaped}');
                }} catch (e) {{
                    console.error('Error adding marker: ' + e.message);
                }}
            }} else {{
                console.error('Map or qtMapWidget not ready when adding device {device_id_escaped}');
                // Retry after a short delay
                setTimeout(function() {{
                    if (window.map && window.qtMapWidget) {{
                        try {{
                            window.qtMapWidget.addMarker(
                                '{device_id_escaped}',
                                {lat},
                                {lng},
                                {device.battery_level},
                                {device.fill_level},
                                {str(device.connected).lower()}
                            );
                            console.log('Successfully added marker (retry) for device: {device_id_escaped}');
                        }} catch (e) {{
                            console.error('Error adding marker (retry): ' + e.message);
                        }}
                    }}
                }}, 1000);
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def update_device(self, device: Device):
        """
        Update a device marker on the map
        
        Args:
            device: Device instance to update
        """
        if device.device_id not in self.devices:
            self.add_device(device)
            return
        
        if device.location is None:
            return
        
        lat, lng = device.location
        self.devices[device.device_id] = device
        
        # Update marker via JavaScript
        device_id_escaped = device.device_id.replace("'", "\\'")
        js_code = f"""
        (function() {{
            if (window.map && window.qtMapWidget) {{
                window.qtMapWidget.updateMarker(
                    '{device_id_escaped}',
                    {lat},
                    {lng},
                    {device.battery_level},
                    {device.fill_level},
                    {str(device.connected).lower()}
                );
            }} else {{
                console.warn('Map not ready for updateMarker: {device_id_escaped}');
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def mark_device_disconnected(self, device: Device):
        """
        Mark a device as disconnected on the map
        
        Args:
            device: Device instance to mark as disconnected
        """
        if device.device_id not in self.devices:
            return
        
        logger.info(f"Marking device {device.device_id} as disconnected on map")
        device_id_escaped = device.device_id.replace("'", "\\'")
        js_code = f"""
        (function() {{
            if (window.map && window.qtMapWidget) {{
                window.qtMapWidget.markDisconnected('{device_id_escaped}');
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def remove_device(self, device_id: str):
        """
        Remove a device marker from the map
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.devices:
            del self.devices[device_id]
        
        js_code = f"window.qtMapWidget.removeMarker('{device_id}');"
        self.web_view.page().runJavaScript(js_code)
    
    def fit_bounds(self):
        """Fit map bounds to show all devices"""
        js_code = """
        (function() {
            if (window.map && window.qtMapWidget) {
                window.qtMapWidget.fitBounds();
            } else {
                console.warn('Map not ready for fitBounds');
            }
        })();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def center_on_device(self, device_id: str):
        """
        Center map on a specific device
        
        Args:
            device_id: Device identifier
        """
        js_code = f"window.qtMapWidget.centerOnDevice('{device_id}');"
        self.web_view.page().runJavaScript(js_code)
    
    def highlight_device(self, device: Device):
        """
        Highlight a device on the map (make it bigger, add glow effect)
        
        Args:
            device: Device instance to highlight
        """
        if device.device_id not in self.devices:
            logger.warning(f"Device {device.device_id} not found on map for highlighting")
            return
        
        if device.location is None:
            return
        
        device_id_escaped = device.device_id.replace("'", "\\'")
        js_code = f"""
        (function() {{
            if (window.map && window.qtMapWidget) {{
                window.qtMapWidget.highlightDevice(
                    '{device_id_escaped}',
                    {device.battery_level},
                    {device.fill_level},
                    {str(device.connected).lower()}
                );
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
        logger.info(f"Highlighted device {device.device_id} on map")
    
    def unhighlight_device(self):
        """Remove highlighting from any selected device"""
        js_code = "window.qtMapWidget.unhighlightDevice();"
        self.web_view.page().runJavaScript(js_code)

