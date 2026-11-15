import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HOST = os.environ.get("B70_HOST", "192.168.31.128")
USER = os.environ.get("B70_USER", "root")
PASS = os.environ.get("B70_PASS", "")  # 密码请用环境变量 B70_PASS 提供


def run(cmd: str, timeout: int = 120) -> int:
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=22, username=USER, password=PASS, timeout=15,
                banner_timeout=30, auth_timeout=30)
    stdin, stdout, stderr = cli.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("[stderr]", file=sys.stderr)
        print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)
    cli.close()
    return code


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "hostname"
    sys.exit(run(command))

