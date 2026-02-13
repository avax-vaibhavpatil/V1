# 🏗️ Analytics Studio - AWS Cloud Architecture

> **Production Deployment Guide** - Comprehensive AWS infrastructure planning for Analytics Studio

## 📊 Application Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + Vite + TypeScript | SPA Dashboard UI |
| **Backend** | FastAPI (Python 3.11+) | REST API + Business Logic |
| **Database** | PostgreSQL 12+ | Primary data store |
| **Cache** | Redis (optional) | Query caching |
| **LLM** | OpenAI API | AI-powered SQL generation |
| **File Storage** | Local uploads (CSV/XLSX) | Dataset uploads up to 100MB |

---

## 🌐 Architecture Diagram

```
                                    ┌─────────────────────────────────────────────────────────────────┐
                                    │                         AWS Cloud                                │
                                    │                                                                   │
    ┌──────────┐                   │  ┌─────────────┐    ┌──────────────────────────────────────┐    │
    │  Users   │◄──────────────────┼──│ CloudFront  │◄───│        S3 (Frontend Static)           │    │
    │          │     HTTPS          │  │   (CDN)     │    │   analytics-studio-frontend           │    │
    └────┬─────┘                   │  └─────────────┘    └──────────────────────────────────────┘    │
         │                         │                                                                   │
         │                         │  ┌─────────────┐    ┌──────────────────────────────────────┐    │
         │     api.yourdomain.com  │  │    ALB      │    │         ECS Fargate Cluster           │    │
         └─────────────────────────┼──│   (HTTPS)   │───▶│  ┌─────────────────────────────────┐  │    │
                                    │  │             │    │  │   FastAPI Backend Service       │  │    │
                                    │  └─────────────┘    │  │   (2-4 tasks, auto-scaling)     │  │    │
                                    │                      │  └─────────────────────────────────┘  │    │
                                    │                      └──────────────────────────────────────┘    │
                                    │                                         │                        │
                                    │                      ┌──────────────────┼──────────────────┐    │
                                    │                      │                  │                  │    │
                                    │               ┌──────▼──────┐    ┌──────▼──────┐    ┌─────▼────┐│
                                    │               │    RDS      │    │ ElastiCache │    │   S3     ││
                                    │               │ PostgreSQL  │    │   Redis     │    │ Uploads  ││
                                    │               │ (Multi-AZ)  │    │  (Cluster)  │    │          ││
                                    │               └─────────────┘    └─────────────┘    └──────────┘│
                                    │                                                                   │
                                    │  ┌─────────────────────────────────────────────────────────────┐ │
                                    │  │                      VPC (Private Subnets)                   │ │
                                    │  └─────────────────────────────────────────────────────────────┘ │
                                    └───────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                    ┌─────────────────┐
                                                    │   OpenAI API    │
                                                    │   (External)    │
                                                    └─────────────────┘
```

---

## 🔧 AWS Services Breakdown

### 1️⃣ Frontend Hosting

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **S3** | Static website hosting | ~$1-5/month |
| **CloudFront** | CDN distribution, HTTPS | ~$10-20/month |
| **Route 53** | DNS management | ~$0.50/month |

**URLs:**
- `https://analytics.yourdomain.com` → CloudFront → S3

