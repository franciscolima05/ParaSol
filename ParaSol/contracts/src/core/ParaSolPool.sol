// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract ParaSolPool is AccessControl{
    IERC20 public usdcToken;
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant ENGINE_ROLE = keccak256("ENGINE_ROLE");
    struct PoolData {
        string name;
        uint256 total_capital;
        uint256 locked_capital;
        uint256 paid_out;
        bool isActive;
    }

    mapping(uint256 => PoolData) public pools;
    uint256 public nextPoolId;

    event PoolCreated(uint256 indexed poolId, string name);
    event CapitalAdded(uint256 indexed poolId, uint256 amount);
    event CapitalLocked(uint256 indexed poolId, uint256 amount);
    event PayoutExecuted(uint256 indexed poolId, address to, uint256 amount);

    constructor(address _usdcAddress, address initialAdmin) {
        usdcToken = IERC20(_usdcAddress);
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(ADMIN_ROLE, initialAdmin);
    }

    //
    function createPool(string memory _name) external onlyRole(ADMIN_ROLE) returns (uint256) {
        uint256 poolId = nextPoolId++;
        pools[poolId] = PoolData({
            name: _name,
            total_capital: 0,
            locked_capital: 0,
            paid_out: 0,
            isActive: true
        });
        emit PoolCreated(poolId, _name);
        return poolId;
    }

    function fundPool(uint256 poolId, uint256 amount) external {
        require(pools[poolId].isActive, "Pool inactivo");
        require(usdcToken.transferFrom(msg.sender, address(this), amount), "Fallo deposito USDC");
        pools[poolId].total_capital += amount;
        emit CapitalAdded(poolId, amount);
    }

    function lockCapital(uint256 poolId, uint256 amount) external {
        require(hasRole(ENGINE_ROLE, msg.sender) || hasRole(ADMIN_ROLE, msg.sender), "No autorizado");
        require(pools[poolId].isActive, "Pool inactivo");
        
        uint256 available = pools[poolId].total_capital - pools[poolId].locked_capital;
        require(available >= amount, "Capital insuficiente en el Pool");

        pools[poolId].locked_capital += amount;
        emit CapitalLocked(poolId, amount);
    }

    //el pago escalonado lo defino en el core principal
    function executePayout(uint256 poolId, address farmerAddress, uint256 payoutAmount) external onlyRole(ENGINE_ROLE) {
        PoolData storage pool = pools[poolId];
        require(pool.isActive, "Pool inactivo");
        require(pool.locked_capital >= payoutAmount, "El Payout supero el capital bloqueado");
        pool.locked_capital -= payoutAmount;
        pool.total_capital -= payoutAmount;
        pool.paid_out += payoutAmount;

        require(usdcToken.transfer(farmerAddress, payoutAmount), "Fallo transferencia de payout");

        emit PayoutExecuted(poolId, farmerAddress, payoutAmount);
    }
    
    //fondos disponibles en el pool
    function getAvailableCapital(uint256 poolId) external view returns (uint256) {
        return pools[poolId].total_capital - pools[poolId].locked_capital;
    }
}