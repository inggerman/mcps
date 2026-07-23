"""Resources de solo lectura para mcp-terraform."""

from __future__ import annotations

import json


def terraform_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-terraform",
            "version": "1.0.0",
            "project_path": ".",
            "transport": "stdio",
        },
        indent=2,
        ensure_ascii=False,
    )


def terraform_basics() -> str:
    return (
        "# Terraform Basics\n\n"
        "## Conceptos\n"
        "- Provider: plugin que gestiona un cloud (AWS, GCP, Azure)\n"
        "- Resource: unidad de infraestructura (instance, vpc, bucket)\n"
        "- State: archivo que mapea recursos TF a recursos reales\n"
        "- Module: coleccion reutilizable de recursos\n"
        "- Variable: input parametrizable\n"
        "- Output: valor de salida\n\n"
        "## Ciclo de vida\n"
        "1. terraform init: inicializa directorio\n"
        "2. terraform plan: muestra cambios planeados\n"
        "3. terraform apply: aplica cambios\n"
        "4. terraform destroy: elimina infraestructura\n\n"
        "## HCL (HashiCorp Configuration Language)\n"
        "- Lenguaje declarativo\n"
        "- Sintaxis: resource \"type\" \"name\" { ... }\n"
        "- Bloques: resource, data, variable, output, provider, module\n"
        "- Funciones: file(), count(), for_each(), dynamic()"
    )


def terraform_best_practices() -> str:
    return (
        "# Terraform Best Practices\n\n"
        "## Estructura\n"
        "- Un modulo por componente logico\n"
        "- Separar environments (dev, staging, prod)\n"
        "- main.tf, variables.tf, outputs.tf por modulo\n"
        "- versions.tf para constraints\n\n"
        "## State\n"
        "- Backend remoto (S3, GCS, Azure Blob)\n"
        "- State locking (DynamoDB, GCS)\n"
        "- No commitear terraform.tfstate\n"
        "- Usar workspaces para environments\n\n"
        "## Variables\n"
        "- Usar variables para parametrizar\n"
        "- Defaults seguros\n"
        "- Validation en variables\n"
        "- tfvars por entorno\n"
        "- No hardcodear secrets\n\n"
        "## Modulos\n"
        "- Versionar modulos\n"
        "- Usar source con tag\n"
        "- Documentar inputs y outputs\n"
        "- Reutilizar modulos de la comunidad\n\n"
        "## Seguridad\n"
        "- No secrets en codigo\n"
        "- Usar sensitive = true\n"
        "- Backend con encryption\n"
        "- RBAC para state access"
    )


def terraform_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- tf_run_cmd(args)\n"
        "- tf_init(backend, upgrade)\n"
        "- tf_plan(destroy, var_file)\n"
        "- tf_validate()\n"
        "- tf_apply(auto_approve, var_file)\n"
        "- tf_destroy(auto_approve)\n"
        "- tf_fmt(check, recursive)\n"
        "- tf_show(plan_file)\n"
        "- tf_output(json_format)\n"
        "- tf_state_list()\n"
        "- tf_workspace_list()\n"
        "- tf_workspace_select(workspace)\n"
        "- tf_import(resource_addr, resource_id)\n"
        "- tf_taint(resource_addr)\n"
        "- tf_graph(plan)\n\n"
        "## Variables .env\n"
        "- TF_PROJECT_PATH\n"
        "- TF_MCP_TRANSPORT\n"
        "- TF_MCP_PORT"
    )


def terraform_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Terraform CLI no encontrado"},
                {"code": -32002, "description": "Error ejecutando terraform"},
                {"code": -32003, "description": "State lock error"},
                {"code": -32004, "description": "Backend no configurado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def terraform_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## terraform init falla\n"
        "- Verificar configuracion de backend\n"
        "- Verificar credenciales del cloud\n"
        "- Verificar conectividad de red\n"
        "- Probar con -upgrade\n\n"
        "## State lock error\n"
        "- Verificar que no hay otra ejecucion\n"
        "- terraform force-unlock si es seguro\n"
        "- Verificar tabla de locking (DynamoDB)\n"
        "- Verificar permisos IAM\n\n"
        "## plan muestra cambios inesperados\n"
        "- Verificar que el state este actualizado\n"
        "- terraform refresh\n"
        "- Verificar variables y tfvars\n"
        "- Verificar version del provider\n\n"
        "## apply falla\n"
        "- Revisar error de la API del cloud\n"
        "- Verificar cuotas del cloud\n"
        "- Verificar permisos IAM\n"
        "- Revisar dependencias circulares\n\n"
        "## fmt encuentra diferencias\n"
        "- Ejecutar terraform fmt -recursive\n"
        "- Configurar pre-commit hook\n"
        "- Usar editor con soporte HCL"
    )


def terraform_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Init\n"
        'tf_init(backend=True, upgrade=True)\n\n'
        "## Plan\n"
        'tf_plan(destroy=False, var_file="dev.tfvars")\n\n'
        "## Apply\n"
        "tf_apply(auto_approve=True)\n\n"
        "## Validate\n"
        "tf_validate()\n\n"
        "## Fmt check\n"
        "tf_fmt(check=True)\n\n"
        "## Import recurso existente\n"
        'tf_import(resource_addr="aws_instance.web", resource_id="i-123456")\n\n'
        "## Workspace\n"
        'tf_workspace_select(workspace="staging")'
    )


