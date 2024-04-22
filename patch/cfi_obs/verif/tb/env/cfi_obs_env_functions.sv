// ------------------------------------------------------------------------
//   file          : cfi_obs_env_functions.sv
//   Date Created  : 12/2020
//   Author        : yuvalman
//   ----------------------------------------------------------------------
//  cfi_obs env external functions
//
// ------------------------------------------------------------------------


//***************************************************************
// Function: build_cfi_obs_regmodel
// Build regmodel
//***************************************************************
function cfi_obs_env::build_cfi_obs_regmodel();

    cfi_obs_regmodel = cfi_obs_regmodel_block::type_id::create("cfi_obs_regmodel",this);

    // Consider calling it from inside cfi_obs_regmodel_block (build)
    cfi_obs_regmodel.set_regmodel_hdl_path();
    cfi_obs_regmodel.build();
    void'(slu_ral_virtual_sequencer::init(null)); //YM from HBO
    `uvm_info("RAL_INFO",$sformatf("For Testbench=%s, RAL env = %s",this.get_full_name(), cfi_obs_regmodel.get_full_name()),UVM_MEDIUM)

endfunction : build_cfi_obs_regmodel

// ---------------------------------------------------------------------------------
// cfi_obs_agent_switches_picker extension to be used in the environment build-up
// This function reads configDB and copies the configuration to the relevant variables
// ---------------------------------------------------------------------------------
function void cfi_obs_env::init_cfi_obs_agent_switches_picker_from_configdb( ref cfi_obs_agent_switches_picker picker, string configDB_path);
    picker.cfi_obs_pa_tracker_en                    = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_PA_TRACKER_EN"});
    picker.cfi_obs_pa_scbd_en                       = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_PA_SCBD_EN"});
    picker.cfi_obs_filter_en                        = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_FILTER_EN"});
    picker.cfi_obs_coverage_en                      = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_COVERAGE_EN"});
    picker.cfi_obs_pa_monitors_en                   = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_PA_MONITORS_EN"});
endfunction : init_cfi_obs_agent_switches_picker_from_configdb

// ---------------------------------------------------------------------------------
// cfi_obs_picker extension to be used in the environment build-up
// This function reads configDB and copies the configuration to the relevant variables
// ---------------------------------------------------------------------------------
function void cfi_obs_env::init_cfi_obs_picker_from_configdb( ref cfi_obs_picker picker, string configDB_path);
    picker.cfi_obs_hbo_mode_en                      = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_HBO_MODE_EN"});
    picker.cfi_obs_cfi_tx0_tlm_path                 = getConfigValAndCheck(                             {configDB_path, "::CFI_OBS_CFI_TX0_TLM_PATH"});
    picker.cfi_obs_tracepacket_filter_en            = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_TRACEPACKET_FILTER_EN"});
    picker.cfi_obs_idi_c_supported                  = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_IDI_C_SUPPORTED"});
    picker.cfi_obs_cxm_obs_en                       = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_CXM_OBS_EN"});
    picker.cfi_obs_upi_c_supported                  = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_UPI_C_SUPPORTED"});
    picker.cfi_obs_extand_payload_en                = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_EXTAND_PAYLOAD_EN"});
    picker.cfi_obs_cfi_rx0_tlm_path                 = getConfigValAndCheck(                             {configDB_path, "::CFI_OBS_CFI_RX0_TLM_PATH"});
    picker.cfi_obs_cfi_vc_hw_col_en                 = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_CFI_VC_HW_COL_EN"});
    picker.cfi_obs_top_rtl_path                     = getConfigValAndCheck(                             {configDB_path, "::CFI_OBS_TOP_RTL_PATH"});
    picker.cfi_obs_upi_nc_supported                 = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_UPI_NC_SUPPORTED"});
    picker.cfi_obs_data_parity_select               = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_DATA_PARITY_SELECT"});
    picker.cfi_obs_cxm_supported                    = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_CXM_SUPPORTED"});
    picker.cfi_obs_num_of_cfi_links                 = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_NUM_OF_CFI_LINKS"});
    picker.cfi_obs_random_protocol_en               = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_RANDOM_PROTOCOL_EN"});
    picker.cfi_obs_rand_config_en                   = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_RAND_CONFIG_EN"});
endfunction : init_cfi_obs_picker_from_configdb

// ---------------------------------------------------------------------------------
// cfi_obs_stress_modes_picker extension to be used in the environment build-up
// This function reads configDB and copies the configuration to the relevant variables
// ---------------------------------------------------------------------------------
function void cfi_obs_env::init_cfi_obs_stress_modes_picker_from_configdb( ref cfi_obs_stress_modes_picker picker, string configDB_path);
    picker.cfi_obs_init_repeaters_num               = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_INIT_REPEATERS_NUM"});
    picker.cfi_obs_main_repeaters_num               = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_MAIN_REPEATERS_NUM"});
    picker.cfi_obs_pkgc_test_en                     = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_PKGC_TEST_EN"});
    picker.cfi_obs_is_connected_by_repeaters        = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_IS_CONNECTED_BY_REPEATERS"});
    picker.cfi_obs_pkgc_test_mode                   = EnumUtils#(cfi_obs_common_pkg::cfi_obs_pm_flow_t)::fromName(getConfigValAndCheck(  {configDB_path, "::CFI_OBS_PKGC_TEST_MODE"}));
    picker.cfi_obs_drop_active_en                   = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_DROP_ACTIVE_EN"});
    picker.cfi_obs_max_clock_freq                   = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_MAX_CLOCK_FREQ"});
    picker.cfi_obs_min_clock_freq                   = getConfigValAndCheckUint64(                       {configDB_path, "::CFI_OBS_MIN_CLOCK_FREQ"});
    picker.cfi_obs_b2b_vc_id_test_en                = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_B2B_VC_ID_TEST_EN"});
    picker.cfi_obs_fast_gv_en                       = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_FAST_GV_EN"});
    picker.cfi_obs_direct_filter_en                 = getConfigValAndCheckBool(                         {configDB_path, "::CFI_OBS_DIRECT_FILTER_EN"});
endfunction : init_cfi_obs_stress_modes_picker_from_configdb

// ***************************************************************
// Need to allow calling it from above at any stage
// SOC will need to call it before our build stage if need to use our CSI stuff at their build stage
// ***************************************************************
function void cfi_obs_env::create_csi_stuff(bit loadConfigDB_required = 0);
    string cfg_path;
    string cfgdb_filename;

    if ($value$plusargs("USE_CFGDB=%s", cfgdb_filename)) begin

        // Load ConfigDB file in case of SLA_TOP
        if (loadConfigDB_required) begin
            loadConfigDB(cfgdb_filename);
        end

        //picker
        if (picker == null) begin
            picker = cfi_obs_picker::type_id::create("picker", this);

            if (picker == null) `slu_error("CFI_OBS_ENV", ("picker create failed"));
            // Get "cfi_obs" picker values
            cfg_path = CFGDB_UP_PATH;
            init_cfi_obs_picker_from_configdb(picker, cfg_path);
        end

        //stress_picker
        if (stress_picker == null) begin
            stress_picker = cfi_obs_stress_modes_picker::type_id::create("stress_picker", this);
            if (stress_picker == null) `slu_error("CFI_OBS_ENV", ("stress_picker create failed"));
            // Get "cfi_obs::stress" picker values
            cfg_path = {CFGDB_UP_PATH, "::stress"};
            init_cfi_obs_stress_modes_picker_from_configdb(stress_picker, cfg_path);
        end

        //agnt_sw_picker
        if (agnt_sw_picker == null) begin
            agnt_sw_picker = cfi_obs_agent_switches_picker::type_id::create("agnt_sw_picker", this);
            if (agnt_sw_picker == null) `slu_error("CFI_OBS_ENV", ("agnt_sw_picker create failed"));
            // Get "cfi_obs::agt_sw" picker values
            cfg_path = {CFGDB_UP_PATH, "::agt_sw"};
            init_cfi_obs_agent_switches_picker_from_configdb(agnt_sw_picker, cfg_path);
        end

    end
