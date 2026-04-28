# Simple Consumer
import time

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

consume("orders", 0)