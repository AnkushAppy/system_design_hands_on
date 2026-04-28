#!/usr/bin/env python3
"""
Kafka Reliability Experiment - Acks and Durability

Demonstrates how different ack settings affect message durability.
Run this with 3 Kafka brokers to see replication in action.

Usage:
  python producer_experiment.py [acks_value] [num_messages]

Examples:
  python producer_experiment.py all 50    # Strongest durability
  python producer_experiment.py 1 50      # Medium durability
  python producer_experiment.py 0 50      # Fire and forget (least durable)
"""

import sys
import time
import random

from kafka import KafkaProducer
from kafka.errors import KafkaError

def create_producer(acks_setting):
    """Create a Kafka producer with the specified acks setting."""
    
    # Map string inputs to Kafka's expected values
    acks_map = {
        '0': 0,
        '1': 1,
        'all': -1,  # Kafka uses -1 for all replicas
        '-1': -1,
    }
    
    acks_value = acks_map.get(str(acks_setting).lower(), -1)
    
    print(f"\n{'='*60}")
    print(f"Creating producer with acks={acks_setting}")
    print(f"  (Kafka internal value: {acks_value})")
    print(f"{'='*60}\n")
    
    if acks_value == 0:
        print("  WARNING: acks=0 means FIRE AND FORGET")
        print("  Messages may be lost if broker crashes!\n")
    elif acks_value == 1:
        print("  WARNING: acks=1 only waits for leader")
        print("  Messages may be lost if leader crashes before replication!\n")
    elif acks_value == -1:
        print("  OK: acks=all waits for all in-sync replicas")
        print("  Zero data loss guarantee (with min.insync.replicas=2)\n")
    
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092', 'localhost:9093', 'localhost:9094'],
        acks=acks_value,
        retries=3,
        max_in_flight_requests_per_connection=1,
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        value_serializer=lambda v: v.encode('utf-8') if v else None,
        # Important for acks=all: don't timeout waiting for replicas
        request_timeout_ms=30000,
    )
    
    return producer

def produce_messages(acks_setting, num_messages=50, delay_between=0.1):
    """Produce messages and track what happens."""
    
    producer = create_producer(acks_setting)
    topic = "orders"
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    print(f"Producing {num_messages} messages to topic '{topic}'...\n")
    print(f"{'─'*60}")
    
    for i in range(1, num_messages + 1):
        key = f"user_{random.randint(1, 10)}"
        value = f"order_{i}:item_{random.choice(['apple','banana','cherry','date','elderberry'])}"
        
        try:
            future = producer.send(topic, key=key, value=value)
            # Wait for the send to complete (this is where acks matter)
            result = future.get(timeout=10)
            successful += 1
            
            status = "✓"
            if i % 10 == 0 or i == 1:
                print(f"{status} Msg {i:3d}: '{key}:{value}' -> partition={result.partition}, offset={result.offset}")
            elif i % 5 == 0:
                print(f"{status} Msg {i:3d}: '{key}:{value}'")
            
        except KafkaError as e:
            failed += 1
            print(f"✗ Msg {i:3d}: FAILED - {e}")
        except Exception as e:
            failed += 1
            print(f"✗ Msg {i:3d}: ERROR - {e}")
        
        time.sleep(delay_between)
    
    elapsed = time.time() - start_time
    
    # Ensure all messages are sent
    producer.flush()
    producer.close()
    
    print(f"{'─'*60}")
    print(f"\nResults:")
    print(f"  Total messages:  {num_messages}")
    print(f"  Successful:      {successful} ({successful/num_messages*100:.1f}%)")
    print(f"  Failed:          {failed} ({failed/num_messages*100:.1f}%)")
    print(f"  Time elapsed:    {elapsed:.2f}s")
    print(f"  Throughput:      {num_messages/elapsed:.2f} msg/s")
    print()
    print(f"Verify (fresh topic recommended): python consumer_verify.py {successful}")
    print()
    
    return successful, failed

def run_comparison():
    """Run the same workload with different acks settings to compare."""
    
    print("\n" + "="*60)
    print("RELIABILITY COMPARISON EXPERIMENT")
    print("="*60)
    print("\nThis will send messages with different acks settings.")
    print("Watch what happens when you kill a broker mid-stream!\n")
    
    input("Press Enter to start with acks=0 (fire and forget)...")
    produce_messages(0, num_messages=20, delay_between=0.2)
    
    input("\nPress Enter to continue with acks=1 (leader only)...")
    produce_messages(1, num_messages=20, delay_between=0.2)
    
    input("\nPress Enter to finish with acks=all (all replicas)...")
    produce_messages('all', num_messages=20, delay_between=0.2)
    
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)
    print("\nKey Insight:")
    print("  With acks=all and min.insync.replicas=2, Kafka can lose")
    print("  1 broker and still NOT lose any messages!")
    print("\nTry this:")
    print("  1. Start the cluster: docker compose up -d")
    print("  2. Run: python producer_experiment.py all 100")
    print("  3. While running, kill a broker:")
    print("     docker kill broker-2")
    print("  4. Watch the producer keep working!")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        run_comparison()
    else:
        acks = sys.argv[1] if len(sys.argv) > 1 else 'all'
        num = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        produce_messages(acks, num_messages=num)
