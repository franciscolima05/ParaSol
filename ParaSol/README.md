# ParaSol

Proyecto para el **Hackathon Avalanche LATAM**.

## Estructura del proyecto

```
ParaSol/
├── contracts/        # Smart contracts (Hardhat + Solidity)
│   ├── contracts/    # Archivos .sol
│   ├── scripts/      # Scripts de deploy
│   ├── test/         # Tests de contratos
│   └── deployments/  # Direcciones desplegadas por red
│
├── frontend/         # dApp (Next.js + TypeScript)
│   ├── public/       # Assets estáticos
│   └── src/
│       ├── app/         # Rutas (App Router)
│       ├── components/  # Componentes React
│       ├── hooks/       # Custom hooks (wagmi, etc.)
│       ├── lib/         # Utilidades (chain config, helpers)
│       ├── abi/         # ABIs generados desde contracts
│       ├── styles/      # Estilos globales
│       └── types/       # Tipos TypeScript
│
├── backend/          # API/servicios off-chain (opcional)
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── middleware/
│   └── tests/
│
├── subgraph/         # The Graph subgraph (indexación)
│
├── docs/             # Documentación
│   ├── diagrams/     # Diagramas de arquitectura
│   └── pitch/        # Material para pitch / demo day
│
├── scripts/          # Scripts útiles del repo
├── assets/           # Logos, screenshots, branding
└── .github/workflows # CI/CD
```

## Networks objetivo

- **Avalanche Fuji** (testnet) — chainId `43113`
- **Avalanche C-Chain** (mainnet) — chainId `43114`

## Quick start

```bash
# Contracts
cd contracts
npm install
npx hardhat compile
npx hardhat test

# Frontend
cd ../frontend
npm install
npm run dev
```

## Equipo

Pancho · [agregar más]

## Licencia

MIT
