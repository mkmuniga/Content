///=====================================================================================================================
/// Module Name:        punit_ccp_vc_intf_conn.sv
///
/// Primary Contact:    Olteanu, Yehonatan
/// Secondary Contact:

/// Creation Date:      10.01.2020
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
/// Punit CCP VC interface assignments
///=====================================================================================================================
/// Generic_code: Assign all newly added Punit CCP VC interface signals here


`define PUNIT_CCP_VC_CONNECT_CONDITIONS(CTESIG, RTLSIG, ACTIVE_COND, BLACK_BOX) \
    if (BLACK_BOX) begin\
        assign RTLSIG = 0;\
    end else if (ACTIVE_COND) begin\
        initial begin\
            force RTLSIG = CTESIG;\
        end\
    end else begin  \
        assign CTESIG = RTLSIG; \
    end \

`define GPSB_SIDE_POK(ID) `PUNIT_TOP_WRAP.ccp``ID``_gpsb_side_pok
`define PMSB_SIDE_POK(ID) `PUNIT_TOP_WRAP.ccp``ID``_pmsb_side_pok
 
`define PUNIT_CCP_VC_CONNECT_IA_CCPS(INDEX_IF) \
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccf_side_rst_b, `PUNIT_TOP.ccf_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].cgp_side_rst_b, `PUNIT_TOP.cgp_side_rst_b, !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_side_rst_b, `PUNIT_TOP.bigcore_ccp_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].media_side_rst_b, `PUNIT_TOP.media_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_vccinf_pwrgood, `PUNIT_TOP.punit_vccinf_pwrgood, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_dts_pwrgood, `PUNIT_TOP.dts_enable, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_A2P_IMMEDIATE_RESPONSE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.a2p_immediate_response, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_WP_CV_IA_CORE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.wp_cv_ia_ccp[INDEX_IF], !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_SIDE_POK_STATUS_3,  `PUNIT_TOP.ptpcbclk.side_pok_status_3_hw_data, !ACTIVE, !BLACK_BOX)

`define PUNIT_CCP_VC_CONNECT_IA_ATOM_CCPS(INDEX_IF) \
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccf_side_rst_b, `PUNIT_TOP.ccf_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].cgp_side_rst_b, `PUNIT_TOP.cgp_side_rst_b, !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_side_rst_b, `PUNIT_TOP.atom_ccp_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].media_side_rst_b, `PUNIT_TOP.media_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_vccinf_pwrgood, `PUNIT_TOP.punit_vccinf_pwrgood, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_dts_pwrgood, `PUNIT_TOP.dts_enable, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_A2P_IMMEDIATE_RESPONSE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.a2p_immediate_response, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_WP_CV_IA_CORE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.wp_cv_ia_ccp[INDEX_IF], !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_SIDE_POK_STATUS_3,  `PUNIT_TOP.ptpcbclk.side_pok_status_3_hw_data, !ACTIVE, !BLACK_BOX)

    

`define PUNIT_CCP_VC_CONNECT_GT(INDEX_IF)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccf_side_rst_b, `PUNIT_TOP.ccf_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].cgp_side_rst_b, `PUNIT_TOP.cgp_side_rst_b,     !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_side_rst_b, `PUNIT_TOP.bigcore_ccp_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].media_side_rst_b, `PUNIT_TOP.media_side_rst_b, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_dts_pwrgood, `PUNIT_TOP.dts_enable, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_vccinf_pwrgood, `PUNIT_TOP.punit_vccinf_pwrgood, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].gpsb_side_pok,  `PUNIT_TOP_WRAP.cgp_gpsb_side_pok,  ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].pmsb_side_pok,  `PUNIT_TOP_WRAP.cgp_pmsb_side_pok,  ACTIVE, !BLACK_BOX)\
    //`PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_gdie_cold_boot_trigger, `PUNIT_TOP.punit_gdie_cold_boot_trigger,  !ACTIVE, !BLACK_BOX)\
    //`PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_gdie_warm_boot_trigger, `PUNIT_TOP.punit_gdie_warm_boot_trigger,  !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_A2P_IMMEDIATE_RESPONSE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.a2p_immediate_response, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_SIDE_POK_STATUS_3,  `PUNIT_TOP.ptpcbclk.side_pok_status_3_hw_data, !ACTIVE, !BLACK_BOX)

