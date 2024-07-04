import numpy as np
import matplotlib.pyplot as plt
from pathlib2 import Path
import os

def write_oommf_file(output_filename, n_x, n_y, n_z, xy_plane_list, zero_plane_list, z_plane_list, current_direction):
    header_template = f"""# OOMMF OVF 2.0
# Segment count: 1
# Begin: Segment
# Begin: Header
# valuedim: 3
# valueunits: 1 1 1
# xnodes: {n_x}
# ynodes: {n_y}
# znodes: {n_z}
# End: Header
# Begin: Data Binary 4
"""
    footer = """# End: Data Binary 4
# End: Segment
"""

    with open(output_filename, 'w', encoding='CP932', newline='\n') as file:
        for z in range(n_z):
            file.write(header_template)

            # 現在の2次元配列を取得
            xy_plane = xy_plane_list[z]
            zero_plane = zero_plane_list[z]
            z_plane = z_plane_list[z]

            # yとxの範囲はxy_planeのサイズに依存
            y_size = len(xy_plane)
            for y in range(y_size):
                x_size = len(xy_plane[y])
                for x in range(x_size):
                    # 各配列の対応する要素を取得して、空白区切りで出力
                    if current_direction == 'x':
                        line = f"{zero_plane[y][x]} {xy_plane[y][x]} {z_plane[y][x]} "
                    else:
                        line = f"{xy_plane[y][x]} {zero_plane[y][x]} {z_plane[y][x]} "
                    file.write(line)
                file.write("\n")

            file.write(footer)
            file.write("\n")

# number of cell
n_x = 1600
n_y = 800
n_z = 1

# size of sample
size_x = 80e-6		#  80 um
size_y = 40e-6		#  40 um
size_z = 300e-9		# 300 nm

# size of sell
size_cell_x = size_x / n_x
size_cell_y = size_y / n_y
size_cell_z = size_z / n_z

# antenna
ant_width = 3000e-9     # [m]
ant_thickness = 100e-9  # [m]
ant_position = 45e-6    # [m]
input_current = 10e-3    # [A]
input_current_direction = ['x', 'y'][1]

input_voltage = 5   # [V]
input_current = input_voltage / 50.

distance_between_antenna_and_sample = 1e-9  # [m]

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

for z_pnt in range(n_z):
    # depth between center of antenna thickness and cell center
    z_value = ant_half_thickness + distance_between_antenna_and_sample + z_arr[z_pnt]
    z_mesh = np.full_like(x_mesh, z_value)
    # print(f"z_mesh shape: {z_mesh.shape}")
    # print(f"z_mesh: {z_mesh}")

    B_pump_xy_plane_arr = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (xy_plane_arr+ant_half_width)/2 * np.log( ((xy_plane_arr+ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr+ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) - (xy_plane_arr-ant_half_width)/2*np.log( ((xy_plane_arr-ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr-ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) + (z_mesh+ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh+ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh+ant_half_thickness)) ) - (z_mesh-ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh-ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh-ant_half_thickness)) ) )

    B_pump_xy_plane_arr_list.append(B_pump_xy_plane_arr)

    B_pump_z_arr = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (z_mesh+ant_half_thickness)/2 * np.log( ((z_mesh+ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh+ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) - (z_mesh-ant_half_thickness)/2*np.log( ((z_mesh-ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh-ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) + (xy_plane_arr+ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr+ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr+ant_half_width)) ) - (xy_plane_arr-ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr-ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr-ant_half_width)) ) )

    B_pump_z_arr_list.append(B_pump_z_arr)

    B_pump_zero_arr_list.append(np.full_like(B_pump_xy_plane_arr, 0.))

    print(np.max(B_pump_xy_plane_arr))
    print(np.max(B_pump_z_arr))
    print(np.max(np.sqrt(B_pump_xy_plane_arr**2 + B_pump_z_arr**2)))

    # plt.figure(figsize=(10, 8))
    # plt.contourf(x_mesh, y_mesh, B_pump_xy_plane_arr, cmap='viridis')
    # plt.colorbar(label='B_pump values [T]')
    # plt.xlabel('x [m]')
    # plt.ylabel('y [m]')
    # plt.title('B_pump_xy_plane_arr Visualization')
    # plt.show()

    # plt.figure(figsize=(10, 8))
    # plt.contourf(x_mesh, y_mesh, B_pump_z, cmap='viridis')
    # plt.colorbar(label='B_pump_z values [T]')
    # plt.xlabel('x [m]')
    # plt.ylabel('y [m]')
    # plt.title('B_pump_z Visualization')
    # plt.show()

dir_str = input('Please input the output directory path: ')
dir_path = Path(dir_str)
output_filename = 'antenna.ovf'
output_path = os.path.join(dir_path, output_filename)
write_oommf_file(output_path, n_x, n_y, n_z, B_pump_xy_plane_arr_list, B_pump_zero_arr_list, B_pump_z_arr_list, input_current_direction)


# B_pump = np.sqrt(B_pump_x**2 + B_pump_z**2)
