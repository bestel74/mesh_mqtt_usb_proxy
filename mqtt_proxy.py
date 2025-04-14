import os
import time
import sys
from meshtastic.serial_interface import SerialInterface
from meshtastic.protobuf import admin_pb2, mqtt_pb2, portnums_pb2
from pubsub import pub
import paho.mqtt.client as mqtt_client

MQTT_PORT = 1883
DEV_PATH = "COM16"

iface = None

def onReceive(proxymessage, interface):
    print(f'{proxymessage}', flush=True)
    it = mqtt.publish(proxymessage.topic, proxymessage.data)
    print(f'{it}', flush=True)
    it.wait_for_publish()

def on_connect(mqttc, obj, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!", flush=True)
    else:
        print("Failed to connect, return code %d\n", rc, flush=True)
        
def on_reconnect():
    mqtt_client.connect(mqtt_cfg.address, MQTT_PORT, 10)
        
def on_disconnect(mqttc, obj, flags, reason_code, properties):
    mqtt_reconnect()


def get_mqtt_config(dev_path=DEV_PATH):
    global iface
    iface = SerialInterface(devPath=dev_path)

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

    global mqtt
    mqtt = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    mqtt.client_id = iface.getLongName() + "_mqttproxyv1"
    mqtt.on_connect = on_connect
    mqtt.on_disconnect = on_disconnect
    mqtt.username = mqtt_cfg.username
    mqtt.password = mqtt_cfg.password
    mqtt.connect(mqtt_cfg.address, MQTT_PORT, 10)
    mqtt.loop_start()
    
    pub.subscribe(onReceive, 'meshtastic.mqttclientproxymessage')


if __name__ == "__main__":
    get_mqtt_config()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Interruption reçue, fermeture propre...", flush=True)
        if iface:
            iface.close()
        if mqtt:
            mqtt.loop_stop()
