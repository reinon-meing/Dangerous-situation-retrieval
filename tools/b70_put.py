import os
import sys

import paramiko

HOST = os.environ.get("B70_HOST", "192.168.31.128")
USER = os.environ.get("B70_USER", "root")
PASS = os.environ.get("B70_PASS", "")  # 密码请用环境变量 B70_PASS 提供

local, remote = sys.argv[1], sys.argv[2]
t = paramiko.Transport((HOST, 22))
t.connect(username=USER, password=PASS)
sftp = paramiko.SFTPClient.from_transport(t)
sftp.put(local, remote)
print("uploaded", local, "->", remote)
sftp.close()
t.close()

