# Docker Folder Organization on NAS

This guide explains how the webhook service integrates with your existing Docker setup on your NAS.

## Folder Structure on Your NAS

```
/volume1/docker/                 # Your NAS Docker root
├── n8n/                         # Your existing n8n (already set up)
│   ├── data/
│   ├── db/
│   └── files/
│
└── notion2claude/               # This webhook project
    ├── src/                     # Source code
    ├── docker-compose.yml       # Configuration
    ├── .env                     # Your API keys
    ├── start.sh                 # Start script
    └── webhook/                 # Runtime data (git-ignored)
        ├── cache/               # Cached job entries (for MCP)
        │   └── jobs.json        # Cache storage
        └── logs/                # Webhook logs
```

## Installation on Your NAS

### Step 1: Clone to Docker Folder

```bash
# SSH to your NAS
ssh admin@your-nas-ip

# Navigate to docker folder
cd /volume1/docker/

# Clone the project
git clone <repository-url> notion2claude
cd notion2claude
```

### Step 2: Configure

```bash
cp .env.example .env
nano .env  # Add your API keys
```

### Step 3: Start Webhook Service

```bash
chmod +x start.sh
./start.sh
```

The webhook service will create `webhook/logs/` automatically.

## Final Structure

After running, your docker folder will look like:

```
/volume1/docker/
├── n8n/                         # Your existing n8n
│   ├── data/
│   ├── db/
│   └── files/
│
└── notion2claude/               # Webhook project
    ├── src/
    ├── docker-compose.yml
    ├── .env
    └── webhook/                 # Created on first run
        ├── cache/               # Job entry cache (for MCP)
        │   └── jobs.json
        └── logs/
            ├── access.log
            └── error.log
```

## Data Locations

| Service | Data Location | What's Stored |
|---------|---------------|---------------|
| n8n | `/volume1/docker/n8n/data` | Workflows, credentials |
| n8n | `/volume1/docker/n8n/db` | PostgreSQL database |
| n8n | `/volume1/docker/n8n/files` | File operations |
| Webhook | `/volume1/docker/notion2claude/webhook/cache` | Cached job entries (for MCP) |
| Webhook | `/volume1/docker/notion2claude/webhook/logs` | Service logs |

## Backup Strategy

```bash
# Backup n8n (your existing setup)
cd /volume1/docker
tar -czf n8n-backup-$(date +%Y%m%d).tar.gz n8n/

# Backup webhook
tar -czf webhook-backup-$(date +%Y%m%d).tar.gz notion2claude/webhook/

# Or backup everything
tar -czf docker-backup-$(date +%Y%m%d).tar.gz n8n/ notion2claude/
```

## Disk Space

### Expected Usage

- **Webhook cache**: ~1-5MB (max 10 jobs, auto-cleaned)
- **Webhook logs**: ~10-100MB (depends on usage)
- **n8n data**: ~50-200MB (workflows and credentials)
- **n8n PostgreSQL**: ~100-500MB (execution history)
- **n8n files**: Variable

### Check Disk Usage

```bash
# Check webhook cache
du -sh /volume1/docker/notion2claude/webhook/cache/

# Check webhook logs
du -sh /volume1/docker/notion2claude/webhook/logs/

# Check all webhook data
du -sh /volume1/docker/notion2claude/webhook/

# Check n8n data
du -sh /volume1/docker/n8n/
```

## Log Management

### Webhook Logs

Logs are stored in `webhook/logs/`:

```bash
# View recent logs
tail -f /volume1/docker/notion2claude/webhook/logs/access.log

# Clear old logs (older than 30 days)
find /volume1/docker/notion2claude/webhook/logs/ -name "*.log" -mtime +30 -delete
```

## Network Communication

### MCP Architecture (Current)

