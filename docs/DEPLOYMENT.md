# SAA Deployment Guide

This guide covers deploying SAA to production environments using Google Cloud Platform.

## Deployment Options

### 1. Vertex AI Agent Engine (Recommended)

**Best for**: Production AI agents with auto-scaling and managed infrastructure.

#### Prerequisites
- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- ADK CLI installed (`pip install google-adk`)

#### Setup Steps

```powershell
# 1. Set your project ID
$env:GOOGLE_CLOUD_PROJECT="your-project-id"

# 2. Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com

# 3. Authenticate
gcloud auth login
gcloud auth application-default login

# 4. Deploy SAA agent
adk deploy agent_engine . `
    --project=$env:GOOGLE_CLOUD_PROJECT `
    --region=us-central1
```

#### Configuration Files

Create `.agent_engine_config.json` in project root:

```json
{
  "min_instances": 0,
  "max_instances": 3,
  "resource_limits": {
    "cpu": "2",
    "memory": "4Gi"
  }
}
```

**Configuration Scenarios:**

| Scenario | min_instances | max_instances | CPU | Memory |
|----------|---------------|---------------|-----|--------|
| Development | 0 | 1 | 1 | 2Gi |
| Production (Small) | 1 | 3 | 2 | 4Gi |
| Production (Large) | 2 | 10 | 4 | 8Gi |

#### Environment Variables

Update `.env` for production:

```bash
# Use Vertex AI instead of AI Studio
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_LOCATION=us-central1

# API keys managed via Secret Manager (not hardcoded)
# GOOGLE_API_KEY=  # Don't include in production

# TTS Settings
TTS_PROVIDER=replicate  # Recommended for production
REPLICATE_API_TOKEN=  # Set via Secret Manager

# Audio
MAX_SEGMENT_LENGTH=250
AUDIO_FORMAT=mp3
```

---

### 2. Cloud Run (Serverless)

**Best for**: Simple deployments, demos, cost-effective small workloads.

#### Deployment Steps

```powershell
# 1. Build container
docker build -t gcr.io/$env:GOOGLE_CLOUD_PROJECT/saa:latest .

# 2. Push to Container Registry
docker push gcr.io/$env:GOOGLE_CLOUD_PROJECT/saa:latest

# 3. Deploy to Cloud Run
gcloud run deploy saa `
    --image gcr.io/$env:GOOGLE_CLOUD_PROJECT/saa:latest `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 4Gi `
    --cpu 2 `
    --timeout 3600
```

#### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install PyTorch with CPU (Cloud Run doesn't have GPU)
RUN pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Install SAA in editable mode
RUN pip install -e .

# Expose port
EXPOSE 8080

