"""Resources de solo lectura para mcp-personal-vault."""

from __future__ import annotations

import json


def vault_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-personal-vault",
            "version": "1.0.0",
            "database_path": "data/personal-vault/personal.db",
            "key_file": "data/personal-vault/vault.key",
            "allow_write": False,
            "allow_highly_sensitive": False,
            "allow_secrets": False,
            "max_results": 25,
        },
        indent=2,
        ensure_ascii=False,
    )


def vault_basics() -> str:
    return (
        "# Personal Vault Basics\n\n"
        "## Que es Personal Vault\n"
        "- Boveda local cifrada para contexto personal\n"
        "- Almacena preferencias, identidad, trayectoria, contactos\n"
        "- NO almacena contrasenas, tokens, PIN, CVV, llaves privadas\n"
        "- Cifrado con Fernet (AES-128-CBC + HMAC SHA256)\n\n"
        "## Sensitivity levels\n"
        "- public: visible por defecto\n"
        "- private: visible por defecto pero marcado\n"
        "- highly_sensitive: oculto salvo autorizacion explicita\n\n"
        "## Categories\n"
        "- preferences: preferencias del usuario\n"
        "- identity: informacion personal\n"
        "- contacts: contactos y redes\n"
        "- career: trayectoria profesional\n"
        "- goals: objetivos y metas\n"
        "- custom: categorias personalizadas\n\n"
        "## Tags\n"
        "- Etiquetas para busqueda y filtrado\n"
        "- Multiples tags por entrada\n"
        "- Tags unicos listados con list_tags\n\n"
        "## Source\n"
        "- user: ingresado por el usuario\n"
        "- import: importado de otra fuente\n"
        "- system: generado por el sistema\n\n"
        "## Audit log\n"
        "- Todas las operaciones se registran\n"
        "- Acciones: upsert, read, delete, search, clear, rotate\n"
        "- Consultable con get_audit_log"
    )


def vault_best_practices() -> str:
    return (
        "# Personal Vault Best Practices\n\n"
        "## Seguridad\n"
        "- No almacenar secrets (passwords, tokens, PIN)\n"
        "- Usar gestor de secretos dedicado\n"
        "- Cifrar la base de datos con Fernet\n"
        "- Proteger el archivo de clave (chmod 600)\n"
        "- Rotar la clave periodicamente\n\n"
        "## Sensitivity\n"
        "- Marcar datos sensibles como highly_sensitive\n"
        "- Requerir autorizacion explicita para revelar\n"
        "- No exponer highly_sensitive en logs\n"
        "- Revisar redacted en respuestas\n\n"
        "## Write protection\n"
        "- allow_write=false por defecto\n"
        "- Habilitar solo cuando sea necesario\n"
        "- Auditar escrituras con get_audit_log\n"
        "- Usar clear_category con precaucion\n\n"
        "## Backup\n"
        "- Hacer backup periodicamente\n"
        "- backup_vault copia la base de datos\n"
        "- Proteger backups con cifrado\n"
        "- Probar restauracion\n\n"
        "## Performance\n"
        "- Usar limit en list y search\n"
        "- Filtrar por categoria cuando sea posible\n"
        "- No exportar toda la boveda frecuentemente\n"
        "- Indexar por (category, entry_key)\n\n"
        "## Privacy\n"
        "- Minimizar datos almacenados\n"
        "- No almacenar datos innecesarios\n"
        "- Revisar y limpiar periodicamente\n"
        "- Usar redacted para proteccion en respuestas"
    )


def vault_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- personal_vault_status()\n"
        "- personal_upsert(category, key, value, sensitivity, tags)\n"
        "- personal_get(category, key, include_sensitive)\n"
        "- personal_list(category, limit)\n"
        "- search_personal_context(query, categories, include_sensitive)\n"
        "- personal_delete(category, key)\n"
        "- personal_export(category, include_sensitive)\n"
        "- personal_import(entries)\n"
        "- personal_audit_log(limit, action)\n"
        "- personal_list_categories()\n"
        "- personal_list_tags()\n"
        "- personal_backup(backup_path)\n"
        "- personal_clear_category(category)\n"
        "- personal_entry_history(category, key)\n"
        "- personal_rotate_key(new_key)\n\n"
        "## Variables .env\n"
        "- PERSONAL_VAULT_DATABASE_PATH\n"
        "- PERSONAL_VAULT_KEY_FILE\n"
        "- PERSONAL_VAULT_ENCRYPTION_KEY\n"
        "- PERSONAL_VAULT_ALLOW_WRITE\n"
        "- PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE\n"
        "- PERSONAL_VAULT_ALLOW_SECRETS"
    )


