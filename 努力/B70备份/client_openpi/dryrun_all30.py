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
print("CUR s14 = [%s]" % ", ".join("%.4f" % v for v in s14))
acts = np.asarray(wcp.WebsocketClientPolicy(host="127.0.0.1", port=8000).infer(obs)["actions"])
print("N =", len(acts))
for i in range(len(acts)):
    a = acts[i][ARM]
    L = ", ".join("%.4f" % v for v in a[0:7])
    R = ", ".join("%.4f" % v for v in a[7:14])
    print("S%02d L=[%s] R=[%s] grip=(%.3f,%.3f)" % (i+1, L, R, acts[i][7], acts[i][15]))
node.destroy_node(); rclpy.shutdown()
