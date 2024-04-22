



//////////////////////////////////////INFO//////////////////////////////////////////////
// base data which generates the rest: the straps inputs : ia_bigcore_mask, ia_atom_mask, disable_stuff, who_is_on_noc, who_is_on_ccf
//  
// please use / read only external utilities functions 
//
// terminology :
// val_idx - the running index of the ccp - similar to what was previously known as PID - tightly related to hw indexing of the ccp's
// location in mask /ccp mask index - the bit location on the ccp mask (ia_big_core_mask|ia_atom_mask)
// pcode_id -  based on 4 bits - assumes 16 bits on cluster - all io's that pcode reads work on 16 bits mask per cluster
// global fid - based on 5 bits - assumes 32 bits cluster 
//      logical fid - most pmsb/post reset phases xactions use logical FID -
//      phys    fid - before switch to logical - most wires transaction -   
//    
//  for registers FID's (from ccp or tie or sb - with use the FID which is given from onesource which is the GLOBAL FID and NOT the PCODE FID
//   for using masks or stuff that PCODE reads and interprets - we use the PCODE ID which assumes 16 bits per cluster - like IODIECONFIG for example
//PCODE_CFG.ADDR[7:0]: {1'b0, ClusterID[1:0], CCP_ID[4:0]}
//ADL: {1'b0, 2'b0, CCP_ID[4:0]}
//
//    CCP("global") PunitHW     Pcode ("PCU_CONFIG")
//LNC0 - 0            0           0
//LNC1 - 1            1           1
//LNC2 - 2            2           2
//LNC3 - 3            3           3
//SKT0 - 32           4           16
//
//9:8     7:3     2:0
//Cluster CCP     LPID
//
//
//[6:5] - [4:0]
//clstr module id 
//phase  mask: 
//00000000000000000000100000000000000000001010

            // Punit strap: die_config_ia_cores_topology: atom_ccp_mask[31:0], big_ia_ccp_mask[31:0] --> each one has 
//            [4]         [3:0]
//            clusterID   LogicalID_in_cluster

// example : 
//                22221111111111
//                321098765432109876543210
// bigcore mask : 001000110001111110111101
// atom mask :    110111000000000001000010
// disable mask : 000000100000000000000110

