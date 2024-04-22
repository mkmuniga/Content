//rqutten - add macro define


`define FORCE(hsd, signal, value) \
begin \
    force signal = value; \
end


`ifdef AUPI_UFI

//UCIe define
`ifndef AUCIE_NUM_MODULES
  `define AUCIE_NUM_MODULES 1
`endif

  
    //can't connect to mb clk/rst for now since MB IP is not out of reset
    //aufi_a2f_intf a2f_i

    //can't connect to mb clk/rst for now since MB IP is not out of reset
    //aufi_a2f_intf a2f_if[2](.clk(uclk_io_adop_d2d_clkout), .rst(rstw_mb_rstw_ip_prim_rst_b));
    //aufi_f2a_intf f2a_if[2](.clk(uclk_io_adop_d2d_clkout), .rst(rstw_mb_rstw_ip_prim_rst_b));

    aufi_a2f_intf a2f_if[2](.clk(uclk_mem_in), .rst(~iosfsbpa_iosfsbpa_rst_b));
    aufi_f2a_intf f2a_if[2](.clk(uclk_mem_in), .rst(~iosfsbpa_iosfsbpa_rst_b));
    
    //Instantiate MB and SB interfaces
    aucie_main_intf main_if1[`AUCIE_NUM_MODULES]();
    aucie_main_intf main_if2[`AUCIE_NUM_MODULES]();
    aucie_sb_intf sb_if1[`AUCIE_NUM_MODULES]();
    aucie_sb_intf sb_if2[`AUCIE_NUM_MODULES]();

    //TODO AUFI_LINK_MUL, a2f_if[AUFI_LINK_MUL] and f2a_if[AUFI_LINK_NUM] get it from uvm_config_db 
    //TODO initial begin
    //TODO     uvm_config_db#(int)::set(uvm_root::get(), env_str, "aufi_link_multiple", AUFI_LINK_MUL);
    //TODO end
    //TODO for (genvar i = 0; i < AUFI_LINK_NUM; i++) begin
        initial begin
          string env_path;
          string rdi_inst;
          env_path = $sformatf("*");
          //env_path = $sformatf("*.d2d_uxi_ufi_bfm_env%0d.*",ENV_INST);
      	  uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), env_path, $sformatf("a2f_if[%0d]", 0+(ENV_INST*2)), a2f_if[0]);
          uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), env_path, $sformatf("f2a_if[%0d]", 0+(ENV_INST*2)), f2a_if[0]);
      	  uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), env_path, $sformatf("a2f_if[%0d]", 1+(ENV_INST*2)), a2f_if[1]);
          uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), env_path, $sformatf("f2a_if[%0d]", 1+(ENV_INST*2)), f2a_if[1]);
          uvm_config_db #(int)::set(uvm_root::get(), "*", "port_mul", 2);//needed so that BFM will instantiate 4 a2f/f2a_if 
          uvm_config_db #(int)::set(uvm_root::get(), "*", "port_offset", 2);//needed so that BFM will instantiate 4 a2f/f2a_if 
          

  
          //required to set even if not being used
          uvm_config_db#(int)::set(uvm_root::get(), "*", "num_modules", `AUCIE_NUM_MODULES);
          uvm_config_db#(virtual aucie_main_intf)::set(uvm_root::get(), "*", $sformatf("main_if1[0]"), main_if1[0]);
          uvm_config_db#(virtual aucie_main_intf)::set(uvm_root::get(), "*", $sformatf("main_if2[0]"), main_if2[0]);
          uvm_config_db#(virtual aucie_sb_intf)::set(uvm_root::get(), "*", $sformatf("sb_if1[0]"), sb_if1[0]);
          uvm_config_db#(virtual aucie_sb_intf)::set(uvm_root::get(), "*", $sformatf("sb_if2[0]"), sb_if2[0]);

          if ($test$plusargs("D2D_B2B_RDI")) begin
             //get in d2d_top_uvm_env to connect b2b using Avery box
             env_path = $sformatf("rdi_if%0d", ENV_INST*2+1);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), "*", env_path, rdi_if1);
             env_path = $sformatf("rdi_if%0d", ENV_INST*2+2);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), "*", env_path, rdi_if2);
          end
          else if (($test$plusargs("D2D_R2B_RDI")||($test$plusargs("D2D_R2B_IFSPHY"))) && (ENV_INST == 0))begin

             // RTL + BFM for 2 RDI Ports (ucie_env0 and ucie_env1)
             env_path = $sformatf("rdi_if%0d", 1);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), $sformatf("ucie_env%0d",ENV_INST), env_path, rdi_if1);
             env_path = $sformatf("rdi_if%0d", 1);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), $sformatf("ucie_env%0d",ENV_INST+1), env_path, rdi_if2);
             env_path = $sformatf("rdi_if%0d", 2);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), $sformatf("ucie_env%0d",ENV_INST), env_path, rdi_if3);
             env_path = $sformatf("rdi_if%0d", 2);
    	     uvm_config_db#(virtual aucie_rdi_intf)::set(uvm_root::get(), $sformatf("ucie_env%0d",ENV_INST+1), env_path, rdi_if4);
          end
        end
    initial begin
      if ($test$plusargs("D2D_B2B_RDI")) begin
          `RDI_CONN_RTL_2_BFM(pard2d1uladda0,uciedda_d2d_0, rdi_if1);
          `RDI_CONN_RTL_2_BFM(pard2d1uladda1,uciedda_d2d_1,  rdi_if2);
       //rdi_if3 and rdi_if4 are the interface to UCIE BFM side and needs lclk
       force rdi_if1.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if2.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if3.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if4.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
      end
      else if ($test$plusargs("D2D_R2B_RDI")) begin
          `RDI_CONN_RTL_2_BFM(pard2d1uladda0,uciedda_d2d_0, rdi_if1);
          `RDI_CONN_RTL_2_BFM(pard2d1uladda1,uciedda_d2d_1, rdi_if2);
       //rdi_if3 and rdi_if4 are the interface to UCIE BFM side and needs lclk
       force rdi_if1.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if2.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if3.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
       force rdi_if4.lclk = uclk_mem_in & pard2d1misc.rstw_mb_rstw_ip_prim_rst_b;
      end
      else if ($test$plusargs("D2D_R2B_PHY")) begin
       // `MB_PHY_CONN_RTL_2_BFM(0, main_if1);
       // `MB_PHY_CONN_RTL_2_BFM(1, main_if2);
       // `SB_PHY_CONN_RTL_2_BFM(0, sb_if1);
       // `SB_PHY_CONN_RTL_2_BFM(1, sb_if2);
      end
      else if ($test$plusargs("D2D_R2B_IFSPHY")) begin
       force rdi_if1.lclk = uclk_mem_in & hwrs_top_early_boot_pwrgood_rst_b;
       force rdi_if2.lclk = uclk_mem_in & hwrs_top_early_boot_pwrgood_rst_b;
       force rdi_if3.lclk = uclk_mem_in & hwrs_top_early_boot_pwrgood_rst_b;
       force rdi_if4.lclk = uclk_mem_in & hwrs_top_early_boot_pwrgood_rst_b;
       //`RDI_CONN_IFS_2_BFM(0, rdi_if1);
       //`RDI_CONN_IFS_2_BFM(1, rdi_if2);
      end
    end

