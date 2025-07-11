# Network Ping Monitor

A simple web-based application to test network connectivity to groups of hosts using real ping commands. Perfect for monitoring wireless network devices and getting quick status reports.

## Features

- ✅ **Real ping tests** (not HTTP checks)
- ✅ **Host grouping** with friendly names
- ✅ **Concurrent testing** for fast results
- ✅ **Connection quality** based on packet loss
- ✅ **Color-coded results** for quick assessment
- ✅ **Docker containerized** for easy deployment
- ✅ **Responsive web interface** works on mobile

## Quick Start

### 1. Create Project Directory
```bash
mkdir ping-monitor
cd ping-monitor
```

### 2. Create Files
Save each of the provided files in your project directory:
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Easy deployment
- `hosts.yaml` - Host configuration
- `templates/index.html` - Web interface (create `templates/` folder first)

### 3. Customize Your Hosts
Edit `hosts.yaml` with your actual network devices:

```yaml
groups:
  office_devices:
    - ip: 192.168.1.10
      name: "Reception Printer"
    - ip: 192.168.1.11  
      name: "Conference Room TV"
  
  servers:
    - ip: 192.168.1.100
      name: "File Server"
```

### 4. Deploy with Docker
```bash
# Build and start the container
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 5. Access the Application
Open your web browser to: `http://localhost:5000`

## Configuration

### Host Format
You can use either format in `hosts.yaml`:

**New format (with friendly names):**
```yaml
groups:
  office:
    - ip: 192.168.1.10
      name: "Reception Desk"
```

**Old format (IP only):**
```yaml
groups:
  office:
    - 192.168.1.10
```

### Connection Quality Thresholds
- 🟢 **Good**: 0% packet loss
- 🟡 **Fair**: 1-20% packet loss  
- 🔴 **Poor**: >20% packet loss or unreachable

## Usage

1. **Select groups** to test (or "All Groups")
2. **Click "Start Ping Test"**
3. **View results** with color-coded status
4. **Clear results** to run another test

Results show:
- Device name and IP address
- Group membership
- Connection status and quality
- Packet loss percentage
- Average, min, and max latency

## Docker Commands

```bash
# View logs
docker logs ping-monitor

# Stop the container
docker-compose down

# Rebuild after changes
docker-compose up --build

# Update hosts without rebuilding
# (just edit hosts.yaml and restart)
docker-compose restart
```

## Troubleshooting

**"Network error" when testing:**
- Check `docker logs ping-monitor` for errors
- Ensure the container is running: `docker ps`
- Test direct access: `curl http://localhost:5000`

**No hosts showing up:**
- Verify `hosts.yaml` syntax is correct
- Check that `templates/index.html` exists
- Restart container after config changes

**Port already in use:**
- Change port in `docker-compose.yml`: `"5001:5000"`
- Or stop conflicting service: `docker-compose down`

## File Structure
```
ping-monitor/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies  
├── Dockerfile            # Container setup
├── docker-compose.yml    # Deployment config
├── hosts.yaml           # Host configuration
├── README.md            # This file
└── templates/
    └── index.html       # Web interface
```

## Advanced Configuration

### Custom Ping Parameters
Edit `ping_host()` function in `app.py`:
- `count=4` - Number of ping packets
- `timeout=5` - Timeout in seconds

### Resource Limits
Modify `docker-compose.yml` to adjust memory/CPU limits.

### Port Changes
Change `ports: "5000:5000"` in `docker-compose.yml` to use different port.

## License
This project is open source. Feel free to modify and distribute.
