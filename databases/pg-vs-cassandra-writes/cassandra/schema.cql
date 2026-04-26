-- LSM / SSTable-backed storage (see README). RF=1 is fine for local Docker.
CREATE KEYSPACE IF NOT EXISTS lab
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS lab.events (
    bucket text,
    id timeuuid,
    payload text,
    PRIMARY KEY (bucket, id)
) WITH compaction = {'class': 'SizeTieredCompactionStrategy'};
