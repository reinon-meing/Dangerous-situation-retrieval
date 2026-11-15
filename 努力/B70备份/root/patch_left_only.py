import py_compile
import shutil

P = "/root/USB/deploy/client/openpi/examples/teleavatar_v2/ros2_interface.py"
src = open(P, encoding="utf-8").read()

if "PARK_RIGHT_ARM" in src:
    print("already patched, nothing to do")
    raise SystemExit(0)

# 1) 确保有 import os
if "\nimport os\n" not in src:
    src = src.replace("\nimport math\n", "\nimport math\nimport os\n", 1)

# 2) 在 arm14/grip2 计算之后插入“固定右臂”
old = (
    "        arm14 = np.concatenate([actions[0:7], actions[8:15]]).astype(np.float64)\n"
    "        grip2 = np.array([actions[7], actions[15]], dtype=np.float64)\n"
)
new = old + (
    "        # [LEFT-ARM-ONLY] 固定右臂在训练起点，忽略模型对右臂的输出\n"
    "        # 关掉：PARK_RIGHT_ARM=0 传给同一个 shell\n"
    "        if os.environ.get(\"PARK_RIGHT_ARM\", \"1\") == \"1\":\n"
    "            arm14[7:14] = (-0.184, -1.271, 0.625, -1.133, -0.436, -0.466, -0.658)\n"
    "            grip2[1] = 0.0\n"
)
assert src.count(old) == 1, f"anchor found {src.count(old)} times"

shutil.copy(P, P + ".bak")
open(P, "w", encoding="utf-8").write(src.replace(old, new))
py_compile.compile(P, doraise=True)
print("patched ok ->", P)
print("backup ->", P + ".bak")