`define PUNIT_CCP_VC_CONNECT_MEDIA(INDEX_IF)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccf_side_rst_b, `PUNIT_TOP.ccf_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].cgp_side_rst_b, `PUNIT_TOP.cgp_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_side_rst_b, `PUNIT_TOP.bigcore_ccp_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].media_side_rst_b, `PUNIT_TOP.media_side_rst_b,     !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_vccinf_pwrgood, `PUNIT_TOP.punit_vccinf_pwrgood, !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].gpsb_side_pok,  `PUNIT_TOP_WRAP.media_gpsb_side_pok,  ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].pmsb_side_pok,  `PUNIT_TOP_WRAP.media_pmsb_side_pok,  ACTIVE, !BLACK_BOX)\
       
`define PUNIT_CCP_VC_CONNECT_SIDE_POK(INDEX_IF,CCP_EN)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].gpsb_side_pok,  `GPSB_SIDE_POK(INDEX_IF), CCP_EN, !CCP_EN)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].pmsb_side_pok,  `PMSB_SIDE_POK(INDEX_IF), CCP_EN, !CCP_EN)

`define PUNIT_CCP_VC_CONNECT_QCHANNEL_REQ(INDEX_IF)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_inf_q_req_b,`PUNIT_TOP.ccp_inf_q_req_b[INDEX_IF], !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_cfc_clk_q_req_b,`PUNIT_TOP.ccp_cfc_clk_q_req_b[INDEX_IF], !ACTIVE, !BLACK_BOX)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_cfc_pwr_q_req_b,`PUNIT_TOP.ccp_cfc_pwr_q_req_b[INDEX_IF], !ACTIVE, !BLACK_BOX)
    
`define PUNIT_CCP_VC_CONNECT_SIDE_POK_FIX(INDEX_IF,INDEX_HW,CCP_EN)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].gpsb_side_pok,  `GPSB_SIDE_POK(INDEX_HW), CCP_EN, !CCP_EN)\
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].pmsb_side_pok,  `PMSB_SIDE_POK(INDEX_HW), CCP_EN, !CCP_EN)

//// Oshik macro - DO NOT USE will not support slice disabling
//`define PUNIT_CCP_VC_CONNECT_TOP_CCPS(INDEX_IF,INDEX_MOD_8) \
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccf_side_rst_b, `PUNIT_TOP.ccf_side_rst_b, !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].ccp_side_rst_b, `PUNIT_TOP.ccp_top0_side_rst_b[INDEX_MOD_8], !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_vccinf_pwrgood, `PUNIT_TOP_WRAP.punit_vccinf_pwrgood, !ACTIVE, !BLACK_BOX)\ 
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].punit_dts_pwrgood, `PUNIT_TOP.dts_enable, !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_A2P_IMMEDIATE_RESPONSE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.a2p_immediate_response, !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_WP_CV_IA_CORE,  `PUNIT_TOP.punit_gated_top.punit_gpsb_top.GPSB_REGS.punit_gpsb_infvnn_crs.punit_infvnn_io_regs.PCUcregU75nH_infvnn_io_regs.wp_cv_ia_ccp[INDEX_IF], !ACTIVE, !BLACK_BOX)\
//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF].IOREG_IO_SIDE_POK_STATUS_3,  `PUNIT_TOP.ptpcbclk.side_pok_status_3_hw_data, !ACTIVE, !BLACK_BOX)
//
//    // Oshik macro - end DO NOT USE will not support slice disabling
    
// FIXME - yolteanu - use this force line        `FORCE(RTLSIG = CTESIG, yolteanu, 17ww06, Punit CCP VC forcing driver and monitor interface);\
begin : punit_ccp_vc_connect
//big ccp
// FIXME - ydror2 - disabled here - hard coded in top file. need to clean
//    for(punit_ccp_vc_instance_loop_ind=0; punit_ccp_vc_instance_loop_ind<(PUNIT_IA_CCP_NUM-1); punit_ccp_vc_instance_loop_ind++) begin //FIXME - UGLY TEMP SOLUTION TILL A PROPER ELEGANT WAY TO DIFFERE BETWEEN ATOM AND CCP
//        `PUNIT_CCP_VC_CONNECT_IA_CCPS(punit_ccp_vc_instance_loop_ind)
//    end
//
//////FIXME - ydror2 - beautify later : start

//    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[INDEX_IF]., `PUNIT_TOP.ccp_top0_side_rst_b, !ACTIVE, !BLACK_BOX)\


