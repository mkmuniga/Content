package d2d_seq_pkg;

    import uvm_pkg::*;
    import sla_pkg::*;

    import vwi_agent_pkg::*;//for vwi_req
    import iosfsbm_seq::*;//for iosf_sb_seq
    import d2d_env_pkg::*;
    import reset_cmd_agent_pkg::*;
    import clk_env_pkg::*;
    import d2d_pkg::*;
    
//FIXME UV2 INTEG    // Coherent packages
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_ca_transaction_sequence_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_ca_avery_sim_context_registrar_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_ca_content_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_ca_source_info_pkg::*;
//FIXME UV2 INTEG    // Non Coherent packages
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_nc_transaction_sequence_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_nc_avery_sim_context_registrar_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_nc_content_pkg::*;
//FIXME UV2 INTEG    import intc_uxi_protocol_stim_nc_source_info_pkg::*;
//FIXME UV2 INTEG    
//FIXME UV2 INTEG    //import intc_addr_utils_stim_server_sim_sm_env_pkg::*;
//FIXME UV2 INTEG    import intc_addr_utils_stim_transaction_address_generator_pkg::*;
//FIXME UV2 INTEG    import intc_addr_utils_stim_server_sim_common_policy_pkg::*;
//FIXME UV2 INTEG    import intc_stim_pool_pkg::*;

    //------------------------------------------------------------------//
    //Place holder for all Mainband traffic sequences
    //required import pkgs and include macros are copied from  MB BFM package sbx_seqlib_pkg;
    //------------------------------------------------------------------//
//FIXME UV2 INTEG    import d2d_mb_bfm_env_pkg::*;
    import aupi_pkg::*;
    import auvm_pkg::*;
    import auvm_cache_pkg::*;
    import avycxl_pkg::*;
    import avycxl_uvm_pkg::*;
    import aufi_pkg::*;
    import aucie_pkg::*;
    import aucie_uvm_pkg::*;

//FIXME UV2 INTEG    `include "por_forces_macro.sv"
//FIXME UV2 INTEG    //Setting up force methodology
//FIXME UV2 INTEG    `FORCE_SETUP

    `include "uvm_macros.svh"
    `include "slu_macros.svh"
    //MLML added for d2d
//FIXME UV2 INTEG    `include "intc_stim_config_macros.svh"
//FIXME UV2 INTEG    `include "intc_stim_debug_macros.svh"
//FIXME UV2 INTEG    `include "intc_addr_utils_macros.svh"
//FIXME UV2 INTEG    `include "intc_stim_policy_macros.svh"
//FIXME UV2 INTEG    `include "intc_stim_pool_macros.svh"
 
     //------------------------------------------------------------------//
     // D2D Stimulus Config Include
//FIXME UV2 INTEG    `include "stim_cfg/d2d_stim_cfg_include.sv"
 
    `include "d2d_base_seq.sv"
    `include "reg/reg_seq_include.inc"
    `include "ras/ras_seq_include.inc"
    `include "d2d_reset_seq.sv"
    `include "d2d_vwi_seq.sv"
    `include "d2d_bios_config_seq.sv"
    `include "d2d_uciedda_dvsec_seq.sv"   
    `include "d2d_pcode_config_seq.sv"
    `include "d2d_sb2ucie_hwsync_seq.sv"
    `include "d2d_asyncwire_concurrent_seq.sv"
    
    `include "d2d_hwrs_reset_cmd_bus_seq.sv"
    `include "d2d_cold_reset_sb_hwrs_seq.sv"
    `include "d2d_cold_reset_mb_hwrs_seq.sv"
    `include "d2d_cold_reset_mb_pcode_seq.sv"
 
    `include "sb2ucie_tunl/iosfsb_seq_include.inc"

    //------------------------------------------------------------------//
    // UXI Main Band Include
//FIXME UV2 INTEG    `include "uxi/uxi_mb_seq_include.inc"
        
    //------------------------------------------------------------------//
    ///MB BFM: `include "uxi/sequences/uxi_nc_rd_txn.svh"
//FIXME UV2 INTEG    `include "uio_uxi_first_fetch_seq.sv"
//FIXME UV2 INTEG   
//FIXME UV2 INTEG    //------------------------------------------------------------------//
//FIXME UV2 INTEG    //Add Perf test sequences here 
//FIXME UV2 INTEG    //------------------------------------------------------------------//
//FIXME UV2 INTEG    `include "perf/uxi_multi_agent_bw_seq.svh"
//FIXME UV2 INTEG    `include "perf/uxi_multi_agent_lat_seq.svh"
//FIXME UV2 INTEG    //------------------------------------------------------------------//
//FIXME UV2 INTEG    // D2D mixer sequene include
//FIXME UV2 INTEG    // we want this compiled last to have access to all sequences before it
//FIXME UV2 INTEG    `include "d2d_mixer_sequence.sv"

//------------------------------------------------------------------//
// DFD Seq
//------------------------------------------------------------------//
//FIXME UV2 INTEG`include "dfd/dtf_vc_base_seq.sv"

endpackage : d2d_seq_pkg
