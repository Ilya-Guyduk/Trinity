import re

class RPCTools:
    def __init__(self, app_setting):
        """
        Initialize RPCMethods with application settings and node setup.

        Args:
            app_setting: Application settings.
            setup_nodes: Node setup.
        """
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()

    def _internal_authorize(self, key_node: str, event_id: str) -> bool:
        """
        Perform internal authorization check.

        Args:
            key_node (str): The key node for authorization.
            event_id (str): The ID of the event.

        Returns:
            bool: True if authorized, False otherwise.
        """
        self.key = self.app_setting.get_config('RPCInterface', 'key')
        self.logger.debug(f"[RPCTools][_internal_authorize][{event_id}]> key_node:{key_node}, my_key:{self.key}")
        if key_node != "1":
            return True
        return False

    def _prepare_response(self, event_id, ret_code, desc, data):
        """
        Prepare a response with status code, description, and data.

        Args:
            ret_code: The return code.
            desc: The description of the response.
            data: The data to include in the response.

        Returns:
            dict: A dictionary containing the response data.
        """
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        answer = {"retcode": ret_code, "desc": desc, "time": formatted_time, "event_id": str(event_id)}
        result = {"answer": [answer], "data": data}
        return result

    def _convert_to_str_recursive(self, value):
        """
        Recursively convert dictionary values to strings.

        Args:
            value: The value to convert.

        Returns:
            Union[str, List[str], Dict[str, str]]: The converted value.
        """
        if isinstance(value, dict):
            return {k: self._convert_to_str_recursive(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._convert_to_str_recursive(v) for v in value]
        elif isinstance(value, int):
            return str(value)
        else:
            return value

    def _validate_ip_port(self, event_id, host, port):
        """
        Validate IP address and port number.

        Args:
            host (str): The IP address to validate.
            port (int): The port number to validate.
        """
        ipv4_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        try:
            if not isinstance(port, int):
                raise ValueError("Port number must be an integer")
            elif port < 0 or port > 65535:
                raise ValueError("Port number out of range")
            elif not ipv4_pattern.match(host): 
                raise ValueError(f"Invalid IP address - {host}")
        except ValueError as error:
            self.logger.warning(f"[RPCTools][_validate_ip_port][{event_id}]> Invalid port number - {port} or IP - {host}: {error}")

    def _handle_custom_error(self, event_id, error):
        """
        Handle custom errors.

        Args:
            error: The error to handle.

        Returns:
            Tuple[int, str, int]: A tuple containing return code, description, and data.
        """
        self.logger.warning(f"[RPCTools][_handle_custom_error][{event_id}]> Custom error occurred: {error}")
        return 2, str(error), 0

    def _handle_unexpected_error(self, event_id, ex):
        """
        Handle unexpected errors.

        Args:
            ex: The unexpected error.

        Returns:
            Tuple[int, str, int]: A tuple containing return code, description, and data.
        """
        self.logger.error(f"[RPCTools][_handle_unexpected_error][{event_id}]> An unexpected error occurred: {ex}")
        return 1, "An unexpected error occurred", 0

