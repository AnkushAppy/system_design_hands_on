# Simple Producer
def produce(topic_name, message):
    with open(f"{topic_name}.log", "a") as f:
        f.write(message + "\n")

produce("orders", "order_id_1:apple")
produce("orders", "order_id_2:banana")