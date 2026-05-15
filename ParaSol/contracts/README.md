# Contracts

Smart contracts del proyecto ParaSol con Hardhat + Solidity.

## Setup

```bash
npm install
cp ../.env.example ../.env
```

## Comandos

```bash
npx hardhat compile             # Compilar
npx hardhat test                # Tests
npx hardhat node                # Nodo local
npx hardhat run scripts/deploy.ts --network fuji      # Deploy a Fuji
npx hardhat run scripts/deploy.ts --network avalanche # Deploy a mainnet
npx hardhat verify --network fuji <address> <args...> # Verificar en Snowtrace
```
