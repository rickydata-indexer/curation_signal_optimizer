# Production Deployment Guide

## Quick Start

### Option 1: Manual Deployment (Recommended for testing)

1. **Make the deployment script executable:**
   ```bash
   chmod +x deploy.sh
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

3. **Access your app:**
   - Local: http://localhost:5174
   - Network: http://YOUR_SERVER_IP:5174

### Option 2: Systemd Service (Recommended for production)

1. **Install and build the app:**
   ```bash
   npm install
   npm run build
   ```

2. **Copy the service file to systemd:**
   ```bash
   sudo cp curation-optimizer.service /etc/systemd/system/
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable curation-optimizer
   sudo systemctl start curation-optimizer
   ```

4. **Check service status:**
   ```bash
   sudo systemctl status curation-optimizer
   ```

5. **View logs:**
   ```bash
   sudo journalctl -u curation-optimizer -f
   ```

## Port Information

- **Port 5174** is currently available and safe to use
- This port is in the user/dynamic range (1024-65535)
- Not a well-known service port, so unlikely to conflict
- Already configured in your application

## Firewall Configuration

If you have a firewall enabled, allow port 5174:

```bash
# For UFW (Ubuntu)
sudo ufw allow 5174

# For firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5174/tcp
sudo firewall-cmd --reload
```

## SSL/HTTPS Setup (Optional but Recommended)

For production, consider setting up a reverse proxy with SSL:

1. **Install nginx:**
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **Create nginx configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/curation-optimizer
   ```

3. **Add this configuration:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5174;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

4. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/curation-optimizer /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Troubleshooting

### Check if port is in use:
```bash
lsof -i :5174
```

### Kill process using the port:
```bash
sudo kill -9 $(lsof -t -i:5174)
```

### Check service logs:
```bash
sudo journalctl -u curation-optimizer -n 50
```

### Restart the service:
```bash
sudo systemctl restart curation-optimizer
```
