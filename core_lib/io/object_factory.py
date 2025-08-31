"""
A generic factory for instantiating objects from configuration dictionaries.
"""
import importlib
import inspect
import logging

class ObjectFactory:
    def __init__(self, context: dict = None, class_map: dict = None):
        """
        Initializes the factory.
        Args:
            context: A dictionary of globally available objects for dependency injection.
            class_map: A dictionary mapping short names to full class paths.
        """
        self.context = context or {}
        self.class_map = class_map or {}
        logging.info(f"ObjectFactory initialized with class map: {self.class_map.keys()}")

    def create(self, config: dict, **additional_dependencies):
        """
        Creates an object from a configuration dictionary.
        """
        if 'class' not in config:
            raise ValueError("Configuration must contain a 'class' key.")

        class_path = config.pop('class')
        ObjectClass = self._get_class(class_path)

        # Prepare constructor arguments
        if 'config' in config:
            args = config['config'].copy()
        else:
            args = config.copy()

        # Inject dependencies from the context
        for key, value in self.context.items():
            args.setdefault(key, value)

        # Inject any additional dependencies passed to this method
        for key, value in additional_dependencies.items():
            args.setdefault(key, value)

        # Recursively create nested objects
        for key, value in args.items():
            if isinstance(value, dict) and 'class' in value:
                args[key] = self.create(value)

        # Filter args to match constructor signature
        sig = inspect.signature(ObjectClass.__init__)
        has_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
        if not has_kwargs:
            valid_args = {p for p in sig.parameters if p != 'self'}
            args = {k: v for k, v in args.items() if k in valid_args}

        return ObjectClass(**args)

    def _get_class(self, class_path: str):
        """
        Dynamically imports and returns a class object from a string path.
        """
        full_class_path = self.class_map.get(class_path, class_path)
        try:
            module_name, class_name = full_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Could not find or import class '{class_path}' (resolved to '{full_class_path}')") from e
