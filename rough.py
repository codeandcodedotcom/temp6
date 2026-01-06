- task: CmdLine@2
  displayName: "DEBUG – Show Pods"
  inputs:
    script: |
      echo "Listing pods"
      kubectl get pods -n apd-lit
      echo "Describing pods"
      kubectl describe pods -n apd-lit
