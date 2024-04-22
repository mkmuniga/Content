from val_utdb_base_components import val_utdb_component
from agents.cncu_agent.dbs.ccf_sm_qry import CCF_SM_QRY


class SM_DB(val_utdb_component):
    _sm_db: CCF_SM_QRY.SM_REC = list()

    @staticmethod
    def sm_is_empty():
        if SM_DB._sm_db == []:
            return True
        else:
            return False

    @staticmethod
    def run_db_builder(qry: CCF_SM_QRY):
        for group in qry.get_sm_records():
            for record in group.EVENTS:
                SM_DB._sm_db.append(qry.SM_REC(record))

    @staticmethod
    def get_memory_space(addr):
        for sm_rec in SM_DB._sm_db:
            if sm_rec.low_addr <= addr <= sm_rec.high_addr:
                return sm_rec.mem_space

    @staticmethod
    def is_address_inside_region(addr, region_name):
        return SM_DB.get_region(addr) == region_name

    @staticmethod
    def get_region(addr):
        for sm_rec in SM_DB._sm_db:
            if sm_rec.low_addr <= addr <= sm_rec.high_addr:
                return sm_rec.region

    @staticmethod
    def get_sub_region(addr):
        for sm_rec in SM_DB._sm_db:
            if sm_rec.low_addr <= addr <= sm_rec.high_addr:
                return sm_rec.sub_region

    @staticmethod
    def get_sub_region_by_offset(region_name, offset):
        sm_region_rec = SM_DB.get_sm_rec_by_name(region_name)
        for sm_rec in SM_DB._sm_db:
            if sm_rec.region == region_name and (sm_rec.low_addr - sm_region_rec.low_addr) <= offset <= (sm_rec.high_addr - sm_region_rec.low_addr):
                return sm_rec.sub_region

    @staticmethod
    def get_size(name):
        for sm_rec in SM_DB._sm_db:
            if name == sm_rec.mem_space or name == sm_rec.region or name == sm_rec.sub_region:
                return sm_rec.size

    @staticmethod
    def get_sm_rec_by_name(name):
        for sm_rec in SM_DB._sm_db:
            if name == sm_rec.mem_space or name == sm_rec.region or name == sm_rec.sub_region:
                return sm_rec

    @staticmethod
    def print_sm_db():
        for sm_rec in SM_DB._sm_db:
            print(sm_rec.get_sm_rec_str())

