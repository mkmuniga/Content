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


package d2d_cfg_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  import clipper_pkg::*;
  `include "clipper_macros.svh"
    //Import Synopys UVM pkg
  import svt_uvm_pkg::*;
  
  //Import Synopsys amba pkg for APB interface
  import svt_amba_uvm_pkg::*; //svt_apb_uvm_pkg::*; cbb hotfix uv2 integ

  // Object files
  `include "d2d_cfg.sv"

  // Programmer files
  `include "d2d_cfg_prog.sv"

  // Domain config
  `include "d2d_cfg_builder.sv"
  
endpackage: d2d_cfg_pkg
