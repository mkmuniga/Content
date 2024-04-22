///=====================================================================================================================
/// Title        : ccf_picker.sv
///
/// Primary Contact:    Roey Nagar
/// Creation Date:      04.2018
/// Last Review Date:
///
/// Copyright (c) 2013 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
///    This is the configuration object to control the ccf env.
///    The fields are being randomized, and support is added for plusargs override,
///    This Class contain all the switches to control the ENV setting.
///
///===================================================================================================================== 

import "DPI-C" function string getenv(input string env_name);

`picker_class_begin(ccf_picker)
    UVM_FILE push_command_file;

    // inside ccf we instantiate additional picker with stress modes knobs.
    rand ccf_agent_switches_picker ccf_agent_switches_pkr;
    string dut_str;
    rand bit module_disable_mask_same_as_cbo;
    rand int ccf_bisr_repair_conf[$];
    
    // ***************************************************************
    // Knobs definition
    // ***************************************************************    
    `add_knob_bit("REGRESSION_RUN", regression_run);
    `add_knob_enum("CCF_DIE", ccf_die, ccf_die_t);
    `add_knob_bit("CCF_ENABLE_NEW_PP_COLL", ccf_enable_new_pp_coll);
    `add_knob("CCF_CBB_ID",   ccf_cbb_id, bit[4:0]);
    `add_knob("CCF_SOCKET_ID",   ccf_socket_id, bit[10:0]);
    `add_knob_bit("SINGLE_THREAD", single_thread);
    `add_knob_uint("NUM_OF_CBO", num_of_cbo);
    `add_knob_uint("NUM_OF_RING_FIVRS", num_of_ring_fivrs);
    `add_knob_uint("NUM_OF_LLC_AGENTS", num_of_llc_agents); // in IP = num_of_cbo, in SOC = num_of_cbo * 4
    `add_knob_uint("NUM_OF_TQ", num_of_tq);
    `add_knob_uint("NUM_OF_SANTA", num_of_santa);
    `add_knob("CCF_ATOM_MASK", ccf_atom_mask, bit[31:0]); //TODO: need to use num_of_cluster and num_of_cbo parameter
    `add_knob_uint("CCF_IA_MASK", ccf_ia_mask);
    `add_knob_bit("SLICE_DISABLE", slice_disabled);
    `add_knob("CBO_DISABLE_MASK", cbo_disable_mask, bit[7:0]); // TODO: need to use num_of_cbo
    `add_knob("CCF_REAL_CORE_MASK", ccf_real_core_mask, bit[31:0]);
    `add_knob("MODULE_DISABLE_MASK", module_disable_mask, bit[31:0]); //TODO: need to use num_of_cluster and num_of_cbo parameter
    `add_knob_int("ALL_CORES_DISABLED", all_cores_disabled);
    `add_knob_bit("CCF_MKTME_EN",    mktme_en);
    `add_knob("CCF_MKTME_WIDTH", mktme_width, bit[3:0]);
    `add_knob("CCF_MKTME_MASK",  mktme_mask, bit[`MAX_MKTME_WIDTH-1:0]);
    `add_knob_enum("CCF_MKTME_MODE", ccf_mktme_mode, ccf_mktme_mode_t);
    `add_knob_enum("CCF_CONFIG_REG_ACCESS_MODE", config_reg_access_mode, ccf_reg_access_t);
    `add_knob_bit("ENABLE_CR_RANDOMIZATION", enable_cr_randomization);
    `add_knob_bit("DBP_EN", dbp_en);
    `add_knob_bit("CCF_MAX_OUTSTANDING_EN",ccf_max_outstanding_en);
    `add_knob_bit("IS_NEM_TEST", is_nem_test);
    `add_knob_uint("PERCENT_REUSE_ADDR", percent_reuse_addr);
    `add_knob_bit("CCF_ADDITIONAL_RING_TRK_FIELDS_EN", ccf_additional_ring_trk_fields_en);
    `add_knob_bit("GENERATE_PV_TRACKERS", generate_pv_trackers);

    
    `add_knob_bit ("CCF_DCD_EN", ccf_dcd_en);


//PMONs
    `add_knob_bit ("CCF_PMON_CHK_EN", pmon_chk_en); 
    `add_knob_uint("CLR_PMON_SLICE_ID", clr_pmon_slice_id);
    `add_knob_uint("CLR_PMON_COUNTER_ID", clr_pmon_counter_id);//0 or 1 in LNL (per cbo)
    `add_knob_uint("SANTA_NCU_PMON_SLICE_ID", santa_ncu_pmon_slice_id); //ncu is always at santa0
    `add_knob_uint("SANTA_NCU_PMON_COUNTER_ID", santa_ncu_pmon_counter_id);//0 or 1 in LNL (per santa)
    `add_knob_enum("PMON_CBO_EVENT_NAME", pmon_cbo_event_name, clr_pmon_event_t);
    `add_knob_enum("PMON_CBO_EVENT_MASK", pmon_cbo_sub_event_mask, ccf_pmon_mask_t);//can be 0:max of 3 lsb ob the event name bits
    `add_knob_enum("PMON_SANTA_NCU_EVENT_NAME", pmon_santa_ncu_event_name, santa_ncu_pmon_event_t);
    `add_knob_enum("PMON_SANTA_NCU_EVENT_MASK", pmon_santa_ncu_sub_event_mask, ccf_pmon_mask_t);//can be 0:max of 3 lsb ob the event name bits
    `add_knob_bit ("PMON_SBO_EN", pmon_sbo_en);
    `add_knob_bit ("PMON_OVERFLOW", pmon_overflow);
    `add_knob_bit ("PMON_LPID_EN", pmon_lpid_en);
    `add_knob_uint("PMON_LPID", pmon_lpid);//pmon_global_ctrl
    `add_knob_uint("PMON_MODULE_ID", pmon_module_id);//pmon_global_ctrl
    
    
    //Follow knobs are in base layer since we need then in ccf_config
    `add_knob_uint("LLC_NUM_OPENED_DATA_WAYS", llc_num_opened_data_ways); // number of LLC ways
    `add_knob_bit("ENABLE_NO_DATA_WAYS", enable_no_data_ways); // Add a constraint to make sure llc_num_opened_data_ways are not equal to 0
    `add_knob_uint("CCF_HASH_BIT0_LSB", hash_bit0_lsb);
    `add_knob_uint("CCF_HASH_BIT0_MASK", hash_bit0_mask);
    `add_knob_bit("CCF_BISR_REPAIR_EN", ccf_bisr_repair_en);
    `add_knob_bit("CCF_PRELOAD_DATA_CORRECTABLE_ERRS",ccf_preload_data_correctable_errs);
    `add_knob_bit("CCF_PRELOAD_TAG_CORRECTABLE_ERRS",ccf_preload_tag_correctable_errs);

    
    `add_knob_bit("LLC_DATA_ROW_RED_STRESS_EN", llc_data_row_red_stress_en);
    `add_knob_bit("LLC_DATA_COL_RED_STRESS_EN", llc_data_col_red_stress_en);
    `add_knob_bit("LLC_TAG_ROW_RED_STRESS_EN", llc_tag_row_red_stress_en);
    `add_knob_bit("LLC_TAG_COL_RED_STRESS_EN", llc_tag_col_red_stress_en);
    `add_knob_bit("LLC_RF_RED_STRESS_EN",      llc_rf_red_stress_en);
    `add_knob_bit("SAVE_RESTORE_RED_STRESS_EN", save_restore_red_stress_en);
    
    //Needed for preload
    `add_knob_bit("CCF_FUSA_RTL_EN", ccf_fusa_rtl_en);
    `add_knob_bit("CCF_FUSA_CONFIG_BY_FUSE", ccf_fusa_config_by_fuse);
    `add_knob_bit ("LLC_DOUBLE_PARITY_OVR_EN",  llc_double_parity_ovr_en);
    `add_knob_bit ("LLC_DOUBLE_PARITY_OVR",  llc_double_parity_ovr);
    `add_knob_bit ("IS_FUSA_TEST",  is_fusa_test);    
    `add_knob_bit ("CCF_FUSA_PARITY_VC_CHK_EN",  ccf_fusa_parity_vc_chk_en);
    
    `add_knob_bit ("CCF_DISABLE_LRU",  ccf_disable_lru);
    
    `add_knob_enum("CCF_VIP_LAYERING", ccf_vip_layering, ccf_vip_layering_t);
    `add_knob_bit ("CCF_PICKER_CSI_COV", ccf_picker_csi_cov); 
    
    `add_knob_bit("CCF_ALWAYS_MEM_LOCK_CPU_CLR", always_mem_lock_cpu_clr);

    //DFD pickers
    `add_knob_bit ("CCF_DFD_EN", ccf_dfd_en);
    `add_knob_bit ("CCF_CDTF_EN", ccf_cdtf_en);
    `add_knob_bit ("CCF_CBO_OBS_EN", ccf_cbo_obs_en);
    `add_knob_bit ("CNCU_OBS_EN", cncu_obs_en);
   
    //CV bit parity error pickers
    `add_knob_bit ("CCF_EN_INJECT_CV_PAR_ERR",     ccf_en_inject_cv_par_err);
    `add_knob_bit ("CCF_EN_MCA_ON_CV_PAR_ERR",     ccf_en_mca_on_cv_par_err);
   
    //PUMBA agents pickers
    `add_knob_bit ("CCF_PUMBA_CBO_OBS_CHK_EN", ccf_pumba_cbo_obs_chk_en);
    `add_knob_bit ("CCF_PUMBA_CBO_OBS_COV_EN", ccf_pumba_cbo_obs_cov_en);
    `add_knob_bit ("CCF_PUMBA_NCU_OBS_CHK_EN", ccf_pumba_ncu_obs_chk_en);
    `add_knob_bit ("CCF_PUMBA_NCU_OBS_COV_EN", ccf_pumba_ncu_obs_cov_en);
    `add_knob_bit ("CCF_PUMBA_SAVE_RESTORE_CHK_EN", ccf_pumba_save_restore_chk_en);
    `add_knob_bit ("CCF_PUMBA_SAVE_RESTORE_COV_EN", ccf_pumba_save_restore_cov_en);

    
    //Hash Adjusment function pickers
    `add_knob("CCF_HASH_ADJUSTMENT_H3_H4_11", ccf_hash_adjustment_h3_h4_11, bit[1:0]);
    `add_knob("CCF_HASH_ADJUSTMENT_H3_H4_10", ccf_hash_adjustment_h3_h4_10, bit[1:0]);
    `add_knob("CCF_HASH_ADJUSTMENT_H3_H4_01", ccf_hash_adjustment_h3_h4_01, bit[1:0]);
    `add_knob("CCF_HASH_ADJUSTMENT_H3_H4_00", ccf_hash_adjustment_h3_h4_00, bit[1:0]);
    `add_knob_enum("CCF_HASH_ADJUSTMENT_SKU", ccf_hash_adjustment_sku     , ccf_hash_adjust_sku_t);    

    `add_knob_bit ("DPT_DIS", dpt_dis);
    
    //RDT- CMT
    `add_knob_int("CCF_RMID_EQUAL_CBO_PERCENT", ccf_rmid_equal_cbo_percent);
    
    `INST_CCF_PICKER_CG

    //----------------------------------------
    //----------------------------------------
    function void build();
        super.build();
        ccf_agent_switches_pkr = ccf_agent_switches_picker::type_id::create("agt_sw", this);
        ccf_agent_switches_pkr.push_command_file = push_command_file;
    endfunction: build
    
    function void randomize_repair_bisr_values();
        bit file_was_created;

        foreach (ccf_bisr_repair_conf[k]) begin
            `uvm_info(get_type_name(),$psprintf("ccf_bisr_repair_conf[%0d] =  %0d",k, ccf_bisr_repair_conf[k]),UVM_LOW)
            if (ccf_bisr_repair_conf[k] > 0) begin
                string create_sv_class_file = "-V ";
                string seed;
                string randomize = "-r ";
                int unsigned random_seed;
                string red_type;
                string bisr_num;
                string aligned_bisr_ip;
                string num_of_defects = "1 ";
                string all_strs;
                string array_type;
                string script_path = "$WORKAREA/bin/CCF_BISR/CreateBISRString.py ";
                string create_dict_chain = "-c $WORKAREA/bin/CCF_BISR/bisr_chain_dict.data ";
                $value$plusargs("ntb_random_seed=%0d",random_seed);
                seed = $sformatf("-s %0d", random_seed);

                case (k)
                    0: begin array_type = "save_restore"; bisr_num = "";  end
                    1: begin array_type = "llc_rf";       bisr_num = "1"; end
                    2: begin array_type = "llc_rf";       bisr_num = "";  end
                    3: begin array_type = "llc_data";     bisr_num = "1"; end
                    4: begin array_type = "llc_data";     bisr_num = "";  end
                    5: begin array_type = "llc_tag";      bisr_num = "1"; end
                    6: begin array_type = "llc_tag";      bisr_num = "";  end
                endcase

                aligned_bisr_ip = {"bisr_ccf_",array_type ,"_hard_repair_bisr_ip_inst"};

                if (bisr_num == "1")
                    aligned_bisr_ip = {aligned_bisr_ip,bisr_num," "};
                else
                    aligned_bisr_ip = {aligned_bisr_ip," "};

                if      (ccf_bisr_repair_conf[k] == 1)
                    red_type = "rows ";
                else if (ccf_bisr_repair_conf[k] == 2)
                    red_type = "cols ";

                all_strs = {script_path, create_dict_chain, "--bisr_ip ", aligned_bisr_ip, randomize, red_type, create_sv_class_file, seed, " -n ", num_of_defects};
                $fdisplay(push_command_file, "PRE: %s", all_strs);
                $fdisplay(push_command_file, "TEST_VLOG_OPTS: +define+include_bisr_%s%s", array_type, bisr_num);
                file_was_created = 1;
            end
        end
        if (file_was_created)
            $fdisplay(push_command_file, "TEST_VLOG_OPTS: +define+INCLUDE_BISR_VALUES");
    endfunction

    //----------------------------------------
    // Place holder to add PUSH_COMMANDs
    //----------------------------------------
    
    function void pre_randomize();
        super.pre_randomize();
        `ifdef CCF_IP_STANDALONE_DEFINE
            dut_str = getenv("DUT");
        `else 
            dut_str = "ccf_8c";//getenv("DUT");
        `endif
    endfunction
  
    function void post_randomize();
        if (ccf_picker_csi_cov) ccf_picker_cg_i.sample();
  
        if (!(dut_str inside {"ccf_2c","ccf_4c", "ccf_6c", "ccf_8c"}) && (ccf_vip_layering == CCF_TYP_LAYER))
            `uvm_fatal("push_command_file", $psprintf("DUT = %s is not defined well for IP validation. It must be ccf_2c or ccf_4c or ccf_6c ccf_8c", dut_str));

    endfunction
    
`picker_class_end

//--------------------------------------------
// ccf picker default constraints
//--------------------------------------------
`constraint_class_begin(ccf_picker_default_constraints, ccf_picker, ptr)
    // default constraints
    
   constraint ccf_enable_new_pp_coll_c {
    soft ptr.ccf_enable_new_pp_coll == 1;
   }
   constraint memlockcpuclr_c{
        ptr.always_mem_lock_cpu_clr == 1;
        
        (ptr.always_mem_lock_cpu_clr == 0) -> (ptr.ccf_agent_switches_pkr.ccf_pp_dump_chk_en == 0);
    }
    
    constraint ccf_default_cfg_const {
        soft ptr.regression_run == 0;
        soft ptr.ccf_vip_layering == CCF_TYP_LAYER;
        ptr.percent_reuse_addr inside {[0:100]};
        soft ptr.enable_cr_randomization dist {0:=1, 1:=9};
        soft ptr.dbp_en == 0;// FIXME: need to re-enable for CBB dist {0:=1, 1:=9};
        soft ptr.ccf_max_outstanding_en dist {0 := 80, 1 := 20};
        soft ptr.is_nem_test == 0; //Only in NEM TEST it's relevant. this is implemented by SI knob (other than plusargs) because it should be propagated to PP env
        soft ptr.generate_pv_trackers == 0; 
        soft ptr.single_thread dist {0:=90, 1:=10};
        soft ptr.dpt_dis == 1;//FIXME: need to re-enable after 0.3 dist {0:=50, 1:=50};
    }
    
    constraint dut_to_ccf_model{
        (ptr.dut_str == "ccf_4c") -> ptr.ccf_die inside {CCF_DIE_CBB_4C};
        (ptr.dut_str == "ccf_6c") -> ptr.ccf_die inside {CCF_DIE_CBB_6C, CCF_DIE_CBB_6C_SOC};
        (ptr.dut_str == "ccf_8c") -> ptr.ccf_die inside {CCF_DIE_CBB_8C, CCF_DIE_CBB_8C_SOC};
    }
    
    constraint module_config_const{
        solve ptr.ccf_die before ptr.num_of_cbo;
        solve ptr.ccf_die before ptr.num_of_ring_fivrs;
        solve ptr.num_of_cbo before ptr.ccf_ia_mask;
        solve ptr.ccf_ia_mask before ptr.ccf_atom_mask;
        solve ptr.num_of_cbo before ptr.slice_disabled;
        solve ptr.slice_disabled before ptr.cbo_disable_mask;
        solve ptr.cbo_disable_mask before ptr.module_disable_mask;
        solve ptr.all_cores_disabled before ptr.module_disable_mask;
        solve ptr.module_disable_mask_same_as_cbo before ptr.module_disable_mask;
        solve ptr.num_of_cbo before ptr.ccf_real_core_mask;
        
        soft ptr.ccf_cbb_id == 4'b0010;//CBB BRINGUP TEMP
        ptr.ccf_socket_id == 4'h0;//CBB BRINGUP TEMP
        
        soft ptr.all_cores_disabled == 0;
        
        ptr.num_of_tq inside {1,2};
        ptr.num_of_tq == 1; //TODO: need to remove this constraint once we will support different TQ values

	(ptr.ccf_vip_layering == CCF_BASE_LAYER) -> (ptr.slice_disabled != PATCHABLE);
        ptr.num_of_cbo inside {4,6,8};
        ptr.num_of_ring_fivrs inside {4,6,8};
        ptr.ccf_real_core_mask inside {[0:(2**ptr.num_of_cbo)-1]};
        soft ptr.ccf_real_core_mask == 0;
        
        (ptr.ccf_atom_mask & ptr.ccf_ia_mask) == 0;
        (ptr.ccf_atom_mask | ptr.ccf_ia_mask) == (2**ptr.num_of_cbo)-1;
        

        if (ptr.ccf_vip_layering == CCF_TYP_LAYER)
            soft ptr.ccf_die inside {CCF_DIE_CBB_8C, CCF_DIE_CBB_6C, CCF_DIE_CBB_4C};
        else
            ptr.ccf_die inside {CCF_DIE_CBB_6C_SOC, CCF_DIE_CBB_8C_SOC};

        if (ptr.ccf_die inside {CCF_DIE_CBB_6C_SOC, CCF_DIE_CBB_8C_SOC})
            ptr.num_of_llc_agents == ptr.num_of_cbo*4; // TODO: nice to have - change 4 to parameter
        else
            ptr.num_of_llc_agents == ptr.num_of_cbo;
    

        (ptr.ccf_die inside {CCF_DIE_CBB_8C, CCF_DIE_CBB_8C_SOC}) -> (ptr.num_of_cbo == 8 && ptr.ccf_atom_mask == 'h0 && ptr.num_of_ring_fivrs==8);
        (ptr.ccf_die inside {CCF_DIE_CBB_6C, CCF_DIE_CBB_6C_SOC}) -> (ptr.num_of_cbo == 6 && ptr.ccf_atom_mask == 'h0 && ptr.num_of_ring_fivrs==6);
        (ptr.ccf_die == CCF_DIE_CBB_4C) -> (ptr.num_of_cbo == 4 && ptr.ccf_atom_mask == 'h0 && ptr.num_of_ring_fivrs==4);
      
        (ptr.num_of_cbo inside {2, 4}) -> (ptr.slice_disabled == 0);   

        ptr.slice_disabled == 0; //TODO: need to enable as soon as we can.
        (ptr.slice_disabled == 1) -> (ptr.cbo_disable_mask != 0);
        (ptr.slice_disabled == 0) -> (ptr.cbo_disable_mask == 0);
        

        ptr.all_cores_disabled == 1 -> ptr.module_disable_mask == (2**(ptr.num_of_cbo*4))-1; //TODO: replace "4" with num_of_cluster parameter
        ptr.num_of_cbo == 4  -> ptr.cbo_disable_mask inside {`SLICE_CONFIG_4_MODULES};
        ptr.num_of_cbo == 6  -> ptr.cbo_disable_mask inside {`SLICE_CONFIG_6_MODULES};
        ptr.num_of_cbo == 8  -> ptr.cbo_disable_mask inside {`SLICE_CONFIG_8_MODULES};
        //ptr.num_of_cbo == 10 -> ptr.cbo_disable_mask inside {`SLICE_CONFIG_10_MODULES};
        
        //(ptr.module_disable_mask == ptr.cbo_disable_mask) dist {1:= 70, 0:=30};
        //ptr.module_disable_mask == (ptr.module_disable_mask | ptr.cbo_disable_mask);

        ptr.module_disable_mask_same_as_cbo dist {1:= 70, 0:=30};

        foreach (ptr.cbo_disable_mask[i]){
            if (i < ptr.num_of_cbo) {
                if (ptr.cbo_disable_mask[i] == 1){
                    ptr.module_disable_mask[i*4 +: 4] == 4'b1111;
                } else {
                    if (ptr.module_disable_mask_same_as_cbo) {
                       ptr.module_disable_mask[i*4 +: 4] == 4'b0000;
                    } else {
                        ptr.module_disable_mask[i*4 +: 4] inside { [4'b0000:4'b1111] }; // Randomize 4-bit value
                    }
                }
            }
        }

        ptr.module_disable_mask inside {[0:(2**(ptr.num_of_cbo*4))-1]}; //TODO: replace "4" with num_of_cluster parameter
        soft ptr.module_disable_mask != (2**(ptr.num_of_cbo*4))-1; //TODO: replace "4" with num_of_cluster parameter
    }

    constraint santa_const{
        ptr.num_of_santa == 1;
    }

    constraint llc_num_opened_data_ways_c {
        solve ptr.enable_no_data_ways before ptr.llc_num_opened_data_ways;

        soft ptr.enable_no_data_ways  dist {1 := 1, 0 := 99};
        
        (ptr.enable_no_data_ways == 0) -> ptr.llc_num_opened_data_ways != 0;
        (ptr.enable_no_data_ways == 1) -> ptr.llc_num_opened_data_ways == 0;
    
        ptr.llc_num_opened_data_ways dist {0:= 1, [1:19] := 39, 20 := 60};
    }

    // if you change this constraint, change in idib as well
    constraint ccf_hash_mask_const {
        solve ptr.hash_bit0_lsb before ptr.hash_bit0_mask;
        ptr.hash_bit0_lsb inside {[0:7]};
        ptr.hash_bit0_mask[31:14] == 0;
        ((ptr.hash_bit0_mask >> ptr.hash_bit0_lsb) %2) == 1;
        ((ptr.hash_bit0_mask >> ptr.hash_bit0_lsb) << ptr.hash_bit0_lsb) == ptr.hash_bit0_mask;
    }

    constraint redundency_c {
    //ccf_bisr_repair_configuration:
    //digit 6 - tag 0
    //digit 5 - tag 1
    //digit 4 - data 0
    //digit 3 - data 1
    //digit 2 - rf 0
    //digit 1 - rf 1
    //digit 0 - save_restore

    //value for each digit:
    //0 - no repair
    //1 - row repair
    //2 - col repair - irrelevant in RF
    //3 - both repair - buggy, won't be use
    soft ptr.ccf_bisr_repair_en == 0;//FIXME: aviad - re-enable when BISR is updated for CBB dist {1 := 9, 0 := 1};
    ptr.ccf_bisr_repair_conf.size() == 7;
    
    foreach (ptr.ccf_bisr_repair_conf[k]) {
            if (ptr.ccf_bisr_repair_en == 0) {
                    ptr.ccf_bisr_repair_conf[k] == 0;
                }
            else {
                    if (k inside {[3:6]}) {//tag and data support both cols/rows
                            ptr.ccf_bisr_repair_conf[k] inside {[0:2]};//to be fixed up to 2
                    }
                    else {//rf and s/r - only row is supported
                            ptr.ccf_bisr_repair_conf[k] inside {0,1};
                    }
                }
        }
    }   

    constraint mca_ecc_en_c {
        soft ptr.ccf_preload_data_correctable_errs dist {1 := 2, 0 := 8};
        soft ptr.ccf_preload_tag_correctable_errs dist {1 := 2, 0 := 8};
    }

    constraint ccf_mktme_c {
        solve ptr.mktme_width before ptr.mktme_mask;
        soft ptr.mktme_en dist {1 := 70, 0 := 30};
        
        ptr.mktme_mask == ({`MAX_MKTME_WIDTH{1'b1}} >> ptr.mktme_width); 

        //0 - no key allowed, 11 - all keys allowed 
        ptr.mktme_width == `MAX_MKTME_WIDTH; //TODO should be removed when dynamic MKTME is enabled
        ptr.mktme_width dist {
            0                := 10,
            [1:5]            :/ 30,
            [6:10]           :/ 30,
            `MAX_MKTME_WIDTH := 30
        };

        ptr.ccf_mktme_mode dist {FULLY_RANDOM := 20, SEMI_RANDOM := 80};
        
    }

    constraint pmon_const {
        solve ptr.pmon_cbo_event_name before ptr.pmon_cbo_sub_event_mask;
        solve ptr.pmon_santa_ncu_event_name before ptr.pmon_santa_ncu_sub_event_mask;
        solve ptr.santa_ncu_pmon_slice_id before ptr.pmon_santa_ncu_event_name;
        solve ptr.pmon_cbo_event_name before ptr.pmon_lpid_en;
        ptr.pmon_lpid_en dist {0:=50, 1:=50};
        ptr.pmon_lpid dist {0:=65, 1:=30, 2:=5}; //in LNL_M we don't have thread 2, but we want to check it doesn't have bugs
        ptr.pmon_module_id <= ptr.num_of_cbo; 
        (ptr.pmon_cbo_event_name == CBO_C2P_SNP_REQ) ->
            ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0_4,PMON_SUB_EV_MASK_1_4,PMON_SUB_EV_MASK_2_4,PMON_SUB_EV_MASK_3_4,
                                                PMON_SUB_EV_MASK_0_5,PMON_SUB_EV_MASK_1_5,PMON_SUB_EV_MASK_2_5,PMON_SUB_EV_MASK_3_5,
                                                PMON_SUB_EV_MASK_0_6,PMON_SUB_EV_MASK_1_6,PMON_SUB_EV_MASK_2_6,PMON_SUB_EV_MASK_3_6,
                                                PMON_SUB_EV_MASK_0_7,PMON_SUB_EV_MASK_1_7,PMON_SUB_EV_MASK_2_7,PMON_SUB_EV_MASK_3_7};
        
        (ptr.pmon_cbo_event_name == CBO_CACHE_HITS) -> 
            ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0_4,PMON_SUB_EV_MASK_3_4,PMON_SUB_EV_MASK_0_5,PMON_SUB_EV_MASK_3_5};
        (ptr.pmon_cbo_event_name == CBO_TOR_OCCUPANCY) -> 
            ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1,PMON_SUB_EV_MASK_2,PMON_SUB_EV_MASK_3,PMON_SUB_EV_MASK_4,PMON_SUB_EV_MASK_5,
						PMON_SUB_EV_MASK_0_6,PMON_SUB_EV_MASK_1_6,PMON_SUB_EV_MASK_2_6,PMON_SUB_EV_MASK_3_6,PMON_SUB_EV_MASK_4_6,PMON_SUB_EV_MASK_5_6};
        ptr.pmon_cbo_event_name inside {CBO_XSNP_RESPONSE, CBO_CACHE_LOOKUP} -> ptr.pmon_cbo_sub_event_mask  == PMON_SUB_EV_MASK_FREE;
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 7 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5, PMON_SUB_EV_MASK_6, PMON_SUB_EV_MASK_7};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP  && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 6 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5, PMON_SUB_EV_MASK_6};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 5 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 4 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 3 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 2 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 1 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1};
        ptr.pmon_cbo_event_name != CBO_XSNP_RESPONSE && ptr.pmon_cbo_event_name != CBO_C2P_SNP_REQ && ptr.pmon_cbo_event_name != CBO_CACHE_LOOKUP && ptr.pmon_cbo_event_name != CBO_CACHE_HITS && ptr.pmon_cbo_event_name[2:0] == 0 -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0};

        ptr.pmon_cbo_event_name == CBO_IPQ_REJECTS  -> ptr.pmon_cbo_sub_event_mask != PMON_SUB_EV_MASK_4;
        ptr.pmon_cbo_event_name == CBO_ISMQ_REJECTS || ptr.pmon_cbo_event_name == CBO_IPQ_REJECTS || ptr.pmon_cbo_event_name == CBO_IRQ_REJECTS || ptr.pmon_cbo_event_name == CBO_INGRESS_ALLOCATION || ptr.pmon_cbo_event_name == RING_SCALE_OCC_EVENTS  -> ptr.pmon_cbo_sub_event_mask != PMON_SUB_EV_MASK_3;
        ptr.pmon_cbo_event_name == CBO_ISMQ_REJECTS || ptr.pmon_cbo_event_name == RING_SCALE_OCC_EVENTS  -> ptr.pmon_cbo_sub_event_mask != PMON_SUB_EV_MASK_2;
        ptr.pmon_cbo_event_name == CBO_INGRESS_STARVATION  || ptr.pmon_cbo_event_name == RING_SCALE_OCC_EVENTS -> ptr.pmon_cbo_sub_event_mask != PMON_SUB_EV_MASK_1; 
        ptr.pmon_cbo_event_name == CBO_MISC -> ptr.pmon_cbo_sub_event_mask != PMON_SUB_EV_MASK_0; 
        ptr.clr_pmon_counter_id dist {0:=50, 1:=50};
        ptr.clr_pmon_slice_id inside {[0:ptr.num_of_cbo-1]};
        
        (!ptr.pmon_cbo_event_name inside {EGRESS_STARVATION_RESERVATION_USED,SBO_ARAC_RING_BLOCK,CBO_SBO_EGRESS_OCCUPANCY,
					CBO_SBO_EGRESS_ALLOCATION,CBO_EGRESS_STARVATION , CBO_EGRESS_ADS_USED , 
                                        CBO_AD_RING_IN_USE, CBO_AK_RING_IN_USE,CBO_BL_RING_IN_USE, CBO_IV_RING_IN_USE,CBO_OCCUPANCY_AUX, 
                                        Travel_ring_switched, RING_SCALE_EVENTS, RING_SCALE_OCC_EVENTS}) -> ptr.pmon_sbo_en == 0;
        ptr.pmon_cbo_event_name inside {EGRESS_STARVATION_RESERVATION_USED, SBO_ARAC_RING_BLOCK} -> ptr.pmon_sbo_en == 1; 
        ptr.pmon_cbo_event_name inside {CBO_SBO_EGRESS_OCCUPANCY,CBO_SBO_EGRESS_ALLOCATION,CBO_EGRESS_STARVATION , CBO_EGRESS_ADS_USED , 
                                        CBO_AD_RING_IN_USE, CBO_AK_RING_IN_USE,CBO_BL_RING_IN_USE, CBO_IV_RING_IN_USE,CBO_OCCUPANCY_AUX, 
                                        Travel_ring_switched} -> ptr.pmon_sbo_en dist {0:=50, 1:=50};
        ptr.pmon_cbo_event_name inside {RING_SCALE_EVENTS, RING_SCALE_OCC_EVENTS} && ptr.pmon_cbo_sub_event_mask == PMON_SUB_EV_MASK_0 -> ptr.pmon_sbo_en dist {0:=50, 1:=50};
        ptr.pmon_cbo_event_name == RING_SCALE_OCC_EVENTS && ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_4,PMON_SUB_EV_MASK_5}-> ptr.pmon_sbo_en == 1; 
        ptr.pmon_sbo_en == 1 -> ptr.pmon_cbo_event_name inside {EGRESS_STARVATION_RESERVATION_USED, SBO_ARAC_RING_BLOCK,
                                        CBO_SBO_EGRESS_OCCUPANCY,CBO_SBO_EGRESS_ALLOCATION,CBO_EGRESS_STARVATION , CBO_EGRESS_ADS_USED , 
                                        CBO_AD_RING_IN_USE, CBO_AK_RING_IN_USE,CBO_BL_RING_IN_USE, CBO_IV_RING_IN_USE,CBO_OCCUPANCY_AUX, 
                                        Travel_ring_switched, RING_SCALE_EVENTS, RING_SCALE_OCC_EVENTS};
        ptr.pmon_sbo_en == 1 && ptr.pmon_cbo_event_name == RING_SCALE_EVENTS -> ptr.pmon_cbo_sub_event_mask == PMON_SUB_EV_MASK_0;
        ptr.pmon_sbo_en == 1 && ptr.pmon_cbo_event_name == RING_SCALE_OCC_EVENTS -> ptr.pmon_cbo_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_4,PMON_SUB_EV_MASK_5};
        ptr.santa_ncu_pmon_counter_id dist {0:=50, 1:=50};
        //ptr.santa_ncu_pmon_slice_id dist {0:=50, 1:=50};
        //ptr.santa_ncu_pmon_slice_id == 1 -> ptr.pmon_santa_ncu_event_name[10:3] >= 8'h70; //NCU pmons can be only in santa0
        ptr.santa_ncu_pmon_slice_id == 0; //We have only one Santa
        
        ptr.pmon_santa_ncu_event_name[2:0] == 7 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5, PMON_SUB_EV_MASK_6, PMON_SUB_EV_MASK_7};
        ptr.pmon_santa_ncu_event_name[2:0] == 6 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5, PMON_SUB_EV_MASK_6};
        ptr.pmon_santa_ncu_event_name[2:0] == 5 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4, PMON_SUB_EV_MASK_5};
        ptr.pmon_santa_ncu_event_name[2:0] == 4 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3, PMON_SUB_EV_MASK_4};
        ptr.pmon_santa_ncu_event_name[2:0] == 3 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2, PMON_SUB_EV_MASK_3};
        ptr.pmon_santa_ncu_event_name[2:0] == 2 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1, PMON_SUB_EV_MASK_2};
        ptr.pmon_santa_ncu_event_name[2:0] == 1 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0,PMON_SUB_EV_MASK_1};
        ptr.pmon_santa_ncu_event_name[2:0] == 0 -> ptr.pmon_santa_ncu_sub_event_mask inside {PMON_SUB_EV_MASK_0};
        ptr.pmon_santa_ncu_event_name == NCU_U2C_EVENTS -> ptr.pmon_santa_ncu_sub_event_mask != PMON_SUB_EV_MASK_0;
        ptr.pmon_santa_ncu_event_name == NCU_U2C_EVENTS -> ptr.pmon_santa_ncu_sub_event_mask != PMON_SUB_EV_MASK_1;
        ptr.pmon_santa_ncu_event_name == SANTA_SNP_RESPONSE -> ptr.pmon_santa_ncu_sub_event_mask != PMON_SUB_EV_MASK_2;

       ptr.pmon_cbo_event_name inside {CBO_XSNP_RESPONSE,CBO_PMON_MONITOR_ARRAY_ALLOCATION, CBO_C2P_SNP_REQ, MUFASA_DBP_Rsp, 
				       CBO_TOR_FULL,CBO_No_CREDITS_FOR_SANTA0 ,CBO_No_CREDITS_FOR_SANTA1} -> ptr.pmon_lpid_en == 0;

        ptr.pmon_chk_en == 1 && ptr.pmon_cbo_event_name inside {CBO_AD_RING_IN_USE, CBO_AK_RING_IN_USE, CBO_BL_RING_IN_USE, CBO_IV_RING_IN_USE} -> ptr.ccf_additional_ring_trk_fields_en == 1;
                
    }

    constraint fusa_const {
        ptr.ccf_fusa_rtl_en == 0; // TODO: should be open for CBB ? dist {0:=3, 1:=7};
//asurend enable later	ptr.ccf_fusa_rtl_en dist {0:=3, 1:=7}; //PTL run with FUSA

        soft ptr.is_fusa_test == 1'b0;
        }

    constraint ccf_config_reg_access_c {
        ptr.config_reg_access_mode inside {RANDOM,IDI,SB,BACKDOOR}; // In TYP picker we will have more constraint for this knob//
        }

    constraint ccf_larger_ring_trk_en_c {
        soft ptr.ccf_additional_ring_trk_fields_en == 0;
    }


    constraint ccf_pmon_chk_en_c {
        if (ptr.ccf_vip_layering != CCF_TYP_LAYER) {
          soft ptr.pmon_chk_en == 0;
        }
        }

    constraint dfd_const {
        soft ptr.ccf_cbo_obs_en dist {0:=8, 1:=2};//== 0; //FIXME: need to re-enable for CBB. dist {0:=6, 1:=4};
        soft ptr.cncu_obs_en    dist {0:=8, 1:=2};
        soft ptr.ccf_dfd_en     == 0; // TODO FIXME lyaakovi re-enabled once pcu_santa obs block/unblock is supported 
//        soft ptr.ccf_dfd_en     dist {0:=8, 1:=2};
        soft ptr.ccf_cdtf_en    dist {0:=8, 1:=2};
        soft ptr.ccf_dcd_en     dist {0:=8, 1:=2};
        
        solve ptr.cncu_obs_en before ptr.ccf_cbo_obs_en;
        solve ptr.ccf_cbo_obs_en before ptr.ccf_dfd_en;
        solve ptr.ccf_cdtf_en    before ptr.ccf_dfd_en;
        solve ptr.ccf_dcd_en     before ptr.ccf_dfd_en;
        
       (ptr.ccf_cbo_obs_en | ptr.cncu_obs_en | ptr.ccf_cdtf_en | ptr.ccf_dcd_en) -> (ptr.ccf_dfd_en == 1);

       ptr.ccf_cbo_obs_en == ptr.cncu_obs_en;//checker use a merged DB for both observers
     

        if (ptr.ccf_vip_layering != CCF_TYP_LAYER) {
            ptr.ccf_cbo_obs_en == 0;
            ptr.ccf_cdtf_en == 0;
            ptr.ccf_dcd_en == 0;
        }
        //cdft doesn't work with dcd
        (ptr.ccf_cdtf_en & ptr.ccf_dcd_en) == 0;

    }

    constraint cv_bit_par_err_const
    {
        soft ptr.ccf_en_mca_on_cv_par_err == 0;
        ptr.ccf_en_inject_cv_par_err dist {0:=95, 1:=5};
    }

    //SAVE_RESTORE section  #FIXME - roeilevi
    constraint ccf_pumba_save_restore_chk_en_c {
      soft ptr.ccf_pumba_save_restore_chk_en == 0;
      soft ptr.ccf_pumba_save_restore_cov_en == 0;
    }

    constraint pumba_const {
        //CNCU OBS section
       
        if (ptr.cncu_obs_en == 1 || ptr.ccf_cbo_obs_en == 1) {     //Enable PUMBA AGENT 
            soft ptr.ccf_pumba_ncu_obs_chk_en == 1;
            soft ptr.ccf_pumba_ncu_obs_cov_en == 1; 
	    soft ptr.ccf_pumba_cbo_obs_chk_en == 1;
            soft ptr.ccf_pumba_cbo_obs_cov_en == 1;
	    
        } else {
            ptr.ccf_pumba_ncu_obs_chk_en == 0; 
            ptr.ccf_pumba_ncu_obs_cov_en == 0; 
            ptr.ccf_pumba_cbo_obs_chk_en == 0; 
            ptr.ccf_pumba_cbo_obs_cov_en == 0; 
        }

      
        solve ptr.ccf_cbo_obs_en before ptr.ccf_pumba_cbo_obs_chk_en;
        solve ptr.ccf_cbo_obs_en before ptr.ccf_pumba_cbo_obs_cov_en;
        solve ptr.cncu_obs_en    before ptr.ccf_pumba_ncu_obs_chk_en;
        solve ptr.cncu_obs_en    before ptr.ccf_pumba_ncu_obs_cov_en;
        // -- 

    }
    
    constraint hash_adjust_const  {
        unique { ptr.ccf_hash_adjustment_h3_h4_11,  ptr.ccf_hash_adjustment_h3_h4_10,  ptr.ccf_hash_adjustment_h3_h4_01,  ptr.ccf_hash_adjustment_h3_h4_00};
        //ptr.ccf_hash_adjustment_h3_h4_11 inside {[0:3]};
        //ptr.ccf_hash_adjustment_h3_h4_10 inside {[0:3]};
        //ptr.ccf_hash_adjustment_h3_h4_01 inside {[0:3]};
        //ptr.ccf_hash_adjustment_h3_h4_00 inside {[0:3]};
    
        //ptr.ccf_hash_adjustment_sku?

        //TODO bfarkash meanwhile the hash values are fixed
        ptr.ccf_hash_adjustment_h3_h4_11 == 3;
        ptr.ccf_hash_adjustment_h3_h4_10 == 1;
        ptr.ccf_hash_adjustment_h3_h4_01 == 2;
        ptr.ccf_hash_adjustment_h3_h4_00 == 0;
    
        ptr.ccf_hash_adjustment_sku          == UCC1;
        solve ptr.ccf_hash_adjustment_sku before ptr.ccf_cbb_id;
        (ptr.ccf_hash_adjustment_sku inside {XCC_HCC_LCC, S_DIMM_XCC_HCC_LCC}) -> ptr.ccf_cbb_id inside {0,1};
    }
    
    constraint rmid_const{
        soft ptr.ccf_rmid_equal_cbo_percent inside {[0:100]};
    }
    
`constraint_class_end


//--------------------------------------------
// Class:         ccf picker SoC constraints
// Description:   SoC constraints to override the defaults constraints.
//                These constraints should be applied in SoC level.
// Command line:  -test_constraints "ccf_picker_soc_constraints"
//--------------------------------------------

`constraint_class_begin(ccf_picker_soc_constraints, ccf_picker, ptr)
    constraint ccf_default_soc_const {
        soft ptr.ccf_vip_layering == CCF_BASE_LAYER;
        ptr.ccf_die == CCF_DIE_CBB_6C_SOC;
    }
`constraint_class_end
