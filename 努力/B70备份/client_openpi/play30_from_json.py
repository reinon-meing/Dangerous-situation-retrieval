"""回放 /tmp/plan30.json 里的 30 步（含夹爪），使用客户端自己的 publish_action。"""

import json
import os
import threading
import time

import numpy as np
import rclpy
from rclpy.executors import MultiThreadedExecutor

from examples.teleavatar_v2 import ros2_interface

STEP_DELAY = float(os.environ.get("STEP_DELAY", "0.088"))
HOLD_AFTER = float(os.environ.get("HOLD_AFTER", "1.0"))

plan = json.load(open("/tmp/plan30.json"))["plan"]
_n = int(os.environ.get("STEP_COUNT", "0"))
if _n > 0:
    plan = plan[:_n]

rclpy.init()
node = ros2_interface.TeleavatarROS2Interface(video_decode="va")
ex = MultiThreadedExecutor()
ex.add_node(node)
threading.Thread(target=ex.spin, daemon=True).start()
time.sleep(1.0)

print("回放 %d 步，每步 %.3f s（共约 %.1f s）" % (
    len(plan), STEP_DELAY, len(plan) * STEP_DELAY))
for i, p in enumerate(plan, 1):
    a = np.zeros(16, dtype=np.float64)
    a[0:7] = p["L"]
    a[8:15] = p["R"]
    # publish_action 期望夹爪为 effort，这里把 trigger 反算回 effort
    a[7] = 2.0 * (1.0 - p["gL"] / 0.10) if p["gL"] < 0.10 else -1.6 * (p["gL"] - 0.10) / 0.90
    a[15] = 2.0 * (1.0 - p["gR"] / 0.10) if p["gR"] < 0.10 else -1.6 * (p["gR"] - 0.10) / 0.90
    node.publish_action(a)
    if i % 5 == 0 or i == len(plan):
        print("  step %d/%d" % (i, len(plan)))
    time.sleep(STEP_DELAY)

print("保持 %.1f s" % HOLD_AFTER)
time.sleep(HOLD_AFTER)
print("回放结束")
node.destroy_node()
rclpy.shutdown()
