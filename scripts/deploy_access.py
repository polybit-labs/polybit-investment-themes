from brownie import PolybitThemeAccess, network, config
from scripts.utils.polybit_utils import get_account


def deploy_access(account):
    access = PolybitThemeAccess.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    return access


def main(account):
    access = deploy_access(account)
    return access
