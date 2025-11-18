# Docker Runtime Data Organization

This project follows a clean data organization structure where all Docker runtime data is stored in the `data/` folder.

## Structure

```
NotionJobTracker2Claude/
├── src/                    # Source code
├── n8n/                    # n8n configuration files
├── docker-compose.yml      # Webhook configuration
└── data/                   # 📁 ALL runtime data here (git-ignored)
    ├── webhook/
    │   └── logs/           # Webhook service logs
    └── n8n/
        ├── data/           # n8n workflows, credentials, settings
        ├── db/             # PostgreSQL database files
        └── files/          # n8n file operations
```

## For Synology NAS Users

If you're running this on Synology, you can map it to your existing docker folder:

```
/volume1/docker/            # Your existing docker folder
├── n8n/
│   ├── data/              # → Maps to data/n8n/data
│   ├── db/                # → Maps to data/n8n/db
│   └── files/             # → Maps to data/n8n/files
└── webhook/
    └── logs/              # → Maps to data/webhook/logs
```

Just place the NotionJobTracker2Claude project in `/volume1/docker/` and the `data/` subfolder will organize everything automatically.

## What Gets Stored Where

### Webhook Data (`data/webhook/`)
- **logs/**: Application logs from the webhook service
  - Access logs
  - Error logs
  - Debug information

### n8n Data (`data/n8n/`)
- **data/**: n8n application data
  - Workflows you create
  - Stored credentials (encrypted)
  - n8n settings and configuration
  - Execution history

- **db/**: PostgreSQL database
  - Workflow definitions
  - Execution logs
  - User data

- **files/**: File storage for n8n workflows
  - Files processed by workflows
  - Temporary files
  - Attachments

## Backup Strategy

To backup everything:

```bash
# Backup all Docker data
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Or backup specific services
tar -czf webhook-backup.tar.gz data/webhook/
tar -czf n8n-backup.tar.gz data/n8n/
```

## First-Time Setup

The `data/` folder structure will be created automatically when you start the services:

```bash
# The folders will be created automatically
./start.sh

# Or manually create them if needed
mkdir -p data/webhook/logs
mkdir -p data/n8n/{data,db,files}
```

## Disk Space Monitoring

Keep an eye on disk usage:

```bash
# Check total data folder size
du -sh data/

# Check individual services
du -sh data/webhook/
du -sh data/n8n/
```

### Typical Disk Usage

- **Webhook logs**: ~10-100MB (depends on usage)
- **n8n data**: ~50-200MB (workflows and credentials)
- **PostgreSQL DB**: ~100-500MB (execution history)
- **n8n files**: Variable (depends on workflow file operations)

**Total estimate**: ~500MB - 2GB

## Cleaning Up

### Clear old logs

```bash
# Clear webhook logs older than 30 days
find data/webhook/logs/ -name "*.log" -mtime +30 -delete
```

### Clean n8n execution history

Do this from n8n web interface:
1. Settings → Execution History
2. Set retention period (e.g., 7 days)

Or manually via PostgreSQL:
```bash
docker exec -it n8n-db psql -U n8nuser -d n8n -c "DELETE FROM execution_entity WHERE finished_at < NOW() - INTERVAL '30 days';"
```

## Security Notes

⚠️ **Important**: The `data/` folder contains sensitive information:
- n8n credentials (API keys, passwords)
- Webhook logs (may contain job data)
- Database with workflow history

**Best practices**:
1. ✅ Folder is already in `.gitignore` (never committed)
2. ✅ Regular backups to secure location
3. ✅ Encrypt backups if storing off-site
4. ✅ Restrict file permissions: `chmod 700 data/`
5. ✅ Include in your NAS backup strategy

## Migration from Old Structure

If you previously used different paths:

```bash
# Old structure
./logs/              → Move to data/webhook/logs/
./n8n_data/          → Move to data/n8n/data/
./n8n_db/            → Move to data/n8n/db/
./n8n_files/         → Move to data/n8n/files/

# Migration commands
mkdir -p data/webhook data/n8n
mv logs data/webhook/ 2>/dev/null || true
mv n8n_data data/n8n/data 2>/dev/null || true
mv n8n_db data/n8n/db 2>/dev/null || true
mv n8n_files data/n8n/files 2>/dev/null || true
```

## Troubleshooting

### Permission errors

```bash
# Fix permissions
sudo chown -R $(id -u):$(id -g) data/
chmod -R 755 data/
```

### Containers can't write to folders

```bash
# For Synology, you may need to set broader permissions
chmod -R 777 data/
```

### PostgreSQL won't start

```bash
# Database folder might be corrupted
# Backup first!
mv data/n8n/db data/n8n/db.backup
mkdir -p data/n8n/db

# Restart - PostgreSQL will reinitialize
cd n8n && docker-compose restart n8n-db
```

**Note**: This creates a fresh database. You'll lose workflow history.
