# from parseAoAstr_0525 import mqtt_run
from src.data_optimization import *  
import yaml
from src.mqtt.subscriber import MQTTSubscriber

with open('config.yaml') as f:
    config = yaml.safe_load(f)

def main():
    # print("? Initializing MQTT Client with config:", config['mqtt'])
    try:
        subscriber = MQTTSubscriber(config=config['mqtt'])
        print("MQTTSubscriber initialized successfully")
        subscriber.subscribe()
        # subscriber.check_for_messages() 
        subscriber.run()
    except Exception as e:
        print(f"? MQTT initialization failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()

    