# FileTimeChanger
 Permite modificar los tiempos de Creación, Acceso y/o Modificación a cualquier archivo en Windows
# Versión 1.0.2
# Probado en Python 3.8.8 - Windows
# Requisitos: PyQT5 y pywin32
Comando: python -m pip install -r requirements.txt

# Ejemplos:
Al Cargar un archivo podremos ver lo siguiente:
Nota: Por defecto se añadirá un archivo de flujo de datos alternativo con nombre 'FTC' (archivo.ext:FTC), el cual contiene registro de los datos actuales/originales del archivo, sobre los datos de creación, modificación y último acceso del archivo. Se puede eliminar dicha información si se presiona el botón 'Eliminar Tiempos Originales'. Si se desea acceder al archivo alterno se puede desde una consola de comandos con el comando "notepad archivo.extension:FTC".

![Capture01](images/FileTimeChanger-v1.0.2-01.png "Captura 01")

Al modificar por ejemplo las fechas, se habilitará la opción de "Cambiar Datos" lo cual modificará los tiempos de Creación, Modificación y Último Acceso al archivo.

![Capture02](images/FileTimeChanger-v1.0.2-02.png "Captura 02")

Al presionar en 'Cambiar Datos' podremos ver ya reflejados los cambios en el archivo con las nuevas fechas. Se habilitará la opción de restaurar los datos originales, los cuales son obtenibles desde el archivo de flujo alternativo ':FTC'. Si el archivo de flujo alterno no existe, no será posible volver a cargar los datos originales del archivo.

![Capture03](images/FileTimeChanger-v1.0.2-03.png "Captura 03")

Si presionamos el botón de 'Restaurar Datos Originales' se restaurarán los datos directamente.

![Capture04](images/FileTimeChanger-v1.0.2-04.png "Captura 04")

Podemos ver los cambios reflejados y la opción de 'Restaurar Datos Originales' y los campos 'FT Original' (FileTime Original) se deshabilitarán, indicando que el archivo tiene ya sus datos originales.

![Capture05](images/FileTimeChanger-v1.0.2-05.png "Captura 05")

Si presionamos el botón de 'Actualizar' esta opción nos permitirá cargar en los campos la fecha y hora actuales en todos los campos.

![Capture06](images/FileTimeChanger-v1.0.2-06.png "Captura 06")

Al presionar 'Cambiar Datos' guardará los nuevos datos para el archivo.

![Capture07](images/FileTimeChanger-v1.0.2-07.png "Captura 07")

Así mismo, podremos volver a ver los cambios reflejados.

![Capture08](images/FileTimeChanger-v1.0.2-08.png "Captura 08")

