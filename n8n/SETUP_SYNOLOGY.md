# Installing n8n on Synology NAS - Production-Ready Setup

For Synology NAS, the standard `docker-compose` approach doesn't work well. Instead, use Synology's **Container Manager** GUI.

This guide shows you how to set up a **production-ready n8n installation** with PostgreSQL database.

## Why PostgreSQL?

n8n can use SQLite (file-based) or PostgreSQL (database server):
- **SQLite** (simpler): Single file, easier setup, good for small workloads
- **PostgreSQL** (recommended): Better performance, more reliable, handles concurrent workflows better

**We'll use PostgreSQL** for a production-ready setup.

## Prerequisites

- Synology NAS with DSM 7.x
- Container Manager installed
- At least 2GB RAM available
- Basic knowledge of Synology File Station

## Reference Guide

This guide is based on the excellent **[MariusHosting guide for n8n on Synology](https://mariushosting.com/how-to-install-n8n-on-your-synology-nas/)**.

---

## Step-by-Step Installation

### Step 1: Install Container Manager

1. Open **Package Center** on your Synology
2. Search for **"Container Manager"**
   - On older DSM versions, it's called "Docker"
3. Click **Install**
4. Wait for installation to complete
5. Open **Container Manager** from the main menu

### Step 2: Create Folder Structure

1. Open **File Station**
2. Navigate to `/volume1/` (or your main volume)
3. Create this folder structure:
   ```
   /volume1/docker/
   └── n8n/
       ├── data/    (for n8n workflows and settings)
       ├── db/      (for PostgreSQL database)
       └── files/   (for n8n file operations)
   ```

**How to create folders**:
- Right-click in File Station → **Create Folder**
- Name it exactly as shown above

### Step 3: Set Up PostgreSQL Database

n8n needs a database to store workflows and credentials. We'll use PostgreSQL.

#### 3.1: Download PostgreSQL Image

1. In **Container Manager**, go to **Registry**
2. Search for `postgres`
3. Select **postgres** (official image)
4. Click **Download**
5. Choose tag `17` (latest stable version)
6. Wait for download to complete

#### 3.2: Create PostgreSQL Container

1. Go to **Image** tab in Container Manager
2. Select **postgres:17**
3. Click **Launch**
4. Configure as follows:

**General Settings**:
- **Container Name**: `n8n-db`
- **Enable auto-restart**: ✅ Check this
- Click **Advanced Settings**

**Port Settings**:
- Skip this (PostgreSQL doesn't need external port access)

**Volume Settings**:
Click **Add Folder** and configure:
- **File/Folder**: `/volume1/docker/n8n/db`
- **Mount path**: `/var/lib/postgresql/data`
- **Read-only**: ❌ Unchecked

**Environment Variables**:
Click **Add** for each of these:

| Variable | Value |
|----------|-------|
| `TZ` | `America/New_York` (or your timezone) |
| `POSTGRES_DB` | `n8n` |
| `POSTGRES_USER` | `n8nuser` |
| `POSTGRES_PASSWORD` | `n8npass` (⚠️ CHANGE THIS!) |

**Important**: Use a strong password for `POSTGRES_PASSWORD`!

**Network**:
- Leave as default (bridge network)

**Links**:
- Skip this for now

Click **Next** → **Apply** → **Done**

The PostgreSQL container should start running.

### Step 4: Set Up n8n

#### 4.1: Download n8n Image

1. Go to **Registry** tab
2. Search for `n8nio/n8n`
3. Click **Download**
4. Select `latest` tag
5. Wait for download

#### 4.2: Create n8n Container

1. Go to **Image** tab
2. Select **n8nio/n8n:latest**
3. Click **Launch**

**General Settings**:
- **Container Name**: `n8n`
- **Enable auto-restart**: ✅ Check this
- Click **Advanced Settings**

**Port Settings**:
Click **Add** and configure:
- **Local Port**: `5678`
- **Container Port**: `5678`
- **Type**: TCP

**Volume Settings**:
Click **Add Folder** twice to add both mappings:

Mapping 1:
- **File/Folder**: `/volume1/docker/n8n/data`
- **Mount path**: `/root/.n8n`
- **Read-only**: ❌ Unchecked

Mapping 2:
- **File/Folder**: `/volume1/docker/n8n/files`
- **Mount path**: `/files`
- **Read-only**: ❌ Unchecked

**Environment Variables**:

⚠️ **This is important!** Add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `TZ` | `America/New_York` | Your timezone |
| `GENERIC_TIMEZONE` | `America/New_York` | Your timezone |
| `N8N_PORT` | `5678` | |
| `N8N_PROTOCOL` | `http` | Use `https` if behind reverse proxy |
| `NODE_ENV` | `production` | |
| `N8N_ENCRYPTION_KEY` | (generate random string) | See below ⬇️ |
| `DB_TYPE` | `postgresdb` | |
| `DB_POSTGRESDB_DATABASE` | `n8n` | |
| `DB_POSTGRESDB_HOST` | `n8n-db` | Container name of PostgreSQL |
| `DB_POSTGRESDB_PORT` | `5432` | |
| `DB_POSTGRESDB_USER` | `n8nuser` | |
| `DB_POSTGRESDB_PASSWORD` | `n8npass` | Same as PostgreSQL password |
| `N8N_RUNNERS_ENABLED` | `true` | Better performance |
| `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` | `true` | Security |

**Optional - Basic Authentication**:
If you want username/password login (recommended for local networks):

| Variable | Value |
|----------|-------|
| `N8N_BASIC_AUTH_ACTIVE` | `true` |
| `N8N_BASIC_AUTH_USER` | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | (your password) |

**Generating N8N_ENCRYPTION_KEY**:
This key encrypts your credentials in the database. You MUST generate a unique random string:

```bash
# On your computer or via SSH to Synology:
openssl rand -hex 32

# Copy the output and use it as N8N_ENCRYPTION_KEY
# Example output: 3f7a8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a
```

⚠️ **IMPORTANT**: Save this key somewhere safe. If you lose it, you'll lose access to all stored credentials!

**Links** (Container Dependencies):
This ensures n8n waits for PostgreSQL to be ready:

1. Click **Add** under Links section
2. Select **n8n-db** from dropdown
3. Alias: `n8n-db`

**Network**:
- Leave as default (bridge network)

**Security**:
- **Run this container using high privilege**: ❌ Leave unchecked
- **Enable privileged access**: ❌ Leave unchecked

Click **Next** → **Apply** → **Done**

### Step 5: Verify Installation

1. In Container Manager, go to **Container** tab
2. You should see two containers:
   - `n8n-db` (PostgreSQL) - Status: Running
   - `n8n` (n8n) - Status: Running

If n8n shows "Stopped":
1. Click on it → **Details** → **Log**
2. Check for errors
3. Common issues:
   - PostgreSQL not running yet (wait 30 seconds and try again)
   - Wrong database credentials
   - Missing encryption key

### Step 6: Access n8n

1. Open your web browser
2. Go to: `http://synology-ip:5678`
   - Replace `synology-ip` with your Synology's IP address
   - Example: `http://192.168.1.50:5678`
3. If you enabled Basic Auth, enter username and password
4. You should see the n8n welcome screen!

**First-time setup**:
- Create your owner account
- Set up email (optional)
- You're ready to create workflows!

### Step 7: Create Your Workflow

Now that n8n is running, **create the workflow** to connect Notion to your webhook:

📘 **See [N8N_WORKFLOW_GUIDE.md](./N8N_WORKFLOW_GUIDE.md)** for complete step-by-step workflow creation instructions.

---

## Using Synology's Reverse Proxy (Optional but Recommended)

If you want to access n8n via HTTPS and a custom domain:

### Prerequisites:
- Domain name pointing to your Synology
- SSL certificate installed on Synology
- Port 443 forwarded to Synology

### Setup:

1. **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create**
3. Configure:
   - **Source Protocol**: HTTPS
   - **Source Hostname**: `n8n.yourdomain.com`
   - **Source Port**: 443
   - **Enable HSTS**: ✅
   - **Destination Protocol**: HTTP
   - **Destination Hostname**: localhost
   - **Destination Port**: 5678
4. Click **Custom Header** → **Create** → **WebSocket**
5. Click **Save**

Now access n8n at: `https://n8n.yourdomain.com`

If using reverse proxy, update n8n environment variables:
- `N8N_PROTOCOL` = `https`
- `N8N_HOST` = `n8n.yourdomain.com`
- `WEBHOOK_URL` = `https://n8n.yourdomain.com`

Restart the n8n container after changing environment variables.

---

## Maintenance

### Updating n8n

To update to the latest n8n version:

1. **Container Manager** → **Registry**
2. Search for `n8nio/n8n`
3. Click **Download** → Select `latest`
4. Wait for download
5. Go to **Container** tab
6. Select `n8n` container
7. Click **Action** → **Stop**
8. Click **Action** → **Clear**
9. Go to **Image** tab
10. Select new `n8nio/n8n:latest`
11. Click **Launch** (use same settings as before)

### Backup

**What to back up**:
- `/volume1/docker/n8n/data/` - Your workflows and credentials
- `/volume1/docker/n8n/db/` - PostgreSQL database
- Your `N8N_ENCRYPTION_KEY` value

**How to backup**:
- Use Synology Hyper Backup
- Or manually copy folders to external drive

### Viewing Logs

1. **Container Manager** → **Container** tab
2. Select container (`n8n` or `n8n-db`)
3. Click **Details** → **Log** tab
4. View real-time logs

---

## Troubleshooting

### n8n container won't start

**Check PostgreSQL is running**:
1. Container Manager → Container tab
2. Verify `n8n-db` status is "Running"
3. If not, select it and click **Action** → **Start**

**Check logs**:
1. Select `n8n` container
2. Details → Log tab
3. Look for error messages

**Common errors**:
- "Connection to database failed": PostgreSQL not ready or wrong credentials
- "Encryption key invalid": Missing or wrong `N8N_ENCRYPTION_KEY`
- "Port already in use": Port 5678 is taken by another service

### Can't access n8n web interface

**Check container is running**:
- Container Manager → Container tab → n8n should show "Running"

**Check firewall**:
- Control Panel → Security → Firewall
- Make sure port 5678 is allowed

**Try different browser**:
- Clear browser cache
- Try incognito mode
- Try different browser

### Workflows not triggering

**Check workflow is active**:
- In n8n, workflow toggle should be green "Active"

**Check polling interval**:
- Notion Trigger node → Settings → Check polling frequency
- Wait for the interval to pass

**Check credentials**:
- Notion credentials in n8n → Test connection
- Make sure Notion integration has database access

### PostgreSQL taking too much disk space

**Vacuum the database** (reclaim space):

```bash
# SSH to Synology
ssh admin@synology-ip

# Access PostgreSQL container
docker exec -it n8n-db psql -U n8nuser -d n8n

# Run vacuum
VACUUM FULL;

# Exit
\q
```

---

## Performance Tips

1. **Allocate more RAM**: If you have RAM to spare, increase container memory limits
2. **Use SSD**: If possible, put `/volume1/docker/n8n/` on an SSD volume
3. **Enable runners**: Already enabled in our setup with `N8N_RUNNERS_ENABLED=true`
4. **Limit executions**: In n8n settings, limit execution history to 7-30 days

---

## Security Best Practices

1. ✅ Use strong passwords for database and Basic Auth
2. ✅ Keep `N8N_ENCRYPTION_KEY` secret and backed up
3. ✅ Use reverse proxy with HTTPS for external access
4. ✅ Don't expose port 5678 directly to internet
5. ✅ Regular backups of `/volume1/docker/n8n/`
6. ✅ Update n8n and PostgreSQL regularly
7. ✅ Use Synology firewall to restrict access

---

## Next Steps

Once n8n is installed and running:

1. ✅ **Create the workflow**: Follow [N8N_WORKFLOW_GUIDE.md](./N8N_WORKFLOW_GUIDE.md)
2. ✅ **Set up Notion integration**: See [SETUP_NOTION.md](./SETUP_NOTION.md)
3. ✅ **Test end-to-end**: Update a job in Notion and verify Claude responds
4. ✅ **Set up backups**: Configure Hyper Backup for your n8n folders
5. ✅ **Explore n8n**: Check out https://docs.n8n.io/ for more workflows

---

## Need Help?

- **n8n Community**: https://community.n8n.io/
- **Marius Hosting**: https://mariushosting.com/
- **Synology Forums**: https://community.synology.com/
- **This project's issues**: Check the GitHub repository

## Resources

- [MariusHosting n8n Guide](https://mariushosting.com/how-to-install-n8n-on-your-synology-nas/)
- [n8n Official Docs](https://docs.n8n.io/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [n8n Docker Image](https://hub.docker.com/r/n8nio/n8n)
