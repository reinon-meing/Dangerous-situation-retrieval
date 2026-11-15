#!/bin/bash
ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1
echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data
echo "=== 零位复位"
timeout 60 python examples/teleavatar_v2/zero.py
sleep 1
echo "=== 启动策略"
python examples/teleavatar_v2/main.py --remote-host 127.0.0.1 --remote-port 8000 --video-decode va --prompt "pick sandbag"
kill $HB 2>/dev/null
