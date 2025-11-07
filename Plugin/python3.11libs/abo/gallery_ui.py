from hutil.PySide import QtWidgets, QtCore, QtGui
import math, tarfile, os, hou, webbrowser 
import abo.db as db

class Window(QtWidgets.QWidget):

	def __init__(self, parent=None):
		super(Window, self).__init__(parent)
		
		# config variables
		self.grid_cols = 6
		self.thumb_size = 128
		self.models_archive_path = hou.text.expandString('$ABO_MODEL_ARCHIVE')

		# init 
		self.grid_widgets = []
		self.orig_pixmaps = []
		self.page=1
		
		self._setupUI()

	def wheelEvent(self, event: QtGui.QWheelEvent):
		incr = 2
		if event.modifiers() == QtCore.Qt.ControlModifier:
			if event.angleDelta().y() > 0:
				self.icon_size.setValue(self.icon_size.value()+incr)
			else:
				self.icon_size.setValue(self.icon_size.value()-incr)
			event.accept()
		else:
			super().wheelEvent(event)

	def resizeEvent(self, event: QtGui.QResizeEvent):
		container_size = event.size()
		self.resize_images(container_size, self.icon_size.value())
		
	def resize_images(self, container_size, icon_mult=10):
		for i, widget in enumerate(self.grid_widgets):
			pixmap = self.orig_pixmaps[i]
			scaled_pixmap = pixmap.scaled((container_size*0.9)/self.grid_cols*(icon_mult/10), QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
			widget.setPixmap(scaled_pixmap)

	def get_model_tooltip_html(self, data):
		fields = [
			'item_id', 'item_name', 'product_type', 'item_shape', 'color',
			'brand', 'bullet_point', 'fabric_type', 'finish_type', 
			'material', 'model_name', 'style', 'item_keywords',
		]
		html = '<table>'
		for f in fields:
			v = data[f]
			v = v.replace('\n', '<br/>')
			truncate_chars = 200
			v_clamp = v[0:truncate_chars]
			if len(v)>truncate_chars: v_clamp+='... [truncated]'
			if f == 'color': 
				color_code = data['color_code']
				html += f'<tr><td bgcolor="grey" align="right" width="35%"><font color="white">{f} &nbsp;</font></td><td valign="top" bgcolor="#474747"><table cellpadding=0 cellspacing=0><tr><td valign="top">&nbsp;{v_clamp}&nbsp;</td><td></td><td bgcolor="{color_code}" width="20"></td></table></td></tr>'
			else:
				html += f'<tr><td bgcolor="grey" align="right" width="35%"><font color="white">{f} &nbsp;</font></td><td bgcolor="#474747">&nbsp;{v_clamp}</td></tr>'
		html += '</table>'

		return html

	def thumb_context_menu(self, pos, caller, data):
		context_menu = QtWidgets.QMenu(self)

		action_import_model = context_menu.addAction('Import 3d model')
		action_import_model.triggered.connect(lambda checked=False, data=data: self.load_3d_model(checked, data))

		action_view_high_res_img = context_menu.addAction('View high-res image')
		action_view_high_res_img.triggered.connect(lambda checked=False, data=data: self.view_highres_img(checked, data))
		
		context_menu.exec_(caller.mapToGlobal(pos)) 

	def view_highres_img(self, checked, data):	
		res = 1024
		image = f'{data["main_image_id"]}._US{res}_.jpg'
		url = f'https://m.media-amazon.com/images/I/{image}'
		webbrowser.open(url)

	def load_3d_model(self, checked, data):

		# extract file from archive
		archive = self.models_archive_path
		file_to_extract = f'3dmodels/original/{data["model_path"]}'
		extraction_path = hou.text.expandString('$HIP/geo/ABO')
		destination_file = f'{extraction_path}/{file_to_extract}'
		if not os.path.isfile(destination_file):
			os.makedirs(extraction_path, exist_ok=True)
			with tarfile.open(archive, 'r') as tar:
				tar.extract(file_to_extract, path=extraction_path)

		# import (SOP)
		obj = hou.node('/obj')
		gltf = obj.createNode('gltf_hierarchy', f'abo_{data["model_id"]}')
		gltf.parm('filename').set(f'$HIP/geo/ABO/{file_to_extract}')
		gltf.parm('assetfolder').set(f'$HIP/geo/ABO/{file_to_extract}'.replace('.glb', ''))
		gltf.parm('buildscene').pressButton()
		gltf.moveToGoodPosition()		

		# status message
		hou.ui.setStatusMessage(f'Model {data["model_id"]} was loaded!', hou.severityType.Message)		

	def build_grid(self):
		
		# clear widgets
		for item in self.grid_widgets:
			item.deleteLater()

		# get search term
		where = self.searchbar.text().strip()

		# image thumbnails
		self.grid_cols = int(self.size().width()/(self.thumb_size*1.1))
		records_per_page = math.ceil(self.size().height()/(self.thumb_size*1.1)) * self.grid_cols
		records = db.get_all(where=where, records_per_page=records_per_page, page=self.page)
		self.grid_widgets = []
		self.orig_pixmaps = []
		for i, item in enumerate(records):
			
			image_file = db.get_or_download_image(item['main_image_id'], image_res=self.thumb_size)
			image = QtGui.QImage()
			image.load(image_file)
			image_label = QtWidgets.QLabel()
			pixmap = QtGui.QPixmap(image)
			image_label.setPixmap(pixmap.scaled(self.thumb_size, pixmap.height(), QtCore.Qt.KeepAspectRatio))
			image_label.setToolTip(self.get_model_tooltip_html(item))
			image_label.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
			image_label.customContextMenuRequested.connect(lambda pos, caller=image_label, data=item: self.thumb_context_menu(pos, caller, data))
			self.grid_widgets.append(image_label)
			self.orig_pixmaps.append(pixmap)
		
			row = math.floor(i/self.grid_cols)
			col = i%self.grid_cols
			self.grid_layout.addWidget(image_label, row, col, QtCore.Qt.AlignCenter)

		# responsive thumbs
		self.resize_images(self.size(), self.icon_size.value())

		# set status message
		num_items = len(self.grid_widgets)
		item_start = ((self.page-1)*num_items)+1
		item_end = item_start + num_items - 1
		self.status.setText(f'Displaying items: {item_start} to {item_end}.   ')
		if num_items == 0 :
			self.status.setText(f'No items found.   ')

	def page_up(self):
		page = int(self.page_cur.text())+1
		if page > 9999: page=9999
		self.page_cur.setText(str(page))

	def page_down(self):
		page = int(self.page_cur.text())-1
		if page < 1: page=1
		self.page_cur.setText(str(page))

	def page_change(self):
		page = int(self.page_cur.text())
		self.page = page
		self.build_grid()

	def page_reset(self):
		self.page = 1
		self.page_cur.setText(str(self.page))

	def color_code_field_search(self):
		if ':' in self.searchbar.text():
			self.searchbar.setStyleSheet('color: #a2dbfa;')
		else:
			self.searchbar.setStyleSheet('')

	def get_searchbar_tooltip(self):
		html = 'Type to search in all fields.<br/><br/>To search in a specific field, use the syntax <b>field_name: value</b> (The search bar will turn blue, indicating this is a unique field search)<br/><br/>Hover any image thumbnail to access field names.'
		return html

	def _setupUI(self):

		# main layout
		main_layout = QtWidgets.QVBoxLayout()
		self.setLayout(main_layout)

		# search bar / pagination
		searchbar_layout = QtWidgets.QHBoxLayout()
		searchbar_label = QtWidgets.QLabel('Search:')
		self.searchbar = QtWidgets.QLineEdit()		
		self.searchbar.textChanged.connect(self.build_grid)
		self.searchbar.textChanged.connect(self.page_reset)
		self.searchbar.textChanged.connect(self.color_code_field_search)
		self.searchbar.setToolTip(self.get_searchbar_tooltip())
		searchbar_layout.addWidget(searchbar_label)
		searchbar_layout.addWidget(self.searchbar)
		clear_icon = hou.qt.Icon('BUTTONS_delete_mini') 
		clear_button = QtWidgets.QPushButton()
		clear_button.setIcon(clear_icon)
		clear_button.setStyleSheet('QPushButton {border: none;}')
		clear_button.setFixedWidth(20)
		clear_button.setToolTip('Clear search')
		clear_button.clicked.connect(lambda: self.searchbar.setText(''))
		clear_button.clicked.connect(lambda: self.searchbar.setFocus())
		searchbar_layout.addWidget(clear_button)
		searchbar_layout.addItem(QtWidgets.QSpacerItem(10, 1))
		self.pag_prev = QtWidgets.QPushButton('<')
		self.pag_prev.clicked.connect(self.page_down)
		self.pag_next = QtWidgets.QPushButton('>')
		self.pag_next.clicked.connect(self.page_up)
		searchbar_layout.addWidget(QtWidgets.QLabel('   page: '))
		searchbar_layout.addWidget(self.pag_prev)
		self.page_cur = QtWidgets.QLineEdit('1')
		self.page_cur.setFixedWidth(50)
		self.page_cur.setAlignment(QtCore.Qt.AlignCenter)
		only_int = QtGui.QIntValidator()
		only_int.setRange(1, 9999)
		self.page_cur.setValidator(only_int)
		self.page_cur.textChanged.connect(self.page_change)
		searchbar_layout.addWidget(self.page_cur)
		searchbar_layout.addWidget(self.pag_next)
		main_layout.addLayout(searchbar_layout)
		main_layout.addSpacing(5)

		# scroll area
		scroll_area = QtWidgets.QScrollArea()
		scroll_area.setWidgetResizable(True)
		scroll_widget = QtWidgets.QWidget()
		scroll_widget.setContentsMargins(0,0,0,0)
		scroll_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.grid_layout = QtWidgets.QGridLayout()
		self.grid_layout.setContentsMargins(0,0,0,0)
		self.grid_layout.setSpacing(2)
		scroll_widget.setLayout(self.grid_layout)
		scroll_area.setWidget(scroll_widget)

		# scrollbar stylesheet
		self.setStyleSheet('''
			QScrollBar::handle:vertical {
				background: gray; 
			}
		''')
		
		main_layout.addWidget(scroll_area)

		# thumbnail size slider 		
		bottom_layout = QtWidgets.QHBoxLayout()
		self.icon_size = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.icon_size.setFixedWidth(100)
		self.icon_size.setMinimum(5)
		self.icon_size.setMaximum(40)
		self.icon_size.setValue(10)
		self.icon_size.valueChanged.connect(lambda value, container_size=self.size(): self.resize_images(container_size, value))
		self.icon_size.setToolTip('Move slider or use "Ctrl + MouseWheel" to increase/decrease thumbnail sizes')
		bottom_layout.addWidget(QtWidgets.QLabel('Thumb size: '))	
		bottom_layout.addWidget(self.icon_size)	
		bottom_layout.addStretch()

		# status message
		self.status = QtWidgets.QLabel()
		self.status.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
		bottom_layout.addWidget(self.status)	
		main_layout.addLayout(bottom_layout)	

		# build image grid
		# (uses a timer, so the window gets evaluated before painting the image grid
		# this way we can get the correct widget size to calc number of columns that best fit the window)
		QtCore.QTimer.singleShot(100, self.build_grid)



		
