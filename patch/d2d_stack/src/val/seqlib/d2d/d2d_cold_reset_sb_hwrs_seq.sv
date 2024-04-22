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

class d2d_cold_reset_sb_hwrs_seq extends d2d_base_sequence;
   `uvm_object_utils(d2d_cold_reset_sb_hwrs_seq);

   d2d_hwrs_reset_cmd_bus_seq d2d_hwrs_reset_cmd_bus_seq_i;
   rand int env_inst; //cbb hotfix

   function new (string name = "d2d_cold_reset_sb_hwrs_seq");
       super.new(name);
   endfunction   

   task body;
     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_sb_hwrs_seq started: env_inst=%0d",env_inst), UVM_LOW)
     super.body();

     //Phase-3
     `uvm_info(get_full_name(), $sformatf("Cold_reset_SB: phase3 early infra reset started"), UVM_LOW)

     fork
       begin //RSTW_SB2UCIE and RSTW_SB commands.
          `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_SB2UCIE; cmd_opcode == GO_PWRUP;} );
          `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_SB;      cmd_opcode == GO_PWRUP;} );
	  wait((d2d_reset_vif[env_inst].rstw_sb2ucie_rstw_ip_pwrgood_rst_b === 1'b1) && (d2d_reset_vif[env_inst].rstw_sb_rstw_ip_side_rst_b === 1'b1) );
          `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_SB2UCIE; cmd_opcode == FUSE_XFER;} );
          `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_SB;      cmd_opcode == FUSE_XFER;} );
         //wait for RSTW_SB2UCIE prim and RSTW_SB prim Resets de-assertion
         wait((d2d_reset_vif[env_inst].rstw_sb2ucie_rstw_ip_prim_rst_b === 1'b1) && (d2d_reset_vif[env_inst].rstw_sb_rstw_ip_prim_rst_b === 1'b1) );
         `uvm_info(get_full_name(), $sformatf("Cold_reset_SB: phase3 D2D config started"), UVM_LOW)
       end
       begin //RSTW_SB2UCIE
          wait(d2d_reset_vif[env_inst].rstw_sb2ucie_rstw_ip_pwrgood_rst_b === 1'b1); 
          wait(d2d_reset_vif[env_inst].rstw_sb2ucie_rstw_ip_side_rst_b    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb2ucie_ser_fuse_xfer_done    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb2ucie_rstw_ip_prim_rst_b    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb2ucie_reset_exit_done       === 1'b1); //IP_ON
          `uvm_info(get_full_name(), $sformatf("Cold_reset_SB: phase3 early infra reset: RSTW_SB2UCIE IP_ON"), UVM_LOW)
       end
       begin //RSTW_SB
          wait(d2d_reset_vif[env_inst].rstw_sb_rstw_ip_pwrgood_rst_b === 1'b1); 
          wait(d2d_reset_vif[env_inst].rstw_sb_rstw_ip_side_rst_b    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb_cri_fuse_xfer_done    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb_rstw_ip_prim_rst_b    === 1'b1);
          wait(d2d_reset_vif[env_inst].rstw_sb_reset_exit_done       === 1'b1); //IP_ON
          `uvm_info(get_full_name(), $sformatf("Cold_reset_SB: phase3 early infra reset: RSTW_SB IP_ON"), UVM_LOW)
       end
     join_any;

     #2us; //TODO: SB PHY training and IP_OK wire

     wait fork; //to make sure all forked threads are completed.
     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_sb_hwrs_seq ended"), UVM_LOW)
   endtask: body

endclass: d2d_cold_reset_sb_hwrs_seq