endfunction : create_csi_stuff

//***************************************************************
// Function: build_ccu_vc
// Build and set up CCU VC & CFG object
//***************************************************************
function void cfi_obs_env::build_ccu_vc();
    int local_clk,gv_local_clk,slow_local_clk;
    uint_t min_freq, max_freq;

    //TODO YM correct values - Different values for CXM!!!!!
    min_freq = stress_picker.cfi_obs_min_clock_freq;
    max_freq = stress_picker.cfi_obs_max_clock_freq;
    `slu_msg (UVM_LOW, get_name(), ("max_freq = %0d, min_freq = %0d,", max_freq,min_freq));
    std::randomize(local_clk) with {local_clk inside {[max_freq:min_freq]};};
    std::randomize(gv_local_clk) with {gv_local_clk inside {[max_freq:min_freq]};};
    `slu_msg (UVM_LOW, get_name(), ("local_clk = %0d, gv_local_clk = %0d,", local_clk,gv_local_clk));
    slow_local_clk = $urandom_range(41666,50000);

    cfi_obs_ccu_vc_cfg = ccu_vc_uvm_pkg::ccu_vc_cfg::type_id::create("cfi_obs_ccu_vc_cfg", this);
    // Clock sources
    //---------------
    // at the moment use a hard coded frequency

    // source_A_src source (100 MHz)
    void'(cfi_obs_ccu_vc_cfg.add_clk_source(0, "Local_clk",local_clk*1ps ));

    // source_B_src source (800 MHz)
    void'(cfi_obs_ccu_vc_cfg.add_clk_source(1, "Crystal_Clk",41666*1ps ));
    //Add GV clk
    void'(cfi_obs_ccu_vc_cfg.add_clk_source(2, "GV_Local_clk",gv_local_clk*1ps ));
    
    // Clock Slices (derived clocks)
    //-------------------------------
    cfi_obs_ccu_vc_cfg.add_slice(
        .slice_num (0),
        .slice_name ("Local_clk"),
        .clk_src (0),
        .clk_status (ccu_types::CLK_GATED),
        .dcg_blk_num (0),
        .set_zero_delay (0)
    );

    cfi_obs_ccu_vc_cfg.add_slice(
        .slice_num (1),
        .slice_name ("Crystal_Clk"),
        .clk_src (1),
        .clk_status (ccu_types::CLK_GATED),
        .dcg_blk_num (1),
        .set_zero_delay (0)
    );

    cfi_obs_ccu_vc_cfg.add_slice(
        .slice_num (2),
        .slice_name ("GV_Local_clk"),
        .clk_src (2),
        .clk_status (ccu_types::CLK_GATED),
        .dcg_blk_num (2),
        .set_zero_delay (0)
    );

    cfi_obs_ccu_vc_cfg.add_slice(
        .slice_num (3),
        .slice_name ("verif_always_on"),
        .clk_src (0),
        .clk_status (ccu_types::CLK_GATED),
        .dcg_blk_num (3),
        .set_zero_delay (0)
    );

    uvm_config_object::set(this,"cfi_obs_ccu_vc*", "CCU_VC_CFG", cfi_obs_ccu_vc_cfg);

    if (_level != SLA_TOP) begin
        cfi_obs_ccu_vc_cfg.set_to_passive();
    end

    cfi_obs_ccu_vc = ccu_vc_uvm_pkg::ccu_vc::type_id::create("cfi_obs_ccu_vc", this);
    `slu_assert((cfi_obs_ccu_vc != null),("Unable to create cfi_obs_ccu_vc"));

endfunction : build_ccu_vc
//***************************************************************
// Function: create_clk
// Create clocks for clock vc
//***************************************************************
function void cfi_obs_env::create_clk();
    int local_clk,gv_local_clk,slow_local_clk;
    uint_t min_freq, max_freq;
    min_freq = stress_picker.cfi_obs_min_clock_freq; //the same code as in build_ccu_vc . consider to make it global
    max_freq = stress_picker.cfi_obs_max_clock_freq;
    `slu_msg (UVM_LOW, get_name(), ("max_freq = %0d, min_freq = %0d,", max_freq,min_freq));
    local_clk = $urandom_range(min_freq,max_freq);
    gv_local_clk = $urandom_range(min_freq,max_freq);
    slow_local_clk = $urandom_range(10416,12500);
    `slu_msg (UVM_LOW, get_name(), ("local_clk = %0d, gv_local_clk = %0d,", local_clk,gv_local_clk));

    
    clks_freq[0] = real'((10**6)/local_clk);//local clk
    clks_freq[1] = real'((10**6)/local_clk);//verif allways on clk
    clks_freq[2] = real'((10**6)/41666);//crystal clk
    gv_clk_freq = real'((10**6)/gv_local_clk);//local clk
    $display("YUVAL_MANOR local_clk = %0d, clks_freq[0] = %0d",local_clk,clks_freq[0]);
//gv_clk_freq = gv_clk_freq*1.2;
endfunction
//***************************************************************
// Function: build_cfi_vc
// Build and set up cfi_vc agents
//***************************************************************
function void cfi_obs_env::build_cfi_vc(int idx);

    string curr_cfi_rx_vc_name;
    string curr_cfi_rx_vc_cfg_name;
    string curr_cfi_tx_vc_name;
    string curr_cfi_tx_vc_cfg_name;    
    // CFI agent instances

    //RX CFI VC
    curr_cfi_rx_vc_name = $sformatf("CFI_VC_RX%0d", idx);
    curr_cfi_rx_vc_cfg_name = $sformatf("CFI_VC_RX_CFG%0d", idx);
    rx_cfi_vc_agent_l[idx] = cfi_vc_agent::type_id::create(curr_cfi_rx_vc_name, this);
    rx_cfi_vc_agent_cfg_l[idx] = cfi_vc_agt_pkg::cfi_vc_config::type_id::create(curr_cfi_rx_vc_cfg_name,this);
    
    rx_cfi_vc_agent_cfg_l[idx].randomize() with {
        is_active == CFI_TRUE; //CFI_TRUE
        use_pp_collector == picker.cfi_obs_cfi_vc_hw_col_en; // Disable post process collector since it uses new for cfi_vc_command item --> override doen't work
        foreach(credit_to_send[iftype,vc])
            credit_to_send[iftype][vc] == ((iftype==CFI_RSP && vc>1)?0:5);
        foreach(credit_to_receive[iftype,vc])
            credit_to_receive[iftype][vc] == ((iftype==CFI_RSP && vc>1)?0:5);
        //foreach(shared_credit_to_send[iftype]) //TODO YM need shared credit?
        //    shared_credit_to_send[iftype] == 5;
        //foreach(shared_credit_to_receive[iftype])
        //    shared_credit_to_receive[iftype] == 5;
        stall_tx_mode == STALL_MANUAL; //TODO YM what is the correct value?
        stall_rx_mode == STALL_MANUAL;
        support_interleaving_between_vc_id == CFI_TRUE;
        max_interleaving_allowed == 8;
        };

    rx_cfi_vc_agent_cfg_l[idx].cfi_vc_generates_uri = CFI_TRUE;

    uvm_config_object::set(this,curr_cfi_rx_vc_name, "cfg", rx_cfi_vc_agent_cfg_l[idx]);
    
    //TX CFI VC
    curr_cfi_tx_vc_name = $sformatf("CFI_VC_TX%0d", idx);
    curr_cfi_tx_vc_cfg_name = $sformatf("CFI_VC_TX_CFG%0d", idx);    
    tx_cfi_vc_agent_l[idx] = cfi_vc_agent::type_id::create(curr_cfi_tx_vc_name, this);
    tx_cfi_vc_agent_cfg_l[idx] = cfi_vc_config::type_id::create(curr_cfi_tx_vc_cfg_name,this);

    tx_cfi_vc_agent_cfg_l[idx].randomize() with {
        is_active == CFI_TRUE; //CFI_TRUE
        use_pp_collector == picker.cfi_obs_cfi_vc_hw_col_en; // Disable post process collector since it uses new for cfi_vc_command item --> override doen't work
        foreach(credit_to_send[iftype,vc])
            credit_to_send[iftype][vc] == ((iftype==CFI_RSP && vc>1)?0:5);
        foreach(credit_to_receive[iftype,vc])
            credit_to_receive[iftype][vc] == ((iftype==CFI_RSP && vc>1)?0:5);
        //foreach(shared_credit_to_send[iftype]) //TODO YM need shared credit?
        //    shared_credit_to_send[iftype] == 5;
        //foreach(shared_credit_to_receive[iftype])
        //    shared_credit_to_receive[iftype] == 5;
        stall_tx_mode == STALL_MANUAL; //TODO YM what is the correct value?
        stall_rx_mode == STALL_MANUAL;
        support_interleaving_between_vc_id == CFI_TRUE;
        max_interleaving_allowed == 6;
    };

    tx_cfi_vc_agent_cfg_l[idx].x_probability = 0;
    tx_cfi_vc_agent_cfg_l[idx].cfi_vc_generates_uri = CFI_TRUE;
    uvm_config_object::set(this,curr_cfi_tx_vc_name, "cfg", tx_cfi_vc_agent_cfg_l[idx]); 

endfunction : build_cfi_vc

//***************************************************************
// Function: build_cxm_vc
// Build and set up cxm_vc agent
//***************************************************************
function void cfi_obs_env::build_cxm_vc(int idx);
    cxm_requestor = cxm_vc_agent::type_id::create("CXM_VC_REQUESTOR", this);
    cxm_responder = cxm_vc_agent::type_id::create("CXM_VC_RESPONDER", this);

    cxm_requestor_cfg = cxm_vc_config::type_id::create("CXM_VC_REQUESTOR_CFG",this);
    cxm_responder_cfg = cxm_vc_config::type_id::create("CXM_VC_RESPONDER_CFG",this);
    
    cxm_requestor_cfg.randomize() with {
      is_active == CFI_TRUE;
      is_requestor == CFI_TRUE;
      adjust_nointerleave_en == 1;
    };

    cxm_responder_cfg.randomize() with {
      is_active == CFI_TRUE;
      is_requestor == CFI_FALSE;
      rctrl_random_en == CFI_FALSE;
    };
    
    //TODO yuvalman - who is rx? tx?
    cxm_responder_cfg.agents_rsp_ids[$sformatf("CFI_VC_TX%0d", idx)] = '{0,1,2,3,4,5,6};
    cxm_requestor_cfg.agents_rsp_ids[$sformatf("CFI_VC_RX%0d", idx)] = '{0,1,2,3,4,5,6};

    for (int i = 0; i<7; i++)begin
        cxm_responder_cfg.rsp_ids[i] = {"RSP_ID_", $sformatf("%0h",i)};
        cxm_responder_cfg.dst_ids[i] = {"DST_ID_", $sformatf("%0h",i)};
        cxm_requestor_cfg.rsp_ids[i] = {"RSP_ID_", $sformatf("%0h",i)};
        cxm_requestor_cfg.dst_ids[i] = {"DST_ID_", $sformatf("%0h",i)};
        
    end

    //TODO yuvalman - who is rx? tx?
    cxm_responder_cfg.interleaving_en[$sformatf("CFI_VC_TX%0d", idx)] = 1;
    cxm_responder_cfg.interleaving_depth[$sformatf("CFI_VC_TX%0d", idx)] = '{5,5, 0,0,0,0,0};
    cxm_responder_cfg.stay_in_interleaved_prob[$sformatf("CFI_VC_TX%0d", idx)] = '{50,50, 0,0,0,0,0};
    cxm_requestor_cfg.interleaving_en[$sformatf("CFI_VC_RX%0d", idx)] = 1;
    cxm_requestor_cfg.interleaving_depth[$sformatf("CFI_VC_RX%0d", idx)] = '{5,5, 0,0,0,0,0};
    
    uvm_config_object::set(this,"CXM_VC_REQUESTOR", "CXM_CFG", cxm_requestor_cfg);
    uvm_config_object::set(this,"CXM_VC_RESPONDER", "CXM_CFG", cxm_responder_cfg);
    
    cxm_requestor.assign_cfi_vc_agent($sformatf("CFI_VC_RX%0d", idx), rx_cfi_vc_agent_l[idx]);
    cxm_responder.assign_cfi_vc_agent($sformatf("CFI_VC_TX%0d", idx), tx_cfi_vc_agent_l[idx]);
    
endfunction : build_cxm_vc

//***************************************************************
// Function: build_upi_vc
// Build and set up cxm_vc agent
//***************************************************************
function void cfi_obs_env::build_upi_vc(int idx);
    uxi::Config        io_vtu_cfg;    
    uxi::Config        io_ioc_cfg;    
    uxi::Config        cache_ccf0_cfg;    
    uxi::Config        cache_ccf1_cfg;    
    uxi::Config        home_hbo_cfg;    
    utils = new();
    //to override p2p_msg_type --> use only P2P Short msg_type
    tunnle_responses = cfi_obs_common_pkg::Tunneled_Response::type_id::create("tunnle_responses",this);

    home_hbo_cfg = uxi::Config::type_id::create("HBO",this);
    home_hbo_cfg.randomize() with {
      ids.size() == 1;
      ids[0] == 6;
      typ[0] == HOME_AGENT;
      mode == uxi::Config::ACTIVE;
      HAUncovered.size() == 2;
      HAUncovered[0].size() == 1;
      HAUncovered[0][0] == 7;
      HAUncovered[1].size() == 1;
      HAUncovered[1][0] == 8;
      HADownGradeSnpToLSnp == uxi::True;
      HADataRsp inside {UPI_DATA}; //RSP_RAND
      cxm_mode inside {CXM_RAND};
      HACxmMcId inside {0,1,2,3,4,5};      
    };
    home_hbo_cfg.address_hash = utils;
    home_hbo_cfg.tunnel_responder = tunnle_responses;

    cache_ccf0_cfg = uxi::Config::type_id::create("CCF0",this);
    cache_ccf0_cfg.randomize() with {
      ids.size() == 1;
      ids[0] == 7;
      typ[0] == CACHE_AGENT;
      mode == uxi::Config::ACTIVE;
    };
    cache_ccf0_cfg.address_hash = utils;
    cache_ccf0_cfg.tunnel_responder = tunnle_responses;

    cache_ccf1_cfg = uxi::Config::type_id::create("CCF1",this);
    cache_ccf1_cfg.randomize() with {
      ids.size() == 1;
      ids[0] == 8;
      typ[0] == CACHE_AGENT;
      mode == uxi::Config::ACTIVE;
    };
    cache_ccf1_cfg.address_hash = utils;
    cache_ccf1_cfg.tunnel_responder = tunnle_responses;

    io_ioc_cfg = uxi::Config::type_id::create("IOC",this);
    io_ioc_cfg.randomize() with {
      ids.size() == 1;
      ids[0] == 11;
      typ[0] == IO_AGENT;
      mode == uxi::Config::ACTIVE;
    };
    io_ioc_cfg.tunnel_responder = tunnle_responses;

    io_vtu_cfg = uxi::Config::type_id::create("VTU",this);
    io_vtu_cfg.randomize() with {
      ids.size() == 1;
      ids[0] == 10;
      typ[0] == IO_AGENT;
      mode == uxi::Config::ACTIVE;
    };
     io_vtu_cfg.tunnel_responder = tunnle_responses;
 
    out_map[home_hbo_cfg.get_name()][0] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][1] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][2] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][3] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][4] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][5] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][7] =  tx_cfi_vc_agent_l[idx];
    out_map[home_hbo_cfg.get_name()][8] =  tx_cfi_vc_agent_l[idx];
    in_map[home_hbo_cfg.get_name()]     = {tx_cfi_vc_agent_l[idx]};
 
    out_map[cache_ccf1_cfg.get_name()][6]  =  rx_cfi_vc_agent_l[idx];
    in_map[cache_ccf1_cfg.get_name()]      = {rx_cfi_vc_agent_l[idx],tx_cfi_vc_agent_l[idx]};
 
    out_map[cache_ccf0_cfg.get_name()][6]  =  rx_cfi_vc_agent_l[idx];
    in_map[cache_ccf0_cfg.get_name()]      = {rx_cfi_vc_agent_l[idx],tx_cfi_vc_agent_l[idx]};
 
    out_map[io_vtu_cfg.get_name()][11] = rx_cfi_vc_agent_l[idx];
    in_map[io_vtu_cfg.get_name()]      = {rx_cfi_vc_agent_l[idx]};

    out_map[io_ioc_cfg.get_name()][10] = tx_cfi_vc_agent_l[idx];
    in_map[io_ioc_cfg.get_name()]      = {tx_cfi_vc_agent_l[idx]};

    //-----------------------------------------------------------
    upi_bfm = uxi::BfmEnv::type_id::create("upi_bfm", this);
    upi_bfm.set_upi_config({io_vtu_cfg,io_ioc_cfg,home_hbo_cfg,cache_ccf0_cfg,cache_ccf1_cfg});
    upi_bfm.set_upi_cfi_in_map(in_map);
    upi_bfm.set_upi_cfi_out_map(out_map);
    
endfunction : build_upi_vc


//***************************************************************
// Function: build_pa_agent
// Build and set up cfi_obs_pa_agent
//***************************************************************
function void cfi_obs_env::build_pa_agent();
    
    if (picker.cfi_obs_cxm_obs_en == 0) begin //Default configuration - RX DSO exists

        CFI_OBS_rx_pa = cfi_obs_pa_agent_pkg::cfi_obs_pa_agent::type_id::create("CFI_OBS_rx_pa", this);

        CFI_OBS_rx_pa_cfg = cfi_obs_pa_agent_pkg::cfi_obs_pa_config::type_id::create("CFI_OBS_rx_pa_cfg", this);
        CFI_OBS_rx_pa_cfg.configDB_path = {CFGDB_UP_PATH,"::agt_sw"};
        CFI_OBS_rx_pa_cfg.agent_name = "CFI_OBS_rx_pa";
        CFI_OBS_rx_pa_cfg.randomize() with {
            idi_c_supported  == picker.cfi_obs_idi_c_supported;
            cxm_supported    == picker.cfi_obs_cxm_supported;
            upi_c_supported  == picker.cfi_obs_upi_c_supported;
            upi_nc_supported == picker.cfi_obs_upi_nc_supported;
            extand_payload   == picker.cfi_obs_extand_payload_en;
            cxm_obs_en       == picker.cfi_obs_cxm_obs_en;
        };

        uvm_config_db #(cfi_obs_pa_config)::set(this, "CFI_OBS_rx_pa","cfg", CFI_OBS_rx_pa_cfg);
        uvm_config_db #(uvm_reg_block)::set(this, "CFI_OBS_rx_pa*","dso_reg_block", cfi_obs_regmodel.rx_dso);
    end
    
    CFI_OBS_tx_pa = cfi_obs_pa_agent_pkg::cfi_obs_pa_agent::type_id::create("CFI_OBS_tx_pa", this);
    CFI_OBS_tx_pa_cfg = cfi_obs_pa_agent_pkg::cfi_obs_pa_config::type_id::create("CFI_OBS_tx_pa_cfg", this);
    CFI_OBS_tx_pa_cfg.agent_name = "CFI_OBS_tx_pa";
    CFI_OBS_tx_pa_cfg.configDB_path = {CFGDB_UP_PATH,"::agt_sw"};
    CFI_OBS_tx_pa_cfg.randomize() with {
        idi_c_supported  == picker.cfi_obs_idi_c_supported;
        cxm_supported    == picker.cfi_obs_cxm_supported;
        upi_c_supported  == picker.cfi_obs_upi_c_supported;
        upi_nc_supported == picker.cfi_obs_upi_nc_supported;
        extand_payload   == picker.cfi_obs_extand_payload_en;
        cxm_obs_en       == picker.cfi_obs_cxm_obs_en;
    };
    uvm_config_db #(cfi_obs_pa_config)::set(this, "CFI_OBS_tx_pa","cfg", CFI_OBS_tx_pa_cfg);
    uvm_config_db #(uvm_reg_block)::set(this, "CFI_OBS_tx_pa*","dso_reg_block", cfi_obs_regmodel.tx_dso);
    uvm_config_db #(uvm_reg_block)::set(this, {"CFI_OBS_","*","pa*"},"pa_reg_block", cfi_obs_regmodel.cfi_obs_regs);

endfunction : build_pa_agent

//***************************************************************
// Function: build_gs_agent
// Build and set up gs_agent
//***************************************************************
function void cfi_obs_env::build_gs_agent();

    if (picker.cfi_obs_cxm_obs_en == 0) begin //Default configuration - RX DSO exists
        CFI_OBS_RX_generic_sniffer = GsAgt_pkg::gs_agent::type_id::create("CFI_OBS_RX_generic_sniffer", this);
        CFI_OBS_RX_generic_sniffer.cfg_path = "main";
        uvm_config_object::set(null,"*CFI_OBS_RX_generic_sniffer*", "TOP_REG_BLOCK", cfi_obs_regmodel.rx_dso);
        uvm_config_string::set(null,"*CFI_OBS_RX_generic_sniffer*","GS_REG_BLOCK_NAME","rx_dso");
    end
    CFI_OBS_TX_generic_sniffer = GsAgt_pkg::gs_agent::type_id::create("CFI_OBS_TX_generic_sniffer", this);
    CFI_OBS_TX_generic_sniffer.cfg_path = "main";
    uvm_config_object::set(null,"*CFI_OBS_TX_generic_sniffer*", "TOP_REG_BLOCK", cfi_obs_regmodel.tx_dso);
    uvm_config_string::set(null,"*CFI_OBS_TX_generic_sniffer*","GS_REG_BLOCK_NAME","tx_dso");
    
endfunction : build_gs_agent

//***************************************************************
// Function: build_dtf_network
// Build and set up dtf_fabric_cfg & dtf_fabric
//***************************************************************
function void cfi_obs_env:: build_dtf_agent();

    if (picker.cfi_obs_cxm_obs_en == 0) begin //Default configuration - RX DSO exists
        rx_dtf_vc_out = dtf_vc_pkg::dtf_vc_env::type_id::create("rx_dtf_vc_out", this);
        rx_dtf_vc_out.cfg_path = "main";
        
        uvm_config_string::set(null, "*rx_dtf_tracker_inst*","DTF_INT_IP_TRK_NAME", "RX_DSO");
        rx_dtf_tracker_inst = ARBchk::dtf_env_tracker::type_id::create("rx_dtf_tracker_inst", this);
    end
    tx_dtf_vc_out = dtf_vc_pkg::dtf_vc_env::type_id::create("tx_dtf_vc_out", this);
    tx_dtf_vc_out.cfg_path = "main";

    uvm_config_string::set(null, "*tx_dtf_tracker_inst*","DTF_INT_IP_TRK_NAME", "TX_DSO");
    tx_dtf_tracker_inst = ARBchk::dtf_env_tracker::type_id::create("tx_dtf_tracker_inst", this);

endfunction : build_dtf_agent

//***************************************************************
// Function: add_ccu_vc_sequencer
// Add CCU VC sequencer
//***************************************************************
function void cfi_obs_env::add_ccu_vc_sequencer();
    if (_level == SLA_TOP) begin
        void'(this.add_sequencer("ccu_seqr", "cfi_obs_ccu_vc", cfi_obs_ccu_vc.ccu_sqr_i));
    end
endfunction : add_ccu_vc_sequencer

//***************************************************************
// Function: add_cxm_vc_sequencer
// Add CXM VC sequencer
//***************************************************************
function void cfi_obs_env::add_cxm_vc_sequencer();
    this.add_sequencer("cxm_vc","CXM_VC_REQUESTOR",cxm_requestor.get_sequencer(cxm_vc_common_pkg::CXM_REQ));    
endfunction : add_cxm_vc_sequencer

//***************************************************************
// Function: add_cfi_vc_rx_sequencer
// Add CFI VC sequencer
//***************************************************************
function void cfi_obs_env::add_cfi_vc_rx_sequencer(string agent_name, IfType it, int num, int idx);
    for (int i = 0;i<num;i++) begin
        this.add_sequencer("cfi_vc",{agent_name,it.name(),$psprintf("%0d",i)},rx_cfi_vc_agent_l[idx].get_sequencer(it,i));
    end
endfunction : add_cfi_vc_rx_sequencer
//***************************************************************
// Function: add_cfi_vc_tx_sequencerr
// Add CFI VC sequencer
//***************************************************************
function void cfi_obs_env::add_cfi_vc_tx_sequencer(string agent_name, IfType it, int num, int idx);
    string sequencer_name;
    for (int i = 0;i<num;i++) begin
        sequencer_name = {agent_name,it.name(),$psprintf("%0d",i)};
        this.add_sequencer("cfi_vc",sequencer_name,tx_cfi_vc_agent_l[idx].get_sequencer(it,i));
        cfi_vc_sequencer_name_array[agent_name][it][num] = sequencer_name;
    end
endfunction : add_cfi_vc_tx_sequencer

//***************************************************************
// Function: connect_cfi_vc
// Add cfi sequencers
//***************************************************************
function void cfi_obs_env::connect_cfi_vc(int idx);

    add_cfi_vc_rx_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_REQ, rx_cfi_vc_agent_cfg_l[idx].REQ_TX, idx);
    add_cfi_vc_rx_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_DATA,rx_cfi_vc_agent_cfg_l[idx].DATA_TX, idx);
    add_cfi_vc_rx_sequencer({"CFI_VC_RX",$psprintf("%0d",idx)},CFI_RSP, rx_cfi_vc_agent_cfg_l[idx].RSP_TX, idx);

    add_cfi_vc_tx_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_REQ, tx_cfi_vc_agent_cfg_l[idx].REQ_TX, idx);
    add_cfi_vc_tx_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_DATA,tx_cfi_vc_agent_cfg_l[idx].DATA_TX, idx);
    add_cfi_vc_tx_sequencer({"CFI_VC_TX",$psprintf("%0d",idx)},CFI_RSP, tx_cfi_vc_agent_cfg_l[idx].RSP_TX, idx);

endfunction : connect_cfi_vc

//***************************************************************
// Function: connect pa_agents
// Connect pa_agents ref_model to cfi_vc monitors
//***************************************************************
function void cfi_obs_env::connect_pa_agent(int idx);
    if (agnt_sw_picker.cfi_obs_pa_scbd_en) begin
        if (picker.cfi_obs_cxm_obs_en == 0) begin //Default configuration - RX DSO exists
            tx_cfi_vc_agent_l[idx].monitor[TRANSMIT][CFI_REQ][tx_cfi_vc_agent_cfg_l[idx].REQ_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.tx_req_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[TRANSMIT][CFI_RSP][tx_cfi_vc_agent_cfg_l[idx].RSP_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.tx_rsp_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[TRANSMIT][CFI_DATA][tx_cfi_vc_agent_cfg_l[idx].DATA_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.tx_data_channel_fifo.analysis_export);

            tx_cfi_vc_agent_l[idx].monitor[RECEIVE][CFI_REQ][tx_cfi_vc_agent_cfg_l[idx].REQ_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_rx_pa.pa_ref_model.rx_req_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[RECEIVE][CFI_RSP][tx_cfi_vc_agent_cfg_l[idx].RSP_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_rx_pa.pa_ref_model.rx_rsp_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[RECEIVE][CFI_DATA][tx_cfi_vc_agent_cfg_l[idx].DATA_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_rx_pa.pa_ref_model.rx_data_channel_fifo.analysis_export);
        end
        else begin
            //For MC LNL-M Compute Die: TX RSP, TX DATA, RX REQ, RX DATA
            tx_cfi_vc_agent_l[idx].monitor[TRANSMIT][CFI_RSP][tx_cfi_vc_agent_cfg_l[idx].RSP_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.tx_rsp_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[TRANSMIT][CFI_DATA][tx_cfi_vc_agent_cfg_l[idx].DATA_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.tx_data_channel_fifo.analysis_export);

            tx_cfi_vc_agent_l[idx].monitor[RECEIVE][CFI_REQ][tx_cfi_vc_agent_cfg_l[idx].REQ_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.rx_req_channel_fifo.analysis_export);
            tx_cfi_vc_agent_l[idx].monitor[RECEIVE][CFI_DATA][tx_cfi_vc_agent_cfg_l[idx].DATA_TX-1].complete_cmd_and_data_out_port.connect(CFI_OBS_tx_pa.pa_ref_model.rx_data_channel_fifo.analysis_export);

        end
    end
endfunction : connect_pa_agent

//***************************************************************
// Function: connect gs_agent
// Connect DTF VC to gs_agent
//***************************************************************
function void cfi_obs_env::connect_gs_agent();

    if (picker.cfi_obs_cxm_obs_en == 0) begin //Default configuration - RX DSO exists
        rx_dtf_vc_out.obs_pkt.connect(CFI_OBS_RX_generic_sniffer.gs_enc.enc_ref_model.dtf_msg_fifo_dtf.analysis_export);
        rx_dtf_vc_out.obs_pkt.connect(rx_dtf_tracker_inst.dtf_pkt_to_tracker);
    end 
    tx_dtf_vc_out.obs_pkt.connect(CFI_OBS_TX_generic_sniffer.gs_enc.enc_ref_model.dtf_msg_fifo_dtf.analysis_export);
    tx_dtf_vc_out.obs_pkt.connect(tx_dtf_tracker_inst.dtf_pkt_to_tracker);
    
    if(stress_picker.cfi_obs_direct_filter_en) begin
        CFI_OBS_rx_pa.pa_scbd.dso_cid = CFI_OBS_RX_generic_sniffer.pa_gs.gs_cfg.gs_pa_cid;
        CFI_OBS_tx_pa.pa_scbd.dso_cid = CFI_OBS_TX_generic_sniffer.pa_gs.gs_cfg.gs_pa_cid;
        CFI_OBS_rx_pa.pa_scbd.direct_filter_test_en = 1'b1;
        CFI_OBS_tx_pa.pa_scbd.direct_filter_test_en = 1'b1;
        CFI_OBS_RX_generic_sniffer.gs_enc.gs_obs_pkt.connect(CFI_OBS_rx_pa.pa_scbd.dso_dtf_pkts_fifo.analysis_export);
        CFI_OBS_TX_generic_sniffer.gs_enc.gs_obs_pkt.connect(CFI_OBS_tx_pa.pa_scbd.dso_dtf_pkts_fifo.analysis_export);
    end 
endfunction : connect_gs_agent

//***************************************************************
// Task: sample_clk_cov
// Connect DTF VC to gs_agent
//***************************************************************
task cfi_obs_env::sample_clk_cov;
    time time_start,time_end;
    wait(CFI_OBS_tx_pa.pa_monitors[0].m_pa_if.valid===1'b1);
    `slu_msg (UVM_LOW, get_name(), ("start sampling local_clk_freq"));
    //local clk sampling
    @(posedge cfi_obs_if.cfi_obs_clk);
    time_start = $time;
    @(posedge cfi_obs_if.cfi_obs_clk);
    time_end = $time;
    local_clk_measured = int'(time_end - time_start);

    //gv clk sampling
    @(posedge cfi_obs_if.cfi_obs_gv_clk);
    time_start = $time;
    @(posedge cfi_obs_if.cfi_obs_gv_clk);
    time_end = $time;
    gv_local_clk_measured = int'(time_end - time_start);

    cfi_obs_clk_cg.sample();
endtask