**S3 Bucket Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::analytics-studio-frontend/*"
    }
  ]
}
```

---

### 2️⃣ Backend (API)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **ECS Fargate** | 2 tasks × 0.5 vCPU, 1GB RAM | ~$30-50/month |
| **ALB** | Application Load Balancer | ~$20/month |
| **ECR** | Docker image registry | ~$1/month |

**Alternative:** EC2 instances (t3.small/medium) if you prefer traditional VMs

**URLs:**
- `https://api.yourdomain.com` → ALB → ECS Fargate

**ECS Task Definition (example):**
```json
{
  "family": "analytics-studio-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/analytics-studio:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/analytics-studio",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

### 3️⃣ Database

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **RDS PostgreSQL** | db.t3.micro/small, Multi-AZ | ~$30-80/month |
| **Automated backups** | 7-day retention | Included |

**Connection String:**
```
postgresql+asyncpg://user:pass@rds-endpoint:5432/analytics_studio
```

**RDS Configuration:**
- **Engine:** PostgreSQL 15+
- **Instance Class:** db.t3.small (production) / db.t3.micro (dev)
- **Storage:** 20GB GP3 with auto-scaling
- **Multi-AZ:** Enabled for production
- **Encryption:** Enabled at rest
- **Backup Retention:** 7 days

---

### 4️⃣ Caching (Optional but Recommended)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **ElastiCache Redis** | cache.t3.micro | ~$15-30/month |

**Connection String:**
```
redis://analytics-redis.xxxxx.cache.amazonaws.com:6379/0
```

**Use Cases:**
- Query result caching
- Session storage
- Rate limiting

---

### 5️⃣ File Storage

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **S3** | uploads bucket with lifecycle policies | ~$5-20/month |

**Bucket:** `analytics-studio-uploads`

**Lifecycle Policy:**
```json
{
  "Rules": [
    {
      "ID": "DeleteOldUploads",
      "Status": "Enabled",
      "Filter": {"Prefix": "temp/"},
      "Expiration": {"Days": 7}
    },
    {
      "ID": "TransitionToIA",
      "Status": "Enabled",
      "Filter": {"Prefix": "datasets/"},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"}
      ]
    }
  ]
}
```

---

### 6️⃣ Security & Secrets

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **Secrets Manager** | Store API keys, DB passwords | ~$1-5/month |
| **WAF** | Web Application Firewall (optional) | ~$5-10/month |
| **ACM** | SSL/TLS certificates | Free |

**Secrets to Store:**
- `analytics-studio/database-url`
- `analytics-studio/openai-api-key`
- `analytics-studio/jwt-secret`
- `analytics-studio/redis-url`

---

## 📋 Environment Variables for AWS

```env
# Application
ENVIRONMENT=production
DEBUG=false
APP_NAME=Analytics Studio
APP_VERSION=0.1.0

# Database (RDS)
DATABASE_URL=postgresql+asyncpg://admin:${DB_PASSWORD}@analytics-rds.xxxxx.us-east-1.rds.amazonaws.com:5432/analytics_studio
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis (ElastiCache)
REDIS_URL=redis://analytics-redis.xxxxx.cache.amazonaws.com:6379/0
CACHE_TTL=3600

# OpenAI (from Secrets Manager)
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=${JWT_SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=30

# S3 Uploads
AWS_S3_BUCKET=analytics-studio-uploads
AWS_REGION=us-east-1

# Query Limits
MAX_QUERY_ROWS=100000
QUERY_TIMEOUT_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (update with your domains)
CORS_ORIGINS=["https://analytics.yourdomain.com"]
```

---

## 💰 Cost Estimation (Monthly)

| Tier | Services | Estimated Cost |
|------|----------|----------------|
| **Development** | S3 + EC2 t3.micro + RDS t3.micro | **$50-80** |
| **Production (Small)** | CloudFront + ECS (2 tasks) + RDS t3.small + ElastiCache | **$150-250** |
| **Production (Medium)** | Above + Multi-AZ + WAF + Auto-scaling | **$300-500** |

### Detailed Cost Breakdown (Production Small)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| CloudFront | 100GB transfer | $10-15 |
| S3 (Frontend) | 1GB storage | $0.50 |
| S3 (Uploads) | 50GB storage | $5-10 |
| ALB | Standard | $20 |
| ECS Fargate | 2 tasks (0.5 vCPU, 1GB) | $35-50 |
| RDS PostgreSQL | db.t3.small | $30-40 |
| ElastiCache | cache.t3.micro | $15-20 |
| Secrets Manager | 4 secrets | $2 |
| Route 53 | 1 hosted zone | $0.50 |
| CloudWatch | Logs & Metrics | $10-15 |
| **Total** | | **$128-173** |

---

## 🚀 Deployment Steps

### Phase 1: Infrastructure Setup

1. **Create VPC**
   ```bash
   # Using AWS CLI
   aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=analytics-studio-vpc}]'
   ```

2. **Create Subnets**
   - Public subnets (2): 10.0.1.0/24, 10.0.2.0/24 (for ALB)
   - Private subnets (2): 10.0.10.0/24, 10.0.11.0/24 (for ECS, RDS)

3. **Set up RDS PostgreSQL**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier analytics-studio-db \
     --db-instance-class db.t3.small \
     --engine postgres \
     --master-username admin \
     --master-user-password <password> \
     --allocated-storage 20 \
     --vpc-security-group-ids sg-xxxxx
   ```

4. **Create S3 Buckets**
   ```bash
   aws s3 mb s3://analytics-studio-frontend
   aws s3 mb s3://analytics-studio-uploads
   ```

5. **Set up ECR Repository**
   ```bash
   aws ecr create-repository --repository-name analytics-studio
   ```

### Phase 2: Backend Deployment

1. **Build Docker Image**
   ```dockerfile
   # Dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install dependencies
   COPY pyproject.toml uv.lock ./
   RUN pip install uv && uv sync --frozen

   # Copy application
   COPY . .

   # Run with uvicorn
   CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Push to ECR**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
   docker build -t analytics-studio .
   docker tag analytics-studio:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/analytics-studio:latest
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/analytics-studio:latest
   ```

3. **Create ECS Cluster and Service**
   ```bash
   aws ecs create-cluster --cluster-name analytics-studio-cluster
   aws ecs create-service \
     --cluster analytics-studio-cluster \
     --service-name analytics-studio-api \
     --task-definition analytics-studio-backend \
     --desired-count 2 \
     --launch-type FARGATE
   ```

4. **Configure ALB**
   - Create Application Load Balancer
   - Add HTTPS listener (port 443)
   - Configure target group pointing to ECS service
   - Attach ACM certificate

### Phase 3: Frontend Deployment

1. **Build React App**
   ```bash
   cd frontend
   npm run build
   ```

2. **Upload to S3**
   ```bash
   aws s3 sync dist/ s3://analytics-studio-frontend --delete
   ```

3. **Configure CloudFront**
   - Create distribution with S3 origin
   - Enable HTTPS with ACM certificate
   - Configure custom domain
   - Set up cache behaviors

4. **Set up Route 53**
   - Create hosted zone for your domain
   - Add A record (alias) pointing to CloudFront
   - Add A record for API subdomain pointing to ALB

### Phase 4: Security & Monitoring

1. **Store Secrets**
   ```bash
   aws secretsmanager create-secret \
     --name analytics-studio/database-url \
     --secret-string "postgresql+asyncpg://..."
   
   aws secretsmanager create-secret \
     --name analytics-studio/openai-api-key \
     --secret-string "sk-..."
   ```

2. **Enable CloudWatch Logging**
   ```bash
   aws logs create-log-group --log-group-name /ecs/analytics-studio
   ```

3. **Set Up Alarms**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name "HighCPUUtilization" \
     --metric-name CPUUtilization \
     --namespace AWS/ECS \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 2
   ```

4. **Configure WAF (Optional)**
   - Enable AWS Managed Rules
   - Add rate limiting rules
   - Block suspicious IP addresses

---

## 🔐 Security Best Practices

### Network Security
- ✅ Keep RDS in private subnets (no public access)
- ✅ Use Security Groups to restrict traffic
- ✅ Enable VPC Flow Logs for monitoring
- ✅ Use NAT Gateway for outbound internet access

### Authentication & Authorization
- ✅ Use IAM roles for ECS tasks (not access keys)
- ✅ Implement least privilege principle
- ✅ Enable MFA for AWS console access
- ✅ Rotate secrets regularly

### Data Protection
- ✅ Enable encryption at rest for RDS and S3
- ✅ Enable encryption in transit (HTTPS only)
- ✅ Use Secrets Manager for sensitive data
- ✅ Enable S3 versioning for uploads bucket

### Monitoring & Auditing
- ✅ Enable CloudTrail for API logging
- ✅ Set up CloudWatch alarms
- ✅ Enable RDS Performance Insights
- ✅ Regular security assessments

---

## 📊 Monitoring & Observability

### CloudWatch Dashboards

Create a dashboard with these widgets:
- ECS CPU/Memory utilization
- ALB request count and latency
- RDS connections and CPU
- S3 request metrics
- Error rates from application logs

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| ECS CPU > 80% | Warning | Scale out |
| ECS Memory > 85% | Warning | Scale out |
| ALB 5xx errors > 1% | Critical | Investigate |
| RDS connections > 80% | Warning | Review queries |
| API latency p99 > 2s | Warning | Optimize |

### Log Queries (CloudWatch Insights)

```sql
# Error rate by endpoint
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)

# Slow queries
fields @timestamp, @message
| filter @message like /query took/
| parse @message "query took * ms" as duration
| filter duration > 1000
| sort @timestamp desc
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/analytics-studio:$IMAGE_TAG .
          docker push $ECR_REGISTRY/analytics-studio:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster analytics-studio-cluster \
            --service analytics-studio-api \
            --force-new-deployment

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install and build
        run: |
          cd frontend
          npm ci
          npm run build
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist s3://analytics-studio-frontend --delete
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

---

## 📝 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 502 Bad Gateway | ECS task unhealthy | Check container logs, health check endpoint |
| Database connection timeout | Security group misconfigured | Allow traffic from ECS security group |
| CORS errors | Missing origin in allowed list | Update CORS_ORIGINS env variable |
| S3 access denied | Bucket policy incorrect | Update policy to allow CloudFront |
| Slow API responses | Database queries inefficient | Add indexes, enable query caching |

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster analytics-studio-cluster --services analytics-studio-api

# View container logs
aws logs tail /ecs/analytics-studio --follow

# Check RDS status
aws rds describe-db-instances --db-instance-identifier analytics-studio-db

# Test database connection
psql "postgresql://admin:password@rds-endpoint:5432/analytics_studio" -c "SELECT 1"
```

---

## 📚 Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Performance Optimization](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

**Last Updated:** February 2026  
**Version:** 1.0.0

