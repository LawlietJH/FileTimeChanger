
#https://realpython.com/python-menus-toolbars/

# pip install PyQt5
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QTimer
from PyQt5.QtWidgets import (
	#QMenuBar, QSpinBox,
	#QVBoxLayout, QHBoxLayout
	QApplication, QLabel, QMainWindow,
	QMenu, QToolBar, QAction,
	QPushButton, QWidget, QGridLayout,
	QDateEdit, QTimeEdit, QFileDialog,
	QLineEdit, QDateTimeEdit,
	QCheckBox, QWidgetAction)
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
__version__ = 'v1.0.3'					# Versión

#=======================================================================
# Tomado de https://github.com/LawlietJH/Utils
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
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self.Clipboard = Clipboard()
		self._createWindow()
		self._createGrid()
		self._createActions()
		self._createMenuBar()
		self._createToolBars()
		self._connectActions()
		self._createStatusBar()
	
	#===================================================================
	# GUI
	
	def _createWindow(self):
		self.setWindowTitle(__title__+' '+__version__ + ' - By: ' + __author__)
		self.setWindowIcon(QIcon('icons/icon.png'))
		self.setFixedSize(720, 360)
		
		self.listRecentFiles = ['Vacío']
		self.qtyListRecentFiles = 7
		self.filenameRecentFiles = '%temp%\\recentFiles.ftc'
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
		self.strToDate   = lambda date_time_str: datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
	
	def _createActions(self):
		#===============================================================
		# 'File' Actions
		# Creating action using the first constructor
		# ~ self.newAction = QAction(self)
		# ~ self.newAction.setText('&New')
		# ~ self.newAction.setIcon(QIcon('icons/new.png'))
		# Creating actions using the second constructor
		self.openAction = QAction(QIcon('icons/open.png'), '&Open...', self)
		self.updateWindowAction = QAction(QIcon('icons/restore.png'), '&Restore', self)
		self.saveAction = QAction(QIcon('icons/save.png'), '&Save', self, enabled=False)
		self.appendOriginalFileTimeAction = QAction(QIcon('icons/agregar.png'), '&Add FT', enabled=False)
		self.removeOriginalFileTimeAction = QAction(QIcon('icons/remove.png'),  '&Del FT', enabled=False)
		self.exitAction = QAction(QIcon('icons/exit.png'), '&Exit', self)
		#---------------------------------------------------------------
		# Using Keys
		self.openAction.setShortcut('Ctrl+O')
		self.updateWindowAction.setShortcut('F5')
		self.saveAction.setShortcut('Ctrl+S')
		self.appendOriginalFileTimeAction.setShortcut('Ctrl+E')
		self.removeOriginalFileTimeAction.setShortcut('Ctrl+R')
		self.exitAction.setShortcut('Esc')
		#---------------------------------------------------------------
		# Adding 'File' Tips
		openTip = 'Abre el explorador para cargar un archivo.'
		self.openAction.setStatusTip(openTip)
		self.openAction.setToolTip(openTip)
		updateWindowTip = 'Restaura los campos modificados de Fecha y Hora\n'\
						  'con los datos actuales del archivo.'
		self.updateWindowAction.setStatusTip(updateWindowTip)
		self.updateWindowAction.setToolTip(updateWindowTip)
		saveTip = 'Cambia los tiempos del archivo\n'\
				  'y respalda los originales.'
		self.saveAction.setStatusTip(saveTip)							# Agrega un mensaje a la barra de estatus
		self.saveAction.setToolTip(saveTip)								# Modifica el mensaje de ayuda que aparece encima
		appendOriginalFileTimeTip = 'Guarda en el archivo los tiempos originales.'
		self.appendOriginalFileTimeAction.setStatusTip(appendOriginalFileTimeTip)
		self.appendOriginalFileTimeAction.setToolTip(appendOriginalFileTimeTip)
		removeOriginalFileTimeTip = 'Elimina del archivo los tiempos originales.'
		self.removeOriginalFileTimeAction.setStatusTip(removeOriginalFileTimeTip)
		self.removeOriginalFileTimeAction.setToolTip(removeOriginalFileTimeTip)
		#===============================================================
		# 'Edit' actions
		self.copyFileNameAction  = QAction(QIcon('icons/copy.png'),   '&Copy',  self, enabled=False)
		self.pasteFileNameAction = QAction(QIcon('icons/paste.png'),  '&Paste', self)
		self.cutFileNameAction   = QAction(QIcon('icons/cut.png'),    'C&ut',   self, enabled=False)
		self.clearFileNameAction = QAction(QIcon('icons/delete.png'), 'C&lear', self, enabled=False)
		# Find and Replace
		# ~ self.findAction    = QAction(QIcon('icons/find.png'),    '&Find...',    self)
		# ~ self.replaceAction = QAction(QIcon('icons/replace.png'), '&Replace...', self)
		#---------------------------------------------------------------
		# Using Keys
		self.copyFileNameAction.setShortcut('Ctrl+Shift+C')
		self.pasteFileNameAction.setShortcut('Ctrl+Shift+V')
		self.cutFileNameAction.setShortcut('Ctrl+Shift+X')
		# Ctrl + Z: Recarga el anterior archivo
		# Ctrl + Y: Recarga el siguiente archivo
		self.clearFileNameAction.setShortcut('Ctrl+L')
		#---------------------------------------------------------------
		# Adding 'Edit' Tips
		copyFileNameTip = 'Copia la ruta del archivo cargado.'
		self.copyFileNameAction.setStatusTip(copyFileNameTip)
		self.copyFileNameAction.setToolTip(copyFileNameTip)
		pasteFileNameTip = 'Pega alguna ruta que se haya copiado.'
		self.pasteFileNameAction.setStatusTip(pasteFileNameTip)
		self.pasteFileNameAction.setToolTip(pasteFileNameTip)
		cutFileNameTip = 'Corta la ruta del archivo cargado.'
		self.cutFileNameAction.setStatusTip(cutFileNameTip)
		self.cutFileNameAction.setToolTip(cutFileNameTip)
		clearFileNameTip = 'Limpia el contenido de ruta de archivo.'
		self.clearFileNameAction.setStatusTip(clearFileNameTip)
		self.clearFileNameAction.setToolTip(clearFileNameTip)
		#===============================================================
		# Check actions
		self.checkToolBarFileAction = QAction(QIcon('icons/check-false.png'), 'Floating: &File Toolbar', self)# checkable=True, checked=True)
		self.checkToolBarEditAction = QAction(QIcon('icons/check-false.png'), 'Floating: &Edit Toolbar', self)# checkable=True)
		self.checkToolBarFileShowNamesAction = QAction(QIcon('icons/check-true.png'), 'Show Names: F&ile Toolbar', self)# checkable=True, checked=True)
		self.checkToolBarEditShowNamesAction = QAction(QIcon('icons/check-true.png'), 'Show Names: E&dit Toolbar', self)# checkable=True, checked=True)
		#===============================================================
		# Help actions
		self.helpContentAction = QAction(QIcon('icons/help-content.png'), '&Help Content', self)
		self.aboutAction = QAction(QIcon('icons/about.png'), '&About', self)
	
	def _createMenuBar(self):
		menuBar = self.menuBar()
		#===============================================================
		# File menu
		fileMenu = QMenu('&File', self)
		menuBar.addMenu(fileMenu)
		fileMenu.addAction(self.openAction)
		self.openRecentMenu = fileMenu.addMenu('O&pen Recent')
		self.openRecentMenu.setIcon(QIcon('icons/open-recent.png'))
		fileMenu.addAction(self.updateWindowAction)
		fileMenu.addSeparator()
		fileMenu.addAction(self.saveAction)
		fileMenu.addAction(self.appendOriginalFileTimeAction)
		fileMenu.addAction(self.removeOriginalFileTimeAction)
		fileMenu.addSeparator()
		fileMenu.addAction(self.exitAction)
		#===============================================================
		# Edit menu
		editMenu = menuBar.addMenu('&Edit')
		editMenu.addAction(self.copyFileNameAction)
		editMenu.addAction(self.pasteFileNameAction)
		editMenu.addAction(self.cutFileNameAction)
		editMenu.addSeparator()
		editMenu.addAction(self.clearFileNameAction)
		# Find and Replace submenu in the Edit menuS
		# ~ findMenu = editMenu.addMenu(QIcon('icons/find-replace.png'), '&Find and Replace')
		# ~ findMenu.addAction(self.findAction)
		# ~ findMenu.addAction(self.replaceAction)
		#===============================================================
		# Check menu
		checkMenu = menuBar.addMenu('&Check')
		checkMenu.addAction(self.checkToolBarFileAction)
		checkMenu.addAction(self.checkToolBarEditAction)
		checkMenu.addAction(self.checkToolBarFileShowNamesAction)
		checkMenu.addAction(self.checkToolBarEditShowNamesAction)
		#===============================================================
		# Help menu
		helpMenu = menuBar.addMenu(QIcon('icons/help.png'), '&Help')
		helpMenu.addAction(self.helpContentAction)
		helpMenu.addAction(self.aboutAction)
	
	def _createToolBars(self):
		
		self.fileToolBar = QToolBar('File', self)
		self.addToolBar(Qt.BottomToolBarArea, self.fileToolBar)
		self.fileToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.fileToolBar.addAction(self.exitAction)
		self.fileToolBar.addSeparator()
		self.fileToolBar.addAction(self.openAction)
		self.fileToolBar.addAction(self.updateWindowAction)
		self.fileToolBar.addAction(self.saveAction)
		self.fileToolBar.addSeparator()
		self.fileToolBar.addAction(self.appendOriginalFileTimeAction)
		self.fileToolBar.addAction(self.removeOriginalFileTimeAction)
		self.fileToolBar.setMovable(False)
		
		self.editToolBar = QToolBar('Edit', self)
		self.addToolBar(Qt.BottomToolBarArea, self.editToolBar)
		self.editToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.editToolBar.addAction(self.copyFileNameAction)
		self.editToolBar.addAction(self.pasteFileNameAction)
		self.editToolBar.addAction(self.cutFileNameAction)
		self.editToolBar.addSeparator()
		self.editToolBar.addAction(self.clearFileNameAction)
		self.editToolBar.setMovable(False)
	
	def _connectActions(self):
		
		# Connect File actions
		self.saveAction.triggered.connect(self.updateFileTimes)
		self.openAction.triggered.connect(self.openFile)
		self.openRecentMenu.aboutToShow.connect(self.populateOpenRecent)
		self.updateWindowAction.triggered.connect(self.updateWindow)
		self.appendOriginalFileTimeAction.triggered.connect(self.appendOriginalFileTimeAgain)
		self.removeOriginalFileTimeAction.triggered.connect(self.removeOriginalFileTime)
		self.exitAction.triggered.connect(self.close)
		
		# Connect Edit actions
		self.copyFileNameAction.triggered.connect(self.copyContent)
		self.pasteFileNameAction.triggered.connect(self.pasteContent)
		self.cutFileNameAction.triggered.connect(self.cutContent)
		self.clearFileNameAction.triggered.connect(self.clearLineFileName)
		
		# Connect Check actions
		self.checkToolBarFileAction.triggered.connect(self.updateMenuCheckFile)
		self.checkToolBarEditAction.triggered.connect(self.updateMenuCheckEdit)
		self.checkToolBarFileShowNamesAction.triggered.connect(self.updateMenuCheckFileShowNames)
		self.checkToolBarEditShowNamesAction.triggered.connect(self.updateMenuCheckEditShowNames)
		
		# Buttons:
		self.buttonOpenFile.clicked.connect(self.openFile)
		self.btnLoadCurrentTime.clicked.connect(self.updateTimesWithCurrentDateTime)
		self.btnUpFileTimes.clicked.connect(self.updateFileTimes)
		self.btnRemoveFileTimes.clicked.connect(self.removeOriginalFileTime)
		self.btnRestoreFileTimes.clicked.connect(self.restoreOriginalFileTime)
		
		# Date and Time Edits
		self.dateCreated.dateChanged.connect(self.compareTimes)
		self.dateModified.dateChanged.connect(self.compareTimes)
		self.dateAccessed.dateChanged.connect(self.compareTimes)
		self.timeCreated.timeChanged.connect(self.compareTimes)
		self.timeModified.timeChanged.connect(self.compareTimes)
		self.timeAccessed.timeChanged.connect(self.compareTimes)
		
		# Clock
		self.timer = QTimer()
		self.timer.timeout.connect(self.updateClock)
		self.timer.start(1000)
	
	def _createStatusBar(self):
		self.statusbar = self.statusBar()
		# Adding a temporary message
		self.statusbar.showMessage('Ready', 3000)
		# Adding a permanent message
		t = QTime.currentTime().toPyTime()
		t = '{}:{}:{}'.format(str(t.hour).zfill(2),
							  str(t.minute).zfill(2),
							  str(t.second).zfill(2))
		self.wcLabel = QLabel(t)
		self.statusbar.addPermanentWidget(self.wcLabel)
	
	def contextMenuEvent(self, event):
		# Creating a menu object with the central widget as parent
		menu = QMenu(self)
		# Populating the menu with actions
		menu.addAction(self.openAction)
		menu.addAction(self.clearFileNameAction)
		menu.addSeparator()
		menu.addAction(self.copyFileNameAction)
		menu.addAction(self.pasteFileNameAction)
		menu.addAction(self.cutFileNameAction)
		menu.addSeparator()
		menu.addAction(self.appendOriginalFileTimeAction)
		menu.addAction(self.removeOriginalFileTimeAction)
		# Launching the menu
		menu.exec(event.globalPos())
	
	#===================================================================
	# FileTime Checks
	
	def restoreOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		datetimeC = self.datetimeCreatedOriginal.dateTime()
		datetimeM = self.datetimeModifiedOriginal.dateTime()
		datetimeA = self.datetimeAccessedOriginal.dateTime()
		
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
		
		accessed = {
			'year':   datetimeA.date().toPyDate().year,
			'month':  datetimeA.date().toPyDate().month,
			'day':    datetimeA.date().toPyDate().day,
			'hour':   datetimeA.time().toPyTime().hour,
			'minute': datetimeA.time().toPyTime().minute,
			'second': datetimeA.time().toPyTime().second
		}
		
		cdate = self.toDatetime(**created)
		mdate = self.toDatetime(**modified)
		adate = self.toDatetime(**accessed)
		
		ctime = self.toFileTime(self.dateToTime(cdate))
		mtime = self.toFileTime(self.dateToTime(mdate))
		atime = self.toFileTime(self.dateToTime(adate))
		
		values = []
		values.append(ctime)
		values.append(atime)
		values.append(mtime)
		
		self.changeFileTimes(fileName, values)				# Modifica los Tiempos del Archivo
		
		self.statusbar.showMessage('Restaurado.', 3000)
		self.updateTimes(fileName)
		
		if self.btnRemoveFileTimes.isEnabled():
			self.originalFileTimeCheck()
	
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
	
	def compareOriginalTimes(self) -> bool:
		
		# Datos actuales del archivo:
		fileName = self.lineFileName.text()
		if not fileName: return False
		
		# Datos actuales en los campos
		datetimeC = QDateTime(self.dateCreated.date(),  self.timeCreated.time()).toPyDateTime()
		datetimeM = QDateTime(self.dateModified.date(), self.timeModified.time()).toPyDateTime()
		datetimeA = QDateTime(self.dateAccessed.date(), self.timeAccessed.time()).toPyDateTime()
		
		datetimeC = datetime.datetime(datetimeC.year, datetimeC.month, datetimeC.day, datetimeC.hour, datetimeC.minute, datetimeC.second)
		datetimeM = datetime.datetime(datetimeM.year, datetimeM.month, datetimeM.day, datetimeM.hour, datetimeM.minute, datetimeM.second)
		datetimeA = datetime.datetime(datetimeA.year, datetimeA.month, datetimeA.day, datetimeA.hour, datetimeA.minute, datetimeA.second)
		
		# Datos actuales en los campos originales
		datetimeCO = self.datetimeCreatedOriginal.dateTime().toPyDateTime()
		datetimeMO = self.datetimeModifiedOriginal.dateTime().toPyDateTime()
		datetimeAO = self.datetimeAccessedOriginal.dateTime().toPyDateTime()
		
		dtC = datetimeC == datetimeCO
		dtM = datetimeM == datetimeMO
		dtA = datetimeA == datetimeAO
		
		# Será True si la fecha y hora no han sido modificadas en los campos
		same = dtC and dtM and dtA
		
		self.btnRestoreFileTimes.setEnabled(not same)
		
		return same
	
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
			self.datetimeAccessedOriginal.setDateTime(datetimeA)
			
			if not self.compareOriginalTimes():
				self.datetimeCreatedOriginal.setEnabled(True)
				self.datetimeModifiedOriginal.setEnabled(True)
				self.datetimeAccessedOriginal.setEnabled(True)
			else:
				self.datetimeCreatedOriginal.setEnabled(False)
				self.datetimeModifiedOriginal.setEnabled(False)
				self.datetimeAccessedOriginal.setEnabled(False)
		else:
			
			self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeAccessedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			
			self.datetimeCreatedOriginal.setEnabled(False)
			self.datetimeModifiedOriginal.setEnabled(False)
			self.datetimeAccessedOriginal.setEnabled(False)
	
	def updateTimes(self, fileName: str):
		
		# Extrae los tiempos del archivo:
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
		
		if self.btnRemoveFileTimes.isEnabled():
			self.originalFileTimeCheck()
	
	def compareTimes(self) -> bool:
		
		# Datos actuales del archivo:
		fileName = self.lineFileName.text()
		if not fileName: return
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		
		dateC, timeC = self.timeToDate(timeCraw).split(' ')
		dateM, timeM = self.timeToDate(timeMraw).split(' ')
		dateA, timeA = self.timeToDate(timeAraw).split(' ')
		
		dateCf = QDate(*[int(d) for d in dateC.split('-')]).toPyDate()
		dateMf = QDate(*[int(d) for d in dateM.split('-')]).toPyDate()
		dateAf = QDate(*[int(d) for d in dateA.split('-')]).toPyDate()
		
		timeCf = QTime(*[int(t) for t in timeC.split(':')]).toPyTime()
		timeMf = QTime(*[int(t) for t in timeM.split(':')]).toPyTime()
		timeAf = QTime(*[int(t) for t in timeA.split(':')]).toPyTime()
		
		#--------------------------------------------------------------
		
		# Datos actuales en los campos
		dateCc = self.dateCreated.date().toPyDate()
		dateMc = self.dateModified.date().toPyDate()
		dateAc = self.dateAccessed.date().toPyDate()
		
		timeCc = self.timeCreated.time().toPyTime()
		timeCc = datetime.time(timeCc.hour, timeCc.minute, timeCc.second)
		timeMc = self.timeModified.time().toPyTime()
		timeMc = datetime.time(timeMc.hour, timeMc.minute, timeMc.second)
		timeAc = self.timeAccessed.time().toPyTime()
		timeAc = datetime.time(timeMc.hour, timeMc.minute, timeMc.second)
		
		#--------------------------------------------------------------
		# Comparamos que los tiempos no hayan sido cambiados
		
		dateC = dateCf == dateCc
		dateM = dateMf == dateMc
		dateA = dateAf == dateAc
		# ~ dateA = dateAf.toPyDate() == dateAc.toPyDate()
		sameDate = dateC and dateM and dateA
		
		timeC = timeCf == timeCc
		timeM = timeMf == timeMc
		timeA = timeAf == timeAc
		sameTime = timeC and timeM and timeA
		
		# Será True si la fecha y hora no han sido modificadas en los campos
		same = sameDate and sameTime
		
		self.btnUpFileTimes.setEnabled(not same)
		self.saveAction.setEnabled(not same)
	
	def _createGrid(self):
		
		self.grid = QGridLayout()	# https://zetcode.com/gui/pyqt5/layout/
		
		w = QWidget()
		w.setLayout(self.grid)
		
		self.setCentralWidget(w)
		
		#---------------------------------------------------------------
		
		# Pos: 0, 0
		labelOpenFile = QLabel('Ruta de Archivo:')
		# ~ labelOpenFile.setFixedSize(80, 20)
		
		# Pos: 0, 1-4
		self.lineFileName = QLineEdit('')
		self.lineFileName.setReadOnly(True)
		
		# Pos: 0, 5
		self.buttonOpenFile = QPushButton(
			QIcon('icons/find.png'),
			'Cargar Archivo...'
		)
		# ~ self.buttonOpenFile.hide()
		# ~ self.buttonOpenFile.show()
		
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
		
		# Pos: 1, 4
		self.labelCreatedOriginal = QLabel('Created Original:')
		# ~ self.labelCreatedOriginal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		# ~ self.labelCreatedOriginal.setVisible(True)
		self.labelCreatedOriginal.setEnabled(False)
		
		# Pos: 1, 5
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
		
		# Pos: 2, 4
		self.labelModifiedOriginal = QLabel('Modified Original:')
		self.labelModifiedOriginal.setEnabled(False)
		
		# Pos: 2, 5
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
		# ~ self.dateAccessed.setEnabled(False)
		
		# Pos: 3, 2
		self.timeAccessed = QTimeEdit()
		self.timeAccessed.setTimeRange(QTime(00, 00, 00), QTime(24, 00, 00))
		self.timeAccessed.setDisplayFormat('hh:mm:ss')
		self.timeAccessed.setTime(QTime.currentTime())
		# ~ self.timeAccessed.setEnabled(False)
		
		# Pos: 3, 4
		self.labelAccessedOriginal = QLabel('Accessed Original:')
		self.labelAccessedOriginal.setEnabled(False)
		
		# Pos: 3, 5
		self.datetimeAccessedOriginal = QDateTimeEdit()
		self.datetimeAccessedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeAccessedOriginal.setReadOnly(True)
		self.datetimeAccessedOriginal.setEnabled(False)
		
		#---------------------------------------------------------------
		
		# Pos: 4, 1
		self.btnLoadCurrentTime = QPushButton(
			QIcon('icons/update.png'),
			'Actualizar'
			)
		self.btnLoadCurrentTime.setToolTip(
			'Agrega la fecha y hora actual\n'
			'en los campos.'
		)
		
		# Pos: 4, 2
		self.btnUpFileTimes = QPushButton(
			QIcon('icons/save.png'),
			'Cambiar Datos'
			)
		self.btnUpFileTimes.setEnabled(False)
		self.btnUpFileTimes.setToolTip(
			'Cambia los tiempos del archivo\n'
			'y respalda los originales.'
		)
		
		# Pos: 4, 5
		self.btnRemoveFileTimes = QPushButton(
			QIcon('icons/remove.png'),
			'Elimina Tiempos Originales'
			)
		self.btnRemoveFileTimes.setEnabled(False)
		self.btnRemoveFileTimes.setToolTip(
			'Elimina del archivo los\n'
			'tiempos originales.'
		)
		
		#---------------------------------------------------------------
		
		# Pos: 5, 5
		self.btnRestoreFileTimes = QPushButton(
			QIcon('icons/reload.png'),
			'Restaurar Datos Originales'
			)
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
		self.grid.setColumnStretch(4, 1)
		self.grid.setColumnStretch(5, 2)
		
		# Add Widgets
		self.grid.addWidget(labelOpenFile,           0, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.lineFileName,       0, 1, 1, 4)
		self.grid.addWidget(self.buttonOpenFile,     0, 5)
		self.grid.addWidget(labelCreated,            1, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeCreated,        1, 1)
		self.grid.addWidget(self.dateCreated,        1, 2)
		self.grid.addWidget(labelModified,           2, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeModified,       2, 1)
		self.grid.addWidget(self.dateModified,       2, 2)
		self.grid.addWidget(labelAccessed,           3, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeAccessed,       3, 1)
		self.grid.addWidget(self.dateAccessed,       3, 2)
		self.grid.addWidget(self.btnLoadCurrentTime, 4, 1)
		self.grid.addWidget(self.btnUpFileTimes,     4, 2)
		
		self.grid.addWidget(self.labelCreatedOriginal,     1, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeCreatedOriginal,  1, 5)
		self.grid.addWidget(self.labelModifiedOriginal,    2, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeModifiedOriginal, 2, 5)
		self.grid.addWidget(self.labelAccessedOriginal,    3, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeAccessedOriginal, 3, 5)
		self.grid.addWidget(self.btnRemoveFileTimes,       4, 5)
		self.grid.addWidget(self.btnRestoreFileTimes,      5, 5)
	
	#===================================================================
	# FileTime Controllers
	
	def appendOriginalFileTimeAgain(self):
		
		self.btnRemoveFileTimes.setEnabled(True)
		self.btnRestoreFileTimes.setEnabled(True)
		self.appendOriginalFileTimeAction.setEnabled(False)
		self.removeOriginalFileTimeAction.setEnabled(True)
		self.appendOriginalFileTime()
	
	def appendOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName):
			return
		
		self.originalFileTime = self.extractOriginalFileTime(fileName)
		if self.originalFileTime:
			return
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		datetimeC = self.timeToDate(timeCraw)
		datetimeM = self.timeToDate(timeMraw)
		datetimeA = self.timeToDate(timeAraw)
		fileTimes = {
			'Created':  datetimeC,
			'Modified': datetimeM,
			'Accessed': datetimeA
		}
		
		# Añadir
		jsonFileTimes = json.dumps(fileTimes).encode()
		jsonFileTimes = bz2.compress(jsonFileTimes)
		
		# ~ with open(fileName+':FTC', 'rb') as f:
			# ~ data = f.read()
		
		with open(fileName+':FTC', 'wb') as f:
			# ~ f.write(data)
			# ~ f.write(b'\n')
			f.write(self.HEADERFILE)
			f.write(jsonFileTimes)
		
		self.originalFileTime = fileTimes
		# ~ self.updateFileTimes()
	
	def extractOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName):
			self.btnRemoveFileTimes.setEnabled(False)
			self.btnRestoreFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(False)
			self.removeOriginalFileTimeAction.setEnabled(False)
			return
		
		if not os.path.isfile(fileName+':FTC'): return
		
		# Extraer datos añadidos del archivo
		with open(fileName+':FTC', 'rb') as f:
			
			data = b''
			lines = self.getLastLines(fileName+':FTC', 16)
			for line in lines:
				data += line + b'\n'
			
			data = data.split(self.HEADERFILE)
			
			if len(data) == 2:
				try: data = bz2.decompress(data[1]).decode()
				except OSError:
					f.close()
					self.removeOriginalFileTime()#update=False)
					return
				data = json.loads(data)
				self.btnRemoveFileTimes.setEnabled(True)
				self.btnRestoreFileTimes.setEnabled(True)
				self.appendOriginalFileTimeAction.setEnabled(False)
				self.removeOriginalFileTimeAction.setEnabled(True)
				return data
			else:
				self.btnRemoveFileTimes.setEnabled(False)
				self.btnRestoreFileTimes.setEnabled(False)
				self.appendOriginalFileTimeAction.setEnabled(True)
				self.removeOriginalFileTimeAction.setEnabled(False)
				return
		
	def removeOriginalFileTime(self, fileName=None, update=True):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		if os.path.isfile(fileName+':FTC'):
			os.remove(fileName+':FTC')
			self.datetimeCreatedOriginal.setEnabled(False)
			self.datetimeModifiedOriginal.setEnabled(False)
			self.datetimeAccessedOriginal.setEnabled(False)
			self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeAccessedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.btnRemoveFileTimes.setEnabled(False)
			self.btnRestoreFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(True)
			self.removeOriginalFileTimeAction.setEnabled(False)
			if update: self.updateFileTimes()
			return True
	
	#===================================================================
	# Action Functions
	
	def updateTimesWithCurrentDateTime(self):
		self.dateCreated.setDate(QDate.currentDate())
		self.dateModified.setDate(QDate.currentDate())
		self.dateAccessed.setDate(QDate.currentDate())
		self.timeCreated.setTime(QTime.currentTime())
		self.timeModified.setTime(QTime.currentTime())
		self.timeAccessed.setTime(QTime.currentTime())
	
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
		
		t = datetime.datetime.now().strftime('%H:%M:%S')
		self.wcLabel.setText(t)
		
		# ~ if not self.lineFileName.text():
			# ~ self.dateAccessed.setDate(QDate.currentDate())
			# ~ self.timeAccessed.setTime(QTime.currentTime())
	
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
				if len(self.listRecentFiles) >= self.qtyListRecentFiles:
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
			self.btnRestoreFileTimes.setEnabled(True)
			self.appendOriginalFileTimeAction.setEnabled(False)
			self.removeOriginalFileTimeAction.setEnabled(True)
			
			self.copyFileNameAction.setEnabled(True)
			self.cutFileNameAction.setEnabled(True)
			self.clearFileNameAction.setEnabled(True)
	
	def openRecentFile(self, fileName):
		if not fileName == 'Vacío':
			self.lineFileName.setText(fileName)
			self.updateTimes(fileName)
			pos = self.listRecentFiles.index(fileName)
			self.listRecentFiles.pop(pos)
			self.listRecentFiles.append(fileName)
			self.originalFileTimeCheck()
			
			self.copyFileNameAction.setEnabled(True)
			self.cutFileNameAction.setEnabled(True)
			self.clearFileNameAction.setEnabled(True)
	
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
		if os.path.isfile(text) and not text.endswith(':FTC'):
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
		self.saveAction.setEnabled(False)
		
		self.datetimeCreatedOriginal.setEnabled(False)
		self.datetimeModifiedOriginal.setEnabled(False)
		self.datetimeAccessedOriginal.setEnabled(False)
		self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
		self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
		self.datetimeAccessedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
		self.btnRemoveFileTimes.setEnabled(False)
		self.btnRestoreFileTimes.setEnabled(False)
		self.appendOriginalFileTimeAction.setEnabled(False)
		self.removeOriginalFileTimeAction.setEnabled(False)
		
		self.copyFileNameAction.setEnabled(False)
		self.cutFileNameAction.setEnabled(False)
		self.clearFileNameAction.setEnabled(False)
		
		# ~ self.dateCreated.setDate(QDate.currentDate())
		# ~ self.dateModified.setDate(QDate.currentDate())
		# ~ self.dateAccessed.setDate(QDate.currentDate())
		# ~ self.timeCreated.setTime(QTime.currentTime())
		# ~ self.timeModified.setTime(QTime.currentTime())
		# ~ self.timeAccessed.setTime(QTime.currentTime())
		self.updateTimesWithCurrentDateTime()
	
	def updateMenuCheckFile(self):
		isMovable = not self.fileToolBar.isMovable()
		self.fileToolBar.setMovable(isMovable)
		if isMovable:
			 self.checkToolBarFileAction.setIcon(QIcon('icons/check-true.png'))
		else:
			 self.checkToolBarFileAction.setIcon(QIcon('icons/check-false.png'))
	
	def updateMenuCheckEdit(self):
		isMovable = not self.editToolBar.isMovable()
		self.editToolBar.setMovable(isMovable)
		if isMovable:
			 self.checkToolBarEditAction.setIcon(QIcon('icons/check-true.png'))
		else:
			 self.checkToolBarEditAction.setIcon(QIcon('icons/check-false.png'))
	
	def updateMenuCheckFileShowNames(self):
		btnStyle = self.fileToolBar.toolButtonStyle()
		if btnStyle == Qt.ToolButtonTextUnderIcon:
			self.checkToolBarFileShowNamesAction.setIcon(QIcon('icons/check-false.png'))
			self.fileToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
		else:
			self.checkToolBarFileShowNamesAction.setIcon(QIcon('icons/check-true.png'))
			self.fileToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
	
	def updateMenuCheckEditShowNames(self):
		btnStyle = self.editToolBar.toolButtonStyle()
		if btnStyle == Qt.ToolButtonTextUnderIcon:
			self.checkToolBarEditShowNamesAction.setIcon(QIcon('icons/check-false.png'))
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
		else:
			self.checkToolBarEditShowNamesAction.setIcon(QIcon('icons/check-true.png'))
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
	
	def xyzzy(self):
		self.statusbar.showMessage('No pasó nada.', 3000)
	
	#===================================================================
	# Functions
	
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
	
	#===================================================================
	#===================================================================
	#===================================================================



if __name__ == '__main__':
	app = QApplication(sys.argv)
	win = Window()
	win.show()
	sys.exit(app.exec_())
	
	# Pendientes:
	
	# Agregar lista de archivos con datos almacenados
	# Agregar opción de ver lista de archivos con datos almacenados
	# Agregar opción de eliminar archivos de datos desde la lista
	
	# Agregar la lista en archivo :FTC al propio código







