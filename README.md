# NotionJobTracker2Claude

A webhook service that integrates your Notion job tracker with Claude AI for intelligent job application analysis and insights.

## Overview

This service allows you to:
- Trigger analysis of job entries from your Notion database
- Get AI-powered insights about job opportunities using Claude
- Deploy on your personal NAS using Docker
- Integrate with automation tools like Zapier, Make.com, or n8n

## Architecture

```
Notion Database → Webhook Trigger → This Service (on NAS) → Claude API
                  (Zapier/Make)           ↓
                                    Claude Analysis Response
```

## Features

- **Webhook Endpoint**: Receive triggers from Notion or automation platforms
- **Notion Integration**: Fetch job entry details from your Notion database
- **Claude AI Processing**: Get intelligent analysis and insights about job opportunities
- **Docker Deployment**: Easy deployment on your NAS with Docker Compose
- **Secure**: Webhook secret authentication
- **Health Monitoring**: Built-in health check endpoints

## Quick Start Guide

### What You'll Install

This project has TWO components:
1. **Webhook Service** (required) - Connects Notion to Claude API
2. **n8n Automation** (optional) - Triggers the webhook automatically

**Most users should start with just the webhook service + Zapier.**

### Prerequisites

Before starting, you need:
- ✅ **A NAS or server** with Docker installed (or your local computer)
- ✅ **Notion account** - Free tier works fine
- ✅ **Anthropic API key** - Get one at https://console.anthropic.com/
- ✅ **Automation tool** - Choose one:
  - Zapier (easiest, paid)
  - Make.com (powerful, paid)
  - n8n (self-hosted, free but complex)

### Step-by-Step Installation

#### Step 1: Clone the Repository

```bash
# On your NAS or local machine, download the code
git clone <repository-url>
cd NotionJobTracker2Claude
```

**What this does**: Downloads all the webhook service code to your machine.

#### Step 2: Configure Your API Keys

```bash
# Copy the example configuration file
cp .env.example .env

# Edit it with your favorite text editor
nano .env  # or use 'vi .env' or open in a text editor
```

**What this does**: Creates your configuration file. You need to fill in:

**Required settings**:
- `NOTION_API_KEY` - Get from https://www.notion.so/my-integrations (see SETUP_NOTION.md)
- `NOTION_DATABASE_ID` - Get from your job tracker database URL
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `WEBHOOK_SECRET` - Make up a random string (like a password)

**Example**:
```env
NOTION_API_KEY=secret_abc123def456...
NOTION_DATABASE_ID=f1234567890abcdef1234567890abcd
ANTHROPIC_API_KEY=sk-ant-abc123...
WEBHOOK_SECRET=my-super-secret-webhook-password-12345
```

**To generate a secure webhook secret**:
```bash
openssl rand -hex 32
```

#### Step 3: Start the Webhook Service

**What this does**: Starts a web service that listens for triggers and sends job data to Claude.

```bash
# Make the start script executable (only needed once)
chmod +x start.sh stop.sh

# Start the webhook service
./start.sh
```

**Behind the scenes**, this command:
1. Builds a Docker container with Python and all dependencies
2. Starts the webhook service on port 8000
3. Makes it available at `http://your-nas-ip:8000`

**To verify it's running**:
```bash
# Check if the container is running
docker ps

# You should see a container named "notion-job-tracker-webhook"
```

