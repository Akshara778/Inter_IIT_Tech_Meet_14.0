#!/bin/bash
# launch for slam and save (press ENTER)

cleanup() {
    echo "Cleaning up..."
    sleep 3.0
    pkill -9 -f "ros2|gazebo|gz|nav2|amcl|bt_navigator|nav_to_pose|rviz2|assisted_teleop|cmd_vel_relay|robot_state_publisher|joint_state_publisher|move_to_free|mqtt|autodock|cliff_detection|moveit|move_group|basic_navigator"
}
trap 'cleanup' SIGINT SIGTERM

echo "Launching SLAM + Gazebo simulation..."

ros2 launch eternal_gazebo eternal_slam.gazebo.launch.py \
    enable_odom_tf:=true \
    headless:=False \
    load_controllers:=true \
    world_file:=arena.world \
    use_rviz:=true \
    use_robot_state_pub:=true \
    use_sim_time:=true \
    x:=0.0 \
    y:=0.0 \
    z:=0.40 \
    roll:=0.0 \
    pitch:=0.0 \
    yaw:=0.0 &

echo "Waiting 25 seconds for simulation to initialize..."
sleep 25

echo "Adjusting Gazebo camera position..."
gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 2000 \
    --req "pose: {position: {x: 0.0, y: -2.0, z: 2.0} orientation: {x: -0.2706, y: 0.2706, z: 0.6533, w: 0.6533}}"

echo ""
echo "=========================================="
echo " Teleoperate and map the environment now "
echo " Press ENTER when ready to save the map"
echo "=========================================="
read -p ""

#save map
MAP_DIR=~/maps
#also waypoint file should be saved here
if [ ! -d "$MAP_DIR" ]; then
    echo "Creating map directory: $MAP_DIR"
    mkdir -p "$MAP_DIR"
fi
MAP_NAME="eternal_warehouse_arena"
MAP_PATH="${MAP_DIR}/${MAP_NAME}"
echo ""
echo "=========================================="
echo "Saving map to: $MAP_PATH"
echo "=========================================="

ros2 run nav2_map_server map_saver_cli -f "$MAP_PATH"
echo ""
echo "=========================================="
echo " Map saved successfully! "
echo " Files:"
echo "   ${MAP_PATH}.yaml"
echo "   ${MAP_PATH}.pgm"
echo "=========================================="
echo ""

wait
