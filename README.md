# billing-management service

This microservice provides a simple API for billing-management.

## Setup

1. Clone the repository:

   ```
   git clone https://github.com/SoloAWS/billing-management-service.git
   cd billing-management-service
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the Service

To run the service locally:

```
uvicorn app.main:app --reload --port 8007
```

The service will be available at `http://localhost:8007`.

## API Endpoints

- `GET /billing-management/health`: Health check endpoint

## Docker

To build and run the Docker container:

```
docker build -t billing-management-service .
docker run -p 8007:8007 billing-management-service
```

Make sure to expose port 8007 in your Dockerfile:

```dockerfile
EXPOSE 8007
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]