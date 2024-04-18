import threading
from typing import Any
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from datetime import datetime
import time
from RPCMethodsLib import RPCMethods
        



class RpcScheduler:
    def __init__(self, app_setting: 'AppSetting', setup_nodes):
        self.setup_nodes = setup_nodes
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()

        

    def loop_handler(self):
        self.logger.debug("[RpcScheduler]> Starting RPC loop handler...")
        while True:
            node_ret_code, nodes = self.setup_nodes.load_json_nodes_config("nodes")
            if int(node_ret_code) != 0:
                self.logger.error(f"[RpcScheduler]> Error load_json_nodes_config: {nodes}")
                break
            self.status_node_check(nodes)
            time.sleep(2)


    def send_reg_for_node(self, host: str, port: int, data, host_id: str) -> None:
        self.logger.info(f"[EventSender][send_Ping][{host_id}]> Registration Event sent!")
        try:
            # Функция для преобразования чисел в строки во всей структуре данных
            def convert_to_str(value):
                if isinstance(value, dict):
                    return {k: convert_to_str(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [convert_to_str(v) for v in value]
                elif isinstance(value, int):
                    return str(value)
                else:
                    return value

            # Преобразование всех чисел в строки в переменной data
            data_str = convert_to_str(data)
            self.logger.debug(f"data - {data_str}")
            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            res = proxy.remote_registration(data_str)
            self.setup_nodes.update_node_by_id(host_id, {"active": "Registration"})

            if "ACK" in res:
                reg_data = res["ACK"]
                self.setup_nodes.add_node_to_config(reg_data)
                self.logger.info(f"[EventSender][send_Registration][{host_id}]> Registration Event response!")
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Registration][{host_id}] Registration - Connection refused!")
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"[EventSender][send_heartbeat] Error sending Registration to node {host_id}: {e}")
            time.sleep(5)

    def send_ping_for_node(self, host: str, port: int, host_id: str) -> None:
        self.logger.info(f"[EventSender][send_Ping][{host_id}]> Ping Event sent!")
        try:
            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            res = proxy.ping()

            if res == "pong":
                reg_data = res["ACK"]
                self.setup_nodes.add_node_to_config(reg_data)
                self.logger.info(f"[EventSender][send_Ping][{host_id}]> Ping Event response!")
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Ping][{host_id}] Ping - Connection refused!")
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"[EventSender][send_Ping] Error sending Ping to node {host_id}: {e}")
            time.sleep(10)


    def status_node_check(self, nodes):
        """Метод проверки статуса и маршрута хоста"""
       
        for node in nodes:
            node_route = node.route
            
            if node.active == "unknown":
                self_ret_code, self.self_data = self.setup_nodes.just_load_json("self")
                if int(self_ret_code) != 0:
                    self.logger.error(f"[RpcScheduler]> Error load_json_nodes_config: {self.self_data}")    
                data = {"REG": self.self_data}
                heartbeat_thread = threading.Thread(target=self.send_reg_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "active":
                heartbeat_thread = threading.Thread(target=self.send_ping_for_node, args=(node.host, node.port, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "disable":
                pass




####################################################################################################
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class RPCInterface:
    """Класс RPC интерфейса"""
    def __init__(self, rpc_host: str, rpc_port: int, app_setting: 'AppSetting', setup_nodes: 'JSONFileManager'):
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()
        self.setup_nodes = setup_nodes
        self.server = SimpleXMLRPCServer((rpc_host, rpc_port), requestHandler=RequestHandler)
        

        # Создаем экземпляр RPCMethods
        rpc_methods = RPCMethods(self.app_setting, self.setup_nodes)

        # Регистрируем методы как удаленные процедуры
        self.server.register_instance(rpc_methods)

    def run(self):
        self.logger.info(f"[RPCInterface]> RPC Interface listening on {self.rpc_host}:{self.rpc_port}")
        self.server.serve_forever()





####################################################################################################
class CoreRpc:
    def __init__(self, app_setting: 'AppSetting', setup_nodes: 'JSONFileManager'):
        self.setup_nodes = setup_nodes
        self.app_setting = app_setting
        self.rpc_host = str(self.app_setting.get_config('RPCInterface', 'rpc_host'))
        self.rpc_port = int(self.app_setting.get_config('RPCInterface', 'rpc_port'))
        
        

    def run(self):


        self.rpc_scheduler = RpcScheduler(self.app_setting, self.setup_nodes)
        self.rpc_listener = RPCInterface(self.rpc_host, self.rpc_port, self.app_setting, self.setup_nodes)

        rpc_listener_thread = threading.Thread(target=self.rpc_scheduler.loop_handler)
        rpc_scheduler_thread = threading.Thread(target=self.rpc_listener.run)

        rpc_scheduler_thread.start()
        rpc_listener_thread.start()