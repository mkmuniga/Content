`include "uvm_macros.svh"


package uciesbbfm_env_pkg;
    typedef struct {
        bit[6:0]    d2d_pc_gpsb_crd;
        bit[6:0]    d2d_np_gpsb_crd;
        bit[6:0]    d2d_pc_pmsb_crd;
        bit[6:0]    d2d_np_pmsb_crd;
        bit[6:0]    d2d_dtf_crd;
    } t_d2d_credit;

    typedef struct {
        bit[255:0] vlw_in;
        bit[255:0] vlw_out;
    } t_vlw;

    typedef enum bit[3:0] {
        PMSB_NP     = 4'b0000,
        PMSB_P      = 4'b0001,
        GPSB_NP     = 4'b0010,
        GPSB_P      = 4'b0011,
        VLW         = 4'b0100,
        CDTRTN      = 4'b0101,
        DTF_DATA    = 4'b0110
    } t_ucie_vn;

    typedef struct {
        bit         enable;
        bit[3:0]    inj_channel;
    } t_force_credit_return;

import "DPI-C" context function void scUpdated2dCredits(input string path, input t_d2d_credit credit);
import "DPI-C" context function void scUpdateRmtd2dCredits(input string path, input t_d2d_credit credit);
import "DPI-C" context function void scUpdateEnableRmtD2DCredits(input string path, input bit rmt_d2d_credit_enable);
import "DPI-C" context function void scUpdateVLWDefaults(input string path, input t_vlw vlw);
import "DPI-C" context function void scUpdateSingleLane(input string path, input bit single_lane_en, input bit[7:0] lane);
import "DPI-C" context function void scUpdateIgnoreD2DCredits(input string path, input bit[7:0] ignore_d2d_credits);
import "DPI-C" context function void scUpdateIgnoreRDICredits(input string path, input bit ignore_rdi_credits);
import "DPI-C" context function void scUpdateDisableTxLanes(input string path, input bit[7:0] disable_lanes);
import "DPI-C" context function void scUpdateForceCreditReturn(input string path, input t_force_credit_return cdt_rtn);
import "DPI-C" context function void scUpdateInitPkt(input string path, input bit first_ok_noop);
import "DPI-C" context function void scUpdateInitPktDelay(input string path, input bit[6:0] delay);
import "DPI-C" context function void scInitialSB2UCIeCfgObj(input string path);
import "DPI-C" context function void scUpdateEnableDtfData(input string path, input bit enable_dtf_data);
import "DPI-C" context function void scUpdateEnableDtfCtrl(input string path, input bit enable_dtf_ctrl);
import "DPI-C" context function void scUpdateGlobalSyncAlign(input string path, input bit[4:0] global_sync_align);

import uvm_pkg::*;
//cbb hotfix import dtf_vc_pkg::*;
`include "sbbfm_iosfsb_ifc_wrapper.sv"
`include "sbbfm_vlw_ifc_wrapper.sv"
`include "sbbfm_rdi_ifc_wrapper.sv"
`include "sbbfm_misc_ifc_wrapper.sv"

`include "sbbfm_common_defines.svh"
`include "uciesbbfm_config.sv"
`include "sbbfm_errinj_seq_item.sv"
`include "sbbfm_errinj_driver.sv"
`include "uciesbbfm_config_sequencer.sv"
`include "vlw_input_monitor.sv"
`include "vlw_output_monitor.sv"
`include "vlw_sequence_item.sv"
`include "vlw_sequencer.sv"
`include "rdi_monitor.sv"
`include "vlw_driver.sv"
`include "phy_module_driver.sv"
`include "vwire_scoreboard.sv"
`include "rdi_scoreboard.sv"
`include "rdi_crd_driver.sv"
//cbb hotfix `include "sbbfm_dtf_vc_primary_stall_driver.sv"
`include "TA_monitor.sv"
`include "iosfsbm_svc_macros.svh"
`include "TA_scoreboard.sv"
//cbb hotfix `include "dtf_scoreboard.sv"
`include "uciesbbfm_agent.sv"
`include "uciesbbfm_agent_env.sv"
`include "gpsb_iosf_scoreboard.sv"
//`include "pmsb_iosf_scoreboard.sv"

endpackage
