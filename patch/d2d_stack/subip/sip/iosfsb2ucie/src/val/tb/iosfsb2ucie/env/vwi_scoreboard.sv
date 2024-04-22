`uvm_analysis_imp_decl(_req_in_intf0) 
`uvm_analysis_imp_decl(_rsp_out_intf0) 
`uvm_analysis_imp_decl(_req_in_intf1) 
`uvm_analysis_imp_decl(_rsp_out_intf1) 
`uvm_analysis_imp_decl(_bfm_req_in_intf1) 
`uvm_analysis_imp_decl(_bfm_rsp_out_intf1) 

class vwi_scoreboard extends uvm_scoreboard;
uvm_analysis_imp_req_in_intf0 #(vwi_req,vwi_scoreboard) req_in_intf0;
uvm_analysis_imp_rsp_out_intf0 #(vwi_rsp,vwi_scoreboard) rsp_out_intf0;
uvm_analysis_imp_req_in_intf1 #(vwi_req,vwi_scoreboard) req_in_intf1;
uvm_analysis_imp_rsp_out_intf1 #(vwi_rsp,vwi_scoreboard)rsp_out_intf1;
uvm_analysis_imp_bfm_req_in_intf1 #(vlw_driven_packet,vwi_scoreboard) bfm_req_in_intf1;
uvm_analysis_imp_bfm_rsp_out_intf1 #(vlw_driven_packet,vwi_scoreboard) bfm_rsp_out_intf1;

vwi_req req_die0_q[$];
vwi_req req_die1_q[$];
vwi_rsp rsp_die0_q[$];
vwi_rsp rsp_die1_q[$];
int req_die0_rsp_die1_errors;
int req_die1_rsp_die0_errors;
bit req_die0_queue[64][$];
bit req_die1_queue[64][$];
bit bfm_req_die1_queue[64][$];
int fail;
bit [63:0]bfm_local_async_virt_out_die1,local_async_virt_out_die1,local_async_virt_out_die0;
bit [63:0]bfm_local_async_virt_in_die1,local_async_virt_in_die0,local_async_virt_in_die1;
vlw_driven_packet vlw_seq_items; 


`uvm_component_utils(vwi_scoreboard)

function new(string name = "vwi_scoreboard", uvm_component parent = null);
  super.new(name, parent);
//local_async_virt_in_die0 = 'h9; 

 if ($value$plusargs("STRAP_DEFAULT_WIRES_IN_VALUE=%x",local_async_virt_in_die0)) begin
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_in value from user %b",local_async_virt_in_die0), UVM_DEBUG)
end else begin
local_async_virt_in_die0 = 'h9; 
end

 if ($value$plusargs("STRAP_DEFAULT_WIRES_IN_VALUE=%x",local_async_virt_in_die1)) begin
        bfm_local_async_virt_in_die1 = local_async_virt_in_die1;
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_in value from user %b",local_async_virt_in_die1), UVM_DEBUG)
        `uvm_info("Strap_value", $sformatf("bfm_local_async_virt_out_die1 %b",bfm_local_async_virt_in_die1), UVM_DEBUG)
end else begin
local_async_virt_in_die1 = 'h9; 
bfm_local_async_virt_in_die1 = 'h9; 
end


 if ($value$plusargs("STRAP_DEFAULT_WIRES_OUT_VALUE=%x",local_async_virt_out_die0)) begin
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_in value from user %b",local_async_virt_out_die0), UVM_DEBUG)
end else begin
local_async_virt_out_die0 = 'h9; 
end

 if ($value$plusargs("STRAP_DEFAULT_WIRES_OUT_VALUE=%x",local_async_virt_out_die1)) begin
        bfm_local_async_virt_out_die1 = local_async_virt_out_die1;
        `uvm_info("Strap_value", $sformatf("Getting strap_default_wires_in value from user %b",local_async_virt_out_die1), UVM_DEBUG)
        `uvm_info("Strap_value", $sformatf("bfm_local_async_virt_out_die1 %b",bfm_local_async_virt_out_die1), UVM_DEBUG)
end else begin
local_async_virt_out_die1 = 'h9; 
bfm_local_async_virt_out_die1 = 'h9; 
end






endfunction


function void build_phase (uvm_phase phase);
	super.build_phase(phase);

req_in_intf0 = new("req_in_intf0",this);
req_in_intf1 = new("req_in_intf1",this);
rsp_out_intf0 = new("rsp_out_intf0",this);
rsp_out_intf1 = new("rsp_out_intf1",this);
bfm_req_in_intf1 = new("bfm_req_in_intf1",this);
bfm_rsp_out_intf1 = new("bfm_rsp_out_intf1",this);
endfunction : build_phase

