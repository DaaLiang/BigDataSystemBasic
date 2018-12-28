import struct
import json
PACKAGE_SIZE = 512


def pack(stock_idx, data):
    packages = []
    header = {
        'stock_idx': stock_idx,
        'data': data,
    }
    temp = json.dumps(header).encode()
    total_length = len(temp)
    data_size = PACKAGE_SIZE - 12
    # print(type(total_length), type(data_size))
    pack_num = int(total_length / data_size)
    if pack_num * data_size == total_length:
        pack_num = pack_num - 1
    packages = [struct.pack("iii", stock_idx, 1, i) +
                temp[i * data_size:min(total_length, (i + 1) * data_size)]
                for i in range(pack_num)]
    last_pack = struct.pack("iii", stock_idx, 0, pack_num) + temp[pack_num * data_size:]
    packages.append(last_pack)
    return packages