// 
//============== init_ccp_global_and_pcode_id_mask() ===============
// CCP_VAL_IDX(HW)  | MASK_IDX         | CLSTR_ID         | MODULE_ID(PHS)   | MODULE_ID(LOG)   | GLOBAL_ID (LOG)  | PCODE_ID (LOG)   | REG FID (GLOBAL) |         CCP TYPE 
// 0                | 0                | 0                | 0                | 0                | 0                | 0                | 00000000         | BIG_CCP
// 1                | 1                | 0                | 1                | 11               | 11               | 11               | 00000058         | ATOM_CCP
// 2                | 2                | 0                | 2                | 12               | 12               | 12               | 00000060         | BIG_CCP
// 3                | 3                | 0                | 3                | 1                | 1                | 1                | 00000008         | BIG_CCP
// 4                | 4                | 0                | 4                | 2                | 2                | 2                | 00000010         | BIG_CCP
// 5                | 5                | 0                | 5                | 3                | 3                | 3                | 00000018         | BIG_CCP
// 6                | 6                | 0                | 6                | 4                | 4                | 4                | 00000020         | ATOM_CCP
// 7                | 7                | 0                | 7                | 5                | 5                | 5                | 00000028         | BIG_CCP
// 8                | 8                | 0                | 8                | 6                | 6                | 6                | 00000030         | BIG_CCP
// 9                | 9                | 0                | 9                | 7                | 7                | 7                | 00000038         | BIG_CCP
// 10               | 10               | 0                | 10               | 8                | 8                | 8                | 00000040         | BIG_CCP
// 11               | 11               | 0                | 11               | 9                | 9                | 9                | 00000048         | BIG_CCP
// 12               | 12               | 0                | 12               | 10               | 10               | 10               | 00000050         | BIG_CCP
// 13               | 16               | 1                | 0                | 0                | 32               | 16               | 00000100         | BIG_CCP
// 14               | 17               | 1                | 1                | 7                | 39               | 23               | 00000138         | BIG_CCP
// 15               | 18               | 1                | 2                | 1                | 33               | 17               | 00000108         | ATOM_CCP
// 16               | 19               | 1                | 3                | 2                | 34               | 18               | 00000110         | ATOM_CCP
// 17               | 20               | 1                | 4                | 3                | 35               | 19               | 00000118         | ATOM_CCP
// 18               | 21               | 1                | 5                | 4                | 36               | 20               | 00000120         | BIG_CCP
// 19               | 22               | 1                | 6                | 5                | 37               | 21               | 00000128         | ATOM_CCP
// 20               | 23               | 1                | 7                | 6                | 38               | 22               | 00000130         | ATOM_CCP
// 21               | 14               | 0                | 14               | 14               | 14               | 14               | 00000070         | MEDIA_CCP
// 22               | 15               | 0                | 15               | 15               | 15               | 15               | 00000078         | GT_CCP
class ccp_common_cfg #(STRAP_MASK_SIZE=32,MAX_CCPS_PER_CLSTR=32,NUM_OF_CLUSTERS=1) extends uvm_object;

    // ccp_common_cfg functions header
    typedef logic[63:0] logic_64;
    logic[STRAP_MASK_SIZE-1:0] punit_ia_big_ccp_mask;
    logic[STRAP_MASK_SIZE:0] punit_ia_atom_ccp_mask;
    logic[STRAP_MASK_SIZE:0] punit_ia_ccp_on_ccf_mask;
    logic[STRAP_MASK_SIZE:0] punit_ia_ccp_on_noc_mask;
    logic[STRAP_MASK_SIZE:0] punit_enabled_ia_ccp_mask;
    logic[STRAP_MASK_SIZE-1:0] all_ia_ccp_mask; // [31:0] in LNL as it is assumed up to 32 bits
    int fuse_cluster0_llc_slice_ia_ccp_dis;
    //int fuse_cluster1_llc_slice_ia_ccp_dis;
    int num_of_atoms_per_module;
    int max_num_of_ccps_per_clstr = MAX_CCPS_PER_CLSTR;
    int fuse_all_llc_slice_ia_ccp_dis;
    int punit_ia_ccp_num;
    int punit_gt_id;
    int punit_media_id;
    int num_of_cores;
    int num_of_threads;
    bit sbft_en;
    bit fuse_ht_dis = 0;
    bit punit_strap_set_1_ht_dis_by_strap = 0;
    bit[$clog2(MAX_CCPS_PER_CLSTR)-1:0] phys2log_map_per_cluster[][]; // [3:0] in LNL as it is assumed 16 ccps in cluster should be log somethign 
    bit[$clog2(MAX_CCPS_PER_CLSTR)-1:0] log2phys_map_per_cluster[][]; // [3:0] in LNL as it is assumed 16 ccps in cluster
    int cte2rtl_core_fid_compressor[int];
    logic[MAX_CCPS_PER_CLSTR*NUM_OF_CLUSTERS*$clog2(MAX_CCPS_PER_CLSTR)-1:0] phys2log_map_per_cluster_packed[];
    int val_idx_2_mask_idx[];
    int mask_idx_2_val_idx[];
    

    protected int_queue ccp_global_id_by_val_idx;
    protected int_queue ccp_pcode_id_by_val_idx;
    protected int_queue ccp_global_id_by_mask_idx;
    protected int_queue ccp_pcode_id_by_mask_idx;
    protected int_dynamic_array hash_ccp_mask_idx_to_ccp_gpsb_pid;


    `uvm_object_utils(ccp_common_cfg);

    //*******************************************************/
    function new (string name = "ccp_common_cfg");
        super.new(name);
    endfunction : new
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
////////////BASIC INITIALIZATION FUNCTIONS  (INTERNAL USE)///////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
     //*******************************************************/
    function void init();
        logic_64 ccp_res;
        int_queue init_ccp_res;
        all_ia_ccp_mask = punit_ia_big_ccp_mask|punit_ia_atom_ccp_mask;
        punit_ia_ccp_on_noc_mask = all_ia_ccp_mask ^ punit_ia_ccp_on_ccf_mask;
        //fuse_all_llc_slice_ia_ccp_dis = fuse_cluster0_llc_slice_ia_ccp_dis | (fuse_cluster1_llc_slice_ia_ccp_dis<<MAX_CCPS_PER_CLSTR);
        fuse_all_llc_slice_ia_ccp_dis = fuse_cluster0_llc_slice_ia_ccp_dis;
//         $display($sformatf("-DBG- REMOVEME TRALALALA INTERNAL clstr 0 fuse disabled is : %0h and all disabled  is : %0h",fuse_cluster0_llc_slice_ia_ccp_dis,fuse_all_llc_slice_ia_ccp_dis));
        punit_enabled_ia_ccp_mask = all_ia_ccp_mask &  (~fuse_all_llc_slice_ia_ccp_dis);
        phys2log_map_per_cluster = new[NUM_OF_CLUSTERS];
        log2phys_map_per_cluster = new[NUM_OF_CLUSTERS];
        foreach (phys2log_map_per_cluster[clstr]) begin
            phys2log_map_per_cluster[clstr] = new[max_num_of_ccps_per_clstr];
            log2phys_map_per_cluster[clstr] = new[max_num_of_ccps_per_clstr];
        end 
        phys2log_map_per_cluster_packed = new[NUM_OF_CLUSTERS];
        val_idx_2_mask_idx = new[STRAP_MASK_SIZE];
        mask_idx_2_val_idx = new[STRAP_MASK_SIZE];
 
        //basic_initialization functions:
        ccp_res=get_ccp_phys2log_mapping_per_cluster(0);
        init_val2mask_array();
        init_ccp_res=init_ccp_global_and_pcode_id_mask();
        init_rtl_compressed_fid();

        uvm_config_db #(int_dynamic_array)::get(null, "*", "hash_ccp_mask_idx_to_ccp_gpsb_pid", hash_ccp_mask_idx_to_ccp_gpsb_pid);
    endfunction : init



    ///////////////////////////init_rtl_compressed_fid/////////////////////////////
    // 
    //
    //
    /////////////////////////////////////////////////////////////////////////////////////
    function void init_rtl_compressed_fid();
        int compressed_core_counter = 0;
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin
                int logic_location_on_mask = get_logical_idx_on_mask_from_mask_idx(location_on_mask);
                int fid = get_fid_from_logical_mask_idx(logic_location_on_mask);
                if (get_ccp_type_by_mask_index(location_on_mask) == BIG_CCP) begin
                    cte2rtl_core_fid_compressor[fid] = compressed_core_counter;
                    compressed_core_counter++;
                end else begin
                    for (int core_idx = 1; core_idx<=4;core_idx++) begin 
                        int logic_location_on_mask = get_logical_idx_on_mask_from_mask_idx(location_on_mask);
                        fid = get_fid_from_logical_mask_idx(logic_location_on_mask,core_idx);
                        cte2rtl_core_fid_compressor[fid] = compressed_core_counter;
                        compressed_core_counter++;
                    end
                end 
            end
        end 
        $display($sformatf("============== fid2rtlfid ia core  hash ===============\n %0p",cte2rtl_core_fid_compressor));
//        $display($sformatf("-DBG- cte2rtl core fid mapping  = %0p",cte2rtl_core_fid_compressor));
    endfunction : init_rtl_compressed_fid

    ///////////////////////////get_ccp_phys2log_mapping_per_cluster/////////////////////////////
    // map logic to physical per cluster
    // will return the mapping io register per requested cluster
    // but also initializes the mapping vector
    /////////////////////////////////////////////////////////////////////////////////////
    function logic_64 get_ccp_phys2log_mapping_per_cluster(int cluster);
        logic[3:0] curr_index[] = new[NUM_OF_CLUSTERS];
        int num_of_enabled_ccps_per_clstr[];
        int indx;
        num_of_enabled_ccps_per_clstr = new[NUM_OF_CLUSTERS];
        foreach(curr_index[clstr]) begin
            num_of_enabled_ccps_per_clstr[clstr] = count_enabled_ccps_per_clstr(clstr);
            curr_index[clstr] = 0;
        end

//        if (phys2log_map_per_cluster[cluster]) begin
//            return phys2log_map_per_cluster_packed[cluster];
//        end 
        
//go over all the enabled ccps and index them: 
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            int clstr = get_clstr_from_mask_idx(location_on_mask);
            if ((all_ia_ccp_mask[location_on_mask]) &&  (! is_ccp_slice_disabled(location_on_mask))) begin 
                int location_on_mask_per_cluster = location_on_mask - (clstr * max_num_of_ccps_per_clstr);
                phys2log_map_per_cluster[clstr][location_on_mask_per_cluster] = curr_index[clstr];
                log2phys_map_per_cluster[clstr][curr_index[clstr]] = location_on_mask_per_cluster;
                curr_index[clstr]++;
                if (sbft_en == 1) begin
                    phys2log_map_per_cluster[clstr][location_on_mask_per_cluster] = 0;
                    log2phys_map_per_cluster[clstr][0] = location_on_mask_per_cluster;
                end
            end
        end
// now go over all the slice disabled and index them 
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            int clstr = get_clstr_from_mask_idx(location_on_mask);
            if ((all_ia_ccp_mask[location_on_mask]) &&  ( is_ccp_slice_disabled(location_on_mask))) begin 
                int location_on_mask_per_cluster = location_on_mask - (clstr * max_num_of_ccps_per_clstr);
                phys2log_map_per_cluster[clstr][location_on_mask_per_cluster] = curr_index[clstr];
                log2phys_map_per_cluster[clstr][curr_index[clstr]] = location_on_mask_per_cluster;
                curr_index[clstr]++;
            end
        end

//        $display($sformatf("-DBG- phys2log_map_per_cluster = %0p",phys2log_map_per_cluster));

//printouts : 
        $display($sformatf("============== get_ccp_phys2log_mapping_per_cluster() ==============="));
        $display($sformatf("%-16s | %-16s | %-16s ", "CLSTR ID","MODULE_ID(PHYS)","MODULE_ID(LOG)"));            
        foreach (phys2log_map_per_cluster[clstr]) begin
            //foreach (phys2log_map_per_cluster[clstr][indx]) begin
            for( indx=0; indx <phys2log_map_per_cluster[clstr].size();indx++) begin
                $display($sformatf("%-14h | %-14h  | %-14h ", clstr,indx,phys2log_map_per_cluster[clstr][indx]));            
            end
        end 
        $display($sformatf("============== get_ccp_log2phys_mapping_per_cluster() ==============="));
        $display($sformatf("%-16s | %-16s | %-16s ", "CLSTR ID","MODULE_ID(PHYS)","MODULE_ID(LOG)"));            
        foreach (log2phys_map_per_cluster[clstr]) begin
            for( indx=0; indx <log2phys_map_per_cluster[clstr].size();indx++) begin
                $display($sformatf("%-14h | %-14h  | %-14h ", clstr,indx,log2phys_map_per_cluster[clstr][indx]));            
            end
        end 

        $display($sformatf("============== LOGICAL_ID_MAPPING_CLUSTER_X() ==============="));
        foreach (phys2log_map_per_cluster_packed[clstr]) begin
            phys2log_map_per_cluster_packed[clstr] = {<<4{phys2log_map_per_cluster[clstr]}};
            $display($sformatf("for cluster %0d: the 4 bit packing of the array is : %0b (%0h)", clstr,phys2log_map_per_cluster_packed[clstr],phys2log_map_per_cluster_packed[clstr]));            
            end

        return phys2log_map_per_cluster_packed[cluster];
    endfunction : get_ccp_phys2log_mapping_per_cluster


    ///////////////////////////init_ccp_global_and_pcode_id_mask/////////////////////////////
    // creating a hash of global fid where the key is the val-index ( running indexing of the ccps)
    // will return the mapping io register per requested cluster
    // but also initializes the mapping vector
    /////////////////////////////////////////////////////////////////////////////////////
    function int_queue init_ccp_global_and_pcode_id_mask();
        int Logical_counter = 0 ;
        if (ccp_global_id_by_val_idx.size() == 0) begin 
            int log_counter_per_clstr[];
            int disabled_ccps_counter_per_clstr[];
            int num_of_enabled_ccps_per_clstr[];
            int ccp_val_idx = 0;
            log_counter_per_clstr = new[NUM_OF_CLUSTERS];
            disabled_ccps_counter_per_clstr = new[NUM_OF_CLUSTERS];
            num_of_enabled_ccps_per_clstr = new[NUM_OF_CLUSTERS];

            foreach (log_counter_per_clstr[j]) begin
                log_counter_per_clstr[j] = 0;
                disabled_ccps_counter_per_clstr[j] = 0;
                num_of_enabled_ccps_per_clstr[j] = count_enabled_ccps_per_clstr(j);
            end

            for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
                logic[1:0] clstr_id;
                logic[4:0] ccp_id;
                logic[3:0] pcode_ccp_id;
                if (all_ia_ccp_mask[location_on_mask]) begin  
                    ccp_vc_env_pkg::ccp_type_t ccp_type = get_ccp_type_by_mask_index(location_on_mask);
                    clstr_id = get_clstr_from_mask_idx(location_on_mask);
                    if (! is_ccp_slice_disabled(location_on_mask)) begin
                        ccp_id = log_counter_per_clstr[clstr_id];
                        log_counter_per_clstr[clstr_id]++;
                    end else if (is_ccp_slice_disabled(location_on_mask)) begin
                        ccp_id = disabled_ccps_counter_per_clstr[clstr_id] + num_of_enabled_ccps_per_clstr[clstr_id]; 
                        disabled_ccps_counter_per_clstr[clstr_id]++;
                    end
                    pcode_ccp_id = ccp_id;
                    ccp_global_id_by_val_idx[ccp_val_idx] = {clstr_id,ccp_id};
                    ccp_global_id_by_mask_idx[location_on_mask] = {clstr_id,ccp_id};
                    ccp_pcode_id_by_val_idx[ccp_val_idx] = {clstr_id,pcode_ccp_id};
                    ccp_pcode_id_by_mask_idx[location_on_mask] = {clstr_id,pcode_ccp_id};
                    ccp_val_idx++;
                end

                if (sbft_en == 1) begin
                    ccp_global_id_by_val_idx[location_on_mask] = 0;
                    ccp_global_id_by_mask_idx[location_on_mask] = {clstr_id,5'h0} ;
                    ccp_pcode_id_by_val_idx[ccp_val_idx] = {clstr_id,5'h0};
                    ccp_pcode_id_by_mask_idx[location_on_mask] = {clstr_id,5'h0};
                end
            end
        //set GT logical id 
            ccp_global_id_by_val_idx[ccp_val_idx] = punit_media_id;
            ccp_global_id_by_val_idx[ccp_val_idx+1] = punit_gt_id ;            
            ccp_global_id_by_mask_idx[punit_media_id] = punit_media_id;
            ccp_global_id_by_mask_idx[punit_gt_id] = punit_gt_id ;            
            ccp_pcode_id_by_val_idx[ccp_val_idx] = punit_media_id;
            ccp_pcode_id_by_val_idx[ccp_val_idx+1] = punit_gt_id ;            
            ccp_pcode_id_by_mask_idx[punit_media_id] = punit_media_id;
            ccp_pcode_id_by_mask_idx[punit_gt_id] = punit_gt_id ;            
        end

//printouts:

        $display($sformatf("============== ia big mask(io die config) ===============\n %0b",punit_ia_big_ccp_mask));
        $display($sformatf("============== ia atom mask(io die config) ===============\n %0b",punit_ia_atom_ccp_mask));
        $display($sformatf("============== ia slice disable mask(io llc something) ===============\n %0b",fuse_all_llc_slice_ia_ccp_dis));
        $display($sformatf("============== init_ccp_global_and_pcode_id_mask() ==============="));
        $display($sformatf(" %-16s | %-16s | %-16s | %-16s | %-16s | %-16s | %-16s | %-16s | %16s ", "CCP_VAL_IDX(HW)","MASK_IDX","CLSTR_ID","MODULE_ID(PHS)","MODULE_ID(LOG)","GLOBAL_ID (LOG)","PCODE_ID (LOG)", "REG FID (GLOBAL)", "CCP TYPE"));            
        foreach (ccp_global_id_by_val_idx[ccp_val_idx]) begin
            int location_on_mask = get_ccp_mask_idx_from_val_idx(ccp_val_idx);
            int clstr_id = get_clstr_from_mask_idx(location_on_mask);
            int phys_id_per_clstr = get_phys_id_per_clstr_from_location_on_mask(location_on_mask);
            int log_id_per_clstr = get_logical_id_per_clstr_from_phys_id(phys_id_per_clstr,clstr_id);
            int fid = get_fid_from_mask_idx(location_on_mask);
            ccp_vc_env_pkg::ccp_type_t ccp_type = get_ccp_type_by_mask_index(location_on_mask);
            $display($sformatf(" %-16d | %-16d | %-16d | %-16d | %-16d | %-16d | %-16d | %-16d | %s", ccp_val_idx,location_on_mask,clstr_id ,phys_id_per_clstr,log_id_per_clstr,ccp_global_id_by_val_idx[ccp_val_idx],ccp_pcode_id_by_val_idx[ccp_val_idx],fid,ccp_type.name()));                                                              
        end
        $display($sformatf("============== init_ccp_global_and_pcode_id_mask() ===============\n"));            
        return ccp_global_id_by_val_idx;
    endfunction
    ///////////////////////////init val2mask array and vice versa/////////////////////////////
    // creating an array that maps between mask index (on ia_ccp_all mask) and the val index  
    // also creating the other direction 
    /////////////////////////////////////////////////////////////////////////////////////

    function void init_val2mask_array();
        int  mask_idx;
        int local_val_idx = 0;
            for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
                if ((all_ia_ccp_mask[location_on_mask])) begin 
                    val_idx_2_mask_idx[local_val_idx] = location_on_mask;
                    mask_idx_2_val_idx[location_on_mask] = local_val_idx;
                    local_val_idx++;
        end
            end
        val_idx_2_mask_idx[$countones(all_ia_ccp_mask)] = punit_media_id;
        val_idx_2_mask_idx[$countones(all_ia_ccp_mask)+1] = punit_gt_id;
        mask_idx_2_val_idx[punit_media_id] = $countones(all_ia_ccp_mask);
        mask_idx_2_val_idx[punit_gt_id] = $countones(all_ia_ccp_mask) + 1;
    endfunction : init_val2mask_array
    
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
///////////////////////////BASIC UTILITIES (EXTERNAL USE)////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
    function int get_num_of_cores();
        if (num_of_cores==0) begin
            int_queue val_idx_list = get_val_index_list_of_any_ia_ccps();
            foreach (val_idx_list[list_idx]) begin
                int val_idx = val_idx_list[list_idx];
                ccp_vc_env_pkg::ccp_type_t ccp_type = get_ccp_type_by_val_index(val_idx);
                if (ccp_type == BIG_CCP) begin
                    num_of_cores++;
                end else begin
                    num_of_cores+=4;
                end
            end
        end 
        return num_of_cores; 
    endfunction
    
    function int get_num_of_ia_ccps();
//        $display("-DBG- num of ccps : %0d ",punit_ia_ccp_num);
        return punit_ia_ccp_num; 
    endfunction

    function int get_num_of_clusters();
        int num_of_clusters = NUM_OF_CLUSTERS;
        return num_of_clusters; 
    endfunction : get_num_of_clusters

    function ccp_vc_env_pkg::ccp_cluster_t get_random_cluster();
        ccp_vc_env_pkg::ccp_cluster_t cluster;
        std::randomize(cluster);
        return cluster;
    endfunction : get_random_cluster

    function int get_ccp_gpsb_portid_from_ccp_index_on_mask(int ccp_idx_on_mask);
        return hash_ccp_mask_idx_to_ccp_gpsb_pid[ccp_idx_on_mask];        
    endfunction : get_ccp_gpsb_portid_from_ccp_index_on_mask

    function int get_ccp_index_on_mask_from_ccp_gpsb_portid(int ccp_gpsb_pid);
        int my_indx[$] = hash_ccp_mask_idx_to_ccp_gpsb_pid.find_first_index(x) with (x == ccp_gpsb_pid);
        return my_indx[0];
    endfunction : get_ccp_index_on_mask_from_ccp_gpsb_portid

/////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////FIDS/////////////////////////////////////////////    
/////////////////////////////////////////////////////////////////////////////////////

    ///////////////////get_fid*//////////////////////////////////////////////////////
    //these functions return the fid (for sideband writes) 
    // clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]
    // this is FID the way that "CCP" see's it (5 bit module id) 
    ////////////////////////////////////////////////////////////////////////////////
    function int_queue get_all_lpids_from_mask_idx(int mask_idx);
        ccp_vc_env_pkg::ccp_type_t m_type = get_ccp_type_by_mask_index(mask_idx);
        if (m_type == ATOM_CCP) return {3,2,1,0}; //FIXME - ydror2 - beautify - 
        return {0}; 
    endfunction : get_all_lpids_from_mask_idx




    ///////////////////any_ia_ccps*//////////////////////////////////////////////////////
    //
    //
    //
    ////////////////////////////////////////////////////////////////////////////////
    function bit[7:0] get_compressed_core_fid_from_fid(logic[9:0] fid);
        if (!(cte2rtl_core_fid_compressor.exists(fid))) begin
            `uvm_error(get_name(), $sformatf("cte2rtl does not contain the cte fid key %0d, why do you expect one?", fid))
        end
        return cte2rtl_core_fid_compressor[fid];
    endfunction


    ///////////////////get_fid*//////////////////////////////////////////////////////
    //these functions return the fid (for sideband writes) 
    // clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]
    // this is FID the way that "CCP" see's it (5 bit module id) 
    ////////////////////////////////////////////////////////////////////////////////
    function bit[9:0] get_fid(int ccp_lid, int domain_id_or_lpid,logic[1:0] clstr_id = 0);
        return {clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]};
    endfunction

    function bit[9:0] get_fid_from_mask_idx(int mask_idx);
        logic[1:0] clstr_id = get_clstr_from_mask_idx(mask_idx);
        int domain_id_or_lpid = 0;
        int ccp_lid = get_logical_id_per_clstr_from_mask_idx(mask_idx);
