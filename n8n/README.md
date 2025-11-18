# n8n Self-Hosted Automation Setup

This folder contains everything you need to set up n8n for self-hosted automation of your Notion job tracker.

## What is n8n?

n8n is a free, open-source workflow automation tool that runs on your NAS. It replaces paid services like Zapier or Make.com.

**Pros:**
- ✅ Free and open source
- ✅ Complete privacy (all data stays on your NAS)
- ✅ More powerful than Zapier
- ✅ No subscription fees

**Cons:**
- ❌ More complex to set up
- ❌ Requires more resources on your NAS
- ❌ You manage updates and maintenance

## Files in This Folder

```
n8n/
├── README.md                # This file - overview and quick links
├── docker-compose.yml       # n8n + PostgreSQL setup (for non-Synology NAS)
├── .env.example             # n8n-specific environment variables
├── WORKFLOW_GUIDE.md        # Step-by-step workflow creation
└── SETUP_SYNOLOGY.md        # Synology-specific installation guide
```

## Quick Start

### Choose Your Installation Method

#### Option 1: Synology NAS (Recommended Path)

**If you have a Synology NAS**, use Container Manager GUI:

📘 **Follow: [SETUP_SYNOLOGY.md](./SETUP_SYNOLOGY.md)**

This guide shows you how to:
1. Install PostgreSQL container
2. Install n8n container
3. Configure both with proper settings
4. Access n8n web interface

#### Option 2: Other NAS Systems (QNAP, TrueNAS, Generic Linux)

**If you have QNAP, TrueNAS, or generic Linux**, use docker-compose:

1. **Configure environment**:
   ```bash
   # From the main project directory
   cd n8n
   cp .env.example .env
   nano .env  # Fill in your settings
   ```

2. **Start n8n + PostgreSQL**:
   ```bash
   # From the n8n folder
   docker-compose up -d
   ```

3. **Access n8n**:
   - Open browser: `http://your-nas-ip:5678`
   - Create your account
   - You're ready to create workflows!

### After Installation

Once n8n is running, create your workflow:

📘 **Follow: [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)**

This guide walks you through:
1. Connecting to Notion
2. Configuring the webhook call
3. Testing the workflow
4. Activating automatic triggers

## Architecture

When you set up n8n, here's what runs on your NAS:

```
┌─────────────────────────────────────────────┐
│  Your NAS                                   │
│                                             │
│  ┌─────────────┐      ┌──────────────────┐│
│  │ PostgreSQL  │◄─────┤ n8n              ││
│  │  Database   │      │  - Workflows     ││
│  └─────────────┘      │  - Credentials   ││
│                       │  - Automation    ││
│                       └─────────┬────────┘│
│                                 │          │
│  ┌──────────────────────────────▼───────┐ │
│  │ Webhook Service                      │ │
│  │  - Notion integration                │ │
│  │  - Claude API                        │ │
│  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
         ▲                    │
         │                    ▼
    Notion API          Claude API
```

## System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 2GB+ available (n8n + PostgreSQL)
- **Disk**: ~2GB for Docker images + database
- **Network**: Internet access for Notion and Claude APIs

## Data Persistence

When running with docker-compose, data is stored in:

```
n8n/
├── n8n_data/     # Workflows, settings, credentials
├── n8n_db/       # PostgreSQL database
└── n8n_files/    # File operations in workflows
```

**⚠️ Important**: Back up these folders regularly!

## Common Tasks

### View n8n Logs

```bash
cd n8n
docker-compose logs -f n8n
```

### Restart n8n

```bash
cd n8n
docker-compose restart n8n
```

### Stop n8n

```bash
cd n8n
docker-compose down
```

### Update n8n

```bash
cd n8n
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Can't access http://nas-ip:5678

1. Check if container is running: `docker-compose ps`
2. Check firewall settings on your NAS
3. Try accessing from the NAS itself: `curl http://localhost:5678`

### Workflows not triggering

1. Make sure workflow is **Active** (green toggle)
2. Check polling interval in Notion Trigger node
3. Verify Notion credentials are valid
4. Check n8n logs: `docker-compose logs -f n8n`

### Database errors

1. Make sure PostgreSQL is running: `docker-compose ps`
2. Check database logs: `docker-compose logs n8n-db`
3. Verify credentials in `.env` match

## Security Notes

1. **Encryption Key**: Keep `N8N_ENCRYPTION_KEY` safe and never change it
2. **Passwords**: Use strong passwords for database and n8n
3. **Access**: Don't expose port 5678 directly to internet
4. **Updates**: Keep n8n and PostgreSQL updated
5. **Backups**: Regular backups of `n8n_data/` and `n8n_db/`

## Next Steps

1. ✅ Install n8n (choose Synology or docker-compose method)
2. ✅ Create workflow (follow WORKFLOW_GUIDE.md)
3. ✅ Test with a Notion job entry
4. ✅ Set up backups
5. ✅ Explore more workflows at https://n8n.io/workflows

## Alternative: Use Zapier Instead

If n8n seems too complex, consider using Zapier instead:

- ✅ Much easier setup (5 minutes)
- ✅ User-friendly interface
- ❌ Costs ~$20/month
- ❌ Data goes through Zapier

See the main README.md for Zapier setup instructions.

## Resources

- [n8n Official Documentation](https://docs.n8n.io/)
- [n8n Community Forum](https://community.n8n.io/)
- [n8n Workflow Templates](https://n8n.io/workflows)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
