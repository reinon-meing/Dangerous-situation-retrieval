"""自动停止 + 保持：检测到模型夹爪闭合后，等待"抬起"，自动停掉推理并锁住姿态。

用法（客户端容器内）：
    python /app/auto_stop.py

流程：
    ① 监听 /api/{left,right}_gripper/cmd
    ② 任一夹爪 trigger > 0.5 持续 0.15 秒  → 认为"夹住了"
    ③ 等 LIFT_SEC（默认 2.5 秒，让它抬起来）
    ④ pkill -INT 掉 main.py（停止推理）
    ⑤ 读取当前姿态，持续发布保持（夹爪保持夹紧）

参数（环境变量）：
    LIFT_SEC=2.5      夹住后等多久再停
    GRIP_CLOSED=0.5   判定闭合的阈值
    HOLD_TRIGGER=1.0  保持时的夹爪值（1=夹紧）
    GRIP_TIMEOUT=90   最多等多久还没夹住就放弃（秒）
"""

import os
import subprocess
import threading
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, JointState

LIFT_SEC = float(os.environ.get("LIFT_SEC", "2.5"))
GRIP_CLOSED = float(os.environ.get("GRIP_CLOSED", "0.5"))
HOLD_TRIGGER = float(os.environ.get("HOLD_TRIGGER", "1.0"))
GRIP_TIMEOUT = float(os.environ.get("GRIP_TIMEOUT", "90"))
HOLD_HZ = float(os.environ.get("HOLD_HZ", "50"))


def trig2eff(t: float) -> float:
    return 2.0 * (1.0 - t / 0.10) if t < 0.10 else -1.6 * (t - 0.10) / 0.90


class AutoStop(Node):
    def __init__(self):
        super().__init__("auto_stop_holder")
        self.left = None
        self.right = None
        self.gl = 0.0
        self.gr = 0.0
        self.lock = threading.Lock()

        self.create_subscription(JointState, "/left_arm/joint_states", self._on_left, 10)
        self.create_subscription(JointState, "/right_arm/joint_states", self._on_right, 10)
        self.create_subscription(Float32, "/api/left_gripper/cmd", self._on_gl, 10)
        self.create_subscription(Float32, "/api/right_gripper/cmd", self._on_gr, 10)

        self.pub_fsm = self.create_publisher(Float32, "/api/fsm/enable", 10)
        self.pub_l = self.create_publisher(JointState, "/api/left_arm/joint_cmd", 10)
        self.pub_r = self.create_publisher(JointState, "/api/right_arm/joint_cmd", 10)
        self.pub_gl = self.create_publisher(Float32, "/api/left_gripper/cmd", 10)
        self.pub_gr = self.create_publisher(Float32, "/api/right_gripper/cmd", 10)

    def _on_left(self, m):
        with self.lock:
            self.left = np.asarray(m.position[:7], dtype=np.float64)

    def _on_right(self, m):
        with self.lock:
            self.right = np.asarray(m.position[:7], dtype=np.float64)

    def _on_gl(self, m):
        with self.lock:
            self.gl = float(m.data)

    def _on_gr(self, m):
        with self.lock:
            self.gr = float(m.data)

    def snapshot(self):
        with self.lock:
            return self.left, self.right, self.gl, self.gr


rclpy.init()
node = AutoStop()
threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

print("等待模型夹住沙包（任一夹爪 trigger > %.2f）..." % GRIP_CLOSED)
t0 = time.time()
grasped = False
closed_since = None
while time.time() - t0 < GRIP_TIMEOUT:
    l, r, gl, gr = node.snapshot()
    hot = max(gl, gr) > GRIP_CLOSED
    if hot:
        if closed_since is None:
            closed_since = time.time()
        elif time.time() - closed_since > 0.15:
            grasped = True
            print("检测到夹爪闭合 (左 %.2f / 右 %.2f)" % (gl, gr))
            break
    else:
        closed_since = None
    time.sleep(0.02)

if not grasped:
    print("超时（%.0f 秒）没等到夹爪闭合，退出" % GRIP_TIMEOUT)
    rclpy.shutdown()
    raise SystemExit(0)

print("等 %.1f 秒让它抬起来..." % LIFT_SEC)
time.sleep(LIFT_SEC)

print("停止推理...")
subprocess.run(["pkill", "-INT", "-f", "teleavatar_v2/main.py"])
time.sleep(1.0)

l, r, gl, gr = node.snapshot()
if l is None or r is None:
    print("!! 读不到关节状态，退出")
    rclpy.shutdown()
    raise SystemExit(1)

print("锁住姿态:")
print("  左:", [round(float(v), 4) for v in l])
print("  右:", [round(float(v), 4) for v in r])
print("保持中，Ctrl-C 结束")

eff = trig2eff(HOLD_TRIGGER)
while rclpy.ok():
    now = node.get_clock().now().to_msg()
    for pub, arr in ((node.pub_l, l), (node.pub_r, r)):
        m = JointState()
        m.header.stamp = now
        m.position = arr.tolist()
        m.velocity = [0.0] * 7
        m.effort = [0.0] * 7
        pub.publish(m)
    node.pub_gl.publish(Float32(data=HOLD_TRIGGER))
    node.pub_gr.publish(Float32(data=HOLD_TRIGGER))
    node.pub_fsm.publish(Float32(data=1.0))
    time.sleep(1.0 / HOLD_HZ)
