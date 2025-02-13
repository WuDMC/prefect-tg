from dotenv import load_dotenv
import os
import yaml
import json


class Config:
    def __init__(self, config_file=None, env_file=None, json_config=None, debug=False):
        """
        Initializes the configuration.

        :param config_file: Path to the YAML configuration file
        :param env_file: Path to the .env file (default: ".env" in the project root)
        :param json_config: JSON dictionary or path to a JSON file (merges with YAML config)
        :param debug: Flag to use the debug configuration
        """

        # Load .env file
        load_dotenv()
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)

        # Select YAML config file
        current_dir = os.path.dirname(__file__)
        default_config_file = os.path.join(
            current_dir, "config_debug.yaml" if debug else "config.yaml"
        )
        self.config_file = config_file if config_file else default_config_file

        # Load configuration (YAML + JSON)
        self.config = self.load_config()
        self.interpolate_config()  # Replace environment variables
        # json config has higher prioritet if exists
        self.merge_json_config(json_config)  # Merge with JSON config

    def load_config(self):
        """Loads the YAML configuration file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                return yaml.safe_load(file) or {}
        else:
            raise FileNotFoundError(f"Configuration file {self.config_file} not found.")

    def merge_json_config(self, json_config):
        """
        Merges YAML configuration with JSON configuration.

        :param json_config: JSON dictionary or path to a JSON file
        """
        if not json_config:
            return

        # Load JSON config as string
        if isinstance(json_config, str):
            json_config = json.loads(json_config)

        # Ensure json_config is a dictionary
        if isinstance(json_config, dict):
            self.config = self.deep_merge(self.config, json_config)
        else:
            raise ValueError("json_config must be a dictionary or a valid JSON str")

    def deep_merge(self, dict1, dict2):
        """
        Deeply merges two dictionaries (YAML + JSON).
        Values from dict2 override those in dict1.
        """
        merged = dict1.copy()
        for key, value in dict2.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self.deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def interpolate_config(self):
        """Replaces environment variables in the configuration."""
        for section, settings in self.config.items():
            for key, value in settings.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    self.config[section][key] = os.getenv(env_var, f"{{MISSING: {env_var}}}")

    def get(self, section, key, default=None):
        """Retrieves a value from the configuration."""
        return self.config.get(section, {}).get(key, default)

    def to_json(self, filepath=None, indent=4):
        """
        Converts the configuration to JSON format.

        :param filepath: If specified, saves JSON to a file
        :param indent: Number of spaces for indentation
        :return: JSON string of the configuration
        """
        json_data = json.dumps(self.config, indent=indent, ensure_ascii=False)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as json_file:
                json_file.write(json_data)
        return json_data
