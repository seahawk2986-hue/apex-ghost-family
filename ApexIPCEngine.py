from typing import Any, Dict, List, Optional, Union, Callable
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class ApexIPCEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connections: Dict[str, Any] = {}
        from queue import Queue
        self.message_queue: Queue = Queue()
        self.logger = logging.getLogger('ApexIPCEngine')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 5))

    def connect(self, endpoint: str, params: Dict[str, Any]) -> None:
        if endpoint not in self.connections:
            self.connections[endpoint] = params
            self.logger.info(f'Connected to {endpoint}')

    def send_message(self, endpoint: str, message: Any) -> Optional[Any]:
        if endpoint in self.connections:
            handler = self.connections[endpoint]['handler']
            future = self.executor.submit(handler, message)
            return future.result()
        self.logger.warning(f'No connection found for {endpoint}')
        return None

    def receive_message(self, endpoint: str) -> Optional[Any]:
        while self.message_queue and self.message_queue[0][0] == endpoint:
            _, result = self.message_queue.popleft()
            return result
        self.logger.warning(f'No message found for {endpoint}')
        return None

    def close_connection(self, endpoint: str) -> None:
        if endpoint in self.connections:
            del self.connections[endpoint]
            self.logger.info(f'Disconnected from {endpoint}')

    def list_connections(self) -> List[str]:
        return list(self.connections.keys())

    def set_handler(self, endpoint: str, handler: Union[Callable[[Any], Any], Callable[[], Any]]) -> None:
        if endpoint in self.connections:
            self.connections[endpoint]['handler'] = handler
            self.logger.info(f'Handler updated for {endpoint}')

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def set_config(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.executor.max_workers = config.get('max_workers', 5)

    def __str__(self) -> str:
        return f'ApexIPCEngine(config={self.config}, connections={self.connections})'