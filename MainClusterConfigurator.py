import logging
import threading
import configparser
import queue

# Модуль обработчика JSON конфига нод 
from NodeJSONCofigurator import JSONFileManager
# Модуль обработчика RPC интерфейса
from RpcInterfaceHaldler import RPCInterface
# Модуль обработчика событий кластера
from NodeEventHandler import ClusterManager
# Модуль обработчика очередей
#from CoreQueueHandler import EventConfigQueue

class AppSetting:

    """Класс натройки логирования и файла конфигурации"""
    
    def __init__(self, config_file: str = 'trinity.ini'):

		# Экземпляр класса логгера
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        # Настройки логирования
        self.log_file = self.config.get('Logging', 'log_file')
        self.log_level = self.config.get('Logging', 'log_level')

        # Настройка логгера
        self.setup_logging()

		
    def setup_logging(self) -> None:

		# Создание логгера
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)

        # Формат логгера
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Создание обработчика для записи в файл
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Создание обработчика для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)


    	# Метод для получения значений из конфигурации
    def get_config(self, section: str, option: str) -> str:
        return self.config.get(section, option)


        # Метод для обращения к логгеру
    def get_logger(self) -> logging.Logger:
        return self.logger


class InitCluster:

    """
    Класс инициализации кластера
    """
    
    def __init__(self):

        # Экземпляр класса настроек 
        self.app_setting = AppSetting()
        # Логгер
        self.logger = self.app_setting.get_logger()
    	# Получение json файла из конфига
        self.json_node_config = self.app_setting.get_config('Nodes', 'json_file')
    	# Экземляр класса строителя нод JSONFileManager
        self.setup_nodes = JSONFileManager(self.json_node_config)




    def init_cluster_worker(self) -> None:


        self.host = str(self.app_setting.get_config('Server', 'host'))
        self.port = int(self.app_setting.get_config('Server', 'port'))
        self.cluster_manager = ClusterManager(self.host, self.port, self.app_setting, self.setup_nodes)

        self.rpc_host = str(self.app_setting.get_config('RPCInterface', 'rpc_host'))
        self.rpc_port = int(self.app_setting.get_config('RPCInterface', 'rpc_port'))
        self.rpc_interface = RPCInterface(self.rpc_host, self.rpc_port, self.app_setting, self.setup_nodes)
  

        cluster_manager_thread = threading.Thread(target=self.cluster_manager.run)
        rpc_interface_thread = threading.Thread(target=self.rpc_interface.run, args=(self.rpc_host, self.rpc_port))

        rpc_interface_thread.start()
        cluster_manager_thread.start()


if __name__ == "__main__":
    main = InitCluster()
    main.init_cluster_worker()
