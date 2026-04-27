# Simple Producer
import time

def produce(topic_name, message):
    with open(f"{topic_name}.log", "a") as f:
        f.write(message + "\n")

# Simple Consumer
def consume(topic_name, start_offset):
    current_offset = start_offset
    while True:
        with open(f"{topic_name}.log", "r") as f:
            lines = f.readlines()
            if len(lines) > current_offset:
                print(f"New Message: {lines[current_offset].strip()} (Offset: {current_offset})")
                current_offset += 1
            else:
                print("Waiting for data...")
                time.sleep(2)

# Demonstration: Producer and Consumer working together
if __name__ == "__main__":
    import threading

    # Start consumer in a separate thread
    consumer_thread = threading.Thread(target=consume, args=("orders", 0), daemon=True)
    consumer_thread.start()

    # Give consumer time to start
    time.sleep(1)

    # Producer produces messages
    print("Producer: Sending order_id_1:apple")
    produce("orders", "order_id_1:apple")

    time.sleep(3)

    print("Producer: Sending order_id_2:banana")
    produce("orders", "order_id_2:banana")

    time.sleep(3)

    print("Producer: Sending order_id_3:cherry")
    produce("orders", "order_id_3:cherry")

    # Let consumer process all messages
    time.sleep(5)