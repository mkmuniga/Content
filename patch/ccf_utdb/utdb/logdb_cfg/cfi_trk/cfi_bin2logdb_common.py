#!/usr/intel/bin/python3.6.3a
import sys, os, re, inspect
#try:
#    from agents.soc_common_base.soc_systeminit import soc_systeminit
#    si = soc_systeminit.get_pointer()
#    soc_cfi_be_zero_data_chk_en = bool(si.get_si_val_by_name("SOC_CFI_BE_ZERO_DATA_CHK"))
#except:
#    soc_cfi_be_zero_data_chk_en = False

from val_uvm_tracker import *
import tableWriter

#---------------------------------------------------------
# global vars definition
class glob:
    err_occured = 0

test_dir = "."
if ('TEST_WORK_AREA' in os.environ):
    test_dir = os.environ["TEST_WORK_AREA"]

#-------------------------------------------------------
# Find systeminit knob in systeminit.dut_cfg file by grep
# Can't use systeminit UTDB solution.
#-------------------------------------------------------
def get_knob_from_systeminit(knob, default):
    cmd = "zegrep \"" + knob + "\" " + test_dir + "/systeminit*/systeminit.dut_cfg* "
    output = subprocess.getoutput([cmd + " 2>/dev/null"])
    val = default;
    if (output != ""):
        match = re.search("= (\d+)", output)
        val = (match.group(1) == "1")
    return val

#-------------------------------------------------------
cfi_be_zero_data_chk_en = get_knob_from_systeminit("CFI_BE_ZERO_DATA_CHK", True)
cfi_unused_bits_chk_en  = get_knob_from_systeminit("CFI_UNUSED_BITS_CHK", True)

#-------------------------------------------------------
def create_report_message(time,msg,file,line):
    report_message = f"VAL_UTDB_ERROR {file}({line}) @ {str(time)}ps: " \
                     f"cfi_bin2logdb [cfi_bin2logdb] {msg}\n"
    glob.err_occured = 1
    return report_message

#-------------------------------------------------------
def unused_bits_chk(line, header_payload, unused_bits_mask):
    if (not cfi_unused_bits_chk_en): return
    value = line[header_payload]         # take header or payload value
    if ((value & unused_bits_mask) != 0):
       err_time = line['TIME']
       err_uri  = line['URI_LID']
       err_msg  = 'Unused bits not zero: %s=%x, mask=%x, URI=%s' % (header_payload, line[header_payload], unused_bits_mask, err_uri)
       print(create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)

