# Kubernetes Pod CrashLoopBackOff Runbook

## Symptoms
- Pod shows "CrashLoopBackOff" status in `kubectl get pods`
- Container restarts repeatedly (visible in pod events)
- Logs show exit code 1, 127, or 137
- Pod unable to reach readiness probe

## Root Causes
1. **Out of Memory (OOM)** — container killed by kubelet (exit 137)
2. **Application crash** — code throws unhandled exception (exit 1)
3. **Missing environment variables** — config not injected
4. **Init container failure** — sidecar/init logic broken
5. **Image not found** — wrong registry or tag
6. **Readiness probe failing** — health check logic broken

## Diagnostics

### Check pod status and events
```bash
kubectl describe pod <pod-name> -n <namespace>
```
Look for: LastState.Reason, LastState.ExitCode, Events section

### Check container logs
```bash
kubectl logs <pod-name> -n <namespace> --previous
```
The `--previous` flag shows logs from the last crashed container.

### Check resource requests/limits
```bash
kubectl get pod <pod-name> -o yaml | grep -A5 resources
```

### Check environment variables
```bash
kubectl exec <pod-name> -n <namespace> -- env | grep CONFIG
```

## Resolution Steps

1. **If OOM (exit 137):**
   - Increase memory limit in deployment:
```yaml
   resources:
     limits:
       memory: "512Mi"  # increase this
```
   - Apply: `kubectl apply -f deployment.yaml`
   - Monitor memory usage: `kubectl top pod <pod-name>`

2. **If exit code 1 (crash):**
   - Check logs: `kubectl logs <pod-name> --previous`
   - Look for stack trace, missing dependencies, or config errors
   - Fix code/config, rebuild image, roll out new version

3. **If readiness probe failing:**
   - Test probe endpoint manually:
```bash
   kubectl port-forward <pod-name> 8080:8080
   curl localhost:8080/health
```
   - Adjust probe timeout: `initialDelaySeconds`, `timeoutSeconds`

4. **If environment variable missing:**
   - Check ConfigMap/Secret: `kubectl get configmap <name> -o yaml`
   - Verify mounted in deployment spec
   - Restart pod after fix: `kubectl rollout restart deployment <name>`

5. **If image not found:**
   - Check image pull policy: `kubectl describe pod <pod-name>` (search "ImagePullBackOff")
   - Verify image exists: `kubectl describe node` (check available images)
   - Rebuild and push with correct tag

## Recovery Verification
- Pod shows "Running" status
- Pod passes readiness probe
- No "CrashLoopBackOff" in 5 minutes of uptime
- Application endpoint responds healthily

## Prevention
- Set appropriate memory/CPU requests and limits
- Configure readiness/liveness probes with sane timeouts
- Use health checks that actually test application logic
- Store configs in ConfigMaps with validation
- Use ImagePullPolicy: "IfNotPresent" to avoid registry flakiness