//        $display("-DBG- got fid %0h from mask idx %0d",{clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]},mask_idx);
        return {clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]};
    endfunction : get_fid_from_mask_idx

    function bit[9:0] get_fid_from_mask_idx_and_lpid(int mask_idx,int lpid_idx);
        logic[1:0] clstr_id = get_clstr_from_mask_idx(mask_idx);
        int domain_id_or_lpid = lpid_idx;
        int ccp_lid = get_logical_id_per_clstr_from_mask_idx(mask_idx);
        bit[9:0] fid = {clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]};
//        $display("-DBG- got fid %0h from mask idx %0d - clstr - %0d, lpid idx %0d",fid,mask_idx,clstr_id,lpid_idx);

        return fid;
    endfunction : get_fid_from_mask_idx_and_lpid

    function bit[9:0] get_fid_from_val_idx_and_lpid(int val_idx,int lpid_idx);
        int mask_idx        = get_ccp_mask_idx_from_val_idx(val_idx);
        bit[9:0] fid = get_fid_from_mask_idx_and_lpid(mask_idx,lpid_idx);
//        $display("-DBG- got fid %0h from val idx %0d and lpid_idx %0d",fid,val_idx,lpid_idx);
        return fid;
    endfunction : get_fid_from_val_idx_and_lpid


    function bit[9:0] get_fid_from_val_idx(int val_idx);
        int mask_idx = get_ccp_mask_idx_from_val_idx(val_idx);
        return get_fid_from_mask_idx(mask_idx);
    endfunction : get_fid_from_val_idx

    function bit[9:0] get_fid_from_logical_mask_idx(int ccp_lid_mask_idx ,int domain_id_or_lpid = 0);
        logic[1:0] clstr_id = get_clstr_from_mask_idx(ccp_lid_mask_idx);
        int ccp_lid = ccp_lid_mask_idx%MAX_CCPS_PER_CLSTR;
