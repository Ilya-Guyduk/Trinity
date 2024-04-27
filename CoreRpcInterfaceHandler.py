import threading
from typing import Any
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from RPCMethodsLib import RPCMethods        
from CoreRpcScheduler import RpcScheduler


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
        self.server = SimpleXMLRPCServer((rpc_host, rpc_port), requestHandler=RequestHandler, allow_none=False)
        

        # Создаем экземпляр RPCMethods
        rpc_methods = RPCMethods(self.app_setting, self.setup_nodes)

        # Регистрируем методы как удаленные процедуры
        self.server.register_instance(rpc_methods)

    def run(self):
        self.logger.info(f"[RPCInterface][run]> RPC Interface listening on {self.rpc_host}:{self.rpc_port}")
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