from agents.ccf_common_base.ccf_coh_defines import CCF_COH_DEFINES
from val_utdb_base_components import val_utdb_component
from val_utdb_bint import bint
from agents.ccf_common_base.ccf_ral_agent import ccf_ral_agent


class hash_calc_agent(val_utdb_component):
    def __init__(self):

        self.ccf_ral_agent_i = ccf_ral_agent.create()

        # On nem test the hash_mask register is not configured so we use the default value in the register
        if(self.si.is_nem_test):
            self.hash_mask = ccf_ral_agent.read_reg_field_at_eot(self.ccf_ral_agent_i,"cbregs_all0","LOCAL_HOME_SLICE_HASH","Hash_Bit0_mask")
        else:
            self.hash_mask = self.si.mem_hash_mask

    def get_hash(self, address):
        addr = bint(int(address, 16))
        mask = int(self.hash_mask)

        hash_result = 0
        addr_and_mask = mask & addr[CCF_COH_DEFINES.hash_msb:CCF_COH_DEFINES.hash_lsb]
        for it in range(CCF_COH_DEFINES.hash_msb-CCF_COH_DEFINES.hash_lsb+1):
            hash_result = hash_result ^ addr_and_mask[it]
        return hash_result

def main():
    mem_hash_chk_i = hash_calc_agent.get_pointer()
    print(mem_hash_chk_i.get_exp_dest_id("7f1340"))

if __name__ == "__main__":
    main()
