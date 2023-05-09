// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.7;

import "./interfaces/IPolybitThemeAccess.sol";

contract PolybitThemeConfig {
    address public polybitAccessAddress;
    IPolybitThemeAccess polybitThemeAccess;
    address internal feeAddress = address(0);
    uint256 internal entryFee = 0;
    address internal polybitRebalancerAddress = address(0);
    address internal polybitSwapRouterAddress = address(0);
    address internal polybitLiquidPathAddress = address(0);
    address internal polybitThemeFactoryAddress = address(0);
    address internal immutable wethAddress;

    constructor(address _polybitAccessAddress, address _wethAddress) {
        polybitAccessAddress = _polybitAccessAddress;
        polybitThemeAccess = IPolybitThemeAccess(polybitAccessAddress);
        wethAddress = _wethAddress;
    }

    modifier onlyPolybitOwner() {
        _checkPolybitOwner();
        _;
    }

    function _checkPolybitOwner() internal view virtual {
        require(
            polybitThemeAccess.polybitOwner() == msg.sender,
            "PolybitThemeConfig: caller is not the owner"
        );
    }

    function setPolybitRebalancerAddress(
        address rebalancerAddress
    ) external onlyPolybitOwner {
        require(address(rebalancerAddress) != address(0));
        polybitRebalancerAddress = rebalancerAddress;
    }

    function getPolybitRebalancerAddress() external view returns (address) {
        return polybitRebalancerAddress;
    }

    function setPolybitSwapRouterAddress(
        address swapRouterAddress
    ) external onlyPolybitOwner {
        require(address(swapRouterAddress) != address(0));
        polybitSwapRouterAddress = swapRouterAddress;
    }

    function getPolybitSwapRouterAddress() external view returns (address) {
        return polybitSwapRouterAddress;
    }

    function setPolybitLiquidPathAddress(
        address liquidPathAddress
    ) external onlyPolybitOwner {
        require(address(liquidPathAddress) != address(0));
        polybitLiquidPathAddress = liquidPathAddress;
    }

    function getPolybitLiquidPathAddress() external view returns (address) {
        return polybitLiquidPathAddress;
    }

    function setPolybitThemeFactoryAddress(
        address themeFactoryAddress
    ) external onlyPolybitOwner {
        require(address(themeFactoryAddress) != address(0));
        polybitThemeFactoryAddress = themeFactoryAddress;
    }

    function getPolybitThemeFactoryAddress() external view returns (address) {
        return polybitThemeFactoryAddress;
    }

    struct ThemeProductParameters {
        uint256 productId;
        string category;
        string dimension;
        uint256 entryFee;
    }

    mapping(uint256 => string) internal productCategory;
    mapping(uint256 => string) internal productDimension;
    mapping(uint256 => uint256) internal productEntryFee;

    ThemeProductParameters[] Themes;

    function createInvestmentTheme(
        uint256 _productId,
        string memory _category,
        string memory _dimension,
        uint256 _entryFee
    ) external onlyPolybitOwner {
        ThemeProductParameters memory Theme = ThemeProductParameters(
            _productId,
            _category,
            _dimension,
            _entryFee
        );
        Themes.push(Theme);
        productCategory[_productId] = _category;
        productDimension[_productId] = _dimension;
        productEntryFee[_productId] = _entryFee;
    }

    function getThemeProductInfo(
        uint256 _productId
    ) external view returns (string memory, string memory, uint256) {
        return (
            productCategory[_productId],
            productDimension[_productId],
            productEntryFee[_productId]
        );
    }

    event FeeSetter(string message, address newFeeAddress);

    function setFeeAddress(address _feeAddress) external onlyPolybitOwner {
        require(
            _feeAddress != address(0),
            ("PolybitThemeConfig: FEE_ADDRESS_INVALID")
        );
        emit FeeSetter("Fee Address changed", _feeAddress);
        feeAddress = _feeAddress;
    }

    function getFeeAddress() external view returns (address) {
        return feeAddress;
    }

    function getWethAddress() external view returns (address) {
        return wethAddress;
    }
}