def vault_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Entrada no encontrada"},
                {"code": -32002, "description": "Escritura deshabilitada"},
                {"code": -32003, "description": "Secret rechazado"},
                {"code": -32004, "description": "Clave de cifrado invalida"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def vault_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Escritura deshabilitada\n"
        "- Set PERSONAL_VAULT_ALLOW_WRITE=true\n"
        "- Verificar configuracion\n\n"
        "## Secret rechazado\n"
        "- La boveda no almacena passwords, tokens, PIN\n"
        "- Usar gestor de secretos dedicado\n"
        "- Set PERSONAL_VAULT_ALLOW_SECRETS=true solo si es necesario\n\n"
        "## Entrada no encontrada\n"
        "- Verificar category y key\n"
        "- Usar personal_list para ver entradas\n"
        "- Usar search_personal_context para buscar\n\n"
        "## Clave invalida\n"
        "- Verificar PERSONAL_VAULT_ENCRYPTION_KEY\n"
        "- Verificar archivo de clave\n"
        "- Regenerar clave si es necesario (rotate_key)\n\n"
        "## Highly sensitive oculto\n"
        "- Set include_sensitive=true en la llamada\n"
        "- Set PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE=true\n"
        "- Ambos flags son requeridos\n\n"
        "## Base de datos corrupta\n"
        "- Restaurar desde backup\n"
        "- Usar personal_backup regularmente\n"
        "- Verificar integridad con personal_vault_status\n\n"
        "## Performance lento\n"
        "- Usar limit en list y search\n"
        "- Filtrar por categoria\n"
        "- Reducir max_results en config"
    )


def vault_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Guardar preferencia\n"
        'personal_upsert(category="preferences", key="editor", value={"name": "VS Code", "theme": "dark"}, tags=["tools"])\n\n'
        "## Obtener preferencia\n"
        'personal_get(category="preferences", key="editor")\n\n'
        "## Buscar contexto\n"
        'search_personal_context(query="editor", categories=["preferences"])\n\n'
        "## Listar entradas\n"
        'personal_list(category="preferences", limit=10)\n\n'
        "## Eliminar entrada\n"
        'personal_delete(category="preferences", key="editor")\n\n'
        "## Exportar boveda\n"
        'personal_export(category="preferences")\n\n'
        "## Importar entradas\n"
        'personal_import(entries=[{"category": "profile", "key": "name", "value": "Ada"}])\n\n'
        "## Ver audit log\n"
        'personal_audit_log(limit=20)\n\n'
        "## Listar categorias\n"
        "personal_list_categories()\n\n"
        "## Backup\n"
        'personal_backup(backup_path="/vault/backup.db")\n\n'
        "## Rotar clave\n"
        'personal_rotate_key(new_key="new-fernet-key-base64")'
    )


def vault_encryption() -> str:
    return (
        "# Vault Encryption Guide\n\n"
        "## Fernet\n"
        "- Cifrado simetrico autenticado\n"
        "- AES-128-CBC + HMAC SHA256\n"
        "- Clave base64 de 32 bytes\n"
        "- Generada con Fernet.generate_key()\n\n"
        "## Key management\n"
        "- PERSONAL_VAULT_ENCRYPTION_KEY: clave en env var\n"
        "- PERSONAL_VAULT_KEY_FILE: archivo de clave\n"
        "- Si hay env var, tiene prioridad\n"
        "- Si no, se lee del archivo\n"
        "- Si no existe, se genera automaticamente\n\n"
        "## Key rotation\n"
        "- personal_rotate_key re-encripta todas las entradas\n"
        "- Generar nueva clave: Fernet.generate_key()\n"
        "- Requiere allow_write=true\n"
        "- Auditable en audit log\n\n"
        "## Security considerations\n"
        "- Proteger archivo de clave (chmod 600)\n"
        "- No commitear claves al repositorio\n"
        "- Usar secrets manager en produccion\n"
        "- Backup de clave en lugar seguro\n\n"
        "## Encryption flow\n"
        "1. Value -> JSON serialize\n"
        "2. JSON -> Fernet encrypt\n"
        "3. Encrypted bytes -> SQLite BLOB\n\n"
        "## Decryption flow\n"
        "1. SQLite BLOB -> Fernet decrypt\n"
        "2. JSON parse -> Python object\n"
        "3. Return value to caller"
    )


