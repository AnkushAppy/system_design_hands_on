import os
import time
import hashlib
import threading

# Configuration
NUM_PARTITIONS = 2

def get_partition(message_key, num_partitions):
    """Hash the key to determine which partition to use."""
    hash_value = int(hashlib.md5(message_key.encode()).hexdigest(), 16)
    return hash_value % num_partitions

def produce(topic_name, message_key, message_value):
    """Produce a message to a specific partition based on key hashing."""
    partition = get_partition(message_key, NUM_PARTITIONS)
    topic_dir = f"{topic_name}_topic"
    os.makedirs(topic_dir, exist_ok=True)
    partition_file = os.path.join(topic_dir, f"partition_{partition}.log")
    
    with open(partition_file, "a") as f:
        f.write(f"{message_key}:{message_value}\n")
    
    print(f"Producer: '{message_key}:{message_value}' -> partition_{partition}.log")

def consume_partition(topic_name, partition_id, start_offset):
    """Consume messages from a specific partition."""
    current_offset = start_offset
    topic_dir = f"{topic_name}_topic"
    partition_file = os.path.join(topic_dir, f"partition_{partition_id}.log")
    
    while True:
        if os.path.exists(partition_file):
            with open(partition_file, "r") as f:
                lines = f.readlines()
                if len(lines) > current_offset:
                    print(f"Consumer-{partition_id}: New Message: {lines[current_offset].strip()} (Offset: {current_offset})")
                    current_offset += 1
                else:
                    print(f"Consumer-{partition_id}: Waiting for data...")
                    time.sleep(2)
        else:
            print(f"Consumer-{partition_id}: Partition file not found, waiting...")
            time.sleep(2)

if __name__ == "__main__":
    # Create topic directory
    os.makedirs("orders_topic", exist_ok=True)
    
    # Clear any existing partition files for clean demo
    for i in range(NUM_PARTITIONS):
        pf = os.path.join("orders_topic", f"partition_{i}.log")
        if os.path.exists(pf):
            open(pf, "w").close()
    
    # Start consumers for each partition in separate threads
    consumer_threads = []
    for i in range(NUM_PARTITIONS):
        t = threading.Thread(target=consume_partition, args=("orders", i, 0), daemon=True)
        t.start()
        consumer_threads.append(t)
    
    time.sleep(1)
    
    # Produce messages with different keys - same key goes to same partition
    messages = [
        ("user_1", "order_1:apple"),
        ("user_2", "order_2:banana"),
        ("user_1", "order_3:cherry"),  # Same key as first, goes to same partition
        ("user_3", "order_4:date"),
        ("user_2", "order_5:elderberry"),  # Same key as second, goes to same partition
    ]
    
    for key, value in messages:
        produce("orders", key, value)
        time.sleep(2)
    
    # Let consumers finish processing
    time.sleep(6)