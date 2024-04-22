//------------------------------------------------------------------------------
//
//  INTEL CONFIDENTIAL
//
//  Copyright 2007-2023 Intel Corporation All Rights Reserved.
//
//  The source code contained or described herein and all documents related
//  to the source code ("Material") are owned by Intel Corporation or its
//  suppliers or licensors. Title to the Material remains with Intel
//  Corporation or its suppliers and licensors. The Material contains trade
//  secrets and proprietary and confidential information of Intel or its
//  suppliers and licensors. The Material is protected by worldwide copyright
//  and trade secret laws and treaty provisions. No part of the Material may
//  be used, copied, reproduced, modified, published, uploaded, posted,
//  transmitted, distributed, or disclosed in any way without Intel's prior
//  express written permission.
//
//  No license under any patent, copyright, trade secret or other intellectual
//  property right is granted to or conferred upon you by disclosure or
//  delivery of the Materials, either expressly, by implication, inducement,
//  estoppel or otherwise. Any license under such intellectual property rights
//  must be express and approved by Intel in writing.
//
//  Copyright (c) 2023 Intel Corporation
//  Intel Proprietary and Top Secret Information
//---------------------------------------------------------------------------------------------------------------------

///=====================================================================================================================
/// Module Name:        ccf_nc_pkg.sv
///
/// Primary Contact:
/// Secondary Contact:
/// Creation Date:      08.2018
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
/// Here enter your description.
///
///=====================================================================================================================

package ccf_nc_pkg;
    `ifndef IDI_BRIDGE_IP
    `include "vip_layering_macros.svh"
    `endif

    `import_base(aupi_pkg::*);
    `import_base(uxi_env_pkg::*);
    `import_base(sla_pkg::*);
    `import_base(uvm_pkg::*);
    `import_base(svlib_pkg::*);
    `import_base(val_svtb_common_uvm_pkg::*);
    `import_base(iosfsbm_cm::*);
    `import_base(ConfigDB::*);

    `import_base(ccf_common_pkg::*);

    `import_base(core_emu_uvm_pkg::*);
    `import_typ(idi_uvm_pkg::*);
    `import_base(idi_common_uvm_pkg::*);

    `import_base (ral_gen_pkg::*);

    `include_base("uvm_macros.svh")
    `include_base("slu_macros.svh")
    `include_base("idi_macros.svh")
    `include_base("val_svtb_common_macros_uvm.svh")
    `include_base("ccf_macros.sv")
    `include_base("ccf_sbr_port_id_params.sv")
    `include_base("ccf_defines.sv")
    `include_base("nc/ccf_nc_defines.sv")
    `include_base("ccf_types.sv")
    `include_base("cncu_types.sv")
    
    `ifndef IDI_BRIDGE_IP
    `include_typ("ccf_seq_defines.sv")
    `else
    `include_typ("idi_bridge_seq_defines.sv")
    `endif
    `include_base("ccf_nc_base_seq.sv")
    `include_typ("ccf_nc_sb_seqlib.sv")
    `include_base("ccf_nc_funnyio_seqlib.sv")
    `include_base("ccf_nc_vcr_seqlib.sv")
    `include_typ("ccf_nc_interrupts_seqlib.sv")
    `include_typ("ccf_nc_mmio_seqlib.sv")
    `include_base("ccf_nc_cfg_seqlib.sv")
    //`include_typ("ccf_nc_lock_seqlib.sv")
    `include_typ("ccf_nc_ucode_resources_seqlib.sv")
    `include_typ("ccf_nc_events_seqlib.sv")
    `include_typ("ccf_nc_seqlib.sv")
    `include_typ("ccf_nc_seq_lib.sv")

    `include_typ("nc/ccf_nc_racu_tracker.sv")
    `include_typ("nc/ccf_nc_cfi_monitor.sv")
    `include_typ("nc/ccf_nc_sb_monitor.sv")
    `include_typ("nc/ccf_nc_agent.sv")
endpackage
