// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.7;

import "./interfaces/IPolybitThemeConfig.sol";
import "./interfaces/IPolybitTheme.sol";
import "./interfaces/IPolybitThemeFactory.sol";

contract PolybitThemeMulticall {
    address public polybitThemeConfigAddress;
    IPolybitThemeConfig polybitThemeConfig;

    constructor(address _polybitThemeConfigAddress) {
        polybitThemeConfigAddress = _polybitThemeConfigAddress;
        polybitThemeConfig = IPolybitThemeConfig(polybitThemeConfigAddress);
    }

    function getAllTokenBalancesInWeth(
        address _themeContractAddress,
        address[] memory _tokenAddresses,
        uint256[] memory _tokenPrices
    ) public view returns (uint256[] memory) {
        require(
            _tokenAddresses.length == _tokenPrices.length,
            "Token address length does not match token price lenth"
        );

        uint256[] memory tokenBalancesInWeth = new uint256[](
            _tokenAddresses.length
        );
        uint8 listIndex = 0;

        for (uint256 i = 0; i < _tokenAddresses.length; i++) {
            (, uint256 tokenBalanceInWeth) = IPolybitTheme(
                _themeContractAddress
            ).getTokenBalance(_tokenAddresses[i], _tokenPrices[i]);
            tokenBalancesInWeth[listIndex] = tokenBalanceInWeth;
            listIndex++;
        }
        return tokenBalancesInWeth;
    }

    struct ThemeContractDetail {
        address themeContractAddress;
        uint256 status;
        uint256 creationTimestamp;
        string productCategory;
        string productDimension;
        uint256[][] deposits;
        uint256 totalDeposited;
        uint256[][] feesPaid;
        address[] ownedAssets;
        uint256 timeLock;
        uint256 timeLockRemaining;
        uint256 closeTimestamp;
        uint256 finalBalanceInWeth;
        address[] finalAssets;
        uint256[] finalAssetsPrices;
        uint256[] finalAssetsBalances;
        uint256[] finalAssetsBalancesInWeth;
    }

    function getAccountDetail(
        address _themeContractAddress
    ) public view returns (ThemeContractDetail memory) {
        ThemeContractDetail memory data;
        data.themeContractAddress = _themeContractAddress;
        data.status = IPolybitTheme(_themeContractAddress).getStatus();
        data.deposits = IPolybitTheme(_themeContractAddress).getDeposits();
        data.creationTimestamp = IPolybitTheme(_themeContractAddress)
            .getCreationTimestamp();
        data.productCategory = IPolybitTheme(_themeContractAddress)
            .getProductCategory();
        data.productDimension = IPolybitTheme(_themeContractAddress)
            .getProductDimension();
        data.totalDeposited = 0;
        data.feesPaid;
        data.ownedAssets;
        data.timeLock = 0;
        data.timeLockRemaining = 0;
        data.closeTimestamp = 0;
        data.finalBalanceInWeth = 0;
        data.finalAssets;
        data.finalAssetsPrices;
        data.finalAssetsBalances;
        data.finalAssetsBalancesInWeth;

        // If Theme contract is active and has more than one deposit
        if (data.status == 1 && data.deposits.length > 0) {
            data.totalDeposited = IPolybitTheme(_themeContractAddress)
                .getTotalDeposited();
            data.feesPaid = IPolybitTheme(_themeContractAddress).getFeesPaid();
            data.ownedAssets = IPolybitTheme(_themeContractAddress)
                .getOwnedAssets();
            data.timeLock = IPolybitTheme(_themeContractAddress).getTimeLock();
            data.timeLockRemaining = IPolybitTheme(_themeContractAddress)
                .getTimeLockRemaining();
        }

        // If Theme contract is inactive and has more than one deposit
        if (data.status == 0 && data.deposits.length > 0) {
            data.totalDeposited = IPolybitTheme(_themeContractAddress)
                .getTotalDeposited();
            data.feesPaid = IPolybitTheme(_themeContractAddress).getFeesPaid();
            data.closeTimestamp = IPolybitTheme(_themeContractAddress)
                .getCloseTimestamp();
            data.finalBalanceInWeth = IPolybitTheme(_themeContractAddress)
                .getFinalBalance();
            (
                data.finalAssets,
                data.finalAssetsPrices,
                data.finalAssetsBalances,
                data.finalAssetsBalancesInWeth
            ) = IPolybitTheme(_themeContractAddress).getFinalAssets();
        }
        return data;
    }

    struct ThemeContractDetailAll {
        ThemeContractDetail data;
    }

    function getAccountDetailAll(
        address[] memory _themeContractAddresses
    ) public view returns (ThemeContractDetailAll[] memory) {
        ThemeContractDetailAll[]
            memory themeContractDetailAll = new ThemeContractDetailAll[](
                _themeContractAddresses.length
            );
        uint8 listIndex = 0;

        for (uint256 i = 0; i < _themeContractAddresses.length; i++) {
            ThemeContractDetail memory themeContractDetail = getAccountDetail(
                _themeContractAddresses[i]
            );
            themeContractDetailAll[listIndex].data = themeContractDetail;
            listIndex++;
        }
        return themeContractDetailAll;
    }

    function getAccountDetailFromWalletOwner(
        address _walletOwner
    ) public view returns (ThemeContractDetailAll[] memory) {
        address polybitThemeFactoryAddress = polybitThemeConfig
            .getPolybitThemeFactoryAddress();
        address[] memory themeContracts = IPolybitThemeFactory(
            polybitThemeFactoryAddress
        ).getThemeContracts(_walletOwner);
        ThemeContractDetailAll[]
            memory themeContractDetailAll = getAccountDetailAll(themeContracts);
        return themeContractDetailAll;
    }
}
