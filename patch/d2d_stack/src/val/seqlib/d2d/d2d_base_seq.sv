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

class d2d_base_sequence extends uvm_sequence;
   string m_name;
   //d2d_top_uvm_env top_env;
   // 1 d2d stim config obj for all sequences
//FIXME UV2 INTEG   d2d_stim_config d2d_stim_cfg;
   int env_inst;

   uvm_reg_block local_reg_block;
   uvm_reg_block sb2ucie_reg_block, isa_reg_block;
   uvm_reg_block rsrc_adapt_phy, rsrc_adapt_pll;
   uvm_reg_block uciedda0_reg_block, uciedda1_reg_block;
   uvm_reg_block ula0_reg_block, ula1_reg_block;
   uvm_reg_block ucie_phy_reg_block;
    
   
virtual d2d_reset_signal_if d2d_reset_vif[3:0]; //cbb hotfix
    
   `uvm_object_utils_begin(d2d_base_sequence)
   `uvm_object_utils_end
    string access_path= "sideband" ;
    uvm_status_e      status;

   // path can be FRONTDOOR or BACKDOOR
   string seq_reg_access_path="UVM_BACKDOOR";
   // Backdoor forces the value into register disregarding frontdoor effects
   bit backdoor_disable = 1;
 
   // Default access path for this seq. Legal space for a access_path should be mapped in space_accessPath_LUT
   // space_constaints constraints the legal spaces for a given access path
   //  access path   ---- Space constraints
   //  primary       ---- MEM, LT_MEM, IO, CFG
   //  sideband      ---- MSG (This includes all opcodes MEM-SB, IO-SB, CFG-SB, CR-SB)
   //  idi           ---- MEM, IO, CFG
   string space_constaints[string][$];
   extern function new(string name = "d2d_base_sequence");
   extern task pre_body();
   extern task body();
   extern virtual task d2d_read_reg(input uvm_reg r,output uvm_status_e status,output  uvm_reg_data_t rd_val, input string in_access_t="", input slu_ral_sai_t u_sai_index = '0, input bit pick_random_sai = 1'b1, input string reg_access_path="UVM_FRONTDOOR");
   extern virtual task d2d_write_reg(input uvm_reg r,output uvm_status_e status,input  uvm_reg_data_t wr_val, input string in_access_t="", input slu_ral_sai_t u_sai_index = '0, input bit pick_random_sai = 1'b1, input string reg_access_path="UVM_FRONTDOOR");
   extern function void get_d2d_reg_blocks();
   extern function uvm_reg get_d2d_register(input d2d_ip_reg_e ip_reg_sb, input string reg_name_s, input string phy_reg_sub_block_s="ucie_ophyreg_0");
endclass : d2d_base_sequence