virtual function void write_bfm_req_in_intf1 (vlw_driven_packet bfm_req);
    
    vlw_seq_items=bfm_req;
    `uvm_info(get_type_name(),$sformatf("RTL_BFM: Data received from the BFM VLW_IP_MONITOR for driven data, index: %d, value: %b ",vlw_seq_items.vwires_in, vlw_seq_items.value),UVM_HIGH)
    bfm_req_die1_queue[vlw_seq_items.vwires_in].push_back(vlw_seq_items.value);

    bfm_local_async_virt_in_die1[vlw_seq_items.vwires_in] = vlw_seq_items.value; 
    `uvm_info ("bfm_req_in_intf1", $sformatf("queue value is %p",bfm_req_die1_queue),UVM_HIGH)

endfunction

virtual function void write_bfm_rsp_out_intf1 (vlw_driven_packet bfm_rsp);
    bit vary;
    int i;
    `uvm_info(get_type_name(),"RTL_BFM: Data received from the BFM VLW_OUT_MONITOR ",UVM_HIGH)
//    `uvm_info(get_type_name(),$sformatf("RTL_BFM: adanabal_expt: printing for the wire ID:%d bfm_rsp.value:%0b and bfm_local_async_virt_out_die1[%d]:%b",i,bfm_rsp.value,i,bfm_local_async_virt_out_die1[i]),UVM_HIGH)

    i= bfm_rsp.vwires_in;

	if (bfm_rsp.value != bfm_local_async_virt_out_die1[i]) begin
              if(req_die0_queue[i].size()!=0) begin
                                    vary=req_die0_queue[i].pop_front();
                                    `uvm_info(get_type_name(),$sformatf("RTL_BFM: VWI_SCB: printing for the wire ID:%d vary:%0b and rmt_vlw_out_pre[%d]:%b",i,vary,i,bfm_local_async_virt_out_die1[i]),UVM_HIGH)
                                    `uvm_info(get_type_name(),$sformatf("RTL_BFM: VWI_SCB: printing for the wire ID:%d bfm_rsp.value :%b",i,bfm_rsp.value),UVM_HIGH)
                                    if(vary==bfm_local_async_virt_out_die1[i]) begin
                                        `uvm_error(get_type_name(),"RTL_BFM: VWI_SCB: here is an error")
                                    end
			       end
			       else begin
			         `uvm_error(get_type_name(),$sformatf("RTL_BFM: Error in the UCIE packet mismatch with input vlw. The size of the vlw_queue for that wire is 0. This is an issue in position %d ",i))
				 fail++;
			       end
	end

	bfm_local_async_virt_out_die1[i] = bfm_rsp.value;

endfunction

virtual function void write_req_in_intf0 (vwi_req req);
bit value,pos;



for (int i=0;i<64;i++) begin
	if (req.b_async_virt_in[i] != local_async_virt_in_die0[i]) begin
		req_die0_queue[i].push_back(req.b_async_virt_in[i]); end
end

local_async_virt_in_die0 = req.b_async_virt_in;

`uvm_info ("req_in_intf0", $sformatf("queue value is %p",req_die0_queue),UVM_HIGH)


endfunction



virtual function void write_rsp_out_intf0 (vwi_rsp rsp);
bit vary_rq1;

`uvm_info ("rsp_out_intf0", $sformatf("Sending it from here"),UVM_LOW)


if ($test$plusargs("SB2UCIEBFM")) begin
    for (int i=0;i<64;i++) begin
    	if (rsp.b_async_virt_out[i] != local_async_virt_out_die0[i]) begin
                  if(bfm_req_die1_queue[i].size()!=0) begin
                                        vary_rq1=bfm_req_die1_queue[i].pop_front();
                                        `uvm_info(get_type_name(),$sformatf("VWI_SCB: printing for the wire ID:%d vary:%0b and rmt_vlw_out_pre[%d]:%b",i,vary_rq1,i,local_async_virt_out_die0[i]),UVM_HIGH)
                                        `uvm_info(get_type_name(),$sformatf("VWI_SCB: printing for the wire ID:%d rsp.b_async_virt_out[%d]:%b",i,i,rsp.b_async_virt_out[i]),UVM_HIGH)
                                        if(vary_rq1==local_async_virt_out_die0[i]) begin
                                            `uvm_error(get_type_name(),"VWI_SCB: here is an error")
                                        end
    			       end
    			       else begin
    			         `uvm_error(get_type_name(),$sformatf("Error in the UCIE packet mismatch with input vlw. The size of the vlw_queue for that wire is 0. This is an issue in position %d ",i))
    				 fail++;
    			       end
          end    
    end
	   local_async_virt_out_die0 = rsp.b_async_virt_out;
end

