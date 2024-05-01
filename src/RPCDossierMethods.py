import re
from datetime import datetime
import shortuuid
from typing import Optional, Dict, Union, List, Any

from RPCCommandTools import RPCTools


class RPCAuthorizationError(Exception):
    """Exception raised for authorization errors in RPC."""
    
    def __init__(self, message="Authorization failed"):
        """
        Initialize RPCAuthorizationError with a custom error message.
        
        Args:
            message (str): The error message to display. Default is "Authorization failed".
        """
        self.message = message
        super().__init__(self.message)






class RPCDossierMethods:
    def __init__(self, app_setting, setup_nodes, event_queue):
        """
        Initialize RPCMethods with application settings and node setup.

        Args:
            app_setting: Application settings.
            setup_nodes: Node setup.
        """
        self.setup_nodes = setup_nodes
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()
        self.rpc_tools = RPCTools(app_setting)
        self.event_queue = event_queue



    def remote_registration(self, data):
        """
        Handle remote registration.

        Args:
            data: The registration data.

        Returns:
            dict: A dictionary containing the response data.
        """
        self.event_id = shortuuid.uuid()
        self.logger.debug(f"[RPCMethods][remote_registration][{self.event_id}]> UNPUT data:{data}")
        if "REG" in data:
            reg_data = data["REG"]
            self.logger.info(f"[RPCMethods][remote_registration][{self.event_id}]> reg_request_recv - {reg_data}")
            ret_code, self.self_node = self.setup_nodes.just_load_json(self.event_id, "self", "full")
            if ret_code == 0:
                ack_data = {"ACK": self.self_node[0]}
                self.logger.debug(f"[RPCMethods][remote_registration][{self.event_id}]> ack_data - {ack_data}")
            else:
                return self.rpc_tools._handle_custom_error(self.self_node)
            event_result = self.setup_nodes.add_node_to_config(self._convert_to_str_recursive(reg_data))
            if event_result == 0:
                self.logger.info(f"[RPCMethods][just_load_json][{self.event_id}]> Created new host")
            else:
                return self.rpc_tools._handle_custom_error("Error created new host")
            return self.rpc_tools._prepare_response(0, "Ok", self.rpc_tools._convert_to_str_recursive(ack_data))
        else:
            return self.rpc_tools._prepare_response(2, "No registration data found", {})

    def synchronis(self, data):
        """
        Handle synchronization.

        Args:
            data: The synchronization data.

        Returns:
            str: A string indicating success.
        """
        self.event_id = shortuuid.uuid()
        self.logger.debug(f"[RPCMethods][synchronis][{self.event_id}]> UNPUT data:{data}")
        if "SYNC" in data:  
            reg_data = data["SYNC"]
            self.logger.info(f"[RPCMethods][remote_registration][{self.event_id}]> reg_request_recv - {reg_data}")
        return "Pong"

    def ping(self):
        """
        Handle ping.

        Returns:
            str: A string indicating success.
        """
        return "Pong"

    def get_dossier(self, key_node: Optional[str] = None, group: str = "nodes", format_data: Union[str, List[str]] = "partial", node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get dossier information.

        Args:
            key_node (str): The key node for authorization.
            group (str): The group for dossier retrieval.
            format_data: The format data for dossier retrieval.
            node_id (str): The ID of the node.

        Returns:
            dict: A dictionary containing the response data.
        """
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCInterface][get_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_get_cmd: key_node:{key_node}, group:{group}, format_data:{format_data}, host_id:{node_id}")
        try:
            if not group.strip() or (isinstance(format_data, str) and not format_data.strip()) or (isinstance(format_data, list) and not all(isinstance(item, str) for item in format_data)):
                raise ValueError("Empty input argument detected.")
            if not isinstance(key_node, str) or not isinstance(group, str) or not (isinstance(format_data, str) or isinstance(format_data, list)):
                raise TypeError("Invalid input type. Expected str.")
            self.aut_res = self.rpc_tools._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
        except RPCAuthorizationError as error:
            return self.rpc_tools._handle_custom_error(self.event_id, error)
        except (ValueError, KeyError, TypeError) as error:
            return self.rpc_tools._handle_custom_error(self.event_id, error)
        except Exception as ex:
            return self.rpc_tools._handle_unexpected_error(self.event_id, ex)
        else:
            return_code, response = self.setup_nodes.find_json_dossier(event_id=self.event_id, group=group, format_data=format_data, node_id=node_id)
            event = "status_node_check"
            self.event_queue.put(event)
            return self._prepare_response(return_code, "Ok", response)

    def upd_dossier(self, key_node: Optional[str] = None, group: str = "nodes", node_id: str = None, change_data: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Update dossier information.

        Args:
            key_node (str): The key node for authorization.
            group (str): The group for dossier update.
            node_id (str): The ID of the node to update.
            change_data: The data to update.

        Returns:
            dict: A dictionary containing the response data.
        """
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCInterface][upd_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_upd_cmd: key_node:{key_node}, group:{group}, node_id:{node_id}, change_data:{change_data}")
        try:
            if not group.strip():
                raise ValueError("Empty input argument detected.")
            if not isinstance(key_node, str) or not isinstance(group, str):
                raise TypeError("Invalid input type. Expected str.")
            self.aut_res = self.rpc_tools._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
        except RPCAuthorizationError as error:
            return self.rpc_tools._handle_custom_error(error)
        except (ValueError, KeyError, TypeError) as error:
            return self.rpc_tools._handle_custom_error(error)
        except Exception as ex:
            return self.rpc_tools._handle_unexpected_error(ex)
        else:
            return_code, response = self.setup_nodes.update_node_by_id(event_id=self.event_id, node_id=node_id, group=group, updated_values=self.rpc_tools._convert_to_str_recursive(change_data))
            return self.rpc_tools._prepare_response(return_code, "Ok", response)

    def add_dossier(self, key_node: Optional[str] = None, group: str = "nodes", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add dossier information.

        Args:
            key_node (str): The key node for authorization.
            group (str): The group for dossier addition.
            data: The data to add.

        Returns:
            dict: A dictionary containing the response data.
        """
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCInterface][add_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_add_cmd: key_node:{key_node}, group:{group}, data:{data}")
        try:
            if not group.strip():
                raise ValueError("Empty input argument detected.")
            if not isinstance(key_node, str) or not isinstance(group, str):
                raise TypeError("Invalid input type. Expected str.")
            self.aut_res = self._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
            self.data = eval(data)
            self.rpc_tools._validate_ip_port(self.data["host"], self.data["port"])
            self.host_id = str(shortuuid.uuid())
            host_info = {'id': self.host_id, 'host': self.data["host"], 'port': int(self.data["port"]), 'type': 'neighbour', 'active': 'unknown', 'route': ""}
            self.logger.debug(f"{self.log_prefix} Adding JSON data - {host_info}")
            event_result = self.setup_nodes.add_node_to_config(host_info)
            if event_result == 0:
                self.logger.info(f"{self.log_prefix} Created new host with ID {self.host_id}, DATA - {host_info}")
                return self.rpc_tools._prepare_response(0, "Ok", host_info)
            else:
                self.logger.error(f"{self.log_prefix} Error created new host with ID {self.host_id}, DATA - {host_info}")
                return self.rpc_tools._prepare_response(2, f"Error adding node to configuration. \n{host_info}", {})
        except RPCAuthorizationError as error:
            return self.rpc_tools._handle_custom_error(error)
        except (ValueError, KeyError, TypeError) as error:
            return self.rpc_tools._handle_custom_error(error)
        except Exception as ex:
            return self.rpc_tools._handle_unexpected_error(ex)

    def del_dossier(self, key_node: Optional[str] = None, group: str = "nodes", node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete dossier information.

        Args:
            key_node (str): The key node for authorization.
            group (str): The group for dossier deletion.
            node_id (str): The ID of the node to delete.

        Returns:
            dict: A dictionary containing the response data.
        """
        self.event_id = shortuuid.uuid()
        self.log_prefix = f"[RPCInterface][put_dossier][{self.event_id}]"
        self.logger.debug(f"{self.log_prefix}> inc_put_cmd: key_node:{key_node}, group:{group}, node_id:{node_id}")
        try:
            if not group.strip():
                raise ValueError("Empty input argument detected.")
            if not isinstance(key_node, str) or not isinstance(group, str):
                raise TypeError("Invalid input type. Expected str.")
            self.aut_res = self.rpc_tools._internal_authorize(key_node, self.event_id)           
            if self.aut_res == 1:
                raise RPCAuthorizationError("Authorization failed.")
        except RPCAuthorizationError as error:
            return self.rpc_tools._handle_custom_error(error)
        except (ValueError, KeyError, TypeError) as error:
            return self.rpc_tools._handle_custom_error(error)
        except Exception as ex:
            return self.rpc_tools._handle_unexpected_error(ex)
        else:
            return_code, response = self.setup_nodes.remove_node_from_config(event_id=self.event_id, node_id=node_id)
            return self.rpc_tools._prepare_response(return_code, "Ok", response)
