""" Base class for all agents """

import logging
from typing import Optional


class BaseAgent:
    def __init__(self, name: str, version: str = "0.0.1", category: Optional[str] = None, enabled: bool = True):
        """ Initialize BaseAgent

        Args:
            name (str): name of the agent
            version (str, optional): version of the agent. Defaults to "0.0.1".
            category (Optional[str], optional): category of the agent defaults to None.
            enabled (bool, optional): enabled status of the agent. Defaults to True.
        """
        self.name = name
        self.version = version
        self.category = category
        self.enabled = enabled
        self.logger = logging.getLogger(name)

    def analyze(self, *args, **kwargs):
        """ Analyze method to be implemented by subclasses

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError()

    # Lightweight logging helpers used by agents
    def log_info(self, msg: str):
        """ log info message 

        Args:
            msg (str): _description_
        """
        self.logger.info(msg)

    def log_debug(self, msg: str):
        """ log debug message

        Args:
            msg (str): _description_
        """
        self.logger.debug(msg)

    def log_error(self, msg: str):
        """ log error message

        Args:
            msg (str): _description_
        """
        self.logger.error(msg)
