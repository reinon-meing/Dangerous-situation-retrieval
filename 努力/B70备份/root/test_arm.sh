#!/bin/bash
# test_arm.sh —— 手臂动作自检（不跑模型）
# 判断：BEFORE 和 AFTER 明显不同 = 手臂能驱动

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1

echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data

b=$(timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*")
echo "BEFORE: $b"

ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState \
  "{position: [0.70, 1.60, -0.90, 1.10, 0.50, -0.40, 0.60]}" >/dev/null 2>&1 &
PUB=$!
sleep 5
kill $PUB 2>/dev/null

a=$(timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*")
echo "AFTER : $a"

kill $HB 2>/dev/null
