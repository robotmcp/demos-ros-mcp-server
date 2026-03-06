cmake_minimum_required(VERSION 3.8)
project(go2_description)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(urdfdom REQUIRED)

# Install directories
install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}/
)

install(DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}/
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

# Testing
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
