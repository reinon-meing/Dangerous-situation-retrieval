#!/bin/bash
# reset_arm.sh —— 复位到零位
#
# 作用：发心跳 + 调用官方 zero.py，让双臂运动到预设零位并等待收敛。
#      每次跑模型之前必须做，保证起点姿态和训练时一致。
#
# 执行：
#   docker exec -i openpi-xpu-client \
#     /usr/local/bin/openpi-client-entrypoint.sh bash -s < /root/reset_arm.sh
#
# 判断：看到 "Both arms converged!" = 复位成功、电机正常

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1

echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data

echo "=== 开始复位（最多等 60 秒）"
timeout 60 python examples/teleavatar_v2/zero.py

kill $HB 2>/dev/null
