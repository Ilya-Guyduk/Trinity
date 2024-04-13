import inspect
import socket
import select
import threading
import queue
import json
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
        self.event_sender = EventSender(self.nodes, self.logger, self.setup_nodes)


        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((tcp_host, tcp_port))

            
    
    def receive_heartbeat(self, server_socket):
        try:
            client_socket, _ = server_socket.accept()
            data = client_socket.recv(1024)
            # Декодирование данных из байтов в строку
            data_str = data.decode()
            # Если данные ожидаются в формате JSON
            heartbeat_data = json.loads(data_str)

        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {e}")

        if heartbeat_data["REG"] and heartbeat_data["REG"] == "12345":
            host_id = heartbeat_data["REG"]
            print(f"{host_id}")

            # Отправка ответного пакета
            ack_data = {"ACK": "12345"}
            print(f"ack_data = {ack_data}")
            self.event_sender.send_event_for_node(client_socket.getpeername()[0], client_socket.getpeername()[1], ack_data, host_id)
            
                
            # Обработка данных
            self.logger.info(f"Heartbeat received from {client_socket.getpeername()}: {heartbeat_data}")

            client_socket.close()
        
    
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
            self.ret_code, self.nodes = self.setup_nodes.load_json_nodes_config("nodes")
            self.event_sender.status_node_check(self.nodes)






class EventSender:
    """docstring for ClassName"""
    def __init__(self, nodes, logger, setup_nodes):
        self.nodes = nodes
        self.logger = logger
        self.setup_nodes = setup_nodes

    def send_event_for_node(self, host: str, port: int, data, host_id: str) -> None:

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((host, int(port)))
                # Создайте словарь данных для отправки
                # Преобразуйте словарь в JSON-строку
                json_data = json.dumps(data)
                # Преобразуйте JSON-строку в байты
                bytes_data = json_data.encode()
                # Отправьте байты через сокет
                s.sendall(bytes_data)
            updated_values = {"active": "Registration"}
            self.setup_nodes.update_node_by_id(host_id, updated_values)
            self.logger.info(f"[EventSender][send_Registration][{host_id}] Event sent!")
        except ConnectionRefusedError as e:
            self.logger.error(f"[EventSender][send_Registration][{host_id}] Registration - Connection refused!")
        except socket.timeout:
            self.logger.error(f"[EventSender][send_Registration][{host_id}] Registration - Connection timeout!")
        except Exception as e:
            self.logger.error(f"[EventSender][send_heartbeat] Error sending heartbeat to node {host_id}: {e}")
    	

    def status_node_check(self, nodes):
        self.nodes = nodes
        for node in self.nodes:
            if node.active == "unknown":
                data = {"REG": "12345"}
                heartbeat_thread = threading.Thread(target=self.send_event_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "active":
                data = {"BIT": "12345"}
                heartbeat_thread = threading.Thread(target=self.send_event_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

