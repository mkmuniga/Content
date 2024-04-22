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

class d2d_cold_reset_mb_hwrs_seq extends d2d_base_sequence;
   `uvm_object_utils(d2d_cold_reset_mb_hwrs_seq);

   d2d_hwrs_reset_cmd_bus_seq d2d_hwrs_reset_cmd_bus_seq_i;
   rand int env_inst; //cbb hotfix
   rand int rstw_pll0_or_mb1; //cbb hotfix

   function new (string name = "d2d_cold_reset_mb_hwrs_seq");
       super.new(name);
   endfunction   

   task body;
     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_mb_hwrs_seq started: env_inst=%0d", env_inst), UVM_LOW)
     super.body();
     if( ($test$plusargs("D2D_R2B_RDI")) || ($test$plusargs("D2D_B2B_RDI")) )begin
        if (rstw_pll0_or_mb1 == 0) begin //cbb hotfix
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == GO_PWRUP;} );
           wait(d2d_reset_vif[env_inst].rstw_pll_rstw_ip_pwrgood_rst_b === 1'b1);
        end // if (rstw_pll0_or_mb1 == 0)
        else begin
           `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_MB; cmd_opcode == GO_PWRUP;} );
           wait(d2d_reset_vif[env_inst].rstw_mb_rstw_ip_pwrgood_rst_b  === 1'b1);
        end // else: !if(rstw_pll0_or_mb1 == 0)
     end
     else if( ($test$plusargs("D2D_R2B_PHY")) || ($test$plusargs("D2D_B2B_PHY")) || ($test$plusargs("D2D_R2B_IFSPHY")))begin
       //Phase-3
       `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase3 infra config started"), UVM_LOW)
       fork
         begin //RSTW_PLL follwed by RSTW_MB commands
            //UCIe PHY HAS: 10'hA0: 16GHz(160x100MHz refclk) or 10'h78: 12GHz(120x100MHz refclk) phy lock frequency.
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == GO_PWRUP;} );

             wait(d2d_reset_vif[env_inst].rstw_pll_rstw_ip_pwrgood_rst_b === 1'b1); 
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == FUSE_XFER;} );
            //PHY does not have FIVR.
            //`uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == SET_VOLTAGES; cmd_data == 11'h40;} ); //T0DO: 'd64
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == SET_RATIOS; cmd_data == 11'hA0;} );   //100MHz refclk x160 = 16GHz/2 = 8GHz 
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == PINS_MASK; cmd_data == 11'h10;} );

            wait(d2d_reset_vif[env_inst].rstw_pll_cri_fuse_xfer_done === 1'b1);
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase3 infra config: RSTW_PLL fuse xfer done"), UVM_LOW)
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == DRIVE_PINS; cmd_data == 11'h10;} );

            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_PLL; cmd_opcode == CHECK_DONE; cmd_data == 11'h1;} );
             
         end
         begin
            wait(d2d_reset_vif[env_inst].d2d_reset_error === 1'b0);
            wait(d2d_reset_vif[env_inst].d2d_reset_error === 1'b1); //assert PWR_UP_CHECK_DONE 
            wait((d2d_reset_vif[env_inst].rstw_pll_pll_lock_en === 1'b1)  && (d2d_reset_vif[env_inst].rstw_pll_o_pll_lock === 1'b1) );
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase3 infra config: RSTW_PLL pll locked"), UVM_LOW)
            wait(d2d_reset_vif[env_inst].d2d_reset_error === 1'b0); //de-assert after RSTW_PLL IP_ON.
            wait(d2d_reset_vif[env_inst].rstw_mb_clk_lock === 2'b11); 
           `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: RSTW_MB clock rdy asserted"), UVM_LOW)
         end
         begin //RSTW_PLL checks.
             wait(d2d_reset_vif[env_inst].rstw_pll_rstw_ip_pwrgood_rst_b === 1'b1); 
             wait(d2d_reset_vif[env_inst].rstw_pll_rstw_adapt_rst_b      === 1'b1)
             wait(d2d_reset_vif[env_inst].rstw_pll_rstw_ip_side_rst_b    === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_pll_pll_ratio             === 9'hA0); //TODO 
             wait(d2d_reset_vif[env_inst].rstw_pll_cri_fuse_xfer_done    === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_pll_rstw_ip_prim_rst_b    === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_pll_reset_exit_done       === 1'b1); //IP_ON
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase3 infra config: RSTW_PLL IP_ON"), UVM_LOW)
         end
         begin
            //RSTW_PLL fuse xfer data reached final destination register in UCIe PHY PLL.    
            //look for HWRS_PLL fuse data: src/val/seqlib/d2d/d2d_hwrs_reset_cmd_bus_seq.sv 
            wait(d2d_reset_vif[env_inst].LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[0] === 8'h32); //PHY HIP_0
            wait(d2d_reset_vif[env_inst].LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[1] === 8'h32); //PHY HIP_1
            wait(d2d_reset_vif[env_inst].LCPLL_DIV0_I_REFCLKFREQ_OVERRIDE_VALUE_7_0[2] === 8'h32); //PHY HIP_2
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase3 infra config: RSTW_PLL fuse Xfer Data for DIV0 register checked"), UVM_LOW)
         end
       join

       fork
         begin
            //Phase-4
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase4 ip bringup started"), UVM_LOW)
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_MB; cmd_opcode == FUSE_XFER;} );
            `uvm_do_with(d2d_hwrs_reset_cmd_bus_seq_i, {env_num == local::env_inst; d2d_rstw_type == RSTW_MB; cmd_opcode == GO_PWRUP;} );
         end
         begin //RSTW_MB Checks
             wait(d2d_reset_vif[env_inst].rstw_mb_rstw_ip_pwrgood_rst_b  === 1'b1); 
             wait(d2d_reset_vif[env_inst].rstw_mb_rstw_ip_side_rst_b     === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_mb_ser_fuse_xfer_done     === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_mb_rstw_ip_prim_rst_b     === 1'b1);
             wait(d2d_reset_vif[env_inst].rstw_mb_reset_exit_done        === 1'b1); //IP_ON
            `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase4 ip bringup: RSTW_MB IP_ON"), UVM_LOW)
         end
       join
        //Phase-5
        `uvm_info(get_full_name(), $sformatf("Cold_reset_MB: phase5 ip config need to start in pcode seq"), UVM_LOW)
     end // else if( ($test$plusargs("D2D_R2B_PHY")) || ($test$plusargs("D2D_B2B_PHY")) || ($test$plusargs("D2D_R2B_IFSPHY")))begin

     `uvm_info(get_full_name(), $sformatf("d2d_cold_reset_mb_hwrs_seq ended"), UVM_LOW)
   endtask: body

endclass: d2d_cold_reset_mb_hwrs_seq
