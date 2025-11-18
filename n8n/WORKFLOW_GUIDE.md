# Creating the n8n Workflow - Step-by-Step Guide

This guide provides detailed, step-by-step instructions for creating the workflow in n8n that connects your Notion job tracker to the webhook service.

## Prerequisites

Before starting, make sure you have:
- ✅ n8n installed and running (see SETUP_N8N_SYNOLOGY.md)
- ✅ Webhook service installed and running on your NAS
- ✅ Notion integration created with API key
- ✅ Notion database ID ready

## Step 1: Access n8n Web Interface

1. Open your web browser
2. Navigate to: `http://your-nas-ip:5678`
   - Replace `your-nas-ip` with your actual NAS IP address
   - Example: `http://192.168.1.100:5678`
3. You'll see the n8n login page
4. Enter your credentials (from your n8n setup)
5. Click **Login**

## Step 2: Create a New Workflow

1. Once logged in, you'll see the n8n dashboard
2. Click the **"+"** button in the top right corner, OR
3. Click **"New workflow"** button
4. You'll see a blank canvas with a single node labeled **"When clicking 'Test workflow'"**

## Step 3: Add the Notion Trigger Node

### 3.1: Add the Node

1. Click the **"+"** button on the canvas (or press `Tab` key)
2. In the search box that appears, type: `notion trigger`
3. Click on **"Notion Trigger"** from the results
4. The Notion Trigger node will appear on your canvas

### 3.2: Create Notion Credentials

1. In the Notion Trigger node settings panel (right side), you'll see **"Credential to connect with"**
2. Click the dropdown and select **"Create New Credential"**
3. A modal will appear asking for credentials
4. Enter the following:
   - **Name**: `Notion Job Tracker` (or any name you prefer)
   - **API Key**: Paste your Notion integration token
     - This is the token you got from https://www.notion.so/my-integrations
     - It starts with `secret_`
5. Click **"Save"** to save the credential

### 3.3: Configure the Trigger

Now configure what the trigger watches:

1. **Resource**: Select `Database Page` from the dropdown
2. **Database ID**:
   - Click the field
   - You'll see a dropdown with your databases (if any are found)
   - OR paste your database ID directly
   - The database ID is the 32-character string from your database URL
3. **Trigger On**: Select `Page Created` or `Page Updated`
   - Choose `Page Created` if you want to trigger when new jobs are added
   - Choose `Page Updated` if you want to trigger when existing jobs are modified
   - You can create two separate workflows if you want both
4. **Polling Interval**:
   - Leave default (checks every few minutes)
   - Or set custom interval (e.g., check every 1 minute for faster response)

### 3.4: Test the Notion Trigger

1. Click **"Execute Node"** button in the top right of the node panel
2. n8n will connect to Notion and fetch recent items
3. You should see green checkmarks if successful
4. Click **"Output"** tab to see the data fetched from Notion
5. You'll see fields like `id`, `properties`, etc.

**Important**: Make note of how the data is structured - you'll need the `id` field for the next step.

## Step 4: Add the HTTP Request Node

### 4.1: Add the Node

1. Click the **"+"** button on the right side of the Notion Trigger node
2. Search for: `http request`
3. Click **"HTTP Request"** from the results
4. The HTTP Request node will appear, connected to your Notion Trigger

### 4.2: Configure Basic Settings

1. **Method**: Select `POST` from the dropdown
2. **URL**: Enter your webhook URL
   - If both n8n and webhook are on the same NAS: `http://notion-job-tracker-webhook:8000/webhook/notion`
   - OR use your NAS IP: `http://192.168.1.100:8000/webhook/notion`
   - Replace `192.168.1.100` with your actual NAS IP
