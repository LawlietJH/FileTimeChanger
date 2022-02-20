# FileTimeChanger
 Permite modificar los tiempos de Creación, Acceso y/o Modificación a cualquier archivo en Windows permitiendo colocar cualquier fecha Pasada o Futura (dentro de las limitaciones del sistema) con la finalidad de poder manipular las fechas de archivos.
# Versión 1.1.0
# Probado en Python 3.8.8 - Windows
# Requisitos: PyQT5 y pywin32
Comando: python -m pip install -r requirements.txt

# Ejemplos:
Al Cargar un archivo podremos ver lo siguiente:
Nota: Por defecto se añadirá un archivo de flujo de datos alternativo con nombre 'FTC' (archivo.ext:FTC), el cual contiene registro de los datos actuales/originales del archivo, sobre los datos de creación, modificación y último acceso del archivo. Se puede eliminar dicha información si se presiona el botón 'Eliminar Tiempos Originales'. Si se desea acceder al archivo alterno se puede desde una consola de comandos con el comando "notepad archivo.extension:FTC".

![Capture01](images/FileTimeChanger-v1.1.0-01.png "Captura 01")

Al modificar por ejemplo las fechas, se habilitará la opción de "Cambiar Datos" lo cual modificará los tiempos de Creación, Modificación y Último Acceso al archivo.

![Capture02](images/FileTimeChanger-v1.1.0-02.png "Captura 02")

Al presionar en 'Cambiar Datos' podremos ver ya reflejados los cambios en el archivo con las nuevas fechas. Se habilitará la opción de restaurar los datos originales, los cuales son obtenibles desde el archivo de flujo alternativo ':FTC'. Si el archivo de flujo alterno no existe, no será posible volver a cargar los datos originales del archivo.

![Capture03](images/FileTimeChanger-v1.1.0-03.png "Captura 03")

Si presionamos el botón de 'Restaurar Datos Originales' se restaurarán los datos directamente.

![Capture04](images/FileTimeChanger-v1.1.0-04.png "Captura 04")

Podemos ver los cambios reflejados y la opción de 'Restaurar Datos Originales' y los campos 'FT Original' (FileTime Original) se deshabilitarán, indicando que el archivo tiene ya sus datos originales.

![Capture05](images/FileTimeChanger-v1.1.0-05.png "Captura 05")

Si presionamos el botón de 'Actualizar' esta opción nos permitirá cargar en los campos la fecha y hora actuales en todos los campos.

![Capture06](images/FileTimeChanger-v1.1.0-06.png "Captura 06")

Al presionar 'Cambiar Datos' guardará los nuevos datos para el archivo.

![Capture07](images/FileTimeChanger-v1.1.0-07.png "Captura 07")

Así mismo, podremos volver a ver los cambios reflejados.

![Capture08](images/FileTimeChanger-v1.1.0-08.png "Captura 08")

Podemos restaurar los valores con los tiempos actuales del archivo.

![Capture09](images/FileTimeChanger-v1.1.0-09.png "Captura 09")

Podremos volver a ver los cambios reflejados.

![Capture10](images/FileTimeChanger-v1.1.0-10.png "Captura 10")

También podemos eliminar el archivo que almacena los tiempos originales.

![Capture11](images/FileTimeChanger-v1.1.0-11.png "Captura 11")

Una vez realizado los campos de los tiempos originales serás deshabilitados.

![Capture12](images/FileTimeChanger-v1.1.0-12.png "Captura 12")

Es posible añadir nuevos tiempos originales utilizando la opción "Add FT". Esto colocará los tiempos actuales del archivo ahora como los nuevos tiempos originales.

![Capture13](images/FileTimeChanger-v1.1.0-13.png "Captura 13")

Ahora veremos los nuevos tiempos originales añadidos en los campos.

![Capture14](images/FileTimeChanger-v1.1.0-14.png "Captura 14")

Otra posible opción disponible es la de El historial de Archivos Recientes el cual al seleccionar un nombre de archivo será recargado inmediatamente.

![Capture15](images/FileTimeChanger-v1.1.0-15.png "Captura 15")

Es posble cambiar el tamaño de la ventana utilizando las opciones de la pestaña "Window" en su apartado "Resize". También es posible Centrar la Ventana en la pantalla utilizando el apartado "Center".

![Capture16](images/FileTimeChanger-v1.1.0-16.png "Captura 16")

En la pestaña "Check" es posible observar checkbox con opciones para los "Toolbars". Con "Floating" se podrá "habilitar/deshabilitar" el que el Toolbar pueda ser Flotante. Con "Show Names" es posible "Mostrar/Ocultar" los nombres de los botones en estas. Con "Visible" es posible "Mostrar/Ocultar" las Toolbars.

![Capture17](images/FileTimeChanger-v1.1.0-17.png "Captura 17")

En este ejemplo se muestra que los toolbars en estado "Flotante" pueden moverse a distintas partes de la ventana (arriba, abajo, izquierda o derecha) siempre y cuando el tamaño de la ventana lo permita, de no ser posible colocar alguno en uno de los lados, hacer la ventana un poco más grande deberá permitirlo.

![Capture18](images/FileTimeChanger-v1.1.0-18.png "Captura 18")

Así mismo, es posible sacar los Toolbars de la ventana y dejarlos fijo o flotante fuera de esta.

![Capture19](images/FileTimeChanger-v1.1.0-19.png "Captura 19")

En la pestaña "Edit" será posible apreciar 4 apartados: "Copy" que permite Copiar la ruta completa de un archivo cargado, "Paste" que permite pegar una ruta copiada (que sea valida) y cargar inmediatamente dicho archivo, "Cut" que corta la ruta cargada y limpia el campo, cerrando así el fichero anteriormente cargado y por último, "Clear" que limpia el campo, cerrando el archivo.

![Capture20](images/FileTimeChanger-v1.1.0-20.png "Captura 20")

Imagen de muestra.

![Capture21](images/FileTimeChanger-v1.1.0-21.png "Captura 21")
