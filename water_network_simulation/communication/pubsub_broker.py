from collections import defaultdict
import threading

class PubSubBroker:
    """
    一个简单的线程安全的发布/订阅消息代理。
    用于在各个智能体之间解耦通信。
    """
    def __init__(self):
        self.topics = defaultdict(list)
        self.lock = threading.Lock()
        print("PubSubBroker: Initialized.")

    def subscribe(self, topic: str, callback):
        """订阅一个主题。当有消息发布到该主题时，将调用回调函数。"""
        with self.lock:
            self.topics[topic].append(callback)
        print(f"PubSubBroker: New subscription to topic '{topic}'.")

    def publish(self, topic: str, message):
        """向一个主题发布消息。"""
        with self.lock:
            if topic in self.topics:
                # print(f"PubSubBroker: Publishing to topic '{topic}': {message}")
                for callback in self.topics[topic]:
                    # 在一个新线程中异步调用回调，以避免阻塞发布者
                    threading.Thread(target=callback, args=(message,)).start()
