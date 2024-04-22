///=====================================================================================================================
/// File name           : cfi_obs_env.sv
///
/// Primary Contact     : yuvalman
/// Secondary Contact   :
/// Creation Date       : 2020
/// Last Review Date:
///
/// Copyright (c) 2018 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
/// CFI_OBS Soala IP env.
/// This is the main IP env file.
/// In this file the IP declare, build and connects the different IP's agents and VCs.
///=====================================================================================================================


class cfi_obs_env extends client_sla_tb_env;

    string CFGDB_UP_PATH = "main::cfi_obs";
    // Pickers
    cfi_obs_picker picker;
    cfi_obs_stress_modes_picker stress_picker;
    cfi_obs_agent_switches_picker agnt_sw_picker;
    string cfi_obs_sideband_access = "sideband";
    string cfi_vc_sequencer_name_array[string][IfType][int];
    string cfi_obs_sb_sqr_name = "cfi_obs_sb_sqr";
    string cfi_obs_ti_path = "cfi_obs_tb.u_cfi_obs_ti";
    int local_clk_measured;
    int gv_local_clk_measured;
    my_uvm_default_report_server m_my_report_server;
    //clock vc
    real clks_freq[3];
    real gv_clk_freq;
    
    `uvm_component_utils_begin(cfi_obs_env)
        `uvm_field_string(cfi_obs_ti_path, UVM_ALL_ON)
        `uvm_field_string(cfi_obs_sideband_access, UVM_ALL_ON)
        `uvm_field_string(CFGDB_UP_PATH, UVM_ALL_ON)
    `uvm_component_utils_end

    // Variable: _cfi_obs_env
    // static pointer to the env
    static cfi_obs_env _cfi_obs_env;

    // Variable: cfi_obs_if
    // CFI_OBS env interface
    virtual cfi_obs_env_if cfi_obs_if;

    // regmodel
    cfi_obs_regmodel_block cfi_obs_regmodel;
    cfi_obs_ral_functions cfi_obs_ral_func;

    // ***************************************************************
    // Variable: CFI_OBSevPool
    // CFI_OBS event pool
    // ***************************************************************
    uvm_event_pool CFI_OBSevPool;

    //CFI_OBS coverage component
    //cfi_obs_coverage cfi_obs_cov;

    // ***************************************************************
    // PA Agents decleration
    // ***************************************************************
    cfi_obs_pa_agent   CFI_OBS_rx_pa;
    cfi_obs_pa_agent   CFI_OBS_tx_pa;
    cfi_obs_pa_config  CFI_OBS_rx_pa_cfg;
    cfi_obs_pa_config  CFI_OBS_tx_pa_cfg;

    // ***************************************************************
    // DEBUG_FABRIC Agent decleration
    // ***************************************************************
    dtf_vc_env      rx_dtf_vc_out;
    dtf_vc_env      tx_dtf_vc_out;
    dtf_env_tracker rx_dtf_tracker_inst;
    dtf_env_tracker tx_dtf_tracker_inst;

    // ***************************************************************
    // GS Agents decleration
    // ***************************************************************
    gs_agent CFI_OBS_RX_generic_sniffer;
    gs_agent CFI_OBS_TX_generic_sniffer;

    // ***************************************************************
    // CCU - clock control unit instantiation
    // ***************************************************************
    ccu_vc     cfi_obs_ccu_vc;
    ccu_vc_cfg cfi_obs_ccu_vc_cfg;

    // ***************************************************************
    // CFI AGENTS 
    // ***************************************************************
    //CFI VC agents
    cfi_vc_agent rx_cfi_vc_agent_l[$];
    cfi_vc_agent tx_cfi_vc_agent_l[$];
    //CFI VC config objects
    cfi_vc_config rx_cfi_vc_agent_cfg_l[$];
    cfi_vc_config tx_cfi_vc_agent_cfg_l[$];
    
    // ***************************************************************
    // CXM AGENTS 
    // ***************************************************************
    //CXM VC agents
    cxm_vc_agent cxm_requestor;
    cxm_vc_agent cxm_responder;
    //CXM VC config objects
    cxm_vc_config cxm_requestor_cfg;
    cxm_vc_config cxm_responder_cfg;
    
    // ***************************************************************
    // UPI BFM
    // ***************************************************************
    uxi::BfmEnv        upi_bfm;
    UpiUtils           utils;
    Tunneled_Response  tunnle_responses;
    uxi::cfi_tx_map    out_map;
    uxi::cfi_rx_map    in_map;    
    
    // ***************************************************************


    covergroup cfi_obs_clk_cg;
        option.per_instance =1;
        CLK_FREQ : coverpoint local_clk_measured {
            bins FREQ_100_400_freq_MHZ = {[2500:10000]};
            bins FREQ_400_700_freq_MHZ = {[1428:2500]};
            bins FREQ_700_1000_freq_MHZ = {[1000:1428]};
            bins FREQ_1000_1300_freq_MHZ = {[769:1000]};
            bins FREQ_1300_1600_freq_MHZ = {[625:769]};
            bins FREQ_1600_1900_freq_MHZ = {[526:625]};
            bins FREQ_1900_2200_freq_MHZ = {[454:526]};
        }
        GV_CLK_FREQ : coverpoint gv_local_clk_measured {
            bins FREQ_100_400_freq_MHZ = {[2500:10000]};
            bins FREQ_400_700_freq_MHZ = {[1428:2500]};
            bins FREQ_700_1000_freq_MHZ = {[1000:1428]};
            bins FREQ_1000_1300_freq_MHZ = {[769:1000]};
            bins FREQ_1300_1600_freq_MHZ = {[625:769]};
            bins FREQ_1600_1900_freq_MHZ = {[526:625]};
            bins FREQ_1900_2200_freq_MHZ = {[454:526]};
        }

        CLK_FREQ_X_GV_CLK_FREQ : cross CLK_FREQ,GV_CLK_FREQ;

    endgroup : cfi_obs_clk_cg


    extern function build_cfi_obs_regmodel();
    extern function void init_cfi_obs_agent_switches_picker_from_configdb( ref cfi_obs_agent_switches_picker picker, string configDB_path);
    extern function void init_cfi_obs_picker_from_configdb( ref cfi_obs_picker picker, string configDB_path);
    extern function void init_cfi_obs_stress_modes_picker_from_configdb( ref cfi_obs_stress_modes_picker picker, string configDB_path);
    extern function void create_csi_stuff(bit loadConfigDB_required = 0);
    extern function void build_ccu_vc();
    extern function void create_clk();
    extern function void build_cfi_vc(int idx);
    extern function void build_cxm_vc(int idx);
    extern function void build_upi_vc(int idx);
    extern function void build_pa_agent();
    extern function void build_gs_agent();
    extern function void build_dtf_agent();
    extern function void add_ccu_vc_sequencer();
    extern function void add_sideband_sequencer();
    extern function void connect_sideband_vc();
    extern function void connect_cfi_vc(int idx);
    extern function void connect_pa_agent(int idx);
    extern function void connect_gs_agent();
    extern function void add_cxm_vc_sequencer();
    extern function void add_cfi_vc_rx_sequencer(string agent_name, IfType it, int num, int idx);
    extern function void add_cfi_vc_tx_sequencer(string agent_name, IfType it, int num, int idx);
    extern task sample_clk_cov();

    //----------------------------------------------------------------------
    function new (string name = "cfi_obs_env", uvm_component parent = null);
        super.new(name, parent);

        // Setting the env static pointer
        _cfi_obs_env = this;
        cfi_obs_clk_cg = new();
        cfi_obs_clk_cg.set_inst_name({get_full_name(), ".cfi_obs_clk_cg"});   
    endfunction : new

    //----------------------------------------------------------------------
    function void build_report_server();
          // Create and configure my_report_server
          m_my_report_server = new();
          m_my_report_server.set_post_err_timeout(50000);
          uvm_report_server::set_server(m_my_report_server);
      endfunction

    // ***************************************************************
    // CFI_OBS ENV UVM phases functions / tasks
    // ***************************************************************

    //*******************************************************
    // FunctIon: cfi_obs_env build
    // build phase of cfi_obs_env
    // All VC's and Agent should be build in this phase.
    // For each new VC's/Agent it is recommended to add it an a specific function
    //*******************************************************
    virtual function void build_phase(uvm_phase phase);


        if (_level == SLA_TOP) begin

            uvm_report_server l_rs = uvm_report_server::get_server();
            build_report_server();
            // In this section all the IP specific stuff that are
            // relevant only when the IP is stand alone should be set
            sm_type = "cfi_obs_sm_env";
            im_type = "cfi_obs_im_env";
            fuse_type = "cfi_obs_fuse_env";

            // Saola timeouts
            max_run_clocks = 20000000;

        end // if (_level == SLA_TOP)

        super.build_phase(phase);
        
        //override cfi_vc_command_item to cfi_vc_command_item_ex 
        //cfi_vc_command_item::type_id::set_type_override(cfi_vc_command_item_ex::get_type());
        if (_level == SLA_TOP)
            build_cfi_obs_regmodel();

        // Update resources
        create_csi_stuff(_level == SLA_TOP);
        if (_level == SLA_TOP) begin
            // UVM timeout
            if (stress_picker.cfi_obs_pkgc_test_en)
                uvm_coreservice_t::get().get_root().set_timeout(7500us);
            else
                uvm_coreservice_t::get().get_root().set_timeout(2000us);        
        end // if (_level == SLA_TOP)
        // CCU VC
        if (stress_picker.cfi_obs_fast_gv_en == 1'b0)
            build_ccu_vc();
        else 
            create_clk();
        // CFI VC & CXM VC
        for (int i=0;i<picker.cfi_obs_num_of_cfi_links;i++) begin
            build_cfi_vc(i);
            build_cxm_vc(i);
            build_upi_vc(i);
        end 
        // PA agent
        build_pa_agent();
        // generic_sniffer agent
        build_gs_agent();
        // dtf_agent
        build_dtf_agent();
        // Coverage
//        if(agnt_sw_picker.cfi_obs_coverage_en) begin
//            cfi_obs_cov = cfi_obs_coverage::type_id::create("cfi_obs_coverage",this);
//        end

        // get global event pool
        CFI_OBSevPool = CFI_OBSevPool.get_global_pool();
        `slu_msg (UVM_LOW, get_name(), ("CFI_OBS build_phase is done"));

    endfunction : build_phase


    //*******************************************************
    // Function: cfi_obs_env connect
    // connect phase of cfi_obs_env
    //*******************************************************
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Get CFI_OBS IF
        assert(uvm_resource_db#(virtual cfi_obs_env_if)::read_by_name("cfi_obs", "CFI_OBS_IF", cfi_obs_if));

        //CCU VC
        if (stress_picker.cfi_obs_fast_gv_en == 1'b0)
            add_ccu_vc_sequencer();
        for (int i=0;i<picker.cfi_obs_num_of_cfi_links;i++) begin
            //CFI VC
            connect_cfi_vc(i);
            //PA agent
            connect_pa_agent(i);
        end
        //CXM VC
        add_cxm_vc_sequencer();

        //Connect DTF actual port of ENC scoreboard
        connect_gs_agent();


        // Coverage
//        if(agnt_sw_picker.cfi_obs_coverage_en) begin
//            cfi_obs_cov.env_if = cfi_obs_if;
//        end

        `slu_msg (UVM_LOW, get_name(), ("CFI_OBS connect_phase is done"));
    endfunction : connect_phase

    //*******************************************************
    // Function: cfi_obs_env end_of_elaboration
    // end_of_elaboration  phase of cfi_obs_env
    // In this pahse we randomize the fuse env
    //*******************************************************
    virtual function void end_of_elaboration_phase (uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        if (_level == SLA_TOP) begin
            cfi_obs_ral_func = new();
            slu_ral_db::set_regmodel(cfi_obs_regmodel);
            cfi_obs_regmodel.connect_phase();
            cfi_obs_regmodel.reset();

            slu_ral_db::set_user_functions(cfi_obs_ral_func);

            // Randomize the fuses
            `slu_assert(fuse.randomize(),("Unable to randomize fuses"));
        end
        `slu_msg (UVM_LOW, get_name(), ("CFI_OBS end_of_elaboration_phase is done"));

    endfunction : end_of_elaboration_phase

    //*******************************************************
    // Function: cfi_obs_env start_of_simulation
    // start_of_simulation  phase of cfi_obs_env
    //*******************************************************
    virtual function void uvm_start_of_simulation_phase(uvm_phase phase);
        super.start_of_simulation_phase(phase);
        uvm_factory::get().print();
    endfunction : uvm_start_of_simulation_phase

    //*******************************************************
    // Function: cfi_obs_env  run
    // run  phase of cfi_obs_env
    //*******************************************************
    virtual task run_phase(uvm_phase phase);      
        super.run_phase(phase);
        fork
            sample_clk_cov();
        join_none
    endtask : run_phase

    //*******************************************************
    // Function: cfi_obs_env  cfi_obs_env
    // get env pointer of cfi_obs_env
    //*******************************************************
    static function cfi_obs_env get_ptr();
        return _cfi_obs_env;
    endfunction


    // Saola TB clk
    virtual task set_clk_rst();
        forever begin
            ->sys_clk_r;
            #10000;
            ->sys_clk_f;
            #10000;
        end
    endtask // set_clk_rst

    `SLA_MONITOR_SEQ_STATUS_OVERRIDE

endclass // cfi_obs_env
