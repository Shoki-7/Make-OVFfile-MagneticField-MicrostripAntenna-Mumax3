import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Divider, Size
from mpl_toolkits.axes_grid1.mpl_axes import Axes
from matplotlib.colors import LinearSegmentedColormap
import tempfile

def calc_magnetic_field(xy_plane_arr, z_mesh, ant_width: float, ant_thickness: float, input_current: float, in_or_out_of_plane: bool):

    ant_half_width = ant_width / 2
    ant_half_thickness = ant_thickness / 2

    # in_or_out_of_plane is True -> in-plane field. Else out-of-plane field.
    if in_or_out_of_plane:
        B_pump = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (xy_plane_arr+ant_half_width)/2 * np.log( ((xy_plane_arr+ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr+ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) - (xy_plane_arr-ant_half_width)/2*np.log( ((xy_plane_arr-ant_half_width)**2+(z_mesh+ant_half_thickness)**2)/((xy_plane_arr-ant_half_width)**2+(z_mesh-ant_half_thickness)**2) ) + (z_mesh+ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh+ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh+ant_half_thickness)) ) - (z_mesh-ant_half_thickness)*( np.arctan((xy_plane_arr+ant_half_width)/(z_mesh-ant_half_thickness)) - np.arctan((xy_plane_arr-ant_half_width)/(z_mesh-ant_half_thickness)) ) )
    else:
        B_pump = 4*np.pi*1e-7 * input_current/(8*np.pi*ant_half_width*ant_half_thickness)*( (z_mesh+ant_half_thickness)/2 * np.log( ((z_mesh+ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh+ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) - (z_mesh-ant_half_thickness)/2*np.log( ((z_mesh-ant_half_thickness)**2+(xy_plane_arr+ant_half_width)**2)/((z_mesh-ant_half_thickness)**2+(xy_plane_arr-ant_half_width)**2) ) + (xy_plane_arr+ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr+ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr+ant_half_width)) ) - (xy_plane_arr-ant_half_width)*( np.arctan((z_mesh+ant_half_thickness)/(xy_plane_arr-ant_half_width)) - np.arctan((z_mesh-ant_half_thickness)/(xy_plane_arr-ant_half_width)) ) )

    return B_pump

def get_magnetic_field(n_x: int, n_y: int, n_z: int, size_x: int, size_y: int, size_z: int, input_current_direction:str, ant_width: float, ant_thickness: float, ant_position: float, distance_between_antenna_and_sample: float, input_current: float, check=False, current_step=None):
    # size of cell
    size_cell_x = size_x / n_x
    size_cell_y = size_y / n_y
    size_cell_z = size_z / n_z

    # Generate 1D arrays for the x, y, and z directions
    x_arr = np.linspace(size_cell_x / 2, size_x - size_cell_x / 2, n_x)
    y_arr = np.linspace(size_cell_y / 2, size_y - size_cell_y / 2, n_y)
    z_arr = np.linspace(size_cell_z / 2, size_z - size_cell_z / 2, n_z)

    # Create xy plane mesh grid
    x_mesh, y_mesh = np.meshgrid(x_arr, y_arr)

    ant_half_width = ant_width / 2
    ant_half_thickness = ant_thickness / 2

    # Create the xy plane array based on the input current direction
    if input_current_direction == 'x':
        # Distance between y = ant_position and y_arr
        xy_plane_arr = y_mesh - ant_position
    else:
        # Distance between x = ant_position and x_arr
        xy_plane_arr = x_mesh - ant_position

    # Initialize B_pump to store the values for each z point
    B_pump_x_list = []
    B_pump_y_list = []
    B_pump_z_list = []

    if check:
        # Only process the current_step when checking
        z_range = range(current_step, current_step + 1)
    else:
        z_range = range(n_z)

    # depth between center of antenna thickness
    z_value_list = [ant_half_thickness + distance_between_antenna_and_sample + z_arr[z_pnt] for z_pnt in z_range]

    plot_data = []

    for i, z_value in enumerate(z_value_list):
        # cell center
        z_mesh = np.full_like(x_mesh, z_value)

        if input_current_direction == 'x':
            B_pump_y = calc_magnetic_field(xy_plane_arr, z_mesh, ant_width, ant_thickness, input_current, True)
            B_pump_y_list.append(B_pump_y)

            B_pump_x = np.full_like(B_pump_y, 0.)
            B_pump_x_list.append(B_pump_x)

        elif input_current_direction == 'y':
            B_pump_x = calc_magnetic_field(xy_plane_arr, z_mesh, ant_width, ant_thickness, input_current, True)
            B_pump_x_list.append(B_pump_x)

            B_pump_y = np.full_like(B_pump_x, 0.)
            B_pump_y_list.append(B_pump_y)


        B_pump_z = calc_magnetic_field(xy_plane_arr, z_mesh, ant_width, ant_thickness, input_current, False)

        B_pump_z_list.append(B_pump_z)

        print("max(B_pump_x) [T] :", np.max(B_pump_x))
        print("max(B_pump_y) [T] :", np.max(B_pump_y))
        print("max(B_pump_z) [T] :", np.max(B_pump_z))
        print("max pumping field [T] :", np.max(np.sqrt(B_pump_x**2 + B_pump_y**2 + B_pump_z**2)))
        
        if check:
            # plot_data.append(get_data_dict(x_arr, y_arr, B_pump_x, B_pump_y, B_pump_z))
            plot_data.append(get_field_temp_figure(x_arr, y_arr, B_pump_x, B_pump_y, B_pump_z, i))
        
    if len(plot_data) != 0:
        return plot_data
    
    return B_pump_x_list, B_pump_y_list, B_pump_z_list

