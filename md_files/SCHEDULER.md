# 📅 Scheduler Documentation

## Overview

The scheduler automatically runs your trading system tasks every day at **4:00 AM local time**.

### Scheduled Tasks:
- **04:00 AM**: Update daily stock data (`daily_data.py`)
- **04:05 AM**: Update ML model with new data (`daily_model_update.py`)

All logs are saved to `log_files/scheduler_heartbeat.log`

---

## How to Use

### Option 1: Command Line (PowerShell Recommended)

```powershell
# Navigate to your project directory
cd C:\Users\SABIN\Desktop\Python-Project

# Run PowerShell launcher
.\start_scheduler.ps1

# Or run directly
.\pythonproject\Scripts\Activate.ps1
python scheduler.py
```

### Option 2: Batch File (Windows CMD)

```batch
# Simply double-click start_scheduler.bat
# Or run from command line
start_scheduler.bat
```

---

## Keeping it Running 24/7

### Option A: Windows Task Scheduler (Recommended)

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name it: `Stock Market Scheduler`
4. Set trigger to run when computer starts
5. Set action to run a PowerShell script:
   ```
   Program: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
   Arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\Users\SABIN\Desktop\Python-Project\start_scheduler.ps1"
   ```
6. Check "Run with highest privileges"
7. Click OK

### Option B: Run in Background with Windows Terminal

1. Open Windows Terminal
2. Tab into PowerShell
3. Run the scheduler in the background:
   ```powershell
   $job = Start-Job -FilePath "C:\Users\SABIN\Desktop\Python-Project\start_scheduler.ps1"
   Get-Job
   ```
4. The job will continue running even if you close the terminal

### Option C: Use `nohup` style persistence (Advanced)

Create a scheduled task that restarts the scheduler if it crashes:

```powershell
# Create a supervision script (supervisor.ps1)
while ($true) {
    python scheduler.py
    Start-Sleep -Seconds 10  # Restart if crashed
}
```

---

## Monitoring

### Check Logs

```bash
# View recent logs
tail -f log_files/scheduler_heartbeat.log

# Or in PowerShell
Get-Content log_files/scheduler_heartbeat.log -Tail 50 -Wait
```

### Check Status

Look for these log messages:

- `[START]` - Pipeline started
- `[OK]` - Tasks completed successfully  
- `[ERROR]` - Something went wrong
- `[INFO]` - General information

---

## Troubleshooting

### Scheduler not running at 4 AM?

1. **Check system time**: Verify your local time is correct
   ```powershell
   Get-Date
   ```

2. **Check if schedule was registered**: Look for "daily.at(04:00)" in logs

3. **Check logs for errors**: 
   ```powershell
   Get-Content log_files/scheduler_heartbeat.log | Select-String "ERROR"
   ```

### Tasks running but failing?

1. Run manually to check for issues:
   ```bash
   python data/daily_data.py
   python -m models.daily_model_update
   ```

2. Check individual log files:
   - `log_files/download.log`
   - `log_files/daily_sync.log`

### Virtual environment not activating?

Make sure `pythonproject` folder exists:
```powershell
ls pythonproject\Scripts\
```

---

## Advanced Configuration

### Change Scheduled Time

Edit `scheduler.py`:
```python
TARGET_TIME = "04:00"  # Change this to your desired time
```

### Add Email Notifications

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(subject, message):
    # Your email implementation
    pass

# In run_daily_pipeline():
if predict_process.returncode != 0:
    send_alert("Pipeline Failed", f"Error: {predict_process.stderr}")
```

### Add Slack/Discord Notifications

```python
import requests

def send_slack_alert(message):
    webhook_url = "your_webhook_url"
    requests.post(webhook_url, json={"text": message})
```

---

## File Structure

```
Python-Project/
├── scheduler.py                 # Main scheduler script
├── start_scheduler.bat          # Windows batch launcher
├── start_scheduler.ps1          # PowerShell launcher
├── SCHEDULER.md                 # This file
├── data/
│   └── daily_data.py           # Daily data update (4:00 AM)
├── models/
│   └── daily_model_update.py    # Model update (4:05 AM)
└── log_files/
    └── scheduler_heartbeat.log  # Scheduler logs
```

---

## Support

For issues:
1. Check logs in `log_files/scheduler_heartbeat.log`
2. Run tasks manually to isolate the problem
3. Verify database connection is working
4. Check if API rate limits are being hit

---

**Happy Trading!** 🚀
