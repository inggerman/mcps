"""Resources de solo lectura para mcp-object-storage."""

from __future__ import annotations

import json


def storage_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-object-storage",
            "version": "1.0.0",
            "endpoint_url": None,
            "region": "us-east-1",
            "allow_write": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def storage_s3_basics() -> str:
    return (
        "# S3 / Object Storage Basics\n\n"
        "## Conceptos\n"
        "- Bucket: contenedor de objetos\n"
        "- Object: archivo + metadata + key\n"
        "- Key: ruta del objeto en el bucket\n"
        "- Region: ubicacion del bucket\n\n"
        "## Operaciones basicas\n"
        "- Listar buckets\n"
        "- Listar objetos\n"
        "- Subir objeto\n"
        "- Descargar objeto\n"
        "- Eliminar objeto\n"
        "- Metadata de objeto\n\n"
        "## URLs pre-firmadas\n"
        "- Descarga: GET con expiracion\n"
        "- Subida: PUT con expiracion\n"
        "- Expiracion: 60s - 604800s (7 dias)"
    )


def storage_best_practices() -> str:
    return (
        "# Best Practices - Object Storage\n\n"
        "## Naming\n"
        "- Nombres de bucket unicos globalmente\n"
        "- Keys con / para estructura logica\n"
        "- Evitar caracteres especiales\n\n"
        "## Performance\n"
        "- Usar prefijos para paralelismo\n"
        "- Multipart upload para archivos grandes\n"
        "- Byte-range fetch para descargas parciales\n\n"
        "## Seguridad\n"
        "- Buckets privados por defecto\n"
        "- IAM policies restrictivas\n"
        "- Encryption at rest (SSE)\n"
        "- Encryption in transit (TLS)\n"
        "- Bucket policies explicitas\n\n"
        "## Costos\n"
        "- Lifecycle rules: mover a Glacier\n"
        "- Eliminar objetos viejos\n"
        "- Monitorear uso de storage\n"
        "- Usar Intelligent Tiering"
    )


def storage_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- storage_list_buckets()\n"
        "- storage_list_objects(bucket, prefix)\n"
        "- storage_object_metadata(bucket, key)\n"
        "- storage_presign_download(bucket, key)\n"
        "- storage_presign_upload(bucket, key)\n"
        "- storage_upload_text(bucket, key, content)\n"
        "- storage_delete_object(bucket, key)\n"
        "- storage_copy_object(src, dest)\n"
        "- storage_get_bucket_size(bucket)\n"
        "- storage_get_storage_metrics()\n\n"
        "## Variables .env\n"
        "- OBJECT_STORAGE_ENDPOINT_URL\n"
        "- OBJECT_STORAGE_REGION\n"
        "- OBJECT_STORAGE_PROFILE\n"
        "- OBJECT_STORAGE_ALLOW_WRITE"
    )


def storage_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "ValidationError: campo invalido"},
                {"code": -32002, "description": "NoSuchBucket: bucket no existe"},
                {"code": -32003, "description": "NoSuchKey: objeto no existe"},
                {"code": -32004, "description": "AccessDenied: sin permisos"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def storage_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## No se pueden listar buckets\n"
        "- Verificar credenciales AWS\n"
        "- Verificar endpoint_url\n"
        "- Verificar region\n\n"
        "## No se puede subir objeto\n"
        "- Verificar OBJECT_STORAGE_ALLOW_WRITE=true\n"
        "- Verificar permisos IAM\n"
        "- Verificar que el bucket existe\n\n"
        "## URL pre-firmada expira\n"
        "- Aumentar expires_seconds (max 604800)\n"
        "- Minimo 60 segundos\n\n"
        "## Error de acceso\n"
        "- Verificar bucket policy\n"
        "- Verificar IAM policy\n"
        "- Verificar que el bucket es accesible"
    )


