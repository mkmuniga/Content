//------------------------------------------------------------------------------
//
//  INTEL CONFIDENTIAL
//
//  Copyright 2022 Intel Corporation All Rights Reserved.
//
//  The source code contained or described herein and all documents related
//  to the source code ("Material") are owned by Intel Corporation or its
//  suppliers or licensors. Title to the Material remains with Intel
//  Corporation or its suppliers and licensors. The Material contains trade
//  secrets and proprietary and confidential information of Intel or its
//  suppliers and licensors. The Material is protected by worldwide copyright
//  and trade secret laws and treaty provisions. No part of the Material may
//  be used, copied, reproduced, modified, published, uploaded, posted,
//  transmitted, distributed, or disclosed in any way without Intel's prior
//  express written permission.
//
//  No license under any patent, copyright, trade secret or other intellectual
//  property right is granted to or conferred upon you by disclosure or
//  delivery of the Materials, either expressly, by implication, inducement,
//  estoppel or otherwise. Any license under such intellectual property rights
//  must be express and approved by Intel in writing.
//
//------------------------------------------------------------------------------
//
//    FILENAME  : 
//    PROJECT   : UCIE IP
//    CREATED   : 01.10.2022
//    MODIFIED  : 02.18.2022
//    AUTHOR    : Ashfak Nazim <mohamed.ashfak.mohamed.nazim@intel.com>
//    CONTACT   : Ashfak Nazim <mohamed.ashfak.mohamed.nazim@intel.com>
//    VERSION   : 
//-----------------------------------------------------------------------------
//    FUNCTIONAL DESCRIPTION:
//    UCIE Aphy dline/glbdca/clk dist.
//-----------------------------------------------------------------------------
//    MODIFICATION HISTORY:
//    
//-----------------------------------------------------------------------------

`ifndef UCIEGEN1TX_TXTERMCBB_WRAP_SV
`define UCIEGEN1TX_TXTERMCBB_WRAP_SV

module uciegen1tx_txtermcbb_wrap
(
  `ifndef INTEL_NO_PWR_PINS
    input logic vccio,
    input logic vssx,
  `endif
  `ifdef INTEL_INST_ON
    `ifndef UCIE_MSV
      input logic [7:0]  i_freq_ratio,
      input logic [1:0]  i_process_corner,
      input logic [10:0] i_vol_ratio,
      input logic        i_fscan_mode,
      input logic        is_data_cbb,
      input logic        is_clk_cbb,
//      input real         skew_dcd_seed,
      input reg          skew_dcd_seed,
    `endif
  `endif
    output logic  odigobs_out,
    output logic  onelbdata_async,
    output logic  onelbdata_even,
    output logic  onelbdata_odd,
    output logic  otxanaspare,

    inout  wire   xxpad_tx,

    input  logic  iasync_ckx8,
    input  logic  iasyncdata,
    input  logic  iasyncmode,
    input  logic  iburnin_en,
    input  logic  ick_train,
    input  logic  ickcal,
    input  logic  icktx,
    input  logic  icktx_div2,
    input  logic  idcs_data_invert,
    input  logic  idcs_stop_counter,
    input  logic  idfxobs_en,
    input  logic  idn_static,
    input  logic  igatecktrain,
    input  logic  inelb_en,
    input  logic  ipadtristate_en,
    input  logic  irstb_cktx,
    input  logic  irstb_counter,
    input  logic  irstb_nelb_ckbtx,
    input  logic  irstb_sampler,
    input  logic  irstb_trainnelb,
    input  logic  irstb_x8,
    input  logic  iup_static,
    input  logic  sideband_data_sel,

    output logic [3:0]  ospare_dcs,
    output logic [4:0]  ocounter,
    output logic [4:0]  otxdigspare,

    input  logic [14:0] ilowpower_eq_en,
    input  logic [84:0] ithermocode_n,
    input  logic [1:0]  idv_n,
    input  logic [3:0]  idata2afe,
    input  logic [2:0]  idigobs_sel,
    input  logic [51:0] idn_therm,
    input  logic [7:0]  ispare_dcs,
    input  logic [15:0] ieq_en,
    input  logic [9:0]  itxanaspare,
    input  logic [1:0]  idv_p,
    input  logic [9:0]  itxdigspare,
    input  logic [51:0] iup_therm,
    input  logic [84:0] ithermocode_p
    );
   

