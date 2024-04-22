  logic [`V_WIRES_IN- 1:0] strap_default_wires_in;
  logic [`V_WIRES_OUT- 1:0] strap_default_wires_out;
  logic [`V_WIRES_IN- 1:0] strap_default_wires_in_tmp;
  logic [`V_WIRES_OUT- 1:0] strap_default_wires_out_tmp;
  logic       [`MAX_LANES-1:0]  phy2soc_sb_pok;
  logic       [`MAX_LANES-1:0]  phy2soc_sb_linkerror;
  logic       [`V_WIRES_IN-1:0]         async_virt_in_s;
  logic       [`V_WIRES_IN-1:0]         async_virt_in;
  logic       [`V_WIRES_OUT-1:0]       async_virt_out;
  logic tbclk;//400Mhz
  logic vw_ip_ready;
  logic bfm_rst;
  
  sbbfm_rdi_ifc rdi_sb_if0();//RTL DUT 0 to SBBFM
  sbbfm_rdi_ifc rdi_sb_if1();//RTL DUT 0 connection to Crd driver


  sbbfm_ti#(.NUM_LANES(`MAX_LANES),
              .V_WIRES_IN(`V_WIRES_IN),
              .V_WIRES_OUT(`V_WIRES_OUT),
              .TB_ENV_PATH($sformatf("*.d2d_env%0d.sbbfm_agent_env_0",ENV_INST)))
            sbbfm(croclk_in, xtalclk_in, bfm_rst, rdi_sb_if0);//need to use RTL rst for BFM
//            sbbfm(croclk_in, xtalclk_in, ~fdfx_powergood, rdi_sb_if0);
  vwi_if vwi_vif_top(.d2d_sb_clk(croclk_in), .async_clk(tbclk), .ip_ready(vw_ip_ready), .tb_reset(phy2soc_sb_pok), .strap_default_wires_in(`STRAP_DEFAULT_WIRES_IN), .async_virt_in(async_virt_in[`V_WIRES_IN-1:0]), .async_virt_out(async_virt_out[`V_WIRES_OUT-1:0]), .async_virt_in_s(async_virt_in_s[`V_WIRES_IN-1:0])); //cbb hotfix for soc checker
//  vwi_if vwi_vif_top(.d2d_sb_clk(croclk_in), .async_clk(tbclk), .tb_reset(phy2soc_sb_pok), .strap_default_wires_in(strap_default_wires_in), .async_virt_in(async_virt_in[`V_WIRES_IN-1:0]), .async_virt_out({o_vw_hwsync_ack,o_vw_hwsync_req,7'b0}));
//  vwi_if vwi_vif_top(.d2d_sb_clk(croclk_in), .async_clk(tbclk), .tb_reset(phy2soc_sb_pok), .strap_default_wires_in(strap_default_wires_in), .async_virt_in(async_virt_in[`V_WIRES_IN-1:0]), .async_virt_out({d2d_iosfsb2ucie_hwsync_ack_out_6,d2d_iosfsb2ucie_hwsync_req_out_5,5'b0}));
//  vwi_if vwi_vif_top();

