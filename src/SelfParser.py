import shortuuid
import json
import platform
import psutil
import cpuinfo
import subprocess


class SelfController:
	"""docstring for SelfController"""
	def __init__(self, app_setting):
		self.app_setting = app_setting
		self.logger = self.app_setting.get_logger()

	def _get_services(self):
	    try:
	        services_output = subprocess.check_output(['systemctl', '--no-page', '--no-legend', '--plain', '--all', '--full', 'list-units']).decode('utf-8')
	        services = []
	        for line in services_output.splitlines():
	            service_name = line.split()[0]
	            services.append(service_name)
	        return services
	    except subprocess.CalledProcessError as error:
	        self.logger.error(f"Failed to get systemd services: {error}")
	        return []


	def _get_cpu_info(self):
	    cpu_info = cpuinfo.get_cpu_info()
	    return cpu_info

	def _get_memory_info(self):
	    memory_info = {
	        "total_physical_memory": psutil.virtual_memory().total,
	        "total_swap_memory": psutil.swap_memory().total
	        }
	    return memory_info


	def _get_system_info(self):
	    hostname = platform.node()
	    memory = self._get_memory_info()
	    cpu = self._get_cpu_info()
	    return hostname, memory, cpu


	def init_json_file(self):
	    self.filename = self.app_setting.get_config('Nodes', 'json_file')
	    self.logger.info(f"[SelfController]> Starting init json file")

	    hostname, memory, cpu = self._get_system_info()
	    services = self._get_services()
	    data = {
	        "self": [
	            {
	                "id": shortuuid.uuid(),
                    "hostname": "hostname",
                    "memory": memory,
                    "cpu": cpu,
                    "host": "127.0.0.1",
                    "port": self.app_setting.get_config('RPCInterface', 'rpc_port'),
                    "type": "neighbour",
                    "active": "alone",
                    "services": services
	            }
	        ],
	        "nodes": [],
	        "cluster":[]
	    }

	    with open(self.filename, 'w') as json_file:
	        json.dump(data, json_file, indent=4)


