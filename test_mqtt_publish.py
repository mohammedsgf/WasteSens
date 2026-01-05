"""
Test script to publish sample MQTT messages to test the dashboard
Publishes 10 devices with different locations in Jeddah City, Saudi Arabia
"""
import json
import time
import paho.mqtt.client as mqtt
import config

def publish_test_message(client, device_id: str, lat: float, lon: float, battery: int, empty: int):
    """Publish a test message to the MQTT broker"""
    try:
        topic = f"smartwaste/{device_id}/data"
        payload = {
            "device_id": device_id,
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "battery_level": battery,
            "empty_level": empty
        }
        
        message = json.dumps(payload)
        print(f"Publishing device: {device_id} | Battery: {battery}% | Empty: {empty}% | Location: ({lat:.4f}, {lon:.4f})")
        
        result = client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"  ✓ Published successfully!")
        else:
            print(f"  ✗ Failed to publish, error code: {result.rc}")
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("MQTT Test Publisher - 10 Devices in Jeddah City, Saudi Arabia")
    print("=" * 70)
    
    # Jeddah City center coordinates: 21.4858°N, 39.1925°E
    # Define 10 devices with different locations, battery levels, and empty levels
    devices = [
        # Device ID, Latitude, Longitude, Battery %, Empty %
        ("device001", 21.4858, 39.1925, 95, 15),   # City Center - High battery, low empty
        ("device002", 21.5100, 39.1800, 45, 75),   # North Jeddah - Medium battery, high empty
        ("device003", 21.4600, 39.2100, 25, 90),   # South Jeddah - Low battery, very high empty
        ("device004", 21.4950, 39.1750, 80, 30),   # West Jeddah - Good battery, medium empty
        ("device005", 21.4700, 39.2000, 60, 50),   # Central-East - Medium battery, medium empty
        ("device006", 21.5200, 39.1950, 15, 85),   # North-East - Very low battery, high empty
        ("device007", 21.4500, 39.1850, 70, 40),   # South-West - Good battery, medium empty
        ("device008", 21.5000, 39.2050, 90, 20),   # North-West - High battery, low empty
        ("device009", 21.4750, 39.1900, 35, 65),   # Central - Low battery, medium-high empty
        ("device010", 21.4900, 39.1980, 55, 55),   # Central-South - Medium battery, medium empty
    ]
    
    try:
        print(f"\nConnecting to {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}...")
        client = mqtt.Client(client_id="test_publisher_jeddah")
        client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, 60)
        print("✓ Connected to MQTT broker\n")
        
        print("Publishing devices:")
        print("-" * 70)
        success_count = 0
        
        for device_id, lat, lon, battery, empty in devices:
            if publish_test_message(client, device_id, lat, lon, battery, empty):
                success_count += 1
            time.sleep(0.5)  # Small delay between messages
        
        client.disconnect()
        
        print("-" * 70)
        print(f"\n✓ Published {success_count}/{len(devices)} devices successfully!")
        print("\nAll devices are located in Jeddah City, Saudi Arabia")
        print("Make sure the dashboard is running and connected to the MQTT broker.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Connection error: {e}")
        print("Make sure the MQTT broker is running and accessible.")

