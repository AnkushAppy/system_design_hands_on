#!/bin/bash
# Quick script to inspect Kafka log and index files inside the container

echo "=== Kafka Log and Index Files ==="
echo ""
echo "1. Listing files in the Kafka log directory inside container:"
docker exec kafka ls -la /tmp/kraft-combined-logs/ 2>/dev/null || echo "   (Directory listing failed)"

echo ""
echo "2. Finding .log and .index files:"
docker exec kafka find /tmp/kraft-combined-logs -name "*.log" -o -name "*.index" 2>/dev/null

echo ""
echo "3. If files exist, showing first 20 lines of the main log as text:"
docker exec kafka strings /tmp/kraft-combined-logs/00000000000000000000.log 2>/dev/null | head -20 || echo "   (No log file found yet)"

echo ""
echo "4. Hexdump of first 256 bytes showing the .log file structure:"
docker exec kafka hexdump -C /tmp/kraft-combined-logs/00000000000000000000.log 2>/dev/null | head -16 || echo "   (No log file found yet)"

echo ""
echo "5. Checking .index file contents:"
docker exec kafka hexdump -C /tmp/kraft-combined-logs/00000000000000000000.index 2>/dev/null | head -10 || echo "   (No index file found yet)"

echo ""
echo "=== Done ==="
echo ""
echo "Key insight: The .log files store your messages in plain text."
echo "The .index files map offset numbers to byte positions for instant seeking."

