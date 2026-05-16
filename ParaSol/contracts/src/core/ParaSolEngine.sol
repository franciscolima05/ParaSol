// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
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

contract ParaSolEngine is Ownable {
    IParaSolPolicy public policyContract;
    IParaSolPool public poolContract;
    
    address public oracle; 

    mapping(uint256 => uint256) public percentagePaidOut;

    event PayoutTriggered(uint256 indexed policyId, uint256 ndviDrop, uint256 payoutPercent, uint256 amountUSDC);

    modifier onlyOracle() {
        require(msg.sender == oracle, "Solo el oraculo (Backend) puede reportar");
        _;
    }

    constructor(address _policyAddress, address _poolAddress, address _oracleAddress, address initialOwner) Ownable(initialOwner) {
        policyContract = IParaSolPolicy(_policyAddress);
        poolContract = IParaSolPool(_poolAddress);
        oracle = _oracleAddress;
    }
    function processParametricEvent(uint256 policyId, uint256 ndviDrop) external onlyOracle {
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