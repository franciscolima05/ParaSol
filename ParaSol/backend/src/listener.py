import asyncio
from web3 import AsyncWeb3 #pip install web3
from web3.providers import AsyncHTTPProvider

# Configuración de Entorno reales
RPC_URL = "https://api.avax-test.network/ext/bc/C/rpc" 
CONTRACT_ADDRESS = "0xd5EE5028332cF8Bf20cdE0eF914268E98a3517c4"

# Mini-ABI: no necesita meter todo el JSON gigante, con pasarle la estructura 
# del evento y de la función de consulta ya puede operar este módulo.
CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "poolId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "coverageUSDC", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "startDate", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "endDate", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "fieldHash", "type": "string"}
        ],
        "name": "PolicyMinted",
        "type": "event"
    }
]

async def save_to_database(policy_data):
    """
    Acá adentro Manu tiene que meter su lógica de base de datos (SQLAlchemy, Tortoise, etc.)
    """
    print(f" [DB] Guardando Póliza #{policy_data['token_id']} en la Base de Datos...")
    # Ejemplo simulado de inserción asíncrona:
    # await db.execute("INSERT INTO policies ... VALUES (...)", policy_data)
    await asyncio.sleep(0.5) 
    print(f" [DB] Póliza #{policy_data['token_id']} sincronizada con éxito.")


async def handle_policy_minted_event(event):
    """
    Desempaqueta los datos que viajan en el evento de la Blockchain
    """
    args = event['args']
    
    policy_data = {
        "token_id": args['tokenId'],
        "owner_address": args['owner'],
        "pool_id": args['poolId'],
        "coverage_usdc": args['coverageUSDC'],
        "start_date": args['startDate'],
        "end_date": args['endDate'],    
        "field_hash": args['fieldHash']
    }
    
    print(f"\n ¡Nueva póliza detectada en Avalanche!")
    print(f"   • Token ID: {policy_data['token_id']}")
    print(f"   • Productor: {policy_data['owner_address']}")
    print(f"   • Cobertura: {policy_data['coverage_usdc']} USDC")
    
    # Mandamos a guardar en la DB de forma asíncrona para no bloquear el hilo principal
    await save_to_database(policy_data)


async def main():
    # Inicializamos la conexión asíncrona a Avalanche Fuji
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    
    # Verificamos conexión
    if await w3.is_connected():
        print(f" Conectado con éxito a Avalanche Fuji RPC")
    else:
        print(" Error de conexión al nodo RPC")
        return

    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    
    # arrancamos a escuchar desde el bloque actual de la red al momento de encender el script.
    last_checked_block = await w3.eth.block_number
    print(f"Buscando eventos PolicyMinted desde el bloque {last_checked_block}...")

    while True:
        try:
            current_block = await w3.eth.block_number
            
            # Si la blockchain avanzó, revisamos los bloques nuevos
            if current_block > last_checked_block:
                from_block = last_checked_block + 1
                to_block = current_block
                
                # Buscamos de forma asíncrona los logs del evento específico
                events = await contract.events.PolicyMinted.get_logs(
                    from_block=from_block,
                    to_block=to_block
                )
                
                for event in events:
                    await handle_policy_minted_event(event)
                
                # Actualizamos el puntero del último bloque revisado
                last_checked_block = current_block
                
        except Exception as e:
            print(f" Error en el loop de lectura: {e}")
            
        # Esperamos 4 segundos antes de volver a consultar si hay bloques nuevos (frecuencia de Avalanche)
        await asyncio.sleep(4)

if __name__ == "__main__":
    # Arrancamos el loop asíncrono principal
    asyncio.run(main())