"""Resources de solo lectura para mcp-design-patterns."""

from __future__ import annotations

import json


def dp_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-design-patterns",
            "version": "1.0.0",
            "project_path": ".",
        },
        indent=2,
        ensure_ascii=False,
    )


def dp_gof_catalog() -> str:
    return (
        "# Catalogo GoF (Gang of Four)\n\n"
        "## Creacionales\n"
        "- Singleton: instancia unica\n"
        "- Factory Method: creacion por subclase\n"
        "- Abstract Factory: familias de objetos\n"
        "- Builder: construccion paso a paso\n"
        "- Prototype: clonacion\n\n"
        "## Estructurales\n"
        "- Adapter: compatibilidad de interfaces\n"
        "- Bridge: separar abstraccion e implementacion\n"
        "- Composite: estructura de arbol\n"
        "- Decorator: agregar comportamiento dinamicamente\n"
        "- Facade: interfaz simplificada\n"
        "- Flyweight: compartir estado\n"
        "- Proxy: control de acceso\n\n"
        "## Comportamiento\n"
        "- Chain of Responsibility: cadena de handlers\n"
        "- Command: encapsular peticion\n"
        "- Interpreter: lenguaje simple\n"
        "- Iterator: recorrido secuencial\n"
        "- Mediator: comunicacion entre objetos\n"
        "- Memento: estado anterior\n"
        "- Observer: notificacion 1-a-N\n"
        "- State: comportamiento por estado\n"
        "- Strategy: algoritmos intercambiables\n"
        "- Template Method: esqueleto de algoritmo\n"
        "- Visitor: operacion sobre estructura"
    )


def dp_solid_principles() -> str:
    return (
        "# Principios SOLID\n\n"
        "## S - Single Responsibility Principle\n"
        "- Una clase debe tener una sola razon para cambiar\n"
        "- Separar responsabilidades\n\n"
        "## O - Open/Closed Principle\n"
        "- Abierto para extension, cerrado para modificacion\n"
        "- Usar herencia o composicion\n\n"
        "## L - Liskov Substitution Principle\n"
        "- Subtipos deben ser sustituibles por sus tipos base\n"
        "- No romper contratos\n\n"
        "## I - Interface Segregation Principle\n"
        "- Muchas interfaces especificas mejor que una general\n"
        "- No forzar implementaciones innecesarias\n\n"
        "## D - Dependency Inversion Principle\n"
        "- Depender de abstracciones, no de concreciones\n"
        "- Inyeccion de dependencias"
    )


def dp_anti_patterns() -> str:
    return (
        "# Antipatrones comunes\n\n"
        "## God Object\n"
        "- Clase que hace demasiado\n"
        "- Sintoma: > 10 metodos\n"
        "- Solucion: dividir en clases mas pequenas\n\n"
        "## Long Method\n"
        "- Funciones demasiado largas\n"
        "- Sintoma: > 50 lineas\n"
        "- Solucion: extraer metodos\n\n"
        "## Too Many Arguments\n"
        "- Funciones con muchos parametros\n"
        "- Sintoma: > 5 argumentos\n"
        "- Solucion: usar objeto de parametros (DTO)\n\n"
        "## Spaghetti Code\n"
        "- Logica entrelazada sin estructura\n"
        "- Solucion: modularizar\n\n"
        "## Golden Hammer\n"
        "- Usar una solucion para todo\n"
        "- Solucion: evaluar alternativas\n\n"
        "## Not Invented Here\n"
        "- Rechazar soluciones externas\n"
        "- Solucion: usar librerias estandar"
    )


def dp_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- dp_analyze_code_patterns(filename)\n"
        "- dp_suggest_pattern(problem_description)\n"
        "- dp_list_patterns(category)\n"
        "- dp_generate_pattern_code(pattern_name)\n"
        "- dp_analyze_solid(filename)\n\n"
        "## Variables .env\n"
        "- DP_PROJECT_PATH"
    )


