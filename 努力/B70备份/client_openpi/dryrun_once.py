import threading, time
import numpy as np
import rclpy
from openpi_client import image_tools
from openpi_client import websocket_client_policy as wcp
from rclpy.executors import MultiThreadedExecutor
from examples.teleavatar_v2 import ros2_interface

ARM = [0,1,2,3,4,5,6,8,9,10,11,12,13,14]
rclpy.init()
node = ros2_interface.TeleavatarROS2Interface(video_decode="va")
ex = MultiThreadedExecutor(); ex.add_node(node)
threading.Thread(target=ex.spin, daemon=True).start()

raw = None
for _ in range(100):
    time.sleep(0.2)
    try: raw = node.get_observation()
    except Exception: raw = None
    if raw is not None: break
if raw is None:
    print("!! no sensor data"); raise SystemExit(1)

st = np.asarray(raw["state"])
obs = {
 "observation/state": st,
 "observation/images/left_color": image_tools.convert_to_uint8(raw["images"]["left_color"]),
 "observation/images/right_color": image_tools.convert_to_uint8(raw["images"]["right_color"]),
 "observation/images/head_camera": image_tools.convert_to_uint8(raw["images"]["head_camera"]),
 "prompt": "pick sandbag",
}
s14 = np.concatenate([st[0:7], st[8:15]])
print("当前 s14:", np.round(s14,4).tolist())

ws = wcp.WebsocketClientPolicy(host="127.0.0.1", port=8000)
res = ws.infer(obs)
acts = np.asarray(res["actions"])
a0 = acts[0][ARM]
print("\n模型第 1 步:", np.round(a0,4).tolist())
print("模型第 5 步:", np.round(acts[4][ARM],4).tolist())
print("模型第 10 步:", np.round(acts[9][ARM],4).tolist())
print("\n与当前角的差:", np.round(a0 - s14,4).tolist())
print("平均偏差 %.4f  最大 %.4f" % (np.abs(a0-s14).mean(), np.abs(a0-s14).max()))
print("2x当前角 参考:", np.round(2*s14,4).tolist())
L = ", ".join("%.4f" % v for v in a0[0:7])
R = ", ".join("%.4f" % v for v in a0[7:14])
print("\n=== 可直接用的左臂指令 ===")
print("ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState \"{position: [%s]}\"" % L)
print("\n=== 可直接用的右臂指令 ===")
print("ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState \"{position: [%s]}\"" % R)
node.destroy_node(); rclpy.shutdown()