# Run FastAPI server (when implemented)
CMD ["uvicorn", "saa.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### 3. Google Kubernetes Engine (Enterprise)

**Best for**: Complex multi-service deployments, full control over infrastructure.

#### Setup Steps

```powershell
# 1. Create GKE cluster
gcloud container clusters create saa-cluster `
    --region us-central1 `
    --num-nodes 3 `
    --machine-type n1-standard-4

# 2. Get credentials
gcloud container clusters get-credentials saa-cluster --region us-central1

# 3. Deploy with kubectl
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

#### Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saa-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: saa
  template:
    metadata:
      labels:
        app: saa
    spec:
      containers:
      - name: saa
        image: gcr.io/YOUR_PROJECT/saa:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_GENAI_USE_VERTEXAI
          value: "1"
        - name: GOOGLE_CLOUD_LOCATION
          value: "us-central1"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

---

## Security Best Practices

### 1. API Key Management

**❌ NEVER do this:**
```bash
# .env (committed to git)
GOOGLE_API_KEY=AIzaSyC_REAL_KEY_HERE  # DON'T COMMIT!
```

**✅ DO this:**

```powershell
# Create secret in Secret Manager
gcloud secrets create google-api-key --data-file=-
# Paste key, then Ctrl+Z, Enter

# Grant access to service account
gcloud secrets add-iam-policy-binding google-api-key `
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

# Access in application
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/YOUR_PROJECT/secrets/google-api-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")
```

### 2. Service Accounts

Create least-privilege service account:

```powershell
# Create service account
gcloud iam service-accounts create saa-service `
    --display-name="SAA Audiobook Service"

# Grant only required permissions
gcloud projects add-iam-policy-binding $env:GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:saa-service@$env:GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" `
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $env:GOOGLE_CLOUD_PROJECT `
    --member="serviceAccount:saa-service@$env:GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"
```

### 3. Network Security

- Enable VPC for private communication
- Use Cloud Armor for DDoS protection
- Implement rate limiting
- Enable audit logging

---

## Cost Management

### Free Tier & Credits

- **Vertex AI Agent Engine**: Monthly free tier available
- **New GCP accounts**: $300 free credits (90 days)
- **Cloud Run**: 2 million requests/month free

### Cost Optimization Tips

1. **Set min_instances: 0** for development (scales to zero when idle)
2. **Use gemini-2.5-flash-lite** for simple tasks (cheaper than Pro)
3. **Enable auto-scaling** to handle traffic spikes efficiently
4. **Set budget alerts** in GCP Console
5. **Monitor usage** with Cloud Monitoring dashboards

### Budget Alerts

```powershell
# Create budget alert
gcloud billing budgets create `
    --billing-account=BILLING_ACCOUNT_ID `
    --display-name="SAA Monthly Budget" `
    --budget-amount=100USD `
    --threshold-rule=percent=50 `
    --threshold-rule=percent=90
```

---

## Monitoring & Observability

### Cloud Logging

```python
# Enable structured logging
import google.cloud.logging

client = google.cloud.logging.Client()
client.setup_logging()

logger = logging.getLogger("saa")
logger.info("Audiobook generation started", extra={
    "job_id": job_id,
    "input_file": input_file
})
```

### Cloud Monitoring

Create custom metrics:

```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{project_id}"

# Record audiobook generation time
series = monitoring_v3.TimeSeries()
series.metric.type = "custom.googleapis.com/saa/generation_time"
series.resource.type = "global"

point = series.points.add()
point.value.double_value = generation_time_seconds
point.interval.end_time.seconds = int(time.time())

client.create_time_series(name=project_name, time_series=[series])
```

### Cloud Trace

Enable tracing for performance insights:

```python
from google.cloud import trace_v1

tracer = trace_v1.TraceServiceClient()
project_id = "your-project-id"

with tracer.span(name="generate_audiobook"):
    # Your code here
    pass
```

---

## Testing Deployed Agent

### Python Client

```python
import vertexai
from vertexai import agent_engines

# Initialize
vertexai.init(project="your-project-id", location="us-central1")

# Get deployed agent
agents = list(agent_engines.list())
saa_agent = agents[0]

# Query agent
response = saa_agent.query(
    message="Generate audiobook from input/sample.txt",
    user_id="user_123"
)

print(response)
```

### REST API

```powershell
# Get agent endpoint
gcloud ai-platform agents list --region=us-central1

# Send request
curl -X POST https://AGENT_ENDPOINT/v1/tasks `
    -H "Authorization: Bearer $(gcloud auth print-access-token)" `
    -H "Content-Type: application/json" `
    -d '{
      "message": "Generate audiobook from input/sample.txt",
      "user_id": "user_123"
    }'
```

---

## Cleanup (CRITICAL to avoid costs!)

### Delete Agent Engine Deployment

```powershell
# List agents
gcloud ai-platform agents list --region=us-central1

# Delete specific agent
gcloud ai-platform agents delete AGENT_ID --region=us-central1
```

### Delete Cloud Run Service

```powershell
gcloud run services delete saa --region=us-central1
```

### Delete GKE Cluster

```powershell
gcloud container clusters delete saa-cluster --region=us-central1
```

---

## Troubleshooting

### Issue: Deployment fails with "quota exceeded"

**Solution**: Request quota increase in GCP Console
- Go to IAM & Admin → Quotas
- Filter by "Vertex AI" or "Cloud Run"
- Request increase

### Issue: Agent times out during audiobook generation

**Solution**: Increase timeout and memory
```json
{
  "resource_limits": {
    "cpu": "4",
    "memory": "8Gi"
  },
  "timeout": "3600s"
}
```

### Issue: Authentication errors in deployed agent

**Solution**: Verify service account permissions
```powershell
gcloud projects get-iam-policy $env:GOOGLE_CLOUD_PROJECT `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:saa-service@*"
```

For more details, see:
- [Vertex AI Agent Engine Docs](https://cloud.google.com/vertex-ai/docs/agent-engine)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [GKE Docs](https://cloud.google.com/kubernetes-engine/docs)
