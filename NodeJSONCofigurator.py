import json
import logging
import inspect
import threading
from typing import Tuple, List, Any, Dict

from SelfParser import SelfController

class SelfInfo(object):
    """docstring for SelfInfo"""
    def __init__(self, id: str, host: str, port: int, type: str, active: str, hostname: str, memory: str, cpu: str, services: str):
        self.id = id
        self.host = host
        self.port = port
        self.type = type
        self.active = active
        #self.route = route
        self.hostname = hostname
        self.memory = memory
        self.cpu = cpu
        self.services = services

    @staticmethod
    def _build_data_self_node(config_data: dict[str, Any]) -> List['SelfInfo']:
        nodes_data = config_data.get("self", [])
        return [SelfInfo(**node_data) for node_data in nodes_data]


class ClusterNode:
    def __init__(self, id: str, host: str, port: int, route: str, type: str, active: str):
        self.id = id
        self.host = host
        self.port = port
        self.type = type
        self.active = active
        self.route = route


    @staticmethod
    def _build_data_node(config_data: dict[str, Any]) -> List['ClusterNode']:
        nodes_data = config_data.get("nodes", [])
        return [ClusterNode(**node_data) for node_data in nodes_data]



class JSONFileManager:
    def __init__(self, file_path: str, app_setting):
        self.file_path = file_path
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            self.logger.warning(f"[JSONFileManager]> '{self.app_setting.get_config('Nodes', 'json_file')}' doesnt not exist! Create new file!")
            self.self_controller = SelfController(self.app_setting)
            self.self_controller = self.self_controller.init_json_file()


    def _write_config(self, data: dict[str, Any]) -> None:
        with open(self.file_path, 'w') as config_file:
            json.dump(data, config_file, indent=4)


    def _get_node_by_id(self, node_id: str) -> Dict[str, Any]:
        config_data = self._load_config()
        nodes = config_data.get("nodes", [])
        return next((node for node in nodes if node.get("id") == node_id), None)

    def just_load_json(self, data_type):
        try:
            return 0, self._load_config().get(data_type, [])
        except Exception as e:
            error_text = f"Error just loading configuration with key {data_type}: {e}"
            return 1, error_text

    def load_json_nodes_config(self, data_type) -> Tuple[int, List[ClusterNode]]:
        try:
            config_data = self._load_config()
            if data_type == "nodes":
                result = ClusterNode._build_data_node(config_data)
            elif data_type == "self":
                result = SelfInfo._build_data_self_node(config_data)
                #self.logger.debug("successfully load json config")
            return 0, result
        except Exception as e:
            error_text = f"Error loading configuration: {e}"
            return 1, error_text


    def add_node_to_config(self, host_info: dict[str, Any]):
        try:
            config_data = self._load_config()
            config_data.setdefault("nodes", []).append(host_info)
            self._write_config(config_data)
            return 0
        except Exception as e:
            logging.error(f"Error adding node to configuration: {e}")
            return 1


    def remove_node_from_config(self, node_id: str):
        try:
            config_data = self._load_config()
            nodes = config_data.get("nodes", [])
            nodes[:] = [node for node in nodes if node.get("id") != node_id]
            self._write_config(config_data)
            logging.info(f"Node with id {node_id} removed from configuration successfully.")
            return 0
        except Exception as e:
            logging.error(f"Error removing node from configuration: {e}")
            return 1


    def find_node_by_id(self, data_type="nodes", node_id=None):
        try:
            if node_id is None:
                return self.just_load_json(data_type)
            else:
                return self._get_node_by_id(node_id)
        except Exception as e:
            logging.error(f"Error finding node in configuration: {e}")
            return None


    def update_node_by_id(self, node_id: str, updated_values):
        try:
            config_data = self._load_config()
            nodes = config_data.get("nodes", [])
            for node in nodes:
                if node.get("id") == node_id:
                    node.update(updated_values)
                    break
            self._write_config(config_data)
            logging.info(f"Node with id {node_id} updated in configuration successfully.")
        except Exception as e:
            logging.error(f"Error updating node in configuration: {e}")