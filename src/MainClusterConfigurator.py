import logging
import threading
import configparser
from NodeJSONCofigurator import JSONFileManager
from CoreRpcInterfaceHandler import CoreRpc
from CoreProxyHandler import CoreRroxy
from SignalHandler import SignalHandler

class AppSetting:
    """
    Class for configuring logging and reading configuration file.

    Attributes:
        config_file (str): Path to the configuration file.
        logger (logging.Logger): Logger object for logging events.
        log_file (str): Path to the log file.
        log_level (str): Logging level.

    Methods:
        __init__: Initializes the AppSetting object.
        setup_logging: Configures the logger.
        get_config: Retrieves a value from the configuration file.
        get_logger: Retrieves the logger object.
    """

    def __init__(self, config_file: str = '../config/trinity.ini'):
        """
        Initializes the AppSetting object.

        Args:
            config_file (str, optional): Path to the configuration file.
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.log_file = self.config.get('Logging', 'log_file')
        self.log_level = self.config.get('Logging', 'log_level')
        self.setup_logging()

    def setup_logging(self) -> None:
        """
        Configures the logger.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.debug("[AppSetting][setup_logging]> Initializing daemon settings...")

    def get_config(self, section: str, option: str) -> str:
        """
        Retrieves a value from the configuration file.

        Args:
            section (str): The section in the configuration file.
            option (str): The option in the specified section.

        Returns:
            str: The value associated with the specified option.
        """
        return self.config.get(section, option)

    def get_logger(self) -> logging.Logger:
        """
        Retrieves the logger object.

        Returns:
            logging.Logger: The logger object.
        """
        return self.logger

class InitCluster:
    """
    Class for initializing the cluster.

    Methods:
        __init__: Initializes the InitCluster object.
        init_cluster_worker: Starts the cluster initialization process.
    """

    def __init__(self):
        """
        Initializes the InitCluster object.
        """
        self.app_setting = AppSetting()
        self.logger = self.app_setting.get_logger()
        self.json_node_config = self.app_setting.get_config('Nodes', 'json_file')
        self.setup_nodes = JSONFileManager(self.json_node_config, self.app_setting)

    def init_cluster_worker(self) -> None:
        """
        Starts the cluster initialization process.
        """
        self.logger.info("[InitCluster]> Initializing daemon...")

        # Создание и регистрация обработчика сигналов
        signal_handler = SignalHandler(self.logger)
        signal_handler.register_signal_handlers()
        
        self.rpc_host = str(self.app_setting.get_config('RPCInterface', 'rpc_host'))
        self.rpc_port = int(self.app_setting.get_config('RPCInterface', 'rpc_port'))
        self.rpc_interface = CoreRpc(self.app_setting, self.setup_nodes)
        rpc_interface_thread = threading.Thread(target=self.rpc_interface.run)
        rpc_interface_thread.start()
        rpc_interface_thread.join()

        self.core_proxy = CoreRroxy(self.app_setting)
        core_proxy_thread = threading.Thread(target=self.core_proxy.main)
        core_proxy_thread.start()
        core_proxy_thread.join()

if __name__ == "__main__":
    main = InitCluster()
    main.init_cluster_worker()
