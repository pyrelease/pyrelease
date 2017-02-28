#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
import json
import ast
import yaml

__all__ = ["trabConfig"]
__license__ = 'MIT'
__version__ = '0.4.5'


class trabConfig():
    """A simple config parser with auto-save that supports yaml and json. - MIT Licensed"""

    def __init__(self, path, autosave=False, data="dict"):
        """Loads a config file from ``path``. If ``autosave`` is set to True
        then any changes made to config parameters will be saved to file.

        - NOTE: Not thread-safe

        :param path: the location of the config file
        :param autosave: turns on save after change
        :param data: data to add to the config on start
        """
        self._file_path = path
        self.auto_save = autosave
        self._format = data
        self._config_data = {}
        self._load_cfg()

    def get(self, key, d=None):
        """Return ``key`` from config or ``d``.

        :param key: key to retrieve
        :param d: default value if key is not found
        :return: self.__config_data[key] or None
        """
        return self._config_data.get(key, d)

    def set(self, key, value):
        """Set config ``key`` to ``value``.

        :param key: config parameter to set
        :param value: new config value
        :return: None if successful else ``exception.KeyError``
        """
        if key in self._config_data:
            self._config_data[key] = value
            if not self.auto_save:
                return
            self.save()
        else:
            raise KeyError

    def new(self, key, value):
        """Make a new config value which can be set and saved.

        :param key: config parameter to create
        :param value: new config value
        """
        if key not in self._config_data:
            self._config_data[key] = value
            if not self.auto_save:
                return
            self.save()

    def save(self):
        """Save the config file and any changes you have made to it.

        """
        self._save_cfg()

    def delete(self, key):
        """Delete config setting ``key``.

        :param key: config setting to delete
        """
        self._config_data.pop(key, None)
        if self.auto_save:
            self.save()

    def items(self):
        return self._config_data.items()

    def keys(self):
        return self._config_data.keys()

    def values(self):
        return [self._config_data[key] for key in self._config_data]

    def __contains__(self, item):
        return item in self._config_data

    def __repr__(self):
        return repr(self._config_data)

    def __getitem__(self, item):
        return self._config_data[item]

    def __setitem__(self, key, value):
        self._config_data[key] = value

    def _load_cfg(self):
        formats = {
            "dict": self._load_from_dict,
            "yaml": self._load_from_yaml,
        }
        return formats[self._format]()

    def _save_cfg(self):
        formats = {
            "dict": self._save_to_dict,
            "yaml": self._save_to_yaml,
        }
        formats[self._format]()

    def _load_from_dict(self):
        with open(self._file_path, 'rb') as f:
            try:
                ast.literal_eval(self._read_file())
            except SyntaxError:
                return

    def _load_from_yaml(self):
        with open(self._file_path, 'rb') as f:
            try:
                yaml.safe_load(self._read_file())
            except SyntaxError:
                return

    def _save_to_dict(self):
        self._save_file(json.dumps(self._config_data))

    def _save_to_yaml(self):
        self._save_file(yaml.safe_dump(self._config_data))

    def _read_file(self):
        with open(self._file_path, 'rb') as f:
            return f.read()

    def _save_file(self, data):
        with open(self._file_path, 'wb') as f:
            f.write(data)

    @staticmethod
    def from_yaml(file_path, auto_save=False):
        """Load a config file from yaml.

        ex:
        ```python

            import trabconfig

            config = trabconfig.from_yaml('config.yml')
        ```

        :param file_path: location of yaml config file
        :param auto_save: toggle save on changes
        :return: ``instance.trabConfig``
        """
        return trabConfig(file_path, auto_save, data="yaml")


def main():
    print("In main.")
