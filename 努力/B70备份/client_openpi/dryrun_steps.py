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
acts = np.asarray(ws.infer(obs)["actions"])
g = acts[0]
print("夹爪 (左,右) 第1步: %.3f %.3f" % (g[7], g[15]))
for i in range(10):
    a = acts[i][ARM]
    L = ", ".join("%.4f" % v for v in a[0:7])
    R = ", ".join("%.4f" % v for v in a[7:14])
    print("\n# 第 %d 步" % (i+1))
    print("L: [%s]" % L)
    print("R: [%s]" % R)
node.destroy_node(); rclpy.shutdown()
