"""
B70 推理端修复：把"增量动作"改回"绝对动作"，与训练端一致。

背景（2026-11-15 离线实测确认）：
    训练平台（A100）的配置 pi05_teleavatar_v2 是 use_delta_joint_actions=False（绝对动作），
    B70 上的 openpi 代码版本较新，默认 True（增量动作）。
    结果：B70 推理时把当前关节角加了两遍 → 下发值 ≈ 当前值×2 → 全部顶到限位。

修复内容（三处，都在一个文件里）：
    1. TeleavatarInputs.__call__  不再从动作里减 state
    2. TeleavatarOutputs.__call__ 不再把 state 加回动作
    3. delta_action_anchor()      恒返回 None（关掉 RTC 的锚点）
    并且把 norm_stats.json 恢复成原始的"绝对"统计（.orig 备份）。

用法（在 B70 上，root）：
    python3 fix_b70_absolute.py
然后重启 server。

回退：
    cp ros2_interface.py... （不动）
    cp teleavatar_v2_policy.py.bak teleavatar_v2_policy.py
    cp norm_stats.json.orig norm_stats.json
"""

import os
import py_compile
import shutil

POLICY = "/root/USB/deploy/server/openpi/src/openpi/policies/teleavatar_v2_policy.py"
CKPTS = [
    "/root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised",
    "/root/ckpt_out/pi05_teleavatar_v2_pytorch/assets/move_all",
]

src = open(POLICY, encoding="utf-8").read()

if "ABS-ACTIONS" in src:
    print("policy 已打过补丁")
else:
    subs = [
        (
            "            if self.use_delta_joint_actions:\n"
            "                selected_actions[:, 0:7] -= state_14d[np.newaxis, 0:7]\n",
            "            if False:  # [ABS-ACTIONS] checkpoint 用绝对动作训练\n"
            "                selected_actions[:, 0:7] -= state_14d[np.newaxis, 0:7]\n",
        ),
        (
            "        if self.use_delta_joint_actions:\n"
            "            state = np.asarray(data[\"state\"])\n",
            "        if False:  # [ABS-ACTIONS]\n"
            "            state = np.asarray(data[\"state\"])\n",
        ),
        (
            "        if not self.use_delta_joint_actions:\n"
            "            return None\n",
            "        if True:  # [ABS-ACTIONS] 关掉 RTC 锚点\n"
            "            return None\n",
        ),
    ]
    for old, new in subs:
        n = src.count(old)
        assert n == 1, f"匹配 {n} 次，期望 1 次：{old[:60]!r}"
        src = src.replace(old, new)

    shutil.copy(POLICY, POLICY + ".bak")
    open(POLICY, "w", encoding="utf-8").write(src)
    py_compile.compile(POLICY, doraise=True)
    print("policy 已改为绝对动作，备份 ->", POLICY + ".bak")

for d in CKPTS:
    f = os.path.join(d, "norm_stats.json")
    b = os.path.join(d, "norm_stats.json.orig")
    if os.path.exists(b):
        shutil.copy(b, f)
        print("已恢复原始（绝对）归一化统计:", d)
    else:
        print("跳过（没有 .orig 备份）:", d)

print("\n完成。下一步：重启 server，然后摆位 + 跑模型。")
