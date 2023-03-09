#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2023 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from rich.console import Console
from genericworker import *
import interfaces as ifaces

import pyrealsense2 as rs
import numpy as np
import cv2
import time
import sys

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)

# Configure how the component works
recordTimeModeActive = True
recordFrameModeActive = False

maxSecondsVideo = 5
maxFramesVideo = 150

startTime = 0.0
countFrames = 0
endExecute = 0

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()                                          # Get all the information about the cam
device_product_line = str(device.get_info(rs.camera_info.product_line))         # Convert information of camera in string


# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel


class SpecificWorker(GenericWorker):
    
    
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 2000
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)


        # Check if camera works correctly (It´s RGBD == Correct)
        found_rgb = False	
        for s in device.sensors:
            print ("Device Name:", s.get_info(rs.camera_info.name))
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break

        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")

            # Program finish because there aren´t cameras RGBD available
            #exit(0)

        # Configure everything about streams (It shows camera information spliting colors and depth)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Preparing record settings
        if recordFrameModeActive or recordTimeModeActive:
            print ("It´s gonna be recorded. Check the folder \"/home/robolab/carpetaVideos\"")
            #config.enable_record_to_file('/home/robolab/carpetaVideos/videoCorto.bag')

        # Start streaming and getting frames
        pipeline.start(config)
        
        # Show the information about how the code will work
        if recordFrameModeActive:
            print ("Mode Selected -> Frame Mode")
            countFrames = 0
        elif recordTimeModeActive:
            print ("Mode Selected -> Time Mode")
            startTime = time.time()
        else:
            print ("Mode Selected -> Only View")
           


    def __del__(self):
        """Destructor"""

    def setParams(self, params):
        # try:
        #	self.innermodel = InnerModel(params["InnerModelPath"])
        # except:
        #	traceback.print_exc()
        #	print("Error reading config params")
        return True


    @QtCore.Slot()
    def compute(self):
        #print('SpecificWorker.compute...')
        

        # Execute a loop who get the image and show it
        try:
            while True:
                # Wait for a coherent pair of frames: depth and color (Should be one color frame and depth frame)
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                if not depth_frame or not color_frame:
                    continue

                # Convert images to numpy arrays
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
                    depth_image, alpha=0.03), cv2.COLORMAP_JET)

                depth_colormap_dim = depth_colormap.shape
                color_colormap_dim = color_image.shape

                # If depth and color resolutions are different, resize color image to match depth image for display
                if depth_colormap_dim != color_colormap_dim:
                    resized_color_image = cv2.resize(color_image, dsize=(
                        depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
                    images = np.hstack((resized_color_image, depth_colormap))
                else:
                    images = np.hstack((color_image, depth_colormap))
                    
                
                if recordFrameModeActive:
                    if maxFramesVideo > countFrames:
                        # Increment the count of frames that are taken
                        countFrames += 1
                        #If we are in this mode we are not interested about show what the cam is seing
                        continue
                    else:                # If we got max value of frames we have to stop recording
                        print ("Finished Recording. Recorded", maxFramesVideo, "frames")
                        break
                    
                if recordTimeModeActive:
                    currentTime = time.time()
                    if (currentTime - startTime) > maxSecondsVideo:
                        print ("Finished Recording. Recorded", maxSecondsVideo, "seconds")
                        break
                    else:
                        #If we are in this mode we are not interested about show what the cam is seing
                        continue

                # If we have both modes desactivated (False) then it will show what the camera is seing
                cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
                cv2.imshow('RealSense', images)
                cv2.waitKey(1)
                
                """
                if maxFramesVideo > countFrames:
                    # Increment the count of frames that are taken
                    countFrames += 1
                    continue

                # If we got max value of frames we have to stop recording
                else:
                    print ("Record Finish")
                    break
                
                
                cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
                cv2.imshow('RealSense', images)
                cv2.waitKey(1)

                """
                #print ("Image Showed")
        finally:
            # Stop streaming
            """
            if endExecute == 0:
                pipeline.stop()
                self.timer.stop()
                print ("Pipeline stopped")
                print ("Numero de seconds grabados ->", (currentTime - startTime))    
                endExecute = 1        
            #exit(0)
            #sys.exit(0)
	    """
            
             
        return True

    def startup_check(self):
        print(f"Testing RoboCompCameraRGBDSimple.Point3D from ifaces.RoboCompCameraRGBDSimple")
        test = ifaces.RoboCompCameraRGBDSimple.Point3D()
        print(f"Testing RoboCompCameraRGBDSimple.TPoints from ifaces.RoboCompCameraRGBDSimple")
        test = ifaces.RoboCompCameraRGBDSimple.TPoints()
        print(f"Testing RoboCompCameraRGBDSimple.TImage from ifaces.RoboCompCameraRGBDSimple")
        test = ifaces.RoboCompCameraRGBDSimple.TImage()
        print(f"Testing RoboCompCameraRGBDSimple.TDepth from ifaces.RoboCompCameraRGBDSimple")
        test = ifaces.RoboCompCameraRGBDSimple.TDepth()
        print(f"Testing RoboCompCameraRGBDSimple.TRGBD from ifaces.RoboCompCameraRGBDSimple")
        test = ifaces.RoboCompCameraRGBDSimple.TRGBD()
        QTimer.singleShot(200, QApplication.instance().quit)



    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # IMPLEMENTATION of getAll method from CameraRGBDSimple interface
    #
    def CameraRGBDSimple_getAll(self, camera):
        ret = ifaces.RoboCompCameraRGBDSimple.TRGBD()
        #
        # write your CODE here
        #
        return ret
    #
    # IMPLEMENTATION of getDepth method from CameraRGBDSimple interface
    #
    def CameraRGBDSimple_getDepth(self, camera):
        ret = ifaces.RoboCompCameraRGBDSimple.TDepth()
        #
        # write your CODE here
        #
        return ret
    #
    # IMPLEMENTATION of getImage method from CameraRGBDSimple interface
    #
    def CameraRGBDSimple_getImage(self, camera):
        ret = ifaces.RoboCompCameraRGBDSimple.TImage()
        #
        # write your CODE here
        #
        return ret
    #
    # IMPLEMENTATION of getPoints method from CameraRGBDSimple interface
    #
    def CameraRGBDSimple_getPoints(self, camera):
        ret = ifaces.RoboCompCameraRGBDSimple.TPoints()
        #
        # write your CODE here
        #
        return ret
    # ===================================================================
    # ===================================================================


    ######################
    # From the RoboCompCameraRGBDSimplePub you can publish calling this methods:
    # self.camerargbdsimplepub_proxy.pushRGBD(...)

    ######################
    # From the RoboCompCameraRGBDSimple you can use this types:
    # RoboCompCameraRGBDSimple.Point3D
    # RoboCompCameraRGBDSimple.TPoints
    # RoboCompCameraRGBDSimple.TImage
    # RoboCompCameraRGBDSimple.TDepth
    # RoboCompCameraRGBDSimple.TRGBD


