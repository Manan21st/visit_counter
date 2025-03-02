# Visit Counter

This is a starter codebase for implementing a distributed visit counter service using FastAPI, Redis, and Docker.

## Architecture Overview

The system is designed with the following components:

1. **FastAPI Application**: Handles HTTP requests and provides REST API endpoints
2. **Redis Cluster**: Multiple Redis instances for distributed storage
3. **Consistent Hashing**: For distributing keys across Redis nodes
4. **Batch Processing**: For optimizing write operations

## Setup Instructions

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Run the application:
   ```bash
   docker compose up --build
   ```
4. The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /visit/{page_id}`: Record a visit
- `GET /visits/{page_id}`: Get visit count

## Testing

You can test the API using curl or any HTTP client:

```bash
# Record a visit
curl -X POST http://localhost:8000/api/v1/counter/visit/123

# Get visit count
curl http://localhost:8000/api/v1/counter/visits/123
```

## File Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── counter.py
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── consistent_hash.py
│   │   └── redis_manager.py
│   ├── services/
│   │   └── visit_counter.py
│   ├── schemas/
│   │   └── counter.py
│   └── main.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
``` 