//        $display("-DBG- got fid %0h from mask idx %0d",{clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]},mask_idx);
        return {clstr_id[1:0],ccp_lid[4:0], domain_id_or_lpid[2:0]};
    endfunction : get_fid_from_logical_mask_idx


    ///////////////////get_all_ia_core_fid_list//////////////////////////////////
    //used mainly in env for changing hdl paths of core fid regs
    ////////////////////////////////////////////////////////////////////////////////
    function int_queue get_all_ia_core_fid_list();
        int_queue fid_list = {};
        int_queue val_idx_list = get_val_index_list_of_any_ia_ccps();
        foreach (val_idx_list[list_idx]) begin
            int val_idx = val_idx_list[list_idx];
            ccp_vc_env_pkg::ccp_type_t ccp_type = get_ccp_type_by_val_index(val_idx);
            if (ccp_type == BIG_CCP) begin
                fid_list.push_back(get_fid_from_val_idx(val_idx));
            end else begin
                for (int i = 1;i<=4;i++) begin
                    fid_list.push_back(get_fid_from_val_idx_and_lpid(val_idx,i));
                end
            end
        end 
        $display("-DBG- returning fid list for cores: %0p",fid_list);
        return fid_list;
    endfunction : get_all_ia_core_fid_list
    ///////////////////get_ia_core_reg_index_from_fid//////////////////////////////////
    //since the crif (cte) represents all ia-core scoped registers as having 4 cores + ccp - we sometimes need to backwards engineer which is the actual serial index
    ////////////////////////////////////////////////////////////////////////////////
    function int get_ia_core_reg_index_from_fid(int req_fid);
        int serial_idx = 0;
        int_queue logical_index_list = get_mask_index_list_of_any_ia_ccps();
        foreach (logical_index_list[list_idx]) begin
            int logic_mask_idx = logical_index_list[list_idx];
            for (int i = 0;i<=4;i++) begin
                int fid = get_fid_from_logical_mask_idx(logic_mask_idx,i);
                if (fid == req_fid) begin
//                    $display("-DBG- returning serial num %0d  for fid: %0d",serial_idx,req_fid);
                    return serial_idx;
                end
                serial_idx++;
            end
        end 
        `uvm_error(get_name(), $sformatf("could not find an index matching for fid %0h .. please check relevant uvm_reg_block file ", req_fid))
        $stacktrace;
        return 0;
    endfunction : get_ia_core_reg_index_from_fid

    ///////////////////get_ia_core_val_idx_from_ccp_val_and_lp_idx//////////////////////////////////
    //since the crif (cte) represents all ia-core scoped registers as having 4 cores + ccp - we sometimes need to backwards engineer which is the actual serial index
    //FIXME -  need to create a constant associative array in order to  save time and only fill it up the first  time 
    ////////////////////////////////////////////////////////////////////////////////
    function int get_ia_core_val_idx_from_ccp_val_and_lp_idx(int ccp_val_idx,int lp_idx);
        int_queue val_idx_list = get_val_index_list_of_any_ia_ccps();
        int running_idx=0;
        foreach (val_idx_list[list_idx]) begin
            int val_idx = val_idx_list[list_idx];
            ccp_vc_env_pkg::ccp_type_t ccp_type = get_ccp_type_by_val_index(val_idx);
            if (val_idx == ccp_val_idx) 
            begin
//                $display("-DBG- returning core_ia_val for val idx %0h, and lp %0h : %0h",ccp_val_idx,lp_idx,running_idx+lp_idx);
                return running_idx+lp_idx; 
            end 
            if (ccp_type == BIG_CCP) begin
                running_idx++;
            end else begin
                for (int i = 1;i<=4;i++) begin
                    running_idx++;
                end
            end
        end 
        `uvm_error(get_name(), $sformatf("couldnt find ccp_val idx of %0d", ccp_val_idx))
        return running_idx;
    endfunction : get_ia_core_val_idx_from_ccp_val_and_lp_idx 

    ///////////////////get_ia_core_logic_idx_from_ccp_val_and_lp_idx//////////////////////////////////
    //since the crif (cte) represents all ia-core scoped registers as having 4 cores + ccp - we sometimes need to backwards engineer which is the actual serial index
    //FIXME -  need to create a constant associative array in order to  save time and only fill it up the first  time 
    ////////////////////////////////////////////////////////////////////////////////
    function int get_ia_core_logic_idx_from_ccp_val_and_lp_idx(int ccp_val_idx,int lp_idx);
        int_queue val_idx_list = get_val_index_list_of_any_ia_ccps();
        int running_idx=0;
