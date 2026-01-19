from typing import Any

class AttributeSetter:
    @staticmethod
    def set_attributes(obj: Any, config: dict):
        """
        Dynamically set attributes on an object from a configuration dictionary.

        Args:
            obj: The object on which attributes will be set.
            config (dict): Configuration dictionary where keys are attribute names and values are their values.
        """
        for key, value in config.items():
            setattr(obj, key, value)