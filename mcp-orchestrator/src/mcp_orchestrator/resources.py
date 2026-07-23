"""Resources de solo lectura para mcp-orchestrator."""

from __future__ import annotations

import json


def orchestrator_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-orchestrator",
            "version": "1.0.0",
            "dags_path": "./dags",
        },
        indent=2,
        ensure_ascii=False,
    )


def orchestrator_airflow_guide() -> str:
    return (
        "# Guia Apache Airflow\n\n"
        "## Conceptos\n"
        "- DAG: Directed Acyclic Graph (flujo de trabajo)\n"
        "- Task: unidad de ejecucion dentro de un DAG\n"
        "- Operator: tipo de task (BashOperator, PythonOperator, etc)\n"
        "- Scheduler: ejecuta DAGs segun schedule\n"
        "- Executor: tipo de ejecucion (Sequential, Local, Celery, Kubernetes)\n\n"
        "## Estructura de un DAG\n"
        "- Importar DAG y operadores\n"
        "- Definir default_args\n"
        "- Instanciar DAG con contexto manager\n"
        "- Crear tasks con operadores\n"
        "- Definir dependencias con >> y <<\n\n"
        "## Ejemplo\n"
        "with DAG('my_dag', schedule_interval='@daily') as dag:\n"
        "    t1 = BashOperator(task_id='extract', bash_command='...')\n"
        "    t2 = PythonOperator(task_id='transform', python_callable=fn)\n"
        "    t1 >> t2"
    )


def orchestrator_dag_patterns() -> str:
    return (
        "# Patrones de DAGs\n\n"
        "## Secuencia lineal\n"
        "t1 >> t2 >> t3\n\n"
        "## Fan-out (paralelo)\n"
        "t1 >> [t2, t3, t4]\n\n"
        "## Fan-in (reunion)\n"
        "[t1, t2, t3] >> t4\n\n"
        "## Diamond\n"
        "t1 >> [t2, t3] >> t4\n\n"
        "## Branching\n"
        "Usar BranchPythonOperator para ejecucion condicional\n\n"
        "## SubDAGs\n"
        "- Encapsular sub-flujos repetidos\n"
        "- Mejor usar TaskGroup en Airflow 2.x\n\n"
        "## Task Groups\n"
        "- Agrupar tareas visualmente\n"
        "- Reutilizar grupos en multiples DAGs"
    )


def orchestrator_best_practices() -> str:
    return (
        "# Mejores practicas orquestacion\n\n"
        "1. DAGs idempotentes\n"
        "2. Tasks pequenas y enfocadas\n"
        "3. Usar XCom para datos pequenos\n"
        "4. Evitar logica compleja en DAGs\n"
        "5. Parametrizar con Variables y Connections\n"
        "6. Usar pools para limitar concurrencia\n"
        "7. Configurar retries y timeout\n"
        "8. Monitorear con SLAs y alerts\n"
        "9. Versionar DAGs en git\n"
        "10. Testear DAGs antes de produccion"
    )


def orchestrator_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- orch_parse_airflow_dag(filename)\n"
        "- orch_validate_dag(edges)\n"
        "- orch_generate_boilerplate(dag_id, tasks)\n"
        "- orch_list_dags()\n"
        "- orch_analyze_dag_dependencies(filename)\n"
        "- orch_generate_task_group(name, tasks)\n\n"
        "## Variables .env\n"
        "- ORCH_DAGS_PATH"
    )


def orchestrator_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del orquestador"},
                {"code": -32001, "description": "FileNotFoundError: DAG no encontrado"},
                {"code": -32002, "description": "ParseError: error de sintaxis Python"},
                {"code": -32003, "description": "ValidationError: DAG invalido"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def orchestrator_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## DAG no encontrado\n"
        "- Verificar ORCH_DAGS_PATH\n"
        "- Usar nombre relativo al directorio\n\n"
        "## Error de parseo\n"
        "- Verificar sintaxis Python valida\n"
        "- El archivo debe ser .py\n\n"
        "## Ciclo detectado\n"
        "- Revisar dependencias con orch_validate_dag\n"
        "- Eliminar arista que causa el ciclo\n\n"
        "## DAG no ejecuta\n"
        "- Verificar schedule_interval\n"
        "- Revisar start_date\n"
        "- Verificar que el scheduler esta corriendo"
    )


def orchestrator_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Parsear DAG\n"
        'orch_parse_airflow_dag(filename="etl_dag.py")\n\n'
        "## Ejemplo 2: Validar DAG\n"
        'orch_validate_dag(edges=[("extract", "transform"), ("transform", "load")])\n\n'
        "## Ejemplo 3: Generar boilerplate\n"
        'orch_generate_boilerplate(dag_id="etl", tasks=["extract", "transform", "load"])\n\n'
        "## Ejemplo 4: Listar DAGs\n"
        "orch_list_dags()"
    )


def orchestrator_scheduling() -> str:
    return (
        "# Scheduling en orquestadores\n\n"
        "## Cron expressions\n"
        "- @daily: cada dia a medianoche\n"
        "- @hourly: cada hora\n"
        "- 0 0 * * 0: cada domingo\n\n"
        "## Timedelta\n"
        "- timedelta(days=1): diario\n"
        "- timedelta(hours=6): cada 6 horas\n"
        "- timedelta(weeks=1): semanal\n\n"
        "## Best practices\n"
        "- Usar start_date estatica, no dynamic\n"
        "- catchup=False para no ejecutar backlog\n"
        "- Considerar zona horaria\n"
        "- Evitar schedules superpuestos"
    )


