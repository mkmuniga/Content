//-----------------------------------------------------------------------------
// Title         : DMR D2D Stack Test Island module file
// Project       : *Valley
//-----------------------------------------------------------------------------
// File          : d2d_bind_mod.sv
// Author        : floydcma
// Created       : 9/19/2022
//-----------------------------------------------------------------------------
// Description :
// This is the test island module of the D2D testbench, includes all intfs
// and registers them to the appropriate tb hierarchy.
//-----------------------------------------------------------------------------
// Copyright (c) 2022 by Intel Corporation This model is the confidential and
// proprietary property of Intel Corporation and the possession or use of this
// file requires a written license from Intel Corporation.
//
// The source code contained or described herein and all documents related to
// the source code ("Material") are owned by Intel Corporation or its suppliers
// or licensors. Title to the Material remains with Intel Corporation or its
// suppliers and licensors. The Material contains trade secrets and proprietary
// and confidential information of Intel or its suppliers and licensors. The
// Material is protected by worldwide copyright and trade secret laws and
// treaty provisions. No part of the Material may be used, copied, reproduced,
// modified, published, uploaded, posted, transmitted, distributed, or
// disclosed in any way without Intel's prior express written permission.
//
// No license under any patent, copyright, trade secret or other intellectual
// property right is granted to or conferred upon you by disclosure or delivery
// of the Materials, either expressly, by implication, inducement, estoppel or
// otherwise. Any license under such intellectual property rights must be
// express and approved by Intel in writing.
//
//------------------------------------------------------------------------------

  initial begin
    static string env_name;
    static string d2d_hier_path = $sformatf("%m");

    // Set the env_name to rest of env
    // Push down the config object to the env
   
//    iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_prvt_rc, fabric_cfg_iosf_rsrc_adapt_pm,
//    fabric_cfg_iosf_isa_gp, fabric_cfg_iosf_isa_pm ;


//    fabric_cfg_iosf_rsrc_adapt_pm = iosfsbm_fbrc_uvm::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_rsrc_adapt_pm", null);
////    fabric_cfg_iosf_prvt_rc   = iosfsbm_fbrc_uvm::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_prvt_rc", null);
//    fabric_cfg_iosf_isa_gp   = iosfsbm_fbrc_uvm::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_isa_gp", null);
//    fabric_cfg_iosf_isa_pm   = iosfsbm_fbrc_uvm::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_isa_pm", null);


//  //  fabric_cfg_iosf_prvt_rc.intf_name = "iosf_rc_prvt_intf";
//    fabric_cfg_iosf_rsrc_adapt_pm.intf_name = "iosf_rsrc_adapt_pm_intf";
//    fabric_cfg_iosf_isa_gp.intf_name   = "iosf_isa_gp_intf";
//    fabric_cfg_iosf_isa_pm.intf_name   = "iosf_isa_pm_intf";

    // Determine the env name.  Read from uvm_resource_db if it exists, otherwise use a default name
    // Use i as the index, since it is the global index used to set the name in uvm_resource_db
    if (!uvm_resource_db#(string)::read_by_name("d2d_env_name", $sformatf("%0d", ENV_INST), env_name)) begin
      env_name = $sformatf("d2d_env%0d", ENV_INST);
    end
    uvm_config_db#(string)::set(null,{"*.", env_name}, "inst_suffix", INST_SUFFIX);
    uvm_config_db#(string)::set(null,{"*.", env_name}, "d2d_hier_path", d2d_hier_path);
    uvm_config_db#(uvm_pkg::uvm_active_passive_enum)::set(null, {"*.", env_name}, "d2d_bfm_mode", d2d_active_passive);  //cbb hotfix  

    // Pass apb_vif to the rest of the d2d env
    uvm_config_db#(svt_amba_uvm_pkg::svt_apb_vif)::set(null,{"*.", env_name,".","apb_env"},"vif",m_svt_apb_if); //cbb hotfix
//  //  uvm_config_db#(iosfsbm_fbrc_uvm::fbrcvc_cfg)::set(null,{"*.", env_name},"fabric_cfg_iosf_prvt_rc",fabric_cfg_iosf_prvt_rc);
//    uvm_config_db#(iosfsbm_fbrc_uvm::fbrcvc_cfg)::set(null,{"*.", env_name},"fabric_cfg_iosf_rsrc_adapt_pm",fabric_cfg_iosf_rsrc_adapt_pm);
//    uvm_config_db#(iosfsbm_fbrc_uvm::fbrcvc_cfg)::set(null,{"*.", env_name},"fabric_cfg_iosf_isa_gp",fabric_cfg_iosf_isa_gp);
//    uvm_config_db#(iosfsbm_fbrc_uvm::fbrcvc_cfg)::set(null,{"*.", env_name},"fabric_cfg_iosf_isa_pm",fabric_cfg_iosf_isa_pm);
  end

