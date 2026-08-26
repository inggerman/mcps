#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
USER=$(kubectl get secret kube-prometheus-stack-grafana -n observability -o jsonpath='{.data.admin-user}' | base64 -d)
PASS=$(kubectl get secret kube-prometheus-stack-grafana -n observability -o jsonpath='{.data.admin-password}' | base64 -d)
echo "User: $USER"
echo "Pass: $PASS"
