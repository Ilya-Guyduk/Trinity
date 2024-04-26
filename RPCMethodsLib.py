import inspect
import shortuuid
import re
from datetime import datetime
import shortuuid
from typing import Optional, Tuple, Any, Dict, Union, List

class RPCAuthorizationError(Exception):
    """Исключение, возникающее при ошибке авторизации в RPC."""
    
    def __init__(self, message="Authorization failed"):
        self.message = message
        super().__init__(self.message)



class Configurator:
    def __init__(self, app_setting, logger, setup_nodes):
        self.logger = logger
        self.setup_nodes = setup_nodes

        self.nodes = []
        self.config_data = app_setting

    def modificate_node(self):
        pass


    def add_node(self, com_id, group, *values):

        """
        Метод добавления и валидации новой ноды
        """
        self.group = group
        
        log_prefix = f"[Configurator /{inspect.currentframe().f_code.co_name}][{com_id}]>"
        # Регулярное выражение для валидации адреса
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        # передаем id события
        
        # Создаем уникальный идентификатор хоста
        self.host_id = str(shortuuid.uuid())

        # Проверяем, что порт и адрес имеет корректный формат
        try:
            port = int(values[1])
            if port < 0 or port > 65535:
                raise ValueError("Port number out of range")
            elif not ipv4_pattern.match(values[0]): 
                raise ValueError(f"Invalid IP address - {values[0]}")
        except ValueError:
            return f"Invalid port number - {values[1]} or IP - {values[0]}"

        # Проверяем, что хост с таким идентификатором уже не существует

        # Добавляем новый хост в конфигурацию
        self.default_type = 'neighbour'
        self.default_mod = 'unknown'
        host_info = {
                                'id': self.host_id, 
                                'host': values[0], 
                                'port': int(values[1]),
                                'type': self.default_type,
                                'active': self.default_mod,
                                'route': ""
                    }
                    
        self.logger.debug(f"{log_prefix} Adding JSON data - {host_info}")

        event_result = self.setup_nodes.add_node_to_config(host_info)
        if event_result == 0:
            
            self.logger.info(f"{log_prefix} Created new host with ID {self.host_id}, DATA - {host_info}")
            return host_info
        else:
            self.logger.error(f"{log_prefix} Error created new host with ID {self.host_id}, DATA - {host_info}")
            return f"Error adding node to configuration. \n{host_info}"


    def delete_node(self, com_id, group, host_id):
        self.group = group
        self.com_id = com_id
        self.host_id = host_id

        # Удаление информации о ноде из JSON-файла
        result = self.setup_nodes.remove_node_from_config(self.host_id)
        self.logger.info(f"[Configurator / delete_node][{self.com_id}] Node with host ID {self.host_id} deleted from configuration.")

        return result


    def status(self, com_id, group, *values):
        self.group = group
        self.com_id = com_id
        if "full" in values:
            format_data = "full"
        else:
            format_data = "partial"   

        self.logger.debug(f"[Configurator/status][{self.com_id}]> len - {len(values)}, values - {values}, group - {self.group}, format data - {format_data}")
        
        if len(values) == 0:
            ret_code, result = self.setup_nodes.find_node_by_id(self.group, format_data)
            if int(ret_code) != 0:
                self.logger.error(f"[Configurator/status][{self.com_id}]> {result}")
                #return result
            #else:
                #self.logger.debug(f"[Configurator/status][{self.com_id}]> result of {format_data} status: {result}")
                #return result


        elif len(values) > 0:

            method = str(values[0])
            

            method_functions = {
                "self": self.setup_nodes.find_node_by_id,
            }
            if method in method_functions:

                func = method_functions[method]
                args_to_pass = values[1:] if len(values) >= 2 else []
                self.logger.info(f"[Configurator/status]> Trying {method} with args: {args_to_pass}")

                data = func(self.group, format_data, *args_to_pass)
                ret_code = 0
                desc = "Ok!"

            ret_code, result = self.setup_nodes.find_node_by_id(self.group, values[0])
            #return result

        self.logger.info(f"[Configurator/status][{self.com_id}]> res {self.group} status  - {result}")
        return result



