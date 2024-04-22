`include "sideband_config/iosf_multi_ep_defines.sv"
typedef sncu_env;
class sideband_config_passive extends uvm_component;
    string sncu_ti_path = "sncu_tb.sb_ti_";

    `uvm_component_utils_begin(sideband_config_passive)
        `uvm_field_string(sncu_ti_path, UVM_ALL_ON)
    `uvm_component_utils_end

    iosfsbm_fbrcvc IDP_SBR_agent[string];
    fbrcvc_cfg     IDP_SBR_agentCfg[string];
    sncu_env _sncu_env;
    string resource_inst = "";

    sncu_racu_tracker racu_tracker;
    iosfsbm_cm::opcode_t fuses_opcodes[$] = {SNCU_types::FUSE_GROUP0_REQ};
    sncu_resource_group group_res; // get a pointer to group resource
    iosfsbm_cm::opcode_t fab_supp_opcodes[$] = {iosfsbm_cm::DEFAULT_OPCODES, fuses_opcodes,
            `SNCU_VLW_INTR_OPCODE, `SNCU_PCU_NCU_MSG_OPCODE, `SNCU_NCU_NCU_MSG_OPCODE,
            `SNCU_MCLK_EVENT_MSG_OPCODE,`SNCU_RAS_NCU_EVENT_MSG_OPCODE,`SNCU_MCA_MSG_OPCODE, `SNCU_FCLK_EVENT_MSG_OPCODE, `SNCU_PCIE_ERR_MSG_OPCODE};


    function new(string name = "sideband_config", uvm_component parent = null);
        super.new(name,parent);
        group_res = `GROUP(sncu); // get a pointer to group resource using resource_inst
    endfunction

    function void set_report_verbosity_level_hier();
        //these will cause the passive vc and router vc - who works in verbosity MEDIUM - to not print to jest log. cuz its higher than LOW.
        foreach(IDP_SBR_agent[ep_name]) begin
            IDP_SBR_agent[ep_name].set_report_verbosity_level_hier(UVM_LOW);
        end
    endfunction

    function int get_payload_width(string comp_name);
        if(comp_name == "ncracu")
            return 16;
        else if(comp_name == "ncevnts")
            return 32;
        uvm_report_error (get_name (), "sncu_ep_vc_cfg randomization failed");
        return 0;
    endfunction : get_payload_width

    function fbrcvc_cfg get_iosf_sb_fabric_vc_cfg(string base_vc_name, fbrcvc_cfg fabric_vc_cfg, pid_queue_t related_pid, pid_queue_t other_pids, pid_queue_t mcast_pids, opcode_t local_supported_opcodes[$], int max_data_size, int local_payload_width, bit is_sb_active, int m_clkack_sync_delay = 4, bit m_input_flop=0);
        pid_queue_t seg_ports_for_fabric_vc = {`CCF_BASE_BOTTOM_SEG_ID};
        string vc_intf_name = {"sncu_",base_vc_name,"_iosf_sb_if"};
    
        fabric_vc_cfg.ext_header_support = 1;
        fabric_vc_cfg.ext_headers_per_txn = 1;
        fabric_vc_cfg.agt_ext_header_support = 1;
        fabric_vc_cfg.m_max_data_size = max_data_size;
        fabric_vc_cfg.global_intf_en = 1;
        fabric_vc_cfg.segment_scaling = 1; 
        assert (fabric_vc_cfg.randomize with  { 
                num_tx_ext_headers == 1;
                ext_headers[0] == 32'h00000000;
                payload_width == local_payload_width;
                compl_delay == 1;
                np_crd_buffer == 1;
                pc_crd_buffer == 1;
                my_ports.size() == related_pid.size();
                other_ports.size() == other_pids.size();
                mcast_ports.size() == mcast_pids.size();
                supported_opcodes.size() == local_supported_opcodes.size();
                foreach (related_pid[i]) my_ports[i] == related_pid[i];
                foreach (other_pids[i]) other_ports[i] == other_pids[i];
                foreach (mcast_pids[i]) mcast_ports[i] == mcast_pids[i];
                foreach (local_supported_opcodes[i]) supported_opcodes[i] == local_supported_opcodes[i];
                my_seg_ports.size() == seg_ports_for_fabric_vc.size();
                foreach (seg_ports_for_fabric_vc[i]) my_seg_ports[i] == seg_ports_for_fabric_vc[i];
            })
        else
            uvm_report_error (get_name (), {"fabric_vc_cfg for ", base_vc_name," randomization failed"});

        fabric_vc_cfg.set_cfg_clkack_sync_delay(m_clkack_sync_delay);
        fabric_vc_cfg.en_flop(m_input_flop);
        if(base_vc_name == "ncracu")   
            fabric_vc_cfg.inst_name = "soc_tb.soc_sncu_passive_iosf_sb_vc_instances.sb_ti_sncu_ncevnts_iosf_sb_if";
        else if(base_vc_name == "ncevnts")
            fabric_vc_cfg.inst_name = "soc_tb.soc_sncu_passive_iosf_sb_vc_instances.sb_ti_sncu_ncracu_iosf_sb_if";
        fabric_vc_cfg.set_debug_name({base_vc_name, "_dbg"});
        fabric_vc_cfg.is_active = uvm_active_passive_enum'(is_sb_active);
        fabric_vc_cfg.disable_compmon = 0;//is_compliance_disabled;
        fabric_vc_cfg.set_iosfspec_ver(IOSF_12);
        //configure SVC to not drive clkack since CCU will drive clkack
        fabric_vc_cfg.mon_enabled = 1;
        fabric_vc_cfg.disable_driving_clkack = 1;
        fabric_vc_cfg.cov_enabled = 0;
        fabric_vc_cfg.parity_en = 0;// FIXME TODO change to 1 after integration
        return fabric_vc_cfg;
    endfunction : get_iosf_sb_fabric_vc_cfg
    function void build_all_idp_sb_ep_monitors_passive_vc();
            pid_queue_t fab_other_ports = '{ SB_PORTID_PUNIT, SB_PORTID_HBO0, SB_PORTID_HBO1, SB_PORTID_CCF_ROOT_PMA,
                            `SNCU_CCF_SB_PORT_IDS, `SNCU_FUSE_PULL_EP_ID, `SNCU_IOMCA_NON_CCF_SOURCE_IDS , `SNCU_DUMP_SOURCE_IDS};
            pid_queue_t fab_mcast_ports ;
            //TODO update when fail pid_queue_t fab_mcast_ports =  {SB_PORTID_MCAST_DEV0CFG, SB_PORTID_MCAST_SAD_ALL, SB_PORTID_MCAST_LTCTRLSTS_ALL, SB_PORTID_MCAST_BIG_CORE_ALL};
            string all_idp_ep_monitor_names[$] = {"ncevnts", "ncracu"};
            
            
            foreach (all_idp_ep_monitor_names[i]) begin
                string ep_name = all_idp_ep_monitor_names[i];
                string comp_name = $sformatf("SBR_agent_%0d", ep_name);
                
                IDP_SBR_agentCfg[ep_name] = fbrcvc_cfg::type_id::create(ep_name, this);
                IDP_SBR_agentCfg[ep_name] = get_iosf_sb_fabric_vc_cfg(.base_vc_name(ep_name),
                                                                      .fabric_vc_cfg(IDP_SBR_agentCfg[ep_name]), 
                                                                      .related_pid('{ SB_PORTID_SNCU }),
                                                                      .other_pids(fab_other_ports), 
                                                                      .mcast_pids(fab_mcast_ports), 
                                                                      .local_supported_opcodes(fab_supp_opcodes), 
                                                                      .max_data_size(62), 
                                                                      .local_payload_width(get_payload_width(ep_name)), 
                                                                      .is_sb_active(0), 
                                                                      .m_clkack_sync_delay(8),
                                                                      .m_input_flop(1));

                IDP_SBR_agentCfg[ep_name].enable_credit_init_check = 1'b0;
                IDP_SBR_agentCfg[ep_name].independent_reset = 1;
                uvm_config_object::set (this, comp_name, "fabric_cfg", IDP_SBR_agentCfg[ep_name]);
                IDP_SBR_agent[ep_name] = iosfsbm_fbrcvc::type_id::create(comp_name,this);
            end
        endfunction : build_all_idp_sb_ep_monitors_passive_vc
    

    function void sb_build();
        racu_tracker = sncu_racu_tracker::type_id::create("sncu_racu_tracker", this);
        racu_tracker._sncu_env =  _sncu_env;
        build_all_idp_sb_ep_monitors_passive_vc();
    endfunction

 function void connect_analysis_fifo(const ref uvm_tlm_analysis_fifo #(iosfsbm_cm::xaction) gpsb_msg_fifo);
        foreach (IDP_SBR_agentCfg[ep_name]) begin
            IDP_SBR_agent[ep_name].tx_ap.connect(gpsb_msg_fifo.analysis_export);
            IDP_SBR_agent[ep_name].rx_ap.connect(gpsb_msg_fifo.analysis_export);
        end
    endfunction : connect_analysis_fifo
    function void connect_to_racu();
        foreach (IDP_SBR_agentCfg[ep_name]) begin
            IDP_SBR_agent[ep_name].open_tracker_file(.file_name({"SNCU_IOSF_", ep_name.toupper(), "_TRK.out"}), .print_new_sip_format(1'b1), .print_pid_name(0), .print_pid(1), .print_opc_name(1), .len_restrict(0), .timescale_info("ps"));
            set_opcodes_names(IDP_SBR_agent[ep_name]);
            if(ep_name == "ncracu") begin
                IDP_SBR_agent[ep_name].tx_ap.connect(racu_tracker.racu_sb_fifo.analysis_export);
                IDP_SBR_agent[ep_name].rx_ap.connect(racu_tracker.racu_sb_fifo.analysis_export);
            end
        end
    endfunction : connect_to_racu



    local function void set_opcodes_names(iosf_sb_vc sb_vc);
        sb_vc.load_opcode_name(`SNCU_PCU_NCU_MSG_OPCODE, "PCU_NCU_MSG");
        sb_vc.load_opcode_name(`SNCU_NCU_PCU_MSG_OPCODE, "NCU_PCU_MSG");
        sb_vc.load_opcode_name(`SNCU_NCU_NCU_MSG_OPCODE, "NCU_NCU_MSG");
        sb_vc.load_opcode_name(`SNCU_PCIE_ERR_MSG_OPCODE, "PCIE_ERR_MSG");
        sb_vc.load_opcode_name(`SNCU_MCLK_EVENT_MSG_OPCODE, "MCLK_EVENTS");
        sb_vc.load_opcode_name(`SNCU_RAS_NCU_EVENT_MSG_OPCODE, "RAS_NCU_EVENTS");
        sb_vc.load_opcode_name(`SNCU_FCLK_EVENT_MSG_OPCODE, "FCLK_EVENTS");
   	sb_vc.load_opcode_name(8'h45, "FUSE_MSG");
        sb_vc.load_opcode_name(8'hd0, "IP_READY");
    endfunction :set_opcodes_names
endclass
