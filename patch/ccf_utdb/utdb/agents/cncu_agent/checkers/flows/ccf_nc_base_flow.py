import copy

from val_utdb_bint import bint
from val_utdb_report import VAL_UTDB_ERROR

from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow import BASE_FLOW
from agents.cncu_agent.common.ccf_base_flow.ccf_base_flow_functions import DoNotCheck
from agents.cncu_agent.common.ccf_nc_common_base import CCF_NC_CONFIG
from agents.cncu_agent.common.cncu_defines import CFI, IDI, SB, SAI, GLOBAL
from agents.cncu_agent.common.cncu_types import CFI_TRANSACTION, UFI_TRANSACTION, SB_TRANSACTION, IDI_TRANSACTION
from agents.cncu_agent.dbs.ccf_nc_sb_db import CCF_NC_SB_DB
from agents.cncu_agent.utils.ccf_vcr_pla_handler import VCR_PLA_HANDLER
from agents.cncu_agent.utils.nc_ral_agent import NC_RAL_AGENT
from agents.cncu_agent.utils.nc_systeminit import NC_SI


class CNCU_BASE_FLOW(BASE_FLOW):
    ral_utils: NC_RAL_AGENT = NC_RAL_AGENT.get_pointer()
    si: NC_SI = NC_SI.get_pointer()
    ccf_nc_config = CCF_NC_CONFIG.get_pointer()
    sb_db: CCF_NC_SB_DB = CCF_NC_SB_DB.get_pointer()
    vcr_pla_handler: VCR_PLA_HANDLER = VCR_PLA_HANDLER
    # run_info: CCF_NC_RUN_INFO = CCF_NC_RUN_INFO.get_pointer()

    def _set_flow_info(self, flow):
        if len(self._act_flow) > 0:
            super()._set_flow_info(flow)
            self._module_id, self._lp_id = self._get_module_and_lp_ids()

    def _get_module_and_lp_ids(self):
        if type(self._get_flow_initial_tran()) == IDI_TRANSACTION:
            return self._get_flow_initial_tran().module_id, self._get_flow_initial_tran().lp_id
        return None, None

    def _get_flow_sai(self):
        if "sai" in vars(self._get_flow_initial_tran()).keys():
            return self._get_flow_initial_tran().sai
        return None

    def _get_flow_data(self):
        data = None
        self._is_ur = False
        for i in range(0, len(self._act_flow)):
            if data is not None and data[0] is not None and data[1] is not None:
                break
            if type(self._act_flow[i]) in [UFI_TRANSACTION, CFI_TRANSACTION] and CFI.has_data(self._act_flow[i].pkt_type) \
                    and not self._act_flow[i].pkt_type == CFI.PKT_TYPE.pr:
                if data is None:
                    data = [None, None]
                data[self._act_flow[i].chunk] = self._act_flow[i].data
            if type(self._act_flow[i]) == IDI_TRANSACTION and IDI.has_data(self._act_flow[i].tran_type):
                if data is None:
                    data = [None, None]
                data[self._act_flow[i].chunk] = self._act_flow[i].data
            if type(self._act_flow[i]) == SB_TRANSACTION and (self._act_flow[i].opcode == SB.OPCODES.cmpd or (self._act_flow[i].opcode == SB.OPCODES.cmp and self._act_flow[i-1].opcode in [SB.OPCODES.mem_rd,
                                                                                     SB.OPCODES.io_rd,
                                                                                     SB.OPCODES.cfg_rd,
                                                                                     SB.OPCODES.cr_rd])):
                if self._length == 0:
                    data = list()
                    if self._initial_tran.opcode == IDI.OPCODES.prd and self._act_flow[i].opcode == SB.OPCODES.cmpd:
                        if len(self._act_flow[i].data) != 4:
                            VAL_UTDB_ERROR(time=self._act_flow[0].time,
                                           msg=f"SB read request with BE=0 must return one DW of data, URI={self._uri}")
                        data = [DoNotCheck,DoNotCheck]
                    else:
                        for i in range(2):
                            data.append([bint(0xff) for j in range(32)])
                    break
                idi_data = [None for j in range(GLOBAL.cacheline_size_in_bytes)]
                ind = self._act_flow[0].addr[5:0]
                if self._act_flow[i].opcode == SB.OPCODES.cmpd:
                    sb_data = self._act_flow[i].data[int(self._act_flow[0].addr[1:0]):]
                    sb_data = sb_data[:self._length]
                else:
                    self._is_ur = True
                    if self._initial_tran.addr[31:28] in [0x4, 0x5] and self._initial_tran.opcode == IDI.OPCODES.port_in and self._sai in [SAI.sunpass, SAI.ucode]:
                        sb_data = [bint(0) for j in range(self._length)]
                    else:
                        sb_data = [bint(0xff) for j in range(self._length)]

                for i in range(self._length):
                    byte_ind = int(ind+i)
                    if byte_ind < GLOBAL.cacheline_size_in_bytes:
                        idi_data[byte_ind] = sb_data[i]
                data = [idi_data[0:32], idi_data[32:64]]
                break
        return data

    def _get_flow_byteen(self):
        be = [None, None]
        for i in range(0, len(self._act_flow)):
            if be[0] is not None and be[1] is not None:
                break
            if type(self._act_flow[i]) in [UFI_TRANSACTION, CFI_TRANSACTION] and CFI.has_byteen(self._act_flow[i].interface):
                be[self._act_flow[i].chunk] = self._act_flow[i].be
            if type(self._act_flow[i]) == IDI_TRANSACTION and IDI.has_byteen(self._act_flow[i].tran_type):
                be[self._act_flow[i].chunk] = self._act_flow[i].byteen
        return be

    def _get_flow_length(self):
        length = None
        for i in range(0, len(self._act_flow)):
            if type(self._act_flow[i]) in [UFI_TRANSACTION, CFI_TRANSACTION] and CFI.has_length(self._act_flow[i].pkt_type):
                length = self._act_flow[i].length
                break
            if type(self._act_flow[i]) == IDI_TRANSACTION and IDI.has_length(self._act_flow[i].tran_type):
                length = self._act_flow[i].length
                break
        return length

    def _get_logical_module_id(self):
        uri = self._uri
        if uri[0:7] == "COR_EMU":
            split_uri = uri.split('_')
            core = split_uri[2].split("T")[0]
            return bint(int(core, 16))
        return None

    def _for_all_modules(self, *trans, enabled_only=False):
        trans_to_modules = list()
        for tran in trans:
            for i in range(self.ccf_nc_config.num_of_modules):
                if not enabled_only or self.si.module_disable_mask[i] == 0:
                    if type(tran) is IDI_TRANSACTION:
                        tran.module_id = i
                    trans_to_modules.append(copy.deepcopy(tran))
        return trans_to_modules

    def _from_all_cbos(self, *trans, enabled_only=False):
        trans_to_cbos = list()
        for tran in trans:
            for i in range(self.si.num_of_cbo):
                if not enabled_only or self.si.cbo_disable_mask[i] == 0:
                    if type(tran) is SB_TRANSACTION:
                        tran.src_pid = SB.EPS.cbo[i]
                    trans_to_cbos.append(copy.deepcopy(tran))
        return trans_to_cbos

    def _get_pr_data(self):
        data_chunks = [[None for i in range(32)], [None for i in range(32)]]
        pr_attr = self.__get_pr_attr()
        for i in range(8):
            data_chunks[0][i] = pr_attr[7 + (8 * i): (8 * i)]
        return data_chunks

    def __get_pr_attr(self):
        pr_attr = bint(0)
        pr_attr[5:0] = self._initial_tran.addr[5:0]
        pr_attr[11:6] = self._length
        return pr_attr

    def _get_enabled_modules(self):
        enabled_modules = list()
        for i in range(self.ccf_nc_config.num_of_modules):
            if self.si.module_disable_mask[i] == 0:
                enabled_modules.append(i)
        return enabled_modules

    def _get_enabled_cbos(self):
        enabled_cbos = list()
        for i in range(self.si.num_of_cbo):
            if self.si.cbo_disable_mask[i] == 0:
                enabled_cbos.append(i)
        return enabled_cbos