//FIXME - for runtime :   //if (core_logic_array.size()!=0) return core_logic_array[get_core_running_idx_by_val_idx_and_lp_idx()]
        for (int clstr_idx = 0; clstr_idx<NUM_OF_CLUSTERS ;clstr_idx++) begin
                // first for loop to count non-disbaled 
                for (int location_on_cluster = 0; location_on_cluster < MAX_CCPS_PER_CLSTR;location_on_cluster++) begin
                    int location_on_mask = location_on_cluster + clstr_idx*MAX_CCPS_PER_CLSTR; 
                    // physical core exists - count it / return 
                    if (all_ia_ccp_mask[location_on_mask]) begin 
                            int val_idx = get_ccp_val_idx_from_mask_idx(location_on_mask);
                            //if it is the requested ccp - returm
                            if (val_idx == ccp_val_idx) begin
                //              $display("-DBG- returning core_ia_val for val idx %0h, and lp %0h : %0h",ccp_val_idx,lp_idx,running_idx+lp_idx);
                                return running_idx+lp_idx; 
                            end 
                            //if it is not the requested - count it ...
                            if ((! is_ccp_slice_disabled(location_on_mask))) begin 
                                int core_idx[$] = get_all_lpids_from_mask_idx(location_on_mask);
                                foreach (core_idx[i]) begin // FIXME - ydror2 - 13.06.22 - need to add core disable:
                                     running_idx += 1;
                                end
                            end
                    end
                end
                //second for loop to count disabled
                for (int location_on_cluster = 0; location_on_cluster < MAX_CCPS_PER_CLSTR;location_on_cluster++) begin
                    int location_on_mask = location_on_cluster + clstr_idx*MAX_CCPS_PER_CLSTR; 
                    // physical core exists - count it / return 
                    if (all_ia_ccp_mask[location_on_mask]) begin 
                            int val_idx = get_ccp_val_idx_from_mask_idx(location_on_mask);
                            if (val_idx == ccp_val_idx) begin
                //              $display("-DBG- returning core_ia_val for val idx %0h, and lp %0h : %0h",ccp_val_idx,lp_idx,running_idx+lp_idx);
                                return running_idx+lp_idx; 
                            end 
                            //if it is not the requested - count it  if it is disabled...
                            if ((is_ccp_slice_disabled(location_on_mask))) begin // FIXME - ydror2 - 13.06.22 - need to add per - core + fuse disbale
                                int core_idx[$] = get_all_lpids_from_mask_idx(location_on_mask);
                                foreach (core_idx[i]) begin // FIXME - ydror2 - 13.06.22 - need to add core disable:
                                     running_idx += 1;
                                end
                            end
                    end
                end

        end 
   //add enumerating for disabled per cluster 
        `uvm_error(get_name(), $sformatf("couldnt find ccp_val idx of %0d", ccp_val_idx))
        return running_idx;
    endfunction : get_ia_core_logic_idx_from_ccp_val_and_lp_idx 



    ///////////////////get_ccp_val_index_from_fid_and_bar//////////////////////////////////
    //undesrtanding which ccp sent a certain message
    ////////////////////////////////////////////////////////////////////////////////
    function int get_ccp_mask_index_from_fid_and_bar(logic[7:0] fid,logic[2:0] bar);
        int module_id = fid[7:3];
        int clstr_id  = bar[1:0];
        int mask_idx_on_clstr_from_log_per_clstr = get_phys_from_log_per_clstr(module_id,clstr_id);
        int ccp_mask_idx = mask_idx_on_clstr_from_log_per_clstr + (clstr_id*MAX_CCPS_PER_CLSTR);
//        $display($sformatf("-DBG- :: input is fid %0d ,bar (%0d),  return mask value is %0d  ",fid,bar,ccp_mask_idx));
        return ccp_mask_idx;
    endfunction : get_ccp_mask_index_from_fid_and_bar


    function int get_ccp_val_index_from_fid_and_bar(logic[7:0] fid,logic[2:0] bar);
        int ccp_mask_idx = get_ccp_mask_index_from_fid_and_bar(fid,bar);
        int ccp_val_idx = get_ccp_val_idx_from_mask_idx(ccp_mask_idx);
//        $display($sformatf("-DBG- :: input is fid %0d ,bar (%0d),  return val value is %0d  ",fid,bar,ccp_val_idx));
        return ccp_val_idx;
    endfunction : get_ccp_val_index_from_fid_and_bar


    /////////////////get_clstr_from_mask_idx//////////
    // given an index on one of the masks - 
    // it will return the clstr in which the index is on  
    //////////////////////////////////////////////////
    function int get_clstr_from_mask_idx(int location_on_mask); //mask is pcode style
//       $display($sformatf("-DBG- :: input is %0d , return value is %0d and max_num_of_ccps_per_clstr is :%0d ",location_on_mask,location_on_mask/(max_num_of_ccps_per_clstr - 1),max_num_of_ccps_per_clstr));            
        return (location_on_mask / (max_num_of_ccps_per_clstr))  ;
    endfunction : get_clstr_from_mask_idx
    /////////////////get_clstr_from_val_idx//////////
    // given a val index 
    // it will return the clstr in which the index is on  
    //////////////////////////////////////////////////
    function int get_clstr_from_val_idx(int val_idx); //mask is pcode style
//        $display($sformatf("-DBG- :: input is %0d , return value is %0d and max_num_of_ccps_per_clstr is :%0d ",val_idx,location_on_mask/(max_num_of_ccps_per_clstr - 1),max_num_of_ccps_per_clstr));            
        int location_on_mask = get_ccp_mask_idx_from_val_idx(val_idx);
        return (location_on_mask / (max_num_of_ccps_per_clstr))  ;
    endfunction : get_clstr_from_val_idx

    /////////////////get_ccp_type_by_val_index//////////
    // given a  val - index 
    // it will return the type of the ccp  
    ///////////////////////////////////////////////////
    function ccp_vc_env_pkg::ccp_type_t get_ccp_type_by_val_index(int ccp_val_idx);
        int mask_index = get_ccp_mask_idx_from_val_idx(ccp_val_idx);
        return get_ccp_type_by_mask_index(mask_index);
    endfunction : get_ccp_type_by_val_index
        
    /////////////////get_ccp_type_by_mask_index//////////
    // given an index on one of the masks - 
    // it will return the type of the ccp  
    ////////////////////////////////////////////////////
    function ccp_vc_env_pkg::ccp_type_t get_ccp_type_by_mask_index(int ccp_mask_idx);
        if(punit_ia_big_ccp_mask[ccp_mask_idx])  return BIG_CCP;
        if(punit_ia_atom_ccp_mask[ccp_mask_idx]) return ATOM_CCP;
        if(ccp_mask_idx == punit_gt_id)          return GT_CCP;
        if(ccp_mask_idx == punit_media_id)       return MEDIA_CCP;        
        $stacktrace;
        `uvm_error(get_name(), $sformatf("Bad CCP MASK ID; %0d", ccp_mask_idx))
    endfunction

    /////////////////is_ccp_slice_disabled//////////
    // given an index on one of the masks - 
    // it will check if the slice disabling mask is also asserted on that location 
    //////////////////////////////////////////////////////////////////////

    function bit is_ccp_slice_disabled(int location_on_mask);
        if(location_on_mask == punit_gt_id || location_on_mask == punit_media_id) return 0; // No Disable for GT or Media?//FIXME - nrapapor- MEDIA Refactoring
        if(punit_ia_big_ccp_mask[location_on_mask]  == 1 && fuse_all_llc_slice_ia_ccp_dis[location_on_mask]) return 1;
        if(punit_ia_atom_ccp_mask[location_on_mask] == 1 && fuse_all_llc_slice_ia_ccp_dis[location_on_mask]) return 1;
    endfunction
    /////////////////is_ccp_disabled//////////
    // given an index on one of the masks - 
    // it will check if there are any disablings (slice/bios/fuse etc....) - currently only slice is enabled 
    // OPEN - FIXME - ccp - ydror2 - when other disables like fuse and such are enabled - add them here as well
    //////////////////////////////////////////////////////////////////////

    function bit is_ccp_disabled(int location_on_mask);
        if ((location_on_mask == punit_media_id) || (location_on_mask == punit_gt_id)) return 0;
        if(is_ccp_slice_disabled(location_on_mask)) return 1;
        return 0;
    endfunction
    /////////////////get_ccp_mask_idx_from_val_idx//////////
    // given a "running" validation index of ccp (core #4 for example),
    // it will return the location of the ccp on the all_ia_ccp mask
    //////////////////////////////////////////////////////////////////////
    function int get_ccp_mask_idx_from_val_idx(int val_idx);
//       $display("-DBG- for val index %0d returning mask index :%0d, from val2mask : %0p",val_idx,val_idx_2_mask_idx[val_idx],val_idx_2_mask_idx);
        return val_idx_2_mask_idx[val_idx]; 
    endfunction : get_ccp_mask_idx_from_val_idx
     
    /////////////////get_ccp_val_idx_from_mask_idx//////////
    // given location on al_ia_ccp_mask - 
    // it will return a  "running" validation index of ccp (core #4 for example),
    //////////////////////////////////////////////////////////////////////
    function int get_ccp_val_idx_from_mask_idx(int mask_idx);