def vault_categories() -> str:
    return (
        "# Vault Categories Guide\n\n"
        "## Categorias estandar\n"
        "- preferences: preferencias del usuario\n"
        "  - editor, theme, language, timezone\n"
        "- identity: informacion personal\n"
        "  - name, location, bio, avatar\n"
        "- contacts: contactos y redes\n"
        "  - email, phone, social_media\n"
        "- career: trayectoria profesional\n"
        "  - role, company, skills, experience\n"
        "- goals: objetivos y metas\n"
        "  - short_term, long_term, learning\n"
        "- custom: categorias personalizadas\n\n"
        "## Crear categoria\n"
        "- Usar personal_upsert con cualquier category\n"
        "- La categoria se crea automaticamente\n"
        "- No hay schema fijo para categorias\n\n"
        "## Gestionar categorias\n"
        "- personal_list_categories: ver todas\n"
        "- personal_list(category=X): ver entradas\n"
        "- personal_clear_category: eliminar todas\n"
        "- personal_export(category=X): exportar\n\n"
        "## Mejores practicas\n"
        "- Usar nombres descriptivos en lowercase\n"
        "- Mantener categorias cohesivas\n"
        "- No crear demasiadas categorias\n"
        "- Revisar y limpiar periodicamente\n\n"
        "## Tags vs Categories\n"
        "- Categories: agrupacion principal\n"
        "- Tags: etiquetas transversales\n"
        "- Tags pueden cruzar categorias\n"
        "- Usar tags para filtrado adicional"
    )


def vault_privacy() -> str:
    return (
        "# Vault Privacy Guide\n\n"
        "## Sensitivity levels\n"
        "- public: datos publicos (nombre, bio)\n"
        "- private: datos privados (email, telefono)\n"
        "- highly_sensitive: datos muy sensibles (government_id)\n\n"
        "## Access control\n"
        "- public y private: visibles por defecto\n"
        "- highly_sensitive: requiere include_sensitive=true\n"
        "- Y tambien PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE=true\n"
        "- Ambos flags deben estar activos\n\n"
        "## Redaction\n"
        "- Cuando no se puede revelar, value = [REDACTED]\n"
        "- redacted=true en la respuesta\n"
        "- Metadata (category, key, tags) siempre visible\n"
        "- Solo el value se oculta\n\n"
        "## Audit trail\n"
        "- Todas las operaciones se registran\n"
        "- read, upsert, delete, search, clear, rotate\n"
        "- personal_audit_log para consultar\n"
        "- Timestamp de cada operacion\n\n"
        "## Data minimization\n"
        "- Solo almacenar lo necesario\n"
        "- No almacenar datos sensibles innecesarios\n"
        "- Limpiar entradas obsoletas\n"
        "- Revisar periodicamente\n\n"
        "## No secrets policy\n"
        "- No passwords, tokens, PIN, CVV\n"
        "- No private keys, seed phrases, mnemonics\n"
        "- Pattern matching para detectar secrets\n"
        "- allow_secrets=false por defecto\n"
        "- Usar gestor de secretos dedicado"
    )


