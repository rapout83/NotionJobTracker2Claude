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

## Quick Start

### Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for deployment)
- Notion account with API access
- Anthropic API key for Claude
- Personal NAS or server (optional, for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NotionJobTracker2Claude
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your API keys
   ```

3. **Required environment variables**:
   - `NOTION_API_KEY`: Your Notion integration token
   - `NOTION_DATABASE_ID`: Your Notion job tracker database ID
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `WEBHOOK_SECRET`: A secret string for webhook authentication
   - `PORT`: Port to run the service (default: 8000)

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python src/main.py
```

The service will be available at `http://localhost:8000`

### Running with Docker

```bash
# Make scripts executable
chmod +x start.sh stop.sh

# Start the service
./start.sh

# Check logs
docker-compose logs -f

# Stop the service
./stop.sh
```

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

## Notion Setup

See [SETUP_NOTION.md](./SETUP_NOTION.md) for detailed Notion integration and webhook setup.

## Zapier Integration

1. Create a new Zap in Zapier
2. **Trigger**: Notion - "Updated Database Item" or "New Database Item"
3. **Action**: Webhooks by Zapier - POST request
   - URL: `http://your-nas-ip:8000/webhook/notion`
   - Header: `X-Webhook-Secret: your-secret-here`
   - Body:
     ```json
     {
       "page_id": "{{page_id}}",
       "action": "process"
     }
     ```

## Alternative: n8n Integration (Self-hosted)

If you prefer a self-hosted automation tool:

1. Install n8n on your NAS
2. Create a workflow:
   - **Trigger**: Notion node - Watch database
   - **Action**: HTTP Request node
     - URL: `http://localhost:8000/webhook/notion`
     - Add header: `X-Webhook-Secret`
     - Body: Page ID from Notion trigger

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
