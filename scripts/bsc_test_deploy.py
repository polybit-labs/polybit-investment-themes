from scripts import (
    deploy_access,
    deploy_config,
    deploy_rebalancer,
    deploy_theme,
    deploy_theme_factory,
    deploy_multicall,
)
from scripts.utils.polybit_utils import get_account
from brownie import config, network, Contract
from pycoingecko import CoinGeckoAPI
from web3 import Web3
import time
import os
from pathlib import Path
import json

cg = CoinGeckoAPI(api_key=config["data_providers"]["coingecko"])

BNBUSD = cg.get_coin_by_id("binancecoin")["market_data"]["current_price"]["usd"]
WETH = config["networks"]["bsc-main"]["weth_address"]

TEST_ONE_ASSETS = [
    "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    "0xBf5140A22578168FD562DCcF235E5D43A02ce9B1",
    "0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F",
    "0xac51066d7bec65dc4589368da368b212745d63e8",
]

TEST_ONE_WEIGHTS = [
    10**8 * (1 / 4),
    10**8 * (1 / 4),
    10**8 * (1 / 4),
    10**8 * (1 / 4),
]

""" TEST_ONE_ASSETS = [
    "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    "0xBf5140A22578168FD562DCcF235E5D43A02ce9B1",
    "0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F",
]

TEST_ONE_WEIGHTS = [
    10**8 * (1 / 3),
    10**8 * (1 / 3),
    10**8 * (1 / 3),
] """

TEST_TWO_ASSETS = [
    "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    # "0xBf5140A22578168FD562DCcF235E5D43A02ce9B1",
    "0xac51066d7bec65dc4589368da368b212745d63e8",
    "0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F",
]

TEST_TWO_WEIGHTS = [
    10**8 * (1 / 3),
    10**8 * (1 / 3),
    10**8 * (1 / 3),
]

TEST_THREE_ASSETS = [
    "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    "0xBf5140A22578168FD562DCcF235E5D43A02ce9B1",
    "0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F",
    "0xac51066d7bec65dc4589368da368b212745d63e8",
]

TEST_THREE_WEIGHTS = [
    10**8 * (0.0052),
    10**8 * (0.0144),
    10**8 * (0.313),
    10**8 * (0.6674),
]


def get_coingecko_price(token_address):
    token_price = 0
    while token_price > 0:
        try:
            token_price = cg.get_coin_info_from_contract_address_by_id(
                id="binance-smart-chain",
                contract_address=token_address,
            )["market_data"]["current_price"]["bnb"]
        except:
            print(token_address, "failed first CG attempt.")

        if token_price == 0:
            # Sometimes CG stores addresses in lowercase
            try:
                token_price = cg.get_coin_info_from_contract_address_by_id(
                    id="binance-smart-chain",
                    contract_address=token_address.lower(),
                )["market_data"]["current_price"]["bnb"]
            except:
                print(token_address, "failed to get price from CG.")
    return int(token_price * 10**18)


