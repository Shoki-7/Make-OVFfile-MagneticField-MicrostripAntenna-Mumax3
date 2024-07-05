def get_header(n_x: int, n_y: int, n_z: int) -> str:
    header = f"""# OOMMF OVF 2.0
# Segment count: 1
# Begin: Segment
# Begin: Header
# valuedim: 3
# valueunits: 1 1 1
# xnodes: {n_x}
# ynodes: {n_y}
# znodes: {n_z}
# End: Header
# Begin: data text
"""
    return header

def get_footer() -> str:
    footer = """# End: data text
# End: Segment
"""
    return footer

def write_oommf_file(output_filename: str, n_x: int, n_y: int, n_z: int, B_pump_x_list, B_pump_y_list, B_pump_z_list) -> None:

    header = get_header(n_x, n_y, n_z)
    footer = get_footer()
    
    with open(output_filename, 'w', encoding='CP932', newline='\n') as file:
        file.write(header)

        for z in range(n_z):
            B_pump_x = B_pump_x_list[z]
            B_pump_y = B_pump_y_list[z]
            B_pump_z = B_pump_z_list[z]

            for y in range(n_y):
                line = " ".join(f"{B_pump_x[y][x]} {B_pump_y[y][x]} {B_pump_z[y][x]}" for x in range(n_x))
                file.write(line + "\n")

        file.write(footer)
        file.write("\n")