def dp_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de DP"},
                {"code": -32001, "description": "FileNotFoundError: archivo no encontrado"},
                {"code": -32002, "description": "ParseError: error de parseo AST"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def dp_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Archivo no encontrado\n"
        "- Verificar DP_PROJECT_PATH\n"
        "- Usar ruta relativa al directorio configurado\n\n"
        "## Error de parseo\n"
        "- Verificar sintaxis Python valida\n"
        "- El archivo debe ser .py\n\n"
        "## No detecta antipatrones\n"
        "- Verificar que el archivo tenga clases/funciones\n"
        "- Los umbrales: God Object > 10 metodos, Long Method > 50 lineas\n\n"
        "## Sugerencia no relevante\n"
        "- Describir el problema con mas detalle\n"
        "- Incluir keywords: global, eventos, estados, crear"
    )


def dp_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Analizar codigo\n"
        'dp_analyze_code_patterns(filename="src/models.py")\n\n'
        "## Ejemplo 2: Sugerir patron\n"
        'dp_suggest_pattern(problem_description="necesito notificar a multiples componentes")\n\n'
        "## Ejemplo 3: Listar patrones\n"
        'dp_list_patterns(category="creational")\n\n'
        "## Ejemplo 4: Generar codigo\n"
        'dp_generate_pattern_code(pattern_name="singleton")'
    )


def dp_refactoring_guide() -> str:
    return (
        "# Guia de refactoring\n\n"
        "## Tecnicas\n"
        "- Extract Method: separar bloques de codigo\n"
        "- Extract Class: dividir responsabilidades\n"
        "- Rename: nombres descriptivos\n"
        "- Move Method: reubicar metodos\n"
        "- Replace Conditional with Polymorphism\n"
        "- Replace Inheritance with Delegation\n\n"
        "## Cuando refactorizar\n"
        "- Antipatrones detectados\n"
        "- Codigo duplicado\n"
        "- Metodos largos\n"
        "- Clases grandes\n"
        "- Dificultad de testing\n\n"
        "## Proceso\n"
        "1. Tests verdes antes de empezar\n"
        "2. Un cambio a la vez\n"
        "3. Tests verdes despues de cada cambio\n"
        "4. Commit despues de cada refactor"
    )


def dp_code_smells() -> str:
    return (
        "# Code Smells\n\n"
        "## Nivel de clase\n"
        "- God Object: demasiada responsabilidad\n"
        "- Data Class: solo datos sin comportamiento\n"
        "- Feature Envy: metodo que usa otra clase\n"
        "- Lazy Class: clase con poco proposito\n\n"
        "## Nivel de metodo\n"
        "- Long Method: demasiadas lineas\n"
        "- Long Parameter List: demasiados argumentos\n"
        "- Deep Nesting: anidacion profunda\n"
        "- Complex Conditionals: condiciones complejas\n\n"
        "## Nivel de codigo\n"
        "- Duplicated Code: codigo repetido\n"
        "- Magic Numbers: numeros sin nombre\n"
        "- Dead Code: codigo no usado\n"
        "- Comments: comentarios que explican codigo malo"
    )


def dp_pattern_relationships() -> str:
    return (
        "# Relaciones entre patrones\n\n"
        "## Combinaciones comunes\n"
        "- Singleton + Factory: factory singleton\n"
        "- Strategy + Factory: seleccionar estrategia dinamicamente\n"
        "- Observer + Mediator: mediador notifica observadores\n"
        "- Decorator + Composite: decoradores en estructura de arbol\n"
        "- State + Strategy: similares estructura, diferente intencion\n\n"
        "## Patrones opuestos\n"
        "- Singleton vs Dependency Injection\n"
        "- Inheritance vs Composition\n"
        "- Observer vs Mediator\n\n"
        "## Evolucion\n"
        "- Prototype -> Singleton si se clona siempre el mismo\n"
        "- Factory Method -> Abstract Factory al anadir tipos\n"
        "- Strategy -> State al anadir persistencia de estado"
    )


