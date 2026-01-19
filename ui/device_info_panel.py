"""
Device Information Panel for displaying detailed device information
"""
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from models.device import Device

logger = logging.getLogger(__name__)


class DeviceInfoPanel(QWidget):
    """Panel displaying detailed information about a selected device"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device: Device = None
        self._setup_ui()
        self._show_no_selection()
    
    def _setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        self.title = QLabel("Device Information")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title.setFont(title_font)
        layout.addWidget(self.title)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Info container
        self.info_container = QWidget()
        self.info_layout = QGridLayout(self.info_container)
        self.info_layout.setSpacing(8)
        self.info_layout.setColumnStretch(1, 1)
        layout.addWidget(self.info_container)
        
        layout.addStretch()
    
    def _show_no_selection(self):
        """Show message when no device is selected"""
        self._clear_info()
        no_selection = QLabel("No device selected.\nSelect a device from the list to view details.")
        no_selection.setAlignment(Qt.AlignCenter)
        no_selection.setStyleSheet("color: gray; padding: 20px;")
        self.info_layout.addWidget(no_selection, 0, 0, 1, 2)
    
    def _clear_info(self):
        """Clear all info widgets"""
        while self.info_layout.count():
            child = self.info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_device(self, device: Device):
        """Show information for a selected device"""
        self.current_device = device
        self._clear_info()
        
        if device is None:
            self._show_no_selection()
            self.title.setText("Device Information")
            self.title.setStyleSheet("")
            return
        
        # Update title to show selected device
        self.title.setText(f"Device Information - {device.device_id}")
        self.title.setStyleSheet("color: #0066cc; font-weight: bold; padding: 5px; background-color: #e6f3ff; border-radius: 3px;")
        
        # Device ID
        self._add_info_row("Device ID:", device.device_id, 0)
        
        # Status
        status_text = "Connected" if device.connected else "Disconnected"
        status_color = "green" if device.connected else "red"
        status_label = QLabel(f'<span style="color: {status_color}; font-weight: bold;">{status_text}</span>')
        self.info_layout.addWidget(QLabel("Status:"), 1, 0)
        self.info_layout.addWidget(status_label, 1, 1)
        
        # Battery Level
        battery_text = f"{device.battery_level}%"
        battery_color = "red" if device.battery_level < 20 else ("orange" if device.battery_level < 50 else "green")
        battery_label = QLabel(f'<span style="color: {battery_color}; font-weight: bold;">{battery_text}</span>')
        self.info_layout.addWidget(QLabel("Battery Level:"), 2, 0)
        self.info_layout.addWidget(battery_label, 2, 1)
        
        # Fill Level
        fill_text = f"{device.fill_level}%"
        fill_color = "green" if device.fill_level < 30 else ("orange" if device.fill_level < 70 else "red")
        fill_label = QLabel(f'<span style="color: {fill_color}; font-weight: bold;">{fill_text}</span>')
        self.info_layout.addWidget(QLabel("Fill Level:"), 3, 0)
        self.info_layout.addWidget(fill_label, 3, 1)
        
        # Location
        if device.location:
            lat, lng = device.location
            location_text = f"{lat:.6f}, {lng:.6f}"
            self._add_info_row("Latitude:", f"{lat:.6f}", 4)
            self._add_info_row("Longitude:", f"{lng:.6f}", 5)
        else:
            self._add_info_row("Location:", "Not available", 4)
        
        # Last Update
        time_since = datetime.now() - device.last_update
        if time_since.total_seconds() < 60:
            time_text = f"{int(time_since.total_seconds())} seconds ago"
        elif time_since.total_seconds() < 3600:
            time_text = f"{int(time_since.total_seconds() / 60)} minutes ago"
        else:
            time_text = f"{int(time_since.total_seconds() / 3600)} hours ago"
        
        self._add_info_row("Last Update:", time_text, 6)
        self._add_info_row("Last Update Time:", device.last_update.strftime("%Y-%m-%d %H:%M:%S"), 7)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.info_layout.addWidget(line, 8, 0, 1, 2)
        
        # Status indicators
        status_title = QLabel("Status Indicators:")
        status_font = QFont()
        status_font.setBold(True)
        status_title.setFont(status_font)
        self.info_layout.addWidget(status_title, 9, 0, 1, 2)
        
        # Battery status
        if device.battery_level < 20:
            battery_status = "⚠️ Critical - Battery very low"
        elif device.battery_level < 50:
            battery_status = "⚠️ Low - Battery needs attention"
        else:
            battery_status = "✓ Good - Battery level acceptable"
        self._add_info_row("Battery Status:", battery_status, 10)
        
        # Fill status
        if device.fill_level > 80:
            fill_status = "⚠️ Full - Container nearly full"
        elif device.fill_level > 50:
            fill_status = "⚠️ Moderate - Container filling up"
        else:
            fill_status = "✓ Good - Container has space"
        self._add_info_row("Fill Status:", fill_status, 11)
    
    def _add_info_row(self, label_text: str, value_text: str, row: int):
        """Add a row of information"""
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold;")
        value = QLabel(str(value_text))
        value.setWordWrap(True)
        self.info_layout.addWidget(label, row, 0)
        self.info_layout.addWidget(value, row, 1)
    
    def update_device(self, device: Device):
        """Update displayed device information"""
        if self.current_device and self.current_device.device_id == device.device_id:
            self.show_device(device)