//the formulas: FIXME - ydror2 [oshikbit]  - is this the right mapping of core to rst signal ? true for slice disable as well ? 
//  index if 0-> 23
//  top[i ] i index /8
//rstb[j]  whaere j = index %8
//sababa - lets hard code it now and I will beautify it later - first step
//- lets check that the ccp send fw -dl 
//afterwards lets connect the poks..
//but I didnt understand waht [j] represents -ahhh got it 
//one sec 




    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[0].ccp_side_rst_b, `COMPUTE0_CORE0.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[1].ccp_side_rst_b, `COMPUTE0_CORE1.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[2].ccp_side_rst_b, `COMPUTE0_CORE2.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[3].ccp_side_rst_b, `COMPUTE0_CORE3.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[4].ccp_side_rst_b, `COMPUTE0_CORE4.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[5].ccp_side_rst_b, `COMPUTE0_CORE5.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[6].ccp_side_rst_b, `COMPUTE0_CORE6.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[7].ccp_side_rst_b, `COMPUTE0_CORE7.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[8].ccp_side_rst_b, `COMPUTE1_CORE0.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[9].ccp_side_rst_b, `COMPUTE1_CORE1.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[10].ccp_side_rst_b, `COMPUTE1_CORE2.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[11].ccp_side_rst_b, `COMPUTE1_CORE3.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[12].ccp_side_rst_b, `COMPUTE1_CORE4.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[13].ccp_side_rst_b, `COMPUTE1_CORE5.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[14].ccp_side_rst_b, `COMPUTE1_CORE6.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[15].ccp_side_rst_b, `COMPUTE1_CORE7.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[16].ccp_side_rst_b, `COMPUTE2_CORE0.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[17].ccp_side_rst_b, `COMPUTE2_CORE1.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[18].ccp_side_rst_b, `COMPUTE2_CORE2.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[19].ccp_side_rst_b, `COMPUTE2_CORE3.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[20].ccp_side_rst_b, `COMPUTE2_CORE4.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[21].ccp_side_rst_b, `COMPUTE2_CORE5.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[22].ccp_side_rst_b, `COMPUTE2_CORE6.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[23].ccp_side_rst_b, `COMPUTE2_CORE7.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)

if (CCP_EXISTS[24]) begin // HSD 13011193167
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[24].ccp_side_rst_b, `COMPUTE3_CORE0.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[25].ccp_side_rst_b, `COMPUTE3_CORE1.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[26].ccp_side_rst_b, `COMPUTE3_CORE2.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[27].ccp_side_rst_b, `COMPUTE3_CORE3.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[28].ccp_side_rst_b, `COMPUTE3_CORE4.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[29].ccp_side_rst_b, `COMPUTE3_CORE5.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[30].ccp_side_rst_b, `COMPUTE3_CORE6.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[31].ccp_side_rst_b, `COMPUTE3_CORE7.core_server_inst.gp_side_rst_b, !ACTIVE, !BLACK_BOX)
end


    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[0].gpsb_side_pok,  `COMPUTE0_CORE0.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[1].gpsb_side_pok,  `COMPUTE0_CORE1.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[2].gpsb_side_pok,  `COMPUTE0_CORE2.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[3].gpsb_side_pok,  `COMPUTE0_CORE3.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[4].gpsb_side_pok,  `COMPUTE0_CORE4.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[5].gpsb_side_pok,  `COMPUTE0_CORE5.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[6].gpsb_side_pok,  `COMPUTE0_CORE6.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[7].gpsb_side_pok,  `COMPUTE0_CORE7.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[8].gpsb_side_pok,  `COMPUTE1_CORE0.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[9].gpsb_side_pok,  `COMPUTE1_CORE1.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[10].gpsb_side_pok, `COMPUTE1_CORE2.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[11].gpsb_side_pok, `COMPUTE1_CORE3.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[12].gpsb_side_pok, `COMPUTE1_CORE4.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[13].gpsb_side_pok, `COMPUTE1_CORE5.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[14].gpsb_side_pok, `COMPUTE1_CORE6.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[15].gpsb_side_pok, `COMPUTE1_CORE7.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[16].gpsb_side_pok, `COMPUTE2_CORE0.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[17].gpsb_side_pok, `COMPUTE2_CORE1.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[18].gpsb_side_pok, `COMPUTE2_CORE2.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[19].gpsb_side_pok, `COMPUTE2_CORE3.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[20].gpsb_side_pok, `COMPUTE2_CORE4.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[21].gpsb_side_pok, `COMPUTE2_CORE5.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[22].gpsb_side_pok, `COMPUTE2_CORE6.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[23].gpsb_side_pok, `COMPUTE2_CORE7.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)

