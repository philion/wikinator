import importlib

import confuse
import yaml
import os


__app_name__ = "wikinator"
__app_version__ = importlib.metadata.version(__app_name__)

__config__ = confuse.Configuration(__app_name__, __name__)


class AppConfig:
    def __init__(self):
        self._config = self._load()


    def config_dir(self):
        from .gdrive import config_link
        return __config__.config_dir(), config_link


    def _load(self):
        cdir, _ = self.config_dir()
        template = {
            "db_url": f"Configure db_url in ${cdir}",
            "db_token": f"Configure db_token in ${cdir}",
            "log_level": "warning",
        }
        __config__.set_env()
        config = __config__.get(template)
        config['app_info'] = f"{__app_name__} v{__app_version__}"
        config['config_dir'] = __config__.config_dir()
        config['config_file'] = os.path.join(__config__.config_dir(), confuse.CONFIG_FILENAME)

        # config["key"].redact = True
        #config.dump(redact=True)
        return config


    def keys(self):
        return self._config.keys()


    def get(self, name:str, default:str = "") -> str:
        return self._config.get(name, default)


    def set(self, name:str, value) -> None:
        self._config[name] = value


    def value(self, name:str, default:str = "") -> str:
        val = self._config.get(name, default)
        if "secret" in name or "token" in name:
            return f"{val[:6]}...{val[-6:]}"
        else:
            return val


    _SKIP_NAMES = ["app_info", "config_dir", "config_file"]
    def write(self):
        # FIXME copy and remove values:   app_info: config_dir: config_file:

        config_filename = os.path.join(__config__.config_dir(), confuse.CONFIG_FILENAME)
        with open(config_filename, "w") as f:
            #yaml.safe_dump(self._config, f) #, default_flow_style=False)
            #f.write(self._config.dump())
            for k, v in self._config.items():
                if k not in self._SKIP_NAMES:
                    f.write(f"{k}: {v}\n")
