from pathlib2 import Path
import math
import json

import output_ovf as oo
import calc_field as cf

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton, QFileDialog, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QDialog, QProgressBar)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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

class CheckWindow(QDialog):
    def __init__(self, image_paths, seved_path, append_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Check Plot')
        self.setGeometry(200, 200, 1100, 420)
        
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
        self.slider.valueChanged.connect(self.update_plot)
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
        self.save_filename = QLineEdit("PumpedField" + append_str)
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
        self.update_plot()
    
    def browse_save_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.save_path.setText(dir_path)
    
    def update_plot(self):
        z = self.slider.value()
        pixmap = QPixmap(self.image_paths[z])
        self.image_label.setPixmap(pixmap)
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
        # Delete temporary files when closing the window
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
        self.setWindowTitle('Antenna Field Calculator')
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QGroupBox {
                font-weight: bold;
            }
            QComboBox {
                background-color: #f8f8f8;
                selection-background-color: #f00000
            }
            QComboBox::drop-down {
                border: none;
            }
            QListView {
                background-color : #f8f8f8;
            }
        """)

        main_layout = QVBoxLayout()

        # Grid settings
        grid_group = QGroupBox("Grid Settings")
        grid_layout = QGridLayout()
        grid_group.setLayout(grid_layout)

        self.n_x = QLineEdit("512")
        self.n_y = QLineEdit("512")
        self.n_z = QLineEdit("32")
        grid_layout.addWidget(QLabel("n_x:"), 0, 0)
        grid_layout.addWidget(self.n_x, 0, 1)
        grid_layout.addWidget(QLabel("n_y:"), 0, 2)
        grid_layout.addWidget(self.n_y, 0, 3)
        grid_layout.addWidget(QLabel("n_z:"), 0, 4)
        grid_layout.addWidget(self.n_z, 0, 5)

        self.size_x = QLineEdit("2500.6e-6")
        self.size_y = QLineEdit("25.6e-6")
        self.size_z = QLineEdit("10e-6")
        grid_layout.addWidget(QLabel("size_x (m):"), 1, 0)
        grid_layout.addWidget(self.size_x, 1, 1)
        grid_layout.addWidget(QLabel("size_y (m):"), 1, 2)
        grid_layout.addWidget(self.size_y, 1, 3)
        grid_layout.addWidget(QLabel("size_z (m):"), 1, 4)
        grid_layout.addWidget(self.size_z, 1, 5)

        self.size_cell_x = QLineEdit()
        self.size_cell_y = QLineEdit()
        self.size_cell_z = QLineEdit()
        grid_layout.addWidget(QLabel("size_cell_x (m):"), 2, 0)
        grid_layout.addWidget(self.size_cell_x, 2, 1)
        grid_layout.addWidget(QLabel("size_cell_y (m):"), 2, 2)
        grid_layout.addWidget(self.size_cell_y, 2, 3)
        grid_layout.addWidget(QLabel("size_cell_z (m):"), 2, 4)
        grid_layout.addWidget(self.size_cell_z, 2, 5)

        # Connect signals for automatic updates
        self.n_x.editingFinished.connect(lambda: self.update_sizes('x', 'n'))
        self.n_y.editingFinished.connect(lambda: self.update_sizes('y', 'n'))
        self.n_z.editingFinished.connect(lambda: self.update_sizes('z', 'n'))
        self.size_x.editingFinished.connect(lambda: self.update_sizes('x', 'size'))
        self.size_y.editingFinished.connect(lambda: self.update_sizes('y', 'size'))
        self.size_z.editingFinished.connect(lambda: self.update_sizes('z', 'size'))
        self.size_cell_x.editingFinished.connect(lambda: self.update_sizes('x', 'cell'))
        self.size_cell_y.editingFinished.connect(lambda: self.update_sizes('y', 'cell'))
        self.size_cell_z.editingFinished.connect(lambda: self.update_sizes('z', 'cell'))

        # Initial calculation of cell sizes
        self.update_sizes('x', 'n')
        self.update_sizes('y', 'n')
        self.update_sizes('z', 'n')

        main_layout.addWidget(grid_group)

        # Antenna settings
        antenna_group = QGroupBox("Antenna Settings")
        antenna_layout = QGridLayout()
        antenna_group.setLayout(antenna_layout)

        self.ant_width = QLineEdit("500000e-9")      # Original: 500000e-9
        self.ant_thickness = QLineEdit("18000e-9")   # Original: 18000e-9
        self.ant_position = QLineEdit()              # Original: size_x/2
        antenna_layout.addWidget(QLabel("Antenna Width (m):"), 0, 0)
        antenna_layout.addWidget(self.ant_width, 0, 1)
        antenna_layout.addWidget(QLabel("Thickness (m):"), 0, 2)
        antenna_layout.addWidget(self.ant_thickness, 0, 3)
        antenna_layout.addWidget(QLabel("Position (m):"), 0, 4)
        antenna_layout.addWidget(self.ant_position, 0, 5)

        self.ant_position_x = QLineEdit("1250.3e-6")
        self.ant_position_y = QLineEdit("12.8e-6")
        antenna_layout.addWidget(QLabel("x (m):"), 1, 0)
        antenna_layout.addWidget(self.ant_position_x, 1, 1)
        antenna_layout.addWidget(QLabel("y (m):"), 1, 2)
        antenna_layout.addWidget(self.ant_position_y, 1, 3)

        self.distance = QLineEdit("0.1e-9")  # Original: 0.1e-9
        antenna_layout.addWidget(QLabel("Distance between antenna and sample (m):"), 2, 0, 1, 3)
        antenna_layout.addWidget(self.distance, 2, 3, 1, 3)

        self.current_direction = QLineEdit("0")  # Original: 0.1e-9
        antenna_layout.addWidget(QLabel("Current direction (degree):"), 3, 0, 1, 3)
        antenna_layout.addWidget(self.current_direction, 3, 3, 1, 3)

        main_layout.addWidget(antenna_group)

        # Input settings
        input_group = QGroupBox("Input Settings")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)

        self.input_current = QLineEdit()
        self.input_voltage = QLineEdit("5")  # Original: 5
        self.input_power_dBm = QLineEdit()
        self.input_power_W = QLineEdit()
        self.impedance = QLineEdit("50")     # Original: 50
        input_layout.addWidget(QLabel("Current (A):"), 0, 0)
        input_layout.addWidget(self.input_current, 0, 1)
        input_layout.addWidget(QLabel("Peak Voltage (V):"), 0, 2)
        input_layout.addWidget(self.input_voltage, 0, 3)
        input_layout.addWidget(QLabel("Power (dBm):"), 1, 0)
        input_layout.addWidget(self.input_power_dBm, 1, 1)
        input_layout.addWidget(QLabel("Power (W):"), 1, 2)
        input_layout.addWidget(self.input_power_W, 1, 3)
        input_layout.addWidget(QLabel("Impedance (Ω):"), 2, 0)
        input_layout.addWidget(self.impedance, 2, 1)

        self.waveform = QComboBox(input_group)
        self.waveform.addItem("Sin wave")
        self.waveform.addItem("Square wave")
        input_layout.addWidget(QLabel("Waveform :"), 2, 2)
        input_layout.addWidget(self.waveform, 2, 3)

        # Connect signals for automatic updates
        self.input_current.editingFinished.connect(lambda: self.update_inputs('current'))
        self.input_voltage.editingFinished.connect(lambda: self.update_inputs('voltage'))
        self.input_power_dBm.editingFinished.connect(lambda: self.update_inputs('power_dBm'))
        self.input_power_W.editingFinished.connect(lambda: self.update_inputs('power_W'))
        self.impedance.editingFinished.connect(lambda: self.update_inputs('impedance'))
        self.waveform.currentIndexChanged.connect(lambda: self.update_inputs('waveform'))

        # Initial calculation of inputs
        self.update_inputs('voltage')

        main_layout.addWidget(input_group)

        # check settings
        check_group = QGroupBox("Check")
        check_layout = QGridLayout()
        check_group.setLayout(check_layout)

        self.field_check = QCheckBox("Field Check")
        self.field_check.setChecked(True)  # Original: True
        check_layout.addWidget(self.field_check, 0, 0, 0, 6)

        main_layout.addWidget(check_group)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)

        self.dir_str = QLineEdit(os.getcwd())
        self.output_filename = QLineEdit("antenna")
        self.output_extension = QComboBox()
        self.output_extension.addItem(".ovf")
        self.output_extension.addItem(".txt")
        self.append_filename = QLineEdit()
        self.save_conditions = QCheckBox("Save conditions")
        self.load_button = QPushButton("Load", clicked=self.load_conditions)
        
        output_layout.addWidget(QLabel("Path:"), 0, 0)
        output_layout.addWidget(self.dir_str, 0, 1)
        output_layout.addWidget(QPushButton("Browse", clicked=self.browse_dir), 0, 2)
        output_layout.addWidget(QLabel("Output Filename:"), 1, 0)
        output_layout.addWidget(self.output_filename, 1, 1, 1, 2)
        output_layout.addWidget(QLabel("Append Filename:"), 2, 0)
        output_layout.addWidget(self.append_filename, 2, 1)
        output_layout.addWidget(self.output_extension, 2, 2)
        output_layout.addWidget(self.save_conditions, 3, 0)
        output_layout.addWidget(self.load_button, 3, 2)

        main_layout.addWidget(output_group)

        self.append_filename.editingFinished.connect(lambda: self.update_append_text())

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

        self.setLayout(main_layout)

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
            # If conversion fails, don't update the sizes
            pass
    
    def update_inputs(self, changed_field):
        try:
            current = float(self.input_current.text()) if self.input_current.text() else 0
            voltage = float(self.input_voltage.text()) if self.input_voltage.text() else 0
            power_dBm = float(self.input_power_dBm.text()) if self.input_power_dBm.text() else 0
            power_W = float(self.input_power_W.text()) if self.input_power_W.text() else 0
            impedance = float(self.impedance.text()) if self.impedance.text() else 50
            waveform = self.waveform.currentText()

            if waveform == "Sin wave":
                if changed_field == 'current':
                    voltage = current * impedance
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance
                elif changed_field == 'voltage':
                    voltage_rms = voltage / math.sqrt(2)
                    current = voltage / impedance
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance
                elif changed_field == 'power_dBm':
                    power_W = 10 ** ((power_dBm - 30) / 10)
                    voltage = math.sqrt(power_W * impedance) * math.sqrt(2)
                    current = voltage / impedance                    
                elif changed_field == 'power_W':
                    voltage = math.sqrt(power_W * impedance) * math.sqrt(2)
                    current = voltage / impedance
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance * 1e3)
                elif changed_field == 'impedance' or 'waveform':
                    voltage = current * impedance
                    voltage_rms = voltage / math.sqrt(2)
                    power_dBm = 10 * math.log10(voltage_rms * voltage_rms / impedance * 1e3)
                    power_W = voltage_rms * voltage_rms / impedance

            elif waveform == "Square wave":
                if changed_field == 'current':
                    voltage = current * impedance
                    power_dBm = 10 * math.log10(voltage * voltage / impedance * 1e3)
                    power_W = voltage * voltage / impedance
                elif changed_field == 'voltage':
                    current = voltage / impedance
                    power_dBm = 10 * math.log10(voltage * voltage / impedance * 1e3)
                    power_W = voltage * voltage / impedance
                elif changed_field == 'power_dBm':
                    power_W = 10 ** ((power_dBm - 30) / 10)
                    voltage = math.sqrt(power_W * impedance)
                    current = voltage / impedance                    
                elif changed_field == 'power_W':
                    voltage = math.sqrt(power_W * impedance)
                    current = voltage / impedance
                    power_dBm = 10 * math.log10(voltage * voltage / impedance * 1e3)
                elif changed_field == 'impedance' or 'waveform':
                    voltage = current * impedance
                    power_dBm = 10 * math.log10(voltage * voltage / impedance * 1e3)
                    power_W = voltage * voltage / impedance

            self.input_current.setText(f"{current:.6e}")
            self.input_voltage.setText(f"{voltage:.6e}")
            self.input_power_dBm.setText(f"{power_dBm:.6f}")
            self.input_power_W.setText(f"{power_W:.6e}")
            self.impedance.setText(f"{impedance:.6f}")                

        except ValueError:
            # If conversion fails, don't update the sizes
            pass
    
    def update_append_text(self):
        try:
            n_x = self.n_x.text() if self.n_x.text() else 0
            n_y = self.n_y.text() if self.n_y.text() else 0
            n_z = self.n_z.text() if self.n_z.text() else 0
            n_str = f"{n_x}x{n_y}x{n_z}cells"

            size_x = float(self.size_x.text()) if self.size_x.text() else 0
            size_y = float(self.size_y.text()) if self.size_y.text() else 0
            size_z = float(self.size_z.text()) if self.size_z.text() else 0
            size_str = f"{add_si_prefix(size_x, 'm')}x{add_si_prefix(size_y, 'm')}x{add_si_prefix(size_z, 'm')}"

            ant_width = float(self.ant_width.text()) if self.size_z.text() else 0
            ant_position_x = float(self.ant_position_x.text()) if self.ant_position_x.text() else 0
            ant_position_y = float(self.ant_position_y.text()) if self.ant_position_y.text() else 0
            distance = float(self.distance.text()) if self.distance.text() else 0
            current_direction = float(self.current_direction.text()) if self.current_direction.text() else 0
            input_current = float(self.input_current.text()) if self.input_current.text() else 0
            antenna_str = f"t{add_si_prefix(ant_width, 'm')}_x{add_si_prefix(ant_position_x, 'm')}_y{add_si_prefix(ant_position_y, 'm')}_s2a{add_si_prefix(distance, 'm')}_{add_si_prefix(current_direction, 'deg')}_I{add_si_prefix(input_current, 'A')}"

            self.append_filename.setText(f"{n_str}_{size_str}_{antenna_str}")

            # print(n_str, size_str)

        except ValueError:
            # If conversion fails, don't update the sizes
            pass
    
    def open_check_window(self):
        image_paths = self.calculate(True)
        if image_paths:
            self.check_window = CheckWindow(image_paths, self.dir_str.text(), "append", self)
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
        if self.save_conditions.isChecked():
            self.save_current_conditions()
        
        self.progress_bar.setValue(0)

        # Here you would implement the calculation logic
        try:
            n_x = int(self.n_x.text())
            n_y = int(self.n_y.text())
            n_z = int(self.n_z.text())

            size_x = float(self.size_x.text())
            size_y = float(self.size_y.text())
            size_z = float(self.size_z.text())

            input_current_direction = ['x', 'y'][1]

            ant_position_x = float(self.ant_position_x.text())
            ant_position_y = float(self.ant_position_y.text())

            current_direction = float(self.current_direction.text())

            ant_width = float(self.ant_width.text())
            ant_thickness = float(self.ant_thickness.text())
            ant_position = float(self.ant_position.text())

            distance_between_antenna_and_sample = float(self.distance.text())

            input_current =  float(self.input_current.text())

            total_steps = n_z if check else 1

            if check:
                result = []
                for step in range(total_steps):
                    progress = int((step + 1) / total_steps * 100)
                    self.progress_bar.setValue(progress)
                    QApplication.processEvents()
                    result.append(cf.get_magnetic_field_1(n_x, n_y, n_z, size_x, size_y, size_z, input_current_direction, ant_width, ant_thickness, ant_position, ant_position_x, ant_position_y, distance_between_antenna_and_sample, current_direction, input_current, check, step)[0])
                    if step == total_steps - 1:
                        image_paths = result
            else:
                self.progress_bar.setValue(50)
                QApplication.processEvents()
                B_pump_x_list, B_pump_y_list, B_pump_z_list = cf.get_magnetic_field(n_x, n_y, n_z, size_x, size_y, size_z, input_current_direction, ant_width, ant_thickness, ant_position, ant_position_x, ant_position_y, distance_between_antenna_and_sample, current_direction, input_current)

                self.progress_bar.setValue(75)
                QApplication.processEvents()
                dir_path = self.dir_str.text()
                output_filename = self.output_filename.text() + self.output_extension.currentText()
                output_path = os.path.join(dir_path, output_filename)
                oo.write_oommf_file(output_path, n_x, n_y, n_z, B_pump_x_list, B_pump_y_list, B_pump_z_list)

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
            'ant_width': self.ant_width.text(),
            'ant_thickness': self.ant_thickness.text(),
            'ant_position': self.ant_position.text(),
            'ant_position_x': self.ant_position_x.text(),
            'ant_position_y': self.ant_position_y.text(),
            'distance': self.distance.text(),
            'current_direction': self.current_direction.text(),
            'input_current': self.input_current.text(),
            'input_voltage': self.input_voltage.text(),
            'input_power_dBm': self.input_power_dBm.text(),
            'input_power_W': self.input_power_W.text(),
            'impedance': self.impedance.text(),
            'waveform': self.waveform.currentText(),
            'field_check': self.field_check.isChecked(),
            'dir_str': self.dir_str.text(),
            'output_filename': self.output_filename.text(),
            'output_extension': self.output_extension.currentText()
        }
        
        with open(os.path.join(self.dir_str.text(), self.output_filename.text() + '_cond.json'), 'w') as f:
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
            self.ant_width.setText(conditions['ant_width'])
            self.ant_thickness.setText(conditions['ant_thickness'])
            self.ant_position.setText(conditions['ant_position'])
            self.ant_position_x.setText(conditions['ant_position_x'])
            self.ant_position_y.setText(conditions['ant_position_y'])
            self.distance.setText(conditions['distance'])
            self.current_direction.setText(conditions['current_direction'])
            self.input_current.setText(conditions['input_current'])
            self.input_voltage.setText(conditions['input_voltage'])
            self.input_power_dBm.setText(conditions['input_power_dBm'])
            self.input_power_W.setText(conditions['input_power_W'])
            self.impedance.setText(conditions['impedance'])
            self.waveform.setCurrentText(conditions['waveform'])
            self.field_check.setChecked(conditions['field_check'])
            self.dir_str.setText(conditions['dir_str'])
            self.output_filename.setText(conditions['output_filename'])
            self.output_extension.setCurrentText(conditions['output_extension'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

# # number of cell
# n_x = 512
# n_y = 512
# n_z = 32

# append_str = f"_{n_x}x{n_y}x{n_z}cells"

# # size of sample
# size_x = 2500.6e-6		# [m]
# size_y = 25.6e-6		# [m]
# size_z = 10e-6		# [m]

# append_str += f"_{add_si_prefix(size_x, 'm')}x{add_si_prefix(size_y, 'm')}x{add_si_prefix(size_z, 'm')}"

# # size of cell
# size_cell_x = size_x / n_x
# size_cell_y = size_y / n_y
# size_cell_z = size_z / n_z

# # antenna
# # ant_width = 500000e-9     # [m]
# # ant_thickness = 18000e-9  # [m]
# # ant_position = 5e-6    # [m]
# ant_width = 500000e-9     # [m]
# ant_thickness = 18000e-9  # [m]
# ant_position = size_x/2 - ant_width/2    # [m]
# ant_position = size_x/2
# # ant_position  = size_x/2
# # ant_position = 20e-6    # [m]
# distance_between_antenna_and_sample = 0.1e-9  # [m]
# append_str += f"_antw{add_si_prefix(ant_width, 'm')}_t{add_si_prefix(ant_thickness, 'm')}_p{add_si_prefix(ant_position, 'm')}_s2a{add_si_prefix(distance_between_antenna_and_sample, 'm')}"

# input_current_direction = ['x', 'y'][1]
# input_current = 10e-3    # [A]
# input_voltage = 5   # [V]
# # input_voltage = 0.5617   # [V]
# impedance = 50.
# input_current = input_voltage / impedance
# append_str += f"_I{add_si_prefix(input_current, 'A')}_{input_current_direction}"

# field_check = True

# print(append_str)

# B_pump_x_list, B_pump_y_list, B_pump_z_list = cf.get_magnetic_field(n_x, n_y, n_z, size_x, size_y, size_z, input_current_direction, ant_width, ant_thickness, ant_position, distance_between_antenna_and_sample, input_current, field_check)

# dir_str = input('Please input the output directory path: ')
# dir_path = Path(dir_str)
# output_filename = 'antenna' + append_str + '.ovf'
# output_path = os.path.join(dir_path, output_filename)

# oo.write_oommf_file(output_path, n_x, n_y, n_z, B_pump_x_list, B_pump_y_list, B_pump_z_list)


