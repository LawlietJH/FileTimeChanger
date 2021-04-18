
# FileTimeChanger v1.0.0

from ctypes import windll, wintypes, byref
import datetime
import time
import os

# Convierte de Unix timestamp a Windows FileTime
# Documentación: https://support.microsoft.com/en-us/help/167296
toTimestamp = lambda epoch: int((epoch * 10000000) + 116444736000000000)
toFileTime = lambda epoch: byref(wintypes.FILETIME(toTimestamp(epoch) & 0xFFFFFFFF, toTimestamp(epoch) >> 32))
timeToDate = lambda time: datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
dateToTime = lambda date: time.mktime(date.timetuple())

def getFileTimes(fp: str):        
	return (
		os.path.getctime(fp), 
		os.path.getmtime(fp), 
		os.path.getatime(fp)
	)

def toDatetime(
		year:  int,
		month: int,
		day:   int,
		hour   = 0,
		minute = 0,
		second = 0
	):
	
	return datetime.datetime(
		year = year, month  = month,  day    = day,
		hour = hour, minute = minute, second = second
	)

def changeFileTimes(filepath: str, values):
	# Llamada al Win32 API para modificar los tiempos del archivo
	handle = windll.kernel32.CreateFileW(filepath, 256, 0, None, 3, 128, None)
	windll.kernel32.SetFileTime(handle, *values)
	windll.kernel32.CloseHandle(handle)

# Arbitrary example of a file and a date
filepath = 'xd.bmp'

# Tiempos actuales (originales de: created, modified, accessed).
# Pendiente: Concatenar esta info al final del archivo, con un
# booleano para saber si ya fue modificado o aún no.
oc, om, oa = getFileTimes(filepath)	# Obtiene los Tiempos actuales

values = [None, None, None]

# El Año, Mes y Día son obligatorios.
# Las Horas, minutos y/o Segundos son opcionales.
# Formatos %Y-%m-%d %H:%M:%S o None
# ~ created = None
created = {
	'year':   2031,
	'month':  2,
	'day':    14,
	'hour':   17,
	# ~ 'minute': 7,
	# ~ 'second': 5
}
# ~ modified = None
modified = {
	'year':   2032,
	'month':  2,
	'day':    14,
	# ~ 'hour':   17,
	'minute': 7,
	# ~ 'second': 5
}
# ~ accessed = None		# Esto permite que se ignore la modificación
accessed = {
	'year':   2033,
	'month':  2,
	'day':    14,
	# ~ 'hour':   17,
	# ~ 'minute': 7,
	'second': 5
}

if created:
	cdate = toDatetime(**created)
	ctime = toFileTime(dateToTime(cdate))
	values[0] = ctime

if accessed:
	adate = toDatetime(**accessed)
	atime = toFileTime(dateToTime(adate))
	values[1] = atime

if modified:
	mdate = toDatetime(**modified)
	mtime = toFileTime(dateToTime(mdate))
	values[2] = mtime

changeFileTimes(filepath, values)	# Modifica los Tiempos del Archivo
c, m, a = getFileTimes(filepath)	# Obtiene los Tiempos actuales

print('\n PoC: Modificar los tiempos en un archivo.\n')
print(' Original Created  Time:', timeToDate(oc))
print(' Original Modified Time:', timeToDate(om))
print(' Original Accessed Time:', timeToDate(oa))
print()
print(' New Created  Time:', timeToDate(c))
print(' New Modified Time:', timeToDate(m))
print(' New Accessed Time:', timeToDate(a))


