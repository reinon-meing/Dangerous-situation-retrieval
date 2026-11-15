"""保持当前姿态 + 夹爪力（抓住后停住不动）。

用法（在客户端容器里）：
    python /app/hold_now.py                    # 保持当前姿态，夹爪夹紧
    GRIP_TRIGGER=0.0 python /app/hold_now.py   # 保持姿态，夹爪松开

Ctrl-C 结束（结束后心跳断，机器人 1 秒后自动暂停）。
"""

import os
import threading
import time

import numpy as np
import rclpy
from rclpy.executors import MultiThreadedExecutor

from examples.teleavatar_v2 import ros2_interface

TRIG = float(os.environ.get("GRIP_TRIGGER", "1.0"))   # 1.0 夹紧 / 0.0 张开
HZ = float(os.environ.get("HOLD_HZ", "50"))


def trig2eff(t: float) -> float:
    return 2.0 * (1.0 - t / 0.10) if t < 0.10 else -1.6 * (t - 0.10) / 0.90


rclpy.init()
node = ros2_interface.TeleavatarROS2Interface(video_decode="va")
ex = MultiThreadedExecutor()
ex.add_node(node)
threading.Thread(target=ex.spin, daemon=True).start()

pos = None
for _ in range(100):
    time.sleep(0.1)
    pos = node._current_arm_positions()
    if pos is not None:
        break

if pos is None:
    print("!! 读不到关节状态，放弃")
    raise SystemExit(1)

print("保持姿态:")
print("  左:", [round(float(v), 4) for v in pos[0:7]])
print("  右:", [round(float(v), 4) for v in pos[7:14]])
print("夹爪 trigger = %.2f （1.0=夹紧, 0.0=松开）" % TRIG)
print("按 Ctrl-C 结束")

a = np.zeros(16, dtype=np.float64)
a[0:7] = pos[0:7]
a[8:15] = pos[7:14]
a[7] = trig2eff(TRIG)
a[15] = trig2eff(TRIG)

t0 = time.time()
try:
    while rclpy.ok():
        node.publish_action(a)
        time.sleep(1.0 / HZ)
        el = time.time() - t0
        if int(el) % 5 == 0 and int(el * 10) % 10 == 0:
            print("  holding %.0f s" % el, end="\r")
except KeyboardInterrupt:
    print("\n停止保持")
finally:
    node.destroy_node()
    rclpy.shutdown()
