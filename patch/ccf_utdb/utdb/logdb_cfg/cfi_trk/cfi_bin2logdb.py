#!/usr/intel/bin/python3.6.3a
import sys, os, re, inspect, queue, argparse

from val_uvm_tracker import *
import tableWriter
from cfi_bin2logdb_types import *
import cfi_bin2logdb_common as common


#################################################################
# Non-readable format: with header, payload
################################################################
class cfi_packets(val_uvm_tracker):
    trans_list = []

    #-------------------------------------------------------
    def build_phase(self, phase):
        self.add_source_to_cb_mapping({source:self.cfi_trans})

        if args.logdb is not None:
            self.logdb_writer = tableWriter.tableWriter(
                storage = tableWriter.STORAGE.LOGDB,
                path = logdbs[0],
                page = 100)

        if args.text is not None:
            self.text_writer = tableWriter.tableWriter(
                path = texts[0],
                storage = tableWriter.STORAGE.FILE,
                page = 100)

        if (args.logdb is not None):
            for h in trk_header_logdb:
                self.logdb_writer.add_header(**h)
        if (args.text is not None):
            for h in trk_header_text:
                self.text_writer.add_header(**h)

    #-------------------------------------------------------
    def final_print(self):
        self.print_logdb()
        if (args.logdb is not None):
            self.logdb_writer.close_writer()
        if (args.text is not None):
            self.text_writer.close_writer()

    #-------------------------------------------------------
    def final_phase(self, phase):
        self.final_print()

    #-------------------------------------------------------
    def cfi_trans(self, source, txn):
        if 'crd_hw_collector' in source:
            return
        for port in EXCLUDE_CFI_PORT_LIST:
            if (re.search(port, source)): return    # exclude records
        interface = ''
        if os.environ.get('IS_EMULATION'):
            if (not (txn)):
                return
            if hasattr(txn, 'txn'):
                pass
            else:
                return
        txn = txn.txn
        #IsUnknown()
        #ToUint()
        #Name()
        trans_values = {}
        trans_values['TIME'] = get_sim_time()
        trans_values['URI_TID']  = '-' if txn.uri.TID.IsUnknown() else common.uri2str(txn.uri.TID)
        trans_values['URI_LID']  = '-' if txn.uri.LID.IsUnknown() else common.uri2str(txn.uri.LID)
        trans_values['URI_PID']  = '-' if txn.uri.PID.IsUnknown() else common.uri2str(txn.uri.PID)
        if ('req_transmit' in source):
            interface = 'TRANSMIT_CFI_REQ_0'
        if ('req_receive' in source):
            interface = 'RECEIVE_CFI_REQ_0'
        if ('rsp_transmit' in source):
            interface = 'TRANSMIT_CFI_RSP_0'
        if ('rsp_receive' in source):
            interface = 'RECEIVE_CFI_RSP_0'
        if ('data_transmit' in source):
            interface = 'TRANSMIT_CFI_DATA_0'
        if ('data_receive' in source):
            interface = 'RECEIVE_CFI_DATA_0'
        vc_name                       = common.get_vc_name(source)
        trans_values['VC_NAME']       = vc_name
        #set subnet name
        subnet_name = "UNDEF"
        if vc_name in MAINNOC :
             subnet_name = "MAINNOC"
        if vc_name in MEMSS :
             subnet_name = "MEMSS"
        if vc_name in EXTERNAL :
             subnet_name = "EXTERNAL"

        trans_values['SUBNET_NAME']   = subnet_name

        trans_values['INTERFACE']     = interface
        trans_values['IS_NULL']       = -1 if txn.null_packet.IsUnknown() else txn.null_packet.ToUint()
        trans_values['PROTOCOL_ID']   = "%x" % (txn.protocol_id.ToUint())
        trans_values['RCTRL']         = -1 if txn.rctrl.IsUnknown() else txn.rctrl.ToUint()
        trans_values['TRACE_PKT']     = -1 if txn.trace_packet.IsUnknown() else txn.trace_packet.ToUint()
        trans_values['VC_ID']         = "%x" % (txn.vc_id.ToUint())
        trans_values['SHARED_CREDIT'] = txn.shared_credit.ToUint()
        trans_values['DST_ID']        = "%x" % (txn.dst_id.ToUint())
        trans_values['HEADER']        = "%x" % (txn.header.ToUint())

        # flag err in case of X's
        if (re.search("DATA", interface)):
            trans_values['PAYLOAD']   = txn.payload                 # may have X's
            if txn.payload.IsUnknown():
                err_time = trans_values['TIME']
                err_uri  = trans_values['URI_LID']
                err_msg  = "PAYLOAD on %s ifc has Xs: URI=%s" % (vc_name, err_uri)
                print(common.create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
                trans_values['PAYLOAD'] = "%x" % 0x0badbadbadbadbad_0badbadbadbadbad_0badbadbadbadbad_0badbadbadbadbad
            else:
                trans_values['PAYLOAD'] = "%x" % trans_values['PAYLOAD'].ToUint()

        # first pass: add to the transactions list
        if ("DATA" in interface):
            trans_values['EOP'] = txn.eop.ToUint()
            # by default we are working with 256 bits DATA flits
            # use CFI_config dictionary to set the 512 bits indication together with header_size(88 bits)
            match = re.search("(\S+)\.hw_collector", source)
            if (not match):
                match = re.search("(\S+)_hw_collector", source)
            if (match):
                path = match.group(1)
                path = re.sub('.*\.', '', path)
                path = re.sub('_CFI', '', path)
                header_size = 44
                if (re.search("TRANSMIT", interface) and path in CFI_config_tx and CFI_config_tx[path] >= 80):    # TX width 86 or 88
                    header_size = CFI_config_tx[path]
                if (re.search("RECEIVE", interface)  and path in CFI_config_rx and CFI_config_rx[path] >= 80):    # RX width 86 or 88
                    header_size = CFI_config_rx[path]
                if (header_size >= 80):
                    header_size = int(header_size / 2);
                    # one flit config: double header and payload 512 bits
                    data0 = trans_values.copy()
                    data1 = trans_values.copy()
                    header0 = int(data0['HEADER'], 16)
                    header1 = header0
                    header0 &= ((1<<header_size) - 1)
                    header1 >>= header_size
                    data0['HEADER'] = "%x" % header0
                    data1['HEADER'] = "%x" % header1
                    payload0 = int(data0['PAYLOAD'], 16)
                    payload1 = payload0
                    payload0 &= ((1<<256) - 1)
                    payload1 >>= 256
                    data0['PAYLOAD'] = "%x" % payload0
                    data1['PAYLOAD'] = "%x" % payload1
                    self.trans_list.append(data0)
                    self.trans_list.append(data1)
                else:
                    self.trans_list.append(trans_values)
        else:
            trans_values['EOP'] = -1
            self.trans_list.append(trans_values)

    #-------------------------------------------------------
    def print_logdb(self):
        for trans in self.trans_list:
            if (args.logdb is not None):
                self.logdb_writer.push_row(**trans)
            if (args.text is not None):
                self.text_writer.push_row(**trans)

################################################################
# Readable format: with Opcodes, Ids, Data e.t.c
################################################################
class cfi_tracker(val_uvm_tracker):
    trans_list = []
    ifc = dict()
    address_hash = dict()

    #-------------------------------------------------------
    def build_phase(self, phase):
        self.add_source_to_cb_mapping({source:self.cfi_trans})

        if args.logdb is not None:
            self.logdb_writer = tableWriter.tableWriter(
                storage = tableWriter.STORAGE.LOGDB,
                path = logdbs[0],
                page = 100)

        if args.text is not None:
            self.text_writer = tableWriter.tableWriter(
                path = texts[0],
                storage = tableWriter.STORAGE.FILE,
                page = 100)

        if (args.logdb is not None):
            for h in full_logdb_header:
                self.logdb_writer.add_header(**h)
        if (args.text is not None):
            for h in full_trk_header:
                self.text_writer.add_header(**h)

    #-------------------------------------------------------
    def final_print(self):
        self.print_logdb()
        if (args.logdb is not None):
            self.logdb_writer.close_writer()
        if (args.text is not None):
            self.text_writer.close_writer()

    #-------------------------------------------------------
    def final_phase(self, phase):
        # in the first pass the transactions were saved in the list
        # now do the second pass
        self.unpack()
        # print final results to logdb
        self.final_print()

        if (common.glob.err_occured): sys.exit(1)

    #-------------------------------------------------------
    def cfi_trans(self, source, txn):
        if 'crd_hw_collector' in source:
            return
        # exclude VC_NAMEs
        if (re.search("hbo_cfi_io", source)): return    # generic sniffer packets

        interface = ''
        vc_name = common.get_vc_name(source)
        if ('INTERNAL_MUX' not in vc_name):
            vc_name = re.sub('CFI_', '', vc_name)
            vc_name = re.sub('_CFI', '', vc_name)
        clk_cnt = txn.clock_counter.ToUint()
        txn = txn.txn

        # if null packet = X, skip it
        if (txn.null_packet.IsUnknown()):
            return
        # if null packet, do the header/payload check
        if (txn.null_packet.ToUint() == 1):
            common.null_packet_bits_chk(txn.header, "HEADER", vc_name)
            if ('data' in source):
                common.null_packet_bits_chk(txn.payload, "PAYLOAD", vc_name)
            return

        trans_values = {}
        trans_values['TIME'] = get_sim_time()
        trans_values['CLK_CNT'] = clk_cnt
        trans_values['VC_NAME'] = vc_name
        trans_values['URI_TID']  = '-' if txn.uri.TID.IsUnknown() else common.uri2str(txn.uri.TID)
        trans_values['URI_LID']  = '-' if txn.uri.LID.IsUnknown() else common.uri2str(txn.uri.LID)
        trans_values['URI_PID']  = '-' if txn.uri.PID.IsUnknown() else common.uri2str(txn.uri.PID)
        if ('req_transmit' in source):
            interface = 'TRANSMIT_REQ_0'
        if ('req_receive' in source):
            interface = 'RECEIVE_REQ_0'
        if ('rsp_transmit' in source):
            interface = 'TRANSMIT_RSP_0'
        if ('rsp_receive' in source):
            interface = 'RECEIVE_RSP_0'
        if ('data_transmit' in source):
            interface = 'TRANSMIT_DATA_0'
        if ('data_receive' in source):
            interface = 'RECEIVE_DATA_0'
        trans_values['INTERFACE']     = interface
        trans_values['PROTOCOL_ID']   = txn.protocol_id.ToUint()
        trans_values['RCTRL']         = -1 if txn.rctrl.IsUnknown() else txn.rctrl.ToUint()
        trans_values['TRACE_PKT']     = -1 if txn.trace_packet.IsUnknown() else txn.trace_packet.ToUint()
        trans_values['VC_ID']         = txn.vc_id.ToUint()
        trans_values['DST_ID']        = common.decode_name(txn.dst_id.ToUint(), AGENT_TYPE)
        trans_values['DST_ID_VAL']    = txn.dst_id.ToUint()
        trans_values['DSTID']         = common.decode_id(txn.dst_id.ToUint(), AGENT_TYPE)           # decode with ID
        if txn.header.IsUnknown():
            err_time = trans_values['TIME']
            err_msg  = "HEADER on %s ifc has Xs: %s" % (vc_name, str(txn.header))
            print(common.create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
            self.final_print()
            sys.exit(1)
        trans_values['HEADER']        = txn.header.ToUint()

        # flag err in case of X's
        if ("DATA" in interface):
            trans_values['PAYLOAD']   = txn.payload                 # may have X's
            if txn.payload.IsUnknown():
                err_time = trans_values['TIME']
                err_uri  = trans_values['URI_LID']
                err_msg  = "PAYLOAD on %s ifc has Xs: URI=%s" % (vc_name, err_uri)
                print(common.create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
                trans_values['PAYLOAD'] = 0x0badbadbadbadbad_0badbadbadbadbad_0badbadbadbadbad_0badbadbadbadbad
            else:
                trans_values['PAYLOAD'] = trans_values['PAYLOAD'].ToUint()


        # first pass: add to the transactions list
        if ("DATA" in interface):
            trans_values['PAR_ERR'] = ''
            trans_values['EOP'] = txn.eop.ToUint()
            # by default we are working with 256 bits DATA flits
            # use CFI_config dictionary to set the 512 bits indication together with header_size(88 bits)
            match = re.search("(\S+)\.hw_collector", source)
            if (not match):
                match = re.search("(\S+)_hw_collector", source)
            if (match):
                path = match.group(1)
                path = re.sub('.*\.', '', path)
                path = re.sub('_CFI', '', path)
                header_size = 54
                if (re.search("TRANSMIT", interface) and path in CFI_config_tx and CFI_config_tx[path] >= 80):    # TX width 86 or 88
                    header_size = CFI_config_tx[path]
                if (re.search("RECEIVE", interface)  and path in CFI_config_rx and CFI_config_rx[path] >= 80):    # RX width 86 or 88
                    header_size = CFI_config_rx[path]
                if (header_size >= 80):
                    header_size = int(header_size / 2);
                    # one flit config: double header and payload 512 bits
                    data0 = trans_values.copy()
                    data1 = trans_values.copy()
                    data0['HEADER'] = txn.header[header_size - 1:0].ToUint()
                    data1['HEADER'] = txn.header[(header_size * 2) - 1:header_size].ToUint()
                    data0['PAYLOAD'] = txn.payload[256:1].ToUint()
                    data1['PAYLOAD'] = txn.payload[522:267].ToUint()
                    data0['D_PAR'] = txn.payload[260:257].ToUint()
                    data1['D_PAR'] = txn.payload[526:523].ToUint()
                    data0['POSION'] = txn.payload[0].ToUint()
                    data1['POSION'] = txn.payload[266].ToUint()
                    data0['IDBE'] = txn.payload[264:261].ToUint()
                    data1['IDBE'] = txn.payload[530:527].ToUint()
                    data0['I_PAR'] = txn.payload[265].ToUint()
                    data1['I_PAR'] = txn.payload[531].ToUint()

                    self.trans_list.append(data0)
                    self.trans_list.append(data1)
                else:
                    trans_values['POSION'] = txn.payload[0].ToUint()
                    trans_values['PAYLOAD'] = txn.payload[256:1].ToUint()
                    trans_values['D_PAR'] = txn.payload[260:257].ToUint()
                    trans_values['IDBE'] = txn.payload[264:261].ToUint()
                    trans_values['I_PAR'] = txn.payload[265].ToUint()
                    self.trans_list.append(trans_values)
        else:
            self.trans_list.append(trans_values)

    #-------------------------------------------------------
    def get_ifc_key(self, vc_name, interface, protocol_id, vc_id):
        match = re.search("TRANSMIT_DATA_(\d+)", interface)
        if match:
            ifc_key = vc_name + "_T" + match.group(1)
        match = re.search("RECEIVE_DATA_(\d+)", interface)
        if match:
            ifc_key = vc_name + "_R" + match.group(1)
        ifc_key = ifc_key + "_" + protocol_id + "_" + vc_id
        return (ifc_key)

    # ---------------------------------------------------------
    def get_data_from_hash(self, ifc_key, time=0):
        if (not self.ifc[ifc_key]["data"].empty()):
            return self.ifc[ifc_key]["data"].get()
        else:
            err_msg  = "No pair for Data record for ifc_key="+ifc_key+"\nCheck, maybe payload is 520 bits width."
            print(common.create_report_message(time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)
            # after the error return empty line, need to stop to proceed further msgs
            return ""

    #-------------------------------------------------------
    def unpack(self):
        for line in self.trans_list:
            uri         = line['URI_LID']
            vc_name     = line['VC_NAME']
            interface   = line['INTERFACE']
            protocol_id = line['PROTOCOL_ID']
            vc_id       = line['VC_ID']
            header      = line['HEADER']
            match = re.search('(TRANSMIT|RECEIVE)_(\w+)_', interface)
            if match: channel = match.group(2)    # REQ/RSP/DATA

            vc_id_key = "%d,%d,%s" % (protocol_id, vc_id, channel)
            line['PROTOCOL_ID'] = common.decode_key(protocol_id, PROTOCOL_NAME)
            line['VC_ID']       = common.decode_key(vc_id_key, VC_ID_NAME)
            line['VC_ID_VAL']   = vc_id
            line['ADDRESS']     = 0xDEADBEEF    # undefined value
            line['LINE_ADDR']   = 0xDEADBEEF    # undefined value

            #- - - - - - - - - - - - - - - - - - - - - -
            if (channel == 'REQ'):
                line['PKT_TYPE'] = ''
                if (vc_id in [0,1,3]):
                    self.unpack_uxi_req(line, vc_id, header)
                    line['record_type'] = 'uxi_req'

                # all protocols have address is the same position
                # add to the hash and print later
                addr   = ((header >> 39) & 0x3FFF_FFFF_FFFF)     # bits[84:39]
                addr <<= 6
                line['LINE_ADDR'] = addr
                # get parity and compare with parity signal
                parity = common.calc_parity(addr)
                if (parity != line['A_PAR']):
                    line['PAR_ERR'] = "A"

                line['ADDRESS'] = addr
                addr_hash_key = common.get_addr_hash_key(line)
                if (uri != '-'): self.address_hash[addr_hash_key] = addr

                #if (line['PKT_TYPE'] == "SA-S"):            # UXI snoop with option to forward data, if rspid != HBO
                #    #rspid = (header >> 69) & 0xFF           # bits[76:69]
                #    #rspto = common.decode_name(rspid, AGENT_TYPE)
                #    #if (rspto in ["HBO_0", "HBO_1"]):       # to HBO with HTID
                #    #    addr_hash_key = common.get_addr_hash_key_with_htid(line)
                #    #else:
                #    #    addr_hash_key = common.get_addr_hash_key_with_rtid(line)
                #    addr_hash_key = common.get_addr_hash_key_with_htid(line)    # temporary in LNL-M
                #    if (uri != '-'): self.address_hash[addr_hash_key] = addr

                elif (line['PKT_TYPE'] == "SA-SL"):         # UXI snoop with data to HBO
                    addr_hash_key = common.get_addr_hash_key_with_htid(line)
                    if (uri != '-'): self.address_hash[addr_hash_key] = addr

            #- - - - - - - - - - - - - - - - - - - - - -
            elif (channel == 'RSP'):
                if (protocol_id == 1):
                    self.unpack_uxi_rsp(line, header, protocol_id)
                    line['record_type'] = 'uxi_rsp'

            #- - - - - - - - - - - - - - - - - - - - - -
            elif (channel == 'DATA'):
                ifc_key = self.get_ifc_key(vc_name, interface, line['PROTOCOL_ID'], line['VC_ID'])
                # create a Queue for the first time
                if (ifc_key not in self.ifc):
                    self.ifc[ifc_key] = {}
                    self.ifc[ifc_key]["data"] = queue.Queue()

                # put msg to FIFO
                self.ifc[ifc_key]["data"].put(line)

                if (protocol_id == 1):
                    line['record_type'] = 'uxi_data'

        # Data pkts located in a separate Queue
        # Unpack it now
        self.unpack_data()

        #- - - - - - - - - - - - - - - - - - - - - -
        # print address according to URI
        for line in self.trans_list:
            # do not update if already set before
            if (line['ADDRESS'] != 0xDEADBEEF): continue
            uri = line['URI_LID']
            addr_hash_key = common.get_addr_hash_key(line)
            if (uri != '-' and addr_hash_key in self.address_hash):
                line['ADDRESS'] = self.address_hash[addr_hash_key]
                line['LINE_ADDR'] = line['ADDRESS'] & ~0x3F

    # ---------------------------------------------------------
    def unpack_uxi_req(self, line, vc_id, header):
        opcode   = (header & 0xFF)                   # bits[7:0]    MsgClass & Opcode
        msgclass = (header >> 5 & 0x7)               # bits[7:5]    MsgClass
        addr_par = (header >> 38) & 0x1              # bit [38]

        line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        line['MSG_CLASS_VAL'] = msgclass
        if (vc_id in [0, 3]):        # A2F req (UXI_REQ, UXI_WBR)
            line['OPCODE'] = common.decode_name(opcode, UXI_REQ_OPCODE) if vc_id == 0 else  common.decode_name(opcode, UXI_DATA_OPCODE)
            line['OPCODE_VAL'] = opcode & 0x1F
            line['PKT_TYPE'] = "SA"
            rtid = (header >> 8) & 0x3FFF            # bits[21:8]
            crnid = (header >> 22) & 0xFF            # bits[29:22]
            clos = (header >> 30) & 0x1F             # bits[34:30]
            tee = (header >> 85) & 0x1               # bits[85:85]
            rspid= (header >> 106) & 0xFF            # bits[113:106]
            line['CLOS'] = clos
            line['TEE'] = tee
            misc_str = "clos=%x tee=%d" % (clos, tee)
            line['MISC']    = misc_str
            common.unused_bits_chk(line, "HEADER", 0x0_03FF_FFC0_0000_0000_0038_0000_0000)         # bits [105:86], [37:35]
        else:                   # F2A req (UXI_SNP)
            line['OPCODE'] = common.decode_name(opcode, UXI_SNP_OPCODE)
            line['OPCODE_VAL'] = opcode >> 3
            line['PKT_TYPE'] = common.decode_name(opcode, UXI_SNP_PKT_TYPE)
            rtid = (header >> 8) & 0x3FFF            # bits[21:8]
            crnid = (header >> 22) & 0xFF            # bits[29:22]
            cdnid = (header >> 30) & 0xFF            # bits[37:30]
            tee = (header >> 85) & 0x1               # bits[85:85]
            htid = (header >> 86) & 0xFFFF           # bits[101:86]
            hnid = (header >> 102) & 0xF             # bits[105:102]
            rspid= (header >> 106) & 0xFF            # bits[113:106]
            misc_str = "tee=%d" % (tee)
            line['CDNID'] = cdnid
            line['HTID'] = htid
            line['TEE'] = tee
            line['HNID'] = hnid
            line['MISC'] = misc_str
            if (line['PKT_TYPE'] == "SA-SL"):
                common.unused_bits_chk(line, "HEADER", 0x3_FC00_0000_0000_0000_0000_3FFF_FF00)         # bits [113:106], [29:8]
        line['A_PAR'] = addr_par

        # SA-SL msgs do not have RSP_ID and RTID
        if (line['PKT_TYPE'] != "SA-SL"):
            line['CRNID'] = common.decode_name(crnid, AGENT_TYPE)
            line['CRNID_VAL'] = crnid
            line['RSP_ID'] = common.decode_name(rspid, AGENT_TYPE)
            line['RSP_ID_VAL'] = rspid
            line['RSPID'] = common.decode_id(rspid, AGENT_TYPE)
            line['RTID']  = rtid

    # ---------------------------------------------------------
    def unpack_uxi_rsp(self, line, header, protocol_id):
        opcode   = (header & 0xFF)                   # bits[7:0]    MsgClass & Opcode
        msgclass = (header >> 5 & 0x7)               # bits[7:5]    MsgClass
        misc_str = ''
        pkt_type = common.decode_name(opcode, UXI_RSP_PKT_TYPE)
        if pkt_type in ["SR-U", "SR-O"]:
            rtid = (header >> 9)  & 0x3FFF       # bits[22:9]
            pcls = (header >> 23) & 0x7          # bits[25:23]
            tee = (header >> 8) & 0x1
            line['PCLS'] = pcls                  
            line['TEE'] = tee
            line['RTID'] = rtid
            if pkt_type == "SR-O":
                mem_loc = ((header >> 34) & 0x1)
                line['MEM_LOC'] = mem_loc
                misc_str = "pcls=%x, tee=%x, mem_loc=%x" % (pcls, tee, mem_loc)
            else:
                misc_str = "pcls=%x, tee=%x" % (pcls, tee)
                common.unused_bits_chk(line, "HEADER", 0x4_0000_0000)
        elif (pkt_type == "SR-H"):
            htid    = (header >> 9) & 0xFFFF     # bits[24:9]
            hdnid   = (header >> 26) & 0xF       # bits[29:26]
            tsx_abort = (header >> 34) & 0x1      # bits[34:34]
            tee = ((header >> 8) & 0x1)
            line['HTID'] = htid
            line['HDNID'] = hdnid
            line['TEE'] = tee
            line['TSX_ABORT'] = tsx_abort
            misc_str = "tsx_abort=%x, tee=%x" % (tsx_abort, tee)
            # snoop rsp is correlated with HTID
            addr_hash_key = common.get_addr_hash_key_with_htid(line)
            uri     = line['URI_LID']
            if (uri != '-' and addr_hash_key in self.address_hash):
                line['ADDRESS'] = self.address_hash[addr_hash_key]
                line['LINE_ADDR'] = line['ADDRESS'] & ~0x3F
            common.unused_bits_chk(line, "HEADER", 0x3_C200_0000)

        line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        line['MSG_CLASS_VAL'] = msgclass
        line['OPCODE'] = common.decode_name(opcode, UXI_RSP_OPCODE)
        line['OPCODE_VAL'] = opcode >> 3
        line['PKT_TYPE'] = pkt_type
        line['MISC'] = misc_str

    # ---------------------------------------------------------
    def unpack_data(self):
        for ifc_key in self.ifc:
            while (not self.ifc[ifc_key]["data"].empty()):
                pkt0_line = self.ifc[ifc_key]["data"].get()

                #- - - - - - - - - - - - - - - - - - - - - -
                protocol_id = pkt0_line['PROTOCOL_ID']
                vc_id       = pkt0_line['VC_ID']

                if (protocol_id == 'UXI'):
                    self.unpack_uxi_data(pkt0_line, ifc_key, protocol_id, vc_id)

    # ---------------------------------------------------------
    def unpack_uxi_data(self, pkt0_line, ifc_key, protocol_id, vc_id):
        header = pkt0_line['HEADER']
        opcode = (header & 0xFF)                   # bits[7:0]    MsgClass & Opcode
        pkt_type = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        if pkt_type == "SR-CD":
            self.unpack_uxi_sr_cd_data_chunk(pkt0_line, ifc_key, protocol_id, pkt_type)
        
        elif pkt_type == "SR-HD":
            self.unpack_uxi_sr_hd_data_chunk(pkt0_line, ifc_key, protocol_id, pkt_type)
        
        elif (pkt_type == "SA-D"):
            self.unpack_uxi_sa_d_data(pkt0_line, ifc_key, protocol_id)

        elif (pkt_type == "PW"):
            self.unpack_uxi_pw_data(pkt0_line, ifc_key, protocol_id)

        elif (pkt_type == "PR"):
            self.unpack_uxi_pr_data(pkt0_line, ifc_key)

        elif (pkt_type == "NCM"):
            self.unpack_uxi_ncm_data(pkt0_line, ifc_key)

        else:
            pkt0_line['OPCODE'] = common.decode_name(opcode, UXI_DATA_OPCODE)
            pkt0_line['OPCODE_VAL'] = opcode >> 3
            err_time = pkt0_line['TIME']
            err_uri  = pkt0_line['URI_LID']
            err_msg  = "Invalid Data opcode="+pkt0_line['OPCODE']+" (URI=" + err_uri + ")"
            #FIXME: in FC C_D2D drives wrong opcode
            #print(common.create_report_message(err_time, err_msg, __file__, inspect.currentframe().f_lineno), file=sys.stderr)

    # ---------------------------------------------------------
    def unpack_uxi_sa_d_data(self, pkt0_line, ifc_key, protocol_id):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        uri     = pkt0_line['URI_LID']
        header0 = pkt0_line['HEADER']
        header1 = pkt1_line['HEADER']

        opcode  = (header0 & 0xFF)                  # bits[7:0]    MsgClass & Opcode
        msgclass = (header0 >> 5 & 0x7)             # bits[2:0]    MsgClass
        addr_par = (header1 >> 26) & 0x1            # bit [26]

        addr0   = ((header0 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr1   = ((header1 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr    = common.get_interleaved_address(addr0, addr1, 6)
        pkt0_line['LINE_ADDR'] = addr
        pkt1_line['LINE_ADDR'] = addr
        pkt0_line['ADDRESS'] = addr
        pkt1_line['ADDRESS'] = addr
        addr_hash_key = common.get_addr_hash_key(pkt0_line)
        if (uri != '-'): self.address_hash[addr_hash_key] = addr

        rtid     = (header0 >> 8) & 0x3FFF           # bits[41:32]
        crnid    = (header1 & 0xFF)                  # bits[7:0]
        rsp_id0  = (header0 >> 50) & 0xF             # bits[53:50]
        rsp_id1  = (header1 >> 50) & 0xF             # bits[53:50]
        rspid    = rsp_id0 + (rsp_id1 << 4)
        
        mem_loc  = ((header0 >> 25) & 0x1)           # bits[25]
        tee      = ((header0 >> 26) & 0x1)           # bits[26]
        clos     = ((header1 >> 8) & 0x1F)           # bits[12:8]
        
        pkt0_line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE'] = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['RTID']   = rtid
        pkt0_line['RSP_ID'] = common.decode_name(rspid, AGENT_TYPE)
        pkt0_line['RSP_ID_VAL'] = rspid
        pkt0_line['RSPID']  = common.decode_id(rspid, AGENT_TYPE)
        pkt0_line['CRNID']  = common.decode_name(crnid, AGENT_TYPE)
        pkt0_line['CRNID_VAL'] = crnid
        pkt0_line['A_PAR'] = addr_par
        pkt0_line['I_PAR'] = None
        pkt1_line['MSG_CLASS'] = pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL']= pkt0_line['MSG_CLASS_VAL']
        pkt1_line['OPCODE'] = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['RTID']   = rtid
        pkt1_line['RSP_ID'] = pkt0_line['RSP_ID']
        pkt1_line['RSP_ID_VAL'] = rspid
        pkt1_line['RSPID']  = pkt0_line['RSPID']
        pkt1_line['CRNID']  = pkt0_line['CRNID']
        pkt1_line['CRNID_VAL'] = crnid
        pkt1_line['A_PAR'] = addr_par
        pkt1_line['I_PAR'] = None

        pkt0_line['MEM_LOC'] = mem_loc
        pkt1_line['MEM_LOC'] = mem_loc
        pkt0_line['TEE']    = tee
        pkt1_line['TEE']    = tee
        pkt0_line['CLOS']   = clos
        pkt1_line['CLOS']   = clos
        misc_str = "mem_loc=%x tee=%x clos=%x" % (mem_loc, tee, clos)
        pkt0_line['MISC'] = misc_str
        pkt1_line['MISC'] = misc_str

        pkt0_line['CHUNK']  = 0
        pkt1_line['CHUNK']  = 1

        if common.calc_parity(addr) != addr_par:
            pkt0_line['PAR_ERR'] += "A"
            pkt1_line['PAR_ERR'] += "A"

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x00_0000_01C0_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x00_0000_03FF_E000)
        
        common.print_full_data(pkt0_line)
        common.print_full_data(pkt1_line)

    # ---------------------------------------------------------
    def unpack_uxi_pw_data(self, pkt0_line, ifc_key, protocol_id):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        uri     = pkt0_line['URI_LID']
        header0 = pkt0_line['HEADER']
        header1 = pkt1_line['HEADER']

        opcode   = (header0 & 0xFF)                 # bits[7:0]    MsgClass & Opcode
        msgclass = ((header0 >> 5) & 0x7)           # bits[2:0]    MsgClass

        addr0    = ((header0 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr1    = ((header1 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr_par = (header1 >> 26) & 0x1            # bit [26]
        addr_low = ((header0 >> 22) & 0x7)           # bits[24:22]
        addr_low = (addr_low << 3)
        addr     = common.get_interleaved_address(addr0, addr1, 6) + addr_low
        
        pkt0_line['ADDRESS'] = addr
        pkt1_line['ADDRESS'] = addr
        pkt0_line['LINE_ADDR'] = addr & ~0x3F
        pkt1_line['LINE_ADDR'] = addr & ~0x3F
        pkt0_line['LOW_ADDR'] = addr_low 
        pkt1_line['LOW_ADDR'] = addr_low 
        addr_hash_key = common.get_addr_hash_key(pkt0_line)
        if (uri != '-'): self.address_hash[addr_hash_key] = addr

        rtid     = (header0 >> 8) & 0x3FFF           # bits[21:8]
        crnid    = (header1 & 0xFF)                  # bits[7:0]
        rsp_id0  = (header0 >> 50) & 0xF             # bits[53:50]
        rsp_id1  = (header1 >> 50) & 0xF             # bits[53:50]
        rspid    = rsp_id0 + (rsp_id1 << 4)

        tee      = ((header0 >> 26) & 0x1)           # bits[26]
        sai      = ((header1 >> 8) & 0xFF)                  # bits[7:0]    SAI
        
        pkt0_line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE'] = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['CHUNK']  = 0
        pkt0_line['RTID']   = rtid
        pkt0_line['RSP_ID'] = common.decode_name(rspid, AGENT_TYPE)
        pkt0_line['RSP_ID_VAL'] = rspid
        pkt0_line['RSPID']  = common.decode_id(rspid, AGENT_TYPE)
        pkt0_line['CRNID']  = common.decode_name(crnid, AGENT_TYPE)
        pkt0_line['CRNID_VAL'] = crnid
        pkt0_line['A_PAR'] = addr_par
        pkt1_line['MSG_CLASS'] = pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL']= pkt0_line['MSG_CLASS_VAL']
        pkt1_line['OPCODE'] = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['CHUNK']  = 1
        pkt1_line['RTID']   = rtid
        pkt1_line['RSP_ID'] = pkt0_line['RSP_ID']
        pkt1_line['RSP_ID_VAL'] = rspid
        pkt1_line['RSPID']  = pkt0_line['RSPID']
        pkt1_line['CRNID']  = pkt0_line['CRNID']
        pkt1_line['CRNID_VAL'] = crnid
        pkt1_line['A_PAR'] = addr_par

        pkt0_line['TEE']    = tee
        pkt1_line['TEE']    = tee
        pkt0_line['SAI']    = sai
        pkt1_line['SAI']    = sai
        misc_str = "sai=%02x, tee=%x" % (sai, tee)
        
        pkt0_line['MISC'] = misc_str
        pkt1_line['MISC'] = misc_str

        pkt0_line['CHUNK']  = 0
        pkt1_line['CHUNK']  = 1

        if common.calc_parity(addr) != addr_par:
            pkt0_line['PAR_ERR'] += "A"
            pkt1_line['PAR_ERR'] += "A"

        if common.calc_parity(pkt0_line['IDBE']) != pkt0_line['I_PAR']:
            pkt0_line['PAR_ERR'] += "I"

        if common.calc_parity(pkt1_line['IDBE']) != pkt1_line['I_PAR']:
            pkt1_line['PAR_ERR'] += "I"

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x00_0000_0200_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x00_0000_03FF_0000)

        common.print_idbe_data(pkt0_line, header0)
        common.print_idbe_data(pkt1_line, header1)

    # ---------------------------------------------------------
    def unpack_uxi_pr_data(self, pkt0_line, ifc_key):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        uri     = pkt0_line['URI_LID']
        header0 = pkt0_line['HEADER']
        header1 = pkt1_line['HEADER']

        opcode   = (header0 & 0xFF)                  # bits[7:0]    MsgClass & Opcode
        msgclass = ((header0 >> 5) & 0x7)            # bits[7:5]    MsgClass

        addr0     = ((header0 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr1     = ((header1 >> 27) & 0x3FFFFF)        # bits[49:27]
        addr_low0 = ((header0 >> 22) & 0x7)             # bits[24:22]
        addr_low1 = ((header1 >> 22) & 0x7)             # bits[24:22]
        addr_low  = (addr_low0 << 3) + addr_low1
        addr_par  = (header1 >> 26) & 0x1               # bit [26]
        length    = ((header1 >> 16) & 0x3F)            # bits[21:16]
        addr    = common.get_interleaved_address(addr0, addr1, 6)
        full_addr  = addr + addr_low
        pkt0_line['ADDRESS'] = full_addr
        pkt1_line['ADDRESS'] = full_addr
        pkt0_line['LINE_ADDR'] = full_addr & ~0x3F
        pkt1_line['LINE_ADDR'] = full_addr & ~0x3F
        pkt0_line['LOW_ADDR'] = addr_low 
        pkt1_line['LOW_ADDR'] = addr_low 
        addr_hash_key = common.get_addr_hash_key(pkt0_line)
        if (uri != '-'): self.address_hash[addr_hash_key] = full_addr

        rtid     = (header0 >> 8) & 0x3FFF           # bits[21:8]
        crnid    = (header1 & 0xFF)                  # bits[7:0]
        rsp_id0  = (header0 >> 50) & 0xF             # bits[53:50]
        rsp_id1  = (header1 >> 50) & 0xF             # bits[53:50]
        rspid    = rsp_id0 + (rsp_id1 << 4)

        tee      = ((header1 >> 26) & 0x1)           # bits[26]
        sai      = ((header1 >> 8) & 0xFF)           # bits[15:8]   SAI

        pkt0_line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE'] = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['CHUNK']  = 0
        pkt0_line['RTID']   = rtid
        pkt0_line['LEN']    = length
        pkt0_line['SAI']    = sai
        pkt0_line['RSP_ID'] = common.decode_name(rspid, AGENT_TYPE)
        pkt0_line['RSP_ID_VAL'] = rspid
        pkt0_line['RSPID']  = common.decode_id(rspid, AGENT_TYPE)
        pkt0_line['CRNID']  = common.decode_name(crnid, AGENT_TYPE)
        pkt0_line['CRNID_VAL'] = crnid
        pkt0_line['A_PAR'] = addr_par
        pkt0_line['I_PAR'] = None
        pkt0_line['D_PAR'] = None
        pkt1_line['MSG_CLASS'] = pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL']= pkt0_line['MSG_CLASS_VAL']
        pkt1_line['OPCODE'] = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['CHUNK']  = 1
        pkt1_line['RTID']   = rtid
        pkt1_line['LEN']    = length
        pkt1_line['SAI']    = sai
        pkt1_line['RSP_ID'] = pkt0_line['RSP_ID']
        pkt1_line['RSP_ID_VAL'] = rspid
        pkt1_line['RSPID']  = pkt0_line['RSPID']
        pkt1_line['CRNID']  = pkt0_line['CRNID']
        pkt1_line['CRNID_VAL'] = crnid
        pkt1_line['A_PAR'] = addr_par
        pkt1_line['I_PAR'] = None
        pkt1_line['D_PAR'] = None

        misc_str = "sai=%02x length=%02x, tee=%x" % (sai, length, tee)
        pkt0_line['MISC'] = misc_str
        pkt1_line['MISC'] = misc_str

        if common.calc_parity(addr) != addr_par:
            pkt0_line['PAR_ERR'] += "A"
            pkt1_line['PAR_ERR'] += "A"

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x00_0000_0200_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x00_0000_0200_0000)
        common.unused_bits_chk(pkt0_line, 'PAYLOAD', 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF)
        common.unused_bits_chk(pkt1_line, 'PAYLOAD', 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF)

    # ---------------------------------------------------------
    def unpack_uxi_ncm_data(self, pkt0_line, ifc_key):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        header0 = pkt0_line['HEADER']
        header1 = pkt1_line['HEADER']

        opcode   = (header0 & 0xFF)                  # bits[7:0]    MsgClass & Opcode
        msgclass = ((header0 >> 5) & 0x7)            # bits[7:5]    MsgClass
        
        rtid     = (header0 >> 8) & 0x3FFF           # bits[21:8]
        crnid    = (header1 & 0xFF)                  # bits[7:0]
        cdnid    = ((header0 >> 27) & 0xFF)          # bits[34:27]
        rsp_id0  = (header0 >> 50) & 0xF             # bits[53:50]
        rsp_id1  = (header1 >> 50) & 0xF             # bits[53:50]
        rspid    = rsp_id0 + (rsp_id1 << 4)

        sai      = ((header1 >> 8) & 0xFF)           # bits[15:8]   SAI
        msg_type = (header1 >> 16) & 0x3F            # bits[21:16]
        paramA0  = (header0 >> 22) & 0xF             # bits[25:22]
        paramA1  = (header1 >> 22) & 0xF             # bits[25:22]
        paramA   = common.get_interleaved_bits(paramA0, paramA1, 0, 8) 
        
        pkt0_line['MSG_CLASS'] = common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE'] = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['CHUNK']  = 0
        pkt0_line['RTID']   = rtid
        pkt0_line['RSP_ID'] = common.decode_name(rspid, AGENT_TYPE)
        pkt0_line['RSP_ID_VAL'] = rspid
        pkt0_line['RSPID']  = common.decode_id(rspid, AGENT_TYPE)
        pkt0_line['CRNID']  = common.decode_name(crnid, AGENT_TYPE)
        pkt0_line['CRNID_VAL'] = crnid
        pkt0_line['CDNID']  = common.decode_name(cdnid, AGENT_TYPE)
        pkt0_line['CDNID_VAL'] = cdnid
        pkt0_line['A_PAR'] = None
        pkt0_line['I_PAR'] = None
        pkt1_line['OPCODE'] = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['MSG_CLASS'] = pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL'] = pkt0_line['MSG_CLASS_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['CHUNK']  = 1
        pkt1_line['RTID']   = rtid
        pkt1_line['RSP_ID'] = pkt0_line['RSP_ID']
        pkt1_line['RSP_ID_VAL'] = rspid
        pkt1_line['RSPID']  = pkt0_line['RSPID']
        pkt1_line['CRNID']  = pkt0_line['CRNID']
        pkt1_line['CRNID_VAL'] = crnid
        pkt1_line['CDNID']  = pkt0_line['CDNID']
        pkt1_line['CDNID_VAL'] = cdnid
        pkt1_line['A_PAR'] = None
        pkt1_line['I_PAR'] = None

        if (pkt0_line['OPCODE'] == 'NcMsgB'):
            msg_type_str = common.decode_id(msg_type, UXI_NCM_MSGB_TYPE)
        else:
            msg_type_str = common.decode_id(msg_type, UXI_NCM_MSGS_TYPE)
        misc_str = "sai=%02x paramA=%02x msg_type=%s" % (sai, paramA, msg_type_str)
        pkt0_line['MISC'] = misc_str
        pkt0_line['SAI'] = sai
        pkt0_line['PARAMA'] = paramA
        pkt0_line['MSG_TYPE'] = msg_type
        pkt1_line['MISC'] = misc_str
        pkt1_line['PARAMA'] = paramA
        pkt1_line['MSG_TYPE'] = msg_type
	
        if "LTDoorbell" in  msg_type_str:
            pkt0_line["ADDRESS"] = ((pkt0_line["PAYLOAD"] >> 0x1) & 0x1FFFFF)
            pkt1_line["ADDRESS"] = pkt0_line["ADDRESS"]
        
        common.print_full_data(pkt0_line)
        common.print_full_data(pkt1_line)

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x03_FFF8_0000_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x03_FFFF_FC00_0000)
    
    # ---------------------------------------------------------
    def unpack_uxi_sr_cd_data_chunk(self, pkt0_line, ifc_key, protocol_id, pkt_type):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        uri     = pkt0_line['URI_LID']
        header0 = pkt0_line['HEADER']

        opcode   = (header0 & 0xFF)                  # bits[7:0]    MsgClass & Opcode
        msgclass = ((header0 >> 5) & 0x7)            # bits[7:5]    MsgClass
        
        rtid     = (header0 >> 8) & 0x3FFF           # bits[21:8]
        cdnid    = ((header0 >> 27) & 0xFF)          # bits[34:27]

        tee     = (header0 >> 26) & 0x1              # bit [26]
        pcls    = (header0 >> 35) & 0x1F             # bits[39:35]

        pkt0_line['MSG_CLASS']= common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE']   = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['RTID']  = rtid
        pkt0_line['CDNID']  = common.decode_name(cdnid, AGENT_TYPE)
        pkt0_line['CDNID_VAL'] = cdnid
        pkt0_line['A_PAR'] = None
        pkt0_line['I_PAR'] = None
        pkt1_line['MSG_CLASS']= pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL']= pkt0_line['MSG_CLASS_VAL']
        pkt1_line['OPCODE']   = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['RTID']  = rtid
        pkt1_line['CDNID']  = pkt0_line['CDNID']
        pkt1_line['CDNID_VAL'] = cdnid
        pkt1_line['A_PAR'] = None
        pkt1_line['I_PAR'] = None

        misc_str = "pcls=%02x, tee = %x" % (pcls, tee)
        pkt0_line['MISC'] = misc_str
        pkt0_line['PCLS'] = pcls
        pkt0_line['TEE'] = tee
        pkt1_line['MISC'] = misc_str
        pkt1_line['PCLS'] = pcls
        pkt1_line['TEE'] = tee

        # snoop data is correlated with RTID
        addr_hash_key = common.get_addr_hash_key_with_rtid(pkt0_line)
        if (uri != '-' and addr_hash_key in self.address_hash):
            pkt0_line['ADDRESS'] = self.address_hash[addr_hash_key]
            pkt1_line['ADDRESS'] = self.address_hash[addr_hash_key]

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x03_FF00_03C0_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x03_FFFF_FFFF_FFFF)

        pkt0_line['LINE_ADDR'] = pkt0_line['ADDRESS']
        pkt1_line['LINE_ADDR'] = pkt0_line['ADDRESS']

        pkt0_line['CHUNK']  = 0
        pkt1_line['CHUNK']  = 1

        common.print_full_data(pkt0_line)
        common.print_full_data(pkt1_line)

    # ---------------------------------------------------------
    def unpack_uxi_sr_hd_data_chunk(self, pkt0_line, ifc_key, protocol_id, pkt_type):
        # get other line
        pkt1_line = self.get_data_from_hash(ifc_key, pkt0_line['TIME'])
        if (pkt1_line == ""): return    # err

        uri     = pkt0_line['URI_LID']
        header0 = pkt0_line['HEADER']

        opcode   = (header0 & 0xFF)                  # bits[7:0]    MsgClass & Opcode
        msgclass = ((header0 >> 5) & 0x7)            # bits[7:5]    MsgClass
        
        htid     = (header0 >> 8) & 0xFFFF           # bits[23:8]
        hdnid    = (header0 >> 27) & 0xF             # bits[30:27]

        tsx_abort = (header0 >> 25) & 0x1            # bit [25]
        tee     = (header0 >> 26) & 0x1              # bit [26]

        pkt0_line['MSG_CLASS']= common.decode_name(msgclass, UXI_MSG_CLASS)
        pkt0_line['MSG_CLASS_VAL'] = msgclass
        pkt0_line['OPCODE']   = common.decode_name(opcode, UXI_DATA_OPCODE)
        pkt0_line['OPCODE_VAL'] = opcode >> 3
        pkt0_line['PKT_TYPE'] = common.decode_name(opcode, UXI_DATA_PKT_TYPE)
        pkt0_line['HTID']  = htid
        pkt0_line['HDNID']  = common.decode_name(hdnid, AGENT_TYPE)
        pkt0_line['HDNID_VAL'] = hdnid
        pkt0_line['A_PAR'] = None
        pkt0_line['I_PAR'] = None
        pkt1_line['MSG_CLASS']= pkt0_line['MSG_CLASS']
        pkt1_line['MSG_CLASS_VAL']= pkt0_line['MSG_CLASS_VAL']
        pkt1_line['OPCODE']   = pkt0_line['OPCODE']
        pkt1_line['OPCODE_VAL'] = pkt0_line['OPCODE_VAL']
        pkt1_line['PKT_TYPE'] = pkt0_line['PKT_TYPE']
        pkt1_line['HTID']  = htid
        pkt1_line['HDNID']  = pkt0_line['HDNID']
        pkt1_line['HDNID_VAL'] = hdnid
        pkt1_line['A_PAR'] = None
        pkt1_line['I_PAR'] = None
        
        misc_str = "tsx_abort=%x, tee = %x" % (tsx_abort, tee)
        pkt0_line['MISC'] = misc_str
        pkt0_line['TSX_ABORT'] = tsx_abort
        pkt0_line['TEE'] = tee
        pkt1_line['MISC'] = misc_str
        pkt1_line['TSX_ABORT'] = tsx_abort
        pkt1_line['TEE'] = tee

        addr_hash_key = common.get_addr_hash_key_with_htid(pkt0_line)
        if (uri != '-' and addr_hash_key in self.address_hash):
            pkt0_line['ADDRESS'] = self.address_hash[addr_hash_key]
            pkt1_line['ADDRESS'] = self.address_hash[addr_hash_key]

        pkt0_line['LINE_ADDR'] = pkt0_line['ADDRESS']
        pkt1_line['LINE_ADDR'] = pkt0_line['ADDRESS']

        pkt0_line['CHUNK']  = 0
        pkt1_line['CHUNK']  = 1

        common.unused_bits_chk(pkt0_line, 'HEADER', 0x3F_FFFF_8100_0000)
        common.unused_bits_chk(pkt1_line, 'HEADER', 0x03_FFFF_FFFF_FFFF)

        common.print_full_data(pkt0_line)
        common.print_full_data(pkt1_line)


    # ---------------------------------------------------------
    def print_logdb(self):
        for trans in self.trans_list:
            t = dict(trans)

            if (args.text is not None):
                t.pop('HEADER', None)
                t.pop('PAYLOAD', None)
                t.pop('record_type', None)
                t.pop('BE', None)
                t.pop('LOW_ADDR', None)
                t.pop('LPID', None)
                t.pop('CLOS', None)
                t.pop('DST_ID', None)
                t.pop('DST_ID_VAL', None)
                t.pop('CRNID_VAL', None)
                t.pop('CDNID_VAL', None)
                t.pop('HNID_VAL', None)
                t.pop('HDNID_VAL', None)
                t.pop('VC_ID_VAL', None)
                t.pop('MSG_CLASS_VAL', None)
                t.pop('OPCODE_VAL', None)
                t.pop('RSP_ID', None)
                t.pop('RSP_ID_VAL', None)
                t.pop('PCLS', None)
                t.pop('LEN', None)
                t.pop('LENGTH', None)
                t.pop('IDBE', None)
                t.pop('SAI', None)
                t.pop('PARAMA', None)
                t.pop('TEE', None)
                t.pop('MEM_LOC', None)
                t.pop('MSG_TYPE', None)
                t.pop('LINE_ADDR', None)
                t.pop('DATA0', None)        # text trk is using DATA_0,1,2,3
                t.pop('DATA1', None)
                t.pop('DATA2', None)
                t.pop('DATA3', None)
                self.text_writer.push_row(**t)

        for trans in self.trans_list:
            payload_local = trans.pop('PAYLOAD', None)
            trans['PAYLOAD_STR'] = f'{payload_local}'

            header_local = trans.pop('HEADER', None)
            trans['HEADER'] = f'{header_local}'

            if (args.logdb is not None):
                trans.pop('DSTID', None)
                trans.pop('RSPID', None)
                trans.pop('MISC', None)
                trans.pop('DATA_0', None)
                trans.pop('DATA_1', None)
                trans.pop('DATA_2', None)
                trans.pop('DATA_3', None)
                if trans.get("record_type",None) is None:
                    print(f"ERROR: unrecognized record: " + str(trans),file=sys.stderr)
                else:
                    self.logdb_writer.push_row(**trans)

