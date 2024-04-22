# port id for the power management controller initiating??the sr_commands
#
PMA_PID = '38'

# port id for the Save Restore FSMs you want to check
SBO_SRFSM_PID = '35'
CBO_PAIR_0_SRFSM_PID = '04'

# This is the path from the model root to the ROM files, such as <rom_name>.debug files
#
MODELROOT_PATH_TO_ROMS = 'output/save_restore'

# names of roms from .debug file. Sytax: <rom_name>.debug
#
SBO_IDP_ROM = 'sbo_sb_compute0'
CBO_PAIR0_ROM = 'cbo_pma0_compute0'

#list of roms to check

ROMS = [CBO_PAIR0_ROM, SBO_IDP_ROM]


# Allow for aborted saves. This means you can see saves without restores because the overall
# cstate has been aborted.
#
ALLOW_ABORTED_SAVES_WITHOUT_RESTORES = False

# Some groups can be restored multiple times without intervening saves. For example, SAGV does one save of
# state very early, and may restore to that state again and again without ever re-saving.
# Also, some IPs contain a set of "locked" registers that are set once (for instance, by bios), and never
# change, so after the first save, they never require saving again
#
groups_that_can_restore_multiple_times_from_same_save = []

# For tightest checking, this needs to be set to True. But, if you have registers that aren't being monitored for
# whatever reason (maybe the register list is changing but the monitor hasn't been updated), set this to false.
#
report_error_when_register_value_is_missing_from_cr_tracker_file = True

# To verify that the PMA is only saving and restore the groups that exist in the ROM enable this check. When set to True
# checker check all groups that save and restored exist in ROM. When set to False this check is ingnored.
report_error_when_rom_group_does_not_exist_in_rom = True

# Most of the times registers that are save restore can not be x. In some special scenarios we might not care
# that the register is x. Setting this flag to True will check that the save and restore value of the register
# are never x. Setting the flag to False will check that both the save and restore value are false.
#
report_error_when_register_is_x = False

# The following is a list of 'counter' registers, registers that are really hard to check because they
# are constantly increasing during many or all tests. But, we can still check some aspects of save/restore, by
# at least saying that the check value after the restore must be higher than the value at the save time.
#
regs_that_count_up = ['ccf_gpsb_top.ncevents.NcuPMONCtrFx']


#list of registers to exclude by full name
# ['ccf_gpsb_top.sbo_misc_regs.arac_ctl']  https://hsdes.intel.com/appstore/article/#/22012836575
exclude_list = [] #'ccf_gpsb_top.sbo_misc_regs.arac_ctl']
# TODO PTL meirlevy - need to add support for ignoring RO/V bits on S&R - https://hsdes.intel.com/appstore/article/#/1309868185
exclude_list += [f'ccf_gpsb_top.ingress_{i}.cbo_ring_scalability_weights_misc' for i in range(4)]
exclude_list += ['ccf_gpsb_top.sbo_misc_regs.sbo_ring_scale_weights_misc']
# TODO yklein - the below register has handcoded fields which should be RO/V - after this is resolved can add to the above TODO on meir
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_c2u_data_hdr' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_c2u_data' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_c2u_req_hdr' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_c2u_rsp_hdr' for i in range(4)]

exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_u2c_data_hdr' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_u2c_data' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_u2c_req_hdr' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.dfx_accum_idi_u2c_rsp_hdr' for i in range(4)]
     

exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_RX_REQ_DCD_CFG' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_TX_REQ_DCD_CFG' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_RX_RSP_DCD_CFG' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_TX_RSP_DCD_CFG' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_RX_DATA_DCD_CFG' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.CFI_TX_DATA_DCD_CFG' for i in range(2)]
#PMONS keep counting so it is common to have mismatches between SAVE to RESTORE
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.pmon_ctr_0' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.santa{i}_regs.pmon_ctr_1' for i in range(2)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.cbopmonct0' for i in range(4)]
exclude_list += [f'ccf_gpsb_top.egress_{i}.cbopmonct1' for i in range(4)]

# TODO roeilevi - bit 30 (field) in LTCtrlSts is WO field. Therefore it shouldn't take place in SnR
exclude_list += [f'ccf_gpsb_top.ncevents.LTCtrlSts']

# IOSF SB tracker that has the save and restore commands send from PMA to the Save Restore IP
#
CBO_PAIR_0_SRFSM_SB_LOG = "_CCF_IOSF_SB_CBO_PAIR0_SRFSM_TRK.log"
SBO_SRFSM_SB_LOG = "_CCF_IOSF_SB_SBO_SRFSM_TRK.log"
PMC_GPSB_SB_LOG =  "_CCF_IOSF_PMC_GPSB_TRK.log"

# Dictionary for ROMs to Logs
#
srfsm_pid_rom_name_dict = {CBO_PAIR_0_SRFSM_PID : CBO_PAIR0_ROM, SBO_SRFSM_PID : SBO_IDP_ROM}



