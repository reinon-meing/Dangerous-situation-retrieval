#!/bin/bash
# run_policy.sh —— 跑训练好的模型
#
# 作用：发心跳 + 启动 main.py，让模型驱动手臂。
#
# 完整链路：
#   main.py 收视频(UDP 8890, VA-API硬解) → 图像+关节角+prompt
#     → server(B70 GPU0, 端口8000) 推理 → 16维动作×30步
#     → main.py 翻译成 /api/left_arm/joint_cmd → 机器人执行
#
# 执行：
#   docker exec -i openpi-xpu-client \
#     /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/run_policy.sh
#
# 停止：Ctrl-C；不行就用
#   docker exec openpi-xpu-client pkill -INT -f examples/teleavatar_v2/main.py
# 严禁 docker stop / kill -9（会跳过零速度指令）
#
# 参数说明：
#   --prompt 必须和训练的 --task 一字不差（当前：pick sandbag）
#   --enable-chassis 不加（16 维模型不含底盘）
#   --rtc 不加（服务端未开 RTC）

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1

echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data

echo "=== 启动策略，Ctrl-C 停止"
python examples/teleavatar_v2/main.py \
  --remote-host 127.0.0.1 --remote-port 8000 \
  --video-decode va --prompt "pick sandbag"

kill $HB 2>/dev/null
