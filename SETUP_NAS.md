# NAS Deployment Guide

Complete guide for deploying NotionJobTracker2Claude on your personal NAS.

## Prerequisites

### NAS Requirements
- Docker support (most modern NAS systems support this)
- At least 512MB RAM available
- Network connectivity
- SSH access to your NAS

### Tested NAS Systems
- Synology DSM 7.x
- QNAP QTS 5.x
- TrueNAS Scale
- Any Linux-based system with Docker

## Step-by-Step Setup

### 1. Enable Docker on Your NAS

#### Synology
1. Open **Package Center**
2. Search for **Docker** or **Container Manager**
3. Click **Install**
4. Wait for installation to complete

#### QNAP
1. Open **App Center**
2. Search for **Container Station**
3. Click **Install**

#### TrueNAS Scale
Docker is built-in, no additional installation needed.

### 2. Access Your NAS via SSH

```bash
ssh your-username@your-nas-ip
```

For Synology: Usually `ssh admin@192.168.x.x`

### 3. Choose Installation Directory

```bash
# Create a directory for the project
# For Synology:
cd /volume1/docker/
mkdir notion-job-tracker
cd notion-job-tracker

# For QNAP:
cd /share/Container/
mkdir notion-job-tracker
cd notion-job-tracker

# For TrueNAS or generic Linux:
mkdir -p /opt/notion-job-tracker
cd /opt/notion-job-tracker
```

### 4. Upload Project Files

**Option A: Using git (recommended)**
```bash
git clone <your-repository-url> .
```

**Option B: Using SCP from your local machine**
```bash
# From your local machine
scp -r NotionJobTracker2Claude/* user@nas-ip:/volume1/docker/notion-job-tracker/
```

**Option C: Using NAS web interface**
1. Use File Station (Synology) or File Manager (QNAP)
2. Upload all files to the project directory

### 5. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file
nano .env  # or vi .env
```

Fill in your configuration:
```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929
WEBHOOK_SECRET=your-random-secret-string-here
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
```

**Generate a secure webhook secret:**
```bash
openssl rand -hex 32
```

### 6. Make Scripts Executable

```bash
chmod +x start.sh stop.sh
```

### 7. Start the Service

```bash
./start.sh
```

This will:
- Build the Docker image
- Start the container
- Set up health monitoring

### 8. Verify It's Running

```bash
# Check container status
docker-compose ps

# Should show:
# NAME                          STATUS
# notion-job-tracker-webhook    Up (healthy)

# View logs
docker-compose logs -f

# Test the health endpoint
curl http://localhost:8000/health
```

### 9. Configure Port Forwarding (for external access)

If you want to access the webhook from outside your network:

#### Synology
1. **Control Panel** → **External Access** → **Router Configuration**
2. Add rule:
   - Service: Custom
   - Port: 8000
   - Local IP: Your NAS IP
   - Local Port: 8000

#### QNAP
1. **myQNAPcloud** → **Auto Router Configuration**
2. Add port forwarding rule for port 8000

#### Router Configuration (generic)
1. Access your router admin panel
2. Find Port Forwarding section
3. Add rule:
   - External Port: 8000 (or your preferred external port)
   - Internal IP: Your NAS IP
   - Internal Port: 8000
   - Protocol: TCP

**Security Note**: If exposing to the internet, consider:
- Using a reverse proxy with HTTPS (nginx, Traefik)
- Setting up a firewall
- Using strong webhook secrets
- Implementing rate limiting

## Using Reverse Proxy (Recommended for Production)

### Option 1: Synology Built-in Reverse Proxy

1. **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Click **Create**
3. Fill in:
   - Source:
     - Protocol: HTTPS
     - Hostname: notion-webhook.your-domain.com
     - Port: 443
   - Destination:
     - Protocol: HTTP
     - Hostname: localhost
     - Port: 8000

### Option 2: nginx Reverse Proxy (Docker)

Create `nginx.conf`:
```nginx
server {
    listen 443 ssl;
    server_name notion-webhook.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://notion-job-tracker-webhook:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Add to `docker-compose.yml`:
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./certs:/etc/nginx/certs
    networks:
      - notion-tracker-network
    depends_on:
      - notion-job-tracker
```

## Auto-Start on NAS Boot

### Synology
1. **Control Panel** → **Task Scheduler**
2. Create → **Triggered Task** → **User-defined script**
3. General:
   - Task: Start NotionJobTracker
   - User: root
   - Event: Boot-up
4. Task Settings:
   - Script:
     ```bash
     cd /volume1/docker/notion-job-tracker
     docker-compose up -d
     ```

### QNAP
1. Create startup script: `/etc/config/autorun.sh`
   ```bash
   #!/bin/bash
   cd /share/Container/notion-job-tracker
   docker-compose up -d
   ```
2. Make executable: `chmod +x /etc/config/autorun.sh`

### TrueNAS Scale
Use the built-in Apps system or create a systemd service.

## Monitoring and Maintenance

### View Logs
```bash
docker-compose logs -f
```

### Restart Service
```bash
docker-compose restart
```

### Update Service
```bash
git pull  # if using git
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup Configuration
```bash
# Backup your .env file regularly
cp .env .env.backup
```

## Resource Usage

Typical resource usage:
- **CPU**: < 5% (idle), 10-20% (processing)
- **RAM**: ~200-400MB
- **Disk**: ~500MB (Docker image + logs)
- **Network**: Minimal (only during API calls)

## Troubleshooting

### Container won't start
```bash
# Check Docker status
docker ps -a

# View detailed logs
docker-compose logs

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Can't access from external network
1. Verify port forwarding is configured
2. Check firewall rules
3. Test with: `curl http://your-external-ip:8000/health`

### High memory usage
1. Adjust resource limits in docker-compose.yml
2. Check for memory leaks in logs
3. Restart container: `docker-compose restart`

## Security Hardening

1. **Use HTTPS** with reverse proxy
2. **Firewall rules**: Only allow necessary ports
3. **Regular updates**: Keep Docker and dependencies updated
4. **Network isolation**: Use Docker networks
5. **Secrets management**: Never commit .env file
6. **Monitoring**: Set up logging and alerts

## Getting Your NAS IP Address

```bash
# On the NAS via SSH
ip addr show | grep inet

# Or
hostname -I
```

For external IP (if port forwarding):
```bash
curl ifconfig.me
```

## Next Steps

After deployment:
1. Test the webhook endpoint
2. Set up Notion integration (see SETUP_NOTION.md)
3. Configure automation tool (Zapier, n8n, etc.)
4. Set up monitoring and alerts
5. Create backups of your configuration
