from brownie import PolybitThemeFactory, network, config
from scripts.utils.polybit_utils import get_account


def deploy_theme_factory(
    account, polybit_access_address, polybit_config_address, polybit_theme_address
):
    theme_factory = PolybitThemeFactory.deploy(
        polybit_access_address,
        polybit_config_address,
        polybit_theme_address,
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    return theme_factory


def main(
    account, polybit_access_address, polybit_config_address, polybit_theme_address
):
    theme_factory = deploy_theme_factory(
        account, polybit_access_address, polybit_config_address, polybit_theme_address
    )
    return theme_factory