if (CCP_EXISTS[24]) begin
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[24].gpsb_side_pok, `COMPUTE3_CORE0.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[25].gpsb_side_pok, `COMPUTE3_CORE1.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[26].gpsb_side_pok, `COMPUTE3_CORE2.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[27].gpsb_side_pok, `COMPUTE3_CORE3.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[28].gpsb_side_pok, `COMPUTE3_CORE4.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[29].gpsb_side_pok, `COMPUTE3_CORE5.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[30].gpsb_side_pok, `COMPUTE3_CORE6.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[31].gpsb_side_pok, `COMPUTE3_CORE7.core_server_inst.gp_side_pok, ACTIVE, !BLACK_BOX)
end
    
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[0].pmsb_side_pok,  `COMPUTE0_CORE0.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[1].pmsb_side_pok,  `COMPUTE0_CORE1.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[2].pmsb_side_pok,  `COMPUTE0_CORE2.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[3].pmsb_side_pok,  `COMPUTE0_CORE3.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[4].pmsb_side_pok,  `COMPUTE0_CORE4.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[5].pmsb_side_pok,  `COMPUTE0_CORE5.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[6].pmsb_side_pok,  `COMPUTE0_CORE6.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[7].pmsb_side_pok,  `COMPUTE0_CORE7.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[8].pmsb_side_pok,  `COMPUTE1_CORE0.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[9].pmsb_side_pok,  `COMPUTE1_CORE1.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[10].pmsb_side_pok, `COMPUTE1_CORE2.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[11].pmsb_side_pok, `COMPUTE1_CORE3.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[12].pmsb_side_pok, `COMPUTE1_CORE4.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[13].pmsb_side_pok, `COMPUTE1_CORE5.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[14].pmsb_side_pok, `COMPUTE1_CORE6.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[15].pmsb_side_pok, `COMPUTE1_CORE7.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[16].pmsb_side_pok, `COMPUTE2_CORE0.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[17].pmsb_side_pok, `COMPUTE2_CORE1.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[18].pmsb_side_pok, `COMPUTE2_CORE2.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[19].pmsb_side_pok, `COMPUTE2_CORE3.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[20].pmsb_side_pok, `COMPUTE2_CORE4.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[21].pmsb_side_pok, `COMPUTE2_CORE5.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[22].pmsb_side_pok, `COMPUTE2_CORE6.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[23].pmsb_side_pok, `COMPUTE2_CORE7.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)

if (CCP_EXISTS[24]) begin
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[24].pmsb_side_pok, `COMPUTE3_CORE0.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[25].pmsb_side_pok, `COMPUTE3_CORE1.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[26].pmsb_side_pok, `COMPUTE3_CORE2.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[27].pmsb_side_pok, `COMPUTE3_CORE3.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[28].pmsb_side_pok, `COMPUTE3_CORE4.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[29].pmsb_side_pok, `COMPUTE3_CORE5.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[30].pmsb_side_pok, `COMPUTE3_CORE6.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[31].pmsb_side_pok, `COMPUTE3_CORE7.core_server_inst.pm_side_pok, ACTIVE, !BLACK_BOX)
end

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[0].punit_vccinf_pwrgood,  `COMPUTE0_CORE0.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[1].punit_vccinf_pwrgood,  `COMPUTE0_CORE1.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[2].punit_vccinf_pwrgood,  `COMPUTE0_CORE2.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[3].punit_vccinf_pwrgood,  `COMPUTE0_CORE3.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[4].punit_vccinf_pwrgood,  `COMPUTE0_CORE4.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[5].punit_vccinf_pwrgood,  `COMPUTE0_CORE5.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[6].punit_vccinf_pwrgood,  `COMPUTE0_CORE6.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[7].punit_vccinf_pwrgood,  `COMPUTE0_CORE7.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[8].punit_vccinf_pwrgood,  `COMPUTE1_CORE0.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[9].punit_vccinf_pwrgood,  `COMPUTE1_CORE1.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[10].punit_vccinf_pwrgood, `COMPUTE1_CORE2.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[11].punit_vccinf_pwrgood, `COMPUTE1_CORE3.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[12].punit_vccinf_pwrgood, `COMPUTE1_CORE4.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[13].punit_vccinf_pwrgood, `COMPUTE1_CORE5.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[14].punit_vccinf_pwrgood, `COMPUTE1_CORE6.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[15].punit_vccinf_pwrgood, `COMPUTE1_CORE7.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)

    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[16].punit_vccinf_pwrgood, `COMPUTE2_CORE0.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[17].punit_vccinf_pwrgood, `COMPUTE2_CORE1.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[18].punit_vccinf_pwrgood, `COMPUTE2_CORE2.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[19].punit_vccinf_pwrgood, `COMPUTE2_CORE3.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[20].punit_vccinf_pwrgood, `COMPUTE2_CORE4.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[21].punit_vccinf_pwrgood, `COMPUTE2_CORE5.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[22].punit_vccinf_pwrgood, `COMPUTE2_CORE6.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[23].punit_vccinf_pwrgood, `COMPUTE2_CORE7.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
