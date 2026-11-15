#!/bin/bash
# pose_v4.sh —— move_all(355条) 首帧均值，v4 专用
# 数据来源：/data/lerobot/move_all 每条 episode 首帧 observation.state[:14]

LEFT="0.339, 1.281, -0.803, 0.903, 0.513, 0.306, 0.646"
RIGHT="0.996, -0.227, -1.122, 0.782, -1.179, -0.480, -0.465"

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1

echo "=== FSM（必须是 1）"
timeout 2 ros2 topic echo --once /fsm_state --field data

echo "=== 摆位：左臂 [$LEFT]"
ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState \
  "{position: [$LEFT]}" >/dev/null 2>&1 &
PUBL=$!

echo "=== 摆位：右臂 [$RIGHT]"
ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState \
  "{position: [$RIGHT]}" >/dev/null 2>&1 &
PUBR=$!

sleep 8

echo "=== 实际到位情况"
timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*"
timeout 2 ros2 topic echo --once /right_arm/joint_states --field position 2>/dev/null | grep -o "array.*"

kill $PUBL $PUBR $HB 2>/dev/null
