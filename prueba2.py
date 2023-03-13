import cv2
import numpy as np
import time
from matplotlib import pyplot as plt


"""
iteracion = 0
time_sleep = 1              # En segundos

while True:
    print ("Iteracion ->", iteracion)
    key = cv2.waitKey (1) & 0xFF
    print ("val key ->", key)
    if key == ord('q'):
        print ("ALERTA -> Se pulso la tecla q")
    
    iteracion += 1
    time.sleep (time_sleep)
"""

vid = cv2.VideoCapture(2)

while(True):

  ret, frame = vid.read()

  cv2.imshow('frame', frame)

  # when 'x' key is pressed the video capture stops
  if cv2.waitKey(1) & 0xFF == 13:
    break

vid.release()

cv2.destroyAllWindows()
"""

cap = cv2.VideoCapture (2)
ret, frame = cap.read()

print (ret)
print (frame)
plt.imshow
"""