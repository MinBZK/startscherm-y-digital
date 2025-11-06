# NextCloud Ingestor Helm Configuration

This Helm chart now supports multiple ways to run the NextCloud ingestor and includes a complete NextCloud deployment:

## Components

### 1. PostgreSQL Database
- **Files**: `deployment-postgresql.yaml`, `service-postgresql.yaml`, `postgresql-pvc.yaml`, `job-postgresql-init.yaml`
- **Purpose**: PostgreSQL database for NextCloud and other services
- **Configuration**: `postgresql.enabled: true`
- **Features**:
  - Persistent storage for database data
  - Health checks and proper startup sequence
  - Automatic database initialization for NextCloud
  - No external dependencies (replaces Bitnami charts)

### 2. NextCloud Instance
- **Files**: `deployment-nextcloud.yaml`, `service-nextcloud.yaml`, `nextcloud-pvc.yaml`, `configmap-nextcloud-init.yaml`
- **Purpose**: Complete NextCloud deployment with users, groups, and dossiers
- **Configuration**: `nextcloud.enabled: true`
- **Features**:
  - Uses PostgreSQL database (shared with other services)
  - Includes user initialization script with demo users and dossiers
  - Persistent storage for data and configuration
  - Health checks and proper startup sequence

## Deployment Options

### 1. API Deployment (Default)
- **File**: `deployment_nextcloud_ingestor.yaml`
- **Purpose**: Runs the FastAPI server for on-demand ingestion
- **Configuration**: `nextcloud_ingestor.runAsDeployment: true`

### 2. Initial Setup Job
- **File**: `job-nextcloud-ingestor-init.yaml`
- **Purpose**: Runs full ingestion once during installation/upgrade
- **Configuration**: `nextcloud_ingestor.initJob.enabled: true`
- **Features**:
  - Can run as Helm hook or regular job
  - Waits for Elasticsearch to be ready (with timeout)
  - Optionally waits for NextCloud to be ready
  - Performs full index recreation and ingestion
  - Configurable timeout and retry policies

#### Hook vs Regular Job Mode

- **Hook Mode** (`useHook: true`): Runs automatically during Helm install/upgrade
  - **Pros**: Automatic execution, part of release lifecycle
  - **Cons**: If it fails, entire release fails and gets cleaned up
  
- **Regular Job Mode** (`useHook: false`): Runs as standalone Kubernetes job
  - **Pros**: Doesn't block release, easier to debug, can be manually rerun
  - **Cons**: Requires manual monitoring

### 3. Scheduled Full Ingestion (CronJob)
- **File**: `cronjob-nextcloud-ingestor-full.yaml`
- **Purpose**: Periodic full reindexing (e.g., weekly)
- **Configuration**: `nextcloud_ingestor.cronjobs.full.enabled: true`
- **Default Schedule**: Every Sunday at 2 AM (`0 2 * * 0`)

### 4. Incremental Ingestion Options

#### Option A: CronJob (Every Minute)
- **File**: `cronjob-nextcloud-ingestor-incremental.yaml`
- **Purpose**: Frequent incremental updates using Kubernetes CronJob
- **Configuration**: `nextcloud_ingestor.cronjobs.incremental.enabled: true`
- **Schedule**: Every minute (`* * * * *`)
- **Limitation**: Standard cron syntax doesn't support seconds

#### Option B: Scheduler Deployment (Every 30 Seconds) - **RECOMMENDED**
- **File**: `deployment-nextcloud-ingestor-incremental-scheduler.yaml`
- **Purpose**: Precise 30-second intervals for incremental updates
- **Configuration**: `nextcloud_ingestor.incrementalScheduler.enabled: true`
- **Features**:
  - Configurable interval (default: 30 seconds)
  - Built-in health checks
  - Continuous monitoring and logging
  - Automatic restart on failure

## Configuration Examples

### Basic Setup (Recommended)
```yaml
nextcloud:
  enabled: true  # Deploy NextCloud in Kubernetes

nextcloud_ingestor:
  enabled: true
  runAsDeployment: true  # API server
  
  # Run full ingestion at installation
  initJob:
    enabled: true
    # waitForNextcloud automatically set to true when nextcloud.enabled is true
    
  # Run incremental every 30 seconds
  incrementalScheduler:
    enabled: true
    intervalSeconds: 30
```

