#!/bin/bash
set -e

ROS_DISTRO="jazzy"
VENV_DIR=".ros_venv"
MAIN_PKG="navigation"

echo "========================================"
echo "  ROS2 FULL CLEAN INSTALL & RUN SCRIPT  "
echo "========================================"

# -----------------------------
# SAFETY CHECK
# -----------------------------
if [ ! -d "src" ]; then
  echo "ERROR: Run this script from the WORKSPACE ROOT (where src/ exists)"
  exit 1
fi

# -----------------------------
# FULL CLEANUP
# -----------------------------
echo "===== FULL CLEANUP ====="
rm -rf build install log ~/.colcon ~/.cache/colcon
rm -rf src/*/build src/*/install src/*/log
rm -rf src/team89bot
rm -rf ${VENV_DIR}

unset ROS_PACKAGE_PATH
unset CMAKE_PREFIX_PATH
unset AMENT_PREFIX_PATH
deactivate 2>/dev/null || true

# -----------------------------
# SYSTEM UPDATE
# -----------------------------
echo "===== SYSTEM UPDATE ====="
sudo apt update

# -----------------------------
# SYSTEM DEPENDENCIES
# -----------------------------
echo "===== INSTALLING SYSTEM DEPENDENCIES ====="
sudo apt install -y \
  curl \
  gnupg \
  lsb-release \
  software-properties-common \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-full \
  python3-catkin-pkg \
  build-essential \
  locales

# -----------------------------
# LOCALE
# -----------------------------
echo "===== LOCALE SETUP ====="
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# -----------------------------
# ROS REPOSITORY
# -----------------------------
echo "===== ROS REPOSITORY SETUP ====="
sudo add-apt-repository universe -y
sudo apt update

# -----------------------------
# ROS INSTALL (IF MISSING)
# -----------------------------
echo "===== CHECKING ROS INSTALL ====="
if ! dpkg -s ros-${ROS_DISTRO}-ros-base >/dev/null 2>&1; then
  sudo apt install -y \
    ros-${ROS_DISTRO}-ros-base \
    ros-dev-tools \
    python3-colcon-common-extensions
fi

# -----------------------------
# PYTHON VENV + TOOLS
# -----------------------------
echo "===== SETTING UP PYTHON VENV ====="
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade cython catkin-pkg

# -----------------------------
# ROSDEP
# -----------------------------
echo "===== ROSDEP SETUP ====="
sudo rosdep init 2>/dev/null || true
rosdep update

# -----------------------------
# VERIFY NAVIGATION PACKAGE
# -----------------------------
echo "===== VERIFYING NAVIGATION PACKAGE ====="
if [ ! -f "src/${MAIN_PKG}/package.xml" ]; then
  echo "ERROR: Package '${MAIN_PKG}' not found in src/"
  find src -maxdepth 2 -name package.xml
  exit 1
fi

# Ensure colcon never scans venv
touch src/.colcon_ignore

# -----------------------------
# INSTALL ROS DEPENDENCIES
# -----------------------------
echo "===== INSTALLING ROS DEPENDENCIES ====="
source /opt/ros/${ROS_DISTRO}/setup.bash
rosdep install -y --from-paths src --ignore-src --rosdistro ${ROS_DISTRO}

# -----------------------------
# BUILD (SYSTEM PYTHON FOR AMENT)
# -----------------------------
echo "===== BUILDING WORKSPACE ====="
deactivate
source /opt/ros/${ROS_DISTRO}/setup.bash

colcon build --symlink-install --event-handlers console_direct+

# -----------------------------
# SOURCE OVERLAY
# -----------------------------
echo "===== SOURCING WORKSPACE ====="
source install/setup.bash

# -----------------------------
# VERIFY PACKAGE REGISTRATION
# -----------------------------
echo "===== VERIFYING PACKAGE REGISTRATION ====="
ros2 pkg list | grep -q "^${MAIN_PKG}$" || {
  echo "ERROR: Package '${MAIN_PKG}' not registered with ROS!"
  ros2 pkg list
  exit 1
}

# -----------------------------
# SHOW LAUNCH FILES
# -----------------------------
echo "===== AVAILABLE LAUNCH FILES ====="
find src/${MAIN_PKG} -name "*.launch.py"

# -----------------------------
# LAUNCH SYSTEM
# -----------------------------
echo "===== LAUNCHING FULL SYSTEM ====="
ros2 launch ${MAIN_PKG} navigation.launch.py &

sleep 5

echo "===== LAUNCHING SIMULATION ====="
ros2 launch ${MAIN_PKG} slam.launch.py
