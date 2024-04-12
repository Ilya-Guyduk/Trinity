import json
import os
import logging
import socket
import select
import threading
import uuid
import re
from xmlrpc.server import SimpleXMLRPCServer
import configparser
from NodeJSONCofigurator import JSONFileManager
import inspect
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler




class InternalReviewer:
    """docstring for ClassName"""
    def __init__(self):
        pass

    def _get_self_method_info(self) -> str:
        caller: str = inspect.stack()[1]  # Получаем информацию о вызывающем коде
        return caller.function  # Возвращаем имя функции вызывающего кода
    
    def _get_caller_class_name(self) -> str:
        caller_frame = inspect.currentframe().f_back
        caller_class = caller_frame.f_locals.get('self').__class__
        return caller_class.__name__



class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

    def on_modified(self, event):
        if event.src_path == self.config_manager.file_path:
            self.config_manager.load_json_nodes_config()



class ClusterManager:
    def __init__(self, tcp_host, tcp_port, nodes):

        self.self_info = InternalReviewer()

        self.class_name = self.self_info._get_caller_class_name()
        self.tcp_host = tcp_host 
        self.tcp_port = tcp_port

        self.nodes = nodes

        self.config_manager = JSONFileManager(CONFIG_FILE_PATH, self.class_name)

        self.start_file_monitoring()

    def start_file_monitoring(self):
        observer = Observer()
        event_handler = ConfigFileHandler(self.config_manager)
        observer.schedule(event_handler, path='.', recursive=False)
        observer.start()
    
    
    def send_heartbeat(self, node):
        method_name = inspect.currentframe().f_code.co_name
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((node.host, int(node.port)))
                s.sendall(b"Heartbeat")
                logging.info(f"[{self.class_name}][{method_name}][{node.id}] Heartbeat sent!")
        except ConnectionRefusedError as e:
            logging.error(f"[{self.class_name}][{method_name}][{node.id}] Heartbeat - Connection refused!")
        except Exception as e:
            logging.error(f"[{self.class_name}][{method_name}] Error sending heartbeat to node {node.id}: {e}")

        
    
    def receive_heartbeat(self, server_socket):
        try:
            client_socket, _ = server_socket.accept()
            data = client_socket.recv(1024)
            logging.info(f"Heartbeat received from {client_socket.getpeername()}")
            client_socket.close()
        except Exception as e:
            logging.error(f"Error receiving heartbeat: {e}")
    
    def run(self):
        method_name = self.self_info._get_self_method_info()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.tcp_host, self.tcp_port))
        server_socket.listen()
        logging.info(f"[{self.class_name}][{method_name}] - Cluster-Manager running on {self.tcp_host}:{self.tcp_port}")
        inputs = [server_socket]

        
        while True:
            readable, _, _ = select.select(inputs, [], [], 1)

            for sock in readable:
                if sock is server_socket:
                    self.receive_heartbeat(server_socket)
                else:
                    pass  # Handle other inputs if any

            self.send_heartbeats()
            
    
    def send_heartbeats(self):
        for node in self.nodes:
            if node.active:
                heartbeat_thread = threading.Thread(target=self.send_heartbeat, args=(node,))
                heartbeat_thread.start()
    


class Configurator:
    def __init__(self):
        self.class_name = self.__class__.__name__
        self.nodes = []
        self.config_file = 'config.json'
        self.config_data = JSONFileManager(self.config_file, self.class_name)


    def add_node(self, com_id, *values):

        """
        Метод добавления и валидации новой ноды
        """
        
        log_prefix = f"[{self.class_name} / {inspect.currentframe().f_code.co_name}][{com_id}]"
        # Регулярное выражение для валидации адреса
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        # передаем id события
        
        # Создаем уникальный идентификатор хоста
        self.host_id = str(uuid.uuid4())
        logging.debug(f"{log_prefix} Trying adding host with id: {self.host_id}")

        # Проверяем, что порт и адрес имеет корректный формат
        try:
            port = int(values[1])
            if port < 0 or port > 65535:
                raise ValueError("Port number out of range")
            elif not ipv4_pattern.match(values[0]): 
                raise ValueError(f"Invalid IP address - {values[0]}")
            else:
                logging.debug(f"{log_prefix} Port - {values[0]} IP - {values[0]}")
        except ValueError:
            return f"Invalid port number - {values[1]} or IP - {values[0]}"

        # Проверяем, что хост с таким идентификатором уже не существует

        #for host_info in self.config_data.nodes:
        #    if isinstance(host_info, dict) and host_info.get('nodes') == self.host_id:
        #        self.host_id = str(uuid.uuid4())

        # Добавляем новый хост в конфигурацию
        self.default_type = 'neighbour'
        self.default_mod = 'unknown'
        host_info = {
                                'id': self.host_id, 
                                'host': values[0], 
                                'port': int(values[1]),
                                'type': self.default_type,
                                'active': self.default_mod,
                                'route': self.host_id
                    }
                    
        logging.debug(f"{log_prefix} Adding JSON data - {host_info}")

        event_result = self.config_data.add_node_to_config(host_info, com_id)
        if event_result == 0:
            self.config_data.load_json_nodes_config()
            self.config_data.nodes
            logging.info(f"{log_prefix} Created new host with ID {self.host_id}, IP {values[0]}, Port {values[1]}")
            return f"{host_info}"
        else:
            logging.error(f"{log_prefix} Error created new host with ID {self.host_id}, IP {values[0]}, Port {values[1]}")
            return f"Error adding node to configuration. \n{host_info}"


    def delete_node(self, com_id, host_id):
        self.com_id = com_id
        self.host_id = host_id

        # Удаление информации о ноде из JSON-файла
        result = self.config_data.remove_node_from_config(self.host_id)
        logging.info(f"[{self.class_name} / delete_node][{self.com_id}] Node with host ID {self.host_id} deleted from configuration.")

        return result





    def status(self, com_id, *values):
        if len(values) >= 0:
            self.setup = JSONFileManager(self.config_file, self.class_name)
            result = self.setup.find_node_by_id()
            return result
        else:
            self.setup = JSONFileManager(self.config_file, self.class_name)
            result = self.setup.find_node_by_id(values)





