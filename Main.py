from pathlib2 import Path
import os
import math

import output_ovf as oo
import calc_field as cf

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QGridLayout, QPushButton, QFileDialog, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

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
        return f"{value} {unit}"
    
    exponent = int('{:.0e}'.format(value).split('e')[1])
    si_exponent = 3 * (exponent // 3)
    
    if si_exponent not in prefixes:
        return f"{value} {unit}"
    
    new_value = value / (10 ** si_exponent)
    si_prefix = prefixes[si_exponent]
    
    return f"{decimal_normalize(round(new_value, 3))}{si_prefix}{unit}"

class ModernUI(QWidget):
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
            QLineEdit {
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

        self.distance = QLineEdit("0.1e-9")  # Original: 0.1e-9
        antenna_layout.addWidget(QLabel("Distance between antenna and sample (m):"), 1, 0, 1, 3)
        antenna_layout.addWidget(self.distance, 1, 3, 1, 3)

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

        self.dir_str = QLineEdit()
        self.output_filename = QLineEdit("antenna.ovf")  # Original: 'antenna' + append_str + '.ovf'
        output_layout.addWidget(QLabel("Path:"), 0, 0)
        output_layout.addWidget(self.dir_str, 0, 1)
        output_layout.addWidget(QPushButton("Browse", clicked=self.browse_dir), 0, 2)
        output_layout.addWidget(QLabel("Output Filename:"), 1, 0)
        output_layout.addWidget(self.output_filename, 1, 1, 1, 2)

        main_layout.addWidget(output_group)

        # Calculate button
        calculate_button = QPushButton("Calculate", clicked=self.calculate)
        main_layout.addWidget(calculate_button)

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
            self.input_power_dBm.setText(f"{power_dBm:.6}")
            self.input_power_W.setText(f"{power_W:.6e}")
            self.impedance.setText(f"{impedance:.6}")                

        except ValueError:
            # If conversion fails, don't update the sizes
            pass

    def browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_str.setText(dir_path)

    def calculate(self):
        # Here you would implement the calculation logic
        print("Calculation triggered!")
        # You can access the input values using self.input_name.text()
        # For example: n_x = int(self.n_x.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ModernUI()
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