//        $display("-DBG- for mask index %0d returning val index :%0d, from array (%0p)",mask_idx,mask_idx_2_val_idx[mask_idx],mask_idx_2_val_idx);
        return mask_idx_2_val_idx[mask_idx]; 
    endfunction : get_ccp_val_idx_from_mask_idx


    /////////////////get_mask_index_list_of_enabled_any_ia_ccps//////////
    //get a list of indices for all_ia_ccp_mask  (merge of atom and big ccp mask)
    //   of ccp indices on the mask that are enabled  
    //  of both atom and bigcore
    //////////////////////////////////////////////////////////////////////
    function int_queue get_mask_index_list_of_enabled_any_ia_ccps();
        int_queue relevant_indices = {};
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                if ((! is_ccp_slice_disabled(location_on_mask))) begin
                    relevant_indices.push_back(location_on_mask);
                end
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_mask_index_list_of_enabled_any_ia_ccps

    /////////////////get_mask_index_list_of_any_ia_ccps//////////
    //get a list of indices for all_ia_ccp_mask  (merge of atom and big ccp mask)
    //   of ccp indices on the mask that are enabled  
    //  of both atom and bigcore
    //////////////////////////////////////////////////////////////////////
    function int_queue get_mask_index_list_of_any_ia_ccps();
        int_queue relevant_indices = {};
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                relevant_indices.push_back(location_on_mask);
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_mask_index_list_of_any_ia_ccps



    /////////////////get_val_index_list_of_enabled_any_ia_ccps//////////
    //get a list of indices for all_ia_ccp_val  (merge of atom and big ccp val)
    //   of ccp indices on the val that are enabled  
    //  of both atom and bigcore
    //////////////////////////////////////////////////////////////////////
    function int_queue get_val_index_list_of_enabled_any_ia_ccps();
        int_queue relevant_indices = {};
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                if ((! is_ccp_slice_disabled(location_on_mask))) begin
                    int val_idx = get_ccp_val_idx_from_mask_idx(location_on_mask);
                    relevant_indices.push_back(val_idx);
                end
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_val_index_list_of_enabled_any_ia_ccps
    /////////////////get_val_index_list_of_any_ia_ccps//////////
    //get a list of indices for all_ia_ccp_val  (merge of atom and big ccp val)
    //   of ccp indices on the val that are enabled  
    //  of both atom and bigcore
    //////////////////////////////////////////////////////////////////////
    function int_queue get_val_index_list_of_any_ia_ccps();
        int_queue relevant_indices = {};
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                int val_idx = get_ccp_val_idx_from_mask_idx(location_on_mask);
                relevant_indices.push_back(val_idx);
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_val_index_list_of_any_ia_ccps

    /////////////////get_mask_index_list_of_enabled_ccps_by_type//////////
    //get a list of indices for all_ia_ccp_mask  (merge of atom and big ccp mask)
    //   of ccp indices on the mask that are enabled  
    //   and have the same requested type 
    //////////////////////////////////////////////////////////////////////
    function int_queue get_mask_index_list_of_enabled_ccps_by_type(ccp_vc_env_pkg::ccp_type_t ccp_type);
        int_queue relevant_indices = {};
        if (ccp_type == GT_CCP) begin
            relevant_indices[0] = punit_gt_id; 
        end else if (ccp_type == MEDIA_CCP) begin
            relevant_indices[0] = punit_media_id; 
        end else begin  
            for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
                if (all_ia_ccp_mask[location_on_mask]) begin 
                    ccp_vc_env_pkg::ccp_type_t this_type = get_ccp_type_by_mask_index(location_on_mask);
                    if ((ccp_type == this_type) && (! is_ccp_slice_disabled(location_on_mask))) begin
                        relevant_indices.push_back(location_on_mask);
                    end
                end
            end
        end
    //        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_mask_index_list_of_enabled_ccps_by_type
    /////////////////get_val_index_list_of_enabled_ccps_by_type//////////
    //get a list of indices for all_ia_ccp_mask  (merge of atom and big ccp mask)
    //   of ccp indices on the mask that are enabled  
    //   and have the same requested type 
    //   convert each mask index to a val index
    //////////////////////////////////////////////////////////////////////
    function int_queue get_val_index_list_of_enabled_ccps_by_type(ccp_vc_env_pkg::ccp_type_t ccp_type);
        int_queue relevant_indices = {};
        if (ccp_type == GT_CCP) begin
            relevant_indices[0] = get_num_of_ia_ccps() + 1; 
        end else if (ccp_type == MEDIA_CCP) begin
            relevant_indices[0] = get_num_of_ia_ccps(); 
        end else begin  
            for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
                if (all_ia_ccp_mask[location_on_mask]) begin 
                    ccp_vc_env_pkg::ccp_type_t this_type = get_ccp_type_by_mask_index(location_on_mask);
                    if ((ccp_type == this_type) && (! is_ccp_slice_disabled(location_on_mask))) begin
                        relevant_indices.push_back(get_ccp_val_idx_from_mask_idx(location_on_mask));
                    end
                end
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_val_index_list_of_enabled_ccps_by_type
    /////////////////get_val_index_list_of_enabled_ccps_by_cluster//////////
    //   of ccp indices on the mask that are enabled on that cluster 
    ////////////////////////////////////////////////////////////////////////
    function int_queue get_val_index_list_of_enabled_ccps_by_cluster(int cluster);
        int_queue relevant_indices = {};
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                int relevant_clstr = get_clstr_from_mask_idx(location_on_mask);
                if ((relevant_clstr == cluster) && (! is_ccp_slice_disabled(location_on_mask))) begin
                    relevant_indices.push_back(get_ccp_val_idx_from_mask_idx(location_on_mask));
                end
            end
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return relevant_indices;
    endfunction : get_val_index_list_of_enabled_ccps_by_cluster
    /////////////////get_random_ccp_val_idx_per_cluster///////////////////////////////////////////////////////////////////////////
    // Input: ccp_cluster_t cluster - enum represents also index of cluster.                                                    //
    // Output: int ccp_val_idx.                                                                                                 //
    // Functionality:                                                                                                           //
    // Returns a random ccp_val_index form whithin the selected cluster among the enabled ones                                  //
    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    function int get_random_ccp_val_idx_per_cluster(ccp_vc_env_pkg::ccp_cluster_t cluster);
        int ccp_val_idx;
        ccp_vc_env_pkg::int_queue ccp_val_index_list = get_val_index_list_of_enabled_ccps_by_cluster(.cluster(cluster));
        std::randomize(ccp_val_idx) with {ccp_val_idx inside {ccp_val_index_list};};
        return ccp_val_idx;
    endfunction :  get_random_ccp_val_idx_per_cluster

    /////////////////get_cluster_from_ccp_val_index////////////////////////////////////////////////////
    // Input:  int ccp_val_index.                                                                    //
    // Output: ccp_cluster_t cluster index.                                                          //
    // Functionality:                                                                                //
    // Returns the index of the cluster whose ccp_val_index belongs to.                              //
    // If ccp_val_index has not been found in the exsiting clusters,                                 //
    // fatal/returns value of -1?                                                                    //
    ///////////////////////////////////////////////////////////////////////////////////////////////////
    function int get_cluster_from_ccp_val_index(int ccp_val_index); 
        for (int cluster_i=0; cluster_i<get_num_of_clusters; cluster_i++) begin
            int_queue ccp_val_index_list_clusterX;
            ccp_val_index_list_clusterX = get_val_index_list_of_enabled_ccps_by_cluster(.cluster(cluster_i));
            foreach (ccp_val_index_list_clusterX[i]) begin
                if (ccp_val_index == ccp_val_index_list_clusterX[i]) return cluster_i;
            end
        end            
        `uvm_fatal(get_name(), $sformatf("ccp_val_index == %0d is not enabled in any cluster! Please review the enabled ccps lists in the following lines:", ccp_val_index))
        return -1;
    endfunction : get_cluster_from_ccp_val_index
    /////////////////get_logic_index_list_of_enabled_any_ia_cores//////////
    //get a list of
    //////////////////////////////////////////////////////////////////////
    function int_queue get_logic_index_list_of_enabled_any_ia_cores();
        int_queue relevant_indices = {};
        int running_idx = 0;
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin 
                if ((! is_ccp_slice_disabled(location_on_mask))) begin // FIXME - ydror2 - 13.06.22 - need to add per - core + fuse disbale
                    int val_idx = get_ccp_val_idx_from_mask_idx(location_on_mask);
                    int core_idx[$] = get_all_lpids_from_mask_idx(location_on_mask);
                    foreach (core_idx[i]) begin // FIXME - ydror2 - 13.06.22 - need to add core disable:
                        relevant_indices.push_back(running_idx);
                        running_idx += 1;
                    end
                end
            end
        end
//        $display("-DBG- returning core indices (of slice enabled  only) :%0p",relevant_indices);
        return relevant_indices;
    endfunction : get_logic_index_list_of_enabled_any_ia_cores
    /////////////////get_mask_of_enabled_any_ia_ccp//////////
    //
    //
    //////////////////////////////////////////////////////////////////////
    function int get_mask_of_enabled_any_ia_ccp();
        int mask_of_enabled_ccp;
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
                mask_of_enabled_ccp[location_on_mask] = (all_ia_ccp_mask[location_on_mask] && (! is_ccp_slice_disabled(location_on_mask)));
        end
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        return mask_of_enabled_ccp;
    endfunction : get_mask_of_enabled_any_ia_ccp
    /////////////////get_logical_mask_of_enabled_any_ia_ccp//////////
    //
    //
    //////////////////////////////////////////////////////////////////////
    function int get_logical_mask_of_enabled_any_ia_ccp();
        int logic_mask_of_enabled_ccp;
//        $display("-DBG- for type %0s returning queue of indices :%0p",ccp_type.name(),relevant_indices);
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask] && (! is_ccp_slice_disabled(location_on_mask))) begin
                int log_id = get_logical_idx_on_mask_from_mask_idx(location_on_mask);
                logic_mask_of_enabled_ccp[log_id] = 1;
            end 
        end
        return logic_mask_of_enabled_ccp;
    endfunction : get_logical_mask_of_enabled_any_ia_ccp

///////////////////////////get_logical_idx_on_mask_from_mask_idx/////////////////////////////
// input: 
// output:
// basically:
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_logical_idx_on_mask_from_mask_idx(int mask_idx);
        int clstr = get_clstr_from_mask_idx(mask_idx);
        int log_id = get_logical_id_per_clstr_from_mask_idx(mask_idx);
        return log_id+clstr*MAX_CCPS_PER_CLSTR;
    endfunction : get_logical_idx_on_mask_from_mask_idx

///////////////////////////get_serial_index_of_ccp_by_clstr/////////////////////////////
// input: 
// output:
// basically: this function is for referring to the relevant hardware index for ccp compression. 
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_serial_index_of_ccp_by_clstr(int val_idx);
        int clstr = get_clstr_from_val_idx(val_idx);
        if (clstr == 0) return val_idx;
        return (val_idx - count_ccps_per_clstr(0));
    endfunction : get_serial_index_of_ccp_by_clstr

///////////////////////////get_serial_logic_idx_from_mask_idx/////////////////////////////
// input: 
// output:
// basically: this function is for referring to the relevant hardware index for ccp compression. 
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_serial_logic_idx_from_mask_idx(int mask_idx);
        int clstr = get_clstr_from_mask_idx(mask_idx);
        int log_id = get_logical_id_per_clstr_from_mask_idx(mask_idx);
        int serial_logic_num = 0 ;
        for (int i = 0; i<clstr; i++) begin
            serial_logic_num += count_ccps_per_clstr(i);
        end 
        serial_logic_num += log_id;
        return serial_logic_num;
    endfunction : get_serial_logic_idx_from_mask_idx



///////////////////////////get_serial_index_of_ccp_per_type_by_val_idx/////////////////////////////
// input: val index  
// output: the serial number of ccp according to type - for example - val -idx #16 is the #3rd ATOM ccp or 14th BIG ccp
// basically: gets the mask index till that point and counts how many ccps with matching types till that index
//////////////////////////////////////////////////////////////////////////////////////////////////
            
    function int get_serial_index_of_ccp_per_type_by_val_idx(int val_idx);
        int counter = 0;
        int mask_idx = get_ccp_mask_idx_from_val_idx(val_idx);
        ccp_vc_env_pkg::ccp_type_t ccp_type_to_match = get_ccp_type_by_mask_index(mask_idx);
        for (int location_on_mask = 0; location_on_mask < mask_idx;location_on_mask++) begin
            if (all_ia_ccp_mask[location_on_mask]) begin
                if (get_ccp_type_by_mask_index(location_on_mask) == ccp_type_to_match) begin
                    counter++;
                end 
            end
        end 
        $display("-DBG- for val idx %0d, which is mask idx %0d, it is the %0d's %0s",val_idx,mask_idx,counter,ccp_type_to_match.name());
        return counter;
    endfunction : get_serial_index_of_ccp_per_type_by_val_idx



    //////////////////////////////////////////////////////////////////////
    function int get_random_mask_index_of_enabled_any_ia_ccp();
        int_queue enabled_ccps_mask_indices;
        int rand_ccp_id;
        bit rand_res;
        enabled_ccps_mask_indices = get_mask_index_list_of_enabled_any_ia_ccps();

        rand_res= std::randomize(rand_ccp_id) with {
            rand_ccp_id inside {enabled_ccps_mask_indices};
        };
        
        return rand_ccp_id;

    endfunction : get_random_mask_index_of_enabled_any_ia_ccp
   //////////////////////////////////////////////////////////////////////
    function int get_random_mask_index_of_enabled_any_ia_ccp_by_type(ccp_vc_env_pkg::ccp_type_t ccp_type);
        int_queue enabled_ccps_mask_indices;
        int rand_ccp_id;
        bit rand_res;
        enabled_ccps_mask_indices = get_mask_index_list_of_enabled_ccps_by_type(ccp_type);

        rand_res= std::randomize(rand_ccp_id) with {
            rand_ccp_id inside {enabled_ccps_mask_indices};
        };
        
        return rand_ccp_id;

    endfunction : get_random_mask_index_of_enabled_any_ia_ccp_by_type

    //////////////////////////////////////////////////////////////////////

    function int get_global_id_from_val_idx(int val_idx); // USED in sequence
        return ccp_global_id_by_val_idx[val_idx];
    endfunction
    //*******************************************************/
    function int get_pcode_id_from_val_idx(int val_idx); // USED in sequence
        return ccp_global_id_by_val_idx[val_idx];
    endfunction
    //*******************************************************/

    function int get_global_id_from_mask_idx(int mask_idx); // USED in sequence
        int val_idx = get_ccp_val_idx_from_mask_idx(mask_idx);
        return ccp_global_id_by_val_idx[val_idx];
    endfunction
    //*******************************************************/
    function int get_pcode_id_from_mask_idx(int mask_idx); // USED in sequence
        int val_idx = get_ccp_val_idx_from_mask_idx(mask_idx);
        return ccp_global_id_by_val_idx[val_idx];
    endfunction

    //********************************************************
    function bit is_gt_enabled();
        return 1;
    endfunction


/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
///////////////////////////BASIC UTILITIES (INTERNAL USE)////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
                
///////////////////////////get_phys_id_per_clstr_from_location_on_mask/////////////////////////////
// input: a location on the all_ia_map (merge between atom and bigcore map) 
// output: which physical id (in its relevant cluster) the map index gets
// basically: gets the relevant cluster, and counts ones only on the relevant cluster in all_ia_ccps
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_phys_id_per_clstr_from_location_on_mask(int location_on_mask);
        int clstr = get_clstr_from_mask_idx(location_on_mask);
        int phys_id = 0;
        if (location_on_mask == punit_media_id) return punit_media_id;
        if (location_on_mask == punit_gt_id) return punit_gt_id;
        for (int mask_idx=clstr*MAX_CCPS_PER_CLSTR; mask_idx < location_on_mask;mask_idx++) begin 
            if (all_ia_ccp_mask[mask_idx]) begin
                phys_id++;
                end
            end
//        $display("-DBG- for  location on mask - %0d, the physical id is %0d",location_on_mask,phys_id);
        return phys_id;
    endfunction : get_phys_id_per_clstr_from_location_on_mask

    function int get_phys_id_per_clstr_from_val_idx(int ccp_val_idx);
        int ccp_mask_idx = get_ccp_mask_idx_from_val_idx(ccp_val_idx);
        return get_phys_id_per_clstr_from_location_on_mask(ccp_mask_idx);
    endfunction : get_phys_id_per_clstr_from_val_idx
///////////////////////////get_location_on_mask_from_clstr_and_phys_id/////////////////////////////
// input: clstr id and physical id  
// output: index on all_ia_ccp mask
// basically: 
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_location_on_mask_from_clstr_and_phys_id(int physical_id,int clstr);
        int mask_idx = clstr * MAX_CCPS_PER_CLSTR;
        int ccp_counter = -1; 
        if ((physical_id == punit_media_id) && (clstr == 0)) return punit_media_id;
        if ((physical_id == punit_gt_id) && (clstr == 0)) return punit_gt_id;
        while ((ccp_counter < physical_id) && (mask_idx <= (clstr+1)*MAX_CCPS_PER_CLSTR)) begin 
            if (all_ia_ccp_mask[mask_idx]) begin
                ccp_counter++;
                end
            mask_idx++;
            end
        if (mask_idx == (clstr+1)*MAX_CCPS_PER_CLSTR) begin 
            //`uvm_error(get_name(), $sformatf("couldn't get location on mask from clstr %0d and phys id %0d", clstr,physical_id)) //FIXME CBB - adjust for non GT?
        end
