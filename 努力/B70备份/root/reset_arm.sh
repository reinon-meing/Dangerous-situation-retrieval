#!/bin/bash
ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1
echo "=== FSM"
timeout 2 ros2 topic echo --once /fsm_state --field data
echo "=== 开始复位（最多等 60 秒）"
timeout 60 python examples/teleavatar_v2/zero.py
kill $HB 2>/dev/null
