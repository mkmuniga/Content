class DoNotCheck:
    pass

class DATA_CONVERSION_UTILS:
    def bytes_to_str(data_bytes):
        data_str = ""
        for byte in data_bytes:
            if byte is None:
                data_str = "--" + data_str
            else:
                data_str = hex(byte)[2:].zfill(2) + data_str
        return data_str

    def get_data_in_bits(data):
        int_data = int.from_bytes(data, "little")
        # return '{:08b}'.format(int(data, 16)).zfill(32)  # bin(int(data, base=16))[2:]
        bits = bin(int_data)[2:]
        return '{}'.format(bits).zfill(32)

    def get_data_slice_from_bit(data_str, end_bit_index, start_bit_index):
        if start_bit_index == 0:
            data_slice = data_str[-(end_bit_index+1):]
        else:
            data_slice = data_str[-(end_bit_index+1):-start_bit_index]
        return int(x=data_slice, base=2)


class BASE_TRANSACTION:

    def to_string(self, attrs=None):
        self_str = ""
        for attr, value in vars(self).items():
            if attrs is None or attr in attrs:
                if value is not None and value is not DoNotCheck:
                    if attr in self._get_attr_to_print_in_hex():
                        self_str += attr.upper() + ": " + hex(value) + ", "
                    elif attr in self._get_attr_to_print_in_bytes():
                        self_str += attr.upper() + ": " + DATA_CONVERSION_UTILS.bytes_to_str(value) + ", "
                    else:
                        self_str += attr.upper() + ": " + str(value) + ", "

        return "{0:<16} {1}".format(type(self).__name__ + ":", self_str.rstrip(", "))

    def _get_attr_to_print_in_hex(self):
        return []

    def _get_attr_to_print_in_bytes(self):
        return []

    def _get_needed_attributes(self):
        return None

    def check_tran_values(self):
            needed_attrs_without_values = list()
            non_needed_attrs_with_values = list()
            needed_attrs = self._get_needed_attributes()

            if needed_attrs is not None:
                for attr, value in vars(self).items():
                    if attr in needed_attrs and value is None:
                        needed_attrs_without_values.append(attr.upper())
                    elif attr not in needed_attrs and value is not None and value is not DoNotCheck:
                        non_needed_attrs_with_values.append(attr.upper())

            return needed_attrs_without_values, non_needed_attrs_with_values

    def get_attrs(self):
        return [attr for attr, value in vars(self).items() if (value is not DoNotCheck and value is not None)]

    def get_uri(self):
        raise NotImplementedError()

    def get_time(self):
        raise NotImplementedError()



class SB_TRANSACTION_BASE(BASE_TRANSACTION):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck, opcode=None, addr=None, data=None, sai=None):
        self.time = time
        self.uri = uri
        self.addr = addr
        self.opcode = opcode
        self.data = data
        self.sai = sai

    def get_src(self):
        raise NotImplementedError()

    def get_dest(self):
        raise NotImplementedError()


class SB_TRANSACTION(SB_TRANSACTION_BASE):

    def __init__(self, time=DoNotCheck, uri=DoNotCheck, msg_type=None, src_pid=None, dest_pid=None, opcode=None,
                 tag=None, misc=None, eh=None, byte_en=None, fid=None, bar=None, addr_len=None, rsp=None,
                 sai=None, addr=None, data=None):
        super().__init__(time=time, uri=uri, opcode=opcode, addr=addr, data=data, sai=sai)
        self.msg_type = msg_type
        self.src_pid = src_pid
        self.dest_pid = dest_pid
        self.tag = tag
        self.misc = misc
        self.eh = eh
        self.byte_en = byte_en
        self.fid = fid
        self.bar = bar
        self.addr_len = addr_len
        self.rsp = rsp

    def get_uri(self):
        return self.uri

    def get_time(self):
        return self.time

    def get_src(self):
        return self.src_pid

    def get_dest(self):
        return self.dest_pid

    def _get_attr_to_print_in_hex(self):
        return ["addr", "byteen", "src_pid", "dest_pid", "sai"]

    def _get_attr_to_print_in_bytes(self):
        return ["data"]
