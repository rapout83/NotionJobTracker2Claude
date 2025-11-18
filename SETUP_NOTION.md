# Notion Setup Guide

Complete guide for setting up Notion integration and configuring webhooks.

## Part 1: Create Notion Integration

### 1. Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Fill in the details:
   - **Name**: NotionJobTracker2Claude
   - **Logo**: (optional)
   - **Associated workspace**: Select your workspace
4. Click **Submit**

### 2. Configure Integration Capabilities

Under **Capabilities**, ensure these are enabled:
- ✅ Read content
- ✅ Read user information (optional)
- ✅ No user information (if you don't need user data)

### 3. Get Your Integration Token

1. After creating, you'll see **Internal Integration Token**
2. Click **Show** and **Copy**
3. Save this as `NOTION_API_KEY` in your `.env` file

```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxx
```

## Part 2: Set Up Job Tracker Database

### 1. Create or Locate Your Job Tracker Database

If you don't have one yet, create a database with these properties:

| Property Name | Property Type | Description |
|--------------|---------------|-------------|
| Name/Title | Title | Job title or company name |
| Company | Text | Company name |
| Position | Text | Job position/role |
| Status | Select | Application status (Applied, Interview, Offer, etc.) |
| Description | Text (long) | Job description |
| Notes | Text (long) | Your notes about the job |
| URL | URL | Link to job posting |

**Example Status Options:**
- To Apply
- Applied
- Phone Screen
- Interview
- Offer
- Rejected
- Accepted

### 2. Share Database with Your Integration

1. Open your Job Tracker database in Notion
2. Click the **•••** (three dots) in the top right
3. Scroll down to **Connections**
4. Click **Add connections**
5. Search for **NotionJobTracker2Claude** (your integration name)
6. Click to add it

The integration now has access to this database!

### 3. Get Your Database ID

**Method 1: From the URL**
```
https://www.notion.so/{workspace_name}/{database_id}?v={view_id}
                                       ^^^^^^^^^^^^^^^^
```

The `database_id` is the 32-character string (with hyphens).

**Method 2: Using the Share Menu**
1. Click **Share** button on the database
2. Click **Copy link**
3. Extract the ID from the URL

Example:
```
https://notion.so/myworkspace/a8f3b2c1d4e5f6a7b8c9d0e1f2a3b4c5?v=...
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                              This is your database_id
```

Add to `.env`:
```env
NOTION_DATABASE_ID=a8f3b2c1d4e5f6a7b8c9d0e1f2a3b4c5
```

### 4. Test the Integration

You can test if the integration works:

```bash
# On your NAS or local machine where the service runs
curl -X POST http://localhost:8000/webhook/notion \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{"page_id": "your-page-id-here"}'
```

To get a test page_id:
1. Open any item in your Job Tracker database
2. Click **•••** → **Copy link**
3. Extract the page ID from the URL (similar to database ID)

## Part 3: Set Up Webhook Triggers

Notion doesn't have built-in webhooks yet, so we need a middleware automation tool.

## Option 1: Using Zapier (Easiest)

### 1. Create a New Zap

1. Go to [zapier.com](https://zapier.com)
2. Click **Create Zap**

### 2. Set Up Trigger

1. **Choose App**: Search for "Notion"
2. **Choose Event**:
   - "Updated Database Item" (triggers when you update an entry)
   - OR "New Database Item" (triggers when you create new entry)
3. Click **Continue**

### 3. Configure Notion Trigger

1. **Sign in to Notion** (authorize Zapier)
2. **Select Database**: Choose your Job Tracker database
3. **Test trigger**: Click "Test trigger" to verify it works
4. Click **Continue**

### 4. Set Up Action (Webhook)

1. **Choose App**: Search for "Webhooks by Zapier"
2. **Choose Event**: "POST"
3. Click **Continue**

### 5. Configure Webhook

Fill in the webhook details:

**URL**:
```
http://your-nas-ip:8000/webhook/notion
```

or if using a domain:
```
https://notion-webhook.your-domain.com/webhook/notion
```

**Payload Type**: JSON

**Data** (click "Add a field" for each):
```
page_id: [Select "ID" from Notion data]
action: process
```

**Headers**:
```
X-Webhook-Secret: your-webhook-secret-here
Content-Type: application/json
```

### 6. Test and Enable

1. Click **Test action**
2. Verify you get a successful response
3. Click **Publish Zap**
4. Turn on the Zap

### 7. Test End-to-End

1. Go to your Notion Job Tracker
2. Update an existing entry or create a new one
3. Wait a few seconds
4. Check your service logs to see if it received the webhook
5. Check Zapier's task history

## Option 2: Using Make.com (More Features)

### 1. Create a New Scenario

1. Go to [make.com](https://make.com)
2. Click **Create a new scenario**

### 2. Add Notion Module (Trigger)

1. Click the **+** button
2. Search for **Notion**
3. Select **Watch Database Items**
4. Connect your Notion account
5. Select your Job Tracker database
6. Set polling interval (e.g., every 5 minutes)

### 3. Add HTTP Module (Action)

1. Click **+** to add another module
2. Search for **HTTP**
3. Select **Make a request**
4. Configure:
   - **URL**: `http://your-nas-ip:8000/webhook/notion`
   - **Method**: POST
   - **Headers**:
     - `X-Webhook-Secret`: your-webhook-secret
     - `Content-Type`: application/json
   - **Body**:
     ```json
     {
       "page_id": "{{1.id}}",
       "action": "process"
     }
     ```

### 4. Test and Activate

1. Click **Run once** to test
2. Update a Notion entry to trigger it
3. Verify it works
4. Click **Schedule** to activate

## Option 3: Using n8n (Self-hosted, Best for Privacy)

If you want complete control and privacy, run n8n on your NAS.

> **⚠️ Synology NAS Users**: The docker-compose method below may not work on Synology.
> See [n8n/SETUP_SYNOLOGY.md](./n8n/SETUP_SYNOLOGY.md) for Synology-specific installation using Container Manager GUI.

### 1. Install n8n on Your NAS

For non-Synology NAS systems, add to your `docker-compose.yml`:

```yaml
services:
  n8n:
    image: n8nio/n8n
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-password
    volumes:
      - ./n8n_data:/home/node/.n8n
    networks:
      - notion-tracker-network
```

Start it:
```bash
docker-compose up -d n8n
```

### 2. Create Workflow

1. Access n8n at `http://your-nas-ip:5678`
2. Login with credentials
3. Create new workflow

### 3. Add Notion Trigger

1. Add **Notion Trigger** node
2. Credential: Add your Notion integration token
3. Resource: Database
4. Database ID: Your database ID
5. Trigger On: Item Updated or Item Created

### 4. Add HTTP Request Node

1. Add **HTTP Request** node
2. Method: POST
3. URL: `http://notion-job-tracker-webhook:8000/webhook/notion`
   (using Docker network name)
4. Headers:
   ```json
   {
     "X-Webhook-Secret": "your-webhook-secret",
     "Content-Type": "application/json"
   }
   ```
5. Body:
   ```json
   {
     "page_id": "={{$json.id}}",
     "action": "process"
   }
   ```

### 5. Activate Workflow

Click **Active** toggle to enable the workflow.

## Part 4: Field Mapping Customization

If your Notion database uses different field names, update `src/notion_client.py`:

```python
def _extract_title(self, properties: Dict[str, Any]) -> str:
    # Update these to match YOUR database field names
    for field_name in ["Name", "Title", "Job Title", "Company + Position"]:
        if field_name in properties:
            # ... rest of the code
```

Common customizations:

```python
# In parse_job_entry method:
company = self._extract_text(properties.get("Company Name"))  # Your field name
position = self._extract_text(properties.get("Role"))         # Your field name
status = self._extract_select(properties.get("App Status"))   # Your field name
```

## Testing Your Setup

### 1. Test Notion API Access

```python
# Quick test script
from notion_client import Client

notion = Client(auth="your-notion-api-key")
database_id = "your-database-id"

# Try to query the database
results = notion.databases.query(database_id=database_id)
print(f"Found {len(results['results'])} items")
```

### 2. Test Webhook Endpoint

```bash
# Get a page ID from your database
PAGE_ID="your-page-id"
SECRET="your-webhook-secret"

curl -X POST http://localhost:8000/webhook/notion \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $SECRET" \
  -d "{\"page_id\": \"$PAGE_ID\"}"
```

### 3. Monitor Logs

```bash
docker-compose logs -f
```

You should see:
```
INFO - Received webhook for page_id: xxx
INFO - Fetched job entry: Software Engineer at Tech Corp
INFO - Sending job entry to Claude: xxx
INFO - Claude processing completed
```

## Troubleshooting

### "Notion API error: object not found"
- Verify the integration is connected to your database
- Check if the database ID is correct
- Ensure the page ID exists

### "Notion API error: unauthorized"
- Verify your NOTION_API_KEY is correct
- Check if the integration token is still valid
- Reconnect the integration to your database

### Webhook not triggering
- Check Zapier/Make/n8n task history
- Verify the webhook URL is accessible
- Check if the service is running: `docker-compose ps`
- Test webhook manually with curl

### Wrong data being sent to Claude
- Check field names in `src/notion_client.py`
- View raw properties: Add logging to see what Notion sends
- Update field mapping to match your database schema

## Next Steps

After setup:
1. Test with a real job entry
2. Review Claude's response
3. Customize the prompt template if needed
4. Set up monitoring for failed webhooks
5. Create a workflow for handling Claude's responses
