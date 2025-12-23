# 📡 API Examples and Testing Guide

## Base URL
```
Development: http://localhost:8000
```

## Interactive API Documentation
Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 1. Health Check

### Request
```bash
curl -X GET http://localhost:8000/health
```

### Response
```json
{
  "status": "ok"
}
```

---

## 2. Upload PDF Document

### Request (using curl)
```bash
curl -X POST "http://localhost:8000/api/lenders/upload" \
  -F "file=@/path/to/your/document.pdf" \
  -F "lender_name=ABC Bank" \
  -F "created_by=admin@example.com"
```

### With Policy Details
```bash
curl -X POST "http://localhost:8000/api/lenders/upload" \
  -F "file=@/path/to/your/document.pdf" \
  -F "lender_name=XYZ Finance" \
  -F 'policy_details={"category": "personal_loan", "region": "north"}' \
  -F "created_by=john.doe@example.com"
```

### Response (Success - 201 Created)
```json
{
  "message": "PDF uploaded successfully. Processing started.",
  "lender_id": 1,
  "status": "uploaded",
  "task_id": "abc123-def456-ghi789"
}
```

### Response (Error - 400 Bad Request)
```json
{
  "detail": "Only PDF files are allowed"
}
```

### Response (Error - 500 Internal Server Error)
```json
{
  "detail": "OCR processing failed: Tesseract not found"
}
```

---

## 3. Get Lender by ID

### Request
```bash
curl -X GET "http://localhost:8000/api/lenders/1"
```

### Response (Status: COMPLETED)
```json
{
  "id": 1,
  "lender_name": "ABC Bank",
  "policy_details": {
    "category": "personal_loan",
    "region": "north"
  },
  "processed_data": {
    "loan_types": ["personal", "home", "auto"],
    "interest_rates": {
      "min": "10.5%",
      "max": "15.0%"
    },
    "eligibility_criteria": [
      "Age 21-65",
      "Minimum income Rs. 25,000",
      "Indian citizen"
    ],
    "loan_amount_range": {
      "min": "Rs. 50,000",
      "max": "Rs. 20,00,000"
    },
    "tenure": {
      "min": "12 months",
      "max": "60 months"
    },
    "processing_fees": "2% of loan amount",
    "documents_required": [
      "PAN Card",
      "Aadhaar Card",
      "Bank Statements (6 months)",
      "Salary Slips (3 months)"
    ],
    "key_terms": [
      "Prepayment allowed after 6 months",
      "No collateral required for loans up to Rs. 5 lakhs"
    ],
    "contact_information": {
      "phone": "+91-1800-XXX-XXXX",
      "email": "loans@abcbank.com",
      "website": "www.abcbank.com"
    },
    "special_offers": [
      "0.5% discount for salaried employees",
      "No processing fee for loans above Rs. 10 lakhs"
    ],
    "_metadata": {
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "tokens_used": 1234,
      "processing_successful": true
    },
    "_validation": {
      "field_completeness": {
        "loan_types": true,
        "interest_rates": true,
        "eligibility_criteria": true
      },
      "completeness_score": 1.0
    }
  },
  "status": "completed",
  "created_by": "admin@example.com",
  "created_at": "2025-12-23T12:00:00.000Z",
  "updated_at": "2025-12-23T12:01:30.000Z",
  "original_filename": "abc_bank_policy.pdf"
}
```

### Response (Status: PROCESSING)
```json
{
  "id": 2,
  "lender_name": "XYZ Finance",
  "policy_details": null,
  "processed_data": null,
  "status": "processing",
  "created_by": "john.doe@example.com",
  "created_at": "2025-12-23T12:05:00.000Z",
  "updated_at": "2025-12-23T12:05:15.000Z",
  "original_filename": "xyz_policy.pdf"
}
```

### Response (Not Found - 404)
```json
{
  "detail": "Lender with ID 999 not found"
}
```

---

## 4. List All Lenders

### Request (All Lenders)
```bash
curl -X GET "http://localhost:8000/api/lenders/"
```

### Request (With Pagination)
```bash
curl -X GET "http://localhost:8000/api/lenders/?limit=10&offset=0"
```

### Request (Filter by Status)
```bash
# Get only completed lenders
curl -X GET "http://localhost:8000/api/lenders/?status_filter=completed"

# Get only processing lenders
curl -X GET "http://localhost:8000/api/lenders/?status_filter=processing"

# Get only failed lenders
curl -X GET "http://localhost:8000/api/lenders/?status_filter=failed"
```

### Request (Combined Filters)
```bash
curl -X GET "http://localhost:8000/api/lenders/?status_filter=completed&limit=5&offset=0"
```

### Response
```json
{
  "total": 25,
  "lenders": [
    {
      "id": 1,
      "lender_name": "ABC Bank",
      "policy_details": {...},
      "processed_data": {...},
      "status": "completed",
      "created_by": "admin@example.com",
      "created_at": "2025-12-23T12:00:00.000Z",
      "updated_at": "2025-12-23T12:01:30.000Z",
      "original_filename": "abc_bank_policy.pdf"
    },
    {
      "id": 2,
      "lender_name": "XYZ Finance",
      "policy_details": null,
      "processed_data": {...},
      "status": "completed",
      "created_by": "john.doe@example.com",
      "created_at": "2025-12-23T12:05:00.000Z",
      "updated_at": "2025-12-23T12:06:45.000Z",
      "original_filename": "xyz_policy.pdf"
    }
  ]
}
```

---

## 5. Delete Lender

### Request
```bash
curl -X DELETE "http://localhost:8000/api/lenders/1"
```

