from brownie import PolybitThemeMulticall, network, config
from scripts.utils.polybit_utils import get_account


def deploy_multicall(account, polybit_config_address):
    polybit_multicall = PolybitThemeMulticall.deploy(
        polybit_config_address,
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    return polybit_multicall


def main(account, polybit_config_address):
    polybit_multicall = deploy_multicall(account, polybit_config_address)
    return polybit_multicall