`ifdef INTEL_SIMONLY
  timeunit 1ps ;
  timeprecision 1ps ;
`endif

logic [84:0] ithermocode_p_inst;
logic [84:0] ithermocode_n_inst;
logic [51:0] iup_therm_inst;
logic [51:0] idn_therm_inst;
logic        idcs_data_invert_inst;
logic [2:1]  itxdigspare_inst;
logic        irstb_counter_inst;
logic        irstb_sampler_inst;

/*AUTOLOGIC*/

`ifdef IP78X_BMODS
   `include "ip78x_delay_params.vh"
 `else
    `include "ip76x_delay_params.vh"
`endif

/*------------------------------------------------------------------------------
--  Instrumentation code
------------------------------------------------------------------------------*/
     logic w_icktx ;
     logic w_icktx_div2;
`ifdef INTEL_INST_ON
    `ifndef INTEL_EMULATION
        `ifndef UCIE_MSV
           bit dcc_dist = 0 ;
           bit dist_low_phase = 0 ;
           real skew;
           real jitter_del_rising, jitter_del_falling;
           real jitter_total_rising, jitter_total_falling;
           bit use_abs_jit =1;
           bit use_percent_jit =0;
           integer skew_delay = 0;
           bit jit_margin_flag = 0;
           reg clk_delay_jitter;
           integer lane2lane_small_skew = 5;
           integer lane_skew;
           integer ucie_tx_data_randskew_range = 0;
           integer ucie_tx_clk_randskew_range = 0;
           class RandClass;
              rand integer randVar;
           endclass
          
           RandClass myRand_rising;
           RandClass myRand_falling;
           RandClass rand_seed;
           
           integer ABS_JIT = 0 ;
           integer ABS_SKEW  = 0;
           integer PERCENTAGE_SIGMA = 0;
           integer PERCENTAGE_SKEW = 0;
           integer JIT_MARGIN = 5;
           
           
           initial begin
              myRand_rising = new();
              myRand_falling = new();
              rand_seed = new();
         
              if(is_data_cbb == 1) begin
                 if ( $test$plusargs("TX_RAND_DATA_DCD")) begin
                     dcc_dist = 1 ; 
                     `ifndef UCIE_XCLM
	                $srandom($urandom() + skew_dcd_seed);
                     `endif
                     dist_low_phase = $urandom() ;
                 end else if ( $test$plusargs("TX_DATA_DCD_M50")) begin
                     dcc_dist = 1 ; 
                     dist_low_phase = 1 ;
                 end else if ( $test$plusargs("TX_DATA_DCD_L50")) begin
                     dcc_dist = 1 ; 
                     dist_low_phase = 0 ;
                 end  
	         if ($test$plusargs("ucie_tx_data_skew")) begin
                     $value$plusargs("ucie_tx_data_skew=%0d", ABS_SKEW);
                     if ( $value$plusargs("LANE2LANE_SMALL_SKEW=%0d", lane2lane_small_skew )) begin
                        `ifndef UCIE_XCLM
		           $srandom(skew_dcd_seed);
                        `endif   
                         lane_skew = $urandom_range(ABS_SKEW+lane2lane_small_skew, ABS_SKEW-lane2lane_small_skew);
                         ABS_SKEW = lane_skew;
                     end
                    // $display("%m Tx data abs skew =%0d, lane2lane_small_skew=%0d", ABS_SKEW, lane2lane_small_skew);
                 end else if ($test$plusargs("ucie_tx_data_randskew_range")) begin
                     $value$plusargs("ucie_tx_data_randskew_range=%0d", ucie_tx_data_randskew_range );
                     `ifndef UCIE_XCLM
		        $srandom($urandom() + skew_dcd_seed);
                     `endif   
                     ABS_SKEW = $urandom_range(ucie_tx_data_randskew_range,0);
                     //$display("%m Tx data abs skew = %0d, rand_range = %0d", ABS_SKEW,ucie_tx_data_randskew_range);
                 end
              end //is_data_cbb

              if(is_clk_cbb == 1) begin
                 if ( $test$plusargs("TX_RAND_CLK_DCD")) begin
                     dcc_dist = 1 ; 
                     `ifndef UCIE_XCLM
	                $srandom($urandom() + skew_dcd_seed);
                     `endif
                     dist_low_phase = $urandom() ;
                 end else if ( $test$plusargs("TX_CLK_DCD_M50")) begin
                     dcc_dist = 1 ; 
                     dist_low_phase = 1 ;
                 end else if ( $test$plusargs("TX_CLK_DCD_L50")) begin
                     dcc_dist = 1 ; 
                     dist_low_phase = 0 ;
                 end  
	         if ($test$plusargs("ucie_tx_clk_skew")) begin
                     $value$plusargs("ucie_tx_clk_skew=%0d", ABS_SKEW);
                     if ( $value$plusargs("LANE2LANE_SMALL_SKEW=%0d", lane2lane_small_skew )) begin
                         `ifndef UCIE_XCLM
		            $srandom(skew_dcd_seed);
                         `endif
                         lane_skew = $urandom_range(ABS_SKEW+lane2lane_small_skew, ABS_SKEW-lane2lane_small_skew);
                         ABS_SKEW = lane_skew;
                     end
                    // $display("%m Tx clk abs skew =%0d, lane2lane_small_skew=%0d", ABS_SKEW, lane2lane_small_skew);
                 end else if ($test$plusargs("ucie_tx_clk_randskew_range")) begin
                     $value$plusargs("ucie_tx_clk_randskew_range=%0d", ucie_tx_clk_randskew_range );
                     `ifndef UCIE_XCLM
		        $srandom($urandom() + skew_dcd_seed);
                     `endif
                     ABS_SKEW = $urandom_range(ucie_tx_clk_randskew_range,0);
                     //$display("%m Tx clk abs skew = %0d, rand_range = %0d", ABS_SKEW,ucie_tx_clk_randskew_range);
                 end
              end //is_clk_cbb

            end //initial block-end

           always_ff @(posedge icktx or ABS_SKEW ) begin
               if (use_abs_jit) begin
                 if ( jit_margin_flag == 0 ) begin
                    skew = ABS_SKEW;
                 end else begin
                    rand_seed.randomize();
                    skew = $dist_uniform( rand_seed.randVar, ABS_SKEW-JIT_MARGIN, ABS_SKEW+JIT_MARGIN );
                    $display("%m SKEW DATA: ABS_SKEW = %0d, skew= %0d jit_margin_flag= %0d JIT_MARGIN= %0d", ABS_SKEW, skew, jit_margin_flag, JIT_MARGIN );
                 end
                 if(myRand_rising == null)
                   myRand_rising = new;
                 if(myRand_falling == null)
                   myRand_falling = new;
                 myRand_rising.randomize();
                 myRand_falling.randomize();
                 jitter_del_rising = $dist_normal(myRand_rising.randVar,0,ABS_JIT*100/3) / 100.0 * 1ps; //Random Jitter -- Gaussian Distribuion
                 jitter_del_falling = $dist_normal(myRand_falling.randVar,0,ABS_JIT*100/3) / 100.0 * 1ps; //Random Jitter -- Gaussian Distribuion
                 if(jitter_del_rising > ABS_JIT)
                   jitter_del_rising = ABS_JIT;
                 else if(jitter_del_rising < (-ABS_JIT))
                   jitter_del_rising = -ABS_JIT;
                 if(jitter_del_falling > ABS_JIT)
                   jitter_del_falling = ABS_JIT;
                 else if(jitter_del_falling < (-ABS_JIT))
                   jitter_del_falling = -ABS_JIT;
               end 
           
               if (jitter_del_rising < 0 ) begin
                 jitter_del_rising = jitter_del_rising - (2*jitter_del_rising); 
               end
               if (jitter_del_falling < 0 ) begin
                 jitter_del_falling = jitter_del_falling - (2*jitter_del_falling); 
               end
           
               jitter_total_rising  = skew + jitter_del_rising;
               jitter_total_falling = skew + jitter_del_falling;
           end //always_ff

           always @(posedge icktx) begin 
             clk_delay_jitter <= #(jitter_total_rising) icktx;
           end
             
           always @(negedge icktx) begin 
             clk_delay_jitter <= #(jitter_total_falling) icktx;
           end
           
           always @(posedge w_icktx or negedge iup_static) begin
             if(iup_static == 0) begin
                w_icktx_div2 <= 0;
             end else begin
                w_icktx_div2 <= ~w_icktx_div2;	
             end
           end  
	   
           assign w_icktx =   dcc_dist  ?  ( dist_low_phase ?   ( clk_delay_jitter | icktx ) : (clk_delay_jitter & icktx ) ) : icktx ;
           //assign wx_icktx_div2 = ($test$plusargs("TXCBB_DCD") && is_data_cbb) ?  w_icktx_div2    :icktx_div2;
        `endif 
    `else
       assign w_icktx = icktx ;
    `endif
`else
       assign w_icktx = icktx ;
