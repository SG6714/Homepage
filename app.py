from flask import Flask, render_template, request
import subprocess
import os
import sys
import datetime

app = Flask(__name__)

# --- Paths and constants ---
SAFE_DIRECTORY = '/app'
LOG_FILE = os.path.join(SAFE_DIRECTORY, 'visitors.log')

# --- NEW: Command Whitelist (Crucial Security Feature) ---
# This is the list of commands that are explicitly permitted. Everything else will be blocked.
ALLOWED_COMMANDS = ['ls', 'cat', 'echo', 'pwd', 'whoami', 'date', 'uname']
if os.getcwd() != SAFE_DIRECTORY:
    # This is a critical failure. If we aren't in the safe dir, the app will not start.
    raise RuntimeError(f"FATAL: Initial working directory is not {SAFE_DIRECTORY}")


def _detect_device(ua: str) -> str:
    """Return a concise device/browser label from a User-Agent string."""
    ua_lower = ua.lower()
    # Device category
    if 'ipad' in ua_lower or ('android' in ua_lower and 'mobile' not in ua_lower):
        device = 'Tablet'
    elif 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        device = 'Mobile'
    else:
        device = 'Desktop'
    # Browser
    if 'edg/' in ua_lower or 'edge/' in ua_lower:
        browser = 'Edge'
    elif 'firefox/' in ua_lower:
        browser = 'Firefox'
    elif 'opr/' in ua_lower or 'opera/' in ua_lower:
        browser = 'Opera'
    elif 'chrome/' in ua_lower:
        browser = 'Chrome'
    elif 'safari/' in ua_lower:
        browser = 'Safari'
    else:
        browser = 'Unknown'
    return f"{device}/{browser}"


def log_visitor(ip: str, device: str, command: str) -> None:
    """Append a single log line to visitors.log."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    line = f"[{ts}] ip={ip} device={device} cmd={command!r}\n"
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line)
    except OSError as e:
        print(f"WARNING: Could not write to {LOG_FILE}: {e}", file=sys.stderr)

def execute_safely(command_string: str):
    """
    Safely executes a command string by checking it against a whitelist
    and running it without shell=True. Returns a tuple of (output, error).
    """
    # Strip leading/trailing whitespace and split the command
    command_parts = command_string.strip().split()

    if not command_parts:
        return None, "No command entered."

    # --- NEW: Whitelist Security Check ---
    if command_parts[0] not in ALLOWED_COMMANDS:
        return None, f"Error: The command '{command_parts[0]}' is not permitted. Allowed commands are: {', '.join(ALLOWED_COMMANDS)}"

    # --- Redundant check to ensure we are still in the safe directory ---
    if os.getcwd() != SAFE_DIRECTORY:
        return None, "CRITICAL ERROR: Application is outside the safe directory. Halting."

    try:
        # --- Execute without the shell ---
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            timeout=10 # Protects against long-running commands
        )
        return result.stdout, result.stderr

    except FileNotFoundError:
        # This case is now less likely due to the whitelist, but good to keep.
        return None, f"Command not found: '{command_parts[0]}'"
    except subprocess.TimeoutExpired:
        return None, "Command timed out after 10 seconds."
    except Exception as e:
        return None, f"An execution error occurred: {str(e)}"


@app.route('/', methods=['GET', 'POST'])
def index():
    command_ran = None
    command_output = None
    command_error = None

    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    device = _detect_device(request.headers.get('User-Agent', ''))

    if request.method == 'POST':
        # User submitted a command via the form
        command_ran = request.form.get('user_text', '')
        log_visitor(ip, device, command_ran)
        command_output, command_error = execute_safely(command_ran)

    else: # GET request: First time visiting the page
        command_ran = 'cat README.md'
        log_visitor(ip, device, command_ran)
        if os.path.exists('README.md'):
            command_output, command_error = execute_safely(command_ran)
        else:
            command_error = "Default 'README.md' not found. Please create it in the 'me' directory."

    return render_template(
        'index.html',
        command_ran=command_ran,
        command_output=command_output,
        command_error=command_error
    )
