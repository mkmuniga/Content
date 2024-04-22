   import uciesbbfm_env_pkg::*;
class vwi_driver extends uvm_driver #(vwi_req);
    `uvm_component_utils(vwi_driver)

    vwi_req vwi_req_inst;
    virtual vwi_if vwi_if_inst;
    logic [`V_WIRES_IN-1:0] async_virt_in_prev;
    logic [`V_WIRES_IN-1:0] async_virt_in_calc;
    logic [`V_WIRES_IN-1:0] new_async_in;
    bit [63:0]counter_vlw[`V_WIRES_IN-1:0];
    bit [63:0]counter_rdi[`V_WIRES_IN-1:0];
    bit [`V_WIRES_IN-1:0] data_combined_prev;
    bit [`V_WIRES_IN-1:0] data_combined_curr;
    ucie_pkt_type ucie_packet;
    uvm_analysis_imp #(ucie_pkt_type,vwi_driver) port_ucie_pkt;
    bit async_virt_in_queue[`V_WIRES_IN][$];
    int vlw_buffer_size;

    function new(string name = "vwi_driver", uvm_component parent);
        super.new(name,parent);
        `uvm_info(get_name(), $sformatf("creating driver component"), UVM_NONE)
    endfunction : new

    function void build_phase(uvm_phase phase);
      super.build_phase(phase);
      port_ucie_pkt=new("port_ucie_pkt", this);

      if(!uvm_config_db #(virtual vwi_if)::get(this,"", "dut_vi", vwi_if_inst)) 
          `uvm_fatal(get_type_name(), "Didn't get handle for interface")
      else begin
          `uvm_info(get_name(), $sformatf("inside driver - Got handle for interface"), UVM_NONE)
      end
      if(!uvm_config_db #(int)::get(this,"", "vlw_bf_size", vlw_buffer_size)) begin
          vlw_buffer_size = 3;
          `uvm_info(get_type_name(), $sformatf("Didn't get handle for vlw_buffer_size, hence setting the default value of %d", vlw_buffer_size), UVM_NONE)
      end else begin
          `uvm_info(get_name(), $sformatf("inside driver - Got handle for vlw_buffer_size, value = %d",vlw_buffer_size), UVM_NONE)
      end
    endfunction

    task run_phase(uvm_phase phase);
        forever begin @(posedge vwi_if_inst.async_clk);
            if (!(&vwi_if_inst.tb_reset)) begin
                `uvm_info(get_name(), $sformatf("adanabal1: inside driver - before reset"), UVM_HIGH)
                data_combined_prev<=vwi_if_inst.strap_default_wires_in;
                vwi_if_inst.async_virt_in <= vwi_if_inst.strap_default_wires_in;
                `uvm_info(get_name(), $sformatf("adanabal1: async_virt_in value is %b",vwi_if_inst.async_virt_in), UVM_HIGH)
                @(&vwi_if_inst.tb_reset); //FIXME lnehama - cbb integ hotfix
            end else if (vwi_if_inst.ip_ready) begin
                seq_item_port.try_next_item(vwi_req_inst);
                if(vwi_req_inst != null) begin
                    `uvm_info(get_name(), $sformatf("adanabal2: inside driver - after reset"), UVM_HIGH)
                    async_virt_in_prev = vwi_if_inst.async_virt_in; 
                    async_virt_in_calc = ((~vwi_if_inst.async_virt_in & vwi_req_inst.mask) | (vwi_if_inst.async_virt_in & ~vwi_req_inst.mask));
                    `uvm_info(get_name(), $sformatf("adanabal2: vwi_req_inst.mask %b", vwi_req_inst.mask), UVM_HIGH)
                    `uvm_info(get_name(), $sformatf("adanabal2:  async_virt_in_prev %b", async_virt_in_prev), UVM_HIGH); 
                    `uvm_info(get_name(), $sformatf("adanabal2:  async_virt_in_calc %b", async_virt_in_calc), UVM_HIGH);

                     for(int bus=0; bus<`V_WIRES_IN; bus++) begin
                         if(((async_virt_in_queue[bus].size() == 0) && (async_virt_in_prev[bus] != async_virt_in_calc[bus])) || ((async_virt_in_queue[bus].size() != 0)&&(async_virt_in_queue[bus][$]!=async_virt_in_calc[bus]))) begin
                          `uvm_info(get_name(), $sformatf("adanabal5: queue size is %d for bus %d", async_virt_in_queue[bus].size(), bus), UVM_HIGH)
                          if (async_virt_in_queue[bus].size() != 0) begin
                          `uvm_info(get_name(), $sformatf("last entry in queue %b, full queue %p", async_virt_in_queue[bus][$], async_virt_in_queue[bus]), UVM_HIGH)
                           end   
                             async_virt_in_queue[bus].push_back(async_virt_in_calc[bus]);
                          `uvm_info(get_name(), $sformatf("adanabal5: pushing %b queue size is %d for bus %d", async_virt_in_calc[bus], async_virt_in_queue[bus].size(), bus), UVM_HIGH)

                         end

                         `uvm_info(get_name(), $sformatf("adanabal2: vlw buffer size is %d for bus %d", counter_vlw[bus] - counter_rdi[bus], bus), UVM_HIGH);

                         if((counter_vlw[bus] - counter_rdi[bus]) >= vlw_buffer_size) begin // buffer full
                             new_async_in[bus] = async_virt_in_prev[bus];
                         end else begin
                             if (async_virt_in_queue[bus].size() != 0) begin
                                 new_async_in[bus] = async_virt_in_queue[bus].pop_front();
                                 counter_vlw[bus]++;
                             end else begin
                                 new_async_in[bus] = async_virt_in_prev[bus];
                                 end

                               `uvm_info(get_name(), $sformatf("adanabal2: counter_vlw value %d for bus %d", counter_vlw[bus], bus), UVM_HIGH);
                             end 
                          `uvm_info(get_name(), $sformatf("adanabal2: vlw queue size is %d for bus %d", async_virt_in_queue[bus].size(), bus), UVM_HIGH)

                     end // for loop

                         vwi_if_inst.async_virt_in <= new_async_in;
                         `uvm_info(get_name(), $sformatf("adanabal2: async_virt_in value is %b",new_async_in), UVM_HIGH)
                         seq_item_port.item_done();

                 end else begin // when no seq_item is available
                     `uvm_info(get_name(), $sformatf("adanabal8: popping rest of the queue"), UVM_HIGH)
                     new_async_in = vwi_if_inst.async_virt_in; 
                     for(int bus_id=0; bus_id<`V_WIRES_IN; bus_id++) begin
                         `uvm_info(get_name(), $sformatf("adanabal8: vlw buffer size is %d for bus %d", counter_vlw[bus_id] - counter_rdi[bus_id], bus_id), UVM_HIGH);
                         `uvm_info(get_name(), $sformatf("adanabal8: in else: vlw queue size is %d for bus %d", async_virt_in_queue[bus_id].size(), bus_id), UVM_HIGH)
                         if((async_virt_in_queue[bus_id].size() != 0) && (!((counter_vlw[bus_id] - counter_rdi[bus_id]) >= vlw_buffer_size))) begin 
                            new_async_in[bus_id] = async_virt_in_queue[bus_id].pop_front(); 
                            counter_vlw[bus_id]++;
                            `uvm_info(get_name(), $sformatf("adanabal9: counter_vlw value %d for bus %d", counter_vlw[bus_id], bus_id), UVM_HIGH);
                            `uvm_info(get_name(), $sformatf("adanabal9: popping rest of the queue bus_id: %d, value popped: %b",bus_id,new_async_in[bus_id]), UVM_HIGH)
                         end   
//                         `uvm_info(get_name(), $sformatf("adanabal9: in else: vlw queue size is %d for bus %d", async_virt_in_queue[bus_id].size(), bus_id), UVM_HIGH)
                     end
                     vwi_if_inst.async_virt_in <= new_async_in;
                     `uvm_info(get_name(), $sformatf("adanabal9: async_virt_in value is %b",new_async_in), UVM_HIGH)
                 end

          end // if-else condition: before and after reset  
      end // forever loop  
endtask

    virtual function void write(input ucie_pkt_type data);
        ucie_packet=data;
        if(ucie_packet.opcode=='h1c && ucie_packet.channel=='h4) begin
     	    data_combined_curr[31:0]=ucie_packet.data0;
     	    data_combined_curr[63:32]=ucie_packet.data1;
     	    `uvm_info(get_type_name(),$sformatf("adanabal3: data_combined_prev:%0h",data_combined_prev),UVM_HIGH)
     	    `uvm_info(get_type_name(),$sformatf("adanabal3: data_combined_curr:%0h",data_combined_curr),UVM_HIGH)
     
            for(int r_bus_id=0; r_bus_id<64; r_bus_id++) begin
               if( data_combined_prev[r_bus_id] != data_combined_curr[r_bus_id]) begin
                   counter_rdi[r_bus_id]++;
                   `uvm_info(get_name(), $sformatf("adanabal3: counter_rdi value %d for r_bus_id %d", counter_rdi[r_bus_id], r_bus_id), UVM_HIGH);
               end  
            end
            data_combined_prev = data_combined_curr;
       end
   endfunction: write
endclass    