//FIXME connect to Agent
  initial begin
    tbclk <= 1'b0;
    vw_ip_ready <= 1'b1;
    bfm_rst <= 1'b1;
  end


  always @(posedge croclk_in) begin
      tbclk = ~tbclk;
  end
 
  always @(pard2d0misc_d2d_4.rstw_sb2ucie_d2d_4.rstw_ip_prim_rst_b_int) begin
     if (pard2d0misc_d2d_4.rstw_sb2ucie_d2d_4.rstw_ip_prim_rst_b_int == 1'b1) begin
        #401ns
        bfm_rst <= 1'b0;
     end else begin
        bfm_rst <= 1'b1;
     end
  end



if (d2d_active_passive == uvm_pkg::UVM_ACTIVE) begin
  //FIXME force iosfsb2ucie interface until it gets connected
/*  initial begin
    if ($value$plusargs("STRAP_DEFAULT_WIRES_IN_VALUE=%x",strap_default_wires_in_tmp)) begin
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_in value from user %b",strap_default_wires_in), UVM_DEBUG)
        strap_default_wires_in <= strap_default_wires_in_tmp;
    end else begin
        strap_default_wires_in <= 16'b0000000000001001;
    end 
    if ($value$plusargs("STRAP_DEFAULT_WIRES_OUT_VALUE=%x",strap_default_wires_out_tmp)) begin
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_out value from user %b",strap_default_wires_out), UVM_DEBUG)
        strap_default_wires_out <= strap_default_wires_out_tmp;
    end else begin
        strap_default_wires_out <= 16'b0;
    end 
  end

  initial begin
    #1
    force pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.strap_default_wires_in  = strap_default_wires_in;
    force pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.strap_default_wires_out  = strap_default_wires_out;
  end
*/
  assign i_vw_pkgc_qacceptn      = async_virt_in[00];
  assign i_vw_pkgc_qactive       = async_virt_in[01];
  assign i_vw_pkgc_qdeny         = async_virt_in[02];
  assign i_vw_pkgc_qreqn         = async_virt_in[03];
  assign i_vw_pc6_qactive        = async_virt_in[04];
  assign i_vw_fast_throttle_2    = async_virt_in[05];
  assign i_vw_memhot_n           = async_virt_in[06];
  assign i_vw_hwsync_req         = async_virt_in[07];
  assign i_vw_hwsync_ack         = async_virt_in[08];
  assign i_vw_hwsync_req_remotes = async_virt_in[09];
  assign i_vw_hwsync_ack_remotes = async_virt_in[10];
  assign i_vw_preq               = async_virt_in[11];
  assign i_vw_prexit             = async_virt_in[12];
  assign i_vw_prdy_req           = async_virt_in[13];
  assign i_vw_prdy               = async_virt_in[14];
  assign i_vw_smbussy            = async_virt_in[15];
  
  assign i_vw_pm_reserved0       = async_virt_in[32];
  assign i_vw_pm_reserved1       = async_virt_in[33];     
end // if (d2d_active_passive == uvm_pkg::UVM_ACTIVE)
 
  //cbb hotfix
  assign async_virt_in_s[00]      = i_vw_pkgc_qacceptn;
  assign async_virt_in_s[01]      = i_vw_pkgc_qactive;
  assign async_virt_in_s[02]      = i_vw_pkgc_qdeny;
  assign async_virt_in_s[03]      = i_vw_pkgc_qreqn;
  assign async_virt_in_s[04]      = i_vw_pc6_qactive;
  assign async_virt_in_s[05]      = i_vw_fast_throttle_2;
  assign async_virt_in_s[06]      = i_vw_memhot_n;
  assign async_virt_in_s[07]      = i_vw_hwsync_req;
  assign async_virt_in_s[08]      = i_vw_hwsync_ack;
  assign async_virt_in_s[09]      = i_vw_hwsync_req_remotes;
  assign async_virt_in_s[10]      = i_vw_hwsync_ack_remotes;
  assign async_virt_in_s[11]      = i_vw_preq;
  assign async_virt_in_s[12]      = i_vw_prexit;
  assign async_virt_in_s[13]      = i_vw_prdy_req;
  assign async_virt_in_s[14]      = i_vw_prdy;
  assign async_virt_in_s[15]      = i_vw_smbussy;
                                
  assign async_virt_in_s[32]      = i_vw_pm_reserved0;
  assign async_virt_in_s[33]      = i_vw_pm_reserved1;     

  assign async_virt_in_s[31:16]   = 16'b0000000000000000;
  assign async_virt_in_s[63:34]   = 30'b000000000000000000000000000000;

   
  assign async_virt_out[00]      = o_vw_pkgc_qacceptn;
  assign async_virt_out[01]      = o_vw_pkgc_qactive;
  assign async_virt_out[02]      = o_vw_pkgc_qdeny;
  assign async_virt_out[03]      = o_vw_pkgc_qreqn;
  assign async_virt_out[04]      = o_vw_pc6_qactive;
  assign async_virt_out[05]      = o_vw_fast_throttle_2;
  assign async_virt_out[06]      = o_vw_memhot_n;
  assign async_virt_out[07]      = o_vw_hwsync_req;
  assign async_virt_out[08]      = o_vw_hwsync_ack;
  assign async_virt_out[09]      = o_vw_hwsync_req_remotes;
  assign async_virt_out[10]      = o_vw_hwsync_ack_remotes;
  assign async_virt_out[11]      = o_vw_preq;
  assign async_virt_out[12]      = o_vw_prexit;
  assign async_virt_out[13]      = o_vw_prdy_req;
  assign async_virt_out[14]      = o_vw_prdy;
  assign async_virt_out[15]      = o_vw_smbussy;

  assign async_virt_out[32]      = o_vw_pm_reserved0;
  assign async_virt_out[33]      = o_vw_pm_reserved1;

  assign async_virt_out[31:16]   = 16'b0000000000000000;
  assign async_virt_out[63:34]   = 30'b000000000000000000000000000000;

   
  always @(bfm_rst) begin
     if (bfm_rst == 1'b1) begin
        phy2soc_sb_pok <= 6'b000000;
        phy2soc_sb_linkerror <= 6'b000000;
     end   
     else begin       
        #400//random delay
        phy2soc_sb_pok <= 6'b111111;
        phy2soc_sb_linkerror <= 6'b000000;
     end   
  end


   initial begin
    if (D2D_PHYLESS || ($test$plusargs("D2D_R2B_RDI")) || ($test$plusargs("D2D_B2B_RDI"))  ) begin
// clk is connected inside sbbfm_ti
//  assign rdi_sb_if0.clk = croclk_in;

     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m5 = phy2soc_sb_pok[5];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m4 = phy2soc_sb_pok[4];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m3 = phy2soc_sb_pok[3];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m2  = phy2soc_sb_pok[2];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m1  = phy2soc_sb_pok[1];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_pok_m0  = phy2soc_sb_pok[0];

   //Connect Credit Driver
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m5 = rdi_sb_if1.pl_cfg_crd[5];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m4 = rdi_sb_if1.pl_cfg_crd[4];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m3 = rdi_sb_if1.pl_cfg_crd[3];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m2 = rdi_sb_if1.pl_cfg_crd[2];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m1 = rdi_sb_if1.pl_cfg_crd[1];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_crd_m0 = rdi_sb_if1.pl_cfg_crd[0];
     force rdi_sb_if1.lp_cfg = pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.soc2phy_sb_cfg;
     force rdi_sb_if1.lp_cfg_vld = pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.soc2phy_sb_cfg_vld;
     force rdi_sb_if1.pl_cfg_ok = phy2soc_sb_pok;
     force rdi_sb_if1.pl_cfg = rdi_sb_if0.lp_cfg;
     force rdi_sb_if1.pl_cfg_vld = rdi_sb_if0.lp_cfg_vld;
     force rdi_sb_if1.clk = croclk_in;
     force rdi_sb_if1.reset = rdi_sb_if0.reset;
   end

   if ($test$plusargs("D2D_R2B_RDI") ) begin
     force rdi_sb_if0.pl_cfg = pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.soc2phy_sb_cfg;
     force rdi_sb_if0.pl_cfg_vld = pard2d0misc_d2d_4.iosfsb2ucie_d2d_4.soc2phy_sb_cfg_vld;
     force rdi_sb_if0.pl_cfg_ok = phy2soc_sb_pok;
     force rdi_sb_if0.pl_cfg_linkerror =  phy2soc_sb_linkerror;
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m5 = rdi_sb_if0.lp_cfg[5];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m4 = rdi_sb_if0.lp_cfg[4];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m3 = rdi_sb_if0.lp_cfg[3];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m2 = rdi_sb_if0.lp_cfg[2];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m1 = rdi_sb_if0.lp_cfg[1];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_m0 = rdi_sb_if0.lp_cfg[0];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m5 = rdi_sb_if0.lp_cfg_vld[5];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m4 = rdi_sb_if0.lp_cfg_vld[4];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m3 = rdi_sb_if0.lp_cfg_vld[3];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m2 = rdi_sb_if0.lp_cfg_vld[2];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m1 = rdi_sb_if0.lp_cfg_vld[1];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_phy2soc_sb_cfg_vld_m0 = rdi_sb_if0.lp_cfg_vld[0];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m5 = rdi_sb_if0.pl_cfg_linkerror[5];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m4 = rdi_sb_if0.pl_cfg_linkerror[4];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m3 = rdi_sb_if0.pl_cfg_linkerror[3];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m2 = rdi_sb_if0.pl_cfg_linkerror[2];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m1 = rdi_sb_if0.pl_cfg_linkerror[1];
     force pard2d0chnl_d2d_4.ucie_phy_d2d_4.o_ophy_sb_error_m0 = rdi_sb_if0.pl_cfg_linkerror[0];
   end
end

  initial begin 
    string env_path, vwi_inst;
    env_path = $sformatf("*.d2d_env%0d.iosfsb2ucie_env_inst.*",ENV_INST);
    uvm_config_db#(virtual sbbfm_rdi_ifc)::set(null, env_path, "rdi_vif", rdi_sb_if1);
    env_path = $sformatf("*.vwi_agent_inst%0d.*",ENV_INST);
    uvm_config_db#(virtual vwi_if)::set(null, env_path, "dut_vi", vwi_vif_top);
    vwi_inst = $sformatf("dut%0d_vi",ENV_INST);
    uvm_config_db#(virtual vwi_if)::set(null, "uvm_test_top", vwi_inst, vwi_vif_top);
  end
