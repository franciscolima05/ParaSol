 // LÓGICA DE DATOS (HARDCODED PARA MVP)
        function loadPolicyView(tokenId = 1042) {
            const policy = {
                fieldHash: "0x772a84b1c16d9e8b3f1e4d2c5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b",
                poolId: 1,
                coverageUSDC: 5000000000, 
                premiumUSDC: 450000000,   
                startDate: 1709251200,    
                endDate: 1735603200,      
                triggerSnapshotHash: "0x5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b",
                isActive: true,
                payoutPct: 40
            };

            const pool = {
                name: "Riesgo Hídrico Pampa Q1",
                total_capital: 250000000000,
                locked_capital: 84200000000,
                paid_out: 12500000000
            };

            const formatUSDC = (val) => (val / 1000000).toLocaleString('en-US', { minimumFractionDigits: 2 });
            const formatDate = (ts) => {
                const d = new Date(ts * 1000);
                const m = ["MAR", "DIC"]; // Simplificado para el ejemplo
                return `${d.getDate().toString().padStart(2, '0')} ${ts === 1709251200 ? 'MAR' : 'DIC'} ${d.getFullYear()}`;
            };

            document.getElementById('policy-coverage').innerText = formatUSDC(policy.coverageUSDC);
            document.getElementById('policy-premium').innerText = formatUSDC(policy.premiumUSDC);
            document.getElementById('policy-snapshot-hash').innerText = policy.triggerSnapshotHash;
            document.getElementById('policy-field-hash').innerText = policy.fieldHash;
            document.getElementById('policy-payout-pct').innerText = `${policy.payoutPct}%`;
            document.getElementById('policy-payout-bar').style.width = `${policy.payoutPct}%`;
            
            document.getElementById('pool-name').innerText = pool.name;
            document.getElementById('pool-available').innerText = formatUSDC(pool.total_capital - pool.locked_capital);
            document.getElementById('pool-locked').innerText = formatUSDC(pool.locked_capital).split('.')[0];
            document.getElementById('pool-paid').innerText = formatUSDC(pool.paid_out).split('.')[0];
        }

        // Ejecutar carga inicial
        window.onload = () => loadPolicyView();