def first_deposit_combo_order_data(
    rebalancer,
    polybit_liquid_path,
    owned_assets,
    target_assets,
    target_assets_weights,
    target_assets_prices,
    weth_input_amount,
):
    start = time.time()
    (buyList, buyListWeights, buyListPrices) = rebalancer.createBuyList(
        owned_assets, target_assets, target_assets_weights, target_assets_prices
    )
    print("Buy List", buyList)
    print("Buy List Weights", buyListWeights)
    print("Buy List Prices", buyListPrices)

    wethBalance = int(weth_input_amount)

    # Begin buy orders
    totalTargetPercentage = 0
    tokenBalances = 0
    totalBalance = 0

    for i in range(0, len(buyList)):
        if buyList[i] != "0x0000000000000000000000000000000000000000":
            targetPercentage = buyListWeights[i]
            totalTargetPercentage += targetPercentage

    buyOrder = [
        [
            [],
            [],
            [],
            [],
        ]
    ]
    if len(buyList) > 0:
        (buyListAmountsIn, buyListAmountsOut) = rebalancer.createBuyOrder(
            buyList, buyListWeights, buyListPrices, wethBalance, totalTargetPercentage
        )

        swap_orders = [[[]]]
        for i in range(0, len(buyList)):
            swap_orders[0][0].append([WETH, buyList[i], buyListAmountsIn[i], 0])
        (factories, paths, amounts) = polybit_liquid_path.getLiquidPaths(swap_orders)

        for i in range(0, len(buyList)):
            if buyList[i] != "0x0000000000000000000000000000000000000000":
                if len(paths[i]) > 0:
                    print(
                        "Buy",
                        factories[i],
                        paths[i],
                        buyListAmountsIn[i],
                        amounts[i],
                    )
                    buyOrder[0][0].append(factories[i])
                    buyOrder[0][1].append(paths[i])
                    buyOrder[0][2].append(buyListAmountsIn[i])
                    buyOrder[0][3].append(amounts[i])

                else:
                    print("PolybitRouter: INSUFFICIENT_TOKEN_LIQUIDITY")

    orderData = [
        [
            [],
            [],
            [
                [
                    [],
                    [],
                    [],
                    [],
                ]
            ],
            [],
            [],
            [],
            [],
            [
                [
                    [],
                    [],
                    [],
                    [],
                ]
            ],
            [],
            [],
            [],
            [
                [
                    [],
                    [],
                    [],
                    [],
                ]
            ],
            buyList,
            buyListWeights,
            buyListPrices,
            buyOrder,
        ]
    ]
    print("Order Data", orderData)
    end = time.time()
    print("First rebalance OrderData time", end - start)
    return orderData


