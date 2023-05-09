from brownie import PolybitTheme, network, config
from scripts.utils.polybit_utils import get_account


def deploy_theme(account):
    polybit_theme = PolybitTheme.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    return polybit_theme


def main(account):
    polybit_theme = deploy_theme(account)
    return polybit_theme
