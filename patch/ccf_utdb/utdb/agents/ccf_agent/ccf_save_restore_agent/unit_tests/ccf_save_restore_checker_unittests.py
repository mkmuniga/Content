import unittest
from val_utdb_report import val_utdb_error
from val_utdb_unit_test import val_utdb_unit_test

from agents.ccf_agent.ccf_save_restore_agent.checkers.ccf_save_restore_checker_defs import *
from agents.ccf_agent.ccf_save_restore_agent.unit_tests.ccf_save_restore_checker_unittest_mocks import \
    TestableSaveRestoreAgent, my_read_reg
from agents.ccf_agent.ccf_save_restore_agent.unit_tests.save_restore_header_attributes import *


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

    def mock_py_ral(self):
        # Assign the custom read function to all registers
        for reg in self.agent.ccf_ral_agent_i.top.get_registers():
            reg.register_hdl_read_func(my_read_reg)

    def run_checker(self):
        super().pre_run()
        self.mock_py_ral()
        self.agent.run()

    def send_cbo_srfsm_sr_commands(self):
        self.sb.add(time=1, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='20423210')
        self.sb.add(time=2, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.sb.add(time=5, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000',data='20413210')
        self.sb.add(time=7, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)

    def run_and_check_errors(self):
        self.run_checker()
        actual_errors = self.get_val_utdb_errors_list()
        self.assertEqual(self.expected_errors, actual_errors)

    def test_PASSES_when_save_and_restore_are_to_same_group(self):
        self.send_cbo_srfsm_sr_commands()
        self.run_and_check_errors()

    def test_FAIL_when_restore_with_out_save(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG,ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041fff0')
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Restore Command issued for group that has never been saved', time=8))
        self.run_and_check_errors()

    def test_FAIL_when_save_with_out_restore(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042fff0')
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Save Command issued that was never followed by a restore', time=8))
        self.run_and_check_errors()

    def test_FAILS_when_save_and_restore_are_to_different_groups(self):
        # Save to group 0 and 1
        self.sb.add(time=8, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042ff10')
        # restore to group 0 and 2
        self.sb.add(time=12, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID,address='0x0000', data='2041ff20')

        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Restore Command issued for group that has never been saved', time=12))
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Save Command issued that was never followed by a restore', time=8))

        self.run_and_check_errors()

    def test_FAILS_when_two_restores_to_the_same_group(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042fff0')
        self.sb.add(time=12, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041fff0')
        self.sb.add(time=13, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041fff0')
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Restore Command issued for group that was already restored', time=13))
        self.run_and_check_errors()

    def test_FAILS_when_two_saves_to_the_same_group(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042fff0')
        self.sb.add(time=9,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042fff0')
        self.sb.add(time=12, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041fff0')
        self.expected_errors.append(val_utdb_error(msg=f'Save Restore Checker: Save Command issued for group that has already been saved', time=9))
        self.run_and_check_errors()

    def test_PASSES_when_two_saves_pair_perfectly_with_one_restore(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042ff10')
        self.sb.add(time=9,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042fff2')
        self.sb.add(time=11, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.sb.add(time=12, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041f210')
        self.sb.add(time=14, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.run_and_check_errors()

    def test_PASSES_when_one_save_pairs_perfectly_with_two_restores(self):
        self.sb.add(time=8,  trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2042f210')
        self.sb.add(time=11, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.sb.add(time=12, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041ff10')
        self.sb.add(time=13, trk=PMC_GPSB_SB_LOG, ldst_pid=CBO_PAIR_0_SRFSM_PID, address='0x0000', data='2041ff2f')
        self.sb.add(time=14, trk=PMC_GPSB_SB_LOG, lsrc_pid=CBO_PAIR_0_SRFSM_PID, address='0x0010', opcode=VIRTUAL_WIRE)
        self.run_and_check_errors()


if __name__ == '__main__':
    unittest.main()
