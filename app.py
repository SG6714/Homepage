from flask import Flask, render_template, request
import subprocess
import os

app = Flask(__name__)

# --- NEW: Command Whitelist (Crucial Security Feature) ---
# This is the list of commands that are explicitly permitted. Everything else will be blocked.
ALLOWED_COMMANDS = ['ls', 'cat', 'echo', 'pwd', 'whoami', 'date', 'uname']

# The safe working directory is now set by the Dockerfile's WORKDIR instruction.
# We confirm this on startup for security.
SAFE_DIRECTORY = '/app'
if os.getcwd() != SAFE_DIRECTORY:
    # This is a critical failure. If we aren't in the safe dir, the app will not start.
    raise RuntimeError(f"FATAL: Initial working directory is not {SAFE_DIRECTORY}")


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

    if request.method == 'POST':
        # User submitted a command via the form
        command_ran = request.form.get('user_text', '')
        command_output, command_error = execute_safely(command_ran)

    else: # GET request: First time visiting the page
        command_ran = 'cat README.md'
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
