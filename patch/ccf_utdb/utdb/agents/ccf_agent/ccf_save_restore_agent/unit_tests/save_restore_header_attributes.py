

#had to modify headers to match format for some reason
sb_trk_utdb_header_attributes = [
{ 'name': 'TIME', 'header_type': 'int'},
{ 'name': 'TRACKER', 'header_type': 'text'},
{ 'name' : 'TYPE', 'header_type': 'text'},
{ 'name' : 'ADDRESS', 'header_type': 'text'},
{ 'name' : 'LSPID', 'header_type': 'text'},
{ 'name' : 'LDPID', 'header_type': 'text'},
{ 'name' : 'OPC', 'header_type': 'text'},
{ 'name' : 'TAG', 'header_type': 'text'},
{ 'name' : 'BE', 'header_type': 'text'},
{ 'name' : 'RSP', 'header_type': 'text'},
{ 'name' : 'DATA', 'logdb_field_type': 'text'},
{ 'name' : 'DIR', 'header_type': 'text'},
{ 'name' : 'MISC', 'header_type': 'text'},
{ 'name' : 'FID', 'header_type': 'text'},
{ 'name' : 'SAI', 'header_type': 'text'}
]


class SrfsmSbLogger:
    def __init__(self, db):
        self.db = db

    def add(self, time=0, trk = '', type ='0', address = 0, lsrc_pid ='0', ldst_pid ='0', tag='0', opcode='0', be='0', rsp='0', data='0', dir='agent', misc='', fid=''):
        self.db.push_row(time, trk, type, address, lsrc_pid, ldst_pid, opcode, tag, be, rsp, data, dir, misc, fid)

registers_utdb_header_attributes = [
{ 'name' : 'TIME', 'header_type': 'bigint'},
{ 'name' : 'UNIT', 'header_type': 'text'},
{ 'name' : 'SIGNAL_PATH', 'header_type': 'text'},
{ 'name' : 'TYPE', 'header_type': 'text'},
{ 'name' : 'REG', 'header_type': 'text'},
{ 'name' : 'FIELD', 'header_type': 'text'},
{ 'name' : 'VALUE', 'header_type': 'bigint'},
]

merged_ccf_header_attributes = [
            {'name':'TIME', 'header_type':'int'},
            {'name':'UNIT', 'header_type':'string'},
            {'name':'TID', 'header_type':'string'},
            {'name':'LID', 'header_type':'string'},
            {'name':'PID', 'header_type':'string'},
            {'name':'ADDRESS', 'header_type':'string'},
            {'name':'OPCODE', 'header_type':'string'},
            {'name':'TYPE', 'header_type':'string'},
            {'name':'HASH', 'header_type':'string'},
            {'name':'CQID', 'header_type':'string'},
            {'name':'UQID', 'header_type':'string'},
            {'name':'LPID', 'header_type':'string'},
            {'name':'SRC_TGT', 'header_type':'string'},
            {'name':'PARITY', 'header_type':'string'},
            {'name':'DATA_ERR', 'header_type':'string'},
            {'name':'POISON', 'header_type':'string'},
            {'name':'ATTRIBUTES', 'header_type':'string'},
            {'name':'CHUNK', 'header_type':'string'},
            {'name':'DATA', 'header_type':'string'}]