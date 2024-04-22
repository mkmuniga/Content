class reset_driver extends uvm_driver #(reset_seq_item);
    `uvm_component_utils(reset_driver)   

    virtual reset_if reset_if_inst;
    reset_seq_item reset_seq_item_inst;

    function new(string name = "reset_driver", uvm_component parent);
        super.new(name,parent);
        `uvm_info(get_name(), $sformatf("creating driver component"), UVM_NONE)
    endfunction : new

    function void build_phase(uvm_phase phase);
      super.build_phase(phase);

      if(!uvm_config_db #(virtual reset_if)::get(this,"", "dut_reset", reset_if_inst)) 
          `uvm_fatal(get_type_name(), "Didn't get handle for interface")
      else
          `uvm_info(get_name(), $sformatf("inside driver - Got handle for interface"), UVM_NONE)
    endfunction

    task run_phase(uvm_phase phase);
        `uvm_info(get_name(), $sformatf("inside run_phase of reset_driver"), UVM_HIGH)
        forever begin @(posedge reset_if_inst.clk);
                seq_item_port.get_next_item(reset_seq_item_inst);
                if(reset_seq_item_inst != null) begin
                    seq_item_port.item_done();
                    reset_if_inst.phy2soc_sb_pok <= reset_seq_item_inst.phy2soc_sb_pok;
                    reset_if_inst.reset_n <= reset_seq_item_inst.reset_n;
                    reset_if_inst.powergood_rst_n <= reset_seq_item_inst.powergood_rst_n;
                    reset_if_inst.fdfx_powergood_rst_b <= reset_seq_item_inst.fdfx_powergood_rst_b;
                    reset_if_inst.fdfx_earlyboot_exit <= reset_seq_item_inst.fdfx_earlyboot_exit;
                    reset_if_inst.dtf_rst_n <= reset_seq_item_inst.dtf_rst_n;
                    reset_if_inst.side_rst_n <= reset_seq_item_inst.side_rst_n;
//cbb hotfix                    `uvm_info(get_name(), $sformatf("value driven reset_n %b powergood_rst_n %b dtf_rst_n %b side_rst_n %b",reset_if_inst.phy2soc_sb_pok, reset_if_inst.reset_n, reset_if_inst.powergood_rst_n,reset_if_inst.dtf_rst_n,reset_if_inst.side_rst_n ), UVM_HIGH)
                 end 
                else begin
                    `uvm_info(get_name(), $sformatf("previous value driven phy2soc_sb_pok %b reset_n %b powergood_rst_n %b dtf_rst_n %b side_rst_n %b",reset_if_inst.phy2soc_sb_pok, reset_if_inst.reset_n, reset_if_inst.powergood_rst_n,reset_if_inst.dtf_rst_n,reset_if_inst.side_rst_n ), UVM_HIGH)
                end
            end
    endtask
 
/* code doesn't work, commenting for now since not needed
    function trigger_warm_reset(int delay);
        reset_if_inst.reset_n   <=  1'b0;
        repeat(delay) begin
            @(reset_if_inst.reset_cb);
        end
        reset_if_inst.reset_n   <=  1'b1;
    endfunction : trigger_warm_reset

    function drive_reset_n (bit reset_value);
        @(reset_if_inst.reset_cb);
        reset_if_inst.reset_n   <= reset_value;
    endfunction: drive_reset_n
*/
endclass    : reset_driver
