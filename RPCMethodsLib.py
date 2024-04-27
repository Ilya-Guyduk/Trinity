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







class RPCMethods:
    def __init__(self, app_setting, setup_nodes):
        self.app_setting = app_setting
        self.setup_nodes = setup_nodes
        self.logger = self.app_setting.get_logger()



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


    def _prepare_response(self, ret_code, desc, data):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        answer = {"retcode": ret_code, "desc": desc, "time": formatted_time, "event_id": str(self.event_id)}
        result = {"answer": [answer], "data": data}
        return result

    def remote_registration(self, data):
        self.event_id: str = shortuuid.uuid()
        self.logger.debug(f"[RPCMethods][remote_registration][{self.event_id}]> UNPUT data:{data}")
        
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
            
            self.logger.info(f"[RPCMethods][remote_registration][{self.event_id}]> reg_request_recv - {reg_data}")

            # Отправка ответного пакета
            self.ret_code, self.self_node = self.setup_nodes.just_load_json(self.event_id, "self", "full")
            if self.ret_code == 0:
                ack_data = {"ACK": self.self_node[0]}
                self.logger.debug(f"[RPCMethods][remote_registration][{self.event_id}]> ack_data - {ack_data}")
            else:
                self.logger.error(f"[RPCMethods][just_load_json][{self.event_id}]> {self.self_node}")
            
            event_result = self.setup_nodes.add_node_to_config(convert_to_str(reg_data))
            if event_result == 0:
                self.logger.info(f"[RPCMethods][just_load_json][{self.event_id}]> Created new host")
            else:
                self.logger.error(f"[RPCMethods][just_load_json][{self.event_id}]> Error created new host")

            return convert_to_str(ack_data)
        else:
            return {"error": "No registration data found"}


    def synchronis(self, data):
        self.event_id: str = shortuuid.uuid()
        self.logger.debug(f"[RPCMethods][synchronis][{self.event_id}]> UNPUT data:{data}")

        def convert_to_str(value):
            if isinstance(value, dict):
                return {k: convert_to_str(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_to_str(v) for v in value]
            elif isinstance(value, int):
                return str(value)
            else:
                return value

        if "SYNC" in data:  
            reg_data = data["SYNC"]
            
            self.logger.info(f"[RPCMethods][remote_registration][{self.event_id}]> reg_request_recv - {reg_data}")

        return "Pong"


    def ping(self):
        return "Pong"

    def get_dossier(self, 
                    key_node: Optional[str] = None, 
                    group: str = "nodes", 
                    format_data: Union[str, List[str]] = "partial", 
                    node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets data in JSON format from a dossier.

        Args:
            key_node (str, optional): Authorization key. Defaults to None.
            group (str, optional): Group of nodes. Defaults to 'nodes'. Possible values: 'nodes', 'self'.
            format_data (str, optional): Data format. Default is 'partial'. Possible values: 'partial', 'full' or list of keys.
            node_id (str, optional): Node identifier. Defaults to None.

        Returns:
            Dict[str, Any]: The prepared response in JSON format.

        Raises:
            RPCAuthorizationError: Authorization error.
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
        self.log_prefix: str = f"[RPCInterface][get_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_get_cmd: key_node:{key_node}, group:{group}, format_data:{format_data}, host_id:{node_id}")
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
            
            # Additional check for 'put' operation
            #if operation == 'put' and (host is None or port is None):
            #    raise ValueError("Host and port are required for 'put' operation.")

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
            self.logger.info(f"{self.log_prefix}> Command execution {format_data} from {key_node} to {node_id}")

            return_code, response = self.setup_nodes.find_json_dossier(event_id=self.event_id, group=group, format_data=format_data, node_id=node_id)

            return_code = 0
            description = "Ok!"
        finally:

            # Return processed response
            return self._prepare_response(return_code, description, response)


    def upd_dossier(self, 
                    key_node: Optional[str] = None, 
                    group: str = "nodes",  
                    node_id: str = None, 
                    change_data: Dict[str, Any] = {}) -> Dict[str, Any]:

        # Initialize variables
        return_code: int = None
        description: str = None
        response: str = None

        # Generate unique event ID for logging
        self.event_id: str = shortuuid.uuid()
        self.log_prefix: str = f"[RPCInterface][upd_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_upd_cmd: key_node:{key_node}, group:{group}, node_id:{node_id}, change_data:{change_data}")
        try:
            # Check for empty input arguments
            if not group.strip():
                raise ValueError("Empty input argument detected.")

            # Check for invalid input types
            if not isinstance(key_node, str) or not isinstance(group, str):
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
            self.logger.info(f"{self.log_prefix}> [group:{group}]Command execution {change_data} from {key_node} to {node_id}")

            return_code, response = self.setup_nodes.update_node_by_id(event_id=self.event_id, node_id=node_id, group=group, updated_values=eval(change_data))

            return_code = 0
            description = "Ok!"

        finally:

            # Return processed response
            return self._prepare_response(return_code, description, response)



    def add_dossier(self, 
                    key_node: Optional[str] = None, 
                    group: str = "nodes", 
                    data: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Gets data in JSON format from a dossier.

        Args:
            key_node (str, optional): Authorization key. Defaults to None.
            group (str, optional): Group of nodes. Defaults to 'nodes'. Possible values: 'nodes', 'service', 'cluster'.
            node_id (str, optional): Node identifier. Defaults to None.

        Returns:
            Dict[str, Any]: The prepared response in JSON format.

        Raises:
            RPCAuthorizationError: Authorization error.
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
        self.log_prefix: str = f"[RPCInterface][get_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_get_cmd: key_node:{key_node}, group:{group}, data:{data}")
        try:
            # Check for empty input arguments
            if not group.strip():
                raise ValueError("Empty input argument detected.")

            # Check for invalid input types
            if not isinstance(key_node, str) or not isinstance(group, str):
                raise TypeError("Invalid input type. Expected str.")

            # Perform authorization
            self.aut_res = self._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
            
            # Additional check for 'put' operation
            #if operation == 'put' and (host is None or port is None):
            #    raise ValueError("Host and port are required for 'put' operation.")

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
            print(data["port"])
            print(data["host"])
            ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
            # передаем id события
            
            # Создаем уникальный идентификатор хоста
            self.host_id = str(shortuuid.uuid())

            # Проверяем, что порт и адрес имеет корректный формат
            try:
                port = int(data["port"])
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

            return_code = 0
            description = "Ok!"
        finally:

            # Return processed response
            return self._prepare_response(return_code, description, response)



    def del_dossier(self, 
                    key_node: Optional[str] = None, 
                    group: str = "nodes",  
                    node_id: Optional[str] = None) -> Dict[str, Any]:

        # Initialize variables
        return_code: int = None
        description: str = None
        response: str = None

        # Generate unique event ID for logging
        self.event_id: str = shortuuid.uuid()
        self.log_prefix: str = f"[RPCInterface][put_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_put_cmd: key_node:{key_node}, group:{group}, node_id:{node_id}, change_data:{change_data}")
        try:
            # Check for empty input arguments
            if not group.strip():
                raise ValueError("Empty input argument detected.")

            # Check for invalid input types
            if not isinstance(key_node, str) or not isinstance(group, str):
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
            self.logger.info(f"{self.log_prefix}> Command execution {format_data} from {key_node} to {node_id}")

            return_code, response = self.setup_nodes.remove_node_from_config(event_id=self.event_id, node_id=node_id)

            return_code = 0
            description = "Ok!"

        finally:

            # Return processed response
            return self._prepare_response(return_code, description, response)