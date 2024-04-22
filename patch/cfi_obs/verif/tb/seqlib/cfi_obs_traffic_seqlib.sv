// -------------------------------------------------------------------------
//   file:     cfi_obs_traffic_seqlib.sv
//   Date Created  : 2021
//   Author        : yuvalman
//   Project       : CFI_OBS IP
// -------------------------------------------------------------------------
// Section: CFI_OBS traffics seq
//
// This file include all the CFI_OBS traffic sequences.
//
// The sequences use RAL and SM to generate traffic to the DUT
//
// -------------------------------------------------------------------------
class cfi_obs_patgen_traffic_seq extends cfi_obs_config_base_seq;

    `uvm_object_utils (cfi_obs_patgen_traffic_seq)
    `uvm_declare_p_sequencer (slu_sequencer)
    `define NUM_OF_PATGEN_TXN 5
    uvm_reg_data_t reg_read_val;
    string block_name[] = {"rx_dso", "tx_dso"};
    virtual dtf_vc_if m_dtf_if[string];
    bit timeout_occurred;
    int rand_delay = 0;

    // new //
    function new(input string name = "cfi_obs_patgen_traffic_seq", uvm_sequencer_base sequencer = null, uvm_sequence parent_seq = null);
        super.new(name, sequencer, parent_seq);
        m_dtf_if["rx_dso"] = _cfi_obs_env.rx_dtf_vc_out.dtf_if;
        m_dtf_if["tx_dso"] = _cfi_obs_env.tx_dtf_vc_out.dtf_if;
    endfunction

    function compare_data (bit toggle_bit,bit [2:0] i_pattern_mode,[63:0] cnt,bit [63:0] lta_mode_val,bit [63:0] leading_one, bit [63:0] actual_payload, string dtf_name);
        bit [63:0] payload;

        case ( {i_pattern_mode,toggle_bit})
            4'b0000 : payload = 64'b0;
            4'b0001 : payload = 64'b0;
            4'b0010 : payload = 64'hffffffffffffffff;
            4'b0011 : payload = 64'hffffffffffffffff;
            4'b0100 : payload = 64'haaaaaaaaaaaaaaaa;
            4'b0101 : payload = 64'haaaaaaaaaaaaaaaa;
            //FIXME
            //should change it to atomic pkt
            4'b0110 : payload = lta_mode_val;
            4'b0111 : payload = lta_mode_val;
            4'b1000 : payload = 64'h0000000000000000;
            4'b1001 : payload = 64'hffffffffffffffff;
            4'b1010 : payload = 64'h5555555555555555;
            4'b1011 : payload = 64'haaaaaaaaaaaaaaaa;
            4'b1100 : payload = cnt;
            4'b1101 : payload = cnt;
            4'b1110 : payload = leading_one;
            4'b1111 : payload = leading_one;
        endcase

        $display("entering compare %t",$time);
        if(payload!= actual_payload) begin
            `uvm_error(get_name(), $sformatf("DTF %0s patgen data ERROR  expected %0h while recieved %0h",dtf_name,payload, actual_payload));
        end
        else begin
            `uvm_info(get_name(), $sformatf("DTF %0s patgen - Great Compare! expected = %0h actual = %0h",dtf_name, payload, actual_payload), UVM_LOW);
        end

    endfunction: compare_data

    task body();

        super.body();
        fork
            begin //config task
                foreach(block_name[block]) begin
                    `slu_msg (UVM_LOW, get_name(), ("Writing 28 to %0s",block_name[block]));
                    ral_utils_uvm.write_reg(.caller_info(`caller_info),
                        .block_name(block_name[block]),
                        .reg_name("DSO_DTF_ENCODER_CONFIG_REG"),
                        .val(32'h28),
                        .access_path("sideband"),
                        .path(UVM_FRONTDOOR),
                        .parent(this));
                    // Read
                    ral_utils_uvm.read_reg(.caller_info(`caller_info),
                        .block_name(block_name[block]),
                        .reg_name("DSO_DTF_ENCODER_CONFIG_REG"),
                        .val(reg_read_val),
                        .access_path("sideband"),
                        .path(UVM_FRONTDOOR),
                        .parent(this));
                    if (reg_read_val != 32'h28)
                        `slu_error(get_name(), ("For %0s.DSO_DTF_ENCODER_CONFIG_REG value miss-match. Expected 32'h28 and actual is %0h", block_name[block],reg_read_val))

                        #1000;
                    `slu_msg (UVM_LOW, get_name(), ("Writing 2C to %0s", block_name[block]));
                    ral_utils_uvm.write_reg(.caller_info(`caller_info),
                        .block_name(block_name[block]),
                        .reg_name("DSO_DTF_ENCODER_CONFIG_REG"),
                        .val(32'h2C),
                        .access_path("sideband"),
                        .path(UVM_FRONTDOOR),
                        .parent(this));

                    // Read
                    ral_utils_uvm.read_reg(.caller_info(`caller_info),
                        .block_name(block_name[block]),
                        .reg_name("DSO_DTF_ENCODER_CONFIG_REG"),
                        .val(reg_read_val),
                        .access_path("sideband"),
                        .path(UVM_FRONTDOOR),
                        .parent(this));
                    if (reg_read_val != 32'h2C)
                        `slu_error(get_name(), ("For %0s.DSO_DTF_ENCODER_CONFIG_REG value miss-match. Expected 32'h28 and actual is %0h", block_name[block],reg_read_val))

                    end
                end //config task
        join_none
        fork
            begin //checking task
                foreach(block_name[i]) begin
                    automatic string dtf_string = block_name[i];
                    `uvm_info(get_name(), $sformatf("Checking task for %s", dtf_string), UVM_LOW);
                    fork
                        begin

                            bit [5:0] txn_type;
                            bit [63:0] lta_mode_val;
                            bit [2:0] pattern_mode;
                            int patgen_cnt;
                            bit toggle_bit = 0;
                            bit [63:0] pattern_data;
                            bit [63:0] cnt = 0;

                            forever begin
                                @(m_dtf_if[dtf_string].monitor_cb);
                                if(m_dtf_if[dtf_string].monitor_cb.valid) begin
                                    if (m_dtf_if[dtf_string].monitor_cb.data != 64'h5555555555555555 && patgen_cnt == 0) begin
                                        continue;
                                    end
                                    pattern_mode = 3'b101;
                                    pattern_data = 64'h5555555555555555;
                                    lta_mode_val = 0;

                                    compare_data(toggle_bit,pattern_mode,cnt,lta_mode_val,'h0,m_dtf_if[dtf_string].monitor_cb.data,dtf_string);
                                    toggle_bit = ~toggle_bit;
                                    pattern_data = ~pattern_data;
                                    patgen_cnt = patgen_cnt+1;
                                    `uvm_info(get_name(), $sformatf("patgen_cnt %0d for %s", patgen_cnt, dtf_string), UVM_LOW);

                                    if(patgen_cnt==`NUM_OF_PATGEN_TXN) begin
                                        `uvm_info(get_name(), $sformatf("Checking task Finished for %s", dtf_string), UVM_LOW);
                                        break;
                                    end
                                end //if valid
                            end //forever
                        end //begin
                    join_none
                end //foreach
                wait fork;
            end //checking task

            begin //timeout task
                #3us;
                `uvm_info(get_name(), $sformatf("Timeout !!!"), UVM_LOW);
                timeout_occurred = 1;
            // Uncomment when DTF will be ready              `uvm_error(get_name(), $sformatf("Not all ", actual_payload));
            end
        join_any
        if (timeout_occurred) begin
            `slu_error(get_name(), ("Timeout occurred! "))
        end

    endtask

endclass : cfi_obs_patgen_traffic_seq

//----------------------------------------------------------------------
class cxm_traffic_seq extends cfi_obs_base_seq;
    cxm_vc_common_pkg::cxm_vc_command_item cxm_item;
    rand int num_of_txns_to_send;
    rand bit randomize_data_in_seq;
    rand bit b2b_vc_id;
    rand bit direct_filter_en;



    `uvm_object_utils_begin(cxm_traffic_seq)
    `uvm_object_utils_end

    constraint num_of_txns_to_send_c {soft num_of_txns_to_send == 30;};
    constraint b2b_vc_id_c {soft b2b_vc_id == 1'b0;};
    constraint direct_filter_en_c {soft direct_filter_en == 1'b0;}; 

    // ----------------------------------------------------------
    task send_random_req_transactions(ref uvm_sequencer_base seqr,IfType it);
        cxm_txn_type_e txn_t = (it == cfi_vc_common_pkg::CFI_REQ)? CXM_REQ:CXM_RWD;
        //repeat(num_of_txns_to_send) begin
        int rspid = $urandom_range(6,0);
        int dstid = $urandom_range(6,0);
        if (((txn_t == CXM_REQ) && (b2b_vc_id ==1'b1)) || (b2b_vc_id ==1'b0)) begin
            //create sequence item with factory
            `uvm_create_on(cxm_item,seqr);
            cxm_item.randomize() with {
                txn_type == txn_t;
                RspID == rspid;
                DstID == dstid;
                b2b_vc_id -> VCID == 0;
                direct_filter_en -> sys_address == 'hcd54ee45100;
            };
            //send to sequencer
            if (!env_if.stop_data) begin
                `uvm_send(cxm_item);
            end 
        end
    endtask

    task send_txn_on_seq(IfType it,int num, uvm_sequencer_base seq);
        fork
            repeat(num_of_txns_to_send) begin
                send_random_req_transactions(seq, it);
            end

        join
    endtask

    task send_on_all_sequencers();
        uvm_sequencer_base seqr;
        seqr = slu_sequencer::pick_sequencer("CXM_VC_REQUESTOR");
        foreach (_cfi_obs_env.tx_cfi_vc_agent_l[idx]) begin
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++) begin
                send_txn_on_seq(cfi_vc_common_pkg::CFI_REQ,i, seqr);
            end
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++) begin
                send_txn_on_seq(cfi_vc_common_pkg::CFI_DATA,i, seqr);
            end
        end

    //#1000ns;
    endtask

    // ----------------------------------------------------------
    task body();
        super.body();
        send_on_all_sequencers();
        wait_for_idle_cfi(1'b1);
    endtask
    // ----------------------------------------------------------
    function new(string name = "");
        super.new(name);
    endfunction

endclass : cxm_traffic_seq

//----------------------------------------------------------------------
class upi_traffic_seq extends cfi_obs_base_seq;

    uxi::CohSequence coh_upi_seq;
    uxi::NcSequence  nc_upi_seq;
    rand bit b2b_vc_id;
    rand bit direct_filter_en;

    constraint b2b_vc_id_c {soft b2b_vc_id == 1'b0;};
    constraint direct_filter_en_c {soft direct_filter_en == 1'b0;};

    `uvm_object_utils_begin(upi_traffic_seq)
    `uvm_object_utils_end
    // ----------------------------------------------------------
    virtual task body();
        super.body();
        if (b2b_vc_id == 1'b0) begin
            if (!env_if.stop_data) begin
                `uvm_do_on_with(coh_upi_seq, _cfi_obs_env.upi_bfm.sequencer, {
                        source_id inside {7,8};
                        //address[46:6] inside {41'hdeadbeaf,41'hdeadbe00,41'hdeadbea0};
                        (direct_filter_en == 1'b1) ? address == 'h44dd9933c0 : address[46:6] inside {41'hdeadbeaf,41'hdeadbe00,41'hdeadbea0};
                    })
            end 
            if (!env_if.stop_data) begin
                `uvm_do_on_with(nc_upi_seq, _cfi_obs_env.upi_bfm.sequencer, {
                        p2p_msg_type inside {upi_spec::IOSF_Posted_Short,upi_spec::IOSF_NonPosted_Short,upi_spec::IOSF_Cmp_Short,upi_spec::P2P_Generic_Short};
                        source_id inside {10};
                        destanation_id inside {11};
                    //b2b_vc_id -> opcode inside {upi_bfm::NcP2pRdS};
                    //b2b_vc_id -> vc_id == 0;
                    //                source_id != destanation_id;
                    })
            end 
            `slu_msg (UVM_LOW, get_name(), ("WAITING "));
        end 
        //#60000000;
        
    //    env.upi_bfm.wait_empty();
    endtask : body
endclass : upi_traffic_seq

class random_cfi_seq extends cfi_obs_base_seq;

    cfi_vc_command_item cfi_item;
    rand int num_of_cfi_txns_to_send;
    rand int CFI_VC;
    rand bit b2b_vc_id;


    uvm_sequencer_base cfi_sequencers_list[string][IfType][int];

    constraint b2b_vc_id_c {soft b2b_vc_id == 1'b0;};

    `uvm_object_utils_begin(random_cfi_seq)
    `uvm_object_utils_end
    `uvm_declare_p_sequencer(slu_sequencer)


    constraint num_of_cfi_txns_to_send_c {soft num_of_cfi_txns_to_send < 25 && num_of_cfi_txns_to_send> 5;};

    // ----------------------------------------------------------

    //***************************************************************
    // task: send_on_all_cfi_sequencers
    //***************************************************************
    task send_on_all_cfi_sequencers();
//        foreach (_cfi_obs_env.rx_cfi_vc_agent_l[idx]) begin
//            cfi_vc_agents_list[{"CFI_VC_RX",$psprintf("%0d",idx)}][idx] = _cfi_obs_env.rx_cfi_vc_agent_l[idx];
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_REQ,i);
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_RSP,i);
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_DATA,i);
//        end

        foreach (_cfi_obs_env.tx_cfi_vc_agent_l[idx]) begin
            cfi_vc_agents_list[{"CFI_VC_TX",$psprintf("%0d",idx)}][idx] = _cfi_obs_env.tx_cfi_vc_agent_l[idx];
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++)
                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_REQ,i);
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_RSP,i);
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_DATA,i);
        end

//        foreach (_cfi_obs_env.rx_cfi_vc_agent_l[idx]) begin
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++)
//                send_txn_on_seq({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_REQ,i,idx);
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
//                send_txn_on_seq({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_RSP,i,idx);
//            for(int i = 0; i < _cfi_obs_env.rx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
//                send_txn_on_seq({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_DATA,i,idx);
//        end

        foreach (_cfi_obs_env.tx_cfi_vc_agent_l[idx]) begin
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++) begin
                if (b2b_vc_id == 1'b0)
                    send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_REQ,i,idx);
            end
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
                send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_RSP,i,idx);
            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
                send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_DATA,i,idx);
        end

    endtask
    //***************************************************************
    // Function: assign_cfi_sequencer
    //***************************************************************
    function void assign_cfi_sequencer(string agent_name, IfType it,int num);
        string name = {agent_name,it.name(),$psprintf("%0d",num)};
        cfi_sequencers_list[agent_name][it][num] = slu_sequencer::pick_sequencer(name);
    endfunction : assign_cfi_sequencer
    //***************************************************************
    // task: send_txn_on_seq
    //***************************************************************
    task send_txn_on_seq(string agent_name, IfType it,int num, int idx);
        uvm_sequencer_base seqr = cfi_sequencers_list[agent_name][it][num];
        cfi_vc_agent agent = cfi_vc_agents_list[agent_name][idx];
        fork
            repeat(num_of_cfi_txns_to_send) begin
                send_random_cfi_transactions(seqr, it, agent);
            end
        join
    endtask : send_txn_on_seq
    //***************************************************************
    // task: send_random_cfi_transactions
    //***************************************************************
    task send_random_cfi_transactions(ref uvm_sequencer_base seqr, IfType it, cfi_vc_agent cfi_agent);
        bit wr_req_ = 1;//0;
        // inject only IDI
        int i_vc_id = 0;// = $urandom_range(cfi_agent.cfg.HIGHEST_VC_ID_USED,0);
        int i_protocol_id = 0;//$urandom_range(cfi_agent.cfg.HIGHEST_PROTOCOL_ID_USED,0);
        int i_dst_id = $urandom_range(2**cfi_agent.if_param_container.DSTID_MSB -1,0);
        int i_rctrl = $urandom_range(3,0);
        int i_trace_packet = $urandom_range(1,0);
        if (it == CFI_REQ)
            i_vc_id = $urandom_range(3,2);
        if (b2b_vc_id)
            i_vc_id = 0;
        `slu_msg (UVM_LOW, get_name(), ("sent txns %s, number of txn = %0d",seqr.get_full_name(), num_of_cfi_txns_to_send));
        //create sequence cfi_item with factory
        `uvm_create_on(cfi_item,seqr);

        // IDI has only 2 pumps data packets
        if (it == CFI_DATA) begin
            cfi_item.payload = new[2];
            cfi_item.header = new[2];
            cfi_item.header_parity = new[2];
        end
        else begin
            cfi_item.payload = new[1];
            cfi_item.header = new[1];
            cfi_item.header_parity = new[1];
        end 
        void'(cfi_item.randomize() with {
                vc_id == i_vc_id;
                protocol_id == i_protocol_id;
                dst_id == i_dst_id;
                rctrl == i_rctrl;
                trace_packet == i_trace_packet;
                foreach(payload[i]) payload[i] inside {[0:'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]};                
                foreach(header[i]) header[i] inside {[0:'hFFFFFFFFF]};            
                foreach(header_parity[i]) header_parity[i] inside {1};});

        `slu_msg (UVM_LOW, get_name(), ("sent item %0s",seqr.get_full_name()));
        if (!env_if.stop_data) begin
            `uvm_send(cfi_item);
        end 
    endtask : send_random_cfi_transactions


    // ----------------------------------------------------------
    task body();
        super.body();
        send_on_all_cfi_sequencers();
        wait_for_idle_cfi(1'b1);
        `slu_msg (UVM_LOW, get_name(), ("finish to send CFI transactions"));
    endtask

    function new(string name = "");
        super.new(name);
    endfunction
endclass

class cfi_obs_traffic_seq extends cfi_obs_base_seq;
    `uvm_object_utils(cfi_obs_traffic_seq)
    `uvm_declare_p_sequencer (slu_sequencer)  
    
    random_cfi_seq    cfi_traffic_seq;       
    cxm_traffic_seq   i_cxm_traffic_seq; 
    upi_traffic_seq   i_upi_traffic_seq;
    rand int          repeats;
    bit               b2b_vc_id_test;
    bit               direct_filter_test;

    constraint repeats_c {
        soft repeats inside {[5:10]};
    };
    
    // ----------------------------------------------------------
    function new(string name="cfi_obs_traffic_seq");
        super.new(name);
    endfunction : new
    
    // ----------------------------------------------------------
    virtual task body();
        super.body();
        `slu_msg(UVM_NONE,get_name(),("Running traffic sequence %0d times", repeats));
        b2b_vc_id_test = _cfi_obs_env.stress_picker.cfi_obs_b2b_vc_id_test_en;
        direct_filter_test = _cfi_obs_env.stress_picker.cfi_obs_direct_filter_en;
        fork
            for(int i = 0; i < repeats; i++) begin
                `uvm_do_with(cfi_traffic_seq,{b2b_vc_id_test -> b2b_vc_id==1'b1;});
            end
            for(int i = 0; i < repeats; i++) begin
                `uvm_do_with(i_cxm_traffic_seq,{b2b_vc_id_test -> b2b_vc_id==1'b1; direct_filter_test -> direct_filter_en == 1'b1;});
            end
            for(int i = 0; i < (repeats/2); i++) begin
                `uvm_do_with(i_upi_traffic_seq,{b2b_vc_id_test -> b2b_vc_id==1'b1; direct_filter_test -> direct_filter_en == 1'b1;});
            end
        join
    endtask : body
endclass : cfi_obs_traffic_seq


//class direct_cfi_seq extends cfi_obs_base_seq;
//
//    cfi_vc_command_item cfi_item;
//    rand int num_of_cfi_txns_to_send;
//    rand int CFI_VC;
//
//
//    uvm_sequencer_base cfi_sequencers_list[string][IfType][int];
//
//    `uvm_object_utils_begin(random_cfi_seq)
//    `uvm_object_utils_end
//    `uvm_declare_p_sequencer(slu_sequencer)
//
//
//    constraint num_of_cfi_txns_to_send_c {soft num_of_cfi_txns_to_send < 25 && num_of_cfi_txns_to_send> 5;};
//
//    // ----------------------------------------------------------
//
//    //***************************************************************
//    // task: send_on_all_cfi_sequencers
//    //***************************************************************
//    task send_on_all_cfi_sequencers();
//
//        foreach (_cfi_obs_env.tx_cfi_vc_agent_l[idx]) begin
//            cfi_vc_agents_list[{"CFI_VC_TX",$psprintf("%0d",idx)}][idx] = _cfi_obs_env.tx_cfi_vc_agent_l[idx];
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_REQ,i);
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_RSP,i);
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
//                assign_cfi_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_DATA,i);
//        end
//
//        foreach (_cfi_obs_env.tx_cfi_vc_agent_l[idx]) begin
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.REQ_TX; i++)
//                send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_REQ,i,idx);
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.RSP_TX; i++)
//                send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_RSP,i,idx);
//            for(int i = 0; i < _cfi_obs_env.tx_cfi_vc_agent_l[idx].cfg.DATA_TX; i++)
//                send_txn_on_seq({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_DATA,i,idx);
//        end
//
//    endtask
//    //***************************************************************
//    // Function: assign_cfi_sequencer
//    //***************************************************************
//    function void assign_cfi_sequencer(string agent_name, IfType it,int num);
//        string name = {agent_name,it.name(),$psprintf("%0d",num)};
//        cfi_sequencers_list[agent_name][it][num] = slu_sequencer::pick_sequencer(name);
//    endfunction : assign_cfi_sequencer
//    //***************************************************************
//    // task: send_txn_on_seq
//    //***************************************************************
//    task send_txn_on_seq(string agent_name, IfType it,int num, int idx);
//        uvm_sequencer_base seqr = cfi_sequencers_list[agent_name][it][num];
//        cfi_vc_agent agent = cfi_vc_agents_list[agent_name][idx];
//        fork
//            repeat(num_of_cfi_txns_to_send) begin
//                send_direct_cfi_transactions(seqr, it, agent, );
//            end
//        join
//    endtask : send_txn_on_seq
//    //***************************************************************
//    // task: send_random_cfi_transactions
//    //***************************************************************
//    task send_direct_cfi_req_transactions(ref uvm_sequencer_base seqr, cfi_vc_agent cfi_agent, int i_protocol_id );
//        bit wr_req_ = 1;//0;
//        int i_vc_id;
//        int i_dst_id = $urandom_range(2**cfi_agent.if_param_container.DSTID_MSB -1,0);
//        int i_rctrl = $urandom_range(3,0);
//        int i_trace_packet = $urandom_range(1,0);
//        case (i_protocol_id)
//            0 : i_vc_id = $urandom_range(3,2); //IDI.C
//            1 : i_vc_id = $urandom_range(5,4); //UPI.C
//            2 : i_vc_id = $urandom_range(1,0); //CXM
//        endcase
//
//        case (i_protocol_id)
//            0 : i_vc_id = $urandom_range(3,2); //IDI.C
//            1 : i_vc_id = $urandom_range(5,4); //UPI.C
//            2 : i_vc_id = $urandom_range(1,0); //CXM
//        endcase
//        //create sequence cfi_item with factory
//        `uvm_create_on(cfi_item,seqr);
//        cfi_item.payload = new[1];
//        cfi_item.header = new[1];
//        
//        cfi_item.header_parity = new[1];
//        void'(cfi_item.randomize() with {
//                vc_id == i_vc_id;
//                protocol_id == i_protocol_id;
//                dst_id == i_dst_id;
//                rctrl == i_rctrl;
//                trace_packet == i_trace_packet;
//                foreach(payload[i]) payload[i] inside {[0:'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]};                
//                foreach(header[i]) header[i] inside {[0:'hFFFFFFFFF]};            
//                foreach(header_parity[i]) header_parity[i] inside {1};});
//
//        `slu_msg (UVM_LOW, get_name(), ("sent item %0s",seqr.get_full_name()));
//        `uvm_send(cfi_item);
//    endtask : send_random_cfi_transactions


class cfi_obs_warm_reset_traffic_seq extends cfi_obs_base_seq;
    `uvm_object_utils(cfi_obs_warm_reset_traffic_seq)
    `uvm_declare_p_sequencer ( slu_sequencer)
   
    cfi_obs_traffic_seq        traffic_seq; 
    cfi_obs_enter_reset_seq    enter_reset;
    cfi_obs_end_reset_seq      end_reset;
    cfi_obs_config_seq         config_seq;    
    
    
    rand int first_num_of_packets;
    rand int second_num_of_packets;
    bit reset_done = 0;
    int reset_delay;    
    event reset_injecting ;
    // ----------------------------------------------------------
    function new(string name="cfi_obs_warm_reset_traffic_seq");
        super.new(name);
    endfunction : new

    // ----------------------------------------------------------
    task body();   
        
        `slu_msg (UVM_LOW, get_name(), ("CFI_OBS_DBG: starting cfi_obs_warm_reset_traffic_seq"))
        fork : data_vs_reset_injection
            begin : data_driving_until_reset
                fork : data_vs_reset_monitor
                //`CFI_OBS_BEGIN_FIRST_OF
                    begin
                        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start first trace session"));
                        `uvm_do(traffic_seq);
                        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("First trace session is done"));
                    end
                    begin
                        @(reset_injecting);
                        `slu_msg (UVM_LOW, get_name(), ("CFI_OBS_DBG: Hit reset, stopping stimuli"));
                    end
                 //`CFI_OBS_END_FIRST_OF
                join_any : data_vs_reset_monitor
                disable data_vs_reset_monitor;
            end : data_driving_until_reset

            begin : random_reset_injection
                // wait random time
                std::randomize(reset_delay) with {reset_delay inside {[200:2000]};};
                `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("waiting %0d cycles before warm_reset start", reset_delay));
                repeat(reset_delay) @(posedge env_if.cfi_obs_main_clk);
                ->reset_injecting ;
                #0;
            end : random_reset_injection
        join_any : data_vs_reset_injection
        disable data_vs_reset_injection;
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("after disabling data_vs_reset_injection"));
 
         // do reset
        `uvm_do(enter_reset);
        `uvm_do(end_reset);
                
        repeat(1) @(posedge env_if.cfi_obs_main_clk); // waiting 1 cycle for being able to send sb trans - issue when sending sb reg at the same ps or cycle that sb_rst_b is being asserted.
        

        // config seq 
//        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start config seq"));
//        `uvm_do(config_seq);
//        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Done config seq"));

        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start second trace session"));
        `uvm_do(traffic_seq);
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Second trace session is done"));    
    endtask : body
endclass :  cfi_obs_warm_reset_traffic_seq




class cfi_obs_pkgc_traffic_seq extends cfi_obs_base_seq;

    `uvm_object_utils(cfi_obs_pkgc_traffic_seq)
    `uvm_declare_p_sequencer ( slu_sequencer)

    cfi_obs_traffic_seq traffic_seq;
    cfi_obs_pkgc_seq pkgc_seq;
    //cfi_obs_config_seq          config_seq;

    bit stop_done_before_pkgc = 0;
    rand int num_of_itterations;
    bit pkgc_done = 0;
    int pkgc_delay;

    constraint num_of_itterations_c {
        soft num_of_itterations inside {[1:3]};
    }

    // ----------------------------------------------------------
    function new(string name = "cfi_obs_pkgc_traffic_seq");
        super.new(name);
    endfunction : new

    // ----------------------------------------------------------
    task body();

        for (int i = 0; i<num_of_itterations; i++) begin
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start first trace session"));
            `uvm_do(traffic_seq);
            // wait random time
            std::randomize(pkgc_delay) with {pkgc_delay inside {[100:400]};};
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("waiting %0d cycles before pkgc_seq start", pkgc_delay));
            repeat(pkgc_delay) @(posedge env_if.cfi_obs_main_clk);
            // do pkgc
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Running pkgc_seq in %0s pkgc_test_mode", _cfi_obs_env.stress_picker.cfi_obs_pkgc_test_mode.name()));
            `uvm_do_with(pkgc_seq,{cfi_obs_pm_flow==_cfi_obs_env.stress_picker.cfi_obs_pkgc_test_mode;});
        end
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start second trace session"));
        `uvm_do(traffic_seq);
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Second trace session is done"));


    endtask : body

endclass


class cfi_obs_pm_retention_traffic_seq extends cfi_obs_base_seq;

    `uvm_object_utils(cfi_obs_pm_retention_traffic_seq)
    `uvm_declare_p_sequencer ( slu_sequencer)

    cfi_obs_traffic_seq      traffic_seq;
    cfi_obs_pm_retention_seq retention_seq;
    //cfi_obs_config_seq          config_seq;

    bit stop_done_before_pkgc = 0;
    rand int num_of_itterations;
    bit pkgc_done = 0;
    int pkgc_delay;

    constraint num_of_itterations_c {
        soft num_of_itterations inside {[1:3]};
    }

    // ----------------------------------------------------------
    function new(string name = "cfi_obs_pm_retention_traffic_seq");
        super.new(name);
    endfunction : new

    // ----------------------------------------------------------
    task body();

        for (int i = 0; i<num_of_itterations; i++) begin
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start first trace session"));
            `uvm_do(traffic_seq);
            // wait random time
            std::randomize(pkgc_delay) with {pkgc_delay inside {[100:400]};};
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("waiting %0d cycles before retention_seq start", pkgc_delay));
            repeat(pkgc_delay) @(posedge env_if.cfi_obs_main_clk);
            // do pkgc
            `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Running retention_seq with abort_stage = 0")); //FIXME change to variable
            `uvm_do_with(retention_seq, {abort_stage == 0;});
        end
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Start second trace session"));
        `uvm_do(traffic_seq);
        `slu_msg (UVM_LOW, "CFI_OBS_DBG", ("Second trace session is done"));


    endtask : body

endclass : cfi_obs_pm_retention_traffic_seq

