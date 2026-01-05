"""
Device Panel for displaying device list and information
"""
import logging
from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QLabel, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from models.device import Device

logger = logging.getLogger(__name__)


class DevicePanel(QWidget):
    """Panel displaying device list with filtering"""
    
    # Signal emitted when a device is selected
    # Arguments: device_id (str)
    device_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices: dict[str, Device] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        
        # Filter/search box
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search by device ID...")
        self.filter_input.textChanged.connect(self._filter_devices)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)
        
        # Device count label
        self.count_label = QLabel("Devices: 0")
        layout.addWidget(self.count_label)
        
        # Device table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Device ID", "Status", "Battery %", "Empty %", "Latitude", "Longitude"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
    
    def add_device(self, device: Device):
        """
        Add a device to the table
        
        Args:
            device: Device instance to add
        """
        self.devices[device.device_id] = device
        self._update_table()
    
    def update_device(self, device: Device):
        """
        Update a device in the table
        
        Args:
            device: Device instance to update
        """
        if device.device_id in self.devices:
            self.devices[device.device_id] = device
            self._update_table()
        else:
            self.add_device(device)
    
    def remove_device(self, device_id: str):
        """
        Remove a device from the table
        
        Args:
            device_id: Device identifier
        """
        if device_id in self.devices:
            del self.devices[device_id]
            self._update_table()
    
    def clear_all(self):
        """Clear all devices"""
        self.devices.clear()
        self._update_table()
    
    def _update_table(self):
        """Update the table with current devices"""
        filter_text = self.filter_input.text().lower()
        filtered_devices = {
            device_id: device 
            for device_id, device in self.devices.items()
            if filter_text in device_id.lower()
        }
        
        self.table.setRowCount(len(filtered_devices))
        
        for row, (device_id, device) in enumerate(sorted(filtered_devices.items())):
            # Device ID
            id_item = QTableWidgetItem(device_id)
            id_item.setData(Qt.UserRole, device_id)
            self.table.setItem(row, 0, id_item)
            
            # Status (Connected/Disconnected)
            status_item = QTableWidgetItem("Connected" if device.connected else "Disconnected")
            status_item.setTextAlignment(Qt.AlignCenter)
            if device.connected:
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                status_item.setBackground(QColor(255, 200, 200))  # Light red
                status_item.setForeground(QColor(150, 0, 0))  # Dark red text
            self.table.setItem(row, 1, status_item)
            
            # Battery level with color coding
            battery_item = QTableWidgetItem(f"{device.battery_level}%")
            battery_item.setTextAlignment(Qt.AlignCenter)
            if device.battery_level < 20:
                battery_item.setBackground(QColor(255, 200, 200))  # Light red
            elif device.battery_level < 50:
                battery_item.setBackground(QColor(255, 235, 200))  # Light orange
            else:
                battery_item.setBackground(QColor(200, 255, 200))  # Light green
            self.table.setItem(row, 2, battery_item)
            
            # Empty level
            empty_item = QTableWidgetItem(f"{device.empty_level}%")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, empty_item)
            
            # Location
            if device.location:
                lat, lng = device.location
                self.table.setItem(row, 4, QTableWidgetItem(f"{lat:.4f}"))
                self.table.setItem(row, 5, QTableWidgetItem(f"{lng:.4f}"))
            else:
                self.table.setItem(row, 4, QTableWidgetItem("N/A"))
                self.table.setItem(row, 5, QTableWidgetItem("N/A"))
        
        # Update count label
        self.count_label.setText(f"Devices: {len(self.devices)} (showing {len(filtered_devices)})")
    
    def _filter_devices(self, text: str):
        """Filter devices based on search text"""
        self._update_table()
    
    def _on_selection_changed(self):
        """Handle device selection in table"""
        selected_items = self.table.selectedItems()
        if selected_items:
            device_id = selected_items[0].data(Qt.UserRole)
            if device_id:
                self.device_selected.emit(device_id)
    
    def get_device_count(self) -> int:
        """Get the number of devices"""
        return len(self.devices)

