# Azure IoT Hub Failover Runbook

## Symptoms
- Region unavailable (Azure status page shows outage)
- IoT Hub returning 503 Service Unavailable
- Devices unable to connect to connection string endpoint
- Portal shows "IoT Hub is offline"

## Root Causes
1. **Regional outage** — data center failure or maintenance
2. **DNS propagation delay** — failover DNS not updated globally
3. **Connection string stale** — devices still pointing to failed region
4. **Network connectivity** — device's internet access broken (less common)

## Pre-Failover Setup (Required)

Your IoT Hub must have **geo-replication** enabled:
- Primary region: East US
- Secondary region: West US
- Failover configured in Azure Portal

Without this, manual failover is not possible.

## Diagnostics

### Check Azure status
- Go to **Azure Status Page** (status.azure.com)
- Look for outages in your region

### Verify IoT Hub is unreachable
```bash
curl -I https://my-iot-hub.azure-devices.net/
# Should get 503 if down
```

### Check current failover state
```bash
az iot hub show --resource-group <rg> --name <hub-name> | grep -i failover
```

## Failover Steps (Automated or Manual)

### Automatic Failover (Recommended)
If enabled, Azure automatically fails over to secondary region within 5-20 minutes.
- No action required
- Monitor device reconnections

### Manual Failover
If automatic failover didn't trigger:

1. **Initiate failover in Azure Portal:**
   - Go to IoT Hub > Overview
   - Click "Initiate Failover"
   - Confirm: Primary (East US) → Secondary (West US)

2. **Via Azure CLI:**
```bash
   az iot hub failover --resource-group <rg> --name <hub-name>
```

3. **Wait for DNS propagation:**
   - Failover API returns immediately, but DNS takes 5-10 minutes globally
   - Primary region endpoint (`my-iot-hub.azure-devices.net`) now resolves to secondary region

## Post-Failover Actions

### Update device connection strings (if manual failover)
Devices can auto-discover the new endpoint via:
- **IoT SDK with automatic failover:** SDK detects new endpoint automatically
- **Hard-coded connection strings:** Must update manually:

```csharp
// Old (failed)
string connectionString = "HostName=my-iot-hub.azure-devices.net;...";

// New (secondary region) — usually auto-updated, but verify
string connectionString = "HostName=my-iot-hub-secondary.azure-devices.net;...";
```

### Monitor reconnections
```bash
az iot hub monitor-events --hub-name <hub-name>
# Should start seeing device events within 2-5 minutes
```

### Verify telemetry flow
- Check Azure Stream Analytics downstream
- Monitor Application Insights for errors
- Verify devices are sending telemetry

## Failback (Return to Primary)

Once primary region is healthy again:

1. **Wait for Azure confirmation** (usually 30+ min after outage ends)

2. **Initiate failback:**
```bash
   az iot hub failover --resource-group <rg> --name <hub-name>
```

3. **Monitor for device reconnections** — devices will re-establish connections to primary

## Recovery Verification
- IoT Hub shows "Online" status
- Connection endpoint resolves correctly: `nslookup my-iot-hub.azure-devices.net`
- Devices connect and send telemetry within 5 minutes
- No data loss: Stream Analytics pipeline resumes processing
- Latency returns to baseline (~100-200ms)

## Prevention
- Enable automatic failover in production IoT Hubs
- Use geo-redundant storage for data
- Set up alerting on IoT Hub availability metrics
- Document failover procedures and test quarterly
- Use connection pooling to reduce reconnection overhead