def get_data_dict(x_arr, y_arr, B_pump_x, B_pump_y, B_pump_z):
    
    x_exp, x_unit = get_si_prefix(max(x_arr), "m")
    y_exp, y_unit = get_si_prefix(max(y_arr), "m")

    B_pump_x_exp, B_pump_x_unit = get_si_prefix(max(list(map(lambda x: max(x), B_pump_x))), "T")
    B_pump_y_exp, B_pump_y_unit = get_si_prefix(max(list(map(lambda x: max(x), B_pump_y))), "T")
    B_pump_z_exp, B_pump_z_unit = get_si_prefix(max(list(map(lambda x: max(x), B_pump_z))), "T")


    plot_data = {
        'x_arr': x_arr / (10**x_exp),
        'y_arr': y_arr / (10**y_exp),
        'B_pump_x': B_pump_x / (10**B_pump_x_exp),
        'B_pump_y': B_pump_y / (10**B_pump_y_exp),
        'B_pump_z': B_pump_z / (10**B_pump_z_exp),
        'x_unit': x_unit,
        'y_unit': y_unit,
        'B_pump_x_unit': B_pump_x_unit,
        'B_pump_y_unit': B_pump_y_unit,
        'B_pump_z_unit': B_pump_z_unit
    }

    return plot_data

