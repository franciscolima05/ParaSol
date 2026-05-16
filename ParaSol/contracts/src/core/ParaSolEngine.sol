// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

interface IParaSolPolicy {
    function getPolicyDetails(uint256 tokenId) external view returns (
        string memory fieldHash, uint256 poolId, uint256 coverageUSDC, 
        uint256 premiumUSDC, uint256 startDate, uint256 endDate, 
        string memory triggerSnapshotHash, bool isActive
    );
    function ownerOf(uint256 tokenId) external view returns (address);
}

interface IParaSolPool {
    function executePayout(uint256 poolId, address farmerAddress, uint256 payoutAmount) external;
}
contract ParaSolEngine is AccessControl{
    IParaSolPolicy public policyContract;
    IParaSolPool public poolContract;
    bytes32 public constant DEV_ROLE = keccak256("DEV_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    mapping(uint256 => uint256) public percentagePaidOut;

    event PayoutTriggered(uint256 indexed policyId, uint256 ndviDrop, uint256 payoutPercent, uint256 amountUSDC);

    constructor(address _policyAddress, address _poolAddress, address initialSuperAdmin, address initialDev, address oracleBackend) {
        policyContract = IParaSolPolicy(_policyAddress);
        poolContract = IParaSolPool(_poolAddress);

        _setRoleAdmin(ADMIN_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(DEV_ROLE, DEFAULT_ADMIN_ROLE);
        _setRoleAdmin(ORACLE_ROLE, DEV_ROLE);

        _grantRole(DEFAULT_ADMIN_ROLE, initialSuperAdmin);
        _grantRole(ADMIN_ROLE, initialSuperAdmin);
        _grantRole(DEV_ROLE, initialDev);
        _grantRole(ORACLE_ROLE, oracleBackend);
    }
    function processParametricEvent(uint256 policyId, uint256 ndviDrop) external onlyRole(ORACLE_ROLE) {
        (
            , uint256 poolId, uint256 coverageUSDC, , 
            uint256 startDate, uint256 endDate, , bool isActive
        ) = policyContract.getPolicyDetails(policyId);

        require(isActive, "La poliza no esta activa");
        require(block.timestamp >= startDate && block.timestamp <= endDate, "Fuera de vigencia");
        
        uint256 targetPayoutPercent = (ndviDrop / 5) * 5;
        require(targetPayoutPercent >= 20, "El dano no supera la franquicia minima del 20%");
        if (targetPayoutPercent > 100) { targetPayoutPercent = 100; }

        uint256 alreadyPaidPercent = percentagePaidOut[policyId];
        require(targetPayoutPercent > alreadyPaidPercent, "Este tramo ya fue pagado");

        uint256 percentToPayNow = targetPayoutPercent - alreadyPaidPercent;
        uint256 amountToPayUSDC = (coverageUSDC * percentToPayNow) / 100;

        percentagePaidOut[policyId] = targetPayoutPercent;

        address farmer = policyContract.ownerOf(policyId);
        poolContract.executePayout(poolId, farmer, amountToPayUSDC);

        emit PayoutTriggered(policyId, ndviDrop, percentToPayNow, amountToPayUSDC);
    }
}