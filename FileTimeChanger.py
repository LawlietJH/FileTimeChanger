
#https://realpython.com/python-menus-toolbars/

# pip install PyQt5
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QTimer
from PyQt5.QtWidgets import (
	QApplication, QLabel, QMainWindow,
	QMenuBar, QMenu, QToolBar, QAction,
	QSpinBox, QVBoxLayout, QHBoxLayout,
	QPushButton, QWidget, QGridLayout,
	QDateEdit, QTimeEdit, QFileDialog,
	QLineEdit, QDateTimeEdit
)
from PyQt5.QtGui import QIcon, QKeySequence

from functools import partial
from ctypes import windll, wintypes, byref
import win32clipboard as WCB
import binascii
import datetime
import base64
import json
import time
import bz2
import sys
import os

__author__  = 'LawlietJH'				# Desarrollador
__title__   = 'FileTimeChanger'			# Nombre
__version__ = 'v1.0.1'					# Versión

#=======================================================================
# Traido de https://github.com/LawlietJH/Utils
class Clipboard:				# Manipula el clipboard (Copiar/Pegar)
	# print(Clipboard.text)		# Pegar: Devuelve el contenido que se haya copiado.
	@property
	def text(self):
		WCB.OpenClipboard()
		try:
			text = WCB.GetClipboardData()
			WCB.CloseClipboard()
			return text
		except TypeError:
			return ''
	# Clipboard.text = 'Texto'	# Copiar: Remplaza el contenido para poder Pegarlo.
	@text.setter
	def text(self, text):
		WCB.OpenClipboard()
		WCB.EmptyClipboard()
		WCB.SetClipboardText(text, WCB.CF_TEXT)
		WCB.CloseClipboard()
	# del Clipboard.text		# Vaciar: Vacia el Clipboard.
	@text.deleter
	def text(self):
		WCB.OpenClipboard()
		WCB.EmptyClipboard()
		WCB.SetClipboardText(b'', WCB.CF_TEXT)
		WCB.CloseClipboard()

#=======================================================================


