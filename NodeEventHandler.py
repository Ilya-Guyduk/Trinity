import inspect
import socket
import select
import threading
import queue
from typing import Tuple, List, Any, Dict
from scapy.all import IP, ICMP, sr1





class ClusterManager:
    def __init__(self, tcp_host: str, tcp_port: int, setting, setup_nodes):
        self.setup_nodes = setup_nodes

        self.nodes = []

    	# Экземпляр класса настроек логирования и конфига
        self.setting = setting
        self.logger = self.setting.get_logger()

        # Экземляр класса обработчика отправок
        self.event_sender = EventSender(self.nodes, self.logger)


        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((tcp_host, tcp_port))

            

    
    def receive_heartbeat(self, server_socket):
        try:
            client_socket, _ = server_socket.accept()
            data = client_socket.recv(1024)
            self.logger.info(f"Heartbeat received from {client_socket.getpeername()}")
            client_socket.close()
        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {e}")
    
    def run(self) -> None:


        address, port = self.server_socket.getsockname()
        self.server_socket.listen()
        self.logger.info(f"[ClusterManager][run] - Cluster-Manager running on {address}:{port}")
        inputs = [self.server_socket]

        
        while True:
            readable, _, _ = select.select(inputs, [], [], 1)

            for sock in readable:
                if sock is self.server_socket:
                    self.receive_heartbeat(self.server_socket)
                else:
                    pass  # Handle other inputs if any
            self.ret_code, self.nodes = self.setup_nodes.load_json_nodes_config()
            self.event_sender.status_node_check(self.nodes)






class EventSender:
    """docstring for ClassName"""
    def __init__(self, nodes, logger):
        self.nodes = nodes
        self.logger = logger


    def node_registration(self, new_node_data: Dict[str, Any]):

    	# Получение адреса и порта новой ноды
        self.new_node_host = new_node_data.host
        self.new_node_port = new_node_data.port


        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((self.new_node_host, int(self.new_node_port)))
                s.sendall(b"Registration")
                self.logger.info(f"[EventSender][send_Registration][{new_node_data.id}] Registration sent!")
        except ConnectionRefusedError as e:
            self.logger.error(f"[EventSender][send_Registration][{new_node_data.id}] Registration - Connection refused!")
        except socket.timeout:
            self.logger.error(f"[EventSender][send_Registration][{new_node_data.id}] Registration - Connection timeout!")
        except Exception as e:
            self.logger.error(f"[EventSender][send_heartbeat] Error sending heartbeat to node {new_node_data.id}: {e}")
    	

    def status_node_check(self, nodes):
        self.nodes = nodes
        for node in self.nodes:
            if node.active == "unknown":
                heartbeat_thread = threading.Thread(target=self.node_registration, args=(node,))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "active":
                heartbeat_thread = threading.Thread(target=self.send_heartbeat, args=(node,))
                heartbeat_thread.start()
                heartbeat_thread.join()


    def send_heartbeat(self, node):
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((node.host, int(node.port)))
                s.sendall(b"Heartbeat")
                self.logger.info(f"[EventSender][send_heartbeat][{node.id}] Heartbeat sent!")
        except ConnectionRefusedError as e:
            self.logger.error(f"[EventSender][send_heartbeat][{node.id}] Heartbeat - Connection refused!")
        except socket.timeout:
            self.logger.error(f"[EventSender][send_heartbeat][{node.id}] Heartbeat - Connection timeout!")
        except Exception as e:
            self.logger.error(f"[EventSender][send_heartbeat] Error sending heartbeat to node {node.id}: {e}")
