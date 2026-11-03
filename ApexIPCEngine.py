"""ApexIPCEngine - the in-process IPC bus (2026-11-04 repair + completion).

The audited bug: message_queue was a queue.Queue - truthiness worked but
`queue[0]` and `queue.popleft()` raise TypeError/AttributeError, so this
engine CRASHED the moment receive_message was ever called (it was dead
scaffolding). It is now real and honest:

  - the queue = a collections.deque of (endpoint, message) pairs;
  - receive_message drains until it finds a row for the endpoint (a routed
    bus, not a single global mailbox) and returns None if none (never raises);
  - send_message submits to the handler pool and returns the result (used).
"""
from typing import Any, Callable, Dict, List, Optional, Union
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor


class ApexIPCEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connections: Dict[str, Any] = {}
        self.message_queue: deque = deque(maxlen=10000)   # bounded (RAM gate)
        self.logger = logging.getLogger('ApexIPCEngine')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get('max_workers', 5))
        self.logger.info('IPC engine up (bounded queue %d, workers %d)',
                         self.message_queue.maxlen, self.config.get('max_workers', 5))

    def connect(self, endpoint: str, params: Dict[str, Any]) -> None:
        if endpoint not in self.connections:
            self.connections[endpoint] = params
            self.logger.info('Connected to %s', endpoint)

    def set_handler(self, endpoint: str,
                    handler: Union[Callable[[Any], Any], Callable[[], Any]]) -> None:
        if endpoint in self.connections:
            self.connections[endpoint]['handler'] = handler
            self.logger.info('Handler updated for %s', endpoint)

    def send_message(self, endpoint: str, message: Any) -> Optional[Any]:
        """Direct handler call through the pool (returns the handler's result)."""
        if endpoint in self.connections:
            handler = self.connections[endpoint].get('handler')
            if handler is None:
                self.logger.warning('Endpoint %s has no handler', endpoint)
                return None
            future = self.executor.submit(handler, message)
            return future.result()
        self.logger.warning('No connection found for %s', endpoint)
        return None

    def enqueue_message(self, endpoint: str, message: Any) -> None:
        """Route a message into the bus for a later receive_message(endpoint)."""
        self.message_queue.append((endpoint, message))

    def receive_message(self, endpoint: str) -> Optional[Any]:
        """Drain the bus until a row for `endpoint` arrives (skips foreign
        rows - they stay queued for their own endpoints). Honest None."""
        keep = []
        result = None
        while self.message_queue:
            ep, payload = self.message_queue.popleft()
            if ep == endpoint:
                result = payload
                break
            keep.append((ep, payload))
        for row in reversed(keep):
            self.message_queue.appendleft(row)
        if result is None:
            self.logger.warning('No message found for %s', endpoint)
        return result

    def close_connection(self, endpoint: str) -> None:
        if endpoint in self.connections:
            del self.connections[endpoint]
            self.logger.info('Disconnected from %s', endpoint)

    def list_connections(self) -> List[str]:
        return list(self.connections.keys())

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def set_config(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.executor.max_workers = config.get('max_workers', 5)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def __str__(self) -> str:
        return (f'ApexIPCEngine(config={self.config}, '
                f'connections={self.connections}, queued={len(self.message_queue)})')