### External NextCloud Setup (for docker-compose testing)
```yaml
nextcloud:
  enabled: false  # Don't deploy NextCloud in Kubernetes

nextcloud_ingestor:
  enabled: true
  nextcloud:
    external:
      enabled: true
      ip: "192.168.1.100"  # Your host IP
      port: 8080
  initJob:
    waitForNextcloud: true
```

### Full Automation Setup
```yaml
nextcloud_ingestor:
  enabled: true
  runAsDeployment: true  # API server
  
  # Initial setup
  initJob:
    enabled: true
    waitForNextcloud: true  # If NextCloud is in same cluster
    
  # Weekly full reindexing
  cronjobs:
    full:
      enabled: true
      schedule: "0 2 * * 0"  # Sunday 2 AM
      
  # Frequent incremental updates
  incrementalScheduler:
    enabled: true
    intervalSeconds: 30
```

### CronJob Only Setup
```yaml
nextcloud_ingestor:
  enabled: true
  runAsDeployment: false  # No API server
  
  # Initial setup
  initJob:
    enabled: true
    
  # Use CronJob for incremental (every minute)
  cronjobs:
    incremental:
      enabled: true
      schedule: "* * * * *"
```

## Resource Considerations

- **Init Job**: Higher resources for full indexing, runs once
- **Incremental Scheduler**: Lower resources, runs continuously
- **CronJobs**: Resources allocated per job execution

## Monitoring

The incremental scheduler includes health checks:
- **Liveness Probe**: Ensures the process is running
- **Readiness Probe**: Checks if the container is responsive

## Environment Variables

All templates support:
- `DRY_RUN`: Test mode without actual changes
- `LOG_LEVEL`: Logging verbosity
- NextCloud connection settings from ConfigMap
- Elasticsearch connection settings from ConfigMap

## Dependencies

The init job automatically waits for:
- Elasticsearch to be healthy
- Optionally NextCloud (if `waitForNextcloud: true`)

## Troubleshooting

### Init Job Fails with "BackoffLimitExceeded"

If you see this error:
```
Error: INSTALLATION FAILED: failed post-install: 1 error occurred:
        * job nextcloud-ingestor-init failed: BackoffLimitExceeded
```

**Solution Options:**

1. **Use Regular Job Mode** (Recommended for debugging):
   ```yaml
   nextcloud_ingestor:
     initJob:
       useHook: false  # Don't run as Helm hook
   ```

2. **Ignore Hook Failures**:
   ```yaml
   nextcloud_ingestor:
     initJob:
       useHook: true
       hookFailurePolicy: "ignore"  # Don't fail release if job fails
   ```

3. **Increase Timeout**:
   ```yaml
   nextcloud_ingestor:
     initJob:
       activeDeadlineSeconds: 7200  # 2 hours
   ```

### Debug Failed Jobs

1. Check job status: `kubectl get jobs`
2. Check job logs: `kubectl logs job/nextcloud-ingestor-init`
3. Check pod events: `kubectl describe job nextcloud-ingestor-init`

### Elasticsearch Not Starting

If Elasticsearch is not initializing properly:

1. **Check Elasticsearch pods:**
   ```bash
   kubectl get pods -l app=elasticsearch
   kubectl logs -l app=elasticsearch
   ```

2. **Check Elasticsearch service:**
   ```bash
   kubectl get svc | grep elasticsearch
   kubectl describe svc <release-name>-elasticsearch
   ```

3. **Enable troubleshooting job:**
   ```yaml
   nextcloud_ingestor:
     troubleshootJob:
       enabled: true
   ```
   Then check logs: `kubectl logs -l app.kubernetes.io/component=nextcloud-ingestor-troubleshoot`

4. **Common fixes:**
   - Increase Elasticsearch resources
   - Check persistent volume availability
   - Verify security contexts and permissions

### Init Job Times Out

If the init job times out waiting for Elasticsearch:

1. **Increase timeout:**
   ```yaml
   nextcloud_ingestor:
     initJob:
       activeDeadlineSeconds: 10800  # 3 hours
   ```

2. **Check wait logic:**
   - Current wait time: 30 minutes (180 attempts × 10 seconds)
   - Elasticsearch health check requires "yellow" status

### Manual Job Execution

If the init job fails, you can run it manually:
```bash
kubectl create job --from=job/nextcloud-ingestor-init manual-init-$(date +%s)
```