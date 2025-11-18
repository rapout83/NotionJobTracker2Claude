# Deployment Options

This guide explains the different ways to deploy and use the NotionJobTracker2Claude webhook service.

## Overview

The webhook service can work with different automation tools to trigger Claude analysis of your Notion job entries:

```
Notion → Automation Tool → Webhook Service → Claude API
```

## Option 1: Webhook Service Only + Cloud Automation (Simplest)

**What you deploy**: Just the webhook service on your NAS
**What triggers it**: Zapier, Make.com, or similar cloud service

### Pros
✅ Simplest setup
✅ Minimal resource usage on NAS
✅ User-friendly interfaces (Zapier/Make)
✅ No need to manage automation software

### Cons
❌ Requires cloud service subscription (Zapier/Make)
❌ Data passes through third-party service

### Deployment

```bash
# Just use the main docker-compose.yml
cp .env.example .env
nano .env  # Configure your API keys
./start.sh
```

**Then set up trigger**:
- Use Zapier (see SETUP_NOTION.md)
- Use Make.com (see SETUP_NOTION.md)

**Best for**: Users who want simplicity and don't mind cloud services

---

## Option 2: Webhook Service + Self-hosted n8n (Best Privacy)

**What you deploy**: Both webhook service AND n8n automation on your NAS
**What triggers it**: n8n (running on your NAS)

### Pros
✅ Complete privacy - everything runs on your NAS
✅ No subscription fees
✅ Full control over automation
✅ n8n is powerful and flexible
✅ Uses official Docker Hub image - no compilation needed

### Cons
❌ More resource usage on NAS
❌ Need to manage one more service
❌ Slightly more complex setup

### Deployment

**Step 1**: Start both services together

```bash
# Configure environment
cp .env.example .env
nano .env  # Add your API keys AND n8n credentials

# Start both webhook service + n8n
docker-compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
```

**Step 2**: Access n8n
- Open browser: `http://your-nas-ip:5678`
- Login with credentials from .env (N8N_USER, N8N_PASSWORD)

**Step 3**: Create n8n workflow (see below)

**Best for**: Users who want full privacy and control, self-hosting enthusiasts

---

## n8n Workflow Setup

If using Option 2, here's how to set up the workflow in n8n:

### 1. Access n8n Web Interface

```
http://your-nas-ip:5678
```

Login with credentials from your `.env` file.

### 2. Create New Workflow

Click **"New workflow"** button

### 3. Add Notion Trigger

1. Click **"+"** to add node
2. Search for **"Notion"**
3. Select **"Notion Trigger"**
4. Click **"Create New Credential"**
5. Add your `NOTION_API_KEY`
6. Configure:
   - **Resource**: Database
   - **Database ID**: Your Notion database ID
   - **Trigger On**: `Database Item Updated` or `Database Item Created`
   - **Poll Times**: Configure how often to check (e.g., every 1 minute)

### 4. Add HTTP Request Node

1. Click **"+"** after Notion Trigger
2. Search for **"HTTP Request"**
3. Configure:
   - **Method**: POST
   - **URL**: `http://notion-job-tracker-webhook:8000/webhook/notion`
     (Note: Use Docker service name, not localhost)
   - **Authentication**: None (we use header instead)

4. Add **Headers**:
   - Click **"Add Header"**
   - Name: `X-Webhook-Secret`
   - Value: Your webhook secret from .env
   - Click **"Add Header"** again
   - Name: `Content-Type`
   - Value: `application/json`

5. Set **Body**:
   - **Body Content Type**: JSON
   - **Specify Body**: Using JSON
   - JSON content:
     ```json
     {
       "page_id": "={{ $json.id }}",
       "action": "process"
     }
     ```

### 5. Activate Workflow

1. Click **"Save"** (top right)
2. Toggle **"Active"** switch to ON
3. Workflow will now monitor your Notion database!

### 6. Test It

1. Go to your Notion job tracker
2. Update or create a job entry
3. Wait for n8n to poll (check interval you set)
4. View execution in n8n interface
5. Check webhook service logs:
   ```bash
   docker-compose logs -f notion-job-tracker
   ```

---

## Resource Usage Comparison

### Option 1 (Webhook Only)
- **RAM**: ~256-400MB
- **CPU**: ~5% idle, ~20% active
- **Disk**: ~500MB

### Option 2 (Webhook + n8n)
- **RAM**: ~512-900MB combined
- **CPU**: ~10% idle, ~30% active
- **Disk**: ~1GB

---

## Which Option Should You Choose?

### Choose Option 1 if:
- You want the simplest setup
- You already use Zapier/Make for other automations
- You don't mind cloud services
- Your NAS has limited resources

### Choose Option 2 if:
- Privacy is important to you
- You want full control over your data
- You want to avoid subscription fees
- Your NAS has decent resources (2GB+ RAM recommended)
- You enjoy self-hosting

---

## Upgrading from Option 1 to Option 2

If you start with Option 1 and later want to add n8n:

```bash
# Stop current service
docker-compose down

# Add your n8n credentials to .env
nano .env

# Start both services
docker-compose -f docker-compose.yml -f docker-compose.n8n.yml up -d

# Access n8n and create workflow
open http://your-nas-ip:5678
```

Then disable your Zapier/Make zap when n8n is working.

---

## Important Notes

### About Docker Images

**All images are from Docker Hub** - no GitHub cloning needed!

- `n8nio/n8n` - Official n8n image from Docker Hub
- `python:3.11-slim` - Official Python image (used in our Dockerfile)

Docker automatically downloads these when you run `docker-compose up`.

### Network Communication

When both services run via Docker Compose, they're on the same network:

- **n8n → webhook**: Use `http://notion-job-tracker-webhook:8000`
- **External → webhook**: Use `http://your-nas-ip:8000`
- **Browser → n8n**: Use `http://your-nas-ip:5678`

### Data Persistence

Both deployments persist data:

```
./logs/        - Webhook service logs
./n8n_data/    - n8n workflows and credentials (Option 2 only)
```

Make sure to back up these directories!

---

## Quick Command Reference

### Start webhook only
```bash
docker-compose up -d
```

### Start webhook + n8n
```bash
docker-compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
```

### View logs
```bash
# Webhook only
docker-compose logs -f notion-job-tracker

# n8n only
docker-compose logs -f n8n

# Both
docker-compose logs -f
```

### Stop services
```bash
docker-compose down
```

### Restart services
```bash
docker-compose restart
```

### Check status
```bash
docker-compose ps
```
