// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ParaSolPolicy is ERC721, Ownable {
    uint256 private _nextTokenId;

    struct PolicyData {
        string fieldHash;
        uint256 poolId;            // opcional por el momento
        uint256 coverageUSDC;      // Monto de cobertura en USDC
        uint256 premiumUSDC;           // monto pagado por el seguro en USDC
        uint256 startDate;         // Fecha inicio vigencia
        uint256 endDate;           // Fecha fin
        string triggerSnapshotHash;// El hash del JSONB (peril, fuentes, severidad congelada)
        bool isActive;
    }

    mapping(uint256 => PolicyData) public policies;
    address public minter;

    constructor(address initialOwner) ERC721("ParaSol Policy", "PSP") Ownable(initialOwner) {
    }

    function setMinter(address _minter) external onlyOwner {
        minter = _minter;
    }

    function mintPolicy(
        address to,
        string memory _fieldHash,
        uint256 _poolId,
        uint256 _coverageUSDC,
        uint256 _premiumUSDC,
        uint256 _startDate,
        uint256 _endDate,
        string memory _triggerSnapshotHash
    ) external returns (uint256) {
        require(msg.sender == minter || msg.sender == owner(), "Solo el Backend puede emitir");

        uint256 tokenId = _nextTokenId++;

        _safeMint(to, tokenId);

        policies[tokenId] = PolicyData({
            fieldHash: _fieldHash,
            poolId: _poolId,
            coverageUSDC: _coverageUSDC,
            premiumUSDC: _premiumUSDC,
            startDate: _startDate,
            endDate: _endDate,
            triggerSnapshotHash: _triggerSnapshotHash,
            isActive: true
        });

        return tokenId;
    }
    
    function getPolicyDetails(uint256 tokenId) external view returns (PolicyData memory) {
        require(_ownerOf(tokenId) != address(0), "Poliza no existe");
        return policies[tokenId];
    }
}