if (d2d_active_passive == uvm_pkg::UVM_ACTIVE) begin

  //-------------------------------------------------------------------------------------------------------// 
  // Agent to Fabric UFI-0 Interface Global, REQ, DATA and RSP Physical Channel connections.
  //-------------------------------------------------------------------------------------------------------// 
     initial begin
       if (ENV_INST == 0)begin
          `UFI_CONN_RTL_A2F_2_BFM_F2A(d2d_ula_d2d_0,f2a_if[0]) 
          `UFI_CONN_BFM_A2F_2_RTL_F2A(d2d_ula_d2d_0,a2f_if[0])
       end
       else if($test$plusargs("D2D_B2B_RDI")|| ($test$plusargs("D2D_B2B_PHY"))) begin
          `UFI_CONN_RTL_A2F_2_BFM_A2F(d2d_ula_d2d_0,a2f_if[0]) 
          `UFI_CONN_BFM_F2A_2_RTL_F2A(d2d_ula_d2d_0,f2a_if[0])
       end
     end
  //-------------------------------------------------------------------------------------------------------// 
  // Agent to Farbric UFI-1 Interface Global, REQ, DATA and RSP Physical Channel connections.
  //-------------------------------------------------------------------------------------------------------// 
     initial begin
       if (ENV_INST == 0)begin
          `UFI_CONN_RTL_A2F_2_BFM_F2A(d2d_ula_d2d_1,f2a_if[1]) 
          `UFI_CONN_BFM_A2F_2_RTL_F2A(d2d_ula_d2d_1,a2f_if[1])
       end
       else if($test$plusargs("D2D_B2B_RDI")|| ($test$plusargs("D2D_B2B_PHY"))) begin
          `UFI_CONN_RTL_A2F_2_BFM_A2F(d2d_ula_d2d_1,a2f_if[1]) 
          `UFI_CONN_BFM_F2A_2_RTL_F2A(d2d_ula_d2d_1,f2a_if[1])
       end
     end
end //d2d_active_passive == uvm_pkg::UVM_ACTIVE
else begin //d2d_active_passive == uvm_pkg::UVM_PASSIVE
//TODO
end

`endif







