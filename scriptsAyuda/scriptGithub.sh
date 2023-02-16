# Subir la carpeta a github

# Se accede a la carpeta general
cd ..

pwd

# Archivos que se van a tener en cuenta
git add . # Sube todos los archivos (Si se quieren coger algunos solo poner en lugar de punto cuales)

# El mensaje de parametro sera el mensaje del commit
git commit -m "$1"

# Se sube a la rama de internet
git push origin main