//        $display("-DBG- for clstr %0d, and physical id %0d, the location on mask is : %0d",clstr,physical_id,mask_idx);
        return mask_idx-1;
    endfunction : get_location_on_mask_from_clstr_and_phys_id


///////////////////////////count_enabled_ccps_per_clstr/////////////////////////////
// input: cluster
// output: how many ccps in the cluster are not disabled 
// basically: gets the relevant cluster, and counts ones only on the relevant cluster in all_ia_ccps
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int count_enabled_ccps_per_clstr(int clstr);
        int num_of_enabled_ccps_per_clstr;
        logic[STRAP_MASK_SIZE-1:0] enabled_ia_ccp_mask_only_clstr;
        logic[STRAP_MASK_SIZE-1:0] cluster_mask = 0;
        for (int i = clstr*MAX_CCPS_PER_CLSTR;i < (clstr+1)*MAX_CCPS_PER_CLSTR;i++) begin
            cluster_mask[i] = 1;
        end
        enabled_ia_ccp_mask_only_clstr = punit_enabled_ia_ccp_mask & cluster_mask;
        num_of_enabled_ccps_per_clstr = $countones(enabled_ia_ccp_mask_only_clstr);
//        $display("-DBG- counting ones on enabled mask for clstr: %0d, enabled_mask : %0b, cluster_mask : %0b , enabled_mask_on_clstr: %0b,returning : %0d",clstr,punit_enabled_ia_ccp_mask,cluster_mask, enabled_ia_ccp_mask_only_clstr,num_of_enabled_ccps_per_clstr);
        return num_of_enabled_ccps_per_clstr;

    endfunction : count_enabled_ccps_per_clstr

