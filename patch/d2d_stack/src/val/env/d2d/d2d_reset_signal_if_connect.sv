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
`define D2D_SIGNAL_PAD(TYPE,LEFT,RIGHT)\
    ``TYPE`` ``LEFT```D2D_SPAD``RIGHT``;\

`define UCIE_PHY_HIP_0  `UCIE_PHY.i_ucie_ophy_m2_p76p9_hip_0//cbb hotfix
`define UCIE_PHY_HIP_1  `UCIE_PHY.i_ucie_ophy_m2_p76p9_hip_1//cbb hotfix
`define UCIE_PHY_HIP_2  `UCIE_PHY.i_ucie_ophy_m2_p76p9_hip_2//cbb hotfix

d2d_reset_signal_if d2d_reset_vif();
`ifdef D2D_TB
//---------------------------------------------------------------//
// SB Reset flow diagram based on D2D stack MAS Reset Flows.
// https://docs.intel.com/documents/arch_datacenter/DMR_MAS/D2D%20Stack/D2D%20Stack%20MAS.html#d2d-stack-reset-domain-wanyu-li
//  Signals to be added  for D2D-DMR
//  IMH reference : src/val/intf/imh/reset_signal_if.sv 
//---------------------------------------------------------------//
//power good signals
//   assign d2d_reset_vif.xx_s0_pwr_ok = 1'b0;
//   assign d2d_reset_vif.xx_xtal_clk = 1'b0;
//   assign d2d_reset_vif.cropll_clkout1_div2_locked = 1'b0; //1600/2 = 800MHz
//   assign d2d_reset_vif.xx_cpupwrgood = 1'b0;
//   assign d2d_reset_vif.hwrs_powerup = 1'b0;
//   assign d2d_reset_vif.stw_sb_pwrgood_rst_b = 1'b0;
//   assign d2d_reset_vif.hwrs_fuse_xfer = 1'b0; 
//   assign d2d_reset_vif.rstw_sb_serial_shift = 1'b0;
//   assign d2d_reset_vif.fpc_ser_fuse_wire = 1'b0;
//   
//   //Reset Phase3 D2D config
   assign d2d_reset_vif.rstw_sb2ucie_ser_fuse_xfer_done      = `RSTW_SB2UCIE.fuse_rstw_ip_cfg_done;
   assign d2d_reset_vif.rstw_sb2ucie_clk                     = `RSTW_SB2UCIE.clk; 
   assign d2d_reset_vif.rstw_sb2ucie_rst_b                   = `RSTW_SB2UCIE.rst_b; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_cmd_data          = `RSTW_SB2UCIE.reset_cmd_data;
   assign d2d_reset_vif.rstw_sb2ucie_reset_cmd_valid         = `RSTW_SB2UCIE.reset_cmd_valid; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_cmd_parity        = `RSTW_SB2UCIE.reset_cmd_parity; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_error             = `RSTW_SB2UCIE.reset_error; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_cmd_ack           = `RSTW_SB2UCIE.reset_cmd_ack; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_adapt_rst_b        = `RSTW_SB2UCIE.rstw_adapt_rst_b; 
   assign d2d_reset_vif.rstw_sb2ucie_ip_disabled             = `RSTW_SB2UCIE.ip_disabled; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_exit_done         = `RSTW_SB2UCIE.reset_exit_done; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_adapt_resource_en  = `RSTW_SB2UCIE.rstw_adapt_resource_en; 
   assign d2d_reset_vif.rstw_sb2ucie_ip_rstw_resource_check  = `RSTW_SB2UCIE.ip_rstw_resource_check; 
   assign d2d_reset_vif.rstw_sb2ucie_fuse_rstw_ip_cfg_done   = `RSTW_SB2UCIE.fuse_rstw_ip_cfg_done; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_pwrgood_rst_b   = `RSTW_SB2UCIE.rstw_ip_pwrgood_rst_b;
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_side_rst_b      = `RSTW_SB2UCIE.rstw_ip_side_rst_b; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_prim_rst_b      = `RSTW_SB2UCIE.rstw_ip_prim_rst_b; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_config_req      = `RSTW_SB2UCIE.rstw_ip_config_req; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_config_done     = `RSTW_SB2UCIE.rstw_ip_config_done; 
   assign d2d_reset_vif.rstw_sb2ucie_rstw_ip_wake            = `RSTW_SB2UCIE.rstw_ip_wake; 
   assign d2d_reset_vif.rstw_sb2ucie_reset_entry_done        = `RSTW_SB2UCIE.reset_entry_done; 
   assign d2d_reset_vif.rstw_sb2ucie_ip_ready                = `RSTW_SB2UCIE.ip_ready; 
   assign d2d_reset_vif.rstw_sb2ucie_strap_port_id           = `RSTW_SB2UCIE.strap_port_id; 
   assign d2d_reset_vif.rstw_sb2ucie_strap_group_id0         = `RSTW_SB2UCIE.strap_group_id0; 
   assign d2d_reset_vif.rstw_sb2ucie_strap_group_id1         = `RSTW_SB2UCIE.strap_group_id1;


