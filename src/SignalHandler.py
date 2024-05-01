import signal
import sys

class SignalHandler:
    """Class for handling operating system signals"""

    def __init__(self, logger):
        """
        Initialize SignalHandler with a logger.

        Args:
            logger: Logger object for logging messages.
        """
        self.logger = logger


    def register_signal_handlers(self):
        """Register signal handlers for SIGINT, SIGTERM, SIGHUP, and SIGUSR1."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler_hup)  # Register handler for SIGHUP
        signal.signal(signal.SIGUSR1, self.signal_handler_usr1)  # Register handler for SIGUSR1


    def signal_handler(self, signum, frame):
        """
        Signal handler for SIGINT and SIGTERM.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        self.logger.info(f"[SignalHandler][signal_handler]> Received signal {signum}, shutting down...")
        # Additional actions upon receiving the signal, such as stopping services or saving data
        sys.exit(0)


    def signal_handler_hup(self, signum, frame):
        """
        Signal handler for SIGHUP.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        self.logger.info("[SignalHandler][signal_handler_hup]> Received SIGHUP signal, restarting services...")


    def signal_handler_usr1(self, signum, frame):
        """
        Signal handler for SIGUSR1.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        self.logger.info("[SignalHandler][signal_handler_usr1]> Received SIGUSR1 signal, performing custom action...")
