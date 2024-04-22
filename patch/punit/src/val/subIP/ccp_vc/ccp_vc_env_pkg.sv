// Module Name:        punit_ccp_vc_env_pkg.sv
///
/// Primary Contact: 	Olteanu, Yehonatan
/// Secondary Contact:
/// Creation Date: 		10.2020
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
/// Holds all files needs to be included for the Punit CCP EMU
///
///=====================================================================================================================

package ccp_vc_env_pkg;
    import sla_pkg::*;
    import uvm_pkg::*;
    import val_svtb_common_uvm_pkg::*;
//    import IosfPkg::*
    import iosfsbm_cm::*;
    import iosfsbm_seq::*;
    import ConfigDB::*;

    `include "uvm_macros.svh"
    `include "slu_macros.svh"
    `include "val_svtb_common_macros_uvm.svh"
    `include "sai_enums.vh"
    
    
    `include "punit_ccp_vc_types.svh"
    `include "punit_ccp_vc_params.sv"
    `include "ccp_base_emulator.svh"
    `include "ccp_vc_regs.svh"
    
    `include "punit_ccp_vc_seq_item.sv"
    `include "punit_ccp_vc_sequencer.sv"
    `include "punit_ccp_vc_base_seq.sv"
    `include "ccp_extension_for_ral.sv"
    `include "punit_ccp_vc_seq.sv"
    `include "punit_ccp_vc_emulator.sv"
    `include "punit_ccp_vc_driver.sv"
    `include "punit_ccp_vc_monitor.sv"
    `include "punit_ccp_vc_tracker.sv"

    `include "ccp_iosfsb_uvm_adapter.sv"

       
    `include "punit_ccp_vc_agent.sv"
    

endpackage: ccp_vc_env_pkg

