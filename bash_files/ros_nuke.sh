#!/bin/bash
set -e

echo "=============================================="
echo " ROS2 FULL PURGE FOR PACKAGE RENAME RECOVERY "
echo "=============================================="

if [ ! -d "src" ]; then
  echo "ERROR: Run only from ROS workspace root"
  exit 1
fi

echo "[1/12] Killing all ROS / Python / colcon processes..."
pkill -f ros2 2>/dev/null || true
pkill -f colcon 2>/dev/null || true
pkill -f python 2>/dev/null || true

echo "[2/12] Removing all workspace artifacts..."
rm -rf build install log

echo "[3/12] Removing per-package CMake artifacts..."
find src -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find src -type d -name "install" -exec rm -rf {} + 2>/dev/null || true
find src -type d -name "log" -exec rm -rf {} + 2>/dev/null || true

echo "[4/12] Removing ALL CMake cache & generated files..."
find . -name "CMakeCache.txt" -delete
find . -name "CMakeFiles" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.cmake" -delete

echo "[5/12] Removing ament + colcon global indexes..."
rm -rf ~/.ament
rm -rf ~/.colcon
rm -rf ~/.cache/colcon
rm -rf ~/.ros

echo "[6/12] Removing ALL Python artifacts..."
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
rm -rf .eggs *.egg-info **/*.egg-info 2>/dev/null || true

echo "[7/12] Removing all virtualenvs..."
rm -rf .ros_venv .venv venv env src/team89bot

echo "[8/12] Unsetting ALL ROS + Python env vars..."
unset ROS_PACKAGE_PATH
unset CMAKE_PREFIX_PATH
unset AMENT_PREFIX_PATH
unset PYTHONPATH
unset COLCON_PREFIX_PATH

echo "[9/12] Removing stray symlinks in install/ if any remain..."
find install -type l -delete 2>/dev/null || true

echo "[10/12] Removing g
