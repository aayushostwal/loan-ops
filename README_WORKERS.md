# Multiple Hatchet Workers - Quick Reference

## 🚀 Quick Start

### Start 2 Workers (Default)
```bash
./start_workers.sh
```

### Start Custom Number of Workers
```bash
./start_workers.sh 4    # Start 4 workers
./start_workers.sh 8    # Start 8 workers
```

### Start Single Worker (Development)
```bash
./start_worker.sh
```

## 📊 What You Get

✅ **Parallel Processing**: Multiple workflows processed simultaneously  
✅ **Higher Throughput**: Handle more uploads concurrently  
✅ **Fault Tolerance**: If one worker crashes, others continue  
✅ **Easy Scaling**: Add more workers as demand grows  

## 📝 Monitor Workers

```bash
# Watch all worker logs
tail -f logs/worker_*.log

# Watch specific worker
tail -f logs/worker_1.log

# Check running workers
ps aux | grep worker.py
```

## 🛑 Stop Workers

Press `Ctrl+C` in the terminal where workers are running.

## 📖 Full Documentation

See **WORKERS_GUIDE.md** for:
- Architecture details
- Performance tuning
- Production deployment
- Troubleshooting
- Best practices

## 💡 When to Use Multiple Workers

| Scenario | Recommended Workers |
|----------|-------------------|
| Local Development | 1 |
| Testing | 1-2 |
| Production (Low Load) | 2-4 |
| Production (High Load) | 4-8 |
| Production (Very High Load) | 8-16 |

## 🔧 What Workers Do

1. **Lender Processing**: Extract and process data from uploaded lender documents
2. **Loan Matching**: Match loan applications against all lenders in parallel

## ⚙️ Configuration

Workers read from `.env`:
- `HATCHET_CLIENT_TOKEN` - Required (get from https://cloud.onhatchet.run/)
- `OPENAI_API_KEY` - Required for LLM processing
- `DATABASE_URL` - Database connection

## 🎯 Architecture

```
API Upload → Hatchet Cloud → Worker Pool → Database
                ↓
         [Worker 1, Worker 2, Worker 3, ...]
```

Each worker independently pulls and processes workflows from Hatchet.

