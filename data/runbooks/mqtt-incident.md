# MQTT Broker Connection Loss Runbook

## Symptoms
- IoT devices showing as offline in dashboard
- Message lag exceeding SLA thresholds (>5 minutes)
- Device heartbeat failures in logs
- Cloud-to-device command timeouts

## Root Causes
1. **Network partition** — connectivity between devices and broker lost
2. **TLS/mTLS certificate expiry** — authentication failure
3. **Broker overload** — max connections reached
4. **DNS resolution failure** — broker hostname unreachable
5. **Firewall rules** — MQTT port (8883) blocked

## Diagnostics

### Check broker health
```bash
curl -I https://mqtt-broker.example.com:8883
telnet mqtt-broker.example.com 8883
```

### Check device logs
- Look for "Connection refused" or "ENOTFOUND"
- Search logs for TLS handshake errors
- Check if last heartbeat timestamp is recent

### Check broker metrics
- Open CloudWatch / Prometheus dashboard
- Monitor: Active connections, message backlog, CPU/memory
- Look for sudden drops in connection count

### Verify DNS
```bash
nslookup mqtt-broker.example.com
```

## Resolution Steps

1. **If certificate expired:**
   - Renew certificate via CA
   - Deploy to broker (with zero-downtime rotation)
   - Devices auto-reconnect within 60 seconds

2. **If broker overloaded:**
   - Scale horizontal: spin up new broker instances
   - Update device connection strings to round-robin across instances
   - Monitor connection distribution

3. **If network partition:**
   - Check firewall rules: confirm port 8883 (or 1883) is open
   - Restart network interface if isolated
   - Failover to backup broker endpoint

4. **If DNS resolution broken:**
   - Update DNS records if broker IP changed
   - Flush local DNS cache: `ipconfig /flushdns` (Windows)
   - Verify devices can reach broker hostname

## Recovery Verification
- Devices reconnect and send heartbeats
- Message lag returns to <1 second
- Active connection count matches baseline
- No new errors in device logs for 5 minutes

## Prevention
- Monitor certificate expiry 30 days in advance
- Set alert if active connections drop >10% in 1 minute
- Use connection pooling to prevent max-connection exhaustion
- Deploy broker behind load balancer for high availability
- Run automated MQTT health checks every 60 seconds