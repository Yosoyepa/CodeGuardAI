"""
Configuración del Protocolo de Contexto de Modelo (MCP).

Contiene el diccionario embebido OWASP Top 10 con descripciones
de vulnerabilidades y remediaciones para enriquecer los prompts
enviados a la IA generativa.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SecurityContext:
    """
    Contexto de seguridad para una categoría de vulnerabilidad.

    Attributes:
        category: Categoría OWASP (ej: "A03:2021 - Injection")
        description: Descripción de la vulnerabilidad
        impact: Impacto potencial en el sistema
        mitigation: Estrategias de mitigación genéricas
        references: URLs de documentación oficial
        cwe_ids: IDs de CWE relacionados
    """

    category: str
    description: str
    impact: str
    mitigation: str
    references: List[str]
    cwe_ids: List[str]


# =============================================================================
# Diccionario OWASP Top 10 (2021)
# =============================================================================

OWASP_TOP_10: Dict[str, SecurityContext] = {
    # A01:2021 - Broken Access Control
    "broken_access_control": SecurityContext(
        category="A01:2021 - Broken Access Control",
        description=(
            "Las restricciones sobre lo que los usuarios autenticados pueden hacer "
            "a menudo no se aplican correctamente. Los atacantes pueden explotar "
            "estos fallos para acceder a funcionalidades y/o datos no autorizados."
        ),
        impact=(
            "Acceso no autorizado a datos sensibles, modificación de datos de otros "
            "usuarios, escalación de privilegios, o ejecución de acciones administrativas."
        ),
        mitigation=(
            "1. Denegar por defecto, excepto para recursos públicos.\n"
            "2. Implementar mecanismos de control de acceso una vez y reutilizarlos.\n"
            "3. Hacer cumplir la propiedad de registros (cada usuario solo accede a sus datos).\n"
            "4. Deshabilitar listado de directorios del servidor web.\n"
            "5. Registrar fallos de control de acceso y alertar a administradores."
        ),
        references=[
            "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-200", "CWE-284", "CWE-285", "CWE-352", "CWE-639"],
    ),
    # A02:2021 - Cryptographic Failures
    "cryptographic_failures": SecurityContext(
        category="A02:2021 - Cryptographic Failures",
        description=(
            "Antes conocido como 'Exposición de Datos Sensibles'. Se centra en "
            "fallos relacionados con la criptografía que a menudo conducen a la "
            "exposición de datos sensibles."
        ),
        impact=(
            "Exposición de credenciales, tokens, datos personales (PII), datos "
            "financieros, o información médica. Posible robo de identidad."
        ),
        mitigation=(
            "1. Clasificar los datos procesados, almacenados o transmitidos.\n"
            "2. No almacenar datos sensibles innecesariamente.\n"
            "3. Cifrar todos los datos sensibles en reposo con algoritmos fuertes.\n"
            "4. Usar protocolos actualizados (TLS 1.3) para datos en tránsito.\n"
            "5. No usar algoritmos criptográficos obsoletos (MD5, SHA1, DES)."
        ),
        references=[
            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-259", "CWE-327", "CWE-328", "CWE-330", "CWE-331"],
    ),
    # A03:2021 - Injection
    "injection": SecurityContext(
        category="A03:2021 - Injection",
        description=(
            "Una aplicación es vulnerable a ataques de inyección cuando datos "
            "suministrados por el usuario no son validados, filtrados o sanitizados. "
            "Incluye SQL, NoSQL, OS Command, LDAP, XPath y ORM injection."
        ),
        impact=(
            "Pérdida de datos, corrupción de datos, divulgación a partes no autorizadas, "
            "pérdida de responsabilidad, denegación de acceso, o toma completa del host."
        ),
        mitigation=(
            "1. Usar APIs seguras que eviten el uso del intérprete (consultas parametrizadas).\n"
            "2. Usar validación de entrada positiva del lado del servidor.\n"
            "3. Escapar caracteres especiales usando la sintaxis de escape específica.\n"
            "4. Usar LIMIT y otros controles SQL para prevenir divulgación masiva.\n"
            "5. No concatenar cadenas con datos del usuario en consultas dinámicas."
        ),
        references=[
            "https://owasp.org/Top10/A03_2021-Injection/",
            "https://cheatsheetseries.owasp.org/cheatsheets/"
            "SQL_Injection_Prevention_Cheat_Sheet.html",
            "https://cheatsheetseries.owasp.org/cheatsheets/"
            "Query_Parameterization_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-77", "CWE-78", "CWE-79", "CWE-89", "CWE-94"],
    ),
    # A04:2021 - Insecure Design
    "insecure_design": SecurityContext(
        category="A04:2021 - Insecure Design",
        description=(
            "Una nueva categoría que se centra en los riesgos relacionados con "
            "defectos de diseño. La diferencia con una implementación insegura es "
            "que un diseño perfecto aún puede tener defectos de implementación."
        ),
        impact=(
            "Vulnerabilidades sistémicas que no pueden ser corregidas solo con código. "
            "Exposición de lógica de negocio, flujos de trabajo inseguros."
        ),
        mitigation=(
            "1. Establecer y usar un ciclo de desarrollo seguro con profesionales de AppSec.\n"
            "2. Usar bibliotecas de patrones de diseño seguro.\n"
            "3. Usar modelado de amenazas para autenticación crítica y control de acceso.\n"
            "4. Integrar controles de seguridad en las historias de usuario.\n"
            "5. Escribir pruebas unitarias y de integración para validar flujos críticos."
        ),
        references=[
            "https://owasp.org/Top10/A04_2021-Insecure_Design/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-209", "CWE-256", "CWE-501", "CWE-522"],
    ),
    # A05:2021 - Security Misconfiguration
    "security_misconfiguration": SecurityContext(
        category="A05:2021 - Security Misconfiguration",
        description=(
            "La aplicación puede ser vulnerable si no está correctamente "
            "endurecida o tiene permisos mal configurados, características "
            "innecesarias habilitadas, o mensajes de error detallados."
        ),
        impact=(
            "Acceso no autorizado a datos o funcionalidad del sistema. "
            "Posible compromiso completo del sistema."
        ),
        mitigation=(
            "1. Proceso de endurecimiento repetible y automatizado.\n"
            "2. Plataforma mínima sin características, componentes o documentación innecesarios.\n"
            "3. Revisar y actualizar configuraciones según avisos de seguridad.\n"
            "4. Arquitectura de aplicación segmentada con contenedores.\n"
            "5. Enviar directivas de seguridad a clientes (CSP, X-Frame-Options)."
        ),
        references=[
            "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
            "https://cheatsheetseries.owasp.org/cheatsheets/"
            "Configuration_Security_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-16", "CWE-611", "CWE-1004", "CWE-2"],
    ),
    # A06:2021 - Vulnerable and Outdated Components
    "vulnerable_components": SecurityContext(
        category="A06:2021 - Vulnerable and Outdated Components",
        description=(
            "Usar componentes con vulnerabilidades conocidas. Esto incluye "
            "bibliotecas, frameworks, y otros módulos de software que se ejecutan "
            "con los mismos privilegios que la aplicación."
        ),
        impact=(
            "Desde ataques menores hasta toma completa del servidor, dependiendo "
            "de la vulnerabilidad del componente."
        ),
        mitigation=(
            "1. Eliminar dependencias no utilizadas, características y componentes innecesarios.\n"
            "2. Inventariar versiones de componentes cliente y servidor continuamente.\n"
            "3. Monitorear fuentes como CVE y NVD para vulnerabilidades.\n"
            "4. Obtener componentes solo de fuentes oficiales sobre enlaces seguros.\n"
            "5. Monitorear bibliotecas y componentes sin mantenimiento."
        ),
        references=[
            "https://owasp.org/Top10/" "A06_2021-Vulnerable_and_Outdated_Components/",
            "https://cheatsheetseries.owasp.org/cheatsheets/"
            "Vulnerable_Dependency_Management_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-1104"],
    ),
    # A07:2021 - Identification and Authentication Failures
    "authentication_failures": SecurityContext(
        category="A07:2021 - Identification and Authentication Failures",
        description=(
            "Confirmación de la identidad del usuario, autenticación y gestión "
            "de sesiones es crítica. La aplicación es vulnerable si permite "
            "ataques automatizados, contraseñas débiles, o sesiones mal gestionadas."
        ),
        impact=(
            "Compromiso de cuentas de usuario, robo de identidad, acceso "
            "no autorizado a datos sensibles o funcionalidad administrativa."
        ),
        mitigation=(
            "1. Implementar autenticación multifactor donde sea posible.\n"
            "2. No desplegar con credenciales por defecto, especialmente admin.\n"
            "3. Implementar verificaciones de contraseñas débiles.\n"
            "4. Limitar o retrasar cada vez más los intentos de login fallidos.\n"
            "5. Usar un gestor de sesiones seguro del lado del servidor con alta entropía."
        ),
        references=[
            "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
            "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-287", "CWE-384", "CWE-307", "CWE-613"],
    ),
    # A08:2021 - Software and Data Integrity Failures
    "integrity_failures": SecurityContext(
        category="A08:2021 - Software and Data Integrity Failures",
        description=(
            "Se relaciona con código e infraestructura que no protege contra "
            "violaciones de integridad. Incluye actualizaciones de software "
            "inseguras, pipelines CI/CD inseguros, y deserialización insegura."
        ),
        impact=(
            "Ejecución remota de código, ataques a la cadena de suministro, "
            "modificación de datos sin autorización."
        ),
        mitigation=(
            "1. Usar firmas digitales para verificar que el software "
            "proviene de la fuente esperada.\n"
            "2. Asegurar que las bibliotecas y dependencias usan "
            "repositorios de confianza.\n"
            "3. Usar herramientas de análisis de composición de software (SCA).\n"
            "4. Asegurar que el pipeline CI/CD tiene segregación apropiada "
            "y control de acceso.\n"
            "5. No enviar datos serializados sin firmar o sin cifrar "
            "a clientes no confiables."
        ),
        references=[
            "https://owasp.org/Top10/" "A08_2021-Software_and_Data_Integrity_Failures/",
            "https://cheatsheetseries.owasp.org/cheatsheets/" "Deserialization_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-829", "CWE-494", "CWE-502"],
    ),
    # A09:2021 - Security Logging and Monitoring Failures
    "logging_failures": SecurityContext(
        category="A09:2021 - Security Logging and Monitoring Failures",
        description=(
            "Sin registro y monitoreo suficiente, los ataques no pueden ser "
            "detectados. Incluye no registrar eventos auditables, no generar "
            "alertas adecuadas, o no tener un plan de respuesta a incidentes."
        ),
        impact=(
            "Los atacantes pueden mantener persistencia, pivotar a más sistemas, "
            "manipular, extraer o destruir datos sin ser detectados."
        ),
        mitigation=(
            "1. Asegurar que todos los fallos de login, control de acceso "
            "y validación de entrada del servidor se registran "
            "con contexto suficiente.\n"
            "2. Asegurar que los logs se generan en formato que las "
            "soluciones de gestión de logs puedan consumir fácilmente.\n"
            "3. Asegurar que los datos de log se codifican correctamente "
            "para prevenir inyecciones.\n"
            "4. Establecer monitoreo y alertas efectivos "
            "para actividades sospechosas.\n"
            "5. Establecer un plan de respuesta y recuperación de incidentes."
        ),
        references=[
            "https://owasp.org/Top10/" "A09_2021-Security_Logging_and_Monitoring_Failures/",
            "https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
    ),
    # A10:2021 - Server-Side Request Forgery (SSRF)
    "ssrf": SecurityContext(
        category="A10:2021 - Server-Side Request Forgery (SSRF)",
        description=(
            "SSRF ocurre cuando una aplicación web obtiene un recurso remoto "
            "sin validar la URL suministrada por el usuario. Permite a un atacante "
            "forzar a la aplicación a enviar una solicitud crafteada a un destino inesperado."
        ),
        impact=(
            "Escaneo de puertos internos, acceso a servicios internos, lectura de "
            "metadatos de servicios en la nube, o ejecución remota de código."
        ),
        mitigation=(
            "1. Segmentar la funcionalidad de acceso a recursos remotos en redes separadas.\n"
            "2. Hacer cumplir políticas de firewall 'deny by default'.\n"
            "3. Sanitizar y validar todos los datos de entrada suministrados por el cliente.\n"
            "4. No enviar respuestas raw al cliente.\n"
            "5. Deshabilitar redirecciones HTTP y usar listas de permitidos para URL."
        ),
        references=[
            "https://owasp.org/Top10/" "A10_2021-Server-Side_Request_Forgery_%28SSRF%29/",
            "https://cheatsheetseries.owasp.org/cheatsheets/"
            "Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",
        ],
        cwe_ids=["CWE-918"],
    ),
}


# =============================================================================
# Mapeo de reglas de CodeGuard a categorías OWASP
# =============================================================================

RULE_TO_OWASP_MAPPING: Dict[str, str] = {
    # SecurityAgent - Dangerous Functions
    "SEC001_EVAL": "injection",
    "SEC001_EXEC": "injection",
    "SEC001_COMPILE": "injection",
    "SEC001___IMPORT__": "injection",
    "SEC001_EXECFILE": "injection",
    "SEC001_PICKLE": "integrity_failures",
    # SecurityAgent - SQL Injection
    "SEC002_SQL_INJECTION": "injection",
    # SecurityAgent - Hardcoded Credentials
    "SEC003_PASSWORD": "cryptographic_failures",
    "SEC003_API_KEY": "cryptographic_failures",
    "SEC003_SECRET_KEY": "cryptographic_failures",
    "SEC003_TOKEN": "cryptographic_failures",
    "SEC003_ACCESS_KEY": "cryptographic_failures",
    # SecurityAgent - Weak Cryptography
    "SEC004_MD5": "cryptographic_failures",
    "SEC004_SHA1": "cryptographic_failures",
    "SEC004_WEAK_ENCRYPTION": "cryptographic_failures",
    # Common patterns by issue_type
    "dangerous_function": "injection",
    "sql_injection": "injection",
    "hardcoded_credentials": "cryptographic_failures",
    "weak_cryptography": "cryptographic_failures",
    "insecure_deserialization": "integrity_failures",
    "path_traversal": "broken_access_control",
    "ssrf": "ssrf",
    "xss": "injection",
    "command_injection": "injection",
    "ldap_injection": "injection",
    "xpath_injection": "injection",
}


# =============================================================================
# Funciones de utilidad
# =============================================================================


def get_security_context(
    rule_id: Optional[str] = None,
    issue_type: Optional[str] = None,
) -> Optional[SecurityContext]:
    """
    Obtiene el contexto de seguridad OWASP para una regla o tipo de issue.

    Args:
        rule_id: ID de la regla (ej: "SEC001_EVAL")
        issue_type: Tipo de issue (ej: "sql_injection")

    Returns:
        SecurityContext si se encuentra mapeo, None en caso contrario
    """
    # Primero intentar con rule_id
    if rule_id:
        owasp_key = RULE_TO_OWASP_MAPPING.get(rule_id)
        if owasp_key:
            return OWASP_TOP_10.get(owasp_key)

    # Luego intentar con issue_type
    if issue_type:
        # Normalizar issue_type (convertir espacios/guiones a underscore)
        normalized = issue_type.lower().replace("-", "_").replace(" ", "_")
        owasp_key = RULE_TO_OWASP_MAPPING.get(normalized)
        if owasp_key:
            return OWASP_TOP_10.get(owasp_key)

        # Buscar coincidencia parcial
        for key, owasp_category in RULE_TO_OWASP_MAPPING.items():
            if key in normalized or normalized in key:
                return OWASP_TOP_10.get(owasp_category)

    return None


def format_security_context(context: SecurityContext) -> str:
    """
    Formatea el contexto de seguridad para incluirlo en un prompt.

    Args:
        context: Contexto de seguridad OWASP

    Returns:
        str: Texto formateado para el prompt de IA
    """
    return f"""
=== CONTEXTO DE SEGURIDAD (OWASP) ===
Categoría: {context.category}

Descripción:
{context.description}

Impacto Potencial:
{context.impact}

Estrategias de Mitigación:
{context.mitigation}

Referencias:
{chr(10).join(f"- {ref}" for ref in context.references)}

CWEs Relacionados: {", ".join(context.cwe_ids)}
===================================
"""