### Response (Success - 204 No Content)
```
(Empty response with status code 204)
```

### Response (Not Found - 404)
```json
{
  "detail": "Lender with ID 999 not found"
}
```

---

## Testing Workflow

### Complete End-to-End Test

```bash
#!/bin/bash

# 1. Check API health
echo "1. Checking API health..."
curl -X GET http://localhost:8000/health
echo -e "\n"

# 2. Upload a PDF
echo "2. Uploading PDF..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/lenders/upload" \
  -F "file=@sample_policy.pdf" \
  -F "lender_name=Test Bank" \
  -F "created_by=test@example.com")

echo $UPLOAD_RESPONSE
LENDER_ID=$(echo $UPLOAD_RESPONSE | jq -r '.lender_id')
echo "Lender ID: $LENDER_ID"
echo -e "\n"

# 3. Wait for processing (give it some time)
echo "3. Waiting for processing (30 seconds)..."
sleep 30

# 4. Check status
echo "4. Checking lender status..."
curl -X GET "http://localhost:8000/api/lenders/$LENDER_ID" | jq
echo -e "\n"

# 5. List all lenders
echo "5. Listing all lenders..."
curl -X GET "http://localhost:8000/api/lenders/?limit=5" | jq
echo -e "\n"

# 6. Filter by completed status
echo "6. Filtering completed lenders..."
curl -X GET "http://localhost:8000/api/lenders/?status_filter=completed" | jq
echo -e "\n"
```

Save this as `test_api.sh` and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Using Python Requests

### Installation
```bash
pip install requests
```

### Example Script

```python
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# 1. Health check
print("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print(response.json())
print()

# 2. Upload PDF
print("2. Uploading PDF")
with open("sample_policy.pdf", "rb") as pdf_file:
    files = {"file": pdf_file}
    data = {
        "lender_name": "Python Test Bank",
        "created_by": "python_script@example.com"
    }
    response = requests.post(
        f"{BASE_URL}/api/lenders/upload",
        files=files,
        data=data
    )
    upload_result = response.json()
    print(json.dumps(upload_result, indent=2))
    lender_id = upload_result["lender_id"]
print()

# 3. Wait for processing
print("3. Waiting for processing (30 seconds)...")
time.sleep(30)

# 4. Get lender details
print(f"4. Getting lender {lender_id}")
response = requests.get(f"{BASE_URL}/api/lenders/{lender_id}")
lender = response.json()
print(f"Status: {lender['status']}")
if lender['status'] == 'completed':
    print("Processed Data:")
    print(json.dumps(lender['processed_data'], indent=2))
print()

# 5. List all lenders
print("5. Listing all lenders")
response = requests.get(f"{BASE_URL}/api/lenders/", params={"limit": 5})
lenders_list = response.json()
print(f"Total lenders: {lenders_list['total']}")
print(f"Showing: {len(lenders_list['lenders'])}")
print()

# 6. Filter by status
print("6. Filter by completed status")
response = requests.get(
    f"{BASE_URL}/api/lenders/",
    params={"status_filter": "completed", "limit": 10}
)
completed = response.json()
print(f"Completed lenders: {completed['total']}")
```

---

## Using Postman

### Import Collection

Create a Postman collection with these requests:

1. **Health Check**
   - Method: GET
   - URL: `{{base_url}}/health`

2. **Upload PDF**
   - Method: POST
   - URL: `{{base_url}}/api/lenders/upload`
   - Body: form-data
     - file: (select file)
     - lender_name: "Test Bank"
     - created_by: "postman@example.com"

3. **Get Lender**
   - Method: GET
   - URL: `{{base_url}}/api/lenders/{{lender_id}}`

4. **List Lenders**
   - Method: GET
   - URL: `{{base_url}}/api/lenders/`
   - Params:
     - status_filter: "completed"
     - limit: 10
     - offset: 0

5. **Delete Lender**
   - Method: DELETE
   - URL: `{{base_url}}/api/lenders/{{lender_id}}`

**Environment Variables:**
- `base_url`: http://localhost:8000
- `lender_id`: 1 (update as needed)

---

## Common Issues and Solutions

### Issue: "Only PDF files are allowed"
**Cause:** File is not a PDF or has wrong extension
**Solution:** Ensure file ends with `.pdf`

### Issue: "No text could be extracted"
**Cause:** PDF is scanned image without text layer, or corrupted
**Solution:** 
- Ensure PDF has text or is high-quality scanned image
- Check if Tesseract is installed properly

### Issue: "OpenAI API key not configured"
**Cause:** OPENAI_API_KEY not set in environment
**Solution:** 
```bash
export OPENAI_API_KEY="your-api-key"
# Or add to .env file
```

### Issue: Connection refused
**Cause:** API server or dependencies not running
**Solution:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Check if Redis is running
redis-cli ping

# Check if PostgreSQL is running
psql -U postgres -d kaaj -c "SELECT 1"
```

### Issue: Processing stuck in "processing" status
**Cause:** Celery worker not running or failed
**Solution:**
```bash
# Check Celery worker status
uv run celery -A app.celery_app inspect active

# Restart worker
uv run celery -A app.celery_app worker --loglevel=info
```

---

## Performance Tips

1. **Batch Operations**: Upload multiple documents in parallel
2. **Polling Interval**: Wait at least 30-60 seconds before checking status
3. **Pagination**: Use `limit` and `offset` for large result sets
4. **Status Filtering**: Use `status_filter` to get specific document states

---

For more information, see:
- **README.md**: General overview
- **SETUP.md**: Installation instructions
- **ARCHITECTURE.md**: System architecture

Happy testing! 🚀