class RPCInterface:

    """
    Класс реализации RPC интерфейса демона
    """
    def __init__(self, rpc_host: str, rpc_port: int):
        self.class_name = self.__class__.__name__
        self.server = SimpleXMLRPCServer((rpc_host, rpc_port))
        # Регистрируем методы как удаленные процедуры
        self.server.register_function(self.node)
        self.server.register_function(self.cluster)
        # Класс конфигуратора кластера
        self.configurator = Configurator()

    def _get_info_about_method(self):

        return inspect.currentframe().f_code.co_name

    def node(self, *args) -> str:

        # Получение имени метода для логирования
        self.method_name = _get_info_about_method()

        # Уникальный идентификатор события 
        self.com_id = uuid.uuid4()
        # Префикс лога
        self.log_prefix = f"[{self.class_name} / {self.method_name}][{self.com_id}]"

        logging.debug(f"{self.log_prefix} New RPC command - {args}")
        # Проверка на наличие аргументов хоста
        if len(args) >= 1:
            # Получаем метод из команды
            method = str(args[0])
            logging.debug(f"{self.log_prefix} RPC method - {method}")




            # метод добавления хоста
            if method == "add":
                logging.info(f"{self.log_prefix} Trying adding host with args: {args[1:]}")
                result = self.configurator.add_node(self.com_id, *args[1:])

            # метод изменения хоста
            elif method == "mod":
                logging.info(f"{self.log_prefix} Trying adding host...")
                result = self.configurator.mod(self.com_id, *args[1:])

            elif method == "del":
                logging.info(f"{self.log_prefix} Trying adding host...")
                result = self.configurator.delete_node(self.com_id, *args[1:])

            elif method == "status":
                if len(args) >= 2:
                    logging.info(f"{self.log_prefix} Trying send stat with args: {args[1:]}")
                    result = self.configurator.status(self.com_id, *args[1:])

                else:
                    logging.info(f"{self.log_prefix} Trying send stat")
                    result = self.configurator.status(self.com_id)

            logging.debug(f"{self.log_prefix} > method: {method}")
            logging.debug(f"{self.log_prefix} Remaining commands: {args[1:]}")

        else:
            help_message = (
            "Usage: node add [address] [port] ...\n"
            "            del [address] ...\n"
            "            mod [address] ...\n"
            "            status [address] ...\n"
            )

            logging.warning(f"[RPCInterface][{self.com_id}] Insufficient arguments provided - {method}")
            result =  help_message

        return result


    def cluster(self, *args):
        # Уникальный идентификатор события 
        self.com_id = uuid.uuid4()
        # Проверка на наличие аргументов хоста
        if len(args) >= 1:
            # Получаем метод из команды
            host_id = args[0]
            print(args[1])
            result = self.self_master.stat(self.com_id, *args[1:])
        else:
            help_message = (
            "Insufficient arguments provided.\n"
            "Usage: node add [address] ...\n"
            "            del [address] ...\n"
            "            mod [address] ...\n"
            "            status [address] ...\n"
            )

            logging.warning("Insufficient arguments provided.")
            result =  help_message

        return result

    def run(self, rpc_host, rpc_port):
        logging.info(f"[RPCInterface] - RPC Interface listening on {rpc_host}:{rpc_port}")
        self.server.serve_forever()




if __name__ == "__main__":

    CONFIG_FILE_PATH = "./config.json"
    # Конфигурация логирования
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Загрузка нод и проверка ее рузльтата
    #nodes = []
    setup_nodes = JSONFileManager(CONFIG_FILE_PATH, "__main__")
    ret_cod, nodes = setup_nodes.load_json_nodes_config()

    if ret_cod == 0:
        logging.info("Load config")
    elif ret_cod == 1:
        logging.error(f"{nodes}")


    RPC_HOST = '0.0.0.0'
    RPC_PORT = 5555
    rpc_interface = RPCInterface(RPC_HOST, RPC_PORT)

    
    
    TCP_HOST = "0.0.0.0"
    TCP_PORT = 9000
    cluster_manager = ClusterManager(TCP_HOST, TCP_PORT, nodes)

    cluster_manager_thread = threading.Thread(target=cluster_manager.run)
    rpc_interface_thread = threading.Thread(target=rpc_interface.run, args=(RPC_HOST, RPC_PORT))

    rpc_interface_thread.start()
    cluster_manager_thread.start()