`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_sb_cri_fuse_xfer_done      =, `PARD2DMISC.fpc_cri_phy,_fpc_rstw_xfer_done);
   assign d2d_reset_vif.rstw_sb_clk                     = `RSTW_SB.clk; 
   assign d2d_reset_vif.rstw_sb_rst_b                   = `RSTW_SB.rst_b; 
   assign d2d_reset_vif.rstw_sb_reset_cmd_data          = `RSTW_SB.reset_cmd_data;
   assign d2d_reset_vif.rstw_sb_reset_cmd_valid         = `RSTW_SB.reset_cmd_valid; 
   assign d2d_reset_vif.rstw_sb_reset_cmd_parity        = `RSTW_SB.reset_cmd_parity; 
   assign d2d_reset_vif.rstw_sb_reset_error             = `RSTW_SB.reset_error; 
   assign d2d_reset_vif.rstw_sb_reset_cmd_ack           = `RSTW_SB.reset_cmd_ack; 
   assign d2d_reset_vif.rstw_sb_rstw_adapt_rst_b        = `RSTW_SB.rstw_adapt_rst_b; 
   assign d2d_reset_vif.rstw_sb_ip_disabled             = `RSTW_SB.ip_disabled; 
   assign d2d_reset_vif.rstw_sb_reset_exit_done         = `RSTW_SB.reset_exit_done; 
   assign d2d_reset_vif.rstw_sb_rstw_adapt_resource_en  = `RSTW_SB.rstw_adapt_resource_en; 
   assign d2d_reset_vif.rstw_sb_ip_rstw_resource_check  = `RSTW_SB.ip_rstw_resource_check; 
   assign d2d_reset_vif.rstw_sb_fuse_rstw_ip_cfg_done   = `RSTW_SB.fuse_rstw_ip_cfg_done; 
   assign d2d_reset_vif.rstw_sb_rstw_ip_pwrgood_rst_b   = `RSTW_SB.rstw_ip_pwrgood_rst_b;
   assign d2d_reset_vif.rstw_sb_rstw_ip_side_rst_b      = `RSTW_SB.rstw_ip_side_rst_b; 
   assign d2d_reset_vif.rstw_sb_rstw_ip_prim_rst_b      = `RSTW_SB.rstw_ip_prim_rst_b; 
   assign d2d_reset_vif.rstw_sb_rstw_ip_config_req      = `RSTW_SB.rstw_ip_config_req; 
   assign d2d_reset_vif.rstw_sb_rstw_ip_config_done     = `RSTW_SB.rstw_ip_config_done; 
   assign d2d_reset_vif.rstw_sb_rstw_ip_wake            = `RSTW_SB.rstw_ip_wake; 
   assign d2d_reset_vif.rstw_sb_reset_entry_done        = `RSTW_SB.reset_entry_done; 
   assign d2d_reset_vif.rstw_sb_ip_ready                = `RSTW_SB.ip_ready; 
   assign d2d_reset_vif.rstw_sb_strap_port_id           = `RSTW_SB.strap_port_id; 
   assign d2d_reset_vif.rstw_sb_strap_group_id0         = `RSTW_SB.strap_group_id0; 
   assign d2d_reset_vif.rstw_sb_strap_group_id1         = `RSTW_SB.strap_group_id1;





