"""
Main Window for the IoT Dashboard
"""
import logging
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QSplitter, QStatusBar, QMenuBar, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from .map_widget import MapWidget
from .device_panel import DevicePanel
from .device_info_panel import DeviceInfoPanel
from mqtt_client import MQTTClient
from device_manager import DeviceManager
import config

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mqtt_client = None
        self.device_manager = None
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._periodic_update)
        self._setup_ui()
        self._setup_mqtt()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Smart Waste IoT Dashboard")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter for map and side panels
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Map widget (takes most of the space)
        self.map_widget = MapWidget()
        main_splitter.addWidget(self.map_widget)
        
        # Create right side splitter for device list and info panel
        right_splitter = QSplitter(Qt.Vertical)
        
        # Device panel (device list)
        self.device_panel = DevicePanel()
        right_splitter.addWidget(self.device_panel)
        
        # Device info panel (detailed information)
        self.device_info_panel = DeviceInfoPanel()
        right_splitter.addWidget(self.device_info_panel)
        
        # Set right splitter proportions (60% list, 40% info)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)
        right_splitter.setSizes([300, 200])
        
        main_splitter.addWidget(right_splitter)
        
        # Set main splitter proportions (70% map, 30% side panels)
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 3)
        main_splitter.setSizes([1000, 500])
        
        layout.addWidget(main_splitter)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected from MQTT broker")
    
    def _create_menu_bar(self):
        """Create menu bar with actions"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fit_bounds_action = QAction("Fit Map to All Devices", self)
        fit_bounds_action.triggered.connect(self.map_widget.fit_bounds)
        view_menu.addAction(fit_bounds_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        connect_action = QAction("Connect to MQTT", self)
        connect_action.triggered.connect(self._connect_mqtt)
        tools_menu.addAction(connect_action)
        
        disconnect_action = QAction("Disconnect from MQTT", self)
        disconnect_action.triggered.connect(self._disconnect_mqtt)
        tools_menu.addAction(disconnect_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_mqtt(self):
        """Setup MQTT client and device manager"""
        self.device_manager = DeviceManager(self)
        self.mqtt_client = MQTTClient(self)
        
        # Auto-connect on startup
        self._connect_mqtt()
    
    def _connect_signals(self):
        """Connect signals between components"""
        # MQTT client signals
        self.mqtt_client.message_received.connect(self._on_mqtt_message)
        self.mqtt_client.connection_changed.connect(self._on_connection_changed)
        
        # Device manager signals
        self.device_manager.device_added.connect(self._on_device_added)
        self.device_manager.device_updated.connect(self._on_device_updated)
        self.device_manager.device_disconnected.connect(self._on_device_disconnected)
        
        # Device panel signals
        self.device_panel.device_selected.connect(self._on_device_selected)
        
        # Device manager signals for info panel updates
        self.device_manager.device_updated.connect(self._update_device_info_if_selected)
        
        # Start periodic update timer
        self.update_timer.start(config.UPDATE_INTERVAL_MS)
    
    def _connect_mqtt(self):
        """Connect to MQTT broker"""
        if self.mqtt_client and not self.mqtt_client.is_connected():
            self.mqtt_client.connect()
            self.status_bar.showMessage("Connecting to MQTT broker...")
    
    def _disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
    
    def _on_mqtt_message(self, topic: str, payload: dict):
        """Handle MQTT message received"""
        logger.debug(f"Received MQTT message on {topic}")
        self.device_manager.process_mqtt_message(topic, payload)
    
    def _on_connection_changed(self, connected: bool, message: str):
        """Handle MQTT connection status change"""
        if connected:
            self.status_bar.showMessage(f"Connected to MQTT broker: {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}")
        else:
            self.status_bar.showMessage(f"MQTT: {message}")
    
    def _on_device_added(self, device):
        """Handle new device added"""
        logger.info(f"New device added: {device.device_id}")
        self.map_widget.add_device(device)
        self.device_panel.add_device(device)
        
        # Auto-fit bounds if this is the first device
        if self.device_manager.get_device_count() == 1:
            QTimer.singleShot(500, self.map_widget.fit_bounds)
        
        # If no device is selected, select this new device
        if self.device_info_panel.current_device is None:
            self.device_info_panel.show_device(device)
    
    def _on_device_updated(self, device):
        """Handle device update"""
        self.map_widget.update_device(device)
        self.device_panel.update_device(device)
    
    def _on_device_selected(self, device_id: str):
        """Handle device selection from panel"""
        # Get device
        device = self.device_manager.get_device(device_id)
        if not device:
            self.device_info_panel.show_device(None)
            return
        
        # Center map on device
        self.map_widget.center_on_device(device_id)
        
        # Highlight device on map (make it bigger with glow)
        self.map_widget.highlight_device(device)
        
        # Show device information in info panel
        self.device_info_panel.show_device(device)
        
        # Ensure info panel is visible by bringing it into view
        # The splitter should already show it, but we can ensure it's expanded
        logger.info(f"Device {device_id} selected - highlighted on map and shown in info panel")
    
    def _update_device_info_if_selected(self, device: Device):
        """Update device info panel if this device is currently selected"""
        if (self.device_info_panel.current_device and 
            self.device_info_panel.current_device.device_id == device.device_id):
            self.device_info_panel.update_device(device)
            # Re-highlight with updated data
            self.map_widget.highlight_device(device)
    
    def _on_device_disconnected(self, device):
        """Handle device disconnection (timeout)"""
        logger.info(f"Device {device.device_id} disconnected (timed out)")
        self.map_widget.mark_device_disconnected(device)
        self.device_panel.update_device(device)  # Update panel to show disconnected status
        self.device_info_panel.update_device(device)  # Update info panel if this device is selected
    
    def _periodic_update(self):
        """Periodic update for UI refresh"""
        # This can be used for any periodic UI updates if needed
        pass
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Smart Waste IoT Dashboard",
            "Smart Waste IoT Dashboard\n\n"
            "A real-time monitoring dashboard for IoT devices.\n\n"
            "Features:\n"
            "- Real-time device tracking on geographic map\n"
            "- MQTT integration for live data\n"
            "- Battery and empty level monitoring\n"
            "- Multiple device support\n\n"
            f"MQTT Broker: {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}\n"
            f"Topic Pattern: {config.MQTT_TOPIC_PATTERN}"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        event.accept()

