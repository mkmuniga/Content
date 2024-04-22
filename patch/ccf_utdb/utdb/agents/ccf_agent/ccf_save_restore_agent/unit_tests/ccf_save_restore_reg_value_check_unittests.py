from val_utdb_report import val_utdb_error
from val_utdb_unit_test import val_utdb_unit_test

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_defs import *
from agents.ccf_agent.ccf_save_restore_agent.unit_tests.ccf_save_restore_checker_unittest_mocks import \
    TestableSaveRestoreAgent, my_read_reg
from agents.ccf_agent.ccf_save_restore_agent.unit_tests.save_restore_header_attributes import *

SBO_SRFSM_REG = 'ccf_gpsb_top.santa0_regs.DPT_Config'
CBO0_SRFSM_REG = 'ccf_gpsb_top.egress_0.ak_egr_ctl'
CBO1_SRFSM_REG = 'ccf_gpsb_top.egress_1.ak_egr_ctl'


# /nfs/site/proj/lnl/lnl.ccf_ddg.integ/USERS/swhaley/lnl_temp/save_restore_checker/target/ccf/onesource/os_rdl/gpsb
class SaveRestoreUnittests(val_utdb_unit_test):
    def setUp(self):
        self._create_workarea_if_none_exists()
        # log to push_rows to
        ral_log = self.create_logdb_from_header("registers_logdb", registers_utdb_header_attributes)
        sb_srfsm_log = self.create_logdb_from_header("merged_sb_logdb", sb_trk_utdb_header_attributes)
        self.sb = SrfsmSbLogger(sb_srfsm_log)
        self._unit_test_setup()
        self.initial_agent_under_test(TestableSaveRestoreAgent)
        self.expected_errors = []
        self.save_val = 0
        self.restore_val = 0

    # need to mock ral env
    def my_read_reg(self, hdl_path, time, x_to_0=False, obj=None):
        if time > 1:
            return self.restore_val
        return self.save_val

    def mock_py_ral(self):
        # Assign the custom read function to all registers
        for reg in self.agent.ccf_ral_agent_i.top.get_registers():
            reg.register_hdl_read_func(my_read_reg)

    def run_checker(self):
        self.pre_run()
        self.agent.run()

    def set_reg_save_and_restore_val(self, reg, save, restore):
        self.save_val = save
        self.restore_val = restore
        reg = self.agent.ccf_ral_agent_i.top.get_reg_by_name(reg)
        reg.register_hdl_read_func(self.my_read_reg)

    def set_sbo_reg_save_and_restore_val(self, save, restore):
        self.save_val = save
        self.restore_val = restore
        reg = self.agent.ccf_ral_agent_i.top.get_reg_by_name(SBO_SRFSM_REG)
        reg.register_hdl_read_func(self.my_read_reg)

    def send_cbo_srfsm_sr_commands(self, group='0'):
        self.sb.add(time=1, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data=f'2042fff{group}')
        self.sb.add(time=2, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.sb.add(time=5, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000',data=f'2041fff{group}')
        self.sb.add(time=7, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)

    def send_sbo_srfsm_sr_commands(self, group='2'):
        self.sb.add(time=1, trk=PMC_GPSB_SB_LOG, ldst_pid=SBO_SRFSM_PID, address='0x0000', data=f'2042fff{group}')
        self.sb.add(time=2, trk=PMC_GPSB_SB_LOG, lsrc_pid=SBO_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.sb.add(time=5, trk=PMC_GPSB_SB_LOG, ldst_pid=SBO_SRFSM_PID, address='0x0000',data=f'2041fff{group}')
        self.sb.add(time=7, trk=PMC_GPSB_SB_LOG, lsrc_pid=SBO_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)

    def run_and_check_errors(self):
        self.agent.run()
        actual_errors = self.get_val_utdb_errors_list()
        print(actual_errors)
        self.assertEqual(self.expected_errors, actual_errors)

    def test_PASSES_when_register_in_cbo_srfsm_rom_is_save_restored(self):
        self.send_cbo_srfsm_sr_commands()
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(CBO0_SRFSM_REG, 2, 2)
        self.run_and_check_errors()

    def test_PASSES_when_register_in_sbo_srfsm_rom_is_save_restored(self):
        self.send_sbo_srfsm_sr_commands()
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(SBO_SRFSM_REG, 2, 2)
        self.run_and_check_errors()

    def test_FAILS_when_register_in_cbo_srfsm_rom_is_save_restored_to_incorrect_val(self):
        self.send_cbo_srfsm_sr_commands()
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(CBO0_SRFSM_REG, 2, 10)
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: save value does not match restore value', time=7))
        self.run_and_check_errors()

    def test_FAILS_when_register_in_cbo1_srfsm_rom_is_save_restored_to_incorrect_val(self):
        self.send_cbo_srfsm_sr_commands(group='2')
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(CBO1_SRFSM_REG, 2, 10)
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: save value does not match restore value', time=7))
        self.run_and_check_errors()

    def test_FAILS_when_register_in_sbo_srfsm_rom_is_save_restored_to_incorrect_val(self):
        self.send_sbo_srfsm_sr_commands()
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(SBO_SRFSM_REG, 2, 10)
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: save value does not match restore value', time=7))
        self.run_and_check_errors()

    def test_PASSES_when_group_zero_is_save_restored_and_incorrect_reg_is_in_group_2(self):
        self.send_sbo_srfsm_sr_commands('0')
        self.pre_run()
        self.mock_py_ral()
        self.set_reg_save_and_restore_val(SBO_SRFSM_REG, 2, 10)
        self.run_and_check_errors()



    # def test_get_all_save_restore_regs(self):
    #     self.pre_run()
    #     with open('save_restore_regs.txt', 'a') as f:
    #         reg_names = ['l3_protected_ways',
    #                         'ni_control',
    #                         'MKTME_KEYID_MASK',
    #                         'cbomcastat',
    #                         'cbomcaconfig',
    #                         'cbregs_spare',
    #                         'mc_ctl',
    #                         'ccf_input_read_counter',
    #                         'ccf_input_write_counter',
    #                         'NCRADECS_OVRD',
    #                         'safbar_comp_allowed_list0',
    #                         'safbar_comp_allowed_list1',
    #                         'safbar_comp_allowed_list2',
    #                         'safbar_comp_allowed_list3',
    #                         'regbar_epmask0',
    #                         'regbar_epmask1',
    #                         'regbar_epmask2',
    #                         'regbar_epmask3',
    #                         'regbar_epmask4',
    #                         'regbar_epmask5',
    #                         'regbar_epmask6',
    #                         'regbar_epmask7',
    #                         'safbar_soc_allowed_list0',
    #                         'uncore_demand_req_memory_priority_0',
    #                         'uncore_prefetch_req_memory_priority_0',
    #                         'NcuLocalFunnyIOOvr',
    #                         'NcuGlobalFunnyIOOvr',
    #                         'NcuCfiPacketOrdering',
    #                         'LTCtrlSts',
    #                         'pam0_0_0_0_pci',
    #                         'pam1_0_0_0_pci',
    #                         'pam2_0_0_0_pci',
    #                         'pam3_0_0_0_pci',
    #                         'pam4_0_0_0_pci',
    #                         'pam5_0_0_0_pci',
    #                         'pam6_0_0_0_pci',
    #                         'egr_misc_cfg',
    #                         'mc_status',
    #                         'general_config1',
    #                         'general_config2',
    #                         'dbp_arac_cntrl',
    #                         'flow_cntrl',
    #                         'ia_cos_ways',
    #                         'CBO_COH_CONFIG_CLIENT',
    #                         'cbopmonct0',
    #                         'cbopmonctrstatus_counter0ovf',
    #                         'cbopmonct1',
    #                         'cbopmonctrstatus_counter1ovf',
    #                         'pmon_ctr_0',
    #                         'pmon_ctr_1',
    #                         'pmon_ctr_status',
    #                         'NcuEvOveride',
    #                         'tx_queues_credit_init',
    #                         'rx_queues_credit_init',
    #                         'CFI_CRDT_CTRL',
    #                         'DPT_RWM']
    #         for reg in self.agent.ccf_ral_agent_i.top.get_registers():
    #             if self.is_save_restore(reg) and self.is_gpsb_reg(reg):
    #                 if reg.Name not in reg_names:
    #                     f.write(self.format_string(reg.Name))
    #                     reg_names.append(reg.Name)
    #     f.close()
    #
    # def format_string(self, reg_name):
    #     return f'include_reg (.*{reg_name}.*)\n'
    #
    # def is_save_restore(self, reg):
    #     return 'SaveRestore' in reg
    #
    # def is_gpsb_reg(self, reg):
    #     return 'ccf_gpsb_top' in reg.get_full_name()


