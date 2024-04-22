// -------------------------------------------------------------------
// INTEL CONFIDENTIAL
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted
// materials, and your use of them is governed by the express license
// under which they were provided to you ("License"). Unless the
// License provides otherwise, you may not use, modify, copy, publish,
// distribute, disclose or transmit this software or the related
// documents without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no
// express or implied warranties, other than those that are expressly
// stated in the License.
// -------------------------------------------------------------------


   import uciesbbfm_env_pkg::*;
   import ula_uvm_env_pkg::*;
   import uciedda_uvm_env_pkg::*;

class d2d_env extends uvm_env;

  `uvm_component_utils_begin(d2d_env)
  `uvm_component_utils_end

  d2d_cfg d2d_cfg_p;

  uciesbbfm_agent_env sbbfm_agent_env_0;
  uciesbbfm_config sbbfm_cfg;
  iosfsb2ucie_env iosfsb2ucie_env_inst;
  logic [`V_WIRES_IN-1:0] default_strap_vlw_in;
  logic [`V_WIRES_OUT-1:0] default_strap_vlw_out;

  uvm_pkg::uvm_active_passive_enum bfm_mode; // cbb hotfix

  iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_fabric_vc_pblc_rc,iosf_sbc_fabric_vc_prvt_rc,iosf_sbc_fabric_vc_rsrc_phy_pm,iosf_sbc_fabric_vc_isa_gp;
  iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_fabric_vc_rsrc_pll_pm,iosf_sbc_fabric_vc_ula_0_gp,iosf_sbc_fabric_vc_ula_1_gp,iosf_sbc_fabric_vc_dda_0_gp,iosf_sbc_fabric_vc_dda_1_gp;
  iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_fabric_vc_phy_0_gp, iosf_sbc_fabric_vc_phy_1_gp, iosf_sbc_fabric_vc_phy_2_gp;

  // ula_d2d_env 
  ula_base_env ula_d2d_env_0;  // per d2d, port1 
  ula_base_env ula_d2d_env_1;  // per d2d, port2  
  ula_cfg ula_d2d_cfg_0;
  ula_cfg ula_d2d_cfg_1;

  // uciedda_d2d_env
  uciedda_base_env uciedda_d2d_env_0;  // per d2d, port1 
  uciedda_base_env uciedda_d2d_env_1;  // per d2d, port2  
  uciedda_cfg uciedda_d2d_cfg_0;
  uciedda_cfg uciedda_d2d_cfg_1;

  svt_apb_system_env apb_env;
  extern function new(string name = "d2d_env", uvm_component parent);
  extern virtual function void build_phase(uvm_phase phase);
  extern virtual function void connect_phase(uvm_phase phase);
endclass

function d2d_env::new(string name = "d2d_env", uvm_component parent);
  super.new(name, parent);
endfunction

