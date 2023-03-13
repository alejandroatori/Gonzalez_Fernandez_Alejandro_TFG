# Script para activar la camara más facil. Anteriormente activar el rcnode & (Se debe matar el proceso si ya existe para poder ejecutarlo en la misma terminal)

# Lo primero es alcanzar la carpeta donde se encuentra
cd /home/robolab/robocomp/robocomp_tools/rcnode

./rcnode.sh &

# Lo primero es ir a la carpeta donde se encuentra
cd /home/robolab/Gonzalez_Fernandez_Alejandro_TFG/robocomp/components/robocomp-robolab/components/hardware/camera/realsense_camera_py

# Activacion de la camara
src/realsense_camera.py etc/config
