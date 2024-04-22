from val_utdb_bint import bint


class DoNotCheck:
    pass


def bytes_to_str(data_bytes):
    data_str = ""
    for byte in data_bytes:
        if byte is None:
            data_str = "--" + data_str
        else:
            data_str = hex(byte)[2:].zfill(2) + data_str
    return data_str


def str_to_bytes(hex_str: str):
    bytes_list = list()
    if len(hex_str) % 2 == 1:
        hex_str = '0' + hex_str
    for i in range(int(len(hex_str) / 2)):
        bytes_list.insert(0, bint(int(hex_str[(i * 2):(i * 2) + 2], 16)))

    return bytes_list


def data_to_bytes(data: str):
    data_bytes = list()
    data = data.replace(' ', '')

    for char1, char2 in zip(data[0::2], data[1::2]):
        byte_str = char1 + char2
        if byte_str == '--':
            data_bytes.insert(0, None)
        else:
            data_bytes.insert(0, bint(int(byte_str, 16)))
    return data_bytes


def data_bytes_to_flat_data(data_bytes, none_to_ones=False):
    flat_data = bint(0)
    for i, byte in enumerate(data_bytes):
        if byte is None:
            byte = 0xff if none_to_ones else 0
        flat_data[(i*8) + 7: i*8] = byte
    return flat_data


def flat_nested_lists(nested_list):
    flat_list = list()
    for item in nested_list:
        if type(item) == list:
            flat_list += item
        else:
            flat_list.append(item)
    return flat_list


def compare_trans(exp_tran, act_tran):
    msg = ""
    if type(exp_tran) != type(act_tran):
        msg = 'Transaction compare type mismatch\n' \
              'actual type: ' + str(type(act_tran)) + \
              '\nexpected type: ' + str(type(exp_tran)) + '\n'
    else:
        act_vars = vars(act_tran)
        for attr, exp_value in vars(exp_tran).items():
            if exp_value is None or exp_value is DoNotCheck:
                pass
            elif type(exp_value) == list and type(act_vars[attr]) == list:
                for i, val in enumerate(exp_value):
                    if (val is not None and act_vars[attr][i] is None) or \
                            (val is None and act_vars[attr][i] is not None):
                        msg = 'Transaction compare attribute mismatch for "' + attr.upper() + '" attribute\n'
                        break
                    elif val != act_vars[attr][i]:
                        msg = 'Transaction compare attribute mismatch for "' + attr.upper() + '" attribute\n'
                        break
            elif act_vars[attr] is None or exp_value != act_vars[attr]:
                msg = 'Transaction compare attribute mismatch for "' + attr.upper() + '" attribute\n'
    return msg == "", msg


def find_tran_and_idx(tran, flow, get_all_matches=False):
    match_trans = list()
    for i, flow_tran in enumerate(flow):
        comp_res, _ = compare_trans(tran, flow_tran)
        if comp_res:
            match_trans.append((i, flow_tran))

    if not get_all_matches:
        return match_trans[0] if len(match_trans) > 0 else (None, None)
    return match_trans


def find_tran(tran, flow, get_all_matches=False):
    match_trans = find_tran_and_idx(tran, flow, get_all_matches)
    if not get_all_matches:
        return match_trans[1]
    return [idx_and_tran[1] for idx_and_tran in match_trans]


def find_tran_idx(tran, flow, get_all_matches=False):
    match_trans = find_tran_and_idx(tran, flow, get_all_matches)
    if not get_all_matches:
        return match_trans[0]
    return [idx_and_tran[0] for idx_and_tran in match_trans]
