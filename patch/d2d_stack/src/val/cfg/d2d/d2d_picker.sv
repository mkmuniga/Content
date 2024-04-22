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


class d2d_picker extends d2d_mb_bfm_cfg_pkg::d2d_mb_bfm_d2d_cfg;

  `uvm_object_utils_begin(d2d_picker)
  `uvm_object_utils_end

  rand bit phy_enable; // Test pushing down from SoC systeminit to IP clipper
  rand int speed;      // Test pushing from IP systeminit (different knob name)
  rand int link_speed; // Test pushing from IP systeminit (same knob name)
  
  `clipper_knobs_begin(d2d_picker,D2D)
    `make_knob_int(phy_enable);
    `make_knob_int(speed);
    `make_knob_int(link_speed);
  `clipper_knobs_end

  function new(string name = "d2d_picker");
    super.new(name);
    add_vip_config();
  endfunction: new

endclass
