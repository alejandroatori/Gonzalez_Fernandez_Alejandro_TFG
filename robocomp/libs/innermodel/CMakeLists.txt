cmake_minimum_required( VERSION 3.10 )
project(innermodel
		VERSION 2021.3.1
		DESCRIPTION "RoboComp InnerModel library"
		LANGUAGES CXX )


find_package(Qt5 COMPONENTS Gui Core Xml REQUIRED)

add_library(innermodel SHARED)
add_library(Robocomp::innermodel ALIAS innermodel)

target_sources(innermodel
		PRIVATE
		innermodel.cpp
		innermodelreader.cpp
		innermodelviewer.cpp
		innermodeldraw.cpp
		innermodelexception.cpp
		innermodelnode.cpp
		innermodeltransform.cpp
		innermodeljoint.cpp
		innermodelomnirobot.cpp
		innermodeldifferentialrobot
		innermodelprismaticjoint.cpp
		innermodelplane.cpp
		innermodelcamera.cpp
		innermodelrgbd.cpp
		innermodellaser.cpp
		innermodelimu.cpp
		innermodelpointcloud.cpp
		innermodelmesh.cpp
		innermodeltouchsensor.cpp
		innermodeldisplay.cpp)
target_link_libraries(innermodel
		PRIVATE
		Qt5::Gui Qt5::Xml
		Robocomp::osgviewer
		PUBLIC
		Qt5::Core
		qmat)


## FCL
#SET(FCL_SUPPORT ON CACHE BOOL "Build FCL shared library" FORCE)
#MESSAGE(STATUS "FCL_SUPPORT Build with FCL support ${FCL_SUPPORT}")

if (FCL_SUPPORT)
	target_link_libraries(innermodel
			PRIVATE fcl )
	target_compile_definitions(innermodel
			PRIVATE FCL_SUPPORT=1)
	MESSAGE( STATUS "COMPILING WITH FCL SUPPORT=1" )
else (FCL_SUPPORT)
	MESSAGE( STATUS "COMPILING WITHOUT FCL SUPPORT=0" )
endif (FCL_SUPPORT)

target_compile_options(innermodel PUBLIC "-std=c++17")

# Define headers for this library. PUBLIC headers are used for
# compiling the library, and will be added to consumers' build
# paths.
target_include_directories(innermodel
		PUBLIC
		$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/>
		$<INSTALL_INTERFACE:include/>
		)

# 'make install' to the correct locations (provided by GNUInstallDirs).
install(TARGETS innermodel EXPORT innermodelConfig
		ARCHIVE  DESTINATION ${CMAKE_INSTALL_LIBDIR}
		LIBRARY  DESTINATION ${CMAKE_INSTALL_LIBDIR})

install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

# This makes the project importable from the install directory
# Put config file in per-project dir (name MUST match), can also
# just go into 'cmake'.
install(EXPORT innermodelConfig DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/innermodel NAMESPACE Robocomp::)


# This makes the project importable from the build directory
export(TARGETS innermodel FILE innermodelConfig.cmake)