#-------------------------------------------------------
def null_packet_bits_chk(value, header_payload, vc_name):
    if (not cfi_unused_bits_chk_en): return
    if (value.IsUnknown()):
        err_msg  = "Null_packet %s on %s has Xs: %s=%s" % (header_payload, vc_name, header_payload, str(txn.header))
        err_time = get_sim_time()
        print(create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
        return

    val = value.ToUint()                # take header or payload value
    if (val != 0):
        err_time = get_sim_time()
        err_msg  = 'Null_packet %s=%x on %s - should be zero' % (header_payload, val, vc_name)
        print(create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)

#-------------------------------------------------------
def uri2str(uri):
    temp_src = re.sub('URI_', '', uri.Source.Name().upper())
    inst = uri.Instance.ToUint()
    cntr = uri.Cntr.ToUint()
    if temp_src == 'NA':
        return temp_src
    elif any([suburi in temp_src for suburi in ["COR", "IAC", "ACF", "ICE", "ATOM"]]):
        thread = 0 if uri.Thread.IsUnknown() else uri.Thread.ToUint()
        return "%s_%XT%X_%X" % (temp_src, inst, thread, cntr)
    else:
        return "%s_%03X_%X" % (temp_src, inst, cntr)

#-------------------------------------------------------
def decode_id(id, mapping):
    if (id in mapping):
        name = '%s(%0x)' % (mapping[id], id)
    else:
        name = 'E:(%0x)' % id;
    return (name)

#-------------------------------------------------------
def decode_name(id, mapping):
    if (id in mapping):
        name = mapping[id]
    else:
        name = 'E:%0x' % id;
    return (name)

#-------------------------------------------------------
def decode_key(id, mapping):
    if (id in mapping):
        name = mapping[id]
    else:
        name = 'E:(%s)' % id;
    return (name)

#-------------------------------------------------------
def get_vc_name(source):
    vc_name = ''
    # special handling for C2C internal MUX
    if (re.search("c2c_cfi_mux", source)):
        match = re.search("(\w+)\.(\w+)\.(\w+)\.hw_collector", source)
        if match:
            inst1 = match.group(1).upper()
            inst2 = match.group(3).upper()
            inst1 = re.sub('^U_C2C_TI', '', inst1)
            inst1 = re.sub('^_', '', inst1)
            inst2 = re.sub('CFI_BFM_INTERNAL_NEAR_CFI_MUX_FROM_', '', inst2)
            vc_name = "%s_%s_INTERNAL_MUX" % (inst1, inst2)
            vc_name = re.sub('^_', '', vc_name)
            return(vc_name)
    source = re.sub(".genblk\d+", "", source)
    source = re.sub("\.hw_collector\.cfi_bfm", "", source, flags=re.I)
    source = re.sub('\[', '', source)
    source = re.sub('\]', '', source)
    match = re.search("(\w+)?\.?(\w+)_hw_collector", source, re.IGNORECASE)
    if match:
        inst = match.group(1).upper()
        inst = re.sub('^U_', '', inst)
        inst = re.sub('^(\w+)_TI', '', inst)
        vc_name = "%s_%s" % (inst, match.group(2).upper())
    vc_name = re.sub('INST_', '', vc_name)
    vc_name = re.sub('TI','', vc_name)
    vc_name = re.sub('_$', '', vc_name)
    vc_name = re.sub('\w+_TB_','',vc_name)
    vc_name = re.sub('\w+_SOC_CFI_','SOC_CFI_',vc_name)
    vc_name = re.sub('__','_',vc_name)
    vc_name = re.sub('_VC$', '', vc_name)
    vc_name = re.sub('^_','',vc_name)
    vc_name = re.sub('^CFI_','',vc_name)
    vc_name = re.sub('^SOUTH_','',vc_name)
    return (vc_name)

# ---------------------------------------------------------
# Convert interleaved addr bits (even/odd) into full address
# ---------------------------------------------------------
def get_interleaved_address(addr0, addr1, start_bit):
    addr = 0
    for i in range(start_bit,46):
        # take even bits from addr0, odd - from addr1
        if (i % 2):
            a = addr1 & 1
            addr1 >>= 1
        else:
            a = addr0 & 1
            addr0 >>= 1
        # shift bit to the right position
        a <<= i
        addr += a
    return (addr)

# ---------------------------------------------------------
# Convert interleaved bits (even/odd) into full bits vector
# ---------------------------------------------------------
def get_interleaved_bits(bits0, bits1, start_bit, end_bit):
    bits_vec = 0
    for i in range(start_bit, end_bit):
        # take even bits from bits0, odd - from bits1
        if (i % 2):
            a = bits1 & 1
            bits1 >>= 1
        else:
            a = bits0 & 1
            bits0 >>= 1
        # shift bit to the right position
        a <<= i
        bits_vec += a
    return (bits_vec)

# ---------------------------------------------------------
# Construct key using URI, VC_NAME and PROTOCOL_ID
# ---------------------------------------------------------
def get_addr_hash_key(line):
    key = ("%s_%s_%s_%s") % (line['URI_TID'], line['URI_LID'], line['VC_NAME'], line['PROTOCOL_ID'])
    return key

# ---------------------------------------------------------
# Construct key using URI, PROTOCOL_ID, and RTID (data forwarding case)
# ---------------------------------------------------------
def get_addr_hash_key_with_rtid(line):
    key = ("%s_%s_%s_%0d") % (line['URI_TID'], line['URI_LID'], line['PROTOCOL_ID'], line['RTID'])
    return key

# ---------------------------------------------------------
# Construct key using URI, PROTOCOL_ID, and HTID (UPI snp case)
# ---------------------------------------------------------
def get_addr_hash_key_with_htid(line):
    key = ("%s_%s_%s_%0d") % (line['URI_TID'], line['URI_LID'], line['PROTOCOL_ID'], line['HTID'])
    return key

# ---------------------------------------------------------
def calc_parity(n):
    ones = 0
    n = bin(n)[2:]
    for i in n:
        if i == '1':
            ones += 1
    return ones % 2

# ---------------------------------------------------------
def idbe_unpack(DataIn, Full):
    Hole = 0
    DataOut = 0

    if (Full == 1):
        DataOut = DataIn
        ByteEn = 0xFF
    else:
        ByteEn = DataIn & 0xFF
        # find the hole - the first invalid data byte
        for b in range(0, 8):
            if ((ByteEn >> b) & 1 == 0):
                Hole = b
                break
        # place the data
        for b in range(0, 8):
            if (b == Hole):
                data = 0
            elif (b < Hole):
                data = (DataIn >> 8*(b+1)) & 0xFF
            else:
                data = (DataIn >> (8*b)) & 0xFF
            DataOut += (data << (8*b))
    return (DataOut, ByteEn)

# ---------------------------------------------------------
def print_idbe_data(line, header):
    data = line['PAYLOAD']
    idbe = line['IDBE'] & 0xF
    be_str = ''
    be_int = 0
    par_err = 0
    sig_par = line['D_PAR']
    for i in range(0,4):
        data_str = ''
        datain = (data >> (64*i)) & 0xFFFFFFFFFFFFFFFF
        # get parity and compare with parity signal
        parity = calc_parity(datain)
        par    = sig_par & 1
        sig_par >>= 1
        if (parity != par):
            par_err = 1

        full   = (idbe >> i) & 1
        (dataout, be) = idbe_unpack(datain, full)
        if (args.logdb is not None):
            print_data = 0
            for b in range(0,8):
                mask = (0xFF << (8*b))
                if ((be >> b) & 1):
                    print_data += (dataout & mask)
                else:
                    print_data += mask
                    #- - - - - - - - - - - - - - - - - -
                    # data byte must be 0 if be=0
                    #- - - - - - - - - - - - - - - - - -
                    if (cfi_be_zero_data_chk_en and (dataout & mask) != 0):
                        err_data = (dataout & mask) >> (8*b)
                        b = 8*i + b
                        err_time = line['TIME']
                        err_msg  = "%s - BE=0 but DATA[%d]=%x, should be 0 (URI=%s)" % (line['VC_NAME'], b, err_data, line['URI_LID'])
                        print(create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
            line['DATA'+str(i)] = print_data
            be_int += (be << (8*i))
        if (args.text is not None):
            for b in range(0,8):
                if ((be >> b) & 1):
                    data_str = "%02x%s" % ((dataout >> (8*b)) & 0xFF, data_str)
                else:
                    data_str = "--%s" % (data_str)
            #be_str = "%02x%s" % (be, be_str)
            line['DATA_'+str(i)] = data_str
    line['BE'] = be_int
    if (par_err):
        line['PAR_ERR'] = line['PAR_ERR'] + "D"

    if (line['PROTOCOL_ID'] == "IDI.C"):
        bogus    = (header >> 1) & 0x1             # bit[1]
        fullline = (header >> 2) & 0x1             # bit[2]
        misc_str = "FullLine=%x bogus=%x" % (fullline, bogus)
        line['MISC']     = misc_str
        line['FULLLINE'] = fullline
        line['BOGUS']    = bogus

# ---------------------------------------------------------
def print_full_data(line):
    data = line['PAYLOAD']
    par_err = 0
    sig_par = line['D_PAR']
    for i in range(0,4):
        datain = (data >> (64*i)) & 0xFFFFFFFFFFFFFFFF
        # get parity and compare with parity signal
        parity = calc_parity(datain)
        par    = sig_par & 1
        sig_par >>= 1
        if (parity != par):
            par_err = 1

        if (args.logdb is not None):
            line['DATA'+str(i)] = datain
        if (args.text is not None):
            line['DATA_'+str(i)] = "%016x" % (datain)

    line['BE']    = 0xFFFFFFFF
    if (par_err):
        line['PAR_ERR'] = line['PAR_ERR'] + "D"
