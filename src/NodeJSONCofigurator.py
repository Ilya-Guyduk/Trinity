import json
import logging
import inspect
import threading
from typing import Tuple, List, Any, Dict

from SelfParser import SelfController



class NodeBuilder:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


    @staticmethod
    def _build_data_node(config_data: dict[str, Any]) -> List['NodeBuilder']:
        nodes_data = config_data.get("nodes", [])
        return [NodeBuilder(**node_data) for node_data in nodes_data]



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
            self.logger.warning(f"[JSONFileManager][_load_config]> '{self.app_setting.get_config('Nodes', 'json_file')}' doesnt not exist! Create new file!")
            self.self_controller = SelfController(self.app_setting)
            self.self_controller = self.self_controller.init_json_file()
        else:
            self.logger.debug("[JSONFileManager][_load_config]> Load config dossier successfully!")


    def _write_config(self, data: dict[str, Any]) -> None:
        with open(self.file_path, 'w') as config_file:
            json.dump(data, config_file, indent=4)


    def _get_node_by_id(self, event_id, node_id: str) -> Dict[str, Any]:
        config_data = self._load_config()
        nodes = config_data.get("nodes", [])
        return next((node for node in nodes if node.get("id") == node_id), None)

    def just_load_json(self, event_id, data_type="nodes", format_data="partial") -> Dict[int, str]:
        try:
            node_partial_data = {}
            config = self._load_config().get(data_type, [])
            self.logger.debug(f"[JSONFileManager][just_load_json][{event_id}]> INPUT: data_type - {data_type}, format_data - {format_data}, config - {config}")
            result = []
            if format_data == "partial":
                for node_data in config:
                    
                    for key in ["id", "host", "port", "type", "active", "route"]:
                        if key in node_data:
                            node_partial_data[key] = node_data[key]
                    result.append(node_partial_data)

                self.logger.debug(f"[JSONFileManager][just_load_json][{event_id}]> OUTPUT: node_partial_data - {node_partial_data}")
                return 0, result
            elif format_data == "full":
                self.logger.debug(f"[JSONFileManager][just_load_json][{event_id}]> OUTPUT: config - {config}")
                return 0, config
            elif isinstance(format_data, list):
                for node_data in config:
                    for key in list(format_data):
                        if key in node_data:
                            node_partial_data[key] = node_data[key]
                    result.append(node_partial_data)
                self.logger.debug(f"[JSONFileManager][just_load_json][{event_id}]> OUTPUT: node_custom_data - {node_partial_data}")
                return 0, result
            else:
                return 1, f"[JSONFileManager][just_load_json][{event_id}]> Invalid format_data parameter"
        except Exception as e:
            error_text = f"[JSONFileManager][just_load_json][{event_id}]> Error with key '{data_type}' '{format_data}': {e}"
            return 1, error_text

    def load_json_nodes_config(self, data_type) -> Tuple[int, List[NodeBuilder]]:
        try:
            config_data = self._load_config()
            
            result = NodeBuilder._build_data_node(config_data)
            return 0, result
        except Exception as e:
            error_text = f"[JSONFileManager][load_json_nodes_config]> Error loading configuration: {e}"
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


    def find_json_dossier(self,event_id: str, group: str = "nodes", format_data="partial", node_id=None):
        self.logger.debug(f"[JSONFileManager][find_json_dossier][{event_id}] -> group - {group}, format_data - {format_data}, node_id - {node_id}")
        try:
            if not node_id or node_id is None:
                return self.just_load_json(event_id, group, format_data)
            else:
                return self._get_node_by_id(event_id, node_id)
        except Exception as e:
            logging.error(f"[JSONFileManager][find_json_dossier][{event_id}]> Error finding node in configuration: {e}")
            return None


    def update_node_by_id(self, event_id: str, node_id: str, group="nodes", updated_values: Dict = {}):
        self.logger.debug(f"[JSONFileManager][update_node_by_id]> INPUT event_id:{event_id}, node_id:{node_id}, group:{group}, updated_values:{updated_values} type_val:{type(updated_values)}")
        try:
            config_data = self._load_config()
            nodes = config_data.get(group, [])
            for i, node in enumerate(nodes):
                if node.get("id") == node_id:
                    # Проверяем, что updated_values содержит обновления
                    if updated_values:
                        nodes[i].update(updated_values)
                    break
            self._write_config(config_data)
            self.logger.info(f"[JSONFileManager][update_node_by_id][{event_id}]> Node id:{node_id} updated successfully.")
            return 0, ""
        except Exception as e:
            self.logger.error(f"[JSONFileManager][update_node_by_id][{event_id}]> Error updating {node_id} in group '{group}': {e}")