def storage_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Listar buckets\n"
        "storage_list_buckets()\n\n"
        "## Listar objetos\n"
        'storage_list_objects(bucket="my-bucket", prefix="data/")\n\n'
        "## Metadata de objeto\n"
        'storage_object_metadata(bucket="my-bucket", key="file.txt")\n\n'
        "## URL de descarga\n"
        'storage_presign_download(bucket="my-bucket", key="file.txt")\n\n'
        "## Subir texto\n"
        'storage_upload_text(bucket="my-bucket", key="test.txt", content="hello")\n\n'
        "## Copiar objeto\n"
        'storage_copy_object(source_bucket="src", source_key="f.txt", dest_bucket="dst", dest_key="f.txt")'
    )


def storage_lifecycle() -> str:
    return (
        "# Lifecycle Rules\n\n"
        "## Tipos de transicion\n"
        "- Standard -> Standard-IA (30 dias)\n"
        "- Standard-IA -> Glacier (60 dias)\n"
        "- Glacier -> Deep Archive (90 dias)\n\n"
        "## Expiracion\n"
        "- Eliminar objetos despues de N dias\n"
        "- Eliminar versiones no actuales\n"
        "- Abortar multipart uploads incompletos\n\n"
        "## Configuracion\n"
        "```json\n"
        "{\n"
        "  \"Rules\": [\n"
        "    {\n"
        "      \"ID\": \"archive-old\",\n"
        "      \"Status\": \"Enabled\",\n"
        "      \"Filter\": {\"Prefix\": \"logs/\"},\n"
        "      \"Transitions\": [\n"
        "        {\"Days\": 30, \"StorageClass\": \"STANDARD_IA\"},\n"
        "        {\"Days\": 90, \"StorageClass\": \"GLACIER\"}\n"
        "      ],\n"
        "      \"Expiration\": {\"Days\": 365}\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )


def storage_security() -> str:
    return (
        "# Storage Security\n\n"
        "## Encryption at rest\n"
        "- SSE-S3: gestionado por S3\n"
        "- SSE-KMS: gestionado por KMS\n"
        "- SSE-C: claves del cliente\n\n"
        "## Encryption in transit\n"
        "- TLS/HTTPS obligatorio\n"
        "- Bucket policy: denyHTTP\n\n"
        "## Access Control\n"
        "- Bucket policies\n"
        "- IAM policies\n"
        "- ACLs (legacy)\n"
        "- Block Public Access\n\n"
        "## Versioning\n"
        "- Habilitar en buckets criticos\n"
        "- MFA Delete para proteccion\n"
        "- Lifecycle para versiones viejas\n\n"
        "## Logging\n"
        "- Server access logs\n"
        "- CloudTrail para API calls\n"
        "- S3 Events para notificaciones"
    )


def storage_multipart() -> str:
    return (
        "# Multipart Upload\n\n"
        "## Cuando usar\n"
        "- Archivos > 100MB\n"
        "- Uploads que pueden fallar\n"
        "- Uploads en paralelo\n\n"
        "## Proceso\n"
        "1. CreateMultipartUpload\n"
        "2. UploadPart (1-10000 partes, min 5MB excepto ultima)\n"
        "3. CompleteMultipartUpload o AbortMultipartUpload\n\n"
        "## Ventajas\n"
        "- Reanudar uploads fallidos\n"
        "- Paralelismo\n"
        "- Manejar archivos grandes\n\n"
        "## Configuracion\n"
        "- Part size: 5MB - 5GB\n"
        "- Max parts: 10000\n"
        "- Max object size: 5TB"
    )


def storage_replication() -> str:
    return (
        "# Replication\n\n"
        "## Cross-Region Replication (CRR)\n"
        "- Replicar a otra region\n"
        "- Disaster recovery\n"
        "- Latencia baja geografica\n\n"
        "## Same-Region Replication (SRR)\n"
        "- Replicar en misma region\n"
        "- Agregar logs\n"
        "- Compartir datos entre cuentas\n\n"
        "## Requisitos\n"
        "- Versioning habilitado en ambos buckets\n"
        "- IAM role con permisos\n"
        "- Replication configuration en origen\n\n"
        "## Configuracion\n"
        "```json\n"
        "{\n"
        "  \"Role\": \"arn:aws:iam::123:role/replication\",\n"
        "  \"Rules\": [\n"
        "    {\n"
        "      \"Status\": \"Enabled\",\n"
        "      \"Prefix\": \"\",\n"
        "      \"Destination\": {\n"
        "        \"Bucket\": \"arn:aws:s3:::dest-bucket\"\n"
        "      }\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )


def storage_cost_optimization() -> str:
    return (
        "# Cost Optimization\n\n"
        "## Storage Classes\n"
        "- Standard: acceso frecuente\n"
        "- Standard-IA: acceso infrecuente\n"
        "- One Zone-IA: una zona, mas barato\n"
        "- Glacier: archivo, minutos-horas retrieval\n"
        "- Deep Archive: mas barato, horas retrieval\n"
        "- Intelligent Tiering: automatico\n\n"
        "## Estrategias\n"
        "- Lifecycle rules para mover datos\n"
        "- Eliminar datos innecesarios\n"
        "- Comprimir antes de subir\n"
        "- Usar S3 Batch Operations\n\n"
        "## Monitoreo\n"
        "- S3 Storage Lens\n"
        "- CloudWatch metrics\n"
        "- Cost Explorer\n"
        "- Budgets y alerts"
    )


def storage_presigned_urls() -> str:
    return (
        "# Presigned URLs\n\n"
        "## Que son\n"
        "- URLs temporales con acceso limitado\n"
        "- No requieren credenciales AWS\n"
        "- Expiran automaticamente\n\n"
        "## Usos\n"
        "- Compartir archivos privados\n"
        "- Upload directo desde browser\n"
        "- Descarga temporal sin auth\n\n"
        "## Limites\n"
        "- Expiracion: 60s - 604800s (7 dias)\n"
        "- Solo para operaciones GET y PUT\n"
        "- No soportan todas las operaciones\n\n"
        "## Seguridad\n"
        "- Usar HTTPS\n"
        "- Minimizar tiempo de expiracion\n"
        "- No loguear URLs\n"
        "- Considerar IAM conditions"
    )


def storage_versioning() -> str:
    return (
        "# Versioning\n\n"
        "## Conceptos\n"
        "- Mantiene multiples versiones de un objeto\n"
        "- Protege contra sobrescritura y eliminacion\n"
        "- Cada version tiene un VersionId unico\n\n"
        "## Estados\n"
        "- Unversioned (default)\n"
        "- VersioningEnabled\n"
        "- VersioningSuspended\n\n"
        "## Operaciones\n"
        "- ListObjectVersions\n"
        "- GetObjectVersion\n"
        "- DeleteObjectVersion\n"
        "- RestoreObjectVersion\n\n"
        "## Mejores practicas\n"
        "- Habilitar en buckets criticos\n"
        "- MFA Delete para proteccion extra\n"
        "- Lifecycle para versiones viejas\n"
        "- NoncurrentVersionExpiration para limpiar"
    )


def storage_migration() -> str:
    return (
        "# Storage Migration\n\n"
        "## Herramientas\n"
        "- aws s3 sync: sincronizacion simple\n"
        "- S3 Batch Operations: operaciones masivas\n"
        "- DataSync: migracion a gran escala\n"
        "- Transfer Acceleration: uploads rapidos\n\n"
        "## Estrategias\n"
        "1. Analizar datos actuales\n"
        "2. Elegir storage class inicial\n"
        "3. Configurar lifecycle rules\n"
        "4. Migrar con sync o batch\n"
        "5. Verificar integridad\n"
        "6. Actualizar aplicaciones\n"
        "7. Eliminar origen\n\n"
        "## Consideraciones\n"
        "- Costos de transferencia\n"
        "- Tiempo de migracion\n"
        "- Integridad de datos (ETag)\n"
        "- Downtime o zero-downtime\n"
        "- Rollback plan"
    )
