// SPDX-License-Identifier: UNLICENSED
pragma solidity >=0.8.7;

import "./PolybitTheme.sol";
import "./interfaces/IPolybitThemeAccess.sol";

/**
 * @title Polybit Investment Theme Factory
 * @author Matt Leeburn
 * @notice A factory to spawn new Investment Theme contracts.
 */

contract PolybitThemeFactory {
    address public polybitThemeAccessAddress;
    IPolybitThemeAccess polybitThemeAccess;
    address public polybitThemeConfigAddress;
    IPolybitThemeConfig polybitThemeConfig;
    address public polybitThemeAddress;
    address[] internal themeAddressList;
    mapping(address => address[]) internal themeAccounts;

    constructor(
        address _polybitThemeAccessAddress,
        address _polybitThemeConfigAddress,
        address _polybitThemeAddress
    ) {
        polybitThemeAccessAddress = _polybitThemeAccessAddress;
        polybitThemeAccess = IPolybitThemeAccess(polybitThemeAccessAddress);
        polybitThemeConfigAddress = _polybitThemeConfigAddress;
        polybitThemeConfig = IPolybitThemeConfig(polybitThemeConfigAddress);
        polybitThemeAddress = _polybitThemeAddress;
    }

    function createClone(
        address implementation
    ) internal returns (address instance) {
        /// @solidity memory-safe-assembly
        assembly {
            // Cleans the upper 96 bits of the `implementation` word, then packs the first 3 bytes
            // of the `implementation` address with the bytecode before the address.
            mstore(
                0x00,
                or(
                    shr(0xe8, shl(0x60, implementation)),
                    0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000
                )
            )
            // Packs the remaining 17 bytes of `implementation` with the bytecode after the address.
            mstore(
                0x20,
                or(shl(0x78, implementation), 0x5af43d82803e903d91602b57fd5bf3)
            )
            instance := create(0, 0x09, 0x37)
        }
        require(instance != address(0), "ERC1167: create failed");
    }

    event ThemeContractCreated(string msg, address ref);

    struct CreateThemeParameters {
        address _walletOwner;
        uint256 _productId;
        uint256 _lockTimestamp;
        PolybitTheme.SwapOrders[] _orderData;
    }

    struct ThemeProductParameters {
        address _themeContractAddress;
        string _productCategory;
        string _productDimension;
    }

    /**
     * @notice Creates a new Investment Theme contract and stores the address in the Factory's list.
     */
    function createThemeContract(
        CreateThemeParameters memory createParams
    ) public payable {
        ThemeProductParameters memory productParams;
        productParams._themeContractAddress = createClone(polybitThemeAddress);
        (
            productParams._productCategory,
            productParams._productDimension,

        ) = polybitThemeConfig.getThemeProductInfo(createParams._productId);

        PolybitTheme(payable(productParams._themeContractAddress)).init{
            value: msg.value
        }(
            polybitThemeAccessAddress,
            polybitThemeConfigAddress,
            createParams._walletOwner,
            address(this),
            createParams._productId,
            productParams._productCategory,
            productParams._productDimension,
            createParams._orderData,
            createParams._lockTimestamp
        );
        themeAddressList.push(address(productParams._themeContractAddress));
        setThemeContracts(
            createParams._walletOwner,
            address(productParams._themeContractAddress)
        );

        emit ThemeContractCreated(
            "New Investment Theme contract created",
            address(productParams._themeContractAddress)
        );
    }

    /**
     * @return themeAddressList is an array of Investment Theme contract addresses.
     */
    function getListOfThemeContracts()
        external
        view
        returns (address[] memory)
    {
        return themeAddressList;
    }

    function setThemeContracts(
        address _walletOwner,
        address _themeAddress
    ) internal {
        themeAccounts[_walletOwner].push(_themeAddress);
    }

    function getThemeContracts(
        address _walletOwner
    ) external view returns (address[] memory) {
        return themeAccounts[_walletOwner];
    }
}
