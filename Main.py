import numpy as np
import matplotlib.pyplot as plt
from pathlib2 import Path
import os
from matplotlib.colors import LinearSegmentedColormap

import output_ovf as oo
import calc_field as cf

def gen_cmap_rgb(cols):
    nmax = float(len(cols)-1)
    cdict = {'red':[], 'green':[], 'blue':[]}
    for n, c in enumerate(cols):
        loc = n/nmax
        cdict['red'  ].append((loc, c[0], c[0]))
        cdict['green'].append((loc, c[1], c[1]))
        cdict['blue' ].append((loc, c[2], c[2]))
    return LinearSegmentedColormap('cmap', cdict)

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

# number of cell
n_x = 512
n_y = 512
n_z = 32

append_str = f"_{n_x}x{n_y}x{n_z}cells"

# size of sample
size_x = 2500.6e-6		# [m]
size_y = 25.6e-6		# [m]
size_z = 10e-6		# [m]

append_str += f"_{add_si_prefix(size_x, 'm')}x{add_si_prefix(size_y, 'm')}x{add_si_prefix(size_z, 'm')}"

# size of cell
size_cell_x = size_x / n_x
size_cell_y = size_y / n_y
size_cell_z = size_z / n_z

# antenna
# ant_width = 500000e-9     # [m]
# ant_thickness = 18000e-9  # [m]
# ant_position = 5e-6    # [m]
ant_width = 500000e-9     # [m]
ant_thickness = 18000e-9  # [m]
ant_position = size_x/2 - ant_width/2    # [m]
ant_position = size_x/2
# ant_position  = size_x/2
# ant_position = 20e-6    # [m]
distance_between_antenna_and_sample = 0.1e-9  # [m]
append_str += f"_antw{add_si_prefix(ant_width, 'm')}_t{add_si_prefix(ant_thickness, 'm')}_p{add_si_prefix(ant_position, 'm')}_s2a{add_si_prefix(distance_between_antenna_and_sample, 'm')}"

input_current_direction = ['x', 'y'][1]
input_current = 10e-3    # [A]
input_voltage = 5   # [V]
# input_voltage = 0.5617   # [V]
input_current = input_voltage / 50.
append_str += f"_I{add_si_prefix(input_current, 'A')}_{input_current_direction}"

field_check = True

print(append_str)

B_pump_x_list, B_pump_y_list, B_pump_z_list = cf.get_magnetic_field(n_x, n_y, n_z, size_x, size_y, size_z, input_current_direction, ant_width, ant_thickness, ant_position, distance_between_antenna_and_sample, input_current, field_check)

dir_str = input('Please input the output directory path: ')
dir_path = Path(dir_str)
output_filename = 'antenna' + append_str + '.ovf'
output_path = os.path.join(dir_path, output_filename)

oo.write_oommf_file(output_path, n_x, n_y, n_z, B_pump_x_list, B_pump_y_list, B_pump_z_list)


# B_pump = np.sqrt(B_pump_x**2 + B_pump_z**2)

