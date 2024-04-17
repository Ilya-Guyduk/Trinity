import inspect
import uuid
import re
from datetime import datetime
import shortuuid

class Configurator:
    def __init__(self, app_setting, logger, setup_nodes):
        self.logging = logger
        self.setup_nodes = setup_nodes

        self.nodes = []
        self.config_data = app_setting


    def add_node(self, com_id, *values):

        """
        Метод добавления и валидации новой ноды
        """
        
        log_prefix = f"[Configurator / {inspect.currentframe().f_code.co_name}][{com_id}]"
        # Регулярное выражение для валидации адреса
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        # передаем id события
        
        # Создаем уникальный идентификатор хоста
        self.host_id = str(uuid.uuid4())
        self.logging.debug(f"{log_prefix} Trying adding host with id: {self.host_id}")

        # Проверяем, что порт и адрес имеет корректный формат
        try:
            port = int(values[1])
            if port < 0 or port > 65535:
                raise ValueError("Port number out of range")
            elif not ipv4_pattern.match(values[0]): 
                raise ValueError(f"Invalid IP address - {values[0]}")
            else:
                self.logging.debug(f"{log_prefix} Port - {values[0]} IP - {values[0]}")
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
                    
        self.logging.debug(f"{log_prefix} Adding JSON data - {host_info}")

        event_result = self.setup_nodes.add_node_to_config(host_info)
        if event_result == 0:
            
            self.logging.info(f"{log_prefix} Created new host with ID {self.host_id}, IP {values[0]}, Port {values[1]}")
            return [host_info]
        else:
            self.logging.error(f"{log_prefix} Error created new host with ID {self.host_id}, IP {values[0]}, Port {values[1]}")
            return f"Error adding node to configuration. \n{host_info}"


    def delete_node(self, com_id, host_id):
        self.com_id = com_id
        self.host_id = host_id

        # Удаление информации о ноде из JSON-файла
        result = self.setup_nodes.remove_node_from_config(self.host_id)
        self.logging.info(f"[Configurator / delete_node][{self.com_id}] Node with host ID {self.host_id} deleted from configuration.")

        return result

    def status(self, com_id, *values):
        if len(values) == 0:
            print(f"{com_id} - {len(values)}")
            ret_code, result = self.setup_nodes.find_node_by_id()
            return result
        elif len(values) >= 0:
            print(len(values))
            method = str(values[0])
            self.logging.debug(f"{self.log_prefix} RPC status method - {method}")
            
            method_functions = {
                "self": self.setup_nodes.find_node_by_id,
            }
            if method in method_functions:

                func = method_functions[method]
                args_to_pass = values[1:] if len(values) >= 2 else []
                self.logger.info(f"{self.log_prefix} Trying {method} with args: {args_to_pass}")

                data = func(*args_to_pass)
                ret_code = 0
                desc = "Ok!"

            result = self.setup_nodes.find_node_by_id(values)




class RPCMethods:
    def __init__(self, app_setting, setup_nodes):
        self.app_setting = app_setting
        self.setup_nodes = setup_nodes
        self.logger = self.app_setting.get_logger()

        self.configurator = Configurator(app_setting, self.logger, setup_nodes)

    def _get_info_about_method(self):

        return inspect.currentframe().f_code.co_name

    def remote_registration(self, data):
        if "REG" in data:  # Проверяем, определена ли переменная и содержит ли она нужное значение
            reg_data = data["REG"]
            print(f"reg_data - {reg_data}")
            for item in reg_data:
                self.remote_host = item['host']
                self.remote_port = item['port']
                self.remote_id = item["id"]

            print(f"{self.remote_host}")
            print(f"{self.remote_port}")
            # Отправка ответного пакета
            self.ret_code, self.self_node = self.setup_nodes.just_load_json("self")
            data = {"ACK": self.self_node[0]}
            print(f"ack_data = {data}")
            return data
                
            # Обработка данных
            self.logger.info(f"Heartbeat received: {data}")


        if "ACK" in data:
            ack_data = data["ACK"]
            
            self.remote_host = ack_data['host']
            self.remote_port = ack_data['port']
            self.remote_id = ack_data["id"]
            event_result = self.setup_nodes.add_node_to_config(ack_data)
            if event_result == 0:
                
                self.logger.info(f" Created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")
            else:
                self.logger.error(f" Error created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")



    def ping(self) -> str:
        return("Pong")



    def node(self, *args) -> str:
        # Получение имени метода для логирования
        self.method_name = self._get_info_about_method()
        # Уникальный идентификатор события 
        self.com_id = shortuuid.uuid()
        # Префикс лога
        self.log_prefix = f"[RPCMethods / {self.method_name}][{self.com_id}]"
        self.logger.debug(f"{self.log_prefix} New RPC command - {args}")
        data = []
        # Проверка на наличие аргументов хоста
        if len(args) >= 1:
            method = str(args[0])
            self.logger.debug(f"{self.log_prefix} RPC method - {method}")
            method_functions = {
                "add": self.configurator.add_node,
                "del": self.configurator.delete_node,
                "status": self.configurator.status
            }
            if method in method_functions:

                func = method_functions[method]
                args_to_pass = args[1:] if len(args) >= 2 else []
                self.logger.info(f"{self.log_prefix} Trying {method} with args: {args_to_pass}")

                data = func(self.com_id, *args_to_pass)
                ret_code = 0
                desc = "Ok!"


            else:
                self.logger.warning(f"{self.log_prefix} Unknown method: {method}")
                ret_code = 2
                desc = "Unknown method"


        else:
            help_message = (
                "node add [address] [port] ...\n"
                "     del [address] ...\n"
                "     mod [address] ...\n"
                "     status [id] ...\n"
            )
            self.logger.warning(f"[RPCInterface][{self.com_id}] Insufficient arguments provided")
            ret_code = 2
            desc = "Do you help?"
            data = [{"Usage": help_message}]





        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        answer = {"retcode": ret_code, "desc": desc, "time": formatted_time, "event_id": str(self.com_id)}
        result = {"answer": [answer], "data": data}
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

            self.logger.warning("Insufficient arguments provided.")
            result =  help_message

        return result