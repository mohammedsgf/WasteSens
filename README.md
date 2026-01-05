# Smart Waste IoT Dashboard

A real-time IoT device monitoring dashboard built with Python and Qt that fetches data from an MQTT broker and displays devices on a geographic map.

## Features

- **Real-time Device Tracking**: Monitor multiple IoT devices in real-time
- **Geographic Map Visualization**: View device locations on an interactive OpenStreetMap
- **Device Information Panel**: See battery levels, empty levels, and locations in a table
- **MQTT Integration**: Automatically connects to MQTT broker and subscribes to device topics
- **Color-coded Markers**: Visual indicators for device battery levels (green/orange/red)
- **Device Filtering**: Search and filter devices by ID
- **Auto-discovery**: Automatically discovers and adds new devices as they publish data

## Requirements

- Python 3.7 or higher
- MQTT broker (e.g., Mosquitto)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure MQTT settings in `config.py` (or use environment variables):
   - `MQTT_BROKER_HOST`: MQTT broker hostname (default: localhost)
   - `MQTT_BROKER_PORT`: MQTT broker port (default: 1883)
   - `MQTT_TOPIC_PATTERN`: Topic pattern to subscribe to (default: `smartwaste/+/data`)

## Usage

Run the dashboard:
```bash
python main.py
```

The dashboard will automatically connect to the MQTT broker and start receiving device data.

## MQTT Message Format

The dashboard expects messages in the following JSON format:

```json
{
  "device_id": "device001",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "battery_level": 85,
  "empty_level": 30
}
```

Messages should be published to topics matching the pattern `smartwaste/+/data` (or your configured pattern), where `+` is a wildcard for the device ID.

## Project Structure

```
smartWasteUI/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── mqtt_client.py         # MQTT client wrapper
├── device_manager.py      # Device state management
├── models/
│   └── device.py          # Device data model
└── ui/
    ├── main_window.py     # Main Qt window
    ├── map_widget.py      # Map visualization widget
    └── device_panel.py    # Device information panel
```

## Testing

To test the dashboard, you can use a local MQTT broker like Mosquitto:

1. Install Mosquitto:
   - Windows: Download from https://mosquitto.org/download/
   - Linux: `sudo apt-get install mosquitto mosquitto-clients`
   - macOS: `brew install mosquitto`

2. Start the broker:
   ```bash
   mosquitto -p 1883
   ```

3. Publish test messages:
   ```bash
   mosquitto_pub -h localhost -t "smartwaste/device001/data" -m '{"device_id":"device001","location":{"latitude":40.7128,"longitude":-74.0060},"battery_level":85,"empty_level":30}'
   ```

## Configuration

You can configure the dashboard using environment variables or by editing `config.py`:

- `MQTT_BROKER_HOST`: MQTT broker hostname
- `MQTT_BROKER_PORT`: MQTT broker port
- `MQTT_TOPIC_PATTERN`: Topic subscription pattern
- `MQTT_USERNAME`: MQTT username (optional)
- `MQTT_PASSWORD`: MQTT password (optional)

## License

This project is provided as-is for demonstration purposes.