if (CCP_EXISTS[24]) begin
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[24].punit_vccinf_pwrgood, `COMPUTE3_CORE0.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[25].punit_vccinf_pwrgood, `COMPUTE3_CORE1.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[26].punit_vccinf_pwrgood, `COMPUTE3_CORE2.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[27].punit_vccinf_pwrgood, `COMPUTE3_CORE3.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[28].punit_vccinf_pwrgood, `COMPUTE3_CORE4.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[29].punit_vccinf_pwrgood, `COMPUTE3_CORE5.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[30].punit_vccinf_pwrgood, `COMPUTE3_CORE6.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
    `PUNIT_CCP_VC_CONNECT_CONDITIONS(punit_ccp_vc_if[31].punit_vccinf_pwrgood, `COMPUTE3_CORE7.core_server_inst.stpwrgoodxnnnh, !ACTIVE, !BLACK_BOX)
end 
//////FIXME - ydror2 - beautify later : end 

//atom : 
//    `PUNIT_CCP_VC_CONNECT_IA_ATOM_CCPS(PUNIT_IA_CCP_NUM-1)

//    for(punit_ccp_vc_instance_loop_ind=0; punit_ccp_vc_instance_loop_ind<PUNIT_IA_CCP_NUM; punit_ccp_vc_instance_loop_ind++) begin
//        `PUNIT_CCP_VC_CONNECT_SIDE_POK(punit_ccp_vc_instance_loop_ind,CCP_EXISTS[punit_ccp_vc_instance_loop_ind])
//    end
//FIXME - nrapapor/ydror2 - fix index to be coherent with ccp id 
//    `PUNIT_CCP_VC_CONNECT_GT(PUNIT_IA_CCP_NUM+1)
//    if (MEDIA_EXISTS == 0) begin
//        `PUNIT_CCP_VC_CONNECT_MEDIA(PUNIT_IA_CCP_NUM)        
//    //FIXME - ydror2 - fix to for loop
//    end


    // FIXME-CBB-oshikbit  disconnecting VC for now, bypassing using forces
//    `PUNIT_CCP_VC_CONNECT_SIDE_POK(0,CCP_EXISTS[0])
//    `PUNIT_CCP_VC_CONNECT_SIDE_POK(1,CCP_EXISTS[1])
//    `PUNIT_CCP_VC_CONNECT_SIDE_POK(2,CCP_EXISTS[2])
//    `PUNIT_CCP_VC_CONNECT_SIDE_POK(3,CCP_EXISTS[3])
//    //`PUNIT_CCP_VC_CONNECT_SIDE_POK(4,CCP_EXISTS[4])
//    `PUNIT_CCP_VC_CONNECT_SIDE_POK(5,CCP_EXISTS[5])
////    `PUNIT_CCP_VC_CONNECT_SIDE_POK(6,CCP_EXISTS[6])
////    `PUNIT_CCP_VC_CONNECT_SIDE_POK(7,CCP_EXISTS[7])
//    //`PUNIT_CCP_VC_CONNECT_SIDE_POK(8,CCP_EXISTS[8])
// // FIXME-PTL-AO - ydror2 - 14.11.22 - FIX that will be superset 
//    if (CCP_EXISTS[8]) begin
//        `PUNIT_CCP_VC_CONNECT_SIDE_POK(8,CCP_EXISTS[8])
//        `PUNIT_CCP_VC_CONNECT_SIDE_POK(4,CCP_EXISTS[4])
//        end
//    else begin
//        `PUNIT_CCP_VC_CONNECT_SIDE_POK_FIX(4,6,CCP_EXISTS[4])
//        `PUNIT_CCP_VC_CONNECT_SIDE_POK_FIX(6,4,CCP_EXISTS[6])
//    end
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(9,CCP_EXISTS[9])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(10,CCP_EXISTS[10])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(11,CCP_EXISTS[11])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(12,CCP_EXISTS[12])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(13,CCP_EXISTS[13])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(14,CCP_EXISTS[14])
////  `PUNIT_CCP_VC_CONNECT_SIDE_POK(15,CCP_EXISTS[15])

    


    
end : punit_ccp_vc_connect
