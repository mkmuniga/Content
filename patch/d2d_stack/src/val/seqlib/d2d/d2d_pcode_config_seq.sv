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

class d2d_pcode_config_seq extends d2d_base_sequence;
   `uvm_object_utils(d2d_pcode_config_seq);

   bit ula0_dda0_config_en, ula1_dda1_config_en;         //enable for RDI or PHY model. 
   bit ucie_phy_ch0_config_en, ucie_phy_ch1_config_en;   //enable only for PHY model.
   bit dda0_start_ucie_link_training, dda1_start_ucie_link_training; //enable only for PHY model.
   d2d_uciedda_dvsec_seq d2d_uciedda_dvsec_seq_i; 

   uvm_reg        isa_config_req, isa_config_ack, isa_config_done;
   uvm_reg        dda0_uciedda_sta_misc_status, dda1_uciedda_sta_misc_status; 
   uvm_reg        ula0_ula_misc_status, ula1_ula_misc_status; 

   uvm_reg_data_t isa_config_req_wr_data, isa_config_ack_wr_data, isa_config_done_wr_data;
   uvm_reg_data_t isa_config_req_rd_data, isa_config_ack_rd_data, isa_config_done_rd_data;
   uvm_reg_data_t dda0_uciedda_sta_misc_status_rd_data, dda1_uciedda_sta_misc_status_rd_data; 
   uvm_reg_data_t ula0_ula_misc_status_rd_data, ula1_ula_misc_status_rd_data; 

   bit dda0_rst_actions_done, dda1_rst_actions_done, ula0_rst_actions_done, ula1_rst_actions_done;

   function new (string name = "d2d_pcode_config_seq");
       super.new(name);
   endfunction   

   task body;

     `uvm_info(get_full_name(), $sformatf("d2d_pcode_config_seq[%0d] started", env_inst), UVM_LOW)
      super.body();

      assign_d2d_pcode_config_registers();

      fork: d2d_pcode_config 
         if(ucie_phy_ch0_config_en && ucie_phy_ch1_config_en) begin
            phy_isa_config_req_ack_set_clear(.set_clear(1'b1));   
            phy_isa_config_req_ack_set_clear(.set_clear(1'b0));   
         end 
         if(ula0_dda0_config_en && ula1_dda1_config_en) begin
            ula_dda_isa_config_done_set();   
         end 
      join;   

      if(dda0_start_ucie_link_training && dda1_start_ucie_link_training) begin
         //TODO: uncomment this logic once PHY implemented DVSEC feature.  
         //TODO: fork 
         //TODO:    begin
         //TODO:      `uvm_info(get_type_name(), $sformatf("d2d_uciedda_dvsec_seq_i[%0d] start UCIe Link training", env_inst), UVM_LOW)
         //TODO:       d2d_uciedda_dvsec_seq_i = d2d_uciedda_dvsec_seq::type_id::create("d2d_uciedda_dvsec_seq_i"); 
         //TODO:       d2d_uciedda_dvsec_seq_i.env_inst                       = this.env_inst; 
         //TODO:       d2d_uciedda_dvsec_seq_i.seq_reg_access_path            ="UVM_FRONTDOOR"; //Always Keep UVM_FRONTDOOR for PHY Shadow reg access.  
         //TODO:       d2d_uciedda_dvsec_seq_i.dda_ucie_link_train_retrain[0] = dda0_start_ucie_link_training;
         //TODO:       d2d_uciedda_dvsec_seq_i.dda_ucie_link_train_retrain[1] = dda1_start_ucie_link_training;
         //TODO:       d2d_uciedda_dvsec_seq_i.start(m_sequencer); 
         //TODO:      `uvm_info(get_type_name(), $sformatf("d2d_uciedda_dvsec_seq_i[%0d] completed UCIe Link training", env_inst), UVM_LOW)
         //TODO:    end
         //TODO:    begin
         //TODO:       #30us;
         //TODO:      `uvm_error(get_type_name(), $sformatf("d2d_uciedda_dvsec_seq_i[%0d] UCIe Link training timeout", env_inst) )
         //TODO:    end 
         //TODO: join_any;
         //TODO: disable fork; //UCIe Linkup;
      end

      `uvm_info(get_full_name(), $sformatf("d2d_pcode_config_seq[%0d] ended", env_inst), UVM_LOW)

   endtask: body

   //------------------------------------------------------------------------------------------------------------//
   //ISA Register isa_config_req[0] set for PHY config_req/ack
   //------------------------------------------------------------------------------------------------------------//
   task phy_isa_config_req_ack_set_clear(input bit set_clear);   
     d2d_read_reg( isa_config_req, status, isa_config_req_rd_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     isa_config_req_wr_data    = {31{1'b1}}; //PHY config_req/ack //bit[31] reserved.
     isa_config_req_wr_data[0] = set_clear; //PHY config_req/ack
     d2d_write_reg(isa_config_req, status, isa_config_req_wr_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     d2d_read_reg( isa_config_req, status, isa_config_req_rd_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     if(isa_config_req_wr_data == isa_config_req_rd_data) begin
       `uvm_info(get_type_name(), $sformatf("isa_config_req[%0d]:  isa_config_req_wr_data=0x%0h isa_config_req_rd_data=0x%0h  access_path=%0s",
                 env_inst, isa_config_req_wr_data, isa_config_req_rd_data, access_path), UVM_LOW)
     end
     else begin
       `uvm_fatal(get_type_name(), $sformatf("isa_config_req[%0d]:  isa_config_req_wr_data=0x%0h isa_config_req_rd_data=0x%0h  access_path=%0s",
                  env_inst, isa_config_req_wr_data, isa_config_req_rd_data, access_path) )
     end

     //------------------------------------------------------------------------------------------------------------//
     //ISA Register isa_config_ack[0] status set for PHY config_req/ack
     //------------------------------------------------------------------------------------------------------------//
     fork 
       begin
          do begin
            d2d_read_reg(isa_config_ack, status, isa_config_ack_rd_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
            `uvm_info(get_type_name(), $sformatf("isa_config_ack[%0d]:  isa_config_req_wr_data=0x%0h isa_config_ack_rd_data=0x%0h  access_path=%0s",
                      env_inst, isa_config_req_wr_data, isa_config_ack_rd_data, access_path), UVM_LOW)
            #100ns;
          end while(isa_config_ack_rd_data != {set_clear, 30'h3FFF_FFFF, set_clear}); 
       end
       begin
          #5us;
         `uvm_fatal(get_type_name(), $sformatf("isa_config_ack[%0d] status timeout:  isa_config_req_wr_data=0x%0h isa_config_ack_rd_data=0x%0h  access_path=%0s",
                    env_inst, isa_config_req_wr_data, isa_config_ack_rd_data, access_path) )
       end
     join_any;
     disable fork; //isa_config_ack;

     //------------------------------------------------------------------------------------------------------------//
     //TODO: Place holder for UCIe PHY registers configuration only if configuration enable. 
     //------------------------------------------------------------------------------------------------------------//
   endtask: phy_isa_config_req_ack_set_clear   


   //------------------------------------------------------------------------------------------------------------//
   //TODO: DDA0 and DDA1 uciedda_sta_misc_status.iosf_sb_rst_actions_done.(bit[0])
   //TODO: ULA0 and ULA1 ula_misc_status.*rst_actions_done.(bit[0]:fsm, bit[1]:sb and bit[2]:link)
   //------------------------------------------------------------------------------------------------------------//
   task ula_dda_isa_config_done_set();   
     fork
        begin
          do begin
              if(!dda0_rst_actions_done) begin 
                d2d_read_reg(dda0_uciedda_sta_misc_status, status, dda0_uciedda_sta_misc_status_rd_data, access_path, .reg_access_path(seq_reg_access_path));
                dda0_rst_actions_done = dda0_uciedda_sta_misc_status_rd_data[0]; 
              end
              if(!ula0_rst_actions_done) begin 
                d2d_read_reg(ula0_ula_misc_status, status, ula0_ula_misc_status_rd_data, access_path, .reg_access_path(seq_reg_access_path));
                ula0_rst_actions_done = (ula0_ula_misc_status_rd_data[2:0] == 3'b111);
              end

              if(!dda1_rst_actions_done) begin 
                d2d_read_reg(dda1_uciedda_sta_misc_status, status, dda1_uciedda_sta_misc_status_rd_data, access_path, .reg_access_path(seq_reg_access_path));
                dda1_rst_actions_done = dda1_uciedda_sta_misc_status_rd_data[0]; 
              end
              if(!ula1_rst_actions_done) begin 
                d2d_read_reg(ula1_ula_misc_status, status, ula1_ula_misc_status_rd_data, access_path, .reg_access_path(seq_reg_access_path));
                ula1_rst_actions_done = (ula1_ula_misc_status_rd_data[2:0] == 3'b111);
              end
     
              `uvm_info(get_full_name(), $sformatf("misc status rst_actions_done: DDA0=%0d, DDA1=%0d, ULA0=%0d and ULA1=%0d", 
                        dda0_rst_actions_done, dda1_rst_actions_done, ula0_rst_actions_done, ula1_rst_actions_done), UVM_LOW)
     
             #100ns;
          end while(! (dda0_rst_actions_done & dda1_rst_actions_done & ula0_rst_actions_done & ula1_rst_actions_done));
        end
        begin
           #5us;
          `uvm_fatal(get_full_name(), $sformatf("misc status rst_actions_done: DDA0=%0d, DDA1=%0d, ULA0=%0d and ULA1=%0d", 
                     dda0_rst_actions_done, dda1_rst_actions_done, ula0_rst_actions_done, ula1_rst_actions_done) )
        end
     join_any;
     disable fork;   
     //------------------------------------------------------------------------------------------------------------//
     //TODO:  Place holder for ULA-0/1 and DDA-0/1 registers configuration. 
     //------------------------------------------------------------------------------------------------------------//

     //------------------------------------------------------------------------------------------------------------//
     //isa_config_done set IOSF-SB CRwrite //DDA0, DDA1, ULA0 and ULA1.
     //ISA Register isa_config_done[7,8,9 and 10] set for DDA, ULA IPs 
     //------------------------------------------------------------------------------------------------------------//
     d2d_read_reg( isa_config_done, status, isa_config_done_rd_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     //isa_config_done_wr_data=isa_config_done_rd_data; 
     isa_config_done_wr_data = {31{1'b1}}; //bit[31] reserved. 
     isa_config_done_wr_data[10:7]=4'b1111; //10:ULA1, 9:ULA0, 8:DDA1 and 7:DDA0 //TODO: redundent.
     d2d_write_reg(isa_config_done, status, isa_config_done_wr_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     d2d_read_reg( isa_config_done, status, isa_config_done_rd_data, access_path, 7'h18, 1'b0, .reg_access_path(seq_reg_access_path));
     if(isa_config_done_wr_data == isa_config_done_rd_data) begin
       `uvm_info(get_type_name(), $sformatf("isa_config_done[%0d]:  isa_config_done_wr_data=0x%0h isa_config_done_rd_data=0x%0h  access_path=%0s",
                 env_inst, isa_config_done_wr_data, isa_config_done_rd_data, access_path), UVM_LOW)
     end
     else begin
       `uvm_fatal(get_type_name(), $sformatf("isa_config_done[%0d]:  isa_config_done_wr_data=0x%0h isa_config_done_rd_data=0x%0h  access_path=%0s",
                  env_inst, isa_config_done_wr_data, isa_config_done_rd_data, access_path) )
     end
   endtask: ula_dda_isa_config_done_set   

   //------------------------------------------------------------------------------------------------------------//
   // Get Register handle for a specific IP register based on env_inst, IP interface name and Register string. 
   //------------------------------------------------------------------------------------------------------------//
   virtual function void assign_d2d_pcode_config_registers();
      isa_config_req                  = get_d2d_register(ISA_D2D_GPSB, "ISA_CONFIG_REQ");
      isa_config_ack                  = get_d2d_register(ISA_D2D_GPSB, "ISA_CONFIG_ACK");
      isa_config_done                 = get_d2d_register(ISA_D2D_GPSB, "ISA_CONFIG_DONE");
      dda0_uciedda_sta_misc_status    = get_d2d_register(UCIEDDA0_GPSB, "uciedda_sta_misc_status");
      dda1_uciedda_sta_misc_status    = get_d2d_register(UCIEDDA1_GPSB, "uciedda_sta_misc_status");
      ula0_ula_misc_status            = get_d2d_register(ULA0_GPSB, "ula_misc_status");
      ula1_ula_misc_status            = get_d2d_register(ULA1_GPSB, "ula_misc_status");

   endfunction: assign_d2d_pcode_config_registers

endclass: d2d_pcode_config_seq