def terraform_state_management() -> str:
    return (
        "# Terraform State Management\n\n"
        "## Backends\n"
        "- local: archivo en disco (no recomendado para prod)\n"
        "- S3: AWS S3 + DynamoDB locking\n"
        "- GCS: Google Cloud Storage\n"
        "- Azure: Azure Blob Storage\n"
        "- Remote: Terraform Cloud/Enterprise\n\n"
        "## Comandos de state\n"
        "- terraform state list: lista recursos\n"
        "- terraform state show <addr>: muestra un recurso\n"
        "- terraform state mv: renombra un recurso\n"
        "- terraform state rm: elimina del state\n"
        "- terraform state pull: descarga state\n"
        "- terraform state push: sube state\n\n"
        "## Mejores practicas\n"
        "- Backend remoto siempre\n"
        "- State locking obligatorio\n"
        "- No editar state manualmente\n"
        "- Usar terraform import para recursos existentes\n"
        "- Backup regular del state\n\n"
        "## Workspaces\n"
        "- Aislar environments\n"
        "- default workspace siempre existe\n"
        "- terraform workspace new/select/list\n"
        "- No confundir con Terraform Cloud workspaces"
    )


def terraform_modules() -> str:
    return (
        "# Terraform Modules\n\n"
        "## Estructura\n"
        "```\n"
        "modules/\n"
        "  vpc/\n"
        "    main.tf\n"
        "    variables.tf\n"
        "    outputs.tf\n"
        "    versions.tf\n"
        "```\n\n"
        "## Uso\n"
        "```hcl\n"
        "module \"vpc\" {\n"
        "  source  = \"terraform-aws-modules/vpc/aws\"\n"
        "  version = \"5.0.0\"\n"
        "  cidr    = \"10.0.0.0/16\"\n"
        "}\n"
        "```\n\n"
        "## Tipos de source\n"
        "- Local: ./modules/vpc\n"
        "- Registry: terraform-aws-modules/vpc/aws\n"
        "- Git: git::https://github.com/...\n"
        "- S3: s3::https://...\n\n"
        "## Mejores practicas\n"
        "- Versionar modulos con semver\n"
        "- Documentar inputs/outputs\n"
        "- Usar for_each para multiples instancias\n"
        "- Validar inputs con validation blocks\n"
        "- Usar count para condicionales\n\n"
        "## Registry\n"
        "- Terraform Registry: modulos publicos\n"
        "- Private Registry: modulos privados\n"
        "- Verificar calidad y mantenimiento\n"
        "- Preferir modulos oficiales"
    )


def terraform_variables() -> str:
    return (
        "# Terraform Variables\n\n"
        "## Declaracion\n"
        "```hcl\n"
        "variable \"instance_type\" {\n"
        "  type        = string\n"
        "  default     = \"t3.micro\"\n"
        "  description = \"EC2 instance type\"\n"
        "  validation {\n"
        "    condition     = can(regex(\"^t[23]\\.\", var.instance_type))\n"
        "    error_message = \"Must be t2 or t3 family.\"\n"
        "  }\n"
        "  sensitive   = false\n"
        "}\n"
        "```\n\n"
        "## Tipos\n"
        "- string, number, bool\n"
        "- list(type), set(type)\n"
        "- map(type), object({...})\n"
        "- tuple([...])\n"
        "- any (no recomendado)\n\n"
        "## Asignacion\n"
        "- Default value\n"
        "- tfvars files\n"
        "- -var flag en CLI\n"
        "- TF_VAR_ environment variables\n"
        "- Variable definitions (.tfvars.json)\n\n"
        "## Sensitive\n"
        "- sensitive = true: oculta en output\n"
        "- No se muestra en plan\n"
        "- Aun se almacena en state\n"
        "- Usar vault para secrets reales"
    )


def terraform_providers() -> str:
    return (
        "# Terraform Providers\n\n"
        "## Providers comunes\n"
        "- aws: Amazon Web Services\n"
        "- azurerm: Microsoft Azure\n"
        "- google: Google Cloud Platform\n"
        "- kubernetes: Kubernetes\n"
        "- docker: Docker\n"
        "- github: GitHub\n"
        "- datadog: Datadog\n"
        "- random: utilidades\n"
        "- null: provisioners\n"
        "- archive: zip/tar\n\n"
        "## Configuracion\n"
        "```hcl\n"
        "provider \"aws\" {\n"
        "  region = \"us-east-1\"\n"
        "  profile = \"production\"\n"
        "  default_tags {\n"
        "    tags = { Project = \"myapp\" }\n"
        "  }\n"
        "}\n"
        "```\n\n"
        "## Versiones\n"
        "- required_providers en versions.tf\n"
        "- version constraints: ~> 5.0, >= 5.0, <= 5.5\n"
        "- Pin version para reproducibilidad\n\n"
        "## Multi-provider\n"
        "- alias para multiples instancias\n"
        "- provider \"aws\" { alias = \"west\" }\n"
        "- provider = aws.west en resource\n\n"
        "## Authentication\n"
        "- Environment variables\n"
        "- Shared credentials file\n"
        "- IAM roles (EC2, EKS)\n"
        "- OIDC (GitHub Actions)"
    )


