import json
import threading
import time

import numpy as np
import rclpy
from openpi_client import image_tools
from openpi_client import websocket_client_policy as wcp
from rclpy.executors import MultiThreadedExecutor

from examples.teleavatar_v2 import ros2_interface

ARM = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14]
LIM_UP = {"L": [1.8, 1.9, 1.3, 2.2, 1.8, 1.4, 0.7],
          "R": [1.8, 0.0, 2.6, -0.25, 1.8, 1.4, 0.7]}
LIM_LO = {"L": [-1.8, 0.0, -2.6, 0.25, -1.8, -1.4, -0.7],
          "R": [-1.8, -1.9, -1.3, -2.2, -1.8, -1.4, -0.7]}


def eff2trig(e):
    return 0.10 * (1.0 - e / 2.0) if e > 0 else 0.10 - e * 0.90 / 1.6


rclpy.init()
node = ros2_interface.TeleavatarROS2Interface(video_decode="va")
ex = MultiThreadedExecutor()
ex.add_node(node)
threading.Thread(target=ex.spin, daemon=True).start()

raw = None
for _ in range(100):
    time.sleep(0.2)
    try:
        raw = node.get_observation()
    except Exception:
        raw = None
    if raw is not None:
        break
if raw is None:
    print("!! no sensor data")
    raise SystemExit(1)

st = np.asarray(raw["state"])
obs = {
    "observation/state": st,
    "observation/images/left_color": image_tools.convert_to_uint8(raw["images"]["left_color"]),
    "observation/images/right_color": image_tools.convert_to_uint8(raw["images"]["right_color"]),
    "observation/images/head_camera": image_tools.convert_to_uint8(raw["images"]["head_camera"]),
    "prompt": "pick sandbag",
}
s14 = np.concatenate([st[0:7], st[8:15]])
acts = np.asarray(wcp.WebsocketClientPolicy(host="127.0.0.1", port=8000).infer(obs)["actions"])

plan = []
for i in range(len(acts)):
    a = acts[i][ARM]
    L = np.clip(a[0:7], LIM_LO["L"], LIM_UP["L"])
    R = np.clip(a[7:14], LIM_LO["R"], LIM_UP["R"])
    plan.append({
        "L": [round(float(v), 4) for v in L],
        "R": [round(float(v), 4) for v in R],
        "gL": round(float(eff2trig(float(acts[i][7]))), 4),
        "gR": round(float(eff2trig(float(acts[i][15]))), 4),
    })

with open("/tmp/plan30.json", "w") as fh:
    json.dump({"state": [round(float(v), 4) for v in s14], "plan": plan}, fh, indent=1)

print("CUR = [%s]" % ", ".join("%.4f" % v for v in s14))
for i, p in enumerate(plan, 1):
    print("S%02d L=%s R=%s G=(%.3f,%.3f)" % (
        i, p["L"], p["R"], p["gL"], p["gR"]))
print("saved /tmp/plan30.json")
node.destroy_node()
rclpy.shutdown()
