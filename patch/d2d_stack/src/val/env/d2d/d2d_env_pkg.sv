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
package d2d_env_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"
   import iosfsbm_cm::*;
   import iosfsbm_fbrc::*;

  import d2d_cfg_pkg::*;
  import reset_cmd_agent_pkg::*;
  import clk_env_pkg::*;
  
    //Import Synopys UVM pkg
  import svt_uvm_pkg::*;
  
  //Import Synopsys amba pkg for APB interface
  import svt_amba_uvm_pkg::*; //cbb hotfix

  import iosfsb2ucie_env_pkg::*;
  
  import ula_uvm_env_pkg::*;
  import uciedda_uvm_env_pkg::*;

  //DFT
//FIXME lnehama - cbb integ hotfix  import dft_common_val_env_pkg::*;
  import sla_pkg::*;
 `include "slu_macros.svh"
 
  `include "d2d_env_sequencer.sv"
   
  `include "d2d_env.sv"
  // Top-level env with non reusable components 
  //`include "d2d_top_uvm_env.sv"
endpackage
