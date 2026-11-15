# 危境取物 · 灵御 TA2 端到端 VLA 实现

> 具身智能黑客松「危境取物」赛题的项目仓库。
> 在 **Intel 双卡 B70** 平台上，跑通 **π0.5（pi05）端到端视觉-语言-动作模型** 的完整链路：
> 数据采集 → 硬件加速转换 → 云端训练 → 本地 XPU 推理 → 真机执行。

---

## 一句话成果

| 指标 | 实测值 |
|---|---|
| 视频解码 | **45.3 fps**，延迟 **8.4 ms**，0 丢包 |
| 推理耗时 | **0.28 s**（热缓存） |
| 关节状态流 | **200 Hz** |
| 指令下发 | 45 Hz → **200 Hz** 插值 |
| 手臂执行精度 | **0.003 弧度**（≈0.17°） |
| 数据转换加速 | **≈50×**（30 分钟 → 35.5 秒，VA-API 硬件编解码） |
| 离线模型误差 | 整条 episode **0.005~0.008 弧度**，不累积 |

---

## 目录结构

```
.
├── README.md                     ← 本文件
├── 总结/
│   └── 技术方案与答辩素材.md      ← 技术栈 / 8 个工程巧思 / 答辩问答 / PPT 大纲
├── 努力/                          ← 全过程记录与可复用资产
│   ├── 正确尝试总结.md            ← 技术总结与证据链
│   ├── 实机跑通记录.md            ← ★ 从零到跑通的完整步骤
│   ├── 进度记录.md / 明日交接.md
│   ├── 完整启动流程.md / 手臂驱动操作手册.md / 复位.md
│   ├── B70部署清单.md / b70_脚本说明.md / 今天流程_v4部署.md
│   ├── 停住不动方案.md
│   ├── 脚本/                      ← pose_*/run_policy/test_arm/fix_b70_absolute 等
│   ├── 模拟器/                    ← 离线推理验证与对照实验
│   ├── 参考画面/                  ← 训练数据首帧（场景对照基准）
│   ├── B70备份/                   ← 部署关键文件存档
│   ├── hold_now.py / auto_stop.py
│   └── ...
└── tools/                         ← 远程运维小工具（SSH 批量执行/传输）
```

---

## 系统架构

```
┌─────────────┐        ┌──────────────────┐        ┌─────────────┐
│  灵御 TA2   │ 视频流 │  B70 工控机        │  训练  │  A100 平台  │
│  双臂机器人 │──UDP──▶│  · VA-API 硬解     │◀──────▶│  4×A100     │
│             │ zenoh  │  · XPU 推理        │  ckpt  │             │
│             │◀──────▶│  · 双臂指令下发     │        │             │
└─────────────┘ 200 Hz └──────────────────┘        └─────────────┘
```

一次推理的数据流：

```
3 路相机（RTP/H.265） + 76 维状态 + 语言指令
    → B70 GPU0 π0.5 推理（8.4 ms 解码 + 动作块）
    → 16 维动作 × 30 步
    → 45 Hz → 200 Hz 插值
    → /api/{left,right}_arm/joint_cmd
```

---

## 技术栈

| 层 | 组件 |
|---|---|
| 模型 | π0.5（pi05）：2B VLM + 300M 动作专家 |
| 训练 | openpi（JAX）+ LeRobot 数据格式，4×A100 |
| 推理 | PyTorch + Intel XPU（`torch.xpu`），Arc Pro B70 |
| 通信 | zenoh（ROS2 桥）+ RTP/H.265 |
| 解码 | VA-API（`vah265dec` / iHD / `libvapp`） |
| 转换 | `rosbag2lerobot`（MCAP → LeRobot） |
| 容器 | `openpi-xpu-env` / `openpi-xpu-client` |

---

## 快速开始

### 前提

- B70 工控机（Ubuntu 24.04 + 2× Intel Arc Pro B70）
- 机器人处于 **API 模式**（`meta_mode=1`），左右臂使能、控制模式 joint
- 机器人视频推流指向 B70 的 UDP 8890

### 1. 起推理 server（抓取模型 → 8000）

```bash
cd /root/USB/deploy/server/openpi-xpu-env
OPENPI_DIR=/root/USB/deploy/server/openpi \
DOCKER_RUN_EXTRA="-p 8000:8000 -v /root/ckpt_out_v3/pi05_teleavatar_v2_pytorch:/ckpt:ro" \
  ./scripts/run.sh python scripts/serve_policy.py --env TELEAVATAR --warmup \
  policy:checkpoint --policy.config pi05_teleavatar_v2 --policy.dir /ckpt \
  --policy.pytorch-device xpu --policy.pytorch-compile-mode default
```

> 看到 `Loaded norm stats from /ckpt/assets/path-to-dataset` 和 `server listening on 0.0.0.0:8000` 即成功。

### 2. 起客户端容器

```bash
cd /root/USB/deploy
export OPENPI_DIR=$(pwd)/client/openpi
RENDER=/dev/dri/renderD129 ZENOH_ENDPOINT=tcp/<ROBOT_IP>:9000 \
  client/run_client.sh start
```

### 3. 摆位 + 跑模型

```bash
# 摆到训练起点
docker exec -i openpi-xpu-client /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/pose_v3.sh

# 慢速推理（30 秒自动停）
docker exec -i openpi-xpu-client /usr/local/bin/openpi-client-entrypoint.sh bash -c \
 'timeout -s INT 30 python examples/teleavatar_v2/main.py --remote-host 127.0.0.1 \
  --remote-port 8000 --video-decode va --prompt "pick sandbag" \
  --control-frequency 20 --open-loop-horizon 10'
```

### 4. 停止（`Ctrl-C` 无效，必须这样停）

```bash
docker exec openpi-xpu-client pkill -INT -f "teleavatar_v2/main.py"
```

---

## 关键工程经验

详见 [`总结/技术方案与答辩素材.md`](总结/技术方案与答辩素材.md)，摘要：

1. **离线推理器**：在 A100 上用数据集帧直接验证模型，不碰机器人即可定位缺陷
2. **靠 `norm_stats` 量级判断动作语义**：`q01` 在 0.4~1.5 = 绝对关节角，`±0.1` = 增量
3. **状态布局陷阱**：`observation.state` 是 `[左臂7][左夹爪][右臂7][右夹爪]`，取右臂用 `[8:15]`
4. **识别假数据**：`action[t]` 与 `state[t+1]` 差 0.23 弧度 → 录制时该臂未跟随
5. **双 server 并行**：8000 抓取 / 8001 放置，切换零等待
6. **`timeout -s INT`**：非交互 bash 的后台进程会忽略 SIGINT，必须前台 + timeout

---

## 说明

- 本仓库**不含**数据集、模型权重、原始录制包与镜像（体积过大）
- 不含比赛官方文档与第三方代码
- 运行前请自行准备：openpi 代码、checkpoint、`arm_config.yml`、机器人环境
