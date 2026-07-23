"""Resources de solo lectura para mcp-architecture."""

from __future__ import annotations

import json


def architecture_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-architecture",
            "version": "1.0.0",
            "project_path": ".",
        },
        indent=2,
        ensure_ascii=False,
    )


def architecture_solid_principles() -> str:
    return (
        "# Principios SOLID\n\n"
        "## S - Single Responsibility\n"
        "- Una clase = una razon para cambiar\n"
        "- Evitar God Objects\n\n"
        "## O - Open/Closed\n"
        "- Abierto para extension, cerrado para modificacion\n"
        "- Usar herencia o composicion\n\n"
        "## L - Liskov Substitution\n"
        "- Subtipos deben ser sustituibles\n"
        "- No romper contratos del padre\n\n"
        "## I - Interface Segregation\n"
        "- Muchas interfaces especificas > una general\n"
        "- No forzar metodos innecesarios\n\n"
        "## D - Dependency Inversion\n"
        "- Depender de abstracciones, no concreciones\n"
        "- Inyeccion de dependencias"
    )


def architecture_clean_architecture() -> str:
    return (
        "# Clean Architecture\n\n"
        "## Capas (de dentro hacia fuera)\n"
        "1. Entities: reglas de negocio core\n"
        "2. Use Cases: logica de aplicacion\n"
        "3. Interface Adapters: controllers, presenters\n"
        "4. Frameworks: DB, web, UI\n\n"
        "## Regla de dependencias\n"
        "- Las dependencias apuntan hacia dentro\n"
        "- Capas externas conocen a internas, no al reves\n\n"
        "## Beneficios\n"
        "- Testabilidad\n"
        "- Independencia de framework\n"
        "- Independencia de UI\n"
        "- Independencia de DB"
    )


def architecture_hexagonal() -> str:
    return (
        "# Arquitectura Hexagonal (Ports & Adapters)\n\n"
        "## Conceptos\n"
        "- Core: logica de negocio\n"
        "- Ports: interfaces definidas por el core\n"
        "- Adapters: implementaciones de ports\n\n"
        "## Tipos de adapters\n"
        "- Driving: llaman al core (REST, CLI, gRPC)\n"
        "- Driven: el core los usa (DB, email, APIs)\n\n"
        "## Ventajas\n"
        "- Cambiar DB sin tocar logica\n"
        "- Testear core sin infraestructura\n"
        "- Nuevas interfaces sin cambiar core"
    )


def architecture_design_patterns() -> str:
    return (
        "# Patrones de diseno\n\n"
        "## Creacionales\n"
        "- Singleton: instancia unica\n"
        "- Factory: creacion flexible\n"
        "- Builder: construccion por pasos\n"
        "- Prototype: clonacion\n\n"
        "## Estructurales\n"
        "- Adapter: compatibilidad de interfaces\n"
        "- Decorator: anadir comportamiento\n"
        "- Facade: interfaz simplificada\n"
        "- Proxy: control de acceso\n\n"
        "## Comportamiento\n"
        "- Strategy: algoritmos intercambiables\n"
        "- Observer: notificacion de cambios\n"
        "- Command: encapsular peticiones\n"
        "- Template Method: esqueleto de algoritmo"
    )


def architecture_anti_patterns() -> str:
    return (
        "# Anti-patrones arquitectonicos\n\n"
        "## God Object\n"
        "- Clase que hace todo\n"
        "- Solucion: separar responsabilidades\n\n"
        "## Spaghetti Code\n"
        "- Logica entrelazada sin estructura\n"
        "- Solucion: modularizar\n\n"
        "## Golden Hammer\n"
        "- Usar la misma solucion para todo\n"
        "- Solucion: evaluar alternativas\n\n"
        "## Big Ball of Mud\n"
        "- Sin arquitectura clara\n"
        "- Solucion: definir capas\n\n"
        "## Vendor Lock-in\n"
        "- Dependencia excesiva de un proveedor\n"
        "- Solucion: abstracciones"
    )


def architecture_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- arch_get_project_tree(max_depth)\n"
        "- arch_analyze_dependencies(target_file)\n"
        "- arch_check_solid_principles(target_file)\n"
        "- arch_analyze_circular_deps(target)\n"
        "- arch_analyze_layering(target)\n"
        "- arch_find_entry_points(target)\n"
        "- arch_analyze_coupling(target)\n"
        "- arch_analyze_cohesion(target)\n\n"
        "## Variables .env\n"
        "- ARCH_PROJECT_PATH"
    )