def dp_python_patterns() -> str:
    return (
        "# Patrones en Python\n\n"
        "## Singleton\n"
        "```python\n"
        "class Singleton:\n"
        "    _instance = None\n"
        "    def __new__(cls):\n"
        "        if cls._instance is None:\n"
        "            cls._instance = super().__new__(cls)\n"
        "        return cls._instance\n"
        "```\n\n"
        "## Observer\n"
        "```python\n"
        "class Subject:\n"
        "    def __init__(self):\n"
        "        self._observers = []\n"
        "    def notify(self, event):\n"
        "        for obs in self._observers:\n"
        "            obs.update(event)\n"
        "```\n\n"
        "## Strategy\n"
        "```python\n"
        "from typing import Protocol\n"
        "class SortStrategy(Protocol):\n"
        "    def sort(self, data): ...\n"
        "```\n\n"
        "## Decorator\n"
        "```python\n"
        "def log(func):\n"
        "    def wrapper(*args, **kw):\n"
        "        print(f'Calling {func.__name__}')\n"
        "        return func(*args, **kw)\n"
        "    return wrapper\n"
        "```"
    )


def dp_testing_patterns() -> str:
    return (
        "# Patrones de testing\n\n"
        "## Test Patterns\n"
        "- Arrange-Act-Assert (AAA): estructura de test\n"
        "- Given-When-Then: BDD style\n"
        "- Test Double: mock, stub, spy, fake\n"
        "- Builder: construir datos de test\n"
        "- Object Mother: factory de objetos de test\n\n"
        "## Test Pyramid\n"
        "```\n"
        "       /E2E\\\n"
        "      /Integ\\\n"
        "     /  Unit  \\\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Tests rapidos y aislados\n"
        "- Un assert por test (idealmente)\n"
        "- Nombres descriptivos\n"
        "- Fixtures reutilizables\n"
        "- Cobertura > 80%"
    )


def dp_ddd_patterns() -> str:
    return (
        "# Domain-Driven Design (DDD)\n\n"
        "## Patrones estrategicos\n"
        "- Bounded Context: limites del dominio\n"
        "- Context Map: relaciones entre contextos\n"
        "- Ubiquitous Language: lenguaje compartido\n\n"
        "## Patrones tacticos\n"
        "- Entity: objeto con identidad\n"
        "- Value Object: objeto inmutable\n"
        "- Aggregate: cluster de entidades\n"
        "- Repository: persistencia de agregados\n"
        "- Domain Service: logica de dominio\n"
        "- Domain Event: evento de dominio\n"
        "- Factory: creacion de agregados\n\n"
        "## Anti-corruption Layer\n"
        "- Proteger dominio de codigo legacy\n"
        "- Adapter entre modelos\n"
        "- Traduccion de conceptos"
    )


def dp_microservice_patterns() -> str:
    return (
        "# Patrones de microservicios\n\n"
        "## Comunicacion\n"
        "- API Gateway: punto de entrada unico\n"
        "- Service Registry: descubrimiento de servicios\n"
        "- Circuit Breaker: tolerancia a fallos\n"
        "- Saga: transacciones distribuidas\n\n"
        "## Datos\n"
        "- Database per Service: base de datos por servicio\n"
        "- CQRS: separar lectura y escritura\n"
        "- Event Sourcing: almacenar eventos\n"
        "- Shared Database: base de datos compartida (anti-pattern)\n\n"
        "## Despliegue\n"
        "- Sidecar: contenedor auxiliar\n"
        "- Service Mesh: malla de servicios\n"
        "- Blue-Green Deployment: despliegue sin downtime\n"
        "- Canary Release: despliegue gradual\n\n"
        "## Observabilidad\n"
        "- Distributed Tracing: trazas distribuidas\n"
        "- Log Aggregation: logs centralizados\n"
        "- Health Check: verificacion de salud"
    )