function void d2d_env::build_phase(uvm_phase phase);
  string inst_suffix_t, d2d_hier_path;
  string env_path = $sformatf("%m");

  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_gpsb_ep ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_gpsb_tunl ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_pmsb_tunl ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_rsrc_phy_pm ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_rsrc_pll_pm ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_isa_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_ula_0_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_ula_1_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_dda_0_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_dda_1_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_phy_0_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_phy_1_gp ;
  iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_iosf_phy_2_gp ;


  iosfsbm_cm::opcode_t fab_gpsb_supp_opcodes[$],fab_pmsb_supp_opcodes[$];

  bit[15:0] fab_gpsb_my_ports0[$], fab_gpsb_other_ports0[$],fab_gpsb_mcast_ports0[$],fab_gpsb_my_seg_ports0[$],fab_gpsb_other_seg_ports0[$] ;
  bit[15:0] fab_pmsb_my_ports0[$], fab_pmsb_other_ports0[$],fab_pmsb_mcast_ports0[$],fab_pmsb_my_seg_ports0[$],fab_pmsb_other_seg_ports0[$] ;
  bit[15:0] fab_gpsb_my_ports1[$], fab_gpsb_other_ports1[$],fab_gpsb_mcast_ports1[$],fab_gpsb_my_seg_ports1[$],fab_gpsb_other_seg_ports1[$] ;
  bit[15:0] fab_pmsb_my_ports1[$], fab_pmsb_other_ports1[$],fab_pmsb_mcast_ports1[$],fab_pmsb_my_seg_ports1[$],fab_pmsb_other_seg_ports1[$] ;
  bit[31:0] ext_headers[$];

  iosfsbm_cm::opcode_t fab_gpsb_simple_opcodes_first='hb0, fab_gpsb_simple_opcodes_second='hb1, fab_gpsb_simple_opcodes_q[$];
  iosfsbm_cm::opcode_t fab_gpsb_msgd_opcodes_first='h70, fab_gpsb_msgd_opcodes_second='h74, fab_gpsb_msgd_opcodes_q[$];

  iosfsbm_cm::opcode_t fab_pmsb_simple_opcodes_first='hb0, fab_pmsb_simple_opcodes_second='hb1, fab_pmsb_simple_opcodes_q[$];
  iosfsbm_cm::opcode_t fab_pmsb_msgd_opcodes_first='h70, fab_pmsb_msgd_opcodes_second='h74, fab_pmsb_msgd_opcodes_q[$];


  super.build_phase(phase);
 `uvm_info(get_type_name(), $sformatf("d2d_env: build_phase -  env_path %s", env_path), UVM_LOW);


  // Build apb_env
  apb_env = svt_apb_system_env::type_id::create("apb_env", this);  
 //uvm_config_db#(int)::dump(); // Used for debug purposes only
  // Get the config object for this env
  if (!uvm_config_db#(d2d_cfg)::get(this, "", "d2d_cfg", d2d_cfg_p)) begin
    `uvm_fatal("D2D_ENV", "Could not find d2d_cfg");
  end
  if (d2d_cfg_p == null) begin
    `uvm_fatal("D2D_ENV", "d2d_cfg is null");
  end
  
  /** Apply the configuration to the System ENV */
  uvm_config_db#(svt_apb_system_configuration)::set(this, "apb_env", "cfg", d2d_cfg_p.apb_cfg);
  
  if (!uvm_config_db#(string)::get(null, this.get_full_name(), "inst_suffix", inst_suffix_t))begin
    `uvm_fatal(get_type_name(), $sformatf("d2d_env: build_phase - failed to create inst_suffix_t"));
  end
  if (!uvm_config_db#(string)::get(null, this.get_full_name(), "d2d_hier_path", d2d_hier_path))begin
    `uvm_fatal(get_type_name(), $sformatf("d2d_env: build_phase - failed to create d2d_hier_path"));
  end
  if (!uvm_config_db#(uvm_pkg::uvm_active_passive_enum)::get(null, this.get_full_name(), "d2d_bfm_mode", bfm_mode)) begin //cbb hotfix
    `uvm_fatal(get_type_name(), $sformatf("d2d_env: build_phase - failed to create d2d_bfm_mode"));
  end

  // Build ula_d2d_env for replay
  ula_d2d_env_0 = ula_uvm_env_pkg::ula_base_env::type_id::create("ula_d2d_env_0",this);
  ula_d2d_env_1 = ula_uvm_env_pkg::ula_base_env::type_id::create("ula_d2d_env_1",this);
  
  ula_d2d_cfg_0 = ula_uvm_env_pkg::ula_cfg::type_id::create("ula_d2d_cfg_0",this);
  ula_d2d_cfg_1 = ula_uvm_env_pkg::ula_cfg::type_id::create("ula_d2d_cfg_1",this);

  uvm_config_db#(ula_uvm_env_pkg::ula_cfg)::set(this,"ula_d2d_env_0", "ula_cfg", ula_d2d_cfg_0);
  uvm_config_db#(ula_uvm_env_pkg::ula_cfg)::set(this,"ula_d2d_env_1", "ula_cfg", ula_d2d_cfg_1);

  uvm_config_db#(string)::set(this,"ula_d2d_env_0", "INST_SUFFIX", $sformatf("%s_0_ula", inst_suffix_t));
  uvm_config_db#(string)::set(this,"ula_d2d_env_1", "INST_SUFFIX", $sformatf("%s_1_ula", inst_suffix_t));

  // Build uciedda_d2d_env for replay
  uciedda_d2d_env_0 = uciedda_uvm_env_pkg::uciedda_base_env::type_id::create("uciedda_d2d_env_0",this);
  uciedda_d2d_env_1 = uciedda_uvm_env_pkg::uciedda_base_env::type_id::create("uciedda_d2d_env_1",this);
  
  uciedda_d2d_cfg_0 = uciedda_uvm_env_pkg::uciedda_cfg::type_id::create("uciedda_d2d_cfg_0",this);
  uciedda_d2d_cfg_1 = uciedda_uvm_env_pkg::uciedda_cfg::type_id::create("uciedda_d2d_cfg_1",this);

  uvm_config_db#(uciedda_uvm_env_pkg::uciedda_cfg)::set(this,"uciedda_d2d_env_0", "uciedda_cfg", uciedda_d2d_cfg_0);
  uvm_config_db#(uciedda_uvm_env_pkg::uciedda_cfg)::set(this,"uciedda_d2d_env_1", "uciedda_cfg", uciedda_d2d_cfg_1);

  uvm_config_db#(string)::set(this,"uciedda_d2d_env_0", "INST_SUFFIX", $sformatf("%s_0_dda", inst_suffix_t));
  uvm_config_db#(string)::set(this,"uciedda_d2d_env_1", "INST_SUFFIX", $sformatf("%s_1_dda", inst_suffix_t));

  // Build the SB BFM Env
  sbbfm_agent_env_0 = uciesbbfm_agent_env::type_id::create("sbbfm_agent_env_0", this);
  sbbfm_cfg = uciesbbfm_config::type_id::create("sbbfm_cfg_0", this);

// GPSB
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "gpsb_simple_opcodes_1", fab_gpsb_simple_opcodes_first);
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "gpsb_simple_opcodes_2", fab_gpsb_simple_opcodes_second);

    fab_gpsb_simple_opcodes_q.push_back(fab_gpsb_simple_opcodes_first);  //SYNC
    fab_gpsb_simple_opcodes_q.push_back(fab_gpsb_simple_opcodes_second);  //DELAY_REQ


    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "gpsb_msgd_opcodes_1", fab_gpsb_msgd_opcodes_first);
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "gpsb_msgd_opcodes_2", fab_gpsb_msgd_opcodes_second);

    fab_gpsb_msgd_opcodes_q.push_back(fab_gpsb_msgd_opcodes_first);  //FOLLOW_UP
    fab_gpsb_msgd_opcodes_q.push_back(fab_gpsb_msgd_opcodes_second);  //DELAY_RSP

