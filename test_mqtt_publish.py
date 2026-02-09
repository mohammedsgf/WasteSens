"""
Test script to publish sample MQTT messages to test the dashboard.
Publishes 10 devices with different locations in Jeddah City, Saudi Arabia.

Topic format: smartwaste/{user_id}/{device_id}/data
NOTE: The user_id must correspond to an existing user in the database.
      Sign up via the web UI first, then use that user's ID here.
"""
import json
import time
import paho.mqtt.client as mqtt
from app.config import settings

# Default user ID for testing -- change to match your signed-up user's ID
DEFAULT_USER_ID = 1


def publish_test_message(client, user_id: int, device_id: str, lat: float, lon: float, battery: int, fill: int):
    """Publish a test message to the MQTT broker"""
    try:
        topic = f"smartwaste/{user_id}/{device_id}/data"
        payload = {
            "device_id": device_id,
            "location": {
                "latitude": lat,
                "longitude": lon
            },
            "battery_level": battery,
            "fill_level": fill
        }

        message = json.dumps(payload)
        print(f"Publishing device: {device_id} | Battery: {battery}% | Fill: {fill}% | Location: ({lat:.4f}, {lon:.4f})")
        print(f"  Topic: {topic}")

        result = client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"  -> Published successfully!")
        else:
            print(f"  -> Failed to publish, error code: {result.rc}")

        return result.rc == mqtt.MQTT_ERR_SUCCESS

    except Exception as e:
        print(f"  -> Error: {e}")
        return False


if __name__ == "__main__":
    user_id = DEFAULT_USER_ID

    print("=" * 70)
    print("MQTT Test Publisher - 10 Devices in Jeddah City, Saudi Arabia")
    print(f"User ID: {user_id}")
    print("=" * 70)
    print()
    print("NOTE: Make sure a user with this ID exists in the database.")
    print("      Sign up via the web UI, then check the database for the user ID.")
    print()

    # Jeddah City center coordinates: 21.4858 N, 39.1925 E
    # Define 10 devices with different locations, battery levels, and fill levels
    devices = [
        # Device ID, Latitude, Longitude, Battery %, Fill %
        ("device001", 21.4858, 39.1925, 95, 15),   # City Center - High battery, low fill
        ("device002", 21.5100, 39.1800, 45, 75),   # North Jeddah - Medium battery, high fill
        ("device003", 21.4600, 39.2100, 25, 90),   # South Jeddah - Low battery, very high fill
        ("device004", 21.4950, 39.1750, 80, 30),   # West Jeddah - Good battery, medium fill
        ("device005", 21.4700, 39.2000, 60, 50),   # Central-East - Medium battery, medium fill
        ("device006", 21.5200, 39.1950, 15, 85),   # North-East - Very low battery, high fill
        ("device007", 21.4500, 39.1850, 70, 40),   # South-West - Good battery, medium fill
        ("device008", 21.5000, 39.2050, 90, 20),   # North-West - High battery, low fill
        ("device009", 21.4750, 39.1900, 35, 65),   # Central - Low battery, medium-high fill
        ("device010", 21.4900, 39.1980, 55, 55),   # Central-South - Medium battery, medium fill
    ]

    try:
        print(f"Connecting to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}...")
        client = mqtt.Client(client_id="test_publisher_jeddah")
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
        print("Connected to MQTT broker\n")

        print("Publishing devices:")
        print("-" * 70)
        success_count = 0

        for device_id, lat, lon, battery, fill in devices:
            if publish_test_message(client, user_id, device_id, lat, lon, battery, fill):
                success_count += 1
            time.sleep(0.5)  # Small delay between messages

        client.disconnect()

        print("-" * 70)
        print(f"\nPublished {success_count}/{len(devices)} devices successfully!")
        print(f"\nAll devices published under user_id={user_id}")
        print("Topic pattern: smartwaste/{user_id}/{device_id}/data")
        print("\nMake sure the dashboard is running and connected to the MQTT broker.")
        print("=" * 70)

    except Exception as e:
        print(f"\nConnection error: {e}")
        print("Make sure the MQTT broker is running and accessible.")
