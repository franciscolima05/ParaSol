// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract ParaSolPolicy is ERC721, AccessControl{
    uint256 private _nextTokenId;
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    struct PolicyData {
        string fieldHash;
        uint256 poolId;            // opcional por el momento
        uint256 coverageUSDC;      // Monto de cobertura en USDC
        uint256 premiumUSDC;       // monto pagado por el seguro en USDC
        uint256 startDate;         // Fecha inicio vigencia
        uint256 endDate;           // Fecha fin
        string triggerSnapshotHash;// El hash del JSONB (peril, fuentes, severidad congelada)
        bool isActive;
    }

    mapping(uint256 => PolicyData) public policies;
    event PolicyMinted(
        uint256 indexed tokenId,
        address indexed owner,
        uint256 poolId,
        uint256 coverageUSDC,
        uint256 startDate,
        uint256 endDate,
        string fieldHash
    );

    constructor(address initialAdmin) ERC721("ParaSol Policy", "PSP") {
        _grantRole(DEFAULT_ADMIN_ROLE, initialAdmin);
        _grantRole(ADMIN_ROLE, initialAdmin);
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
    ) external onlyRole(MINTER_ROLE) returns (uint256) {
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
        emit PolicyMinted(tokenId, to, _poolId, _coverageUSDC, _startDate, _endDate, _fieldHash);
        return tokenId;
    }
    
    function getPolicyDetails(uint256 tokenId) external view returns (PolicyData memory) {
        require(_ownerOf(tokenId) != address(0), "Poliza no existe");
        return policies[tokenId];
    }
    //override de openzeppelin para conflictos de libreria ERC165
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}