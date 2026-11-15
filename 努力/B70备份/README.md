# B70 备份（2026-11-15 18:05）

> 从 B70 `192.168.31.128` 拉回的关键文件，共 **37 个 / 163 KB**。
> 全部经过校验：补丁版与备份版可比对，归一化统计量级正确。

---

## 目录说明

### `server_openpi/` —— **最重要**

| 文件 | 说明 |
|---|---|
| `teleavatar_v2_policy.py` | **已打补丁的推理代码**（3 处 `[ABS-ACTIONS]`），实机跑通的就是它 |
| `teleavatar_v2_policy.py.bak` | 打补丁前的原版（增量逻辑），出问题可回退 |

校验结果：
- 补丁版：第 204/233/297 行有 `[ABS-ACTIONS]` 标记 ✅
- 备份版：0 处标记（原版）✅

**恢复方法**：把 `teleavatar_v2_policy.py` 放回
`/root/USB/deploy/server/openpi/src/openpi/policies/`，然后**重启 server**。

---

### `ckpt_assets/` —— 归一化统计

| 文件 | 说明 |
|---|---|
| `v3_move_raised/norm_stats.json` | v3（move_raised）的**绝对**统计，q01 = `[0.029, 1.036, -1.095]` |
| `v3_move_raised/norm_stats.json.orig` | 同上（原始备份，内容一致） |
| `v4_move_all/norm_stats.json` | v4（move_all）的绝对统计 |

> ⚠️ **判据**：`actions.q01` 是 **0.4~1.5 量级 = 绝对动作（正确）**；如果是 **±0.1 量级 = 增量（错误配置）**。

放回位置：
```
/root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised/norm_stats.json
/root/ckpt_out/pi05_teleavatar_v2_pytorch/assets/move_all/norm_stats.json
```

---

### `client_openpi/` —— 客户端代码与工具

| 文件 | 说明 |
|---|---|
| `arm_config.yml` | **关节限位表**（左右臂镜像范围），右 j4 = `[-2.2, -0.25]` |
| `hold_now.py` | 保持当前姿态 + 夹爪力（抓住后停住） |
| `auto_stop.py` | **自动检测夹爪闭合 → 等抬起 → 停推理 → 锁定姿态** |
| `infer_plan30.py` | 推理一次，把 30 步计划存到 `/tmp/plan30.json` |
| `play30_from_json.py` | 回放 `/tmp/plan30.json`（可 `STEP_COUNT`/`STEP_DELAY` 控制） |
| `play30.py` | 早期版本（计划写死在脚本里） |
| `dryrun_once.py` | 只读推理演练（单步，判断 delta/绝对） |
| `dryrun_steps.py` / `dryrun_all30.py` / `dryrun_final30.py` | 只读推理打印多步 |

放回位置：`/root/USB/deploy/client/openpi/`（容器内即 `/app/`，注意 `/app` 只读，写文件到 `/tmp`）。

---

### `root/` —— B70 根目录脚本

| 文件 | 说明 |
|---|---|
| `pose_v3.sh` | **v3 起点摆位**（最常用） |
| `pose_v4.sh` | v4 起点摆位 |
| `pose_raised.sh` | v3 起点的旧版本（move_raised 均值，与 pose_v3 相同） |
| `pose_true.sh` | 现场确认的"真实复位点"（≈v4 起点） |
| `reset_arm.sh` | 官方零位（调 `zero.py`，带心跳） |
| `run_policy.sh` | 心跳 + `main.py`（跑模型） |
| `v3_all_in_one.sh` | 摆位 + 跑模型（一次 exec 完成） |
| `test_arm.sh` | 手臂自检（发一个固定角度验证链路） |
| `fix_b70_absolute.py` | **B70 推理端修复脚本**（3 处补丁 + 恢复统计） |
| `patch_left_only.py` | 临时"只用左臂"补丁（已撤销，留档） |
| `plan30.json` | 最后一次推理的 30 步计划（含夹爪 trigger） |
| `dt.py` / `jogtest.sh` / `usb_compare.sh` / `copy_usb_rest.sh` | 环境自带的工具，顺手备份 |

---

### `logs/`

| 文件 | 说明 |
|---|---|
| `server_v3_fixed.log` | **修复后**的 server 启动日志（有 `Loaded norm stats` + `listening`） |
| `server_v3.log` | v3 server 日志 |
| `server.log` | 更早的 server 日志（v4 时代） |
| `convert_v3.log` / `convert_v4.log` | PyTorch 转换日志（811 tensors） |
| `conv-vaapi.log` | 数据集 VA-API 转换日志 |

---

## 快速恢复清单（换机器 / 重装时）

```bash
# 1. 服务端补丁
cp 备份/server_openpi/teleavatar_v2_policy.py \
   /root/USB/deploy/server/openpi/src/openpi/policies/

# 2. 归一化统计（绝对版）
cp 备份/ckpt_assets/v3_move_raised/norm_stats.json \
   /root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised/

# 3. 客户端脚本
cp 备份/client_openpi/*.py /root/USB/deploy/client/openpi/
cp 备份/root/*.sh /root/

# 4. 检查
grep -c "ABS-ACTIONS" /root/USB/deploy/server/openpi/src/openpi/policies/teleavatar_v2_policy.py   # 应为 3
python3 -c "import json;d=json.load(open('/root/ckpt_out_v3/pi05_teleavatar_v2_pytorch/assets/move_raised/norm_stats.json'))['norm_stats']['actions'];print(d['q01'][:3])"
# 应为 [0.029, 1.036, -1.095]

# 5. 重启 server → 重启 client 容器 → 摆位 → 跑
```
