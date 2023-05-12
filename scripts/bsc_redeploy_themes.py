from scripts import (
    deploy_access,
    deploy_config,
    deploy_rebalancer,
    deploy_theme,
    deploy_theme_factory,
    deploy_multicall,
)
from scripts.utils.polybit_utils import get_account
from brownie import config, network, Contract, PolybitThemeAccess, PolybitThemeConfig
from pycoingecko import CoinGeckoAPI
from web3 import Web3
import time
import os
from pathlib import Path
import json


def main():
    print(network.show_active())
    polybit_owner_account = get_account(type="polybit_owner")
    rebalancer_account = get_account(type="rebalancer_owner")
    router_account = get_account(type="router_owner")
    non_owner = get_account(type="non_owner")
    wallet_owner = get_account(type="wallet_owner")
    fee_address = get_account(type="polybit_fee_address")
    print("Polybit Owner", polybit_owner_account.address)

    polybit_theme_access_address = "0x6bAF1A9EEd3E824303E085d085a7665551957CF3"
    polybit_theme_access = Contract.from_abi(
        "", polybit_theme_access_address, abi=PolybitThemeAccess.abi
    )

    polybit_theme_config_address = "0xCCc3756F53CECFF9e5EF435dB2b828D371A8A5a4"
    polybit_theme_config = Contract.from_abi(
        "", polybit_theme_config_address, abi=PolybitThemeConfig.abi
    )

    ##
    # Deploy Investment Theme Contract
    ##
    polybit_theme = deploy_theme.main(polybit_owner_account)

    ##
    # Deploy Theme Factory
    ##
    polybit_theme_factory = deploy_theme_factory.main(
        polybit_owner_account,
        polybit_theme_access.address,
        polybit_theme_config.address,
        polybit_theme.address,
    )

    tx = polybit_theme_config.setPolybitThemeFactoryAddress(
        polybit_theme_factory.address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])
    print("Theme Factory Address", polybit_theme_config.getPolybitThemeFactoryAddress())
    print(polybit_theme_factory.address)

    ##
    # Print Contract Info for Export
    ##
    print("theme", polybit_theme.address)
    print("theme_factory", polybit_theme_factory.address)

    print("Theme ABI")
    print(polybit_theme.abi)

    print("Theme Factory ABI")
    print(polybit_theme_factory.abi)