def rebalance(
    account,
    theme,
    polybit_rebalancer,
    polybit_liquid_path,
    owned_assets,
    owned_assets_prices,
    target_assets,
    target_assets_weights,
    target_assets_prices,
):
    start = time.time()
    (sellList, sellListPrices) = polybit_rebalancer.createSellList(
        owned_assets, owned_assets_prices, target_assets
    )
    print("Sell List", sellList)
    print("Sell List Prices", sellListPrices)

    (
        adjustList,
        adjustListWeights,
        adjustListPrices,
    ) = polybit_rebalancer.createAdjustList(
        owned_assets, owned_assets_prices, target_assets, target_assets_weights
    )
    print("Adjust List", adjustList)
    print("Adjust List Weights", adjustListWeights)
    print("Adjust List Prices", adjustListPrices)

    total_balance = theme.getTotalBalanceInWeth(owned_assets_prices)

    (
        adjustToSellList,
        adjustToSellWeights,
        adjustToSellPrices,
    ) = polybit_rebalancer.createAdjustToSellList(
        theme.address,
        total_balance,
        # owned_assets_prices,
        adjustList,
        adjustListWeights,
        adjustListPrices,
    )
    print("Adjust To Sell List", adjustToSellList)
    print("Adjust To Sell List Weights", adjustToSellWeights)
    print("Adjust To Sell List Prices", adjustToSellPrices)

    (
        adjustToBuyList,
        adjustToBuyWeights,
        adjustToBuyPrices,
    ) = polybit_rebalancer.createAdjustToBuyList(
        theme.address,
        total_balance,
        # owned_assets_prices,
        adjustList,
        adjustListWeights,
        adjustListPrices,
    )
    print("Adjust To Buy List", adjustToBuyList)
    print("Adjust To Buy List Weights", adjustToBuyWeights)
    print("Adjust To Buy List Prices", adjustToBuyPrices)

    (buyList, buyListWeights, buyListPrices) = polybit_rebalancer.createBuyList(
        owned_assets, target_assets, target_assets_weights, target_assets_prices
    )
    print("Buy List", buyList)
    print("Buy List Weights", buyListWeights)
    print("Buy List Prices", buyListPrices)

    wethBalance = theme.getWethBalance({"from": account})

    sellOrder = [
        [
            [],
            [],
            [],
            [],
        ]
    ]
    if len(sellList) > 0:
        (sellListAmountsIn, sellListAmountsOut) = polybit_rebalancer.createSellOrder(
            sellList, sellListPrices, theme.address
        )

        swap_orders = [[[]]]
        for i in range(0, len(sellList)):
            swap_orders[0][0].append(
                [
                    sellList[i],
                    WETH,
                    sellListAmountsIn[i],
                    0
                    # sellListAmountsOut[i],
                ]
            )
        (factories, paths, amounts) = polybit_liquid_path.getLiquidPaths(swap_orders)

        for i in range(0, len(sellList)):
            if sellList[i] != "0x0000000000000000000000000000000000000000":
                if len(paths[i]) > 0:
                    print(
                        "Sell",
                        factories[i],
                        paths[i],
                        sellListAmountsIn[i],
                        amounts[i],
                    )
                    sellOrder[0][0].append(factories[i])
                    sellOrder[0][1].append(paths[i])
                    sellOrder[0][2].append(sellListAmountsIn[i])
                    sellOrder[0][3].append(amounts[i])
                    wethBalance = wethBalance + sellListAmountsOut[i]  # simulate SELL
                else:
                    print("PolybitRouter: INSUFFICIENT_TOKEN_LIQUIDITY")

    adjustToSellOrder = [
        [
            [],
            [],
            [],
            [],
        ]
    ]
    if len(adjustToSellList) > 0:
        (
            adjustToSellListAmountsIn,
            adjustToSellListAmountsOut,
        ) = polybit_rebalancer.createAdjustToSellOrder(
            owned_assets_prices,
            adjustToSellList,
            adjustToSellWeights,
            adjustToSellPrices,
            theme.address,
        )

        swap_orders = [[[]]]
        for i in range(0, len(adjustToSellList)):
            swap_orders[0][0].append(
                [
                    adjustToSellList[i],
                    WETH,
                    adjustToSellListAmountsIn[i],
                    0
                    # adjustToSellListAmountsOut[i],
                ]
            )
        (factories, paths, amounts) = polybit_liquid_path.getLiquidPaths(swap_orders)

        for i in range(0, len(adjustToSellList)):
            if adjustToSellList[i] != "0x0000000000000000000000000000000000000000":
                if len(paths[i]) > 0:
                    print(
                        "Adjust To Sell",
                        factories[i],
                        paths[i],
                        adjustToSellListAmountsIn[i],
                        amounts,
                    )
                    adjustToSellOrder[0][0].append(factories[i])
                    adjustToSellOrder[0][1].append(paths[i])
                    adjustToSellOrder[0][2].append(adjustToSellListAmountsIn[i])
                    adjustToSellOrder[0][3].append(amounts[i])
                    wethBalance = wethBalance + adjustToSellListAmountsOut[i]
                    # simulate SELL
                else:
                    print("PolybitRouter: INSUFFICIENT_TOKEN_LIQUIDITY")

    # Begin buy orders
    totalTargetPercentage = 0
    tokenBalances = 0
    totalBalance = 0
    if len(adjustList) > 0:
        for i in range(0, len(adjustList)):
            (tokenBalance, tokenBalanceInWeth) = theme.getTokenBalance(
                adjustList[i], adjustListPrices[i]
            )
            tokenBalances = tokenBalances + tokenBalanceInWeth
        totalBalance = tokenBalances + wethBalance

    for i in range(0, len(adjustToBuyList)):
        if adjustToBuyList[i] != "0x0000000000000000000000000000000000000000":
            (tokenBalance, tokenBalanceInWeth) = theme.getTokenBalance(
                adjustToBuyList[i], adjustToBuyPrices[i]
            )
            tokenBalancePercentage = (10**8 * tokenBalanceInWeth) / totalBalance
            targetPercentage = adjustToBuyWeights[i]
            totalTargetPercentage += targetPercentage - tokenBalancePercentage

    for i in range(0, len(buyList)):
        if buyList[i] != "0x0000000000000000000000000000000000000000":
            targetPercentage = buyListWeights[i]
            totalTargetPercentage += targetPercentage

    print("totalTargetPercentage", totalTargetPercentage)

    adjustToBuyOrder = [
        [
            [],
            [],
            [],
            [],
        ]
    ]

    if len(adjustToBuyList) > 0:
        (
            adjustToBuyListAmountsIn,
            adjustToBuyListAmountsOut,
        ) = polybit_rebalancer.createAdjustToBuyOrder(
            totalBalance,
            wethBalance,
            adjustToBuyList,
            adjustToBuyWeights,
            adjustToBuyPrices,
            totalTargetPercentage,
            theme.address,
        )

        swap_orders = [[[]]]
        for i in range(0, len(adjustToBuyList)):
            swap_orders[0][0].append(
                [
                    WETH,
                    adjustToBuyList[i],
                    adjustToBuyListAmountsIn[i],
                    0
                    # adjustToBuyListAmountsOut[i],
                ]
            )
        (factories, paths, amounts) = polybit_liquid_path.getLiquidPaths(swap_orders)

        for i in range(0, len(adjustToBuyList)):
            if adjustToBuyList[i] != "0x0000000000000000000000000000000000000000":
                if len(paths[i]) > 0:
                    print(
                        "Adjust To Buy",
                        factories[i],
                        paths[i],
                        adjustToBuyListAmountsIn[i],
                        amounts[i],
                    )
                    adjustToBuyOrder[0][0].append(factories[i])
                    adjustToBuyOrder[0][1].append(paths[i])
                    adjustToBuyOrder[0][2].append(adjustToBuyListAmountsIn[i])
                    adjustToBuyOrder[0][3].append(amounts[i])

                else:
                    print("PolybitRouter: INSUFFICIENT_TOKEN_LIQUIDITY")

    buyOrder = [
        [
            [],
            [],
            [],
            [],
        ]
    ]
    if len(buyList) > 0:
        (buyListAmountsIn, buyListAmountsOut) = polybit_rebalancer.createBuyOrder(
            buyList, buyListWeights, buyListPrices, wethBalance, totalTargetPercentage
        )

        swap_orders = [[[]]]
        for i in range(0, len(buyList)):
            swap_orders[0][0].append(
                [
                    WETH,
                    buyList[i],
                    buyListAmountsIn[i],
                    0
                    # buyListAmountsOut[i]
                ]
            )
        (factories, paths, amounts) = polybit_liquid_path.getLiquidPaths(swap_orders)

        for i in range(0, len(buyList)):
            if buyList[i] != "0x0000000000000000000000000000000000000000":
                if len(paths[i]) > 0:
                    print(
                        "Buy",
                        factories[i],
                        paths[i],
                        buyListAmountsIn[i],
                        amounts[i],
                    )
                    buyOrder[0][0].append(factories[i])
                    buyOrder[0][1].append(paths[i])
                    buyOrder[0][2].append(buyListAmountsIn[i])
                    buyOrder[0][3].append(amounts[i])

                else:
                    print("PolybitRouter: INSUFFICIENT_TOKEN_LIQUIDITY")

    orderData = [
        [
            sellList,
            sellListPrices,
            sellOrder,
            adjustList,
            adjustListPrices,
            adjustToSellList,
            adjustToSellPrices,
            adjustToSellOrder,
            adjustToBuyList,
            adjustToBuyWeights,
            adjustToBuyPrices,
            adjustToBuyOrder,
            buyList,
            buyListWeights,
            buyListPrices,
            buyOrder,
        ]
    ]
    print("Order Data", orderData)
    end = time.time()
    print("Full rebalance OrderData time", end - start)

    tx = theme.rebalanceThemeContract(
        orderData,
        {"from": account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])


