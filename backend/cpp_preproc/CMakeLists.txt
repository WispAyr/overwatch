cmake_minimum_required(VERSION 3.15)
project(overwatch_frame_processor)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

# Find packages
find_package(OpenCV REQUIRED)
find_package(pybind11 REQUIRED)

# Find turbojpeg
find_library(TURBOJPEG_LIBRARY NAMES turbojpeg)
find_path(TURBOJPEG_INCLUDE_DIR turbojpeg.h)

if(NOT TURBOJPEG_LIBRARY OR NOT TURBOJPEG_INCLUDE_DIR)
    message(FATAL_ERROR "turbojpeg not found. Install with: brew install jpeg-turbo (macOS) or apt install libturbojpeg0-dev (Linux)")
endif()

message(STATUS "Found turbojpeg: ${TURBOJPEG_LIBRARY}")
message(STATUS "OpenCV version: ${OpenCV_VERSION}")

# OpenMP support (optional but recommended)
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found - enabling parallel processing")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
else()
    message(WARNING "OpenMP not found - parallel processing disabled")
endif()

# Include directories
include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${TURBOJPEG_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Source files
set(SOURCES
    frame_processor.cpp
    python_bindings.cpp
)

# Create Python module
pybind11_add_module(frame_processor ${SOURCES})

# Link libraries
target_link_libraries(frame_processor PRIVATE
    ${OpenCV_LIBS}
    ${TURBOJPEG_LIBRARY}
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(frame_processor PRIVATE OpenMP::OpenMP_CXX)
endif()

# Install target
install(TARGETS frame_processor
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}
)

# Print build info
message(STATUS "")
message(STATUS "================================")
message(STATUS "Overwatch Frame Processor Build")
message(STATUS "================================")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ flags: ${CMAKE_CXX_FLAGS}")
message(STATUS "OpenCV: ${OpenCV_VERSION}")
message(STATUS "turbojpeg: ${TURBOJPEG_LIBRARY}")
message(STATUS "OpenMP: ${OpenMP_CXX_FOUND}")
message(STATUS "================================")
message(STATUS "")