def orchestrator_xcom() -> str:
    return (
        "# XCom (Cross-Communication)\n\n"
        "## Concepto\n"
        "- Intercambio de datos entre tasks\n"
        "- Limitado a datos pequenos (<2MB)\n"
        "- Push: ti.xcom_push(key, value)\n"
        "- Pull: ti.xcom_pull(task_ids, key)\n\n"
        "## Cuando usar\n"
        "- Pasar IDs o metadatos pequenos\n"
        "- Senales entre tasks\n\n"
        "## Cuando NO usar\n"
        "- DataFrames grandes (usar almacenamiento externo)\n"
        "- Archivos (usar rutas)\n\n"
        "## Alternativas\n"
        "- S3/GCS para datos grandes\n"
        "- Variables de Airflow para config\n"
        "- Base de datos para estado compartido"
    )


def orchestrator_operators() -> str:
    return (
        "# Operadores de Airflow\n\n"
        "## Basicos\n"
        "- BashOperator: ejecuta comando bash\n"
        "- PythonOperator: ejecuta funcion Python\n"
        "- EmailOperator: envia email\n"
        "- HTTPOperator: llama API REST\n\n"
        "## Transfer\n"
        "- S3ToRedshiftOperator\n"
        "- GCSToBigQueryOperator\n"
        "- SqlToS3Operator\n\n"
        "## Sensors\n"
        "- S3KeySensor: espera archivo en S3\n"
        "- SqlSensor: espera condicion SQL\n"
        "- TimeDeltaSensor: espera tiempo\n"
        "- ExternalTaskSensor: espera otro DAG\n\n"
        "## Especiales\n"
        "- BranchPythonOperator: branching\n"
        "- SubDagOperator: sub-DAGs\n"
        "- TaskFlowOperator: API funcional"
    )


def orchestrator_testing() -> str:
    return (
        "# Testing de DAGs\n\n"
        "## Tipos de tests\n"
        "1. DAG structure: verificar tasks y dependencias\n"
        "2. Custom logic: testear funciones Python\n"
        "3. Integration: testear con servicios reales\n\n"
        "## Framework\n"
        "- pytest + airflow.utils.dag_test\n"
        "- Mock operadores y conexiones\n"
        "- Verificar DAG validity\n\n"
        "## Ejemplo\n"
        "def test_dag_structure():\n"
        "    dag = DAG('test')\n"
        "    assert len(dag.tasks) == 3\n"
        "    assert dag.has_task('extract')\n\n"
        "## CI/CD\n"
        "- Lint DAGs en PR\n"
        "- Test en pre-commit\n"
        "- Deploy a staging antes de produccion"
    )


def orchestrator_monitoring() -> str:
    return (
        "# Monitoring de orquestacion\n\n"
        "## Metricas clave\n"
        "- DAG runs: exitosas vs fallidas\n"
        "- Task duration: p50, p95, p99\n"
        "- Queue size: tasks esperando\n"
        "- SLA misses: tasks fuera de tiempo\n\n"
        "## Alerting\n"
        "- Email on failure\n"
        "- Slack/PagerDuty para criticos\n"
        "- SLA callbacks\n\n"
        "## Dashboards\n"
        "- Airflow UI: Grafana\n"
        "- Task duration trends\n"
        "- Success rate por DAG\n\n"
        "## Logs\n"
        "- Centralizados (ELK, CloudWatch)\n"
        "- Correlacion con traces\n"
        "- Retencion configurable"
    )


def orchestrator_ci_cd() -> str:
    return (
        "# CI/CD para DAGs\n\n"
        "## Workflow\n"
        "1. Developer crea DAG en rama feature\n"
        "2. PR trigger: lint + tests\n"
        "3. Merge a main: deploy a staging\n"
        "4. Validacion en staging\n"
        "5. Promover a produccion\n\n"
        "## Tools\n"
        "- Git: versionado\n"
        "- pytest: tests unitarios\n"
        "- ruff: linting\n"
        "- airflow dags test: validacion\n\n"
        "## Estrategias\n"
        "- Blue-green: dos ambientes\n"
        "- Canary: DAG nuevo en pausa\n"
        "- GitOps: deploy via git merge"
    )


def orchestrator_security() -> str:
    return (
        "# Seguridad en orquestacion\n\n"
        "## Connections\n"
        "- Usar Airflow Connections, no hardcoded\n"
        "- Backend: Vault, AWS Secrets Manager\n"
        "- Rotar credenciales regularmente\n\n"
        "## RBAC\n"
        "- Roles por equipo\n"
        "- Permisos minimos\n"
        "- Auditar accesos\n\n"
        "## DAG security\n"
        "- No ejecutar codigo no confiable\n"
        "- Sanitizar parametros de entrada\n"
        "- Limitar recursos por task\n\n"
        "## Network\n"
        "- VPC isolation\n"
        "- Secrets en env vars\n"
        "- TLS para comunicaciones"
    )