function d2d_base_sequence::new(string name = "d2d_base_sequence");
  super.new(name);
   m_name = name;
   `uvm_info(get_type_name(), $sformatf("constructing d2d base seq for %s", m_name), UVM_DEBUG);
          // Populate the space_constraints array
        // THIS VALUES ARE JUST AN EXAMPLE. PLEASE CHANGE AS PER PROJECT NEEDS
   space_constaints["primary"] = {"MEM", "IO", "CFG", "LT_MEM"};
   space_constaints["sideband"] = {"MSG"};
   space_constaints["idi"] = {"MEM", "IO", "CFG"};
   if(!uvm_config_db#(virtual d2d_reset_signal_if)::get(null, "*", $sformatf("d2d_reset_vif[%0d]", 0), d2d_reset_vif[0]) ) begin
      `uvm_fatal(get_full_name(), $sformatf("Could not find d2d_reset_signal_if instance d2d_reset_vif[%0d]", 0))
   end
   if(!uvm_config_db#(virtual d2d_reset_signal_if)::get(null, "*", $sformatf("d2d_reset_vif[%0d]", 1), d2d_reset_vif[1]) ) begin //cbb hotfix
      `uvm_fatal(get_full_name(), $sformatf("Could not find d2d_reset_signal_if instance d2d_reset_vif[%0d]", 1))
   end
//cbb hotfix `ifdef D2D_B2B
   if(!uvm_config_db#(virtual d2d_reset_signal_if)::get(null, "*", $sformatf("d2d_reset_vif[%0d]", 2), d2d_reset_vif[2]) ) begin //cbb hotfix
      `uvm_fatal(get_full_name(), $sformatf("Could not find d2d_reset_signal_if instance d2d_reset_vif[%0d]", 2))
   end
   if(!uvm_config_db#(virtual d2d_reset_signal_if)::get(null, "*", $sformatf("d2d_reset_vif[%0d]", 3), d2d_reset_vif[3]) ) begin //cbb hotfix
      `uvm_fatal(get_full_name(), $sformatf("Could not find d2d_reset_signal_if instance d2d_reset_vif[%0d]", 3))
   end
// `endif
endfunction

task d2d_base_sequence::pre_body();
  super.pre_body();
  `uvm_info(get_type_name(), $sformatf("[%s] starting pre_body task:", m_name), UVM_DEBUG);
  get_d2d_reg_blocks();
endtask: pre_body

task d2d_base_sequence::body();
  `uvm_info(get_type_name(), $sformatf("[%s] starting body task", m_name), UVM_DEBUG);
endtask : body

task d2d_base_sequence::d2d_write_reg(input uvm_reg r,output uvm_status_e status, input  uvm_reg_data_t wr_val, input string in_access_t="", input slu_ral_sai_t u_sai_index = '0, input bit pick_random_sai = 1'b1, input string reg_access_path="UVM_FRONTDOOR");
  slu_reg_access_extension extension = new();
  slu_ral_sai_t sai_index;
  uvm_reg_map space_map;
//CBB TEMP EXCLUDE lnehama  string src_type = intc_iosf_sb_reg_stim_server_sim_pkg::get_src_type();

  if(in_access_t != "") access_path = in_access_t;
  //Step 1 : Pick a relevant map
  space_map = slu_ral_db::regs.pick_random_map(r, space_constaints[access_path]);

  //Step 2 : Pick a SAI index if register is SAI protected
  if(slu_ral_db::regs.get_sai_secure_status(r,UVM_WRITE)) begin
    `uvm_info(get_type_name(), $sformatf("Pick random sai bit = %d", pick_random_sai), UVM_MEDIUM);  
    if(pick_random_sai) begin
      sai_index = slu_ral_db::regs.pick_random_sai_index(r, UVM_WRITE);
      `uvm_info(get_type_name(), $sformatf("[write reg] sai index = %h", sai_index), UVM_MEDIUM);
    end
    else
      sai_index = u_sai_index;
    extension.set_sai_index(sai_index); // Sets SAI index
  end
  else begin
    sai_index = -1;
    extension.set_sai_index(sai_index);
  end

  //Step 3 : Populate any other information needed for this access into the extension object
  extension.set_wait_for_complete(1);
  extension.set_access_path(access_path);

  // Step 4 : Perform the register operation
  if(reg_access_path=="UVM_BACKDOOR" && backdoor_disable)
    r.poke(status, wr_val,, this, extension, .fname(`uvm_file) , .lineno(`uvm_line));
 else
//CBB TEMP EXCLUDE lnehama	slu_ral_db::write_reg(r, status, wr_val, UVM_FRONTDOOR, null, this,.sai_index(sai_index),.access_path(src_type));
	slu_ral_db::write_reg(r, status, wr_val, UVM_FRONTDOOR, space_map, this,.sai_index(sai_index),.access_path(""));
   
endtask: d2d_write_reg

// IP specific read function. Append IP name to function *_read_reg
task d2d_base_sequence::d2d_read_reg(input uvm_reg r,output uvm_status_e status,output  uvm_reg_data_t rd_val, input string in_access_t="", input slu_ral_sai_t u_sai_index = '0, input bit pick_random_sai = 1'b1, input string reg_access_path="UVM_FRONTDOOR");
  slu_reg_access_extension extension = new();
  slu_ral_sai_t sai_index;
  uvm_reg_map space_map;
//CBB TEMP EXCLUDE lnehama  string src_type = intc_iosf_sb_reg_stim_server_sim_pkg::get_src_type();

  if(in_access_t != "") access_path = in_access_t;

  //Step 1 : Pick a relevant map
  space_map = slu_ral_db::regs.pick_random_map(r, space_constaints[access_path]);

  //Step 2 : Pick a SAI index if register is SAI protected
  if(slu_ral_db::regs.get_sai_secure_status(r,UVM_READ)) begin
    if(pick_random_sai) begin
      sai_index = slu_ral_db::regs.pick_random_sai_index(r, UVM_READ);
      `uvm_info(get_type_name(), $sformatf("[read_reg] sai index = %h", sai_index), UVM_MEDIUM);
    end  
    else
      sai_index = u_sai_index;
    extension.set_sai_index(sai_index);  // Sets SAI index
  end
  else begin
    sai_index = -1;
    extension.set_sai_index(sai_index);
  end 

  //Step 3 : Populate any other information needed for this access into the extension object
  extension.set_wait_for_complete(1);
  extension.set_access_path(access_path);

  // Step 4 : Perform the register operation
  if(reg_access_path=="UVM_BACKDOOR" && backdoor_disable)
    r.peek(status, rd_val,, this, extension, .fname(`uvm_file) , .lineno(`uvm_line));
  else begin
	slu_ral_db::read_reg(r, status, rd_val, UVM_FRONTDOOR, space_map, this,.sai_index(sai_index),.access_path(""));
 //`uvm_info ("d2d_base_seq",$sformatf("accessing SB2UCIE register through  read "),UVM_NONE)
  end
endtask: d2d_read_reg

function uvm_reg d2d_base_sequence::get_d2d_register(input d2d_ip_reg_e ip_reg_sb, input string reg_name_s, input string phy_reg_sub_block_s="ucie_ophyreg_0");
  uvm_reg reg_name;

  case(ip_reg_sb)
    IOSFSB2UCIE_GPSB : begin reg_name = uvm_reg::m_get_reg_by_full_name({sb2ucie_reg_block.get_full_name(),".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {sb2ucie_reg_block.get_full_name(),".",reg_name_s}));
                       end
    ISA_D2D_GPSB     : begin reg_name = uvm_reg::m_get_reg_by_full_name({isa_reg_block.get_full_name(),".","isa_base_reg",".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {isa_reg_block.get_full_name(),".","isa_base_reg",".",reg_name_s}));
                       end
    ULA0_GPSB        : begin reg_name = uvm_reg::m_get_reg_by_full_name({ula0_reg_block.get_full_name(),".","ula",".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {ula0_reg_block.get_full_name(),".","ula",".",reg_name_s}));
                       end
    ULA1_GPSB        : begin reg_name = uvm_reg::m_get_reg_by_full_name({ula1_reg_block.get_full_name(),".","ula",".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {ula1_reg_block.get_full_name(),".","ula",".",reg_name_s}));
                       end
    UCIEDDA0_GPSB    : begin reg_name = uvm_reg::m_get_reg_by_full_name({uciedda0_reg_block.get_full_name(),".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {uciedda0_reg_block.get_full_name(),".",reg_name_s}));
                       end
    UCIEDDA1_GPSB    : begin reg_name = uvm_reg::m_get_reg_by_full_name({uciedda1_reg_block.get_full_name(),".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {uciedda0_reg_block.get_full_name(),".",reg_name_s}));
                       end
    UCIE0_PHY_GPSB   : begin reg_name = uvm_reg::m_get_reg_by_full_name({ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s});
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s}));
                       end
    UCIE1_PHY_GPSB   : begin reg_name = uvm_reg::m_get_reg_by_full_name({ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s});
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s}));
                       end
    UCIE2_PHY_GPSB   : begin reg_name = uvm_reg::m_get_reg_by_full_name({ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s});
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {ucie_phy_reg_block.get_full_name(),".",phy_reg_sub_block_s,".",reg_name_s}));
                       end
    RA_PHY_PMSB      : begin reg_name = uvm_reg::m_get_reg_by_full_name({rsrc_adapt_phy.get_full_name(),".","rsrc_adapt_reg",".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {rsrc_adapt_phy.get_full_name(),".","rsrc_adapt_reg",".",reg_name_s}));
                       end
    RA_PLL_PMSB      : begin reg_name = uvm_reg::m_get_reg_by_full_name({rsrc_adapt_pll.get_full_name(),".","rsrc_adapt_reg",".",reg_name_s});  
                             if (!reg_name) `uvm_error(get_full_name(),$sformatf("Could not find reg %s", {rsrc_adapt_pll.get_full_name(),".","rsrc_adapt_reg",".",reg_name_s}));
                       end
    default          : `uvm_error(get_full_name(),$sformatf("Could not find reg %s in d2d ip: %s ", reg_name_s, ip_reg_sb.name()) )
  endcase

  return(reg_name);
endfunction: get_d2d_register

function void d2d_base_sequence::get_d2d_reg_blocks();

  //Index for register blocks to access specific register instance  
  int sb2ucie_reg_block_index, isa_reg_block_index, rsrc_adapt_phy_reg_block_index, rsrc_adapt_pll_reg_block_index; 
  int uciedda0_reg_block_index, uciedda1_reg_block_index, ula0_reg_block_index, ula1_reg_block_index;
  int ucie_phy_reg_block_index; 

  case(env_inst)
    0: begin
         sb2ucie_reg_block_index        = `D2D_0_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_0_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_0_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_0_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_0_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_0_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_0_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_0_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_0_UCIE_PHY_REG_INDEX; 
       end
    1: begin
         sb2ucie_reg_block_index        = `D2D_1_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_1_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_1_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_1_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_1_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_1_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_1_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_1_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_1_UCIE_PHY_REG_INDEX; 
       end
    2: begin
         sb2ucie_reg_block_index        = `D2D_2_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_2_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_2_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_2_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_2_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_2_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_2_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_2_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_2_UCIE_PHY_REG_INDEX; 
       end
    3: begin
         sb2ucie_reg_block_index        = `D2D_3_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_3_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_3_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_3_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_3_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_3_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_3_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_3_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_3_UCIE_PHY_REG_INDEX; 
       end
    4: begin
         sb2ucie_reg_block_index        = `D2D_4_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_4_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_4_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_4_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_4_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_4_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_4_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_4_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_4_UCIE_PHY_REG_INDEX; 
       end
    5: begin
         sb2ucie_reg_block_index        = `D2D_5_SB2UCIE_REG_INDEX;   isa_reg_block_index            = `D2D_5_ISA_REG_INDEX;        
         ula0_reg_block_index           = `D2D_5_ULA0_REG_INDEX;      ula1_reg_block_index           = `D2D_5_ULA1_REG_INDEX;        
         uciedda0_reg_block_index       = `D2D_5_DDA0_REG_INDEX;      uciedda1_reg_block_index       = `D2D_5_DDA1_REG_INDEX;        
         rsrc_adapt_phy_reg_block_index = `D2D_5_RSRC_PHY_REG_INDEX;  rsrc_adapt_pll_reg_block_index = `D2D_5_RSRC_PLL_REG_INDEX; 
         ucie_phy_reg_block_index       = `D2D_5_UCIE_PHY_REG_INDEX; 
       end
    default:  `uvm_fatal(get_name(), $sformatf("d2d env_inst=%0d is out of (0 to 5)", env_inst) )
   endcase

  `uvm_info(get_full_name(), $sformatf("env_inst=%0d d2d IPs reg_block index picked from imh_reg_block: \n\
         sb2ucie_reg_block_index        = %0d \n\
         isa_reg_block_index            = %0d \n\
         rsrc_adapt_phy_reg_block_index = %0d \n\
         rsrc_adapt_pll_reg_block_index = %0d \n\
         uciedda0_reg_block_index       = %0d \n\
         uciedda1_reg_block_index       = %0d \n\
         ula0_reg_block_index           = %0d \n\
         ula1_reg_block_index           = %0d \n\
         ucie_phy_reg_block_index       = %0d ",
   env_inst, sb2ucie_reg_block_index, isa_reg_block_index, rsrc_adapt_phy_reg_block_index, rsrc_adapt_pll_reg_block_index, 
   uciedda0_reg_block_index, uciedda1_reg_block_index, ula0_reg_block_index, ula1_reg_block_index,ucie_phy_reg_block_index), UVM_LOW)           

  if(local_reg_block == null) begin
    $cast(local_reg_block,slu_ral_db::get_regmodel());
    `uvm_info(get_type_name(), $sformatf("local_reg_block.get_full_name(): %s", local_reg_block.get_full_name()), UVM_LOW);
  end

  // Find the relevant block underneath the local_reg_block
  if(!($cast(sb2ucie_reg_block, uvm_reg_block::find_block($sformatf("iosfsb2ucie[%0d].iosfsb2ucie", sb2ucie_reg_block_index), local_reg_block))) || sb2ucie_reg_block==null)
    `uvm_error(get_name(), $sformatf("Could not find block [iosfsb2ucie[%0d]] within root block=[%s]", sb2ucie_reg_block_index, local_reg_block.get_full_name()));

  if(!($cast(isa_reg_block, uvm_reg_block::find_block($sformatf("isa[%0d]", isa_reg_block_index), local_reg_block))) || isa_reg_block==null)
   `uvm_error(get_name(), $sformatf("Could not find block [isa[%0d]] within root block=[%s]", isa_reg_block_index, local_reg_block.get_full_name()));
  
  if(!($cast(uciedda0_reg_block, uvm_reg_block::find_block($sformatf("uciedda_d2d[%0d]", uciedda0_reg_block_index), local_reg_block))) || uciedda0_reg_block==null)
    `uvm_error(get_name(), $sformatf("Could not find block [uciedda_d2d[%0d]] within root block=[%s]", uciedda0_reg_block_index, local_reg_block.get_full_name()));

  if(!($cast(uciedda1_reg_block, uvm_reg_block::find_block($sformatf("uciedda_d2d[%0d]", uciedda1_reg_block_index), local_reg_block))) || uciedda1_reg_block==null)
    `uvm_error(get_name(), $sformatf("Could not find block [uciedda_d2d[%0d]] within root block=[%s]", uciedda1_reg_block_index, local_reg_block.get_full_name()));
  
  if(!($cast(ula0_reg_block, uvm_reg_block::find_block($sformatf("ula_d2d[%0d]", ula0_reg_block_index), local_reg_block))) || ula0_reg_block==null)
    `uvm_error(get_name(), $sformatf("Could not find block [ula_d2d[%0d]] within root block=[%s]", ula0_reg_block_index, local_reg_block.get_full_name()));

  if(!($cast(ula1_reg_block, uvm_reg_block::find_block($sformatf("ula_d2d[%0d]", ula1_reg_block_index), local_reg_block))) || ula1_reg_block==null)
    `uvm_error(get_name(), $sformatf("Could not find block [ula_d2d[%0d]] within root block=[%s]", ula1_reg_block_index, local_reg_block.get_full_name()));
  
  if(!($cast(rsrc_adapt_phy, uvm_reg_block::find_block($sformatf("rsrc_adapt[%0d]", rsrc_adapt_phy_reg_block_index), local_reg_block))) || rsrc_adapt_phy==null)
   `uvm_error(get_name(), $sformatf("Could not find block [rsrc_adapt[%0d]] within root block=[%s]", rsrc_adapt_phy_reg_block_index, local_reg_block.get_full_name()));
  
  if(!($cast(rsrc_adapt_pll, uvm_reg_block::find_block($sformatf("rsrc_adapt[%0d]", rsrc_adapt_pll_reg_block_index), local_reg_block))) || rsrc_adapt_pll==null)
   `uvm_error(get_name(), $sformatf("Could not find block [rsrc_adapt[%0d]] within root block=[%s]", rsrc_adapt_pll_reg_block_index, local_reg_block.get_full_name()));
  
  `ifdef D2D_TB
       `ifdef D2D0_VARIANT
            if(!($cast(ucie_phy_reg_block, uvm_reg_block::find_block($sformatf("ucie_ophy_m6_p76"), local_reg_block))) || ucie_phy_reg_block==null)
             `uvm_error(get_name(), $sformatf("Could not find block [ucie_ophy_m6_p76] within root block=[%s] %s ", local_reg_block.get_full_name(),ucie_phy_reg_block.get_name() ));//cbb hotfix
       `else
            if(!($cast(ucie_phy_reg_block, uvm_reg_block::find_block($sformatf("ucie_ophy_m6_p76_alt[%0d]", ucie_phy_reg_block_index), local_reg_block))))
             `uvm_error(get_name(), $sformatf("Could not find block [ucie_ophy_m6_p76_alt] within root block=[%s] %s ", local_reg_block.get_full_name(),ucie_phy_reg_block.get_name() ));//cbb hotfix
       `endif
  `else //IMH level reuse for 6 instances of D2D stacks.
       if(env_inst == 4) begin //D2D_4 instance is based on D2D0 variant. 
          if(!($cast(ucie_phy_reg_block, uvm_reg_block::find_block($sformatf("ucie_ophy_m6_p76"), local_reg_block))) || ucie_phy_reg_block==null)
           `uvm_error(get_name(), $sformatf("Could not find block [ucie_ophy_m6_p76] within root block=[%s] %s ", local_reg_block.get_full_name(),ucie_phy_reg_block.get_name() ));//cbb hotfix
       end
       else begin //D2D_0,1,2,3 and 5 instances are based on D2D1 and D2D2 Variants.
          if(!($cast(ucie_phy_reg_block, uvm_reg_block::find_block($sformatf("ucie_ophy_m6_p76_alt[%0d]", ucie_phy_reg_block_index), local_reg_block))))
           `uvm_error(get_name(), $sformatf("Could not find block [ucie_ophy_m6_p76_alt] within root block=[%s] %s ", local_reg_block.get_full_name(),ucie_phy_reg_block.get_name() ));//cbb hotfix
       end 
   `endif

  `uvm_info(get_type_name(), $sformatf("local_reg_block type name: %s", local_reg_block.get_type_name()), UVM_LOW);

endfunction: get_d2d_reg_blocks



