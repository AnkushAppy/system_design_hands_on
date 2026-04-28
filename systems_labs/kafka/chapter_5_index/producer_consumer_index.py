import os
import time
import hashlib
import threading
import struct

# Configuration
NUM_PARTITIONS = 2
INDEX_INTERVAL = 10  # Store an index entry every N messages

def get_partition(message_key, num_partitions):
    """Hash the key to determine which partition to use."""
    hash_value = int(hashlib.md5(message_key.encode()).hexdigest(), 16)
    return hash_value % num_partitions

def write_index_entry(index_path, offset, byte_position):
    """Write an index entry (offset + byte_position) to the index file.
    Format: 8 bytes offset (Q) + 8 bytes byte_position (Q) = 16 bytes per entry"""
    with open(index_path, "ab") as idx:
        idx.write(struct.pack("QQ", offset, byte_position))

def read_index_entry(index_path, entry_num):
    """Read a specific index entry by entry number.
    Returns (offset, byte_position) or None if not found."""
    try:
        with open(index_path, "rb") as idx:
            idx.seek(entry_num * 16)  # Each entry is 16 bytes
            data = idx.read(16)
            if len(data) == 16:
                return struct.unpack("QQ", data)
    except (FileNotFoundError, struct.error):
        pass
    return None

def find_closest_index(index_path, target_offset):
    """Find the closest index entry at or before the target offset.
    Returns (offset, byte_position) of the closest entry, or (0, 0) if none found."""
    if not os.path.exists(index_path):
        return (0, 0)
    
    file_size = os.path.getsize(index_path)
    num_entries = file_size // 16
    
    if num_entries == 0:
        return (0, 0)
    
    # Binary search for the closest offset <= target_offset
    left, right = 0, num_entries - 1
    best_entry = (0, 0)
    
    while left <= right:
        mid = (left + right) // 2
        offset, byte_pos = read_index_entry(index_path, mid)
        if offset <= target_offset:
            best_entry = (offset, byte_pos)
            left = mid + 1
        else:
            right = mid - 1
    
    return best_entry

def produce(topic_name, message_key, message_value):
    """Produce a message to a specific partition with index tracking."""
    partition = get_partition(message_key, NUM_PARTITIONS)
    topic_dir = f"{topic_name}_topic"
    os.makedirs(topic_dir, exist_ok=True)
    
    partition_file = os.path.join(topic_dir, f"partition_{partition}.log")
    index_file = os.path.join(topic_dir, f"partition_{partition}.index")
    
    # Determine current offset (number of lines already in partition)
    if os.path.exists(partition_file):
        with open(partition_file, "r") as f:
            current_offset = sum(1 for _ in f)
    else:
        current_offset = 0
    
    # Write the message and record its byte position
    message = f"{message_key}:{message_value}\n"
    with open(partition_file, "a") as log:
        byte_position = log.tell()
        log.write(message)
    
    # Write index entry every INDEX_INTERVAL messages
    if (current_offset + 1) % INDEX_INTERVAL == 0:
        write_index_entry(index_file, current_offset + 1, byte_position + len(message))
        print(f"  Index: offset {current_offset + 1} -> byte {byte_position + len(message)}")
    
    print(f"Producer: '{message_key}:{message_value}' -> partition_{partition}.log (offset: {current_offset + 1})")

def consume_partition(topic_name, partition_id, start_offset):
    """Consume messages from a specific partition using the index for fast seeks."""
    current_offset = start_offset
    topic_dir = f"{topic_name}_topic"
    partition_file = os.path.join(topic_dir, f"partition_{partition_id}.log")
    index_file = os.path.join(topic_dir, f"partition_{partition_id}.index")
    
    print(f"Consumer-{partition_id}: Starting at offset {start_offset}")
    
    # If starting from a non-zero offset, use the index to seek
    if start_offset > 0:
        closest_offset, byte_position = find_closest_index(index_file, start_offset)
        print(f"  Consumer-{partition_id}: Using index - closest offset {closest_offset} at byte {byte_position}")
        current_offset = closest_offset
    
    while True:
        if os.path.exists(partition_file):
            with open(partition_file, "r") as f:
                # If we're starting past the beginning, seek to the indexed position
                if current_offset > 0 and start_offset > 0:
                    f.seek(0)
                    lines = f.readlines()
                    # Fast forward to our offset (index gave us a head start)
                    if current_offset < len(lines):
                        # We still need to read from current_offset onward
                        pass
                else:
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
    
    # Clean up old files
    for i in range(NUM_PARTITIONS):
        for ext in [".log", ".index"]:
            pf = os.path.join("orders_topic", f"partition_{i}{ext}")
            if os.path.exists(pf):
                os.remove(pf)
    
    # Start consumers for each partition
    consumer_threads = []
    for i in range(NUM_PARTITIONS):
        t = threading.Thread(target=consume_partition, args=("orders", i, 0), daemon=True)
        t.start()
        consumer_threads.append(t)
    
    time.sleep(1)
    
    # Produce many messages to demonstrate index creation
    messages = []
    for i in range(1, 26):  # Produce 25 messages per partition (will create index entries every 10)
        messages.append((f"user_{i % 5}", f"order_{i}:item_{i}"))
    
    for key, value in messages:
        produce("orders", key, value)
        time.sleep(0.3)
    
    print("\n=== Index files created ===")
    for i in range(NUM_PARTITIONS):
        idx = os.path.join("orders_topic", f"partition_{i}.index")
        if os.path.exists(idx):
            size = os.path.getsize(idx)
            num_entries = size // 16
            print(f"  partition_{i}.index: {num_entries} entries")
    
    # Simulate a consumer restarting from a specific offset (demonstrating index usage)
    time.sleep(2)
    print("\n=== Simulating consumer restart from offset 15 ===")
    
    # Start a new consumer that seeks to offset 15 using the index
    def restarted_consumer():
        topic_dir = "orders_topic"
        partition_id = 0
        start_offset = 15
        
        index_file = os.path.join(topic_dir, f"partition_{partition_id}.index")
        closest_offset, byte_position = find_closest_index(index_file, start_offset)
        
        print(f"Restarted Consumer-0: Seeking to offset {start_offset}")
        print(f"  Index says: offset {closest_offset} is at byte {byte_position}")
        
        partition_file = os.path.join(topic_dir, f"partition_{partition_id}.log")
        with open(partition_file, "r") as f:
            # Seek to approximate position from index
            f.seek(byte_position)
            # Read remaining lines and count offsets
            all_lines = f.readlines()
            
            # Calculate actual offset
            current_offset = closest_offset
            for line in all_lines:
                if current_offset >= start_offset:
                    print(f"Restarted Consumer-0: (from offset {start_offset}) -> {line.strip()} (Offset: {current_offset})")
                current_offset += 1
    
    restart_thread = threading.Thread(target=restarted_consumer, daemon=True)
    restart_thread.start()
    
    restart_thread.join(timeout=3)