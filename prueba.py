import pyrealsense2 as rs
import numpy as np
import cv2
import time

# This variables modify how the code works
recordTimeModeActive = False
recordFrameModeActive = True

maxSecondsVideo = 5
maxFramesVideo = 150







if recordTimeModeActive & recordFrameModeActive == False:

	# Configure depth and color streams
	pipeline = rs.pipeline()
	config = rs.config()

	# Get device product line for setting a supporting resolution
	pipeline_wrapper = rs.pipeline_wrapper(pipeline)
	pipeline_profile = config.resolve(pipeline_wrapper)
	device = pipeline_profile.get_device()                                          # Get all the information about the cam
	device_product_line = str(device.get_info(rs.camera_info.product_line))         # Convert information of camera in string

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
		exit(0)

	# Configure everything about streams (It shows camera information spliting colors and depth)
	config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

	if device_product_line == 'L500':
		config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
	else:
		config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

	# Preparing record settings
	config.enable_record_to_file('prueba2.bag')

	if recordFrameModeActive:
		print ("Mode Selected -> Frame Mode")
		countFrames = 0
	elif recordTimeModeActive:
		print ("Mode Selected -> Time Mode")
		startTime = time.time()
	else:
		print ("Mode Selected -> Only View")
	
	
	
	
	# Start streaming and getting frames
	pipeline.start(config)

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
		        
		    if maxFramesVideo > countFrames:
		        # Increment the count of frames that are taken
		        countFrames += 1
		        continue
		        
		    # If we got max value of frames we have to stop recording
		    else:
		        print ("Record Finish")
		        break    
		    
		    """
		    # Make the work for each mode (Frame, time, only view)
		   	
		    if recordFrameModeActive:
				# Check if the video is recorded (It get all frames required. The limit is defined at the start)
		    	if maxFramesVideo > countFrames:
		        	# Increment the count of frames that are taken
		        	countFrames += 1
		        	continue
		        
		    	# If we got max value of frames we have to stop recording
		    	else:
		        	print ("Record Finish")
		        	break
		        	
		        	
			if recordTimeModeActive:
				if maxSecondsVideo < (startTime - time.time()):
					print ("Record Finish")
		        	break

		        	
		    	# If we didn´t get x seconds we continue
		    	else:
		        	continue
		  	
		    cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
			cv2.imshow('RealSense', images)
			cv2.waitKey(1)
			"""
	finally:

		# Stop streaming
		pipeline.stop()
		print ("Pipeline stopped")
		
else:
	print ("Code can´t execute because both modes are active. Please desactivate one of them.")