def get_field_temp_figure(x_arr, y_arr, B_pump_x, B_pump_y, B_pump_z, z):
    # color map
    cmap = gen_cmap_rgb([(0,0,0.5),(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0.5,0),(1,0,0)])

    plt, fig, axes, caxes, shrink = figure_size_setting(3)

    for i in range(3):
        ax = axes[i]
        cax = caxes[i]
        x_exp, x_unit = get_si_prefix(max(x_arr), "m")
        y_exp, y_unit = get_si_prefix(max(y_arr), "m")
        B_pump = [B_pump_x, B_pump_y, B_pump_z][i]
        z_exp, z_unit = get_si_prefix(max(list(map(lambda x: max(x), B_pump))), "T")
        z_min, z_max = 0 if i != 2 else min(list(map(lambda x: min(x), B_pump / (10**z_exp)))), max(list(map(lambda x: max(x), B_pump / (10**z_exp)))) if i != 2 else max(list(map(lambda x: max(x), abs(B_pump / (10**z_exp)))))
        im = ax.pcolor(x_arr / (10**x_exp), y_arr / (10**y_exp), B_pump / (10**z_exp), cmap=cmap, rasterized=True, vmin=z_min, vmax=z_max)
        ax.locator_params(axis='x',nbins=10)
        ax.locator_params(axis='y',nbins=10)
        
        cbar = fig.colorbar(im, cax=cax, shrink=shrink)             #show colorbar
        cbar.set_label(f'Pumped field ({z_unit})', labelpad=2, fontsize=7)

        ax.set_xlabel(f'x ({x_unit})', labelpad=0, fontsize=7)      #x-axis label
        ax.set_ylabel(f'y ({y_unit})', labelpad=1, fontsize=7)      #y-axis label

        ax.set_title(f"Z-slice: {z}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        plt.savefig(tmp.name)
    plt.close(fig)

    return tmp.name

def print_field_figure(x_arr, y_arr, B_pump_x, B_pump_y, B_pump_z):
    # color map
    cmap = gen_cmap_rgb([(0,0,0.5),(0,0,1),(0,1,1),(0,1,0),(1,1,0),(1,0.5,0),(1,0,0)])

    plt, fig, axes, caxes, shrink = figure_size_setting(3)

    for i in range(3):
        ax = axes[i]
        cax = caxes[i]
        x_exp, x_unit = get_si_prefix(max(x_arr), "m")
        y_exp, y_unit = get_si_prefix(max(y_arr), "m")
        B_pump = [B_pump_x, B_pump_y, B_pump_z][i]
        z_exp, z_unit = get_si_prefix(max(list(map(lambda x: max(x), B_pump))), "T")
        z_min, z_max = 0 if i != 2 else min(list(map(lambda x: min(x), B_pump / (10**z_exp)))), max(list(map(lambda x: max(x), B_pump / (10**z_exp)))) if i != 2 else max(list(map(lambda x: max(x), abs(B_pump / (10**z_exp)))))
        im = ax.pcolor(x_arr / (10**x_exp), y_arr / (10**y_exp), B_pump / (10**z_exp), cmap=cmap, rasterized=True, vmin=z_min, vmax=z_max)
        ax.locator_params(axis='x',nbins=10)
        ax.locator_params(axis='y',nbins=10)
        
        cbar = fig.colorbar(im, cax=cax, shrink=shrink)             #show colorbar
        cbar.set_label(f'Pumped field ({z_unit})', labelpad=2, fontsize=7)

        ax.set_xlabel(f'x ({x_unit})', labelpad=0, fontsize=7)      #x-axis label
        ax.set_ylabel(f'y ({y_unit})', labelpad=1, fontsize=7)      #y-axis label

    # plt.show()

    return plt

def figure_setting():
    plt.rcParams['pdf.fonttype'] = 42           #true type font
    plt.rcParams['ps.fonttype'] = 42
    plt.rcParams['font.family'] = 'Arial'       #text font
    plt.rcParams["mathtext.fontset"] = "dejavusans"
    plt.rcParams['font.size'] = 6               #size of font
    plt.rcParams['xtick.labelsize'] = 6         #font size of x-axis scale label
    plt.rcParams['ytick.labelsize'] = 6         #font size of y-axis scale label
    plt.rcParams['xtick.direction'] = 'in'      #Whether the x-axis scale line is inward ('in'), outward ('out') or bi-directional ('inout').
    plt.rcParams['ytick.direction'] = 'in'      #Whether the y-axis scale line is inward ('in'), outward ('out') or bi-directional ('inout').
    plt.rcParams['xtick.major.width'] = 0.5     #Line width of x-axis main scale line
    plt.rcParams['ytick.major.width'] = 0.5     #Line width of y-axis main scale line
    plt.rcParams['xtick.major.size'] = 2        #Line length of x-axis main scale line
    plt.rcParams['ytick.major.size'] = 2        #Line length of y-axis main scale line
    plt.rcParams['axes.linewidth'] = 0.5        #Line width of axis
    plt.rcParams['xtick.major.pad'] = 3         #Distance between scale and scale label of x-axis
    plt.rcParams['ytick.major.pad'] = 2         #Distance between scale and scale label of y-axis
    plt.rcParams['xtick.top'] = True            #Upper scale of x-axis
    plt.rcParams['ytick.right'] = True          #Upper scale of y-axis
    plt.rcParams['text.usetex'] = False
    return plt

def figure_size_setting(num_plots=3):
    plt = figure_setting()
    ax_w_px = 400  # プロット領域の幅をピクセル単位で指定
    ax_h_px = 400  # プロット領域の高さをピクセル単位で指定

    fig_dpi = 300
    ax_w_inch = ax_w_px / fig_dpi
    ax_h_inch = ax_h_px / fig_dpi
    ax_margin_inch = (0.7, 0.5, 0.7, 0.5)  # Left,Top,Right,Bottom [inch]
    inter_plot_margin_inch = 0.7  # グラフ間の余白 [inch]
    colorbar_width_inch = 0.075  # カラーバーの幅 [inch]
    colorbar_margin_inch = 0.05  # カラーバーと図の余白 [inch]

    fig_w_inch = num_plots * (ax_w_inch + colorbar_margin_inch + colorbar_width_inch) + (num_plots - 1) * inter_plot_margin_inch + ax_margin_inch[0] + ax_margin_inch[2]
    fig_h_inch = ax_h_inch + ax_margin_inch[1] + ax_margin_inch[3]

    fig = plt.figure(dpi=fig_dpi, figsize=(fig_w_inch, fig_h_inch))
    
    ax_p_w = [Size.Fixed(ax_margin_inch[0])] + [Size.Fixed(ax_w_inch), Size.Fixed(colorbar_margin_inch), Size.Fixed(colorbar_width_inch), Size.Fixed(inter_plot_margin_inch)] * (num_plots - 1) + [Size.Fixed(ax_w_inch), Size.Fixed(colorbar_margin_inch), Size.Fixed(colorbar_width_inch), Size.Fixed(ax_margin_inch[2])]

    ax_p_h = [Size.Fixed(ax_margin_inch[1]), Size.Fixed(ax_h_inch)]
    divider = Divider(fig, (0.0, 0.0, 1.0, 1.0), ax_p_w, ax_p_h, aspect=False)
    
    axes = []
    caxes = []
    for i in range(num_plots):
        ax = Axes(fig, divider.get_position())
        ax.set_axes_locator(divider.new_locator(nx=4*i+1, ny=1))
        fig.add_axes(ax)
        axes.append(ax)

        color_ax = Axes(fig, divider.get_position())
        color_ax.set_axes_locator(divider.new_locator(nx=4*i+3, ny=1))
        fig.add_axes(color_ax)
        caxes.append(color_ax)

    # colorbar size
    shrink = ax_h_inch / fig_h_inch

    return plt, fig, axes, caxes, shrink

def figure_size_setting_check(num_plots=3):
    plt = figure_setting()
    ax_w_px = 200  # プロット領域の幅をピクセル単位で指定
    ax_h_px = 200  # プロット領域の高さをピクセル単位で指定

    fig_dpi = 150
    ax_w_inch = ax_w_px / fig_dpi
    ax_h_inch = ax_h_px / fig_dpi
    ax_margin_inch = (0.7, 0.5, 0.7, 0.5)  # Left,Top,Right,Bottom [inch]
    inter_plot_margin_inch = 0.7  # グラフ間の余白 [inch]
    colorbar_width_inch = 0.075  # カラーバーの幅 [inch]
    colorbar_margin_inch = 0.05  # カラーバーと図の余白 [inch]

    fig_w_inch = num_plots * (ax_w_inch + colorbar_margin_inch + colorbar_width_inch) + (num_plots - 1) * inter_plot_margin_inch + ax_margin_inch[0] + ax_margin_inch[2]
    fig_h_inch = ax_h_inch + ax_margin_inch[1] + ax_margin_inch[3]
    # print(fig_w_inch, fig_h_inch)

    fig = plt.figure(dpi=fig_dpi, figsize=(fig_w_inch, fig_h_inch))
    
    ax_p_w = [Size.Fixed(ax_margin_inch[0])] + [Size.Fixed(ax_w_inch), Size.Fixed(colorbar_margin_inch), Size.Fixed(colorbar_width_inch), Size.Fixed(inter_plot_margin_inch)] * (num_plots - 1) + [Size.Fixed(ax_w_inch), Size.Fixed(colorbar_margin_inch), Size.Fixed(colorbar_width_inch), Size.Fixed(ax_margin_inch[2])]

    ax_p_h = [Size.Fixed(ax_margin_inch[1]), Size.Fixed(ax_h_inch)]
    divider = Divider(fig, (0.0, 0.0, 1.0, 1.0), ax_p_w, ax_p_h, aspect=False)
    
    axes = []
    caxes = []
    for i in range(num_plots):
        ax = Axes(fig, divider.get_position())
        ax.set_axes_locator(divider.new_locator(nx=4*i+1, ny=1))
        fig.add_axes(ax)
        axes.append(ax)

        color_ax = Axes(fig, divider.get_position())
        color_ax.set_axes_locator(divider.new_locator(nx=4*i+3, ny=1))
        fig.add_axes(color_ax)
        caxes.append(color_ax)

    # colorbar size
    shrink = ax_h_inch / fig_h_inch

    return plt, fig, axes, caxes, shrink

def gen_cmap_rgb(cols):
    nmax = float(len(cols)-1)
    cdict = {'red':[], 'green':[], 'blue':[]}
    for n, c in enumerate(cols):
        loc = n/nmax
        cdict['red'  ].append((loc, c[0], c[0]))
        cdict['green'].append((loc, c[1], c[1]))
        cdict['blue' ].append((loc, c[2], c[2]))
    return LinearSegmentedColormap('cmap', cdict)

def save_figure(plt, output_dir_path, outname):
    output_name_pdf = outname + '.pdf'
    output_name_png = outname + '.png'
    output_path_pdf = os.path.join(output_dir_path, output_name_pdf)
    output_path_png = os.path.join(output_dir_path, output_name_png)
    
    # plt.tight_layout()
    plt.savefig(output_path_png, transparent=True, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_pdf, transparent=True, bbox_inches='tight')
    return 0

def save_figure_png(plt, output_dir_path, outname):
    output_name_png = outname + '.png'
    output_path_png = os.path.join(output_dir_path, output_name_png)
    
    # plt.tight_layout()
    plt.savefig(output_path_png, transparent=True, dpi=300, bbox_inches='tight')
    return 0

def save_figure_pdf(plt, output_dir_path, outname):
    output_name_pdf = outname + '.pdf'
    output_path_pdf = os.path.join(output_dir_path, output_name_pdf)
    
    # plt.tight_layout()
    plt.savefig(output_path_pdf, transparent=True, bbox_inches='tight')
    return 0

def save_to_csv(output_dir_path, outname, array1, array2):
    rows = zip(array1, array2)
    output_name_csv = outname + '.csv'
    output_path_csv = os.path.join(output_dir_path, output_name_csv)

    # CSVファイルに書き込み
    with open(output_path_csv, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # csv_writer.writerow(['Freqency (GHz)', 'Spectrum (Counts)'])  # ヘッダーを追加
        csv_writer.writerows(rows)

def get_si_prefix(value, unit):
    prefixes = {
        -24: 'y', -21: 'z', -18: 'a', -15: 'f', -12: 'p', -9: 'n', -6: 'µ', -3: 'm',
        0: '', 3: 'k', 6: 'M', 9: 'G', 12: 'T', 15: 'P', 18: 'E', 21: 'Z', 24: 'Y'
    }

    si_exponent = 0
    
    if value == 0:
        return si_exponent, unit
    
    exponent = int('{:.0e}'.format(value).split('e')[1])
    si_exponent = 3 * (exponent // 3)
    
    if si_exponent not in prefixes:
        return 0, unit
    
    new_value = value / (10 ** si_exponent)
    si_prefix = prefixes[si_exponent]
    
    return si_exponent, si_prefix + unit