"""
Lógica de mcp-design-patterns.

Evalúa AST en busca de métricas que indiquen antipatrones (ej. God Object).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from mcp_shared.errors import FileNotFoundError, ParseError


def analyze_code_patterns(file_path: Path) -> dict[str, Any]:
    """
    Analiza un archivo en busca de antipatrones (métricas simples):
    - God Object: Clase con demasiados métodos (> 10).
    - Long Method: Método con demasiadas líneas (> 50).
    - Too Many Arguments: Función con > 5 argumentos.
    """
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    antipatterns = []

    for node in ast.walk(tree):
        # Evaluar clases
        if isinstance(node, ast.ClassDef):
            methods = [
                n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if len(methods) > 10:
                antipatterns.append(
                    {
                        "type": "God Object",
                        "entity": node.name,
                        "line": node.lineno,
                        "detail": f"Clase tiene {len(methods)} métodos. Considera SRP (Single Responsibility Principle).",
                    }
                )

        # Evaluar funciones
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Demasiados argumentos
            if len(node.args.args) > 5:
                antipatterns.append(
                    {
                        "type": "Too Many Arguments",
                        "entity": node.name,
                        "line": node.lineno,
                        "detail": f"Función recibe {len(node.args.args)} argumentos. Considera usar un objeto de parámetros (DTO).",
                    }
                )

            # Método muy largo (aproximación)
            if (
                hasattr(node, "end_lineno")
                and node.end_lineno is not None
                and node.lineno is not None
            ):
                lines_count = node.end_lineno - node.lineno
                if lines_count > 50:
                    antipatterns.append(
                        {
                            "type": "Long Method",
                            "entity": node.name,
                            "line": node.lineno,
                            "detail": f"Función tiene aprox {lines_count} líneas. Divídela en funciones más pequeñas.",
                        }
                    )

    return {
        "file": file_path.name,
        "antipatterns_found": len(antipatterns),
        "antipatterns": antipatterns,
    }


def suggest_design_pattern(problem_description: str) -> dict[str, str]:
    """Sugiere patrones clásicos basados en keywords simples (simulación ligera)."""
    desc = problem_description.lower()

    if (
        "global" in desc
        or "única instancia" in desc
        or "instancia compartida" in desc
        or "single instance" in desc
    ):
        return {
            "pattern": "Singleton",
            "type": "Creational",
            "advice": "Cuidado con estado global mutable.",
        }
    if "crear" in desc and ("dinámico" in desc or "depende" in desc or "factory" in desc):
        return {
            "pattern": "Factory Method / Abstract Factory",
            "type": "Creational",
            "advice": "Desacopla la creación.",
        }
    if "notificar" in desc or "eventos" in desc or "suscrip" in desc:
        return {"pattern": "Observer", "type": "Behavioral", "advice": "Ideal para 1-a-N."}
    if "estados" in desc or "máquina" in desc:
        return {"pattern": "State", "type": "Behavioral", "advice": "Evita switch/case gigantes."}

    return {
        "pattern": "Unknown",
        "advice": "Describe mejor si necesitas instanciacion, comportamiento o estructura.",
    }


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def list_patterns(category: str = "") -> list[dict[str, str]]:
    """Lista patrones GoF por categoria."""
    all_patterns = [
        {"name": "Singleton", "category": "Creational", "description": "Instancia unica"},
        {"name": "Factory Method", "category": "Creational", "description": "Creacion por subclase"},
        {"name": "Abstract Factory", "category": "Creational", "description": "Familias de objetos"},
        {"name": "Builder", "category": "Creational", "description": "Construccion paso a paso"},
        {"name": "Prototype", "category": "Creational", "description": "Clonacion"},
        {"name": "Adapter", "category": "Structural", "description": "Compatibilidad de interfaces"},
        {"name": "Bridge", "category": "Structural", "description": "Separar abstraccion e implementacion"},
        {"name": "Composite", "category": "Structural", "description": "Estructura de arbol"},
        {"name": "Decorator", "category": "Structural", "description": "Agregar comportamiento"},
        {"name": "Facade", "category": "Structural", "description": "Interfaz simplificada"},
        {"name": "Flyweight", "category": "Structural", "description": "Compartir estado"},
        {"name": "Proxy", "category": "Structural", "description": "Control de acceso"},
        {"name": "Chain of Responsibility", "category": "Behavioral", "description": "Cadena de handlers"},
        {"name": "Command", "category": "Behavioral", "description": "Encapsular peticion"},
        {"name": "Iterator", "category": "Behavioral", "description": "Recorrido secuencial"},
        {"name": "Mediator", "category": "Behavioral", "description": "Comunicacion entre objetos"},
        {"name": "Memento", "category": "Behavioral", "description": "Estado anterior"},
        {"name": "Observer", "category": "Behavioral", "description": "Notificacion 1-a-N"},
        {"name": "State", "category": "Behavioral", "description": "Comportamiento por estado"},
        {"name": "Strategy", "category": "Behavioral", "description": "Algoritmos intercambiables"},
        {"name": "Template Method", "category": "Behavioral", "description": "Esqueleto de algoritmo"},
        {"name": "Visitor", "category": "Behavioral", "description": "Operacion sobre estructura"},
    ]

    if category:
        cat_lower = category.lower()
        return [p for p in all_patterns if p["category"].lower() == cat_lower]
    return all_patterns


def generate_pattern_code(pattern_name: str) -> str:
    """Genera codigo de ejemplo para un patron."""
    name = pattern_name.lower()

    if name == "singleton":
        return "\n".join([
            "class Singleton:",
            "    _instance = None",
            "",
            "    def __new__(cls):",
            "        if cls._instance is None:",
            "            cls._instance = super().__new__(cls)",
            "        return cls._instance",
            "",
            "# Uso",
            "s1 = Singleton()",
            "s2 = Singleton()",
            "assert s1 is s2",
        ])
    elif name == "observer":
        return "\n".join([
            "from typing import Protocol",
            "",
            "class Observer(Protocol):",
            "    def update(self, event: str) -> None: ...",
            "",
            "class Subject:",
            "    def __init__(self):",
            "        self._observers: list[Observer] = []",
            "",
            "    def attach(self, obs: Observer) -> None:",
            "        self._observers.append(obs)",
            "",
            "    def detach(self, obs: Observer) -> None:",
            "        self._observers.remove(obs)",
            "",
            "    def notify(self, event: str) -> None:",
            "        for obs in self._observers:",
            "            obs.update(event)",
        ])
    elif name == "strategy":
        return "\n".join([
            "from typing import Protocol",
            "",
            "class SortStrategy(Protocol):",
            "    def sort(self, data: list) -> list: ...",
            "",
            "class QuickSort:",
            "    def sort(self, data: list) -> list:",
            "        return sorted(data)",
            "",
            "class Context:",
            "    def __init__(self, strategy: SortStrategy):",
            "        self._strategy = strategy",
            "",
            "    def execute(self, data: list) -> list:",
            "        return self._strategy.sort(data)",
        ])
    elif name == "factory" or name == "factory method":
        return "\n".join([
            "from abc import ABC, abstractmethod",
            "",
            "class Product(ABC):",
            "    @abstractmethod",
            "    def operation(self) -> str: ...",
            "",
            "class ConcreteProductA(Product):",
            "    def operation(self) -> str:",
            "        return 'Product A'",
            "",
            "class ConcreteProductB(Product):",
            "    def operation(self) -> str:",
            "        return 'Product B'",
            "",
            "class Creator(ABC):",
            "    @abstractmethod",
            "    def factory_method(self) -> Product: ...",
            "",
            "    def some_operation(self) -> str:",
            "        product = self.factory_method()",
            "        return product.operation()",
        ])
    elif name == "decorator":
        return "\n".join([
            "def log_decorator(func):",
            "    def wrapper(*args, **kwargs):",
            "        print(f'Calling {func.__name__}')",
            "        result = func(*args, **kwargs)",
            "        print(f'{func.__name__} returned')",
            "        return result",
            "    return wrapper",
            "",
            "@log_decorator",
            "def greet(name: str) -> str:",
            "    return f'Hello, {name}!'",
        ])
    elif name == "adapter":
        return "\n".join([
            "class OldSystem:",
            "    def get_data(self) -> str:",
            "        return 'old-format-data'",
            "",
            "class NewInterface:",
            "    def fetch(self) -> dict: ...",
            "",
            "class Adapter(NewInterface):",
            "    def __init__(self, old: OldSystem):",
            "        self._old = old",
            "",
            "    def fetch(self) -> dict:",
            "        data = self._old.get_data()",
            "        return {'data': data}",
        ])
    elif name == "command":
        return "\n".join([
            "from abc import ABC, abstractmethod",
            "",
            "class Command(ABC):",
            "    @abstractmethod",
            "    def execute(self) -> None: ...",
            "",
            "class LightOnCommand(Command):",
            "    def execute(self) -> None:",
            "        print('Light is ON')",
            "",
            "class RemoteControl:",
            "    def __init__(self):",
            "        self._command: Command | None = None",
            "",
            "    def set_command(self, cmd: Command) -> None:",
            "        self._command = cmd",
            "",
            "    def press_button(self) -> None:",
            "        if self._command:",
            "            self._command.execute()",
        ])
    elif name == "state":
        return "\n".join([
            "from abc import ABC, abstractmethod",
            "",
            "class State(ABC):",
            "    @abstractmethod",
            "    def handle(self, context) -> None: ...",
            "",
            "class ActiveState(State):",
            "    def handle(self, context) -> None:",
            "        print('Active: processing')",
            "",
            "class PausedState(State):",
            "    def handle(self, context) -> None:",
            "        print('Paused: waiting')",
            "",
            "class Context:",
            "    def __init__(self, state: State):",
            "        self._state = state",
            "",
            "    def set_state(self, state: State) -> None:",
            "        self._state = state",
            "",
            "    def request(self) -> None:",
            "        self._state.handle(self)",
        ])
    else:
        return f"# Pattern '{pattern_name}' not found. Try: singleton, observer, strategy, factory, decorator, adapter, command, state"


def analyze_solid(file_path: Path) -> dict[str, Any]:
    """Analiza un archivo en busca de violaciones de principios SOLID."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    violations: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if len(methods) > 10:
                violations.append({
                    "principle": "SRP",
                    "violation": "Single Responsibility",
                    "entity": node.name,
                    "line": node.lineno,
                    "detail": f"Clase con {len(methods)} metodos. Posible violacion de SRP.",
                })

            for method in methods:
                if len(method.args.args) > 5:
                    violations.append({
                        "principle": "ISP",
                        "violation": "Interface Segregation",
                        "entity": f"{node.name}.{method.name}",
                        "line": method.lineno,
                        "detail": f"Metodo con {len(method.args.args)} argumentos. Posible violacion de ISP.",
                    })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.args.args) > 5:
                violations.append({
                    "principle": "ISP",
                    "violation": "Interface Segregation",
                    "entity": node.name,
                    "line": node.lineno,
                    "detail": f"Funcion con {len(node.args.args)} argumentos.",
                })

    return {
        "file": file_path.name,
        "violations_found": len(violations),
        "violations": violations,
    }


