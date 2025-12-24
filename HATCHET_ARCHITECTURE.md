# Hatchet Workflow Architecture

## Overview

The Kaaj platform uses **Hatchet** for distributed workflow orchestration with a clean, centralized architecture.

## File Structure

```
app/workflows/
├── hatchet_workflows.py          # Central Hatchet client initialization
├── lender_processing_workflow.py # Lender document processing tasks
├── loan_matching_workflow.py     # Loan matching tasks
└── worker.py                      # Worker script to start processing
```

## Architecture

### 1. Central Initialization (`hatchet_workflows.py`)

This file handles:
- Reading `HATCHET_CLIENT_TOKEN` from environment
- Initializing the Hatchet client
- Creating workflow decorators for each workflow

```python
# Creates workflow decorators
lender_processing_workflow = hatchet_client.workflow(
    name="lender-processing", 
    on_events=["lender:document:uploaded"]
)

loan_matching_workflow = hatchet_client.workflow(
    name="loan-matching",
    on_events=["loan:application:uploaded"]
)
```

### 2. Workflow Task Files

Each workflow file:
- Imports its workflow decorator from `hatchet_workflows.py`
- Defines business logic functions
- Decorates functions with `@workflow.step()` to register them as workflow steps

#### Lender Processing Workflow

```python
from app.workflows.hatchet_workflows import lender_processing_workflow

# Define the processing logic
async def _process_lender_document(lender_id: int):
    # Business logic here
    pass

# Register as workflow step
if lender_processing_workflow:
    @lender_processing_workflow.step()
    async def process_lender_document(context):
        lender_id = context.workflow_input().get("lender_id")
        return await _process_lender_document(lender_id)
```

#### Loan Matching Workflow

Multi-step workflow with dependencies:

```python
from app.workflows.hatchet_workflows import loan_matching_workflow

if loan_matching_workflow:
    @loan_matching_workflow.step(timeout="60s")
    async def prepare_matching(context):
        # Step 1: Prepare data
        pass
    
    @loan_matching_workflow.step(timeout="300s", parents=["prepare_matching"])
    async def calculate_matches(context):
        # Step 2: Calculate matches (depends on prepare_matching)
        pass
    
    @loan_matching_workflow.step(timeout="30s", parents=["calculate_matches"])
    async def finalize_matching(context):
        # Step 3: Finalize (depends on calculate_matches)
        pass
```

### 3. Worker Script (`worker.py`)

The worker:
1. Imports the Hatchet client from `hatchet_workflows.py`
2. Imports workflow modules (which registers their steps)
3. Starts the worker to process workflows

```python
from app.workflows.hatchet_workflows import hatchet_client
from app.workflows import lender_processing_workflow
from app.workflows import loan_matching_workflow

worker = hatchet_client.worker("kaaj-worker")
worker.start()
```

## Workflow Execution Flow

### Lender Processing

```
1. API receives PDF upload
   ↓
2. API triggers workflow:
   hatchet_client.admin.run_workflow("lender-processing", {"lender_id": 123})
   ↓
3. Hatchet dispatches to available worker
   ↓
4. Worker executes process_lender_document step
   ↓
5. Step processes document with LLM
   ↓
6. Updates database with results
```

### Loan Matching

```
1. API receives loan application
   ↓
2. API triggers workflow:
   hatchet_client.admin.run_workflow("loan-matching", {"application_id": 456})
   ↓
3. Hatchet dispatches to available worker
   ↓
4. Worker executes Step 1: prepare_matching
   - Fetches all active lenders
   - Creates match records
   ↓
5. Worker executes Step 2: calculate_matches
   - Calculates match scores in parallel
   ↓
6. Worker executes Step 3: finalize_matching
   - Updates application status
```

## Running Workers

### Single Worker (Development)

```bash
./start_worker.sh
```

### Multiple Workers (Production)

```bash
# Start 2 workers (default)
./start_workers.sh

# Start 4 workers
./start_workers.sh 4
```

## API Integration

### Triggering Workflows from API

Both route files import the Hatchet client:

```python
from app.workflows.hatchet_workflows import get_hatchet_client

hatchet_client = get_hatchet_client()

# Trigger lender processing
workflow_run = hatchet_client.admin.run_workflow(
    "lender-processing",
    {"lender_id": lender.id}
)

# Trigger loan matching
workflow_run = hatchet_client.admin.run_workflow(
    "loan-matching",
    {"application_id": application.id}
)
```

## Benefits of This Architecture

### ✅ Centralized Configuration
- Single source of truth for Hatchet client
- Easy to modify workflow names and events
- Consistent configuration across all workflows

### ✅ Clean Separation
- Business logic separate from workflow orchestration
- Each workflow in its own file
- Easy to test business logic independently

### ✅ Type Safety
- Workflow decorators are properly typed
- Context objects provide type hints
- Better IDE support

### ✅ Scalability
- Multiple workers can process workflows in parallel
- Each worker registers all workflows automatically
- No manual registration needed

### ✅ Maintainability
- Clear file structure
- Easy to add new workflows
- Simple to understand flow

## Adding a New Workflow

1. **Add workflow decorator to `hatchet_workflows.py`:**

```python
new_workflow = hatchet_client.workflow(
    name="new-workflow",
    on_events=["new:event:triggered"]
)
```

2. **Create workflow file `new_workflow.py`:**

```python
from app.workflows.hatchet_workflows import new_workflow

if new_workflow:
    @new_workflow.step()
    async def process_task(context):
        # Your logic here
        pass
```

3. **Import in `worker.py`:**

```python
from app.workflows import new_workflow
```

4. **Trigger from API:**

```python
from app.workflows.hatchet_workflows import get_hatchet_client

hatchet_client = get_hatchet_client()
workflow_run = hatchet_client.admin.run_workflow(
    "new-workflow",
    {"param": "value"}
)
```

Done! The worker will automatically pick up and process the new workflow.

## Environment Variables

```bash
# Required
HATCHET_CLIENT_TOKEN=your-token-from-cloud.onhatchet.run

# Optional
DATABASE_URL=postgresql+asyncpg://...
OPENAI_API_KEY=your-openai-key
```

## Monitoring

- **Hatchet Dashboard**: https://cloud.onhatchet.run/
- **Worker Logs**: `logs/worker_*.log` (for multiple workers)
- **API Logs**: Check FastAPI console output

## Troubleshooting

### Workers not starting
- Check `HATCHET_CLIENT_TOKEN` is set in `.env`
- Verify token is valid at https://cloud.onhatchet.run/
- Check worker logs for errors

### Workflows not executing
- Verify workflow names match between API and workflow definitions
- Check Hatchet dashboard for workflow runs
- Ensure workers are running and connected

### Database connection errors
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Ensure database migrations are applied

## Performance Tips

1. **Worker Count**: Start with 2-4 workers, scale based on load
2. **Timeouts**: Adjust step timeouts based on actual processing time
3. **Parallel Processing**: Use `asyncio.gather()` for independent tasks
4. **Database Connections**: Each worker uses connection pooling automatically

## Security

- Store `HATCHET_CLIENT_TOKEN` securely (never commit to git)
- Use environment variables for all secrets
- Rotate tokens periodically
- Monitor workflow execution in Hatchet dashboard

