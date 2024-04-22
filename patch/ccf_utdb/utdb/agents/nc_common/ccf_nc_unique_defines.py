import os
from val_utdb_bint import bint

class UNIQUE_DEFINES():

    is_low_power_ccf = False
    ip_name = "CCF"
    ncracu_sb_pid = bint(0xf60d)
    ncevents_sb_pid = bint(0xf60a)
    ccf_cfi_ep = "CCF_0(10)"
    ccf_id = bint(0)
    local_cbo0 = bint(0xee03)

    hdl_path_root = 'ccf_tb.CCF_TOP_INST'
    if os.environ.get('WORKAREA') is not None:
        ccf_path = os.environ.get('WORKAREA')
        ncu0_inst_hdl_path = 'par_base_santa_clst0.ncu'
        ncu1_inst_hdl_path = 'par_base_santa_clst1.ncu'
        ncu2_inst_hdl_path = 'par_base_santa_clst2.ncu'
        ncu3_inst_hdl_path = 'par_base_santa_clst3.ncu'
        custom_hw_col_db_name = 'ccf_custom_hw_col_db'
    else:
        ccf_path = os.environ.get('CCF_ROOT')
        custom_hw_col_db_name = 'ccf_custom_hw_col_db'
        ncu0_inst_hdl_path = 'par_base_santa_clst0.ncu'
        ncu1_inst_hdl_path = 'par_base_santa_clst1.ncu'
        ncu2_inst_hdl_path = 'par_base_santa_clst2.ncu'
        ncu3_inst_hdl_path = 'par_base_santa_clst3.ncu'
    vcr_pla_file_path = ccf_path + '/src/idp/rtl/vcrpla/mapped_vcrpla.yaml'