///////////////////////////count_ccps_per_clstr/////////////////////////////
// input: cluster
// output: how many ccps in the cluster 
// basically: gets the relevant cluster, and counts ones only on the relevant cluster in all_ia_ccps
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int count_ccps_per_clstr(int clstr);
        int num_of_ccps_per_clstr = 0;
        logic[STRAP_MASK_SIZE-1:0] cluster_mask = 0;
        logic[STRAP_MASK_SIZE-1:0] ia_ccp_mask_only_clstr = 0;
        for (int i = clstr*MAX_CCPS_PER_CLSTR;i < (clstr+1)*MAX_CCPS_PER_CLSTR;i++) begin
            cluster_mask[i] = 1;
        end
        ia_ccp_mask_only_clstr = all_ia_ccp_mask & cluster_mask;
        num_of_ccps_per_clstr = $countones(ia_ccp_mask_only_clstr);
//        $display("-DBG- counting ones on enabled mask for clstr: %0d, enabled_mask : %0b, cluster_mask : %0b , enabled_mask_on_clstr: %0b,returning : %0d",clstr,punit_enabled_ia_ccp_mask,cluster_mask, enabled_ia_ccp_mask_only_clstr,num_of_enabled_ccps_per_clstr);
        return num_of_ccps_per_clstr;
    endfunction : count_ccps_per_clstr


    
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////// LOGIC AND PHYS2LOGIC(EXTERNAL USE)///////////////////////
/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////
            
///////////////////////////get_logical_id_per_clstr_from_phys_id/////////////////////////////
// input: 
// output:
// basically:
//////////////////////////////////////////////////////////////////////////////////////////////////

    function int get_logical_id_per_clstr_from_phys_id(int physical_id,int clstr);
        int location_on_mask = get_location_on_mask_from_clstr_and_phys_id(physical_id,clstr); 
        int log_id = phys2log_map_per_cluster[clstr][physical_id];
//        $display("-DBG- for clstr %0d, and physical id %0d (location on mask %0d), the logical id  is : %0d",clstr,physical_id,location_on_mask,log_id);
        if (location_on_mask == punit_media_id) return punit_media_id;
        if (location_on_mask == punit_gt_id) return punit_gt_id;
        return log_id;
    endfunction : get_logical_id_per_clstr_from_phys_id

///////////////////////////get_logical_id_per_clstr_from_mask_idx/////////////////////////////
// input: 
// output:
// basically:
//////////////////////////////////////////////////////////////////////////////////////////////////
            
    function int get_logical_id_per_clstr_from_mask_idx(int mask_idx);
        int clstr = get_clstr_from_mask_idx(mask_idx);
        int physical_id = get_phys_id_per_clstr_from_location_on_mask(mask_idx); 
        int log_id = phys2log_map_per_cluster[clstr][physical_id];
//        $display("-DBG- for clstr %0d, and physical id %0d (location on mask %0d), the logical id  is : %0d",clstr,physical_id,mask_idx,log_id);
        if (mask_idx == punit_media_id) return punit_media_id;
        if (mask_idx == punit_gt_id) return punit_gt_id;
        return log_id;
    endfunction : get_logical_id_per_clstr_from_mask_idx

//////////////get_phys_from_log_per_clstr//////////
//////////////////////////////////////////////////
function int get_phys_from_log_per_clstr(int logical_id,int clstr); //mask is pcode style
    int mask_logical_idx = MAX_CCPS_PER_CLSTR*clstr + logical_id; 
    if (get_ccp_type_by_mask_index(mask_logical_idx) == GT_CCP) return punit_gt_id; 
    if (get_ccp_type_by_mask_index(mask_logical_idx) == MEDIA_CCP) return punit_media_id; 
    return log2phys_map_per_cluster[clstr][logical_id];
endfunction : get_phys_from_log_per_clstr

///////////////////get_phys_from_log//////////////
//////////////////////////////////////////////////
function int get_phys_from_log(int logical_id); //mask is pcode style
    int clstr = logical_id/MAX_CCPS_PER_CLSTR;
    int mask_logical_idx = logical_id; 
    int phys_idx = get_phys_from_log_per_clstr(logical_id,clstr);
    return phys_idx;
    endfunction : get_phys_from_log
        
    /////////////////get_ccp_mask_logic_idx_from_val_idx//////////
    // given a "running" validation index of ccp (core #4 for example),
    // it will return the location of the ccp on the all_ia_ccp mask (but after sliced disabling - i.e logical index)
    //////////////////////////////////////////////////////////////////////
    function int get_ccp_mask_logic_idx_from_val_idx(int val_idx);
        int mask_idx = get_ccp_mask_idx_from_val_idx(val_idx);
        int clstr = get_clstr_from_mask_idx(mask_idx);
        int log_idx_on_clstr = get_logical_id_per_clstr_from_mask_idx(mask_idx);
//       $display("-DBG- for val index %0d returning mask index :%0d, from val2mask : %0p",val_idx,val_idx_2_mask_idx[val_idx],val_idx_2_mask_idx);
        return log_idx_on_clstr + MAX_CCPS_PER_CLSTR*clstr; 
    endfunction : get_ccp_mask_logic_idx_from_val_idx


    /////////////////get_ccp_logical_mask_from_phys_mask//////////
    //////////////////////////////////////////////////////////////////////
    function int get_ccp_logical_mask_from_phys_mask(int phys_mask);
        int log_mask;
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (phys_mask[location_on_mask] == 1) begin
                int phys_idx = location_on_mask;
                int log_idx = get_logical_idx_on_mask_from_mask_idx(location_on_mask);
                log_mask[log_idx] = 1;
            end
        end 
        return log_mask;
    endfunction : get_ccp_logical_mask_from_phys_mask

    /////////////////get_ccp_phys_mask_from_logical_mask//////////
    //////////////////////////////////////////////////////////////////////
    function int get_ccp_phys_mask_from_logical_mask(int log_mask);
        int phys_mask;
        for (int location_on_mask = 0; location_on_mask < $size(all_ia_ccp_mask);location_on_mask++) begin
            if (log_mask[location_on_mask] == 1) begin
                int log_idx = location_on_mask;
                int phys_idx = get_phys_from_log(log_idx);
                phys_mask[phys_idx] = 1;
            end
        end 
        return phys_mask;
    endfunction : get_ccp_phys_mask_from_logical_mask


endclass : ccp_common_cfg
