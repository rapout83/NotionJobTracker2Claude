# Installing n8n on Synology NAS

If you're using a Synology NAS, the standard `docker-compose` approach may not work properly. Instead, use Synology's Container Manager interface.

## Recommended Approach for Synology

Follow this comprehensive guide for Synology NAS:
**[How to Install n8n on Your Synology NAS - Marius Hosting](https://mariushosting.com/how-to-install-n8n-on-your-synology-nas/)**

## Quick Overview for Synology

### Method 1: Using Container Manager GUI (Recommended for Synology)

1. **Install Container Manager**
   - Open **Package Center**
   - Search for **Container Manager** (or **Docker** on older DSM versions)
   - Click **Install**

2. **Create Folder Structure**
   - Open **File Station**
   - Navigate to your main volume (e.g., `/volume1/`)
   - Create folder structure:
     ```
     /volume1/docker/
     └── n8n/
         ├── data/
         ├── db/
         └── files/
     ```

3. **Create n8n Container in Container Manager**
   - Open **Container Manager**
   - Go to **Registry** → Search for `n8nio/n8n` → Download
   - Go to **Image** → Select `n8nio/n8n` → Launch

4. **Configure Container Settings**
   - **Container Name**: `n8n`
   - **Enable auto-restart**
   - Click **Advanced Settings**

5. **Port Settings**
   - Add port mapping:
     - Local Port: `5678`
     - Container Port: `5678`
     - Type: TCP

6. **Volume Settings**
   - Add folder mapping:
     - Local Folder: `/volume1/docker/n8n/data`
     - Mount Path: `/home/node/.n8n`

7. **Environment Variables**
   Add these variables:
   ```
   N8N_BASIC_AUTH_ACTIVE=true
   N8N_BASIC_AUTH_USER=admin
   N8N_BASIC_AUTH_PASSWORD=your-password-here
   GENERIC_TIMEZONE=America/New_York
   TZ=America/New_York
   ```

8. **Apply and Start**
   - Click **Apply** → **Next** → **Done**
   - Container should start automatically

9. **Access n8n**
   - Open browser: `http://synology-ip:5678`
   - Login with credentials from environment variables

### Method 2: Using Synology Task Scheduler with Docker Commands

If you prefer command-line but Container Manager GUI doesn't work:

1. Enable SSH on your Synology
2. SSH into your Synology: `ssh admin@synology-ip`
3. Create folders:
   ```bash
   mkdir -p /volume1/docker/n8n/data
   ```

4. Run n8n container:
   ```bash
   docker run -d \
     --name n8n \
     --restart unless-stopped \
     -p 5678:5678 \
     -e N8N_BASIC_AUTH_ACTIVE=true \
     -e N8N_BASIC_AUTH_USER=admin \
     -e N8N_BASIC_AUTH_PASSWORD=changeme \
     -e GENERIC_TIMEZONE=America/New_York \
     -e TZ=America/New_York \
     -v /volume1/docker/n8n/data:/home/node/.n8n \
     n8nio/n8n:latest
   ```

## Connecting n8n to Your Webhook Service

Once n8n is running on your Synology:

1. **Access n8n**: `http://synology-ip:5678`

2. **Create Workflow** (see main SETUP_NOTION.md for detailed steps):
   - Add **Notion Trigger** node
   - Add **HTTP Request** node with:
     - URL: `http://synology-ip:8000/webhook/notion`
     - Headers: Add `X-Webhook-Secret`
     - Body: `{"page_id": "={{ $json.id }}", "action": "process"}`

3. **Activate Workflow**

## Why docker-compose Doesn't Work Well on Synology

Synology's Docker implementation has some limitations:
- May not support standard docker-compose commands
- Container Manager GUI is the recommended approach
- Some features like compose networks behave differently
- Resource limits (CPU CFS) not supported on many models

## Troubleshooting on Synology

### Container won't start
1. Check logs in Container Manager → Container → Details → Log
2. Verify folder permissions: folders should be readable/writable
3. Make sure port 5678 isn't already in use

### Can't access n8n web interface
1. Verify container is running in Container Manager
2. Check firewall settings: Control Panel → Security → Firewall
3. Try accessing from same network first

### WebSocket errors
If you see WebSocket connection issues, you may need to configure Reverse Proxy:
1. Control Panel → Login Portal → Advanced → Reverse Proxy
2. Create rule for n8n with WebSocket support enabled

## Alternative: Use Cloud Automation Instead

If n8n setup on Synology is too complex, consider using:
- **Zapier** (easiest, paid)
- **Make.com** (powerful, paid)

These work perfectly with just your webhook service running on the Synology NAS, and don't require n8n installation.

## Next Steps

After n8n is installed and running:
1. Return to [SETUP_NOTION.md](./SETUP_NOTION.md) for workflow configuration
2. Follow the n8n workflow setup instructions
3. Test with a Notion job entry

## Additional Resources

- [Official n8n Documentation](https://docs.n8n.io/)
- [Marius Hosting Synology Guides](https://mariushosting.com/)
- [n8n Community Forums](https://community.n8n.io/)
