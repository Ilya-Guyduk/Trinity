import threading
import time
import xmlrpc.client
import shortuuid
import queue




class RpcScheduler:
    def __init__(self, app_setting: 'AppSetting', setup_nodes, event_queue):
        self.event_queue = event_queue
        self.setup_nodes = setup_nodes
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()

        
    def loop_handler(self):
        self.logger.debug("[RpcScheduler][loop_handler]> Starting RPC loop handler...")
        while True:
            node_ret_code, nodes = self.setup_nodes.load_json_nodes_config("nodes")
            if int(node_ret_code) != 0:
                self.logger.error(f"[RpcScheduler][loop_handler]>{nodes}")
                break

            self.status_node_check(nodes)
            
            try:
                # Извлечь событие из очереди без блокировки
                event = self.event_queue.get_nowait()
                # Обработать событие
                print("Handling event:", event)
            except queue.Empty:
                # Если очередь пуста, продолжить выполнение основного цикла
                pass


    def send_reg_for_node(self, host: str, port: int, data, host_id: str) -> None:
        self.logger.info(f"[EventSender][send_Registration][{host_id}]> Registration Event sent!")
        try:
            # Функция для преобразования чисел в строки во всей структуре данных
            def convert_to_str(value):
                if isinstance(value, dict):
                    return {k: convert_to_str(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [convert_to_str(v) for v in value]
                elif isinstance(value, int):
                    return str(value)
                else:
                    return value

            # Преобразование всех чисел в строки в переменной data
            data_str = convert_to_str(data)
            self.logger.debug(f"[EventSender][convert_to_str]> data_str - {data_str}")
            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            res = proxy.remote_registration(data_str)
            self.logger.info(f"[EventSender][send_reg_for_node][{host_id}]> ANSWER: {res}")
            self.setup_nodes.update_node_by_id(host_id, {"active": "registration"})

            if "ACK" in res:
                reg_data = res["ACK"]
                self.setup_nodes.remove_node_from_config(host_id)
                self.setup_nodes.add_node_to_config(reg_data)
                self.logger.info(f"[EventSender][send_Registration][{host_id}]> Registration Event response!")
                self.setup_nodes.update_node_by_id(host_id, {"active": "active"})
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Registration][{host_id}] Registration - Connection refused!")
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"[EventSender][send_Registration] Error sending Registration to node {host_id}: {e}")
            time.sleep(7)

    def send_ping_for_node(self, host: str, port: int, host_id: str) -> None:
        self.logger.info(f"[EventSender][send_Ping][{host_id}]> Ping Event sent!")
        try:
            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            res = proxy.ping()
            if res == "Pong":
                self.logger.info(f"[EventSender][send_Ping][{host_id}]> Ping Event response!")
            time.sleep(2)
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Ping][{host_id}] Ping - Connection refused!")
            self.setup_nodes.update_node_by_id(host_id, {"active": "Connection refused"})
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"[EventSender][send_Ping] Error sending Ping to node {host_id}: {e}")
            self.setup_nodes.update_node_by_id(host_id, {"active": "down"})
            time.sleep(10)


    def synchronisation(self, host: str, port: int, host_id: str) -> None:
        def convert_to_str(value):
                if isinstance(value, dict):
                    return {k: convert_to_str(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [convert_to_str(v) for v in value]
                elif isinstance(value, int):
                    return str(value)
                else:
                    return value
        time.sleep(10)
        self.logger.info(f"[EventSender][synchronisation][{host_id}]> Start synchronisation!")
        try:

            proxy = xmlrpc.client.ServerProxy(f'http://{host}:{port}')
            data = self.setup_nodes._load_config()
            data_str = convert_to_str(data)
            res = proxy.synchronis(data_str)
            if res == "Pong":
                self.logger.info(f"[EventSender][send_Ping][{host_id}]> Sync Event response!")
        except ConnectionRefusedError:
            self.logger.error(f"[EventSender][send_Ping][{host_id}] Ping - Connection refused!")
            self.setup_nodes.update_node_by_id(host_id, {"active": "Connection refused"})

        except Exception as e:
            self.logger.error(f"[EventSender][send_Ping] Error sending Ping to node {host_id}: {e}")
            self.setup_nodes.update_node_by_id(host_id, {"active": "down"})







    def status_node_check(self, nodes):
        """Метод проверки статуса и маршрута хоста"""
       
        for node in nodes:
            self.event_id: str = shortuuid.uuid()
            #node_route = node.route
            if node.active == "unknown" or node.active == "registration":

                self.logger.warning(f"[EventSender][status_node_check][{node.id}]> Node has status {node.active}!")
                self.logger.info(f"[EventSender][status_node_check][{node.id}]> The registration process has begun!")
                
                self.ret_code, self.self_data = self.setup_nodes.just_load_json(self.event_id, "self", "full")
                if int(self.ret_code) != 0:
                    self.logger.error(f"[RpcScheduler]> Error load_json_nodes_config: {self.self_data}")    
                
                data = {"REG": self.self_data[0]}
                
                heartbeat_thread = threading.Thread(target=self.send_reg_for_node, args=(node.host, node.port, data, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

            elif node.active == "active" or node.active == "down" or node.active == "Connection refused":
                #sync_thread = threading.Thread(target=self.synchronisation, args=(node.host, node.port, node.id))
                #sync_thread.start()
                #sync_thread.join()

                heartbeat_thread = threading.Thread(target=self.send_ping_for_node, args=(node.host, node.port, node.id))
                heartbeat_thread.start()
                heartbeat_thread.join()

                



            elif node.active == "disable":
                pass
            else:
                self.logger.warning(f"[EventSender][status_node_check][{node.id}]> Unknown 'active' parameter: {node.active}!")



