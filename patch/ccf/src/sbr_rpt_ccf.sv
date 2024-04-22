//-----------------------------------------------------------------
// Intel Proprietary -- Copyright 2013 Intel -- All rights reserved
//-----------------------------------------------------------------
// Author       : rpadler
// Date Created : 2015-2-9
//-----------------------------------------------------------------
// Description:
// Sequential repeater for SBR
//
// Features:
// Configurable payload width
// Modified to have async resetable flops -> provides scan interface for the
// same
//-----------------------------------------------------------------

module sbr_rpt_ccf
  #(
    parameter PAYLOAD_WIDTH = 8,
    parameter PARITY_REQUIRED = 0,
    parameter RESET_EN = 1,
    parameter POWERGOOD = 0
   )
  (
   // reuse-pragma attr if(Name =~.*parity.*) GenerateIf ((@PARITY_REQUIRED))
   input logic 			    mnpput_agt,
   input logic 			    mpcput_agt,
   output logic 		    mnpcup_agt,
   output logic 		    mpccup_agt,
   input logic 			    meom_agt,
   input logic [PAYLOAD_WIDTH-1:0]  mpayload_agt,
   input logic                      mparity_agt,
   
   output logic 		    tnpput_agt,
   output logic 		    tpcput_agt,
   input logic 			    tnpcup_agt,
   input logic 			    tpccup_agt,
   output logic 		    teom_agt,
   output logic [PAYLOAD_WIDTH-1:0] tpayload_agt,
   output logic                     tparity_agt,
   
   input logic [2:0] 		    side_ism_agent_agt,
   output logic [2:0] 		    side_ism_fabric_agt,
   input logic 			    pok_agt,
   
  // Between repeater and router
  //
   output logic 		    mnpput_rtr,
   output logic 		    mpcput_rtr,
   input logic 			    mnpcup_rtr,
   input logic 			    mpccup_rtr,
   output logic 		    meom_rtr,
   output logic [PAYLOAD_WIDTH-1:0] mpayload_rtr,
   output logic                     mparity_rtr,
   
   input logic 			    tnpput_rtr,
   input logic 			    tpcput_rtr,
   output logic 		    tnpcup_rtr,
   output logic 		    tpccup_rtr,
   input logic 			    teom_rtr,
   input logic [PAYLOAD_WIDTH-1:0]  tpayload_rtr,
   input logic                      tparity_rtr,
   
   output logic [2:0] 		    side_ism_agent_rtr,
   input logic [2:0] 		    side_ism_fabric_rtr,
   output logic 		    pok_rtr,

// reuse-pragma attr if(Name =~fscan.*rst.*) GenerateIf ((@RESET_EN))
   input logic				fscan_rstbypen, //HOTFIX
   input logic 				fscan_byprst_b, //HOTFIX
// reuse-pragma attr if(Name =~rep_rst_b) GenerateIf ((@RESET_EN))
   input logic 				rep_rst_b,
// reuse-pragma attr if(Name =~clk) GenerateIf ((@RESET_EN))
   input logic 			    clk,
   output logic             clk_req,
// reuse-pragma attr if(Name =~powergood) GenerateIf ((@POWERGOOD))
   input logic 			    powergood
   );

  generate
     if (RESET_EN) begin: sbr_rpt_ccf_module
    	logic sync_rep_rst_b;
    	logic sync_rep_rst_b_int;
        logic sync_rep_rst_b_int_scan;

  /*********************
   * Implement repeater flops. Every single sideband interface signal will be repeated
   * These flops are modified to be resetable. 
   * #They will naturally be reset by the flops driving the interface during reset propagation before reset is released. 
   */

        // FSCAN Bypass before the double flop synchronizer for all the resets in the sideband
        ctech_lib_mux_2to1 i_ctech_lib_scan_mux_rep_rst_b ( // lintra s-80018
            .d2( rep_rst_b      ),
            .d1( fscan_byprst_b ), 
            .s ( fscan_rstbypen ),
            .o ( sync_rep_rst_b )
        );

        // Router main clock reset synchronizer
        ctech_lib_doublesync_rstb i_ctech_lib_doublesync_rstb_rep_rst_b (
            .clk  ( clk ),
            .rstb ( sync_rep_rst_b ),
            .d    ( 1'b1 ),
            .o    ( sync_rep_rst_b_int )
        );
        // FSCAN Bypass after the double flop synchronizer for all the resets in the sideband
        ctech_lib_mux_2to1 i_ctech_lib_scan_mux_rep_rst_b_int ( // lintra s-80018
           .d2( sync_rep_rst_b_int ),
           .d1( fscan_byprst_b ), 
           .s ( fscan_rstbypen ),
           .o ( sync_rep_rst_b_int_scan )
        );
        always_ff @(posedge clk) begin
    
            mnpput_rtr 		 <= mnpput_agt;
            mpcput_rtr 		 <= mpcput_agt;
            mnpcup_agt 		 <= mnpcup_rtr;
            mpccup_agt 		 <= mpccup_rtr;

            
            tnpput_agt 		 <= tnpput_rtr;
            tpcput_agt 		 <= tpcput_rtr;
            tnpcup_rtr 		 <= tnpcup_agt;
            tpccup_rtr 		 <= tpccup_agt;
             
            side_ism_fabric_agt  <= side_ism_fabric_rtr;
            side_ism_agent_rtr   <= side_ism_agent_agt;
            pok_rtr              <= pok_agt;

            // reuse-pragma startSub remove_sig [IncludeIf (@PARITY_REQUIRED) %subText] 
            mparity_rtr      <= mparity_agt;
            tparity_agt      <= tparity_rtr;
            // reuse-pragma endSub remove_sig
        end

        always_ff @(posedge clk or negedge sync_rep_rst_b_int_scan) begin
            if(!sync_rep_rst_b_int_scan) begin
      	         meom_rtr 		 <=  'b0;
      	         mpayload_rtr 	 <=  'b0;
      	    end 
            else if (|side_ism_agent_agt) begin
        	    meom_rtr 		 <= meom_agt;
      	        mpayload_rtr 	 <= mpayload_agt;
            end
        end

        always_ff @(posedge clk or negedge sync_rep_rst_b_int_scan) begin
    	    if(!sync_rep_rst_b_int_scan) begin
      	        teom_agt 		 	 <= 'b0;
      	        tpayload_agt 	 <= 'b0;  
            end
      	    else if (|side_ism_fabric_rtr) begin
         	    teom_agt 		 <= teom_rtr;
      	        tpayload_agt 	 <= tpayload_rtr;  
            end
        end
    end : sbr_rpt_ccf_module

    else begin : els_dummy_buff 
         assign mnpput_rtr = mnpput_agt;
         assign mpcput_rtr = mpcput_agt;
         assign mnpcup_agt = mnpcup_rtr;
         assign mpccup_agt = mpccup_rtr;
         assign meom_rtr = meom_agt;
         assign mpayload_rtr[PAYLOAD_WIDTH-1:0] = mpayload_agt[PAYLOAD_WIDTH-1:0];
         //assign mparity_rtr = mparity_agt;
         assign tnpput_agt = tnpput_rtr;
         assign tpcput_agt = tpcput_rtr;
         assign tnpcup_rtr = tnpcup_agt;
         assign tpccup_rtr = tpccup_agt;
         assign teom_agt = teom_rtr;
         assign tpayload_agt[PAYLOAD_WIDTH-1:0] = tpayload_rtr[PAYLOAD_WIDTH-1:0];
         //assign tparity_agt = tparity_rtr;
         assign side_ism_agent_rtr[2:0] = side_ism_agent_agt[2:0];
         assign side_ism_fabric_agt[2:0] = side_ism_fabric_rtr[2:0];
         assign pok_rtr = pok_agt;
    end  :  els_dummy_buff

  endgenerate

  assign clk_req =  |(side_ism_agent_agt) | side_ism_fabric_rtr;

endmodule

