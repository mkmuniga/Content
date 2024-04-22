class ccf_address_map_handler extends uvm_component;
    `uvm_component_utils(ccf_address_map_handler)

    ccf_resource_group group_res;
    string resource_inst = "";

    static idi_phyaddr_t dram_low_addr, dram_low_len, dram_high_addr, dram_high_len;
    static idi_phyaddr_t mmio_low_addr, mmio_low_len, mmio_high_addr, mmio_high_len;
    slu_sm_env sm;
    slu_sm_am_tagmap memmap;

    function new(string name = "ccf_address_map_handler", uvm_component parent = null);
        super.new(name, parent);
        `slu_assert($cast(sm, slu_sm_env::get_ptr()),("Unable to get handle to SM."))
        group_res = `GROUP(ccf);
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        memmap = sm.am.find_map("memmap");
        allocate_main_regions();
        allocate_preload();
        allocate_mmio();
        allocate_legacy();
        print_memory_map();
    endfunction

    virtual function void allocate_main_regions();
        longint mem_space_top = 2**(`CFGg.mem_map_picker.address_width);
        bit status;

        dram_low_addr = 0;
        dram_low_len = `CFGg.mem_map_picker.tolm_value;
        mmio_low_addr = `CFGg.mem_map_picker.tolm_value;
        mmio_low_len = `CFGg.mem_map_picker.boleg_value - `CFGg.mem_map_picker.tolm_value;

        dram_high_addr = `FOUR_G;
        dram_high_len = `CFGg.mem_map_picker.tohm_value-`FOUR_G;
        mmio_high_addr = `CFGg.mem_map_picker.mmio_h_base;
        mmio_high_len = `CFGg.mem_map_picker.mmio_h_limit-`CFGg.mem_map_picker.mmio_h_base;

        if(`CFGg.mem_map_picker.dram_low_en) begin
            status = memmap.add(.name("DRAM_LOW"), .addr(dram_low_addr), .len(dram_low_len));
            `slu_assert(status,("DRAM_LOW could not be added to MEM"));
        end
        if(`CFGg.mem_map_picker.mmio_low_en) begin
            status = memmap.add(.name("MMIO_LOW"), .addr(mmio_low_addr), .len(mmio_low_len));
            `slu_assert(status,("MMIO_LOW could not be added to MEM"));
        end
        if(`CFGg.mem_map_picker.legacy_en) begin
            status = memmap.add(.name("LEGACY"), .addr(`CFGg.mem_map_picker.boleg_value), .len(`CFGg.mem_map_picker.toleg_value - `CFGg.mem_map_picker.boleg_value));
            `slu_assert(status,("LEGACY could not be added to MEM"));
        end
        if(`CFGg.mem_map_picker.dram_high_en) begin
            status = memmap.add(.name("DRAM_HIGH"), .addr(dram_high_addr), .len(dram_high_len));
            `slu_assert(status,("DRAM_HIGH could not be added to MEM"));
        end
        if(`CFGg.mem_map_picker.mmcfgbar_en) begin
            status = memmap.add(.name("MMCFGBAR"), .addr(`CFGg.mem_map_picker.mmcfgbar_value), .len(`CFGg.mem_map_picker.mmio_h_base-`CFGg.mem_map_picker.mmcfgbar_value));
            `slu_assert(status,("MMCFGBAR could not be added to MEM"));
        end
        if(`CFGg.mem_map_picker.mmio_high_en) begin
            status = memmap.add(.name("MMIO_HIGH"), .addr(mmio_high_addr), .len(mmio_high_len));
            `slu_assert(status,("DRAM_LOW could not be added to MEM"));
        end
    endfunction

    function void allocate_preload();
        slu_sm_ag_result ag_result;
        int num_of_cbo = ccf_module_config::get_num_of_cbo()*NUM_OF_CCF_CLUSTERS;
        int dram_rand_preload_low_0_size      = `ONE_K*num_of_cbo;
        int dram_rand_preload_low_1_size      = 2*`ONE_K*num_of_cbo;
        int dram_rand_non_preload_low_0_size  = 2*`ONE_K*num_of_cbo;
        longint dram_rand_non_preload_low_1_size  = `ONE_M*3;

        int dram_rand_preload_high_0_size     = `ONE_K*num_of_cbo;
        int dram_rand_preload_high_1_size     = 2*`ONE_K*num_of_cbo;
        int dram_rand_non_preload_high_0_size = `ONE_K*64;
        longint dram_rand_non_preload_high_1_size = `ONE_M*256;

        int mmio_rand_preload_low_0_size      = `ONE_K*num_of_cbo/2;
        int mmio_rand_preload_low_1_size      = `ONE_K*num_of_cbo;
        int mmio_rand_non_preload_low_0_size  = `ONE_K*num_of_cbo;
        int mmio_rand_non_preload_low_1_size  = `ONE_M/2;

        int mmio_rand_preload_high_0_size     = `ONE_K*num_of_cbo/2;
        int mmio_rand_preload_high_1_size     = `ONE_K*num_of_cbo;
        int mmio_rand_non_preload_high_0_size = `ONE_K*num_of_cbo;
        longint mmio_rand_non_preload_high_1_size = `ONE_M;

        if (`CFGg.mem_map_picker.dram_low_en) begin
            sm.ag.allocate_mem(ag_result, "DRAM_LOW", .name("DRAM_RAND_NON_PRELOAD_LOW_1"), .length(dram_rand_non_preload_low_1_size), .alignment_mask(`ONE_M - 1));
            sm.ag.allocate_mem(ag_result, "DRAM_LOW", .name("DRAM_RAND_NON_PRELOAD_LOW_0"), .length(dram_rand_non_preload_low_0_size), .alignment_mask(`ONE_K - 1));
            sm.ag.allocate_mem(ag_result, "DRAM_LOW", .name("DRAM_RAND_PRELOAD_LOW_1"),     .length(dram_rand_preload_low_1_size),     .alignment_mask(`ONE_K - 1));
            sm.ag.allocate_mem(ag_result, "DRAM_LOW", .name("DRAM_RAND_PRELOAD_LOW_0"),     .length(dram_rand_preload_low_0_size),     .alignment_mask(`ONE_K - 1));
        end

//        sm.ag.allocate_mem(ag_result, "MMIO_LOW", .name("MMIO_RAND_NON_PRELOAD_LOW_1"), .length(mmio_rand_non_preload_low_1_size), .alignment_mask(`ONE_M - 1));
//        sm.ag.allocate_mem(ag_result, "MMIO_LOW", .name("MMIO_RAND_NON_PRELOAD_LOW_0"), .length(mmio_rand_non_preload_low_0_size), .alignment_mask(`ONE_K - 1));
//        sm.ag.allocate_mem(ag_result, "MMIO_LOW", .name("MMIO_RAND_PRELOAD_LOW_1"),     .length(mmio_rand_preload_low_1_size),     .alignment_mask(`ONE_K - 1));
//        sm.ag.allocate_mem(ag_result, "MMIO_LOW", .name("MMIO_RAND_PRELOAD_LOW_0"),     .length(mmio_rand_preload_low_0_size),     .alignment_mask(`ONE_K - 1));

        if (`CFGg.mem_map_picker.dram_high_en) begin
            sm.ag.allocate_mem(ag_result, "DRAM_HIGH", .name("DRAM_RAND_NON_PRELOAD_HIGH_1"), .length(dram_rand_non_preload_high_1_size), .alignment_mask(get_alignment_mask(dram_rand_non_preload_high_1_size)));
            sm.ag.allocate_mem(ag_result, "DRAM_HIGH", .name("DRAM_RAND_NON_PRELOAD_HIGH_0"), .length(dram_rand_non_preload_high_0_size), .alignment_mask(get_alignment_mask(dram_rand_non_preload_high_0_size)));
            sm.ag.allocate_mem(ag_result, "DRAM_HIGH", .name("DRAM_RAND_PRELOAD_HIGH_1"),     .length(dram_rand_preload_high_1_size),     .alignment_mask(get_alignment_mask(dram_rand_preload_high_1_size)));
            sm.ag.allocate_mem(ag_result, "DRAM_HIGH", .name("DRAM_RAND_PRELOAD_HIGH_0"),     .length(dram_rand_preload_high_0_size),     .alignment_mask(get_alignment_mask(dram_rand_preload_high_0_size)));
        end

//        sm.ag.allocate_mem(ag_result, "MMIO_HIGH", .name("MMIO_RAND_NON_PRELOAD_HIGH_1"), .length(mmio_rand_non_preload_high_1_size), .alignment_mask(get_alignment_mask(dram_rand_non_preload_high_1_size)));
//        sm.ag.allocate_mem(ag_result, "MMIO_HIGH", .name("MMIO_RAND_NON_PRELOAD_HIGH_0"), .length(mmio_rand_non_preload_high_0_size), .alignment_mask(get_alignment_mask(dram_rand_non_preload_high_0_size)));
//        sm.ag.allocate_mem(ag_result, "MMIO_HIGH", .name("MMIO_RAND_PRELOAD_HIGH_1"),     .length(mmio_rand_preload_high_1_size),     .alignment_mask(get_alignment_mask(dram_rand_preload_high_1_size)));
//        sm.ag.allocate_mem(ag_result, "MMIO_HIGH", .name("MMIO_RAND_PRELOAD_HIGH_0"),     .length(mmio_rand_preload_high_0_size),     .alignment_mask(get_alignment_mask(dram_rand_preload_high_0_size)));
    endfunction

    function void allocate_mmio();
        if(`CFGg.mem_map_picker.mmio_low_en) begin
            sm_allocate(.region_parent(CCF_types::MMIO_LOW), .region(CCF_types::MMIO_L_FUNC), .region_size(`MMIO_FUNC_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_l_cbbbar));
            sm_allocate(.region_parent(CCF_types::MMIO_LOW), .region(CCF_types::MMIO_L_RDT),  .region_size(`MMIO_RDT_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_l_cbbbar+`MMIO_FUNC_SIZE));
            sm_allocate(.region_parent(CCF_types::MMIO_LOW), .region(CCF_types::MMIO_L_MINISAF),  .region_size(`MMIO_MINISAF_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_l_cbbbar+`MMIO_FUNC_SIZE+`MMIO_RDT_SIZE));
            sm_allocate(.region_parent(CCF_types::MMIO_LOW), .region(CCF_types::MMIO_L_PMON),  .region_size(`MMIO_PMON_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_l_cbbbar+`MMIO_FUNC_SIZE+`MMIO_RDT_SIZE+`MMIO_MINISAF_SIZE));
        end
        
        if(`CFGg.mem_map_picker.mmio_high_en) begin
            sm_allocate(.region_parent(CCF_types::MMIO_HIGH), .region(CCF_types::MMIO_H_FUNC), .region_size(`MMIO_FUNC_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_h_cbbbar));
            sm_allocate(.region_parent(CCF_types::MMIO_HIGH), .region(CCF_types::MMIO_H_RDT),  .region_size(`MMIO_RDT_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_h_cbbbar+`MMIO_FUNC_SIZE));
            sm_allocate(.region_parent(CCF_types::MMIO_HIGH), .region(CCF_types::MMIO_H_MINISAF),  .region_size(`MMIO_MINISAF_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_h_cbbbar+`MMIO_FUNC_SIZE+`MMIO_RDT_SIZE));
            sm_allocate(.region_parent(CCF_types::MMIO_HIGH), .region(CCF_types::MMIO_H_PMON),  .region_size(`MMIO_PMON_SIZE), .low_addr(`CFGg.mem_map_picker.mmio_h_cbbbar+`MMIO_FUNC_SIZE+`MMIO_RDT_SIZE+`MMIO_MINISAF_SIZE));
        end
        
        allocate_mmio_sub_regions();
    endfunction
    
    function void allocate_mmio_sub_regions();
        if(`CFGg.mem_map_picker.mmio_low_en) begin
            allocate_mmio_func(.region_parent(CCF_types::MMIO_L_FUNC), .sub_region_list('{`MMIO_FUNC_SUB_REG(L, CCF_types::)}));
            allocate_mmio_rdt(.region_parent(CCF_types::MMIO_L_RDT), .sub_region_list('{`MMIO_RDT_SUB_REG(L, CCF_types::)}));
            allocate_mmio_minisaf(.region_parent(CCF_types::MMIO_L_MINISAF), .sub_region_list('{`MMIO_MINISAF_SUB_REG(L, CCF_types::)}));
            allocate_mmio_pmon(.region_parent(CCF_types::MMIO_L_PMON), .sub_region_list('{`MMIO_PMON_SUB_REG(L, CCF_types::)}));
        end
        if(`CFGg.mem_map_picker.mmio_high_en) begin
            allocate_mmio_func(.region_parent(CCF_types::MMIO_H_FUNC), .sub_region_list('{`MMIO_FUNC_SUB_REG(H, CCF_types::)}));
            allocate_mmio_rdt(.region_parent(CCF_types::MMIO_H_RDT), .sub_region_list('{`MMIO_RDT_SUB_REG(H, CCF_types::)}));
            allocate_mmio_minisaf(.region_parent(CCF_types::MMIO_H_MINISAF), .sub_region_list('{`MMIO_MINISAF_SUB_REG(H, CCF_types::)}));
            allocate_mmio_pmon(.region_parent(CCF_types::MMIO_H_PMON), .sub_region_list('{`MMIO_PMON_SUB_REG(H, CCF_types::)}));
        end
    endfunction
    
    function void allocate_mmio_func(CCF_types::ag_tags_type region_parent, CCF_types::ag_tags_q sub_region_list);
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[0]),  .high_offset('h4fff),  .low_offset(0));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[1]),  .high_offset('h53ff),  .low_offset('h5000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[2]),  .high_offset('h55ff),  .low_offset('h5400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[3]),  .high_offset('h57ff),  .low_offset('h5600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[4]),  .high_offset('h5fff),  .low_offset('h5800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[5]),  .high_offset('h67ff),  .low_offset('h6000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[6]),  .high_offset('h6bff),  .low_offset('h6800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[7]),  .high_offset('h8fff),  .low_offset('h6c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[8]),  .high_offset('h93ff),  .low_offset('h9000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[9]),  .high_offset('h97ff),  .low_offset('h9400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[10]), .high_offset('hffff),  .low_offset('h9800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[11]), .high_offset('h12fff), .low_offset('h10000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[12]), .high_offset('h15fff), .low_offset('h13000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[13]), .high_offset('h18fff), .low_offset('h16000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[14]), .high_offset('h19fff), .low_offset('h19000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[15]), .high_offset('h1ffff), .low_offset('h1a000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[16]), .high_offset('h27fff), .low_offset('h20000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[17]), .high_offset('h28fff), .low_offset('h28000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[18]), .high_offset('h2ffff), .low_offset('h29000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[19]), .high_offset('h37fff), .low_offset('h30000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[20]), .high_offset('h38fff), .low_offset('h38000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[21]), .high_offset('h3ffff), .low_offset('h39000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[22]), .high_offset('h42fff), .low_offset('h40000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[23]), .high_offset('h45fff), .low_offset('h43000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[24]), .high_offset('h48fff), .low_offset('h46000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[25]), .high_offset('h49fff), .low_offset('h49000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[26]), .high_offset('h4ffff), .low_offset('h4a000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[27]), .high_offset('h57fff), .low_offset('h50000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[28]), .high_offset('h58fff), .low_offset('h58000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[29]), .high_offset('h5ffff), .low_offset('h59000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[30]), .high_offset('h67fff), .low_offset('h60000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[31]), .high_offset('h68fff), .low_offset('h68000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[32]), .high_offset('h6ffff), .low_offset('h69000));
    endfunction
    
    function void allocate_mmio_rdt(CCF_types::ag_tags_type region_parent, CCF_types::ag_tags_q sub_region_list);
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[0]),  .high_offset('h7fff),  .low_offset(0));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[1]),  .high_offset('h8fff),  .low_offset('h8000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[2]),  .high_offset('h9fff),  .low_offset('h9000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[3]),  .high_offset('hafff),  .low_offset('ha000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[4]),  .high_offset('hbfff),  .low_offset('hb000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[5]),  .high_offset('hcfff),  .low_offset('hc000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[6]),  .high_offset('hffff),  .low_offset('hd000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[7]),  .high_offset('h101ff), .low_offset('h10000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[8]),  .high_offset('h103ff), .low_offset('h10200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[9]),  .high_offset('h105ff), .low_offset('h10400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[10]), .high_offset('h107ff), .low_offset('h10600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[11]), .high_offset('h109ff), .low_offset('h10800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[12]), .high_offset('h10bff), .low_offset('h10a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[13]), .high_offset('h10dff), .low_offset('h10c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[14]), .high_offset('h10fff), .low_offset('h10e00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[15]), .high_offset('h111ff), .low_offset('h11000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[16]), .high_offset('h113ff), .low_offset('h11200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[17]), .high_offset('h115ff), .low_offset('h11400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[18]), .high_offset('h117ff), .low_offset('h11600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[19]), .high_offset('h119ff), .low_offset('h11800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[20]), .high_offset('h11bff), .low_offset('h11a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[21]), .high_offset('h11dff), .low_offset('h11c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[22]), .high_offset('h11fff), .low_offset('h11e00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[23]), .high_offset('h121ff), .low_offset('h12000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[24]), .high_offset('h123ff), .low_offset('h12200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[25]), .high_offset('h125ff), .low_offset('h12400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[26]), .high_offset('h127ff), .low_offset('h12600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[27]), .high_offset('h129ff), .low_offset('h12800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[28]), .high_offset('h12bff), .low_offset('h12a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[29]), .high_offset('h12dff), .low_offset('h12c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[30]), .high_offset('h12fff), .low_offset('h12e00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[31]), .high_offset('h1ffff), .low_offset('h13000));
    endfunction
    
    function void allocate_mmio_minisaf(CCF_types::ag_tags_type region_parent, CCF_types::ag_tags_q sub_region_list);
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[0]),  .high_offset('hfff),  .low_offset(0));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[1]),  .high_offset('h1fff),  .low_offset('h1000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[2]),  .high_offset('h2fff),  .low_offset('h2000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[3]),  .high_offset('h3fff),  .low_offset('h3000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[4]),  .high_offset('h4fff),  .low_offset('h4000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[5]),  .high_offset('h5fff),  .low_offset('h5000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[6]),  .high_offset('h6fff),  .low_offset('h6000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[7]),  .high_offset('hffff),  .low_offset('h7000));
    endfunction
    
    function void allocate_mmio_pmon(CCF_types::ag_tags_type region_parent, CCF_types::ag_tags_q sub_region_list);
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[0]),  .high_offset('h1ff),  .low_offset(0));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[1]),  .high_offset('h3ff),  .low_offset('h200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[2]),  .high_offset('h5ff),  .low_offset('h400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[3]),  .high_offset('h7ff),  .low_offset('h600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[4]),  .high_offset('h9ff),  .low_offset('h800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[5]),  .high_offset('hbff),  .low_offset('ha00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[6]),  .high_offset('hdff),  .low_offset('hc00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[7]),  .high_offset('hfff),  .low_offset('he00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[8]),  .high_offset('h11ff), .low_offset('h1000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[9]),  .high_offset('h13ff), .low_offset('h1200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[10]), .high_offset('h4fff), .low_offset('h1400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[11]), .high_offset('h51ff), .low_offset('h5000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[12]), .high_offset('h53ff), .low_offset('h5200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[13]), .high_offset('h55ff), .low_offset('h5400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[14]), .high_offset('h57ff), .low_offset('h5600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[15]), .high_offset('h59ff), .low_offset('h5800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[16]), .high_offset('h5bff), .low_offset('h5a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[17]), .high_offset('h5dff), .low_offset('h5c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[18]), .high_offset('h5fff), .low_offset('h5e00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[19]), .high_offset('h61ff), .low_offset('h6000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[20]), .high_offset('h63ff), .low_offset('h6200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[21]), .high_offset('h65ff), .low_offset('h6400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[22]), .high_offset('h67ff), .low_offset('h6600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[23]), .high_offset('h69ff), .low_offset('h6800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[24]), .high_offset('h6bff), .low_offset('h6a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[25]), .high_offset('h6dff), .low_offset('h6c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[26]), .high_offset('h6fff), .low_offset('h6e00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[27]), .high_offset('h71ff), .low_offset('h7000));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[28]), .high_offset('h73ff), .low_offset('h7200));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[29]), .high_offset('h75ff), .low_offset('h7400));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[30]), .high_offset('h77ff), .low_offset('h7600));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[31]), .high_offset('h79ff), .low_offset('h7800));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[32]), .high_offset('h7bff), .low_offset('h7a00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[33]), .high_offset('h7dff), .low_offset('h7c00));
        sm_allocate_sub_region(.region_parent(region_parent), .region(sub_region_list[34]), .high_offset('h7fff), .low_offset('h7e00));
    endfunction
        
    function void allocate_legacy();
        if(`CFGg.mem_map_picker.legacy_en) begin
            slu_sm_addr_t next_base_addr = `CFGg.mem_map_picker.boleg_value;
            slu_sm_addr_t next_region_size = 104*`ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::Extended_Flash), .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = 2560*`ONE_K;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::No_EGo0),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = 512*`ONE_K;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::PSEG),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = `ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::CRAB_ABORT),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = `ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::IOAPIC), .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = `ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::ICH_LT),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = `ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::MSI),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = `ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::No_EGo1),  .region_size(next_region_size), .low_addr(next_base_addr));
            
            next_base_addr += next_region_size;
            next_region_size = 16*`ONE_M;
            sm_allocate(.region_parent(CCF_types::LEGACY), .region(CCF_types::Flash),  .region_size(next_region_size), .low_addr(next_base_addr));
        end
    endfunction

    function void sm_allocate(CCF_types::ag_range_name_type region_parent, CCF_types::ag_tags_type region, slu_sm_addr_t region_size, slu_sm_addr_t low_addr=-1);
        slu_sm_ag_result ag_result;
        slu_sm_ag_status_t status;
        slu_sm_addr_t alignment_mask = low_addr != -1 ? 'h7 : get_alignment_mask(region_size);

        status = sm.ag.allocate_mem(ag_result, region_parent.name(), .name(region.name()), .length(region_size), .alignment_mask(alignment_mask), .addr(low_addr));

        if(status != slu_sm_ag_result::slu_sm_ag_status[`SLU_SM_AG_OK])
            `uvm_error("SM_MEM_ALLOCATE", $sformatf("Failed to allocate %0s region in MEM space", region.name()))
    endfunction
    
    function void sm_allocate_sub_region(CCF_types::ag_tags_type region_parent, CCF_types::ag_tags_type region, slu_sm_addr_t high_offset, slu_sm_addr_t low_offset);
        slu_sm_ag_result ag_result = sm.get_sm_hash(region_parent.name());
        slu_sm_ag_status_t status;
        slu_sm_ag_result sub_ag_result;
        slu_sm_addr_t region_size = high_offset-low_offset+1;
        
        status = ag_result.allocate(sub_ag_result, .name(region.name()), .length(region_size), .addr(ag_result.addr + low_offset));
        if (status != SLA_TRUE)
            `uvm_error("SUB_RANGE_ALLOCATE",$psprintf("Failed to allocate sub region %0s in %0s region", region.name(), region_parent.name()))
    endfunction

    function slu_sm_addr_t get_alignment_mask(slu_sm_addr_t region_size);
        slu_sm_addr_t alignment_mask = 0;
        for(int i=0; i<`SLU_SM_NUM_ADDRESS_BITS; i++) begin
            if(region_size[i] == 1) begin
                alignment_mask[i] = 1;
                break;
            end
        end
        alignment_mask -= 1;
        return alignment_mask;
    endfunction

    function void print_memory_map();
        sm.mode = SLA_SM_FULL;
        memmap.print_tagmap();
    endfunction : print_memory_map
endclass
