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
        heartbeat_data = None  # Здесь инициализируем переменную
        try:
            client_socket, _ = server_socket.accept()
            data = client_socket.recv(1024)
            # Декодирование данных из байтов в строку
            data_str = data.decode()
            # Если данные ожидаются в формате JSON
            heartbeat_data = json.loads(data_str)

        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {e}")

        if "REG" in heartbeat_data:  # Проверяем, определена ли переменная и содержит ли она нужное значение
            reg_data = heartbeat_data["REG"]
            print(f"{reg_data}")
            for item in reg_data:
                self.remote_host = item['host']
                self.remote_port = item['port']
                self.remote_id = item["id"]

            print(f"{self.remote_host}")
            print(f"{self.remote_port}")
            # Отправка ответного пакета
            self.ret_code, self.self_node = self.setup_nodes.just_load_json("nodes")
            data = {"ACK": self.self_node[0]}
            print(f"ack_data = {data}")
            self.event_sender.send_event_for_node(self.remote_host, self.remote_port, data, self.remote_id)
                
            # Обработка данных
            self.logger.info(f"Heartbeat received from {client_socket.getpeername()}: {heartbeat_data}")


        if "ACK" in heartbeat_data:
            ack_data = heartbeat_data["ACK"]
            
            self.remote_host = ack_data['host']
            self.remote_port = ack_data['port']
            self.remote_id = ack_data["id"]
            event_result = self.setup_nodes.add_node_to_config(ack_data)
            if event_result == 0:
                
                self.logger.info(f" Created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")
            else:
                self.logger.error(f" Error created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")


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
            self.logger.error(f"[EventSender][send_heartbeat] Error sending to node {host_id}: {e}")
    	

    def status_node_check(self, nodes):
        self.nodes = nodes
        for node in self.nodes:
            if node.active == "unknown":
                self.ret_code, self.self_node = self.setup_nodes.just_load_json("self")
                data = {"REG": self.self_node}
                heartbeat_thread = threading.Thread(target=self.send_event_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "active":
                data = {"BIT": "12345"}
                heartbeat_thread = threading.Thread(target=self.send_event_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

