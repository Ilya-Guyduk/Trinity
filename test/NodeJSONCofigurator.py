import json
import logging
import inspect
from typing import Tuple, List

class ClusterNode:
    def __init__(self, id: str, host: str, port: int, type: str, active: str, route: str):
        self.id = id
        self.host = host
        self.port = port
        self.type = type
        self.active = active
        self.route = route

    def _build_data_node(self, config_data: dict[str, Any]) -> List[ClusterNode]:

    	nodes_data = config_data.get("nodes", [])
        return [ClusterNode(**node_data) for node_data in nodes_data]



class JSONFileManager:
    def __init__(self, file_path: str):
        self.file_path = file_path


    def _load_config(self) -> Dict[str, Any]:
        with open(self.file_path, 'r') as config_file:
            return json.load(config_file)


    def _write_config(self, data: dict[str, Any]):
        with open(self.file_path, 'w') as config_file:
            json.dump(data, config_file, indent=4)


    def _get_node_by_id(self, node_id: str) -> Dict[str, Any]:
        config_data = self._load_config()
        nodes = config_data.get("nodes", [])
        return next((node for node in nodes if node.get("id") == node_id), None)



    def load_json_nodes_config(self) -> Tuple[int, List[ClusterNode]]:

        try:
            config_data = self._load_config()
            nodes = ClusterNode._build_data_node(config_data)
            return 0, nodes

        except Exception as e:
            error_text = f"Error loading configuration: {e}"
            logging.error(error_text)
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
        except Exception as e:
            logging.error(f"Error removing node from configuration: {e}")


    def find_node_by_id(self, node_id=None):
        try:
            if node_id is None:
                return self._load_config().get("nodes", [])
            else:
                return self._get_node_by_id(node_id)
        except Exception as e:
            logging.error(f"Error finding node in configuration: {e}")
            return None


    def update_node_by_id(self, node_id, updated_values):
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