**To check the logs** (see what's happening):
```bash
docker-compose logs -f

# Press Ctrl+C to exit logs view
```

**To stop the service**:
```bash
./stop.sh
```

#### Step 4: Test the Webhook

Test if the webhook service is working:

```bash
# Check health endpoint
curl http://localhost:8000/health

# You should see:
# {"status": "healthy", "notion_client": "initialized", "claude_client": "initialized"}
```

If you see this, **the webhook service is working!** ✅

#### Step 5: Set Up Automation (Choose One)

Now you need something to trigger the webhook when you update Notion.

**Option A: Zapier** (Easiest - Recommended for beginners)
- See section "Zapier Integration" below
- Takes 5 minutes to set up
- Costs ~$20/month

**Option B: Make.com** (More features)
- Similar to Zapier, different interface
- See SETUP_NOTION.md for details

**Option C: Self-hosted n8n** (Free but complex)
- Requires installing n8n on your NAS
- See n8n/WORKFLOW_GUIDE.md for complete instructions
- For Synology: See n8n/SETUP_SYNOLOGY.md

### What Happens When Everything is Running?

1. You update a job in your Notion database
2. Zapier/Make/n8n detects the change
3. It sends the job's page ID to your webhook at `http://your-nas:8000/webhook/notion`
4. The webhook fetches the full job details from Notion
5. It sends the job info to Claude AI for analysis
6. Claude responds with insights, talking points, and recommendations
7. The response is returned (you can save it back to Notion or view it in logs)

## API Endpoints

### `GET /`
Health check endpoint

### `GET /health`
Detailed health status

### `POST /webhook/notion`
Main webhook endpoint to receive Notion triggers

**Headers:**
- `X-Webhook-Secret`: Your webhook secret

**Body:**
```json
{
  "page_id": "notion-page-id-here",
  "action": "process"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job entry processed successfully",
  "page_id": "notion-page-id-here",
  "claude_response": "Claude's analysis here..."
}
```

### `POST /process`
Direct processing endpoint (for testing)

**Body:**
```json
{
  "job_entry": {
    "page_id": "test-id",
    "title": "Software Engineer",
    "company": "Tech Corp",
    "position": "Senior Engineer",
    "status": "Applied",
    "description": "Job description...",
    "notes": "My notes..."
  }
}
```

## Deployment on NAS

See [SETUP_NAS.md](./SETUP_NAS.md) for detailed NAS deployment instructions.

**Synology NAS users**: For n8n installation, see [n8n/SETUP_SYNOLOGY.md](./n8n/SETUP_SYNOLOGY.md) for Synology-specific instructions.

## Notion Setup

See [SETUP_NOTION.md](./SETUP_NOTION.md) for detailed Notion integration and webhook setup.

## Zapier Integration (Recommended)

**Zapier is the easiest way to connect Notion to the webhook.** Here's how:

### Step 1: Create a New Zap

1. Go to [zapier.com](https://zapier.com) and log in
2. Click **"Create Zap"** button
3. You'll be taken to the Zap editor

### Step 2: Set Up the Trigger (Notion)

1. **Choose App**: Click the trigger box and search for "Notion"
2. **Choose Event**:
   - Select **"Updated Database Item"** (triggers when you edit a job)
   - OR **"New Database Item"** (triggers when you create a new job)
3. Click **Continue**
4. **Connect Notion Account**: Sign in to Notion and authorize Zapier
5. **Configure Trigger**:
   - **Database**: Select your Job Tracker database
   - Leave other settings as default
6. **Test Trigger**: Click "Test trigger" - you should see your recent jobs
7. Click **Continue**

### Step 3: Set Up the Action (Webhook)

1. **Choose App**: Click the action box and search for "Webhooks by Zapier"
2. **Choose Event**: Select **"POST"**
3. Click **Continue**
4. **Configure Webhook**:
   - **URL**: `http://your-nas-ip:8000/webhook/notion`
     - Replace `your-nas-ip` with your actual NAS IP address
     - Example: `http://192.168.1.100:8000/webhook/notion`
   - **Payload Type**: `JSON`
   - **Data**: Click "Add a field" and add:
     - Field Name: `page_id`
     - Field Value: Click the field and select "ID" from Notion data
     - Field Name: `action`
     - Field Value: Type `process` (just plain text)
   - **Headers**:
     - Click "Add header"
     - Key: `X-Webhook-Secret`
     - Value: Your webhook secret from `.env` file
     - Click "Add header" again
     - Key: `Content-Type`
     - Value: `application/json`
5. **Test Action**: Click "Test action" - you should see a successful response with Claude's analysis
6. If the test succeeds, click **Continue**

### Step 4: Activate Your Zap

1. Give your Zap a name: "Notion Job Tracker → Claude Analysis"
2. Click **"Publish"** to activate it
3. Toggle should show "On"

**That's it!** Now when you update a job in Notion, Zapier will automatically send it to Claude for analysis.

### Viewing Results

To see Claude's analysis:
- Check Zapier's task history (click on your Zap → Task History)
- Or check webhook logs: `docker-compose logs -f`
- Or optionally: Add another step to write results back to Notion

---

## Alternative: n8n Integration (Self-hosted, Free)

**Want to avoid subscription costs?** Use n8n instead of Zapier (runs on your NAS for free).

### Quick Overview:

1. **Install n8n** on your NAS
   - **Synology NAS**: See [n8n/SETUP_SYNOLOGY.md](./n8n/SETUP_SYNOLOGY.md)
   - **Other NAS**: See [DEPLOYMENT_OPTIONS.md](./DEPLOYMENT_OPTIONS.md)
2. **Create the workflow**: See [n8n/WORKFLOW_GUIDE.md](./n8n/WORKFLOW_GUIDE.md) for complete step-by-step instructions

**Pros of n8n**:
- Free and open source
- Complete privacy (no data leaves your NAS)
- More powerful than Zapier

**Cons of n8n**:
- More complex to set up
- Requires more resources on your NAS
- You manage everything yourself

## Customization

### Custom Prompt Template

You can customize the prompt sent to Claude by modifying `src/claude_client.py`:

```python
DEFAULT_PROMPT_TEMPLATE = """
Your custom prompt here...
"""
```

### Notion Field Mapping

Update field names in `src/notion_client.py` to match your Notion database schema:

```python
def _extract_title(self, properties: Dict[str, Any]) -> str:
    # Adjust field names to match your database
    for field_name in ["Name", "Title", "Job Title"]:
        ...
```

## Troubleshooting

### Service won't start
- Check if .env file exists and has all required variables
- Verify API keys are valid
- Check Docker logs: `docker-compose logs`

### Webhook receives 401 Unauthorized
- Verify `X-Webhook-Secret` header matches your .env file
- Check if WEBHOOK_SECRET is set correctly

### Notion API errors
- Verify Notion integration has access to your database
- Check if NOTION_DATABASE_ID is correct
- Ensure Notion API key has proper permissions

### Claude API errors
- Verify ANTHROPIC_API_KEY is valid
- Check if you have API credits
- Review rate limits

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Use a strong WEBHOOK_SECRET
- Consider running behind a reverse proxy (nginx) with HTTPS
- Limit network access to the webhook endpoint
- Regular update dependencies for security patches

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit pull requests or open issues.

## Support

For issues and questions:
1. Check the documentation in this README
2. Review [SETUP_NAS.md](./SETUP_NAS.md) and [SETUP_NOTION.md](./SETUP_NOTION.md)
3. Open an issue on GitHub
