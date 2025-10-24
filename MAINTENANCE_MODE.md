# Maintenance Mode

This application includes a maintenance mode feature that displays a "temporarily down for maintenance" page while you perform updates or maintenance tasks.

## How It Works

The maintenance mode system uses a simple flag file (`instance/MAINTENANCE_MODE`). When this file exists, all requests to the application will show the maintenance page instead of the normal application.

## Usage

### Enable Maintenance Mode (Local)
```bash
./enable-maintenance.sh
```

### Disable Maintenance Mode (Local)
```bash
./disable-maintenance.sh
```

### Deploy with Maintenance Mode (Production)
The `deploy-with-maintenance.sh` script automates the entire deployment process:
```bash
./deploy-with-maintenance.sh
```

This script will:
1. Enable maintenance mode on the server
2. Pull latest code from GitHub
3. Install/update dependencies
4. Restart the application
5. Wait for startup
6. Disable maintenance mode

Total downtime: ~5-10 seconds of actual maintenance page display

### Manual Server Control
If you need to manually control maintenance mode on the server:

**Enable:**
```bash
ssh dg_precinct_root "touch /home/precinct/precinct/instance/MAINTENANCE_MODE"
```

**Disable:**
```bash
ssh dg_precinct_root "rm -f /home/precinct/precinct/instance/MAINTENANCE_MODE"
```

## Maintenance Page

The maintenance page (`templates/maintenance.html`) displays:
- Professional animated design with branding colors
- "We'll Be Right Back!" message
- Loading animation
- Expected return time notice
- Responsive layout

You can customize the maintenance page by editing `templates/maintenance.html`.

## Technical Details

- **HTTP Status Code:** 503 (Service Unavailable)
- **Check Location:** `main.py` - `check_maintenance_mode()` before_request handler
- **Flag File:** `instance/MAINTENANCE_MODE` (empty file, presence indicates maintenance mode)
- **Static Files:** Always accessible (CSS, JS, images) even during maintenance
- **Implementation:** Flask before_request decorator ensures all requests are checked

## Best Practices

1. **Always use maintenance mode for deployments** - Use `deploy-with-maintenance.sh`
2. **Test locally first** - Run `./enable-maintenance.sh` locally to see the page
3. **Quick updates** - The flag file approach means zero config changes needed
4. **Monitor the process** - Watch the deployment script output for any errors
5. **Have a rollback plan** - Keep previous version accessible via git

## Troubleshooting

**Q: Maintenance mode won't disable**  
A: Manually remove the flag file: `rm -f instance/MAINTENANCE_MODE` (or on server via SSH)

**Q: Getting 503 errors after disabling**  
A: The file might still exist. Check with `ls -la instance/` and remove if present.

**Q: Can I customize the maintenance message?**  
A: Yes! Edit `templates/maintenance.html` and modify the text, styling, or add estimated time.

**Q: Does this work with the systemd service?**  
A: Yes! The maintenance check happens at the Flask application level, before any route processing.
