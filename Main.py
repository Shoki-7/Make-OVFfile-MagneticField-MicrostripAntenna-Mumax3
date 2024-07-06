import numpy as np
import matplotlib.pyplot as plt
from pathlib2 import Path
import os
from matplotlib.colors import LinearSegmentedColormap

import output_ovf as oo

def gen_cmap_rgb(cols):
    nmax = float(len(cols)-1)
    cdict = {'red':[], 'green':[], 'blue':[]}
    for n, c in enumerate(cols):
        loc = n/nmax
        cdict['red'  ].append((loc, c[0], c[0]))
        cdict['green'].append((loc, c[1], c[1]))
        cdict['blue' ].append((loc, c[2], c[2]))
    return LinearSegmentedColormap('cmap', cdict)

# number of cell
n_x = 512
n_y = 512
n_z = 32

# size of sample
size_x = 25.6e-6		# [m]
size_y = 25.6e-6		# [m]
size_z = 10e-6		# [m]

# size of sell
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
# ant_position  = size_x/2
# ant_position = 20e-6    # [m]
input_current = 10e-3    # [A]
input_current_direction = ['x', 'y'][1]

input_voltage = 5   # [V]
input_current = input_voltage / 50.

distance_between_antenna_and_sample = 0.1e-9  # [m]

ant_half_width = ant_width / 2
ant_half_thickness = ant_thickness / 2

# Generate 1D arrays for the x, y, and z directions
x_arr = np.linspace(size_cell_x / 2, size_x - size_cell_x / 2, n_x)
y_arr = np.linspace(size_cell_y / 2, size_y - size_cell_y / 2, n_y)
z_arr = np.linspace(size_cell_z / 2, size_z - size_cell_z / 2, n_z)

# Print arrays to verify (optional)
# print(f"x_arr: {x_arr}")
# print(f"y_arr: {y_arr}")
# print(f"z_arr: {z_arr}")

# Create xy plane mesh grid
x_mesh, y_mesh = np.meshgrid(x_arr, y_arr)

# Create the xy plane array based on the input current direction
if input_current_direction == 'x':
    # Distance between y = ant_position and y_arr
    xy_plane_arr = y_mesh - ant_position
else:
    # Distance between x = ant_position and x_arr
    xy_plane_arr = x_mesh - ant_position

# Print shapes of the mesh grids to verify (optional)
# print(f"x_mesh shape: {x_mesh.shape}")
# print(f"y_mesh shape: {y_mesh.shape}")
# input()

# Initialize B_pump to store the values for each z point
B_pump_xy_plane_arr_list = []
B_pump_zero_arr_list = []
B_pump_z_arr_list = []

B_pump_x_list = []
B_pump_y_list = []
B_pump_z_list = []

for z_pnt in range(n_z):
    # depth between center of antenna thickness and cell center
    z_value = ant_half_thickness + distance_between_antenna_and_sample + z_arr[z_pnt]
    z_mesh = np.full_like(x_mesh, z_value)

    if input_current_direction == 'x':
        B_pump_y = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (xy_plane_arr+ant_half_width)/2 * np.log( ((xy_plane_arr+ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr+ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) - (xy_plane_arr-ant_half_width)/2*np.log( ((xy_plane_arr-ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr-ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) + (z_mesh+ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh+ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh+ant_half_thickness)) ) - (z_mesh-ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh-ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh-ant_half_thickness)) ) )
        B_pump_y_list.append(B_pump_y)

        B_pump_x = np.full_like(B_pump_y, 0.)
        B_pump_x_list.append(B_pump_x)

    elif input_current_direction == 'y':
        B_pump_x = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (xy_plane_arr+ant_half_width)/2 * np.log( ((xy_plane_arr+ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr+ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) - (xy_plane_arr-ant_half_width)/2*np.log( ((xy_plane_arr-ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr-ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) + (z_mesh+ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh+ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh+ant_half_thickness)) ) - (z_mesh-ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh-ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh-ant_half_thickness)) ) )
        B_pump_x_list.append(B_pump_x)

        B_pump_y = np.full_like(B_pump_x, 0.)
        B_pump_y_list.append(B_pump_y)


    B_pump_z = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (z_mesh+ant_half_thickness)/2 * np.log( ((z_mesh+ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh+ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) - (z_mesh-ant_half_thickness)/2*np.log( ((z_mesh-ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh-ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) + (xy_plane_arr+ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr+ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr+ant_half_width)) ) - (xy_plane_arr-ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr-ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr-ant_half_width)) ) )

    B_pump_z_list.append(B_pump_z)

    print("max(B_pump_x) [T] :", np.max(B_pump_x))
    print("max(B_pump_y) [T] :", np.max(B_pump_y))
    print("max(B_pump_z) [T] :", np.max(B_pump_z))
    print("max pumping field [T] :", np.max(np.sqrt(B_pump_x**2 + B_pump_y**2 + B_pump_z**2)))

    if 0:
        cmap = gen_cmap_rgb([(0,0,0.5),(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0.5,0),(1,0,0)])

        plt.figure(figsize=(10, 8))
        plt.pcolor(x_mesh, y_mesh, B_pump_x, cmap=cmap)
        plt.colorbar(label='B_pump values [T]')
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.title('B_pump_x Visualization')
        plt.show()

        plt.figure(figsize=(10, 8))
        plt.pcolor(x_mesh, y_mesh, B_pump_y, cmap=cmap)
        plt.colorbar(label='B_pump values [T]')
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.title('B_pump_y Visualization')
        plt.show()

        plt.figure(figsize=(10, 8))
        plt.pcolor(x_mesh, y_mesh, B_pump_z, cmap=cmap)
        plt.colorbar(label='B_pump_z values [T]')
        plt.xlabel('x [m]')
        plt.ylabel('y [m]')
        plt.title('B_pump_z Visualization')
        plt.show()

dir_str = input('Please input the output directory path: ')
dir_path = Path(dir_str)
output_filename = 'antenna.ovf'
output_path = os.path.join(dir_path, output_filename)

oo.write_oommf_file(output_path, n_x, n_y, n_z, B_pump_x_list, B_pump_y_list, B_pump_z_list)


# B_pump = np.sqrt(B_pump_x**2 + B_pump_z**2)

