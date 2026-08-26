#!/bin/bash
# Script de validacion post-reinicio - verifica que toda la infra esta arriba
# Ejecutar despues de cualquier reinicio/hibernacion/suspension
export KUBECONFIG=/home/german/.kube/config

FAIL=0

echo "=========================================="
echo "  VALIDACION POST-REINICIO - $(date)"
echo "=========================================="
echo ""

# 1. Verificar k3s
echo -n "1. K3s service: "
if systemctl is-active k3s >/dev/null 2>&1; then
  echo "OK"
else
  echo "FAIL - k3s no activo"
  FAIL=1
fi

# 2. Verificar nodo
echo -n "2. Node ready: "
NODE_READY=$(kubectl get nodes --no-headers 2>/dev/null | awk '{print $2}')
if [ "$NODE_READY" = "Ready" ]; then
  echo "OK"
else
  echo "FAIL - nodo no ready"
  FAIL=1
fi

# 3. Verificar pods no running
echo -n "3. All pods running: "
NOT_RUNNING=$(kubectl get pods -A --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
if [ "$NOT_RUNNING" = "0" ]; then
  echo "OK"
else
  echo "FAIL - $NOT_RUNNING pods no running"
  kubectl get pods -A --field-selector=status.phase!=Running 2>&1
  FAIL=1
fi

# 4. Verificar servicios criticos
for NS in harbor gitea databases argocd n8n mcps minio rabbitmq; do
  echo -n "4.$NS: "
  NS_PODS=$(kubectl get pods -n $NS --no-headers 2>/dev/null | wc -l)
  NS_RUNNING=$(kubectl get pods -n $NS --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
  if [ "$NS_PODS" = "$NS_RUNNING" ] && [ "$NS_PODS" != "0" ]; then
    echo "OK ($NS_RUNNING/$NS_PODS)"
  elif [ "$NS_PODS" = "0" ]; then
    echo "WARN - sin pods"
  else
    echo "FAIL ($NS_RUNNING/$NS_PODS)"
    FAIL=1
  fi
done

echo ""

# 5. Total
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total pods: $TOTAL | Running: $RUNNING"
echo ""

if [ "$FAIL" = "0" ]; then
  echo "=========================================="
  echo "  RESULTADO: TODO OK"
  echo "=========================================="
else
  echo "=========================================="
  echo "  RESULTADO: HAY PROBLEMAS"
  echo "=========================================="
fi
echo ""
echo "DONE"
