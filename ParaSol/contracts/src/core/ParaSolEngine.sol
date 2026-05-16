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