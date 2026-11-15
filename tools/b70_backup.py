import os
import posixpath

import paramiko

HOST = os.environ.get("B70_HOST", "192.168.31.128")
USER = os.environ.get("B70_USER", "root")
PASS = os.environ.get("B70_PASS", "")  # 密码请用环境变量 B70_PASS 提供
DEST = r"E:\怀客松\努力\B70备份"

# (远端路径, 本地子目录)
FILES = [
    # /root 下的脚本
    ("/root/copy_usb_rest.sh", "root"),
    ("/root/dt.py", "root"),
    ("/root/fix_b70_absolute.py", "root"),
    ("/root/jogtest.sh", "root"),
    ("/root/patch_left_only.py", "root"),
    ("/root/pose_raised.sh", "root"),
    ("/root/pose_true.sh", "root"),
    ("/root/pose_v3.sh", "root"),
    ("/root/pose_v4.sh", "root"),
    ("/root/reset_arm.sh", "root"),
    ("/root/run_policy.sh", "root"),
    ("/root/run_v4.sh", "root"),
    ("/root/test_arm.sh", "root"),
    ("/root/usb_compare.sh", "root"),
    ("/root/v3_all_in_one.sh", "root"),
    ("/root/plan30.json", "root"),
    # 日志
    ("/root/server.log", "logs"),
    ("/root/server_v3.log", "logs"),
    ("/root/server_v3_fixed.log", "logs"),
    ("/root/convert_v3.log", "logs"),
    ("/root/convert_v4.log", "logs"),
    ("/root/conv-vaapi.log", "logs"),
    # 客户端 openpi
    ("/root/USB/deploy/client/openpi/arm_config.yml", "client_openpi"),
    ("/root/USB/deploy/client/openpi/auto_stop.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/dryrun_all30.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/dryrun_final30.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/dryrun_once.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/dryrun_steps.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/hold_now.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/infer_plan30.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/play30.py", "client_openpi"),
    ("/root/USB/deploy/client/openpi/play30_from_json.py", "client_openpi"),
    # 服务端（已打补丁的 policy）
    ("/root/USB/deploy/server/openpi/src/openpi/policies/teleavatar_v2_policy.py", "server_openpi"),
    ("/root/USB/deploy/server/openpi/src/openpi/policies/teleavatar_v2_policy.py.bak", "server_openpi"),
    # 归一化统计
    ("/root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised/norm_stats.json", "ckpt_assets/v3_move_raised"),
    ("/root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised/norm_stats.json.orig", "ckpt_assets/v3_move_raised"),
    ("/root/ckpt_out/pi05_teleavatar_v2_pytorch/assets/move_all/norm_stats.json", "ckpt_assets/v4_move_all"),
]

t = paramiko.Transport((HOST, 22))
t.connect(username=USER, password=PASS)
sftp = paramiko.SFTPClient.from_transport(t)

ok = 0
for remote, sub in FILES:
    local_dir = os.path.join(DEST, sub)
    os.makedirs(local_dir, exist_ok=True)
    local = os.path.join(local_dir, posixpath.basename(remote))
    try:
        sftp.get(remote, local)
        print("OK   %-12s %s" % (sub, posixpath.basename(remote)))
        ok += 1
    except Exception as e:
        print("SKIP %-12s %s  (%s)" % (sub, posixpath.basename(remote), e))

print("\n下载完成：%d/%d 个文件 -> %s" % (ok, len(FILES), DEST))
sftp.close()
t.close()

