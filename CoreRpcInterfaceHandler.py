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
        self.daemon_address_template = 'http://127.0.0.1:5555'
        self.daemon_proxy = xmlrpc.client.ServerProxy(self.daemon_address_template)
        

    def loop_handler(self):
        print("Starting loop_handler")
        while True:
            my_ret_code, nodes = self.setup_nodes.load_json_nodes_config("self")
            print(my_ret_code)
            ret_code, nodes = self.setup_nodes.load_json_nodes_config("nodes")
            if int(ret_code) != 0:
                self.logger.error(f"[RpcScheduler]Error load_json_nodes_config: {nodes}")
                break
            self.status_node_check(nodes)
            time.sleep(1)


    def send_event_for_node(self, host: str, port: int, data, host_id: str) -> None:
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
            print(f"data - {data_str}")
            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            res = proxy.remote_registration(data_str)
            if "Pong" in res:
                pass
            elif "ACK" in res:
                self.setup_nodes.update_node_by_id(host_id, {"active": "active"})
            self.logger.info(f"[EventSender][send_Registration][{host_id}] Event sent!")
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Registration][{host_id}] Registration - Connection refused!")
        except Exception as e:
            self.logger.error(f"[EventSender][send_heartbeat] Error sending to node {host_id}: {e}")


    def status_node_check(self, nodes):
        """Метод проверки статуса и маршрута хоста"""
        ret_code, my_data = self.setup_nodes.just_load_json("self")
        self.node_actions = {
            'unknown': {"REG": my_data},
            'active': {"BIT": "12345"},
            'down': {"BIT": "12345"}
        }

        for node in nodes:
            node_route = node.route
            action_data = self.node_actions.get(node.active)
            if action_data:
                data = action_data
                heartbeat_thread = threading.Thread(target=self.send_event_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()




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
        self.logger.info(f"[RPCInterface] - RPC Interface listening on {self.rpc_host}:{self.rpc_port}")
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