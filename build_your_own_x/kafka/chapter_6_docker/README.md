# Chapter 6: Kafka with Docker Compose - "For Real"

This chapter shows the real Kafka running in Docker, producing actual messages and inspecting the `.log` and `.index` files on disk.

## Quick Start

```bash
# 1. Start Kafka
docker compose up -d

# Wait ~15 seconds for Kafka to be ready, then:

# 2. Produce messages
python produce_messages.py

# 3. Inspect the files on disk
./inspect_files.sh

# 4. Or manually explore inside the container:
docker exec -it kafka bash
cd /tmp/kraft-combined-logs
ls -la
strings 00000000000000000000.log
```

## What You'll See


total 36
drwxr-xr-x 4 appuser appuser 4096 Apr 26 16:42 .
drwxrwxrwt 1 root    root    4096 Apr 26 16:36 ..
-rw-r--r-- 1 appuser appuser    0 Apr 26 16:36 .lock
drwxr-xr-x 2 appuser appuser 4096 Apr 26 16:36 __cluster_metadata-0
-rw-r--r-- 1 appuser appuser  249 Apr 26 16:36 bootstrap.checkpoint
-rw-r--r-- 1 appuser appuser    0 Apr 26 16:36 cleaner-offset-checkpoint
-rw-r--r-- 1 appuser appuser    4 Apr 26 16:41 log-start-offset-checkpoint
-rw-r--r-- 1 appuser appuser   86 Apr 26 16:36 meta.properties
drwxr-xr-x 2 appuser appuser 4096 Apr 26 16:40 orders-0
-rw-r--r-- 1 appuser appuser   15 Apr 26 16:41 recovery-point-offset-checkpoint
-rw-r--r-- 1 appuser appuser   15 Apr 26 16:42 replication-offset-checkpoint

/tmp/kraft-combined-logs/__cluster_metadata-0:
total 84
drwxr-xr-x 2 appuser appuser     4096 Apr 26 16:36 .
drwxr-xr-x 4 appuser appuser     4096 Apr 26 16:42 ..
-rw-r--r-- 1 appuser appuser 10485760 Apr 26 16:42 00000000000000000000.index
-rw-r--r-- 1 appuser appuser    50087 Apr 26 16:42 00000000000000000000.log
-rw-r--r-- 1 appuser appuser 10485756 Apr 26 16:42 00000000000000000000.timeindex
-rw-r--r-- 1 appuser appuser        8 Apr 26 16:36 leader-epoch-checkpoint
-rw-r--r-- 1 appuser appuser       43 Apr 26 16:36 partition.metadata
-rw-r--r-- 1 appuser appuser      125 Apr 26 16:36 quorum-state

/tmp/kraft-combined-logs/orders-0:
total 20
drwxr-xr-x 2 appuser appuser     4096 Apr 26 16:40 .
drwxr-xr-x 4 appuser appuser     4096 Apr 26 16:42 ..
-rw-r--r-- 1 appuser appuser 10485760 Apr 26 16:40 00000000000000000000.index
-rw-r--r-- 1 appuser appuser      451 Apr 26 16:40 00000000000000000000.log
-rw-r--r-- 1 appuser appuser 10485756 Apr 26 16:40 00000000000000000000.timeindex
-rw-r--r-- 1 appuser appuser        8 Apr 26 16:40 leader-epoch-checkpoint
-rw-r--r-- 1 appuser appuser       43 Apr 26 16:40 partition.metadata

- **`00000000000000000000.log`**: The actual log file with your messages stored as text mixed with binary headers
- **`00000000000000000000.index`**: The index file mapping offsets → byte positions (16 bytes per entry)

## The "Aha!" Moment

Running `strings 00000000000000000000.log` reveals your messages in plain text. Kafka is just a very high-performance way of managing a folder full of text files.

cat 00000000000000000000.log
M�_@�ʩ�,�ʩ�,��������������6
                           user_1order_101:appleNr�y3�ʩ�B�ʩ�B��������������8
                                                                            user_2 order_102:bananaN��{�ʩ�D�ʩ�D��������������8
                 user_1 order_103:cherryL�����ʩ�G�ʩ�G��������������4
                                                                    user_3order_104:dateRY��ʩ�K�ʩ�K��������������@
[appuser@cb55d344b546 orders-0]$ 

## Files

- `docker-compose.yml` - Kafka KRaft configuration (no ZooKeeper)
- `produce_messages.py` - Python producer using `kafka-python`
- `inspect_files.sh` - Inspect the `.log` and `.index` files inside the container
- `README.md` - This file

## Cleanup

```bash
docker compose down
```