def terraform_workspaces() -> str:
    return (
        "# Terraform Workspaces\n\n"
        "## Concepto\n"
        "- Mismo config, diferente state\n"
        "- Util para environments similares\n"
        "- No recomendado para prod vs dev muy diferentes\n\n"
        "## Comandos\n"
        "- terraform workspace new <name>\n"
        "- terraform workspace select <name>\n"
        "- terraform workspace list\n"
        "- terraform workspace delete <name>\n\n"
        "## Uso en HCL\n"
        "```hcl\n"
        "resource \"aws_instance\" \"web\" {\n"
        "  count = terraform.workspace == \"prod\" ? 3 : 1\n"
        "  tags = {\n"
        "    Environment = terraform.workspace\n"
        "  }\n"
        "}\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Usar para environments similares\n"
        "- Para environments muy diferentes, usar modulos separados\n"
        "- Nombrar workspaces consistentemente\n"
        "- default workspace para dev local\n\n"
        "## Alternativas\n"
        "- Directorios separados por environment\n"
        "- Terragrunt con hcl files por environment\n"
        "- Terraform Cloud workspaces"
    )


def terraform_ci_cd() -> str:
    return (
        "# Terraform CI/CD\n\n"
        "## GitHub Actions\n"
        "- actions/checkout\n"
        "- hashicorp/setup-terraform\n"
        "- terraform init, plan, apply\n"
        "- PR comments con plan output\n\n"
        "## GitLab CI\n"
        "- terraform image\n"
        "- stages: validate, plan, apply\n"
        "- Manual approval para apply\n\n"
        "## Mejores practicas\n"
        "- Validar en PR (fmt, validate, plan)\n"
        "- Apply solo en merge a main\n"
        "- Usar OIDC para auth sin secrets\n"
        "- Cachear .terraform directory\n"
        "- Plan output como comment en PR\n\n"
        "## Terragrunt\n"
        "- Wrapper para Terraform\n"
        "- DRY configuration\n"
        "- Multi-environment\n"
        "- Parallel execution\n"
        "- Remote state management\n\n"
        "## Atlantis\n"
        "- Terraform Pull Request automation\n"
        "- Plan on PR, apply on merge\n"
        "- Self-hosted\n"
        "- Policy checks con OPA"
    )


def terraform_security() -> str:
    return (
        "# Terraform Security\n\n"
        "## Secrets\n"
        "- No hardcodear secrets\n"
        "- Usar sensitive = true\n"
        "- Vault provider para secrets\n"
        "- AWS Secrets Manager / SSM Parameter Store\n"
        "- External data source para secrets\n\n"
        "## State Security\n"
        "- Backend con encryption at rest\n"
        "- IAM policies restrictivas\n"
        "- State locking para concurrencia\n"
        "- No commitear .tfstate\n"
        "- Auditar acceso al state\n\n"
        "## Code Security\n"
        "- tfsec: static analysis\n"
        "- checkov: policy-as-code\n"
        "- terrascan: compliance scanning\n"
        "- OPA/Conftest: policy checks\n\n"
        "## Provider Security\n"
        "- Pin provider versions\n"
        "- Usar OIDC cuando sea posible\n"
        "- Least privilege IAM\n"
        "- Rotar credenciales\n\n"
        "## Network Security\n"
        "- Security groups restrictivos\n"
        "- Private subnets para datos\n"
        "- NACLs para defense in depth\n"
        "- VPC endpoints para AWS services"
    )


def terraform_import() -> str:
    return (
        "# Terraform Import\n\n"
        "## Concepto\n"
        "- Importar recursos existentes al state\n"
        "- No genera codigo HCL automaticamente\n"
        "- Necesitas escribir el resource block manualmente\n\n"
        "## Comando\n"
        "```bash\n"
        "terraform import aws_instance.web i-1234567890\n"
        "```\n\n"
        "## Flujo recomendado\n"
        "1. Escribir el resource block en HCL\n"
        "2. terraform import para traer al state\n"
        "3. terraform plan para verificar drift\n"
        "4. Ajustar codigo hasta plan limpio\n\n"
        "## Import masivo\n"
        "- terraform import para cada recurso\n"
        "- Usar scripts para automatizar\n"
        "- Herramientas: terraformer, former2\n"
        "- Considerar terraform plan -refresh-only\n\n"
        "## Limitaciones\n"
        "- No importa codigo, solo state\n"
        "- Recursos importados pueden tener drift\n"
        "- Algunos recursos no soportan import\n"
        "- Data sources como alternativa\n\n"
        "## Mejores practicas\n"
        "- Importar antes de aplicar cambios\n"
        "- Verificar con plan despues de import\n"
        "- Documentar recursos importados\n"
        "- Usar import block (Terraform 1.5+)"
    )
