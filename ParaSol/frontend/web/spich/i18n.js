const translations = {
    en: {
        "nav.satellite": "Satellite Intelligence",
        "nav.contracts": "Parametric Engine",
        "nav.dashboard": "Risk Dashboard",
        "nav.docs": "API Reference",
        "nav.launch": "Access Platform",
        "hero.title": "Empowering Insurers with <span class=\"text-primary-container\">Parametric Intelligence</span>",
        "hero.subtitle": "ParaSol provides insurers with high-fidelity satellite data and blockchain automation to streamline claims, eliminate adjustment costs, and scale climate resilience products.",
        "hero.demo": "Schedule B2B Demo",
        "hero.infra": "Technical Stack",
        "hero.sentinel": "SENTINEL-2: ACTIVE",
        "hero.ndvi": "NDVI Analysis",
        "hero.twi": "TWI Vulnerability",
        "problem.title": "Optimizing the <span class=\"text-primary\">Insurance Value Chain</span>",
        "problem.subtitle": "We help insurers overcome operational bottlenecks by providing deterministic data triggers that replace manual inspections with orbital precision.",
        "problem.bureaucracy.title": "Operational Efficiency",
        "problem.bureaucracy.desc": "We automate administrative workflows to focus resources on underwriting and portfolio growth.",
        "problem.delays.title": "Instant Settlement",
        "problem.delays.desc": "Reduce payout cycles from months to hours, enhancing policyholder trust and retention.",
        "problem.opaque.title": "Deterministic Data",
        "problem.opaque.desc": "Replace subjective assessments with immutable satellite evidence and verifiable climate indices.",
        "problem.errors.title": "Cost Reduction",
        "problem.errors.desc": "Augment field observations with a second layer of satellite-driven insights using continuous remote sensing.",
        "engine.label": "The Intelligence Engine",
        "engine.title": "Multi-Source Orbital Pipeline",
        "engine.ingestion.title": "Satellite Ingestion",
        "engine.ingestion.desc": "Daily multispectral imagery from Sentinel-1 (SAR), Sentinel-2 (CHIRPS and NDVI). ",
        "engine.ndvi.title": "Vegetation Health",
        "engine.climate.title": "Topographic Risk",
        "engine.smart.title": "Automated Payouts",
        "engine.smart.desc": "Secure settlement via Avalanche smart contracts and custom oracles.",
        "integrations.title": "Mission-Critical <span class=\"text-primary\">Integrations</span>",
        "integrations.subtitle": "Our geospatial backend processes petabytes of orbital data to deliver environmental truth directly to your insurance infrastructure.",
        "integrations.telemetry.title": "Sentinel-1 SAR Detection",
        "integrations.telemetry.desc": "Radar-based flood detection that penetrates cloud cover, ensuring 24/7 monitoring of water-logged areas.",
        "integrations.oracles.title": "Custom Risk Models",
        "integrations.oracles.desc": "Proprietary TWI (Topographic Wetness Index) and NDVI time-series to assess damage with sub-meter precision.",
        "audience.title": "Scalable Solutions for <span class=\"text-primary\">Risk Managers</span>",
        "audience.insurers.title": "Reinsurers",
        "audience.insurers.desc": "Access transparent, real-time loss data to optimize capital allocation and risk transfer mechanisms.",
        "audience.farmers.title": "Primary Insurers",
        "audience.farmers.desc": "Launch competitive parametric products with zero loss adjustment expenses (LAE).",
        "audience.landowners.title": "Agro-Corporates",
        "audience.landowners.desc": "Protect large-scale operations with institutional-grade climate hedging and automated recovery.",
        "audience.governments.title": "Public Sector",
        "audience.governments.desc": "Deploy sovereign disaster relief programs with full transparency and zero administrative leakage.",
        "velocity.title": "Settlement <span class=\"text-secondary\">Velocity</span>",
        "velocity.avg": "Avg Settlement",
        "velocity.fee": "Network Fee",
        "velocity.docs": "Developer Documentation",
        "roadmap.title": "The Path Forward",
        "roadmap.p1.title": "Alpha Infrastructure",
        "roadmap.p1.desc": "Full integration of GEE APIs with Avalanche C-Chain testnets for automated indexing.",
        "roadmap.p2.title": "LATAM Pilot Launch",
        "roadmap.p2.desc": "Direct field testing with soy producers in Mato Grosso and Argentina corn belts.",
        "roadmap.p3.title": "Actuarial ML Engine",
        "roadmap.p3.desc": "Deploying dynamic pricing models that adjust premiums based on AI seasonal forecasts.",
        "roadmap.p4.title": "Liquidity Pools",
        "roadmap.p4.desc": "Enabling institutional capital to provide decentralized reinsurance liquidity via vault tokens.",
        "roadmap.p5.title": "African Expansion",
        "roadmap.p5.desc": "Micro-insurance deployment for smallholder farmers in arid East African regions.",
        "roadmap.p6.title": "ParaSol Subnet",
        "roadmap.p6.desc": "Transition to a dedicated Avalanche Subnet for sovereign throughput and compliance.",
        "cta.title": "\"Standardizing the network for the people most committed to our land.\"",
        "cta.subtitle": "The transition from reactive to predictive insurance is here. Join ParaSol in building the climate infrastructure of the future.",
        "cta.button": "See what ParaSol is like",
        "footer.copy": "© 2026 ParaSol. Protecting the future of global agriculture.",
        "footer.tos": "Terms of Service",
        "footer.privacy": "Privacy Policy",
        "footer.risk": "Risk Disclosure",
        "footer.gov": "Governance"
    },
    es: {
        "nav.satellite": "¿Quienes Somos?",
        "nav.contracts": "Nuestro Motor",
        "nav.dashboard": "Gestores de Riesgo",
        "nav.docs": "Nuestro Camino",
        "nav.launch": "Acceder a Plataforma",
        "hero.title": "Potenciando Aseguradoras con <span class=\"text-primary-container\">Inteligencia Paramétrica</span>",
        "hero.subtitle": "ParaSol proporciona a las aseguradoras datos satelitales de alta fidelidad y automatización blockchain para agilizar reclamos, eliminar costos de ajuste y escalar productos de resiliencia climática.",
        "hero.demo": "Agendar Demo B2B",
        "hero.infra": "Stack Técnico",
        "hero.sentinel": "SENTINEL-2: ACTIVO",
        "hero.ndvi": "Análisis NDVI",
        "hero.twi": "Vulnerabilidad TWI",
        "problem.title": "Optimizando la <span class=\"text-primary\">Cadena de Valor del Seguro</span>",
        "problem.subtitle": "Ayudamos a las aseguradoras a superar cuellos de botella operativos mediante disparadores de datos deterministas que reemplazan las inspecciones manuales con precisión orbital.",
        "problem.bureaucracy.title": "Eficiencia Operativa",
        "problem.bureaucracy.desc": "Automatizamos flujos administrativos para centrar recursos en la suscripción y el crecimiento de la cartera.",
        "problem.delays.title": "Liquidación Instantánea",
        "problem.delays.desc": "Reduzca los ciclos de pago de meses a horas, mejorando la confianza y retención del asegurado.",
        "problem.opaque.title": "Datos Deterministas",
        "problem.opaque.desc": "Reemplace evaluaciones subjetivas con evidencia satelital inmutable e índices climáticos verificables.",
        "problem.errors.title": "Reducción de Costos",
        "problem.errors.desc": "Complementa la observación en campo con una segunda mirada satelital basada en teledetección continua.",
        "engine.label": "El Motor de Inteligencia",
        "engine.title": "Pipeline Orbital Multi-Fuente",
        "engine.ingestion.title": "Ingesta Satelital",
        "engine.ingestion.desc": "Imágenes multiespectrales diarias de Sentinel-1 (SAR), Sentinel-2 (CHIRPS y NDVI). ",
        "engine.ndvi.title": "Salud Vegetativa",
        "engine.climate.title": "Riesgo Topográfico",
        "engine.smart.title": "Pagos Automatizados",
        "engine.smart.desc": "Liquidación segura mediante contratos inteligentes de Avalanche y oráculos personalizados.",
        "integrations.title": "Integraciones <span class=\"text-primary\">Críticas</span>",
        "integrations.subtitle": "Nuestro backend geoespacial procesa petabytes de datos orbitales para entregar la verdad ambiental directamente a su infraestructura de seguros.",
        "integrations.telemetry.title": "Detección Sentinel-1 SAR",
        "integrations.telemetry.desc": "Detección de inundaciones basada en radar que penetra la cobertura de nubes, asegurando monitoreo 24/7 de zonas anegadas.",
        "integrations.oracles.title": "Modelos de Riesgo Propios",
        "integrations.oracles.desc": "Series temporales de TWI (Índice de Humedad Topográfica) y NDVI para evaluar daños con precisión sub-métrica.",
        "audience.title": "Soluciones Escalables para <span class=\"text-primary\">Gestores de Riesgo</span>",
        "audience.insurers.title": "Reaseguradoras",
        "audience.insurers.desc": "Acceda a datos de pérdidas transparentes en tiempo real para optimizar la asignación de capital y mecanismos de transferencia de riesgo.",
        "audience.farmers.title": "Aseguradoras Primarias",
        "audience.farmers.desc": "Lance productos paramétricos competitivos con cero gastos de ajuste de pérdidas (LAE).",
        "audience.landowners.title": "Agro-Corporativos",
        "audience.landowners.desc": "Proteja operaciones a gran escala con cobertura climática de grado institucional y recuperación automatizada.",
        "audience.governments.title": "Sector Público",
        "audience.governments.desc": "Despliegue programas soberanos de alivio de desastres con total transparencia y cero fugas administrativas.",
        "velocity.title": "Velocidad de <span class=\"text-secondary\">Liquidación</span>",
        "velocity.avg": "Liquidación Promedio",
        "velocity.fee": "Tarifa de Red",
        "velocity.docs": "Documentación para Desarrolladores",
        "roadmap.title": "El Camino a Seguir",
        "roadmap.p1.title": "Infraestructura Alpha",
        "roadmap.p1.desc": "Integración completa de las API de GEE con las redes de prueba de Avalanche C-Chain para indexación automatizada.",
        "roadmap.p2.title": "Lanzamiento Piloto LATAM",
        "roadmap.p2.desc": "Pruebas de campo directas con productores de soja en Mato Grosso y cinturones de maíz en Argentina.",
        "roadmap.p3.title": "Motor ML Actuarial",
        "roadmap.p3.desc": "Despliegue de modelos de precios dinámicos que ajustan las primas basadas en pronósticos estacionales de IA.",
        "roadmap.p4.title": "Pools de Liquidez",
        "roadmap.p4.desc": "Permitir que el capital institucional proporcione liquidez de reaseguro descentralizada a través de tokens de bóveda.",
        "roadmap.p5.title": "Expansión Africana",
        "roadmap.p5.desc": "Despliegue de microseguros para pequeños agricultores en regiones áridas de África Oriental.",
        "roadmap.p6.title": "Subred ParaSol",
        "roadmap.p6.desc": "Transición a una subred dedicada de Avalanche para rendimiento soberano y cumplimiento.",
        "cta.title": "\"Estandarizando la red para las personas mas comprometidas con nuestro suelo.\"",
        "cta.subtitle": "La transición del seguro reactivo al predictivo está aquí. Únase a ParaSol en la construcción de la infraestructura climática del futuro.",
        "cta.button": "Vea como es ParaSol",
        "footer.copy": "© 2026 ParaSol. Protegiendo el futuro de la agricultura global.",
        "footer.tos": "Términos de Servicio",
        "footer.privacy": "Política de Privacidad",
        "footer.risk": "Divulgación de Riesgos",
        "footer.gov": "Gobernanza"
    }
};

function setLanguage(lang) {
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });

    localStorage.setItem("lang", lang);
    updateToggleButton(lang);
    document.documentElement.lang = lang;
}

function updateToggleButton(lang) {
    const btn = document.getElementById("lang-toggle");
    if (btn) {
        // Si el idioma actual es español, el botón debe invitar a cambiar a inglés
        btn.textContent = lang === "es" ? "EN / ES" : "ES / EN";
    }
}

function toggleLanguage() {
    const currentLang = localStorage.getItem("lang") || "es";
    const newLang = currentLang === "es" ? "en" : "es";
    setLanguage(newLang);
}
const links = document.querySelectorAll(".nav-link");

links.forEach(link => {
  link.addEventListener("click", () => {
    // quitar active de todos
    links.forEach(l => l.classList.remove("active"));

    // poner active al clickeado
    link.classList.add("active");
  });
});
document.addEventListener("DOMContentLoaded", () => {
    // Idioma por defecto: español
    const savedLang = localStorage.getItem("lang") || "es";
    setLanguage(savedLang);

    const btn = document.getElementById("lang-toggle");
    if (btn) {
        btn.addEventListener("click", toggleLanguage);
    }
});