def architecture_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de arquitectura"},
                {"code": -32001, "description": "FileNotFoundError: archivo no encontrado"},
                {"code": -32002, "description": "ParseError: error de sintaxis"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def architecture_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Archivo no encontrado\n"
        "- Verificar ARCH_PROJECT_PATH\n"
        "- Usar ruta relativa al proyecto\n\n"
        "## Error de parseo\n"
        "- Verificar sintaxis Python\n"
        "- El archivo debe ser .py\n\n"
        "## Arbol vacio\n"
        "- Verificar que el proyecto tiene archivos\n"
        "- Aumentar max_depth\n\n"
        "## Dependencias circulares\n"
        "- Usar arch_analyze_circular_deps\n"
        "- Refactorizar separando modulos"
    )


def architecture_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Ver estructura\n"
        "arch_get_project_tree(max_depth=3)\n\n"
        "## Ejemplo 2: Analizar imports\n"
        "arch_analyze_dependencies(target_file='src/main.py')\n\n"
        "## Ejemplo 3: Verificar SOLID\n"
        "arch_check_solid_principles(target_file='src/models.py')\n\n"
        "## Ejemplo 4: Dependencias circulares\n"
        "arch_analyze_circular_deps(target='src/')"
    )


def architecture_metrics() -> str:
    return (
        "# Metricas arquitectonicas\n\n"
        "## Acoplamiento (Coupling)\n"
        "- Bajo acoplamiento = bueno\n"
        "- Afferent: cuantos dependen de mi\n"
        "- Efferent: de cuantos dependo yo\n\n"
        "## Cohesion (Cohesion)\n"
        "- Alta cohesion = bueno\n"
        "- Funcional: elementos hacen lo mismo\n"
        "- Logica: elementos relacionados logicamente\n\n"
        "## Inestabilidad\n"
        "- I = Ce / (Ca + Ce)\n"
        "- I=0: estable, I=1: inestable\n\n"
        "## Distancia de la secuencia principal\n"
        "- D = |A + I - 1|\n"
        "- D=0: balance ideal"
    )


def architecture_refactoring() -> str:
    return (
        "# Refactoring arquitectonico\n\n"
        "## Extraccion de capa\n"
        "1. Identificar logica de negocio mezclada\n"
        "2. Crear nueva capa/modulo\n"
        "3. Mover codigo gradualmente\n"
        "4. Actualizar imports\n"
        "5. Verificar tests\n\n"
        "## Inversion de dependencias\n"
        "1. Definir interface (port)\n"
        "2. Implementar adapter\n"
        "3. Inyectar dependencia\n"
        "4. Eliminar acoplamiento directo\n\n"
        "## Estrangulacion\n"
        "1. Nuevo sistema junto al viejo\n"
        "2. Migrar gradualmente\n"
        "3. Eliminar codigo viejo"
    )


def architecture_documentation() -> str:
    return (
        "# Documentacion arquitectonica\n\n"
        "## ADR (Architecture Decision Records)\n"
        "- Context: problema a resolver\n"
        "- Decision: opcion elegida\n"
        "- Status: proposed/accepted/deprecated\n"
        "- Consequences: impactos\n\n"
        "## C4 Model\n"
        "- Context: sistema como caja\n"
        "- Containers: aplicaciones/datos\n"
        "- Components: modulos internos\n"
        "- Code: clases y funciones\n\n"
        "## Diagramas\n"
        "- Component diagram\n"
        "- Deployment diagram\n"
        "- Sequence diagram"
    )


def architecture_microservices() -> str:
    return (
        "# Arquitectura de microservicios\n\n"
        "## Principios\n"
        "- Un servicio = una capacidad de negocio\n"
        "- Despliegue independiente\n"
        "- Comunicacion via API/ eventos\n"
        "- Datos propios por servicio\n\n"
        "## Patrones\n"
        "- API Gateway: punto de entrada unico\n"
        "- Service Discovery: localizar servicios\n"
        "- Circuit Breaker: tolerancia a fallos\n"
        "- Saga: transacciones distribuidas\n"
        "- CQRS: separar lectura/escritura\n\n"
        "## Desafios\n"
        "- Consistencia eventual\n"
        "- Debugging distribuido\n"
        "- Versionado de APIs"
    )


def architecture_best_practices() -> str:
    return (
        "# Mejores practicas arquitectonicas\n\n"
        "1. Definir capas claras\n"
        "2. Dependencias hacia dentro\n"
        "3. Interfaces estables\n"
        "4. Alta cohesion, bajo acoplamiento\n"
        "5. Evitar God Objects\n"
        "6. Usar inyeccion de dependencias\n"
        "7. Separar logica de infraestructura\n"
        "8. Documentar decisiones (ADR)\n"
        "9. Pensar en testabilidad\n"
        "10. Iterar incrementalmente"
    )