//   assign d2d_reset_vif.sapll_clkout1_div2_locked = 1'b0; //1600/2 = 800MHz
//   assign d2d_reset_vif.hwrs_soc_infra_sb_rst_b = 1'b0;
//    
//   assign d2d_reset_vif.infra_die_sb_infra_up0 = 1'b0;
//    
//   assign d2d_reset_vif.clk_src_rdy = 1'b0;
//   assign d2d_reset_vif.fpc_rstw_xfer_done = 1'b0;
//    
//   assign d2d_reset_vif.rstw_sb_prim_rst_b = 1'b0;
//    
//   assign d2d_reset_vif.sb0_phy_to_sb1_phy_training = 1'b0;
//   assign d2d_reset_vif.sb1_phy_to_sb0_phy_training = 1'b0;
//    
//   assign d2d_reset_vif.sb0_phy_to_sb2ucie0_ip_ready_wire = 1'b0;
//   assign d2d_reset_vif.sb1_phy_to_sb2ucie1_ip_ready_wire = 1'b0;
//    
//   assign d2d_reset_vif.sb2ucie0_to_sb2ucie1_sbmsg_link_init_req = 1'b0;
//   assign d2d_reset_vif.sb2ucie1_to_sb2ucie0_sbmsg_link_init_req = 1'b0;
//   assign d2d_reset_vif.sb2ucie1_to_sb2ucie0_sbmsg_ack;
//   assign d2d_reset_vif.sb2ucie0_to_sb2ucie1_sbmsg_ack = 1'b0;
//    
//   assign d2d_reset_vif.sb2ucie_to_hwrs_ip_ready_wire = 1'b0;
//   assign d2d_reset_vif.socdie_register_die_ready_set_to_1 = 1'b0;
//    
//   assign d2d_reset_vif.sb2ucie_hwrs_hwsync_req_in = 1'b0; 
//   assign d2d_reset_vif.sb2ucie1_to_sb2ucie0_sbmsg_hwsync_req_out = 1'b0; 
//   assign d2d_reset_vif.hwrs1_to_sb2ucie1_hwsync_req_out = 1'b0; 
//   assign d2d_reset_vif.hwrs_sb2ucie_hwsync_ack_out = 1'b0; 
//   assign d2d_reset_vif.sb2ucie0_to_sb2ucie1_sbmsg_hwsync_ack_out = 1'b0 
//   assign d2d_reset_vif.sb2ucie1_to_hwrs1_hwsync_ack_in = 1'b0;
//    
//   assign d2d_reset_vif.hwrs_to_s3m_d2d_hwsync_ack = 1'b0;
//   assign d2d_reset_vif.infra_die_sb_infra_up1 = 1'b0;

     assign d2d_reset_vif.iosfsb2ucie_ptx_all_lane_cfg_ok = `IOSFSB2UCIE.ptx_all_lane_cfg_ok;
`D2D_SIGNAL_PAD(assign d2d_reset_vif.iosfsb2ucie_d2d_0_ip_ready      =, `PARD2DMISC.iosfsb2ucie,_ip_ready);
     assign d2d_reset_vif.iosfsb2ucie_async_virt_in       = `IOSFSB2UCIE.async_virt_in;
     assign d2d_reset_vif.iosfsb2ucie_async_virt_out      = `IOSFSB2UCIE.async_virt_out;

//   
//   //----------------------------------------------------------------------//
//   //Main Band Reset signals 
//   //----------------------------------------------------------------------//
//   //Phase3 Infra config
`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_pll_cri_fuse_xfer_done      =, `PARD2DMISC.fpc_cri_pll,_fpc_rstw_xfer_done);
`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_pll_pll_ratio               =, `PARD2DMISC.rsrc_adapt_pll,_pll_ratio_h);
`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_pll_pll_mode                =, `PARD2DMISC.rstw_pll,_rstw_fuse_fpc_mode);
`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_pll_pll_lock_en             =, `PARD2DMISC.rsrc_adapt_pll,_pll_locken_l);
`D2D_SIGNAL_PAD(assign d2d_reset_vif.rstw_pll_o_pll_lock              =, `PARD2DMISC.rsrc_adapt_phy,_pll_lock_final_sticky_l);
   assign d2d_reset_vif.rstw_pll_clk                     = `RSTW_PLL.clk; 
   assign d2d_reset_vif.rstw_pll_rst_b                   = `RSTW_PLL.rst_b; 
   assign d2d_reset_vif.rstw_pll_reset_cmd_data          = `RSTW_PLL.reset_cmd_data;
   assign d2d_reset_vif.rstw_pll_reset_cmd_valid         = `RSTW_PLL.reset_cmd_valid; 
   assign d2d_reset_vif.rstw_pll_reset_cmd_parity        = `RSTW_PLL.reset_cmd_parity; 
   assign d2d_reset_vif.rstw_pll_reset_error             = `RSTW_PLL.reset_error; 
   assign d2d_reset_vif.rstw_pll_reset_cmd_ack           = `RSTW_PLL.reset_cmd_ack; 
   assign d2d_reset_vif.rstw_pll_rstw_adapt_rst_b        = `RSTW_PLL.rstw_adapt_rst_b; 
   assign d2d_reset_vif.rstw_pll_ip_disabled             = `RSTW_PLL.ip_disabled; 
   assign d2d_reset_vif.rstw_pll_reset_exit_done         = `RSTW_PLL.reset_exit_done; 
   assign d2d_reset_vif.rstw_pll_rstw_adapt_resource_en  = `RSTW_PLL.rstw_adapt_resource_en; 
   assign d2d_reset_vif.rstw_pll_ip_rstw_resource_check  = `RSTW_PLL.ip_rstw_resource_check; 
   assign d2d_reset_vif.rstw_pll_fuse_rstw_ip_cfg_done   = `RSTW_PLL.fuse_rstw_ip_cfg_done; 
   assign d2d_reset_vif.rstw_pll_rstw_ip_pwrgood_rst_b   = `RSTW_PLL.rstw_ip_pwrgood_rst_b;
   assign d2d_reset_vif.rstw_pll_rstw_ip_side_rst_b      = `RSTW_PLL.rstw_ip_side_rst_b; 
   assign d2d_reset_vif.rstw_pll_rstw_ip_prim_rst_b      = `RSTW_PLL.rstw_ip_prim_rst_b; 
   assign d2d_reset_vif.rstw_pll_rstw_ip_config_req      = `RSTW_PLL.rstw_ip_config_req; 
   assign d2d_reset_vif.rstw_pll_rstw_ip_config_done     = `RSTW_PLL.rstw_ip_config_done; 
   assign d2d_reset_vif.rstw_pll_rstw_ip_wake            = `RSTW_PLL.rstw_ip_wake; 
   assign d2d_reset_vif.rstw_pll_reset_entry_done        = `RSTW_PLL.reset_entry_done; 
   assign d2d_reset_vif.rstw_pll_ip_ready                = `RSTW_PLL.ip_ready; 
   assign d2d_reset_vif.rstw_pll_strap_port_id           = `RSTW_PLL.strap_port_id; 
   assign d2d_reset_vif.rstw_pll_strap_group_id0         = `RSTW_PLL.strap_group_id0; 
   assign d2d_reset_vif.rstw_pll_strap_group_id1         = `RSTW_PLL.strap_group_id1;

//   //Phase4 IP Bringup
   assign d2d_reset_vif.rstw_mb_ser_fuse_xfer_done      = `RSTW_MB.fuse_rstw_ip_cfg_done;
   assign d2d_reset_vif.rstw_mb_clk                     = `RSTW_MB.clk; 
   assign d2d_reset_vif.rstw_mb_rst_b                   = `RSTW_MB.rst_b; 
   assign d2d_reset_vif.rstw_mb_reset_cmd_data          = `RSTW_MB.reset_cmd_data;
   assign d2d_reset_vif.rstw_mb_reset_cmd_valid         = `RSTW_MB.reset_cmd_valid; 
   assign d2d_reset_vif.rstw_mb_reset_cmd_parity        = `RSTW_MB.reset_cmd_parity; 
   assign d2d_reset_vif.rstw_mb_reset_error             = `RSTW_MB.reset_error; 
   assign d2d_reset_vif.rstw_mb_reset_cmd_ack           = `RSTW_MB.reset_cmd_ack; 
   assign d2d_reset_vif.rstw_mb_rstw_adapt_rst_b        = `RSTW_MB.rstw_adapt_rst_b; 
   assign d2d_reset_vif.rstw_mb_ip_disabled             = `RSTW_MB.ip_disabled; 
   assign d2d_reset_vif.rstw_mb_reset_exit_done         = `RSTW_MB.reset_exit_done; 
   assign d2d_reset_vif.rstw_mb_rstw_adapt_resource_en  = `RSTW_MB.rstw_adapt_resource_en; 
   assign d2d_reset_vif.rstw_mb_ip_rstw_resource_check  = `RSTW_MB.ip_rstw_resource_check; 
   assign d2d_reset_vif.rstw_mb_fuse_rstw_ip_cfg_done   = `RSTW_MB.fuse_rstw_ip_cfg_done; 
   assign d2d_reset_vif.rstw_mb_rstw_ip_pwrgood_rst_b   = `RSTW_MB.rstw_ip_pwrgood_rst_b;
   assign d2d_reset_vif.rstw_mb_rstw_ip_side_rst_b      = `RSTW_MB.rstw_ip_side_rst_b; 
   assign d2d_reset_vif.rstw_mb_rstw_ip_prim_rst_b      = `RSTW_MB.rstw_ip_prim_rst_b; 
   assign d2d_reset_vif.rstw_mb_rstw_ip_config_req      = `RSTW_MB.rstw_ip_config_req; 
   assign d2d_reset_vif.rstw_mb_rstw_ip_config_done     = `RSTW_MB.rstw_ip_config_done; 
   assign d2d_reset_vif.rstw_mb_rstw_ip_wake            = `RSTW_MB.rstw_ip_wake; 
   assign d2d_reset_vif.rstw_mb_reset_entry_done        = `RSTW_MB.reset_entry_done; 
   assign d2d_reset_vif.rstw_mb_ip_ready                = `RSTW_MB.ip_ready; 
   assign d2d_reset_vif.rstw_mb_strap_port_id           = `RSTW_MB.strap_port_id; 
   assign d2d_reset_vif.rstw_mb_strap_group_id0         = `RSTW_MB.strap_group_id0; 
   assign d2d_reset_vif.rstw_mb_strap_group_id1         = `RSTW_MB.strap_group_id1;

  assign d2d_reset_vif.dda0_rst_actions_done = `DDA0.uciedda.lcm_inst.reg_inst.iosf_sb_rst_actions_done; 
  assign d2d_reset_vif.dda1_rst_actions_done = `DDA1.uciedda.lcm_inst.reg_inst.iosf_sb_rst_actions_done; 
  assign d2d_reset_vif.ula0_rst_actions_done = `ULA0.ula.ulaln_inst.ulacw_inst.ulalncru_inst.ularstsm_inst.ula_sb_rst_actions_done; 
  assign d2d_reset_vif.ula1_rst_actions_done = `ULA1.ula.ulaln_inst.ulacw_inst.ulalncru_inst.ularstsm_inst.ula_sb_rst_actions_done; 


//`ULA0.ula.ulaln_inst.ulacw_inst.ulalncru_inst.ularstsm_inst.ula_sb_rst_actions_done   & //second level pulse 
//`ULA0.ula.ulaln_inst.ulacw_inst.ulalncru_inst.ularstsm_inst.ula_link_rst_actions_done & //second level pulse
//`ULA0.ula.ulaln_inst.ulacw_inst.ulalncru_inst.ularstsm_inst.ula_fsm_rst_actions_done  & //first level pulse 

`D2D_SIGNAL_PAD(assign d2d_reset_vif.d2d_reset_error =, `PARD2DMISC.d2d_reset_error_or_3_1,_out);
   assign d2d_reset_vif.rstw_mb_clk_lock = `RSTW_MB.clk_lock; 
   assign d2d_reset_vif.LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[0] = `UCIE_PHY_HIP_0.i_ucie_oglobal_m2_p76p9_top_1.i_ucie_ldo_lcpll_wrapper.i_ucie_lcpll_wrapper.i_ucie_lcpll_hip.plldigtop0.crislv0.DIV0.I_REFCLKFREQ_OVERRIDE_VALUE_7_0[7:0];
   assign d2d_reset_vif.LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[1] = `UCIE_PHY_HIP_1.i_ucie_oglobal_m2_p76p9_top_1.i_ucie_ldo_lcpll_wrapper.i_ucie_lcpll_wrapper.i_ucie_lcpll_hip.plldigtop0.crislv0.DIV0.I_REFCLKFREQ_OVERRIDE_VALUE_7_0[7:0];
   assign d2d_reset_vif.LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[2] = `UCIE_PHY_HIP_2.i_ucie_oglobal_m2_p76p9_top_1.i_ucie_ldo_lcpll_wrapper.i_ucie_lcpll_wrapper.i_ucie_lcpll_hip.plldigtop0.crislv0.DIV0.I_REFCLKFREQ_OVERRIDE_VALUE_7_0[7:0];

   //Phase5 IP Config
   assign d2d_reset_vif.phy_config_req  = `UCIE_PHY.i_ophy_config_req; 
   assign d2d_reset_vif.phy_config_ack  = `UCIE_PHY.o_ophy_config_ack;
   assign d2d_reset_vif.reg_isa_config_req  = `ISA_D2D.isa_base_reg_bank.ISA_CONFIG_REQ;
   assign d2d_reset_vif.reg_isa_config_ack  = `ISA_D2D.isa_base_reg_bank.ISA_CONFIG_ACK; 
   assign d2d_reset_vif.reg_isa_config_done = `ISA_D2D.isa_base_reg_bank.ISA_CONFIG_DONE; 
//    
//   //Brought mainband up
//   //sets up basic crediting and legacy IO mesh ID
//   //Possible servivability patch
//   
//   assign d2d_reset_vif.ucie_link_control_target_link_speed;
//   assign d2d_reset_vif.ucie_link_control_start_ucie_link_training;
    
//   assign d2d_reset_vif.phy0_phy1_training;
//   assign d2d_reset_vif.phy1_phy0_training;
    
   assign d2d_reset_vif.rdi0_pl_clk_req = `DDA0.uciedda.uciedda_rdi_pl_clk_req; 
   assign d2d_reset_vif.rdi1_pl_clk_req = `DDA1.uciedda.uciedda_rdi_pl_clk_req; 
   assign d2d_reset_vif.rdi0_lp_clk_ack = `DDA0.uciedda.uciedda_rdi_lp_clk_ack; 
   assign d2d_reset_vif.rdi1_lp_clk_ack = `DDA1.uciedda.uciedda_rdi_lp_clk_ack; 

   assign d2d_reset_vif.rdi0_pl_inband_pres = `DDA0.uciedda.uciedda_rdi_pl_inband_pres;
   assign d2d_reset_vif.rdi1_pl_inband_pres = `DDA1.uciedda.uciedda_rdi_pl_inband_pres;
    
   assign d2d_reset_vif.rdi0_lp_wake_req = `DDA0.uciedda.uciedda_rdi_lp_wake_req; 
   assign d2d_reset_vif.rdi1_lp_wake_req = `DDA1.uciedda.uciedda_rdi_lp_wake_req; 
   assign d2d_reset_vif.rdi0_pl_wake_ack = `DDA0.uciedda.uciedda_rdi_pl_wake_ack; 
   assign d2d_reset_vif.rdi1_pl_wake_ack = `DDA1.uciedda.uciedda_rdi_pl_wake_ack; 
    
   assign d2d_reset_vif.rdi0_lp_state_req = `DDA0.uciedda.uciedda_rdi_lp_state_req; 
   assign d2d_reset_vif.rdi1_lp_state_req = `DDA1.uciedda.uciedda_rdi_lp_state_req; 
    
//   assign d2d_reset_vif.phy_tx_sb_msg_linkmgmt_rdi0_req_active = ;
//   assign d2d_reset_vif.phy_rx_sb_msg_linkmgmt_rdi0_req_active = ;
//   assign d2d_reset_vif.phy_tx_sb_msg_linkmgmt_rdi0_rsp_active = ;
//   assign d2d_reset_vif.phy_rx_sb_msg_linkmgmt_rdi0_rsp_active = ;
//   assign d2d_reset_vif.phy_tx_sb_msg_linkmgmt_rdi1_req_active = ;
//   assign d2d_reset_vif.phy_rx_sb_msg_linkmgmt_rdi1_req_active = ;
//   assign d2d_reset_vif.phy_tx_sb_msg_linkmgmt_rdi1_rsp_active = ;
//   assign d2d_reset_vif.phy_rx_sb_msg_linkmgmt_rdi1_rsp_active = ;
    
   assign d2d_reset_vif.rdi0_pl_state_sts = `DDA0.uciedda.uciedda_rdi_pl_state_sts;
   assign d2d_reset_vif.rdi1_pl_state_sts = `DDA1.uciedda.uciedda_rdi_pl_state_sts;
    
//   assign d2d_reset_vif.phy_ucie_link_control_start_link_training_clear = ;
    
 //  assign d2d_reset_vif.phy_tx_sb_msg_advcap_Adapter = ;
 //  assign d2d_reset_vif.phy_rx_sb_msg_advcap_Adapter = ;
    
   assign d2d_reset_vif.dda0_fdi0_pl_clk_req = `DDA0.uciedda.uciedda_fdi0_pl_clk_req; 
   assign d2d_reset_vif.dda1_fdi0_pl_clk_req = `DDA1.uciedda.uciedda_fdi0_pl_clk_req; 
   assign d2d_reset_vif.dda0_fdi0_lp_clk_ack = `DDA0.uciedda.uciedda_fdi0_lp_clk_ack;
   assign d2d_reset_vif.dda1_fdi0_lp_clk_ack = `DDA1.uciedda.uciedda_fdi0_lp_clk_ack;
    
   assign d2d_reset_vif.dda0_fdi0_pl_inband_pres = `DDA0.uciedda.uciedda_fdi0_pl_inband_pres; 
   assign d2d_reset_vif.dda1_fdi0_pl_inband_pres = `DDA1.uciedda.uciedda_fdi0_pl_inband_pres; 
    
   assign d2d_reset_vif.dda0_fdi0_lp_wake_req = `DDA0.uciedda.uciedda_fdi0_lp_wake_req; 
   assign d2d_reset_vif.dda1_fdi0_lp_wake_req = `DDA1.uciedda.uciedda_fdi0_lp_wake_req; 
   assign d2d_reset_vif.dda0_fdi0_pl_wake_ack = `DDA0.uciedda.uciedda_fdi0_pl_wake_ack; 
   assign d2d_reset_vif.dda1_fdi0_pl_wake_ack = `DDA1.uciedda.uciedda_fdi0_pl_wake_ack; 
    
   assign d2d_reset_vif.dda0_fdi0_lp_state_req = `DDA0.uciedda.uciedda_fdi0_lp_state_req; 
   assign d2d_reset_vif.dda1_fdi0_lp_state_req = `DDA1.uciedda.uciedda_fdi0_lp_state_req; 

//  assign d2d_reset_vif.dda_tx_sb_msg_linkmgmt_dda0_fdi0_req_active = `DDA0.;
//  assign d2d_reset_vif.dda_rx_sb_msg_linkmgmt_dda0_fdi0_req_active = `DDA0.;
//  assign d2d_reset_vif.dda_tx_sb_msg_linkmgmt_dda0_fdi0_rsp_active = `DDA0.;
//  assign d2d_reset_vif.dda_rx_sb_msg_linkmgmt_dda0_fdi0_rsp_active = `DDA0.;
//  assign d2d_reset_vif.dda_tx_sb_msg_linkmgmt_dda1_fdi0_req_active = `DDA0.;
//  assign d2d_reset_vif.dda_rx_sb_msg_linkmgmt_dda1_fdi0_req_active = `DDA0.;
//  assign d2d_reset_vif.dda_tx_sb_msg_linkmgmt_dda1_fdi0_rsp_active = `DDA0.;
//  assign d2d_reset_vif.dda_rx_sb_msg_linkmgmt_dda1_fdi0_rsp_active = `DDA0.;
    
   assign d2d_reset_vif.dda0_fdi0_pl_state_sts = `DDA0.uciedda.uciedda_fdi0_pl_state_sts; 
   assign d2d_reset_vif.dda1_fdi0_pl_state_sts = `DDA1.uciedda.uciedda_fdi0_pl_state_sts; 
   
//   assign d2d_reset_vif.dda_ip_ready = 1'b0;
//   assign d2d_reset_vif.phy_ip_ready = 1'b0;


//`DDA0.uciedda_rdi_pl_speedmode[2:0] 
//`DDA0.uciedda_rdi_pl_lnk_cfg[2:0]
//----------------------------------------------------------------------//
//Add relavent checks/assertions for the D2D stack cold reset SB and MB.
//----------------------------------------------------------------------//
`endif //D2D_TB
initial begin
   uvm_config_db#(virtual d2d_reset_signal_if)::set(null, "*", $sformatf("d2d_reset_vif[%0d]", ENV_INST), d2d_reset_vif);
end
