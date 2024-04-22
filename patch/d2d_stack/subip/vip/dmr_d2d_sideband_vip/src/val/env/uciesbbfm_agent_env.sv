class uciesbbfm_agent_env extends uvm_env;
    `uvm_component_utils(uciesbbfm_agent_env)

    //Put env cfg, agent, scoreboards here
    uciesbbfm_agent sbbfm_agent;
    uciesbbfm_config sbbfm_cfg;

//cbb hotfix     dtf_vc_env dtf_master;
//cbb hotfix     dtf_vc_env dtf_slave;

//cbb hotfix     sbbfm_dtf_vc_primary_stall_driver dtf_primary_stall;


    //See if you can put IOSF SVC BFM connections here
    //IOSF SVC components
    `iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_gpsb_fabric_vc_i;
    `iosfsbm_fbrc::fbrcvc_cfg        gpsb_fabric_cfg_i;
    `iosfsbm_fbrc::iosfsbm_fbrcvc    iosf_sbc_pmsb_fabric_vc_i;
    `iosfsbm_fbrc::fbrcvc_cfg        pmsb_fabric_cfg_i;
    int gpsb_indices[$], pmsb_indices[$];

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        string path;
        `iosfsbm_cm::pid_t gpsb_fab_my_ports[$], gpsb_fab_other_ports[$],pmsb_fab_my_ports[$], pmsb_fab_other_ports[$], fab_mcast_ports[$];
        `iosfsbm_cm::opcode_t gpsb_supp_opcodes[$], pmsb_supp_opcodes[$];
        `iosfsbm_cm::opcode_t gpsb_simple_opcodes[$], pmsb_simple_opcodes[$];
        `iosfsbm_cm::opcode_t gpsb_msgd_opcodes[$], pmsb_msgd_opcodes[$];


        super.build_phase(phase);
        //TODO Not sure if the names here need to be uniquified or if the ENV_PATH will be different.
       uvm_config_db#(int)::set(this, "sbbfm_agent", "is_agent", UVM_ACTIVE);
//cbb hotfix       set_config_int("sbbfm_agent","is_agent",UVM_ACTIVE); //trial
        if (!uvm_config_db #(uciesbbfm_config)::get(this, "", "sbbfm_cfg", sbbfm_cfg))
            `uvm_fatal(get_type_name(), "Didn't get handle to m_env_cfg")
        sbbfm_agent = uciesbbfm_agent::type_id::create("sbbfm_agent", this);
        sbbfm_agent.sbbfm_cfg = sbbfm_cfg;
        gpsb_indices= sbbfm_cfg.gpsb_indices;
        pmsb_indices= sbbfm_cfg.pmsb_indices;

        foreach (gpsb_indices[ports]) begin
            gpsb_fab_my_ports.push_back(2*gpsb_indices[ports] + 1);
            gpsb_fab_other_ports.push_back(2*gpsb_indices[ports]);
        end

        foreach (pmsb_indices[ports]) begin
            pmsb_fab_my_ports.push_back(2*pmsb_indices[ports] + 1);
            pmsb_fab_other_ports.push_back(2*pmsb_indices[ports]);
        end

        iosf_sbc_gpsb_fabric_vc_i = `iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_gpsb_fabric_vc_i", this);
        iosf_sbc_pmsb_fabric_vc_i = `iosfsbm_fbrc::iosfsbm_fbrcvc::type_id::create("iosf_sbc_pmsb_fabric_vc_i", this);

        //Adding GPSB supported opcodes
        //Time sync simple opcodes
        gpsb_simple_opcodes.push_back('hb0);  //SYNC
        gpsb_simple_opcodes.push_back('hb1);  //DELAY_REQ
        gpsb_msgd_opcodes.push_back('h70); //FOLLOW_UP
        gpsb_msgd_opcodes.push_back('h74); //DELAY_RSP
        gpsb_msgd_opcodes.push_back('h60); //MCTPoSB 
        //RAS opcodes
        gpsb_msgd_opcodes.push_back('h46); //MCA 
        gpsb_msgd_opcodes.push_back('h49); //PCIE_ERR 
        gpsb_simple_opcodes.push_back('h88); //DO_SERR -> TODO simple opcodes
        gpsb_msgd_opcodes.push_back('h64); //CORR_AER or PCH_EVENT 
        gpsb_msgd_opcodes.push_back('h65); //UNCORR_AER 
        gpsb_msgd_opcodes.push_back('h66); //FBMCA 
        gpsb_msgd_opcodes.push_back('h6E); //INTER_RASIP_MSG
        gpsb_msgd_opcodes.push_back('h7C);//RAS_NCU_MSG

        //Patching Flows opcodes
        gpsb_simple_opcodes.push_back('hA3);  // DEVARBREQ
        gpsb_simple_opcodes.push_back('hA4);  // DEVARBGNT
        gpsb_simple_opcodes.push_back('hA5);  // DEVARBREL
        gpsb_simple_opcodes.push_back('hA6);  // DEVARBRELREQ
        gpsb_msgd_opcodes.push_back('h63);  // GET_PATCH
        gpsb_msgd_opcodes.push_back('h6C);  // PATCH_LOAD
        gpsb_msgd_opcodes.push_back('h6D);  // PATCH_CONTENT
        gpsb_msgd_opcodes.push_back('h7B);  // PATCH_LOAD_ACK
                
        //Security related opcodes
        gpsb_msgd_opcodes.push_back('h67);  // VERIFY_PAYLOAD
        gpsb_msgd_opcodes.push_back('h7A);  // SERVICE_SYNC

        //Register GPSB opcode callbacks
        iosf_sbc_gpsb_fabric_vc_i.register_cb(`iosfsbm_cm::SIMPLE, gpsb_simple_opcodes);
        iosf_sbc_gpsb_fabric_vc_i.register_cb(`iosfsbm_cm::MSGD, gpsb_msgd_opcodes);

        //Adding opcodes to GPSB supported opcodes
        gpsb_supp_opcodes = {`iosfsbm_cm::DEFAULT_OPCODES, gpsb_simple_opcodes, gpsb_msgd_opcodes};

        //Adding PMSB supported opcodes
        pmsb_msgd_opcodes.push_back('h68); //PM2IP
        pmsb_msgd_opcodes.push_back('h7E); //IP2PM
        pmsb_supp_opcodes = {`iosfsbm_cm::DEFAULT_OPCODES, pmsb_simple_opcodes, pmsb_msgd_opcodes};

        fab_mcast_ports = '{'h20};

        //GPSB Fabric ENV setup
        gpsb_fabric_cfg_i = `iosfsbm_fbrc::fbrcvc_cfg::type_id::create("gpsb_fabric_cfg", this);
        uvm_config_object::set(null,"","gpsb_fabric_cfg",gpsb_fabric_cfg_i);
        uvm_config_db#(string)::get(this, "", "hier_path", path);
        $sformat(gpsb_fabric_cfg_i.inst_name, "%s.gpsb_fabric_ti", path);
        gpsb_fabric_cfg_i.set_iosfspec_ver(`iosfsbm_cm::IOSF_12);



        if(!gpsb_fabric_cfg_i.randomize with {
                                       gpsb_fabric_cfg_i.num_tx_ext_headers == 1;
                                       gpsb_fabric_cfg_i.payload_width == 32;
                                       gpsb_fabric_cfg_i.compl_delay == 1;
                                       gpsb_fabric_cfg_i.my_ports.size() == gpsb_fab_my_ports.size();
                                       gpsb_fabric_cfg_i.other_ports.size() == gpsb_fab_other_ports.size();
                                       gpsb_fabric_cfg_i.mcast_ports.size() == fab_mcast_ports.size();
                                       foreach (gpsb_fab_my_ports[i])
                                         gpsb_fabric_cfg_i.my_ports[i] == gpsb_fab_my_ports[i];
                                       foreach (gpsb_fab_other_ports[i])
                                         gpsb_fabric_cfg_i.other_ports[i] == gpsb_fab_other_ports[i];
                                       foreach (fab_mcast_ports[i])
                                         gpsb_fabric_cfg_i.mcast_ports[i] == fab_mcast_ports[i];
                                       })
            `uvm_fatal(get_name(), "Unable to randomize gpsb fabric cfg obj")

        gpsb_fabric_cfg_i.supported_opcodes = gpsb_supp_opcodes;



        iosf_sbc_gpsb_fabric_vc_i.cfg_name = "gpsb_fabric_cfg";



        //PMSB Fabric ENV setup
        pmsb_fabric_cfg_i = `iosfsbm_fbrc::fbrcvc_cfg::type_id::create("pmsb_fabric_cfg", this);
        uvm_config_object::set(null,"","pmsb_fabric_cfg",pmsb_fabric_cfg_i);
        $sformat(pmsb_fabric_cfg_i.inst_name, "%s.pmsb_fabric_ti", path);
        pmsb_fabric_cfg_i.set_iosfspec_ver(`iosfsbm_cm::IOSF_12);


        if(!pmsb_fabric_cfg_i.randomize with {
                                       pmsb_fabric_cfg_i.num_tx_ext_headers == 1;
                                       pmsb_fabric_cfg_i.payload_width == 32;
                                       pmsb_fabric_cfg_i.compl_delay == 1;
                                       pmsb_fabric_cfg_i.my_ports.size() == pmsb_fab_my_ports.size();
                                       pmsb_fabric_cfg_i.other_ports.size() == pmsb_fab_other_ports.size();
                                       pmsb_fabric_cfg_i.mcast_ports.size() == fab_mcast_ports.size();
                                       foreach (pmsb_fab_my_ports[i])
                                         pmsb_fabric_cfg_i.my_ports[i] == pmsb_fab_my_ports[i];
                                       foreach (pmsb_fab_other_ports[i])
                                         pmsb_fabric_cfg_i.other_ports[i] == pmsb_fab_other_ports[i];
                                       foreach (fab_mcast_ports[i])
                                         pmsb_fabric_cfg_i.mcast_ports[i] == fab_mcast_ports[i];
                                       })
            `uvm_fatal(get_name(), "Unable to randomize pmsb fabric cfg obj")



        iosf_sbc_pmsb_fabric_vc_i.cfg_name = "pmsb_fabric_cfg";
        pmsb_fabric_cfg_i.supported_opcodes = pmsb_supp_opcodes;


        pmsb_fabric_cfg_i.ext_header_support = 1;
        pmsb_fabric_cfg_i.agt_ext_header_support = 1;
        pmsb_fabric_cfg_i.ext_headers_per_txn = 1;
        pmsb_fabric_cfg_i.np_crd_buffer = 15;
        pmsb_fabric_cfg_i.pc_crd_buffer = 15;
        pmsb_fabric_cfg_i.use_mem = 1;

        gpsb_fabric_cfg_i.ext_header_support  = 1;
        gpsb_fabric_cfg_i.agt_ext_header_support = 1;
        gpsb_fabric_cfg_i.ext_headers_per_txn = 1;
        gpsb_fabric_cfg_i.np_crd_buffer = 15;
        gpsb_fabric_cfg_i.pc_crd_buffer = 15;
        gpsb_fabric_cfg_i.use_mem  = 1;
        gpsb_fabric_cfg_i.m_max_data_size = 24;
        gpsb_fabric_cfg_i.opcode_SpiRd = 'h61;

//cbb hotfix         //DTF VC integration
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "DTF_VC_ACTIVE", 1);
//cbb hotfix         uvm_config_db#(string)::set(this, "dtf_master*", "DTF_VC_LEG_NAME", {get_full_name(), ".DTF_PRIMARY"});
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "CREDIT_DEPTH", 32);
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "DTF_VC_MASTER", 1);
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "DTF_ARB_WIDTH", 8);
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "MIN_DTF_CREDIT_DELAY", 0);
//cbb hotfix         uvm_config_int::set(this, "dtf_master*", "MAX_DTF_CREDIT_DELAY", 2);
//cbb hotfix         uvm_config_string::set(this, "dtf_master*", "DTF_INT_IP_TRK_NAME", {get_full_name(), ".DTF_PRIMARY_TRK.log"});
//cbb hotfix         dtf_master = dtf_vc_env::type_id::create("dtf_master", this);
//cbb hotfix 
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "DTF_VC_ACTIVE", 1);
//cbb hotfix         uvm_config_db#(string)::set(this, "dtf_slave*", "DTF_VC_LEG_NAME", {get_full_name(), ".DTF_SECONDARY"});
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "CREDIT_DEPTH", 32);
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "DTF_VC_MASTER", 0);
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "DTF_ARB_WIDTH", 8);
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "MIN_DTF_CREDIT_DELAY", 0);
//cbb hotfix         uvm_config_int::set(this, "dtf_slave*", "MAX_DTF_CREDIT_DELAY", 2);
//cbb hotfix         uvm_config_string::set(this, "dtf_slave*", "DTF_INT_IP_TRK_NAME", {get_full_name(), ".DTF_SECONDARY_TRK.log"});
//cbb hotfix         dtf_slave = dtf_vc_env::type_id::create("dtf_slave", this);
//cbb hotfix 
//cbb hotfix         dtf_primary_stall = sbbfm_dtf_vc_primary_stall_driver::type_id::create("dtf_primary_stall", this);
//cbb hotfix         if(!uvm_config_db#(virtual dtf_vc_if)::get(this, "dtf_master", "dtf_vc_if", dtf_primary_stall.dtf_primary_if))
//cbb hotfix             `uvm_fatal(get_name(), "Could not find dtf_vc_if in this scope")

       
    endfunction : build_phase

    function void register_gpsb_opcodes();

    endfunction 


    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if(sbbfm_agent.d2d_TA_scbd_disable!=1) begin
            iosf_sbc_gpsb_fabric_vc_i.rx_ap.connect(sbbfm_agent.TA_scbd.rcvd_msgs.analysis_export);
            iosf_sbc_gpsb_fabric_vc_i.tx_ap.connect(sbbfm_agent.TA_scbd.txd_msgs.analysis_export);
        end

//cbb hotfix        dtf_primary_stall.dtf_primary = dtf_master;
    endfunction: connect_phase


    task run_phase(uvm_phase phase);
        string svc_log_name;
        super.run_phase(phase);

        $sformat(svc_log_name, "%s.gpsb_fab_trk.log", get_full_name());
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hb0, "SYNC");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hb1, "DELAY_REQ");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h70, "FOLLOW_UP");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h74, "DELAY_RSP");

        //RAS opcodes
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h46, "GPSB_MCA");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h49, "PCIE_ERR");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h88, "DO_SERR");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h66, "FBMCA");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h64, "CORR_AER");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h65, "UNCORR_AER");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h6E, "INTER_RASIP");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h7C, "RAS_NCU_MSG");

        //iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h64, "PCH_EVENT");

        //Patching Flows opcodes
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hA3, "DEVARBREQ");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hA4, "DEVARBGNT");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hA5, "DEVARBREL");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('hA6, "DEVARBRELREQ");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h63, "GET_PATCH");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h6C, "PATCH_LOAD");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h6D, "PATCH_CONTENT");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h7B, "PATCH_LOAD_ACK");
                
        //Security related opcodes
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h67, "VERIFY_PAYLOAD");
        iosf_sbc_gpsb_fabric_vc_i.load_opcode_name('h7A, "SERVICE_SYNC");

//cbb hotfix        iosf_sbc_gpsb_fabric_vc_i.open_tracker_file(.file_name(svc_log_name),
//cbb hotfix                                                    .trk_fmt(`iosfsbm_cm::SIP_FMT),
//cbb hotfix                                                    .print_reset_state(1'b1),
//cbb hotfix                                                    .print_clock_state(1'b0),
//cbb hotfix                                                    .print_ism_state(1'b1),
//cbb hotfix                                                    .print_opc_name(1'b1),
//cbb hotfix                                                    .print_pid_name(1'b0));

        $sformat(svc_log_name, "%s.pmsb_fab_trk.log", get_full_name());
        iosf_sbc_pmsb_fabric_vc_i.load_opcode_name('h68, "PM2IP");
        iosf_sbc_pmsb_fabric_vc_i.load_opcode_name('h7E, "IP2PM");
        
//cbb hotfix        iosf_sbc_pmsb_fabric_vc_i.open_tracker_file(.file_name(svc_log_name),
//cbb hotfix                                                    .trk_fmt(`iosfsbm_cm::SIP_FMT),
//cbb hotfix                                                    .print_reset_state(1'b1),
//cbb hotfix                                                    .print_clock_state(1'b0),
//cbb hotfix                                                    .print_ism_state(1'b1),
//cbb hotfix                                                    .print_opc_name(1'b1),
//cbb hotfix                                                    .print_pid_name(1'b0));

    endtask : run_phase

    task do_resetprep();
        sbbfm_agent.do_resetprep();
    endtask;
    task undo_resetprep();
        sbbfm_agent.undo_resetprep();
    endtask;


endclass : uciesbbfm_agent_env
