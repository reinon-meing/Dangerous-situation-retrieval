"""
离线推理模拟器 —— 不连 B70、不动机器人，直接在 A100 上验证模型。

用法（在 A100 上）：
    cd /app && python3 offline_infer.py

它做什么：
    1. 用训练平台的配置（use_delta_joint_actions=False）加载 JAX checkpoint
    2. 从数据集里取一帧：三路相机图像 + 76 维状态 + prompt
    3. 让模型预测动作
    4. 和数据集里录制的真实动作逐关节对比

结论（2026-11-15 实测）：
    左臂 MAE 0.006~0.019，右臂 MAE 0.002~0.014 → 模型完全正常。
"""

import subprocess

import numpy as np
import pyarrow.parquet as pq
from PIL import Image

from openpi.policies import policy_config as PC
from openpi.shared import normalize as _n
from openpi.training import config as C

CFG_NAME = "pi05_teleavatar_v2"
CKPT = "/outputs/checkpoints/pi05_teleavatar_v2/v3-raised/6035"
DS = "/data/lerobot/move_raised"
EP = "episode_000000"
ASSET_DIR = "move_raised"   # checkpoint 里的 assets/<数据集目录名>

cfg = C.get_config(CFG_NAME)
print("use_delta_joint_actions =", cfg.data.use_delta_joint_actions)

_ns = _n.load(f"{CKPT}/assets/{ASSET_DIR}")
policy = PC.create_trained_policy(cfg, CKPT, norm_stats=_ns)
print("policy loaded")

t = pq.read_table(f"{DS}/data/chunk-000/{EP}.parquet")
state = np.asarray(t.column("observation.state").to_pylist(), dtype=np.float32)
acts = np.asarray(t.column("action").to_pylist(), dtype=np.float32)
print("frames", state.shape, acts.shape)


def frame(cam, idx):
    v = f"{DS}/videos/chunk-000/observation.images.{cam}/{EP}.mp4"
    out = f"/tmp/{cam}_{idx}.png"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{idx/45.0:.4f}", "-i", v,
         "-frames:v", "1", out],
        check=True,
    )
    return np.array(Image.open(out).convert("RGB"))


for idx in (0, 45, 90):
    ex = {
        "observation/state": state[idx],
        "observation/images/head_camera": frame("head_camera", idx),
        "observation/images/left_color": frame("left_color", idx),
        "observation/images/right_color": frame("right_color", idx),
        "prompt": "pick sandbag",
    }
    out = policy.infer(ex)
    pred = np.asarray(out["actions"])
    gt = acts[idx]
    print("\n=== frame", idx)
    print("  pred L :", np.round(pred[0, 0:7], 3).tolist())
    print("  gt   L :", np.round(gt[0:7], 3).tolist())
    print("  MAE  L : %.3f" % np.abs(pred[0, 0:7] - gt[0:7]).mean())
    print("  pred R :", np.round(pred[0, 8:15], 3).tolist())
    print("  gt   R :", np.round(gt[8:15], 3).tolist())
    print("  MAE  R : %.3f" % np.abs(pred[0, 8:15] - gt[8:15]).mean())
