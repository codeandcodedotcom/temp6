- task: CmdLine@2
  displayName: "DEBUG - Cluster diagnostics"
  inputs:
    script: |
      echo "Checking Helm release status..."
      helm status $(deploymentName) -n apd-lit || echo "Release not found"

      echo "Listing pods"
      kubectl get pods -n apd-lit

      echo "Describing pods"
      kubectl describe pods -n apd-lit

      echo "Listing events"
      kubectl get events -n apd-lit --sort-by=.metadata.creationTimestamp

      POD_NAMES=$(kubectl get pods -n apd-lit -o jsonpath='{.items[*].metadata.name}')
      for POD in $POD_NAMES; do
        echo "====== Logs for $POD ======"
        kubectl logs $POD -n apd-lit --tail=200 || true
      done
