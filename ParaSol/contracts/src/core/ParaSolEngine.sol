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
}