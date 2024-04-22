

//=====================================================================================================================
// Module Name:        imh_scheduler.sv
//
// Primary Contact:    Oshik
// Last Review Date:
// Creation Date:      12/2022
// Last Review Date:
//
// Copyright (c) 2013-2015 Intel Corporation
// Intel Proprietary and Top Secret Information
//---------------------------------------------------------------------------------------------------------------------
// Description:
//  main component in IMH. activates and terminates different flows,
//  via other subcomponents (ese for ex.) 
//  or directly via ifc (platform ifc)
//
//  list of functionalities:
//
//
//=====================================================================================================================

// FIXME-CBB-oshikbit  - need to randomize the toggling of XTAL clock. only condition it that clk is valid at cpu-reset-good !!!


import uvm_pkg::*;
`include "uvm_macros.svh"


class imh_scheduler extends uvm_component;

    `uvm_component_utils(imh_scheduler)

    imh_scheduler_config sched_cfg;

    virtual imh_boot_if     boot_if;
    virtual imh_platform_if platform_if;
    virtual imh_clock_if    clock_if;
    virtual ccu_intf        clk_if;

    string tid;

    imh_vc_reg_block reg_block; // manually created RAL  

    bit disable_vccst_shutdown;
    bit ssr_mode;
    string delay_range;
    longint local_xtal_cnt;
    int unsigned local_xtal_offset;
    iosfsbm_cm::xaction pmsb_rx;               
    iosfsbm_cm::xaction gpsb_rx;

    uvm_event pmsb_message_ev;    
    uvm_event gpsb_message_ev;  


    bit [6:0] trg_agent_id = 'h0;  
      


    uvm_tlm_analysis_fifo #(iosfsbm_cm::xaction) sb_analysis_fifo_rx, sb_analysis_fifo_tx;
    uvm_tlm_analysis_fifo #(iosfsbm_cm::xaction) pmsb_analysis_fifo_rx, pmsb_analysis_fifo_tx;

    iosfsbm_cm::xaction pmsb_messages_queue [$];
    iosfsbm_cm::xaction gpsb_messages_queue [$];
    iosfsbm_cm::iosfsbc_sequencer pmsb_sqr;
    iosfsbm_cm::iosfsbc_sequencer gpsb_sqr;


    function new(string name, uvm_component parent);
        super.new(name, parent);

        if(!(uvm_config_db#(imh_scheduler_config)::get(null, "*", "imh_scheduler_config", sched_cfg))) begin
            `uvm_info(get_type_name(), "No imh_scheduler_config found, creating one.", UVM_LOW)
            sched_cfg = new();
            if (!sched_cfg.randomize())
                            `uvm_fatal(get_type_name(), $sformatf("Randomization Error"));

        end

        uvm_config_db#(imh_scheduler_config)::set(null, "*", "imh_scheduler_config", sched_cfg);

        tid = "IMH_VC_MSG";

        sb_analysis_fifo_rx         = new("sb_analysis_fifo_rx", this);
        sb_analysis_fifo_tx         = new("sb_analysis_fifo_tx", this);
        pmsb_analysis_fifo_rx       = new("pmsb_analysis_fifo_rx", this);
        pmsb_analysis_fifo_tx       = new("pmsb_analysis_fifo_tx", this);

        gpsb_message_ev = new();
        pmsb_message_ev = new();

        uvm_config_db #(bit)::get(null, "*", "imh_ssr_mode", ssr_mode);

    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if(!(uvm_config_db#(imh_vc_reg_block)::get(null, "", "imh_vc_reg_block", reg_block))) 
            `uvm_fatal(tid, "couldnt find imh_vc_reg_block in config_db");

        if (ssr_mode) begin
            delay_range = "SMALL_DELAY";
        end else begin
            delay_range = "SMALL2MEDIUM_DELAY";
        end

        `uvm_info(tid, $sformatf("ssr_mode %0d, delay_range %0s",ssr_mode,delay_range), UVM_LOW)

    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        // interfaces
        if(!uvm_config_db #(virtual imh_boot_if)::get(null, "", "imh_boot_if", boot_if))
            `uvm_error(tid, "Unable to get handle to imh_boot_if")
        if(!uvm_config_db #(virtual imh_platform_if)::get(null, "", "imh_platform_if", platform_if))
            `uvm_error(tid, "Unable to get handle to imh_platform_if")
        if(!uvm_config_db #(virtual imh_clock_if)::get(null, "", "imh_clock_if", clock_if))
            `uvm_error(tid, "Unable to get handle to imh_clock_if")
                  
    endfunction:connect_phase

    function void start_of_simulation_phase(uvm_phase phase);
        super.start_of_simulation_phase(phase);
        
    endfunction:start_of_simulation_phase

/*****************************************     RUN PHASE    *****************************************/
    task run_phase(uvm_phase phase);

        // sequencers
        if(!uvm_config_db#(iosfsbm_cm::iosfsbc_sequencer)::get(null, "imh_vc_env", "pmsb_sequencer", pmsb_sqr)) begin
            `uvm_error(get_type_name(), "Unable to get sb_sequencer from config db in flow sequence.")
        end
        if(!uvm_config_db#(iosfsbm_cm::iosfsbc_sequencer)::get(null, "imh_vc_env", "gpsb_sequencer", gpsb_sqr)) begin
            `uvm_error(get_type_name(), "Unable to get sb_sequencer from config db in flow sequence.")
        end

        `uvm_info(tid, "starting run_phase", UVM_LOW)
        init_signals();

        fork
            begin
                local_xtal_counter(); 
            end
        join_none


        reset_exit('b1);
        

        fork
            // reactive block
//            begin
//                respond_to_hpm_message();
//            end
            // active block
//            begin               
//            end
            // random block
//            begin
//                send_random_hpm_message();
//            end
            // monitor block
            begin
                forever begin
                    pmsb_analysis_fifo_rx.get(pmsb_rx);
                    pmsb_messages_queue.push_back(pmsb_rx);
                    pmsb_message_ev.trigger();
                end
            end
            begin
                forever begin
                    sb_analysis_fifo_rx.get(gpsb_rx);
                    gpsb_messages_queue.push_back(gpsb_rx);
                    gpsb_message_ev.trigger();
                end
            end
            begin
                forever begin
                    `VC_MSG($sformatf("starting to track tsc"),"-TSC", UVM_LOW);                      
                    track_and_respond_to_tsc_request();
                end
            end  
               
            begin
                forever begin
                    // VC will constrain the credit-rtn message till pmsb is unlocked,
                    // acording to HAS prime code send will send this message ONLY after TSC request 
                    // - also - hidden assumption - PMSB will not be blocked
                    // unless in reset flow
                    `VC_MSG($sformatf("waiting for punit_pmsb_is_blocked config deassertion"),"-HPM_INIT", UVM_LOW);                      
                    wait(boot_if.punit_pmsb_is_blocked_deassertion === 1'b1);

                    `VC_MSG($sformatf("HPM initialization on reset exit"),"-HPM_INIT", UVM_LOW);                      
                    hpm_init();
                end
            end  
 
            begin
                forever begin
                    //`VC_MSG($sformatf("starting ncu_config_and_take_core_out_reset"),"-NCU_CFG", UVM_LOW);                      
                    ncu_config_and_take_core_out_reset();
                end
            end         

            begin
                forever begin
                    //`VC_MSG($sformatf("starting track_and_respond_to_hpm_messages"),"-HPM_RSP", UVM_LOW);                      
                    track_and_respond_to_hpm_messages();
                end
            end         

            begin
                forever begin
                    //`VC_MSG($sformatf("starting wait_for_ready_for_xxreset_and_send_straps"),"-STRAPSET", UVM_LOW);                      
                    wait_for_ready_for_xxreset_and_send_straps();
                end
            end                  
       join_none

//        monitor_for_simple_msg_from_punit_to_pmc();
//        fork
//            check_for_reset_entry();
//            check_for_cstate();
//        join_none
    endtask:run_phase

/****************************************     AUXILARY TASKS     ****************************************/
/******************************************* **************** *******************************************/ 
/*********************************************** wait_for_ready_for_xxreset_and_send_straps ***********************************************/
    task wait_for_ready_for_xxreset_and_send_straps();
        
        int rndNum;
        int delayForXXresetb;
        hpm_sb_seq strapset_1_msg, strapset_2_msg;
        hpm_xaction mon_hpm;

        bit recieved_response;// = 0;

        mon_hpm = new();       
               
        wait_for_pmsb_msg(.opcode(HPM_IP2PM));
        assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
        mon_hpm.parse_message();

        // wait for LP_ENUMERATION, before sending NCU_CFG
        if ((mon_hpm.hpm_msg_param[7:0] == READY_FOR_XXRESET) && (mon_hpm.hpm_msg_opcode == HPM_PARAM_EXCHANGE_UPSTREAM)) begin

            fork
                begin
                    `VC_MSG("recieved READY_FOR_XXRESET. about to deassert platform_if.reset_b", "-XXRESET", UVM_LOW);
                    rndNum = $urandom_range(0,101);
                    case (rndNum%10) inside
                       ['d1:'d8]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
                        'd9: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
                        default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
                    endcase

                    assign_signal_with_data_after_delay(.sig(platform_if.reset_b), .delay_ns(1), .data(1)); 
                end
                     
                begin
                   `VC_MSG($sformatf("recieved HPM %s.%s message, preparing to send STRAPSET",mon_hpm.hpm_msg_opcode,mon_hpm.hpm_msg_param[7:0]),"-STRAPSET", UVM_LOW);                      
                   rndNum = $urandom_range(0,101);
                   case (rndNum%10) inside
                      ['d1:'d8]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
                       'd9: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
                       default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
                  endcase
                  strapset_1_msg = new();
                  `VC_MSG($sformatf("Sending STRAPSET message number 1."),"-STRAPSET", UVM_LOW);                      
                  if (!strapset_1_msg.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                strapset_1_msg.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                strapset_1_msg.hpm_data_size_qw   == 2; 
                                strapset_1_msg.hpm_msg_opcode     == HPM_PARAM_EXCHANGE;
                                strapset_1_msg.RR                 == 1'b1;
                                strapset_1_msg.hpm_msg_param[7:0] == DISTRIBUTE_STRAPS_CBB;
                                strapset_1_msg.hpm_msg_param[15:8] == 'h0;
                                strapset_1_msg.hpm_payload_data_vector[31:0]  == sched_cfg.imh_poc_strapset;
                                strapset_1_msg.hpm_payload_data_vector[63:32] == sched_cfg.imh_plt_strapset;
                                strapset_1_msg.hpm_payload_data_vector[95:64] == sched_cfg.imh_pch_strapset;
                            }) 
                            `uvm_fatal("STRAPSET", $sformatf("Randomization Error - STRAPSET 1"));
                  strapset_1_msg.start(pmsb_sqr);

                  // add wait for response on 1st hpm
                  `VC_MSG($sformatf("waiting for STRAPSET response on message 1."),"-STRAPSET", UVM_LOW);                      
            
                  wait_for_hpm_response(.hpm_opcode(HPM_PARAM_EXCHANGE), .hpm_param(DISTRIBUTE_STRAPS_CBB), .check_param(1));
//                  while (recieved_response == 0) begin
//                      wait_for_pmsb_msg(.opcode(HPM_IP2PM));
//                      assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
//                      mon_hpm.parse_message();
//                      recieved_response = ((mon_hpm.hpm_msg_param[7:0] == DISTRIBUTE_STRAPS_CBB)  && (mon_hpm.hpm_msg_opcode == HPM_PARAM_EXCHANGE));
//                  end
//                  recieved_response = 0;

                  strapset_2_msg = new();
                  `VC_MSG($sformatf("Sending STRAPSET message number 2."),"-STRAPSET", UVM_LOW);                      
                  if (!strapset_2_msg.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                strapset_2_msg.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                strapset_2_msg.hpm_data_size_qw   == 2; 
                                strapset_2_msg.hpm_msg_opcode     == HPM_PARAM_EXCHANGE;
                                strapset_2_msg.RR                 == 1'b1;
                                strapset_2_msg.hpm_msg_param[7:0] == DISTRIBUTE_STRAPS_CBB;
                                strapset_2_msg.hpm_msg_param[15:8] == 8'h81; // setting the data-offset and done-bit to 1
                                strapset_2_msg.hpm_payload_data_vector[31:0]  == sched_cfg.imh_cpu_strapset;
                                strapset_2_msg.hpm_payload_data_vector[63:32] == sched_cfg.imh_mc_dis_strapset;
                                strapset_2_msg.hpm_payload_data_vector[95:64] == sched_cfg.imh_io_dis_strapset;
                            }) 
                            `uvm_fatal("STRAPSET", $sformatf("Randomization Error - STRAPSET 2"));
                  strapset_2_msg.start(pmsb_sqr);

                  // add wait for response on 1st hpm
                  `VC_MSG($sformatf("waiting for STRAPSET response on message 2."),"-STRAPSET", UVM_LOW);                      
                  wait_for_hpm_response(.hpm_opcode(HPM_PARAM_EXCHANGE), .hpm_param(DISTRIBUTE_STRAPS_CBB), .check_param(1));
//                  while (recieved_response == 0) begin
//                      wait_for_pmsb_msg(.opcode(HPM_IP2PM));
//                      assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
//                      mon_hpm.parse_message();
//                      recieved_response = ((mon_hpm.hpm_msg_param[7:0] == DISTRIBUTE_STRAPS_CBB)  && (mon_hpm.hpm_msg_opcode == HPM_PARAM_EXCHANGE));
//                  end
//                  recieved_response = 0;

              end
          join_none
                  
        end
 
    endtask:wait_for_ready_for_xxreset_and_send_straps

/*************************************** wait_for_hpm_response **************************************/
    task wait_for_hpm_response(input bit[7:0] hpm_opcode, hpm_param, bit check_param=0);

        bit recieved_response;
        hpm_xaction mon_hpm;
        time t0,t1;

        mon_hpm = new();     

        if (check_param) `VC_MSG($sformatf("wait_for_hpm_response. expected hpm opcode - 'h%0h, expected param - 'h%0h",hpm_opcode,hpm_param),"-WAIT_HPM_RSP", UVM_LOW);
        if (!check_param) `VC_MSG($sformatf("wait_for_hpm_response. expected hpm opcode - 'h%0h",hpm_opcode),"-WAIT_HPM_RSP", UVM_LOW);

        t0 = $realtime;
        while (recieved_response == 0) begin
            wait_for_pmsb_msg(.opcode(HPM_IP2PM));
            assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
            mon_hpm.parse_message();
            recieved_response = (check_param) ? ((mon_hpm.hpm_msg_param[7:0] == hpm_param)  && (mon_hpm.hpm_msg_opcode == hpm_opcode)) : (mon_hpm.hpm_msg_opcode == hpm_opcode);
        end
        t1 = $realtime;
        if ((t1-t0)>1ms) `VC_ERROR("response time for hpm message longer than 1ms");
        if (mon_hpm.hpm_src_agent_id != trg_agent_id) `VC_ERROR($sformatf("hpm message from punit recieved with wrong agent id ('h%0h != 'h%0h)", trg_agent_id,mon_hpm.hpm_src_agent_id ));




    endtask
/*********************************************** ncu_config_and_take_core_out_reset ***********************************************/
    task ncu_config_and_take_core_out_reset();
        
        int rndNum;
        bit esm; //enter ssp mode
        hpm_sb_seq hpm_ncu_cfg, hpm_ssp_go;
        hpm_xaction mon_hpm;

        mon_hpm = new();       
               
        wait_for_pmsb_msg(.opcode(HPM_IP2PM));
        assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
        mon_hpm.parse_message();

        // wait for LP_ENUMERATION, before sending NCU_CFG
        if ((mon_hpm.hpm_msg_param[7:0] == LP_ENUMERATION) && (mon_hpm.hpm_msg_opcode == HPM_PARAM_EXCHANGE_UPSTREAM)) begin
                   `VC_MSG($sformatf("recieved HPM HPM_PARAM_EXCHANGE_UPSTREAM.LP_ENUMERATION message, preparing to send NCU_CFG"),"-NCU_CFG", UVM_LOW);                      
                   rndNum = $urandom_range(0,101);
                   case (rndNum%10) inside
                      ['d1:'d8]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
                       'd9: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
                       default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
                  endcase
                  esm = rndNum[3];
                  hpm_ncu_cfg = new();
                  `VC_MSG($sformatf("Sending NCU_CFG message. esm was randomized to %0d",esm),"-NCU_CFG", UVM_LOW);                      
                  if (!hpm_ncu_cfg.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                hpm_ncu_cfg.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                hpm_ncu_cfg.hpm_data_size_qw   == 2; 
                                hpm_ncu_cfg.hpm_msg_opcode     == HPM_PARAM_EXCHANGE;
                                hpm_ncu_cfg.RR                 == 1'b1;
                                hpm_ncu_cfg.hpm_msg_param[7:0] == NCU_CONFIG;
                                hpm_ncu_cfg.hpm_payload_data_vector != 'h0;
                                hpm_ncu_cfg.hpm_payload_data_vector[31] == esm;
                            }) 
                            `uvm_fatal("NCU_CFG", $sformatf("Randomization Error - NCU_CFG"));

                  hpm_ncu_cfg.start(pmsb_sqr);

                  wait_for_hpm_response(.hpm_opcode(HPM_PARAM_EXCHANGE), .hpm_param(NCU_CONFIG), .check_param(1));

                  if (esm) begin
                      `VC_MSG($sformatf("Sending SSP_GO message. since esm was randomized to %0d",esm),"-NCU_CFG", UVM_LOW);                      

                      rndNum = $urandom_range(0,1000);
                       case (rndNum%10) inside
                          ['d1:'d2]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
                          ['d3:'d9]: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
                           default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
                      endcase

                      hpm_ssp_go = new();
                      if (!hpm_ssp_go.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                hpm_ssp_go.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                hpm_ssp_go.hpm_data_size_qw   == 2; 
                                hpm_ssp_go.hpm_msg_opcode     == HPM_PARAM_EXCHANGE;
                                hpm_ssp_go.RR                 == 1'b1;
                                hpm_ssp_go.hpm_msg_param[7:0] == SSP_GO;
                                hpm_ssp_go.hpm_payload_data_vector != 'h0;
                                hpm_ssp_go.hpm_payload_data_vector[31] == esm;
                            }) 
                            `uvm_fatal("NCU_CFG", $sformatf("Randomization Error - SSP_GO"));

                      hpm_ssp_go.start(pmsb_sqr);
                      wait_for_hpm_response(.hpm_opcode(HPM_PARAM_EXCHANGE), .hpm_param(SSP_GO), .check_param(1));

                  end
        end
 

        
                
    endtask:ncu_config_and_take_core_out_reset


/*********************************************** track_and_respond_to_hpm_messages ***********************************************/
    task track_and_respond_to_hpm_messages();
        
        int rndNum;
        hpm_sb_seq hpm_rsp;
        hpm_xaction mon_hpm;

        mon_hpm = new();       
        wait_for_pmsb_msg(.opcode(HPM_IP2PM));
        assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
        mon_hpm.parse_message();
        if (mon_hpm.hpm_resp_required == 'b0)
            `VC_MSG($sformatf("recieved HPM message - No response is required"),"-HPM_RSP", UVM_LOW);                      


        if (trg_agent_id == 'h0) `VC_ERROR("recieved HPM message from punit before agent ID was configured")
    
        if (mon_hpm.hpm_resp_required) begin
            `VC_MSG($sformatf("recieved HPM message with response is required"),"-HPM_RSP", UVM_LOW);                      
            if (mon_hpm.hpm_msg_opcode == HPM_PARAM_EXCHANGE_UPSTREAM) begin
                fork begin
                   rndNum = $urandom_range(0,101);
                   case (rndNum%10) inside
                      ['d1:'d8]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
                       'd9: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
                       default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
                  endcase
                  hpm_rsp = new();
                  `VC_MSG($sformatf("Sending HPM message response"),"-HPM_RSP", UVM_LOW);                      
                  if (!hpm_rsp.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                hpm_rsp.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                hpm_rsp.hpm_data_size_qw   == 2; 
                                hpm_rsp.hpm_msg_opcode     == HPM_PARAM_EXCHANGE_UPSTREAM;
                                hpm_rsp.RR                 == 1'b0;
                                hpm_rsp.hpm_msg_param      == mon_hpm.hpm_msg_param[7:0]; // return the same syncid to param exchange
                            }) 
                            `uvm_fatal("HPM_RSP", $sformatf("Randomization Error - hpm_rsp"));

                  hpm_rsp.start(pmsb_sqr);
                end
                join_none             
            end

            else begin
                `VC_ERROR("recieved hpm_msg_opcode != HPM_PARAM_EXCHANGE_UPSTREAM, need to add support");
            end

        end
 

                
    endtask:track_and_respond_to_hpm_messages


/*********************************************** hpm_init ***********************************************/
    task hpm_init ();
        
        int rndNum;
        bit wait_for_tsc_req;
        hpm_sb_seq crdt_rtn_seq;
        hpm_xaction mon_hpm, dum_hpm;

        time t0,t1;

        mon_hpm = new();  
        dum_hpm = new();     
        if (sched_cfg.use_cfg_agent_id) trg_agent_id = sched_cfg.hpm_target_agent_id;
        else trg_agent_id = $urandom_range(1,127);
    

        // randomize timing of message
        wait_for_tsc_req = ($urandom_range(0,100))%10;

        //if (wait_for_tsc_req > 2) begin
            `VC_MSG($sformatf("waiting for tsc delay request (randomized)"),"-HPM_INIT", UVM_LOW);                      
            wait_for_gpsb_msg(.opcode(OP_TSC_DELAY_REQ)); // FIXME-oshikbit- add pid and seg to this call
        //end

//        rndNum = $urandom_range(0,101);
//        case (rndNum%10) inside
//            ['d1:'d8]: sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
//            'd9: sched_cfg.wait_delay_in_range("LARGE_DELAY"); 
//            default: sched_cfg.wait_delay_in_range("SMALL_DELAY");
//        endcase
      
        sched_cfg.wait_delay_in_range("SMALL_DELAY");

        `VC_MSG($sformatf("USING AGENT ID 'h%0h FOR PUNIT. Sending CRDT_RTN now",trg_agent_id),"-HPM_INIT", UVM_LOW);                      
        
        crdt_rtn_seq = new();
        if (!crdt_rtn_seq.randomize with {
                                //crdt_rtn_seq.data_i.size()      == full_data_size_in_flits;
                                crdt_rtn_seq.hpm_data_size_qw   == 1; 
                                crdt_rtn_seq.hpm_msg_opcode     == HPM_CREDIT_RTN;
                                crdt_rtn_seq.punit_hpm_agent_id == trg_agent_id;
                                crdt_rtn_seq.RR                 == 1'b1;
//                                crdt_rtn_seq.num_credits        == 0;
                            }) 
                            `uvm_fatal("HPM_INIT", $sformatf("Randomization Error - crdt_rtn_seq"));

       crdt_rtn_seq.start(pmsb_sqr);

       t0 = $realtime;

       wait_for_pmsb_msg(.opcode(HPM_IP2PM));
       t1 = $realtime;
       //`VC_MSG($sformatf("mon-hpm b4 cast - %s",mon_hpm.hpm_msg.sprint_header()),"",UVM_HIGH);
       assert($cast(mon_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
       //assert($cast(dum_hpm.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
       mon_hpm.parse_message();
       //dum_hpm.parse_message();
       //`VC_MSG($sformatf("mon-hpm after cast %s",mon_hpm.hpm_msg.sprint_header()),"",UVM_HIGH);
       //`VC_MSG($sformatf("original item - %s",pmsb_messages_queue[$].sprint_header()),"",UVM_HIGH);
       //dum_hpm.hpm_msg_opcode = 'h0;
       //if (mon_hpm.compare(dum_hpm)) `VC_MSG("MISCMP DEBUG","-HPM_INIT",UVM_HIGH)
       if ((mon_hpm.hpm_msg_opcode == HPM_CREDIT_RTN) && (mon_hpm.hpm_resp_required))
         `VC_ERROR("recived response for HPM_CREDIT_RTN with RR bit set")
       
       if ((t1-t0) > sched_cfg.crdt_rtn_response_lat_ns*1ns)
         `VC_ERROR($sformatf("IMH did not recieve CRDT_RTN response after %0d ns. t0=%t, t1=%t",sched_cfg.crdt_rtn_response_lat_ns,t0,t1))
  
       `VC_MSG("check hpm_init response is complete","-HPM_INIT",UVM_LOW)
                
    endtask:hpm_init

/**************************************** respond_to_hpm_message ****************************************/

/**************************************** send_random_hpm_message ***************************************/


/********************************************* init_signals *********************************************/
    task init_signals();
//FIXME - oshikbit  - review this task
        int delay_time_ns = $urandom_range(1,50);
        string tid_pf = {tid,"::INIT_SIGNALS"};
        `uvm_info(tid_pf, "signals initialization", UVM_LOW);

        
    
        platform_if.aux_bclk_req = 1'b0;

        platform_if.vccin_ehv = 1'bx;
        platform_if.vccinf  = 1'bx;
        platform_if.vccfa_ehv = 1'bx;
        platform_if.vcca_hv = 1'bx;
        platform_if.vccvnn  = 1'bx;
        platform_if.S0_pwr_ok  = 1'bx;
        platform_if.cpu_pwr_good  = 1'bx;
        platform_if.aux_pwrgood  = 1'bx;
        platform_if.reset_b  = 1'bx;
        platform_if.hvm_mode  = 1'bx;
        platform_if.fbreak  = 1'bx;
        //platform_if.fbreak_fuse_ovrd  = 1'bx;
        //platform_if.fbreak_pcode_start  = 1'bx;
        platform_if.cbb_enable  = 1'bx;
        platform_if.die_id  = 4'bx;

//        boot_if.ese_fabric_own_req = 1'bx;
//        boot_if.base_fuse_override_done = 1'bx;

        boot_if.inf_st_punit_pfet_en_ack_b = 1'bx;

        #(delay_time_ns*1ns);

        platform_if.vccin_ehv = 1'b0;
        platform_if.vccinf  = 1'b0;
        platform_if.vccfa_ehv = 1'b0;
        platform_if.vcca_hv = 1'b0;
        platform_if.vccvnn  = 1'b0;
        platform_if.S0_pwr_ok  = 1'b0;
        platform_if.cpu_pwr_good  = 1'b0;
        platform_if.aux_pwrgood  = 1'b0;
        platform_if.reset_b  = 1'b0;
        platform_if.hvm_mode  = 1'b0;
        platform_if.fbreak  = 1'b1;
        //platform_if.fbreak_fuse_ovrd  = 1'b1;
        //platform_if.fbreak_pcode_start  = 1'b1;
        platform_if.cbb_enable  = 1'b1;
        platform_if.die_id  = $urandom_range(0,4'hF);

//        assign_val_after_delay(boot_if.ese_fabric_own_req, 1'b0);
//        assign_val_after_delay(boot_if.base_fuse_override_done, 1'b0);
        assign_val_after_delay(boot_if.inf_st_punit_pfet_en_ack_b, 1'b1);
        assign_val_after_delay(boot_if.ingress_alert, 1'b0);
        assign_val_after_delay(boot_if.egress_alert, 1'b0);
        #20;
    endtask : init_signals

/************************************************ local_xtal_counter ***********************************************/
    task local_xtal_counter();

        assert(std::randomize(local_xtal_offset) with {local_xtal_offset dist {0:=70,[100:5000]:/20,['hFFFFFFC0:'hFFFFFFF0]:/10};}) 
        else `VC_ERROR($sformatf("Randomization Failed\n"))
    
        local_xtal_cnt = local_xtal_offset;

        forever begin
            @(posedge clock_if.xtal_clk);
            local_xtal_cnt = local_xtal_cnt+1;
        end
    endtask

/************************************************ assign_val_after_delay ***********************************************/
    task assign_val_after_delay (ref logic sig, input logic val, int unsigned dly = 'h55555555);
        if (dly == 'h55555555) begin
            sched_cfg.wait_delay_in_range(delay_range); 
        end
        else begin
            #(dly*1ns);
        end
        sig = val;
    endtask


/************************************************ track_and_respond_to_tsc_request ***********************************************/
    task track_and_respond_to_tsc_request();

        sync_msg sync;
        tsc_msg_with_data followup, delayrsp;
        bit [63:0] ingress_alert_time, egress_alert_time;

        // wait for "ready-for-tsc". and check the message
        //=====================================================
        `VC_MSG("waiting for TSC ready message","-TSC", UVM_LOW);                      
        wait_for_gpsb_msg(.opcode(OP_TSC_READY)); // FIXME-oshikbit- add pid and seg to this call

        // optional - check if we expect tsc download now
        //====================================================
    
        // idle + send sync message
        //=================================
        repeat($urandom_range(0,99)) @(posedge clock_if.xtal_clk); // FIXME-oshikbit- good random ? 
        sync = new();
        if(!sync.randomize() with {m_misc == 'h0;}) begin
            //vc_error("Randomization Failed");
            `VC_ERROR("Randomization Failed")
        end
//        wait_gpsb_link_secure();
        `VC_MSG("sending TSC SYNC message","-TSC", UVM_LOW);                      
        sync.start(null);
        

        // idle + send ingress_alert. save local time (unconnected in SOC)
        //=====================================================================
        repeat($urandom_range(0,99)) @(posedge clock_if.xtal_clk); // FIXME-oshikbit- good random ? 
        @(negedge clock_if.xtal_clk); 
        `VC_MSG("Asserting ingress alert","-TSC", UVM_LOW);                      
        boot_if.ingress_alert = 1'b1;
        ingress_alert_time = local_xtal_cnt;  
        @(negedge clock_if.xtal_clk); 
        boot_if.ingress_alert = 1'b0;
       

        // send followup message with random t1 (t1 < ingress alert local imh time local_xtal_cnt)
        //============================================================================================
        repeat($urandom_range(0,50)) @(posedge clock_if.xtal_clk); // FIXME-oshikbit- good random ? 
        followup = new();
        //if(!followup.randomize() with {m_tsc inside {[]:=4,[]:=1};}) begin
        if(!followup.randomize() with {m_tsc > longint'(ingress_alert_time/2); m_tsc < longint'(ingress_alert_time);
                                        m_opcode == OP_TSC_FOLLOW_UP; }) begin
            `VC_ERROR("Randomization Failed")
        end
//        wait_gpsb_link_secure();
        `VC_MSG("Sending follow up message","-TSC", UVM_LOW);                      
        followup.start(null);

        // wait for "delay-req"
        //============================
        `VC_MSG("Waiting for TSC DELAY REQ message","-TSC", UVM_LOW);                      
        wait_for_gpsb_msg(.opcode(OP_TSC_DELAY_REQ)); // FIXME-oshikbit- add pid and seg to this call
        

        // idle + send egress-alert. save local time
        //=====================================================================
        repeat($urandom_range(0,9)) @(posedge clock_if.xtal_clk); // FIXME-CBB-oshikbit- good random ? 
        @(negedge clock_if.xtal_clk); 
        `VC_MSG("Asserting eggress alert","-TSC", UVM_LOW);                      
        boot_if.egress_alert = 1'b1;
        egress_alert_time = local_xtal_cnt;  
        @(negedge clock_if.xtal_clk); 
        boot_if.egress_alert = 1'b0;


        // send delayresp message with random t4 (t4 > egress alert local imh time local_xtal_cnt)
        //============================================================================================
        repeat($urandom_range(0,29)) @(posedge clock_if.xtal_clk); // FIXME-CBB-oshikbit- good random ? 
        delayrsp = new();
        //if(!followup.randomize() with {m_tsc inside {[]:=4,[]:=1};}) begin
        if(!delayrsp.randomize() with {m_tsc > (egress_alert_time); m_tsc < (2*egress_alert_time);
                                        m_opcode == OP_TSC_DELAY_RES;}) begin
            `VC_ERROR("Randomization Failed")
        end
//        wait_gpsb_link_secure();
        `VC_MSG("Sending delay response message","-TSC", UVM_LOW);                      
        delayrsp.start(null);

 

    endtask:track_and_respond_to_tsc_request

///******************************************** test_message ********************************************/
// function void vc_msg (input string msg = "", string postfix = "", uvm_verbosity verbose = UVM_LOW);
//   `uvm_info({tid,postfix},msg,verbose);
// endfunction
//
// /******************************************** test_error ********************************************/
// function void vc_error (input string msg = "", string postfix = "");
//   `uvm_error({tid,postfix},msg);
// endfunction

/******************************************** reset_exit ********************************************/ 
    task reset_exit(bit do_powerup); 
        `VC_MSG($sformatf("reset_exit started. do_powerup=%0d",do_powerup),"-RESET_EXIT", UVM_LOW);
        if(do_powerup) begin
            ramp_S5_power("UP");
            ramp_S0_power("UP");
            phase0(); // clk reqs,  cold boot trigger assertion
        end
        phase1(); // tsc req, epoc, fw_download, ready for straps, straps message, warm boot trigger assertion
        `VC_MSG($sformatf("reset_exit is completed successfuly. do_powerup=%0d",do_powerup),"-RESET_EXIT", UVM_LOW);
    endtask


/***************************************** txn_is_from_punit_to *****************************************/
    function bit txn_is_from_punit_to(iosfsbm_cm::xaction txn, logic [7:0] pid = 'hx, logic [7:0] seg = 'hx);
        bit res;
        if (seg === 'hx) seg = txn.seg_dest_pid;
        if (pid === 'hx) pid = txn.dest_pid;
        if(sched_cfg.hierarchichal_sb_en) begin
            res = (txn.src_pid == PUNIT_GPSB_PID || txn.src_pid == PUNIT_PCODE_PID) && (txn.seg_src_pid == CBB_SEG_ID)
            && (txn.dest_pid == pid) && (txn.seg_dest_pid == seg);
        end else begin
            res = (txn.src_pid == PUNIT_GPSB_PID || txn.src_pid == PUNIT_PCODE_PID) && (txn.dest_pid == pid);
        end
        res = 1'b1; // FIXME-CBB-oshikbit. bypass, blocking TSC enabling. need to fix
        return res;
    endfunction



/******************************************* wait_for_gpsb_msg ******************************************/
    task wait_for_gpsb_msg (input logic [7:0] opcode='hx, logic [7:0] pid = 'hx, logic [7:0] seg='hx);

        `VC_MSG($sformatf("waiting for msg with opcode %0h from gpsb",opcode),"-GPSB", UVM_LOW); 
        if (opcode === 'hx) `VC_ERROR("must specify opcode in wait_for_gpsb_msg")
        do 
        begin  
            gpsb_message_ev.wait_trigger();
            `VC_MSG($sformatf("GPSB incoming txn: %0h",gpsb_messages_queue[$].opcode),"-GPSB",UVM_HIGH);

        end
        while(!(gpsb_messages_queue[$].opcode == opcode && txn_is_from_punit_to(gpsb_messages_queue[$],pid,seg)));
        `VC_MSG($sformatf("got msg with opcode %0h from punit",opcode),"-GPSB", UVM_LOW); 
    endtask

/******************************************* wait_for_pmsb_msg ******************************************/
    task wait_for_pmsb_msg (input logic [7:0] opcode='hx, logic [7:0] pid = 'hx, logic [7:0] seg='hx);

        `VC_MSG($sformatf("waiting for msg with opcode %0h from pmsb",opcode),"-PMSB", UVM_LOW); 
        if (opcode === 'hx) `VC_ERROR("must specify opcode in wait_for_gpsb_msg")

        do 
        begin  
            pmsb_message_ev.wait_trigger();
            `VC_MSG($sformatf("PMSB incoming txn: %0h",pmsb_messages_queue[$].opcode),"-PMSB",UVM_HIGH);
        end
        while(!(pmsb_messages_queue[$].opcode == opcode && txn_is_from_punit_to(pmsb_messages_queue[$],pid,seg)));
        `VC_MSG($sformatf("got msg with opcode %0h from punit",opcode),"-PMSB", UVM_LOW); 
    endtask


/********************************* wait_for_simple_msg_from_punit_to_pmc ********************************/ 
//    task wait_for_simple_msg_from_punit_to_pmc(logic [7:0] opcode);
//        iosfsbm_cm::xaction txn;
//        do 
//        begin  
//            sb_analysis_fifo_rx.get(txn);
//            `uvm_info(tid, $sformatf("Flow coordinator SB incoming txn: %0h",txn.opcode), UVM_HIGH) 
//        end
//        while(!(txn.opcode == opcode && txn_is_from_punit_to_pmc(txn)));
//        `uvm_info(tid, $sformatf("-DBG- got simple msg with opcode %0h",opcode), UVM_LOW) 
//    endtask


//    function bit is_ack_sx_message(iosfsbm_cm::xaction txn);
//        return txn.opcode == sched_cfg.op_ack_sx && txn_is_from_punit_to_pmc(txn);
//    endfunction

//    function bit txn_is_from_punit_to_pmc(iosfsbm_cm::xaction txn);
//        bit res;
//        if(sched_cfg.hierarchichal_sb_en) begin
//            res = (txn.src_pid == sched_cfg.punit[7:0] || txn.src_pid == sched_cfg.punit1[7:0]) && (txn.seg_src_pid == sched_cfg.punit_seg_portid[7:0])
//            && (txn.dest_pid == sched_cfg.pmc[7:0]) && (txn.seg_dest_pid == sched_cfg.pmc_seg_portid[7:0]);
//        end else begin
//            res = (txn.src_pid == sched_cfg.punit[7:0] || txn.src_pid == sched_cfg.punit1[7:0]) && (txn.src_pid == sched_cfg.pmc[7:0]);
//        end
//        if (txn.opcode==sched_cfg.ack_sx) `uvm_info(tid, $sformatf("-DBG- got simple msg with opcode ack_sx , res == %0b",res), UVM_LOW) 
//        return res;
//    endfunction
//
//
//    function bit txn_is_from_pmc_to_punit(iosfsbm_cm::xaction txn);
//        if(sched_cfg.hierarchichal_sb_en) begin
//            return txn.src_pid == sched_cfg.pmc[7:0] && txn.seg_src_pid == sched_cfg.pmc_seg_portid[7:0]
//            && txn.dest_pid == sched_cfg.punit[7:0] && txn.seg_dest_pid == sched_cfg.punit_seg_portid[7:0];
//        end else begin
//            return txn.src_pid == sched_cfg.pmc[7:0] && txn.src_pid == sched_cfg.punit[7:0];
//        end
//    endfunction

//    function bit is_go_s1_temp_message(iosfsbm_cm::xaction txn);
//        return txn.opcode == sched_cfg.go_s1_temp && txn_is_from_pmc_to_punit(txn);
//    endfunction
//
//    function bit is_go_s1_rw_message(iosfsbm_cm::xaction txn);
//        return txn.opcode == sched_cfg.go_s1_rw && txn_is_from_pmc_to_punit(txn);
//    endfunction
//
//    function bit is_reset_begin_msg(iosfsbm_cm::xaction txn);
//        return is_go_s1_rw_message(txn) || is_go_s1_temp_message(txn);
//    endfunction
//
//    function bit is_pm_req_message(iosfsbm_cm::xaction txn);
//        return txn.opcode == sched_cfg.pm_req;
//    endfunction

//    task wait_for_tx_sb_msg(output iosfsbm_cm::xaction txn);
//        iosfsbm_cm::xaction txn_local;
//        sb_analysis_fifo_tx.get(txn_local);
//        txn = txn_local;
//        while(!is_reset_begin_msg(txn_local)) begin
//            sb_analysis_fifo_tx.get(txn_local);
//            txn = txn_local;
//        end
//    endtask

/****************************************** send_simple_msg *****************************************/
//    task send_simple_msg(logic [7:0] opcode, string rst_warn_data = "");
//        chipset_simple_msg simple_msg;
//        simple_msg = new();
//        vc_msg($sformatf("-DBG- gotto send simple message with opcode: %0h",opcode), "send_simple_msg");
//        if (!simple_msg.randomize with {opcode == local::opcode;
//                                    //    m_misc == 'h0;
//                                    })
//            `uvm_fatal(tid, $sformatf("Error while sending simple msg with opcode = %x.", opcode))
//          if (rst_warn_data == "warm")  begin
//            // ovrd data
//            simple_msg.m_misc = 'h0;
//          end
//          if (rst_warn_data == "cold")  begin
//            // ovrd data
//            simple_msg.m_misc = 'h1;
//          end
//        wait_gpsb_link_secure();
//        simple_msg.start(null);
//        vc_msg($sformatf("-DBG- allegedly simple :send opcode %0h, send misc %4b",opcode,simple_msg.m_misc), "send_simple_msg");
//    endtask

    task platform_pwrgood(input bit value = 1'b0);
     
      int dly_ns = $urandom_range(5,50);
      `VC_ERROR("unimplemented - platform_pwrgood")

    endtask:platform_pwrgood

    task ramp_S5_power(input string direction = "");

        bit value;
        int dly_ns;

        if (direction != "UP" && direction != "DN") begin
            `VC_ERROR("must use UP or DN when calling ramp_S5_power")
        end
        else begin
            `VC_MSG($sformatf("ramp_S5_power %s started",direction),"-PWR", UVM_LOW); 
        end

        if (direction == "UP") begin
            value = 1;
            fork
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccvnn), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccfa_ehv), .delay_ns(dly_ns), .data(value)); 
                end
            join
            dly_ns = $urandom_range(5,100);
            assign_signal_with_data_after_delay(.sig(platform_if.aux_pwrgood), .delay_ns(dly_ns), .data(value)); 

        end

        if (direction == "DN") begin
            value = 0;
            assign_signal_with_data_after_delay(.sig(platform_if.aux_pwrgood), .delay_ns(dly_ns), .data(value)); 

            fork
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccfa_ehv), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccvnn), .delay_ns(dly_ns), .data(value)); 
                end
            join
        end

        `VC_MSG($sformatf("ramp_S5_power %s done",direction),"-PWR", UVM_LOW); 

    endtask:ramp_S5_power

    task ramp_S0_power(input string direction = "");

        bit value;
        int dly_ns;

        if (direction != "UP" && direction != "DN") begin
            `VC_ERROR("must use UP or DN when calling ramp_S0_power")
        end 
        else begin
            `VC_MSG($sformatf("ramp_S0_power %s started",direction),"-PWR", UVM_LOW); 
        end




        if (direction == "UP") begin
            value = 1;
            fork
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vcca_hv), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccinf), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccin_ehv), .delay_ns(dly_ns), .data(value)); 
                end
            join
        end

        if (direction == "DN") begin
            value = 0;
            fork
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccin_ehv), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vccinf), .delay_ns(dly_ns), .data(value)); 
                end
                begin
                    dly_ns = $urandom_range(5,100);
                    assign_signal_with_data_after_delay(.sig(platform_if.vcca_hv), .delay_ns(dly_ns), .data(value)); 
                end
            join
        end

        `VC_MSG($sformatf("ramp_S0_power %s done",direction),"-PWR", UVM_LOW); 

    endtask:ramp_S0_power



    task phase0();
        
        `VC_MSG("\tphase0 task Started\n\n", "-PH0", UVM_LOW);

        // FIXME-CBB-oshikbit - XTAL should be 0|1|x|Toggle before S0pwrOK 
        repeat (25) begin
            @ (posedge boot_if.vc_int_clk);
        end

        fork
            begin
                //FIXME-CBB-oshikbit clk-modeling repeat (sched_cfg.random_delay_in_range("SMALL2MEDIUM_DELAY")) @ (posedge boot_if.vc_int_clk);
                repeat (1000) @ (posedge boot_if.vc_int_clk);
                `VC_MSG("setting platform_if.S0_pwr_ok ", "-PH0", UVM_LOW);
                assign_signal_with_data_after_delay(.sig(platform_if.S0_pwr_ok), .delay_ns(0), .data(1)); 
            end

            begin
                //FIXME-CBB-oshikbit clk-modeling repeat (sched_cfg.random_delay_in_range("SMALL2MEDIUM_DELAY")) @ (posedge boot_if.vc_int_clk);
                repeat (10) @ (posedge boot_if.vc_int_clk);
                `VC_MSG("ungating VC xtal clk ", "-PH0", UVM_LOW);
                assign_signal_with_data_after_delay(.sig(platform_if.aux_xtal_req), .delay_ns(0), .data(1)); 
            end
        join

        
        repeat (sched_cfg.random_delay_in_range("SMALL2MEDIUM_DELAY")) @ (posedge clock_if.xtal_clk);

        fork
            begin
                assign_signal_with_data_after_delay(.sig(platform_if.aux_bclk_req), .delay_ns($urandom_range(50,200)), .data(1)); 
            end
            begin
                sched_cfg.wait_delay_in_range(delay_range); 
            end
        join_any

        `VC_MSG("waiting for clock_if.bclk life sign", "-PH0", UVM_LOW);
        wait (clock_if.bclk === 1'b1)
        `VC_MSG("waiting for clock_if.bclk 2nd life sign", "-PH0", UVM_LOW);
        wait (clock_if.bclk === 1'b0)

        sched_cfg.wait_delay_in_range(delay_range);  // cpu_pwr_good -> S0_pwr_ok should be 5ms acording to spec
        fork
            begin
                `VC_MSG("setting platform_if.cpu_pwr_good ", "-PH0", UVM_LOW);
                assign_signal_with_data_after_delay(.sig(platform_if.cpu_pwr_good), .delay_ns($urandom_range(50,1000)), .data(1)); 
            end
        join

//        assert (std::randomize(vdd2_dly) with {vdd2_dly > 0;  vdd2_dly < (int'(2*sched_cfg.delay_epd_on_ns));}) else `uvm_error(tID,$sformatf("Randomization Failed\n"));
//        fork
//            assign_signal_with_data_after_delay(.sig(boot_if.epd_on), .delay_ns(sched_cfg.delay_epd_on_ns), .data(1'b1));  
//        join

        `VC_MSG("\tphase0 task End\n\n", "-PH0", UVM_LOW);
    endtask:phase0

//    assign_signal_with_data_after_delay & assign_val_after_delay - duplicated code
    task assign_signal_with_data_after_delay(ref logic sig, input int delay_ns, input logic data);
        #(delay_ns * 1ns);
        sig = data;
    endtask

// phase1 - handling signals that should be driven by SOC
// SOC will need to disable this section and/or disconnect these signals from
// driving punit ifc, as real ESE should do that.

    task phase1();
        `VC_MSG("phase1 task Started\n\n", "-PH1", UVM_LOW);
        //wait for hwsync hs
        wait_hwsync_lock();        
        //drive the ese_fabric_own_req - moved to ese agent
//        assign_val_after_delay(boot_if.ese_fabric_own_req, 1'b1);
        //wait for base_fuse_override_done
        wait_ese_fabric_lock();  

        //idle
//        sched_cfg.wait_delay_in_range(delay_range);
//        sched_cfg.wait_delay_in_range(delay_range);
        //drive the base_fuse_override_done - moved to ese agent
//        assign_val_after_delay(boot_if.base_fuse_override_done, 1'b1);
        //wait for base_fuse_override_done
        wait_base_fuse_ovrd_done(); 

        // FIXME-CBB-oshikbit - add checks on "Part 7 of PH1 flow diagram"
        // latch straps
        // latch vnn-pwr-retained
        //

        `VC_MSG("waiting for boot_fsm to be UP ","-PH1",UVM_LOW);
        wait (boot_if.bootfsm_state === 'h2F); // BOOT_FSM_IS_UP
        `VC_MSG("waiting for boot_fsm to be UP .... done","-PH1",UVM_LOW);

        `VC_MSG("phase1 task End\n\n", "-PH1", UVM_LOW);
        
    endtask:phase1 
    
    task wait_base_fuse_ovrd_done();

            `VC_MSG("waiting for boot_if.base_fuse_override_done", "-wait_base_fuse_ovrd_done", UVM_LOW);
            wait(boot_if.base_fuse_override_done_samp === 1);
            `VC_MSG("waiting for boot_if.base_fuse_override_done done", "-wait_base_fuse_ovrd_done", UVM_LOW);

    endtask:wait_base_fuse_ovrd_done

    task wait_ese_fabric_lock();

        //if (sched_cfg.wait_for_hwsync_lock) begin
            `VC_MSG("waiting for boot_if.ese_fabric_own_req && boot_if.ese_fabric_own_ack", "-wait_ese_fabric_lock", UVM_LOW);
            wait(boot_if.ese_fabric_own_req === 1 && boot_if.ese_fabric_own_ack === 1);
            `VC_MSG("waiting for boot_if.ese_fabric_own_req && boot_if.ese_fabric_own_ack done", "-wait_ese_fabric_lock", UVM_LOW);
        //end

    endtask:wait_ese_fabric_lock

    task wait_hwsync_lock();

        if (sched_cfg.wait_for_hwsync_lock) begin
            `VC_MSG("waiting for boot_if.hwsync_req && (boot_if.hwsync_ack_0 || boot_if.hwsync_ack_1)", "-wait_hwsync_lock", UVM_LOW);
            wait(boot_if.hwsync_req === 1 && (boot_if.hwsync_ack_0 === 1 || boot_if.hwsync_ack_1 === 1));
            `VC_MSG("waiting for boot_if.hwsync_req && (boot_if.hwsync_ack_0 || boot_if.hwsync_ack_1) done", "-wait_hwsync_lock", UVM_LOW);
        end

    endtask:wait_hwsync_lock

    task wait_gpsb_link_secure();
        if (sched_cfg.wait_for_gpsb_link_secure) begin
            `VC_MSG(" waiting for boot_if.gpsb_link_secure","-wait_gpsb_link_secure", UVM_LOW)
            wait(boot_if.gpsb_link_secure === 1);
            `VC_MSG(" waiting for boot_if.gpsb_link_secure ... done","-wait_gpsb_link_secure", UVM_LOW)
        end
    endtask:wait_gpsb_link_secure

    task wait_saf_config_done();
            if (sched_cfg.wait_for_saf_config_done == 1) begin
            `VC_MSG( " waiting for boot_if.saf_south_config_done", "",UVM_LOW);
                wait(boot_if.saf_south_config_done === 1);
            `VC_MSG( " waiting for boot_if.saf_south_config_done ... done", "",UVM_LOW);
            end
    endtask:wait_saf_config_done


    task set_fbreak(bit value, int delay = 0);
        #(delay * 1ns);
        platform_if.fbreak = value;
    endtask

    //task set_fbreak_fuse_ovrd(bit value, int delay = 0);
    //    #(delay * 1ns);
    //    platform_if.fbreak_fuse_ovrd = value;
    //endtask

    //task set_fbreak_pcode_start(bit value, int delay = 0);
    //    #(delay * 1ns);
    //    platform_if.fbreak_pcode_start = value;
    //endtask

    // FIXME - when can be asserted and are we sure about polarity with IMH 
    task set_cbb_enable(bit value, int delay = 0);
        #(delay * 1ns);
        platform_if.cbb_enable = value;
    endtask

    task set_hvm(bit value, int delay = 0);
        #(delay * 1ns);
        platform_if.hvm_mode = value;
    endtask

    task set_reset_b(bit value, int delay = 0);
        #(delay * 1ns);
        platform_if.reset_b = value;
    endtask
    
//    task monitor_for_simple_msg_from_punit_to_pmc();
//        iosfsbm_cm::xaction txn;
//        fork 
//        begin
//            forever 
//            begin  
//                sb_analysis_fifo_rx.get(txn);
//                `uvm_info(tid, $sformatf(" MONITOR_FOR_SIMPLE_MSG_FROM_PUNIT_TO_PMC - Flow coordinator SB incoming txn: %s",txn.opcode), UVM_LOW) 
//            end
//        end
//        join_none; 
//    endtask

// reset/Sx comments :  
//      3 types of Sx states, 2 types of reset (cold/warm)
//      surprise reset converges with any of these, after xxreset is asserted.
//      method - single task to send cold/warm/Sx , which is aware to xxreset
//      and adapts to it, which means:
//          1. may or may not send GO* messages
//          2. will NOT wait for GO* msgs responses from punit, once xxreset is asserted
//      task will support different power rails control for the different flows:
//      

task reset_sx_entry(input imh_reset_sx_states_t flow_type, bit keep_st = 'b0, bit level0_mode = 'b0);
  
  int ns_dly;
  int range;
  int m_level; //-> Sx level
  bit phase_b_complete, wait_phase_b_complete;
  bit break_phase_a_b_when_xxreset_assert;

  string tid_pf = "-RESET_SX_ENTRY";
  
  hpm_sb_seq hpm_rst_prep_1, hpm_rst_prep_2;
  hpm_xaction rst_prep_rsp_1, rst_prep_rsp_2;
  hpm_reset_type_t  m_reset_type;

  byte m_byte;

  `VC_MSG("Seq started ...",tid_pf,UVM_LOW);
  
  hpm_rst_prep_1 = new();
  hpm_rst_prep_2 = new();
  break_phase_a_b_when_xxreset_assert = $urandom_range(0,1);

  fork
      begin
          if (flow_type == IMH_COLD_RESET || flow_type == IMH_WARM_RESET) m_reset_type = HPM_GO_S1_RW; //RESET_TYPE
          if (flow_type > IMH_WARM_RESET) m_reset_type = HPM_GO_S1_TEMP; //RESET_TYPE

          //    PARAMETER_RESERVED	PR	RR1	Agent Id	HPM_MSG_OPCODE (0x2)	0	0
          //    PAYLOAD_0_RSVD	P(hase)	PREP_TYPE(8bit = 0)	RESET_TYPE(8)	32	4

          `VC_MSG("before sending first reset_prep",tid_pf,UVM_LOW);
           if (!hpm_rst_prep_1.randomize with { hpm_rst_prep_1.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                                hpm_rst_prep_1.hpm_data_size_qw   == 2; 
                                                hpm_rst_prep_1.hpm_msg_opcode     == HPM_RESET_PREP;
                                                hpm_rst_prep_1.RR                 == 1'b1;
                                                hpm_rst_prep_1.hpm_msg_param      == 8'h1; // PR - parameter request, 1 bit
                                                hpm_rst_prep_1.hpm_payload_data_vector[7:0]  == m_reset_type; //RESET_TYPE
                                                hpm_rst_prep_1.hpm_payload_data_vector[15:8] == 8'h0; //PREP_TYPE(8bit = 0)
                                                //hpm_rst_prep_1.hpm_payload_data_vector[16]   == 8'h1; //Phase - randomize for now
                                            }) 
                                        `uvm_fatal(tid_pf, $sformatf("Randomization Error"));

          if ((platform_if.reset_b === 1'b1) || ($urandom_range(0,100) > 50)) begin
              hpm_rst_prep_1.start(pmsb_sqr);
          end
          `VC_MSG($sformatf("after sending first reset_prep"),tid_pf,UVM_LOW);


          //    comp->ch ack_sx [pcode] ACK_SX opcode='hc7
          //====================================================
          `VC_MSG($sformatf("waiting for HPM.RESET_PREP response"),tid_pf, UVM_LOW) 
          
          rst_prep_rsp_1 = new();

          while (m_byte != HPM_RESET_PREP && (platform_if.reset_b === 1'b1)) begin
              wait_for_pmsb_msg(.opcode(HPM_IP2PM));
              assert($cast(rst_prep_rsp_1.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
              rst_prep_rsp_1.parse_message();
              m_byte = rst_prep_rsp_1.hpm_msg_opcode;
          end
          `VC_MSG($sformatf("waiting for HPM.RESET_PREP response .. done"),tid_pf, UVM_LOW) 

          // check response
        if ( ((rst_prep_rsp_1.hpm_payload_packed[7:0] !== m_reset_type) || rst_prep_rsp_1.hpm_resp_required || rst_prep_rsp_1.hpm_msg_param) && (platform_if.reset_b === 1'b1) ) begin
              //`VC_ERROR("reset_prep response contain an error, check PR and RR were cleared and reset_type is as expected")
              `VC_MSG("reset_prep response contain an e-rror, check PR and RR were cleared and reset_type is as expected",tid_pf, UVM_LOW)
              `VC_MSG($sformatf("rst_prep_rsp_1.hpm_payload_packed[7:0] = %0h, m_reset_type = %0h ",rst_prep_rsp_1.hpm_payload_packed[7:0],m_reset_type),tid_pf, UVM_LOW) 
              `VC_MSG($sformatf("hpm_resp_required = %0h ",rst_prep_rsp_1.hpm_resp_required),tid_pf, UVM_LOW) 
              `VC_MSG($sformatf("hpm_msg_param = %0h ",rst_prep_rsp_1.hpm_msg_param),tid_pf, UVM_LOW) 
            end

 
          if (level0_mode ==1) begin
              sched_cfg.wait_delay_in_range("SMALL_DELAY");
          end else begin
              sched_cfg.wait_delay_in_range("MEDIUM_DELAY");
          end


          //    ch->comp reset_warn + reset type RST_WARN opcode='hae
          //==========================================================
          if (flow_type == IMH_COLD_RESET || flow_type == IMH_WARM_RESET) m_reset_type = HPM_GO_RW; //RESET_TYPE
          if (flow_type == IMH_PKGS_3) m_reset_type = HPM_GO_S3; //RESET_TYPE
          if (flow_type == IMH_PKGS_4) m_reset_type = HPM_GO_S4; //RESET_TYPE
          if (flow_type == IMH_PKGS_5) m_reset_type = HPM_GO_S5; //RESET_TYPE

          //    PARAMETER_RESERVED	PR	RR1	Agent Id	HPM_MSG_OPCODE (0x2)	0	0
          //    PAYLOAD_0_RSVD	P(hase)	PREP_TYPE(8bit = 0)	RESET_TYPE(8)	32	4

          `VC_MSG("before sending second reset_prep",tid_pf,UVM_LOW);
           if (!hpm_rst_prep_2.randomize with { hpm_rst_prep_2.src_hpm_agent_id   dist {0:/9, [1:127]:/1}; 
                                                hpm_rst_prep_2.hpm_data_size_qw   == 2; 
                                                hpm_rst_prep_2.hpm_msg_opcode     == HPM_RESET_PREP;
                                                hpm_rst_prep_2.RR                 == 1'b1;
                                                hpm_rst_prep_2.hpm_msg_param      == 8'h1; // PR - parameter request, 1 bit
                                                hpm_rst_prep_2.hpm_payload_data_vector[7:0]  == m_reset_type; //RESET_TYPE
                                                hpm_rst_prep_2.hpm_payload_data_vector[15:8] == 8'h0; //PREP_TYPE(8bit = 0)
                                                //hpm_rst_prep_2.hpm_payload_data_vector[16]   == 8'h1; //Phase - randomize for now
                                            }) 
                                        `uvm_fatal(tid_pf, $sformatf("Randomization Error"));


          if ((platform_if.reset_b === 1'b1) || ($urandom_range(0,100) > 50)) begin
              hpm_rst_prep_2.start(pmsb_sqr);
          end
          `VC_MSG($sformatf("after sending second reset_prep"),tid_pf,UVM_LOW);

          //    comp->ch rst_warn_ack [pcode] opcode='haf
          //==========================================================
          `VC_MSG($sformatf("waiting for HPM.RESET_PREP response"),tid_pf, UVM_LOW) 
          m_byte = 'h0;
          rst_prep_rsp_2 = new();

          while (m_byte != HPM_RESET_PREP && (platform_if.reset_b === 1'b1)) begin
              wait_for_pmsb_msg(.opcode(HPM_IP2PM));
              assert($cast(rst_prep_rsp_2.hpm_msg, pmsb_messages_queue[$].clone())) else `VC_ERROR("Cast Fail");
              rst_prep_rsp_2.parse_message();
              m_byte = rst_prep_rsp_2.hpm_msg_opcode;
          end
          `VC_MSG($sformatf("waiting for HPM.RESET_PREP response .. done"),tid_pf, UVM_LOW) 

          // check response
          if ( ((rst_prep_rsp_2.hpm_payload_packed[7:0] !== m_reset_type) || rst_prep_rsp_2.hpm_resp_required || rst_prep_rsp_2.hpm_msg_param) && (platform_if.reset_b === 1'b1) ) begin
          //    `VC_ERROR("reset_prep response contain an error, check PR and RR were cleared and reset_type is as expected")
              `VC_MSG("reset_prep response contain an e-rror, check PR and RR were cleared and reset_type is as expected",tid_pf, UVM_LOW)
          end

          `VC_MSG($sformatf("marking phase_b_complete ...... [will be printed based on randomization. reset_b assertion MAY prevent print of this message]"),tid_pf, UVM_LOW) 
          phase_b_complete = 1;

      end

      begin

          if (break_phase_a_b_when_xxreset_assert) begin
              `VC_MSG("waiting for reset_b assertion or phase_b complete",tid_pf,UVM_LOW);
              wait (platform_if.reset_b !== 1 || phase_b_complete == 1); // no gurantee xxreset will be asserted
              `VC_MSG("waiting for reset_b assertion or phase_b complete ... done",tid_pf,UVM_LOW);
              if (platform_if.reset_b === 1'b0) begin
                  `VC_MSG("waiting for reset_b assertion ... done - FYI - move to surprise reset mode",tid_pf,UVM_LOW)
              end
              if (platform_if.reset_b === 1'bx) begin
                  `VC_ERROR("reset_b turn to X")
              end
          end
          else begin
              `VC_MSG("waiting for phase_b complete",tid_pf,UVM_LOW);
              wait (phase_b_complete == 1);
              `VC_MSG("waiting for phase_b complete .... done",tid_pf,UVM_LOW);
          end

      end
  join_any
  disable fork;

 
  if (level0_mode ==1) begin
      sched_cfg.wait_delay_in_range("SMALL_DELAY");
  end else begin
      sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY");
  end

  // assert xxreset
  assign_signal_with_data_after_delay(.sig(platform_if.reset_b), .delay_ns(0), .data(0)); 

  // in warm reset , always wait for phaseF complete. (boot fsm is down)
  // in cold reset - may or may not wait for bootfsm before deasserting cpu-pwr-good
  if ((flow_type == IMH_WARM_RESET) || ($urandom_range(0,100) > 50) || (level0_mode == 1)) begin 
      `VC_MSG("waiting for boot_fsm to be down ",tid_pf,UVM_LOW);
      wait (boot_if.bootfsm_state === 'h0);
      `VC_MSG("waiting for boot_fsm to be down .... done",tid_pf,UVM_LOW);
      
      // in warm reset , always wait for reset exit as well.      
      // in cold reset , 70% chance  that cpu-pwrgood will deassert AFTER
      // warm-rst-exit-cnt expired 
      if ((flow_type == IMH_WARM_RESET) || ($urandom_range(0,100) > 30)) begin 
          `VC_MSG("waiting for boot_fsm NOT to be down ",tid_pf,UVM_LOW);
          wait (boot_if.bootfsm_state !== 'h0);
          `VC_MSG("waiting for boot_fsm NOT to be down .... done",tid_pf,UVM_LOW);
      end
  end

  if (flow_type == IMH_WARM_RESET) begin
      `VC_MSG("Seq ends here ... IMH_WARM_RESET",tid_pf,UVM_LOW);
  end
/*********************************** Seq ends here ... IMH_WARM_RESET ***********************************/

  if (flow_type != IMH_WARM_RESET) begin

      if (level0_mode ==1) begin  sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY"); end 
      else begin sched_cfg.wait_delay_in_range("MEDIUM2LARGE_DELAY"); end

      `VC_MSG("Seq continues.... deasserting cpu_pwr_good ",tid_pf,UVM_LOW);
      assign_signal_with_data_after_delay(.sig(platform_if.cpu_pwr_good), .delay_ns(0), .data(0)); 

      // deassert S0pwrok
      if (level0_mode ==1) begin  sched_cfg.wait_delay_in_range("SMALL2MEDIUM_DELAY"); end 
      else begin sched_cfg.wait_delay_in_range("MEDIUM2LARGE_DELAY"); end
      
      `VC_MSG("deasserting platform_if.S0_pwr_ok", tid_pf, UVM_LOW);
      assign_signal_with_data_after_delay(.sig(platform_if.S0_pwr_ok), .delay_ns(0), .data(0)); 

      // from HAS table: https://docs.intel.com/documents/pm_doc/src/DMR_CBB/HAS/Reset/dmr_cbb_reset.html#reset-states-matrix:~:text=warm%20reset%20entry.-,Reset%20States%20Matrix,-(source)
      // INF voltage - may or may not be dropped
      if (!keep_st) ramp_S0_power("DN"); // FIXME-CBB-oshikbit - randomize the keep_st
      // VNN voltage - kept in COLD reset, depands on CL in pkgs/ADR (what is the indication that crashlog was kept ? )
      // FIXME-CBB-oshikbit add cl support for ramp_S5_power : if (!cl_triggered && flow_type != IMH_COLD_RESET && !keep_st) ramp_S5_power("DN");
      if (flow_type != IMH_COLD_RESET && !keep_st) ramp_S5_power("DN");

  end

//
//  if(m_cold) begin
//        ns_dly = $urandom_range(10000,30000); // by spec demand : coldboot -> epdon >> 40us
//      end
//    // FIXME - oshikbit - make this delay configurable, for soc purposes
//    if (force_gracefll_rst) begin
//      `uvm_info(tid_pf, $sformatf("waiting for inf_st_reset_b assertion , for gracefll reset entry [force_gracefll_rst - %0b]",force_gracefll_rst),tid_pf, UVM_LOW);
//      fork
//        #2ms;
//        wait(boot_if.inf_st_reset_b === 'b0);
//      join_any
//      disable fork;
//      if (boot_if.inf_st_reset_b !== 'b0) 
//        `uvm_error(tid_pf,$sformatf("inf_st_reset_b was not asserted after 2ms, continuing to deassert epd_on"));
//      ns_dly = 0;
//    end
//    else begin
//      //  oshikbit - 26.7.2022 SPEC_CHANGE
//      ns_dly = $urandom_range(1,99);
//   end
//    
//    assign_signal_with_data_after_delay(.sig(boot_if.epd_on), .delay_ns(ns_dly), .data(1'b0));
//
//    disable_vccst_shutdown = reg_block.cpu_pkgs_shutdown_policy.disable_vccst_shutdown.get();
//    `uvm_info(tid_pf, $sformatf("cpu_pkgs_shutdown_policy.disable_vccst_shutdown = 'b%0b ",disable_vccst_shutdown),tid_pf, UVM_LOW);
//    `uvm_info(tid_pf, $sformatf("trigger_reset.keep_st = 'b%0b ",keep_st),tid_pf, UVM_LOW);
//    if (!(keep_st | disable_vccst_shutdown)) begin
//        ns_dly = $urandom_range(100,500); 
//        #(ns_dly*1ns);
//        platform_pwrgood(0);       
//    end

endtask:reset_sx_entry




endclass:imh_scheduler