```
Notion Button ──HTTP──> Webhook (NAS:8000) ──Notion API──> Notion
                              │
                              ├──> Cache (webhook/cache/jobs.json)
                              │
Claude Desktop ──MCP──> MCP Server ──HTTP GET──> Webhook (NAS:8000)
                                                       │
                                                       └──> Cache (read)
```

From Notion automation button:
- **URL**: `http://192.168.x.x:8000/webhook/notion`

From Claude Desktop via MCP:
- MCP server calls webhook REST API
- **List jobs**: `GET http://192.168.x.x:8000/cache/list`
- **Get job**: `GET http://192.168.x.x:8000/cache/{page_id}`

### Legacy n8n Integration (Optional)

If you want to use n8n instead of direct Notion button:

```
n8n (localhost:5678) ──HTTP──> Webhook (localhost:8000)
```

From n8n workflow, use:
- **URL**: `http://notion-job-tracker-webhook:8000/webhook/notion`

Or if using IP:
- **URL**: `http://192.168.x.x:8000/webhook/notion`

## Ports Used

| Service | Port | Access |
|---------|------|--------|
| Webhook | 8000 | Internal/LAN |
| n8n | 5678 | Web UI + Webhooks |
| PostgreSQL | 5432 | Internal only |

## Updating the Webhook Service

```bash
cd /volume1/docker/notion2claude

# Pull latest changes
git pull

# Rebuild and restart
./stop.sh
./start.sh
```

## Removing the Webhook Service

```bash
cd /volume1/docker/notion2claude

# Stop service
./stop.sh

# Remove containers
docker-compose down -v

# Remove project folder (optional)
cd ..
rm -rf notion2claude/
```

Your n8n installation remains untouched.

## Synology-Specific Notes

### File Station Access

You can access your webhook logs via File Station:
1. Open **File Station**
2. Navigate to: `docker/notion2claude/webhook/logs/`
3. Right-click logs to download or view

### Container Manager

The webhook shows up in Container Manager as:
- **Container Name**: `notion-job-tracker-webhook`
- **Image**: Local build
- **Port**: 8000

### Auto-Start on Boot

To make webhook auto-start:

1. **Control Panel** → **Task Scheduler**
2. Create → **Triggered Task** → **User-defined script**
3. **General**:
   - Task: Start Webhook
   - User: root
   - Event: Boot-up
4. **Task Settings**:
   ```bash
   cd /volume1/docker/notion2claude
   docker-compose up -d
   ```

## Integration with Existing n8n

Your n8n is already set up at `/volume1/docker/n8n/`.

To connect it to the webhook:

1. Access n8n at `http://your-nas-ip:5678`
2. Create workflow (see [n8n/WORKFLOW_GUIDE.md](../n8n/WORKFLOW_GUIDE.md))
3. Use webhook URL: `http://your-nas-ip:8000/webhook/notion`

Both services run independently but communicate via HTTP.

## Troubleshooting

### Can't start webhook - port 8000 in use

```bash
# Check what's using port 8000
sudo netstat -tulpn | grep 8000

# Change port in .env file
echo "PORT=8001" >> .env
```

### Logs not appearing

```bash
# Check if folder exists
ls -la /volume1/docker/notion2claude/webhook/

# Check permissions
chmod -R 755 /volume1/docker/notion2claude/webhook/
```

### Webhook can't reach n8n

If using service name `notion-job-tracker-webhook` in n8n but getting connection errors:
- Use NAS IP instead: `http://192.168.x.x:8000/webhook/notion`
- Or ensure both containers are on the same Docker network

## Security

1. ✅ `.env` file is git-ignored (contains API keys)
2. ✅ `webhook/` folder is git-ignored (contains logs)
3. ✅ Use strong `WEBHOOK_SECRET` in `.env`
4. ✅ Don't expose port 8000 to internet without HTTPS
5. ✅ Regular backups of both n8n and webhook folders

## Support

- **Webhook Issues**: Check logs at `webhook/logs/`
- **n8n Issues**: Check n8n logs in Container Manager
- **Network Issues**: Verify both services can reach each other