def vault_backup() -> str:
    return (
        "# Vault Backup Guide\n\n"
        "## Backup\n"
        "- personal_backup(backup_path): copia la DB\n"
        "- Copia completa de SQLite\n"
        "- Incluye todas las entradas y audit log\n"
        "- No incluye la clave de cifrado\n\n"
        "## Restore\n"
        "- Restaurar archivo de backup a database_path\n"
        "- Asegurar que la clave coincida\n"
        "- Si la clave cambio, usar rotate_key\n"
        "- Verificar con personal_vault_status\n\n"
        "## Backup strategy\n"
        "- Backups regulares (diario/semanal)\n"
        "- Multiple copias (local + remoto)\n"
        "- Cifrar backups en reposo\n"
        "- Probar restauracion periodicamente\n\n"
        "## Export/Import\n"
        "- personal_export: JSON plano de entradas\n"
        "- personal_import: cargar desde JSON\n"
        "- Util para migraciones\n"
        "- No incluye clave de cifrado\n\n"
        "## Key backup\n"
        "- Backupear clave separadamente\n"
        "- Almacenar en lugar seguro\n"
        "- No en el mismo lugar que la DB\n"
        "- Considerar secrets manager\n\n"
        "## Disaster recovery\n"
        "1. Restaurar DB desde backup\n"
        "2. Restaurar clave desde backup seguro\n"
        "3. Verificar con personal_vault_status\n"
        "4. Si clave cambio, usar rotate_key\n"
        "5. Verificar entradas con personal_list"
    )


def vault_api() -> str:
    return (
        "# Vault API Reference\n\n"
        "## Tools\n"
        "- personal_vault_status: metadata de la boveda\n"
        "- personal_upsert: crear/actualizar entrada\n"
        "- personal_get: leer una entrada\n"
        "- personal_list: listar entradas (metadata)\n"
        "- search_personal_context: buscar entradas\n"
        "- personal_delete: eliminar entrada\n"
        "- personal_export: exportar entradas\n"
        "- personal_import: importar entradas\n"
        "- personal_audit_log: ver log de auditoria\n"
        "- personal_list_categories: listar categorias\n"
        "- personal_list_tags: listar tags\n"
        "- personal_backup: crear backup\n"
        "- personal_clear_category: eliminar categoria\n"
        "- personal_entry_history: historial de entrada\n"
        "- personal_rotate_key: rotar clave de cifrado\n\n"
        "## Parameters\n"
        "- category: string (1-100 chars)\n"
        "- key: string (1-100 chars)\n"
        "- value: any JSON-serializable\n"
        "- sensitivity: public | private | highly_sensitive\n"
        "- tags: list[str]\n"
        "- include_sensitive: bool\n"
        "- limit: int (1-200)\n\n"
        "## Returns\n"
        "- status: saved | deleted | cleared | success\n"
        "- redacted: bool (si value fue oculto)\n"
        "- entries: list[dict] en export\n"
        "- history: list[dict] en entry_history\n"
        "- count: int en list/export"
    )


def vault_integration() -> str:
    return (
        "# Vault Integration Guide\n\n"
        "## MCP ecosystem\n"
        "- mcp-personal-vault: almacenamiento personal\n"
        "- mcp-orchestrator: coordina MCPs\n"
        "- mcp-llm-router: enruta a LLMs\n"
        "- mcp-observability: monitoreo\n\n"
        "## LLM integration\n"
        "- LLM usa search_personal_context para personalizar\n"
        "- LLM usa personal_upsert para guardar preferencias\n"
        "- LLM respeta sensitivity levels\n"
        "- LLM no debe almacenar secrets\n\n"
        "## Docker deployment\n"
        "- Volumen montado en /vault\n"
        "- PERSONAL_VAULT_DATABASE_PATH=/vault/personal.db\n"
        "- PERSONAL_VAULT_KEY_FILE=/vault/vault.key\n"
        "- Clave persistente entre restarts\n\n"
        "## CI/CD\n"
        "- No incluir claves en imagenes\n"
        "- Usar secrets en CI para tests\n"
        "- Backup antes de deploy\n"
        "- Health check con personal_vault_status\n\n"
        "## Multi-user\n"
        "- Una boveda por usuario\n"
        "- Clave unica por usuario\n"
        "- Isolation entre bovedas\n"
        "- No compartir claves\n\n"
        "## Security checklist\n"
        "- [ ] Clave protegida (chmod 600)\n"
        "- [ ] allow_write=false en produccion\n"
        "- [ ] allow_secrets=false\n"
        "- [ ] Backup regular configurado\n"
        "- [ ] Audit log monitoreado\n"
        "- [ ] Clave rotada periodicamente"
    )


