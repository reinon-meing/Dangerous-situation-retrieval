#!/bin/bash
# run_policy.sh —— 心跳 + main.py 跑模型
# --prompt 必须和训练 --task 一字不差；16 维模型不加 --enable-chassis；不加 --rtc
# 执行：docker exec -i openpi-xpu-client /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/run_policy.sh

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