def get_owned_assets(theme):
    owned_assets = theme.getOwnedAssets()
    owned_assets_prices = []
    print("Getting owned asset prices from CoinGecko")

    for i in range(0, len(owned_assets)):
        try:
            owned_assets_prices.append(
                int(
                    cg.get_coin_info_from_contract_address_by_id(
                        id="binance-smart-chain",
                        contract_address=owned_assets[i],
                    )["market_data"]["current_price"]["bnb"]
                    * 10**18
                )
            )
        except:
            owned_assets_prices.append(
                int(
                    cg.get_coin_info_from_contract_address_by_id(
                        id="binance-smart-chain",
                        contract_address=owned_assets[i].lower(),
                    )["market_data"]["current_price"]["bnb"]
                    * 10**18
                )
            )

    return owned_assets, owned_assets_prices


def get_target_assets(target_assets, target_assets_weights):
    target_assets_prices = []
    print("Getting target asset prices from CoinGecko")
    for i in range(0, len(target_assets)):
        try:
            target_assets_prices.append(
                int(
                    cg.get_coin_info_from_contract_address_by_id(
                        id="binance-smart-chain",
                        contract_address=target_assets[i],
                    )["market_data"]["current_price"]["bnb"]
                    * 10**18
                )
            )
        except:
            target_assets_prices.append(
                int(
                    cg.get_coin_info_from_contract_address_by_id(
                        id="binance-smart-chain",
                        contract_address=target_assets[i].lower(),
                    )["market_data"]["current_price"]["bnb"]
                    * 10**18
                )
            )
    return target_assets, target_assets_weights, target_assets_prices


