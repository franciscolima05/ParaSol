# ParaSol Smart Contracts - Guía de Integración para Frontend (MVP)
Este repositorio contiene los contratos inteligentes de **ParaSol**, el protocolo de seguros paramétricos agrícolas sobre la red Avalanche.

> **Nota para el Frontend (MVP):** Para esta etapa, la interfaz de usuario operará en **modo de solo lectura (Read-Only)**. No es necesario implementar flujos de conexión con MetaMask/Core Wallet ni firmas de transacciones desde el navegador. Todas las consultas se realizan llamando de forma directa a las funciones de lectura (`view`) del contrato a través de un proveedor RPC público.

## Direcciones de los Contratos (Testnet Fuji)

Colocá estas direcciones en las variables de entorno de tu frontend (`.env.local`):

```env
NEXT_PUBLIC_AVALANCHE_FUJI_RPC="https://api.avax-test.network/ext/bc/C/rpc"
NEXT_PUBLIC_POLICY_CONTRACT_ADDRESS="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512" 
NEXT_PUBLIC_POOL_CONTRACT_ADDRESS=""
NEXT_PUBLIC_ENGINE_CONTRACT_ADDRESS=""

```

*Los archivos **ABI (JSON)** necesarios para instanciar los contratos con `ethers.js` o `viem` se encuentran en la carpeta `out/NombrDelContrato.sol/NombreDelContrato.json` después de compilar.*

---

## Diccionario de Consultas para el Frontend

A continuación, se detallan todas las variables, mapeos y funciones públicas que el Frontend puede consultar de forma libre utilizando una instancia básica de lectura.

### 1. Contrato: `ParaSolPolicy.sol` (Pólizas / NFTs)

Este contrato maneja los contratos individuales de los productores en formato ERC721.

#### `getPolicyDetails(uint256 tokenId)`

Devuelve de forma agrupada toda la estructura de datos comerciales y climáticos de una póliza específica .

* **Parámetro de entrada:** `tokenId` (ID de la póliza/NFT).
* 
**Retorno (Objeto / Tupla):** 


* 
`fieldHash` (`string`): Hash identificador del lote o campo (origen satelital).


* 
`poolId` (`uint256`): ID del fondo de liquidez que respalda esta póliza.


* 
`coverageUSDC` (`uint256`): Monto máximo de indemnización que cobrará el productor si se ejecuta el parámetro (Ojo: Viene con los decimales de USDC, generalmente 6 decimales) .


* 
`premiumUSDC` (`uint256`): El precio que pagó el productor por adquirir el seguro .


* 
`startDate` (`uint256`): Timestamp Unix de cuándo arranca la vigencia de la protección .


* 
`endDate` (`uint256`): Timestamp Unix de cuándo finaliza la vigencia .


* 
`triggerSnapshotHash` (`string`): Hash identificador de los metadatos congelados (métrica NDVI inicial, fuentes, severidad).


* 
`isActive` (`bool`): Indica si la póliza está actualmente operativa .





#### `ownerOf(uint256 tokenId)`

Método estándar del estándar ERC721. Devuelve la dirección criptográfica pública del productor dueño de esa póliza.

* **Parámetro de entrada:** `tokenId`.
* **Retorno:** `address` (ej. `0xf39Fd...`).

---

### 2. Contrato: `ParaSolPool.sol` (Fondos de Respaldo)

Maneja los capitales asignados para cubrir los siniestros paramétricos.

#### `pools(uint256 poolId)`

Mapeo público para consultar el estado contable de un fondo de inversión.

* 
**Parámetro de entrada:** `poolId` (ID del pool).


* 
**Retorno (Estructura):** 


* 
`name` (`string`): Nombre descriptivo del pool (ej. "Riesgo Sequía Chaco Q1").


* 
`total_capital` (`uint256`): Todo el capital histórico depositado en el pool (en USDC).


* 
`locked_capital` (`uint256`): Capital actualmente retenido para garantizar pólizas vigentes. No se puede retirar.


* 
`paid_out` (`uint256`): Capital total que ya fue transferido a los agricultores debido a siniestros gatillados.


* 
`isActive` (`bool`): Si el pool acepta nuevas pólizas o fondos.





#### `getAvailableCapital(uint256 poolId)`

Cálculo directo que expone el dinero disponible y "libre" que le queda al pool para suscribir nuevos seguros .

* 
**Parámetro de entrada:** `poolId`.


* 
**Retorno:** `uint256` (Monto neto libre en USDC) .



#### `nextPoolId()`

Contador público incremental. Sirve para saber la cantidad exacta de pools creados en el protocolo (haciendo un bucle desde `0` hasta `nextPoolId - 1` podés listar todos los pools en la UI).

---

### 3. Contrato: `ParaSolEngine.sol` (Oráculo y Lógica de Pagos)

Es el cerebro paramétrico del sistema. Vincula las alertas de Earth Engine con las órdenes de transferencia monetaria.

#### `percentagePaidOut(uint256 policyId)`

Mapeo clave para mostrar la evolución del siniestro en la pantalla del usuario. Como el contrato admite **pagos escalonados progresivos**, este número te dice qué porcentaje total de la póliza ya fue indemnizado .

* 
**Parámetro de entrada:** `policyId` (Token ID del NFT).


* **Retorno:** `uint256` (Un número de 0 a 100).
* 
*Ejemplo:* Si el valor es `40`, significa que el campo ya sufrió un siniestro parcial y cobró el 40% de su cobertura total .





---

## Ejemplo Rápido de Implementación para Manu (Viem / Next.js)

Para leer el estado de una póliza en la UI sin requerir billetera, se configura un cliente público simple:

```typescript
import { createPublicClient, http } from 'viem';
import { avalancheFuji } from 'viem/chains';
import { PARASOL_POLICY_ABI } from '../abis/ParaSolPolicy';

// 1. Instanciar el cliente usando el nodo público de Fuji
const client = createPublicClient({
  chain: avalancheFuji,
  transport: http(process.env.NEXT_PUBLIC_AVALANCHE_FUJI_RPC),
});

// 2. Ejecutar la lectura directa
async function cargarDatosPoliza(id: number) {
  const data = await client.readContract({
    address: process.env.NEXT_PUBLIC_POLICY_CONTRACT_ADDRESS as `0x${string}`,
    abi: PARASOL_POLICY_ABI,
    functionName: 'getPolicyDetails',
    args: [BigInt(id)],
  });
  
  console.log("Campos de la póliza:", data);
  // data devolverá una tupla ordenada: [fieldHash, poolId, coverageUSDC, ...]
}

```

## Historial y Sincronización Real-Time (Eventos)

Si necesitás armar una sección de "Actividad Reciente del Protocolo" en la web, podés usar el cliente para escuchar o pedir los registros históricos (`logs`) de estos eventos fundamentales:

1. 
**`PolicyMinted`** (`ParaSolPolicy`) : Se dispara cuando nace una póliza. Aporta: `tokenId`, `owner`, `coverageUSDC`, y `fieldHash`.


2. 
**`PayoutTriggered`** (`ParaSolEngine`): Ideal para alertas en vivo. Se dispara cuando el backend automatizado liquida fondos. Aporta: `policyId`, `ndviDrop` (caída satelital detectada), `payoutPercent` (tramo pagado), y `amountUSDC` (plata enviada) .


3. 
**`PoolCreated`** (`ParaSolPool`) : Salta al dar de alta un nuevo mercado de cobertura en la plataforma.