// PMSB
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "pmsb_simple_opcodes_1", fab_pmsb_simple_opcodes_first);
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "pmsb_simple_opcodes_2", fab_pmsb_simple_opcodes_second);

    fab_pmsb_simple_opcodes_q.push_back(fab_pmsb_simple_opcodes_first);  //SYNC
    fab_pmsb_simple_opcodes_q.push_back(fab_pmsb_simple_opcodes_second);  //DELAY_REQ


    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "pmsb_msgd_opcodes_1", fab_pmsb_msgd_opcodes_first);
    uvm_config_db#(iosfsbm_cm::opcode_t)::set(this, "*", "pmsb_msgd_opcodes_2", fab_pmsb_msgd_opcodes_second);

    fab_pmsb_msgd_opcodes_q.push_back(fab_pmsb_msgd_opcodes_first);  //FOLLOW_UP
    fab_pmsb_msgd_opcodes_q.push_back(fab_pmsb_msgd_opcodes_second);  //DELAY_RSP

  //TODO: ext_headers = '{32'h0000_4800};//TODO need to match RTL SAI
  // Create component
  //TODO: hardcoding for now- must match the remap tables under src/val/tests/iosfsb2ucie/ 
  //for gpsb endpoint
  fab_gpsb_other_ports0 = '{'h50};
  fab_gpsb_my_ports0 =    '{'h51,'h52,'h56};
  fab_gpsb_my_seg_ports0 = '{'hEE};
  fab_gpsb_other_seg_ports0 = '{'hEE,'hF6,'hF7,'hEF,'hF0,'hF1,'hF2};       
  fab_gpsb_mcast_ports0 = '{'hFA};  

  //D2D1
  fab_gpsb_other_ports1 = '{'h50};
  fab_gpsb_my_ports1 =    '{'h51,'h52,'h56};
  fab_gpsb_my_seg_ports1 = '{'hEE};
  fab_gpsb_other_seg_ports1 = '{'hEE,'hF6,'hF7,'hEF,'hF0,'hF1,'hF2};       
  fab_gpsb_mcast_ports1 = '{'hFB};  

  fab_gpsb_supp_opcodes = iosfsbm_cm::DEFAULT_OPCODES;

  //for pmsb endpoint
  fab_pmsb_other_ports0 = '{'h01};
  fab_pmsb_my_ports0 =    '{'h50,'h51};
  fab_pmsb_my_seg_ports0 = '{'hEE};
  fab_pmsb_other_seg_ports0 = '{'hEE,'hF6,'hF7,'hEF,'hF0,'hF1,'hF2};
  fab_pmsb_mcast_ports0 = '{};


 //D2D1 for pmsb endpoint
  fab_pmsb_other_ports1 = '{'h01};
  fab_pmsb_my_ports1 =    '{'h50,'h51};
  fab_pmsb_my_seg_ports1 = '{'hEE};
  fab_pmsb_other_seg_ports1 = '{'hEE,'hF6,'hF7,'hEF,'hF0,'hF1,'hF2};
  fab_pmsb_mcast_ports1 = '{};

  fab_pmsb_supp_opcodes = {iosfsbm_cm::DEFAULT_OPCODES,'h68};

  fabric_cfg_gpsb_ep        = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_gpsb_ep", null);
  fabric_cfg_gpsb_tunl      = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_gpsb_tunl", null);
  fabric_cfg_pmsb_tunl      = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_pmsb_tunl", null);
  fabric_cfg_iosf_rsrc_phy_pm = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_rsrc_phy_pm", null);
  fabric_cfg_iosf_rsrc_pll_pm = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_rsrc_pll_pm", null);
  fabric_cfg_iosf_isa_gp    = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_isa_gp", null);
  fabric_cfg_iosf_ula_0_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_ula_0_gp", null);
  fabric_cfg_iosf_ula_1_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_ula_1_gp", null);
  fabric_cfg_iosf_dda_0_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_dda_0_gp", null);
  fabric_cfg_iosf_dda_1_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_dda_1_gp", null);
  fabric_cfg_iosf_phy_0_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_phy_0_gp", null);
  fabric_cfg_iosf_phy_1_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_phy_1_gp", null);
  fabric_cfg_iosf_phy_2_gp  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_iosf_phy_2_gp", null);


`ifndef IOSF_SB_PH2
  fabric_cfg_gpsb_ep.intf_name         = "gpsb_ep_fabric_intf";
  fabric_cfg_gpsb_tunl.intf_name       = "gpsb_tunl_fabric_intf";
  fabric_cfg_pmsb_tunl.intf_name       = "pmsb_tunl_fabric_intf";
  fabric_cfg_iosf_rsrc_phy_pm.intf_name  = "iosf_rsrc_adapt_phy_pm_intf";
  fabric_cfg_iosf_rsrc_pll_pm.intf_name  = "iosf_rsrc_adapt_pll_pm_intf";
  fabric_cfg_iosf_isa_gp.intf_name     = "iosf_isa_gpsb_intf";
  fabric_cfg_iosf_ula_0_gp.intf_name   = "iosf_ula_0_gp_intf";
  fabric_cfg_iosf_ula_1_gp.intf_name   = "iosf_ula_1_gp_intf";
  fabric_cfg_iosf_dda_0_gp.intf_name   = "iosf_dda_0_gp_intf";
  fabric_cfg_iosf_dda_1_gp.intf_name   = "iosf_dda_1_gp_intf";
  fabric_cfg_iosf_phy_0_gp.intf_name   = "iosf_ucie_phy_0_intf";
  fabric_cfg_iosf_phy_1_gp.intf_name   = "iosf_ucie_phy_1_intf";
  fabric_cfg_iosf_phy_2_gp.intf_name   = "iosf_ucie_phy_2_intf";

`else  
  fabric_cfg_gpsb_ep.inst_name         = {d2d_hier_path,".gpsb_ep_fabric_ti"};
  fabric_cfg_gpsb_tunl.inst_name       = {d2d_hier_path,".gpsb_tunl_fabric_ti"};
  fabric_cfg_pmsb_tunl.inst_name       = {d2d_hier_path,".pmsb_tunl_fabric_ti"};
  fabric_cfg_iosf_rsrc_phy_pm.inst_name  = {d2d_hier_path,".iosf_rsrc_adapt_phy_pm_intf_ti"};
  fabric_cfg_iosf_rsrc_pll_pm.inst_name  = {d2d_hier_path,".iosf_rsrc_adapt_pll_pm_intf_ti"};
  fabric_cfg_iosf_isa_gp.inst_name     = {d2d_hier_path,".iosf_isa_gp_intf_ti"};
  fabric_cfg_iosf_ula_0_gp.inst_name   = {d2d_hier_path,".iosf_ula_0_gp_intf_ti"};
  fabric_cfg_iosf_ula_1_gp.inst_name   = {d2d_hier_path,".iosf_ula_1_gp_intf_ti"};
  fabric_cfg_iosf_dda_0_gp.inst_name   = {d2d_hier_path,".iosf_dda_0_gp_intf_ti"};
  fabric_cfg_iosf_dda_1_gp.inst_name   = {d2d_hier_path,".iosf_dda_1_gp_intf_ti"};
  fabric_cfg_iosf_phy_0_gp.inst_name   = {d2d_hier_path,".iosf_ucie_phy_0_intf_ti"};
  fabric_cfg_iosf_phy_1_gp.inst_name   = {d2d_hier_path,".iosf_ucie_phy_1_intf_ti"};
  fabric_cfg_iosf_phy_2_gp.inst_name   = {d2d_hier_path,".iosf_ucie_phy_2_intf_ti"};
`endif
  //randomize cfgs
//=============GPSB_EP CFG==================/
  assert (fabric_cfg_gpsb_ep.randomize with {
                                            fabric_cfg_gpsb_ep.payload_width == 8 ;//`IOSFSB_PLD_WIDTH_8; `IOSFSB2UCIE_PLD_WIDTH;
                                            fabric_cfg_gpsb_ep.num_tx_ext_headers == 1;
                                            fabric_cfg_gpsb_ep.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_gpsb_ep.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_gpsb_ep cfg obj")
  fabric_cfg_gpsb_ep.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_gpsb_ep.is_agent_vc = 0;
  fabric_cfg_gpsb_ep.ext_header_support  = 1;
  fabric_cfg_gpsb_ep.agt_ext_header_support = 1;
  fabric_cfg_gpsb_ep.ctrl_ext_header_support = 1;
  fabric_cfg_gpsb_ep.ext_headers_per_txn = 1;
  fabric_cfg_gpsb_ep.use_mem = 1;
  fabric_cfg_gpsb_ep.global_intf_en = 1;
  fabric_cfg_gpsb_ep.segment_scaling = 1;
  fabric_cfg_gpsb_ep.is_active = bfm_mode; //cbb hotfix



//=============GPSB_TUNL CFG==================/
  assert (fabric_cfg_gpsb_tunl.randomize with {
                                            fabric_cfg_gpsb_tunl.payload_width == 8; //`IOSFSB2UCIE_PLD_WIDTH;
                                            fabric_cfg_gpsb_tunl.num_tx_ext_headers == 1;
                                            fabric_cfg_gpsb_tunl.compl_delay == 1;
                                            fabric_cfg_gpsb_tunl.my_ports.size() == fab_gpsb_my_ports0.size();
                                            fabric_cfg_gpsb_tunl.other_ports.size() == fab_gpsb_other_ports0.size();
                                            fabric_cfg_gpsb_tunl.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_gpsb_tunl.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();
                                            fabric_cfg_gpsb_tunl.mcast_ports.size() == fab_gpsb_mcast_ports0.size();
                                            foreach (fab_gpsb_my_ports0[i])
                                              fabric_cfg_gpsb_tunl.my_ports[i] == fab_gpsb_my_ports0[i];
                                            foreach (fab_gpsb_other_ports0[i])
                                              fabric_cfg_gpsb_tunl.other_ports[i] == fab_gpsb_other_ports0[i];
                                            foreach (fab_gpsb_my_seg_ports0[i])
                                              fabric_cfg_gpsb_tunl.my_seg_ports[i] == fab_gpsb_my_seg_ports0[i];
                                            foreach (fab_gpsb_other_seg_ports0[i])
                                              fabric_cfg_gpsb_tunl.other_seg_ports[i] == fab_gpsb_other_seg_ports0[i];
                                            foreach (fab_gpsb_mcast_ports0[i])
                                              fabric_cfg_gpsb_tunl.mcast_ports[i] == fab_gpsb_mcast_ports0[i];
                                            foreach (fab_gpsb_supp_opcodes[i])
                                              fabric_cfg_gpsb_tunl.supported_opcodes[i] == fab_gpsb_supp_opcodes[i];

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_gpsb_tunl cfg obj")
  fabric_cfg_gpsb_tunl.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_gpsb_tunl.is_agent_vc = 0;
  fabric_cfg_gpsb_tunl.ext_header_support  = 1;
  fabric_cfg_gpsb_tunl.agt_ext_header_support = 1;
  fabric_cfg_gpsb_tunl.ctrl_ext_header_support = 1;
  fabric_cfg_gpsb_tunl.ext_headers_per_txn = 1;
  fabric_cfg_gpsb_tunl.use_mem = 1;
  fabric_cfg_gpsb_tunl.global_intf_en = 1;
  fabric_cfg_gpsb_tunl.segment_scaling = 1;
  fabric_cfg_gpsb_tunl.is_active = bfm_mode; //cbb hotfix

//=============PMSB_TUNL CFG==================/
  assert (fabric_cfg_pmsb_tunl.randomize with {
                                            fabric_cfg_pmsb_tunl.payload_width == 8; // `IOSFSB2UCIE_PLD_WIDTH;
                                            fabric_cfg_pmsb_tunl.num_tx_ext_headers == 1;
                                            fabric_cfg_pmsb_tunl.compl_delay == 1;
                                            fabric_cfg_pmsb_tunl.my_ports.size() == fab_pmsb_my_ports0.size();
                                            fabric_cfg_pmsb_tunl.other_ports.size() == fab_pmsb_other_ports0.size();
                                            fabric_cfg_pmsb_tunl.my_seg_ports.size() == fab_pmsb_my_seg_ports0.size();
                                            fabric_cfg_pmsb_tunl.other_seg_ports.size() == fab_pmsb_other_seg_ports0.size();
                                            fabric_cfg_pmsb_tunl.mcast_ports.size() == fab_pmsb_mcast_ports0.size();
                                            fabric_cfg_pmsb_tunl.supported_opcodes.size() == fab_pmsb_supp_opcodes.size();
                                            foreach (fab_pmsb_my_ports0[i])
                                              fabric_cfg_pmsb_tunl.my_ports[i] == fab_pmsb_my_ports0[i];
                                            foreach (fab_pmsb_other_ports0[i])
                                              fabric_cfg_pmsb_tunl.other_ports[i] == fab_pmsb_other_ports0[i];
                                            foreach (fab_pmsb_my_seg_ports0[i])
                                              fabric_cfg_pmsb_tunl.my_seg_ports[i] == fab_pmsb_my_seg_ports0[i];
                                            foreach (fab_pmsb_other_seg_ports0[i])
                                              fabric_cfg_pmsb_tunl.other_seg_ports[i] == fab_pmsb_other_seg_ports0[i];
                                            foreach (fab_pmsb_mcast_ports0[i])
                                              fabric_cfg_pmsb_tunl.mcast_ports[i] == fab_pmsb_mcast_ports0[i];
                                            foreach (fab_pmsb_supp_opcodes[i])
                                              fabric_cfg_pmsb_tunl.supported_opcodes[i] == fab_pmsb_supp_opcodes[i];
                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_pmsb_tunl cfg obj")
  fabric_cfg_pmsb_tunl.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_pmsb_tunl.is_agent_vc = 0;
  fabric_cfg_pmsb_tunl.ext_header_support  = 1;
  fabric_cfg_pmsb_tunl.agt_ext_header_support = 1;
  fabric_cfg_pmsb_tunl.ctrl_ext_header_support = 1;
  fabric_cfg_pmsb_tunl.ext_headers_per_txn = 1;
  fabric_cfg_pmsb_tunl.use_mem = 1;
  fabric_cfg_pmsb_tunl.global_intf_en = 1;
  fabric_cfg_pmsb_tunl.segment_scaling = 1;
  fabric_cfg_pmsb_tunl.is_active = bfm_mode; //cbb hotfix

//============= RSRC PM PHY ==================//
  assert (fabric_cfg_iosf_rsrc_phy_pm.randomize with {
                                            fabric_cfg_iosf_rsrc_phy_pm.payload_width == 8 ; //`IOSFSB_PLD_WIDTH_8; `IOSFSB2UCIE_PLD_WIDTH;
                                            fabric_cfg_iosf_rsrc_phy_pm.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_rsrc_phy_pm.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_rsrc_phy_pm.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();
                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_rsrc_phy_pm cfg obj")
  fabric_cfg_iosf_rsrc_phy_pm.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_rsrc_phy_pm.is_agent_vc = 0;
  fabric_cfg_iosf_rsrc_phy_pm.ext_header_support  = 1;
  fabric_cfg_iosf_rsrc_phy_pm.agt_ext_header_support = 1;
  fabric_cfg_iosf_rsrc_phy_pm.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_rsrc_phy_pm.ext_headers_per_txn = 1;
  fabric_cfg_iosf_rsrc_phy_pm.use_mem = 1;
  fabric_cfg_iosf_rsrc_phy_pm.global_intf_en = 1;
  fabric_cfg_iosf_rsrc_phy_pm.segment_scaling = 1;
  fabric_cfg_iosf_rsrc_phy_pm.is_active = bfm_mode; //cbb hotfix

//============= RSRC PM PLL ==================//
  assert (fabric_cfg_iosf_rsrc_pll_pm.randomize with {
                                            fabric_cfg_iosf_rsrc_pll_pm.payload_width == 8 ; //`IOSFSB_PLD_WIDTH_8; `IOSFSB2UCIE_PLD_WIDTH;
                                            fabric_cfg_iosf_rsrc_pll_pm.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_rsrc_pll_pm.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_rsrc_pll_pm.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();
                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_rsrc_pll_pm cfg obj")
  fabric_cfg_iosf_rsrc_pll_pm.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_rsrc_pll_pm.is_agent_vc = 0;
  fabric_cfg_iosf_rsrc_pll_pm.ext_header_support  = 1;
  fabric_cfg_iosf_rsrc_pll_pm.agt_ext_header_support = 1;
  fabric_cfg_iosf_rsrc_pll_pm.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_rsrc_pll_pm.ext_headers_per_txn = 1;
  fabric_cfg_iosf_rsrc_pll_pm.use_mem = 1;
  fabric_cfg_iosf_rsrc_pll_pm.global_intf_en = 1;
  fabric_cfg_iosf_rsrc_pll_pm.segment_scaling = 1;
  fabric_cfg_iosf_rsrc_pll_pm.is_active = bfm_mode; //cbb hotfix

//============= ISA GP ==================//
  assert (fabric_cfg_iosf_isa_gp.randomize with {
                                            fabric_cfg_iosf_isa_gp.payload_width == 8 ; //`IOSFSB_PLD_WIDTH_8; 
                                            fabric_cfg_iosf_isa_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_isa_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_isa_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();


                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_isa_gp cfg obj")
  fabric_cfg_iosf_isa_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_isa_gp.is_agent_vc = 0;
  fabric_cfg_iosf_isa_gp.ext_header_support  = 1;
  fabric_cfg_iosf_isa_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_isa_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_isa_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_isa_gp.use_mem = 1;
  fabric_cfg_iosf_isa_gp.global_intf_en = 1;
  fabric_cfg_iosf_isa_gp.segment_scaling = 1;
  fabric_cfg_iosf_isa_gp.is_active = bfm_mode; //cbb hotfix


//============= ULA 0 ==================//
  assert (fabric_cfg_iosf_ula_0_gp.randomize with {
                                            fabric_cfg_iosf_ula_0_gp.payload_width == 16; //`IOSFSB_PLD_WIDTH_16;  
                                            fabric_cfg_iosf_ula_0_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_ula_0_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_ula_0_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();


                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_ula_0_gp cfg obj")
  fabric_cfg_iosf_ula_0_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_ula_0_gp.is_agent_vc = 0;
  fabric_cfg_iosf_ula_0_gp.ext_header_support  = 1;
  fabric_cfg_iosf_ula_0_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_ula_0_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_ula_0_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_ula_0_gp.use_mem = 1;
  fabric_cfg_iosf_ula_0_gp.global_intf_en = 1;
  fabric_cfg_iosf_ula_0_gp.segment_scaling = 1;
  fabric_cfg_iosf_ula_0_gp.is_active = bfm_mode; //cbb hotfix

//============= ULA 1 ==================//
  assert (fabric_cfg_iosf_ula_1_gp.randomize with {
                                            fabric_cfg_iosf_ula_1_gp.payload_width == 16 ; //`IOSFSB_PLD_WIDTH_16; 
                                            fabric_cfg_iosf_ula_1_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_ula_1_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_ula_1_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();


                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_ula_1_gp cfg obj")
  fabric_cfg_iosf_ula_1_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_ula_1_gp.is_agent_vc = 0;
  fabric_cfg_iosf_ula_1_gp.ext_header_support  = 1;
  fabric_cfg_iosf_ula_1_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_ula_1_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_ula_1_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_ula_1_gp.use_mem = 1;
  fabric_cfg_iosf_ula_1_gp.global_intf_en = 1;
  fabric_cfg_iosf_ula_1_gp.segment_scaling = 1;
  fabric_cfg_iosf_ula_1_gp.is_active = bfm_mode; //cbb hotfix

//============= DDA 0 ==================//
  assert (fabric_cfg_iosf_dda_0_gp.randomize with {
                                            fabric_cfg_iosf_dda_0_gp.payload_width == 16 ; // `IOSFSB_PLD_WIDTH_16; 
                                            fabric_cfg_iosf_dda_0_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_dda_0_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_dda_0_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();


                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_dda_0_gp cfg obj")
  fabric_cfg_iosf_dda_0_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_dda_0_gp.is_agent_vc = 0;
  fabric_cfg_iosf_dda_0_gp.ext_header_support  = 1;
  fabric_cfg_iosf_dda_0_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_dda_0_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_dda_0_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_dda_0_gp.use_mem = 1;
  fabric_cfg_iosf_dda_0_gp.global_intf_en = 1;
  fabric_cfg_iosf_dda_0_gp.segment_scaling = 1;
  fabric_cfg_iosf_dda_0_gp.is_active = bfm_mode; //cbb hotfix


//============= DDA 1 ==================//
  assert (fabric_cfg_iosf_dda_1_gp.randomize with {
                                            fabric_cfg_iosf_dda_1_gp.payload_width == 16 ; //`IOSFSB_PLD_WIDTH_16; 
 											fabric_cfg_iosf_dda_1_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_dda_1_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_dda_1_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_dda_1_gp cfg obj")
  fabric_cfg_iosf_dda_1_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_dda_1_gp.is_agent_vc = 0;
  fabric_cfg_iosf_dda_1_gp.ext_header_support  = 1;
  fabric_cfg_iosf_dda_1_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_dda_1_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_dda_1_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_dda_1_gp.use_mem = 1;
  fabric_cfg_iosf_dda_1_gp.global_intf_en = 1;
  fabric_cfg_iosf_dda_1_gp.segment_scaling = 1;
  fabric_cfg_iosf_dda_1_gp.is_active = bfm_mode; //cbb hotfix


//============= PHY 0 ==================//
  assert (fabric_cfg_iosf_phy_0_gp.randomize with {
                                            fabric_cfg_iosf_phy_0_gp.payload_width == 16 ; //`IOSFSB_PLD_WIDTH_16; 
 											fabric_cfg_iosf_phy_0_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_phy_0_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_phy_0_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_phy_0_gp cfg obj")
  fabric_cfg_iosf_phy_0_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_phy_0_gp.is_agent_vc = 0;
  fabric_cfg_iosf_phy_0_gp.ext_header_support  = 1;
  fabric_cfg_iosf_phy_0_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_phy_0_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_phy_0_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_phy_0_gp.use_mem = 1;
  fabric_cfg_iosf_phy_0_gp.global_intf_en = 1;
  fabric_cfg_iosf_phy_0_gp.segment_scaling = 1;
  fabric_cfg_iosf_phy_0_gp.is_active = bfm_mode; //cbb hotfix


//============= PHY 1 ==================//
  assert (fabric_cfg_iosf_phy_1_gp.randomize with {
                                            fabric_cfg_iosf_phy_1_gp.payload_width == 16 ; //`IOSFSB_PLD_WIDTH_16; 
 											fabric_cfg_iosf_phy_1_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_phy_1_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_phy_1_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_phy_1_gp cfg obj")
  fabric_cfg_iosf_phy_1_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_phy_1_gp.is_agent_vc = 0;
  fabric_cfg_iosf_phy_1_gp.ext_header_support  = 1;
  fabric_cfg_iosf_phy_1_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_phy_1_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_phy_1_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_phy_1_gp.use_mem = 1;
  fabric_cfg_iosf_phy_1_gp.global_intf_en = 1;
  fabric_cfg_iosf_phy_1_gp.segment_scaling = 1;
  fabric_cfg_iosf_phy_1_gp.is_active = bfm_mode; //cbb hotfix

//============= PHY 2 ==================//
  assert (fabric_cfg_iosf_phy_2_gp.randomize with {
                                            fabric_cfg_iosf_phy_2_gp.payload_width == 16 ; //`IOSFSB_PLD_WIDTH_16; 
 											fabric_cfg_iosf_phy_2_gp.num_tx_ext_headers == 1;
                                            fabric_cfg_iosf_phy_2_gp.my_seg_ports.size() == fab_gpsb_my_seg_ports0.size();
                                            fabric_cfg_iosf_phy_2_gp.other_seg_ports.size() == fab_gpsb_other_seg_ports0.size();

                                            }) else
  `uvm_fatal(get_name(), "Unable to randomize fabric_cfg_iosf_phy_2_gp cfg obj")
  fabric_cfg_iosf_phy_2_gp.set_iosfspec_ver(iosfsbm_cm::IOSF_12);
  fabric_cfg_iosf_phy_2_gp.is_agent_vc = 0;
  fabric_cfg_iosf_phy_2_gp.ext_header_support  = 1;
  fabric_cfg_iosf_phy_2_gp.agt_ext_header_support = 1;
  fabric_cfg_iosf_phy_2_gp.ctrl_ext_header_support = 1;
  fabric_cfg_iosf_phy_2_gp.ext_headers_per_txn = 1;
  fabric_cfg_iosf_phy_2_gp.use_mem = 1;
  fabric_cfg_iosf_phy_2_gp.global_intf_en = 1;
  fabric_cfg_iosf_phy_2_gp.segment_scaling = 1;
  fabric_cfg_iosf_phy_2_gp.is_active = bfm_mode; //cbb hotfix

//==================IOSF EP VC START=======================//

//start creating VC, 3 SB ep will be mapped to iosf2ucie ep
`uvm_info(get_type_name(), $sformatf("d2d_env: build_phase -  created iosfsb2ucie_env_inst"), UVM_LOW);
  iosfsb2ucie_env_inst = iosfsb2ucie_env::type_id::create("iosfsb2ucie_env_inst", this);

  uvm_config_object::set(this,"iosfsb2ucie_env_inst.iosf_sbc_fabric_vc_gpsb_ep","fabric_cfg_gpsb_ep",fabric_cfg_gpsb_ep);
  uvm_config_object::set(this,"iosfsb2ucie_env_inst.iosf_sbc_fabric_vc_gpsb_tunl","fabric_cfg_gpsb_tunl",fabric_cfg_gpsb_tunl);
  uvm_config_object::set(this,"iosfsb2ucie_env_inst.iosf_sbc_fabric_vc_pmsb_tunl","fabric_cfg_pmsb_tunl",fabric_cfg_pmsb_tunl);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_rsrc_phy_pm","fabric_cfg_iosf_rsrc_phy_pm",fabric_cfg_iosf_rsrc_phy_pm);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_rsrc_pll_pm","fabric_cfg_iosf_rsrc_pll_pm",fabric_cfg_iosf_rsrc_pll_pm);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_isa_gp","fabric_cfg_iosf_isa_gp",fabric_cfg_iosf_isa_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_ula_0_gp","fabric_cfg_iosf_ula_0_gp",fabric_cfg_iosf_ula_0_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_ula_1_gp","fabric_cfg_iosf_ula_1_gp",fabric_cfg_iosf_ula_1_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_dda_0_gp","fabric_cfg_iosf_dda_0_gp",fabric_cfg_iosf_dda_0_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_dda_1_gp","fabric_cfg_iosf_dda_1_gp",fabric_cfg_iosf_dda_1_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_phy_0_gp","fabric_cfg_iosf_phy_0_gp",fabric_cfg_iosf_phy_0_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_phy_1_gp","fabric_cfg_iosf_phy_1_gp",fabric_cfg_iosf_phy_1_gp);
  uvm_config_object::set(this,"iosf_sbc_fabric_vc_phy_2_gp","fabric_cfg_iosf_phy_2_gp",fabric_cfg_iosf_phy_2_gp);

  iosf_sbc_fabric_vc_rsrc_phy_pm = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_rsrc_phy_pm", this);
  iosf_sbc_fabric_vc_rsrc_pll_pm = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_rsrc_pll_pm", this);
  iosf_sbc_fabric_vc_isa_gp    = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_isa_gp", this);
  iosf_sbc_fabric_vc_ula_0_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_ula_0_gp", this);
  iosf_sbc_fabric_vc_ula_1_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_ula_1_gp", this);
  iosf_sbc_fabric_vc_dda_0_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_dda_0_gp", this);
  iosf_sbc_fabric_vc_dda_1_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_dda_1_gp", this);
  iosf_sbc_fabric_vc_phy_0_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_phy_0_gp", this);
  iosf_sbc_fabric_vc_phy_1_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_phy_1_gp", this);
  iosf_sbc_fabric_vc_phy_2_gp = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_phy_2_gp", this);
  
  iosf_sbc_fabric_vc_rsrc_phy_pm.cfg_name = "fabric_cfg_iosf_rsrc_phy_pm";
  iosf_sbc_fabric_vc_rsrc_pll_pm.cfg_name = "fabric_cfg_iosf_rsrc_pll_pm";
  iosf_sbc_fabric_vc_isa_gp.cfg_name = "fabric_cfg_iosf_isa_gp";
  iosf_sbc_fabric_vc_ula_0_gp.cfg_name = "fabric_cfg_iosf_ula_0_gp";
  iosf_sbc_fabric_vc_ula_1_gp.cfg_name = "fabric_cfg_iosf_ula_1_gp";
  iosf_sbc_fabric_vc_dda_0_gp.cfg_name = "fabric_cfg_iosf_dda_0_gp";
  iosf_sbc_fabric_vc_dda_1_gp.cfg_name = "fabric_cfg_iosf_dda_1_gp";
  iosf_sbc_fabric_vc_phy_0_gp.cfg_name = "fabric_cfg_iosf_phy_0_gp";
  iosf_sbc_fabric_vc_phy_1_gp.cfg_name = "fabric_cfg_iosf_phy_1_gp";
  iosf_sbc_fabric_vc_phy_2_gp.cfg_name = "fabric_cfg_iosf_phy_2_gp";

//=========================================//


  sbbfm_cfg.num_lanes = 6;
  sbbfm_cfg.gpsb_indices =  '{'h0, 'h1, 'h2, 'h3, 'h4, 'h5, 'h6, 'h7, 'h8, 'h9, 'ha, 'hb, 'hc, 'hd, 'he, 'hf, 'h10, 'h11, 'h12, 'h13, 'h14, 'h15, 'h16, 'h17, 'h18, 'h19, 'h1a, 'h1b, 'h1c, 'h1d, 'h1e, 'h1f};
  sbbfm_cfg.pmsb_indices =  '{'h0, 'h1, 'h2, 'h3, 'h4, 'h5, 'h6, 'h7, 'h8, 'h9, 'ha, 'hb, 'hc, 'hd, 'he, 'hf};
  sbbfm_cfg.num_v_wires_in = 64;
  sbbfm_cfg.num_v_wires_out = 64;
  sbbfm_cfg.global_time_align = 5'h0;
  sbbfm_cfg.ref_d2d_credits_en = 1;
//sbbfm_cfg.DEFAULT_D2D_CREDITS = 16;
  sbbfm_cfg.d2d_pc_gpsb_credits = 16;
  sbbfm_cfg.d2d_np_gpsb_credits = 16;
  sbbfm_cfg.d2d_pc_pmsb_credits = 16;
  sbbfm_cfg.d2d_np_pmsb_credits = 16;
  sbbfm_cfg.dtf_data_en=1; 
  sbbfm_cfg.dtf_ctrl_en=1;
  sbbfm_cfg.ref_d2d_dtf_credits = 0;
  sbbfm_cfg.initpkt_delay = 0;
  sbbfm_cfg.force_initpkt_noop = 0;

    
  if ($value$plusargs("STRAP_DEFAULT_WIRES_OUT_VALUE=%x", default_strap_vlw_in)) begin
     sbbfm_cfg.default_vlw_in.rand_mode(0);
     sbbfm_cfg.default_vlw_in = default_strap_vlw_in;
     `uvm_info(get_name(), $sformatf("BFM STRAP_DEFAULT_WIRES_IN %x", sbbfm_cfg.default_vlw_in), UVM_HIGH) 
  end else begin
     sbbfm_cfg.default_vlw_in.rand_mode(0);
     sbbfm_cfg.default_vlw_in = 0;//this needs to connect to strap_default_wires_out
     `uvm_info(get_name(), $sformatf("BFM STRAP_DEFAULT_WIRES_IN %x", sbbfm_cfg.default_vlw_in), UVM_HIGH)
  end
  if ($value$plusargs("STRAP_DEFAULT_WIRES_IN_VALUE=%x", default_strap_vlw_out)) begin
     sbbfm_cfg.default_vlw_out.rand_mode(0);
     sbbfm_cfg.default_vlw_out = default_strap_vlw_out;
     `uvm_info(get_name(), $sformatf("BFM STRAP_DEFAULT_WIRES_OUT %x", sbbfm_cfg.default_vlw_out), UVM_HIGH)
  end else begin
     sbbfm_cfg.default_vlw_out.rand_mode(0);
     sbbfm_cfg.default_vlw_out = 0;//this needs to connect to strap_default_wires_out
     `uvm_info(get_name(), $sformatf("BFM STRAP_DEFAULT_WIRES_OUT %x", sbbfm_cfg.default_vlw_out), UVM_HIGH)
  end


  uvm_config_db#(uciesbbfm_config)::set(this, "sbbfm_agent_env_0", "sbbfm_cfg", sbbfm_cfg);


  //uvm_config_db#(int)::dump();



endfunction

function void d2d_env::connect_phase(uvm_phase phase);
  super.connect_phase(phase);

  //cbb hotfix
  sbbfm_agent_env_0.pmsb_fabric_cfg_i.global_intf_en = 1;
  sbbfm_agent_env_0.pmsb_fabric_cfg_i.segment_scaling = 1;
  sbbfm_agent_env_0.pmsb_fabric_cfg_i.is_active = bfm_mode; 

  sbbfm_agent_env_0.gpsb_fabric_cfg_i.global_intf_en = 1;
  sbbfm_agent_env_0.gpsb_fabric_cfg_i.segment_scaling = 1;
  sbbfm_agent_env_0.gpsb_fabric_cfg_i.is_active = bfm_mode; 
endfunction
