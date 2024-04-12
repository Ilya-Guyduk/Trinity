import logging
import threading
import socket
import select
from typing import List
from dataclasses import dataclass
from queue import Queue

@dataclass
class ClusterNode:
    id: str
    host: str
    port: int
    active: str
    # Другие атрибуты ноды можно добавить по необходимости

class NodeEventHandler:
    def __init__(self, nodes: List[ClusterNode], logger: logging.Logger):
        self.nodes = nodes
        self.logger = logger
        self.node_changes_queue = Queue()
        self.running = False

    def start(self):
        self.running = True
        # Здесь можно добавить инициализацию сокетов и других необходимых ресурсов
        self.start_node_monitoring()

    def stop(self):
        self.running = False
        # Здесь можно добавить освобождение ресурсов

    def start_node_monitoring(self):
        while self.running:
            # Обработка изменений в списке нод
            if not self.node_changes_queue.empty():
                # Пример: обработка добавления/удаления ноды из очереди изменений
                node_change = self.node_changes_queue.get()
                if node_change.action == 'add':
                    self.logger.info(f"Node added: {node_change.node.id}")
                    # Здесь можно выполнить действия при добавлении ноды, например, подключение к ней
                elif node_change.action == 'remove':
                    self.logger.info(f"Node removed: {node_change.node.id}")
                    # Здесь можно выполнить действия при удалении ноды

            # Отправка хардбитов
            self.send_heartbeats()

            # Здесь можно добавить другие действия по необходимости

    def send_heartbeats(self):
        for node in self.nodes:
            if node.active != "disabled":
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5)
                        s.connect((node.host, node.port))
                        s.sendall(b"Heartbeat")
                        self.logger.info(f"Heartbeat sent to {node.id}")
                except Exception as e:
                    self.logger.error(f"Error sending heartbeat to {node.id}: {e}")

    def add_node(self, node: ClusterNode):
        # Добавление ноды в список и отправка сигнала о добавлении в очередь изменений
        self.nodes.append(node)
        self.node_changes_queue.put(NodeChange('add', node))

    def remove_node(self, node_id: str):
        # Удаление ноды из списка и отправка сигнала о удалении в очередь изменений
        for node in self.nodes:
            if node.id == node_id:
                self.nodes.remove(node)
                self.node_changes_queue.put(NodeChange('remove', node))

@dataclass
class NodeChange:
    action: str
    node: ClusterNode
