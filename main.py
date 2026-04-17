# -*- encoding=utf8 -*-
__author__ = "CYM"

from src.core.app_builder import AppBuilder
from src.core.config_manager import ConfigManager, parse_args
from src.core.service_factory import ServiceFactory


def main():
    args = parse_args()
    config = ConfigManager().load(args)

    services = ServiceFactory(config).build()
    services.device_manager.connect_runtime(__file__)
    services.game_initializer.startup()

    main_loop = AppBuilder(config, services).build_main_loop()
    main_loop.run()


if __name__ == "__main__":
    main()