3. **Authentication**: Select `None` (we'll use headers for auth)
4. **Send Body**: Toggle this to **ON** (enabled)

### 4.3: Add Headers

Headers tell the webhook who you are and what data you're sending.

1. Scroll down to the **"Headers"** section
2. Click **"Add Header"**
3. Enter first header:
   - **Name**: `X-Webhook-Secret`
   - **Value**: Your webhook secret (from your `.env` file)
   - This is the value you set for `WEBHOOK_SECRET`
4. Click **"Add Header"** again
5. Enter second header:
   - **Name**: `Content-Type`
   - **Value**: `application/json`

### 4.4: Configure the Body

This is the data we send to the webhook.

1. **Body Content Type**: Select `JSON`
2. **Specify Body**: Select `Using JSON`
3. In the **JSON** field, enter:
   ```json
   {
     "page_id": "={{ $json.id }}",
     "action": "process"
   }
   ```

**Explanation**:
- `={{ $json.id }}` is an n8n expression that extracts the page ID from the Notion Trigger
- `$json` refers to the data from the previous node (Notion Trigger)
- `.id` gets the `id` field from that data
- The webhook service needs this to know which job to process

### 4.5: Test the HTTP Request Node

1. Click **"Execute Node"** button
2. n8n will send the request to your webhook
3. You should see a green checkmark if successful
4. Click **"Output"** tab to see the response from the webhook
5. You should see something like:
   ```json
   {
     "success": true,
     "message": "Job entry processed successfully",
     "page_id": "...",
     "claude_response": "Claude's analysis here..."
   }
   ```

**If you see errors**:
- Check that the webhook service is running: `docker ps`
- Check the webhook secret matches your `.env` file
- Check the URL is correct
- View webhook logs: `docker-compose logs -f notion-job-tracker`

## Step 5: (Optional) Add Error Handling

To handle errors gracefully:

### 5.1: Add an IF Node

1. Click **"+"** after the HTTP Request node
2. Search for `if`
3. Add the **"IF"** node

### 5.2: Configure the IF Node

1. **Condition**: `Boolean`
2. **Value 1**: `={{ $json.success }}`
3. **Operation**: `Is equal to`
4. **Value 2**: `true`

This checks if the webhook responded with success.

### 5.3: Add Success and Failure Paths

- Connect "true" output to a **"Slack"** or **"Email"** node to notify on success
- Connect "false" output to a different notification node to alert on errors

(This is optional - skip if you don't need notifications)

## Step 6: Save and Activate the Workflow

### 6.1: Save the Workflow

1. Click **"Save"** button in the top right corner
2. Give your workflow a name:
   - Example: `Notion Job Tracker → Claude Analysis`
3. Click **"Save"**

### 6.2: Activate the Workflow

**This is critical - the workflow won't run unless activated!**

1. Look for the toggle switch in the top right (next to Save button)
2. It will say **"Inactive"** in gray
3. Click the toggle to turn it **ON**
4. It should now say **"Active"** in green
5. The workflow is now running and monitoring your Notion database!

## Step 7: Test End-to-End

Now test the complete flow:

1. **Go to your Notion job tracker database**
2. **Create a new job entry** OR **update an existing one** (depending on your trigger)
   - Add a company name
   - Add a position
   - Add any other details
3. **Wait for the polling interval** (usually 1-3 minutes)
4. **Check n8n executions**:
   - In n8n, click **"Executions"** in the left sidebar
   - You should see a new execution appear
   - Click it to view details
   - Check if it succeeded (green checkmark) or failed (red X)
5. **Check webhook logs**:
   ```bash
   docker-compose logs -f notion-job-tracker
   ```
   You should see:
   ```
   INFO - Received webhook for page_id: xxxxx
   INFO - Fetched job entry: [Job Title]
   INFO - Sending job entry to Claude: xxxxx
   INFO - Claude processing completed
   ```

## Troubleshooting

### Workflow doesn't trigger

**Problem**: You updated Notion but nothing happened

**Solutions**:
1. Check workflow is **Active** (green toggle in top right)
2. Wait for polling interval to pass (default is a few minutes)
3. Check n8n executions for errors
4. Verify Notion credentials are correct
5. Make sure Notion integration has access to your database

### HTTP Request fails with "Connection refused"

**Problem**: HTTP node shows connection error

**Solutions**:
1. Check webhook service is running:
   ```bash
   docker ps | grep notion-job-tracker
   ```
2. If using Docker service name (`notion-job-tracker-webhook`):
   - Make sure both containers are on same network
   - Try using NAS IP address instead
3. Test webhook manually:
   ```bash
   curl http://localhost:8000/health
   ```

### "Invalid webhook secret" error

**Problem**: Response shows 401 Unauthorized

**Solutions**:
1. Check the `X-Webhook-Secret` header value
2. Make sure it matches `.env` file exactly (no extra spaces)
3. Restart webhook service after changing `.env`:
   ```bash
   docker-compose restart
   ```

### Notion Trigger shows "No data"

**Problem**: Execute node shows no results

**Solutions**:
1. Verify database ID is correct
2. Check Notion integration has access to database
3. Make sure there's at least one page in the database
4. Try re-authenticating Notion credentials

### Claude response is empty or error

**Problem**: Webhook returns success but no Claude response

**Solutions**:
1. Check webhook service logs for Claude API errors
2. Verify `ANTHROPIC_API_KEY` is correct in `.env`
3. Check you have API credits available
4. Review rate limits

## Workflow Configuration Summary

Here's a quick reference of what you configured:

**Notion Trigger Node:**
- Resource: Database Page
- Database ID: [Your database ID]
- Trigger On: Page Created/Updated
- Polling: Every X minutes

**HTTP Request Node:**
- Method: POST
- URL: `http://[nas-ip]:8000/webhook/notion`
- Headers:
  - `X-Webhook-Secret`: [Your secret]
  - `Content-Type`: application/json
- Body:
  ```json
  {
    "page_id": "={{ $json.id }}",
    "action": "process"
  }
  ```

## Next Steps

Once your workflow is running:

1. **Monitor executions** regularly to check for errors
2. **Customize the Claude prompt** if needed (see main README.md)
3. **Set up notifications** to alert you when jobs are processed
4. **Create additional workflows** for different triggers (created vs updated)
5. **Back up your workflow**: In n8n, go to Settings → Export workflow

## Advanced: Viewing Claude's Response in Notion

If you want to write Claude's response back to Notion:

1. Add another **HTTP Request** node after the webhook call
2. Configure it to call **Notion API's Update Page** endpoint
3. Use `={{ $json.claude_response }}` to get Claude's analysis
4. Update a "Notes" or "AI Analysis" field in your Notion page

(This is advanced - let me know if you need a separate guide for this!)

## Need Help?

If you're stuck:
1. Check n8n community forums: https://community.n8n.io/
2. Review n8n documentation: https://docs.n8n.io/
3. Check webhook service logs for errors
4. Try the workflow in "manual" mode first before activating
