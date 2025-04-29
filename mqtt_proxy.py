import os
import time
import sys
from meshtastic.serial_interface import SerialInterface
from meshtastic.protobuf import admin_pb2, mqtt_pb2, portnums_pb2
from pubsub import pub
import paho.mqtt.client as mqtt_client

MQTT_PORT = 1883
DEV_PATH = "/dev/ttyACM0"

iface = None
mqtt = None
mqtt_cfg = None


def onReceive(proxymessage, interface):
    global mqtt

    print(f'{proxymessage}', flush=True)

    if not mqtt.is_connected():
        print("MQTT disconnected, trying to reconnect...", flush=True)
        try:
            mqtt_connect()
            print("Reconnected!", flush=True)
        except Exception as e:
            print(f"Reconnect failed: {e}", flush=True)
            return

    it = mqtt.publish(proxymessage.topic, proxymessage.data)
    print(f'{it}', flush=True)
    it.wait_for_publish()

def on_connect(mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!", flush=True)
    else:
        print("Failed to connect, return code %d\n", rc, flush=True)

def mqtt_connect():
    global mqtt, mqtt_cfg

    mqtt = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    mqtt.client_id = iface.getLongName() + "_mqttproxyv2"
    mqtt.on_connect = on_connect
    mqtt.on_disconnect = on_disconnect
    mqtt.username = mqtt_cfg.username
    mqtt.password = mqtt_cfg.password
    mqtt.connect(mqtt_cfg.address, MQTT_PORT, 10)
    mqtt.loop_start()

def on_disconnect(mqttc, obj, flags, reason_code, properties):
    mqtt_connect()


def get_mqtt_config(dp=DEV_PATH):
    global iface, mqtt_cfg

    iface = SerialInterface(devPath=dp)
    node = iface.localNode

    if not node.waitForConfig("moduleConfig"):
        print("Timeout en attendant la config MQTT")
        iface.close()
        return

    mqtt_cfg = node.moduleConfig.mqtt
    print("MQTT Config:", flush=True)
    print(f"  Enabled: {mqtt_cfg.enabled}")
    print(f"  Server: {mqtt_cfg.address}")
    print(f"  User: {mqtt_cfg.username}")
    print(f"  Password: {mqtt_cfg.password}")
    print(f"  Root: {mqtt_cfg.root}")
    print(f"  TLS Enabled: {mqtt_cfg.tls_enabled}", flush=True)


if __name__ == "__main__":
    get_mqtt_config()
    mqtt_connect()

    pub.subscribe(onReceive, 'meshtastic.mqttclientproxymessage')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Interruption reçue, fermeture propre...", flush=True)
        if iface:
            iface.close()
        if mqtt:
            mqtt.loop_stop()
