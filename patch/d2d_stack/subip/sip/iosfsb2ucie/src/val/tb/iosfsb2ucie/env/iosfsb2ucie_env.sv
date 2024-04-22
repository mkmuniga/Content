
`ifndef IOSFSB_UVM
      `define IOSFSB_UVM
`endif

   `include "iosfsb2ucie_defines.vh"
   import uciesbbfm_env_pkg::*;
class iosfsb2ucie_env extends uvm_env;

  iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_fabric_vc_gpsb_ep,iosf_sbc_fabric_vc_gpsb_tunl,iosf_sbc_fabric_vc_pmsb_tunl;
  
`uvm_component_utils(iosfsb2ucie_env)
vwi_agent vwi_agent_inst0;
`ifdef SB2UCIE_TB
pm_agent pm_agent_inst0;
sec_agent sec_agent_inst0;
ras_agent ras_agent_inst0;
reset_agent reset_agent_inst0;
pmon_agent pmon_agent_inst0;
qchan_agent qchan_agent_inst0;
qchan_config qchan_cfg_inst0;
`endif
virtual qchan_controller_if ctrl_vif;
rdi_agent rdi_agent_inst0;
//cbb hotfix dtf_vc_env dtf_master;
//cbb hotfix dtf_vc_env dtf_slave;
logic [`V_WIRES_IN-1:0] default_strap_vlw_in;
logic [`V_WIRES_OUT-1:0] default_strap_vlw_out;
string comp_name;
iosfsbm_cm::opcode_t fab_gpsb_simple_opcodes_1,fab_gpsb_simple_opcodes_2, fab_gpsb_simple_opcodes_queue[$];
iosfsbm_cm::opcode_t fab_gpsb_msgd_opcodes_1,fab_gpsb_msgd_opcodes_2, fab_gpsb_msgd_opcodes_queue[$];
iosfsbm_cm::opcode_t fab_pmsb_simple_opcodes_1,fab_pmsb_simple_opcodes_2, fab_pmsb_simple_opcodes_queue[$];
iosfsbm_cm::opcode_t fab_pmsb_msgd_opcodes_1,fab_pmsb_msgd_opcodes_2, fab_pmsb_msgd_opcodes_queue[$];

function new(string name = "iosfsb2ucie_env", uvm_component parent = null);
  super.new(name, parent);

endfunction : new


function void build_phase(uvm_phase phase);

    // ============================================================================
    //Configuration
    // ============================================================================
    //iosfsbm_fbrc::fbrcvc_cfg fabric_cfg_gpsb_ep,fabric_cfg_gpsb_tunl,fabric_cfg_pmsb_tunl;



       super.build_phase(phase);
    `uvm_info ("iosfsb2ucie_env",$sformatf("Building top level env"),UVM_NONE)
    comp_name = "Fabric_VC";
    `uvm_info ("iosfsb2ucie_env",$sformatf("Creating Fabric VCs %s", comp_name),UVM_NONE)

    //fabric_cfg_gpsb_ep    = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_gpsb_ep", this);
    //fabric_cfg_gpsb_tunl  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_gpsb_tunl", this);
    //fabric_cfg_pmsb_tunl  = iosfsbm_fbrc::fbrcvc_cfg::type_id::create("fabric_cfg_pmsb_tunl", this);
    //if (!uvm_config_db #(iosfsbm_fbrc::fbrcvc_cfg)::get(this,"","fabric_cfg_gpsb_ep",fabric_cfg_gpsb_ep))
    //   `uvm_fatal(get_type_name(), "No handle to fabric_cfg_gpsb_ep")
    //if (!uvm_config_db #(iosfsbm_fbrc::fbrcvc_cfg)::get(this,"","fabric_cfg_gpsb_tunl",fabric_cfg_gpsb_tunl))
    //   `uvm_fatal(get_type_name(), "No handle to fabric_cfg_gpsb_tunl")
    //if (!uvm_config_db #(iosfsbm_fbrc::fbrcvc_cfg)::get(this,"","fabric_cfg_pmsb_tunl",fabric_cfg_pmsb_tunl))
    //   `uvm_fatal(get_type_name(), "No handle to fabric_cfg_pmsb_tunl")


    //assert( $cast(iosf_sbc_fabric_vc_gpsb_ep, create_component("iosfsbm_fbrc::iosfsbm_fbrcvc", comp_name)) )
    //    else `uvm_fatal ("iosfsb2ucie_env","CASTING type mismatch in creating Fabric VC")
    iosf_sbc_fabric_vc_gpsb_ep = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_gpsb_ep", this);
    iosf_sbc_fabric_vc_gpsb_tunl = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_gpsb_tunl", this);
    iosf_sbc_fabric_vc_pmsb_tunl = iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_fabric_vc_pmsb_tunl", this);

    iosf_sbc_fabric_vc_gpsb_ep.cfg_name     = "fabric_cfg_gpsb_ep";
    iosf_sbc_fabric_vc_gpsb_tunl.cfg_name   = "fabric_cfg_gpsb_tunl";
    iosf_sbc_fabric_vc_pmsb_tunl.cfg_name   = "fabric_cfg_pmsb_tunl";    

`ifdef SB2UCIE_TB

// GPSB
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","gpsb_simple_opcodes_1",fab_gpsb_simple_opcodes_1))
       `uvm_fatal(get_type_name(), "No handle to fab_gpsb_simple_opcodes_1")
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","gpsb_simple_opcodes_2",fab_gpsb_simple_opcodes_2))
       `uvm_fatal(get_type_name(), "No handle to fab_gpsb_simple_opcodes_2")

    fab_gpsb_simple_opcodes_queue.push_back(fab_gpsb_simple_opcodes_1);  //SYNC
    fab_gpsb_simple_opcodes_queue.push_back(fab_gpsb_simple_opcodes_2);  //DELAY_REQ

    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","gpsb_msgd_opcodes_1",fab_gpsb_msgd_opcodes_1))
       `uvm_fatal(get_type_name(), "No handle to fab_gpsb_msgd_opcodes_1")
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","gpsb_msgd_opcodes_2",fab_gpsb_msgd_opcodes_2))
       `uvm_fatal(get_type_name(), "No handle to fab_gpsb_msgd_opcodes_2")

    fab_gpsb_msgd_opcodes_queue.push_back(fab_gpsb_msgd_opcodes_1);  //FOLLOW_UP
    fab_gpsb_msgd_opcodes_queue.push_back(fab_gpsb_msgd_opcodes_2);  //DELAY_RSP

    iosf_sbc_fabric_vc_gpsb_tunl.register_cb(iosfsbm_cm::SIMPLE, fab_gpsb_simple_opcodes_queue);
    iosf_sbc_fabric_vc_gpsb_tunl.register_cb(iosfsbm_cm::MSGD, fab_gpsb_msgd_opcodes_queue);

//PMSB
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","pmsb_simple_opcodes_1",fab_pmsb_simple_opcodes_1))
       `uvm_fatal(get_type_name(), "No handle to fab_pmsb_simple_opcodes_1")
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","pmsb_simple_opcodes_2",fab_pmsb_simple_opcodes_2))
       `uvm_fatal(get_type_name(), "No handle to fab_pmsb_simple_opcodes_2")

    fab_pmsb_simple_opcodes_queue.push_back(fab_pmsb_simple_opcodes_1);  //SYNC
    fab_pmsb_simple_opcodes_queue.push_back(fab_pmsb_simple_opcodes_2);  //DELAY_REQ

    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","pmsb_msgd_opcodes_1",fab_pmsb_msgd_opcodes_1))
       `uvm_fatal(get_type_name(), "No handle to fab_pmsb_msgd_opcodes_1")
    if (!uvm_config_db #(iosfsbm_cm::opcode_t)::get(this,"","pmsb_msgd_opcodes_2",fab_pmsb_msgd_opcodes_2))
       `uvm_fatal(get_type_name(), "No handle to fab_pmsb_msgd_opcodes_2")

    fab_pmsb_msgd_opcodes_queue.push_back(fab_pmsb_msgd_opcodes_1);  //FOLLOW_UP
    fab_pmsb_msgd_opcodes_queue.push_back(fab_pmsb_msgd_opcodes_2);  //DELAY_RSP

    iosf_sbc_fabric_vc_pmsb_tunl.register_cb(iosfsbm_cm::SIMPLE, fab_pmsb_simple_opcodes_queue);
    iosf_sbc_fabric_vc_pmsb_tunl.register_cb(iosfsbm_cm::MSGD, fab_pmsb_msgd_opcodes_queue);


    vwi_agent_inst0    = vwi_agent::type_id::create("vwi_agent_inst0",this);
    pm_agent_inst0     = pm_agent::type_id::create("pm_agent_inst0",this);
    ras_agent_inst0     = ras_agent::type_id::create("ras_agent_inst0",this);    
    sec_agent_inst0    = sec_agent::type_id::create("sec_agent_inst0",this); 
    reset_agent_inst0    = reset_agent::type_id::create("reset_agent_inst0",this); 
    pmon_agent_inst0    = pmon_agent::type_id::create("pmon_agent_inst0",this);

    ucie_pkt_subscriber_inst = ucie_pkt_subscriber::type_id::create("ucie_pkt_subscriber_inst",this);

    qchan_cfg_inst0 = qchan_config::type_id::create("qchan_cfg_inst0");
 
    assert(qchan_cfg_inst0) else `uvm_fatal(get_type_name(),"unable to build qchannel config")

    if(!uvm_config_db#(virtual qchan_controller_if)::get(this, "", "qchan_controller_vif", qchan_cfg_inst0.ctrl_vif)) begin
        `uvm_fatal("no_qchan_if", $psprintf("You must pass a valid interface for qchan_controller_vif"))
    end
    if (qchan_cfg_inst0.ctrl_vif == null) begin
        `uvm_fatal("null_virtual_qchan_if", $psprintf("You must pass a valid virtual qchan_if for qchan_controller_vif"))
    end

    qchan_cfg_inst0.is_active       = UVM_ACTIVE;
    qchan_cfg_inst0.master_slave    = Q_MASTER;
    qchan_cfg_inst0.b2b_mode        = OFF;      //TODO: check what is this?
    qchan_cfg_inst0.qactive_present = 0;        //SB2UCIE does not have qactive, qdeny
    
    uvm_config_db#(qchan_config)::set(this, "qchan_agent_inst0", "qchan_agent_inst0_config", qchan_cfg_inst0);
    
     qchan_agent_inst0   = qchan_agent::type_id::create("qchan_agent_inst0",this);
    assert(qchan_agent_inst0) else `uvm_fatal(get_type_name(),"unable to build qchannel agent")


`endif

    uvm_config_db#(int)::set(null, "*", "num_lanes", `MAX_LANES);
    rdi_agent_inst0    = rdi_agent::type_id::create("rdi_agent_inst0",this);

//cbb hotfix    dtf_master = dtf_vc_env::type_id::create("dtf_master", this);
//cbb hotfix    dtf_slave = dtf_vc_env::type_id::create("dtf_slave", this);   
 endfunction: build_phase

function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    `uvm_info(get_name(), "env: connect_phase", UVM_NONE);
    `ifdef SB2UCIE_TB
    rdi_agent_inst0.rdi_mon.mon_analysis_port.connect(vwi_agent_inst0.vwi_driver_inst.port_ucie_pkt);
    rdi_agent_inst0.rdi_mon.mon_analysis_port.connect(ucie_pkt_subscriber_inst.lp_ucie_pkt_port);
    rdi_agent_inst0.rdi_mon.mon_pl_analysis_port.connect(ucie_pkt_subscriber_inst.pl_ucie_pkt_port);
    `endif

endfunction: connect_phase

// Setting a bit to differenitate the Interface in monitor level


function void end_of_elaboration_phase(uvm_phase phase);
	super.end_of_elaboration_phase(phase);
`ifdef SB2UCIE_TB
 vwi_agent_inst0.vwi_monitor_inst.intf_inst = 0; 
`endif
    uvm_config_db#(int)::set(null, "*", "num_lanes", `MAX_LANES);

endfunction : end_of_elaboration_phase

   task run_phase(uvm_phase phase);
        string svc_log_name1, svc_log_name2;
        super.run_phase(phase);

        $sformat(svc_log_name1, "%s.gpsb_tunl_trk.log", get_full_name());
        iosf_sbc_fabric_vc_gpsb_tunl.load_opcode_name('hb0, "SYNC");
        iosf_sbc_fabric_vc_gpsb_tunl.load_opcode_name('hb1, "DELAY_REQ");
        iosf_sbc_fabric_vc_gpsb_tunl.load_opcode_name('h70, "FOLLOW_UP");
        iosf_sbc_fabric_vc_gpsb_tunl.load_opcode_name('h74, "DELAY_RSP");
        iosf_sbc_fabric_vc_gpsb_tunl.open_tracker_file(.file_name(svc_log_name1),
                                                    .trk_fmt(iosfsbm_cm::SIP_FMT),
                                                    .print_reset_state(1'b1),
                                                    .print_clock_state(1'b0),
                                                    .print_ism_state(1'b1),
                                                    .print_opc_name(1'b1),
                                                    .print_pid_name(1'b0)); 



        $sformat(svc_log_name1, "%s.pmsb_tunl_trk.log", get_full_name());
        iosf_sbc_fabric_vc_pmsb_tunl.load_opcode_name('hb0, "SYNC");
        iosf_sbc_fabric_vc_pmsb_tunl.load_opcode_name('hb1, "DELAY_REQ");
        iosf_sbc_fabric_vc_pmsb_tunl.load_opcode_name('h70, "FOLLOW_UP");
        iosf_sbc_fabric_vc_pmsb_tunl.load_opcode_name('h74, "DELAY_RSP");
        iosf_sbc_fabric_vc_pmsb_tunl.open_tracker_file(.file_name(svc_log_name1),
                                                    .trk_fmt(iosfsbm_cm::SIP_FMT),
                                                    .print_reset_state(1'b1),
                                                    .print_clock_state(1'b0),
                                                    .print_ism_state(1'b1),
                                                   .print_opc_name(1'b1),
                                                    .print_pid_name(1'b0)); 



					     $sformat(svc_log_name1, "%s.gpsb_reg_ep_trk.log", get_full_name());
        iosf_sbc_fabric_vc_gpsb_ep.open_tracker_file(.file_name(svc_log_name1),
                                                    .trk_fmt(iosfsbm_cm::SIP_FMT),
                                                    .print_reset_state(1'b1),
                                                    .print_clock_state(1'b0),
                                                    .print_ism_state(1'b1),
                                                   .print_opc_name(1'b1),
                                                    .print_pid_name(1'b0)); 


    endtask : run_phase
endclass: iosfsb2ucie_env