class Window(QMainWindow):
	'''Main Window.'''
	def __init__(self, parent=None):
		'''Initializer.'''
		super().__init__(parent)
		self.Clipboard = Clipboard()
		self._createWindow()
		self._createGrid()
		self._createActions()
		self._createMenuBar()
		self._createToolBars()
		self._connectActions()
		self._createStatusBar()
	
	def _createWindow(self):
		self.setWindowTitle(__title__+' '+__version__ + ' - By: ' + __author__)
		self.setWindowIcon(QIcon('icons/icon.png'))
		self.setFixedSize(720, 360)
		
		self.listRecentFiles = ['Vacío']
		self.encode = lambda data: base64.urlsafe_b64encode(data.encode()).decode()
		self.decode = lambda data: base64.urlsafe_b64decode(data.encode()).decode()
		self.HEADERFILE = self.encode('&&FTC&&').encode()
		self.originalFileTime = None
		
		# Convierte de Unix timestamp a Windows FileTime
		# Documentación: https://support.microsoft.com/en-us/help/167296
		self.toTimestamp = lambda epoch: int((epoch * 10000000) + 116444736000000000)
		self.toFileTime  = lambda epoch: byref(wintypes.FILETIME(self.toTimestamp(epoch) & 0xFFFFFFFF, self.toTimestamp(epoch) >> 32))
		self.timeToDate  = lambda time: datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
		self.dateToTime  = lambda date: time.mktime(date.timetuple())
		
	def getFileTimes(self, filePath: str):
		return (
			os.path.getctime(filePath), 
			os.path.getmtime(filePath),
			os.path.getatime(filePath)
		)
	
	def toDatetime(
			self,
			year: int, month: int, day:   int,
			hour  = 0, minute = 0, second = 0
		):
		
		return datetime.datetime(
			year = year, month  = month,  day    = day,
			hour = hour, minute = minute, second = second
		)
	
	def changeFileTimes(self, filePath: str, values):
		# Llamada al Win32 API para modificar los tiempos del archivo
		handle = windll.kernel32.CreateFileW(filePath, 256, 0, None, 3, 128, None)
		windll.kernel32.SetFileTime(handle, *values)
		windll.kernel32.CloseHandle(handle)
	
	def restoreOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		datetimeC = self.datetimeCreatedOriginal.dateTime()
		datetimeM = self.datetimeModifiedOriginal.dateTime()
		
		created = {
			'year':   datetimeC.date().toPyDate().year,
			'month':  datetimeC.date().toPyDate().month,
			'day':    datetimeC.date().toPyDate().day,
			'hour':   datetimeC.time().toPyTime().hour,
			'minute': datetimeC.time().toPyTime().minute,
			'second': datetimeC.time().toPyTime().second
		}
		
		modified = {
			'year':   datetimeM.date().toPyDate().year,
			'month':  datetimeM.date().toPyDate().month,
			'day':    datetimeM.date().toPyDate().day,
			'hour':   datetimeM.time().toPyTime().hour,
			'minute': datetimeM.time().toPyTime().minute,
			'second': datetimeM.time().toPyTime().second
		}
		
		cdate = self.toDatetime(**created)
		mdate = self.toDatetime(**modified)
		
		ctime = self.toFileTime(self.dateToTime(cdate))
		mtime = self.toFileTime(self.dateToTime(mdate))
		
		values = []
		values.append(ctime)
		values.append(None)
		values.append(mtime)
		
		self.changeFileTimes(fileName, values)				# Modifica los Tiempos del Archivo
		
		self.statusbar.showMessage('Restaurado.', 3000)
		self.updateTimes(fileName)
		if self.btnRemoveFileTimes.isEnabled():
			self.originalFileTimeCheck()
	
	def compareOriginalTimes(self) -> bool:
		
		# Datos actuales del archivo:
		
		fileName = self.lineFileName.text()
		
		if not fileName: return False
		
		# Datos actuales en los campos
		datetimeC = QDateTime(self.dateCreated.date(),  self.timeCreated.time())
		datetimeM = QDateTime(self.dateModified.date(), self.timeModified.time())
		# ~ datetimeA = QDateTime(self.dateAccessed.date(), self.timeAccessed.time())
		
		# Datos actuales en los campos originales
		datetimeCO = self.datetimeCreatedOriginal.dateTime()
		datetimeMO = self.datetimeModifiedOriginal.dateTime()
		# ~ datetimeAO = self.datetimeAccessedOriginal.dateTime()
		
		dtC = datetimeC == datetimeCO
		dtM = datetimeM == datetimeMO
		# ~ dtA = datetimeA == datetimeAO
		
		# Será True si la fecha y hora no han sido modificadas en los campos
		same = dtC and dtM #and dtA
		
		self.btnRestoreFileTimes.setEnabled(not same)
		
		return same
	
	def compareTimes(self) -> bool:
		
		# Datos actuales del archivo:
		
		fileName = self.lineFileName.text()
		
		if not fileName: return
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		
		dateC, timeC = self.timeToDate(timeCraw).split(' ')
		dateM, timeM = self.timeToDate(timeMraw).split(' ')
		# ~ dateA, timeA = self.timeToDate(timeAraw).split(' ')
		
		# ~ print(self.timeToDate(timeMraw))
		
		dateCf = QDate(*[int(d) for d in dateC.split('-')])
		dateMf = QDate(*[int(d) for d in dateM.split('-')])
		# ~ dateAf = QDate(*[int(d) for d in dateA.split('-')])
		
		timeCf = QTime(*[int(t) for t in timeC.split(':')])
		timeMf = QTime(*[int(t) for t in timeM.split(':')])
		# ~ timeAf = QTime(*[int(t) for t in timeA.split(':')])
		
		#--------------------------------------------------------------
		
		# Datos actuales en los campos
		dateCc = self.dateCreated.date()
		dateMc = self.dateModified.date()
		# ~ dateAc = self.dateAccessed.date()
		
		timeCc = self.timeCreated.time()
		timeMc = self.timeModified.time()
		# ~ timeAc = self.timeAccessed.time()
		
		#--------------------------------------------------------------
		# Comparamos que los tiempos no hayan sido cambiados
		
		dateC = dateCf.toPyDate() == dateCc.toPyDate()
		dateM = dateMf.toPyDate() == dateMc.toPyDate()
		# ~ dateA = dateAf.toPyDate() == dateAc.toPyDate()
		sameDate = dateC and dateM #and dateA
		
		timeC = timeCf.toPyTime() == timeCc.toPyTime()
		timeM = timeMf.toPyTime() == timeMc.toPyTime()
		# ~ timeA = timeAf.toPyTime() == timeAc.toPyTime()
		sameTime = timeC and timeM #and timeA
		
		# Será True si la fecha y hora no han sido modificadas en los campos
		same = sameDate and sameTime
		
		self.btnUpFileTimes.setEnabled(not same)
		self.saveAction.setEnabled(not same)
	
	def originalFileTimeCheck(self):
		
		self.appendOriginalFileTime()
		
		if self.originalFileTime and self.lineFileName.text():
			
			datetimeC = self.originalFileTime['Created']
			datetimeM = self.originalFileTime['Modified']
			datetimeA = self.originalFileTime['Accessed']
			
			datetimeC = datetimeC.split(' ')
			datetimeC = datetimeC[0].split('-') + datetimeC[1].split(':')
			datetimeC = QDateTime(*[int(d) for d in datetimeC])
			
			datetimeM = datetimeM.split(' ')
			datetimeM = datetimeM[0].split('-') + datetimeM[1].split(':')
			datetimeM = QDateTime(*[int(d) for d in datetimeM])
			
			datetimeA = datetimeA.split(' ')
			datetimeA = datetimeA[0].split('-') + datetimeA[1].split(':')
			datetimeA = QDateTime(*[int(d) for d in datetimeA])
			
			self.datetimeCreatedOriginal.setDateTime(datetimeC)
			self.datetimeModifiedOriginal.setDateTime(datetimeM)
			# ~ self.datetimeAccessedOriginal.setDateTime(datetimeA)
			
			if not self.compareOriginalTimes():
				self.datetimeCreatedOriginal.setEnabled(True)
				self.datetimeModifiedOriginal.setEnabled(True)
				# ~ self.datetimeAccessedOriginal.setEnabled(True)
			else:
				self.datetimeCreatedOriginal.setEnabled(False)
				self.datetimeModifiedOriginal.setEnabled(False)
				# ~ self.datetimeAccessedOriginal.setEnabled(False)
		else:
			
			self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			# ~ self.datetimeAccessedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			
			self.datetimeCreatedOriginal.setEnabled(False)
			self.datetimeModifiedOriginal.setEnabled(False)
			# ~ self.datetimeAccessedOriginal.setEnabled(False)
	
	def updateFileTimes(self):
		
		fileName = self.lineFileName.text()
		
		if not os.path.isfile(fileName):
			
			self.statusbar.showMessage('No se ha cargado ningun archivo', 3000)
			return
		
		if self.btnRemoveFileTimes.isEnabled():
			self.originalFileTimeCheck()
		
		dateC = self.dateCreated.date().toPyDate()
		dateM = self.dateModified.date().toPyDate()
		dateA = self.dateAccessed.date().toPyDate()
		
		timeC = self.timeCreated.time().toPyTime()
		timeM = self.timeModified.time().toPyTime()
		timeA = self.timeAccessed.time().toPyTime()
		
		created = {
			'year':   dateC.year,
			'month':  dateC.month,
			'day':    dateC.day,
			'hour':   timeC.hour,
			'minute': timeC.minute,
			'second': timeC.second
		}
		
		modified = {
			'year':   dateM.year,
			'month':  dateM.month,
			'day':    dateM.day,
			'hour':   timeM.hour,
			'minute': timeM.minute,
			'second': timeM.second
		}
		# ~ print(modified)
		accessed = {
			'year':   dateA.year,
			'month':  dateA.month,
			'day':    dateA.day,
			'hour':   timeA.hour,
			'minute': timeA.minute,
			'second': timeA.second
		}
		
		cdate = self.toDatetime(**created)
		adate = self.toDatetime(**accessed)
		mdate = self.toDatetime(**modified)
		
		ctime = self.toFileTime(self.dateToTime(cdate))
		atime = self.toFileTime(self.dateToTime(adate))
		mtime = self.toFileTime(self.dateToTime(mdate))
		
		values = []
		values.append(ctime)
		values.append(atime)
		values.append(mtime)
		
		self.changeFileTimes(fileName, values)				# Modifica los Tiempos del Archivo
		
		self.statusbar.showMessage('Actualizado.', 3000)
		self.compareTimes()
	
	def updateTimes(self, fileName: str):
		
		# Estrae los tiempos del archivo:
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		dateC, timeC = self.timeToDate(timeCraw).split(' ')
		dateM, timeM = self.timeToDate(timeMraw).split(' ')
		dateA, timeA = self.timeToDate(timeAraw).split(' ')
		
		dateC = QDate(*[int(d) for d in dateC.split('-')])
		dateM = QDate(*[int(d) for d in dateM.split('-')])
		dateA = QDate(*[int(d) for d in dateA.split('-')])
		
		timeC = QTime(*[int(t) for t in timeC.split(':')])
		timeM = QTime(*[int(t) for t in timeM.split(':')])
		timeA = QTime(*[int(t) for t in timeA.split(':')])
		
		self.dateCreated.setDate(dateC)
		self.dateModified.setDate(dateM)
		self.dateAccessed.setDate(dateA)
		
		self.timeCreated.setTime(timeC)
		self.timeModified.setTime(timeM)
		self.timeAccessed.setTime(timeA)
		
		# ~ print(self.dateModified.date(), self.timeModified.time())
		
		if self.btnRemoveFileTimes.isEnabled():
			self.originalFileTimeCheck()
	
	def _createGrid(self): # https://zetcode.com/gui/pyqt5/layout/
		
		self.grid = QGridLayout()
		
		w = QWidget()
		w.setLayout(self.grid)
		
		self.setCentralWidget(w)
		
		#---------------------------------------------------------------
		
		# Pos: 0, 0
		labelOpenFile = QLabel('Ruta de Archivo:')
		# ~ labelOpenFile.setFixedSize(80, 20)
		
		# Pos: 0, 1-3
		self.lineFileName = QLineEdit('')
		self.lineFileName.setReadOnly(True)
		
		# Pos: 0, 4
		self.buttonOpenFile = QPushButton(
			QIcon('icons/open.png'),
			'Cargar Archivo...'
		)
		
		#---------------------------------------------------------------
		
		# Pos: 1, 0
		labelCreated = QLabel('Created:')
		
		# Pos: 1, 1
		self.dateCreated = QDateEdit(calendarPopup=True)
		self.dateCreated.setMinimumDate(QDate(1970,  1,  1))
		self.dateCreated.setMaximumDate(QDate(3000, 12, 31))
		self.dateCreated.setDisplayFormat('dd/MM/yyyy')
		self.dateCreated.setDate(QDate.currentDate())
		# ~ self.dateCreated.setDate(QDate(2000, 1, 1))
		
		# Pos: 1, 2
		self.timeCreated = QTimeEdit()
		self.timeCreated.setTimeRange(QTime(00, 00, 00), QTime(24, 00, 00))
		self.timeCreated.setDisplayFormat('hh:mm:ss')
		self.timeCreated.setTime(QTime.currentTime())
		# ~ self.timeCreated.setTime(QTime(0, 0, 0))
		
		# Pos: 1, 3
		self.labelCreatedOriginal = QLabel('Original:')
		# ~ self.labelCreatedOriginal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		# ~ self.labelCreatedOriginal.setVisible(True)
		self.labelCreatedOriginal.setEnabled(False)
		
		# Pos: 1, 4
		self.datetimeCreatedOriginal = QDateTimeEdit()
		self.datetimeCreatedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeCreatedOriginal.setReadOnly(True)
		# ~ self.datetimeCreatedOriginal.setVisible(True)
		self.datetimeCreatedOriginal.setEnabled(False)
		
		#---------------------------------------------------------------
		
		# Pos: 2, 0
		labelModified = QLabel('Modified:')
		
		# Pos: 2, 1
		self.dateModified = QDateEdit(calendarPopup=True)
		self.dateModified.setMinimumDate(QDate(1970,  1,  1))
		self.dateModified.setMaximumDate(QDate(3000, 12, 31))
		self.dateModified.setDisplayFormat('dd/MM/yyyy')
		self.dateModified.setDate(QDate.currentDate())
		
		# Pos: 2, 2
		self.timeModified = QTimeEdit()
		self.timeModified.setTimeRange(QTime(00, 00, 00), QTime(24, 00, 00))
		self.timeModified.setDisplayFormat('hh:mm:ss')
		self.timeModified.setTime(QTime.currentTime())
		
		# Pos: 2, 3
		self.labelModifiedOriginal = QLabel('Original:')
		self.labelModifiedOriginal.setEnabled(False)
		
		# Pos: 2, 4
		self.datetimeModifiedOriginal = QDateTimeEdit()
		self.datetimeModifiedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeModifiedOriginal.setReadOnly(True)
		self.datetimeModifiedOriginal.setEnabled(False)
		
		#---------------------------------------------------------------
		
		# Pos: 3, 0
		labelAccessed = QLabel('Accessed:')
		
		# Pos: 3, 1
		self.dateAccessed = QDateEdit(calendarPopup=True)
		self.dateAccessed.setMinimumDate(QDate(1970,  1,  1))
		self.dateAccessed.setMaximumDate(QDate(3000, 12, 31))
		self.dateAccessed.setDisplayFormat('dd/MM/yyyy')
		self.dateAccessed.setDate(QDate.currentDate())
		self.dateAccessed.setEnabled(False)
		
		# Pos: 3, 2
		self.timeAccessed = QTimeEdit()
		self.timeAccessed.setTimeRange(QTime(00, 00, 00), QTime(24, 00, 00))
		self.timeAccessed.setDisplayFormat('hh:mm:ss')
		self.timeAccessed.setTime(QTime.currentTime())
		self.timeAccessed.setEnabled(False)
		
		# ~ # Pos: 3, 3
		# ~ self.labelAccessedOriginal = QLabel('Original:')
		# ~ self.labelAccessedOriginal.setEnabled(False)
		
		# ~ # Pos: 3, 4
		# ~ self.datetimeAccessedOriginal = QDateTimeEdit()
		# ~ self.datetimeAccessedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		# ~ self.datetimeAccessedOriginal.setReadOnly(True)
		# ~ self.datetimeAccessedOriginal.setEnabled(False)
		
		# Pos: 3, 4
		self.btnRemoveFileTimes = QPushButton(
			QIcon('icons/remove.png'),
			'Elimina Datos Cargados'
			)
		# ~ self.btnRestoreFileTimes.hide()
		self.btnRemoveFileTimes.setEnabled(False)
		self.btnRemoveFileTimes.setToolTip(
			'Elimina la informacíon de los tiempos\n'
			'originales agregados al archivo.'
		)
		
		#---------------------------------------------------------------
		
		# Pos: 4, 3
		self.btnUpFileTimes = QPushButton(
			QIcon('icons/save.png'),
			'Cambiar Datos'
			)
		# ~ self.btnUpFileTimes.hide()
		self.btnUpFileTimes.setEnabled(False)
		self.btnUpFileTimes.setToolTip(
			'Cambia los tiempos del archivo\n'
			'y respalda los originales.'
		)
		
		# Pos: 4, 4
		self.btnRestoreFileTimes = QPushButton(
			QIcon('icons/reload.png'),
			'Restaurar Datos Originales'
			)
		# ~ self.btnRestoreFileTimes.hide()
		self.btnRestoreFileTimes.setEnabled(False)
		self.btnRestoreFileTimes.setToolTip(
			'Restaura los tiempos del archivo\n'
			'con los datos originales.'
		)
		
		#---------------------------------------------------------------
		
		# ~ self.grid.setRowStretch(0, 0)
		# ~ self.grid.setRowStretch(1, 0)
		# ~ self.grid.setRowStretch(2, 0)
		# ~ self.grid.setRowStretch(3, 0)
		# ~ self.grid.setRowStretch(4, 1)
		
		self.grid.setColumnStretch(0, 0)
		self.grid.setColumnStretch(1, 1)
		self.grid.setColumnStretch(2, 1)
		self.grid.setColumnStretch(3, 1)
		self.grid.setColumnStretch(4, 2)
		
		# Add Widgets
		self.grid.addWidget(labelOpenFile,       0, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.lineFileName,   0, 1, 1, 3)
		self.grid.addWidget(self.buttonOpenFile, 0, 4)
		self.grid.addWidget(labelCreated,        1, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeCreated,    1, 1)
		self.grid.addWidget(self.dateCreated,    1, 2)
		self.grid.addWidget(labelModified,       2, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeModified,   2, 1)
		self.grid.addWidget(self.dateModified,   2, 2)
		self.grid.addWidget(labelAccessed,       3, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeAccessed,   3, 1)
		self.grid.addWidget(self.dateAccessed,   3, 2)
		self.grid.addWidget(self.btnUpFileTimes, 4, 2)
		self.grid.addWidget(self.labelCreatedOriginal,     1, 3, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeCreatedOriginal,  1, 4)
		self.grid.addWidget(self.labelModifiedOriginal,    2, 3, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeModifiedOriginal, 2, 4)
		# ~ self.grid.addWidget(self.labelAccessedOriginal,    3, 3, alignment=Qt.AlignRight)
		# ~ self.grid.addWidget(self.datetimeAccessedOriginal, 3, 4)
		# ~ self.grid.addWidget(self., 3, 3,)
		self.grid.addWidget(self.btnRemoveFileTimes,  3, 4)
		self.grid.addWidget(self.btnRestoreFileTimes, 4, 4)
	
	#---------------------------------------------------------------
	
	def _createActions(self):
		
		# Creating action using the first constructor
		self.newAction = QAction(self)
		# ~ self.newAction.setText('&New')
		# ~ self.newAction.setIcon(QIcon('icons/new.png'))
		
		# Creating actions using the second constructor
		self.saveAction = QAction(QIcon('icons/save.png'), '&Save', self)
		self.saveAction.setEnabled(False)
		self.openAction = QAction(QIcon('icons/open.png'), '&Open...', self)
		self.updateWindowAction = QAction(QIcon('icons/restore.png'), '&Restore', self)
		self.exitAction = QAction(QIcon('icons/exit.png'), '&Exit', self)
		
		# Using string-based key sequences
		self.saveAction.setShortcut('Ctrl+S')
		self.openAction.setShortcut('Ctrl+O')
		self.updateWindowAction.setShortcut('F5')
		self.exitAction.setShortcut('Esc')
		
		# Adding help tips
		saveTip = 'Cambia los tiempos del archivo\n'\
				  'y respalda los originales.'
		self.saveAction.setStatusTip(saveTip)							# Agrega un mensaje a la barra de estatus
		self.saveAction.setToolTip(saveTip)								# Modifica el mensaje de ayuda que aparece encima
		
		openTip = 'Abre el explorador para cargar un archivo.'
		self.openAction.setStatusTip(openTip)
		self.openAction.setToolTip(openTip)
		
		updateWindowTip = 'Restaura los campos modificados de Fecha y Hora\n'\
						  'con los datos actuales del archivo.'
		self.updateWindowAction.setStatusTip(updateWindowTip)
		self.updateWindowAction.setToolTip(updateWindowTip)
		
		# Edit actions
		self.copyAction  = QAction(QIcon('icons/copy.png'),  '&Copy',  self)
		self.pasteAction = QAction(QIcon('icons/paste.png'), '&Paste', self)
		self.cutAction   = QAction(QIcon('icons/cut.png'),   'C&ut',   self)
		self.clearFileNameAction = QAction(QIcon('icons/delete.png'), 'C&lear',   self)
		
		copyTip = 'Copia la ruta del archivo cargado.'
		self.copyAction.setStatusTip(copyTip)
		self.copyAction.setToolTip(copyTip)
		
		pasteTip = 'Pega alguna ruta que se haya copiado.'
		self.pasteAction.setStatusTip(pasteTip)
		self.pasteAction.setToolTip(pasteTip)
		
		cutTip = 'Corta la ruta del archivo cargado.'
		self.cutAction.setStatusTip(cutTip)
		self.cutAction.setToolTip(cutTip)
		
		
		# Using standard keys
		self.copyAction.setShortcut('Ctrl+Shift+C')
		self.pasteAction.setShortcut('Ctrl+Shift+V')
		self.cutAction.setShortcut('Ctrl+Shift+X')
		# Ctrl + Z: Recarga el anterior archivo
		# Ctrl + Y: Recarga el siguiente archivo
		self.clearFileNameAction.setShortcut('Ctrl+L')
		
		clearFileNameTip = 'Limpia el contenido de ruta de archivo.'
		self.clearFileNameAction.setStatusTip(clearFileNameTip)
		self.clearFileNameAction.setToolTip(clearFileNameTip)
		
		# Find and Replace
		# ~ self.findAction    = QAction(QIcon('icons/find.png'),    '&Find...',    self)
		# ~ self.replaceAction = QAction(QIcon('icons/replace.png'), '&Replace...', self)
		
		# Help actions
		self.helpContentAction = QAction(QIcon('icons/help-content.png'), '&Help Content', self)
		self.aboutAction = QAction(QIcon('icons/about.png'), '&About', self)
	
	def _createMenuBar(self):
		menuBar = self.menuBar()
		# File menu
		fileMenu = QMenu('&File', self)
		menuBar.addMenu(fileMenu)
		fileMenu.addAction(self.saveAction)
		fileMenu.addAction(self.openAction)
		
		# Adding an Open Recent submenu
		self.openRecentMenu = fileMenu.addMenu('Open &Recent')
		self.openRecentMenu.setIcon(QIcon('icons/open-recent.png'))
		
		fileMenu.addAction(self.updateWindowAction)
		fileMenu.addSeparator()
		fileMenu.addAction(self.exitAction)
		# Edit menu
		editMenu = menuBar.addMenu('&Edit')
		editMenu.addAction(self.copyAction)
		editMenu.addAction(self.pasteAction)
		editMenu.addAction(self.cutAction)
		editMenu.addSeparator()
		editMenu.addAction(self.clearFileNameAction)
		# Find and Replace submenu in the Edit menuS
		# ~ findMenu = editMenu.addMenu(QIcon('icons/find-replace.png'), '&Find and Replace')
		# ~ findMenu.addAction(self.findAction)
		# ~ findMenu.addAction(self.replaceAction)
		# ~ # Help menu
		helpMenu = menuBar.addMenu(QIcon('icons/help.png'), '&Help')
		helpMenu.addAction(self.helpContentAction)
		helpMenu.addAction(self.aboutAction)
	
	def _createToolBars(self):
		# Using a title
		# ~ toolsToolBar = self.addToolBar('Tools')
		# ~ self.spinBoxNum = QSpinBox()
		# ~ self.spinBoxNum.setFocusPolicy(Qt.NoFocus)
		# ~ toolsToolBar.addWidget(self.spinBoxNum)
		
		fileToolBar = QToolBar('File', self)
		self.addToolBar(Qt.BottomToolBarArea, fileToolBar)
		# ~ fileToolBar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)
		fileToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		fileToolBar.addAction(self.exitAction)
		fileToolBar.addAction(self.clearFileNameAction)
		fileToolBar.addAction(self.openAction)
		fileToolBar.addAction(self.updateWindowAction)
		fileToolBar.addAction(self.saveAction)
		fileToolBar.setMovable(True)
		
		editToolBar = QToolBar('Edit', self)
		self.addToolBar(Qt.RightToolBarArea, editToolBar)
		editToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		editToolBar.addAction(self.copyAction)
		editToolBar.addAction(self.pasteAction)
		editToolBar.addAction(self.cutAction)
	
	def contextMenuEvent(self, event):
		# Creating a menu object with the central widget as parent
		menu = QMenu(self)
		# Populating the menu with actions
		menu.addAction(self.openAction)
		
		# ~ # Creating a separator action
		# ~ separator = QAction(self)
		# ~ separator.setSeparator(True)
		# ~ # Adding the separator to the menu
		# ~ menu.addAction(separator)
		
		menu.addAction(self.clearFileNameAction)
		menu.addSeparator()
		menu.addAction(self.copyAction)
		menu.addAction(self.pasteAction)
		menu.addAction(self.cutAction)
		# Launching the menu
		menu.exec(event.globalPos())
	
	def _connectActions(self):
		
		# Connect File actions
		self.saveAction.triggered.connect(self.updateFileTimes)
		self.openAction.triggered.connect(self.openFile)
		self.openRecentMenu.aboutToShow.connect(self.populateOpenRecent)
		self.updateWindowAction.triggered.connect(self.updateWindow)
		self.exitAction.triggered.connect(self.close)
		
		# Connect Edit actions
		self.copyAction.triggered.connect(self.copyContent)
		self.pasteAction.triggered.connect(self.pasteContent)
		self.cutAction.triggered.connect(self.cutContent)
		self.clearFileNameAction.triggered.connect(self.clearLineFileName)
		
		self.buttonOpenFile.clicked.connect(self.openFile)
		self.btnUpFileTimes.clicked.connect(self.updateFileTimes)
		self.btnRemoveFileTimes.clicked.connect(self.removeOriginalFileTime)
		self.btnRestoreFileTimes.clicked.connect(self.restoreOriginalFileTime)
		
		self.dateCreated.dateChanged.connect(self.compareTimes)
		self.dateModified.dateChanged.connect(self.compareTimes)
		self.dateAccessed.dateChanged.connect(self.compareTimes)
		
		self.timeCreated.timeChanged.connect(self.compareTimes)
		self.timeModified.timeChanged.connect(self.compareTimes)
		self.timeAccessed.timeChanged.connect(self.compareTimes)
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.updateClock)
		self.timer.start(1000)
	
	def _createStatusBar(self):
		self.statusbar = self.statusBar()
		# Adding a temporary message
		self.statusbar.showMessage('Ready', 3000)
		# Adding a permanent message
		t = QTime.currentTime().toPyTime()
		t = '{}:{}'.format(str(t.hour).zfill(2),
						   str(t.minute).zfill(2))
		self.wcLabel = QLabel(t)
		self.statusbar.addPermanentWidget(self.wcLabel)
	
	#-------------------------------------------------------------------
	
	def appendOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		self.originalFileTime = self.extractOriginalFileTime(fileName)
		if self.originalFileTime:
			return
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		datetimeC = self.timeToDate(timeCraw)
		datetimeM = self.timeToDate(timeMraw)
		datetimeA = self.timeToDate(timeAraw)
		fileTimes = {
			'Created': datetimeC,
			'Modified': datetimeM,
			'Accessed': datetimeA
		}
		
		# Añadir
		jsonFileTimes = json.dumps(fileTimes).encode()
		jsonFileTimes = bz2.compress(jsonFileTimes)
		
		with open(fileName, 'rb') as f:
			data = f.read()
		
		with open(fileName, 'wb') as f:
			f.write(data)
			f.write(b'\n')
			f.write(self.HEADERFILE)
			f.write(jsonFileTimes)
		
		self.originalFileTime = fileTimes
		self.updateFileTimes()
		
	
	def extractOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName):
			self.btnRemoveFileTimes.setEnabled(False)
			return
		
		# ~ # Extraer datos añadidos del archivo
		with open(fileName, 'rb') as f:
			
			data = b''
			lines = self.getLastLines(fileName, 8)
			for line in lines:
				data += line + b'\n'
			
			data = data.split(self.HEADERFILE)
			
			if len(data) == 2:
				data = bz2.decompress(data[1]).decode()
				data = json.loads(data)
				self.btnRemoveFileTimes.setEnabled(True)
				return data
			else:
				self.btnRemoveFileTimes.setEnabled(False)
				return
		
	def removeOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		# Eliminar datos añadidos al archivo:
		with open(fileName, 'rb') as f:
			data = f.read()
			data = data.split(b'\n'+self.HEADERFILE)
			if not len(data) == 2:
				return False
		
		with open(fileName, 'wb') as f:
			f.write(data.pop(0))
			self.datetimeCreatedOriginal.setEnabled(False)
			self.datetimeModifiedOriginal.setEnabled(False)
			self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.btnRemoveFileTimes.setEnabled(False)
			self.btnRestoreFileTimes.setEnabled(False)
			self.updateFileTimes()
			return True
	
	#-------------------------------------------------------------------
	
	def updateWindow(self):
		if self.lineFileName.text():
			self.updateTimes(self.lineFileName.text())
		else:
			self.dateCreated.setDate(QDate.currentDate())
			self.dateModified.setDate(QDate.currentDate())
			self.dateAccessed.setDate(QDate.currentDate())
			
			self.timeCreated.setTime(QTime.currentTime())
			self.timeModified.setTime(QTime.currentTime())
			self.timeAccessed.setTime(QTime.currentTime())
	
	def updateClock(self):
		
		t = QTime.currentTime().toPyTime()
		t = '{}:{}'.format(str(t.hour).zfill(2),
						   str(t.minute).zfill(2))
		
		self.wcLabel.setText(t)
		
		if not self.lineFileName.text():
			self.dateAccessed.setDate(QDate.currentDate())
			self.timeAccessed.setTime(QTime.currentTime())
	
	def openFile(self, fileName=None):
		if not fileName:
			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			fileName, _ = QFileDialog.getOpenFileName(
				self, 'Abrir', os.getcwd(),
				# ~ 'Imágenes (*.jpg *.bmp);;Todos los archivos (*.*)',
				'Todos los archivos (*.*)'
				';;Texto (*.txt)'
				';;Imágen (*.jpg *.png *.bmp *.ico *svg)'
				';;Video (*.mp4 *.avi *.mkv)'
				';;Audio (*.mp3 *.wav)'
				';;Documento (*.pdf *.docx)',
				options=options
			)
		fileName = fileName.replace('/', '\\') 
		if fileName and not fileName == self.lineFileName.text():
			self.lineFileName.setText(fileName)
			if not fileName in self.listRecentFiles:
				if len(self.listRecentFiles) > 7:
					self.listRecentFiles.pop(0)
				elif self.listRecentFiles == ['Vacío']:
					self.listRecentFiles = []
			else:
				pos = self.listRecentFiles.index(fileName)
				self.listRecentFiles.pop(pos)
			self.listRecentFiles.append(fileName)
			# Actualiza los tiempos en los campos
			# Current, Modified y Accessed en la ventana.
			self.updateTimes(fileName)
			self.originalFileTimeCheck()
			self.btnRemoveFileTimes.setEnabled(True)
	
	def openRecentFile(self, fileName):
		if not fileName == 'Vacío':
			self.lineFileName.setText(fileName)
			self.updateTimes(fileName)
			pos = self.listRecentFiles.index(fileName)
			self.listRecentFiles.pop(pos)
			self.listRecentFiles.append(fileName)
			self.originalFileTimeCheck()
	
	def cleanRecentFiles(self):
		self.openRecentMenu.clear()
		self.listRecentFiles = [self.lineFileName.text()]
	
	def populateOpenRecent(self):
		# Step 1. Remove the old options from the menu
		self.openRecentMenu.clear()
		# Step 2. Dynamically create the actions
		actions = []
		# ~ filenames = [f'File-{n}' for n in range(5)]
		for filename in self.listRecentFiles[::-1]:
			if filename == 'Vacío':
				icon = QIcon('icons/icon.png')
				name = '...' + ' Xyzzy'
			else:
				icon = QIcon('icons/recent-file.png')
				path = filename.split('\\')
				if len(path) > 3:
					name = '...\\'+'\\'.join(path[-3:])
				else:
					name = '\\'.join(path)
			action = QAction(icon, name, self)
			if name == '... Xyzzy':
				actionTip = 'No pasa nada...'
				con = self.xyzzy
			elif filename == self.lineFileName.text():
				actionTip = f'El archivo {repr(path[-1])} ya esta abierto...'
				con = partial(self.openRecentFile, filename)
			else:
				actionTip = 'Carga el archivo '+repr(path[-1])
				con = partial(self.openRecentFile, filename)
			action.setStatusTip(actionTip)		# Agrega un mensaje a la barra de estatus
			action.setToolTip(actionTip)		# Modifica el mensaje de ayuda que aparece encima
			action.triggered.connect(con)
			actions.append(action)
		# Step 3. Add the actions to the menu
		self.openRecentMenu.addActions(actions)
		
		if not self.listRecentFiles == ['Vacío']:
			self.openRecentMenu.addSeparator()
			action = QAction(QIcon('icons/delete.png'), 'Limpiar historial...', self)
			actionTip = 'Limpia el historial de archivos recientes.'
			action.setStatusTip(actionTip)
			action.setToolTip(actionTip)
			action.triggered.connect(self.cleanRecentFiles)
			self.openRecentMenu.addAction(action)
	
	def copyContent(self):
		text = self.lineFileName.text()
		if text:
			self.Clipboard.text = text
			self.statusbar.showMessage('Ruta de archivo copiada.', 3000)
		else:
			self.statusbar.showMessage('No hay nada que copiar.', 3000)
	
	def pasteContent(self):
		text = self.Clipboard.text
		if os.path.isfile(text):
			if not text == self.lineFileName.text():
				self.openFile(text)
				self.statusbar.showMessage('Ruta de Archivo pegada.', 3000)
			else:
				self.statusbar.showMessage('El archivo ya esta cargado.', 3000)
		else:
			self.statusbar.showMessage('El texto copiado no es ruta de un archivo existente.', 3000)
		self.originalFileTimeCheck()
	
	def cutContent(self):
		text = self.lineFileName.text()
		if text:
			self.Clipboard.text = text
			self.clearLineFileName()
			self.statusbar.showMessage('Ruta de Archivo cortada.', 3000)
		else:
			self.statusbar.showMessage('No hay nada que copiar.', 3000)
		self.originalFileTimeCheck()
	
	def clearLineFileName(self):
		self.lineFileName.setText('')
		self.btnUpFileTimes.setEnabled(False)
		
		self.datetimeCreatedOriginal.setEnabled(False)
		self.datetimeModifiedOriginal.setEnabled(False)
		self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
		self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
		self.btnRemoveFileTimes.setEnabled(False)
		self.btnRestoreFileTimes.setEnabled(False)
		
		self.dateCreated.setDate(QDate.currentDate())
		self.dateModified.setDate(QDate.currentDate())
		self.dateAccessed.setDate(QDate.currentDate())
		self.timeCreated.setTime(QTime.currentTime())
		self.timeModified.setTime(QTime.currentTime())
		self.timeAccessed.setTime(QTime.currentTime())
	
	def xyzzy(self):
		self.statusbar.showMessage('No pasó nada.', 3000)
	
	def getLastLines(self, file_name, N):
		list_of_lines = []
		with open(file_name, 'rb') as read_obj:
			read_obj.seek(0, os.SEEK_END)
			buffer_ = bytearray()
			pointer_location = read_obj.tell()
			while pointer_location >= 0:
				read_obj.seek(pointer_location)
				pointer_location = pointer_location -1
				new_byte = read_obj.read(1)
				if new_byte == b'\n':
					list_of_lines.append(buffer_[::-1])
					if len(list_of_lines) == N:
						return list(reversed(list_of_lines))
					buffer_ = bytearray()
				else:
					buffer_.extend(new_byte)
			if len(buffer_) > 0:
				list_of_lines.append(buffer_[::-1])
		return list(reversed(list_of_lines))

if __name__ == '__main__':
	app = QApplication(sys.argv)
	win = Window()
	win.show()
	sys.exit(app.exec_())







