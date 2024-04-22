

package iosfsb2ucie_env_pkg;
    
 //   import iosfsbm_cm::*;
 //   import iosfsbm_fbrc::*;
//    import intc_iosf_sb_reg_stim_server_sim_pkg::*;
 //   import intc_iosf_sb_protocol_stim_server_sim_context_pkg::*;
 //   import intc_iosf_sb_protocol_stim_seq_item_pkg::*;
 //   import intc_iosf_sb_protocol_stim_server_sim_context_registrar_pkg::*;
   `include "uvm_macros.svh"
 //  `include "slu_macros.svh"

    import uvm_pkg::*;
    import sla_pkg::*;
    //import uvm_ml::*
    //import base_uvm_utils_pkg::*;

     
 //   import iosfsbm_agent::*;
 //   import iosfsbm_seq::*;
 //
 //   import iosfsb_eps_pkg::*;
    import vwi_agent_pkg::*;
    import pm_agent_pkg::*;
    import pmon_agent_pkg::*;
    import ras_agent_pkg::*;    
    import sec_agent_pkg::*;
    import rdi_agent_pkg::*;
//FIXME cbb UV1 integ    import intc_iosf_sb_reg_stim_server_sim_pkg::*; // for RAL
//FIXME cbb UV1 integ    import intc_iosf_sb_protocol_stim_server_sim_context_pkg::*; // for RAL
//FIXME cbb UV1 integ    import dtf_vc_pkg::*;   
`ifdef SB2UCIE_TB    
    import reset_agent_pkg::*;
    import qchan_agent_pkg::*;
`endif
    `include "ucie_pkt_subscriber.sv"
    `include "iosfsb2ucie_env.sv"
    `include "iosf_e2e_scoreboard.sv"
    `include "vwi_scoreboard.sv"
    `include "agent/qch_agent/qchan_if.sv"
//FIXME cbb UV1 integ    `include "dtf_scoreboard.sv"

endpackage
`include "sysip_clk_if.sv"
`include "agent/vwi_agent/vwi_if.sv"
`include "agent/pm_agent/pm_if.sv"
`include "agent/pmon_agent/pmon_if.sv"
`include "agent/ras_agent/ras_if.sv"
`include "agent/sec_agent/sec_if.sv"
`include "agent/reset_agent/reset_if.sv"



