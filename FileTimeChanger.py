
# Tested in: Python 3.8.8 - Windows
# By: LawlietJH
# FileTimeChanger v1.1.0

from PyQt5.QtCore import (
	Qt, QDate, QTime, QUrl,
	QTimer, QDateTime
)
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QGridLayout,
	QWidget, QLabel, QLineEdit, QPushButton,
	QDateEdit, QTimeEdit, QDateTimeEdit,
	QFileDialog, QCheckBox, QMenu, QToolBar,
	QAction, QWidgetAction, QDesktopWidget
)
from PyQt5.QtGui import (
	QIcon, QKeySequence,
	QDesktopServices
)

from functools import partial
from ctypes import windll, wintypes, byref
import win32clipboard as WCB
import binascii
import datetime
import atexit
import base64
import json
import time
import bz2
import sys
import os

#=======================================================================

__author__  = 'LawlietJH'				# Desarrollador
__title__   = 'FileTimeChanger'			# Titulo
__appname__ = 'File Time Changer'		# Nombre
__version__ = 'v1.1.0'					# Versión

#=======================================================================
#=======================================================================
#=======================================================================
# Material de Apoyo: https://realpython.com/python-menus-toolbars/

class Window(QMainWindow):
	
	def __init__(self, parent=None):
		
		super().__init__(parent)
		self.Clipboard = self.Clipboard()
		
		#-----------------------------------------------------------
		# Read the config file if it exists:
		self.filenameConfigFile = 'FileTimeChanger_Config.ftc'
		self.filenameConfigFile = f'{os.environ["TEMP"]}\\'+self.filenameConfigFile
		self.configs = {
			'window': {
				'pos': {
					'x': 'Center',
					'y': 'Center'
				},
				'width':  '740',
				'height': '400',
				'default': {
					'width':  '740',
					'height': '400'
				}
			},
			'checkToolBarFile': {
				'FloatingAction':  'True',
				'ShowNamesAction': 'True',
				'VisibleAction':   'True',
				'FloatingActionEnabled':  'True',
				'ShowNamesActionEnabled': 'True',
			},
			'checkToolBarEdit': {
				'FloatingAction':  'True',
				'ShowNamesAction': 'True',
				'VisibleAction':   'True',
				'FloatingActionEnabled':  'True',
				'ShowNamesActionEnabled': 'True',
			}
		}
		try:
			if os.path.isfile(self.filenameConfigFile):
				with open(self.filenameConfigFile, 'r') as f:
					self.configs = json.loads(f.read())
		except:
			pass
		#-----------------------------------------------------------
		
		self._createWindow()
		self._createGrid()
		self._createActions()
		self._createMenuBar()
		self._createToolBars()
		self._connectActions()
		self._createStatusBar()
	
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
	
	def moveEvent(self, event):		# QMoveEvent
		self.configs['window']['pos']['x'] = str(event.pos().x())
		self.configs['window']['pos']['y'] = str(event.pos().y())
	
	def resizeEvent(self, event):	# QResizeEvent
		self.configs['window']['width']  = str(event.size().width())
		self.configs['window']['height'] = str(event.size().height())
	
	#===================================================================
	#===================================================================
	#===================================================================
	# GUI
	
	def _createWindow(self):
		
		self.setWindowTitle(f'{__appname__} {__version__} - By: {__author__}')
		self.setWindowIcon(QIcon('icons/icon.png'))
		
		self.defaultSize = (
			eval(self.configs['window']['default']['width']),
			eval(self.configs['window']['default']['height'])
		)
		size = (
			eval(self.configs['window']['width']),
			eval(self.configs['window']['height'])
		)
		
		if not 'Center' in [self.configs['window']['pos']['x'], self.configs['window']['pos']['y']]:
			self.move(
				eval(self.configs['window']['pos']['x']),
				eval(self.configs['window']['pos']['y'])
			)
		else: self.centerTheWindow()
		
		# ~ self.setFixedSize(*size)
		self.resize(*size)
		self.setMaximumWidth( size[0]+size[0]//4)
		self.setMaximumHeight(size[1]+size[1]//4)
		
		#-----------------------------------------------------------
		# Read Recent Files from Temp File:
		self.qtyListRecentFiles = 7
		self.filenameRecentFiles = f'{os.environ["TEMP"]}\\FileTimeChanger_RecentFiles.ftc'
		self.listRecentFiles = ['Vacío']
		try:
			if os.path.isfile(self.filenameRecentFiles):
				with open(self.filenameRecentFiles, 'r') as f:
					self.listRecentFiles = json.loads(f.read())
		except:
			pass
		#-----------------------------------------------------------
		
		self.urlHelpContent = QUrl('https://github.com/LawlietJH/FileTimeChanger')
		self.urlAbout = QUrl('https://github.com/LawlietJH')
		
		self.toolbarFileIsVisible = eval(self.configs['checkToolBarFile']['VisibleAction'])
		self.toolbarEditIsVisible = eval(self.configs['checkToolBarEdit']['VisibleAction'])
		
		#-----------------------------------------------------------
		self.encode = lambda data: base64.urlsafe_b64encode(data.encode()).decode()
		self.decode = lambda data: base64.urlsafe_b64decode(data.encode()).decode()
		self.originalFileTime = {}
		#-----------------------------------------------------------
		
		# Convierte de Unix timestamp a Windows FileTime
		# Documentación: https://support.microsoft.com/en-us/help/167296
		self.toTimestamp = lambda epoch: int((epoch * 10000000) + 116444736000000000)
		self.toFileTime  = lambda epoch: byref(wintypes.FILETIME(self.toTimestamp(epoch) & 0xFFFFFFFF, self.toTimestamp(epoch) >> 32))
		self.timeToDate  = lambda time: datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
		self.dateToTime  = lambda date: time.mktime(date.timetuple())
		self.strToDate   = lambda date_time_str: datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
	
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
		self.lineFileName = QLineEdit()
		self.lineFileName.setReadOnly(True)
		self.lineFileName.setPlaceholderText('Cargar Archivo...')
		self.lineFileName.setFocusPolicy(Qt.NoFocus)
		
		# Pos: 0, 5
		self.btnOpenFile = QPushButton(
			QIcon('icons/find.png'),
			'Cargar Archivo...'
		)
		# ~ self.btnOpenFile.hide()
		# ~ self.btnOpenFile.show()
		
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
		self.labelCreatedOriginal = QLabel('Created (Original):')
		self.labelCreatedOriginal.setEnabled(False)
		# ~ self.labelCreatedOriginal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		
		# Pos: 1, 5
		self.datetimeCreatedOriginal = QDateTimeEdit()
		self.datetimeCreatedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeCreatedOriginal.setButtonSymbols(2)	# No Buttons
		self.datetimeCreatedOriginal.setReadOnly(True)
		self.datetimeCreatedOriginal.setEnabled(False)
		self.datetimeCreatedOriginal.setFocusPolicy(Qt.NoFocus)
		# ~ self.datetimeCreatedOriginal.setVisible(False)
		
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
		self.labelModifiedOriginal = QLabel('Modified (Original):')
		self.labelModifiedOriginal.setEnabled(False)
		
		# Pos: 2, 5
		self.datetimeModifiedOriginal = QDateTimeEdit()
		self.datetimeModifiedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeModifiedOriginal.setButtonSymbols(2)	# No Buttons
		self.datetimeModifiedOriginal.setReadOnly(True)
		self.datetimeModifiedOriginal.setEnabled(False)
		self.datetimeModifiedOriginal.setFocusPolicy(Qt.NoFocus)
		
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
		self.labelAccessedOriginal = QLabel('Accessed (Original):')
		self.labelAccessedOriginal.setEnabled(False)
		
		# Pos: 3, 5
		self.datetimeAccessedOriginal = QDateTimeEdit()
		self.datetimeAccessedOriginal.setDisplayFormat('hh:mm:ss dd/MM/yyyy')
		self.datetimeAccessedOriginal.setButtonSymbols(2)	# No Buttons
		self.datetimeAccessedOriginal.setReadOnly(True)
		self.datetimeAccessedOriginal.setEnabled(False)
		self.datetimeAccessedOriginal.setFocusPolicy(Qt.NoFocus)
		
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
		
		# Pos: 5, 1
		self.btnRestoreCurrentFileTimes = QPushButton(
			QIcon('icons/restore.png'),
			'Restaurar'
			)
		self.btnRestoreCurrentFileTimes.setEnabled(False)
		self.btnRestoreCurrentFileTimes.setToolTip(
			'Restaura los tiempos del archivo\n'
			'con los datos actuales.'
		)
		
		# Pos: 5, 2
		self.btnRestoreFileTimes = QPushButton(
			QIcon('icons/reload.png'),
			'Restaurar Orig.'
			)
		self.btnRestoreFileTimes.setEnabled(False)
		self.btnRestoreFileTimes.setToolTip(
			'Restaura los tiempos del archivo\n'
			'con los datos originales.'
		)
		
		#---------------------------------------------------------------
		
		# ~ self.grid.setRowStretch(6, 1)
		
		self.grid.setColumnStretch(0, 0)
		self.grid.setColumnStretch(1, 1)
		self.grid.setColumnStretch(2, 1)
		self.grid.setColumnStretch(3, 1)
		self.grid.setColumnStretch(4, 1)
		self.grid.setColumnStretch(5, 2)
		
		# Add Widgets
		self.grid.addWidget(labelOpenFile,           0, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.lineFileName,       0, 1, 1, 4)
		self.grid.addWidget(self.btnOpenFile,        0, 5)
		self.grid.addWidget(labelCreated,            1, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeCreated,        1, 1)
		self.grid.addWidget(self.dateCreated,        1, 2)
		self.grid.addWidget(labelModified,           2, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeModified,       2, 1)
		self.grid.addWidget(self.dateModified,       2, 2)
		self.grid.addWidget(labelAccessed,           3, 0, alignment=Qt.AlignRight)
		self.grid.addWidget(self.timeAccessed,       3, 1)
		self.grid.addWidget(self.dateAccessed,       3, 2)
		
		self.grid.addWidget(self.btnLoadCurrentTime,         4, 1)
		self.grid.addWidget(self.btnUpFileTimes,             4, 2)
		self.grid.addWidget(self.btnRestoreCurrentFileTimes, 5, 1)
		self.grid.addWidget(self.btnRestoreFileTimes,        5, 2)
		
		self.grid.addWidget(self.labelCreatedOriginal,     1, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeCreatedOriginal,  1, 5)
		self.grid.addWidget(self.labelModifiedOriginal,    2, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeModifiedOriginal, 2, 5)
		self.grid.addWidget(self.labelAccessedOriginal,    3, 4, alignment=Qt.AlignRight)
		self.grid.addWidget(self.datetimeAccessedOriginal, 3, 5)
		self.grid.addWidget(self.btnRemoveFileTimes,       4, 5)
	
	def _createActions(self):
		#===============================================================
		# 'File' Actions
		# Creating action using the first constructor
		# ~ self.newAction = QAction(self)
		# ~ self.newAction.setText('&New')
		# ~ self.newAction.setIcon(QIcon('icons/new.png'))
		# Creating actions using the second constructor
		self.openAction = QAction(QIcon('icons/open.png'), '&Open...', self)
		self.updateWindowAction = QAction(QIcon('icons/restore.png'), '&Restore', self, enabled=False)
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
		self.checkToolBarFileFloatingAction  = QAction(QIcon(f'icons/check-{self.configs["checkToolBarFile"]["FloatingAction"]}.png'),  '&Floating',   self)# checkable=True, checked=True)
		self.checkToolBarFileShowNamesAction = QAction(QIcon(f'icons/check-{self.configs["checkToolBarFile"]["ShowNamesAction"]}.png'), '&Show Names', self)
		self.checkToolBarFileVisibleAction   = QAction(QIcon(f'icons/check-{self.configs["checkToolBarFile"]["VisibleAction"]}.png'),   '&Visible',    self)
		self.checkToolBarEditFloatingAction  = QAction(QIcon(f'icons/check-{self.configs["checkToolBarEdit"]["FloatingAction"]}.png'),  '&Floating',   self)
		self.checkToolBarEditShowNamesAction = QAction(QIcon(f'icons/check-{self.configs["checkToolBarEdit"]["ShowNamesAction"]}.png'), '&Show Names', self)
		self.checkToolBarEditVisibleAction   = QAction(QIcon(f'icons/check-{self.configs["checkToolBarEdit"]["VisibleAction"]}.png'),   '&Visible',    self)
		#===============================================================
		# Window actions
		self.resizeSmallAction   = QAction(QIcon('icons/mark.png'), '&Small', self)
		self.resizeMediumAction  = QAction(QIcon('icons/mark.png'), '&Medium', self)
		self.resizeDefaultAction = QAction(QIcon('icons/mark.png'), '&Default', self)
		self.resizeLargeAction   = QAction(QIcon('icons/mark.png'), '&Large', self)
		self.resizeExtraLargeAction = QAction(QIcon('icons/mark.png'), '&Extra Large', self)
		self.centerTheWindowAction = QAction(QIcon('icons/center.png'), '&Center', self)
		# ~ self.fixedSizeAction     = QAction(QIcon(f'icons/check-{self.configs["window"]["fixed"]}.png'), '&Fixed', self)
		#---------------------------------------------------------------
		# Adding 'Window' Tips
		self.resizeSmallAction.setStatusTip('670x267')
		self.resizeMediumAction.setStatusTip('720x360')
		self.resizeDefaultAction.setStatusTip('740x400')
		self.resizeLargeAction.setStatusTip('770x450')
		self.resizeExtraLargeAction.setStatusTip('800x500')
		self.centerTheWindowAction.setStatusTip('Centra la ventana en la pantalla')
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
		checkToolBarFileMenu = checkMenu.addMenu('&File Toolbar')
		checkToolBarFileMenu.setIcon(QIcon('icons/mark.png'))
		checkToolBarEditMenu = checkMenu.addMenu('&Edit Toolbar')
		checkToolBarEditMenu.setIcon(QIcon('icons/mark.png'))
		checkToolBarFileMenu.addAction(self.checkToolBarFileFloatingAction)
		checkToolBarFileMenu.addAction(self.checkToolBarFileShowNamesAction)
		checkToolBarFileMenu.addAction(self.checkToolBarFileVisibleAction)
		checkToolBarEditMenu.addAction(self.checkToolBarEditFloatingAction)
		checkToolBarEditMenu.addAction(self.checkToolBarEditShowNamesAction)
		checkToolBarEditMenu.addAction(self.checkToolBarEditVisibleAction)
		#===============================================================
		# Window menu
		windowMenu = menuBar.addMenu('&Window')
		windowResizeMenu = windowMenu.addMenu(QIcon('icons/resize.png'), '&Resize')
		windowResizeMenu.addAction(self.resizeSmallAction)
		windowResizeMenu.addAction(self.resizeMediumAction)
		windowResizeMenu.addAction(self.resizeDefaultAction)
		windowResizeMenu.addAction(self.resizeLargeAction)
		windowResizeMenu.addAction(self.resizeExtraLargeAction)
		windowMenu.addSeparator()
		windowMenu.addAction(self.centerTheWindowAction)
		#===============================================================
		# Help menu
		helpMenu = menuBar.addMenu(QIcon('icons/help.png'), '&Help')
		helpMenu.addAction(self.helpContentAction)
		helpMenu.addAction(self.aboutAction)
	
	def _createToolBars(self):
		
		self.editToolBar = QToolBar('Edit', self)
		self.addToolBar(Qt.TopToolBarArea, self.editToolBar)
		if eval(self.configs['checkToolBarEdit']['ShowNamesAction']):
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		else:
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
		self.editToolBar.addAction(self.copyFileNameAction)
		self.editToolBar.addAction(self.pasteFileNameAction)
		self.editToolBar.addAction(self.cutFileNameAction)
		self.editToolBar.addSeparator()
		self.editToolBar.addAction(self.clearFileNameAction)
		self.editToolBar.setMovable(eval(self.configs['checkToolBarEdit']['FloatingAction']))
		if eval(self.configs['checkToolBarEdit']['VisibleAction']):
			self.editToolBar.show()
		else:
			self.editToolBar.hide()
		
		self.fileToolBar = QToolBar('File', self)
		self.addToolBar(Qt.TopToolBarArea, self.fileToolBar)
		if eval(self.configs['checkToolBarFile']['ShowNamesAction']):
			self.fileToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		else:
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
		
		enabledF = eval(self.configs['checkToolBarEdit']['FloatingActionEnabled'])
		enabledSN = eval(self.configs['checkToolBarEdit']['ShowNamesActionEnabled'])
		self.checkToolBarEditFloatingAction.setEnabled(enabledF)
		self.checkToolBarEditShowNamesAction.setEnabled(enabledSN)
		
		#---------------------------------------------------------------
		
		self.fileToolBar.addAction(self.openAction)
		self.fileToolBar.addAction(self.updateWindowAction)
		self.fileToolBar.addAction(self.saveAction)
		self.fileToolBar.addSeparator()
		self.fileToolBar.addAction(self.appendOriginalFileTimeAction)
		self.fileToolBar.addAction(self.removeOriginalFileTimeAction)
		self.fileToolBar.addSeparator()
		self.fileToolBar.addAction(self.exitAction)
		self.fileToolBar.setMovable(eval(self.configs['checkToolBarFile']['FloatingAction']))
		if eval(self.configs['checkToolBarFile']['VisibleAction']):
			self.fileToolBar.show()
		else:
			self.fileToolBar.hide()
		
		enabledF = eval(self.configs['checkToolBarFile']['FloatingActionEnabled'])
		enabledSN = eval(self.configs['checkToolBarFile']['ShowNamesActionEnabled'])
		self.checkToolBarFileFloatingAction.setEnabled(enabledF)
		self.checkToolBarFileShowNamesAction.setEnabled(enabledSN)
	
	def _connectActions(self):
		
		# Connect File actions:
		self.openAction.triggered.connect(self.openFile)
		self.openRecentMenu.aboutToShow.connect(self.populateOpenRecent)
		self.updateWindowAction.triggered.connect(self.updateTimesWithCurrentFileTime)
		self.saveAction.triggered.connect(self.updateFileTimes)
		self.appendOriginalFileTimeAction.triggered.connect(self.addOriginalFileTimesAgain)
		self.removeOriginalFileTimeAction.triggered.connect(self.removeOriginalFileTime)
		self.exitAction.triggered.connect(self.close)
		
		# Connect Edit actions:
		self.copyFileNameAction.triggered.connect(self.copyContent)
		self.pasteFileNameAction.triggered.connect(self.pasteContent)
		self.cutFileNameAction.triggered.connect(self.cutContent)
		self.clearFileNameAction.triggered.connect(self.clearLineFileName)
		
		# Connect Check actions:
		self.checkToolBarFileFloatingAction.triggered.connect(self.updateMenuCheckFile)
		self.checkToolBarEditFloatingAction.triggered.connect(self.updateMenuCheckEdit)
		self.checkToolBarFileShowNamesAction.triggered.connect(self.updateMenuCheckFileShowNames)
		self.checkToolBarEditShowNamesAction.triggered.connect(self.updateMenuCheckEditShowNames)
		self.checkToolBarFileVisibleAction.triggered.connect(self.updateMenuCheckFileVisible)
		self.checkToolBarEditVisibleAction.triggered.connect(self.updateMenuCheckEditVisible)
		
		# Connect Window Actions:
		self.resizeSmallAction.triggered.connect(lambda: self.resize(670, 267))
		self.resizeMediumAction.triggered.connect(lambda: self.resize(720, 360))
		self.resizeLargeAction.triggered.connect(lambda: self.resize(770, 450))
		self.resizeExtraLargeAction.triggered.connect(lambda: self.resize(800, 500))
		self.resizeDefaultAction.triggered.connect(lambda: self.resize(
			eval(self.configs['window']['default']['width']),
			eval(self.configs['window']['default']['height'])
		))
		self.centerTheWindowAction.triggered.connect(self.centerTheWindow)
		
		# Connect Help Actions:
		self.helpContentAction.triggered.connect(lambda: QDesktopServices.openUrl(self.urlHelpContent))
		self.aboutAction.triggered.connect(lambda: QDesktopServices.openUrl(self.urlAbout))
		
		# Buttons:
		self.btnOpenFile.clicked.connect(self.openFile)
		self.btnLoadCurrentTime.clicked.connect(self.updateTimesWithCurrentDateTime)
		self.btnUpFileTimes.clicked.connect(self.updateFileTimes)
		self.btnRestoreCurrentFileTimes.clicked.connect(self.updateTimesWithCurrentFileTime)
		self.btnRestoreFileTimes.clicked.connect(self.restoreOriginalFileTime)
		self.btnRemoveFileTimes.clicked.connect(self.removeOriginalFileTime)
		
		# Date and Time Edits:
		self.dateCreated.dateChanged.connect(self.chkFileTimeChanges)
		self.timeCreated.timeChanged.connect(self.chkFileTimeChanges)
		self.dateModified.dateChanged.connect(self.chkFileTimeChanges)
		self.timeModified.timeChanged.connect(self.chkFileTimeChanges)
		self.dateAccessed.dateChanged.connect(self.chkFileTimeChanges)
		self.timeAccessed.timeChanged.connect(self.chkFileTimeChanges)
		
		# Clock:
		self.timer = QTimer()
		self.timer.timeout.connect(self.updateClock)
		self.timer.start(1000)
	
	def _createStatusBar(self):
		self.statusbar = self.statusBar()
		# ~ self.statusbar.setSizeGripEnabled(False)		# Quita el icono de escalado
		self.statusbar.showMessage('Ready', 3000)			# Agrega un texto durante 3 segundos
		curtime = datetime.datetime.now().strftime('%H:%M:%S')
		self.labelClock = QLabel(curtime+'  ')
		self.statusbar.addPermanentWidget(self.labelClock)	# Agrega un texto permanente
	
	#===================================================================
	# FileTime Checks
	
	def isThereAFTCFile(self):
		fileName = self.lineFileName.text()
		if not fileName: return False
		return os.path.isfile(fileName+':FTC') 
	
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
		timeAc = datetime.time(timeAc.hour, timeAc.minute, timeAc.second)
		
		#--------------------------------------------------------------
		# Comparamos que los tiempos no hayan sido cambiados
		
		dateC = dateCf == dateCc
		dateM = dateMf == dateMc
		dateA = dateAf == dateAc
		timeC = timeCf == timeCc
		timeM = timeMf == timeMc
		timeA = timeAf == timeAc
		
		sameDate = dateC and dateM and dateA
		sameTime = timeC and timeM and timeA
		
		# Será True si la fecha y hora no han sido modificadas en los campos
		return sameDate and sameTime
	
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
		
		return same
	
	def updateFileTimes(self):
		
		fileName = self.lineFileName.text()
		
		if not os.path.isfile(fileName):
			self.statusbar.showMessage('No se ha cargado ningun archivo', 3000)
			return
		
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
		
		self.changeFileTimes(fileName, [ctime, atime, mtime])			# Modifica los Tiempos del Archivo
		
		self.updateOriginalTimes()		# Actualiza los campos con los tiempos originales
		
		self.statusbar.showMessage('Actualizado', 3000)
		
		self.btnUpFileTimes.setEnabled(False)
		self.btnRestoreCurrentFileTimes.setEnabled(False)
		
		if self.isThereAFTCFile() and self.originalFileTime:
			same = self.compareOriginalTimes()
			self.btnRestoreFileTimes.setEnabled(not same)
			self.btnRemoveFileTimes.setEnabled(True)
			self.appendOriginalFileTimeAction.setEnabled(False)
			self.removeOriginalFileTimeAction.setEnabled(True)
		else:
			self.btnRestoreFileTimes.setEnabled(False)
			self.btnRemoveFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(True)
			self.removeOriginalFileTimeAction.setEnabled(False)
		
		self.saveAction.setEnabled(False)
		self.updateWindowAction.setEnabled(False)
	
	def restoreOriginalFileTime(self):
		
		fileName = self.lineFileName.text()
		
		if not os.path.isfile(fileName):
			self.statusbar.showMessage('No se ha cargado ningun archivo', 3000)
			return
		
		dateC = self.datetimeCreatedOriginal.date().toPyDate()
		dateM = self.datetimeModifiedOriginal.date().toPyDate()
		dateA = self.datetimeAccessedOriginal.date().toPyDate()
		
		timeC = self.datetimeCreatedOriginal.time().toPyTime()
		timeM = self.datetimeModifiedOriginal.time().toPyTime()
		timeA = self.datetimeAccessedOriginal.time().toPyTime()
		
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
		
		self.changeFileTimes(fileName, [ctime, atime, mtime])			# Modifica los Tiempos del Archivo
		
		self.updateTimes(fileName)		# Actualiza los campos con los datos actuales del archivo
		self.updateOriginalTimes()		# Actualiza los campos con los tiempos originales
		
		self.statusbar.showMessage('Actualizado', 3000)
		
		self.btnUpFileTimes.setEnabled(False)
		self.btnRestoreCurrentFileTimes.setEnabled(False)
		
		if self.isThereAFTCFile() and self.originalFileTime:
			same = self.compareOriginalTimes()
			self.btnRestoreFileTimes.setEnabled(not same)
			self.btnRemoveFileTimes.setEnabled(True)
			self.appendOriginalFileTimeAction.setEnabled(False)
			self.removeOriginalFileTimeAction.setEnabled(True)
		else:
			self.btnRestoreFileTimes.setEnabled(False)
			self.btnRemoveFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(True)
			self.removeOriginalFileTimeAction.setEnabled(False)
		
		self.saveAction.setEnabled(False)
		self.updateWindowAction.setEnabled(False)
	
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
	
	#===================================================================
	# FileTime Controllers
	
	def addOriginalFileTimesAgain(self):
		
		self.btnRestoreFileTimes.setEnabled(False)
		self.btnRemoveFileTimes.setEnabled(True)
		self.appendOriginalFileTimeAction.setEnabled(False)
		self.removeOriginalFileTimeAction.setEnabled(True)
		
		self.addOriginalFileTimes()		# Agrega un respaldo con los tiempos originales
		self.updateOriginalTimes()		# Actualiza los campos de tiempos originales
		self.updateFileTimes()			# Se cambian los tiempos del archivo por los de los campos con los datos actuales (Porque al abrir el archvio se modifican los tiempos, esto los restaura)
	
	def addOriginalFileTimes(self):
		
		fileName = self.lineFileName.text()
		if not os.path.isfile(fileName):
			return
		
		timeCraw, timeMraw, timeAraw = self.getFileTimes(fileName)
		
		fileTimes = {
			'Created':  self.timeToDate(timeCraw),
			'Modified': self.timeToDate(timeMraw),
			'Accessed': self.timeToDate(timeAraw)
		}
		
		self.originalFileTime = fileTimes
		
		jsonFileTimes = json.dumps(fileTimes, indent=4).encode()
		jsonFileTimes = bz2.compress(jsonFileTimes)
		
		with open(fileName+':FTC', 'wb') as f:
			f.write(jsonFileTimes)
	
	def extractOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName):
			return
		
		if not os.path.isfile(fileName+':FTC'): return
		
		try: # Extraer datos añadidos del archivo
			with open(fileName+':FTC', 'rb') as f:
				data = bz2.decompress(f.read()).decode()
				jsonContent = json.loads(data)
		except:
			jsonContent = {}
		
		return jsonContent
	
	def removeOriginalFileTime(self, fileName=None):
		
		if not fileName: fileName = self.lineFileName.text()
		if not os.path.isfile(fileName): return
		
		if os.path.isfile(fileName+':FTC'):
			
			os.remove(fileName+':FTC')
			
			self.originalFileTime = {}
			self.updateOriginalTimes()
			
			self.btnRestoreFileTimes.setEnabled(False)
			self.btnRemoveFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(True)
			self.removeOriginalFileTimeAction.setEnabled(False)
	
	#===================================================================
	# Action Functions
	
	def copyContent(self):
		text = self.lineFileName.text()
		if text:
			self.Clipboard.text = text
			self.statusbar.showMessage('Ruta de archivo copiada', 3000)
		else:
			self.statusbar.showMessage('No hay nada que copiar', 3000)
	
	def pasteContent(self):
		text = self.Clipboard.text
		if os.path.isfile(text) and not text.endswith(':FTC'):
			if not text == self.lineFileName.text():
				self.openFile(text)
				self.statusbar.showMessage('Ruta de Archivo pegada', 3000)
			else:
				self.statusbar.showMessage('El archivo ya esta cargado', 3000)
		else:
			self.statusbar.showMessage('El texto copiado no es ruta de un archivo existente', 3000)
	
	def cutContent(self):
		text = self.lineFileName.text()
		if text:
			self.Clipboard.text = text
			self.clearLineFileName()
			self.statusbar.showMessage('Ruta de Archivo cortada', 3000)
		else:
			self.statusbar.showMessage('No hay nada que copiar', 3000)
	
	def clearLineFileName(self):
		
		self.lineFileName.setText('')
		
		self.originalFileTime = {}
		self.updateOriginalTimes()
		
		self.btnUpFileTimes.setEnabled(False)
		self.btnRestoreCurrentFileTimes.setEnabled(False)
		self.btnRestoreFileTimes.setEnabled(False)
		self.btnRemoveFileTimes.setEnabled(False)
		
		self.saveAction.setEnabled(False)
		self.updateWindowAction.setEnabled(False)
		self.appendOriginalFileTimeAction.setEnabled(False)
		self.removeOriginalFileTimeAction.setEnabled(False)
		
		self.copyFileNameAction.setEnabled(False)
		self.cutFileNameAction.setEnabled(False)
		self.clearFileNameAction.setEnabled(False)
		
		self.updateTimesWithCurrentDateTime()
	
	#-------------------------------------------------------------------
	
	def cleanRecentFiles(self):
		self.openRecentMenu.clear()
		if self.lineFileName.text():
			self.listRecentFiles = [self.lineFileName.text()]
			#-----------------------------------------------------------
			# Write Recent Files in Temp File:
			with open(self.filenameRecentFiles, 'w') as f:
				jsonContent = json.dumps(self.listRecentFiles, indent=4)
				f.write(jsonContent)
			#-----------------------------------------------------------
		else:
			self.listRecentFiles = ['Vacío']
			os.remove(self.filenameRecentFiles)
	
	def chkFileTimeChanges(self):
		
		same = self.compareTimes()
		
		if same == None: return
		
		self.btnUpFileTimes.setEnabled(not same)
		self.btnRestoreCurrentFileTimes.setEnabled(not same)
		
		self.saveAction.setEnabled(not same)
		self.updateWindowAction.setEnabled(not same)
	
	def openFile(self, fileName=None):
		
		if not fileName:
			options  = QFileDialog.Options()
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
		
		if not os.path.isfile(fileName):
			return
		
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
			
			#-----------------------------------------------------------
			# Write Recent Files in Temp File:
			with open(self.filenameRecentFiles, 'w') as f:
				jsonContent = json.dumps(self.listRecentFiles, indent=4)
				f.write(jsonContent)
			#-----------------------------------------------------------
			
			# Actualiza los tiempos en los campos
			# Current, Modified y Accessed en la ventana.
			self.updateTimes(fileName)
			
			# Si no existe el archivo con los tiempos originales lo crea
			if not self.isThereAFTCFile():
				self.addOriginalFileTimes()
			else:
				# Si existe el archivo de tiempos originales, extrae su contenido
				jsonContent = self.extractOriginalFileTime(fileName)
				self.originalFileTime = jsonContent
			
			self.updateOriginalTimes()		# Actualiza los campos de tiempos originales
			self.updateFileTimes()			# Se cambian los tiempos del archivo por los de los campos con los datos actuales (Porque al abrir el archvio se modifican los tiempos, esto los restaura)
			
			self.btnUpFileTimes.setEnabled(False)
			self.btnRestoreCurrentFileTimes.setEnabled(False)
			
			if self.isThereAFTCFile() and self.originalFileTime:
				same = self.compareOriginalTimes()
				self.btnRestoreFileTimes.setEnabled(not same)
				self.btnRemoveFileTimes.setEnabled(True)
				self.appendOriginalFileTimeAction.setEnabled(False)
				self.removeOriginalFileTimeAction.setEnabled(True)
			else:
				self.btnRestoreFileTimes.setEnabled(False)
				self.btnRemoveFileTimes.setEnabled(False)
				self.appendOriginalFileTimeAction.setEnabled(True)
				self.removeOriginalFileTimeAction.setEnabled(False)
			
			self.saveAction.setEnabled(False)
			self.updateWindowAction.setEnabled(False)
			
			self.copyFileNameAction.setEnabled(True)
			self.cutFileNameAction.setEnabled(True)
			self.clearFileNameAction.setEnabled(True)
	
	def populateOpenRecent(self):
		
		self.openRecentMenu.clear()		# Step 1. Remove the old options from the menu
		actions = []					# Step 2. Dynamically create the actions
		
		for filename in self.listRecentFiles[::-1]:
			
			if filename == 'Vacío':
				icon = QIcon('icons/icon.png')
				name = '... Xyzzy'
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
				con = lambda: self.statusbar.showMessage('No pasó nada', 3000)
			elif filename == self.lineFileName.text():
				actionTip = f'El archivo {repr(path[-1])} ya esta abierto...'
				con = partial(self.openFile, filename)
				action.setEnabled(False)
			else:
				actionTip = 'Carga el archivo '+repr(path[-1])
				con = partial(self.openFile, filename)
			
			action.setStatusTip(actionTip)		# Agrega un mensaje a la barra de estatus
			action.setToolTip(actionTip)		# Modifica el mensaje de ayuda que aparece encima
			action.triggered.connect(con)
			actions.append(action)
		
		self.openRecentMenu.addActions(actions)	# Step 3. Add the actions to the menu
		
		if not self.listRecentFiles == ['Vacío']:
			
			self.openRecentMenu.addSeparator()
			action = QAction(QIcon('icons/delete.png'), 'Limpiar historial...', self)
			actionTip = 'Limpia el historial de archivos recientes'
			action.setStatusTip(actionTip)
			action.setToolTip(actionTip)
			action.triggered.connect(self.cleanRecentFiles)
			self.openRecentMenu.addAction(action)
	
	def updateClock(self):
		curtime = datetime.datetime.now().strftime('%H:%M:%S')
		self.labelClock.setText(curtime+'  ')
	
	def updateOriginalTimes(self):
		
		def setEnabled(value):
			self.labelCreatedOriginal.setEnabled(value)
			self.labelModifiedOriginal.setEnabled(value)
			self.labelAccessedOriginal.setEnabled(value)
			self.datetimeCreatedOriginal.setEnabled(value)
			self.datetimeModifiedOriginal.setEnabled(value)
			self.datetimeAccessedOriginal.setEnabled(value)
			
		
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
				setEnabled(True)
			else:
				setEnabled(False)
		else:
			setEnabled(False)
			self.datetimeCreatedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeModifiedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
			self.datetimeAccessedOriginal.setDateTime(QDateTime(2000, 1, 1, 0, 0, 0))
	
	def updateTimesWithCurrentDateTime(self):
		
		self.dateCreated.setDate(QDate.currentDate())
		self.dateModified.setDate(QDate.currentDate())
		self.dateAccessed.setDate(QDate.currentDate())
		
		self.timeCreated.setTime(QTime.currentTime())
		self.timeModified.setTime(QTime.currentTime())
		self.timeAccessed.setTime(QTime.currentTime())
	
	def updateTimesWithCurrentFileTime(self):
		
		fileName = self.lineFileName.text()
		
		if not os.path.isfile(fileName): return
		
		self.updateTimes(fileName)
		
		self.btnUpFileTimes.setEnabled(False)
		self.btnRestoreCurrentFileTimes.setEnabled(False)
		
		if self.isThereAFTCFile() and self.originalFileTime:
			same = self.compareOriginalTimes()
			self.btnRestoreFileTimes.setEnabled(not same)
			self.btnRemoveFileTimes.setEnabled(True)
			self.appendOriginalFileTimeAction.setEnabled(False)
			self.removeOriginalFileTimeAction.setEnabled(True)
		else:
			self.btnRestoreFileTimes.setEnabled(False)
			self.btnRemoveFileTimes.setEnabled(False)
			self.appendOriginalFileTimeAction.setEnabled(True)
			self.removeOriginalFileTimeAction.setEnabled(False)
		
		self.saveAction.setEnabled(False)
		self.updateWindowAction.setEnabled(False)
	
	#===================================================================
	# Checks
	
	def updateMenuCheckFile(self):
		
		isMovable = not self.fileToolBar.isMovable()
		self.configs['checkToolBarFile']['FloatingAction'] = str(isMovable)
		self.fileToolBar.setMovable(isMovable)
		
		isMovable = str(isMovable).lower()
		self.checkToolBarFileFloatingAction.setIcon(QIcon(f'icons/check-{isMovable}.png'))
	
	def updateMenuCheckEdit(self):
		
		isMovable = not self.editToolBar.isMovable()
		self.configs['checkToolBarEdit']['FloatingAction'] = str(isMovable)
		self.editToolBar.setMovable(isMovable)
		
		isMovable = str(isMovable).lower()
		self.checkToolBarEditFloatingAction.setIcon(QIcon(f'icons/check-{isMovable}.png'))
	
	def updateMenuCheckFileShowNames(self):
		btnStyle = self.fileToolBar.toolButtonStyle()
		if btnStyle == Qt.ToolButtonTextUnderIcon:
			self.checkToolBarFileShowNamesAction.setIcon(QIcon('icons/check-false.png'))
			self.fileToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
			self.configs['checkToolBarFile']['ShowNamesAction'] = 'False'
		else:
			self.checkToolBarFileShowNamesAction.setIcon(QIcon('icons/check-true.png'))
			self.fileToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
			self.configs['checkToolBarFile']['ShowNamesAction'] = 'True'
	
	def updateMenuCheckEditShowNames(self):
		btnStyle = self.editToolBar.toolButtonStyle()
		if btnStyle == Qt.ToolButtonTextUnderIcon:
			self.checkToolBarEditShowNamesAction.setIcon(QIcon('icons/check-false.png'))
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonIconOnly)
			self.configs['checkToolBarEdit']['ShowNamesAction'] = 'False'
		else:
			self.checkToolBarEditShowNamesAction.setIcon(QIcon('icons/check-true.png'))
			self.editToolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
			self.configs['checkToolBarEdit']['ShowNamesAction'] = 'True'
	
	def updateMenuCheckFileVisible(self):
		
		self.toolbarFileIsVisible = not self.toolbarFileIsVisible
		self.configs['checkToolBarFile']['VisibleAction'] = str(self.toolbarFileIsVisible)
		visible = str(self.toolbarFileIsVisible).lower()
		self.checkToolBarFileVisibleAction.setIcon(QIcon(f'icons/check-{visible}.png'))
		
		if self.toolbarFileIsVisible:
			self.fileToolBar.show()
			self.configs['checkToolBarFile']['FloatingActionEnabled'] = 'True'
			self.configs['checkToolBarFile']['ShowNamesActionEnabled'] = 'True'
		else:
			self.fileToolBar.hide()
			self.configs['checkToolBarFile']['FloatingActionEnabled'] = 'False'
			self.configs['checkToolBarFile']['ShowNamesActionEnabled'] = 'False'
		
		enabledF = eval(self.configs['checkToolBarFile']['FloatingActionEnabled'])
		enabledSN = eval(self.configs['checkToolBarFile']['ShowNamesActionEnabled'])
		self.checkToolBarFileFloatingAction.setEnabled(enabledF)
		self.checkToolBarFileShowNamesAction.setEnabled(enabledSN)
	
	def updateMenuCheckEditVisible(self):
		
		self.toolbarEditIsVisible = not self.toolbarEditIsVisible
		self.configs['checkToolBarEdit']['VisibleAction'] = str(self.toolbarEditIsVisible)
		visible = str(self.toolbarEditIsVisible).lower()
		self.checkToolBarEditVisibleAction.setIcon(QIcon(f'icons/check-{visible}.png'))
		
		if self.toolbarEditIsVisible:
			self.editToolBar.show()
			self.configs['checkToolBarEdit']['FloatingActionEnabled'] = 'True'
			self.configs['checkToolBarEdit']['ShowNamesActionEnabled'] = 'True'
		else:
			self.editToolBar.hide()
			self.configs['checkToolBarEdit']['FloatingActionEnabled'] = 'False'
			self.configs['checkToolBarEdit']['ShowNamesActionEnabled'] = 'False'
		
		enabledF = eval(self.configs['checkToolBarEdit']['FloatingActionEnabled'])
		enabledSN = eval(self.configs['checkToolBarEdit']['ShowNamesActionEnabled'])
		self.checkToolBarEditFloatingAction.setEnabled(enabledF)
		self.checkToolBarEditShowNamesAction.setEnabled(enabledSN)
	
	#===================================================================
	# Functions
	
	def changeFileTimes(self, filePath: str, values):
		# Llamada al Win32 API para modificar los tiempos del archivo
		handle = windll.kernel32.CreateFileW(filePath, 256, 0, None, 3, 128, None)
		windll.kernel32.SetFileTime(handle, *values)
		windll.kernel32.CloseHandle(handle)
	
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
	
	def centerTheWindow(self):
		width   = QDesktopWidget().screenGeometry().width()
		height  = QDesktopWidget().screenGeometry().height()
		windowW = eval(self.configs['window']['width'])
		windowH = eval(self.configs['window']['height'])
		x = width //2-int(windowW//2)
		y = height//2-int(windowH//1.52)
		self.move(x, y)
	
	#===================================================================
	#===================================================================
	#===================================================================



@atexit.register
def close():
	try:
		#-----------------------------------------------------------
		# Write Recent Files in Temp File:
		with open(win.filenameConfigFile, 'w') as f:
			jsonContent = json.dumps(win.configs, indent=4)
			print('"configs":', jsonContent)
			f.write(jsonContent)
		#-----------------------------------------------------------
	except:
		pass



if __name__ == '__main__':
	
	app = QApplication(sys.argv)
	win = Window()
	win.show()
	sys.exit(app.exec_())




