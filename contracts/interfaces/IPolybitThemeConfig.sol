// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.7;

interface IPolybitThemeConfig {
    function getPolybitRebalancerAddress() external view returns (address);

    function getPolybitSwapRouterAddress() external view returns (address);

    function getPolybitLiquidPathAddress() external view returns (address);

    function getPolybitThemeFactoryAddress() external view returns (address);

    function getThemeProductInfo(
        uint256 _productId
    ) external view returns (string memory, string memory, uint256);

    function getFeeAddress() external view returns (address);

    function getWethAddress() external view returns (address);
}