class RPCMethods:
    def __init__(self, app_setting, setup_nodes):
        self.app_setting = app_setting
        self.setup_nodes = setup_nodes
        self.logger = self.app_setting.get_logger()

        self.configurator = Configurator(app_setting, self.logger, setup_nodes)

        # Словарь с методами
        self.method_functions = {
            "add": self.configurator.add_node,
            "del": self.configurator.delete_node,
            "status": self.configurator.status,
            "mod": self.configurator.modificate_node,
        }

    def _internal_authorize(self, key_node: str, event_id: str) -> bool:
        result = 0
        # Получение ключа из конфигурации приложения
        self.key = self.app_setting.get_config('RPCInterface', 'key')
        self.logger.debug(f"[RPCInterface][_internal_authorize][{event_id}]> key_node:{key_node}, my_key:{self.key}")
        # Проверка наличия ключа
        if key_node is None:
            result = 1

        # Сравнение ключей с использованием Secure Compare
        #if not hmac.compare_digest(key_node, self.key):
        #    result =  False

        if key_node != "1":
            result = 1
        
        self.logger.debug(f"[RPCInterface][_internal_authorize][{event_id}]> result:{result}!")
        return result

    def _get_info_about_method(self):
        return inspect.currentframe().f_code.co_name



    def _process_command(self, group, method, args):
        if method in self.method_functions:
            func = self.method_functions[method]
            args_to_pass = args[1:] if len(args) >= 2 else []
            self.logger.debug(f"[RPCMethods/{group}] Trying {method} with args: {args_to_pass}")
            data = func(self.event_id, group, *args_to_pass)
            ret_code = 0
            desc = "Ok!"
        else:
            self.logger.warning(f"[RPCMethods/{group}] Unknown method: {method}")
            ret_code = 2
            desc = "Unknown method"
            data = [{"method": method}]

        return ret_code, desc, data



    def _prepare_response(self, ret_code, desc, data):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        answer = {"retcode": ret_code, "desc": desc, "time": formatted_time, "event_id": str(self.event_id)}
        result = {"answer": [answer], "data": data}
        return result

    def ping(self):
        return "Pong"


    def authorize(self, key_node: str) -> str:
        """
        Метод для авторизации по ключу `key_node`.

    Args:
        key_node (str): Ключ узла для авторизации.
        args: Дополнительные аргументы (если необходимо).

    Returns:
        str: Результат выполнения авторизации.
        """
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCMethods/authorize][{self.event_id}]>"
        self.logger.info(f"{self.log_prefix} New authorization attempt - {key_node}")

        # Проверка наличия ключа
        if key_node == "1":
            ret_code = 0
            desc = "Authorization successful"
            data = [{"key_node": key_node}]
        else:
            ret_code = 2
            desc = "Authorization failed"
            data = [{"error": "Invalid key_node"}]

        return self._prepare_response(ret_code, desc, data)

    def remote_registration(self, data):
        self.logger.debug(f"[RPCMethods][remote_registration]> data - {data}")
        
        def convert_to_str(value):
            if isinstance(value, dict):
                return {k: convert_to_str(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_to_str(v) for v in value]
            elif isinstance(value, int):
                return str(value)
            else:
                return value

        if "REG" in data:  
            reg_data = data["REG"]

            for key, value in reg_data.items():  
                if key in ['host', 'port', 'id']:
                    setattr(self, f"remote_{key}", value)
                    self.logger.info(f"[RPCMethods][remote_registration]> self.remote_{key} - {value}")
            
            self.logger.debug(f"[RPCMethods][remote_registration]> reg_data - {reg_data}")

            # Отправка ответного пакета
            self.ret_code, self.self_node = self.setup_nodes.just_load_json("self", "full")
            if self.ret_code == 0:
                ack_data = {"ACK": self.self_node[0]}
                self.logger.debug(f"[RPCMethods][remote_registration]> ack_data - {ack_data}")
            else:
                self.logger.error(f"[RPCMethods][just_load_json]> {self.self_node}")
            
            event_result = self.setup_nodes.add_node_to_config(convert_to_str(reg_data))
            if event_result == 0:
                self.logger.info(f" Created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")
            else:
                self.logger.error(f" Error created new host with ID {self.remote_id}, IP {self.remote_host}, Port {self.remote_port}")

            return convert_to_str(ack_data)
        else:
            return {"error": "No registration data found"}



    def node(self, key_node, method, host, port, *args) -> str:
        self.method = method
        self.key_node = key_node
        group = "nodes"
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCMethods/node_gateway][{self.event_id}]>"
        self.logger.info(f"{self.log_prefix} New command for group {group}, method - {method}, - {args}")

        if len(args) >= 1:
            ret_code, desc, data = self._process_command(group, self.method, args)
        else:
            help_message = (
                "node add [address] [port] ...\n"
                "     del [address] ...\n"
                "     mod [address] ...\n"
                "     status [id] ...\n"
            )
            self.logger.info(f"[RPCInterface][{self.event_id}] Insufficient arguments for group {group} - {args}")
            ret_code = 2
            desc = "Do you help?"
            data = [{"Usage": help_message}]

        return self._prepare_response(ret_code, desc, data)

    def proxy_port_operation(self):
        pass


    def json_dossier_operation(self, operation: str, key_node: Optional[str] = None, group: str = "nodes", format_data: Union[str, List[str]] = "partial", node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets data in JSON format from a dossier.

        Args:
            operation (str): The operation to be performed. Possible values: 'get', 'put', 'del'.
            key_node (str, optional): Authorisation key. Defaults to None.
            group (str, optional): Group of nodes. Defaults to 'nodes'. Possible values: 'nodes', 'self'.
            format_data (str, optional): Data format. Default is 'partial'. Possible values: 'partial', 'full' or list of keys.
            id (str, optional): Node identifier. Defaults to None.

        Returns:
            Dict[str, Any]: The prepared response in JSON format.

        Raises:
            RPCAuthorisationError: Authorisation error.
            ValueError: An empty input argument was detected.
            KeyError: Key not found.
            TypeError: Incorrect type of input arguments.
        """

        # Initialize variables
        return_code: int = None
        description: str = None
        response: str = None

        # Generate unique event ID for logging
        self.event_id: str = shortuuid.uuid()
        self.log_prefix: str = f"[RPCInterface][json_dossier_operation][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_cmd: operation:{operation}, key_node:{key_node}, group:{group}, format_data:{format_data}, host_id:{node_id}")
        try:
            # Check for empty input arguments
            if not group.strip() or (isinstance(format_data, str) and not format_data.strip()) or (isinstance(format_data, list) and not all(isinstance(item, str) for item in format_data)):
                raise ValueError("Empty input argument detected.")

            # Check for invalid input types
            if not isinstance(key_node, str) or not isinstance(group, str) or not (isinstance(format_data, str) or isinstance(format_data, list)):
                raise TypeError("Invalid input type. Expected str.")

            # Perform authorization
            self.aut_res = self._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
            
        except RPCAuthorizationError as error:

            # Handle authorization error
            self.logger.warning(f"{self.log_prefix}> Authorization error occurred: {error}")
            return_code = 2
            description = str(error)
            response = 0

        except (ValueError, KeyError, TypeError) as error:

            # Handle custom errors
            self.logger.warning(f"{self.log_prefix}> Custom error occurred: {error}")
            return_code = 2
            description = str(error)
            response = 0

        except Exception as ex:

            # Handle unexpected errors
            self.logger.error(f"{self.log_prefix}> An unexpected error occurred: {ex}")
            return_code = 1
            description = "An unexpected error occurred"
            response = 0

        else:

            # Execute command and handle success
            self.logger.info(f"{self.log_prefix}> Command execution {operation} {format_data} from {key_node} to {node_id}")

            if operation == 'get':
                return_code, response = self.setup_nodes.find_json_dossier(event_id=self.event_id, group=group, format_data=format_data, node_id=node_id)
            elif operation == 'put':
                return_code, response = self.setup_nodes.add_node_to_config(group=group, format_data=format_data, node_id=node_id)
            elif operation == 'del':
                return_code, response = self.setup_nodes.delete_node(event_id=self.event_id, group=group, node_id=node_id)
            return_code = 0
            description = "Ok!"
        finally:

            # Return processed response
            return self._prepare_response(return_code, description, response)

    