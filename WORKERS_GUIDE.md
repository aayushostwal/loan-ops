# Hatchet Workers Guide

This guide explains how to run Hatchet workers for processing lender documents and matching loan applications.

## Overview

The Kaaj platform uses **Hatchet** for distributed workflow orchestration. Workers process two types of workflows:

1. **Lender Processing Workflow**: Extracts and processes data from uploaded lender documents
2. **Loan Matching Workflow**: Matches loan applications against all active lenders in parallel

## Prerequisites

1. **Hatchet Account**: Sign up at [https://cloud.onhatchet.run/](https://cloud.onhatchet.run/)
2. **Environment Configuration**: Add your `HATCHET_CLIENT_TOKEN` to `.env`
3. **Database**: Ensure PostgreSQL is running and migrations are applied
4. **OpenAI API**: Set `OPENAI_API_KEY` for LLM processing

## Starting Workers

### Option 1: Single Worker (Development)

For local development or testing:

```bash
./start_worker.sh
```

This starts one worker process that handles both workflow types.

### Option 2: Multiple Workers (Production)

For better throughput and parallel processing:

```bash
# Start 2 workers (default)
./start_workers.sh

# Start custom number of workers
./start_workers.sh 4

# Start 8 workers for high load
./start_workers.sh 8
```

**Benefits of Multiple Workers:**
- ✅ Higher throughput - process multiple workflows simultaneously
- ✅ Better resource utilization - distribute CPU load
- ✅ Fault tolerance - if one worker crashes, others continue
- ✅ Scalability - add more workers as demand grows

## Worker Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hatchet Cloud                         │
│              (Workflow Orchestration)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌────▼────┐
   │ Worker 1│          │ Worker 2│
   │         │          │         │
   │ ┌─────┐ │          │ ┌─────┐ │
   │ │Lender│ │          │ │Loan │ │
   │ │ Flow│ │          │ │Match│ │
   │ └─────┘ │          │ └─────┘ │
   └────┬────┘          └────┬────┘
        │                    │
        └──────────┬─────────┘
                   │
        ┌──────────▼──────────┐
        │   PostgreSQL DB     │
        └─────────────────────┘
```

## Monitoring Workers

### View Worker Logs

When using multiple workers, logs are saved to individual files:

```bash
# Watch all worker logs in real-time
tail -f logs/worker_*.log

# Watch specific worker
tail -f logs/worker_1.log

# View last 50 lines from all workers
tail -n 50 logs/worker_*.log
```

### Log Format

Workers log with the following format:

```
2025-12-24 10:30:45 - [Worker PID:12345] - app.workflows - INFO - Processing lender ID: 42
```

### Check Worker Status

```bash
# List running workers
ps aux | grep worker.py

# Count active workers
ps aux | grep worker.py | grep -v grep | wc -l
```

## Worker Management

### Stop Workers

Workers are automatically stopped when you press `Ctrl+C` in the terminal where you started them.

For workers started in the background:

```bash
# Kill all worker processes
pkill -f "python.*worker.py"

# Or kill by PID file
for pid_file in .worker_pids/*.pid; do
    kill $(cat "$pid_file")
done
```

### Restart Workers

```bash
# Stop current workers (Ctrl+C)
# Then start new workers
./start_workers.sh 2
```

### Scale Workers

You can scale up or down by stopping and restarting with a different number:

```bash
# Currently running 2 workers? Stop them and start 4:
# (Press Ctrl+C to stop)
./start_workers.sh 4
```

## Workflow Details

### Lender Processing Workflow

**Trigger**: When a lender document is uploaded via API
**Event**: `lender:document:uploaded`
**Steps**:
1. Fetch lender record from database
2. Extract text from document (OCR if needed)
3. Process text with LLM to extract structured data
4. Validate and enrich data
5. Update lender record with processed data

**Typical Duration**: 30-120 seconds per document

### Loan Matching Workflow

**Trigger**: When a loan application is uploaded via API
**Event**: `loan:application:uploaded`
**Steps**:
1. **Prepare Matching**: Fetch all active lenders, create match records
2. **Calculate Matches**: Process all lender matches in parallel
3. **Finalize**: Update application status and rankings

**Typical Duration**: 60-300 seconds (depends on number of lenders)

**Parallelism**: The matching step processes all lenders simultaneously using asyncio

## Performance Tuning

### Recommended Worker Count

| Load Level | Active Lenders | Daily Uploads | Recommended Workers |
|-----------|----------------|---------------|-------------------|
| Low       | 1-10           | < 100         | 1-2               |
| Medium    | 10-50          | 100-500       | 2-4               |
| High      | 50-200         | 500-2000      | 4-8               |
| Very High | 200+           | 2000+         | 8-16              |

### Timeouts

Current timeout configuration:

- **Lender Processing**: 120 seconds per step
- **Prepare Matching**: 60 seconds
- **Calculate Matches**: 300 seconds (handles many lenders)
- **Finalize Matching**: 30 seconds

To adjust timeouts, edit the `@hatchet.step(timeout="XXs")` decorators in workflow files.

### Resource Considerations

Each worker consumes:
- **Memory**: ~200-500 MB per worker (depends on document size)
- **CPU**: 1-2 cores when processing (LLM calls, OCR)
- **Database**: 1-2 connections per worker

For a server with 8 GB RAM and 4 cores, 4-8 workers is typically optimal.

## Troubleshooting

### Workers Not Starting

**Issue**: `HATCHET_CLIENT_TOKEN not set`

```bash
# Add token to .env file
echo "HATCHET_CLIENT_TOKEN=your-token-here" >> .env
```

**Issue**: `Database connection failed`

```bash
# Verify PostgreSQL is running
pg_isready

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Workflows Not Processing

1. **Check Hatchet Dashboard**: Visit [https://cloud.onhatchet.run/](https://cloud.onhatchet.run/)
2. **Verify Worker Registration**: Look for "Lender Processing" and "Loan Matching" workflows
3. **Check Worker Logs**: `tail -f logs/worker_*.log`
4. **Verify API Triggers**: Ensure API is calling `hatchet.admin.run_workflow()`

### High Memory Usage

If workers consume too much memory:

1. **Reduce Worker Count**: Use fewer workers
2. **Increase Server Resources**: More RAM
3. **Optimize Document Processing**: Reduce image quality in OCR

### Slow Processing

If workflows take too long:

1. **Increase Worker Count**: More parallel processing
2. **Check OpenAI API**: May be rate-limited
3. **Optimize Database**: Add indexes, tune queries
4. **Review Timeouts**: May need to increase for large documents

## Best Practices

1. **Always use multiple workers in production** (minimum 2 for redundancy)
2. **Monitor logs regularly** to catch errors early
3. **Set up log rotation** to prevent disk space issues
4. **Use Hatchet dashboard** to monitor workflow execution
5. **Test with single worker first** before scaling up
6. **Keep workers updated** with latest code changes (restart after deployment)

## Development Workflow

```bash
# 1. Make code changes to workflows
vim app/workflows/lender_processing_workflow.py

# 2. Test with single worker
./start_worker.sh

# 3. Upload test document via API
curl -X POST http://localhost:8000/api/lenders/upload ...

# 4. Check logs
tail -f logs/worker_1.log

# 5. If working, scale to multiple workers
./start_workers.sh 2
```

## Production Deployment

For production, consider using a process manager:

### Option 1: systemd (Linux)

Create `/etc/systemd/system/kaaj-workers.service`:

```ini
[Unit]
Description=Kaaj Hatchet Workers
After=network.target postgresql.service

[Service]
Type=simple
User=kaaj
WorkingDirectory=/opt/kaaj
ExecStart=/opt/kaaj/start_workers.sh 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable kaaj-workers
sudo systemctl start kaaj-workers
sudo systemctl status kaaj-workers
```

### Option 2: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  worker:
    build: .
    command: python app/worker.py
    environment:
      - HATCHET_CLIENT_TOKEN=${HATCHET_CLIENT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    deploy:
      replicas: 4  # Run 4 worker containers
    restart: always
```

### Option 3: Kubernetes

Create a Deployment with multiple replicas:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kaaj-workers
spec:
  replicas: 4
  selector:
    matchLabels:
      app: kaaj-worker
  template:
    metadata:
      labels:
        app: kaaj-worker
    spec:
      containers:
      - name: worker
        image: kaaj:latest
        command: ["python", "app/worker.py"]
        envFrom:
        - secretRef:
            name: kaaj-secrets
```

## Support

For issues or questions:
- Check Hatchet documentation: [https://docs.hatchet.run/](https://docs.hatchet.run/)
- Review worker logs: `logs/worker_*.log`
- Check application logs: API will show workflow triggers


