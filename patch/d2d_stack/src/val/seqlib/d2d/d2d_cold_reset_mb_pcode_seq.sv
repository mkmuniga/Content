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

class d2d_cold_reset_mb_pcode_seq extends d2d_base_sequence;
   `uvm_object_utils(d2d_cold_reset_mb_pcode_seq);

   rand int env_inst; //cbb hotfix

   function new (string name = "d2d_cold_reset_mb_pcode_seq");
       super.new(name);
   endfunction   

   task body;
     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_mb_pcode_seq started: env_inst=%0d", env_inst), UVM_LOW)

   fork
     begin //ULA0 and DDA0 path

         //RDI0 Interface brinup.
         wait((d2d_reset_vif[env_inst].rdi0_pl_clk_req === 1'b1) && (d2d_reset_vif[env_inst].rdi0_lp_clk_ack === 1'b1) ); 
         wait( d2d_reset_vif[env_inst].rdi0_pl_inband_pres === 1'b1);
         wait((d2d_reset_vif[env_inst].rdi0_lp_wake_req === 1'b1) && (d2d_reset_vif[env_inst].rdi0_pl_wake_ack === 1'b1) ); 
         wait( d2d_reset_vif[env_inst].rdi0_lp_state_req === 4'h1); //Active 
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_linkmgmt_rdi0_req_active ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_linkmgmt_rdi0_req_active ;
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_linkmgmt_rdi0_rsp_active ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_linkmgmt_rdi0_rsp_active ;
         wait( (d2d_reset_vif[env_inst].rdi0_lp_state_req === 4'h1) && (d2d_reset_vif[env_inst].rdi0_pl_state_sts === 4'h1) ); //Active

      //-----------------------------------------------------------------------------------//    
      // wait(d2d_reset_vif[env_inst].phy_ucie_link_control_start_link_training_clear = ;
      //-----------------------------------------------------------------------------------//    
          
         //FDI0 Interface brinup.
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_advcap_Adapter = ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_advcap_Adapter = ;
         wait((d2d_reset_vif[env_inst].dda0_fdi0_pl_clk_req === 1'b1) && (d2d_reset_vif[env_inst].dda0_fdi0_lp_clk_ack === 1'b1) );
         wait( d2d_reset_vif[env_inst].dda0_fdi0_pl_inband_pres === 1'b1); 
         wait((d2d_reset_vif[env_inst].dda0_fdi0_lp_wake_req === 1'b1) && (d2d_reset_vif[env_inst].dda0_fdi0_pl_wake_ack == 1'b1) );
         wait(d2d_reset_vif[env_inst].dda0_fdi0_lp_state_req === 4'h1); //Active 
      // wait(d2d_reset_vif[env_inst].dda_tx_sb_msg_linkmgmt_fdi_req_active ;
      // wait(d2d_reset_vif[env_inst].dda_rx_sb_msg_linkmgmt_fdi_req_active ;
      // wait(d2d_reset_vif[env_inst].dda_tx_sb_msg_linkmgmt_fdi_rsp_active ;
      // wait(d2d_reset_vif[env_inst].dda_rx_sb_msg_linkmgmt_fdi_rsp_active ;
         wait( (d2d_reset_vif[env_inst].dda0_fdi0_lp_state_req === 4'h1) && (d2d_reset_vif[env_inst].dda0_fdi0_pl_state_sts === 4'h1) ); //Active
     end //ULA0 and DDA0 Path 
     begin //ULA1 and DDA1 path

         //RDI1 Interface brinup.
         wait((d2d_reset_vif[env_inst].rdi1_pl_clk_req === 1'b1) && (d2d_reset_vif[env_inst].rdi1_lp_clk_ack === 1'b1) ); 
         wait( d2d_reset_vif[env_inst].rdi1_pl_inband_pres === 1'b1);
         wait((d2d_reset_vif[env_inst].rdi1_lp_wake_req === 1'b1) && (d2d_reset_vif[env_inst].rdi1_pl_wake_ack === 1'b1) ); 
         wait( d2d_reset_vif[env_inst].rdi1_lp_state_req === 4'h1); //Active 
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_linkmgmt_rdi1_req_active ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_linkmgmt_rdi1_req_active ;
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_linkmgmt_rdi1_rsp_active ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_linkmgmt_rdi1_rsp_active ;
         wait( (d2d_reset_vif[env_inst].rdi1_lp_state_req === 4'h1) && (d2d_reset_vif[env_inst].rdi1_pl_state_sts === 4'h1) ); //Active

      //-----------------------------------------------------------------------------------//    
      // wait(d2d_reset_vif[env_inst].phy_ucie_link_control_start_link_training_clear = ;
      //-----------------------------------------------------------------------------------//    
          
         //FDI1 Interface brinup.
      // wait(d2d_reset_vif[env_inst].phy_tx_sb_msg_advcap_Adapter = ;
      // wait(d2d_reset_vif[env_inst].phy_rx_sb_msg_advcap_Adapter = ;
         wait((d2d_reset_vif[env_inst].dda1_fdi0_pl_clk_req === 1'b1) && (d2d_reset_vif[env_inst].dda1_fdi0_lp_clk_ack === 1'b1) );
         wait( d2d_reset_vif[env_inst].dda1_fdi0_pl_inband_pres === 1'b1); 
         wait((d2d_reset_vif[env_inst].dda1_fdi0_lp_wake_req === 1'b1) && (d2d_reset_vif[env_inst].dda1_fdi0_pl_wake_ack == 1'b1) );
         wait(d2d_reset_vif[env_inst].dda1_fdi0_lp_state_req === 4'h1); //Active 
      // wait(d2d_reset_vif[env_inst].dda_tx_sb_msg_linkmgmt_dda1_fdi0_req_active ;
      // wait(d2d_reset_vif[env_inst].dda_rx_sb_msg_linkmgmt_dda1_fdi0_req_active ;
      // wait(d2d_reset_vif[env_inst].dda_tx_sb_msg_linkmgmt_dda1_fdi0_rsp_active ;
      // wait(d2d_reset_vif[env_inst].dda_rx_sb_msg_linkmgmt_dda1_fdi0_rsp_active ;
         wait( (d2d_reset_vif[env_inst].dda1_fdi0_lp_state_req === 4'h1) && (d2d_reset_vif[env_inst].dda1_fdi0_pl_state_sts === 4'h1) ); //Active
     end //ULA1 and DDA1 Path
   join ;

     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_mb_pcode_seq ended"), UVM_LOW)
   endtask: body
endclass: d2d_cold_reset_mb_pcode_seq