def detect_code_smells(file_path: Path) -> dict[str, Any]:
    """Detecta code smells en un archivo Python."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    smells: list[dict[str, Any]] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and stripped.isdigit():
            smells.append({
                "type": "Magic Number",
                "line": i,
                "detail": f"Numero magico: {stripped}",
            })
        if stripped.count("if ") > 3:
            smells.append({
                "type": "Deep Nesting",
                "line": i,
                "detail": "Posible anidacion profunda",
            })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, "end_lineno") and node.end_lineno and node.lineno:
                if node.end_lineno - node.lineno > 50:
                    smells.append({
                        "type": "Long Method",
                        "entity": node.name,
                        "line": node.lineno,
                        "detail": f"Metodo de {node.end_lineno - node.lineno} lineas",
                    })

    return {
        "file": file_path.name,
        "smells_found": len(smells),
        "smells": smells[:50],
    }


def suggest_refactoring(file_path: Path) -> dict[str, Any]:
    """Sugiere refactorings basados en el analisis del archivo."""
    analysis = analyze_code_patterns(file_path)
    suggestions: list[dict[str, str]] = []

    for ap in analysis["antipatterns"]:
        if ap["type"] == "God Object":
            suggestions.append({
                "antipattern": "God Object",
                "refactoring": "Extract Class",
                "description": f"Dividir '{ap['entity']}' en clases mas pequenas con responsabilidades unicas.",
            })
        elif ap["type"] == "Long Method":
            suggestions.append({
                "antipattern": "Long Method",
                "refactoring": "Extract Method",
                "description": f"Dividir '{ap['entity']}' en metodos mas pequenos.",
            })
        elif ap["type"] == "Too Many Arguments":
            suggestions.append({
                "antipattern": "Too Many Arguments",
                "refactoring": "Introduce Parameter Object",
                "description": f"Agrupar argumentos de '{ap['entity']}' en un objeto de parametros.",
            })

    return {
        "file": file_path.name,
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
    }


def analyze_project_patterns(project_path: Path) -> dict[str, Any]:
    """Analiza todos los archivos Python del proyecto en busca de antipatrones."""
    results: list[dict[str, Any]] = []
    total_antipatterns = 0

    for f in project_path.rglob("*.py"):
        if any(part.startswith(".") for part in f.parts):
            continue
        if "__pycache__" in f.parts:
            continue
        try:
            analysis = analyze_code_patterns(f)
            if analysis["antipatterns_found"] > 0:
                results.append({
                    "file": str(f.relative_to(project_path)),
                    "antipatterns_found": analysis["antipatterns_found"],
                    "antipatterns": analysis["antipatterns"],
                })
                total_antipatterns += analysis["antipatterns_found"]
        except Exception:
            continue

    return {
        "files_analyzed": len(results),
        "total_antipatterns": total_antipatterns,
        "results": results[:50],
    }


def get_pattern_info(pattern_name: str) -> dict[str, str]:
    """Retorna informacion detallada de un patron especifico."""
    patterns = {
        "singleton": {
            "name": "Singleton",
            "category": "Creational",
            "intent": "Asegurar una unica instancia de una clase.",
            "applicability": "Cuando se necesita exactamente una instancia.",
            "consequences": "Control de acceso, pero puede ser dificil de testear.",
        },
        "observer": {
            "name": "Observer",
            "category": "Behavioral",
            "intent": "Notificar a multiples objetos sobre cambios.",
            "applicability": "Cuando un cambio debe notificar a muchos dependientes.",
            "consequences": "Desacoplamiento, pero actualizaciones inesperadas.",
        },
        "strategy": {
            "name": "Strategy",
            "category": "Behavioral",
            "intent": "Intercambiar algoritmos dinamicamente.",
            "applicability": "Cuando se necesitan multiples variantes de un algoritmo.",
            "consequences": "Flexibilidad, pero mas clases.",
        },
        "factory": {
            "name": "Factory Method",
            "category": "Creational",
            "intent": "Crear objetos sin especificar la clase exacta.",
            "applicability": "Cuando la creacion debe ser flexible.",
            "consequences": "Desacoplamiento de creacion.",
        },
        "decorator": {
            "name": "Decorator",
            "category": "Structural",
            "intent": "Agregar comportamiento dinamicamente.",
            "applicability": "Cuando se necesita extender sin herencia.",
            "consequences": "Flexibilidad, pero mas objetos.",
        },
        "adapter": {
            "name": "Adapter",
            "category": "Structural",
            "intent": "Compatibilidad entre interfaces.",
            "applicability": "Cuando se necesita integrar interfaces incompatibles.",
            "consequences": "Integracion sin modificar codigo existente.",
        },
    }

    key = pattern_name.lower().replace(" ", "_")
    if key in patterns:
        return patterns[key]
    return {
        "name": "Unknown",
        "category": "Unknown",
        "intent": f"Pattern '{pattern_name}' not found in catalog.",
        "applicability": "",
        "consequences": "",
    }


def compare_patterns(pattern_a: str, pattern_b: str) -> dict[str, Any]:
    """Compara dos patrones de diseno."""
    info_a = get_pattern_info(pattern_a)
    info_b = get_pattern_info(pattern_b)

    same_category = info_a["category"] == info_b["category"]

    return {
        "pattern_a": info_a,
        "pattern_b": info_b,
        "same_category": same_category,
        "comparison": f"{info_a['name']} ({info_a['category']}) vs {info_b['name']} ({info_b['category']})",
    }


def generate_pattern_test(pattern_name: str) -> str:
    """Genera un test basico para un patron."""
    name = pattern_name.lower()

    if name == "singleton":
        return "\n".join([
            "def test_singleton_single_instance():",
            "    s1 = Singleton()",
            "    s2 = Singleton()",
            "    assert s1 is s2",
        ])
    elif name == "observer":
        return "\n".join([
            "def test_observer_notification():",
            "    class Spy:",
            "        def __init__(self):",
            "            self.events = []",
            "        def update(self, event):",
            "            self.events.append(event)",
            "    subject = Subject()",
            "    spy = Spy()",
            "    subject.attach(spy)",
            "    subject.notify('test')",
            "    assert spy.events == ['test']",
        ])
    elif name == "strategy":
        return "\n".join([
            "def test_strategy_swap():",
            "    class Ascending:",
            "        def sort(self, data): return sorted(data)",
            "    class Descending:",
            "        def sort(self, data): return sorted(data, reverse=True)",
            "    ctx = Context(Ascending())",
            "    assert ctx.execute([3, 1, 2]) == [1, 2, 3]",
            "    ctx.set_strategy(Descending())",
            "    assert ctx.execute([3, 1, 2]) == [3, 2, 1]",
        ])
    else:
        return f"# Test template for '{pattern_name}' not available. Try: singleton, observer, strategy"


def export_pattern_catalog() -> dict[str, Any]:
    """Exporta el catalogo completo de patrones."""
    all_patterns = list_patterns()
    by_category: dict[str, list] = {}

    for p in all_patterns:
        by_category.setdefault(p["category"], []).append(p)

    return {
        "total_patterns": len(all_patterns),
        "categories": list(by_category.keys()),
        "by_category": by_category,
    }


def get_pattern_stats() -> dict[str, Any]:
    """Retorna estadisticas del catalogo de patrones."""
    all_patterns = list_patterns()
    by_category: dict[str, int] = {}

    for p in all_patterns:
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1

    return {
        "total_patterns": len(all_patterns),
        "by_category": by_category,
        "categories_count": len(by_category),
    }


def get_pattern_examples(pattern_name: str) -> dict[str, Any]:
    """Retorna ejemplos de uso de un patron."""
    examples = {
        "singleton": {
            "use_cases": ["Database connection", "Logger", "Configuration manager"],
            "python_example": "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
            "when_to_use": "Cuando se necesita exactamente una instancia compartida.",
            "when_not_to_use": "Cuando se necesita testabilidad o inyeccion de dependencias.",
        },
        "observer": {
            "use_cases": ["Event systems", "GUI updates", "Pub/sub messaging"],
            "python_example": "class Subject:\n    def __init__(self):\n        self._observers = []\n    def notify(self, event):\n        for obs in self._observers:\n            obs.update(event)",
            "when_to_use": "Cuando cambios en un objeto deben notificar a otros.",
            "when_not_to_use": "Cuando la notificacion causa efectos en cascada incontrolables.",
        },
        "strategy": {
            "use_cases": ["Sorting algorithms", "Payment methods", "Compression strategies"],
            "python_example": "class Context:\n    def __init__(self, strategy):\n        self._strategy = strategy\n    def execute(self, data):\n        return self._strategy.process(data)",
            "when_to_use": "Cuando se necesitan multiples variantes de un algoritmo.",
            "when_not_to_use": "Cuando solo hay una forma de hacer algo.",
        },
    }

    key = pattern_name.lower().replace(" ", "_")
    if key in examples:
        return {"pattern": pattern_name, **examples[key]}
    return {
        "pattern": pattern_name,
        "use_cases": [],
        "python_example": "",
        "when_to_use": f"No examples available for '{pattern_name}'.",
        "when_not_to_use": "",
    }


def validate_pattern_usage(file_path: Path, pattern_name: str) -> dict[str, Any]:
    """Valida si un patron esta correctamente implementado en un archivo."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    name = pattern_name.lower()
    findings: list[dict[str, Any]] = []

    if name == "singleton":
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_new = any(isinstance(n, ast.FunctionDef) and n.name == "__new__" for n in ast.walk(node))
                has_instance_attr = "_instance" in content
                if has_new and has_instance_attr:
                    findings.append({
                        "check": "Singleton pattern detected",
                        "valid": True,
                        "detail": f"Class '{node.name}' implements Singleton correctly.",
                    })
                elif has_new or has_instance_attr:
                    findings.append({
                        "check": "Partial Singleton implementation",
                        "valid": False,
                        "detail": f"Class '{node.name}' has partial Singleton. Missing __new__ or _instance.",
                    })

    elif name == "observer":
        has_list = False
        has_notify = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for n in ast.walk(node):
                    if isinstance(n, ast.FunctionDef) and n.name in ("notify", "update", "attach", "detach"):
                        has_notify = True
                    if isinstance(n, ast.Assign):
                        for target in n.targets:
                            if isinstance(target, ast.Name) and "observer" in target.id.lower():
                                has_list = True

        if has_notify:
            findings.append({"check": "Observer methods detected", "valid": True, "detail": "Found notify/update/attach methods."})
        else:
            findings.append({"check": "No Observer methods found", "valid": False, "detail": "No notify/update/attach methods detected."})

    elif name == "strategy":
        has_protocol = "Protocol" in content or "ABC" in content
        has_context = "Context" in content or "context" in content
        if has_protocol:
            findings.append({"check": "Strategy interface detected", "valid": True, "detail": "Found Protocol or ABC for strategy."})
        if has_context:
            findings.append({"check": "Context class detected", "valid": True, "detail": "Found Context class."})
        if not findings:
            findings.append({"check": "No Strategy pattern detected", "valid": False, "detail": "No Strategy pattern elements found."})

    if not findings:
        findings.append({
            "check": f"Pattern '{pattern_name}' validation not implemented",
            "valid": False,
            "detail": f"Cannot validate '{pattern_name}'. Try: singleton, observer, strategy.",
        })

    all_valid = all(f["valid"] for f in findings)

    return {
        "file": file_path.name,
        "pattern": pattern_name,
        "all_checks_passed": all_valid,
        "findings": findings,
    }