def vault_security() -> str:
    return (
        "# Vault Security Guide\n\n"
        "## Threat model\n"
        "- Atacante con acceso al filesystem: necesita clave para descifrar\n"
        "- Atacante con acceso a memoria: puede leer datos descifrados\n"
        "- Atacante con acceso a red: MCP expone solo via HTTP local\n"
        "- Atacante con acceso a logs: audit log no incluye values\n\n"
        "## Encryption\n"
        "- Fernet: AES-128-CBC + HMAC SHA256\n"
        "- Clave de 32 bytes base64\n"
        "- No se almacena en la DB\n"
        "- Rotacion periódica recomendada\n\n"
        "## Access control\n"
        "- allow_write: protege contra escrituras accidentales\n"
        "- allow_highly_sensitive: protege datos sensibles\n"
        "- allow_secrets: bloquea almacenamiento de secrets\n"
        "- include_sensitive: flag por llamada para revelar\n\n"
        "## Secret detection\n"
        "- Pattern matching: password, token, api_key, pin, cvv\n"
        "- Bloquea antes de almacenar\n"
        "- allow_secrets=false por defecto\n"
        "- Mensaje claro: usar gestor de secretos\n\n"
        "## Audit\n"
        "- Todas las operaciones registradas\n"
        "- Timestamp, action, category, key\n"
        "- No se registran values\n"
        "- Consultable con personal_audit_log\n\n"
        "## Hardening\n"
        "- Ejecutar como usuario no-root\n"
        "- chmod 600 en archivo de clave\n"
        "- Volumen separado para /vault\n"
        "- Network isolation\n"
        "- No exponer puerto innecesariamente\n\n"
        "## Incident response\n"
        "1. Identificar entrada comprometida\n"
        "2. Eliminar con personal_delete\n"
        "3. Rotar clave con personal_rotate_key\n"
        "4. Revisar audit_log\n"
        "5. Restaurar desde backup si es necesario"
    )


def vault_data_model() -> str:
    return (
        "# Vault Data Model\n\n"
        "## entries table\n"
        "- id: INTEGER PRIMARY KEY AUTOINCREMENT\n"
        "- category: TEXT NOT NULL\n"
        "- entry_key: TEXT NOT NULL\n"
        "- encrypted_value: BLOB NOT NULL\n"
        "- sensitivity: TEXT NOT NULL (public|private|highly_sensitive)\n"
        "- tags: TEXT NOT NULL DEFAULT '[]' (JSON array)\n"
        "- source: TEXT NOT NULL DEFAULT 'user'\n"
        "- created_at: TEXT NOT NULL (ISO 8601)\n"
        "- updated_at: TEXT NOT NULL (ISO 8601)\n"
        "- UNIQUE(category, entry_key)\n\n"
        "## audit_log table\n"
        "- id: INTEGER PRIMARY KEY AUTOINCREMENT\n"
        "- action: TEXT NOT NULL (upsert|read|delete|search|clear|rotate)\n"
        "- category: TEXT (nullable)\n"
        "- entry_key: TEXT (nullable)\n"
        "- occurred_at: TEXT NOT NULL (ISO 8601)\n\n"
        "## Encryption\n"
        "- encrypted_value = Fernet.encrypt(JSON.serialize(value))\n"
        "- value can be any JSON-serializable type\n"
        "- Fernet: AES-128-CBC + HMAC SHA256\n\n"
        "## Indexes\n"
        "- Primary key on id\n"
        "- Unique constraint on (category, entry_key)\n"
        "- No additional indexes (small dataset)\n\n"
        "## Relationships\n"
        "- audit_log references entries by (category, entry_key)\n"
        "- No foreign keys (simplified for SQLite)\n"
        "- audit_log is append-only\n\n"
        "## Schema migration\n"
        "- initialize_database creates tables if not exist\n"
        "- No migration framework (manual for now)\n"
        "- Backup before schema changes\n"
        "- rotate_key for encryption changes"
    )
