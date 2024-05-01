import threading
from typing import Any
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from RPCDossierMethods import RPCDossierMethods        
from CoreRpcScheduler import RpcScheduler
from queue import Queue


class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for XML-RPC server."""
    rpc_paths = ('/RPC2',)

class RPCInterface:
    """Class representing the RPC interface."""
    def __init__(self, rpc_host: str, rpc_port: int, app_setting: 'AppSetting', setup_nodes: 'JSONFileManager', event_queue):
        """
        Initialize the RPCInterface.

        Args:
            rpc_host (str): Host IP address for the RPC server.
            rpc_port (int): Port number for the RPC server.
            app_setting (AppSetting): Instance of the AppSetting class.
            setup_nodes (JSONFileManager): Instance of the JSONFileManager class.
        """
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()
        self.setup_nodes = setup_nodes
        self.server = SimpleXMLRPCServer((rpc_host, rpc_port), requestHandler=RequestHandler, allow_none=False)
        
        # Create an instance of RPCDossierMethods
        rpc_methods = RPCDossierMethods(self.app_setting, self.setup_nodes, event_queue)

        # Register methods as remote procedures
        self.server.register_instance(rpc_methods)

    def run(self):
        """Start the RPC interface server."""
        self.logger.info(f"[RPCInterface][run]> RPC Interface listening on {self.rpc_host}:{self.rpc_port}")
        self.server.serve_forever()

class CoreRpc:
    """Class representing the core RPC functionality."""
    def __init__(self, app_setting: 'AppSetting', setup_nodes: 'JSONFileManager'):
        """
        Initialize CoreRpc.

        Args:
            app_setting (AppSetting): Instance of the AppSetting class.
            setup_nodes (JSONFileManager): Instance of the JSONFileManager class.
        """
        self.setup_nodes = setup_nodes
        self.app_setting = app_setting
        self.rpc_host = str(self.app_setting.get_config('RPCInterface', 'rpc_host'))
        self.rpc_port = int(self.app_setting.get_config('RPCInterface', 'rpc_port'))
        self.event_queue = Queue()
        
    def run(self):
        """Start the RPC listener and scheduler."""
        self.rpc_scheduler = RpcScheduler(self.app_setting, self.setup_nodes, self.event_queue)
        self.rpc_listener = RPCInterface(self.rpc_host, self.rpc_port, self.app_setting, self.setup_nodes, self.event_queue)

        rpc_listener_thread = threading.Thread(target=self.rpc_scheduler.loop_handler)
        rpc_scheduler_thread = threading.Thread(target=self.rpc_listener.run)

        rpc_scheduler_thread.start()
        rpc_listener_thread.start()
