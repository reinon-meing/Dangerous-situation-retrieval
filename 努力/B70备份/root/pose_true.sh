#!/bin/bash
# pose_true.sh —— 真实复位点（2026-11-15 15:30 现场确认）
LEFT="0.3370, 1.2945, -0.8154, 0.9040, 0.5150, 0.3075, 0.6504"
RIGHT="-0.2093, -1.1257, 0.7904, -1.1710, -0.5070, -0.4743, -0.6286"

ros2 topic pub -r 20 /api/fsm/enable std_msgs/msg/Float32 "{data: 1.0}" >/dev/null 2>&1 &
HB=$!
sleep 1
echo "=== FSM"; timeout 2 ros2 topic echo --once /fsm_state --field data

ros2 topic pub -r 20 /api/left_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$LEFT]}" >/dev/null 2>&1 &
PUBL=$!
ros2 topic pub -r 20 /api/right_arm/joint_cmd sensor_msgs/msg/JointState "{position: [$RIGHT]}" >/dev/null 2>&1 &
PUBR=$!
sleep 7

echo "=== 实际到位"
timeout 2 ros2 topic echo --once /left_arm/joint_states --field position 2>/dev/null | grep -o "array.*"
timeout 2 ros2 topic echo --once /right_arm/joint_states --field position 2>/dev/null | grep -o "array.*"

kill $PUBL $PUBR $HB 2>/dev/null
