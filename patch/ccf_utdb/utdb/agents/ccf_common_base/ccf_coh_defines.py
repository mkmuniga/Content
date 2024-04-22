from agents.ccf_systeminit.ccf_systeminit import ccf_systeminit

class CCF_COH_DEFINES:
    CCF_SI = ccf_systeminit.get_pointer()

    num_of_tor_entries = 40
    num_physical_cv_bits = 32
    num_of_data_chunk = 2
    num_of_cfi_data_chunk = 2
    num_of_santa = 1
    num_of_sets = 4096
    num_of_ccf_clusters = 4
    max_num_of_tag_ways = 36
    max_num_of_data_ways = 20
    set_lsb = 6
    set_msb = 17
    num_of_set_bits = set_msb - set_lsb + 1
    tag_lsb = set_msb + 1
    tag_msb = 51
    address_lenth_in_hex = 12 #TODO: need to update for the new address length
    mktme_lsb = 41 + (bin(CCF_SI.ccf_mktme_mask).count('1'))#TODO: this is not correct
    mktme_msb = 51
    address_lsb = 0
    address_msb = mktme_msb
    hash_lsb = 6
    hash_msb = 19
    LT_region_prefix = "0xfed"
    LT_LOW_OFFSET = "0x20000"
    LT_HIGH_OFFSET = "0x8ffff"
    clos_reg_tag_way_size = 16
    num_of_clos_supported = 16
    MAX_PMON_COUNTER = int(0xFFF_FFFF_FFFF)
    num_of_monitor_entries = 16
    num_of_monitor_copy_addresses = 12
    data_chunk_0 = "01"
    data_chunk_1 = "10"

    SNOOP_FILTER = 31

    #Addressless defines
    llc_addressless_llcway_addr_range_msb = 32
    llc_addressless_llcway_addr_range_lsb = 27