import struct

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
# Begin: Data Binary 4
"""
    return header

# Begin: data text

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

# OVF2のバイナリフォーマットで必要なコントロールナンバー
OVF_CONTROL_NUMBER_4 = 1234567.0  # 4バイト用コントロールナンバー

def write_oommf_binary_file(output_filename: str, n_x: int, n_y: int, n_z: int, 
                            B_pump_x_list, B_pump_y_list, B_pump_z_list, 
                            endianness='<f') -> None:
    """
    バイナリ形式でOOMMFファイルを書き出す。

    Parameters
    ----------
    output_filename : str
        出力ファイルのパス
    n_x : int
        x方向のノード数
    n_y : int
        y方向のノード数
    n_z : int
        z方向のノード数
    B_pump_x_list : list
        x方向のスカラーデータリスト
    B_pump_y_list : list
        y方向のスカラーデータリスト
    B_pump_z_list : list
        z方向のスカラーデータリスト
    endianness : str
        エンディアン（デフォルトはリトルエンディアン `<f`）
    """
    
    # ヘッダーを生成（メタデータに基づくヘッダー生成関数が必要）
    header = get_header(n_x, n_y, n_z)
    footer = get_footer()

    # バイナリファイルを書き込みモードで開く
    with open(output_filename, 'wb') as file:
        # ヘッダーを書き込み
        file.write(header.encode('utf-8'))
        
        # コントロールナンバーを書き込み
        file.write(struct.pack(endianness, OVF_CONTROL_NUMBER_4))
        
        # スカラーデータをバイナリ形式で書き込み
        for z in range(n_z):
            B_pump_x = B_pump_x_list[z]
            B_pump_y = B_pump_y_list[z]
            B_pump_z = B_pump_z_list[z]

            for y in range(n_y):
                for x in range(n_x):
                    # x, y, z 各方向のスカラー値をバイナリ形式で書き込む
                    file.write(struct.pack(endianness, B_pump_x[y][x]))
                    file.write(struct.pack(endianness, B_pump_y[y][x]))
                    file.write(struct.pack(endianness, B_pump_z[y][x]))

        # フッターを書き込み
        file.write(footer.encode('utf-8'))

def write_oommf_binary_file_step(current_z: int, output_filename: str, n_x: int, n_y: int, n_z: int, 
                                B_pump_x_array, B_pump_y_array, B_pump_z_array, endianness='<f') -> None:
    """
    バイナリ形式でOOMMFファイルを書き出す。

    Parameters
    ----------
    current_z : int
        保存するz方向の層の値
    output_filename : str
        出力ファイルのパス
    n_x : int
        x方向のノード数
    n_y : int
        y方向のノード数
    n_z : int
        z方向のノード数
    B_pump_x_array : 2D array
        Bxのスカラーデータ配列
    B_pump_y_array : 2D array
        Byのスカラーデータ配列
    B_pump_z_array : 2D array
        Bzのスカラーデータ配列
    endianness : str
        エンディアン（デフォルトはリトルエンディアン `<f`）
    """

    # ヘッダーとフッターの生成
    if current_z == 0:
        header = get_header(n_x, n_y, n_z)
    if current_z + 1 == n_z:
        footer = get_footer()

    # ファイルモードを決定
    mode = 'wb' if current_z == 0 else 'ab'

    # バイナリファイルを開く
    with open(output_filename, mode) as file:
        # ヘッダーを書き込み（最初の層のみ）
        if current_z == 0:
            file.write(header.encode('utf-8'))
            # コントロールナンバーを書き込み
            file.write(struct.pack(endianness, OVF_CONTROL_NUMBER_4))

        

        # current_z の層のデータをバイナリ形式で書き込み
        B_pump_x = B_pump_x_array
        B_pump_y = B_pump_y_array
        B_pump_z = B_pump_z_array

        for y in range(n_y):
            for x in range(n_x):
                # x, y, z 各方向のスカラー値をバイナリ形式で書き込む
                file.write(struct.pack(endianness, B_pump_x[y][x]))
                file.write(struct.pack(endianness, B_pump_y[y][x]))
                file.write(struct.pack(endianness, B_pump_z[y][x]))

        # フッターを追加（最後の層のみ）
        if current_z + 1 == n_z:
            file.write(footer.encode('utf-8'))