def run_rebalance(
    account, theme, polybit_rebalancer, polybit_liquid_path, assets, weights
):
    (owned_assets, owned_assets_prices) = get_owned_assets(theme)
    (
        target_assets,
        target_assets_weights,
        target_assets_prices,
    ) = get_target_assets(assets, weights)
    print("Owned Assets Before:", owned_assets)
    print("Target Assets Before:", target_assets)

    rebalance(
        account,
        theme,
        polybit_rebalancer,
        polybit_liquid_path,
        owned_assets,
        owned_assets_prices,
        target_assets,
        target_assets_weights,
        target_assets_prices,
    )

    (owned_assets, owned_assets_prices) = get_owned_assets(theme)
    (
        target_assets,
        target_assets_weights,
        target_assets_prices,
    ) = get_target_assets(assets, weights)
    print("Owned Assets After:", owned_assets)
    print("Target Assets After:", target_assets)

    total_balance = theme.getTotalBalanceInWeth(owned_assets_prices)
    print("Total Balance", total_balance)
    print("Total Balance %", round(total_balance / theme.getTotalDeposited(), 4))

    for i in range(0, len(owned_assets)):
        token_balance, token_balance_in_weth = theme.getTokenBalance(
            owned_assets[i], owned_assets_prices[i]
        )
        for x in range(0, len(assets)):
            if owned_assets[i] == assets[x]:
                print(
                    "Address",
                    owned_assets[i],
                    "Target",
                    round(
                        (weights[x] / 10**8),
                        4,
                    ),
                    "Actual",
                    round(token_balance_in_weth / total_balance, 4),
                )