`endif

`ifdef IP78X_BMODS
      ip78xuciegen1tx_txtermcbb      
  `else
      ip76xuciegen1tx_txtermcbb      
  `endif
  i_txcbb
      (
  `ifndef INTEL_NO_PWR_PINS
  .vccio   (vccio), 
  .vssx    (vssx),
  `endif
  `ifdef INTEL_INST_ON
    `ifndef UCIE_MSV
      .i_freq_ratio     (i_freq_ratio), 
      .i_process_corner (i_process_corner), 
      .i_vol_ratio      (i_vol_ratio),
      .i_fscan_mode     (i_fscan_mode),
    `endif
  `endif
	.odigobs_out      (odigobs_out),
	.onelbdata_async  (onelbdata_async),
	.onelbdata_even   (onelbdata_even),
	.onelbdata_odd    (onelbdata_odd),
	.otxanaspare      (otxanaspare),
    .xxpad_tx         (xxpad_tx),
	.iasync_ckx8      (iasync_ckx8),
	.iasyncdata       (iasyncdata),
	.iasyncmode       (iasyncmode),
	.iburnin_en       (iburnin_en),
	.ick_train        (ick_train),
	.ickcal           (ickcal),
  `ifdef UCIE_MSV
	.icktx            (icktx),
	.icktx_div2       (icktx_div2),
  `else
	.icktx            (w_icktx),
	.icktx_div2       (icktx_div2),
  `endif
	.idcs_data_invert (idcs_data_invert_inst),
	.idcs_stop_counter(idcs_stop_counter),
	.idfxobs_en       (idfxobs_en),
	.idn_static       (idn_static),
	.igatecktrain     (igatecktrain),
	.inelb_en         (inelb_en),
	.ipadtristate_en  (ipadtristate_en),
	.irstb_cktx       (irstb_cktx),
	.irstb_counter    (irstb_counter_inst),
	.irstb_nelb_ckbtx (irstb_nelb_ckbtx),
	.irstb_sampler    (irstb_sampler_inst),
	.irstb_trainnelb  (irstb_trainnelb),
	.irstb_x8         (irstb_x8),
	.iup_static       (iup_static),
	.sideband_data_sel(sideband_data_sel),
	.ospare_dcs       (ospare_dcs),
	.ocounter         (ocounter),
	.otxdigspare      (otxdigspare),
	.ilowpower_eq_en  (ilowpower_eq_en),
	.ithermocode_n    (ithermocode_n_inst),
	.idv_n            (idv_n),
	.idata2afe        (idata2afe),
	.idigobs_sel      (idigobs_sel),
	.idn_therm        (idn_therm_inst),
	.ispare_dcs       (ispare_dcs),
	.ieq_en           (ieq_en),
	.itxanaspare      (itxanaspare),
	.idv_p            (idv_p),
	.itxdigspare      ({itxdigspare[9:3],itxdigspare_inst[2:1],itxdigspare[0]}),
	.iup_therm        (iup_therm_inst),
	.ithermocode_p    (ithermocode_p_inst)
);

  `ifdef IP78X_BMODS
      ip78xuciegen1tx_txtermesdcbb 
  `else
      ip76xuciegen1tx_txtermesdcbb 
  `endif
  i_uciegen1tx_txtermesdcbb
( `ifndef INTEL_NO_PWR_PINS
  .vccio   (vccio),
  .vssx    (vssx),
  `endif
  `ifdef INTEL_INST_ON
    `ifndef UCIE_MSV
      .i_freq_ratio     (i_freq_ratio),
      .i_process_corner (i_process_corner),
      .i_vol_ratio      (i_vol_ratio),
    `endif
  `endif
  .xxpad_txafe (xxpad_tx)
);

//Below CBB interfaces are not timed in SD, SD is allowed to add up to 1ns buffer for these paths.
//Model interface delay in non GLS to ensure nothing break.
`ifdef INTEL_SIMONLY
    `ifndef UCIE_GLS
    
        `ifdef IP78X_BMODS
            import ip78xuciegen1tx_txcbb_pkg::*;
        `else
            import ip76xuciegen1tx_txcbb_pkg::*;
        `endif
        
        realtime intf_delay;
        
        assign intf_delay = uciegen1tx_intf_delay;
        
        always_comb begin
                 ithermocode_p_inst    <= #(intf_delay*3) ithermocode_p;
                 ithermocode_n_inst    <= #(intf_delay*3) ithermocode_n;
                 iup_therm_inst        <= #(intf_delay*3) iup_therm;
                 idn_therm_inst        <= #(intf_delay*3) idn_therm;
                 idcs_data_invert_inst <= #(intf_delay*5) idcs_data_invert;
                 itxdigspare_inst[2:1] <= #(intf_delay*5) itxdigspare[2:1];
                 irstb_counter_inst    <= #(20)irstb_counter;
                 irstb_sampler_inst    <= #(20)irstb_sampler;
        end
    `else // UCIE_GLS
        always_comb begin
                 ithermocode_p_inst    = ithermocode_p;
                 ithermocode_n_inst    = ithermocode_n;
                 iup_therm_inst        = iup_therm;
                 idn_therm_inst        = idn_therm;
                 idcs_data_invert_inst = idcs_data_invert;
                 itxdigspare_inst[2:1] = itxdigspare[2:1];
                 irstb_counter_inst    = irstb_counter;
                 irstb_sampler_inst    = irstb_sampler;
        end
    `endif
`else // !INTEL_SIMONLY
    always_comb begin
             ithermocode_p_inst    = ithermocode_p;
             ithermocode_n_inst    = ithermocode_n;
             iup_therm_inst        = iup_therm;
             idn_therm_inst        = idn_therm;
             idcs_data_invert_inst = idcs_data_invert;
             itxdigspare_inst[2:1] = itxdigspare[2:1];
             irstb_counter_inst    = irstb_counter;
             irstb_sampler_inst    = irstb_sampler;
    end
`endif

endmodule //uciegen1tx_txcbb_wrap
// Local Variables:
// verilog-typedef-regexp: "^t_"
// verilog-auto-logic-type: "logic"
// verilog-library-directories:("." "ip76x")
// verilog-library-extensions:(".v" ".sv")
// verilog-auto-inst-param-value: t
// End:
`endif // UCIEGEN1TX_TXCBB_WRAP_SV
