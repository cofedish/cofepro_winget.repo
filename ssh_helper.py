#!/usr/bin/env python3
"""SSH helper to execute commands on remote server"""
import sys
import subprocess

def run_ssh_command(command):
    """Run command on remote server via SSH"""
    # Using ssh with password in environment or key
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        'root@cofemon.online',
        command
    ]

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print("SSH command timed out", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ssh_helper.py '<command>'")
        sys.exit(1)

    command = ' '.join(sys.argv[1:])
    exit_code = run_ssh_command(command)
    sys.exit(exit_code)