if (!$test$plusargs("SB2UCIEBFM")) begin
    for (int i=0;i<64;i++) begin
    	if (rsp.b_async_virt_out[i] != local_async_virt_out_die0[i]) begin
                  if(req_die1_queue[i].size()!=0) begin
                                        vary_rq1=req_die1_queue[i].pop_front();
                                        `uvm_info(get_type_name(),$sformatf("VWI_SCB: printing for the wire ID:%d vary:%0b and rmt_vlw_out_pre[%d]:%b",i,vary_rq1,i,local_async_virt_out_die0[i]),UVM_HIGH)
                                        `uvm_info(get_type_name(),$sformatf("VWI_SCB: printing for the wire ID:%d rsp.b_async_virt_out[%d]:%b",i,i,rsp.b_async_virt_out[i]),UVM_HIGH)
                                        if(vary_rq1==local_async_virt_out_die0[i]) begin
                                            `uvm_error(get_type_name(),"VWI_SCB: here is an error")
                                        end
    			       end
    			       else begin
    			         `uvm_error(get_type_name(),$sformatf("Error in the UCIE packet mismatch with input vlw. The size of the vlw_queue for that wire is 0. This is an issue in position %d ",i))
    				 fail++;
    			       end
    	end
    end
	   local_async_virt_out_die0 = rsp.b_async_virt_out;

end
endfunction


virtual function void write_req_in_intf1 (vwi_req req);

bit value,pos;



for (int i=0;i<64;i++) begin
	if (req.b_async_virt_in[i] != local_async_virt_in_die1[i]) begin
		req_die1_queue[i].push_back(req.b_async_virt_in[i]); end
end

local_async_virt_in_die1 = req.b_async_virt_in;

`uvm_info ("req_in_intf1", $sformatf("queue value is %p",req_die1_queue),UVM_HIGH)





endfunction



virtual function void write_rsp_out_intf1 (vwi_rsp rsp);
bit vary;

for (int i=0;i<64;i++) begin
	if (rsp.b_async_virt_out[i] != local_async_virt_out_die1[i]) begin
              if(req_die0_queue[i].size()!=0) begin
                                    vary=req_die0_queue[i].pop_front();
                                    `uvm_info(get_type_name(),$sformatf("VWI_SCB:, printing for the wire ID:%d vary:%0b and rmt_vlw_out_pre[%d]:%b",i,vary,i,local_async_virt_out_die1[i]),UVM_HIGH)
                                    if(vary==local_async_virt_out_die1[i]) begin
                                        `uvm_error(get_type_name(),"VWI_SCB: here is an error")
                                    end
			       end
			       else begin
			         `uvm_error(get_type_name(),$sformatf("Error in the UCIE packet mismatch with input vlw. The size of the vlw_queue for that wire is 0. This is an issue in position %d ",i))
				 fail++;
			       end
		end
	   end
	   local_async_virt_out_die1 = rsp.b_async_virt_out;



rsp_die1_q.push_back(rsp);


endfunction





function void check_phase(uvm_phase phase);
super.check_phase(phase);

    for (int itr1=0;itr1<64;itr1++) begin
              if(req_die0_queue[itr1].size()!=0)
                  `uvm_error(get_type_name(),$sformatf("VWI_SCB: Die0 virt_in queue: req_die0_queue[%d] is not empty and size is %d", itr1, req_die0_queue[itr1].size()))
    end    


if ($test$plusargs("SB2UCIEBFM")) begin

    for (int itr2=0;itr2<64;itr2++) begin
              if(bfm_req_die1_queue[itr2].size()!=0)
                  `uvm_error(get_type_name(),$sformatf("VWI_SCB: BFM Die1 virt_in queue: bfm_req_die1_queue[%d] is not empty and size is %d", itr2, bfm_req_die1_queue[itr2].size()))
    end   

    if (bfm_local_async_virt_out_die1 != local_async_virt_in_die0 ) begin
     `uvm_error(get_type_name(),"VWI_SCB: Request going from Die0 doesn't match with the Response coming from Die1")
    
    end
    
    if (local_async_virt_out_die0 != bfm_local_async_virt_in_die1 ) begin
     `uvm_error(get_type_name(),"VWI_SCB: Request going from Die1 doesn't match with the Response coming from Die0")
    
    end
end else begin   

    for (int itr3=0;itr3<64;itr3++) begin
              if(req_die1_queue[itr3].size()!=0)
                  `uvm_error(get_type_name(),$sformatf("VWI_SCB: Die1 virt_in queue: req_die1_queue[%d] is not empty and size is %d", itr3, req_die1_queue[itr3].size()))
    end   

    if (local_async_virt_out_die1 != local_async_virt_in_die0 ) begin
     `uvm_error(get_type_name(),"VWI_SCB: Request going from Die0 doesn't match with the Response coming from Die1")
    
    end
    
    if (local_async_virt_out_die0 != local_async_virt_in_die1 ) begin
     `uvm_error(get_type_name(),"VWI_SCB: Request going from Die1 doesn't match with the Response coming from Die0")
    
    end
end

endfunction

endclass: vwi_scoreboard


