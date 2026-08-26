#!/bin/bash
# trigger-n8n-workflow.sh
# Ejecuta el workflow "Monitor Cluster Health v3" via n8n internal API
# Uso: bash trigger-n8n-workflow.sh

N8N_HOST="http://n8n.mrrobot.fs"
WORKFLOW_ID="c3d4e5f6-a7b8-9012-cdef-345678901234"
EMAIL="inggermantics@gmail.com"
PASS="N8nAdmin123!"

echo "=== Login to n8n ==="
LOGIN_RESP=$(curl -s -D - -X POST "${N8N_HOST}/rest/login" \
  -H "Content-Type: application/json" \
  -d "{\"emailOrLdapLoginId\":\"${EMAIL}\",\"password\":\"${PASS}\"}" 2>&1)

COOKIE=$(echo "$LOGIN_RESP" | grep -oi 'set-cookie: n8n-auth=[^;]*' | head -1 | sed 's/set-cookie: //I')

if [ -z "$COOKIE" ]; then
  echo "ERROR: Login failed"
  echo "$LOGIN_RESP"
  exit 1
fi

echo "Login OK"

echo "=== Execute workflow ==="
EXEC_RESP=$(curl -s -X POST "${N8N_HOST}/rest/workflows/${WORKFLOW_ID}/run" \
  -H "Content-Type: application/json" \
  -H "Cookie: ${COOKIE}" \
  -d '{"triggerToStartFrom":{"name":"Manual Trigger"}}' 2>&1)

echo "Response:"
echo "$EXEC_RESP" | head -20
echo ""
echo "=== Done ==="
