cmake_minimum_required(VERSION 3.10)
PROJECT(  ImageBasedGestureRecognitionClient )

SET(RC_COMPONENT_PATH ${CMAKE_CURRENT_SOURCE_DIR} CACHE STRING "component base path")
SET(RC_COMPONENT_DEVEL_PATH ${CMAKE_CURRENT_SOURCE_DIR} CACHE STRING "component binary path")
ADD_SUBDIRECTORY( src )

