import output_ovf as oo
import calc_field as cf
import get_icon as gi

try:
    import footer_widget as fw
    footer_available = True
except ImportError:
    footer_available = False

import sys
import os
import math
import json
import ctypes

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton, QFileDialog, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QDialog, QProgressBar, QTabWidget, QTabBar, QFrame)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

BACKGROUND_COLOR = "#f0f0f0"
FONT_FAMILY = "Arial"
LABEL_COLOR = "#333"
BORDER_COLOR = "#ccc"
BUTTON_COLOR = "#191970"
BUTTON_HOVER_COLOR = "#0000cd"
GROUP_BOX_BORDER_COLOR = "#3B4252"
COMBO_BOX_BG_COLOR = "#f8f8f8"
COMBO_BOX_SELECTION_COLOR = "#f00000"
BUTTON_FONT_COLOR = "white"
CLOSE_BUTTON_HOVER = "#E6E6E6"
CLOSE_BUTTON_FONT_COLOR = "black"
FOOTER_FONT_COLOR = "#666"

def decimal_normalize(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value

def add_si_prefix(value, unit):
    prefixes = {
        -24: 'y', -21: 'z', -18: 'a', -15: 'f', -12: 'p', -9: 'n', -6: 'µ', -3: 'm',
        0: '', 3: 'k', 6: 'M', 9: 'G', 12: 'T', 15: 'P', 18: 'E', 21: 'Z', 24: 'Y'
    }
    
    if value == 0:
        return f"{value}{unit}"
    
    exponent = int('{:.0e}'.format(value).split('e')[1])
    si_exponent = 3 * (exponent // 3)
    
    if si_exponent not in prefixes:
        return f"{value} {unit}"
    
    new_value = value / (10 ** si_exponent)
    si_prefix = prefixes[si_exponent]
    
    return f"{decimal_normalize(round(new_value, 3))}{si_prefix}{unit}"

def get_windows_display_scale():
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi / 96.0 * 0.9

class PlusTabBar(QTabBar):
    plusClicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        scale_factor = get_windows_display_scale()
        tab_padding_x = f"{int(8 * scale_factor)}px"
        tab_padding_y = f"{int(9 * scale_factor)}px"
        border_radius = f"{int(8 * scale_factor)}px"
        margin_small = f"{int(3 * scale_factor)}px"
        margin_large = f"{int(2 * scale_factor)}px"

        # Create the plus button
        self.plus_button = QPushButton("+")
        self.plus_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {BUTTON_FONT_COLOR};
                padding: {tab_padding_x} {tab_padding_y};
                border: none;
                border-radius: {border_radius};
                font-weight: bold;
                margin-right: {margin_small};
                margin-left: {margin_large};
                margin-top: {margin_large};
                margin-bottom: {margin_large};
            }}
            QPushButton:hover {{
                background-color: {BUTTON_HOVER_COLOR};
            }}
        """)

        # self.plus_button.setFixedSize(25, 25)
        self.plus_button.clicked.connect(self.plusClicked)
        
        self.setDrawBase(False)
        self.setExpanding(False)


class CheckWindow(QDialog):
    def __init__(self, image_paths, seved_path, append_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Check Plot')
        scale_factor = get_windows_display_scale()
        self.setGeometry(int(200 * scale_factor), int(200 * scale_factor), int(1100 * scale_factor), int(420 * scale_factor))
        
        layout = QVBoxLayout()
        
        # Image display
        self.image_label = QLabel()
        layout.addWidget(self.image_label)
        
        # Slider and buttons layout
        slider_layout = QHBoxLayout()
        
        # Decrease z button
        self.decrease_button = QPushButton("-")
        self.decrease_button.clicked.connect(self.decrease_z)
        slider_layout.addWidget(self.decrease_button)
        
        # Slider for z-value
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(image_paths) - 1)
        self.slider.valueChanged.connect(lambda: (self.update_plot(img_scale_factor), self.update_name(append_str)))
        slider_layout.addWidget(self.slider)
        
        # Increase z button
        self.increase_button = QPushButton("+")
        self.increase_button.clicked.connect(self.increase_z)
        slider_layout.addWidget(self.increase_button)
        
        layout.addLayout(slider_layout)
        
        # Save path and button
        save_layout = QVBoxLayout()
        
        # Path and browse button
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Path:"))
        self.save_path = QLineEdit(seved_path)
        path_layout.addWidget(self.save_path)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.browse_button)
        save_layout.addLayout(path_layout)
        
        # Filename and extension
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Output Filename:"))
        self.save_filename = QLineEdit()
        file_layout.addWidget(self.save_filename)
        self.save_extension = QComboBox()
        self.save_extension.addItem(".png")
        file_layout.addWidget(self.save_extension)
        save_layout.addLayout(file_layout)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_plot)
        save_layout.addWidget(self.save_button)
        
        layout.addLayout(save_layout)
        
        self.setLayout(layout)
        
        self.image_paths = image_paths
        img_scale_factor = scale_factor * 0.6
        self.update_plot(img_scale_factor)
        self.update_name(append_str)
    
    def browse_save_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.save_path.setText(dir_path)
    
    def update_name(self, append_str):
        z = self.slider.value()
        self.save_filename.setText(f"PumpedField_{append_str}_z{str(z)}")

    def update_plot(self, scale_factor):
        z = self.slider.value()
        pixmap = QPixmap(self.image_paths[z])
        scaled_pixmap = pixmap.scaled(int(pixmap.width() * scale_factor), int(pixmap.height() * scale_factor), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setScaledContents(True)
    
    def decrease_z(self):
        new_value = max(self.slider.value() - 1, self.slider.minimum())
        self.slider.setValue(new_value)
    
    def increase_z(self):
        new_value = min(self.slider.value() + 1, self.slider.maximum())
        self.slider.setValue(new_value)
    
    def save_plot(self):
        path = self.save_path.text()
        filename = self.save_filename.text()
        extension = self.save_extension.currentText()
        if path and filename:
            full_path = os.path.join(path, filename + extension)
            current_image = self.image_paths[self.slider.value()]
            pixmap = QPixmap(current_image)
            pixmap.save(full_path)
            print(f"Plot saved to {full_path}")

    def closeEvent(self, event):
        for path in self.image_paths:
            try:
                os.remove(path)
            except:
                pass
        super().closeEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        scale_factor = get_windows_display_scale()
        width = int(650 * scale_factor)
        height = int(880 * scale_factor)
        # self.setFixedSize(width, height)
        self.setWindowTitle('Microtrip Antenna Magnetic Field Calculator')

        # Define size variables
        font_size = f"{int(14 * scale_factor)}px"
        padding_small = f"{int(5 * scale_factor)}px"
        padding_medium = f"{int(8 * scale_factor)}px"
        padding_large = f"{int(16 * scale_factor)}px"
        border_radius = f"{int(3 * scale_factor)}px"
        border_radius_large = f"{int(4 * scale_factor)}px"
        group_box_padding = f"{int(17 * scale_factor)}px 0 {int(2 * scale_factor)}px 0"
        tab_width = f"{int(120 * scale_factor)}px"
        tab_height = f"{int(30 * scale_factor)}px"
        footer_font_size = f"{int(12 * scale_factor)}px"
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BACKGROUND_COLOR};
                font-family: {FONT_FAMILY};
                font-size: {font_size};
            }}
            QLabel {{
                color: {LABEL_COLOR};
            }}
            QLineEdit, QComboBox {{
                padding: {padding_small};
                border: 1px solid {BORDER_COLOR};
                border-radius: {border_radius};
            }}
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {BUTTON_FONT_COLOR};
                padding: {padding_medium} {padding_large};
                border: none;
                border-radius: {border_radius_large};
            }}
            QPushButton:hover {{
                background-color: {BUTTON_HOVER_COLOR};
            }}
            QGroupBox {{
                border: 1px solid;
                border-color: {GROUP_BOX_BORDER_COLOR};
                border-radius: {border_radius_large};
                padding: {group_box_padding};
                font-weight: bold;
                font-size: 15px;
            }}
            QGroupBox::title {{
                color: black;
                background: transparent;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: {padding_small} 0 0 0;
            }}
            QComboBox {{
                background-color: {COMBO_BOX_BG_COLOR};
                selection-background-color: {COMBO_BOX_SELECTION_COLOR}
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QListView {{
                background-color : {COMBO_BOX_BG_COLOR};
            }}
            QTabBar::tab {{
                width: {tab_width};
                height: {tab_height};
            }}
        """)

        main_layout = QVBoxLayout()

        # Grid settings
        grid_group = QGroupBox("Grid Size")
        grid_layout = QGridLayout()
        grid_group.setLayout(grid_layout)

        self.n_x = QLineEdit("500")
        self.n_y = QLineEdit("50")
        self.n_z = QLineEdit("5")
        grid_layout.addWidget(QLabel("<i>N<sub>x</sub></i> :"), 0, 0)
        grid_layout.addWidget(self.n_x, 0, 1)
        grid_layout.addWidget(QLabel("<i>N<sub>y</sub></i> :"), 0, 2)
        grid_layout.addWidget(self.n_y, 0, 3)
        grid_layout.addWidget(QLabel("<i>N<sub>z</sub></i> :"), 0, 4)
        grid_layout.addWidget(self.n_z, 0, 5)

        self.size_x = QLineEdit("5e-5")
        self.size_y = QLineEdit("5e-6")
        self.size_z = QLineEdit("5e-8")
        grid_layout.addWidget(QLabel("Size<i><sub>x</sub></i> (m) :"), 1, 0)
        grid_layout.addWidget(self.size_x, 1, 1)
        grid_layout.addWidget(QLabel("Size<i><sub>y</sub></i> (m) :"), 1, 2)
        grid_layout.addWidget(self.size_y, 1, 3)
        grid_layout.addWidget(QLabel("Size<i><sub>z</sub></i> (m) :"), 1, 4)
        grid_layout.addWidget(self.size_z, 1, 5)

        self.size_cell_x = QLineEdit()
        self.size_cell_y = QLineEdit()
        self.size_cell_z = QLineEdit()
        grid_layout.addWidget(QLabel("CellSize<i><sub>x</sub></i> (m) :"), 2, 0)
        grid_layout.addWidget(self.size_cell_x, 2, 1)
        grid_layout.addWidget(QLabel("CellSize<i><sub>y</sub></i> (m) :"), 2, 2)
        grid_layout.addWidget(self.size_cell_y, 2, 3)
        grid_layout.addWidget(QLabel("CellSize<i><sub>z</sub></i> (m) :"), 2, 4)
        grid_layout.addWidget(self.size_cell_z, 2, 5)

        # Connect signals for automatic updates
        self.n_x.editingFinished.connect(lambda: (self.update_sizes('x', 'n'), self.update_append_text()))
        self.n_y.editingFinished.connect(lambda: (self.update_sizes('y', 'n'), self.update_append_text()))
        self.n_z.editingFinished.connect(lambda: (self.update_sizes('z', 'n'), self.update_append_text()))
        self.size_x.editingFinished.connect(lambda: (self.update_sizes('x', 'size'), self.update_append_text()))
        self.size_y.editingFinished.connect(lambda: (self.update_sizes('y', 'size'), self.update_append_text()))
        self.size_z.editingFinished.connect(lambda: (self.update_sizes('z', 'size'), self.update_append_text()))
        self.size_cell_x.editingFinished.connect(lambda: (self.update_sizes('x', 'cell'), self.update_append_text()))
        self.size_cell_y.editingFinished.connect(lambda: (self.update_sizes('y', 'cell'), self.update_append_text()))
        self.size_cell_z.editingFinished.connect(lambda: (self.update_sizes('z', 'cell'), self.update_append_text()))

        # Initial calculation of cell sizes
        self.update_sizes('x', 'n')
        self.update_sizes('y', 'n')
        self.update_sizes('z', 'n')

        main_layout.addWidget(grid_group)

        # Antenna Widget
        antenna_widget = QWidget()
        antenna_layout = QVBoxLayout()
        antenna_widget.setLayout(antenna_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        antenna_layout.addWidget(self.tab_widget)

        self.puls_tab_bar = PlusTabBar()
        self.tab_widget.setCornerWidget(self.puls_tab_bar.plus_button, Qt.TopRightCorner)
        self.puls_tab_bar.plusClicked.connect(self.add_antenna_tab)

        main_layout.addWidget(antenna_widget)

        # Conditions settings
        cond_group = QGroupBox("Conditions")
        cond_layout = QGridLayout()
        cond_group.setLayout(cond_layout)

        self.save_conditions = QCheckBox("Save conditions at calculation.")
        self.save_conditions.setChecked(True)
        self.save_button = QPushButton("Save", clicked=self.save_current_conditions)
        self.load_button = QPushButton("Load", clicked=self.load_conditions)

        cond_layout.addWidget(self.save_conditions, 0, 0)
        cond_layout.addWidget(self.save_button, 0, 1)
        cond_layout.addWidget(self.load_button, 0, 2)

        main_layout.addWidget(cond_group)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)

        self.dir_str = QLineEdit(os.getcwd())
        self.output_filename = QLineEdit("antenna")
        self.output_extension = QComboBox()
        self.output_extension.addItem(".ovf")
        # self.output_extension.addItem(".txt")
        self.append_filename = QLineEdit()
        
        output_layout.addWidget(QLabel("Path:"), 0, 0)
        output_layout.addWidget(self.dir_str, 0, 1)
        output_layout.addWidget(QPushButton("Browse", clicked=self.browse_dir), 0, 2)
        output_layout.addWidget(QLabel("Output Filename:"), 1, 0)
        output_layout.addWidget(self.output_filename, 1, 1, 1, 2)
        output_layout.addWidget(QLabel("Append Filename:"), 2, 0)
        output_layout.addWidget(self.append_filename, 2, 1)
        output_layout.addWidget(self.output_extension, 2, 2)

        main_layout.addWidget(output_group)

        # self.append_filename.editingFinished.connect(lambda: self.update_append_text())
        self.update_append_text()

        # Add check and calculate buttons in a horizontal layout
        button_layout = QHBoxLayout()
        self.check_button = QPushButton("Check", clicked=self.open_check_window)
        button_layout.addWidget(self.check_button)
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(lambda: self.calculate(False))
        button_layout.addWidget(self.calculate_button)
        main_layout.addLayout(button_layout)

        # Add the progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        if footer_available:
            footer_widget = fw.create_footer_widget(FOOTER_FONT_COLOR, footer_font_size, BACKGROUND_COLOR, scale_factor)
            main_layout.addWidget(footer_widget)

        self.setLayout(main_layout)

        # Initial antenna tab
        self.add_antenna_tab()

    def create_antenna_widget(self):
        widget = QWidget()
        layout = QGridLayout()
        widget.setLayout(layout)

        # Antenna Settings group
        ant_group = QGroupBox("Antenna Settings")
        ant_layout = QGridLayout()
        ant_group.setLayout(ant_layout)

        ant_width = QLineEdit("5e-6")
        ant_width.setObjectName("ant_width")
        ant_thickness = QLineEdit("100e-9")
        ant_thickness.setObjectName("ant_thickness")
        ant_layout.addWidget(QLabel("Width (m) :"), 0, 0)
        ant_layout.addWidget(ant_width, 0, 1)
        ant_layout.addWidget(QLabel("Thickness (m) :"), 0, 2)
        ant_layout.addWidget(ant_thickness, 0, 3)

        ant_position_x = QLineEdit("2.5e-5")
        ant_position_x.setObjectName("ant_position_x")
        ant_position_y = QLineEdit("2.5e-6")
        ant_position_y.setObjectName("ant_position_y")
        ant_layout.addWidget(QLabel("x (m) :"), 1, 0)
        ant_layout.addWidget(ant_position_x, 1, 1)
        ant_layout.addWidget(QLabel("y (m) :"), 1, 2)
        ant_layout.addWidget(ant_position_y, 1, 3)

        distance = QLineEdit("1e-12")
        distance.setObjectName("distance")
        ant_layout.addWidget(QLabel("Distance between antenna and sample (m) :"), 2, 0, 1, 2)
        ant_layout.addWidget(distance, 2, 2, 1, 2)

        current_direction = QLineEdit("90")
        current_direction.setObjectName("current_direction")
        ant_layout.addWidget(QLabel("Current direction (degree) :"), 3, 0, 1, 2)
        ant_layout.addWidget(current_direction, 3, 2, 1, 2)

        layout.addWidget(ant_group)

        # Input Current group
        input_group = QGroupBox("Input Current")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)

        input_current = QLineEdit()
        input_current.setObjectName("input_current")
        input_voltage = QLineEdit("5")
        input_voltage.setObjectName("input_voltage")
        input_power_dBm = QLineEdit()
        input_power_dBm.setObjectName("input_power_dBm")
        input_power_W = QLineEdit()
        input_power_W.setObjectName("input_power_W")
        impedance = QLineEdit("50")
        impedance.setObjectName("impedance")
        input_layout.addWidget(QLabel("Current (A) :"), 0, 0)
        input_layout.addWidget(input_current, 0, 1)
        input_layout.addWidget(QLabel("Peak Voltage (V) :"), 0, 2)
        input_layout.addWidget(input_voltage, 0, 3)
        input_layout.addWidget(QLabel("Power (dBm) :"), 1, 0)
        input_layout.addWidget(input_power_dBm, 1, 1)
        input_layout.addWidget(QLabel("Power (W) :"), 1, 2)
        input_layout.addWidget(input_power_W, 1, 3)
        input_layout.addWidget(QLabel("Impedance (Ω) :"), 2, 0)
        input_layout.addWidget(impedance, 2, 1)

        waveform = QComboBox()
        waveform.setObjectName("waveform")
        waveform.addItem("Sin wave")
        waveform.addItem("Square wave")
        input_layout.addWidget(QLabel("Waveform :"), 2, 2)
        input_layout.addWidget(waveform, 2, 3)

        layout.addWidget(input_group)

        input_current.editingFinished.connect(lambda: (self.update_tab_inputs('current'), self.update_append_text()))
        input_voltage.editingFinished.connect(lambda: (self.update_tab_inputs('voltage'), self.update_append_text()))
        input_power_dBm.editingFinished.connect(lambda: (self.update_tab_inputs('power_dBm'), self.update_append_text()))
        input_power_W.editingFinished.connect(lambda: (self.update_tab_inputs('power_W'), self.update_append_text()))
        impedance.editingFinished.connect(lambda: (self.update_tab_inputs('impedance'), self.update_append_text()))
        waveform.currentIndexChanged.connect(lambda: (self.update_tab_inputs('waveform'), self.update_append_text()))

        return widget

    def add_antenna_tab(self):
        new_tab = self.create_antenna_widget()
        tab_index = self.tab_widget.addTab(new_tab, f"Antenna {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(tab_index)
        self.add_close_button(tab_index)
        self.update_tab_inputs('voltage')
        self.update_append_text()

    def add_close_button(self, index):
        close_button = QPushButton("✖")
        scale_factor = get_windows_display_scale()
        close_button_padding = f"{int(2 * scale_factor)}px {int(2 * scale_factor)}px"
        close_button_redius = f"{int(8 * scale_factor)}px"
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                color: {CLOSE_BUTTON_FONT_COLOR}; 
                padding: {close_button_padding};
                border: none;
                border-radius: {close_button_redius};
            }}
            QPushButton:hover {{
                background-color: {CLOSE_BUTTON_HOVER};
            }}""")
        close_button.clicked.connect(lambda: self.close_tab(self.sender()))
        self.tab_widget.tabBar().setTabButton(index, QTabBar.RightSide, close_button)

    def close_tab(self, button):
        index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabBar().tabButton(i, QTabBar.RightSide) == button:
                index = i
                break
        
        if index != -1 and self.tab_widget.count() > 1:  # Keep at least one antenna tab
            self.tab_widget.removeTab(index)
            self.update_tab_names()
        
        self.update_append_text()

    def update_tab_names(self):
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabText(i, f"Antenna {i + 1}")


    def update_sizes(self, dimension, changed_field):
        try:
            if dimension == 'x':
                n = float(self.n_x.text())
                size = float(self.size_x.text())
                cell_size = float(self.size_cell_x.text()) if self.size_cell_x.text() else 0
            elif dimension == 'y':
                n = float(self.n_y.text())
                size = float(self.size_y.text())
                cell_size = float(self.size_cell_y.text()) if self.size_cell_y.text() else 0
            elif dimension == 'z':
                n = float(self.n_z.text())
                size = float(self.size_z.text())
                cell_size = float(self.size_cell_z.text()) if self.size_cell_z.text() else 0

            if changed_field == 'n':
                cell_size = size / n
            elif changed_field == 'size':
                cell_size = size / n
            elif changed_field == 'cell':
                size = cell_size * n

            if dimension == 'x':
                self.size_cell_x.setText(f"{cell_size:.6e}")
                self.size_x.setText(f"{size:.6e}")
            elif dimension == 'y':
                self.size_cell_y.setText(f"{cell_size:.6e}")
                self.size_y.setText(f"{size:.6e}")
            elif dimension == 'z':
                self.size_cell_z.setText(f"{cell_size:.6e}")
                self.size_z.setText(f"{size:.6e}")

        except ValueError:
            pass
    
    def update_inputs(self, changed_field, input_current, input_voltage, input_power_dBm, input_power_W, impedance, waveform):
        try:
            current = float(input_current.text()) if input_current.text() else 0
            voltage = float(input_voltage.text()) if input_voltage.text() else 0
            power_dBm = float(input_power_dBm.text()) if input_power_dBm.text() else 0
            power_W = float(input_power_W.text()) if input_power_W.text() else 0
            impedance_value = float(impedance.text()) if impedance.text() else 50
            waveform_text = waveform.currentText()

            if waveform_text == "Sin wave":
                if changed_field == 'current':
                    voltage = current * impedance_value
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance_value * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance_value
                elif changed_field == 'voltage':
                    voltage_rms = voltage / math.sqrt(2)
                    current = voltage / impedance_value
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance_value * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance_value
                elif changed_field == 'power_dBm':
                    power_W = 10 ** ((power_dBm - 30) / 10)
                    voltage = math.sqrt(power_W * impedance_value) * math.sqrt(2)
                    current = voltage / impedance_value                    
                elif changed_field == 'power_W':
                    voltage = math.sqrt(power_W * impedance_value) * math.sqrt(2)
                    current = voltage / impedance_value
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance_value * 1e3)
                elif changed_field == 'impedance' or 'waveform':
                    voltage = current * impedance_value
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance_value * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance_value

            elif waveform_text == "Square wave":
                if changed_field == 'current':
                    voltage = current * impedance_value
                    power_dBm = 10 * math.log10(voltage * voltage / impedance_value * 1e3)
                    power_W = voltage * voltage / impedance_value
                elif changed_field == 'voltage':
                    current = voltage / impedance_value
                    power_dBm = 10 * math.log10(voltage * voltage / impedance_value * 1e3)
                    power_W = voltage * voltage / impedance_value
                elif changed_field == 'power_dBm':
                    power_W = 10 ** ((power_dBm - 30) / 10)
                    voltage = math.sqrt(power_W * impedance_value)
                    current = voltage / impedance_value                    
                elif changed_field == 'power_W':
                    voltage = math.sqrt(power_W * impedance_value)
                    current = voltage / impedance_value
                    power_dBm = 10 * math.log10(voltage * voltage / impedance_value * 1e3)
                elif changed_field == 'impedance' or 'waveform':
                    voltage = current * impedance_value
                    power_dBm = 10 * math.log10(voltage * voltage / impedance_value * 1e3)
                    power_W = voltage * voltage / impedance_value

            return {
                'current': current,
                'voltage': voltage,
                'power_dBm': power_dBm,
                'power_W': power_W,
                'impedance': impedance_value,
                'waveform': waveform_text
            }              

        except ValueError:
            pass
    
    def update_tab_inputs(self, changed_field):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            
            input_current = tab.findChild(QLineEdit, "input_current")
            input_voltage = tab.findChild(QLineEdit, "input_voltage")
            input_power_dBm = tab.findChild(QLineEdit, "input_power_dBm")
            input_power_W = tab.findChild(QLineEdit, "input_power_W")
            impedance = tab.findChild(QLineEdit, "impedance")
            waveform = tab.findChild(QComboBox, "waveform")

            updated_values = self.update_inputs(changed_field, input_current, input_voltage, input_power_dBm, input_power_W, impedance, waveform)
            
            if updated_values:
                input_current.setText(f"{updated_values['current']:.6e}")
                input_voltage.setText(f"{updated_values['voltage']:.6e}")
                input_power_dBm.setText(f"{updated_values['power_dBm']:.6f}")
                input_power_W.setText(f"{updated_values['power_W']:.6e}")
                impedance.setText(f"{updated_values['impedance']:.6f}")
                waveform.setCurrentText(updated_values['waveform'])
    
    def update_append_text(self):
        try:
            dir_path = self.dir_str.text()
            output_filename = self.output_filename.text()
            output_extension = self.output_extension.currentText()
            path_len = len(dir_path) + len(output_filename) + len(output_extension) + 2
            

            n_x = int(self.n_x.text()) if self.n_x.text() else 0
            n_y = int(self.n_y.text()) if self.n_y.text() else 0
            n_z = int(self.n_z.text()) if self.n_z.text() else 0
            n_str = f"{n_x}x{n_y}x{n_z}cells"

            size_x = float(self.size_x.text()) if self.size_x.text() else 0
            size_y = float(self.size_y.text()) if self.size_y.text() else 0
            size_z = float(self.size_z.text()) if self.size_z.text() else 0
            size_str = f"{add_si_prefix(size_x, 'm')}x{add_si_prefix(size_y, 'm')}x{add_si_prefix(size_z, 'm')}"

            path_len += len(n_str) + len(size_str) + 1
            
            ant_dict_list = self.get_antenna_parameters()
            antenna_str = ""
            for i, ant_dict in enumerate(ant_dict_list):
                antenna_str += f"_ant{i+1}_t{add_si_prefix(ant_dict['ant_width'], 'm')}_x{add_si_prefix(ant_dict['ant_position_x'], 'm')}_y{add_si_prefix(ant_dict['ant_position_y'], 'm')}_s2a{add_si_prefix(ant_dict['distance'], 'm')}_{add_si_prefix(ant_dict['current_direction'], 'deg')}_I{add_si_prefix(ant_dict['input_current'], 'A')}"
                path_len += len(antenna_str)
                if path_len > 240:
                    antenna_str = f"_{len(ant_dict_list)}Antennas"
                    break
            self.append_filename.setText(f"{n_str}_{size_str}{antenna_str}")

        except ValueError:
            pass
    
    def get_antenna_parameters(self):
        antenna_params = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            
            ant_width = float(tab.findChild(QLineEdit, "ant_width").text())
            ant_thickness = float(tab.findChild(QLineEdit, "ant_thickness").text())
            ant_position_x = float(tab.findChild(QLineEdit, "ant_position_x").text())
            ant_position_y = float(tab.findChild(QLineEdit, "ant_position_y").text())
            distance = float(tab.findChild(QLineEdit, "distance").text())
            current_direction = float(tab.findChild(QLineEdit, "current_direction").text())
            
            input_current = float(tab.findChild(QLineEdit, "input_current").text()) if tab.findChild(QLineEdit, "input_current").text() else 0
            input_voltage = float(tab.findChild(QLineEdit, "input_voltage").text())
            input_power_dBm = float(tab.findChild(QLineEdit, "input_power_dBm").text()) if tab.findChild(QLineEdit, "input_power_dBm").text() else 0
            input_power_W = float(tab.findChild(QLineEdit, "input_power_W").text()) if tab.findChild(QLineEdit, "input_power_W").text() else 0
            impedance = float(tab.findChild(QLineEdit, "impedance").text())
            waveform = tab.findChild(QComboBox, "waveform").currentText()
            
            antenna_params.append({
                "ant_width": ant_width,
                "ant_thickness": ant_thickness,
                "ant_position_x": ant_position_x,
                "ant_position_y": ant_position_y,
                "distance": distance,
                "current_direction": current_direction,
                "input_current": input_current,
                "input_voltage": input_voltage,
                "input_power_dBm": input_power_dBm,
                "input_power_W": input_power_W,
                "impedance": impedance,
                "waveform": waveform
            })
        
        return antenna_params               
    
    def open_check_window(self):
        image_paths = self.calculate(True)
        if image_paths:
            self.check_window = CheckWindow(image_paths, self.dir_str.text(), self.append_filename.text(), self)
            self.check_window.show()

    def browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_str.setText(dir_path)
    
    def disable_inputs(self):
        for widget in self.findChildren((QLineEdit, QPushButton, QComboBox, QCheckBox)):
            widget.setEnabled(False)
        self.progress_bar.show()

    def enable_inputs(self):
        for widget in self.findChildren((QLineEdit, QPushButton, QComboBox, QCheckBox)):
            widget.setEnabled(True)
        self.progress_bar.hide()

    def calculate(self, check):
        self.disable_inputs()
        if self.save_conditions.isChecked() and not check:
            self.save_current_conditions()
        
        self.progress_bar.setValue(0)

        try:
            n_x = int(self.n_x.text())
            n_y = int(self.n_y.text())
            n_z = int(self.n_z.text())

            size_x = float(self.size_x.text())
            size_y = float(self.size_y.text())
            size_z = float(self.size_z.text())

            ant_dict = self.get_antenna_parameters()

            total_steps = n_z

            result = []

            dir_path = self.dir_str.text()
            output_filename = self.output_filename.text() + "_" + self.append_filename.text() + self.output_extension.currentText()
            output_path = os.path.join(dir_path, output_filename)
            
            for step in range(total_steps):
                progress = int((step + 1) / total_steps * 90)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()

                if check:
                    result.append(cf.get_magnetic_field(n_x, n_y, n_z, size_x, size_y, size_z, ant_dict, check, step)[0])
                    if step == total_steps - 1:
                        image_paths = result
                else:
                    B_pump_x_array, B_pump_y_array, B_pump_z_array = cf.get_magnetic_field(n_x, n_y, n_z, size_x, size_y, size_z, ant_dict, current_step=step)
                    oo.write_oommf_binary_file_step(step, output_path, n_x, n_y, n_z, B_pump_x_array, B_pump_y_array, B_pump_z_array)

            self.progress_bar.setValue(100)
            QApplication.processEvents()

        except ValueError:
            print("Value error")
            self.enable_inputs()
            return None if check else None

        self.enable_inputs()
        return image_paths if check else None
    
    def save_current_conditions(self):
        conditions = {
            'n_x': self.n_x.text(),
            'n_y': self.n_y.text(),
            'n_z': self.n_z.text(),
            'size_x': self.size_x.text(),
            'size_y': self.size_y.text(),
            'size_z': self.size_z.text(),
            'dir_str': self.dir_str.text(),
            'output_filename': self.output_filename.text(),
            'output_extension': self.output_extension.currentText(),
            'antennas': []
        }
        
        # Save conditions for each antenna tab
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            antenna_conditions = {
                'ant_width': tab.findChild(QLineEdit, "ant_width").text(),
                'ant_thickness': tab.findChild(QLineEdit, "ant_thickness").text(),
                'ant_position_x': tab.findChild(QLineEdit, "ant_position_x").text(),
                'ant_position_y': tab.findChild(QLineEdit, "ant_position_y").text(),
                'distance': tab.findChild(QLineEdit, "distance").text(),
                'current_direction': tab.findChild(QLineEdit, "current_direction").text(),
                'input_current': tab.findChild(QLineEdit, "input_current").text(),
                'input_voltage': tab.findChild(QLineEdit, "input_voltage").text(),
                'input_power_dBm': tab.findChild(QLineEdit, "input_power_dBm").text(),
                'input_power_W': tab.findChild(QLineEdit, "input_power_W").text(),
                'impedance': tab.findChild(QLineEdit, "impedance").text(),
                'waveform': tab.findChild(QComboBox, "waveform").currentText()
            }
            conditions['antennas'].append(antenna_conditions)
        
        with open(os.path.join(self.dir_str.text(), 'cond_' + self.output_filename.text() + '_' + self.append_filename.text() + '.json'), 'w') as f:
            json.dump(conditions, f)

    def load_conditions(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Conditions", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as f:
                conditions = json.load(f)
            
            self.n_x.setText(conditions['n_x'])
            self.n_y.setText(conditions['n_y'])
            self.n_z.setText(conditions['n_z'])
            self.size_x.setText(conditions['size_x'])
            self.size_y.setText(conditions['size_y'])
            self.size_z.setText(conditions['size_z'])

            self.update_sizes('x', 'n')
            self.update_sizes('y', 'n')
            self.update_sizes('z', 'n')

            self.dir_str.setText(conditions['dir_str'])
            self.output_filename.setText(conditions['output_filename'])
            self.output_extension.setCurrentText(conditions['output_extension'])
            
            # Remove existing antenna tabs
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
            
            # Load conditions for each antenna tab
            for antenna_conditions in conditions['antennas']:
                self.add_antenna_tab()
                tab = self.tab_widget.widget(self.tab_widget.count() - 1)
                
                tab.findChild(QLineEdit, "ant_width").setText(antenna_conditions['ant_width'])
                tab.findChild(QLineEdit, "ant_thickness").setText(antenna_conditions['ant_thickness'])
                tab.findChild(QLineEdit, "ant_position_x").setText(antenna_conditions['ant_position_x'])
                tab.findChild(QLineEdit, "ant_position_y").setText(antenna_conditions['ant_position_y'])
                tab.findChild(QLineEdit, "distance").setText(antenna_conditions['distance'])
                tab.findChild(QLineEdit, "current_direction").setText(antenna_conditions['current_direction'])
                tab.findChild(QLineEdit, "input_current").setText(antenna_conditions['input_current'])
                tab.findChild(QLineEdit, "input_voltage").setText(antenna_conditions['input_voltage'])
                tab.findChild(QLineEdit, "input_power_dBm").setText(antenna_conditions['input_power_dBm'])
                tab.findChild(QLineEdit, "input_power_W").setText(antenna_conditions['input_power_W'])
                tab.findChild(QLineEdit, "impedance").setText(antenna_conditions['impedance'])
                tab.findChild(QComboBox, "waveform").setCurrentText(antenna_conditions['waveform'])
            
            self.update_append_text()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(gi.iconFromBase64())
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
