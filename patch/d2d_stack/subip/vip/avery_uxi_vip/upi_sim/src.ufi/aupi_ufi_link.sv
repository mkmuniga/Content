/*
 * |-----------------------------------------------------------------------|
 * |                                                                       |
 * |   Copyright Avery Design Systems, Inc. 2020.			   |
 * |     All Rights Reserved.       Licensed Software.		           |
 * |                                                                       |
 * |                                                                       |
 * | THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF AVERY DESIGN SYSTEMS   |
 * | The copyright notice above does not evidence any actual or intended   |
 * | publication of such source code.				           |
 * |                                                                       |
 * |-----------------------------------------------------------------------|
 */
// $Revision: 1.53 $

`ifndef _aupi_ufi_link_sv
`define _aupi_ufi_link_sv

class aupi_ufi_link extends uvm_object;
    `include "aupi_gasket.sv"
    bit passive_mode;

    // ---- UPI ---- //
            aupi_agent     upi_agt;
	    aupi_port_id_t port_id;
            aupi_nid_t     node_id;
    virtual aupi_if        if_upi; 
            aupi_pkt       ufi_link_tx_p;
            event          ufi_link_tx_e;
            aupi_pkt       ufi_link_rx_p;
            event          ufi_link_rx_e;

    // ---- UFI ---- //
            bit [2:0]      valid_channelQ[$]; // array index mapping ufi_dev, bit 2 data, bit 1 rsp, bit 0 req
            aufi_device    ufi_dev_q[$];
            bit            is_ufi_sw;         //multi node connect to ufi
    // ---- HIOP --- //
            aupi_sid_t     stack_id;
    // ---- UVM ----
    `uvm_object_utils_begin(aupi_ufi_link)
    `uvm_object_utils_end

    function new(
	string          name    = "aupi_ufi_link",
	aupi_port_id_t  port_id = 0,
	aupi_agent      upi_agt = null,
	aufi_device     ufi_dev = null,
        bit             is_ufi_sw = 1
	);
	super.new(name);
	this.port_id = port_id;
	this.upi_agt = upi_agt;
        this.is_ufi_sw = is_ufi_sw;
        node_id = upi_agt.cfg_info.nid;
        stack_id = upi_agt.cfg_info.sid;
	if_upi  = upi_agt.upi_ifs[port_id];
	if_upi.connect_mode = AUPI_CONNECT_link_ufi;
        ufi_dev_q.push_back(ufi_dev);
        valid_channelQ.push_back(3'b111);

        //$display("%s: %s use port%d to %s",get_name(), upi_agt.get_name(), port_id, ufi_dev.get_name());
	fork
	    init_run();
	join_none
    endfunction

    local task init_run();
	fork
            trk_ufi();
	    forever proc_tx_pkt_upi2ufi();
	    proc_rx_pkt_ufi2upi();
	join
    endtask

    local task trk_ufi();
        string s;
        wait(upi_agt!=null);
        wait(upi_agt.log!=null);
        wait(upi_agt.log.trk_file_ptl!=0);
        s = $psprintf("port%0d connect ufis:", port_id);
        foreach(ufi_dev_q[i])
            s = $psprintf("%s %s(%h),", s, ufi_dev_q[i].get_name(), ufi_dev_q[i]);
        upi_agt.log.track_ptl(s);
    endtask

    local task proc_tx_pkt_upi2ufi();
        int idx2;
	aupi_pkt p;
        aufi_message msgs[$], msg_null= new();
       
        foreach(ufi_dev_q[i])
            wait (ufi_dev_q[i].istate == AUFI_ISTATE_CONED1);
	wait (if_upi.ufi_tx_pkts.size());
	p = if_upi.ufi_tx_pkts.pop_front();
        //if (ufi_dev_q[0].log.dbg_flag[AUPI_DBG_ufi])
        //    ufi_dev_q[0].log.info($psprintf("upi2ufi: %s",p.aprint(1)));
        if (!upi_agt.cfg_info.is_uxi)   upi2ufi(upi_agt, ufi_dev_q[0], p, msgs);
        else                            uxi2ufi(upi_agt, ufi_dev_q[0], p, msgs);
        foreach(msgs[i])
            p.ufi_msgs.push_back(msgs[i]);
        begin //CALLBACK
            `AUVM_CALLBACK_BFM(upi_agt, aupi_callbacks, ufi_link_tx_pkt(upi_agt, p));
            ufi_link_tx_p = p;
            ->ufi_link_tx_e;
            #1ps;
        end
        for (int i=0; i<msgs.size; i++) begin 
            if (ufi_dev_q[0].is_agent) begin
                case(1)
                    msgs[i].a2f_req.req_is_valid: begin
                        if (i==0)   idx2 = select_ufi_idx(0, p); 
                        ufi_dev_q[idx2].upi_req_pend_msgQ.push_back(msgs[i]);

                    end
                    msgs[i].a2f_data.data_is_valid: begin 
                        if (i==0)   idx2 = select_ufi_idx(2, p); 
                        ufi_dev_q[idx2].upi_data_pend_msgQ.push_back(msgs[i]);
                    end
                    msgs[i].a2f_rsp.rsp_is_valid: begin
                        if (i==0)   idx2 = select_ufi_idx(1, p); 
                        ufi_dev_q[idx2].upi_rsp_pend_msgQ.push_back(msgs[i]);
                    end
                endcase
            end else begin
                case(1)
                    msgs[i].f2a_req.req_is_valid: begin
                        if (i==0)   idx2 = select_ufi_idx(0, p); 
                        ufi_dev_q[idx2].upi_req_pend_msgQ.push_back(msgs[i]);
                    end
                    msgs[i].f2a_data.data_is_valid: begin
                        if (i==0)   idx2 = select_ufi_idx(2, p); 
                        ufi_dev_q[idx2].upi_data_pend_msgQ.push_back(msgs[i]);
                    end
                    msgs[i].f2a_rsp.rsp_is_valid: begin
                        if (i==0)   idx2 = select_ufi_idx(1, p); 
                        ufi_dev_q[idx2].upi_rsp_pend_msgQ.push_back(msgs[i]);
                    end
                endcase 
            end
        end
        if (p.mc inside {AUPI_MC_rsp2, AUPI_MC_rspd}) begin
            fork
                begin
                    foreach(msgs[i])
                        if (msgs[i]!= null)
                            wait(msgs[i].is_done);
                    p.is_done = 1;
                end
            join_none
        end
    endtask

    function int select_ufi_idx(input int ch2, aupi_pkt p);
        int idxQ2[$];
        int idx2;

        foreach (valid_channelQ[i]) begin
            if (valid_channelQ[i][ch2])
                idxQ2.push_back(i);
        end

        void'(std::randomize(idx2) with {idx2 inside {idxQ2};});
        if (p.ufi_port != -1) idx2 = p.ufi_port;

        return idx2;
    endfunction

    local task proc_rx_pkt_ufi2upi();
        aufi_message    msg;
        bit             req_is_valid, data_is_valid, rsp_is_valid;
        fork
            forever begin
                wait(ufi_dev_q[0].is_agent || passive_mode);
                @(posedge ufi_dev_q[0].f2a_if.clk);
                foreach(ufi_dev_q[i]) begin
                    aufi_device ufi_dev = ufi_dev_q[i]; 
                    if (ufi_dev.upi_rx_msgQ.size()) begin
                        msg = ufi_dev.upi_rx_msgQ.pop_front();
                        if (msg.f2a_req.req_is_valid    ||  msg.a2f_req.req_is_valid)   ufi_dev.upi_agt_rx_req_msgQ.push_back(msg); //cbb hotfix
                        if (msg.f2a_data.data_is_valid  ||  msg.a2f_data.data_is_valid) ufi_dev.upi_agt_rx_data_msgQ.push_back(msg); //cbb hotfix
                        if (msg.f2a_rsp.rsp_is_valid    ||  msg.a2f_rsp.rsp_is_valid)   ufi_dev.upi_agt_rx_rsp_msgQ.push_back(msg); //cbb hotfix
                    end
                    ch2upi(ufi_dev, i); 
                end
            end
            forever begin
                wait(!ufi_dev_q[0].is_agent || passive_mode);
                @(posedge ufi_dev_q[0].a2f_if.clk);
                foreach(ufi_dev_q[i]) begin
                    aufi_device ufi_dev = ufi_dev_q[i]; 
                    if (ufi_dev.upi_rx_msgQ.size()) begin
                        msg = ufi_dev.upi_rx_msgQ.pop_front();
                        if (msg.f2a_req.req_is_valid    ||  msg.a2f_req.req_is_valid)   ufi_dev.upi_agt_rx_req_msgQ.push_back(msg); //cbb hotfix
                        if (msg.f2a_data.data_is_valid  ||  msg.a2f_data.data_is_valid) ufi_dev.upi_agt_rx_data_msgQ.push_back(msg); //cbb hotfix
                        if (msg.f2a_rsp.rsp_is_valid    ||  msg.a2f_rsp.rsp_is_valid)   ufi_dev.upi_agt_rx_rsp_msgQ.push_back(msg); //cbb hotfix
                    end
                    ch2upi(ufi_dev, i); 
                end
            end
        join
    endtask

    local task ch2upi(aufi_device ufi_dev, int ufi_port);
        aupi_pkt        rx_p;
        aufi_message    msgs[2];

        if (ufi_dev.upi_agt_rx_req_msgQ.size) begin //cbb hotfix
            rx_p = new();
            rx_p.ufi_port = ufi_port;
            msgs[0] = ufi_dev.upi_agt_rx_req_msgQ[0]; //cbb hotfix
            ufi2upi(upi_agt, ufi_dev, rx_p, msgs);
            foreach(msgs[i])
                rx_p.ufi_msgs.push_back(msgs[i]);
            upi_agt.route.uxi_route(rx_p);
            begin //CALLBACK
                `AUVM_CALLBACK_BFM(upi_agt, aupi_callbacks, ufi_link_rx_pkt(upi_agt, rx_p));
                ufi_link_rx_p = rx_p;
                ->ufi_link_rx_e;
                #1ps;
            end
            if ((rx_p.dnid == node_id && rx_p.same_stack_id(stack_id))|| !is_ufi_sw) begin
                if_upi.ufi_rx_pkts.push_back(rx_p);
                ufi_dev.upi_agt_rx_req_msgQ.delete(0); //cbb hotfix
            end 
            msgs[0] = null;
            msgs[1] = null;
        end
        if (ufi_dev.upi_agt_rx_data_msgQ.size) begin // cbb hotfix
            bit data_eop;
            rx_p = new();
            rx_p.ufi_port = ufi_port;
            msgs[0] = ufi_dev.upi_agt_rx_data_msgQ[0]; //cbb hotfix
            data_eop = (ufi_dev.is_agent) ? msgs[0].f2a_data.data_eop : msgs[0].a2f_data.data_eop;
            if (data_eop) begin
                ufi2upi(upi_agt, ufi_dev, rx_p, msgs);
                foreach(msgs[i])
                    rx_p.ufi_msgs.push_back(msgs[i]);
                upi_agt.route.uxi_route(rx_p);
                begin //CALLBACK
                    `AUVM_CALLBACK_BFM(upi_agt, aupi_callbacks, ufi_link_rx_pkt(upi_agt, rx_p));
                    ufi_link_rx_p = rx_p;
                    ->ufi_link_rx_e;
                    #1ps;
                end
                if ((rx_p.dnid == node_id && rx_p.same_stack_id(stack_id))|| !is_ufi_sw) begin
                    if_upi.ufi_rx_pkts.push_back(rx_p);
                    ufi_dev.upi_agt_rx_data_msgQ.delete(0); //cbb hotfix
                end
            end else if (ufi_dev.upi_agt_rx_data_msgQ.size() > 1) begin //cbb hotfix
                msgs[1] = ufi_dev.upi_agt_rx_data_msgQ[1]; //cbb hotfix
                ufi2upi(upi_agt, ufi_dev, rx_p, msgs);
                foreach(msgs[i])
                    rx_p.ufi_msgs.push_back(msgs[i]);
                upi_agt.route.uxi_route(rx_p);
                begin //CALLBACK
                    `AUVM_CALLBACK_BFM(upi_agt, aupi_callbacks, ufi_link_rx_pkt(upi_agt, rx_p));
                    ufi_link_rx_p = rx_p;
                    ->ufi_link_rx_e;
                    #1ps;
                end
                if ((rx_p.dnid == node_id && rx_p.same_stack_id(stack_id))|| !is_ufi_sw) begin
                    if_upi.ufi_rx_pkts.push_back(rx_p);
                    repeat(2) ufi_dev.upi_agt_rx_data_msgQ.delete(0); //cbb hotfix
                end
            end
            msgs[0] = null;
            msgs[1] = null;
        end
        if (ufi_dev.upi_agt_rx_rsp_msgQ.size) begin //cbb hotfix
            rx_p = new();
            rx_p.ufi_port = ufi_port;
            msgs[0] = ufi_dev.upi_agt_rx_rsp_msgQ[0]; //cbb hotfix
            ufi2upi(upi_agt, ufi_dev, rx_p, msgs);
            foreach(msgs[i])
                rx_p.ufi_msgs.push_back(msgs[i]);
            upi_agt.route.uxi_route(rx_p);
            begin //CALLBACK
                `AUVM_CALLBACK_BFM(upi_agt, aupi_callbacks, ufi_link_rx_pkt(upi_agt, rx_p));
                ufi_link_rx_p = rx_p;
                ->ufi_link_rx_e;
                #1ps;
            end
            if ((rx_p.dnid == node_id && rx_p.same_stack_id(stack_id))|| !is_ufi_sw) begin
                if_upi.ufi_rx_pkts.push_back(rx_p);
                ufi_dev.upi_agt_rx_rsp_msgQ.delete(0); //cbb hotfix
            end
            msgs[0] = null;
            msgs[1] = null;
        end
    endtask

    function void assign_ufi(ref aufi_uvm_agent ufi2[$], input bit [2:0] valid_ch2[$]= {3'b111});
        string s;
        ufi_dev_q.delete();
        foreach (ufi2[i])
            ufi_dev_q.push_back(ufi2[i].driver);
        valid_channelQ = valid_ch2;
        if (valid_ch2.size > ufi2.size) begin
            $display("valid_ch2.size(%d) is not same as ufi2.size(%d)", valid_ch2.size, ufi2.size);
            $finish;
        end    
        foreach (ufi2[i]) 
            s = $psprintf("%s %s,", s ,ufi2[i].get_name());
        //$display("%s: %s use port%d to {%s}",get_name(), upi_agt.get_name(), port_id, s);
    endfunction
endclass

`endif