def main():
    print(network.show_active())
    polybit_owner_account = get_account(type="polybit_owner")
    rebalancer_account = get_account(type="rebalancer_owner")
    router_account = get_account(type="router_owner")
    non_owner = get_account(type="non_owner")
    wallet_owner = get_account(type="wallet_owner")
    fee_address = get_account(type="polybit_fee_address")
    print("Polybit Owner", polybit_owner_account.address)

    ##
    # Deploy Polybit Theme Access
    ##
    print("Deploying Theme Access")
    polybit_theme_access = deploy_access.main(polybit_owner_account)

    print("Polybit Owner", polybit_theme_access.polybitOwner())
    print("Rebalancer Owner", polybit_theme_access.rebalancerOwner())

    tx = polybit_theme_access.transferRebalancerOwnership(
        rebalancer_account.address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    print("Polybit Owner", polybit_theme_access.polybitOwner())
    print("Rebalancer Owner", polybit_theme_access.rebalancerOwner())

    ##
    # Deploy Theme Config
    ##
    polybit_theme_config = deploy_config.main(
        polybit_owner_account, polybit_theme_access.address
    )

    tx = polybit_theme_config.setFeeAddress(
        fee_address.address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])
    print("Fee Address", polybit_theme_config.getFeeAddress())

    tx = polybit_theme_config.createInvestmentTheme(
        5610001000,
        "BSC Index Top 10",
        "Market Cap",
        {"from": polybit_owner_account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610001001,
        "BSC Index Top 10",
        "Liquidity",
        {"from": polybit_owner_account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610001002,
        "BSC Index Top 10",
        "Equally Balanced",
        {"from": polybit_owner_account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610011000, "DeFi", "Market Cap", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610011001, "DeFi", "Liquidity", {"from": polybit_owner_account}
    )
    tx.wait(1)

    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610011002, "DeFi", "Equally Balanced", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610021000, "Metaverse", "Market Cap", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610021001, "Metaverse", "Liquidity", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610021002,
        "Metaverse",
        "Equally Balanced",
        {"from": polybit_owner_account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610031000, "Governance", "Market Cap", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610031001, "Governance", "Liquidity", {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    tx = polybit_theme_config.createInvestmentTheme(
        5610031002,
        "Governance",
        "Equally Balanced",
        {"from": polybit_owner_account},
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    print(
        "Test product info call", polybit_theme_config.getThemeProductInfo(5610031002)
    )

    ##
    # Deploy Rebalancer
    ##
    polybit_rebalancer = deploy_rebalancer.main(polybit_owner_account)
    tx = polybit_theme_config.setPolybitRebalancerAddress(
        polybit_rebalancer.address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])
    print("Rebalancer Address", polybit_theme_config.getPolybitRebalancerAddress())

    ##
    # Set Liquid Path address and contract
    ##
    polybit_liquid_path_address = "0x40a961cd0d9896b59635E48fFCAEf6aDD5b7dE79"  # "0x31Fa516E3451944c3707efA963e9ADfC58844d09"  # config["networks"][network.show_active()]["polybit_liquid_path"]
    path = str(Path(os.path.abspath(os.path.dirname(__file__))))
    f = open(path + "/abis/IPolybitLiquidPath.json")
    IPolybitLiquidPath = json.load(f)

    polybit_liquid_path = Contract.from_abi(
        "", polybit_liquid_path_address, IPolybitLiquidPath
    )
    tx = polybit_theme_config.setPolybitLiquidPathAddress(
        polybit_liquid_path_address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])
    print("Liquid Path Address", polybit_theme_config.getPolybitLiquidPathAddress())

    ##
    # Set Swap Router address and contract
    ##
    polybit_swap_router_address = config["networks"][network.show_active()][
        "polybit_swap_router"
    ]

    tx = polybit_theme_config.setPolybitSwapRouterAddress(
        polybit_swap_router_address, {"from": polybit_owner_account}
    )
    tx.wait(1)
    for i in range(0, len(tx.events)):
        print(tx.events[i])
    print("Swap Router Address", polybit_theme_config.getPolybitSwapRouterAddress())

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
    # Deploy Multicall
    ##
    polybit_multicall = deploy_multicall.main(
        polybit_owner_account,
        polybit_theme_config.address,
    )

    """ ##
    # First Establish/Deposit combo
    ##

    product_id = 5610031002
    lock_duration = time.time() + 30 * 86400
    deposit_amount = Web3.toWei(1, "ether")
    owned_assets = []
    (
        target_assets,
        target_assets_weights,
        target_assets_prices,
    ) = get_target_assets(TEST_ONE_ASSETS, TEST_ONE_WEIGHTS)

    order_data = first_deposit_combo_order_data(
        polybit_rebalancer,
        polybit_liquid_path,
        owned_assets,
        target_assets,
        target_assets_weights,
        target_assets_prices,
        deposit_amount,
    )

    tx = polybit_theme_factory.createThemeContract(
        [wallet_owner, product_id, lock_duration, order_data],
        {"from": polybit_owner_account, "value": deposit_amount},
    )
    for i in range(0, len(tx.events)):
        print(tx.events[i])

    theme = Contract.from_abi(
        "", polybit_theme_factory.getListOfThemeContracts()[0], polybit_theme.abi
    )

    ##
    # First rebalance
    ##
    print("REBALANCE #2")
    run_rebalance(
        rebalancer_account,
        theme,
        polybit_rebalancer,
        polybit_liquid_path,
        TEST_TWO_ASSETS,
        TEST_TWO_WEIGHTS,
    )
    print("Deposits", theme.getDeposits())
    print("Total Deposits", theme.getTotalDeposited())

    ##
    # Second rebalance
    ##
    print("REBALANCE #3")
    run_rebalance(
        rebalancer_account,
        theme,
        polybit_rebalancer,
        polybit_liquid_path,
        TEST_THREE_ASSETS,
        TEST_THREE_WEIGHTS,
    )
    print("Deposits", theme.getDeposits())
    print("Total Deposits", theme.getTotalDeposited()) """

    """

    print(
        "multicall - wallet owner",
        polybit_multicall.getAccountDetailFromWalletOwner(wallet_owner),
    )

    ##
    # Report account data with multicall
    ##
    print(
        "Multicall from single DETF",
        polybit_multicall.getAccountDetail(theme.address),
    )

    detf_list = [theme.address, theme.address]
    print(
        "Multicall from list of DETFs",
        polybit_multicall.getAccountDetailAll(detf_list),
    )

    print(
        "Multicall from Wallet Owner",
        polybit_multicall.getAccountDetailFromWalletOwner(wallet_owner.address),
    )

    print("Status", theme.getStatus())

    owned_assets = theme.getOwnedAssets()
    owned_assets_prices = []
    for i in range(0, len(owned_assets)):
        price = int(
            cg.get_coin_info_from_contract_address_by_id(
                id="binance-smart-chain",
                contract_address=owned_assets[i],
            )["market_data"]["current_price"]["bnb"]
            * 10**18
        )
        owned_assets_prices.append(price)
    print("Owned assets", owned_assets)
    print("Owned assets prices", owned_assets_prices)
    print(
        "Get all token balances in weth",
        polybit_multicall.getAllTokenBalancesInWeth(
            theme.address, owned_assets, owned_assets_prices
        ),
    ) """

    ##
    # Print Contract Info for Export
    ##
    # print("router", polybit_swap_router.address)
    print("rebalancer", polybit_rebalancer.address)
    print("theme", polybit_theme.address)
    print("theme_factory", polybit_theme_factory.address)
    print("config", polybit_theme_config.address)
    print("access", polybit_theme_access.address)
    print("multicall", polybit_multicall.address)

    print("Theme ABI")
    print(polybit_theme.abi)

    print("Theme Factory ABI")
    print(polybit_theme_factory.abi)

    print("Rebalancer ABI")
    print(polybit_rebalancer.abi)

    # print("Router ABI")
    # print(polybit_router.abi)

    print("Config ABI")
    print(polybit_theme_config.abi)

    print("Access ABI")
    print(polybit_theme_access.abi)

    print("Multicall ABI")
    print(polybit_multicall.abi)
