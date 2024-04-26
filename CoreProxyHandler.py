import configparser
import socket
import threading
import queue
import time

class ProxyThread(threading.Thread):
    """
    Класс для реализации прокси-сервера.
    
    Args:
        config_section (dict): Словарь с параметрами конфигурации прокси.
        queue_lock (threading.Lock): Блокировка для синхронизации доступа к очереди.
        logger (logging.Logger): Логгер для записи информации о работе прокси.
    """
    def __init__(self, config_section, queue_lock, logger):
        super().__init__()
        self.logger = logger
        self.config_section = config_section
        self.queue_lock = queue_lock
        self.input_host = '127.0.0.1'
        self.input_port = int(config_section['proxy_port'])
        self.output_host = config_section['proxy_host']
        self.output_port = int(config_section['proxy_port'])
        self.timeout = int(config_section['timeout'])
        self.timeout_queue = int(config_section['timeout_queue'])
        self.max_queue = int(config_section['max_queue'])
        self.allow_hosts = [host.strip() for host in config_section['allow_hosts'].split(',') if host.strip()]
        self.deny_hosts = [host.strip() for host in config_section['deny_hosts'].split(',') if host.strip()]
        self.input_socket = None
        self.output_socket = None
        self.queue = queue.Queue(self.max_queue)


    def run(self):
        """
        Метод для запуска потока прокси-сервера.
        """
        self.input_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.input_socket.bind((self.output_host, self.output_port))
        self.input_socket.listen(5)
        self.logger.info(f"[ProxyThread][run]> Proxy for {self.input_host}:{self.input_port} <=> {self.output_host}:{self.output_port}")
        
        while True:
            client_socket, client_address = self.input_socket.accept()
            if self.is_allowed(client_address):
                self.queue_lock.acquire()
                if self.queue.qsize() >= self.max_queue:
                    self.queue.get()
                self.queue.put((client_socket, client_address))
                self.queue_lock.release()
            else:
                client_socket.close()


    def is_allowed(self, client_address):
        """
        Метод для проверки, разрешено ли соединение с клиентом.

        Args:
            client_address (tuple): Кортеж, содержащий IP-адрес и порт клиента.

        Returns:
            bool: True, если соединение разрешено, иначе False.
        """
        if self.allow_hosts and client_address[0] not in self.allow_hosts:
            return False
        if self.deny_hosts and client_address[0] in self.deny_hosts:
            return False
        return True


    def process_queue(self):
        """
        Метод для обработки очереди запросов.
        """
        while True:
            if not self.queue.empty():
                self.queue_lock.acquire()
                client_socket, client_address = self.queue.get()
                self.queue_lock.release()
                if self.output_socket is None or self.output_socket.fileno() == -1:
                    self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.output_socket.connect((self.output_host, self.output_port))
                try:
                    data = client_socket.recv(4096)
                    if data:
                        self.logger.info(f"[ProxyThread][process_queue]> Received data from {client_address}: {data.decode()}")
                        self.output_socket.sendall(data)
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                finally:
                    client_socket.close()
            else:
                time.sleep(self.timeout_queue)


class CoreRroxy:
    """Класс для управления прокси-серверами."""
    def __init__(self, app_setting):
        """
        Инициализация класса.

        Args:
            app_setting: Экземпляр класса настроек приложения.
        """
        self.app_setting = app_setting
        self.logger = self.app_setting.get_logger()
        
    def main(self):
        """
        Основной метод для запуска прокси-серверов.
        """
        self.logger.info("[CoreRroxy][main]> Initializing Proxy...")
        queue_lock = threading.Lock()

        proxy_threads = []
        for section in self.app_setting.config.sections():
            # Проверяем, что имя секции содержит хотя бы одну цифру
            if any(char.isdigit() for char in section):
                proxy_thread = ProxyThread(self.app_setting.config[section], queue_lock, self.logger)
                proxy_threads.append(proxy_thread)
                proxy_thread.start()

        for proxy_thread in proxy_threads:
            proxy_thread.process_queue()
