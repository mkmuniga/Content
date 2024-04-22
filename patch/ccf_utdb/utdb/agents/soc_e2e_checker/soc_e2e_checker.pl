#!/usr/intel/bin/perl

#FIXME: Need to add Read opcodes : RDCURR , UCRDF, RFO
#FIXME: Need to make sure a read does not read a write that came after it in the same channel.

#  ----------------------------------------------------------------------
#    ----------------------------------------------------------------------
#    file:    soc_e2e_checker.pl
#    Date Created  : 06/JUN/2016
#    Author        : eyal.sinuani@intel.com
#    Project       : ICL
#    ----------------------------------------------------------------------
#  
#  SOC IO e2e checker 
# ------------------------------------------------------------------------
#
# Checker runs as post processing checker on simulation results files.
# It read PSF files, pcie link files (pcie bfm files0), OPIO link & psf files, iommu files.
#
#- SOC E2E checker - pros
#    Do data checking for IO system from PCIE to MC.
#    It covers for well-known SOC validation hole.
#    E2E checking is overall arch checking that can only be done in SOC.
#    Does IOMMU VTD checks.
#    Can be extended to also check IDI traffic.
#    It's new checking. Good chance to find bug.
#    Can run on emulation.
#    Checker can be implemented gradually, priority wise. Feature by feature.
#
#-	Why do post simulation checker in perl?
#    Can always run it post process.
#    It overcomes SOC long runs problem.
#    Has fast perl debugger
#    Fast development
#    You can easily create regression list for test by simulation log files.
#       Can easily create error test, by inserting an error in the log file.
#       Test can be taken from any model and project.
#    Can be moved easily to another projects.
#    Flexible. Work also on TCSS.
#    I think perl is fast & efficient for complex algorithms development.
#       Program by scalar, list & hash (no types).
#
#-	Soc e2e Cons
#    For emulation checker runs slow.
#    Checker use logs and not TLMs.
#    Missing checks. Need to complete them.
#
#-	Checker has its own testing env
#    Has a list of tests for all its features.
#    Has fail 2 pass test that ensures that checker finds bugs.
#    Ensures that check finds all kinds of mismatches
#    Allow further development ensuring all previous features works 
#    Test driven development. Like in Code Dojo.
#    Has debug verbosity.
#
#-	Checks
#    Performs data checkings
#    Check transaction ordering.
#    Checks all IOP channels
#    Checks TCSS PCIE
#    Checks PEGS PCIE
#    Checks OPIO/ DMI
#    Checks P2P
#    IOP IOMMU
#    TCSS IOMMU 
#
#-	Detail checking
#    IOP to MC MWr ["address","data"] and ordering.
#    All PCIE LINK to MC MWr ["address","data"] and ordering.
#    IOP to All PCIE PSF, MWr&MRd ("data","cmd","id","address","fbe_lbe").
#    All PCIE PSF to IOP, (CAS|Swap|FAdd|IOWr|IORd|MRd|CfgWr|CfgWr) ("data","cmd","id","address","fbe_lbe").
#    IOP to All PCIE Cpl ("data","cmd","id","address","fbe_lbe").
#    All PCIE to IOP Cpl ("data","cmd","id","address","fbe_lbe").
#    All PCIE PSF to all PCIE LINK CfgWr cmd "id" only.
#    All PCIE PSF to all PCIE LINK MWr ["id","data","address"].
#    All PCIE LINK to all PCIE PSF all ["BDF","id","address","data"]
#    Check P2P MCTP DMI to all PCIE ["data","cmd","id"]
#    Check P2P MCTP all PCIE to DMI ["data","cmd","id"]
#    
#-	Flow
#    It parse all input files and converts them into transaction list.
#    It takes two lists, filter them, and compare a lists of fields.
#    Checker read IOMMU files, and can make address conversions.
#    For MC data checking, its breaks all transactions to byte stream
#    Check knows to retry several possible options.
#
#-	IO memory ordering rules (for WR)
#    Transaction from IOP always sent to MC in the same order (only per source channel basis).
#    But they can be splitted to shorter chunks.
#    Transaction from different source can overtake each other.
#    IO system does not merge transactions.
#    IO system does not care about their address. 
#
#-	What next
#    Comparing also reads (they can be bypassed by writes)
#    Checking memory ordering of input streams only.
#    Checking also IDI streams.
#    Checking interrupts flows.
#    Tracking relevant register programming (like BARs).
# 
#   LNL future features
#   To complete the ordering check that Irael asked for GT, when a read is commited on some write, all previous write transactions that got GT before should be commited 
#   need to check reads from DISPLAY and MEDIA NAPs SOC_DEIOSF too
#   Need to fix the VPU AXI tracker and remove this skip: "Skip this test because the AXI file is bad fixme:axi:";
#   need to fix: $skip_e2e_write_chk=1 unless defined($skip_e2e_write_chk); #FIXME:temporarily disabling write checking in lnl if there is Atomic command. need to fix it later.
#    Israel Diamand said that for for write ordering check we need to see that the GT is waiting for GT before it sends the next transaction.
#     So write should commit a previous write only it was send after the previous write got GT.
#    In the VPU AXI transacion I have to set that start and end cycle more exactly.
#    Need to impelenet checking also for IPU AXI.
#    SNP writes that case from CCF and ATOM should have an end time, and we should consider it.
#    Need to support ccf_preload file with M state.
#    Need to debug why this test have a different output every run: r141_chassis_rand_test__model_uncore_ADL_reg
#    need tp improve the merge_ns_write_channels() by giving common channels to all the nc MemWr from all devices
#
#

$e2e_help = '


Command line:
soc_e2e_checker.pl [-debug=(1|2|..|9)] [-do_e2e_warning_only=0]

-debug=(1|2|..|9)
  Dump debug information.
  The -debug=1 is minimal debug information.
  The -debug=9 is maximum debug information.

-do_e2e_warning_only=0
  Checker by default gives only warnings and does not fail the test.
  You can disable it by -do_e2e_warning_only=0
  Then the checker reports error and exit with error code on any problem.

Checker can be added to a trex simulation as post processing tool by:
-post soc_e2e_checker.pl -post-

Or added to simregress by:
-trex -post soc_e2e_checker.pl -post- -trex- -save_ptrn logbook.log

The warnings or errors will be reported to the logbook.log file.

';

#use e2e_XS;
use Cwd qw(getcwd);
use IO::Handle;
use Try::Tiny;
use List::Util qw(min);
use constant REC_ATTR_WCIL => 0x1;

use constant CH_ATTR_WCIL => 0x1;
use constant CH_ATTR_MINE => 0x2;
use constant CH_ATTR_CXL  => 0x4;

use constant REFMEM_REC    => 0;
use constant REFMEM_INDEX2 => 1;
use constant REFMEM_INDEX1 => 2;
use constant REFMEM_COMMIT => 3;
use constant REFMEM_DATA   => 4;

use constant OBJ_INDEX => 0;
use constant OBJ_REC   => 1;

# Version
$version = "255.0";
# Debug verbosity flag
$debug = 0; 
$e2e_write_retry_count = -1; # this feature allow the user to stop instead of retry and hence get detailed debug information at that retry
$e2e_fast_mode = undef;
# Program return code. 0 - success
$exit_code = 0;
# Due to bug in TBTDMA files that cause transaction to have trnasactions with zero parameters, I have a workaround for it.
$skip_TBTDMA_PSF = 0; # FIXME: Need to disable this skip once mkremene fix the TBTDMA PSF files.
# Allow test to have bad IOMMU accesses that gets UR (and checker will ignore them). 
$skip_iommu_no_conv = 1;
# Enable IOMMI MSI checkings
$check_iommu_msi_conv = 1;
# Allow skipping the e2e_chk.
$skip_e2e_read_chk = undef;
$is_e2e_monitor_read = undef;
$is_e2e_advane_WCIL = undef;
$no_CCF_write_merge = undef;
$e2e_write_chk_use_uri = undef;
$skip_e2e_pcie_read_chk = undef; # FIXME: *** Need to enable this important check.***
$skip_e2e_write_chk = undef;
$skip_e2e_axi_write_chk = undef;
#$argv{skip_axi_compare_timing_chk} = undef;
#argv#$skip_bad_uri_filter = undef;
$verify_write_time = undef;
$verify_parent_index = undef;

$lnl_use_mc_vs_hbomc = undef; # FIXME: *** Need to enable this important check.***

$lnl_mc_tick_update = undef;
$ICELAND_IDI = "AT_IDI_[456]"; # this is for lnl
$sys_addr_mask = 0xFFFFFFFF_FFFFFFFF;
$sys_full_addr_mask = 0xFFFFFFFF_FFFFFFFF; # by default no mask. put mask for lnl later
$hbo_mufasa_en = undef;

$mcc_preloader_ver = 0;

$skip_psf_Cplt_chk = undef;
$skip_psf_long_trans_chk = undef;

$skip_ACF_IDI_chk = undef;

$skip_CL_recheck = undef;
$lnl_vpu_btrs_ver = undef;

@skip_DPR_changing_range = ();
$skip_DPR_changing_chk = undef;
@CXL_CFI_FILTER_STR_l = ("SOC_DEIOSF","SOC_SVTU","SOC_PUNIT",);
$parent_idx_count = 0; # parent index will be global


# This flag creaqte a preload memory image from MRd the cmi log files.
# This way I can work without the mcc_preload or astro preload.
# This also enable running when tme encryption is enabled.
# It is used in ADL tme simulatiuons or when having complex mc hashing.
$create_cmi_preload=undef;

$do_e2e_read_channel=undef;
$skip_e2e_read_channel={};
$do_e2e_warning_only=undef;
#$use_die_for_error=undef;
$do_e2e_preload_encrypt=undef;
$use_refmem_recalc = 0;
$is_nbace=undef;
$is_dump_time=undef;
$emulation_obj_file = undef;
$emulation_obj_load_time = undef;
$emulation_tick_eot = undef;
$systeminit_file;
$idi_log_file = "idi.log";
$push_cmd_file;

#$emu_transactor_cmd_range = undef;
$argv{skip_if_non_snoop} = undef;
#$argv{skip_PRD_opcode} = undef;
#$argv{skip_mmio_chk} = undef;
#$argv{skip_wcil_for_dram} = undef;
#$debug_address = undef;
$debug_start_time = undef;
$debug_ch_idx1 = undef;
$systeminit_file_exist = undef;
$use_write_update_file = undef;
$gen_write_update_file = undef;
$fork_proc_count = 0;
$argv{max_proc} = 4;
#$is_scalable_nested = undef
$run_in_failed_test = undef;

# FIXME: Temporarily disable this check because PCIE bars that being written twice are not supported.
# This failed in RKL GNA sequences.
$skip_iop_D_mem_chk = 0;

$ibecc_act = 0;
$lnl_ibecc_en = 0;
$mee_act = 0;
$use_iop_cmi_log = undef;
$skip_iop_cmi_log = undef;

$skip_axi_file = undef;
$skip_gtcxl_file = undef;
@gtcxl_idi_filter_l = ();
$skip_uri_chk = undef;
$max_tick_end = (~0>>1);
$max_tick_go = $max_tick_end-1;

$cpu_proj = "icl";
$cpu_proj_step = "";

$PCIE_CFG_SPACE->{0}->{0} = { };
$PCIE_CFG_SPACE->{6}->{0} = { };
$PCIE_CFG_SPACE->{1}->{0} = { };
$PCIE_CFG_SPACE->{1}->{1} = { };
$PCIE_CFG_SPACE->{1}->{2} = { };

$skip_OPIO_LINK_err = undef; # Skip know error in OPIO_LINK with this message "EER occurred"  that happens in C6 & C7 tests. 
$skip_timeout_err = undef;
$script_timeout_param = undef;

$script_start_time = time();

@pcie_compare_field_l = ("data","cmd","id","address","fbe_lbe");

$NPK_DID = 9;
$XDCI_DID = 13;
$XHCI_DID = 13;
$IDC_DID = 10;
$PEP_DID = 11;
$GNA_DID = 8; 
$TAM_DID = 6; 
$IPU_DID = 5; 
$DISPLAY_DID = 2; 
$PSFPCI_DID = 31; # This is not  a real device number. Its for ADL model.

%all_DID_h = (NPK=>[$NPK_DID,0,12],GMM=>[8,0,15],GNA=>[8,0,15],XDCI=>[13,1],XHCI=>[13,0],IDC=>[$IDC_DID,0],PEP=>[$PEP_DID,0],
    # DID Added for ADL
    PSFPCI=>[$PSFPCI_DID,0],DISPLAY=>[$DISPLAY_DID,0],TAM=>[$TAM_DID,0],IPU=>[$IPU_DID,0]);
%DID_info_h = (
    $IDC_DID => { 
        BAR_MASK => { 0=>0x7F_FFFF, 1=> 0x7_FFFF }, 
    },
    $PEP_DID => { 
        BAR_MASK => { 0=>0x3F_FFFF, }, 
    },
    $GNA_DID => { 
        BAR_MASK => { 0=>0xFFF, }, 
    },
);
$bar_max_index = 1;

# OCH cmi hashing
$soc_mc_hash_disable = 1;
$soc_mc_hash_lsb = 6;
$soc_mc_hash_lsb_mask = 0;
$soc_mc_hash_mask = 0;

# OCH cmi hashing
$soc_hbo_hash_disable = 1;
$soc_hbo_hash_lsb = 10; #6+2;
$soc_hbo_hash_lsb_mask = 0;
$soc_hbo_hash_mask = 0; #0x174c>>2;


$ADL_cmi_addr_h = undef;

# Pointer to tracker log file that we will load
$cmi_iop_trans_file_scbd = undef;
$cmi_ibecc_trans_file_scbd = undef;
@cmi_ibecc_trans_file_scbd_l = ();
@cmi_idp_trans_file_scbd_l = ();
$mcc_trans_file_scbd = undef;
@mcc_trans_file_scbd_l = ();
$iop_psf_file_scbd = undef;
$PSF5_psf_file_scbd = undef;
$opio_psf_file_scbd = undef;
$dmi_psf_file_scbd = undef;
$npk_psf_file_scbd = undef;
$pegs_psf_file_scbd = undef;
$tcss_psf_file_scbd = undef;
$pep_psf_file_scbd = undef;
@more_psf_file_scbd = ();
$tbtpcie_iommu_scbd_h = undef;
$IOP_iommu_scbd_h = undef;
#$IOC_iommu_scbd_h = undef;
@pcie_psf_file_scbd_l = ();
@tbtdma_psf_file_scbd_l = ();
$opio_link_file_scbd = undef;
$pep_svt_link_file_scbd = undef;
$mufasa_file_scbd = undef;
$dmi_link_file_scbd = undef;
@pcie_link_file_scbd_l = ();
$IOP_IMR_RS0_EN_val = 0;
$all_imr_range = { BASE=>2,LIMIT=>1,MASK=>0xFFFFFFFF_FFFFFFFF,region=>"all_imr_range"}; # Just a dummpy empty range 

$tick_mul = 1.0;
$is_scbd_tick_tunings = 0;

$to_WRC_VC_h;

local %pch_non_snoop_addr_h = ();

local $idi_file_scbd = { };

local $idi_file_scbd = { };
local $cxl_idi_file_scbd = { 
    MemWr_chs => { # Give src_ch_tc to GT cxl.log opcodes of WOWrInv and WOWrInvF using merge_ns_write_channels()
        GT_IDI_0 => { count => 0 , prefix=>"_WO" }, #
        GT_IDI_1 => { count => 0 , prefix=>"_WO" }, #
        GT_IDI_2 => { count => 0 , prefix=>"_WO" }, #
        GT_IDI_3 => { count => 0 , prefix=>"_WO" }, #
        GT_IDI_4 => { count => 0 , prefix=>"_WO" },
        GT_IDI_5 => { count => 0 , prefix=>"_WO" },
        GT_IDI_6 => { count => 0 , prefix=>"_WO" },
        GT_IDI_7 => { count => 0 , prefix=>"_WO" },
        GT_IDI_8 => { count => 0 , prefix=>"_WO" },
        D2D      => { count => 0 , prefix=>"_WO" },
        IOC      => { count => 0 , prefix=>"_WO" },
        GTC_0     => { count => 0 , prefix=>"_WO" },
        GT_0     => { count => 0 , prefix=>"_WO" },
        GT_1     => { count => 0 , prefix=>"_WO" },
        GT_2     => { count => 0 , prefix=>"_WO" },
        GT_3     => { count => 0 , prefix=>"_WO" },
        MEDIA_0  => { count => 0 , prefix=>"_WO" },
        MEDIA_1  => { count => 0 , prefix=>"_WO" },
        IAX      => { count => 0 , prefix=>"_WO" },
        NOC_IDI_0 => { count => 0 , prefix=>"_WO" }, 
        NOC_IDI_1 => { count => 0 , prefix=>"_WO" }, 
        NOC_IDI_2 => { count => 0 , prefix=>"_WO" }, 
        NOC_IDI_3 => { count => 0 , prefix=>"_WO" }, 
        NOC_IDI_4 => { count => 0 , prefix=>"_WO" }, 
        NOC_IDI_5 => { count => 0 , prefix=>"_WO" },
    },
    MemRd_chs => { # Give src_ch_tc to GT cxl.log opcodes of WOWrInv and WOWrInvF using merge_ns_write_channels()
        GT_IDI_0 => { count => 0 , prefix=>"_RO" }, #
        GT_IDI_1 => { count => 0 , prefix=>"_RO" }, #
        GT_IDI_2 => { count => 0 , prefix=>"_RO" }, #
        GT_IDI_3 => { count => 0 , prefix=>"_RO" }, #
        GT_IDI_4 => { count => 0 , prefix=>"_RO" },
        GT_IDI_5 => { count => 0 , prefix=>"_RO" },
        GT_IDI_6 => { count => 0 , prefix=>"_RO" },
        GT_IDI_7 => { count => 0 , prefix=>"_RO" },
        D2D      => { count => 0 , prefix=>"_RO" },
        IOC      => { count => 0 , prefix=>"_RO" },
        GTC_0     => { count => 0 , prefix=>"_RO" },
        GT_0     => { count => 0 , prefix=>"_RO" },
        GT_1     => { count => 0 , prefix=>"_RO" },
        GT_2     => { count => 0 , prefix=>"_RO" },
        GT_3     => { count => 0 , prefix=>"_RO" },
        MEDIA_0  => { count => 0 , prefix=>"_RO" },
        MEDIA_1  => { count => 0 , prefix=>"_RO" },
        IAX      => { count => 0 , prefix=>"_RO" },
        NOC_IDI_0 => { count => 0 , prefix=>"_RO" }, 
        NOC_IDI_1 => { count => 0 , prefix=>"_RO" }, 
        NOC_IDI_2 => { count => 0 , prefix=>"_RO" }, 
        NOC_IDI_3 => { count => 0 , prefix=>"_RO" }, 
        NOC_IDI_4 => { count => 0 , prefix=>"_RO" }, 
        NOC_IDI_5 => { count => 0 , prefix=>"_RO" },
    },
};
local @axi_file_scbd_l = ();
local @gtcxl_file_scbd_l = ();
local $cfi_trk_file_scbd;
local $ufi_trk_file_scbd;
local $mcc_preloader_file_scbd_l;

$e2e_read_ch_scan_count = 0;
$e2e_read_compare_count = 0;
$e2e_read_retry_count = 0;
$e2e_total_write_retry_count = 0;
$e2e_refmem_update_count = 0;
$e2e_refmem_reverse_count = 0;
$e2e_write_compare_count = 0;

$all_pcie_link_write_byte_stream_l = [];
$all_WRC_pcie_link_write_byte_stream_l = [];
$all_pcie_link_read__byte_stream_l = [];
%all_pcie_link_write_byte_stream_l_use_hash = ();

# Test pass only if it failed.
$is_fail_2_pass = 0;

# Ensure that test has MCTO stimuli.
$has_OPIO_MCTP=0;

# 
$is_parse_OPIO_LINK_file = 1;

$IOMMU_SAI = 0x18; # SAI from transaction initated by IOMMU (like page walk).
$CSME_SAI = 0x20; # SAI from transaction CSME - It can access IMR

$CSME_SRCID = 0x482; # I can access IMR
 
$msi_range = {BASE=>0xFEE00000,LIMIT=>0xFFEFFFFF,MASK=>0xFFFFFFFFFF};
$iocce_mktme_range = undef;
$mc_abort_range = {BASE=>0xc0000,LIMIT=>0xc003F,MASK=>0xFFFFFFFF_FFFFFFFF};
$low_non_msi_range = {BASE=>0x00000000,LIMIT=>0xFEDFFFFF,MASK=>0xFFFFFFFFFF};
$high_non_msi_range = {BASE=>0xFEF00000,LIMIT=>0xFFFFFFFFFF,MASK=>0xFFFFFFFFFF};
@not_dram_ranges_l = ();     # ranges that does excluded from DRAM for IDI transactions
@IOP_not_dram_ranges_l = (); # ranges that does excluded from DRAM for IOP transactions
@mmio_ranges_l = (); # ranges that does excluded from DRAM for IOP transactions
@prmrr_ranges_l = (); @lnl_prmrr_ranges_l = ();
$global_remap_range = undef;
$sm_TOLUD_addr = undef;
$sm_TOUUD_addr = undef;
@pep_host_direct_range_l = ();
@pep_host_dma_range_l = ();
$my_PWD = getcwd();

%convert_8bit_sai_to_6bit = (
    0x1 => 0x0,
    0x3 => 0x1,
    0x5 => 0x2,
    0x7 => 0x3,
    0x9 => 0x4,
    0xB => 0x5,
    0xD => 0x6,
    0xF => 0x7,
    0x1E => 0xF,
    0x46 => 0x23,
    0x10 => 0x8,
    0x5E => 0x2F,
    0x58 => 0x2C,
    0x50 => 0x28,
    0x68 => 0x34,
    0x16 => 0xB,
    0x1C => 0xE,
    0x24 => 0x12,
    0x26 => 0x13,
    0x12 => 0x9,
    0x2A => 0x15,
    0x18 => 0xC,
    0x30 => 0x18,
    0x54 => 0x2A,
    0x56 => 0x2B,
    0x32 => 0x19,
    0x3E => 0x1F,
    0x14 => 0xA,
    0xB2 => 0x3F,
    0x0 => 0x3F,
    0x20 => 0x10,
    0x22 => 0x11,
    0x2C => 0x16,
    0x1A => 0xD,
    0x34 => 0x1A,
    0x74 => 0x3A,
    0x38 => 0x1C,
    0x40 => 0x20,
    0x42 => 0x21,
    0x44 => 0x22,
    0x48 => 0x24,
    0x52 => 0x29,
    0x62 => 0x31,
    0x4C => 0x26,
    0x72 => 0x39,
    0x76 => 0x3B,
    0x70 => 0x38,
    0x5C => 0x2E,
    0x6E => 0x37,
    0x36 => 0x1B,
    0x4A => 0x25,
    0x4E => 0x27,
    0x5A => 0x2D,
    0x66 => 0x33,
    0x28 => 0x14,
    0x2E => 0x17,
    0x3A => 0x1D,
    0x3C => 0x1E,
    0x60 => 0x30,
    0x64 => 0x32,
    0x6A => 0x35,
    0x6C => 0x36,
    0x78 => 0x3C,
    0x7A => 0x3D,
    0x7C => 0x3E,
);

%ch_name_h = ();
$ch_name_counter = 0;
@ch_name_l = ("bad_ch_name");
@ch_cache_l = ([undef,undef],[undef,undef],[undef,undef]);
$ch_cache_idx = 0;

sub addr_str($) {
    return sprintf("%012x",$_[0]);
}

sub hash_str(@) {
    my ($h,$pre) = @_;
    my $str = ""; 
    my $count=30; # limit has elements to 30
    for my $k (sort keys %$h) {
        if($k=~/^(BASE|MASK|LIMIT|address|addr|snp_address|address2|address1|hbo_address|BusWidthMask|beg_virt_addr|beg_addr|end_addr)$/) { 
            $str.= sprintf("%s %s=> 0x%x\n",$pre,$k,$h->{$k}) 
        } elsif($k eq "shash_index") {
            $str.= sprintf("%s %s=> %1d offset %1d\n",$pre,$k,$h->{$k}&0xFFFFFFFF,get_word2($h->{$k})) 
        } elsif($k eq "join_l" and ref($h->{$k}) eq "ARRAY" and $h->{address}) { my $i=0;
            for my $shash_index (@{$h->{$k}}) {
                $str.= sprintf("%s %s[%2d]=> addr=%s..%s shash_index=%1d\n",$pre,$k,$i++,addr_str($h->{address}+get_word2($shash_index)+get_word3($shash_index)),addr_str($h->{address}+get_word2($shash_index)),$shash_index&0xFFFFFFFF) 
            }
        } elsif($k=~/^(src_ch_rd|src_ch_tc|src_ch)$/ && $h->{$k}==int($h->{$k})) { 
            $str.= sprintf("%s %s=> %s\n",$pre,$k,$ch_name_l[$h->{$k}]) 
        } else { 
            $str .= obj_str($h->{$k},"$pre $k=> "); 
        } 
        if(!--$count) { last };
    }
    return $str;
}
sub trans_str($) {
    my $rec_ptr = $_[0];
    my $line = defined($rec_ptr->{line}) ? $rec_ptr->{line} : $rec_ptr->{parent}->{line};
    my $cmd = (defined($rec_ptr->{cmd}) ? "cmd=$rec_ptr->{cmd} " : ""); 
    my $snp_cmd = (defined($rec_ptr->{snp_cmd}) ? "snp_cmd=$rec_ptr->{snp_cmd} " : ""); 
    my $bogus = (defined($rec_ptr->{bogus}) ? "bogus=$rec_ptr->{bogus} " : ""); 
    return sprintf("address=".addr_str($rec_ptr->{address})." data=$rec_ptr->{data} ${cmd}${snp_cmd}${bogus}line=$line");
}

sub obj_str(@) {
    my ($p,$pre) = @_;
    my $str;
    if(ref($p) eq "ARRAY") {
        my $max = 1*@$p;
        $str.=$pre."ARRAY elemets=$max\n";
        my $i=0;
        if($max>5) { $max=5; }
        for(@$p) {
            $str .= obj_str($_,"$pre [$i] ");
            if($i++ > $max) { last }
        }
        if($max < @$p) {
            $str .= "$pre....\n";
        }
    } elsif(ref($p) eq "HASH") {
        my $count=0; for(keys %$p) { $count++; }
        if(defined($p->{address}) and defined($p->{data}) and (defined($p->{tick}) or defined($p->{tick_beg}))) { 
            my $s = trans_str($p);
            chomp $s; $s = substr($pre.$s,0,200);
            $str .= $s."\n"; 
        } else { 
            $str.=$pre."HASH elemets=$count\n";
            $str .= hash_str($p,$pre); 
       }
    } elsif(!defined($p)) {
        $str .= $pre."undef\n";
    } else {
        $str .= $pre."$p\n";
    }
    return $str;
}

sub my_chomp($) {
    my $l=$_[0];
    chomp $l;
    return $l;
}

# This function gives unquie id number to each channel
sub get_ch_id($) {
    # Try ti search in the cache
    #
    for my $ch (@ch_cache_l) {
        if($ch->[0] eq $_[0]) {
            return $ch->[1];
        }
    }
    
    # If not found in cache, try in hash;
    my $id = $ch_name_h{$_[0]};
    if(defined($id)) { 
        # Put it in tha cache.
        $ch_cache_l[$ch_cache_idx]->[0] = $_[0];
        $ch_cache_l[$ch_cache_idx]->[1] = $id;
        if(++$ch_cache_idx>=@ch_cache_l) { $ch_cache_idx=0; }
        return $id; 
    } else { 
        $ch_name_h{$_[0]} = 1*@ch_name_l;
        push @ch_name_l,$_[0];
        return (1*@ch_name_l-1);
    }
}

sub append_ch_id($$) {
    get_ch_id($ch_name_l[$_[0]].$_[1]);
}

sub die_ERROR($) {

    if($debug_skip_err) {
        # This is for debug with -ptkdb. You can make the script not exit by  $debug_skip_err=1
    } elsif($use_die_for_error) {
        die(join("",@_));
    } elsif($do_e2e_warning_only) {
        my @str_l; 
        for(@_) { my $s = $_; $s=~s/ERROR/ERR2WARN/g; push @str_l,$s; }
        print "die ERR2WARN: ",@str_l,"\n";
        $exit_code = 1;
        ending();
    } else {
        print "die ERROR: ",@_,"\n";
        $exit_code = 1;
        ending();
    }
}

sub print_ERROR($) {
    if($do_e2e_warning_only) {
        my @str_l; 
        for(@_) { my $s = $_; $s=~s/ERROR/ERR2WARN/g; push @str_l,$s; }
        print @str_l;
    } else {
        print @_;
    }
}

sub script_timeout_chk() {
    my $script_time = time() - $script_start_time;
    if($script_time+$script_start_time>$script_max_time && !$script_timeout) {
        $script_timeout = 1;
        if($skip_timeout_err) {
            print("060 WARNING: Script run $script_time and overflow timeout!\n");
        } else {
            $exit_code = 1;
            print_ERROR("060 ERROR: Script run $script_time and overflow timeout!\n");
        }
    }
    #print "Time:$script_time\n";
    return $script_time;
}

my @save_ARGV = @ARGV;

my $e2e_args_fd;
if(open_gz(\$e2e_args_fd,"soc_e2e_args.txt",0)) {
    while(<$e2e_args_fd>) {
        /^-/ or last;
        chomp;
        unshift @ARGV,$_;
    }
    close $e2e_args_fd;
}

# This loop parse command line switches and convert them to program variables
while(+@ARGV) {
    if($ARGV[0] =~ /-debug=(\d+)/) {
        $debug = $1;
    } elsif($ARGV[0] eq "-debug") {
        $debug = 1000;
    } elsif($ARGV[0] eq "-ver") {
        printf "sos_e2e_checker.pl version %s. Written by eyal.sinuani\@intel.com\n",$version;
        exit(0);
    } elsif($ARGV[0] eq "-h" || $ARGV[0] eq "--help") {
        printf "\nsos_e2e_checker.pl version %s. Written by eyal.sinuani\@intel.com\n",$version;
        print $e2e_help;
        exit(0);
    } elsif($ARGV[0] eq "-skip_OPIO_LINK") { $is_parse_OPIO_LINK_file=0;
    } elsif($ARGV[0] eq "-skip_TBTDMA_PSF") { $skip_TBTDMA_PSF=1;
    } elsif($ARGV[0] eq "-skip_TBTDMA_PSF=0") { $skip_TBTDMA_PSF=0;
    } elsif($ARGV[0] eq "-skip_TBTDMA_PSF=1") { $skip_TBTDMA_PSF=1;
    } elsif($ARGV[0] eq "-skip_iommu_no_conv=0") { $skip_iommu_no_conv=0;
    } elsif($ARGV[0] eq "-skip_iommu_no_conv=1") { $skip_iommu_no_conv=1;
    } elsif($ARGV[0] eq "-skip_e2e_write_chk") { $skip_e2e_write_chk=1;
    } elsif($ARGV[0] eq "-skip_e2e_write_chk=0") { $skip_e2e_write_chk=0;
    } elsif($ARGV[0] eq "-skip_e2e_write_chk=1") { $skip_e2e_write_chk=1;
    } elsif($ARGV[0] eq "-skip_e2e_write_chk=undef") { $skip_e2e_write_chk=undef;
    } elsif($ARGV[0] eq "-skip_e2e_axi_write_chk=0") { $skip_e2e_axi_write_chk=0;
    } elsif($ARGV[0] eq "-skip_e2e_axi_write_chk=1") { $skip_e2e_axi_write_chk=1;
    } elsif($ARGV[0] eq "-skip_axi_compare_timing_chk=1") { $argv{skip_axi_compare_timing_chk}=1;
    } elsif($ARGV[0] eq "-skip_bad_uri_filter=0") { $skip_bad_uri_filter=0;
    } elsif($ARGV[0] eq "-skip_bad_uri_filter=1") { $skip_bad_uri_filter=1;
    } elsif($ARGV[0] eq "-fast_mode=0") { $e2e_fast_mode=0;
    } elsif($ARGV[0] eq "-fast_mode=1") { $e2e_fast_mode=1;
    } elsif($ARGV[0] eq "-skip_iop_D_mem_chk=0") { $skip_iop_D_mem_chk=0;
    } elsif($ARGV[0] eq "-skip_iop_D_mem_chk=1") { $skip_iop_D_mem_chk=1;
    } elsif($ARGV[0] eq "-check_iommu_msi_conv=0") { $check_iommu_msi_conv=0;
    } elsif($ARGV[0] eq "-check_iommu_msi_conv=1") { $check_iommu_msi_conv=1;
    } elsif($ARGV[0] eq "-skip_e2e_read_chk=1") { $skip_e2e_read_chk=1;
    } elsif($ARGV[0] =~ /^-lnl_vpu_btrs_ver=(\d+)$/) { $lnl_vpu_btrs_ver=$1;
    } elsif($ARGV[0] eq "-skip_e2e_read_chk=0") { $skip_e2e_read_chk=0;
    } elsif($ARGV[0] eq "-skip_e2e_read_chk=undef") { $skip_e2e_read_chk=undef;
    } elsif($ARGV[0] eq "-skip_group_trans_bytes=1") { $argv{skip_group_trans_bytes} = 1; $argv{skip_group_ref_mem} = 1;  $argv{skip_group_reads} = 1;
    } elsif($ARGV[0] eq "-skip_group_trans_bytes=0") { $argv{skip_group_trans_bytes} = 0;
    } elsif($ARGV[0] eq "-skip_group_ref_mem=1") { $argv{skip_group_ref_mem} = 1; $argv{skip_group_reads} = 1;
    } elsif($ARGV[0] eq "-skip_group_ref_mem=0") { $argv{skip_group_trans_bytes} = 0; $argv{skip_group_ref_mem} = 0;
    } elsif($ARGV[0] eq "-skip_group_reads=1") {  $argv{skip_group_reads} = 1;
    } elsif($ARGV[0] eq "-skip_group_reads=0") {  $argv{skip_group_trans_bytes} = 0; $argv{skip_group_ref_mem} = 0; $argv{skip_group_reads} = 0;
    } elsif($ARGV[0] eq "-split_reads_dump=1") { $argv{split_reads_dump} = 1;
    } elsif($ARGV[0] eq "-skip_PAM_range=1") { $argv{skip_PAM_range} = 1;
    } elsif($ARGV[0] eq "-skip_PAM_range=0") { $argv{skip_PAM_range} = 0;
    } elsif($ARGV[0] eq "-e2e_write_chk_use_uri=1") { $e2e_write_chk_use_uri=1;
    } elsif($ARGV[0] eq "-e2e_write_chk_use_uri=0") { $e2e_write_chk_use_uri=0;
    } elsif($ARGV[0] eq "-skip_e2e_pcie_read_chk=1") { $skip_e2e_pcie_read_chk=1;
    } elsif($ARGV[0] eq "-skip_e2e_pcie_read_chk=0") { $skip_e2e_pcie_read_chk=0;
    } elsif($ARGV[0] eq "-create_cmi_preload=0") { $create_cmi_preload=0;
    } elsif($ARGV[0] eq "-create_cmi_preload=1") { $create_cmi_preload=1;
    } elsif($ARGV[0] eq "-skip_CL_recheck=1") { $skip_CL_recheck=1;
    } elsif($ARGV[0] =~ /-debug_address=(\S+)/) { $argv{debug_address}=$1;
    } elsif($ARGV[0] =~ /-run_in_failed_test=(\S+)/) { $run_in_failed_test=$1;
    } elsif($ARGV[0] =~ /-debug_start_time=(\S+)/) { $debug_start_time=1*$1;
    } elsif($ARGV[0] =~ /-debug_ch_idx1=(\S+)/) { $debug_ch_idx1=1*$1;
    } elsif($ARGV[0] =~ /-e2e_write_retry_count=(\d+)/) { $e2e_write_retry_count=1*$1;
    } elsif($ARGV[0] eq "-skip_ACF_IDI_chk=0") { $skip_ACF_IDI_chk=0;
    } elsif($ARGV[0] eq "-skip_ACF_IDI_chk=1") { $skip_ACF_IDI_chk=1;
    } elsif($ARGV[0] eq "-skip_iop_cmi_log=0") { $skip_iop_cmi_log=0;
    } elsif($ARGV[0] eq "-skip_iop_cmi_log=1") { $skip_iop_cmi_log=1;
    } elsif($ARGV[0] eq "-use_iop_cmi_log=0") { $use_iop_cmi_log=0;
    } elsif($ARGV[0] eq "-use_iop_cmi_log=1") { $use_iop_cmi_log=1;
    } elsif($ARGV[0] eq "-skip_if_non_snoop=0") { $argv{skip_if_non_snoop}=0;
    } elsif($ARGV[0] eq "-skip_if_non_snoop=1") { $argv{skip_if_non_snoop}=1;
    } elsif($ARGV[0] eq "-skip_PRD_opcode=0") { $argv{skip_PRD_opcode}=0;
    } elsif($ARGV[0] eq "-skip_PRD_opcode=1") { $argv{skip_PRD_opcode}=1;
    } elsif($ARGV[0] eq "-skip_mmio_chk=0") { $argv{skip_mmio_chk}=0;
    } elsif($ARGV[0] eq "-skip_mmio_chk=1") { $argv{skip_mmio_chk}=1;
    } elsif($ARGV[0] eq "-do_e2e_warning_only=0") { $do_e2e_warning_only=0;
    } elsif($ARGV[0] eq "-do_e2e_warning_only=1") { $do_e2e_warning_only=1;
    } elsif($ARGV[0] eq "-lnl_use_mc_vs_hbomc=1") { $lnl_use_mc_vs_hbomc=1;
    } elsif($ARGV[0] eq "-skip_pep_svt_file=0") { $skip_pep_svt_file=0;
    } elsif($ARGV[0] eq "-skip_pep_svt_file=1") { $skip_pep_svt_file=1;
    } elsif($ARGV[0] =~ /-skip_timeout_err=([01])/) { $skip_timeout_err=$1;
    } elsif($ARGV[0] eq "-skip_axi_file=0") { $skip_axi_file=0;
    } elsif($ARGV[0] eq "-skip_axi_file=1") { $skip_axi_file=1;
    } elsif($ARGV[0] eq "-skip_gtcxl_file=0") { $skip_gtcxl_file=0;
    } elsif($ARGV[0] eq "-skip_gtcxl_file=1") { $skip_gtcxl_file=1;
    } elsif($ARGV[0] eq "-skip_uri_chk=0") { $skip_uri_chk=0;
    } elsif($ARGV[0] eq "-skip_uri_chk=1") { $skip_uri_chk=1;
    } elsif($ARGV[0] =~ "-rerun=(.*)") { $argv{rerun_failure_log}=$1;
    } elsif($ARGV[0] eq "-skip_OPIO_LINK_err=0") { $skip_OPIO_LINK_err=0;
    } elsif($ARGV[0] eq "-skip_OPIO_LINK_err=1") { $skip_OPIO_LINK_err=1;
    } elsif($ARGV[0] eq "-skip_OPIO_LINK_err=undef") { $skip_OPIO_LINK_err=undef;
    } elsif($ARGV[0]=~m/^-nbace/) { $is_nbace=1;
    } elsif($ARGV[0]=~m/^-dump_time(|=1)$/) { $is_dump_time=1;
    } elsif($ARGV[0]=~m/^-(do_e2e_read_channel|src_ch_tc|src_ch)=([\w,]+)/) { 
        my @a = split /,/,$2;
        $do_e2e_read_channel = {};
        for(@a) { $do_e2e_read_channel->{$_}=1; }
    } elsif($ARGV[0]=~m/^(-skip_e2e_read_channel)=([\w,:]+)/) { 
        my @a = split /[:,]/,$2;
        for(@a) { $skip_e2e_read_channel->{$_}=1; }
    } elsif($ARGV[0]=~m/^-use_write_update_file=(\S+)/) { $use_write_update_file=$1;
    } elsif($ARGV[0]=~m/^-gen_write_update_file=(\S+)/) { $gen_write_update_file=$1;
    } elsif($ARGV[0]=~m/^-use_refmem_recalc=(\w+)/) { $use_refmem_recalc=$1;
    } elsif($ARGV[0] eq "-fail_2_pass") { $is_fail_2_pass=1;
    } elsif($ARGV[0] eq "-has_OPIO_MCTP") { $has_OPIO_MCTP=1;
    } elsif($ARGV[0] eq "-skip_IOP_to_mcc_check") { $skip_IOP_to_mcc_check=1;
    } elsif($ARGV[0] eq "-cd") { chdir $ARGV[1] or die "186 ERROR: Can not cd $ARGV[1]"; $my_PWD = $ARGV[1]; shift @ARGV;
    } elsif($ARGV[0] eq "-log") { 
        open(STDOUT,">>$ARGV[1]") or die_ERROR("063 ERROR: Can not open log file $ARGV[1]");
        open(STDERR,">>$ARGV[1]") or die_ERROR("064 ERROR: Can not open log file $ARGV[1]");
        shift @ARGV;
    } elsif($ARGV[0]=~/^-timeout=(\d+)$/) { $script_timeout_param=$1; $script_max_time = $script_start_time+$1;
    } else {
    }    

    shift(@ARGV);
}    

if(!-e ($systeminit_file = "systeminit/systeminit.dut_cfg") and !-e ($systeminit_file = "systeminit/systeminit.dut_cfg.gz") and
   !-e ($systeminit_file = "test_cfg/systeminit.dut_cfg") and !-e ($systeminit_file = "test_cfg/systeminit.dut_cfg.gz")) {
} else {
    $systeminit_file_exist = 1;
}

$skip_DPR_changing_chk = 1 if !defined($skip_DPR_changing_chk);

$is_postsim_good = 999; # when there are severe error in the acerun.lo like hang, don't run the e2e checker.
$is_postsim_status = 999; # when there are severe error in the acerun.lo like hang, don't run the e2e checker.
#$is_acerun_good = 999; # when there are severe error in the acerun.lo like hang, don't run the e2e checker.
if(-e 'postsim.log' or -e 'postsim.log.gz') { $is_postsim_good = system('zgrep -q -e "^[0-9].*UVM_FATAL.*Explicit timeout of.*indicating a probable testbench issue" -e "^[0-9].*Error-.NOA" -e "UVM_FATAL.*PCODE MCA detected" postsim.log'); }
if(-e 'postsim.log' or -e 'postsim.log.gz') { $is_postsim_status = system('zgrep -q -e "^ *Status *: *FAIL" postsim.log'); }
#if(-e 'acerun.log') { $is_acerun_good = system('grep -q -e "UVM_FATAL.*Explicit timeout of.*indicating a probable testbench issue" -e "UVM_ERROR.*is another transaction with the same identification details" acerun.log'); }
$skip_uri_chk = 1 unless defined($skip_uri_chk); # fixme:temporarily uri check until it will be stable in lnl
$do_e2e_warning_only = 1 unless defined($do_e2e_warning_only) or !length($ENV{"RESULTS_PATH"}) 
    or (!($ENV{"TEST_CMDLINE"}=~/soc_vpu_imr_access_test|soc_vpu_mktme_abort_test/) and $is_postsim_good )
    or ($ENV{"RESULTS_PATH"}=~/\/level0\.list/); 
if(defined($skip_timeout_err)) {
} elsif(!length($ENV{"RESULTS_PATH"})) {
    # in non regression runs still fail on timeout
} elsif($ENV{"RESULTS_PATH"}=~/\/level0\.list/) {
    # in level0 test still fail on timeout unless it is Elad's pv test
} elsif($gen_write_update_file and (%$do_e2e_read_channel)[0]=~/^xxx/) {
    # if we are running only write check in regression, keep the timeout error
    # this because i assume this stage will be short.
    #if(($ENV{"TEST_CMDLINE"}=~/\/pv\/soc_pv_test/)) {
    #    $skip_timeout_err = 1; # still mask timeout failures in pv tests
    #}
    #if( ($ENV{"TEST_CMDLINE"}=~/\/soc_hbo_alive_test/)
    #    and $systeminit_file_exist and !system("zgrep -q '/SOC_HBO_RANDOMIZE_DATA_M *:= *0' $systeminit_file")
    #) {
    #    $skip_timeout_err = 1; # still mask timeout failures in soc_hbo_alive_test that writes multiple time with the same address and data
    #}
} else {
    #$skip_timeout_err = 1; #mask timeout failures in the regression
}
#print "Set skip_timeout_err=$skip_timeout_err\n";

if(!defined($script_timeout_param)) {
    if(defined($ENV{SOC_E2E_TIMEOUT}) and $ENV{SOC_E2E_TIMEOUT}=~/^(\d+)$/) {
        $script_timeout_param = $1;
        push @save_ARGS,"-timeout=$1";
    } else {
        $script_timeout_param = 2989;
    }
}
$script_max_time = $script_start_time+$script_timeout_param;
$script_timeout = 0;

my $e2e_command_line = "Command line: ".join(" ",@save_ARGV)."\n";
if($debug) {
    print $e2e_command_line;
}

if(-f "sequence_trk.log" || -f "sequence_trk.log.gz") {
    if(!defined($skip_pep_svt_file) && (my_grep_gz("sequence_trk.log",[" pciess_ep_read_dma_seq"," pciess_ep_write_dma_seq"," soc_pciess_ep_linked_list_dma_seq"," pciess_ep_write_ll_dma_seq"," pciess_ep_read_ll_dma_seq"])==1)) {
        $skip_pep_svt_file = 1;    
        print "WARNING: set skip_pep_svt_file=1 because there are unsupported pep dma seqeunces in the test\n" if $debug>=1;
    }
    if(my_grep_gz("sequence_trk.log",[" soc_sippcie2_aer_ucerr_interrupt_seq"," pciex4_dpc_sci_smi_seq"," pciex4_global_err_reporting_seq"])==1) {
        print "WARNING: Skip checking because there are unsupport RKL PEG err seqeunces in the test\n" if $debug>=1;
        exit 0;
    }
}

if(!defined($skip_pep_svt_file)) { 
    $skip_pep_svt_file = 0;  # By default enable PEP pcie_vip_trans checking.
}

# Parse bit 
sub big_hex($) {
    no warnings;
    return hex($_[0]);
}

sub check_64int_support() {
    my $int64 = 1;
    $int64<<=31;
    $int64<<=31;
    $int64<<=1;
    if(!$int64) {
        die_ERROR("064 ERROR: perl doe not support int64");
    }
}

sub get_field($$$) {
    return (($_[0]>>$_[2]) & ((1<<($_[1]-$_[2]+1))-1));
}

sub get_word2($) { (($_[0]&0xFFFF_00000000)>>32) }

sub get_word3($) { (($_[0]&0xFFFF0000_00000000)>>48) }

sub fix_little_indian($) {
    my @data_l = (split /[\s_]+/,$_[0]);
    my $str;
    my $size = 1*@data_l;
    for(my $i=0 ; $i<$size ; $i+=1) {
        my $d = $data_l[$size-$i-1];
        if($d=~/-/) { next }
        $d = hex($d);
        $d = (($d & 0x000000FF)<<24) | (($d & 0x0000FF00)<<8) | (($d & 0x00FF0000)>>8) | (($d & 0xFF000000)>>24);
        if($i>0) { $str .= "_"; }
        $str .= sprintf("%08x",$d);
    }
    return $str;
}

sub regression_report($$) {
    my $pass = $_[0];
    my $run_time = $_[1];
    my $fd;

    if($cpu_proj eq "lnl" and length($ENV{RESULTS_PATH}) and -d $ENV{RESULTS_PATH}) {
        if(open($fd,">>$ENV{RESULTS_PATH}/e2e.report")) {
            my $str = ($pass?"PASS: ":"FAIL: ") . $ENV{PWD}."\n";
            for("RESULTS_PATH","TEST_WORK_AREA","TEST_CMDLINE","TEST_RESULT_PATH") {
                $str.="$_=$ENV{$_}\n";
            }
            $str .= "run_time: $run_time\n";
            $str .= "postsim: ".($is_postsim_good?"Unknown":"FAIL")."\n";
            $str .= "postsim status: ".($is_postsim_status?"Unknown":"FAIL")."\n";
            $str .= "\n";
            print $fd $str;
            close $fd;
        }
    }

    1;
}

sub vim_match($$) {
    my $rec_ptr = shift;
    my $i = shift;
    my $uri = ($rec_ptr->{LID} or $rec_ptr->{uri});
    (length($uri)>3 ? ":syn match c$i /.*\\<$uri\\>.*/\n" : "");
}

sub create_debug_rc_file() {
    if($log_err_data->{rec}) {
        my $fd; my $match_i;
        if(open($fd,">$ENV{HOME}/e2e.rc")) {
            print $fd ":set noic\n";
            print $fd ":hi c1 guifg=red\n:hi c2 guifg=green\n:hi c3 guifg=yellow\n:hi c4 guifg=purple\n:hi c5 guifg=orange\n:hi c6 guifg=magenta\n:hi c7 guifg=brown\n";
            my $addr  = (($log_err_data->{rec}->{address}>>4)&0xc);
            my $filter  = sprintf("%1x[%1x%1x%1x%1x][0-9a-f]",($log_err_data->{rec}->{address}>>8),$addr,$addr+1,$addr+2,$addr+3);
            print $fd ":v/$filter * | /d\n";
            print $fd vim_match($log_err_data->{rec}->{parent},++$match_i);
            if($#{$log_err_data->{wr_l}}>=0) {
                for my $rec_ptr2 (reverse @{$log_err_data->{wr_l}}) {
                    print $fd vim_match($rec_ptr2->{parent},++$match_i);
                    if($match_i>5) { last }
                }
            }
            my $uri = ($log_err_data->{rec}->{parent}->{LID} or $log_err_data->{rec}->{parent}->{uri});
            print $fd "/$uri\\>\n" if $uri;
            close $fd;
        }
        my @file_l = ();
        for my $scbd ($idi_file_scbd,$cxl_idi_file_scbd,$cfi_trk_file_scbd) {
            if(is_scbd_exists($scbd)) {
                push @file_l,$scbd->{filename};
            }
        }
        print STDERR "gvim -p @file_l";
    }
}

sub rerun_failure_parms($) {
    my $filename = shift;
    my $fd;
    if(open_gz(\$fd,$filename,0)) {
        while(<$fd>) {
            if(index($_,"035 ERROR")>=0) {
                if(/035 ERR.* address=(\w+).* data=(\w+)/) {
                    $argv{rerun_failure_address} = big_hex($1);
                    $debug = 3 unless $debug;
                    while(<$fd>) {
                        if(/^ *to rec2 src_ch_tc=(\w+)/) {
                            $do_e2e_read_channel->{$1}=1;
                            last;
                        }
                    }
                }
                last;
            }
        }
        close $fd;
    }
}

sub cl_data_cmp($$) {
    my $data1 = $_[0];
    my $data2 = $_[1];

    if(length($data1) != length($data2)) { 
        return 0; 
    }

    for (my ($i1)=(length($data1)); $i1>=0 ; $i1--) {
        my $ch1 = substr($data1,$i1,1);
        if($ch1 ne "x") { 
            if($ch1 ne substr($data2,$i1,1)) {
                return 0; 
            }
        }
    }

    return 1;
}

# FIXME: Maybe do this function in c to improve performance
sub merge_preload_cl_data($$) {
    my ($pres,$val) = @_;
    my $len = length($val);
    if(length($$pres) != $len) {
        die_ERROR("065 ERROR:  data string sizes does not match, hence I can not merge them. data1=$$pres data2=$val.");
    }
    for (my $i=0; $i<$len ; $i++) {
        my $ch = substr($val,$i,1);
        if($ch ne "x" && $ch ne " ") { substr($$pres,$i,1) = "x"; }
    }
    return 1;
}

# FIXME: Maybe do this function in c to improve performance
sub merge_two_cl_data($$) {
    my ($pres,$val) = @_;
    my $len = length($val);
    if(length($$pres) != $len) {
        die_ERROR("145 ERROR:  data string sizes does not match, hence I can not merge them. data1=$$pres data2=$val.");
    }
    for (my $i=0; $i<$len ; $i++) {
        my $ch = substr($val,$i,1);
        if($ch ne "x") { substr($$pres,$i,1) = $ch; }
    }
    return 1;
}

# FIXME: Maybe do this function in c to improve performance
sub is_contradicts_cl_data($$) {
    my ($pres,$val) = @_;
    my $len = length($val);
    if(length($pres) != $len) {
        die_ERROR("065 ERROR:  data string sizes does not match, hence I can not merge them. data1=$pres data2=$val.");
    }
    for (my $i=0; $i<$len ; $i++) {
        my $ch = substr($val,$i,1);
        my $ch2 = substr($pres,$i,1);
        if($ch ne "x" and $ch ne " " and $ch ne "-" and $ch2 ne "x" and $ch2 ne " " and $ch2 ne "-" and $ch ne $ch2) { return 1; }
    }
    return 0;
}

sub get_trans_addresses($) {
    my @address_l = ();
    my $rec_ptr = shift;
    my $data = $rec_ptr->{data};
    my $address = $rec_ptr->{address};
    my $max = length($rec_ptr->{data});
    for(my $i=0; $i<$max ; $i+=2) {
        if("xx" ne substr($data,-2-$i,2)) {
            push @address_l,$address;
        }
        $address += 1;
    }
    return @address_l;
}

check_64int_support();

sub is_scbd_exists($) {
    my $scbd = shift;
    if(defined($scbd) && defined($scbd->{filename})) {
        return 1;
    } else {
        return 0;
    }
}

sub open_gz($$$){
    #print "open processes ".`ps |wc -l`;
    my ($fd_ptr,$log_file_name,$is_die) = @_;
    my $filename;
    if(-e $log_file_name) { 
        $filename  = $log_file_name;
        if($log_file_name=~/\.gz$/) { $log_file_name = "zcat $log_file_name |"; }
    }
    elsif(-e "$log_file_name.gz") { $filename = "$log_file_name.gz"; $log_file_name = "zcat $log_file_name |"; }
    elsif($is_die) {
        die_ERROR("066 ERROR: Can not open file $log_file_name.");
    } else {
        return 0;
    }
    if(open($$fd_ptr,$log_file_name)) { return $filename; }
    elsif($is_die) { die_ERROR("067 ERROR: Can not open file $log_file_name."); }
    else { return 0; }
}

sub my_grep_gz($$) {
    my ($fname,$grep_l) = @_;
    my $fd;
    my $filename = open_gz(\$fd,$fname,0) or return 0;
    my $is_found=0;
    if($filename) {
        while(<$fd>) {
            for my $sz (@$grep_l) {
                if(index($_,$sz)>=0) { 
                    $is_found=1;
                    last;
                }
            }
        }
        close $fd;
        if($is_found) {
            print "grep $filename is TRUE\n" if $debug>=9;
            return 1;
        } else {
            print "grep $filename is FALSE\n" if $debug>=9;
            return 0;
        }
    }
    return undef;
}

sub scbd_tick_tunings($$) {
    my ($scbd,$tick_str) = @_;
    my $tick = 1.0*$tick_str;
    if($is_scbd_tick_tunings== 1 and defined($scbd->{last_tick_str})) {
        if( length($tick_str)>=(length($scbd->{last_tick_str})+3)
            and $scbd->{last_tick_str} > 0 && $tick >= $scbd->{last_tick_str}
            #this not correct#and $tick>=(($scbd->{last_tick_str})*1000)
            and $scbd->{tick_mul}>=1000
        ) {
            $scbd->{tick_mul} /= 1000;
        }
    } elsif($is_scbd_tick_tunings==-1 and defined($scbd->{last_tick_str})) {
        if( length($tick_str)+3<=(length($scbd->{last_tick_str}))
            and $scbd->{last_tick_str} > 0 && $tick < $scbd->{last_tick_str}
        ) {
            $scbd->{tick_mul} *= 1000;
        }
    }
    $scbd->{last_tick_str} = $tick_str;
    return $scbd->{tick_mul} * $tick;
}

sub iommu_page_builder_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;

    my $last_BDF;
    my $last_Table = "";

    while(<$fd>) {
        if(/Device *BDF *: *(\w+)/) {
            $last_BDF = lc($1);
        } elsif(/(\w+) +Table +Start/) {
            $last_Table = $1;
            if(/Start +Addr *: +0*(\w+) +.*End +Addr *: *0*(\w+)/i) {
                $scbd->{IntTable}->{beg_addr} = big_hex($1);
                $scbd->{IntTable}->{end_addr} = big_hex($2);
            } else {
                die_ERROR("029 ERROR: Bad interrupt table");
            }
        } elsif(/virtual\s*Addr:/i) {
          if(/^\s*\|\s*sm_address\s+start\s*:\s*(\w+)\s*\|\s*sm_address\s*end\s*:\s*(\w+)\s*\|\s*start\s*virtual\s*Addr:\s*(\w+)\s*\|/i) {
            my %rec_page = (
                beg_addr => big_hex($1),
                end_addr => big_hex($2),
                beg_virt_addr => big_hex($3),
            );
            if(!defined($scbd->{$last_BDF}->{$rec_page{beg_virt_addr}})) {
                $scbd->{$last_BDF}->{$rec_page{beg_virt_addr}} = \%rec_page;
                if($debug>=2) {
                    print "IOMMU PAGE BDF: $last_BDF $_";
                }
            }
          } else {
            die_ERROR("068 ERROR: ");
          }
        } elsif(($last_Table eq "Interrupt") && (/^\| *[0-9A-F][0-9A-F]/i) && $check_iommu_msi_conv) {
            my @a = split(/ *\| */);
            my $addr = big_hex($a[1]);
            my $int_rec = { addr=>$addr, P=>$a[15] , DEST_ID =>bin2dec($a[5]),VECTOR=>bin2dec($a[7]), line=>$_, 
                SVT=>bin2dec($a[2]), SQ=>bin2dec($a[3]), SID=>bin2dec($a[4]), DLV=>bin2dec($a[10]), TRG=>bin2dec($a[11]),
                DST=>bin2dec($a[13]),RDH=>bin2dec($a[12]),};
            $scbd->{IntTable}->{$addr} = $int_rec;
            if($debug>=2) {
                print "IOMMU INTERRUPT ENTRY: $_";
            }
        }
    }

}

sub merge_ns_write_channels($$$) {
    #fixme: can inmprve the merge_ns_write_channels() by giving common channels to all the nc MemWr from all devices
    my $rec_ptr = $_[0];
    my $MemWr_chs = $_[1];
    my $tick_end_name = $_[2];
    if(!defined($MemWr_chs) or !defined($MemWr_chs->{prefix})) {
        die_ERROR("150 ERROR: MemWr_chs not defined for trans : ".trans_str($rec_ptr));
    }
    my $idx = 0;
    my $idx_found; 
    my $idx_found_tick = (~0>>1);
    my $idx_max = 1*@{$MemWr_chs->{ch_l}};
    for(; $idx < $idx_max; $idx+=1) {
        my $tick = $MemWr_chs->{ch_l}->[$idx]->{$tick_end_name};
        if(defined($tick) && $tick < $rec_ptr->{tick} && $tick < $idx_found_tick) {
            $idx_found = $idx;
            last; # $idx_found_tick = $tick;
        }
    }

    if(defined($idx_found)) {
        $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = $MemWr_chs->{ch_l}->[$idx_found]->{src_ch_tc};
        $MemWr_chs->{ch_l}->[$idx_found] = $rec_ptr;
    } else {
        $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch_tc},$MemWr_chs->{prefix}.sprintf("%04d",$MemWr_chs->{count}++));
        #add the nre channel to the list
        push (@{$MemWr_chs->{ch_l}},$rec_ptr);
    }
}

sub merge_ns_read_channels($$$) {
    #fixme: can inmprve the merge_ns_write_channels() by giving common channels to all the nc MemWr from all devices
    my $rec_ptr = $_[0];
    my $MemWr_chs = $_[1];
    my $tick_end_name = $_[2];
    if(!defined($MemWr_chs) or !defined($MemWr_chs->{prefix})) {
        die_ERROR("150 ERROR: MemWr_chs not defined for trans : ".trans_str($rec_ptr));
    }
    my $idx = 0;
    my $idx_found;
    my $idx_found_tick = (~0>>1);
    my $idx_max = 1*@{$MemWr_chs->{ch_l}};
    for(; $idx < $idx_max; $idx+=1) {
        my $tick = $MemWr_chs->{ch_l}->[$idx]->{$tick_end_name};
        if(defined($tick) && $tick < $rec_ptr->{tick} && $tick < $idx_found_tick) {
            $idx_found = $idx;
            last; # $idx_found_tick = $tick;
        }
    }

    if(defined($idx_found)) {
        $rec_ptr->{src_ch_rd} = $MemWr_chs->{ch_l}->[$idx_found]->{src_ch_rd};
        $MemWr_chs->{ch_l}->[$idx_found] = $rec_ptr;
    } else {
        $rec_ptr->{src_ch_rd} = append_ch_id($rec_ptr->{src_ch_rd},$MemWr_chs->{prefix}.sprintf("%04d",$MemWr_chs->{count}++));
        #add the nre channel to the list
        push (@{$MemWr_chs->{ch_l}},$rec_ptr);
    }
}

sub Reading_file_dump($) {
    my $filename = $_[0];
    my $time_str = "";
    if($is_dump_time) { $time_str = " time=".time(); }
    
    print "Reading file $filename$time_str\n";
}

sub iop_all_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;

    while(<$fd>) {
        if(/(ReqID +with +RC +entries +exists|Built +full +pages).*, *GPA *= *(\w+), *FourK_Page_ADDR *= *(\w+), *ReqID *= *(\w+)/) {
            my $BDF = sprintf("%04x",hex($4));
            my $beg_virt_addr = big_hex($2)& 0xFFFFFFFF_FFFFF000;
            my $rec_page;
            $rec_page->{beg_addr} = big_hex($3);
            $rec_page->{end_addr} = $rec_page->{beg_addr} + 0xFFF;
            $rec_page->{beg_virt_addr} = $beg_virt_addr;
            #$state = "read_ReqID";     
            if(!defined($scbd->{$BDF}->{$beg_virt_addr})) {
                $scbd->{$BDF}->{$beg_virt_addr} = $rec_page;
                if($debug>=2) {
                    printf "IOMMU PAGE BDF: $BDF beg_addr=%012x end_addr=%012x beg_virt_addr=%012x\n",$rec_page->{beg_addr},$rec_page->{end_addr},$rec_page->{beg_virt_addr};
                }
            }
        }
    }
    $scbd->{is_auto_pass_through} = 1;
}

sub iop_iommu_pages_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;

    my $last_BDF;
    my $pages_h;
    my $state = "IDLE";

    while(<$fd>) {
        if(/^\s*=============================/) {
            $state = "IDLE";     
            undef $pages_h;
        } elsif($state eq "IDLE" && /IOP IOMMU 4KByte of FourK pages built:/) {
            $state = "read_ReqID";     
            undef $pages_h;
        } elsif(($state eq "read_ReqID" || $state eq "read_GPA_pages") && /ReqID +num +(\d+) *: *Bus_num *= *(\w+) *, *Dev_num *= *(\w+) *, *Fun_num *= *(\w+)/i) {
            $last_BDF = sprintf("%02x%02x",hex($2),(hex($3)*8+hex($4)));
            $state = "read_GPA_pages";     
        } elsif($state eq "read_GPA_pages" && /Page +(\d+) +GPA +range *: *0x(\w+) *- *0x(\w+)/i) {
            $pages_h->{$1}->{beg_virt_addr} = big_hex($2);
            $pages_h->{$1}->{BDF} = $last_BDF;
        } elsif($state eq "read_GPA_pages" && /^FourK_PT_Entries/i) {
            $state = "read_FourK_PT_Entries";     
        } elsif($state eq "read_FourK_PT_Entries") {
          if(/^\|\s+\d+\s+\|/i) {
            my @a = split /\s*\|\s*/,$_;
            $pages_h->{$a[2]}->{beg_addr} = big_hex($a[4])*4096;
            $pages_h->{$a[2]}->{end_addr} = big_hex($a[4])*4096+0xFFF;
            my $BDF = $pages_h->{$a[2]}->{BDF};
            my $rec_page = $pages_h->{$a[2]};
            if(!defined($scbd->{$BDF}->{$rec_page->{beg_virt_addr}})) {
                $scbd->{$BDF}->{$rec_page->{beg_virt_addr}} = $rec_page;
                if($debug>=2) {
                    printf "IOMMU PAGE BDF: $BDF beg_addr=%012x end_addr=%012x beg_virt_addr=%012x\n",$rec_page->{beg_addr},$rec_page->{end_addr},$rec_page->{beg_virt_addr};
                }
            }
          } elsif(/^\s*|/) {
          } else {
            $state = "IDLE";
          }
        };
    }
    $scbd->{is_auto_pass_through} = 1;
}

sub parse_iommu_page_builder_file() {

    my $iop_iommu_scbd = { };


    opendir(D,".") or die_ERROR("069 ERROR: ");
    while($_ = readdir(D)) { 
        my $file_scbd = { };
        my $fd;
        my $filename = $_;
        my @pcie_inst_l;
        my $filename;
        if(/^sippcietbt_iommu_page_builder(\d*).out/ && -f $_) {
            my $inst = length($1) ? $1 : 0;
            push @pcie_inst_l,"pcie_link$inst";
            $filename = open_gz(\$fd,$_,0) or return 0;
  
            if($debug>=1) {
                print "Reading file $filename\n";
            }
            iommu_page_builder_file_reader($fd,$file_scbd);
            close $fd;
        } elsif(/^iop_all.log/) {
            $file_scbd = $iop_iommu_scbd;
            $filename = open_gz(\$fd,$_,0) or return 0;
  
            if($debug>=1) {
                print "Reading file $filename\n";
            }
            iop_all_file_reader($fd,$file_scbd);
            close $fd;
        } elsif(/^iop_iommu_pages_trk.out/) {
            $file_scbd = $iop_iommu_scbd;
            push @pcie_inst_l,"dmi_link","peg10_link","peg11_link","peg12_link","peg60_link","opio";
            $filename = open_gz(\$fd,$_,0) or return 0;
  
            if($debug>=1) {
                print "Reading file $filename\n";
            }

            if(!defined($skip_e2e_write_chk)) {
                $skip_e2e_write_chk = 1; #FIXME: Temporarily disable IOP IOMMU checking, because I can not relay on the data in this file. iop_iommu_pages_trk.out
                #FIXME: Need to complete it later.
            }

            if(!defined($skip_e2e_read_chk)) {
                $skip_e2e_read_chk = 1; #FIXME: Temporarily disable read check for all tests that do IOMMU.
                #FIXME: Need to complete it later.
            }
            iop_iommu_pages_file_reader($fd,$file_scbd);
            close $fd;
        }
        
        if(keys(%$file_scbd)) {
            for my $pcie_inst (@pcie_inst_l) {
                $tbtpcie_iommu_scbd_h->{$pcie_inst} = $file_scbd;
            }
        }
    }
    close D;
}

sub IOMMU_convert_address($$$) {
    my $iommu_scbd = shift;
    my $BDF = shift;
    my $virt_addr = shift;

    my $masked_virt_addr;
    my $rec_page_ptr;

    for my $mask_bits (12,21,30) {
        $masked_virt_addr = ($virt_addr>>$mask_bits)<<$mask_bits;
        $rec_page_ptr = $iommu_scbd->{$BDF}->{$masked_virt_addr};
        last if defined($rec_page_ptr);
    }

    if($rec_page_ptr) {
        return ($rec_page_ptr->{beg_addr} + ($virt_addr-$masked_virt_addr));
        $skip_e2e_read_chk = 1; #FIXME: Temporarily disable read check for all tests that do IOMMU.
    } else {
        if(!$skip_iommu_no_conv) {
            print_ERROR("014 ERROR: can not convert virt_addr=".addr_str($virt_addr)."\n");
            $exit_code = 1;
        }
        if($iommu_scbd->{is_auto_pass_through}) {
            return $virt_addr;
        } else {
            return undef;
        }
    }
}

sub lnl_iommu_file_read_record($) {
    local $_ = shift;
    if(!m/vtu_second_level_pt_e|vtu_second_level_pd_e|vtu_second_level_pdpt_e|vtu_first_level_pt_e|vtu_first_level_pd_e|vtu_first_level_pdpt_e/) { return undef; }

    my @a = split /\s*\|\s*/;

    my $page_type = $a[$idi_header_h{Page_Type}]; $page_type=~s/_en\w*$/_e/;
    my $page_shift = $iommu_page_size_conv->{$page_type}->{$a[$idi_header_h{SuperPage} or ($page_type=~/first/ ? $idi_header_h{SuperPageFL} : $idi_header_h{SuperPageSL})]} or return undef;

    my $page_data = $a[$idi_header_h{Page_Data}]; chomp($page_data);
    my $page_addr = big_hex($a[$idi_header_h{Page_Address}]);
    my $page_mask = (0xffff_ffffffff-((1<<$page_shift)-1));
    
    my $pos1 = length($page_data)-($page_addr&0x3f)*2; 
    my $pos2 = $pos1-16; 
    my $HPA;
    if($is_scalable_nested) {
        $HPA = big_hex($a[$idi_header_h{Req_Address}]) & $page_mask & $sys_addr_mask; # for nested mode I use only 1:1 remap
    } elsif($pos1>=16 and $pos1<=length($page_data)) {
        $HPA = big_hex(substr($page_data,$pos1-16,16)) & $page_mask & $sys_addr_mask;
    } else {
        return undef;
    }

    my %rec = (
        tick => $a[$idi_header_h{Time}],
        beg_virt_addr => big_hex($a[$idi_header_h{Req_Address}]) & $page_mask,
        beg_addr => $HPA,
        end_addr => $HPA+((1<<$page_shift)-1),
        BDF => $a[$idi_header_h{BDF}],
    );

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    return \%rec;
}

sub lnl_iommu_pages_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;
    local $iommu_page_size_conv = {
        vtu_second_level_pt_e => { NO_SP => 12, } , 
        vtu_second_level_pd_e => { SP_2Mega => 21, } ,
        vtu_second_level_pdpt_e => { SP_1Giga => 30, } ,
        vtu_first_level_pt_e => { NO_SP => 12, SP_2Mega => 21, SP_1Giga => 30, } ,
        vtu_first_level_pd_e => { SP_2Mega => 21, } ,
        vtu_first_level_pdpt_e => { SP_1Giga => 30, } ,
    };

    while(<$fd>) {
        my $rec_ptr; my $line = $_;
        $rec_ptr = &{$scbd->{read_record_func}}($line) or next;

        if(!defined($scbd->{$rec_ptr->{BDF}}->{$rec_ptr->{beg_virt_addr}})) {
            $scbd->{$rec_ptr->{BDF}}->{$rec_ptr->{beg_virt_addr}} = $rec_ptr;
            if($debug>=3) {
                printf "IOMMU PAGE BDF: $rec_ptr->{BDF} beg_addr=%012x end_addr=%012x beg_virt_addr=%012x\n",$rec_ptr->{beg_addr},$rec_ptr->{end_addr},$rec_ptr->{beg_virt_addr};
            }
        }

    }
    $scbd->{is_auto_pass_through} = 1;
}

sub parse_lnl_vtu_address_translation_trk($) {
    my ($fname) = @_;

    my $fd;
    local %idi_header_h = ();
    open_gz(\$fd,$fname,0) or return undef;
    my $filename = (-e "$fname.gz" ? "$fname.gz" : $fname);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    local $scbd = $ioc_iommu_file_scbd = { filename => $filename, };
    $scbd->{tick_mul} = $tick_mul*1000.0;
    $scbd->{read_record_func} = \&lnl_iommu_file_read_record;

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $idi_header_h{$_} = $i++; }
            last;
        }
    }

    lnl_iommu_pages_file_reader($fd,$scbd);
    close $fd;
    return $scbd
}

sub psf_prepare_data_and_be_string($$) {
    my $orig_data = shift;
    my $orig_be = shift;
    my $data = lc($orig_data);
    my $be = $orig_be;

    # Joins all data chucks
    my @data_l;
    my @data_be_out_l;
    if($data=~/[:_]/) { 
        # handle probably PSF data
        @data_l = split /\s*:\s*/,$data;
    } else {
        @data_l = ($data);
    }
    my $d;
    while(defined($d = shift @data_l)) { 
        while($d=~s/([_\s]*)([0-9A-Fa-f][0-9A-Fa-f])$//) { 
            my $my_d = $2;
            my $my_be = ($be=~s/(.)$//) ? $1 : undef;
            if(!defined($my_be)) {
                die_ERROR("070 ERROR: be parse error. be=$orig_be data=$orig_data");
            }
            push @data_be_out_l,($my_be ? $my_d : "xx");
        }
        if(length($d)) { 
            die_ERROR("015 ERROR: parsing data $orig_data. Can not decode $d.");
        }
    }
    return join(" ",reverse(@data_be_out_l));
}

sub FAdd_data($$$) {
    my ($rec_ptr1,$rec_ptr2,$len) = @_;
    $rec_ptr2->{fbe_lbe} = "1111_1111";
    my $data_be_str1 = record_2_data_be_str($rec_ptr1);
    my $data_be_str2 = record_2_data_be_str($rec_ptr2);
    my @data_l1 = split(/ +/,$data_be_str1);
    my @data_l2 = split(/ +/,$data_be_str2);
    my @data_l3;
    my $res=0;
    for(my $i = 1*@data_l2-1; $i>=0; $i-=1) {
        $res = hex($data_l1[$i]) +  hex($data_l2[$i]) + ($res>255 ? 1 : 0);
        push @data_l3,sprintf("%02X",$res&0xFF);
    }
    my $res_str = ""; 
    for(my $i = 0; $i<1*@data_l3; $i+=1) {
        if($i>0 && $i%4==0) {
            $res_str = "_".$res_str;
        }
        $res_str = $data_l3[$i].$res_str;
    }
    return $res_str;
}

sub CAS_Atomic($$) {
    my ($tr,$data_rd) = @_;
    my ($len) = ($tr->{length});
    my $rec_rd = {data=>$data_rd,fbe_lbe=>"1111_1111",length=>$tr->{length}/2,rec_type=>"pcie",src_ch_tc=>$tr->{src_ch_tc}};
    if($len<2 || ($len%2==1)) { 
        print_ERROR("054 ERROR: Bad len of CAS command".$tr->{line}."\n");
        $exit_code=1; return 1;
    }
    $tr->{fbe_lbe} = "1111_1111";
    my $data_be_str =  record_2_data_be_str($tr);
    my $data_be_str_rd = record_2_data_be_str($rec_rd);
    $tr->{atomic_rec}->{data} = substr($data_be_str,0,int(length($data_be_str)/2)); 
    $tr->{atomic_rec}->{length} = $tr->{length}/2;
    if(index($data_be_str,$data_be_str_rd)==int((length($data_be_str)+1)/2)) {
    } else {
        if($cpu_proj eq "adl") {
            $tr->{atomic_rec}->{data} = $data_rd;
        } else {
            $tr->{atomic_rec}->{is_UR} = "CAS_false";
        }
    }
    return 0;
}

sub fix_adl_psf_data($) {
    if($_[0]=~/[0-9A-Fa-f]/) {
        $_[0]=~s/ /0/g;
    }
    $_[0];
}

sub psf_file_read_record($) {
    local $_ = shift;
    if(!m/^\s*\|\s*\d/) { return undef; }

    my @a = split /\|/;
    if($cpu_proj eq "adl") {
        if($a[10]=~/_/) {
            $a[10] = fix_adl_psf_data($a[10]);
        } else {
            $a[10]=~s/^ +//;
            $a[10] = sprintf("%08X",hex($a[10]));
        }
        $a[6] = fix_adl_psf_data($a[6]);
        $a[9] = fix_adl_psf_data($a[9]);
        $a[12] = fix_adl_psf_data($a[12]);
    } else {
        $a[10]=~s/^ +//;
    }
    $a[1]=~s/^ +//;
    $a[3]=~s/ +$//;
    $a[7]=~s/^ +//;
    $a[14]=~s/^ +//;

    $a[6] = lc($a[6]);
    my $BDF = $a[6]; $BDF=~s/_.*//;
    my %rec = ( 
        id=>$a[6] , 
        BDF=>$BDF,
        direction=>$a[2] , 
        cmd=>$a[3],
        address=>$a[5],
        rs=>$a[4],
        data=>$a[10],
        sai=>$a[14],
        at=>$a[16],
        fbe_lbe=>$a[9],
        length=>$a[7],
        rec_type=>"psf",
        tick=>($tick_mul*$a[1]),
        );

    if(defined($a[12]) && $a[12]=~m#(\w+)/(\w+)#) {
        my $opcode = $rec{cmd};
        $rec{src_ch_tc} = $rec{src_ch} = get_ch_id($2."_psf");
        if($is_e2e_advane_WCIL and ($opcode eq "MWr32" || $opcode eq "MWr64")) {
            if(!defined($scbd->{MemWr_chs}->{$rec{src_ch_tc}})) {
                $scbd->{MemWr_chs}->{$rec{src_ch_tc}} = { count => 0 , prefix=>"_PCI" },
            }
            $rec{src_ch_rd} = $rec{src_ch_tc};
            merge_ns_write_channels(\%rec,$scbd->{MemWr_chs}->{$rec{src_ch_rd}},"tick_end");
        }
    } 

    if($rec{address}=~/([0-9a-fA-F]+)$/) { $rec{address} = big_hex($1); }

    if($rec{cmd}) {
        $rec{vc} = substr($a[8],0,1);
        if($a[18]=~/N/) { $rec{ns}=1; }
    }

    return \%rec;
}

sub match_MRd_to_Cplt($$) {
    my ($req_ptr,$cplt_ptr) = @_; 
    if($req_ptr->{cmd}=~/^MRd/) {
        my $addr1 = $req_ptr->{address}  & 0xFFFF;
        my $addr2 = $cplt_ptr->{address} & 0xFFFF;
        my $fl1 = $req_ptr->{fbe_lbe};
        my $fbe1 = substr($fl1,0,4);
        my $addr1_fbe;
        if($fbe1 eq '0000') { $addr1_fbe=0;
        } elsif($fbe1 =~/^...1/) { $addr1_fbe=0;
        } elsif($fbe1 =~/^..10/) { $addr1_fbe=1;
        } elsif($fbe1 =~/^.100/) { $addr1_fbe=2;
        } elsif($fbe1 eq '1000') { $addr1_fbe=3;
        } else {                   $addr1_fbe=-1;
        }
        if(!($addr1_fbe==($addr2&0x3))) {
            return 0;
        }
        if(!($addr1&0x7C)==($addr2&0x7C)) {
            return 0;
        }
        my $len1 = $req_ptr->{length};
        my $bc; # Byte count calculation from IOSF Spec Table 2-9. Calculating byte count from length and byte enables
        if($fl1=~/1..1_0000/)      { $bc=4;
        } elsif($fl1=~/01.1_0000/) { $bc=3;
        } elsif($fl1=~/1.10_0000/) { $bc=3;
        } elsif($fl1=~/0011_0000/) { $bc=2;
        } elsif($fl1=~/0110_0000/) { $bc=2;
        } elsif($fl1=~/1100_0000/) { $bc=2;
        } elsif($fl1=~/0001_0000/) { $bc=1;
        } elsif($fl1=~/0010_0000/) { $bc=1;
        } elsif($fl1=~/0100_0000/) { $bc=1;
        } elsif($fl1=~/1000_0000/) { $bc=1;
        } elsif($fl1=~/0000_0000/) { $bc=1;
        } elsif($fl1=~/...1_1.../) { $bc=4*$len1
        } elsif($fl1=~/...1_01../) { $bc=4*$len1-1
        } elsif($fl1=~/...1_001./) { $bc=4*$len1-2
        } elsif($fl1=~/...1_0001/) { $bc=4*$len1-3
        } elsif($fl1=~/..10_1.../) { $bc=4*$len1-1
        } elsif($fl1=~/..10_01../) { $bc=4*$len1-2
        } elsif($fl1=~/..10_001./) { $bc=4*$len1-3
        } elsif($fl1=~/..10_0001/) { $bc=4*$len1-4
        } elsif($fl1=~/.100_1.../) { $bc=4*$len1-2
        } elsif($fl1=~/.100_01../) { $bc=4*$len1-3
        } elsif($fl1=~/.100_001./) { $bc=4*$len1-4
        } elsif($fl1=~/.100_0001/) { $bc=4*$len1-5
        } elsif($fl1=~/1000_1.../) { $bc=4*$len1-3
        } elsif($fl1=~/1000_01../) { $bc=4*$len1-4
        } elsif($fl1=~/1000_001./) { $bc=4*$len1-5
        } elsif($fl1=~/1000_0001/) { $bc=4*$len1-6
        } else {                     $bc=-1;
        }
        my $bc2 = (($addr2&0xFF00)>>4) | bin2dec(substr($cplt_ptr->{fbe_lbe},-4));
        if(!($bc==$bc2)) {
            return 0;
        }
    }
    return 1;
}

sub psf_find_Cplt($$) {
    my ($cplt_l,$cplt_ptr) = @_; 
    my @cplt_l2;
    while(1*@$cplt_l) {
        my $req_ptr = shift (@$cplt_l);
        if(match_MRd_to_Cplt($req_ptr,$cplt_ptr)) {
            if(1*@cplt_l2) { unshift @$cplt_l,@cplt_l2; }
            return $req_ptr;
        } else {
            push @cplt_l2,$req_ptr;
        }
    }
    return undef;
}

sub psf_check_all_Cpl($) {
    my $scbd = shift @_;
    # Check if there are bad trnasactions that has no CMP.

    if($skip_psf_Cplt_chk) { return; };

    for my $direction ("U","D") {
        for my $id_key (keys %{$scbd->{$direction}}) {
            if(defined($scbd ->{$direction} -> { $id_key }) && $id_key ne "all") {
                my $unfinihsed_trans_l = $scbd ->{$direction} -> { $id_key };
                for my $rec_ptr (@$unfinihsed_trans_l) {
                    if($rec_ptr->{cmd}=~m/CAS|MRd|Cfg|IOWr/i) {
                        print_ERROR("016 ERROR: This transaction does not have CMP: ".$rec_ptr->{line}."\n");
                        $exit_code=1;
                    }
                }
            }
        }
    }

}

sub psf_Cpl_to_MRd_data($) {
    my $scbd = shift @_;
    # Check if there are bad trnasactions that has no CMP.

    for my $direction ("U","D") {
        if(defined($scbd ->{$direction} -> { "all"})) {
            my $trans_l = $scbd ->{$direction} -> { "all" };
            for my $rec_ptr (@$trans_l) {
                if($rec_ptr->{cmd}=~m/Cpl/i and defined($rec_ptr->{my_req}) and $rec_ptr->{my_req}->{cmd}=~m/MRd/) {
                    join_data_str(":",\$rec_ptr->{my_req}->{data},$rec_ptr->{data});
                }
            }
        }
    }

}

sub psf_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;
    my $last_cmd_line;
    my $last_cmd_line_data_join;
    my $count=0;
    local $tick_mul = $scbd->{tick_mul};

    $scbd->{read_record_func} = \&psf_file_read_record;

    while(<$fd>) {
        if(/\|[UD]\|/) {
            my $line = $_;
            my $is_join = 0;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;
            $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id($scbd->{file_src_ch}) if defined($scbd->{file_src_ch});
            # the $rec_ptr->{src_ch} is needed in PSF transactions only for IOMMU checkings.
            my $id_rs = $rec_ptr->{id}."_RS".$rec_ptr->{rs};

            if(defined($iommu_scbd_ptr) and $rec_ptr->{cmd}=~/^(CAS|Swap|FAdd|MRd|MWr)/) {
                $rec_ptr->{address} = IOMMU_convert_address($iommu_scbd_ptr,$rec_ptr->{BDF},$rec_ptr->{address});
            }

            if($skip_psf_long_trans_chk and $rec_ptr->{cmd} =~ /^(MRd|MWr)/ and $rec_ptr->{length}+($rec_ptr->{address}&0x3C)>16) {
                printf("Exit soc_e2e_checker because I am not supporting long psf transactions.\n");
                exit(0);
            }

            if($rec_ptr->{cmd} =~ /^(CAS|Swap|FAdd|IOWr|IORd|MRd|CfgRd|CfgWr|LTMRd)/) {
                $count+=1;
                push @{$scbd->{ $rec_ptr->{direction} }->{ $id_rs }} , $rec_ptr;
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                push @{$scbd->{ "A" }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                if($rec_ptr->{cmd} =~ /^(Swap|FAdd|CAS)/) {
                    # To emulate Swap, I add MWrSwap pseudo opcode here.
                    # No need to create MRdSwap to, because the Swap command will play that role.
                    $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch},"_atom"); # Atomic opcodescan change thier order related to the other MWr (and MRd) transactions. SoI give them a channel by themselves.                    my $new_rec_ptr = { };
                    $rec_ptr->{src_ch_tc} = append_ch_id($rec_ptr->{src_ch_tc},"_atom"); # Atomic opcodescan change thier order related to the other MWr (and MRd) transactions. SoI give them a channel by themselves.                    my $new_rec_ptr = { };
                    my $new_rec_ptr = { };
                    for(keys %$rec_ptr) { $new_rec_ptr->{$_} = $rec_ptr->{$_}; }
                    $new_rec_ptr->{cmd} = "MWr$rec_ptr->{cmd}";
                    $new_rec_ptr->{fbe_lbe} = "1111_1111";
                    $rec_ptr->{atomic_rec} = $new_rec_ptr;
                    push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $new_rec_ptr;
                    push @{$scbd->{ "A" }->{ all }} , $new_rec_ptr;
                    if($cpu_proj eq "lnl") {
                        $skip_e2e_write_chk=1 unless defined($skip_e2e_write_chk); #FIXME:temporarily disabling write checking in lnl if there is Atomic command. need to fix it later.
                    }
                }
            } elsif($rec_ptr->{cmd} =~ /^Cpl/) {
                my $other_direction = ($rec_ptr->{direction} eq "U" ? "D" : "U");
                my $tr = psf_find_Cplt($scbd ->{$other_direction} -> { $id_rs },$rec_ptr);
                if($tr) {
                    if($debug>=3) {
                        my $tr_id_rs = $tr->{id}."_RS".$tr->{rs};
                        print "In   :id=$tr_id_rs: ".$tr->{line};
                        print " Out :id=$id_rs: ".$line; 
                    }
                    if($tr->{cmd}=~/MRd|Swap|FAdd|CAS/) {
                        $tr->{Cpl_rec} = $rec_ptr;
                        $tr->{tick_end} = $rec_ptr->{tick};
                    }
                } else {
                    print_ERROR("017 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                push @{$scbd->{ "A" }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
            } elsif($rec_ptr->{cmd}=~/^(Msg|MWr)/) {
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                push @{$scbd->{ "A" }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
            } elsif(length($rec_ptr->{cmd})==0 && length($rec_ptr->{direction})>=1 && length($rec_ptr->{data})>=1 ) {
                # This code join all data from the next lines  
                my $trans_l = $scbd->{ $rec_ptr->{direction} }->{ all };
                my $fix_line_idx = +@$trans_l;
                my $fix_line = $trans_l->[$fix_line_idx-1]->{line};
                if(defined($last_cmd_line_data_join)) {
                    if($last_cmd_line eq $last_cmd_line_data_join) {
                        $is_join = 1;
                    }
                } else {
                    if($last_cmd_line eq $fix_line) {
                        $is_join = 1;
                        $last_cmd_line_data_join = $fix_line;
                    }
                }
                if($is_join && $fix_line_idx>=1) {
                    my $last_rec = $trans_l->[$fix_line_idx-1];
                    $last_rec->{data} .= ":".$rec_ptr->{data};
                }
            } else {
                undef $last_cmd_line;
            }

            if(!$is_join) {
                undef $last_cmd_line_data_join;
            }
        }
    }

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
    
    # Fix Atomic data
    for $tr (@{$scbd->{ A }->{ all }}) {
        if($tr->{Cpl_rec}) {
            if($tr->{cmd}=~/FAdd/) {
                $tr->{atomic_rec}->{data} = FAdd_data($tr->{atomic_rec},$tr->{Cpl_rec},$tr->{length});
            } elsif($tr->{cmd}=~/CAS/) {
                $tr->{data} = $tr->{atomic_rec}->{data}; # The full data is putted on the atomic_rec so copy it alao to the $tr->{data}
                CAS_Atomic($tr,$tr->{Cpl_rec}->{data});
            }
            $tr->{data} = $tr->{Cpl_rec}->{data} unless $tr->{cmd}=~/CAS/;
            delete $tr->{Cpl_rec};
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});
    assign_rec_parent_idx($scbd->{D}->{all});

    psf_check_all_Cpl($scbd);
}

sub axi_uri_update_func($$) {
    my ($rec_ptr1,$rec_ptr2) = @_;
    $rec_ptr1->{parent}->{uri} = $rec_ptr2->{parent}->{LID};
}

sub axi_timing_compare_func($$) {
    my ($rec_ptr1,$rec_ptr2) = @_;
    if($rec_ptr1->{tick_beg} < $rec_ptr2->{tick_beg} && $rec_ptr1->{tick_end} > $rec_ptr2->{tick_end}) {
        return 1;
    } else {
        return 0;
    }
}

sub push_ARADDR_keep_order($$) {
    my ($trans_l,$tr) = @_; die "Bad array pointer trans_l!" unless $trans_l;
    my $i = 0;
    my $max = 1*@$trans_l;
    my $push_i=$max;
    my $addr6 = $tr->{address}>>6;
    if($max>=1) {
        for($i=$max-1; $i>=0; $i-=1) {
            my $rec_ptr = $trans_l->[$i];
            if($rec_ptr->{tick_beg}>$tr->{tick_beg}) {
                $push_i = $i;
            } elsif($rec_ptr->{tick_beg}<$tr->{tick_beg}) {
                last;
            }
        }
    }
    for($i=$max; $i>0 && $i>$push_i; $i-=1) {
        $trans_l->[$i] = $trans_l->[$i-1];
    }
    $trans_l->[$push_i] = $tr;
}

sub axi_file_read_record($) {
    local $_ = shift;
    if(m/^\|-/) { return undef; }

    my @a = split /\s*\|\s*/;
    my $ifc = $a[$axi_header_h{INTERFACE}];
    $ifc =~ s/_\d$//;
    if(!$a[$axi_header_h{Time}]) {
        my $data_be_str = ($last_axi_rec->{cmd} ne "ARADDR" ? psf_prepare_data_and_be_string($a[$axi_header_h{Data}],$a[$axi_header_h{Strobe}]) : $a[$axi_header_h{Data}]);
        $last_axi_rec->{data} = $data_be_str . $last_axi_rec->{data};
        if(++$last_axi_rec->{data_i}>$last_axi_rec->{BSz}) { 
            if($rec->{strobe}=~/1/) {
                die_ERROR("187 ERROR: We get bad strobe in: ".trans_str($last_axi_rec));
            }
        }
        return undef;
    }
    my $typ = $a[$axi_header_h{Channel}];
    my %rec = ( 
        cmd=>$a[$axi_header_h{Channel}],
        rec_type=>"axi",
        typ=>$typ,
        count=>++$axi_header_h{count},
        tick=>$a[$axi_header_h{Time}], # Simulatiopn time
        Unit=>$AXI_Unit,
        src_ch => $AXI_Unit,
        cid =>$a[$axi_header_h{ID}],
        rs  =>0,
        data => $a[$axi_header_h{Data}],
        strobe => $a[$axi_header_h{Strobe}],
        stat => $a[$axi_header_h{Resp}],
        BL => $a[$axi_header_h{BL}],
        BSz => $a[$axi_header_h{BSz}], 
        BSz_orig => $a[$axi_header_h{BSz}],
        last => $a[$axi_header_h{L}],
    );

    $rec{orig_address} = $rec{address} = big_hex($a[$axi_header_h{Addr}]);
    $rec{address} &= $scbd->{BusWidthMask} if($scbd->{BusWidth}<=32); # dont mask 64B bus because we want to support 32B transactions

    if($rec{cmd} =~ /ARADDR|AWADDR/) { 
        $rec{prefetch} = 1 if((hex($a[$axi_header_h{User}]) & 8));
    }
    if($rec{cmd} eq "ARADDR" || $rec{cmd} eq "AWADDR") { 
        $rec{ns} = 1 if(!(hex($a[$axi_header_h{User}]) & 1));
    }
    $rec{direction} = $rec{cmd};
    
    if($rec{tick} =~/(\d+)\.(\d+) *ns/) { 
        $rec{tick} = sprintf("%d",1000*"$1.$2"); 
    }
    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    $last_axi_rec = \%rec;
    #if($rec{cmd}=~/DATA/) { return undef; }
    return \%rec;
}

$axi_file_trans_counter = 0;

sub axi_file_reader($$) {
    my $fd = shift;
    local $scbd = shift;
    #my $last_cmd_line;
    my $last_cmd_line_data_join;
    my $count=0;
    my $AWADDR_count=0;
    my $WDATA_count=0;
    local $last_axi_rec;
    local %other_direction_h = ( RDATA=>"ARADDR", WDATA=>"AWADDR", WRESP=>"AWADDR" );
    my @trans_U_l = ();
    local $MemWr_chs = { count => 0 , prefix=>"_MemWr" };
    my $WDATA_chunk_l = []; # Current trasaction WDATA chunks list
    $scbd->{U}->{all} = [];
    while(<$fd>) {
        if(/^[^-]/) {
            my $line = $_;
            #my $is_join = 0;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            if($debug>=3) { $rec_ptr->{line} = $line; }
            #$rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id($scbd->{file_src_ch}) if defined($scbd->{file_src_ch});
            # the $rec_ptr->{src_ch} is needed in PSF transactions only for IOMMU checkings.
            my $id_rs = $rec_ptr->{cid}."_RS".$rec_ptr->{rs};

            if($rec_ptr->{cmd} =~ /^(AWADDR|ARADDR)$/) {
                $count+=1;
                push @{$scbd->{ $rec_ptr->{direction} }->{ $id_rs }},$rec_ptr;
                push @trans_U_l , $rec_ptr;
                if($rec_ptr->{cmd} =~ /^(ARADDR)$/) { $rec_ptr->{address} &= $scbd->{BusWidthMask}; }
                if($rec_ptr->{BSz}<$scbd->{BusWidth}) { $rec_ptr->{BSz} = $scbd->{BusWidth}; }
                $last_cmd_line = $line;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                $rec_ptr->{AWADDR_count} = $AWADDR_count++ if ($rec_ptr->{cmd} =~ /^(AWADDR)$/);
                if(defined($iommu_scbd_ptr)) {
                    $rec_ptr->{address} = IOMMU_convert_address($iommu_scbd_ptr,$scbd->{BDF},$rec_ptr->{address} & 0xffff_ffff_ffff);
                }
            } elsif($rec_ptr->{cmd} =~ /^(RDATA)$/) {
                my $other_direction = $other_direction_h{$rec_ptr->{direction}};
                my $tr = $scbd ->{$other_direction} -> { $id_rs }->[0];
                if($tr) {
                    if($debug>=3) {
                        my $tr_id_rs = $tr->{cid}."_RS".$tr->{rs};
                        print "In   :id=$tr_id_rs: ".$tr->{line};
                        print " Out :id=$id_rs: ".$line; 
                    }
                    my $data_be_str = $rec_ptr->{data};
                    $tr->{data} = $data_be_str . $tr->{data};
                    $tr->{data_i}=1;
                    $tr->{tick_go} = $rec_ptr->{tick};
                    $rec_ptr->{tick_end} = $rec_ptr->{tick};
                    if(++$tr->{BL_cnt}>=$tr->{BL}) { 
                        shift @{$scbd ->{$other_direction} -> { $id_rs }}; 
                    }
                    $tr->{is_UR}++ if($rec_ptr->{stat} =~ /OKAY|SLVE/);
                    $tr->{prefetch}=1 if($rec_ptr->{stat} =~ /SLVE/);
                    # Since this axi is not coherent and does not keep ordering then I creates new transaction for each cache line
                    my $new_rec = {
                        data => $data_be_str,
                        cmd      => $tr->{cmd     },
                        typ      => $tr->{typ     },
                        Unit     => $tr->{Unit    },
                        cmd      => $tr->{cmd     },
                        BSz      => $tr->{BSz}, 
                        BSz_orig      => $tr->{BSz_orig},
                        rec_type => $tr->{rec_type},
                        tick_beg => $tr->{tick_beg},
                        tick_go  => $rec_ptr->{tick},
                        tick_end => $rec_ptr->{tick},
                        address  => $tr->{address} + $scbd->{BusWidth}*($tr->{BL_cnt}-1),
                        orig_address  => $tr->{orig_address},
                    };
                    $new_rec->{ns      } = $tr->{ns} if($tr->{ns});
                    if($tr->{is_UR}) { $new_rec->{is_UR} = $tr->{is_UR}; }
                    $new_rec->{src_ch_tc} = $new_rec->{src_ch} = get_ch_id($scbd->{file_src_ch});
                    if($debug>=3) {
                        $new_rec->{line} = $tr->{line};
                        chomp $new_rec->{line}; 
                        $new_rec->{line} .= $rec_ptr->{line};
                    }
                    push_ARADDR_keep_order($scbd->{U}->{all}, $new_rec) if !$tr->{prefetch}; #push @{$scbd->{U}->{ all }} , $new_rec if !$tr->{prefetch};
                    $last_axi_rec = $new_rec;

                } else {
                    die_ERROR("123 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
            } elsif($rec_ptr->{cmd} =~ /^(WDATA)$/) {
                my $other_direction = $other_direction_h{$rec_ptr->{direction}};
                #the AWADDR command can come after the WDATA, so create a new tr here and get the AWADDR when we get the WRESP
                if(1) {
                    if($debug>=3) {
                        print "In   :id=$id_rs: \n";
                        print " Out :id=$id_rs: ".$line; 
                    }
                    my $data_be_str = psf_prepare_data_and_be_string($rec_ptr->{data},$rec_ptr->{strobe});
                    # Since this axi is not coherent and does not keep ordering then I creates new transaction for each cache line
                    my $new_rec = {
                        data => $data_be_str,
                        tick => $rec_ptr->{tick},
                        tick_beg => $rec_ptr->{tick},
                    };
                    #$new_rec->{src_ch_tc} = $new_rec->{src_ch} = get_ch_id(sprintf("%s_%04d",$scbd->{file_src_ch},$axi_file_trans_counter++));
                    $new_rec->{src_ch_tc} = $new_rec->{src_ch} = get_ch_id($scbd->{file_src_ch});
                    merge_ns_write_channels($new_rec,$MemWr_chs,"tick_go");
                    if($debug>=3) {
                        $new_rec->{line} = $rec_ptr->{line};
                    }
                    push @$WDATA_chunk_l,$new_rec;
                    if($rec_ptr->{last}) {
                        $scbd->{WRESP}->{$WDATA_count++} = $WDATA_chunk_l;
                        $WDATA_chunk_l = [];
                    }
                    push @{$scbd->{U}->{ all }} , $new_rec;
                    $last_axi_rec = $new_rec;

                } else {
                    die_ERROR("123 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
            } elsif($rec_ptr->{cmd} =~ /^(WRESP)$/) {
                my $other_direction = $other_direction_h{$rec_ptr->{direction}};
                my $AWADDR_tr = shift @{$scbd ->{$other_direction} -> { $id_rs }}; 
                if(!defined($AWADDR_tr)) {
                    die_ERROR("123 ERROR: Can not find AWADDR for this WRESP: $line");
                }
                $AWADDR_tr->{BL_cnt} = 0;
                if($debug>=9) {
                    print "In   :id=$id_rs: ".$AWADDR_tr->{line};
                    print " Out :id=$id_rs: ".$line; 
                }
                for (1..$AWADDR_tr->{BL}) {
                    my $son = shift @{$scbd->{WRESP}->{$AWADDR_tr->{AWADDR_count}}};
                    if(!defined($son)) {
                        die_ERROR("128 ERROR: missing DATA chunk for: $AWADDR_tr->{line} ; $line");
                    }
                    $son->{address } = $AWADDR_tr->{address} + $scbd->{BusWidth}*$AWADDR_tr->{BL_cnt},
                    $AWADDR_tr->{BL_cnt}+=1;
                    $son->{tick_go} = $rec_ptr->{tick};
                    $son->{tick_end} = $rec_ptr->{tick};
                    $son->{cmd     } = $AWADDR_tr->{cmd     };
                    $son->{typ     } = $AWADDR_tr->{typ     };
                    $son->{Unit    } = $AWADDR_tr->{Unit    };
                    $son->{cmd     } = $AWADDR_tr->{cmd     };
                    $son->{rec_type} = $AWADDR_tr->{rec_type};
                    $son->{ns      } = $AWADDR_tr->{ns} if($AWADDR_tr->{ns});
                    my $offset = $son->{address}&0x3f;
                    $son->{data}=~s/ //g;
                    if($offset) {
                        $son->{data} .= "xx" x $offset;
                        my $len = $son->{data};
                        if(length($son->{data})>128) { $son->{data} = substr($son->{data},$len-128); }
                    }
                    $son->{address} &= 0xffffffff_ffffffc0;
                    if($debug>=3) {
                        $son->{line} = my_chomp($AWADDR_tr->{line})." ; ".$son->{line};
                    }
                    if($AWADDR_tr->{prefetch}) { 
                        $son->{data} = undef; 
                    }
                }
                if(@{$scbd->{WRESP}->{$AWADDR_tr->{AWADDR_count}}}) {
                    die_ERROR("169 ERROR: too much data chunks for $AWADDR_tr->{line} ; $line");
                }
                delete $scbd->{WRESP}->{$AWADDR_tr->{AWADDR_count}};
                $AWADDR_tr->{is_UR}++ if($rec_ptr->{stat} eq "OKAY");
            } elsif(length($rec_ptr->{cmd})==0 && length($rec_ptr->{direction})>=1 && length($rec_ptr->{data})>=1 ) {
                # This code join all data from the next lines  
            } else {
                #undef $last_cmd_line;
            }

        }
    }

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 

    for my $rec_ptr (@trans_U_l) {
        if($rec_ptr->{BL} != $rec_ptr->{BL_cnt}) {
            die_ERROR("124 ERROR: Bad DATA chunk count=$rec_ptr->{BL_cnt}: ".trans_str($rec_ptr));
        }
        my $is_UR_cnt = ($rec_ptr->{cmd} eq "ARADDR" ? $rec_ptr->{BL} : 1);
        if($rec_ptr->{is_UR} != $is_UR_cnt) {
            die_ERROR("125 ERROR: Bad UR=$rec_ptr->{is_UR}!=$is_UR_cnt: ".trans_str($rec_ptr));
        } else {
            $rec_ptr->{is_UR} = 0;
        }
        delete $rec_ptr->{AWADDR_count};
    }

    # my $parent_idx_count = 0;
    # fix the ARADDR unaligned transactions to have correct data size
    for my $rec_ptr (@{$scbd->{U}->{ all }}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        if($rec_ptr->{cmd} eq "ARADDR" and ($rec_ptr->{address} & ($scbd->{BusWidth}-1) or $rec_ptr->{BSz} < $scbd->{BusWidth})) {
            $rec_ptr->{data}=~s/ //g;
            $rec_ptr->{data} = substr($rec_ptr->{data},2*((($rec_ptr->{BSz}-1)&$rec_ptr->{address}) - $rec_ptr->{BSz}));
            my $offset = $rec_ptr->{address}&0x3f;
            if($offset) {
                $rec_ptr->{data} .= "xx" x $offset;
                my $len = $rec_ptr->{data};
                if(length($rec_ptr->{data})>128) { $rec_ptr->{data} = substr($rec_ptr->{data},$len-128); }
            }
            $rec_ptr->{address} &= 0xffffffff_ffffffc0;
        }

        # ARADDR transaction of 32 byte to have a 32 byte data.
        if($rec_ptr->{cmd} eq "ARADDR" and ($scbd->{BusWidth}==64) and $rec_ptr->{BSz_orig} ==32 and length($rec_ptr->{data})==128) {
            $rec_ptr->{data} = substr($rec_ptr->{data},($rec_ptr->{address} & 0x3f ? 0 : 64),64);
        }
        if($rec_ptr->{cmd} eq "ARADDR" and ($scbd->{BusWidth}==64) and $rec_ptr->{BSz_orig} ==64 and length($rec_ptr->{data})==128 and ($rec_ptr->{orig_address} & 0x3f)==0x20) {
            $rec_ptr->{data} = substr($rec_ptr->{data},64,64);
            $rec_ptr->{address} |= 0x20;
        }
       
        # delete variable that i don;t need any more to save memory
        for(qw(typ BL stat BSz_orig orig_address)) {
            delete $rec_ptr->{$_};
        }
    }

    undef $scbd->{ARADDR};
    undef $scbd->{AWADDR};
    delete $scbd->{WRESP};
    my $tmp_trans_l = $scbd->{U}->{all};
    undef $scbd->{U};
    undef $scbd->{D};
    $scbd->{U}->{all} = $tmp_trans_l;
    
    return;
}

sub gtcxl_file_read_record_REQ($) {
    local $_ = shift;
    if(m/^\|-/) { return undef; }

    my @a = split /\s*\|\s*/;
    my %rec = ( 
        cmd=>$a[$header_h->{OPCODE}],
        rec_type=>"gtcxl",
        typ=>$typ,
        count=>++$header_h->{count},
        tick=>$a[$header_h->{TIME}], # Simulatiopn time
        Unit=>$CXL_Unit,
        src_ch => $CXL_Unit,
        cid =>$a[defined($header_h->{UQID})?$header_h->{UQID}:$header_h->{CQID}],
        rs  =>0,
        stat => $a[$header_h->{Resp}],
        LID => $a[$header_h->{URI_LID}],
    );

    $rec{address} = big_hex($a[$header_h->{ADDRESS}]) & 0xFFFFFFFF_FFFFFFC0;

    $rec{cmd} =~s/\(.*$//;

    $rec{direction} = $rec{cmd};

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
    if($rec{cid} =~ /^0+(..*)/) { $rec{cid} = $1; }

    return \%rec;
}

sub gtcxl_file_read_record_DATA($) {
    local $_ = shift;
    if(m/^\|-/) { return undef; }


    my @a = split /\s*\|\s*/;
    my %rec = ( 
        rec_type=>"gtcxl",
        typ=>$typ,
        tick=>$a[$header_h->{TIME}], # Simulatiopn time
        Unit=>$CXL_Unit,
        src_ch => $CXL_Unit,
        rs  =>0,
        protocol => $a[$header_h->{PROTOCOL}],
        LID => $a[$header_h->{URI_LID}],
    );

    if(defined($header_h->{UQID})) {
        $rec{uid} = $a[$header_h->{UQID}];
        if($rec{uid} =~ /^0+(..*)/) { $rec{uid} = $1; }
    } else {
        $rec{cid} = $a[$header_h->{CQID}];
    }

    my $BE = hex($a[$header_h->{BYTE_ENABLE}]);
    if($typ=~/U2C/) { $BE = 0xFFFFFFFF; } # All reads use full cache line

    if($rec{protocol}!=3) {
        my $d = $a[$header_h->{DATA}];
        my $l = 64-length($d);
        if($l>0) { $d = ("0" x $l) . $d; }
        $rec{data} = psf_prepare_data_and_be_string($d,sprintf("%032b",$BE));
        $rec{data} =~ s/ //g;
    }

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    return \%rec;
}

sub gtcxl_file_read_record_RSP($) {
    local $_ = shift;
    if(m/^\|-/) { return undef; }

    $_=~s/\s*$//;
    my @a = split /\s*\|\s*/;
    my %rec = ( 
        cmd=>$a[$header_h->{OPCODE}],
        rec_type=>"gtcxl",
        typ=>$typ,
        count=>++$header_h->{count},
        tick=>$a[$header_h->{TIME}], # Simulatiopn time
        Unit=>$CXL_Unit,
        src_ch => $CXL_Unit,
        cid =>$a[defined($header_h->{UQID})?$header_h->{UQID}:$header_h->{CQID}],
        LID => $a[$header_h->{URI_LID}],
    );

    if(defined($header_h->{UQID})) {
        $rec{uid} = $a[$header_h->{UQID}];
        if($rec{uid} =~ /^0+(..*)/) { $rec{uid} = $1; }
    }
    if(defined($header_h->{CQID})) {
        $rec{cid} = $a[$header_h->{CQID}];
    }
    if(defined($header_h->{RESPONSE_DATA})) {
        $rec{uid} = sprintf("%1x",hex($a[$header_h->{RESPONSE_DATA}])&0x1FF);
    }


    #$rec{direction} = $rec{cmd};

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
    if($rec{cid} =~ /^0+(..*)/) { $rec{cid} = $1; }

    return \%rec;
}

sub gtcxl_file_reader($$) {
    my $fd_h = shift;
    local $scbd = shift;
    my %idi_cid_h;
    my %idi_uri_h;
    my %idi_uid_h;
    my %GT_NS_C2U_h;
    my $count=0;
    local $typ;
    my $line_h;
    my $time_h;
    local $header_h;
    my $spec_snp_count = 0; # In LNL snoop are speculative


    if($cpu_proj eq "adl") {
        $scbd->{tick_mul}=$tick_mul;
    } else {
        $scbd->{tick_mul}=$tick_mul*1000.0;
    }

    if($header_h{TIME}) { return undef; }
    $scbd->{U}->{all} = [];
    
    for $typ (keys %$fd_h) {
        my $line;
        my $fd = $fd_h->{$typ}{fd};
        while(<$fd>) {
            if(/^(\d+)/) {
                $line = $_;
                $time_h->{$typ} = 0+$1;
                last;
            } 
        }
        $line_h->{$typ} = $line;
    }

    while(1) {
        my $line;
        # find the earliest line
        my $min_time = 0x7FFFFFFF_FFFFFFFF;
        undef $typ;
        for my $k (keys %$line_h) {
            if($min_time>$time_h->{$k} && defined($line_h->{$k})) {
                $min_time = $time_h->{$k};
                $typ = $k; 
            }
        }
        if($min_time==0x7FFFFFFF_FFFFFFFF) { last };
        $line = $line_h->{$typ};
        $header_h = $fd_h->{$typ}{header_h};
        #fetch the next line
        my $fd = $fd_h->{$typ}{fd};
        $line_h->{$typ} = undef;
        while(<$fd>) {
            if(/^(\d+)/) {
                $line_h->{$typ} = $_;
                $time_h->{$typ} = 0+$1;
                last;
            } 
        }

        my $is_idp_snp = 0; # index($line,"CXL2UFI_Snp")>=0;
        if(!$is_idp_snp) {

            my $rec_ptr = &{$scbd->{read_record_func}{$typ}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem

            if($rec_ptr->{Unit}=~/IDP/) { next; }

            if($rec_ptr->{typ} eq "C2U REQ") {
                $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id($scbd->{file_src_ch}) if defined($scbd->{file_src_ch});
                $count+=1;
                $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} = $rec_ptr;
                $idi_uri_h{$rec_ptr->{LID}} = $rec_ptr;
                if($rec_ptr->{cmd}=~/^CXL2UFI_PushWr/) {
                    print "Skip checking if there is a CXL PushWr dont supprot it yet\n" if $debug>=1;
                    exit; # fixme: need to support CXL PushWr
                    push @{$scbd->{U}->{all}} , $rec_ptr;
                }
            } elsif($rec_ptr->{typ} eq "U2C REQ") {
                $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id($scbd->{file_src_ch}) if defined($scbd->{file_src_ch});
                # This will record BACKINT opcodes too.
                $idi_uid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} = $rec_ptr;

                if($rec_ptr->{cmd}=~/SNPINV/) {
                    my $addr6 = ($rec_ptr->{address}>>6);
                    # If we snoop a read that got GO but no data, we snoop it, because it will get MoNuke in read core
                    while(my ($k,$read_rec) = each %{$idi_cid_h{$rec_ptr->{Unit}}}) {
                        if($addr6 == ($read_rec->{address}>>6) and $read_rec->{tick_go} and $read_rec->{cmd}=~/^(RDCURR|RFO|DRD|CRD|PRD)/) {
                            if(length($read_rec->{data_rd})<128) {
                                # if not all data received it is bad
                                $read_rec->{slfsnp_bad} = 1; # Signals that this transaction is bad (got MoNuke)
                            }
                        }
                    }
                }
            } elsif($rec_ptr->{typ} =~ /DATA/) {
                my $tr;
                my $id;
                if($rec_ptr->{protocol}==3) { next }
                if($rec_ptr->{typ} =~ /C2U/) {
                    $tr = $idi_uri_h{ $rec_ptr->{LID} };
                    if(defined($tr) and !($tr->{cmd}=~/^CXL2UFI_PushWr/)) {
                        if($tr->{uid} ne $idi_uid_h{$rec_ptr->{Unit}}->{ $id=$rec_ptr->{uid} }->{uid}) {
                            die_ERROR("119 ERROR: can not match uid for this write. Trans: $rec_ptr->{line}\n");
                        }
                    } else {
                        $id = 0;
                    }
                } else {
                    $tr = $idi_cid_h{$rec_ptr->{Unit}}->{ $id=$rec_ptr->{cid} };
                }
                if(!$skip_uri_chk and !defined($tr)) {
                    die_ERROR("043 ERROR: Can not match IDI transaction by id. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }
                my $data_key = (($rec_ptr->{typ}=~/C2U/) ? "data_wr" : "data_rd");
                if(defined($tr)) {
                    my $skip_uri_chk = $::skip_uri_chk || ($cpu_proj eq "lnl" && defined($tr->{$data_key})); #fixme: need to remove this mask to the second data chunk uri check after Amal will fix the EMU_URI_STITCH bug on it.
                    if(defined($tr->{$data_key})) { 
                        $tr->{$data_key} = $rec_ptr->{data}.$tr->{$data_key};
                    } else {
                        $tr->{$data_key} = $rec_ptr->{data};
                    }
                    use_max_tick_end($tr,$rec_ptr->{tick});
                    if($rec_ptr->{bogus}) { 
                        $tr->{bogus}=1;  
                        print "Cought bogus=1 data trans : $tr->{line}" if $debug>=6; 
                    }
                    if($debug>=3) {
                        print "In   :id=$id: ".$tr->{line};
                        print " Out :id=$id: ".$line; 
                    }
                    if(!$skip_uri_chk && $rec_ptr->{LID} ne $tr->{LID} and !($tr->{cmd}=~/^INT/)) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("032 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    if($rec_ptr->{Attributes}=~/byteen=(\w+)/) {
                        $tr->{byteen} = $1;
                    }
                };
            } elsif($rec_ptr->{cmd} eq "CXL_GO") {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    $tr->{count_go} = $rec_ptr->{count};
                    if($debug>=9) {
                        print "In   :id=$rec_ptr->{uid}: ".$tr->{line};
                        print " GO :id=$rec_ptr->{uid}: ".$line; 
                    }
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        if(!($tr->{cmd} =~/LLCPREF/)) {
                            die_ERROR("033 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                        }
                    }
                    idi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                };
            } elsif($rec_ptr->{typ} eq "U2C RSP") {
              if($rec_ptr->{cmd} =~ /WRITEPULL/i) {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        die_ERROR("034 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("044 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }
                $tr->{uid} = $rec_ptr->{uid};
                if($rec_ptr->{cmd} =~ /GO_WRITEPULL/i) {
                    idi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                }
                $idi_uid_h{$rec_ptr->{Unit}}->{$tr->{uid}} = $tr;
              } elsif($rec_ptr->{cmd}=~/FwdM/) {
                # Correct the Snoop response like : RspIFwdMO
                my $tr = $idi_uid_h{$rec_ptr->{Unit}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if($rec_ptr->{LID} ne $tr->{LID}) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("042 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("041 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                $tr->{snp_rsp_cmd} = $rec_ptr->{cmd};
              } elsif($rec_ptr->{cmd}=~/EXTCMP/i) {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_EXTCMP} = $rec_ptr->{tick};
                }
              }
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
              if($rec_ptr->{cmd}=~/FwdM/) {
                # Take the Snoop response for IOP Snoops like : RspIFwdMO
                # FIXME: More accurate is to match the snoop data to the IOP write or read that did the snoop.
                my $tr = $idi_uid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("051 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    $tr->{tick_go} = $rec_ptr->{tick};
                    $tr->{tick_beg} = $tr->{tick};
                } else {
                    die_ERROR("052 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                if($skip_e2e_write_chk) {
                    $tr->{src_ch_tc} = get_ch_id($scbd->{file_src_ch}."_Spec_SNP".addr_str($tr->{address} & $sys_addr_mask));
                } else {
                    $tr->{src_ch_tc} = get_ch_id($scbd->{file_src_ch}."_Spec_SNP".++$spec_snp_count);
                }
                push @{$scbd->{U}->{all}} , $tr;
              }
            }
        } elsif($is_idp_snp) {
            # Handle the snoops
            my $rec_ptr = &{$scbd->{read_record_func}{$typ}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem
            if($rec_ptr->{typ} eq "U2C REQ") {
                push @{$scbd->{GTCXL_snp_h}->{$rec_ptr->{cid}}},$rec_ptr;
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
                my $tr = get_trans_by_uri($scbd->{GTCXL_snp_h}->{$rec_ptr->{cid}},undef,undef);
                if(defined($tr)) {
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_end} = $rec_ptr->{tick};
                    $tr->{rsp} = $rec_ptr->{cmd};
                }
            }
        }
    }

    # Fix the data_wr & data_rd to be only data.
    my @new_rec_l;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        if($rec_ptr->{bogus}) { next; }
        push @new_rec_l,idi_rec_fix_data($rec_ptr);
    }
    $scbd->{U}->{all} = \@new_rec_l;

    # Checking for DRD_PREF with bad SelfSnoop that comes just after ITOM.
    # Since the ITOM takes ownership without writing data to LLC, there is bad data to LLC.
    # Next transaction from the same core, 
    my %addr_itom_h;
    # my $parent_idx_count = 0;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        undef ($rec_ptr->{snp_rec_l}); # just free memory
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(ITOM)$/i) {
            # If there is ITOM opcode then note it.
            $addr_itom_h{$addr6} = src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}]);
        } else {
            my $skip_undef = 0;
            my $was_itom = defined($addr_itom_h{$addr6});
            if($was_itom) {
                if($rec_ptr->{cmd}=~/^(LLCPREFRFO|DRD_PREF|CRD_PREF|DRD_OPT_PREF|CRD_OPT_PREF|RFO_PREF)/) {
                    if($addr_itom_h{$addr6} eq src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}])) {
                        if(defined($rec_ptr->{slfsnp_bad})) {
                            $rec_ptr->{slfsnp_bad} = 1;
                            $skip_undef = 1;
                        }
                    }
                } elsif($rec_ptr->{cmd}=~/^(WBSTOI|LLCPREFCODE|LLCPREFDATA)/) {
                    $skip_undef = 1;
                }
                # If there any transaction after the ITOM - then clear the flag.
                $addr_itom_h{$addr6} = undef unless $skip_undef;
            }
        }
        if($debug<=2) {
            # Remove redundant info
            delete $rec_ptr->{cid};
            delete $rec_ptr->{uid};
        }
    }

    # Checking for RFO_PREF come with FFFFF data and the address was already owned by the cbo.
    # This case in ADL is ok 
    # oshitrit saidthis case can be skiped.
    my %addr_cbo_owner_h;
    if($cpu_proj eq "adl") { for my $rec_ptr (@{$scbd->{U}->{all}}) {
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(DRD_PREF|CRD_PREF|DRD_OPT_PREF|CRD_OPT_PREF|RFO_PREF)$/i) {
            if($rec_ptr->{Unit} and $rec_ptr->{data} eq "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff") {
            if($addr_cbo_owner_h{$addr6} eq $rec_ptr->{Unit}) {
                $rec_ptr->{slfsnp_bad} = 1; # oshitrit saidthis case can be skiped.
            } 
            }
        }

        if($rec_ptr->{cmd}=~/^(RFO)/i) {
            $addr_cbo_owner_h{$addr6} = $rec_ptr->{Unit};
        } elsif($rec_ptr->{cmd}=~/^(WOWrInv|WIL|WBMTOI|WBETOI)$/i) {
            $addr_cbo_owner_h{$addr6} = undef;
        }
    } }

    undef $scbd->{GTCXL_snp_h};
    assign_rec_parent_idx($scbd->{U}->{all});

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}
sub idi_late_update_tick_go($$) {
    my ($rec_ptr,$tick) = @_;
    no warnings;
    if(length($rec_ptr->{data})>=128 && exists($tr->{count_go})) {
        if(!defined($rec_ptr->{tick_go})) {
            $rec_ptr->{tick_go} = $tick;
        } else {
            die_ERROR("160 ERROR: tick_go was already set for : ".trans_str($rec_ptr)); 
        }
    }
}


sub use_max_tick_end($$) {
    my ($rec_ptr,$tick) = @_;
    no warnings;
    if($tick>$rec_ptr->{tick_end})  {
        $rec_ptr->{tick_end} = $tick;
    }
}

sub idi_update_tick_end($$) {
    my ($rec_ptr,$tick) = @_;
    no warnings;
    if($rec_ptr->{cmd}=~/WOWrInv|WIL|WBMTOI|WBMTOE|WCIL|ITOMWR|MEMPUSHWR|ITOMWR/i) { # put tick_end only if the transction got GO and DATA
        if(length($rec_ptr->{data_wr})>=128 && defined($rec_ptr->{tick_go})) {
            if(!defined($rec_ptr->{tick_end})) {
                $rec_ptr->{tick_end} = $tick;
            } else {
                die_ERROR("159 ERROR: tick_end was already set for : ".trans_str($rec_ptr)); 
            }
        }
    } elsif($tick>$rec_ptr->{tick_end})  {
        $rec_ptr->{tick_end} = $tick;
    }
}

%idi_cmd_conv = (
    #"WOWrInv"       => "WIL", #this opcode gets EXTCMP hence can not be aliased to WIL
    #"WOWrInvF"      => "WIL", #this opcode gets EXTCMP hence can not be aliased to WIL
    "WrInv"         => "WIL",
    "MemWr"         => "WIL",
    "ItoMWr"         => "WIL",
    "DirtyEvict"    => "WIL",
    "RdAny"         => "DRD",
    "RdOwn"         => "DRD",
    "RdShared"      => "DRD",
    "UcRdF"         => "DRD",
    "RdCurr"        => "RDCURR",
    "RdCurr_NS"        => "RDCURR",
);

sub mc_cxm_cfi_trk_file_read_record_CFI45($) {
    local $_ = shift;
    if(!m/\s*\d+/) { return undef; }
    if(!m/$cfi_filter/) { return undef; }

    my @a = split /\s*\|\s*/;
    my $typ = $a[$idi_header_h{VC_ID}];
    my $ifc = $a[$idi_header_h{INTERFACE}];
    $ifc =~ s/_\d$//;
    $typ = ($cfi_trk_typ_conv{$typ}->{$ifc} or die_ERROR("Bad opcode decode for typ=$typ ifc=$ifc line=$_"));
    my %rec = ( 
        uri=>$a[$idi_header_h{URI_LID}],
        uri_pid=>$a[$idi_header_h{URI_PID}],
        direction=>$typ, 
        cmd=>$a[$idi_header_h{OPCODE}],
        address=>(big_hex($a[$idi_header_h{ADDRESS}])&0x3f_ffffffff),
        rec_type=>"idi",
        typ=>$typ,
        count=>++$idi_header_h{count},
        tick=>$a[$idi_header_h{TIME}], # Simulatiopn time
        Unit=>$a[$idi_header_h{VC_NAME}],
        prot=>$a[$idi_header_h{PROTOCOL_ID}],
        rsp=>$a[$idi_header_h{RSPID}],
        dst=>$a[$idi_header_h{DSTID}], 
        eop=>$a[$idi_header_h{EOP}], 
        go_state=>$a[$idi_header_h{GO}]
    );

    if($rec{cmd}=~/ReqFwdCnflt|FwdCnfltO/) { return undef }; #no need to decode these opcodes

    $rec{UnitU} = $rec{Unit};
    #$rec{Unit} .= "-".$a[$idi_header_h{RSPID}];

    my $hbo_id;
    if($rec{Unit} eq "SOC_HBOIO0") { $hbo_id = 0 }
    elsif($rec{Unit} eq "SOC_HBOIO1") { $hbo_id = 1; }
    elsif($rec{Unit} eq "SOC_HBOMC0") { $hbo_id = 0; }
    elsif($rec{Unit} eq "SOC_HBOMC1") { $hbo_id = 1; }

    $rec{cmd} =~s/\(.*$//;
    if(defined($hbo_id)) {
        $rec{hbo_id} = $hbo_id;
    }

    if(/SlfSnp=0/i) { $rec{slfsnp_bad} = 0; }
    if(/bogus=1/i) { $rec{bogus} = 1; }
    if($cpu_proj eq "adl") {
        $rec{tick}=~s/ *ps *//;
    }

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    $rec{cid}  = $a[$idi_header_h{RTID}] if $a[$idi_header_h{RTID}] ne "-";
    $rec{uid}  = $a[$idi_header_h{HTID}] if $a[$idi_header_h{HTID}] ne "-";

    if($rec{cmd}=~/WrInv|MemWr$/) {
        $rec{address} &= 0xFFFFFFFF_FFFFFFC0;
    }

    if($typ=~/DATA/) {
        $rec{data} = $a[$idi_header_h{DATA_3}].$a[$idi_header_h{DATA_2}].$a[$idi_header_h{DATA_1}].$a[$idi_header_h{DATA_0}];
        $rec{data} =~ s/ //g;
        $rec{data} =~ s/-/x/g;
        $rec{Chunk} = $a[$idi_header_h{CHUNK}] ? "1100" : "0011";
        if(/bogus=1/) { $rec{bogus}=1; }
    } elsif($typ=~/C2U REQ/) {
        if(my $new_cmd=$idi_cmd_conv{$rec{cmd}}) { $rec{cmd} = $new_cmd; };
        $rec{src_ch_tc} = get_ch_id($rec{Unit}."_".$a[$idi_header_h{RSPID}]);
        $rec{id}  = $ch_name_l[$rec{src_ch_tc}]."_id_".$rec{cid};
    }

    return \%rec;
}

sub remove_duplicate_transactions($$) {
    my $ret_l = [];
    my $trans_l = shift;
    my $func = shift;
    my %dup_h ;
    for(my $i=0; $i<@$trans_l ; $i+=1) { my $key;
        if($dup_h{$key = &{$func}($trans_l->[$i])}) {
            print "remove duplicated transction: ".trans_str($trans_l->[$i])."\n" if $debug>=9;
        } else {
            push @$ret_l , $trans_l->[$i];
            $dup_h{&{$func}($trans_l->[$i])} = $trans_l->[$i]
        }
    }

    return $ret_l;
}

sub idi_file_read_record($) {
    local $_ = shift;
    if(!m/\s*\d+/) { return undef; }

    my @a = split /\s*\|\s*/;
    my ($src,$tgt);
    my $hash_id = "";
    my $typ = $a[$idi_header_h{Type}];
    my $opcode = $a[$idi_header_h{Opcode}];
    my %rec = ( 
        LID=>$a[$idi_header_h{LID}],
        PID=>$a[$idi_header_h{PID}],
        direction=>$typ, 
        cmd=>$opcode,
        address=>big_hex($a[$idi_header_h{Address}]),
        rec_type=>"idi",
        typ=>$typ,
        count=>++$idi_header_h{count},
        tick=>$a[$idi_header_h{Time}], # Simulatiopn time
        Unit=>$a[$idi_header_h{Unit}],
    );
    
    if($cpu_proj eq "lnl" or $cpu_proj eq "cbb" && $ACERUN_CLUSTER=~/^ccf/) {
        ($src,$tgt) = split("/",$a[$idi_header_h{"Src/Tgt"}]);
        if($src eq "-") { $src = undef; }
        $rec{UnitU} = $rec{Unit};
        if($src eq "--") { 
            $rec{Unit} .= "-".$tgt;
        } elsif($tgt eq "--") { 
            $rec{Unit} .= "-".$src;
        } elsif(defined($tgt)) { 
            if($typ eq "U2C RSP") { 
                $rec{Unit} .= "-".$tgt;
                $hash_id = $src;
            } elsif($typ eq "C2U DATA") { 
                $rec{Unit} .= "-".$src;
                $hash_id = $tgt;
            } elsif($typ eq "U2C REQ") { 
                $rec{Unit} .= "-".$tgt;
                $hash_id = $src;
            } elsif($typ eq "C2U RSP") { 
                $rec{Unit} .= "-".$src;
                $hash_id = $tgt;
            } else {
                $rec{Unit} .= "-".$src;
            }
        } else {
            $rec{Unit} .= "-".$a[$idi_header_h{"Src/Tgt"}];
        }
    } else {
        $rec{UnitU} = $rec{Unit};
    }

    if(/SlfSnp=0/i) { $rec{slfsnp_bad} = 0; }

    if($cpu_proj eq "adl") {
        $rec{tick}=~s/ *ps *//;
    }

    if(($rec{cmd} eq "WCILF_NS" or $rec{cmd} eq "WCIL_NS") && ($cpu_proj eq "lnl" || $cpu_proj eq "adl" || $cpu_proj eq "cbb")) {
        mark_non_snoop_addr(\%rec);
    }

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    if($typ=~/DATA/) {
        $rec{data} = lc($a[$idi_header_h{Data}]);
        $rec{data} =~ s/ //g;
        $rec{Chunk} = $a[$idi_header_h{Chunk}];
        if(/bogus=1/) { $rec{bogus}=1; }
    } elsif($typ=~/C2U REQ/) {
        if(my $new_cmd=$idi_cmd_conv{$rec{cmd}}) { $rec{cmd} = $new_cmd; };
        $rec{src_ch_rd} = $rec{src_ch_tc} = get_ch_id($a[$idi_header_h{Unit}]."_".$a[$idi_header_h{Lpid}]);
        $rec{id}  = $ch_name_l[$rec{src_ch_tc}]."_id_".$a[$idi_header_h{Cqid}];
        $rec{mktme_address} = $rec{address}; $rec{address} &= $sys_full_addr_mask;
    } elsif($typ=~/U2C REQ/) {
        $rec{src_ch_rd} = $rec{src_ch_tc} = get_ch_id($a[$idi_header_h{Unit}]."_".$a[$idi_header_h{Lpid}]);
        $rec{address} &= $sys_full_addr_mask;
    }

    $rec{cid}  = $a[$idi_header_h{Cqid}] if $a[$idi_header_h{Cqid}] ne "-";
    $rec{uid}  = $a[$idi_header_h{Uqid}].$hash_id if $a[$idi_header_h{Uqid}] ne "-";

    if(defined($scbd->{MemWr_chs}) and ($opcode eq "WOWrInv" || $opcode eq "WOWrInvF")) {
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs}->{$rec{UnitU}},"tick_end");
        merge_ns_read_channels (\%rec,$scbd->{MemRd_chs}->{$rec{UnitU}},"tick_go");
        #$rec{src_ch_tc} = append_ch_id($rec{src_ch_tc},"_WO");
    } elsif(defined($scbd->{MemWr_chs}) and ($opcode eq "WrInv" || $opcode eq "WrInvF")) {
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs}->{$rec{UnitU}},"tick_end");
        #merge_ns_read_channels (\%rec,$scbd->{MemRd_chs}->{$rec{UnitU}},"tick_go");
        #$rec{src_ch_tc} = append_ch_id($rec{src_ch_tc},"_WO");
    } elsif(defined($scbd->{MemWr_chs}) and ($opcode eq "DirtyEvict" || $opcode eq "MemWr" || $opcode eq "ItoMWr")) {
        if($e2e_fast_mode) {
            merge_ns_write_channels(\%rec,$scbd->{MemWr_chs}->{$rec{UnitU}},"tick_end");
        } else {
            $rec{src_ch_tc} = append_ch_id($rec{src_ch_tc},sprintf("_wg%04d",++$scbd->{MemWr_chs}->{GT_WR_count}));
        }
        #merge_ns_read_channels (\%rec,$scbd->{MemRd_chs}->{$rec{UnitU}},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_CCF_WCIL}) and !($rec{UnitU} =~ /$ICELAND_IDI/) and ($opcode=~/WCIL/)) {
        $rec{src_ch_rd} = append_ch_id($rec{src_ch_tc},"_RC".addr_str($rec{address} & $sys_addr_mask));
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_CCF_WCIL}->{$rec{UnitU}},"tick_end");
        #FIXME:need to return this performance feature#merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_CCF_WCIL}->{$rec{UnitU}},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_Atom}) and ($rec{UnitU} =~ /$ICELAND_IDI/) and ($opcode=~/WCIL/)) {
        $rec{src_ch_rd} = append_ch_id($rec{src_ch_tc},"_RC".addr_str($rec{address} & $sys_addr_mask));
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_Atom_WCIL},"tick_end");
        #FIXME:need to return this performance feature#merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_Atom_WCIL},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_Atom}) and ($rec{UnitU} =~ /$ICELAND_IDI]/) and ($opcode=~/WOWrInv/)) {
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_Atom},"tick_end");
        merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_Atom},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_Atom}) and ($rec{UnitU} =~ /$ICELAND_IDI/) and ($opcode=~/WIL|ITOMWR/)) {
        merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_Atom},"tick_end");
        #merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_Atom},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_Atom}) and ($rec{UnitU} =~ /$ICELAND_IDI/) and ($opcode=~/WBMTOI|WBMTOE/)) {
        if($e2e_fast_mode) {
            merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_Atom},"tick_end");
        } else {
            $rec{src_ch_tc} = append_ch_id($rec{src_ch_tc},sprintf("_wg%04d",++$scbd->{MemWr_chs_Atom}->{GT_WR_count}));
        }
        #merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_Atom},"tick_go");
    } elsif(defined($scbd->{MemWr_chs_Atom}) and ($rec{UnitU} =~ /$ICELAND_IDI/) and ($opcode=~/MEMPUSHWR/)) {
        if($e2e_fast_mode) {
            merge_ns_write_channels(\%rec,$scbd->{MemWr_chs_Atom},"tick_end");
        } else {
            $rec{src_ch_tc} = append_ch_id($rec{src_ch_tc},sprintf("_wa%04d",++$scbd->{MemWr_chs}->{AT_WR_count}));
        }
        merge_ns_read_channels (\%rec,$scbd->{MemRd_chs_Atom},"tick_go");
    }


    return \%rec;
}

sub dup_idi_rec($) {
    my ($rec_ptr) = @_;
    my $ret_rec = {};
    for(keys %$rec_ptr) { 
        if($_ ne "data_wr" && $_ ne "data_rd") {
            $ret_rec->{$_} = $rec_ptr->{$_};
        }
    }
    return $ret_rec; 
}

sub src_ch_chop_tid($) {
    my $src_ch = $_[0];
    $src_ch=~s/\d+$//;
    return $src_ch;
}

sub check_trans_uri($$) {
    my ($rec_ptr1,$rec_ptr2) = @_;
    if(($rec_ptr1->{address}>>6) != ($rec_ptr2->{address}>>6)) {
        print_ERROR("112 ERROR: These two transaciton with the same URI, does not have the same address:\n    ".trans_str($rec_ptr1)."    ".trans_str($rec_ptr2));
        $exit_code=1;
    }
    return undef;
}

sub get_trans_by_uri($$$) {
    # Get the transaction with the URI before this $rec_ptr
    my ($uri_l,$rec_ptr,$tick_name) = @_;
    if(!defined($uri_l)) { return undef; }
    my $tick;
    if(defined($rec_ptr)) { 
        $tick = $rec_ptr->{$tick_name};
        if(defined($rec_ptr->{tick_beg}) and $rec_ptr->{tick_beg}!=$tick) {
            die_ERROR("071 ERROR: FIXME: Need to remove this");
        }
    }
    my $tr = undef;
    my $max_i = 1*@$uri_l;
    if($max_i==1) {
        $tr = $uri_l->[$max_i-1];
    } elsif(!$max_i) {
        return undef;
    } elsif(!defined($tick)) {
        $tr = $uri_l->[$max_i-1];
    } else {
        for(my $i=0; $i<$max_i ; $i+=1) {
            if($uri_l->[$i]->{tick}>$tick) { last }
            $tr = $uri_l->[$i];
            if(defined($tr->{tick_beg}) and $tr->{tick_beg}!=$tr->{tick}) {
                die_ERROR("072 ERROR: FIXME: Need to remove this");
            }
        }
    }
    return $tr;
}

sub assign_rec_parent_idx($) { 
    my $trans_l = shift;
    if(!defined($trans_l)) { return 1; } 
    # my $parent_idx_count = 0;
    for my $rec_ptr (@$trans_l) {
        $rec_ptr->{idx} = $parent_idx_count++;
    }
    return 0;
}

sub push_RDCURR_keep_order($$) {
    my ($trans_l,$tr) = @_; die "Bad array pointer trans_l!" unless $trans_l;
    my $i = 0;
    my $max = 1*@$trans_l;
    my $push_i=$max;
    my $addr6 = $tr->{address}>>6;
    if($max>=1) {
        for($i=$max-1; $i>=0; $i-=1) {
            my $rec_ptr = $trans_l->[$i];
            if($rec_ptr->{tick}>$tr->{tick}) {
                $push_i = $i;
            } elsif($rec_ptr->{tick_beg}<$tr->{tick_beg}) {
                last;
            }
        }
    }
    for($i=$max; $i>0 && $i>$push_i; $i-=1) {
        $trans_l->[$i] = $trans_l->[$i-1];
    }
    $trans_l->[$push_i] = $tr;
}

sub idi_rec_fix_data($) {
    my ($rec_ptr) = @_;
    my @ret_rec_l = ();
    if(defined($rec_ptr->{data_rd})) {
        if(defined($rec_ptr->{data_wr})) {
            if($rec_ptr->{cmd}=~/^RFOWR/) {
                my $new_rec_ptr = dup_idi_rec($rec_ptr);
                $new_rec_ptr->{cmd} = "DRD";
                $new_rec_ptr->{data} = $rec_ptr->{data_rd};
                push @ret_rec_l,$new_rec_ptr;
                $rec_ptr->{cmd} = "WBMTOI";
                $rec_ptr->{data} = $rec_ptr->{data_wr};
                undef $rec_ptr->{data_rd};
                undef $rec_ptr->{data_wr};
            } else {
                die_ERROR("039 ERROR: This un-intentified IDI opcode have both dara_rd & data_wr : $rec_ptr->{line}");
            }
        } else {
            $rec_ptr->{data} = $rec_ptr->{data_rd};
            undef $rec_ptr->{data_rd};
        }
    } elsif(defined($rec_ptr->{data_wr})) {
        $rec_ptr->{data} = $rec_ptr->{data_wr};
        undef $rec_ptr->{data_wr};
    }
    if(defined($rec_ptr->{snp_rec_l})) {
        my $find_cnt = 0;
        for my $snp_rec (@{$rec_ptr->{snp_rec_l}}) {
            if(!defined($snp_rec->{data_wr})) { next }
            $snp_rec->{src_ch_tc} = $rec_ptr->{src_ch_tc};
            if($debug>=3) {
                print "Found snp_rec:$snp_rec->{line}";
                print " For this rec:$rec_ptr->{line}"; 
            }
            $find_cnt+=1;
            if($find_cnt>1) {
                die_ERROR("046 ERROR: Found more that one FwdM simultaniously. \n  snp_rec: $snp_rec->{line}\n  orig_rec: $rec_ptr->{line}\n");
            }
            idi_rec_fix_data($snp_rec);
            push @ret_rec_l,$snp_rec;
        }
    }
    push @ret_rec_l,$rec_ptr;
    return (@ret_rec_l);
}

sub idi_find_and_push_snp_rec_l($$) {
    my ($trans_l,$tr) = @_;
    my $cl_addr = $tr->{address}&0xFFFFFFFF_FFFFFFC0;
    my $idx = (@$trans_l)-1;
    my $tick_finish = $tr->{tick};
    # Search to find if there was a FwdM on this address 
    for(; $idx>=0 ;$idx-=1) {
        my $snp_rec = $trans_l->[$idx];
        if($snp_rec->{tick}<$tick_finish) { last };
        if(($snp_rec->{address}&0xFFFFFFFF_FFFFFFC0) == $cl_addr
                and $snp_rec->{cmd}=~/BACKINV|SNPCODE|SNPDATA|SNPINV|SNPCUR|SELFSNPINV/
                and $snp_rec->{PID} eq $tr->{LID}) {
            push @{$tr->{snp_rec_l}},$snp_rec;
        }
    }
}

sub idi_file_reader($$) {
    my $fd = shift;
    local $scbd = shift;
    local $WO_count = 0;
    my %idi_cid_h;
    my %EXTCMP_idi_cid_h;
    my %idi_uid_h;
    my %GT_NS_C2U_h;
    my $count=0;
    my $is_Spec_Snp = $cpu_proj eq "lnl";
    my $spec_snp_count = 0; # In LNL snoop are speculative
    my $gtcxl_idi_filter = (@gtcxl_idi_filter_l ? " (".join("|",@gtcxl_idi_filter_l).") " : undef);
    my $WCIL_is_skip_l = [];
    if($cpu_proj eq "adl") {
        $scbd->{tick_mul}=$tick_mul;
    } else {
        $scbd->{tick_mul}=$tick_mul*1000.0;
    }
    my $MKTME_EN = ($scbd->{filename}=~/cxl.log/ ? 0 : $CCF_MKTME_EN);
    if($idi_header_h{Time}) { return undef; }
    $scbd->{U}->{all} = [];

    while(<$fd>) {
            my $line = $_;
        my $is_idp_snp = index($line," IDP")>=0;
        next unless $line=~/^\s*\d+(\.\d+)?\s/;
        next if defined($gtcxl_idi_filter) and $line=~/$gtcxl_idi_filter/; 
        next if $line=~/\| reset /;
        if(!$is_idp_snp) {

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem

            if($rec_ptr->{Unit}=~/IDP/) { next; }

            if($rec_ptr->{typ} eq "C2U REQ") {
                $count+=1;
                if($rec_ptr->{cmd}=~/NSW/) {
                    $GT_NS_C2U_h{$rec_ptr->{Unit}} = $rec_ptr;
                } else {   
                    $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} = $rec_ptr;
                }
                if($MKTME_EN and $CCF_MKTME_MASK and ($rec_ptr->{mktme_address}>>$sys_addr_mktme_bit) & 0xF & $CCF_MKTME_MASK) {
                    # find whether this tranction is canceled by the MKTME_MAKS
                    $rec_ptr->{canceled} = 1;
                }
                if($rec_ptr->{cmd}=~/WCIL|LLCWB|LLCWBINV|CLWB|CLWb|CLFLUSHOPT|WOWrInv|ITOMWR_WT|NSWF|NSW/) {
                    push @{$EXTCMP_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}}->{req_l}},$rec_ptr;
                }
                if($rec_ptr->{cmd} =~ /ITOMWR_WT|MEMPUSHWR|WCIL|WOWrInv|WIL|NSWF|NSW/)  {
                    push @{$scbd->{UC_WR_cmd}->{$rec_ptr->{LID}}},$rec_ptr;
                }
            } elsif($rec_ptr->{typ} eq "U2C REQ") {
                # This will record BACKINT opcodes too.
                $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}} = $rec_ptr;

                if($rec_ptr->{cmd}=~/SNPINV|SNPCUR|BACKINV/) {
                    my $addr6 = ($rec_ptr->{address}>>6);
                    # If we snoop a read that got GO but no data, we snoop it, because it will get MoNuke in read core
                    while(my ($k,$read_rec) = each %{$idi_cid_h{$rec_ptr->{Unit}}}) {
                        if($addr6 == ($read_rec->{address}>>6) and $read_rec->{tick_go} and $read_rec->{cmd}=~/^(RDCURR|RFO|DRD|CRD|PRD)/) {
                            if(length($read_rec->{data_rd})<128) {
                                # if not all data received it is bad
                                $read_rec->{slfsnp_bad} = 1; # Signals that this transaction is bad (got MoNuke)
                            }
                        }
                    }
                }
            } elsif($rec_ptr->{typ} =~ /DATA/) {
                my $tr;
                if($rec_ptr->{typ} =~ /C2U/) {
                    my $GT_NS_rec = $GT_NS_C2U_h{$rec_ptr->{Unit}};
                    if($GT_NS_rec and $GT_NS_rec->{tick} == $rec_ptr->{tick}) {
                        $tr = $GT_NS_rec;
                        $idi_uid_h{$rec_ptr->{UnitU}}->{ $rec_ptr->{uid} } = $tr; # Next time we will know this uid
                        $GT_NS_C2U_h{$rec_ptr->{Unit}} = undef;
                    } else {
                        $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{ $rec_ptr->{uid} };
                    }
                } else {
                    $tr = $idi_cid_h{$rec_ptr->{Unit}}->{ $rec_ptr->{cid} };
                }
                if(!defined($tr)) {
                    die_ERROR("167 ERROR: Can not match IDI transaction by id. cid=$rec_ptr->{cid} uid=$rec_ptr->{uid}.\n  Trans: $rec_ptr->{line}\n");
                }
                my $data_key = (($rec_ptr->{typ}=~/C2U/) ? "data_wr" : "data_rd");
                if(defined($tr)) {
                    my $skip_uri_chk = $::skip_uri_chk || ($cpu_proj eq "lnl" && defined($tr->{$data_key})); #fixme: need to remove this mask to the second data chunk uri check after Amal will fix the EMU_URI_STITCH bug on it.
                    if(defined($tr->{$data_key})) { 
                        $tr->{$data_key."chunks"}->{(1*$rec_ptr->{Chunk})} += 1;
                        if($rec_ptr->{Chunk} eq "0011" or $rec_ptr->{Chunk} eq "11" or $rec_ptr->{Chunk} eq "01") {
                            $tr->{$data_key} = $tr->{$data_key}.$rec_ptr->{data};
                        } else {
                            $tr->{$data_key} = $rec_ptr->{data}.$tr->{$data_key};
                        }
                        for my $k (keys %{$tr->{$data_key."chunks"}}) {
                            if($k eq "0" and $tr->{$data_key."chunks"}->{$k}>=2) { next }
                            if($tr->{$data_key."chunks"}->{$k}>=2) {
                                die_ERROR("127 ERROR: Bad chunk id in this trans : $rec_ptr->{line}\n");
                            }
                        }
                        undef $tr->{$data_key."chunks"};
                    } else {
                        $tr->{$data_key} = $rec_ptr->{data};
                        $tr->{$data_key."chunks"}->{(1*$rec_ptr->{Chunk})} += 1;
                        if($tr->{cmd}=~/RDCURR|PRD/){ 
                            push_RDCURR_keep_order($scbd->{U}->{all}, $tr); 
                        }
                    }
                    if($tr->{cmd}=~/^WCIL/ && ($cpu_proj ne "adl")) { }
                    elsif($tr->{cmd}=~/^WOWrInv/) { } # this command get the tick_end from EXTCMP
                    else { idi_update_tick_end($tr,$rec_ptr->{tick}); }
                    if($rec_ptr->{bogus}) { 
                        $tr->{bogus}=1;  
                        print "Cought bogus=1 data trans : $tr->{line}" if $debug>=6; 
                    }
                    if($debug>=3) {
                        print "In   :id=$rec_ptr->{id}: ".$tr->{line};
                        print " Out :id=$rec_ptr->{id}: ".$line; 
                    }
                    if(!$skip_uri_chk && $rec_ptr->{LID} ne $tr->{LID} && $rec_ptr->{PID} ne $tr->{LID} and !($tr->{cmd}=~/^INT/)) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("032 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    if($rec_ptr->{Attributes}=~/byteen=(\w+)/) {
                        $tr->{byteen} = $1;
                    }
                };
            } elsif($rec_ptr->{cmd} =~ /IDI_GO/) {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    $tr->{count_go} = $rec_ptr->{count};
                    if($debug>=9) {
                        print "In   :id=$rec_ptr->{uid}: ".$tr->{line};
                        print " GO :id=$rec_ptr->{uid}: ".$line; 
                    }
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        if(!($tr->{cmd} =~/LLCPREF/)) {
                            die_ERROR("033 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                        }
                    }
                    idi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr unless $tr->{cmd}=~/RDCURR|PRD/; # The PRD (and RDCURR) will be handled by push_RDCURR_keep_order
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    idi_update_tick_end($tr,$rec_ptr->{tick});
                    if($line=~/state=GO_M/) { $tr->{go_state} = "GO_M"; } 
                    if($line=~/state=GO_E/) { $tr->{go_state} = "GO_E"; }
                };
            } elsif($rec_ptr->{typ} eq "U2C RSP") {
              if($rec_ptr->{cmd} =~ /WRITEPULL/) {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        die_ERROR("034 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("044 ERROR: Can not match IDI transaction by cid. cid=$rec_ptr->{cid}.\n  Trans: $rec_ptr->{line}\n");
                }
                $tr->{uid} = $rec_ptr->{uid};
                if($rec_ptr->{cmd} =~ /GO_WRITEPULL/) {
                    idi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    if($tr->{cmd}=~/^WCIL/ && ($cpu_proj ne "adl")) { $tr->{tick_go_writepull} = $rec_ptr->{tick}; }
                    else { 
                        $tr->{tick_go} = $rec_ptr->{tick};
                        idi_update_tick_end($tr,$rec_ptr->{tick});
                    }
                    if($tr->{cmd}=~/^ITOMWR_WT/ && $rec_ptr->{cmd} eq "GO_WRITEPULL" && ($cpu_proj ne "adl")) { 
                        # when the ITOMWR_WT gets GO_WRITEPULL it will not get EXTCMP. (only if it gets FAST_GO_WRITEPULL)
                        push @{$EXTCMP_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}}->{cmp_l}},$rec_ptr;
                    }
                }
                $idi_uid_h{$rec_ptr->{UnitU}}->{$tr->{uid}} = $tr;
              } elsif($rec_ptr->{cmd}=~/FwdM|FwdV/) {
                # Correct the Snoop response like : RspIFwdMO
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if($rec_ptr->{LID} ne $tr->{LID}) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("042 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("041 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                $tr->{snp_rsp_cmd} = $rec_ptr->{cmd};
              } elsif($rec_ptr->{cmd} eq "EXTCMP" or $rec_ptr->{cmd} eq "FASTGO_EXTCMP") {
                # give the WCIL* transaction the end time and go time of the EXTCMP
                my $EXTCMP_h = $EXTCMP_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(!defined($EXTCMP_h) or !@{$EXTCMP_h->{req_l}} or 1*@{$EXTCMP_h->{cmp_l}}>=1*@{$EXTCMP_h->{req_l}}) {
                    die_ERROR("400 ERROR: fail to match EXTCMP. Trans: $rec_ptr->{line}\n");
                }
                push @{$EXTCMP_h->{cmp_l}},$rec_ptr;
                if($cpu_proj ne "adl" and 1*@{$EXTCMP_h->{cmp_l}}==1*@{$EXTCMP_h->{req_l}}) {
                    for my $tr (@{$EXTCMP_h->{req_l}}) {
                        $tr->{tick_EXTCMP} = $rec_ptr->{tick}; 
                        if($tr->{cmd}=~/WCIL/) { 
                            $tr->{tick_end} = $tr->{tick_go} = $rec_ptr->{tick}; 
                            # check whether some other command got go during the WCIL
                            if(!($cpu_proj eq "lnl" && $tr->{Unit} eq "IA_IDI_4" && !$skip_e2e_write_chk)) {
                                for my $prev_wr (@{$scbd->{U}->{all}}) {
                                    if($prev_wr->{cmd}=~/DirtyEvict|WOWrInv|WIL|WBMTOI|WBMTOE|ITOMWR|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SELFSNPINV|ITOMWR_WT|SNPCURR/) {
                                        if(($prev_wr->{address}>>6)==($tr->{address}>>6) && $prev_wr->{tick_go}>=$tr->{tick_go_writepull} && $prev_wr->{tick_go}<=$tr->{tick_go}) {
                                            print "WARNING: Skip Address  ".addr_str($rec_ptr->{address})." because WCIL has other write in between. $tr->{line}" if $debug>=8;
                                            push @$WCIL_is_skip_l, [$tr,$prev_wr]; # i will check at the end of the file read whether this is a real contracition or a false sharing
                                            if($prev_wr->{PID} eq $tr->{LID}) {
                                                die_ERROR("401 ERROR: Trying to mask a WCIL due to its own shoop Trans: WCIL Trans : ".trans_str($tr)."\n SNP Trans : ".trans_str($prev_wr));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    $EXTCMP_h->{req_l} = ( );
                    $EXTCMP_h->{cmp_l} = ( );
                }
              }
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
              if($rec_ptr->{cmd}=~/FwdM|FwdV/) {
                # Take the Snoop response for IOP Snoops like : RspIFwdMO
                # FIXME: More accurate is to match the snoop data to the IOP write or read that did the snoop.
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("051 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    $tr->{tick_go} = $rec_ptr->{tick};
                    $tr->{tick_beg} = $tr->{tick};
                } else {
                    die_ERROR("052 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                if($is_Spec_Snp) { 
                    if($skip_e2e_write_chk) {
                        $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_Spec_SNP".addr_str($tr->{address} & $sys_addr_mask));
                    } else {
                        $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_Spec_SNP".++$spec_snp_count);
                    }
                } else {
                    $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_IOP_SNP");
                }
                push @{$scbd->{U}->{all}} , $tr;
              }
            }
        } elsif($is_idp_snp && index($line," DMI_")>=0) {
            # Handle the snoops
            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem
            if($rec_ptr->{typ} eq "U2C REQ") {
                push @{$scbd->{DMI_snp_h}->{$rec_ptr->{PID}}},$rec_ptr;
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
                my $tr = get_trans_by_uri($scbd->{DMI_snp_h}->{$rec_ptr->{PID}},undef,undef);
                if(defined($tr)) {
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_end} = $rec_ptr->{tick};
                    $tr->{rsp} = $rec_ptr->{cmd};
                }
            }
        }
    }

    # Fix the data_wr & data_rd to be only data.
    my @new_rec_l;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        if($rec_ptr->{bogus}) { next; }
        my @rec_ptr_l = (idi_rec_fix_data($rec_ptr));
        if($rec_ptr->{canceled} && $rec_ptr->{cmd}=~/PRD|DRD|RDCURR/) {
            if($rec_ptr->{data}=~/[^-xf]/) {
                print_ERROR("185 ERROR: This transation should get FF because is was caceled by CCF_MKTME_MASK : ".trans_str($rec_ptr));
                $exit_code = 1;
            }
        }
        if($rec_ptr->{canceled}) { next; }
        push @new_rec_l,@rec_ptr_l;
    }
    $scbd->{U}->{all} = \@new_rec_l;

    # Fix filter the PRD if needed
    if($argv{skip_PRD_opcode}) {
        $scbd->{U}->{all} = [ grep { $_->{cmd} ne "PRD" } @{$scbd->{U}->{all}} ];
    }

    # Checking for DRD_PREF with bad SelfSnoop that comes just after ITOM.
    # Since the ITOM takes ownership without writing data to LLC, there is bad data to LLC.
    # Next transaction from the same core, 
    my %addr_itom_h;
    # my $parent_idx_count = 0;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        undef ($rec_ptr->{snp_rec_l}); # just free memory
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(ITOM)$/i) {
            # If there is ITOM opcode then note it.
            $addr_itom_h{$addr6} = src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}]);
        } else {
            my $skip_undef = 0;
            my $was_itom = defined($addr_itom_h{$addr6});
            if($was_itom) {
                if($rec_ptr->{cmd}=~/^(LLCPREFRFO|DRD_PREF|CRD_PREF|DRD_OPT_PREF|CRD_OPT_PREF|RFO_PREF)/) {
                    if($addr_itom_h{$addr6} eq src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}])) {
                        if(defined($rec_ptr->{slfsnp_bad})) {
                            $rec_ptr->{slfsnp_bad} = 1;
                            $skip_undef = 1;
                        }
                    }
                } elsif($rec_ptr->{cmd}=~/^(WBSTOI|LLCPREFCODE|LLCPREFDATA)/) {
                    $skip_undef = 1;
                }
                # If there any transaction after the ITOM - then clear the flag.
                $addr_itom_h{$addr6} = undef unless $skip_undef;
            }
        }
        if($debug<=2) {
            # Remove redundant info
            delete $rec_ptr->{cid};
            delete $rec_ptr->{uid};
        }
    }

    # check whether a WCIL has another write contradicting it. If yes, mask this address.
    for my $pair (@$WCIL_is_skip_l) {
        my ($tr,$prev_wr) = ($pair->[0],$pair->[1]);
        if(length($tr->{data}) != length($prev_wr->{data}) or is_contradicts_cl_data($tr->{data},$prev_wr->{data})) {
            print "WARNING: Skip Address ".addr_str($tr->{address})." because WCIL has other write in between. $tr->{line}" if $debug>=9;
            mark_non_snoop_addr($tr);
        } else {
            1; # is_contradicts_cl_data($tr->{data},$prev_wr->{data});
        }
    }

    # Checking for RFO_PREF come with FFFFF data and the address was already owned by the cbo.
    # This case in ADL is ok 
    # oshitrit saidthis case can be skiped.
    my %addr_cbo_owner_h;
    if($cpu_proj eq "adl" || $cpu_proj eq "lnl"  || $cpu_proj eq "cbb" ) { for my $rec_ptr (@{$scbd->{U}->{all}}) {
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(CRD|DRD_PREF|DRD_OPT|RFO|DRD_SHARED)/i) {
            if($rec_ptr->{Unit} and ($addr_cbo_owner_h{$addr6} eq $rec_ptr->{Unit})) {
                if(defined($rec_ptr->{slfsnp_bad})) {
                    $rec_ptr->{slfsnp_bad} = 1; # oshitrit saidthis case can be skiped.
                } 
            }
        }

        if($rec_ptr->{cmd}=~/^(RFO|ITOM)/i) {
            $addr_cbo_owner_h{$addr6} = $rec_ptr->{Unit};
        } elsif($rec_ptr->{cmd}=~/^(SPEC_ITOM)/i and $rec_ptr->{go_state}=~/GO_M|GO_E/) {
            $addr_cbo_owner_h{$addr6} = $rec_ptr->{Unit};
        } elsif($rec_ptr->{cmd}=~/^(DRD)/i and $rec_ptr->{go_state}=~/GO_M|GO_E/) {
            $addr_cbo_owner_h{$addr6} = $rec_ptr->{Unit};
        } elsif($rec_ptr->{cmd}=~/(^MONITOR|CLWB|WCIL|WIL|WBMTOI|WBETOI|CLFLUSH)$/i) {
            $addr_cbo_owner_h{$addr6} = undef;
        } elsif($rec_ptr->{cmd}=~/(SNP)$/) { # Not including the BACKINV
            $addr_cbo_owner_h{$addr6} = undef;
        }
    } }

    if(!$args{skip_idi_dup_filter}) {
        # remove duplications. Ususally snoops with FwdM can be duplocation (in case of snoop on PRD for example)
        $scbd->{U}->{all} = remove_duplicate_transactions($scbd->{U}->{all},sub { $_[0]->{tick} . "_" . $_[0]->{Unit} . "_" . $_[0]->{cmd} . "_" . $_[0]->{typ} } ); 
    }

    assign_rec_parent_idx($scbd->{U}->{all});

    if($debug<8) {
        for my $rec_ptr (@{$scbd->{U}->{all}}) {
            delete $rec_ptr->{go_state}; delete $rec_ptr->{id}; delete $rec_ptr->{count_go}; delete $rec_ptr->{snp_rec_l}; delete $rec_ptr->{direction};
        }
    }

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

# this function is to find our what are the address that have coherent problem and should be skiped in LNL
# this addresses gets coherent write while the address was in the ownership of the CCF.
sub get_owned_slots($) {
    my $trans_l = shift;
    my $addr_got_ownership_h;
    my $addr_owned_h;
    my $debug = $::debug;

    # find all where the address was owned by coherent agent
    for my $rec_ptr (@$trans_l) {
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(MWr)/i and $rec_ptr->{state} eq "M") {
            # address got ownership by the preloader
            #if(!$addr_got_ownership_h->{$addr6}) {
                $addr_got_ownership_h->{$addr6}->{owned_tick_beg} = get_rec_tick_go($rec_ptr);
            #}
        } elsif($rec_ptr->{cmd}=~/^(RdOwn|CRD$|CRD_PREF|DRD|RFO|MONITOR|WBMTOI|WBETOI|ITOM)/i) {
            if(!$addr_got_ownership_h->{$addr6}) {
                $addr_got_ownership_h->{$addr6}->{owned_tick_beg} = get_rec_tick_go($rec_ptr); 
                $addr_got_ownership_h->{$addr6}->{owned_beg_rec} = $rec_ptr if $debug>=3;
                $addr_got_ownership_h->{$addr6}->{owned_src_ch} = ($rec_ptr->{src_ch_rd} or $rec_ptr->{src_ch_tc} or undef);
            }
        } elsif($rec_ptr->{cmd}=~/(EMemWr|PRD|WCIL|WOWrInv|WIL|CLFLUSH|UCRDF|CRD_UC)/i) {
            if($addr_got_ownership_h->{$addr6}) {
                $addr_got_ownership_h->{$addr6}->{owned_tick_end} = get_rec_tick_go($rec_ptr);
                $addr_got_ownership_h->{$addr6}->{owned_end_rec} = $rec_ptr if $debug>=3;
                push @{$addr_owned_h->{$addr6}},$addr_got_ownership_h->{$addr6};
                $addr_got_ownership_h->{$addr6} = undef;
            } elsif($rec_ptr->{cmd}=~/^(WILF|WIL)/i and $rec_ptr->{UnitU}=~/^(IA_|AT_)/ and !($rec_ptr->{UnitU} =~ /$ICELAND_IDI/)) { 
                # this transactions gets ownership during thier time period because they do read modify write
                $addr_got_ownership_h->{$addr6} = { };
                $addr_got_ownership_h->{$addr6}->{owned_tick_beg} = $rec_ptr->{tick_beg}; 
                $addr_got_ownership_h->{$addr6}->{owned_beg_rec} = $rec_ptr if $debug>=3;
                $addr_got_ownership_h->{$addr6}->{owned_end_rec} = $rec_ptr if $debug>=3;
                $addr_got_ownership_h->{$addr6}->{owned_src_ch} = ($rec_ptr->{src_ch_rd} or $rec_ptr->{src_ch_tc} or undef);
                $addr_got_ownership_h->{$addr6}->{owned_tick_end} = get_rec_tick_go($rec_ptr);
                push @{$addr_owned_h->{$addr6}},$addr_got_ownership_h->{$addr6};
                $addr_got_ownership_h->{$addr6} = undef;
            }
        }
    }

    # mask all range that was not finished, as finish with an infinite end time
    my $max_int = (~0>>1);
    for my $addr6 (keys %$addr_got_ownership_h) {
        my $range = $addr_got_ownership_h->{$addr6};
        if($range) {
            $range->{owned_tick_end} = $max_int;
            push @{$addr_owned_h->{$addr6}},$range;
        }
    }
    return $addr_owned_h;
}

sub ownership_on_address_beg($$) {
    my ($addr6,$rec_ptr) = @_;
    if(!$addr_got_ownership_h->{$addr6}) {
        $addr_got_ownership_h->{$addr6}->{owned_tick_beg} = get_rec_tick_go($rec_ptr) or die_ERROR("170 ERR: No tick_go to trans: ".trans_str($rec_ptr));;
    }
}

sub ownership_on_address_end($$) {
    my ($addr6,$rec_ptr) = @_;
    if($addr_got_ownership_h->{$addr6}) {
        $addr_got_ownership_h->{$addr6}->{owned_tick_end} = get_rec_tick_go($rec_ptr) or die_ERROR("171 ERR: No tick_go to trans: ".trans_str($rec_ptr));
        push @{$addr_owned_h->{$addr6}},$addr_got_ownership_h->{$addr6};
        $addr_got_ownership_h->{$addr6} = undef;
    }
}

# this function is to find our what are the address that have coherent problem and should be skiped in LNL
# this addresses gets coherent write while the address was in the ownership of the CCF.
sub get_owned_slots_CCF($) {
    my $trans_l = shift;
    local $addr_got_ownership_h;
    local $addr_owned_h;

    # find all where the address was owned by coherent agent
    for my $rec_ptr (@$trans_l) {
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if(!defined(get_rec_tick_go($rec_ptr))) {
            if($rec_ptr->{cmd} =~ /RDCURR/i) {
                next
            } else {
                die_ERROR("172 ERR: No tick_go to trans: ".trans_str($rec_ptr));
            }
        }
        if($rec_ptr->{cmd}=~/^(WbMtoI|WbEtoI)/ and $rec_ptr->{Unit}=~/^SOC_CCF_LINK/) { # WB from CCF will end ownership
            ownership_on_address_end($addr6,$rec_ptr);
        } elsif($rec_ptr->{cmd}=~/^(SnpLInv|SnpLData|SnpLCode|SnpLFlush|SnpL)/ and $rec_ptr->{Unit}=~/^SOC_CCF_LINK/) { # SNP to CCF with RspI* will end ownership
            if($rec_ptr->{snp_rsp}=~/^RspI/) {
                ownership_on_address_end($addr6,$rec_ptr);
            }
        } elsif($rec_ptr->{cmd}=~/^(RdOwn|CRD|DRD|RFO|MONITOR|ITOM)/i) {
            if($rec_ptr->{Unit}=~/^IA_IDI_[0123]/) {
                ownership_on_address_beg($addr6,$rec_ptr); # owership requested by IA core, so ccf got ownership
            } elsif($rec_ptr->{cmd}=~/^(RdOwn|RFO|ITOM)/i) {
                ownership_on_address_end($addr6,$rec_ptr); # ownership requested by another device, so ccf loose ownership.
            }
        } elsif($rec_ptr->{cmd}=~/(EMemWr|PRD|WCIL|WOWrInv|WIL|CLFLUSH|UCRDF)/i) {
            ownership_on_address_end($addr6,$rec_ptr); # a device snoop the address so CCF loose ownership 
        }
    }

    # mask all range that was not finished, as finish with an infinite end time
    my $max_int = (~0>>1);
    for my $addr6 (keys %$addr_got_ownership_h) {
        my $range = $addr_got_ownership_h->{$addr6};
        if($range) {
            $range->{owned_tick_end} = $max_int;
            push @{$addr_owned_h->{$addr6}},$range;
        }
    }
    return $addr_owned_h;
}

sub is_addr_owned($$) {
    my ($addr_owned_h,$rec_ptr) = @_;
    my $addr6 = $rec_ptr->{address}>>6;
    my $range_l = $addr_owned_h->{$addr6};
    my $found = 0;
    if($range_l) {
        my $max_i = 1*@$range_l;
        for(my $i; $i<$max_i ; $i++) {
            if($rec_ptr->{tick_beg}<$range_l->[$i]->{owned_tick_end} and $rec_ptr->{tick_end}>=$range_l->[$i]->{owned_tick_beg}) {
                if($rec_ptr->{cmd}=~/(WCIL)/i 
                    and defined($range_l->[$i]->{owned_src_ch})
                    and index($ch_name_l[$rec_ptr->{src_ch_rd}],$ch_name_l[$range_l->[$i]->{owned_src_ch}]) == 0 # check that both trans are from the same core
                    ) {
                    # When WCIL happens while address is owned by the same core 
                    1; # it does not considered coh & WCIL conflict
                } else {
                    $found = 1;
                    last;
                }
            }
        }
    }
    return $found;
}

sub find_non_coh_writes($$) {
    my $addr_owned_h = shift;
    my $trans_l = shift;
    
    for my $rec_ptr (@$trans_l) {
        # In case there is an 
        if($rec_ptr->{cmd}=~/^(AWADDR|MWR|MemWr)/i and $rec_ptr->{ns}) {
            if(is_addr_owned($addr_owned_h,$rec_ptr)) {
                mark_non_snoop_addr($rec_ptr);
            }
        } elsif($rec_ptr->{cmd}=~/(WCIL)/i) {
            if(is_addr_owned($addr_owned_h,$rec_ptr)) {
                mark_non_snoop_addr($rec_ptr);
            }
        } elsif($rec_ptr->{cmd}=~/(ARADDR)/i and $rec_ptr->{ns}) {
            if(is_addr_owned($addr_owned_h,$rec_ptr)) {
                $rec_ptr->{slfsnp_bad} = 1; # Signals that this transaction is bad (ns while address is owned)
            }
        }
    }
}

sub cfi_trk_file_read_record_CFI7($) {
    local $_ = shift;
    if(!m/\s*\d+/) { return undef; }
    if(!m/SOC_CCF_LINK|SOC_ICELAND|SOC_IAX|SOC_DNC0|SOC_MEDIA|SOC_SVTU|SOC_DEIOSF|SOC_IAX|SOC_IPU|SOC_VPU|SOC_INOC_D2D|SOC_PUNIT/) { return undef; }

    s/SOC_IPU\d/SOC_IPU/; #s/IPU_\d\(\S*/IPU/g;
    s/SOC_VPU\d/SOC_VPU/; #s/VPU_\d\(\S*/VPU/g;
    my @a = split /\s*\|\s*/;
    my $typ = $a[$idi_header_h{VC_ID}];
    my $ifc = $a[$idi_header_h{INTERFACE}];
    my $opcode = $a[$idi_header_h{OPCODE}];
    if($opcode =~/NcIOWr|NcMsgS|NCCmpU|IntPhysical|IntAck/i) { return undef; }
    if($a[$idi_header_h{PROTOCOL_ID}] eq "UPI.NC") { return undef; }
    $ifc =~ s/_\d$//;
    $typ = ($cfi_trk_typ_conv{$typ}->{$ifc} or die_ERROR("Bad opcode decode for typ=$typ ifc=$ifc line=$_"));
    my %rec = ( 
        LID=>$a[$idi_header_h{URI_LID}],
        PID=>$a[$idi_header_h{URI_PID}],
        direction=>$typ, 
        cmd=>$opcode,
        address=>(big_hex($a[$idi_header_h{ADDRESS}])&0x3f_ffffffff),
        rec_type=>"idi",
        typ=>$typ,
        count=>++$idi_header_h{count},
        tick=>$a[$idi_header_h{TIME}], # Simulatiopn time
        Unit=>$a[$idi_header_h{VC_NAME}],
    );

    if($rec{cmd}=~/ReqFwdCnflt|FwdCnfltO/) { return undef }; #no need to decode these opcodes

    $rec{UnitU} = $rec{Unit};
    #$rec{Unit} .= "-".$a[$idi_header_h{RSPID}];
    if($rec{UnitU} eq "SOC_INOC_D2D") {
        if($ifc eq "RECEIVE_DATA" or $ifc eq "RECEIVE_RSP") {
            $rec{Unit} = $rec{UnitU}."-".$a[$idi_header_h{DSTID}];
        } elsif($ifc eq "TRANSMIT_REQ" or $ifc eq "TRANSMIT_DATA") {
            $rec{Unit} = $rec{UnitU}."-".$a[$idi_header_h{RSPID}];
        } else {
            $rec{Unit} = $rec{Unit};
        }
    }

    $rec{cmd} =~s/\(.*$//;

    if(/SlfSnp=0/i) { $rec{slfsnp_bad} = 0; }

    if($cpu_proj eq "adl") {
        $rec{tick}=~s/ *ps *//;
    }

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    $rec{cid}  = $a[$idi_header_h{RTID}] if $a[$idi_header_h{RTID}] ne "-";
    $rec{uid}  = $a[$idi_header_h{HTID}] if $a[$idi_header_h{HTID}] ne "-";

    if($typ=~/DATA/) {
        $rec{data} = $a[$idi_header_h{DATA_3}].$a[$idi_header_h{DATA_2}].$a[$idi_header_h{DATA_1}].$a[$idi_header_h{DATA_0}];
        $rec{data} =~ s/ //g;
        $rec{Chunk} = $a[$idi_header_h{CHUNK}] ? "1100" : "0011";
        if(/bogus=1/) { $rec{bogus}=1; }
    }
    if($typ=~/C2U REQ/ or $rec{cmd}=~/WbMtoE|WbMtoS|WbEtoI|WbMtoI|MemWrPtl|MemWr/) {
        if(my $new_cmd=$cmd_conv{$rec{cmd}}) { $rec{cmd} = $new_cmd; };
        $rec{src_ch_tc} = get_ch_id($rec{Unit});
        $rec{id}  = $ch_name_l[$rec{src_ch_tc}]."_id_".$rec{cid}; 
        if($rec{cmd}=~/^(MemWr)$/ and $a[$idi_header_h{PROTOCOL_ID}]=~/^CXM/) { 
            $rec{ns}=1; 
        }
    }
    if($typ=~/U2C REQ/ or $rec{cmd}=~/snp/) {
        $rec{src_ch_tc} = get_ch_id($rec{Unit}."_Spec_SNP".++$spec_snp_count);
    }

    if(($ifc eq "TRANSMIT_DATA" or $ifc eq "TRANSMIT_REQ") and ($rec{Unit} eq "SOC_VPU" or $rec{Unit} eq "SOC_IPU")) {  
        $rec{cid} .= "-".$a[$idi_header_h{RSPID}];
    }
    if(($ifc eq "RECEIVE_RSP" or $ifc eq "RECEIVE_DATA") and   ($rec{Unit} eq "SOC_VPU" or $rec{Unit} eq "SOC_IPU")) {  
        $rec{cid} .= "-".$a[$idi_header_h{DSTID}];
    }

    if($ifc eq "RECEIVE_REQ" or $ifc eq "TRANSMIT_REQ") { 
        $rec{hbo_id} = hbo_hash_get_idx($rec{address}); 
    } elsif($ifc eq "TRANSMIT_DATA" or $ifc eq "TRANSMIT_RSP") { 
        if($a[$idi_header_h{DSTID}]=~/^HBO_([01])/) { $rec{hbo_id} = 1*$1; } 
    } elsif($ifc eq "RECEIVE_RSP") { 
        if($a[$idi_header_h{RSPID}]=~/^HBO_([01])/) { $rec{hbo_id} = 1*$1; } 
    }

    return \%rec;
}

sub cfi_find_and_push_snp_rec_l($$) {
    my ($trans_l,$tr) = @_;
    my $cl_addr = $tr->{address}&0xFFFFFFFF_FFFFFFC0;
    my $idx = (@$trans_l)-1;
    my $tick_finish = $tr->{tick};
    # Search to find if there was a FwdM on this address 
    for(; $idx>=0 ;$idx-=1) {
        my $snp_rec = $trans_l->[$idx];
        if($snp_rec->{tick}<$tick_finish) { last };
        if(($snp_rec->{address}&0xFFFFFFFF_FFFFFFC0) == $cl_addr
                and $snp_rec->{cmd}=~/BACKINV|SNPCODE|SNPDATA|SNPINV|SNPCUR|SELFSNPINV/
                and $snp_rec->{PID} eq $tr->{LID}) {
            push @{$tr->{snp_rec_l}},$snp_rec;
        }
    }
}

sub cfi_file_reader($$) {
    my $fd = shift;
    local $scbd = shift;
    local $WO_count = 0;
    my %idi_cid_h;
    my %idi_uid_h;
    my %sys_pref_idi_cid_h;
    my $count=0;
    my $is_Spec_Snp = $cpu_proj eq "lnl";
    local $spec_snp_count = 0; # In LNL snoop are speculative
    my $MemWr_chs = { count => 0 , prefix=>"_MemWr" };
    local $MemWr_chs_CCF_WBMtoI = { count => 0 , prefix=>"_WBMtoIES" };
    my $SpecWr_count;
    my $CCF_Wr_count;

    if($cpu_proj eq "adl") {
        $scbd->{tick_mul}=$tick_mul;
    } else {
        $scbd->{tick_mul}=$tick_mul*1000.0;
    }

    if($idi_header_h{Time}) { return undef; }
    $scbd->{U}->{all} = [];

    while(<$fd>) {
            my $line = $_;
        next unless $line=~/^\s*\d+(\.\d+)?\s/;
        next if $line=~/\| reset /;
        {

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem

            if($rec_ptr->{typ} eq "C2U REQ") {
                $count+=1;
                if($rec_ptr->{cmd} eq "PrefetchToSysCache") {
                    $sys_pref_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} += 1;
                } else {
                    $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} = $rec_ptr;
                }
                if($rec_ptr->{cmd} =~ /ITOMWR_WT|MEMPUSHWR|WCIL|WOWrInv|WIL/i)  {
                    push @{$scbd->{UC_WR_cmd}->{$rec_ptr->{LID}}},$rec_ptr;
                }
            } elsif($rec_ptr->{typ} eq "U2C REQ") {
                # This will record BACKINT opcodes too.
                $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = $rec_ptr;
                if($rec_ptr->{cmd}=~/SNPINV|SNPCUR|SnpLInv|SnpLData|SnpLCode|SnpLFlush/) {
                    $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                    my $addr6 = ($rec_ptr->{address}>>6);
                    # If we snoop a read that got GO but no data, we snoop it, because it will get MoNuke in read core
                    while(my ($k,$read_rec) = each %{$idi_cid_h{$rec_ptr->{Unit}}}) {
                        if($addr6 == ($read_rec->{address}>>6) and $read_rec->{tick_go} and $read_rec->{cmd}=~/^(RDCURR|RFO|DRD|CRD|PRD)/) {
                            if(length($read_rec->{data_rd})<128) {
                                # if not all data received it is bad
                                $read_rec->{slfsnp_bad} = 1; # Signals that this transaction is bad (got MoNuke)
                            }
                        }
                    }
                }
            } elsif($rec_ptr->{typ} =~ /DATA/) {
                if($rec_ptr->{cmd} =~ /MemWrPtl|MemWr|WbMtoI|WbMtoE|WbMtoS|WbEtoI|NcIOWr|NCIORd|NcMsgS|IntPhysical/i)  {
                    $rec_ptr->{uid}=$rec_ptr->{cid};
                    if($rec_ptr->{Chunk} eq "0011")  { $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                        $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} = $rec_ptr;
                        #$idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}} = $rec_ptr;
                        push @{$scbd->{UC_WR_cmd}->{$rec_ptr->{LID}}},$rec_ptr;
                        push @{$scbd->{U}->{all}} , $rec_ptr;
                        if($rec_ptr->{cmd} =~ /MemWrPtl|MemWr/i)  {
                            my $UnitName = $rec_ptr->{UnitU}; $UnitName=~s/MEDIA\d/MEDIA/; # makes the two media port as one channel
                            if(!defined($MemWr_chs->{$UnitName})) { $MemWr_chs->{$UnitName} = { count => 0 , prefix=>"_MemWr" }; };
                            merge_ns_write_channels($rec_ptr,$MemWr_chs->{$UnitName},"tick_end");
                        } elsif($rec_ptr->{cmd} =~ /WbMtoI|WbMtoE|WbMtoS/ and $rec_ptr->{Unit}=~/^SOC_CCF_LINK/) { 
                            if($no_CCF_write_merge) {
                                $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch_tc},"_ccf_Wr".sprintf("%04d",++$CCF_count));
                            } else {
                                merge_ns_write_channels($rec_ptr,$MemWr_chs_CCF_WBMtoI,"tick_go");
                            }
                        } elsif($rec_ptr->{cmd} =~ /WbEtoI/) { # there speculatinve write from CCF does not always gets to memory
                            $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch_tc},"_Spec_Wr".sprintf("%04d",++$SpecWr_count));
                        }
                    }
                }
                my $tr;
                if($rec_ptr->{typ} =~ /C2U/ and !($rec_ptr->{cmd}=~/MemWrPtl|MemWr|WbMtoI|WbMtoE|WbMtoS|WbEtoI/)) {
                    $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{ $rec_ptr->{uid} };
                } else {
                    $tr = $idi_cid_h{$rec_ptr->{Unit}}->{ $rec_ptr->{cid} };
                }
                if(!defined($tr)) {
                    die_ERROR("168 ERROR: Can not match IDI transaction by id.\n  Trans: $rec_ptr->{line}\n");
                }
                my $data_key = (($rec_ptr->{typ}=~/C2U/) ? "data_wr" : "data_rd");
                if(defined($tr)) {
                    my $skip_uri_chk = $::skip_uri_chk || ($cpu_proj eq "lnl" && defined($tr->{$data_key})); #fixme: need to remove this mask to the second data chunk uri check after Amal will fix the EMU_URI_STITCH bug on it.
                    if(defined($tr->{$data_key})) { 
                        if($rec_ptr->{cmd} eq "EMemWr" or $rec_ptr->{cmd} eq "EMemWrPtl" or $rec_ptr->{cmd} eq "EMemWr32B" or $rec_ptr->{cmd} eq "EMemWrPtl32B") { 
                            $tr->{tick_go} = $rec_ptr->{tick}; 
                        }
                        if($rec_ptr->{Chunk} eq "0011" or $rec_ptr->{Chunk} eq "11") {
                            $tr->{$data_key} = $tr->{$data_key}.$rec_ptr->{data};
                        } else {
                            if($tr->{cmd}=~/^F?MemWrCompress/) {
                                $rec_ptr->{data} = "0000000000000000000000000000000000000000000000000000000000000000";
                            }
                            $tr->{$data_key} = $rec_ptr->{data}.$tr->{$data_key};
                        }
                        if($tr->{cmd}=~/SnpLInv|SnpLData|SnpLCode|SnpLFlush/) {
                            #ccf WB of SnpLInv and SnpLData
                            push @{$scbd->{U}->{all}} , $tr;
                        }
                    } else {
                        $tr->{$data_key} = $rec_ptr->{data}; 
                        if($tr->{cmd}=~/^SnpL/) { 
                            $tr->{snp_rsp} = $rec_ptr->{cmd}; 
                            $tr->{tick_go} = $rec_ptr->{tick}; 
                        }
                    }
                    use_max_tick_end($tr,$rec_ptr->{tick}) unless $tr->{cmd}=~/MemWr/;
                    if($rec_ptr->{bogus}) { 
                        $tr->{bogus}=1;  
                        print "Cought bogus=1 data trans : $tr->{line}" if $debug>=6; 
                    }
                    if($debug>=3) {
                        print "In   :id=$rec_ptr->{id}: ".$tr->{line};
                        print " Out :id=$rec_ptr->{id}: ".$line; 
                    }
                    if(!$skip_uri_chk && $rec_ptr->{LID} ne $tr->{LID} and !($tr->{cmd}=~/^INT/)) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("032 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    if($rec_ptr->{Attributes}=~/byteen=(\w+)/) {
                        $tr->{byteen} = $1;
                    }
                };
            } elsif($rec_ptr->{cmd} =~ /IDI_GO/) {
              if($sys_pref_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}}) {
                $sys_pref_idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}} -= 1;
              } else {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    $tr->{count_go} = $rec_ptr->{count};
                    if($debug>=9) {
                        print "In   :id=$rec_ptr->{uid}: ".$tr->{line};
                        print " GO :id=$rec_ptr->{uid}: ".$line; 
                    }
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        if(!($tr->{cmd} =~/LLCPREF/)) {
                            die_ERROR("033 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                        }
                    }
                    cfi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                };
              }
            } elsif($rec_ptr->{typ} eq "U2C RSP") {
              if($rec_ptr->{cmd} =~ /WRITEPULL/) {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        die_ERROR("034 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("044 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }
                $tr->{uid} = $rec_ptr->{uid};
                if($rec_ptr->{cmd} =~ /GO_WRITEPULL/) {
                    cfi_find_and_push_snp_rec_l($scbd->{U}->{all},$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                }
                $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$tr->{uid}} = $tr;
              } elsif($rec_ptr->{cmd}=~/FwdM|FwdV/) {
                # Correct the Snoop response like : RspIFwdMO
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if($rec_ptr->{LID} ne $tr->{LID}) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("042 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("041 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                $tr->{snp_rsp_cmd} = $rec_ptr->{cmd};
              } elsif($rec_ptr->{cmd} eq "EXTCMP") {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_EXTCMP} = $rec_ptr->{tick};
                }
              } elsif($rec_ptr->{cmd} eq "Cmp") {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_end} = $rec_ptr->{tick};
                    if(!defined($tr->{tick_go})) {
                        $tr->{tick_go} = $rec_ptr->{tick};
                    }
                    if($tr->{cmd} =~ /MemWr32B|MemWrPtl32B/i) {
                        if(($tr->{address}&0x3f)>=32) {
                            # in case MemWr32B and we have a second CL chuck add xx-es before
                            $tr->{data_wr} =~ s/^xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx//;
                            $tr->{data_wr} =~ s/^----------------------------------------------------------------//;
                            $tr->{data_wr}.= "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
                        }
                    }
                    if($tr->{LID} ne $rec_ptr->{LID} and !$skip_bad_uri_filter) {
                        undef $tr->{LID}; # This is a URI error , so disregard it
                    }
                }
              } elsif($rec_ptr->{cmd} eq "CmpU") {
                my $tr = $idi_cid_h{$rec_ptr->{Unit}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_end} = $rec_ptr->{tick};
                    if(!defined($tr->{tick_go})) {
                        $tr->{tick_go} = $rec_ptr->{tick};
                    }
                }
              }
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
              if($rec_ptr->{cmd}=~/FwdM|FwdV/) {
                # Take the Snoop response for IOP Snoops like : RspIFwdMO
                # FIXME: More accurate is to match the snoop data to the IOP write or read that did the snoop.
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("051 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    $tr->{tick_go} = $rec_ptr->{tick};
                    $tr->{tick_beg} = $tr->{tick};
                } else {
                    die_ERROR("052 ERROR: Can not match IDI transaction by uid. \n  Trans: $rec_ptr->{line}\n");
                }

                if($is_Spec_Snp) { 
                    $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_Spec_SNP".++$spec_snp_count);
                } else {
                    $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_IOP_SNP");
                }
                push @{$scbd->{U}->{all}} , $tr;
              } elsif($rec_ptr->{cmd}=~/RspI/) { # RspI only capture the rsp opcode in the Snoop transaction
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    $tr->{snp_rsp} = $rec_ptr->{cmd};
                    $tr->{tick_go} = $rec_ptr->{tick}; 
                    push @{$scbd->{U}->{all}} , $tr; # stop also Snoop transactins with RspI for got_owned_slots_CCF
                }
              }
            }
        }
    }

    # Fix the data_wr & data_rd to be only data.
    my @new_rec_l;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        if($rec_ptr->{bogus}) { next; }
        push @new_rec_l,idi_rec_fix_data($rec_ptr);
    }
    $scbd->{U}->{all} = \@new_rec_l;

    # Checking for DRD_PREF with bad SelfSnoop that comes just after ITOM.
    # Since the ITOM takes ownership without writing data to LLC, there is bad data to LLC.
    # Next transaction from the same core, 
    my %addr_itom_h;
    # my $parent_idx_count = 0;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        undef ($rec_ptr->{snp_rec_l}); # just free memory
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(ITOM)$/i) {
            # If there is ITOM opcode then note it.
            $addr_itom_h{$addr6} = src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}]);
        } else {
            my $skip_undef = 0;
            my $was_itom = defined($addr_itom_h{$addr6});
            if($was_itom) {
                if($rec_ptr->{cmd}=~/^(LLCPREFRFO|DRD_PREF|CRD_PREF|DRD_OPT_PREF|CRD_OPT_PREF|RFO_PREF)/) {
                    if($addr_itom_h{$addr6} eq src_ch_chop_tid($ch_name_l[$rec_ptr->{src_ch_tc}])) {
                        if(defined($rec_ptr->{slfsnp_bad})) {
                            $rec_ptr->{slfsnp_bad} = 1;
                            $skip_undef = 1;
                        }
                    }
                } elsif($rec_ptr->{cmd}=~/^(WBSTOI|LLCPREFCODE|LLCPREFDATA)/) {
                    $skip_undef = 1;
                }
                # If there any transaction after the ITOM - then clear the flag.
                $addr_itom_h{$addr6} = undef unless $skip_undef;
            }
        }
        if($debug<=2) {
            # Remove redundant info
            delete $rec_ptr->{cid};
            delete $rec_ptr->{uid};
        }
    }

    # Checking for RFO_PREF come with FFFFF data and the address was already owned by the cbo.
    # This case in ADL is ok 
    # oshitrit saidthis case can be skiped.
    my %addr_cbo_owner_h;
    if($cpu_proj eq "adl") { for my $rec_ptr (@{$scbd->{U}->{all}}) {
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($rec_ptr->{cmd}=~/^(DRD_PREF|CRD_PREF|DRD_OPT_PREF|CRD_OPT_PREF|RFO_PREF)$/i) {
            if($rec_ptr->{Unit} and $rec_ptr->{data} eq "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff") {
            if($addr_cbo_owner_h{$addr6} eq $rec_ptr->{Unit}) {
                $rec_ptr->{slfsnp_bad} = 1; # oshitrit saidthis case can be skiped.
            } 
            }
        }

        if($rec_ptr->{cmd}=~/^(RFO)/i) {
            $addr_cbo_owner_h{$addr6} = $rec_ptr->{Unit};
        } elsif($rec_ptr->{cmd}=~/^(WOWrInv|WIL|WBMTOI|WBETOI)$/i) {
            $addr_cbo_owner_h{$addr6} = undef;
        }
    } }

    assign_rec_parent_idx($scbd->{U}->{all});

    if($debug<8) {
        for my $rec_ptr (@{$scbd->{U}->{all}}) {
            delete $rec_ptr->{go_state}; delete $rec_ptr->{id}; delete $rec_ptr->{count_go}; delete $rec_ptr->{snp_rec_l}; delete $rec_ptr->{direction};
            delete $rec_ptr->{typ}; delete $rec_ptr->{hbo_id};
        }
    }

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub ufi_trk_file_read_record($) {
    local $_ = shift;
    if(!m/\s*\d+/) { return undef; }
    if(!m/HW_COLLECTOR_UFI_BFM/) { return undef; }



    my @a = split /\s*\|\s*/;
    my $typ = $a[$ufi_header_h{VC_ID}];
    my $ifc = $a[$ufi_header_h{IFC_TYPE}]; my $ifc_ch = $a[$ufi_header_h{CHANNEL}];
    my $opcode = $a[$ufi_header_h{OPCODE}];
    if($opcode =~/NcIOWr|NcMsgS|NCCmpU|IntPhysical|IntAck/i) { return undef; }
    if($a[$ufi_header_h{PROTOCOL}] eq "UXI.NC") { return undef; }
    $ifc =~ s/_\d$//;
    $typ = ($ufi_trk_typ_conv{$typ}->{$ifc}->{$ifc_ch} or die_ERROR("Bad opcode decode for typ=$typ ifc=$ifc ifc_ch=$ifc_ch line=$_"));
    my %rec = ( 
        LID=>$a[$ufi_header_h{URI_LID}],
        PID=>$a[$ufi_header_h{URI_PID}],
        direction=>$typ, 
        cmd=>$opcode,
        address=>(big_hex($a[$ufi_header_h{ADDRESS}])&$sys_full_addr_mask),
        rec_type=>"idi",
        typ=>$typ,
        count=>++$ufi_header_h{count},
        tick=>$a[$ufi_header_h{TIME}], # Simulatiopn time
        Unit=>$a[$ufi_header_h{VC_NAME}].$a[$ufi_header_h{UFI_ID}], 
        UnitU=>$a[$ufi_header_h{VC_NAME}], 
        htype=>$a[$ufi_header_h{HEADER_TYPE}],
        ufi_inst=>$a[$ufi_header_h{UFI_ID}],
    );

    if($rec{cmd}=~/ReqFwdCnflt|FwdCnfltO/) { return undef }; #no need to decode these opcodes
    if($rec{htype} eq "SR-CD" && $ifc eq "A2F" && $ifc_ch eq "DATA") { return undef } # this is duplicated data

    $rec{cmd} =~s/\(.*$//;

    if(/SlfSnp=0/i) { $rec{slfsnp_bad} = 0; }

    if($cpu_proj eq "adl") {
        $rec{tick}=~s/ *ps *//;
    }
    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
    if(length($a[$ufi_header_h{RTID}]) and $a[$ufi_header_h{RTID}] ne "-") {
        $rec{cid_snp}  = $a[$ufi_header_h{RTID}];
        $rec{cid}      = $a[$ufi_header_h{RTID}] ."-". ($typ eq "U2C RSP" ? $a[$ufi_header_h{CRNID}] : $a[$ufi_header_h{CDNID}]);
    }
    $rec{uid}  = $a[$ufi_header_h{HTID}] if length($a[$ufi_header_h{HTID}]) and $a[$ufi_header_h{HTID}] ne "-";
    if($typ=~/DATA/) {
        $rec{data} = $a[$ufi_header_h{PAYLOAD_DATA}];
        $rec{data} =~ s/ //g;
        $rec{Chunk} = $a[$ufi_header_h{CHUNK}] ? "1100" : "0011";
        if(/bogus=1/) { $rec{bogus}=1; }
    }
    if($typ=~/C2U REQ/ or $rec{cmd}=~/WbMtoE|WbMtoS|WbEtoI|WbMtoI|MemWrPtl|MemWr/) {
        if(my $new_cmd=$cmd_conv{$rec{cmd}}) { $rec{cmd} = $new_cmd; };
        $rec{src_ch_tc} = get_ch_id($rec{UnitU});
        $rec{id}  = $ch_name_l[$rec{src_ch_tc}]."_id_".$rec{cid}; 
        if($rec{cmd}=~/^(MemWr)$/ and $a[$ufi_header_h{PROTOCOL_ID}]=~/^CXM/) { 
            $rec{ns}=1; 
        }
    }
    if($typ=~/U2C REQ/ or $rec{cmd}=~/snp/) {
        $rec{src_ch_tc} = get_ch_id($rec{UnitU}."_Spec_SNP".++$spec_snp_count);
    }

    return \%rec;
}

sub ufi_file_reader($$) {
    my $fd = shift;
    local $scbd = shift;
    local $WO_count = 0;
    my %idi_cid_h;
    my %idi_uid_h; my %snp_cid_h; my $snp_old_l = [ ];
    my %sys_pref_idi_cid_h;
    my $count=0;
    my $is_Spec_Snp = $cpu_proj eq "lnl";
    local $spec_snp_count = 0; # In LNL snoop are speculative
    my $MemWr_chs = { count => 0 , prefix=>"_MemWr" };
    local $MemWr_chs_CCF_WBMtoI = { count => 0 , prefix=>"_WBMtoIES" };
    my $SpecWr_count;
    my $CCF_Wr_count;

    if($cpu_proj eq "adl") {
        $scbd->{tick_mul}=$tick_mul;
    } else {
        $scbd->{tick_mul}=$tick_mul*1000.0;
    }

    if($ufi_header_h{Time}) { return undef; }
    $scbd->{U}->{all} = [];

    while(<$fd>) {
            my $line = $_;
        next unless $line=~/^\s*\d+(\.\d+)?\s/;
        next if $line=~/\| reset /;
        {

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line if $debug>=3; #save_mem

            if($rec_ptr->{typ} eq "C2U REQ") {
                $count+=1;
                if($rec_ptr->{cmd} eq "PrefetchToSysCache") {
                    $sys_pref_idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}} += 1;
                } else {
                    $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}} = $rec_ptr;
                }
                if($rec_ptr->{cmd} =~ /ITOMWR_WT|MEMPUSHWR|WCIL|WOWrInv|WIL/i)  {
                    push @{$scbd->{UC_WR_cmd}->{$rec_ptr->{LID}}},$rec_ptr;
                }
            } elsif($rec_ptr->{typ} eq "U2C REQ") {
                # This will record BACKINT opcodes too.
                if(defined($rec_ptr->{cid})) { $snp_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid_snp}} = $rec_ptr; } #ufi
                $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}} = $rec_ptr;
                if($rec_ptr->{cmd}=~/SNPINV|SNPCUR|SnpLInv|SnpLData|SnpLCode|SnpLFlush|SnpData|SnpCode|SnpInvOwn/) {
                    $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                    my $addr6 = ($rec_ptr->{address}>>6);
                    # If we snoop a read that got GO but no data, we snoop it, because it will get MoNuke in read core
                    while(my ($k,$read_rec) = each %{$idi_cid_h{$rec_ptr->{UnitU}}}) {
                        if($addr6 == ($read_rec->{address}>>6) and $read_rec->{tick_go} and $read_rec->{cmd}=~/^(RDCURR|RFO|DRD|CRD|PRD)/) {
                            if(length($read_rec->{data_rd})<128) {
                                # if not all data received it is bad
                                $read_rec->{slfsnp_bad} = 1; # Signals that this transaction is bad (got MoNuke)
                            }
                        }
                    }
                } push @$snp_old_l,$rec_ptr;
            } elsif($rec_ptr->{typ} =~ /DATA/) {
                if($rec_ptr->{cmd} =~ /MemWrPtl|MemWr|WbMtoI|WbMtoE|WbMtoS|WbEtoI|NcIOWr|NCIORd|NcMsgS|IntPhysical/i)  {
                    $rec_ptr->{uid}=$rec_ptr->{cid};
                    if($rec_ptr->{Chunk} eq "0011")  { $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                        $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}} = $rec_ptr;
                        #$idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}} = $rec_ptr;
                        push @{$scbd->{UC_WR_cmd}->{$rec_ptr->{LID}}},$rec_ptr;
                        push @{$scbd->{U}->{all}} , $rec_ptr;
                        if($rec_ptr->{cmd} =~ /MemWrPtl|MemWr/i)  {
                            my $UnitName = $rec_ptr->{UnitU}; $UnitName=~s/MEDIA\d/MEDIA/; # makes the two media port as one channel
                            if(!defined($MemWr_chs->{$UnitName})) { $MemWr_chs->{$UnitName} = { count => 0 , prefix=>"_MemWr" }; };
                            merge_ns_write_channels($rec_ptr,$MemWr_chs->{$UnitName},"tick_end");
                        } elsif($rec_ptr->{cmd} =~ /WbMtoI|WbMtoE|WbMtoS/ and $rec_ptr->{Unit}=~/^SOC_CCF_LINK/) { 
                            if($no_CCF_write_merge) {
                                $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch_tc},"_ccf_Wr".sprintf("%04d",++$CCF_count));
                            } else {
                                merge_ns_write_channels($rec_ptr,$MemWr_chs_CCF_WBMtoI,"tick_go");
                            }
                        } elsif($rec_ptr->{cmd} =~ /WbEtoI/) { # there speculatinve write from CCF does not always gets to memory
                            $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = append_ch_id($rec_ptr->{src_ch_tc},"_Spec_Wr".sprintf("%04d",++$SpecWr_count));
                        }
                    }
                }
                my $tr;
                if($rec_ptr->{typ} =~ /C2U/ and !($rec_ptr->{cmd}=~/MemWrPtl|MemWr|WbMtoI|WbMtoE|WbMtoS|WbEtoI/)) {
                    if($rec_ptr->{htype} eq "SR-CD") { 
                        $tr = $snp_cid_h{$rec_ptr->{UnitU}}->{ $rec_ptr->{cid_snp} }; # ufi
                    } else { 
                        $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{ $rec_ptr->{uid} }; 
                    }
                } else {
                    $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{ $rec_ptr->{cid} };
                }
                if(!defined($tr)) {
                    die_ERROR("168 ERROR: Can not match IDI transaction by id.\n  Trans: $rec_ptr->{line}\n");
                }
                my $data_key = (($rec_ptr->{typ}=~/C2U/) ? "data_wr" : "data_rd");
                if(defined($tr)) {
                    my $skip_uri_chk = $::skip_uri_chk || ($cpu_proj eq "lnl" && defined($tr->{$data_key})); #fixme: need to remove this mask to the second data chunk uri check after Amal will fix the EMU_URI_STITCH bug on it.
                    if(defined($tr->{$data_key})) { 
                        if($rec_ptr->{cmd} eq "EMemWr" or $rec_ptr->{cmd} eq "EMemWrPtl" or $rec_ptr->{cmd} eq "EMemWr32B" or $rec_ptr->{cmd} eq "EMemWrPtl32B") { 
                            $tr->{tick_go} = $rec_ptr->{tick}; 
                        }
                        if($rec_ptr->{Chunk} eq "0011" or $rec_ptr->{Chunk} eq "11") {
                            $tr->{$data_key} = $tr->{$data_key}.$rec_ptr->{data};
                        } else {
                            if($tr->{cmd}=~/^F?MemWrCompress/) {
                                $rec_ptr->{data} = "0000000000000000000000000000000000000000000000000000000000000000";
                            }
                            $tr->{$data_key} = $rec_ptr->{data}.$tr->{$data_key};
                        }
                        if($tr->{cmd}=~/SnpLInv|SnpLData|SnpLCode|SnpLFlush|SnpData|SnpCode|SnpInvOwn/) {
                            #ccf WB of SnpLInv and SnpLData
                            push @{$scbd->{U}->{all}} , $tr;
                        }
                    } else {
                        $tr->{$data_key} = $rec_ptr->{data}; 
                        if($tr->{cmd}=~/^SnpL/) { 
                            $tr->{snp_rsp} = $rec_ptr->{cmd}; 
                            $tr->{tick_go} = $rec_ptr->{tick}; 
                        }
                    }
                    use_max_tick_end($tr,$rec_ptr->{tick}) unless $tr->{cmd}=~/MemWr/;
                    if($rec_ptr->{bogus}) { 
                        $tr->{bogus}=1;  
                        print "Cought bogus=1 data trans : $tr->{line}" if $debug>=6; 
                    }
                    if($debug>=3) {
                        print "In   :id=$rec_ptr->{id}: ".$tr->{line};
                        print " Out :id=$rec_ptr->{id}: ".$line; 
                    }
                    if(!$skip_uri_chk && $rec_ptr->{LID} ne $tr->{LID} and !($tr->{cmd}=~/^INT/)) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("032 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    if($rec_ptr->{Attributes}=~/byteen=(\w+)/) {
                        $tr->{byteen} = $1;
                    }
                };
            } elsif($rec_ptr->{cmd} =~ /IDI_GO/) {
              if($sys_pref_idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}}) {
                $sys_pref_idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}} -= 1;
              } else {
                my $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    $tr->{count_go} = $rec_ptr->{count};
                    if($debug>=9) {
                        print "In   :id=$rec_ptr->{uid}: ".$tr->{line};
                        print " GO :id=$rec_ptr->{uid}: ".$line; 
                    }
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        if(!($tr->{cmd} =~/LLCPREF/)) {
                            die_ERROR("033 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                        }
                    }
                    ufi_find_and_push_snp_rec_l($snp_old_l,$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                };
              }
            } elsif($rec_ptr->{typ} eq "U2C RSP") {
              if($rec_ptr->{cmd} =~ /WRITEPULL/) {
                my $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        die_ERROR("034 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("044 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }
                $tr->{uid} = $rec_ptr->{uid};
                if($rec_ptr->{cmd} =~ /GO_WRITEPULL/) {
                    ufi_find_and_push_snp_rec_l($snp_old_l,$tr);
                    push @{$scbd->{U}->{all}} , $tr;
                    $tr->{tick_beg} = $tr->{tick};
                    $tr->{tick_go} = $rec_ptr->{tick};
                    use_max_tick_end($tr,$rec_ptr->{tick});
                }
                $idi_uid_h{$rec_ptr->{UnitU}}->{$tr->{uid}} = $tr;
              } elsif($rec_ptr->{cmd}=~/FwdM|FwdV/) {
                # Correct the Snoop response like : RspIFwdMO
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if($rec_ptr->{LID} ne $tr->{LID}) { # && $rec_ptr->{LID} ne $tr->{PID}
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("042 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                } else {
                    die_ERROR("041 ERROR: Can not match IDI transaction by uid. LID differs.\n  Trans: $rec_ptr->{line}\n");
                }

                $tr->{snp_rsp_cmd} = $rec_ptr->{cmd};
              } elsif($rec_ptr->{cmd} eq "EXTCMP") {
                my $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_EXTCMP} = $rec_ptr->{tick};
                }
              } elsif($rec_ptr->{cmd} eq "Cmp") {
                my $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_end} = $rec_ptr->{tick};
                    if(!defined($tr->{tick_go})) {
                        $tr->{tick_go} = $rec_ptr->{tick};
                    }
                    if($tr->{cmd} =~ /MemWr32B|MemWrPtl32B/i) {
                        if(($tr->{address}&0x3f)>=32) {
                            # in case MemWr32B and we have a second CL chuck add xx-es before
                            $tr->{data_wr} =~ s/^xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx//;
                            $tr->{data_wr} =~ s/^----------------------------------------------------------------//;
                            $tr->{data_wr}.= "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
                        }
                    }
                    if($tr->{LID} ne $rec_ptr->{LID} and !$skip_bad_uri_filter) {
                        undef $tr->{LID}; # This is a URI error , so disregard it
                    }
                }
              } elsif($rec_ptr->{cmd}=~/CmpO|CmpU/) {
                my $tr = $idi_cid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{cid}};
                if($tr) {
                    $tr->{tick_end} = $rec_ptr->{tick};
                    if(!defined($tr->{tick_go})) {
                        $tr->{tick_go} = $rec_ptr->{tick};
                    }
                }
                ufi_find_and_push_snp_rec_l($snp_old_l,$tr); push @{$scbd->{U}->{all}} , $tr;
              }
            } elsif($rec_ptr->{typ} eq "C2U RSP") {
              if($rec_ptr->{cmd}=~/FwdM|FwdV|FwdI-C|FwdI-D/) {
                # Take the Snoop response for IOP Snoops like : RspIFwdMO
                # FIXME: More accurate is to match the snoop data to the IOP write or read that did the snoop.
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    if(!$skip_uri_chk and $rec_ptr->{LID} ne $tr->{LID}) {
                        # FIXME: Need to make this ERROR and not die
                        die_ERROR("051 ERROR: Can not match IDI transaction by ID. LID differs.\n  Trans1: $rec_ptr->{line}\n  Trans2: $tr->{line}\n");
                    }
                    $tr->{tick_go} = $rec_ptr->{tick}; $tr->{tick_beg} = $tr->{tick};
                    $tr->{snp_rsp} = $rec_ptr->{cmd};
                } else {
                    die_ERROR("052 ERROR: Can not match IDI transaction by uid. \n  Trans: $rec_ptr->{line}\n");
                }

                if($is_Spec_Snp) { 
                    $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_Spec_SNP".++$spec_snp_count);
                } else {
                    $tr->{src_ch_tc} = append_ch_id($tr->{src_ch_tc},"_IOP_SNP");
                }
                push @{$scbd->{U}->{all}} , $tr;
              } elsif($rec_ptr->{cmd}=~/RspI/) { # RspI only capture the rsp opcode in the Snoop transaction
                my $tr = $idi_uid_h{$rec_ptr->{UnitU}}->{$rec_ptr->{uid}};
                if(defined($tr)) {
                    $tr->{snp_rsp} = $rec_ptr->{cmd};
                    $tr->{tick_go} = $rec_ptr->{tick}; 
                    push @{$scbd->{U}->{all}} , $tr; # stop also Snoop transactins with RspI for got_owned_slots_CCF
                }
              }
            }
        }
    }

    # Fix the data_wr & data_rd to be only data.
    my @new_rec_l;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        if($rec_ptr->{bogus}) { next; }
        push @new_rec_l,uri_rec_fix_data($rec_ptr);
    }
    $scbd->{U}->{all} = \@new_rec_l;

    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        undef ($rec_ptr->{snp_rec_l}); # just free memory
        # In case there is an 
        my $addr6 = $rec_ptr->{address}>>6;
        if($debug<=2) {
            # Remove redundant info
            delete $rec_ptr->{cid};
            delete $rec_ptr->{uid};
        }
        if($rec_ptr->{ufi_inst}==0 && ($rec_ptr->{cmd}=~/WbMtoI|WbMtoE|WbMtoS|WbEtoI/ || $rec_ptr->{typ} eq "C2U REQ" || $rec_ptr->{typ} eq "C2U DATA" || $rec_ptr->{typ} eq "U2C REQ")) {
            # cancel all  writes from my CBB agent becase they are included in the idi transactions
            $rec_ptr->{canceled} = 1;
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

    if($debug<8) {
        for my $rec_ptr (@{$scbd->{U}->{all}}) {
            delete $rec_ptr->{go_state}; delete $rec_ptr->{id}; delete $rec_ptr->{count_go}; delete $rec_ptr->{snp_rec_l}; delete $rec_ptr->{direction};
            delete $rec_ptr->{typ}; delete $rec_ptr->{hbo_id}; delete $rec_ptr->{htype}; delete $rec_ptr->{ufi_inst};
        }
    }

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub ufi_find_and_push_snp_rec_l($$) {
    my ($trans_l,$tr) = @_;
    my $cl_addr = $tr->{address}&0xFFFFFFFF_FFFFFFC0;
    my $idx = (@$trans_l)-1;
    my $tick_finish = $tr->{tick};
    # Search to find if there was a FwdM on this address 
    for(; $idx>=0 ;$idx-=1) {
        my $snp_rec = $trans_l->[$idx];
        if(!($snp_rec->{cmd}=~/Snp/)) { next };
        if($snp_rec->{tick}<$tick_finish) { last };
        if(($snp_rec->{address}&0xFFFFFFFF_FFFFFFC0) == $cl_addr
                and $snp_rec->{cmd}=~/SnpLInv|SnpLData|SnpLCode|SnpLFlush|SnpInvOwn|SnpData|SnpCode|SnpInvOwn/
                and $snp_rec->{tick}>= $tr->{tick} and $snp_rec->{tick} <= $tr->{tick_go}) {
            push @{$tr->{snp_rec_l}},$snp_rec; $snp_rec->{tick_go} = $tr->{tick_go}; #ufi#
        }
    }
}

sub uri_rec_fix_data($) {
    my ($rec_ptr) = @_;
    my @ret_rec_l = ();
    if(defined($rec_ptr->{data_rd})) {
        if(defined($rec_ptr->{data_wr})) {
            if($rec_ptr->{cmd}=~/^RFOWR/) {
                my $new_rec_ptr = dup_idi_rec($rec_ptr);
                $new_rec_ptr->{cmd} = "DRD";
                $new_rec_ptr->{data} = $rec_ptr->{data_rd};
                push @ret_rec_l,$new_rec_ptr;
                $rec_ptr->{cmd} = "WBMTOI";
                $rec_ptr->{data} = $rec_ptr->{data_wr};
                undef $rec_ptr->{data_rd};
                undef $rec_ptr->{data_wr};
            } else {
                die_ERROR("039 ERROR: This un-intentified IDI opcode have both dara_rd & data_wr : $rec_ptr->{line}");
            }
        } else {
            $rec_ptr->{data} = $rec_ptr->{data_rd};
            undef $rec_ptr->{data_rd};
        }
    } elsif(defined($rec_ptr->{data_wr})) {
        $rec_ptr->{data} = $rec_ptr->{data_wr};
        undef $rec_ptr->{data_wr};
    }
    if(defined($rec_ptr->{snp_rec_l})) {
        my $find_cnt = 0;
        for my $snp_rec (@{$rec_ptr->{snp_rec_l}}) {
            if($snp_rec->{snp_rsp}=~/^RspFwdI-D$/) {
                if(defined($snp_rec->{data}) || defined($snp_rec->{data_wr})) {
                    die_ERROR("000 ERROR: Not expecting data here.");
                }
                $snp_rec->{data} = $rec_ptr->{data};
            }
            if(!defined($snp_rec->{data_wr})) { next }
            $snp_rec->{src_ch_tc} = $rec_ptr->{src_ch_tc};
            if($debug>=3) {
                print "Found snp_rec:$snp_rec->{line}";
                print " For this rec:$rec_ptr->{line}"; 
            }
            $find_cnt+=1;
            if($find_cnt>1) {
                die_ERROR("046 ERROR: Found more that one FwdM simultaniously. \n  snp_rec: $snp_rec->{line}\n  orig_rec: $rec_ptr->{line}\n");
            }
            uri_rec_fix_data($snp_rec);
            push @ret_rec_l,$snp_rec;
        }
    }
    push @ret_rec_l,$rec_ptr;
    return (@ret_rec_l);
}



sub ccf_preloader_file_read_record($) {
    local $_ = shift;

    my @a = split /\s*\|\s*/;
    my $typ = $a[$mcc_preloader_h{TRANS_TYPE}];
    my $addr = $a[$mcc_preloader_h{Address}],
    my %rec = ( 
        direction=>"U",
        cmd=>"MWr",
        rec_type=>"ccf_preloader",
        src_ch_tc=>$local_src_ch,
        typ=>$typ,
        state=>$a[$mcc_preloader_h{State}], 
        Unit =>$a[$mcc_preloader_h{Unit}], 
        tick=>$a[$mcc_preloader_h{Time}],
    );

    $addr =~ s/^0x//;
    $rec{address} = big_hex($addr) & 0xFFFFFFFF_FFFFFFC0;
    $rec{data} = $a[$mcc_preloader_h{Data}];
    $rec{data} =~ s/ //g;
    $rec{data} =~ s/^0x//g;
    $rec{data} = ("0" x (128-length($rec{data}))) . $rec{data};
    if($rec{tick} ne "-") { 
        $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
        $rec{tick} += 1;     # I add one tick here to make sure that it will be before the mc preloader.
        $rec{tick_beg} = $rec{tick};
        $rec{tick_end} = $rec{tick};
        $rec{tick_go} = $rec{tick};
        $rec{tick_mc} = $rec{tick};
    }

    return \%rec;
}

sub ccf_preloader_file_reader($$) {
    my $fd = shift;
    my $mc_idx;
    local $scbd = shift;
    my $is_ccf_cte = ($ACERUN_CLUSTER=~/^(idi_bridge|ccf|cbb)/ or ($ACERUN_STEPPING=~/^cbb/));

    $scbd->{read_record_func} = \&ccf_preloader_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(s/^#header,\w*,//) {
            my @a = split ",";
            my $i = 0;
            for(@a) { 
                chomp;
                s/:\d+$//; 
                s/\s*\[.*//;
                s/ /_/g;
                $mcc_preloader_h{$_} = $i++; 
            }
            last;
        }
    }
    if(!defined($mcc_preloader_h{Time}) or $mcc_preloader_h{Time}) { return undef; }
    $mcc_preloader_h{State} = ($mcc_preloader_h{State} or $mcc_preloader_h{"Sta+te"});
    while(<$fd>) {
        if(/^\|?\s*\d+\s/ && !m/ IDP/) {
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;
            if(defined($mc_idx)) {
                $rec_ptr->{address} = cmi_hash_mc_addr_uncompress($rec_ptr->{address},$mc_idx);
            }
           
            if($debug>=7) {
                print " addr=".addr_str($rec_ptr->{address}).": ".$rec_ptr->{line};
            }
            my $is_LLC_M = ($rec_ptr->{state} eq "M") && ($rec_ptr->{Unit}=~/^LLC/);
            if($is_ccf_cte) {
                # in cce cte record also MEM lines and let the LLC M lines overide them
                if($is_LLC_M) {
                    my $prev_rec = $scbd->{U}->{all}->[-1];
                    if($prev_rec && ($prev_rec->{address}>>6) == ($rec_ptr->{address}>>6)) {
                        # remove the MEM preload from the list and let it get overidden by the LLC preload
                        pop @{$scbd->{U}->{all}};
                    }
                }
                push @{$scbd->{U}->{all}} , $rec_ptr if $is_LLC_M or ($rec_ptr->{Unit}=~/^MEM/);
            } else {
                # in soc env recode only LLC lines which are M state. The rest data is in the global preloader
                push @{$scbd->{U}->{all}} , $rec_ptr if $is_LLC_M;
            }
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

}

sub ccf_llc_file_read_record($) {
    local $_ = shift;

    my @a = split /\s*\|\s*/;
    my $typ = $a[$mcc_preloader_h{Arbcmd}];
    if($typ ne "Invd") { return undef; }
    my $addr = $a[$mcc_preloader_h{Address}],
    my %rec = ( 
        direction=>"U",
        cmd=>$typ,
        rec_type=>"llc_trk",
        src_ch_tc=>$local_src_ch,
        tick=>$a[$mcc_preloader_h{Time}],
    );

    $addr =~ s/^0x//;
    $rec{address} = big_hex($addr);
    if($rec{tick} ne "-") { 
        $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
    }

    return \%rec;
}

sub ccf_llc_file_reader($$) {
    my $fd = shift;
    my $mc_idx;
    local $scbd = shift;

    $scbd->{read_record_func} = \&ccf_llc_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(s/^#header,\w*,//) {
            my @a = split ",";
            my $i = 0;
            for(@a) { 
                chomp;
                s/:\d+$//; 
                s/\s*\[.*//;
                s/ /_/g;
                $mcc_preloader_h{$_} = $i++; 
            }
            last;
        }
    }

    while(<$fd>) {
        if(/^\|?\s*\d+\s/) {
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;
            if(defined($mc_idx)) {
                $rec_ptr->{address} = cmi_hash_mc_addr_uncompress($rec_ptr->{address},$mc_idx);
            }

            if($debug>=7) {
                print " addr=".addr_str($rec_ptr->{address}).": ".$rec_ptr->{line};
            }
            if($rec_ptr->{cmd} eq "Invd") {
                mark_non_snoop_addr($rec_ptr);
            }
            push @{$scbd->{U}->{all}} , $rec_ptr;
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

}

sub mcc_preloader_file_read_record($) {
    local $_ = shift;
    if(!$mcc_preloader_ver) {
        if(!m/\s*\d+.*(Direct|On the fly|CCF_PRE|GLOBAL_PRE|SRC)/i) { return undef; }
    }

    my @a = split /\s*\|\s*/;
    my $typ = $a[$mcc_preloader_h{TRANS_TYPE}];
    my $addr = $a[$mcc_preloader_h{SYS_ADDR}],
    my %rec = ( 
        direction=>"U",
        cmd=>"MWr",
        rec_type=>"mcc_preloader",
        src_ch_tc=>$local_src_ch,
        typ=>$typ,
        tick=>$a[$mcc_preloader_h{TIME}],
    );

    $addr =~ s/^0x//;
    $rec{address} = big_hex($addr)*($mcc_preloader_ver?32:4);
    $rec{data} = $a[$mcc_preloader_h{DATA}];
    $rec{data} =~ s/ //g;
    $rec{data} =~ s/^0x//g;
    $rec{data} = ("0" x (128-length($rec{data}))) . $rec{data};
    if($rec{tick} ne "-") { 
        $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

        $rec{tick_beg} = $rec{tick};
        $rec{tick_end} = $rec{tick};
        $rec{tick_go} = $rec{tick};
        $rec{tick_mc} = $rec{tick};
    }

    return \%rec;
}

sub mcc_preloader_file_reader($$) {
    my $fd = shift;
    my $mc_idx;
    local $scbd = shift;
    local $local_src_ch = get_ch_id("mcc_preloader");

    $scbd->{read_record_func} = \&mcc_preloader_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(s/^#header,\w*,//) {
            my @a = split ",";
            my $i = 0;
            for(@a) { 
                chomp;
                s/:\d+$//; 
                s/\s*\[.*//;
                s/ /_/g;
                $mcc_preloader_h{$_} = $i++; 
            }
            last;
        }
    }
    if($mcc_preloader_h{Time}) { return undef; }
    if($mcc_preloader_h{CCA} and !$mcc_preloader_h{SYS_ADDR}) { $mcc_preloader_h{SYS_ADDR} = $mcc_preloader_h{CCA}; }
    if($mcc_preloader_h{CXM} and !$mcc_preloader_h{CCA}) { $mcc_preloader_h{SYS_ADDR} = $mcc_preloader_h{CXM}; }
    if($mcc_preloader_ver) {
        for my $k (keys %mcc_preloader_h) { $mcc_preloader_h{$k}+=1; }
    }

    while(<$fd>) {
        if($cpu_proj eq "lnl" and /^\| *(\d+)\.(\d*) *ns *\|/) {
            my $fix_time = sprintf("| %d |","$1.$2"*1000);
            s/^\| *(\d+\.\d*) *ns *\|/$fix_time/ or die_ERROR("158 ERROR: Can not fix this line in mc_preload file: $_");
        }
        if(/^\|?\s*\d+\s/ && !m/ IDP/) {
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;
            if(defined($mc_idx)) {
                $rec_ptr->{address} = cmi_hash_mc_addr_uncompress($rec_ptr->{address},$mc_idx);
            }
            if(@lnl_prmrr_ranges_l and is_addr_in_range(($rec_ptr->{address}),$lnl_prmrr_ranges_l[0],undef)) {
            } else {
                if($debug>=7) {
                    print " addr=".addr_str($rec_ptr->{address}).": ".$rec_ptr->{line};
                }
                if(@{$scbd->{U}->{all}}) {
                    # filter duplicated lines. This saves a lot of run time.
                    my $rec_ptr1 = $scbd->{U}->{all}->[@{$scbd->{U}->{all}}-1];
                    if($rec_ptr1->{address} == $rec_ptr->{address} and  $rec_ptr1->{tick_beg} == $rec_ptr->{tick_beg} and !($rec_ptr->{data}=~/[-xX]/)) {
                        pop @{$scbd->{U}->{all}}; # delete the last transaction because it is overwitten by this transaction.
                    }
                }
                push @{$scbd->{U}->{all}} , $rec_ptr; 
            }
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

}

%cxm_preloader_h = ();

sub cxm_preloader_file_read_record($) {
    local $_ = shift;
    if(!m/\s*\d+.*( Back )/i) { return undef; }

    my @a = split /\s*\|\s*/;
    my $typ = $a[$cxm_preloader_h{OPCODE}];
    my $addr = $a[$cxm_preloader_h{ALIGNED_ADDRESS}],
    my %rec = ( 
        direction=>"U",
        cmd=>"MWr",
        rec_type=>"mcc_preloader",
        src_ch_tc=>$local_src_ch,
        typ=>$typ,
        count=>++$cxm_preloader_h{count},
        tick=>$a[$cxm_preloader_h{TIME}],
    );

    $addr =~ s/^0x//;
    $rec{address} = big_hex($addr)*64;
    my $d = $a[$cxm_preloader_h{DATA}];
    $d =~s/\s*$//;
    if(length($d)<128) { $d = ("0" x (128-length($d))) . $d; } 
    $rec{data}=$d;
    if($rec{tick} ne "-") { 
        $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

        $rec{tick_beg} = $rec{tick};
        $rec{tick_end} = $rec{tick};
        $rec{tick_go} = $rec{tick};
        $rec{tick_mc} = $rec{tick};
    }

    return \%rec;
}

sub cxm_preloader_file_reader($$) {
    my $fd = shift;
    my $mc_idx;
    local $scbd = shift;
    local $local_src_ch = get_ch_id("mcc_preloader");

    $scbd->{read_record_func} = \&cxm_preloader_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(/^TIME/) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { 
                s/:\d+$//; 
                s/\s*\[.*//;
                s/ /_/g;
                $cxm_preloader_h{$_} = $i++; 
            }
            last;
        }
    }
    if($cxm_preloader_h{Time}) { return undef; }

    while(<$fd>) {
        if(/^\s*\d+\s/ && !m/ IDP/) {
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;
            if(defined($mc_idx)) {
                $rec_ptr->{address} = cmi_hash_mc_addr_uncompress($rec_ptr->{address},$mc_idx);
            }

            if($debug>=7) {
                print " addr=".addr_str($rec_ptr->{address}).": ".$rec_ptr->{line};
            }
            if(@{$scbd->{U}->{all}}) {
                # filter duplicated lines. This saves a lot of run time.
                my $rec_ptr1 = $scbd->{U}->{all}->[@{$scbd->{U}->{all}}-1];
                if($rec_ptr1->{address} == $rec_ptr->{address} and  $rec_ptr1->{tick_beg} == $rec_ptr->{tick_beg} and !($rec_ptr->{data}=~/[-xX]/)) {
                    pop @{$scbd->{U}->{all}}; # delete the last transaction because it is overwitten by this transaction.
                }
            }
            push @{$scbd->{U}->{all}} , $rec_ptr;
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

}

sub astro_preloader_file_read_record($) {
    local $_ = shift;
    ~s/\s*$//;

    my @a = split /\s*\|\s*/;
    my $typ = $a[$astro_preloader_h{TRANS_TYPE}];
    my $addr = $a[$astro_preloader_h{ORIG_ADDR}],
    my %rec = ( 
        direction=>"U",
        cmd=>"MWr",
        rec_type=>"mcc_preloader",
        src_ch_tc=>$local_src_ch,
        typ=>$typ,
        count=>++$astro_preloader_h{count},
        tick=>$a[$astro_preloader_h{Time}],
    );

    $addr =~ s/^0x//;
    $rec{address} = big_hex($addr);
    my $d = $a[$astro_preloader_h{DATA}];
    my @d_l = split /\s+/,$a[$astro_preloader_h{DATA}];
    $d = "";
    for(my $i=0; $i<16 ; $i+=1) {
        $d.= ("0" x (8-length($d_l[$i]))) . $d_l[$i] ." ";
    }
    $d=~s/\s*$//;
    $rec{data}=$d;

    if($rec{tick} ne "-") { 
        $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

        $rec{tick_beg} = $rec{tick};
        $rec{tick_end} = $rec{tick};
        $rec{tick_go} = $rec{tick};
        $rec{tick_mc} = $rec{tick};
    }

    return \%rec;
}

sub astro_preloader_file_reader($$) {
    my $fd = shift;
    my $mc_idx;
    local $scbd = shift;
    local $local_src_ch = get_ch_id("mcc_preloader");
    local %astro_preloader_h = ();

    $scbd->{read_record_func} = \&astro_preloader_file_read_record;
    $scbd->{tick_mul}=$tick_mul;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(s/^#header,[^,]*,//) {
            my @a = split ",";
            my $i = 0;
            for(@a) { 
                s/:\d+$//; 
                s/\s*\[.*//;
                s/ /_/g;
                chomp;
                $astro_preloader_h{$_} = $i++; 
            }
            last;
        }
    }
    if(!defined($astro_preloader_h{Time})) { return undef; }

    while(<$fd>) {
        if(/^\s*\d+\s/) {
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($line) or next;
            $rec_ptr->{line} = $line;

            if($debug>=7) {
                print " addr=".addr_str($rec_ptr->{address}).": ".$rec_ptr->{line};
            }
            push @{$scbd->{U}->{all}} , $rec_ptr;
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});

}

sub psf_file_post_process($) {
    my $scbd = shift;

    if($skip_psf_Cplt_chk) { return; };

    for my $direction ("U","D") {
      for my $id (keys %{$scbd->{$direction}}) {
          if($id =~ /all/) { next }
          my @cmd_of_this_id_list = @{$scbd->{$direction}->{$id}};
          if(+@cmd_of_this_id_list) {
              for(@cmd_of_this_id_list) {
                  print_ERROR("018 ERROR: Transaction left if SCBD ($direction) for file ".$scbd->{filename}.": ".trans_str($_)."\n"); 
                  $exit_code = 1;
              }    
          }
      }
   }
}

sub get_pcie_exclude_range_l() {
    my @exclude_range_l = ();
    for my $D (keys %$PCIE_CFG_SPACE) {
        for my $F (keys %{$PCIE_CFG_SPACE->{$D}}) {
            my $space_ptr = $PCIE_CFG_SPACE->{$D}->{$F};
            if(defined($space_ptr)) {
                my $LIMIT = $space_ptr->{PMLIMIT};
                my $BASE  = $space_ptr->{PMBASE};
                if(defined($BASE) && defined($LIMIT) && $BASE<=$LIMIT) {
                    push @exclude_range_l,{BASE=>$BASE,LIMIT=>$LIMIT};
                }
                my $LIMIT = $space_ptr->{MLIMIT};
                my $BASE  = $space_ptr->{MBASE};
                if(defined($BASE) && defined($LIMIT) && $BASE<=$LIMIT) {
                    push @exclude_range_l,{BASE=>$BASE,LIMIT=>$LIMIT};
                }
                my $LIMIT = $space_ptr->{LIMIT};
                my $BASE  = $space_ptr->{BASE};
                if(defined($BASE) && defined($LIMIT) && $BASE<=$LIMIT) {
                    my %h = (BASE=>$BASE,LIMIT=>$LIMIT);
                    if($space_ptr->{PMCS}) { $h{PMCS} = $space_ptr->{PMCS}; }
                    if($space_ptr->{GCMD}) { $h{GCMD} = $space_ptr->{GCMD}; }
                    push @exclude_range_l,\%h;
                }
            }
        }
    }
    return @exclude_range_l;
}

sub get_TSEG_DSM_GSM_exclude_range_l() {
    my @exclude_range_l = ();
    my $space_ptr = $PCIE_CFG_SPACE->{0}->{0};
    # Calculate the DRAM_1MB_TSEG_DRAM (from ADDR 1MB to TSEG which is MC ABORT)
    if(defined($space_ptr->{"TOLUD"})) {
        my $MIN_BASE = undef;
        my $MAX_BASE = undef;
        my $BASE;
        my $LIMIT = (get_field($space_ptr->{"TOLUD"},31,20)<<20);
        if($space_ptr->{"TSEGMB"}) {
            $BASE = $space_ptr->{"TSEGMB"} & 0xFFF00000;
        } 
        if($BASE && $space_ptr->{"DPR"}) {
            if(ref($space_ptr->{"DPR"}) eq "ARRAY") {
                # Create a range with an array 
                my $TSEG_beg_addr = $BASE;
                $BASE = [ ];
                for $reg_update_ptr (@{$space_ptr->{"DPR"}}) {
                    my $BASE_update_ptr = [ 
                        $reg_update_ptr->[0], # tick
                        # I checker only DPR_0_0_0_PCI.EPM==1 because DPR_0_0_0_PCI.PRS will rise by hardware several cycles later.
                        (get_field($reg_update_ptr->[1],2,2)==1 ? $TSEG_beg_addr - (get_field($reg_update_ptr->[1],11,4)<<20) : $TSEG_beg_addr ), # BASE value
                        15,                   # byte_en 
                        $reg_update_ptr->[3]
                    ]; 
                    if(!defined($MIN_BASE) or $MIN_BASE>$BASE_update_ptr->[1]) {
                        # Capture the minimum base is this test. It helps to find marginal cases.
                        $MIN_BASE = $BASE_update_ptr->[1];
                    }
                    if(!defined($MAX_BASE) or $MAX_BASE<$BASE_update_ptr->[1]) {
                        # Capture the minimum base is this test. It helps to find marginal cases.
                        $MAX_BASE = $BASE_update_ptr->[1];
                    }
                    print"get_TSEG_DSM=".addr_str($BASE_update_ptr->[1])." at ".$BASE_update_ptr->[0]."\n" if $debug>=2;
                    push @$BASE,$BASE_update_ptr;
                }
                print"DPR MIN_BASE=".addr_str($MIN_BASE)." MAX_BASE=".addr_str($MAX_BASE)." TSEG_beg_addr=".addr_str($TSEG_beg_addr)."\n" if $debug >= 2;
                if($skip_DPR_changing_chk && $MIN_BASE<$MAX_BASE) {
                    # In ADL there is a stimuli that always change DPR and send transactions without waiting for DPR to be accepted by IOP.
                    # Hence, if that happens, I skip the checking for the DPR range:
                    push @skip_DPR_changing_range,{ BASE=>$MIN_BASE, LIMIT=>$MAX_BASE };
                }
            } else {
                if(get_field($space_ptr->{"DPR"},2,2) == 1) {
                    $BASE -= (get_field($space_ptr->{"DPR"},11,4)<<20);
                } 
            }
        }
        printf("DRAM_1MB_TSEG_DRAM is %08X to %08X.\n",0x100000,chkget_reg_val_in_tick($BASE)) if $debug>=7;
        printf("TSEG,DSM,GDM is %08X to %08X.\n",chkget_reg_val_in_tick($BASE),$LIMIT) if $debug>=7;
        push @exclude_range_l,{BASE=>$BASE,LIMIT=>$LIMIT,MIN_BASE=>$MIN_BASE,MAX_BASE=>$MAX_BASE} if($BASE && $LIMIT);
    }
    return @exclude_range_l;
}

sub get_VGA_exclude_range_l() {
    my @exclude_range_l = ();
    print "Analize VGA ranges\n" if $debug>=7;
    for my $peg_DBF ([6,0,13],[1,0,3],[1,1,2],[1,2,1]) {
        my ($D,$F,$DEVEN_bit) = @$peg_DBF;
        my $DEVEN_val = chkget_reg_val_in_tick($PCIE_CFG_SPACE->{0}->{0}->{DEVEN},undef);
        next unless defined($DEVEN_val);
        next unless get_field($DEVEN_val,$DEVEN_bit,$DEVEN_bit);
        if(!defined($PCIE_CFG_SPACE->{$D}->{$F}->{PMCS})) { unshift @{$PCIE_CFG_SPACE->{$D}->{$F}->{PMCS}},[0,0,0]; }
        if(!defined($PCIE_CFG_SPACE->{$D}->{$F}->{GCMD})) { unshift @{$PCIE_CFG_SPACE->{$D}->{$F}->{GCMD}},[0,0,0]; }
        my $space_ptr = $PCIE_CFG_SPACE->{$D}->{$F};
        # Calculate the DRAM_1MB_TSEG_DRAM (from ADDR 1MB to TSEG which is MC ABORT)
        if(chkget_reg_val_in_tick($space_ptr->{BCTRL},undef)&8) {
            my $BASE = 0xA0000;
            my $LIMIT = 0xBFFFF;
            printf("PEG".$D.$F." VGA range enabled in %08X to %08X.\n",$BASE,$LIMIT) if $debug>=7;
            push @exclude_range_l,{BASE=>$BASE,LIMIT=>$LIMIT,GCMD=>$space_ptr->{GCMD},PMCS=>$space_ptr->{PMCS}};
        }
    }
    return @exclude_range_l;
}

sub get_IMR_exclude_range_l() {
    my @exclude_range_l = ();
    my $space_ptr = $PCIE_CFG_SPACE->{0}->{0};
    if(defined($space_ptr) && defined($space_ptr->{"IOP_IMR_RS0_EN"})) {
        $IOP_IMR_RS0_EN_val = $space_ptr->{"IOP_IMR_RS0_EN"};
    }
    for my $i (0..15) {
        if(defined($space_ptr) && defined($space_ptr->{"IMR${i}MASK"})) {
            my $MASK = ($space_ptr->{"IMR${i}MASK"}<<10);
            if(get_field($MASK,31,31)) {
                my $BASE  = (get_field($space_ptr->{"IMR${i}BASE"},28,0)<<10);
                my $LIMIT = $BASE | (((1<<28)-1)&~$MASK);
                if(defined($BASE) && $BASE<$LIMIT) {##FIXME##
                    my $range = {BASE=>$BASE,LIMIT=>$LIMIT,WAC=>$space_ptr->{"IMR${i}WAC"},RAC=>$space_ptr->{"IMR${i}RAC"},IMR_i=>$i
                        ,IMR_en => get_field($MASK,31,31)
                    };
                    push @exclude_range_l,$range;
                    printf("IMR$i is %08X to %08X MASK=%08X WAC=%08X RAC=%08X en=%1d.\n",$BASE,$LIMIT,$MASK,$range->{WAC},$range->{RAC},$range->{IMR_en}) if $debug>=7;
                }
            }
        }
    }
    # Calculate the DRAM_1MB_TSEG_DRAM (from ADDR 1MB to TSEG which is MC ABORT)
    return (@exclude_range_l);
}

sub get_reg_val_in_tick($$) {
    my ($reg,$tick) = @_;
    my $val = 0;
    my $max_i = 1*@$reg;
    for(my $i=0; $i<$max_i ; $i+=1) {
        if(defined($tick) and $reg->[$i]->[0]>$tick) { last }
        $val = $reg->[$i]->[1];
        #print "get_get_val=".addr_str($val)." at ".$reg->[$i]->[0]."<=$tick.\n";
    }
    return $val;
}

sub chkget_reg_val_in_tick($$) {
    my ($reg,$tick) = @_;
    my $val = 0;
    my $max_i = 1*@$reg;
    if(ref($reg) eq "ARRAY") {
        return get_reg_val_in_tick($reg,$tick);
    } else {
        return $reg;
    }
}

sub is_addr_in_range($$$) {
    my ($addr,$range,$tick) = @_;
    if(defined($range->{MASK})) { $addr &= $range->{MASK}; }
    if($addr<=chkget_reg_val_in_tick($range->{LIMIT},$tick) and $addr>=chkget_reg_val_in_tick($range->{BASE},$tick)) {
        return 1;
    } else {
        return 0;
    }
}

sub check_range_exclude($$$) {
    my ($addr, $rec_ptr , $range) = @_;
    my $is_next = 0;
    my $is_PMCS = 0;
    my $is_GCMD;
    if($range->{PMCS}) {
        $is_PMCS = 3&chkget_reg_val_in_tick($range->{PMCS},$rec_ptr->{tick_beg});
    }
    if($range->{GCMD}) {
        $is_GCMD = 2&chkget_reg_val_in_tick($range->{GCMD},$rec_ptr->{tick_beg});
    }
    if(is_addr_in_range($addr,$range,$rec_ptr->{tick_beg}) && !$is_PMCS && (!defined($is_GCMD) or $is_GCMD)) { 
        $is_next = 1;
        if(defined($range->{pass_func_l})) {
            for my $func_h (@{$range->{pass_func_l}}) {
                if(&{$func_h->{func}}(rec_ptr=>$rec_ptr,%$func_h)) {
                    $is_next = 0; last;
                }
            }
        }
    }
    return $is_next;
}

sub is_addr_in_range_l_fast($$) {
    my ($addr,$range_l) = @_;
    for my $range (@$range_l) {

        if(defined($range) and $addr<=$range->{LIMIT} and $addr>=$range->{BASE}) {
            return 1;
        }
    }
    return 0;
}

sub get_filtered_cmds($$$@) {
    my $scbd = shift;
    my $direction = shift;
    my $filter = shift;
    my %parms      = @_;
    my $exclude = $parms{exclude};
    my $exclude_range_l = $parms{exclude_range_l};
    my $exclude_func_l = ($parms{exclude_func_l} or []);
    my $filter_cmd = defined($parms{cmd}) ? $parms{cmd} : undef;
    my $filter_src_ch_tc = defined($parms{src_ch_tc}) ? $parms{src_ch_tc} : undef;
    my $filter_Unit = defined($parms{Unit}) ? $parms{Unit} : undef;
    my $count = 0;
    my @trans_l;

    my $exclude_dump = defined($exclude) ? " exclude=$exclude" : "";
    my $cmd_dump = defined($filter_cmd) ? " cmd=$filter_cmd" : "";
    print($parms{label}." ") if $debug>=2 and $parms{label};
    print("Searching in file: ".$scbd->{filename}." direction=$direction for pattern filter=$filter$cmd_dump$exclude_dump\n") if $debug>=2;       
    if(!defined($scbd) or !defined($scbd->{filename})) {
        die_ERROR("019 ERROR: Undefined scbd.");
    }
    for my $rec_ptr (@{$scbd->{$direction}->{all}}) {
        #print "get_filtered_cmds: filename=".$scbd->{filename}." line=$line";
        if(defined($filter)) {
            next unless $rec_ptr->{line}=~m#$filter#;
        }
        if(defined($filter_cmd)) {
            next unless $rec_ptr->{cmd}=~m#$filter_cmd#;
        }
        if(defined($filter_src_ch_tc)) {
            next unless $ch_name_l[$rec_ptr->{src_ch_tc}]=~m#$filter_src_ch_tc#;
        }
        if(defined($filter_Unit)) {
            next unless $rec_ptr->{Unit}=~m#$filter_Unit#;
        }
        if(defined($exclude)) {
            next if $rec_ptr->{line}=~m#$exclude#;
        }
        if(defined($exclude_range_l) && $rec_ptr->{cmd}=~/^(MONITOR|MWr|MRd|WOWrInv|WIL|DirtyEvict|WCIL|ITOMWR|WBMTOI|WBMTOE|UCRDF|LLCPREFRFO|RDCURR|PRD|RFO|DRD|CRD|PRD|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SNPCUR|SELFSNPINV|P-WR|F-WR)/i) {
            my $is_next =0;
            for my $range (@$exclude_range_l) {
                if(defined($range) and check_range_exclude($rec_ptr->{address},$rec_ptr,$range)) { 
                    $is_next = 1;
                    last;
                }
            }
            if($is_next) { next };
        }
        if(@$exclude_func_l) {
            my $is_next;
            for my $func_h (@$exclude_func_l) {
                if(&{$func_h->{func}}(rec_ptr=>$rec_ptr,%$func_h)) {
                    #$is_next = 0; last;
                } else {
                    $is_next = 1; last;
                }
            }
            if($is_next) { next };
        }
        if(length($rec_ptr->{cmd})) {
            push @trans_l,$rec_ptr;
            print "Found : $rec_ptr->{line}" if $debug>=3;       
            $count++;
        }
    }
    if(!$count) { 
        print "Found no transact in ".$scbd->{filename}."\n" if $debug>=2; 
    }
    return \@trans_l;
}

sub filter_cmd_l(@) {
    my %parms      = @_;
    my $input_trans_l = $parms{trans_l};
    my @filtered_trans_l;
    my $exclude_range_l = $parms{exclude_range_l};
    my $exclude_func_l = ($parms{exclude_func_l} or []);
    my $skip_iommu_no_conv = $parms{skip_iommu_no_conv};
    my $iommu_scbd_h = $parms{iommu_scbd_h};
    my $is_full_dump = ($parms{is_full_dump} or $debug >= 7);
    my $count = 0;
    my @trans_l;

    print($parms{label}." ") if $debug>=2 and $parms{label};
    print("Filter cmd list.\n") if $debug>=2;       
    for my $rec_ptr (@$input_trans_l) {
        my $has_parent = defined($rec_ptr->{parent});
        my $line = ($has_parent ? $rec_ptr->{parent}->{line} : $rec_ptr->{line});
        my $iommu_scbd_ptr;
        if(defined($iommu_scbd_h)) {
            $src_ch = ($has_parent ? $rec_ptr->{parent}->{src_ch} : $rec_ptr->{src_ch}) or die_ERROR("074 ERROR: Can not find src_ch!");
            $iommu_scbd_ptr = ( ($iommu_scbd_h->{$ch_name_l[$src_ch]}) or ($iommu_scbd_h->{"sai_".$rec_ptr->{sai}}) or undef );  
        }
        if(defined($exclude_range_l) or $skip_iommu_no_conv or @$exclude_func_l) {
            my $is_next =0;
            my $addr = $rec_ptr->{address};
            if(defined($iommu_scbd_ptr)) {
                $addr = IOMMU_convert_address($iommu_scbd_ptr,$rec_ptr->{BDF},$addr);
            }
            if($skip_iommu_no_conv) {
                if(!defined($addr)) { $is_next = 1; }
            }
            if(defined($exclude_range_l) && !$is_next) {
                for my $range (@$exclude_range_l) {
                    if(defined($range) and check_range_exclude($addr,$rec_ptr,$range)) { 
                        $is_next = 1;
                        last;
                    }
                }
            }
            if(@$exclude_func_l && !$is_next) {
                my $is_next;
                for my $func_h (@$exclude_func_l) {
                    if(&{$func_h->{func}}(rec_ptr=>$rec_ptr,%$func_h)) {
                        #$is_next = 0; last;
                    } else {
                        $is_next = 1; last;
                    }
                }
                if($is_next) { next };
            }
            if($is_next) { next };
        }
        if(defined($rec_ptr->{address})) {
            push @trans_l,$rec_ptr;
            print "Filtered: adddress=".addr_str($rec_ptr->{address})." data=$rec_ptr->{data} $line" if $is_full_dump;
            $count++;
        }
    }
    if(!$count) { 
        print "Found no transact in ".$scbd->{filename}."\n" if $debug>=3; 
    }
    return \@trans_l;
}

sub clean_data_string($) {
    my $orig_data = shift;
    my $data = uc($orig_data);
    my $is_pcie_data = 0;
    # Remove the first data chunk in the OPI_LINK file.
    if($data =~m/^[0-9A-Fa-f]{8}/) {
    } else {
        $data =~s/^[^:]+://;
        $is_pcie_data = 1;
    }
    # Joins all data chucks
    my @data_l;
    if($is_pcie_data) {
        # handle PCIE data. probabliy from OPIO_LINK* flie.
        for(split /\s*:\s*/,$data) {
            my @dw_l = split / +|:|_/,$_;
            if(8<+@dw_l) { 
                die_ERROR("020 ERROR: too many chucks. Bad data chunk ($data) of ($orig_data)"); 
            };
            if(!+@dw_l) { die_ERROR("021 ERROR: too few chucks. Bad data chunk ($data) of ($orig_data)"); };
            # recorder the chucks
            for my $i (2,3,0,1) {
                next if($i>=+@dw_l);
                my $dat = $dw_l[$i];
                if($dw_l[$i]=~m/^[0-9A-Fa-f]{8}$/) {
                    push @data_l,$dw_l[$i];
                }
            }
        }
    } else { 
        # handle probably PSF data
        @data_l = split /\s*[:_]\s*/,$data;
    }
    while(defined($data_l[0]) && !($data_l[0]=~/^[0-9A-Fa-f]+$/)) { shift @data_l; }
    return join(" ",@data_l);
}

sub data_compare_func($$) {
    my $str1 = clean_data_string($_[0]);
    my $str2 = clean_data_string($_[1]); 
    if($str1 eq $str2) {
        return 1;
    } else {
        return 0;
    }
}

%div64_conv = (
    0=>0, 1=>0, 2=>0, 3=>0,
    4=>4, 5=>4, 6=>4, 7=>4,
    8=>4, 9=>8, a=>8, b=>8,
    c=>"c", d=>"c", e=>"c", f=>"c",
);

sub mcc_address_compare_func($$) {
    if($_[0] =~ /0+(.*)(......)(.).$/) {
        $_[0] = ($1.$2.$div64_conv{$3}."0");
    }
    if($_[1] =~ /0+(.*)(......)(.).$/) {
        $_[1] = ($1.$2.$div64_conv{$3}."0");
    }
    if($_[0] eq $_[1]) {
        return 1;
    } else {
        return 0;
    }
}

sub big_hex_compare_func($$$) {
    if(big_hex($_[0]->{$_[2]})==big_hex($_[1]->{$_[2]})) { return 1 }
    else { return 0; }
}

sub get_cmp_vals($$$) {
    my ($rec1_ptr,$rec2_ptr,$name) = @_;
    my ($val1,$val2) = ($rec1_ptr->{$name},$rec2_ptr->{$name});
    while(ref $val1 eq 'HASH') {
        for my $k1 (keys %$val1) {
            if(defined($rec2_ptr->{modes}->{$k1}) && defined($val1->{$k1}->{$rec2_ptr->{modes}->{$k1}})) {
                $val1 = $val1->{$k1}->{$rec2_ptr->{modes}->{$k1}};
                last;
            }
            die_ERROR("075 ERROR: FATAL bad mode");
        }
    }

    return ($val1,$val2);
}

sub eval_skip_conds($$) {
    # This function take the skip condition defined in a HASH tree, and check it via the modes in $rec2_ptr->{modes} 
    my ($skip_conds,$rec2_ptr) = @_;
        while(my ($flag,$val) = each %$skip_conds) {
            if(defined($flag) && defined($val)) {
                if(ref $val eq "HASH") {
                    while(my ($flag2,$val2) = each %{$skip_conds->{$flag}})  {
                        if($flag2 == $rec2_ptr->{modes}->{$flag}) {
                            return eval_skip_conds($val2,$rec2_ptr);
                        }
                    }
                } elsif($val == $rec2_ptr->{modes}->{$flag}) {
                        return 1;
                }
            }
        }
    return 0;
}

sub compare_trans_l(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l1} or die_ERROR("076 ERROR: ");
    my $trans_l2 = $parms{trans_l2} or die_ERROR("077 ERROR: ");
    my $convert_flag = $parms{convert_flag} or undef;
    my $field_l = ($parms{field_l} or ["data","cmd","id","address","fbe_lbe"]);
    my $count=0;
    my $i2 = 0;
    printf "Start comparing to transaction lists.\n" if $debug>=2;
    # corelate the MWr
    for my $i1 (0..((+@{$trans_l1})-1)) {
        my $rec1_ptr = $trans_l1->[$i1];
        my $rec1_ptr_orig = $rec1_ptr;
        if($i1>=1*@$trans_l2 && !$parms{disable_size_check}) {
            if(defined($emulation_tick_eot) && $rec1_ptr->{tick}>$emulation_tick_eot) {
                # Skip unfinished transaction after emulation test finished.
            } else {
                print_ERROR("027 ERROR: trans_l2 is smaller than trans_l1. This is the first trans left in trabs_l1: $rec1_ptr->{line}");
                $exit_code = 1;
            }
            last;
        }
        my $rec2_ptr;
        $rec2_ptr = $trans_l2->[$i2];
        if(defined($convert_flag)) {
            if($rec2_ptr->{modes}->{convert_mode_change}) {
                print("convert_mode_change: $convert_flag=".$rec2_ptr->{modes}->{$convert_flag}."\n") if $debug>=7;
            }
            # Evaluate the skip_code, to know whether the transaction was blocked
            if(defined($rec1_ptr->{skip_conds})) {
                if(eval_skip_conds($rec1_ptr->{skip_conds},$rec2_ptr)) {
                    print "This MSI was blocked: $rec1_ptr->{line}" if $debug>=7;
                    next 
                }
            }
        }
        my %field_comperator_l = defined($parms{field_comperator_l}) ? @{$parms{field_comperator_l}} : ();
        print "Comparing: \n  $rec1_ptr->{line}  $rec2_ptr->{line}" if($debug>=9); 
        my $convert_mismatch_on_to_off_skip = 0;
        for (@$field_l) {
            my $cmp = 0;

            my ($val1,$val2) = get_cmp_vals($rec1_ptr,$rec2_ptr,$_);

            if(defined($field_comperator_l{$_})) {
                $cmp = &{$field_comperator_l{$_}}($rec1_ptr,$rec2_ptr,$_);
            } elsif($_ eq "data") {
                $cmp = data_compare_func($val1,$val2);
            } elsif($_ eq "address") {
                $cmp = $val1 == $val2;
            } else {
                $cmp = $val1 eq $val2;
            }

            if(!$cmp) {
                if($rec2_ptr->{modes}->{convert_mode_change}) {
                    print "Compare mismatch, This MSI was possiblly blocked or skipped: $rec1_ptr->{line}" if $debug>=7;
                    $convert_mismatch_on_to_off_skip = 1;
                    last;
                } else {
                    my ($val1_str,$val2_str) = $_ eq "address" ? (addr_str($val1),addr_str($val2)) : ($val1,$val2);
                    print_ERROR("022 ERROR: comparing $_ ($val1_str != $val2_str) of $rec1_ptr->{line} && $rec2_ptr->{line}");
                    $exit_code = 1;
                }
            }
        }
        if($convert_mismatch_on_to_off_skip) { next; }
        $count += 1;
        $i2+=1;
    }
    print "  Compared $count transactions\n" if $debug>=1;

    if(+@{$trans_l1} != +@{$trans_l2} && !$parms{disable_size_check} && !$skip_list_size_check) {
        if(defined($emulation_tick_eot) and (+@{$trans_l1} > +@{$trans_l2} ? $trans_l1->[@{$trans_l2}]->{tick}>$emulation_tick_eot : $trans_l2->[@{$trans_l1}]->{tick}>$emulation_tick_eot) ) {
            # Skip unfinished transaction after emulation test finished.
        } else {
            print_ERROR(sprintf("001 ERROR: list sizes to compare don't match - %d != %d\n",1*@{$trans_l1},1*@{$trans_l2}));
            $exit_code = 1;
        }
    }

    if(!+@{$trans_l1} || !+@{$trans_l2} and $parms{fail_count_zero}) {
        print_ERROR(sprintf("002 ERROR: list sizes to compare don't match - %d != %d\n",@{$trans_l1}*1,@{$trans_l2}*1));
        $exit_code = 1;
    }
}

sub sort_WRC_trans_l($) {
    my $trans_l = shift;
    my $is_switch = 1;
    my $max_i = (@$trans_l-1);
    while($is_switch) {
        $is_switch = 0;
        for(my $i; $i<$max_i;$i++) {
            my ($a,$b)  = ($trans_l->[$i],$trans_l->[$i+1]);
            $a->{PID}=~/^IOP_CII_000_(\w+)/ or die_ERROR("078 ERROR: Bad WRC $a->{PID} uri in ".trans_str($a));
            my $a_uri = hex($1);
            $b->{PID}=~/^IOP_CII_000_(\w+)/ or die_ERROR("079 ERROR: Bad WRC $b->{PID} uri in ".trans_str($b));
            my $b_uri = hex($1);
            if($a_uri>$b_uri) {
                $trans_l->[$i] = $b;
                $trans_l->[$i+1] = $a;
                $is_switch = 1;
            }
        }
    }
    return $trans_l;
}

sub read_2_write_cmp($$$) {
    my ($rec_ptr2,$address_diff,$rec_data1) = @_; 
    my $i=0; 
    my $data1, $data2;
    $address_diff <<= 1;

    do {
        $data1 = substr($rec_data1,-$address_diff-2-$i,2);
        $data2 = substr($rec_ptr2->{data},-$i-2,2);
        if($data1 ne $data2 && $data1 ne "ZZ" && $data2 ne "xx") {
            return 0;
        }
        $i+=2;
    } while($i<length($rec_ptr2->{data}));
    
    return 1;
}

sub rec_2_refmem_cmp($$) {
    my ($rec_ptr2,$refmem_rec_l) = @_; 
    #(($data = substr($refmem_rec_l->[REFMEM_DATA],-(get_word2($rec_ptr2->{shash_index})+1<<1),2)) eq $rec_ptr2->{data} or $data eq "ZZ")
    read_2_write_cmp($rec_ptr2,get_word2($rec_ptr2->{shash_index}),$refmem_rec_l->[REFMEM_DATA])
}

sub cl_address_cmp_func($$$) {
    my $address1 = $_[0]->{address};
    if(defined($iommu_scbd_ptr)) {
        $address1 = IOMMU_convert_address($iommu_scbd_ptr,$_[0]->{BDF},$address1);
    }

    return ($address1>>6) == ($_[1]->{address}>>6);
}

sub cl_data_cmp_func($$$) {
    my $offset1 = int(($_[0]->{address}&63)>>2);
    my $len1 = ($_[0]->{length}*4);
    my $address2 = ($_[0]->{address}>>2);
    my $data1 = record_2_data_be_str($_[0]);
    my $data2 = $_[1]->{data};
    $data1=~s/ //g;
    $data2=~s/ //g;
    $data1 = ("xx" x (64-$len1-$offset1*4)) . $data1 . ("xx" x ($offset1*4));

    if($cpu_proj eq "adl" and $_[0]->{cmd}=~/CAS|Swap|FAdd/) {
        if($data2=~/x/ or $_[1]->{cmd}=~/MWrPtl/) {
            # A CMI write for CAS|Swap|FAdd in ADL should be a full cache line.
            return 0;
        }
    }
    
    if(length($data1) != length($data2)) { 
        return 0; 
    }

    for (my ($i1)=(length($data1)); $i1>=0 ; $i1--) {
        my $ch1 = substr($data1,$i1,1);
        if($ch1 ne "x") { 
            if($ch1 ne substr($data2,$i1,1)) {
                return 0; 
            }
        }
    }

    return 1;
}

sub cl_data_cmp_AXI_func($$$) {
    #my $offset1 = int(($_[0]->{address}&63)>>2);
    my $len1 = length($_[0]->{data});
    my $len2 = length($_[1]->{data});
    #my $address2 = ($_[0]->{address}>>2);
    my $data1 = $_[0]->{data};
    my $data2 = $_[1]->{data};

    for (my ($i1)=(0); $i1<$len1 ; $i1++) {
        my $ch1 = substr($data1,$len1-$i1-1,1);
        if($ch1 ne "x") { 
            if($ch1 ne substr($data2,$len2-$i1-1,1)) {
                return 0; 
            }
        }
    }

    return 1;
}

sub ADL_fix_cl_data_func($$) {
    # This function make the data of the second transaction have X in place were the first transaction have no data.
    return undef unless $_[0]->{cmd}=~/CAS|Swap|FAdd/;
    my $offset1 = ($_[0]->{address}&63)*2;
    my $len1 = ($_[0]->{length}*4)*2;
    my $pdata = \$_[1]->{data};
    my $i;
    my $i_max = length($$pdata);
    while($i<$i_max && $offset1>0) {
        my $ch = substr($$pdata,-1-$i,1);
        if($ch ne " ") {
            substr($$pdata,-1-$i,1) = "x";
            $offset1-=1;
        }
        $i+=1;
    }

    while($i<$i_max && $len1>0) {
        my $ch = substr($$pdata,-1-$i,1);
        if($ch ne " ") {
            $len1-=1;
        }
        $i+=1;
    }

    while($i<$i_max) {
        my $ch = substr($$pdata,-1-$i,1);
        if($ch ne " ") {
            substr($$pdata,-1-$i,1) = "x";
        }
        $i+=1;
    }

}

sub push_reg_and_tick($$$$$) {
    my ($space_ptr,$reg_name,$tick_parm,$data,$offset) = @_;
    my $val = 0;
    my $val_be = 0;
    my $tick_go,$tick;
    if(ref($tick_parm) eq "ARRAY") {
        $tick    = $tick_parm->[0];
        $tick_go = $tick_parm->[1];
    } else {
        $tick    = $tick_parm;
        $tick_go = $tick_parm;
    }
    $cnt = 0;
    if($space_ptr->{$reg_name}) {
        my $my_ref = ref($space_ptr->{$reg_name});
        if($my_ref eq "ARRAY") {
            $cnt = 1*@{$space_ptr->{$reg_name}};
            #print "push_reg_and_tick: reg_name=$reg_name data=$data offset=$offset \n";
            if($cnt) {
                $val = $space_ptr->{$reg_name}->[$cnt-1]->[1];
                $val_be = $space_ptr->{$reg_name}->[$cnt-1]->[2];
                # if the tick of this transaction is the same as the previous, then overite it
                if($space_ptr->{$reg_name}->[$cnt-1]->[0]==$tick) { $cnt -= 1; }
            }
        } else {
            delete $space_ptr->{$reg_name};
        }
    }
    $val = $val & ~(0xFF<<($offset*8)); # Clear the byte that I want to write.
    $val = $val | ($data<<($offset*8)); # Write a signle byte to register.
    $val_be |= (1<<$offset);
    $space_ptr->{$reg_name}->[$cnt  ] = [$tick,$val,$val_be,$tick_go];
    return $val;
}

sub push_ACTRR_and_tick($$$$$) {
    my ($space_ptr,$reg_name,$tick_parm,$data,$offset) = @_;
    my $val = 0;
    my $val_be = 0;
    my $tick_go,$tick;
    if(ref($tick_parm) eq "ARRAY") {
        $tick    = $tick_parm->[0];
        $tick_go = $tick_parm->[1];
    } else {
        $tick    = $tick_parm;
        $tick_go = $tick_parm;
    }
    $cnt = 0;
    if($space_ptr->{$reg_name}) {
        my $my_ref = ref($space_ptr->{$reg_name});
        if($my_ref eq "ARRAY") {
            $cnt = 1*@{$space_ptr->{$reg_name}};
            # print "push_reg_and_tick: reg_name=$reg_name data=$data offset=$offset \n";
            if($cnt) {
                $val = $space_ptr->{$reg_name}->[$cnt-1]->[1];
                $val_be = $space_ptr->{$reg_name}->[$cnt-1]->[2];
                # if the tick of this transaction is the same as the previous, then overite it
                if($space_ptr->{$reg_name}->[$cnt-1]->[0]==$tick) { $cnt -= 1; }
            }
        } else {
            delete $space_ptr->{$reg_name};
        }
    }
    $val = $val & ~(0xFF<<($offset*8)); # Clear the byte that I want to write.
    $val = $val | ($data<<($offset*8)); # Write a signle byte to register.
    $val_be |= (1<<$offset);
    $space_ptr->{$reg_name}->[$cnt  ] = [$tick,$val,$val_be,$tick_go];
    return $val;
}

sub pcie_registers_parse(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l1} or die_ERROR("080 ERROR: ");
    my $read_record_func1 = (defined($parms{read_record_func1}) ? $parms{read_record_func1} : \&psf_file_read_record);
    my $count=0;
    my $space_ptr = $PCIE_CFG_SPACE->{$parms{PCIE_DEVICE}}->{$parms{PCIE_FUNCTION}};
    my %is_pcie_bridge = ( 1=>1, 6=>1 , 7=>1 ); # The PEG1[012], PEG60 and TCSS are the bridge and hence have MBASE and PMBASE
    if(!defined($space_ptr)) {
        $space_ptr = { };
        $PCIE_CFG_SPACE->{$parms{PCIE_DEVICE}}->{$parms{PCIE_FUNCTION}} = $space_ptr;
    }

    my $cfg_base = ($parms{PCIE_DEVICE}<<19) | ($parms{PCIE_FUNCTION}<<16);
    # corelate the MWr
    for my $i (0..((+@{$trans_l1})-1)) {
        my $rec1_ptr = $trans_l1->[$i];
        if($rec1_ptr->{cmd} =~ /CfgWr/) {
            my $addr = $rec1_ptr->{address};
            my $data_be_str =  record_2_data_be_str($rec1_ptr);

            while($data_be_str=~s/[_\s]*([xa-fA-F0-9][xa-fA-F0-9])$//) {
                if($1 ne "xx") {
                    my $data = $1;
                    my $offset;

                    $offset = $addr - $cfg_base-0x04; # Parse GCMD register
                    if($offset>=0 && $offset<2) {
                        push_reg_and_tick($space_ptr,"GCMD",$rec1_ptr->{tick_beg},hex($data),$offset);
                    }

                    if($parms{PCIE_DEVICE}==$NPK_DID) {
                        $offset = $addr - $cfg_base-0x20; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<8) {
                            $space_ptr->{RTIT_BASE} |= (hex($data) << ($offset*8));
                            $space_ptr->{RTIT_BASE_be} |= (1 << ($offset));
                            $space_ptr->{RTIT_BASE} &= 0xFFFFFFFFFFFFC000; # Register is always 1MB alligned
                            $space_ptr->{RTIT_LIMIT_be} |= (1 << ($offset));
                            $space_ptr->{RTIT_LIMIT} =  $space_ptr->{RTIT_BASE};
                            $space_ptr->{RTIT_LIMIT} |= 0x3FFF; # FIXME: Need to determize the size of NPK RTIT range from SM
                        }
                    } else {
                      if($is_pcie_bridge{$parms{PCIE_DEVICE}}) {
                        $offset = $addr - $cfg_base-0xD8; # Parse MPC register
                        if($offset>=0 && $offset<4) {
                            push_reg_and_tick($space_ptr,"MPC",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x20; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{MBASE} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{MBASE_be} |= (1 << ($offset+2));
                            $space_ptr->{MBASE} &= 0xFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x22; # Parse PMLIMIT LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{MLIMIT} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{MLIMIT_be} |= (1 << ($offset+2));
                            $space_ptr->{MLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x28; # Parse PMBASE register
                        if($offset>=0 && $offset<4) {
                            $space_ptr->{PMBASE} |= (hex($data) << ($offset*8+32));
                            $space_ptr->{PMBASE_be} |= (1 << ($offset+4));
                            $space_ptr->{PMBASE} &= 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x24; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{PMBASE} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{PMBASE_be} |= (1 << ($offset+2));
                            $space_ptr->{PMBASE} &= 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x2c; # Parse PMLIMIT register
                        if($offset>=0 && $offset<4) {
                            $space_ptr->{PMLIMIT} |= (hex($data) << ($offset*8+32));
                            $space_ptr->{PMLIMIT_be} |= (1 << ($offset+4));
                            $space_ptr->{PMLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x26; # Parse PMLIMIT LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{PMLIMIT} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{PMLIMIT_be} |= (1 << ($offset+2));
                            $space_ptr->{PMLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x19; # Read SBUSN_0_1_0_PCI register
                        if($offset==0) {
                            my $bus = hex($data);
                            if($parms{PCIE_DEVICE}==7) { $bus+=2 }; # If TCSS TBT PCIE, then actual bus is +2.
                            push_reg_and_tick($space_ptr,"SBUSN",$rec1_ptr->{tick_beg},$bus,$offset);
                        }
                        $offset = $addr - $cfg_base-0x1A; # Read SUBUSN_0_1_0_PCI register
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"SUBUSN",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                      }
                        $offset = $addr - $cfg_base-0xe0; # Read Power state register.
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"PMCS",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x3e; # Read Power state register.
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"BCTRL",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                    }

                    # Reading PCIE bar in 10h address. This was done to collect thr MTB BASE & LIMIT
                    for my $bar_index (0..$bar_max_index) {
                        $offset = $addr - $cfg_base-(0x10+$bar_index*8); # Parse PMBASE LOW register
                        if($offset>=0 && $offset<8) {
                            my $bar_mask = $DID_info_h{$parms{PCIE_DEVICE}}->{BAR_MASK}->{$bar_index};
                            if(!defined($bar_mask) || !$bar_mask) { $bar_mask = 0xF_FFFF; }
                            if(!defined($space_ptr->{$bar_index})) { $space_ptr->{$bar_index} = { }; }
                            my $base_byte = hex($data) & (((0xFFFFFFFFFFF00000|~$bar_mask)>>($offset*8))&0xFF); # Apply the bar mask
                            my $bar_base = push_reg_and_tick($space_ptr->{$bar_index},"BASE",$rec1_ptr->{tick_beg},$base_byte,$offset);
                            my $bar_limit = (($bar_base|$bar_mask)>>($offset*8)) & 0xFF;
                            push_reg_and_tick($space_ptr->{$bar_index},"LIMIT",$rec1_ptr->{tick_beg},$bar_limit,$offset);
                            if(!defined($space_ptr->{GCMD})) { $space_ptr->{GCMD} = [ ]; }
                        }
                    }
                    $offset = $addr - $cfg_base-0x590; # Parse VTDBADDRL register
                    if($offset>=0 && $offset<4) {
                        $space_ptr->{VTD_BASE} |= (hex($data) << ($offset*8));
                        $space_ptr->{VTD_BASE_be} |= (1 << ($offset));
                        $space_ptr->{VTD_BASE} &= 0xFFFFFFFFFFFF0000; # Register is always 1MB alligned
                        $space_ptr->{VTD_LIMIT_be} |= (1 << ($offset));
                        $space_ptr->{VTD_LIMIT} =  $space_ptr->{VTD_BASE};
                        $space_ptr->{VTD_LIMIT} |= 0xFFFF; # Register is always 1MB alligned
                    }
                    $offset = $addr - $cfg_base-0x58C; # Parse VTDBADDRH LOW register
                    if($offset>=0 && $offset<4) {
                        $space_ptr->{VTD_BASE} |= (hex($data) << ($offset*8+32));
                        $space_ptr->{VTD_BASE_be} |= (1 << ($offset+4));
                        $space_ptr->{VTD_BASE} &= 0xFFFFFFFFFFFF0000; # Register is always 1MB alligned
                        $space_ptr->{VTD_LIMIT_be} |= (1 << ($offset+4));
                        $space_ptr->{VTD_LIMIT} =  $space_ptr->{VTD_BASE};
                        $space_ptr->{VTD_LIMIT} |= 0xFFFF; # Register is always 1MB alligned
                    }
                }
                $addr += 1;
            }
            print "  Parse transactions $rec1_ptr->{line}" if $debug>=5;
        }
    }

}

sub Dump_BIOS_register($$$$) {
    my ($reg_name,$reg,$tick,$is_dump) = @_;
    my $val = ($reg ? chkget_reg_val_in_tick($reg,$tick) : undef );
    if($val) {
        printf "BIOS Register $reg_name=%012X\n",$val if $is_dump;
        return $val;
    }
    return undef;
}

sub idi_registers_parse(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l1} or die_ERROR("081 ERROR: ");
    my $read_record_func1 = (defined($parms{read_record_func1}) ? $parms{read_record_func1} : \&psf_file_read_record);
    my $count=0;
    my $space_ptr = $PCIE_CFG_SPACE->{$parms{PCIE_DEVICE}}->{$parms{PCIE_FUNCTION}};
    if(!defined($space_ptr)) {
        $space_ptr = { };
        $PCIE_CFG_SPACE->{$parms{PCIE_DEVICE}}->{$parms{PCIE_FUNCTION}} = $space_ptr;
    }

    my $cfg_base = ($parms{PCIE_DEVICE}<<19) | ($parms{PCIE_FUNCTION}<<16);
    # corelate the MWr
    for my $i (0..((+@{$trans_l1})-1)) {
        my $rec1_ptr = $trans_l1->[$i];
        my $BAR;
        if($rec1_ptr->{cmd} =~ /\b(PORT_OUT|WIL)\b/) {
            my $cmd = $1;
            my $addr = (($rec1_ptr->{address}>>6)<<6);
            my $data_be_str =  record_2_data_be_str($rec1_ptr);
            my $PCIE_DEVICE = $parms{PCIE_DEVICE};

            if($cmd eq "PORT_OUT") {
                if(($addr & 0xFFFFFFFF_FFFFFC00) == 0x80000000) {
                    # Write device 00:00:00
                    $cfg_base=0x80000000;
                    $PCIE_DEVICE=0;
                } else {
                    next;
                }
            } elsif($cmd eq "WIL") {
                my $PCIEXBAR = $PCIE_CFG_SPACE->{0}->{0}->{PCIEXBAR};
                my $PCIEXBAR_val = ($PCIEXBAR ? chkget_reg_val_in_tick($PCIEXBAR,$rec1_ptr->{tick_beg}) : undef );

                my $MCHBAR = $PCIE_CFG_SPACE->{0}->{0}->{MCHBAR};
                my $MCHBAR_val = ($MCHBAR ? chkget_reg_val_in_tick($MCHBAR,$rec1_ptr->{tick_beg}) : undef );

                my $VTDPVC0BAR = $PCIE_CFG_SPACE->{0}->{0}->{VTDPVC0BAR};
                my $VTDPVC0BAR_val = ($VTDPVC0BAR ? chkget_reg_val_in_tick($VTDPVC0BAR,$rec1_ptr->{tick_beg}) : undef );

                if($PCIEXBAR_val and $PCIEXBAR_val&1 and ($addr>>10) == ($PCIEXBAR_val>>10)) {
                    $cfg_base=$PCIEXBAR_val>>10<<10;
                    $PCIE_DEVICE=0;
                    $BAR =  "PCIEXBAR";
                } elsif($MCHBAR_val and $MCHBAR_val&1 and ($addr>>16) == ($MCHBAR_val>>16)) {
                    $cfg_base=$MCHBAR_val>>16<<16;
                    $PCIE_DEVICE=0;
                    $BAR = "MCHBAR";
                } elsif($VTDPVC0BAR_val and $VTDPVC0BAR_val&1 and ($addr>>12) == ($VTDPVC0BAR_val>>12)) {
                    $cfg_base=$VTDPVC0BAR_val>>12<<12;
                    $PCIE_DEVICE=0;
                    $BAR = "VTDPVC0BAR";
                } else {
                    next;
                }
            } else {
                next;
            }

            while($data_be_str=~s/[_\s]*([xa-fA-F0-9][xa-fA-F0-9])$//) {
                if($1 ne "xx") {
                    my $data = $1;
                    my $offset;

                    $offset = $addr - $cfg_base-0x04; # Parse GCMD register
                    if($offset>=0 && $offset<2) {
                        push_reg_and_tick($space_ptr,"GCMD",$rec1_ptr->{tick_beg},hex($data),$offset);
                    }

                    if($BAR eq "MCHBAR") {
                        $offset = $addr - $cfg_base-0x5410; # Parse VTDPVC0BAR
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"VTDPVC0BAR",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x5090; # Parse REMAPBASE
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"REMAPBASE",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x5098; # Parse REMAPLIMIT
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"REMAPLIMIT",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                    } elsif($BAR eq "VTDPVC0BAR") {
                        $offset = $addr - $cfg_base-0x18; # Parse VTDPVC0_GCMD
                        if($offset>=0 && $offset<4) {
                            push_reg_and_tick($space_ptr,"VTDPVC0_GCMD",$rec1_ptr->{tick_beg},hex($data),$offset);
                            Dump_BIOS_register("VTDPVC0_GCMD",$PCIE_CFG_SPACE->{0}->{0}->{"VTDPVC0_GCMD"},undef,$debug>=9);
                        }
                        $offset = $addr - $cfg_base-0x20; # Parse VTDPVC0_RTADDR
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"VTDPVC0_RTADDR",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                    } elsif($PCIE_DEVICE==0) {
                        $offset = $addr - $cfg_base-0x60; # Parse PCIEXBAR
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"PCIEXBAR",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x54; # Parse PCIEXBAR
                        if($offset>=0 && $offset<4) {
                            push_reg_and_tick($space_ptr,"DEVEN",$rec1_ptr->{tick_beg},hex($data),$offset);
                            Dump_BIOS_register("DEVEN",$PCIE_CFG_SPACE->{0}->{0}->{"DEVEN"},undef,$debug>=9);
                        }
                        $offset = $addr - $cfg_base-0x48; # Parse PCIEXBAR
                        if($offset>=0 && $offset<8) {
                            push_reg_and_tick($space_ptr,"MCHBAR",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x5c; # Parse DPR_0_0_0_PCI
                        if($offset>=0 && $offset<4) {
                            if(ref($space_ptr->{"DPR"}) ne "ARRAY") { undef $space_ptr->{"DPR"} };
                            push_reg_and_tick($space_ptr,"DPR",[$rec1_ptr->{tick_beg},$rec1_ptr->{tick_go}],hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0xbc; # TOLUD
                        if($offset>=0 && $offset<4) {
                            $space_ptr->{TOLUD} |= (hex($data) << ($offset*8));
                            $space_ptr->{TOLUD_be} |= (1 << ($offset+2));
                            $space_ptr->{TOLUD} &= 0xFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0xa8; # TOUUD
                        if($offset>=0 && $offset<8) {
                            $space_ptr->{TOUUD} |= (hex($data) << ($offset*8));
                            $space_ptr->{TOUUD_be} |= (1 << ($offset+2));
                            $space_ptr->{TOUUD} &= 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
                        }
                    } elsif($PCIE_DEVICE==$NPK_DID) {
                        $offset = $addr - $cfg_base-0x20; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<8) {
                            $space_ptr->{RTIT_BASE} |= (hex($data) << ($offset*8));
                            $space_ptr->{RTIT_BASE_be} |= (1 << ($offset));
                            $space_ptr->{RTIT_BASE} &= 0xFFFFFFFFFFFFC000; # Register is always 1MB alligned
                            $space_ptr->{RTIT_LIMIT_be} |= (1 << ($offset));
                            $space_ptr->{RTIT_LIMIT} =  $space_ptr->{RTIT_BASE};
                            $space_ptr->{RTIT_LIMIT} |= 0x3FFF; # FIXME: Need to determize the size of NPK RTIT range from SM
                        }
                    } else {
                        $offset = $addr - $cfg_base-0xD8; # Parse MPC register
                        if($offset>=0 && $offset<4) {
                            push_reg_and_tick($space_ptr,"MPC",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x20; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{MBASE} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{MBASE_be} |= (1 << ($offset+2));
                            $space_ptr->{MBASE} &= 0xFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x22; # Parse PMLIMIT LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{MLIMIT} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{MLIMIT_be} |= (1 << ($offset+2));
                            $space_ptr->{MLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x28; # Parse PMBASE register
                        if($offset>=0 && $offset<4) {
                            $space_ptr->{PMBASE} |= (hex($data) << ($offset*8+32));
                            $space_ptr->{PMBASE_be} |= (1 << ($offset+4));
                            $space_ptr->{PMBASE} &= 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x24; # Parse PMBASE LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{PMBASE} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{PMBASE_be} |= (1 << ($offset+2));
                            $space_ptr->{PMBASE} &= 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x2c; # Parse PMLIMIT register
                        if($offset>=0 && $offset<4) {
                            $space_ptr->{PMLIMIT} |= (hex($data) << ($offset*8+32));
                            $space_ptr->{PMLIMIT_be} |= (1 << ($offset+4));
                            $space_ptr->{PMLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x26; # Parse PMLIMIT LOW register
                        if($offset>=0 && $offset<2) {
                            $space_ptr->{PMLIMIT} |= (hex($data) << ($offset*8+16));
                            $space_ptr->{PMLIMIT_be} |= (1 << ($offset+2));
                            $space_ptr->{PMLIMIT} |= 0xFFFFF; # Register is always 1MB alligned
                        }
                        $offset = $addr - $cfg_base-0x19; # Read SBUSN_0_1_0_PCI register
                        if($offset==0) {
                            my $bus = hex($data);
                            if($PCIE_DEVICE==7) { $bus+=2 }; # If TCSS TBT PCIE, then actual bus is +2.
                            push_reg_and_tick($space_ptr,"SBUSN",$rec1_ptr->{tick_beg},$bus,$offset);
                        }
                        $offset = $addr - $cfg_base-0x1A; # Read SUBUSN_0_1_0_PCI register
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"SUBUSN",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0xe0; # Read Power state register.
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"PMCS",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                        $offset = $addr - $cfg_base-0x3c; # Read Power state register.
                        if($offset==0) {
                            push_reg_and_tick($space_ptr,"BCTRL",$rec1_ptr->{tick_beg},hex($data),$offset);
                        }
                    }

                    for my $bar_index (0..$bar_max_index) {
                        $offset = $addr - $cfg_base-(0x10+$bar_index*8); # Parse PMBASE LOW register
                        if($offset>=0 && $offset<8) {
                            my $bar_mask = $DID_info_h{$PCIE_DEVICE}->{BAR_MASK}->{$bar_index};
                            if(!defined($bar_mask) || !$bar_mask) { $bar_mask = 0xF_FFFF; }
                            if(!defined($space_ptr->{$bar_index})) { $space_ptr->{$bar_index} = { }; }
                            my $base_byte = hex($data) & (((0xFFFFFFFFFFF00000|~$bar_mask)>>($offset*8))&0xFF); # Apply the bar mask
                            my $bar_base = push_reg_and_tick($space_ptr->{$bar_index},"BASE",$rec1_ptr->{tick_beg},$base_byte,$offset);
                            my $bar_limit = (($bar_base|$bar_mask)>>($offset*8)) & 0xFF;
                            push_reg_and_tick($space_ptr->{$bar_index},"LIMIT",$rec1_ptr->{tick_beg},$bar_limit,$offset);
                            if(!defined($space_ptr->{GCMD})) { $space_ptr->{GCMD} = [ ]; }
                        }
                    }
                    $offset = $addr - $cfg_base-0x590; # Parse VTDBADDRL register
                    if($offset>=0 && $offset<4) {
                        $space_ptr->{VTD_BASE} |= (hex($data) << ($offset*8));
                        $space_ptr->{VTD_BASE_be} |= (1 << ($offset));
                        $space_ptr->{VTD_BASE} &= 0xFFFFFFFFFFFF0000; # Register is always 1MB alligned
                        $space_ptr->{VTD_LIMIT_be} |= (1 << ($offset));
                        $space_ptr->{VTD_LIMIT} =  $space_ptr->{VTD_BASE};
                        $space_ptr->{VTD_LIMIT} |= 0xFFFF; # Register is always 1MB alligned
                    }
                    $offset = $addr - $cfg_base-0x58C; # Parse VTDBADDRH LOW register
                    if($offset>=0 && $offset<4) {
                        $space_ptr->{VTD_BASE} |= (hex($data) << ($offset*8+32));
                        $space_ptr->{VTD_BASE_be} |= (1 << ($offset+4));
                        $space_ptr->{VTD_BASE} &= 0xFFFFFFFFFFFF0000; # Register is always 1MB alligned
                        $space_ptr->{VTD_LIMIT_be} |= (1 << ($offset+4));
                        $space_ptr->{VTD_LIMIT} =  $space_ptr->{VTD_BASE};
                        $space_ptr->{VTD_LIMIT} |= 0xFFFF; # Register is always 1MB alligned
                    }
                }
                $addr += 1;
            }
            print "  Parse transactions $rec1_ptr->{line}" if $debug>=5;
        }
    }
    
    if($debug>=2) {
        Dump_BIOS_register("PCIEXBAR",$PCIE_CFG_SPACE->{0}->{0}->{"PCIEXBAR"},undef,1);
        Dump_BIOS_register("DEVEN",$PCIE_CFG_SPACE->{0}->{0}->{"DEVEN"},undef,1);
        Dump_BIOS_register("MCHBAR",$PCIE_CFG_SPACE->{0}->{0}->{"MCHBAR"},undef,1);
        Dump_BIOS_register("VTDPVC0BAR",$PCIE_CFG_SPACE->{0}->{0}->{"VTDPVC0BAR"},undef,1);
        Dump_BIOS_register("VTDPVC0_GCMD",$PCIE_CFG_SPACE->{0}->{0}->{"VTDPVC0_GCMD"},undef,1);
        Dump_BIOS_register("VTDPVC0_RTADDR",$PCIE_CFG_SPACE->{0}->{0}->{"VTDPVC0_RTADDR"},undef,1);
    }

}

sub idi_ACTRR_range_parse(@) {
    my ($trans_l1,$ACTRR_DATA_h) = @_;
    my $count=0;

    if(!defined($PCIE_CFG_SPACE->{0}->{0}->{CCE_SEAM_CONFIG})) {
        push_reg_and_tick($PCIE_CFG_SPACE->{0}->{0},"CCE_SEAM_CONFIG",1,1,0);
    }

    my $cfg_base = $ACTRR_DATA_range_l->[0]->{BASE};
    # corelate the MWr
    for my $i (0..((+@{$trans_l1})-1)) {
        my $rec_ptr = $trans_l1->[$i];
        my $BAR;
        if(is_addr_in_range_l_fast(($rec_ptr->{address}),$ACTRR_DATA_range_l)) {
            my $cmd = $1;
            my $addr = (($rec_ptr->{address}>>6)<<6);
            my $data_be_str =  record_2_data_be_str($rec_ptr);

            while($data_be_str=~s/[_\s]*([xa-fA-F0-9][xa-fA-F0-9])$//) {
                if($1 ne "xx") {
                    my $data = $1;
                    my $offset;

                    $offset = $addr & 7; # Parse GCMD register
                    push_ACTRR_and_tick($ACTRR_DATA_h,($addr-$cfg_base)&0xFFFFFFFF_FFFFFFF8,$rec_ptr->{tick_beg},hex($data),$offset);

                }
                $addr += 1;
            }
            print "  Parse ACTRR trans ".trans_str($rec_ptr) if $debug>=5;
        }
    }
    
}

sub is_ACTRR_trusted($) {
    my ($address) = @_;
    my $my_keyid = ($address & $sys_addr_mktme_mask);
    if($address & $sys_addr_mktme_mask) {
        $my_keyid >>= $sys_addr_mktme_bit;
        for my $keyid (@{$sysinit{TDX_trusted}}) {
            if($my_keyid==$keyid) { return 1; }
        }
        return 0; 
    }
    else { return 0; }
}

sub calc_ACTRR_address($) {
    my ($address) = @_;
    if($sysinit{HBO_SINGLE_MC} or $soc_hbo_hash_disable) {
        return (($address >> 21) << 6) + (($address>>15) & 0x3F & 0x38);
    } else {
        $address0 = $address;
        $address = (($address >> 21) << 6) + (($address>>15) & 0x3F & 0x38);
        $address = (($address>>($soc_hbo_hash_lsb))<<($soc_hbo_hash_lsb+1)) | ($address&((1<<($soc_hbo_hash_lsb))-1));
        $address ^= (1<<$soc_hbo_hash_lsb) unless hbo_hash_get_idx($address+$ACTRR_DATA_range_l->[0]->{BASE}) == hbo_hash_get_idx($address0);
        return $address;
    }
}

sub calc_ACTRR_bit($) {
    my ($address) = @_;  
    my $byte_bit  = (($address >> 12) & 0x07);
    if(!($sysinit{HBO_SINGLE_MC} or $soc_hbo_hash_disable)) {
        $address = (($address>>($soc_hbo_hash_lsb+1))<<($soc_hbo_hash_lsb)) | ($address&((1<<($soc_hbo_hash_lsb))-1));
    }
    return  $byte_bit | (($address >> 12) & 0x38);
}

sub ACTRR_str($) {
    my ($rec_ptr) = @_;
    return "addr=".addr_str($ACTRR_DATA_range_l->[0]->{BASE} + calc_ACTRR_address($rec_ptr->{address}))." bit=".calc_ACTRR_bit($rec_ptr->{address});
}

sub idi_ACTRR_filter($$) { 
    my ($trans_l,$ACTRR_DATA_h) = @_;
    if(!defined($trans_l)) { return 1; } 
    my $MONITOR_read = ($is_e2e_monitor_read ? "^MONITOR|" : "");
    for my $rec_ptr (@$trans_l) {
        if(!is_ACTRR_trusted($rec_ptr->{mktme_address}) 
            and (get_reg_val_in_tick($ACTRR_DATA_h->{calc_ACTRR_address($rec_ptr->{address})},$rec_ptr->{tick_beg}) >> calc_ACTRR_bit($rec_ptr->{address})) & 1
            and (get_reg_val_in_tick($PCIE_CFG_SPACE->{0}->{0}->{CCE_SEAM_CONFIG},$rec_ptr->{tick_beg})&1)
        ) {
            if($rec_ptr->{cmd} =~ /^(WOWrInv|WIL|WBMTOI|WBMTOE|WCIL|ITOMWR|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SELFSNPINV|ITOMWR_WT|SNPCURR)/) {
                $rec_ptr->{canceled} = 1;
                print "ACTRR ".ACTRR_str($rec_ptr)." block write trans : ".trans_str($rec_ptr) if $debug>=5;
            } elsif($rec_ptr->{cmd} =~ /^(${MONITOR_read}RDCURR|PRD|RFO|DRD|CRD|UCRDF)/) {
                if($rec_ptr->{data}=~/[1-9a-fA-F]/) {
                    die_ERROR("155 ERROR: This read trans should be zeroed by ACTRR : ".trans_str($rec_ptr));
                }
                $rec_ptr->{canceled} = 1;
                print "ACTRR ".ACTRR_str($rec_ptr)." block read trans : ".trans_str($rec_ptr) if $debug>=5;
            }
        }
        delete $rec_ptr->{mktme_address} if $debug<3;
    }
    return 0;
}

sub create_TDX_MKTME_info() {
    $sysinit{TDX_trusted}  = [];

    if($sysinit{TDX_EN}) {
        if ($sysinit{MKTME_KEYID_BITS} == 4 && $sysinit{TDX_KEYID_BITS} == 4) {
            #shared_keyid = 0;
            $sysinit{TDX_trusted}  = [1..15];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 4 && $sysinit{TDX_KEYID_BITS} == 3) {
            #shared_keyid inside {[0:1]};
            $sysinit{TDX_trusted}  = [2..15];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 4 && $sysinit{TDX_KEYID_BITS} == 2) {
            #shared_keyid inside {[0:3]};
            $sysinit{TDX_trusted}  = [4..15];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 4 && $sysinit{TDX_KEYID_BITS} == 1) {
            #shared_keyid inside {[0:7]};
            $sysinit{TDX_trusted}  = [8..15];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 3 && $sysinit{TDX_KEYID_BITS} == 3) {
            #shared_keyid = 0;
            $sysinit{TDX_trusted}  = [2,4,6,8,10,12,14];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 3 && $sysinit{TDX_KEYID_BITS} == 2) {
            #shared_keyid inside {0,2};
            $sysinit{TDX_trusted}  = [4,6,8,10,12,14];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 3 && $sysinit{TDX_KEYID_BITS} == 1) {
            #shared_keyid inside {0,2,4,6};
            $sysinit{TDX_trusted}  = [8,10,12,14];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 2 && $sysinit{TDX_KEYID_BITS} == 2) {
            #shared_keyid = 0;
            $sysinit{TDX_trusted}  = [4,8,12];
        } elsif ($sysinit{MKTME_KEYID_BITS} == 2 && $sysinit{TDX_KEYID_BITS} == 1) {
            #shared_keyid inside {0,4};
            $sysinit{TDX_trusted}  = [8,12];
        }
    }
}

# 
sub create_byte_stream(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l};
    if(!$trans_l1) { die_ERROR("082 ERROR: "); }
    my $count=0;
    my @byte_stream_l;
    my $space_ptr = defined($parms{PCIE_FUNCTION}) ? $PCIE_CFG_SPACE->{$parms{PCIE_DEVICE}}->{$parms{PCIE_FUNCTION}} : undef;
    my $PCIE_PMLIMIT = $space_ptr->{PMLIMIT} || 0;
    my $PCIE_PMBASE  = $space_ptr->{PMBASE}  || 1;
    my $PCIE_MLIMIT  = $space_ptr->{MLIMIT}  || 0;
    my $PCIE_MBASE   = $space_ptr->{MBASE}   || 1;
    print($parms{label}." ") if $debug>=2 and $parms{label};

    # corelate the MWr
    for my $i (0..((+@{$trans_l1})-1)) {
        my $rec_ptr = $trans_l1->[$i];
        
        my $data_be_str = record_2_data_be_str($rec_ptr);

        my $addr = $rec_ptr->{address};
        if($rec_ptr->{rec_type} eq "mcc" or $rec_ptr->{rec_type} eq "mcc_preloader" or $rec_ptr->{rec_type} eq "idi") { no warnings; $addr &= 0xFFFFFFFF_FFFFFFC0; }
        if($rec_ptr->{rec_type} eq "psf" or $rec_ptr->{rec_type}) { no warnings; $addr &= 0xFFFFFFFF_FFFFFFFC; }
        # Skip if address hit the PMBASE & PMLIMIT range
        if($addr>=$PCIE_PMBASE && $addr<$PCIE_PMLIMIT) { 
            next;
        }
        if($addr>=$PCIE_MBASE  && $addr<$PCIE_MLIMIT) { 
            next;
        }
        
        print "Convert transaction to stream: src_ch_tc=$ch_name_l[$rec_ptr->{src_ch_tc}]".(defined($rec_ptr->{src_ch_rd})?" src_ch_rd=$ch_name_l[$rec_ptr->{src_ch_rd}]":"")."\n  address=".addr_str($rec_ptr->{address})." data=$data_be_str \n $rec_ptr->{line} " if($debug>=5); 

        while($data_be_str=~s/[_\s]*([xa-fA-F0-9][xa-fA-F0-9])$//) {
            if($1 ne "xx") {
                my %stream_rec = (
                    data => $1,
                    address => $addr,
                    # parent_idx => $i,
                    parent => $rec_ptr,
                    # cmd => $rec_ptr->{cmd},
                );
                ##$stream_rec{src_ch} = defined($parms{src_ch}) ? $parms{src_ch} : (defined($rec_ptr->{src_ch}) ? $rec_ptr->{src_ch} : "src_ch_none");
                ##$stream_rec{src_ch_tc} = $rec_ptr->{src_ch_tc} if defined($rec_ptr->{src_ch_tc});
                #$stream_rec{dst_ch} = defined($rec_ptr->{dst_ch}) ? $rec_ptr->{dst_ch} : "dst_ch_none";
                $stream_rec{BDF} = $rec_ptr->{BDF}   if defined($rec_ptr->{BDF});
                $stream_rec{id} = $rec_ptr->{id}     if defined($rec_ptr->{id}); 
                $stream_rec{sai} = $rec_ptr->{sai}     if defined($rec_ptr->{sai});
                $stream_rec{rs} = $rec_ptr->{rs}     if defined($rec_ptr->{rs});
                $stream_rec{at} = $rec_ptr->{at}     if defined($rec_ptr->{at});
                $stream_rec{tick_beg} = $rec_ptr->{tick_beg}     if defined($rec_ptr->{tick_beg});
                $stream_rec{tick_end} = $rec_ptr->{tick_end}     if defined($rec_ptr->{tick_end});
                $stream_rec{tick_go}  = $rec_ptr->{tick_go}      if defined($rec_ptr->{tick_go});
                $stream_rec{tick_mc}  = $rec_ptr->{parent_tick_mc}    if defined($rec_ptr->{parent_tick_mc});
                if(!defined($stream_rec{tick_mc}) and index($rec_ptr->{cmd},"WCIL")>=0) {
                    $stream_rec{attr} |= REC_ATTR_WCIL; # Mark it as WCIL from CCF
                }
                push @byte_stream_l,\%stream_rec;
            }
            $addr += 1;
        }
        $count += 1;
    }
    print($parms{label}." ") if $debug>=2 and $parms{label};
    print "Create_byte_stream from $count transactions\n" if $debug>=1;

    return \@byte_stream_l;
}

sub compare_byte_rec($$) {
    my ($rec_ptr1,$rec_ptr2) = @_;
    my $log_str;
    my $err_str;
    my $err_code = 0;
    local $iommu_scbd_ptr;
    if(defined($iommu_scbd_h)) {
        $iommu_scbd_ptr = ( ($iommu_scbd_h->{$ch_name_l[$rec_ptr1->{parent}->{src_ch}]}) or ($iommu_scbd_h->{"sai_".$rec_ptr1->{sai}}) or undef );  
    }
    $log_str .= "Comparing: data=$rec_ptr1->{data}\n  ".trans_str($rec_ptr1)."\n  ".trans_str($rec_ptr2)."\n" if($debug>=3); 
    for (@$field_l) {
        my $cmp = 0;

        if(defined($field_comperator_l{$_})) {
            $cmp = &{$field_comperator_l{$_}}($rec_ptr1,$rec_ptr2,$_);
        } elsif(($_ eq "address") && defined($iommu_scbd_ptr)) {
            my $address1 = IOMMU_convert_address($iommu_scbd_ptr,$rec_ptr1->{BDF},$rec_ptr1->{$_});
            my $address2 = $rec_ptr2->{$_};
            $cmp = $address1 == $address2;
        } elsif(($_ eq "uri_if_any")) {
            if(defined($rec_ptr1->{parent}->{uri}) and defined($rec_ptr2->{parent}->{uri})) {
                $cmp = ($rec_ptr1->{parent}->{uri}) eq ($rec_ptr2->{parent}->{uri});
            } elsif (defined($rec_ptr1->{parent}->{LID}) and defined($rec_ptr2->{parent}->{uri})) {
                $cmp = ($rec_ptr1->{parent}->{LID}) eq ($rec_ptr2->{parent}->{uri}) || ($rec_ptr1->{parent}->{PID}) eq ($rec_ptr2->{parent}->{uri});
            } elsif($rec_ptr1->{parent}->{cmd} eq "AWADDR") {
                $cmp = 1;
            } else {
                $cmp = 1;
            }
        } else {
            $cmp = $rec_ptr1->{$_} eq $rec_ptr2->{$_};
        }

        if(!$cmp) {
            if($debug>=3) {
                my $val1 = $_ eq "address" ? addr_str($rec_ptr1->{$_}) : $rec_ptr1->{$_};
                my $val2 = $_ eq "address" ? addr_str($rec_ptr2->{$_}) : $rec_ptr2->{$_};
                $err_str .= "003 ERROR: comparing $_ ($val1 != $val2) of $rec_ptr1->{parent}->{line} && $rec_ptr2->{parent}->{line}\n";
            } else {
                $err_str .= "003 ERROR: comparing\n";
            }
            $err_code = 1;
        }
    }
    return ($err_code,$log_str,$err_str);
}

# Temporaruily using this fast compare_byte_rec that does not support IOMMU
sub fast_compare_byte_rec($$) {
    my ($rec_ptr1,$rec_ptr2) = @_;
    my $log_str;
    my $err_str;
    my $err_code = 0;
    my $data;
    $log_str .= "Comparing: address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data}\n  address=".addr_str($rec_ptr1->{address})
        .(($debug_shash_index and $debug_shash_index->{$rec_ptr2->{shash_index}&0xFFFFFFFF}) ? " EYAL8:" : "")
        ." line=$rec_ptr1->{parent}->{line}\n  address=".addr_str($rec_ptr2->{address})." line=$rec_ptr2->{parent}->{line}\n" if($debug>=3); 

    if($rec_ptr1->{address} > $rec_ptr2->{address} || $rec_ptr1->{address} + (length($rec_ptr1->{data})>>1) <= $rec_ptr2->{address}) {
        if($debug>=3) {
            $err_str .= "047 ERROR: comparing address (".addr_str($rec_ptr1->{address})." != ".addr_str($rec_ptr2->{address}).") of $rec_ptr1->{parent}->{line} && $rec_ptr2->{parent}->{line}\n";
        } else {
            $err_str =  "047 ERROR: comparing adderss\n";
        }
        $err_code = 1;
    } elsif(!read_2_write_cmp($rec_ptr2,$rec_ptr2->{address}-$rec_ptr1->{address},$rec_ptr1->{data})) {
        if($debug>=3) {
            $err_str .= "048 ERROR: comparing data ($rec_ptr1->{data} != $rec_ptr2->{data}) of $rec_ptr1->{parent}->{line} && $rec_ptr2->{parent}->{line}\n";
        } else {
            $err_str =  "048 ERROR: comparing data\n";
        }
        $err_code = 1;
    }

    return ($err_code,$log_str,$err_str);
}

sub compare_write_order_channels {
    my ($astr,$bstr) = ($ch_name_l[$a->{src_ch_tc_key}],$ch_name_l[$b->{src_ch_tc_key}]);
    my $aspec = 1*$astr=~/Spec_SNP(\d+)/;
    my $aspec_cnt = $1;
    my $aspec_wr = 1*$astr=~/Spec_Wr/;
    my $bspec = 1*$bstr=~/Spec_SNP(\d+)/;
    my $bspec_cnt = $1;
    my $bspec_wr = 1*$bstr=~/Spec_Wr/;
    if( ($aspec||$aspec_wr) && !$bspec) { return  1; }
    if(!$aspec &&  ($bspec||$bspec_wr)) { return -1; }
    if( $aspec &&  $bspec) { return $aspec_cnt <=> $bspec_cnt; }
    return $astr cmp $bstr;
}

sub save_update_write_l1($$$) {
    my ($full_rec_ptr1,$name,$val) = @_;
    push @$write_updates_l,[$full_rec_ptr1->[OBJ_INDEX],$name,$val,$full_rec_ptr1->[OBJ_REC]->{$name},$full_rec_ptr1->[OBJ_REC]->{tick_beg}];
}

sub exec_update_write_l1($$) {
    my ($trans_l1,$write_updates_l) = @_;
    my $i; 
    my $i_max = 1*@$write_updates_l; 
    for($i=0; $i<$i_max ; $i+=1) {
        my ($index1,$name,$val,$old_val,$tick_beg) = @{$write_updates_l->[$i]};
        #if($trans_l1->[$index1]->{parent}) {
        #    $trans_l1->[$index1]->{parent}->{$name} = $val;
        #} else {
            $trans_l1->[$index1]->{$name} = $val;
        #}
        if($trans_l1->[$index1]->{tick_beg} != $tick_beg) {
            die_ERROR("164 ERROR: bad write_updates_l for i=$i index1=$index1,name=$name,val=$val,old_val=$old_val,tick_beg=$tick_beg");
        }
    }
}

sub gen_update_write_file($$) {
    my ($filename,$write_updates_l) = @_;
    my $i; 
    my $i_max = 1*@$write_updates_l; 
    unlink("$filename.txt.tmp.gz");
    unlink("$filename.txt.tmp");
    open(F,">$filename.txt.tmp") or die_ERROR("168 ERROR: can not zcat  and open write_update file $filename");
    for($i=0; $i<$i_max ; $i+=1) {
        my ($index1,$name,$val,$old_val,$tick_beg) = @{$write_updates_l->[$i]};
        print F "$index1,$name,$val,$old_val,$tick_beg\n"; 
    }
    close F;
    unlink("$filename.txt.gz");
    system("gzip $filename.txt.tmp");
    rename("$filename.txt.tmp.gz","$filename.txt.gz");
    unlink("$filename.txt.tmp.gz");
    return 1;
}

sub use_update_write_file($$) {
    my ($filename,$write_updates_l) = @_;
    my $fd;
    my $i_max = 1*@$write_updates_l; 
    if(!open_gz(\$fd,"$filename.txt",0)) {
        print_ERROR("167 WARNING: Can not open write_update file $filename.\n");
        exit(0);
    }
    while(<$fd>) {
        my @a = split ",",$_;
        if($#a!=4) {
            die_ERROR("165 ERROR: bad number or arguments in line : $_");
        }
        push @$write_updates_l,\@a;
    }
    close F;
    return 1;
}

# Compare transactions byte by byte
sub compare_write_byte_stream_l(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l1} or die_ERROR("083 ERROR: ");
    my $trans_l2 = $parms{trans_l2} or die_ERROR("084 ERROR: ");
    my $link_to  = ($parms{link_to} || undef);
    local $iommu_scbd_h = $parms{iommu_scbd_h};
    local $field_l = ($parms{field_l} or ["data","cmd","id","address","fbe_lbe"]);
    my $count=0; my $write_retry_count = 0; my $time_cnt=0;
    my $debug = $::debug;
    my $e2e_write_compare_count = $::e2e_write_compare_count;
    my $last_e2e_write_compare_count = $e2e_write_compare_count;
    #Virtual channel hash
    my %ch_h1;
    my $index1 = 0;
    my $index2 = 0;
    my $index1_vc;
    my @recompare_posibilities_l;
    my $is_mcc_log = ($parms{is_mcc_log} or 0);
    my $is_cmi_log = $parms{is_cmi_log} || (!defined($cmi_iop_trans_file_scbd) && !$lnl_mc_tick_update && $is_mcc_log);
    my $update_func = ($parms{update_func} or undef);
    local $write_updates_l = ($parms{write_updates_l} or []);
    my $save_src_ch_tc_point_h = { };

    if($parms{add_self_parent}){
        # Make this transation be the parent of inself because compare_write_byte_stream_l function, need a parent.
        for my $rec_ptr (@$trans_l1) { $rec_ptr->{parent} = $rec_ptr; }
        for my $rec_ptr (@$trans_l2) { $rec_ptr->{parent} = $rec_ptr; }
    }

    # split the first stream to source channels
    for (my $index1=0; $index1<=$#$trans_l1 ; $index1++) {
        my $rec_ptr1 = $trans_l1->[$index1];
        my @ch_rec_a;
        my $src_ch_tc = $rec_ptr1->{parent}->{src_ch_tc} or die_ERROR("085 ERROR: ");
        if(!defined($ch_h1{$src_ch_tc})) {
            my %new_ch_rec_l;
            $new_ch_rec_l{rec_l} = [];
            $new_ch_rec_l{rec_l_index}=0; #init the index to its rec_l
            $new_ch_rec_l{src_ch_tc_key}=$src_ch_tc;
            $ch_h1{$src_ch_tc} = \%new_ch_rec_l;
        } else { # Support here a case where no src_ch defined
        }
        $ch_rec_a[OBJ_INDEX] = $index1;
        $ch_rec_a[OBJ_REC]   = $rec_ptr1;
        push @{$ch_h1{$src_ch_tc}->{rec_l}},\@ch_rec_a;
    }
    $index1 = 0;

    my @trans_ch_l1;
    for (keys %ch_h1) { push @trans_ch_l1,$ch_h1{$_}; }
    @trans_ch_l1 = sort compare_write_order_channels @trans_ch_l1;
    for(my $ch_idx; $ch_idx<=$#trans_ch_l1 ; $ch_idx++) {
        $trans_ch_l1[$ch_idx]->{ch_idx} = $ch_idx
    }

    if($debug>=2) { my $ch_idx=0;
        print "012.1 COMP_FLOW: Write channel list : total ".(1*@trans_ch_l1)."\n";
        for my $ch_ptr (@trans_ch_l1) {
            print "write_ch0: ch_idx1=$ch_idx name=$ch_name_l[$ch_ptr->{src_ch_tc_key}] trans_count=".(1*@{$ch_ptr->{rec_l}})."\n"; $ch_idx+=1;
        }
        STDOUT->flush();
    }

    # corelate the MWr
    while($count<=$#$trans_l2) {
        my $rec_ptr1;
        my $rec_ptr2 = $trans_l2->[$index2];
        local %field_comperator_l = defined($parms{field_comperator_l}) ? @{$parms{field_comperator_l}} : ();

        my $match_case_l_ptr = [];

        my ($err_code,$log_str,$err_str);

        for my $ch_ptr (@trans_ch_l1) {
            if($ch_ptr->{rec_l_index}<+@{$ch_ptr->{rec_l}}) {
                $rec_ptr1 = $ch_ptr->{rec_l}->[$ch_ptr->{rec_l_index}]->[OBJ_REC];
            } else {
                $ch_ptr->{err_str} = "End_of_transaction_list\n";
                next; # Nothing more in rec_l of this channel
            }
            if($verify_write_time) {
                if(!defined($rec_ptr1->{tick_beg}) || !defined($rec_ptr2->{tick_beg})) {
                    #die_ERROR("148 ERROR: transactions in write compare does not have tick_beg");
                } elsif($rec_ptr1->{tick_beg}>$rec_ptr2->{tick_beg}) {
                    $ch_ptr->{err_str} = "Write did not happen yet\n"; next;
                }
            }
            $e2e_write_compare_count+=1;
            ($err_code,$log_str,$err_str) = compare_byte_rec($rec_ptr1,$rec_ptr2);
            if($err_code) {
                #$ch_h1{$rec_ptr1->{parent}->{src_ch_tc}}->[OBJ_INDEX] = $index1;
                $ch_h1{$rec_ptr1->{parent}->{src_ch_tc}}->{err_code} = $err_code;
                $ch_h1{$rec_ptr1->{parent}->{src_ch_tc}}->{err_str} = $err_str;
                $ch_h1{$rec_ptr1->{parent}->{src_ch_tc}}->{log_str} = $log_str;
            } else {
                my %match_case_h = (
                    log_str => $log_str,
                    index1 => $index1,
                    ch_ptr => $ch_ptr,
                );
                push @$match_case_l_ptr,\%match_case_h;
            }
        }

        my $is_match_again = 1;
        while($is_match_again==1) { # Matching loop
            if(0<=$#$match_case_l_ptr) {
                my $match_case_ptr = shift @$match_case_l_ptr;
                print $match_case_ptr->{log_str} if($debug>=9); 
                if($link_to) { $match_case_ptr->{ch_ptr}->{rec_l}->[ $match_case_ptr->{ch_ptr}->{rec_l_index} ]->[OBJ_REC]->{$link_to} = $trans_l2->[$index2]; }
                $err_code = 0;
                if(0<=$#$match_case_l_ptr) {
                    # If there are move possible match - save this compare point for future re-compare in case of future mismatch
                    my %posibility_h = (
                        match_case_l => $match_case_l_ptr,
                        index1 => $index1,
                        index2 => $index2,
                        count  => $count,
                        write_updates_count => $#$write_updates_l,
                    );
                    #for my $ch_ptr (@trans_ch_l1) {
                    #    $posibility_h{save_src_ch_tc_point_h}->{$ch_ptr->{src_ch_tc_key}}->{rec_l_index} = $ch_ptr->{rec_l_index};
                    #}
                    $posibility_h{save_src_ch_tc_point_h} = $save_src_ch_tc_point_h = { };
                    push @recompare_posibilities_l,\%posibility_h;
                }
                {
                my $full_rec_ptr1 = $match_case_ptr->{ch_ptr}->{rec_l}->[$match_case_ptr->{ch_ptr}->{rec_l_index}];
                my $rec_ptr1 = $full_rec_ptr1->[OBJ_REC]; 
                $rec_ptr2 = $trans_l2->[$index2];
                if($update_func) {
                    &$update_func($rec_ptr1,$rec_ptr2);
                }
                if($is_mcc_log) {
                    save_update_write_l1($full_rec_ptr1,"tick_end",$rec_ptr2->{tick_beg});
                    save_update_write_l1($full_rec_ptr1,"tick_mc",$rec_ptr2->{parent}->{tick_beg});
                    if($rec_ptr1->{parent}->{cmd} eq "AWADDR") { 
                        save_update_write_l1($full_rec_ptr1,"tick_go",$rec_ptr2->{parent}->{tick_beg});
                    }
                }
                if($is_cmi_log or ($is_mcc_log and !defined($rec_ptr1->{tick_go}))) {
                    save_update_write_l1($full_rec_ptr1,"tick_go",$rec_ptr2->{tick_beg});
                    my $snp_rec=get_trans_by_uri($idi_file_scbd->{DMI_snp_h}->{$rec_ptr2->{parent}->{uri}},$rec_ptr2,"tick_beg");
                    if(defined($snp_rec)) { check_trans_uri($snp_rec,$rec_ptr2); }
                    if(defined($snp_rec) and ($snp_rec->{address}>>6) == ($rec_ptr2->{address}>>6) ) {
                        my $tmp_tick_go = (($snp_rec->{rsp}=~/HitI/) ? $snp_rec->{tick_beg} : $snp_rec->{tick_end}); # I tried this but it did not worked : $snp_rec->{tick_beg} and also $snp_rec->{tick_end};
                        save_update_write_l1($full_rec_ptr1,"tick_go",$tmp_tick_go);
                    }
                }
                }
                # saving the previous ch index in order to restore.
                $save_src_ch_tc_point_h->{$match_case_ptr->{ch_ptr}->{ch_idx}} = $match_case_ptr->{ch_ptr}->{rec_l_index} unless (exists $save_src_ch_tc_point_h->{$match_case_ptr->{ch_ptr}->{ch_idx}});
                $match_case_ptr->{ch_ptr}->{rec_l_index} += 1;
                $index1 += 1;
                $is_match_again = 0;
            } elsif(0>$#$match_case_l_ptr) {
                if(0<=$#recompare_posibilities_l and ++$write_retry_count != $e2e_write_retry_count) {
                    # Try another match possibility if exists
                    my $posibility_h_ptr = pop @recompare_posibilities_l; $last_index2 = $index2;
                    $index1 = $posibility_h_ptr->{index1};
                    $index2 = $posibility_h_ptr->{index2};
                    $count  = $posibility_h_ptr->{count};
                    $#$write_updates_l = $posibility_h_ptr->{write_updates_count};
                    while (my ($key, $value) = each %{$posibility_h_ptr->{save_src_ch_tc_point_h}}) {
                        $trans_ch_l1[$key]->{rec_l_index} = $value;
                    }
                    #for my $ch_idx (0..$#trans_ch_l1) {
                    #    print "ch_idx=$ch_idx => $trans_ch_l1[$ch_idx]->{rec_l_index}\n";
                    #}
                    $match_case_l_ptr = $posibility_h_ptr->{match_case_l};
                    if($#{$match_case_l_ptr}>0 or $#recompare_posibilities_l<0) {
                        # if we have another case in this posibility then we need to clear the posibility list
                        $save_src_ch_tc_point_h = { };
                    } elsif($#recompare_posibilities_l>=0) {
                        # if we have no more case in this posibolity we have to take the $save_src_ch_tc_point_h from the previous posibility
                        $save_src_ch_tc_point_h = $recompare_posibilities_l[-1]->{save_src_ch_tc_point_h};
                    }
                    print "Mismatch at index2=$last_index2, but I am trying write_retry_count=$write_retry_count another possibility. Returning to index1=$index1 index2=$index2\n" if $debug>=5;
                    $is_match_again = 1; # Got to remap
                    if(!(++$time_cnt&0x1FF)) {
                        script_timeout_chk();
                    }
                    if($script_timeout) { return; }
                    if($debug>=2 and $e2e_write_compare_count-$last_e2e_write_compare_count>1000000) {
                        my $time_str = "";
                        if($is_dump_time) { $time_str = " pid=$$ time=".time(); }
                        print "Run status: index2=$index2 write_compare_count=$e2e_write_compare_count write_retry_count=$write_retry_count$time_str\n";
                        STDOUT->flush();
                        $last_e2e_write_compare_count = $e2e_write_compare_count;
                    }

                } else {
                    my $dump_mismatch_str;
                    # Dump compare error from all channles
                    for my $ch_ptr (@trans_ch_l1) {
                        if($ch_ptr->{err_code}) {
                            $dump_mismatch_str .= "mismatch in src_ch_tc=".$ch_name_l[$ch_ptr->{src_ch_tc_key}]." index2=$index2 : ".$ch_ptr->{err_str};
                        }
                    }

                    if($dump_mismatch_str) {
                        print_ERROR("023 ERROR in comparing all channels. Below I list the mismatched of every channel. rec2 is address=".addr_str($rec_ptr2->{address})." line: $rec_ptr2->{parent}->{line}");
                        print_ERROR("You probably need to review them all and see why there is no match with the correct channel.\n");
                        print_ERROR($dump_mismatch_str);
                    } else {
                        print_ERROR("026 ERROR there is transaction #$count in trans_l2 but no transaction in trans_l1. address=".addr_str($rec_ptr2->{address})." line:".$rec_ptr2->{parent}->{line}."\n");
                    }
                    $is_match_again = 2; # exit loop
                    $exit_code = 1;
                }
            } else {
                 die_ERROR("004 ERROR: Bad match case. Never suppose to get to here.");
            }
         
            if(!$is_match_again) {
                $count += 1;
                $index2+=1;
                if(!(++$time_cnt&0x1FF)) {
                    script_timeout_chk();
                    if($script_timeout) { return; }
                }
            }
        } # Matching loop
        if($is_match_again==2) { 
            last; # I got error. Not comparing any more
        }
    }
    print "  Compared $count transactions\n" if $debug>=1;
    $e2e_total_write_retry_count += $write_retry_count;

    if(+@{$trans_l1} != +@{$trans_l2}) {

        if(+@{$trans_l1} > +@{$trans_l2}) {
            if($cpu_proj ne "lnl") {
                print_ERROR("024 ERROR: These transactions in l1 after finished comparing all transactions in l0:\n");
                $exit_code = 1;
            }
            my @trans_ch_l1;
            for (keys %ch_h1) { push @trans_ch_l1,$ch_h1{$_}; }
            for my $ch_ptr (@trans_ch_l1) {
                if($ch_ptr->{rec_l_index}<+@{$ch_ptr->{rec_l}} && !($ch_name_l[$ch_ptr->{src_ch_tc_key}]=~/Spec_SNP|Spec_Wr/)) {
                    $rec_ptr1 = $ch_ptr->{rec_l}->[$ch_ptr->{rec_l_index}]->[OBJ_REC];
                    print_ERROR("025 ERROR: This transaction left unmatched in src_ch_tc=".$ch_name_l[$ch_ptr->{src_ch_tc_key}]." address=".addr_str($rec_ptr1->{address})." line=".$rec_ptr1->{parent}->{line}."\n");
                    $exit_code = 1;
                } else {
                    next; # Nothing more in rec_l of this channel
                }
            }
        } else {
            $exit_code = 1;
            print_ERROR(sprintf("005 ERROR: list sizes to compare don't match - %d != %d\n",@{$trans_l1}*1,@{$trans_l2}*1));
        }

    }

    if($index1 != $index2) {
        print_ERROR(sprintf("006 ERROR: index1 != index2 - %d != %d\n",$index1,$index2));
        $exit_code = 1;
    }

    if(!+@{$trans_l1} || !+@{$trans_l2} and $parms{fail_count_zero}) {
        print_ERROR(sprintf("007 ERROR: list sizes to compare don't match - %d != %d\n",@{$trans_l1}*1,@{$trans_l2}*1));
        $exit_code = 1;
    }

    if($parms{add_self_parent}){
        # Make this transation be the parent of inself because compare_write_byte_stream_l function, need a parent.
        for my $rec_ptr (@$trans_l1) { delete $rec_ptr->{parent}; }
        for my $rec_ptr (@$trans_l2) { delete $rec_ptr->{parent}; }
    }

    if(!$exit_code and !$parms{write_updates_l}) {
        exec_update_write_l1($trans_l1,$write_updates_l);
    }

}

# Convert a record to data_be string to byte stream creation
sub record_2_data_be_str($) {
    my $rec_ptr = shift;
    if($rec_ptr->{rec_type} eq "psf" or $rec_ptr->{rec_type} eq "pcie" or $rec_ptr->{rec_type} eq "opio" or $rec_ptr->{rec_type} eq "svt") {
        my ($fbe,$lbe);

        ## Prepare the @be_l
        my $be_full_str;
        if($rec_ptr->{fbe_lbe} =~/^([01]{4})_([01]{4})$/) {
            $fbe=$1; $lbe = $2;
        } else {
            die_ERROR("086 ERROR: ");
        }
        $be_full_str = $fbe;
        if($rec_ptr->{length}>=3) {
            $be_full_str = ("1" x (4*($rec_ptr->{length}-2))).$be_full_str;
        }
        if($rec_ptr->{length}>=2) {
            $be_full_str = $lbe.$be_full_str;
        }

        my $data_str = $rec_ptr->{data};
        if($rec_ptr->{rec_type} eq "pcie") { 
            #$data_str =~ s/^[^:]+://; 
            $data_str =~ s/[-_]*-[-_]*//; 
        }

        return psf_prepare_data_and_be_string($data_str,$be_full_str);

    } elsif($rec_ptr->{rec_type} eq "mcc_preloader" or $rec_ptr->{rec_type} eq "idi") {
        my $data_str = $rec_ptr->{data};
        $data_str=~s/-/x/g;
        return $data_str;
    } else {
        return $rec_ptr->{data};
    }
}

sub bin2dec($) {
    my $res = 0;
    for (split(//,$_[0])) {
        if($_ eq "0") {
            $res = ($res<<1);
        } elsif($_ eq 1) {
            $res = ($res<<1) + 1;
        }
    }
    return $res;
}

sub opio_or_pcie_link_data_manipulation($) {
    my $my_data = $_[0];
    $my_data =~s/^[-\s_]+//;
    if($my_data=~/^(\w\w\w\w\w\w\w\w)[_\s](\w\w\w\w\w\w\w\w)[_\s]+(\w\w\w\w\w\w\w\w)[_\s](\w\w\w\w\w\w\w\w)$/) {
        $my_data = "$3_$4:$1_$2";
    } elsif($my_data=~/^[\s_]*(\w\w\w\w\w\w\w\w)[_\s]+(\w\w\w\w\w\w\w\w)[_\s](\w\w\w\w\w\w\w\w)$/) {
        $my_data = "$2_$3:         $1";
    } elsif($my_data=~/^---------[_\s]--------[_\s]+(\w\w\w\w\w\w\w\w)[_\s](\w\w\w\w\w\w\w\w)$/) {
        $my_data = "$1_$2";
    } else {
        $my_data=~s/\s+/_/g;
    }
    return $my_data;
}

sub join_data_str($$$) {
    my ($breaker_str,$data_ptr,$my_data) = @_;
    $$data_ptr = (length($$data_ptr) ? $$data_ptr.$breaker_str.$my_data : $my_data);
}

sub mark_non_snoop_addr($) {
    my $rec_ptr = shift;
    my $bit_set = 0;
    if($rec_ptr->{cmd}=~/^(MWr|AWADDR|Invd|WCILF|WCIL|MemWr)/) {
        $bit_set = 1;
    } elsif($rec_ptr->{cmd}=~/MRd/) {
        $bit_set = 2;
    } else {
        return 0;
    }
    my $addr = $rec_ptr->{address};
    $pch_non_snoop_addr_h{$addr>>6} |= $bit_set;
    print "WARNING: $rec_ptr->{rec_type} LINK has non-snoop MWR or MRd to ".addr_str($rec_ptr->{address})." , So I skip e2e check if err on this address. $rec_ptr->{line}" if $debug>=7;
    my $last_addr;
    my $len = 1*$rec_ptr->{length};
    while($len>0) {
        $last_addr = $addr;
        $addr+=4;
        $pch_non_snoop_addr_h{$addr>>6} |= $bit_set unless ($last_addr>>6) == ($addr>>6);
        $len-=1;
    }
}

%opio_link_file_opcode_to_MsgType = (
    MsgD0=>0x70, MsgD1=>0x71, MsgD2=>0x72, MsgD3=>0x73, 
);

%opio_link_header_h = ();

sub opio_link_file_read_record($) {
    local $_ = shift;
    if(!/^|\s+\d+/) { return undef; } 

    my @a = split /\s*\|\s*/;
    $a[13]=~s/ /_/;
    $a[14]=~m/[ \w]+$/;
    my %rec = ( 
        id=>lc($a[10]."_".$a[11]), 
        BDF=>lc($a[10]),
        direction=>($a[4] eq "DWNSTRM" ? "U" : "D") , # cerfull . I invert the direction here. Because is SOC we need it inverted.
        cmd=>$a[3],
        address=>big_hex($a[9]),
        data=>$a[14],
        fbe_lbe=>$a[13],
        length=>$a[15],
        sai=>$a[$opio_link_header_h{SAI}],
        at=>$a[$opio_link_header_h{AT}],
        rs=>$a[$opio_link_header_h{RTS}],
        ns=>$a[$opio_link_header_h{NS}],
        rec_type=>"opio",
        );

    if($rec{length}=~/--/) { $rec{length}=0; }

    my $tick = ( ($rec{cmd}=~/^Cpl/i) ? $a[2] : $a[1] );
    if($tick=~m/^([0-9][0-9\.]+)/) {
        $rec{tick} = $tick_mul*1000.0*$1;
    }

    my $MsgType = $opio_link_file_opcode_to_MsgType{$rec{cmd}};
    if(defined($MsgType)) {
        my @tlp_l;
        my $fbe_lbe_dec = bin2dec($rec{fbe_lbe}) & 0xFF;
        $tlp_l[0] = ($MsgType<<24) | $rec{length};
        $tlp_l[1] = (hex($rec{BDF})<<16) | ($a[11]<<8) | ($fbe_lbe_dec);
        $tlp_l[2] = $rec{address} & 0xFFFFFFFF;
        $tlp_l[3] = $rec{address} >> 32;
        $rec{tlp} = \@tlp_l;
    }

    if($rec{fbe_lbe}) {
        # Switch the FBE & LBE that seems to be inverted related to other PSF files
        $rec{fbe_lbe} =~s/^([10]+)_([01]+)/$2_$1/;
    }

    if($a[12]=~/^[0-9a-fA-F]+$/) {
        $rec{src_ch} = get_ch_id("opio");
        $rec{src_ch_tc} = get_ch_id("opio_tc_$a[12]");
    }

    return \%rec;
}

sub opio_link_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;
    my $last_cmd_line;
    my $last_cmd_line_data_join;
    my @header_l = ();
    my $SAI_filter = big_hex("dfca62f79ef320e0"); # This is the default vaule.

    $scbd->{read_record_func} = \&opio_link_file_read_record;

    if(defined($PCIE_CFG_SPACE->{0}->{0}->{OPI_SAIFILTER_ACL})) {
        $SAI_filter = ($SAI_filter & 0xFFFFFFFF00000000) | $PCIE_CFG_SPACE->{0}->{0}->{OPI_SAIFILTER_ACL};
    }
    if(defined($PCIE_CFG_SPACE->{0}->{0}->{OPI_SAIFILTER_ACH})) {
        $SAI_filter = ($SAI_filter & 0x0FFFFFFFF) | ($PCIE_CFG_SPACE->{0}->{0}->{OPI_SAIFILTER_ACH}<<32);
    }

    my $start_header = 0;

    while(<$fd>) {
        if($start_header==0) {
            if(/^\|\s+\|\s+\|/) { $start_header=1; }
        }
        if($start_header==1) {
            if(/^\|==========/) { $start_header = 2; last; }
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for my $title (@a) {
                $title=~s/^\s+//;
                $title=~s/\s+$//;
                $header_l[$i] .= $title;
                $i++;
            }
        }
    }

    if($start_header==2) { 
        my $i = 0;
        for(@header_l) {
            $opio_link_header_h{$_} = $i;
            $i++;
        }
    } else { return 0 }

    while(<$fd>) {
        if(index($_,"EER occurred")>=0 && !defined($skip_OPIO_LINK_err)) {
            if($ACERUN_TESTNAME=~/\bPKGC7\b|\bPKGC8\b|\bPKGC9\b|\bPKGC10\b/) {
                $skip_OPIO_LINK_err = 1;
            }
            next;
            # In case I see this "EER occurred" in OPIO_LINK file, then I will skip 
        } elsif(/^\|.*(UPSTRM|DWNSTRM)/) {
            my $line = $_;
            my $is_join = 0;

            my $rec_ptr = &{$scbd->{read_record_func}}($_) or next;
            $rec_ptr->{line} = $line;

            if($rec_ptr->{direction} eq "U" && $rec_ptr->{cmd}=~/^(MRd|MWr)/) {
                my $sai6 = $convert_8bit_sai_to_6bit{hex($rec_ptr->{sai})};
                if(defined($sai6) && defined($SAI_filter)) {
                    if(!get_field($SAI_filter,$sai6,$sai6)) {
                        $rec_ptr->{is_UR} = "OPIO_SAI_UR";
                    }
                }
            }

            if($rec_ptr->{cmd} =~ /^(CAS|Swap|FAdd|IOWr|IORd|MRd|CfgRd|CfgWr|LTMRd32)/) {
                # We expect a cpl with length 0 or all Wr cmd and length fo Rd cmd
                $rec_ptr->{length_cpl} = ($rec_ptr->{cmd}=~/Wr/ ? 0 : $rec_ptr->{length});
                push @{$scbd->{ $rec_ptr->{direction} }->{ $rec_ptr->{id} }} , $rec_ptr;
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                if($argv{skip_if_non_snoop} && $rec_ptr->{ns}) {
                    mark_non_snoop_addr($rec_ptr);
                }
            } elsif($rec_ptr->{cmd} =~ /^Cpl/) {
                $rec_ptr->{data} = "";
                my $other_direction = ($rec_ptr->{direction} eq "U" ? "D" : "U");
                my $id_list_ptr = $scbd ->{$other_direction} -> { $rec_ptr->{id} };
                my $tr = $id_list_ptr->[0];
                if(defined($tr)) {
                    if($debug>=3) {
                        print "In   :id=".$rec_ptr->{id}.": ".$tr->{line};
                        print " Out :id=".$rec_ptr->{id}.": ".$line; 
                    }
                    $tr->{length_recv} += $rec_ptr->{length};
                    if(/UNSUP_REQ/) {
                        shift @$id_list_ptr;
                        $tr->{is_UR}="OPIO_UR";
                    } elsif($tr->{length_recv} < $tr->{length_cpl}) {
                        $rec_ptr->{my_req} = $tr;
                    } elsif($tr->{length_recv} == $tr->{length_cpl}) {
                        shift @$id_list_ptr;
                        $tr->{tick_end} = $rec_ptr->{tick};
                        $tr->{data} = undef;
                        $rec_ptr->{my_req} = $tr;
                        if($tr->{is_UR}) {
                            $exit_code=1;
                            print_ERROR("040 ERROR: This transaction shoulg get UR $tr->{is_UR} : $tr->{line}");
                        }
                    } elsif($tr->{length_recv} > $tr->{length_cpl}) {
                        print_ERROR("008 ERROR: Too many data DW received by this transaction: $line");
                        $exit_code=1;
                    }
                } else {
                    print_ERROR("009 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
            } elsif($rec_ptr->{cmd}=~/^(Msg|MWr)/) {
                $rec_ptr->{data}="";
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                $last_cmd_line = $line;
                my $sai6 = $convert_8bit_sai_to_6bit{hex($rec_ptr->{sai})};
                if($argv{skip_if_non_snoop} && $rec_ptr->{ns}) {
                    mark_non_snoop_addr($rec_ptr);
                }
            } elsif($rec_ptr->{cmd}=~/^Data/ && length($rec_ptr->{direction})>=1) {
                # This code join all data from the next lines  
                my $trans_l = $scbd->{ $rec_ptr->{direction} }->{ all };
                my $fix_line_idx = +@$trans_l;
                my $fix_line = $trans_l->[$fix_line_idx-1]->{line};
                if(defined($last_cmd_line_data_join)) {
                    if($last_cmd_line eq $last_cmd_line_data_join) {
                        $is_join = 1;
                    }
                } else {
                    if($last_cmd_line eq $fix_line) {
                        $is_join = 1;
                        $last_cmd_line_data_join = $fix_line;
                    }
                }
                if($is_join && $fix_line_idx>=1) {
                    join_data_str(":",\$trans_l->[$fix_line_idx-1]->{data},opio_or_pcie_link_data_manipulation($rec_ptr->{data}));
                }
            } else {
                undef $last_cmd_line;
            }

            if(!$is_join) {
                undef $last_cmd_line_data_join;
            }
        }
    }

    psf_check_all_Cpl($scbd);

    # copy the Cpl Data to its Mrd
    psf_Cpl_to_MRd_data($scbd);
    assign_rec_parent_idx($scbd->{U}->{all});
    assign_rec_parent_idx($scbd->{D}->{all});

}

%pcie_link_file_MsgType_to_opcode = (
    0x70=>"MsgD0", 0x71=>"MsgD1", 0x72=>"MsgD2", 0x73=>"MsgD3", 
);

sub pcie_link_file_read_record($) {
    local $_ = shift;
    if(!/^\s*\d+/ && !/^\s*-/) { return undef; } 

    my %cmd_convert = (
        "CFG_WR_0" => "CfgWr0",
        "CFG_WR_1" => "CfgWr1",
        "CFG_RD_0" => "CfgRd0",
        "CFG_RD_1" => "CfgRd1",
        "MEM_WR" => "MWr32",
        "MEM_RD" => "MRd",
        "LT_RD" => "LTMRd",
        "IO_WR"  => "IOWr",
        "IO_RD"  => "IORd",
        "MSG"    => "Msg",
        "MSG_D"  => "MsgD",
        "CMPLT_D"=> "CplD",
        "CMPLT"  => "Cpl",
        "SWAP"   => "Swap",
        "SWAP32" => "Swap",
        "SWAP64" => "Swap",
        "CAS"    => "CAS",
        "FETCH_ADD" => "FAdd",
        "FADD"   => "FAdd",
        "FADD32" => "FAdd",
        "FADD64" => "FAdd",
    );

    my @a = split /\s+/;
    $a[$header_h{"ADDRESS"}]=~s/ /_/;
    $a[$header_h{"ADDRESS"}+1]=~m/[ \w]+$/;
    $a[$header_h{"TAG"}]=~s/^0+(\w\w)$/$1/; # Fix for ICL-G
    my %rec = ( 
        id=>lc($a[$header_h{"REQ"}]."_".$a[$header_h{"TAG"}]), 
        BDF=>lc($a[$header_h{"REQ"}]),
        direction=>$a[$header_h{"DIR"}] , 
        cmd=>($cmd_convert{$a[$header_h{"COMMAND"}]} or $a[$header_h{"COMMAND"}]),
        address=>big_hex(($a[$header_h{"ADDRESS"}] eq "--------" ? "00000000" : $a[$header_h{"ADDRESS"}]).$a[$header_h{"ADDRESS"}+1]),
        data=>($a[$header_h{"HEADER/DATA"}]."_".$a[$header_h{"HEADER/DATA"}+1]."_".$a[$header_h{"HEADER/DATA"}+2]."_".$a[$header_h{"HEADER/DATA"}+3]),
        fbe_lbe=> ( $a[$header_h{"BEF"}]=~/^-/ ? undef : sprintf("%04b_%04b",hex($a[$header_h{"BEF"}]),hex($a[$header_h{"BEL"}])) ),
        length=>+$a[$header_h{"LEN/INDEX"}],
        ns=>(1*$a[$header_h{"SNR"}]),
        rec_type=>"pcie",
        src_ch_tc => $src_ch_tc_pcie, # This will give src_ch_tc only for D transactions.
        );
    my $rec_ext_ptr = {
        serial_number=>$a[$header_h{"SEQ"}],
    };

    my $tick = ( ($rec{cmd}=~/^Cpl/i) ? $a[$header_h{"FINISHTIME"}] : $a[$header_h{"STARTTIME"}] );
    if($tick=~m/^([0-9][0-9\.]+)/) {
        $rec{tick} = $tick_mul*1000.0*$1;
    }

    if(($rec{cmd}=~/^Cfg/ || $rec{cmd}=~/^M[WR]/ || $rec{cmd}=~/CAS|Swap|FAdd/) && $rec{direction} eq "U") {
        $rec{src_ch} = get_ch_id($local_src_ch);
        if($rec{cmd}=~/CAS|Swap|FAdd/) { $rec{src_ch} = append_ch_id($rec{src_ch},"_atom"); }
        $rec{src_ch_tc} = append_ch_id($rec{src_ch},"_tc_".$a[11]); ## the next two lines can be used instead of this line to make the pcie write changes order
        ##$rec{src_ch_rd} = append_ch_id($rec{src_ch},"_tc_".$a[11]);
        ##$rec{src_ch_tc} = append_ch_id($rec{src_ch},"_tc_".$a[11]._.sprintf("_MWR%04d",$pcie_trans_count++));
        $rec{vc} = $a[$header_h{"VC/TC"}];
    }

    if($rec{cmd}=~/^Msg/) {
        $rec{tlp} = [hex($a[24]),hex($a[25]),hex($a[26])];
        my $tmp_cmd=$pcie_link_file_MsgType_to_opcode{$rec{tlp}->[0]>>24};
        if(defined($tmp_cmd)) { $rec{cmd} = $tmp_cmd; }
    }

    return (\%rec,$rec_ext_ptr);
}

sub pcie_link_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;
    my $last_cmd_line;
    my $last_cmd_line_data_join;
    my $last_MWr_rec_ptr;
    my %serial_number_h;
    my $is_fix_little_indian = !!($scbd->{filename}=~/(DMI|PEG\d+)_pkt_trk.log/);
    local $src_ch_tc_pcie = get_ch_id("pcie"); # This will give src_ch_tc only for D transactions.
    local $pcie_trans_count;

    my @header_l = ();
    local %header_h = ();
    my $start_header = 0;

    while(<$fd>) {
        if($start_header==0) {
            if(/^\|\s+\|\s+\|/) { $start_header=1; }
        }
        if($start_header==1) {
            if(/^\|-+\+-+\+-/) { $start_header = 2; last; }
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for my $title (@a) {
                $title=~s/^\s+//;
                $title=~s/\s+$//;
                $header_l[$i] .= $title;
                $i++;
            }
        }
    }

    if($start_header==2) { 
        my $i = 0;
        for(@header_l) {
            $header_h{$_} = $i;
            if(/^CREDITS/) { $i++;};
            if(/^ADDRESS/) { $i++; }
            if(/^HEADER\/DATA/) { $i+=4; }
            $i++;
        }
        if(!$header_h{"FINISHTIME"}) { $header_h{"FINISHTIME"}=$header_h{"TIME"}; }
        if(!$header_h{"STARTTIME"}) { $header_h{"STARTTIME"}=$header_h{"TIME"}; }
    } else { return 0 }

    $scbd->{read_record_func} = \&pcie_link_file_read_record;

    while(<$fd>) {
        if(/ [UD] /) {
            undef $last_MWr_rec_ptr;
            my $line = $_;
            my $is_join = 0;

            my ($rec_ptr,$rec_ext_ptr) = &{$scbd->{read_record_func}}($_) or next;
            next unless defined($rec_ptr->{id});
            if(!$emulation_obj_file and defined($header_h{"SEQ"}) and 1<++($serial_number_h{$rec_ptr->{direction}.":".$rec_ptr->{id}.":".$rec_ext_ptr->{serial_number}})) { 
                next; # Avoid reading duplicate opcode twice. This usually happens in PEG BFM files. 
            }
            $rec_ptr->{line} = $line;

            if(defined($iommu_scbd_ptr) and $rec_ptr->{cmd}=~/^(CAS|Swap|FAdd|MRd|MWr)/) {
                $rec_ptr->{address} = IOMMU_convert_address($iommu_scbd_ptr,$rec_ptr->{BDF},$rec_ptr->{address});
            }

            if($rec_ptr->{cmd} =~ /^(CAS|Swap|FAdd|IOWr|IORd|MRd|CfgRd|CfgWr|LTMRd)/) {
                push @{$scbd->{ $rec_ptr->{direction} }->{ $rec_ptr->{id} }} , $rec_ptr;
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
                if($rec_ptr->{cmd} =~ /^(Swap|FAdd|CAS)/) {
                    # To emulate Swap, I add MWrSwap pseudo opcode here.
                    # No need to create MRdSwap to, because the Swap command will play that role.
                    my $new_rec_ptr = { };
                    for(keys %$rec_ptr) { $new_rec_ptr->{$_} = $rec_ptr->{$_}; }
                    $new_rec_ptr->{cmd} = "MWr$rec_ptr->{cmd}";
                    $new_rec_ptr->{fbe_lbe} = "1111_1111";
                    $new_rec_ptr->{data}="";
                    $last_MWr_rec_ptr = $new_rec_ptr;
                    $rec_ptr->{atomic_rec} = $new_rec_ptr;
                    push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $new_rec_ptr;
                    push @{$scbd->{ "A" }->{ all }} , $new_rec_ptr;
                } else {
                }
                if($argv{skip_if_non_snoop} && $rec_ptr->{ns}) {
                    mark_non_snoop_addr($rec_ptr);
                }
            } elsif($rec_ptr->{cmd} =~ /^Cpl/) {
                my $other_direction = ($rec_ptr->{direction} eq "U" ? "D" : "U");
                my $tr = shift @{$scbd ->{$other_direction} -> { $rec_ptr->{id} }};
                if($tr) {
                    if($debug>=3) {
                        print "In   :id=$id: ".$tr->{line};
                        print " Out :id=$id: ".$line; 
                    }
                    if($tr->{cmd}=~/^(MRd|CAS|Swap|FAdd|IOWr|IORd|CfgRd|CfgWr|LTMRd)/) {
                        push @{$tr->{Cpl_rec}},$rec_ptr;
                        $tr->{tick_end} = $rec_ptr->{tick};

                        # If  not all bytes where received, then push $tr back to queue. 
                        my $rcv_len = 0;
                        for $cpl_rec (@{$tr->{Cpl_rec}}) {
                            $rcv_len += $cpl_rec->{length};
                        }

                        my $max_length;
                        if($tr->{cmd}=~/^CAS/) {              $max_length = $tr->{length}/2;
                        } elsif($tr->{cmd}=~/CfgWr|IOWr/) {   $max_length = 0;
                        } else {                              $max_length = $tr->{length};
                        }

                        if($rcv_len<$max_length) {
                            unshift @{$scbd ->{$other_direction} -> { $rec_ptr->{id} }},$tr;
                        } elsif($rcv_len>$max_length) {
                            print_ERROR("055 ERROR: Too many Cpl were recived for Trans: $tr->{line}\n");
                            $exit_code=1;
                        }
                    }
                    $rec_ptr->{data}="";
                    $last_MWr_rec_ptr = $rec_ptr;
                } else {
                    print_ERROR("010 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
            } elsif($rec_ptr->{cmd}=~/^(MWr|Msg)/i) {
                $rec_ptr->{data}="";
                $last_MWr_rec_ptr = $rec_ptr;
                if($rec_ptr->{length}<=64) { # This is to filter too big TLP in ADL (the PEG just drop them).
                    push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                }
                $last_cmd_line = $line;
                if($argv{skip_if_non_snoop} && $rec_ptr->{ns}) {
                    mark_non_snoop_addr($rec_ptr);
                }
            } elsif($rec_ptr->{cmd}=~/^Data/ && length($rec_ptr->{direction})>=1) {
                # This code join all data from the next lines  
                my $trans_l = $scbd->{ $rec_ptr->{direction} }->{ all };
                my $fix_line_idx = +@$trans_l;
                my $fix_line = $trans_l->[$fix_line_idx-1]->{line};
                if(defined($last_cmd_line_data_join)) {
                    if($last_cmd_line eq $last_cmd_line_data_join) {
                        $is_join = 1;
                        $rec_ptr->{data} = "";
                    }
                } else {
                    if($last_cmd_line eq $fix_line) {
                        $is_join = 1;
                        $last_cmd_line_data_join = $fix_line;
                    }
                }
                if($is_join && $fix_line_idx>=1) {
                    my @a1 = split /\|/,$fix_line; 
                    my @a2 = split /\|/,$line; 
                    $a1[14] .= ":". $a2[14]; 
                    my $new_line = join "|",@a1;
                    $trans_l->[$fix_line_idx-1]->{line} = $new_line;
                    my $my_data = $a1[14];
                    $trans_l->[$fix_line_idx-1]->{data} .= length($trans_l->[$fix_line_idx-1]->{data}) ? ":".$my_data : $my_data;
                }
            } else {
                undef $last_cmd_line;
            }

            if(!$is_join) {
                undef $last_cmd_line_data_join;
            }
        } elsif(/ P0 /) {
            next; # Skip like this that apears in DMI link file: - -    P0 8E200012 --------
        } elsif($last_MWr_rec_ptr) {
            my ($rec_ptr,$rec_ext_ptr) = &{$scbd->{read_record_func}}($_) or next;
            if($rec_ptr->{cmd} =~/^-+$/ && $rec_ptr->{length}=~/^[0-9]/) {
                if($is_fix_little_indian) { $rec_ptr->{data} = fix_little_indian($rec_ptr->{data}); }
                join_data_str(":",\$last_MWr_rec_ptr->{data},opio_or_pcie_link_data_manipulation($rec_ptr->{data}));
            };
        }
    }
    
    # Go over the transactions and calculate the atomic commands
    for my $tr (@{$scbd->{ "U" }->{ all }}) {
        if($tr->{cmd}=~/^(MRd|Swap|FAdd|CAS)/) {
            if($tr->{cmd}=~/^FAdd/) {
                $tr->{atomic_rec}->{data} = FAdd_data($tr->{atomic_rec},$tr->{Cpl_rec}->[0],$tr->{length});
            } elsif($tr->{cmd}=~/^CAS/) {
                $tr->{data} = $tr->{atomic_rec}->{data};
                $tr->{atomic_rec}->{data} = $tr->{Cpl_rec}->[0]->{data};
                CAS_Atomic($tr,$tr->{Cpl_rec}->[0]->{data});
            } elsif($tr->{cmd}=~/^MRd/) {
                $tr->{data} = $tr->{Cpl_rec}->[0]->{data};
                for my $i (1..(@{$tr->{Cpl_rec}}-1)) {
                    $tr->{data} .= ":".$tr->{Cpl_rec}->[$i]->{data};
                }
            }
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});
    assign_rec_parent_idx($scbd->{D}->{all});
}





sub parse_all_psf_files_in_dir() {

    opendir(D,".");

    while($_ = readdir(D)) {
        if(/(.*iosf.trk|PSFNODE.*iosf.hw_mon.trk)(\.gz)?$/) {
            my $fd;
            my $filename = $1; 
            local $iommu_scbd_ptr;

            next unless 
            /^TBTPCIE0_/ || /^TBTPCIE1_/ || /^TBTPCIE2_/ || /^TBTPCIE3_/ ||
            ((/^TBTDMA0_/ || /^TBTDMA1_/) && !$skip_TBTDMA_PSF) ||
            /^PEG10/ || /^PEG11/ || /^PEG12/ || /^PEG60/ ||
            /^peg10/ || /^peg11/ || /^peg12/ || /^peg60/ || /^peg62/ ||
            /^DMI/ || /^IOP/ || /^IOM/ || /^DISPLAY/ ||/^display/ || /^NPK/ || /^XHCI/ || /^XDCI/ || /^GMM/ || /^GNA/ ||/^gna/ ||
            /^OPIO_/ || /^opi_soc_tb/ || /^IDC_/ || /^PEP_/ ||
            /^PSF\d--PSF\d_/ || /^psfpci/ || /^psftctop/ || /^tam/ || /^ipu/
            # Emulation files
            || /_IOP.psf/ || /_OPI.psf/ || /_NPK.psf/ || /_GNA.psf/
            || /^IOSF_PRI_IOP_TRK/ || /^IOSF_PRI_IOC_TRK/ || /^dmi_soc_tb/ || /^npk_soc_tb/;
            ;

            $filename = open_gz(\$fd,$filename,1) or next;
 
            if($debug>=1) {
                Reading_file_dump($_);
            }
 
            my %psf_file_scbd;
 
            $psf_file_scbd{filename} = $filename;

            if($cpu_proj eq "lnl") {
                $psf_file_scbd{tick_mul}=$tick_mul*1000.0;
            } else {
                $psf_file_scbd{tick_mul}=$tick_mul;
            }

            if(/IOSF_PRI_IOC_TRK/) {  # do iommu convertion for LNL project
                $iommu_scbd_ptr = $ioc_iommu_file_scbd; 
            }

            psf_file_reader($fd,\%psf_file_scbd);
            close $fd;
            psf_file_post_process(\%psf_file_scbd);
 
            if($filename =~/^OPIO_|^opi_soc_tb|_OPI.psf/) {
                $opio_psf_file_scbd = \%psf_file_scbd;
            } elsif($filename =~/^IOP_soc_|_IOP.psf|^IOSF_PRI_IOP_TRK|^IOSF_PRI_IOC_TRK/) {
                $iop_psf_file_scbd = \%psf_file_scbd;
                if($ACERUN_SYSTEM_MODEL=~/^soc_c2saf_model_compute/ or $ACERUN_CLUSTER=~/^ioc/) {
                    $pegs_psf_file_scbd = \%psf_file_scbd;
                    $pegs_psf_file_scbd->{U} = $pegs_psf_file_scbd->{D};
                    $pegs_psf_file_scbd->{D} = { all => [] };
                }
            }
           
            if($filename =~/^TBTPCIE0_/) {
                $pcie_psf_file_scbd_l[0] = \%psf_file_scbd;
            } elsif($filename =~/^TBTPCIE1_/) {
                $pcie_psf_file_scbd_l[1] = \%psf_file_scbd;
            } elsif($filename =~/^TBTPCIE2_/) {
                $pcie_psf_file_scbd_l[2] = \%psf_file_scbd;
            } elsif($filename =~/^TBTPCIE3_/) {
                $pcie_psf_file_scbd_l[3] = \%psf_file_scbd;
            } elsif($filename =~/^(PEG|peg)(\d+)_/) {
                $pcie_psf_file_scbd_l[$2] = \%psf_file_scbd;
            } elsif($filename =~/^DMI_|^dmi_soc_tb/) {
                $dmi_psf_file_scbd = \%psf_file_scbd;
            } elsif($filename =~/(NPK|npk_soc_tb)/) {
                $psf_file_scbd{file_src_ch} = "$1_src_ch";
                $npk_psf_file_scbd = \%psf_file_scbd;
                $psf_file_scbd{VC_h} = { 0=>"VC0b"};
            } elsif($filename =~/(psfpci)/) {
                $psf_file_scbd{file_src_ch} = "$1_src_ch";
                if($ACERUN_SYSTEM_MODEL=~/^(chassis_astro_mem|chassis_mem_model|chassis_model)/) {
                    $pegs_psf_file_scbd = \%psf_file_scbd;
                    $psf_file_scbd{VC_h} = { 0=>"VC0c", 1=>"VC0d", 3=>"VC0f", 4=>"VCrt" };
                }
            } elsif($filename =~/(psftctop)/) {
                $psf_file_scbd{file_src_ch} = "$1_src_ch";
                if($ACERUN_SYSTEM_MODEL=~/^(chassis_astro_mem|chassis_mem_model|chassis_model)/) {
                    $tcss_psf_file_scbd = \%psf_file_scbd;
                    $psf_file_scbd{VC_h} = { 0=>"VC0h" };
                }
            } elsif($filename =~/^(PEP_)/) {
                $psf_file_scbd{file_src_ch} = "$1_src_ch";
                $pep_psf_file_scbd = \%psf_file_scbd;
            } elsif($filename =~/(GMM|XDCI|XHCI|IDC|PEP|GNA|gna|DISPLAY|display|tam|ipu)/) {
                my $name = $1;
                if($name=~/DISPLAY/i) {
                    $psf_file_scbd{VC_h} = { 0=>"VC0a" , 1=>"VC1a" };
                } elsif($name=~/XDCI|XHCI/) {
                    $psf_file_scbd{VC_h} = { 0=>"VC0h" };
                } elsif($name=~/ipu/) {
                    $psf_file_scbd{VC_h} = { 0=>"VC0a", 1=>"VC1b", 2=>"VC2a" };
                } else {
                    $psf_file_scbd{VC_h} = { 0=>"VC0b" };
                }
                $psf_file_scbd{file_src_ch} = "${name}_src_ch";
                ($psf_file_scbd{DID},$psf_file_scbd{FID}) = @{$all_DID_h{uc($name)}} or die_ERROR("028 ERROR: Can not find DID for this DEVIDE $1");
                push @more_psf_file_scbd ,\%psf_file_scbd;
            } elsif($filename =~/^TBTDMA0_/ && !$skip_TBTDMA_PSF) {
                $tbtdma_psf_file_scbd_l[0] = \%psf_file_scbd;
            } elsif($filename =~/^TBTDMA1_/ && !$skip_TBTDMA_PSF) {
                $tbtdma_psf_file_scbd_l[1] = \%psf_file_scbd;
            } elsif($filename =~/^PSF0--PSF5/) {
                $PSF5_psf_file_scbd = \%psf_file_scbd;
            }
        }
    }
    close D;

    return 1;
}

sub parse_OPIO_LINK_file() {

    my $fd;
    my $filename;
    $filename = (open_gz(\$fd,"OPIO_LINK_trk.out",0)) or return 0;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my %psf_file_scbd;

    $psf_file_scbd{filename} = $filename;

    opio_link_file_reader($fd,\%psf_file_scbd);
    #psf_file_post_process(\%psf_file_scbd);

    if($filename =~/^OPIO_LINK/) {
        $opio_link_file_scbd = \%psf_file_scbd;
    }
}

sub parse_idi_file($$$) {

    my $fd;
    local %idi_header_h = ();
    local ($_,$scbd,$use_idi_hbo_hash) = @_;
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $idi_header_h{$_} = $i++; }
            last;
        }
    }

    $scbd->{filename} = $filename;

    $scbd->{read_record_func} = \&idi_file_read_record;
    idi_file_reader($fd,$scbd);
    close $fd;
}

sub parse_cfi_trk_file() {

    local %cmd_conv = (
        "WOWrInv"       => "WIL",
        "WOWrInvF"      => "WIL",
        "WrInv"         => "WIL",
        "ItoMWr"         => "WIL",
        "DirtyEvict"    => "WIL",
        "RdAny"         => "DRD",
        "RdOwn"         => "DRD",
        "RdShared"      => "DRD",
        "RdCurr"        => "DRD",
    );

    local %cfi_trk_typ_conv = (
        "IDI_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        "UPI_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        "VC0_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        "VC1_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        "UPI_WB"        => { TRANSMIT_DATA => "C2U DATA" },
        "VC0_WUO"       => { TRANSMIT_DATA => "C2U DATA" },
        "VC0_RwD"       => { TRANSMIT_DATA => "C2U DATA" },
        "VC1_RwD"       => { TRANSMIT_DATA => "C2U DATA" },
        "VC0_NCS"       => { TRANSMIT_DATA => "C2U DATA" },
        "VC0_NCB"       => { TRANSMIT_DATA => "C2U DATA" },
        "IDI_SNP"       => { RECEIVE_REQ  => "U2C REQ" },
        "UPI_SNP"       => { RECEIVE_REQ  => "U2C REQ" },
        "VC0_NDR"       => { RECEIVE_RSP   => "U2C RSP" , TRANSMIT_RSP  => "C2U RSP" },
        "VC1_NDR"       => { RECEIVE_RSP   => "U2C RSP" , TRANSMIT_RSP  => "C2U RSP" },
        "VC0_DRS"       => { TRANSMIT_DATA => "C2U DATA" ,RECEIVE_DATA  => "U2C DATA" },
        "VC1_DRS"       => { TRANSMIT_DATA => "C2U DATA" ,RECEIVE_DATA  => "U2C DATA" },
    );

    my $fd;
    local %idi_header_h = ();
    local $_ = "SOC_CFI_trk.log";
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if(!system("zgrep -q Err SOC_CFI_trk.log")) {
        printf("Exit soc_e2e_checker because I am not supporting Err in the SOC_CFI_trk file.\n");
        exit(0);
    }

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    $cfi_trk_file_scbd->{filename} = $filename;
    local $scbd = $cfi_trk_file_scbd;
    $scbd->{tick_mul} = $tick_mul*1000.0;

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $idi_header_h{$_} = $i++; }
            last;
        }
    }

    if(defined($idi_header_h{CQID})) {
    } else {
        $scbd->{read_record_func} = \&cfi_trk_file_read_record_CFI7;
        
        cfi_file_reader($fd,$scbd);
    }
    close $fd;
    
}

sub parse_ufi_trk_file() {

    local %cmd_conv = (
        "WOWrInv"       => "WIL",
        "WOWrInvF"      => "WIL",
        "WrInv"         => "WIL",
        "ItoMWr"         => "WIL",
        "DirtyEvict"    => "WIL",
        "RdAny"         => "DRD",
        "RdOwn"         => "DRD",
        "RdShared"      => "DRD",
        "RdCurr"        => "DRD",
    );

    local %ufi_trk_typ_conv = (
        "VN0_REQ"       => { A2F => { REQ  => "C2U REQ" } },
        "VN0_WB"        => { A2F => { REQ  => "C2U REQ" , DATA  => "C2U DATA"} },
        "VN0_SNP"       => { F2A => { REQ  => "U2C REQ" } },
        "VN0_RSP"       => { A2F => { RSP  => "C2U RSP" , DATA  => "C2U DATA" } , F2A => { RSP  => "U2C RSP" , DATA  => "U2C DATA" } },
        "VN0_NCS"       => { A2F => { DATA  => "C2U DATA"} },

        #"IDI_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        #"UPI_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        #"VC0_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        #"VC1_REQ"       => { TRANSMIT_REQ  => "C2U REQ" },
        #"UPI_WB"        => { TRANSMIT_DATA => "C2U DATA" },
        #"VC0_WUO"       => { TRANSMIT_DATA => "C2U DATA" },
        #"VC0_RwD"       => { TRANSMIT_DATA => "C2U DATA" },
        #"VC1_RwD"       => { TRANSMIT_DATA => "C2U DATA" },
        #"VC0_NCS"       => { TRANSMIT_DATA => "C2U DATA" },
        #"VC0_NCB"       => { TRANSMIT_DATA => "C2U DATA" },
        #"IDI_SNP"       => { RECEIVE_REQ  => "U2C REQ" },
        #"UPI_SNP"       => { RECEIVE_REQ  => "U2C REQ" },
        #"VC0_NDR"       => { RECEIVE_RSP   => "U2C RSP" , TRANSMIT_RSP  => "C2U RSP" },
        #"VC1_NDR"       => { RECEIVE_RSP   => "U2C RSP" , TRANSMIT_RSP  => "C2U RSP" },
        #"VC0_DRS"       => { TRANSMIT_DATA => "C2U DATA" ,RECEIVE_DATA  => "U2C DATA" },
        #"VC1_DRS"       => { TRANSMIT_DATA => "C2U DATA" ,RECEIVE_DATA  => "U2C DATA" },
    );

    my $fd;
    local %ufi_header_h = ();
    local $_ = "ufi_trk.log";
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    $ufi_trk_file_scbd->{filename} = $filename;
    local $scbd = $ufi_trk_file_scbd;
    $scbd->{tick_mul} = $tick_mul*1000.0;

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $ufi_header_h{$_} = $i++; }
            last;
        }
    }

    if(defined($ufi_header_h{CQID})) {
    } else {
        $scbd->{read_record_func} = \&ufi_trk_file_read_record;
        
        ufi_file_reader($fd,$scbd);
    }
    close $fd;
    
}

sub parse_axi_file($) {

    my $axi_file_l = shift;
    local $iommu_scbd_ptr = $ioc_iommu_file_scbd; 
    my $width_map_h = {
        VPU0 => 64,
        VPU1 => 64,
        VPU2 => 16,
        VPU3 => 16,
        IPU0 => 64,
        IPU1 => 64,
        IPU2 => 8,
        IPU3 => 8,
    };

    for(@$axi_file_l) {
        if(/(.pu).*axi2ufi_axi_master_port([0-3])(\.log)(\.gz)?$/ or /^(axi2ufi)_axi_master_port([0-3])(\.log)(\.gz)?$/) {
            my $vpu_ch = $2;
            my $port = ($1 eq "axi2ufi" ? "vpu" : $1);
            local $AXI_Unit = uc($port)."$vpu_ch";
            my $scbd = { };
            $scbd->{axi_port} = $port;
            if($lnl_vpu_btrs_ver eq "1") {
                $scbd->{BusWidthMask} = ($vpu_ch=~/^[123]/ ? 0xFFFFFFFF_FFFFFFF0 : 0xFFFFFFFF_FFFFFFC0);
                $scbd->{BusWidth} = ($vpu_ch=~/^[123]/ ? 16 : 64);
            } else {
                $scbd->{BusWidth} = $width_map_h->{$AXI_Unit};
                $scbd->{BusWidthMask} = ($scbd->{BusWidth}-1) ^ 0xFFFFFFFF_FFFFFFFF;
            }
            if(!$scbd->{BusWidth}) {
                die_ERROR("170 ERROR: Bad AXI width");
            }
            $scbd->{tick_mul} = 1000;
            
            if($port=~/vpu/) { $scbd->{BDF} = "0058"; }
            if($port=~/ipu/) { $scbd->{BDF} = "0028"; }

            my $filename = $_;
            next unless -f $filename;
            my $fd;
            local %axi_header_h = ();
            open_gz(\$fd,$filename,0) or return 0;

            if($debug>=1) {
                Reading_file_dump($filename);
            }

            $scbd->{filename} = $filename;
            $scbd->{file_src_ch} = "${AXI_Unit}_src_ch";

            while(<$fd>) {
                if(/^\s*\|\s*Time/i) {
                    s/\s*$//;
                    my @a = split /\s*\|\s*/;
                    my $i = 0;
                    for(@a) { s/:\d+$//; $axi_header_h{$_} = $i++; }
                    last;
                }
            }

            $scbd->{read_record_func} = \&axi_file_read_record;
            axi_file_reader($fd,$scbd);
            push @axi_file_scbd_l,$scbd;
            close $fd;
            return 1;

        } # if
    } # while

    return 0;
}

sub parse_axi_all_files() {

    for my $i (0..3) {
        parse_axi_file([
            "_uvm_test_top.env.vpu_btrs_axi_agent_axi2ufi_axi_master_port$i.log",
            "_uvm_test_top.env.vpu_btrs_axi_agent_axi2ufi_axi_master_port$i.log.gz",
            "axi2ufi_axi_master_port$i.log",
            "axi2ufi_axi_master_port$i.log.gz",
            "vpu_axi2ufi_axi_master_port$i.log",
            "vpu_axi2ufi_axi_master_port$i.log.gz",
            "vpu_trackers/vpu_axi2ufi_axi_master_port$i.log",
            "vpu_trackers/vpu_axi2ufi_axi_master_port$i.log.gz",
        ]);
        parse_axi_file([
            "ipu_axi2ufi_axi_master_port$i.log",
            "ipu_axi2ufi_axi_master_port$i.log.gz",
            "ipu_trackers/ipu_axi2ufi_axi_master_port$i.log",
            "ipu_trackers/ipu_axi2ufi_axi_master_port$i.log.gz",
        ]);
    };

}

sub parse_gtcxl_file() {

    opendir(D,"cxl_trackers");

    while($_ = readdir(D)) {
        if(/^(gt_cxl|cxl)(_master_agent_|)(.)(_d2h_requests_tracker)(\.log)(\.gz)?$/) {
            my $base_name = "cxl_trackers/$1$2$3";
            local $CXL_Unit = ($1 eq "cxl" ? "gt_cxl" : $1); $CXL_Unit = uc($CXL_Unit).$3;
            my $scbd = { };
            $scbd->{BusWidthMask} = ($3 ? 0xFFFFFFFF_FFFFFFF0 : 0xFFFFFFFF_FFFFFFC0);

            my $filename = "cxl_trackers/$_";
            next unless -f $filename;
            my $fd1,$fd2,$fd3,$fd4,$fd5,$fd6;
            my $fd_h;
            open_gz(\$fd1,$filename,0) or return 0;
            $scbd->{filename} = $filename;
            $fd_h->{"C2U REQ"}{fd} = $fd1;
            
            try {

                $filename = "${base_name}_d2h_responses_tracker.log";
                open_gz(\$fd2,$filename,0) or die("113 ERROR: Can not open $filename.");
                $fd_h->{"C2U RSP"}{fd} = $fd2;
                
                $filename = "${base_name}_d2h_data_tracker.log";
                open_gz(\$fd3,$filename,0) or die("114 ERROR: Can not open $filename.");
                $fd_h->{"C2U DATA"}{fd} = $fd3;
                
                $filename = "${base_name}_h2d_requests_tracker.log";
                open_gz(\$fd4,$filename,0) or die("115 ERROR: Can not open $filename.");
                $fd_h->{"U2C REQ"}{fd} = $fd4;
                
                $filename = "${base_name}_h2d_responses_tracker.log";
                open_gz(\$fd5,$filename,0) or die("116 ERROR: Can not open $filename.");
                $fd_h->{"U2C RSP"}{fd} = $fd5;
                
                $filename = "${base_name}_h2d_data_tracker.log";
                open_gz(\$fd6,$filename,0) or die("113 ERROR: Can not open $filename.");
                $fd_h->{"U2C DATA"}{fd} = $fd6;

            } catch {
                for my $k (keys %$fd_h) { close $fd_h->{$k}{fd} if defined($fd_h->{$k}{fd}); };
                undef $fd_h;
                die_ERROR($_);
            };
            
            # $skip_uri_chk = 1;

            if($debug>=1) {
                Reading_file_dump($filename);
            }

            $scbd->{file_src_ch} = "${CXL_Unit}_src_ch";

            for my $k (keys %$fd_h) {
                my $fd = $fd_h->{$k}{fd};
                while(<$fd>) {
                    if(/^\s*Time/i) {
                        s/\s*$//;
                        my @a = split /\s*\|\s*/;
                        my $i = 0;
                        for(@a) { s/:\d+$//; $fd_h->{$k}{header_h}{$_} = $i++; }
                        last;
                    }
                }
            }

            $scbd->{read_record_func}{"C2U REQ"}  = \&gtcxl_file_read_record_REQ;
            $scbd->{read_record_func}{"U2C REQ"}  = \&gtcxl_file_read_record_REQ;
            $scbd->{read_record_func}{"C2U RSP"}  = \&gtcxl_file_read_record_RSP;
            $scbd->{read_record_func}{"U2C RSP"}  = \&gtcxl_file_read_record_RSP;
            $scbd->{read_record_func}{"C2U DATA"} = \&gtcxl_file_read_record_DATA;
            $scbd->{read_record_func}{"U2C DATA"} = \&gtcxl_file_read_record_DATA;
            gtcxl_file_reader($fd_h,$scbd);
            for my $k (keys %$fd_h) { close $fd_h->{$k}{fd} if defined($fd_h->{$k}{fd}); };
            push @gtcxl_file_scbd_l,$scbd;

        } # if
    } # while

    close D;
}

sub parse_logbook_log($) {
    my ($fname) = @_;

    my $fd;
    open_gz(\$fd,$fname,0) or return undef;
    my $filename = (-e "$fname.gz" ? "$fname.gz" : $fname);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    local $scbd = { filename => $filename, };
    $scbd->{tick_mul} = $tick_mul*1000.0;
    $scbd->{read_record_func} = \&lnl_iommu_file_read_record;

    my $found_all = 0;
    {
        my $vtu_rec;
        my %page_type_h = ( 4096 => 12 , 2097152 => 21 , 1073741824 => 30 );

        while(<$fd>) {
            if(index($_,"STEPPING:")==0 && !defined($ACERUN_STEPPING)) {
                if(/STEPPING:\s*(\S+)/) {
                    $ACERUN_STEPPING = $1;
                }
                print "stepping4: $ACERUN_STEPPING\n" if $debug>=9;
            } elsif(index($_,"CLUSTER:")==0 && !defined($ACERUN_CLUSTER)) {
                if(/CLUSTER:\s*(\S+)/) {
                    $ACERUN_CLUSTER = $1;
                }
                print "cluster4: $ACERUN_CLUSTER\n" if $debug>=4;
            } elsif(index($_,"Using MODEL ")>=0) {
                if(/Using MODEL +(\S+)/) {
                    $LOGBOOK_MODEL = $1;
                    if($LOGBOOK_MODEL=~/icl-l0/ && !defined($ACERUN_STEPPING)) {
                        $ACERUN_STEPPING = "icl-l0";
                    }
                }
            } elsif(/^Source +file: +(\S+)/) {
                $emulation_obj_file = $1;
                $emulation_obj_file=~s/\.asm\b/.obj/g;
                $emulation_obj_file=~s/\.32.obj\b/.obj/g;
            } elsif(!defined($emulation_obj_file) and /^emurun: .*TESTNAME +(\S+)/) {
                $emulation_obj_file = $1;
                $emulation_obj_file=~s/\.asm\b/.obj/g;
                $emulation_obj_file=~s/\.32.obj\b/.obj/g;
                $emulation_obj_file.=".obj";
            } elsif(/vtd_agent_utils_c::vtd_legacy_domain_setup.* Start/) {
                if(defined($vtu_rec)) {
                    die_ERROR("179 ERROR: vtu_rec was not completed prerly");
                }
                $vtu_rec = { };
            } elsif(/vtd_agent_utils_c::vtd_legacy_domain_setup.* (Page Size|Guest Address|Host Address|B:D:F) *: *(\S+)/) {
                if(!defined($vtu_rec)) {
                    die_ERROR("181 ERROR: vtu_rec not created");
                }
                $vtu_rec->{$1} = $2;
            } elsif(/vtd_agent_utils_c::vtd_legacy_domain_setup.* Finished/) {
                if(!defined($vtu_rec)) {
                    die_ERROR("181 ERROR: vtu_rec not created");
                }
                for("Page Size","Guest Address","Host Address","B:D:F") {
                    if(!defined $vtu_rec->{$_}) {
                        die_ERROR("181 ERROR: vtu_rec not created");
                    }
                }
                my $page_shift = $page_type_h{$vtu_rec->{"Page Size"}};
                if(!$page_shift) {
                    die_ERROR("180 ERROR: vtu_rec has bad $1");
                }
                my $page_addr = big_hex($vtu_rec->{"Host Address"});
                my $page_mask = (0xffff_ffffffff-((1<<$page_shift)-1));
                if($vtu_rec->{"B:D:F"}=~/0x(\w+):0x(\w+):0x(\w+)/) {
                    $vtu_rec->{BDF} = sprintf("%04x",(hex($1)<<8)+(hex($2)<<3)+hex($3));
                } else {
                    die_ERROR("182 ERROR: vtu_rec has bad BDF=".$vtu_rec->{"B:D:F"});
                }
                $vtu_rec->{beg_virt_addr} = ((big_hex($vtu_rec->{"Guest Address"})>>$page_shift)<<$page_shift); 
                $vtu_rec->{beg_addr} = ((big_hex($vtu_rec->{"Host Address"})>>$page_shift)<<$page_shift); 
                $vtu_rec->{end_addr} = ((($vtu_rec->{beg_addr}>>$page_shift)+1)<<$page_shift)-1; 
                $scbd->{$vtu_rec->{BDF}}->{$vtu_rec->{beg_virt_addr}} = $vtu_rec; 
                $scbd->{is_auto_pass_through} = 1;
                if($debug>=3) {
                    printf "IOMMU PAGE BDF: $vtu_rec->{BDF} beg_addr=%012x end_addr=%012x beg_virt_addr=%012x\n",$vtu_rec->{beg_addr},$vtu_rec->{end_addr},$vtu_rec->{beg_virt_addr};
                }
                for("page_shift","Page Size","Guest Address","Host Address","B:D:F") {
                    delete $vtu_rec->{$_};
                }
                $vtu_rec = undef;
            }
        }
    }

    if($scbd->{is_auto_pass_through}) {
        # we have an iommu translation in this file. So create the iommu scbd
        $ioc_iommu_file_scbd = $scbd;
    }

    close $fd;
    return $scbd
}

sub parse_sm_file() {

    my $fd;
    local $_ = "sm.out";
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);
    my %dram_ranges_h;
    my %dram_ranges_h2;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $region_name;

    while(<$fd>) {
        if(/^[\|\+]/) {
            if(/^\|\s*(\S+)\s+has\s+\d+\s+REGIONS/) {
                $region_name = $1;
            }
        } else {
            $region_name = "";
        }
        
        if(/^\|\s*(\w+)[\s\(\)][^\|]*\|\s*0x*[0 ]*(\w+)\s*\|\s*0x*[0 ]*(\w+)\s*\|/) {
            my $name = $1;
            $dram_ranges_h{"$1"} = {BASE=>big_hex($2),LIMIT=>big_hex($3),MASK=>0xFFFFFFFF_FFFFFFFF,region=>$region_name,name=>$name};
            $dram_ranges_h2{$region_name}->{"$1"} = $dram_ranges_h{"$1"};
            if($name=~/pciess_ep_dma_seq/) {
                $skip_pep_svt_file=1;
                # If there is an PEP IP old dma_read or dma_write sequence, then skip the svt file becuase PEP range mappings are not known in this case.
            }
        }
    }
    close $fd;

    push @$ACTRR_DATA_range_l,$dram_ranges_h{ACTRR_DATA} if $dram_ranges_h{ACTRR_DATA};

    my $mmio_l = [ undef , undef];

    if($dram_ranges_h2{memmap}->{DRAM_LOW}) {
        my %mmio_low = (name=>"MMIO_LOW");
        $sm_TOLUD_addr = $mmio_low{BASE} = $dram_ranges_h2{memmap}->{DRAM_LOW}->{LIMIT}+1;
        $mmio_low{LIMIT} = 0xFFFFFFFF;
        $mmio_low{MASK} = 0xFFFFFFFF_FFFFFFFF;
        $mmio_l->[0] = \%mmio_low;
        #push @not_dram_ranges_l,\%mmio_low;
        push @IOP_not_dram_ranges_l,\%mmio_low;
    }

    if($dram_ranges_h2{memmap}->{REMAP_AREA} and $cpu_proj eq "lnl") {
        $global_remap_range->{BASE}  = $dram_ranges_h2{memmap}->{REMAP_AREA}->{BASE};
        $global_remap_range->{LIMIT} = $dram_ranges_h2{memmap}->{REMAP_AREA}->{LIMIT};
        $global_remap_range->{SIZE} = $global_remap_range->{LIMIT} - $global_remap_range->{BASE};
    }

    if($dram_ranges_h2{memmap}->{DRAM_HIGH}) {
        my %mmio_high = (name=>"MMIO_HIGH");
        $sm_TOUUD_addr = $mmio_high{BASE} = $dram_ranges_h2{memmap}->{DRAM_HIGH}->{LIMIT}+1;
        if($global_remap_range) { $sm_TOUUD_addr = $mmio_high{BASE} = $global_remap_range->{LIMIT}+1; }
        $mmio_high{LIMIT} = 0xFFFFFF_FFFFFFFF;
        $mmio_l->[1] = \%mmio_high;
        #push @not_dram_ranges_l,\%mmio_high;
        push @IOP_not_dram_ranges_l,\%mmio_high;
    }

    @mmio_ranges_l = grep { $_ } @$mmio_l;

    if($dram_ranges_h{DRAM_FOR_INBOUND_BAR2} && $dram_ranges_h{HOST_DRAM_FOR_INBOUND_BAR2}) {
        push @pep_host_direct_range_l,{host=>$dram_ranges_h{HOST_DRAM_FOR_INBOUND_BAR2},guest=>$dram_ranges_h{DRAM_FOR_INBOUND_BAR2}};
    }

    if($dram_ranges_h{IMR}) {
        # Just defined the whole range
        $all_imr_range = { BASE=>0,LIMIT=>0x7FFFFFFF_FFFFFFFF,MASK=>0xFFFFFFFF_FFFFFFFF,region=>"all_imr_range"};
        ##$all_imr_range = $dram_ranges_h{IMR};
        push @{$all_imr_range->{pass_func_l}},{func=>\&filter_IOP_IMR_RS0_trans};
    }

    for my $host_range_name (keys %dram_ranges_h) {
        if($host_range_name=~/^HOST_(\S+)/) {
            my $guest_range_name = $1;
            if(defined($dram_ranges_h{$guest_range_name})) {
                push @pep_host_dma_range_l,{host=>$dram_ranges_h{$host_range_name},guest=>$dram_ranges_h{$guest_range_name}};
                print "PEP convert range $host_range_name to $guest_range_name\n" if $debug>5;
            }
        }
    }

    my $mmio_ioc_range_l = [
        [
            $dram_ranges_h{MMIO_RAND_PRELOAD_LOW_0},
            $dram_ranges_h{MMIO_RAND_PRELOAD_LOW_1},
            $dram_ranges_h{MMIO_RAND_NON_PRELOAD_LOW_0},
            $dram_ranges_h{MMIO_RAND_NON_PRELOAD_LOW_1},
        ],
        [
            $dram_ranges_h{MMIO_RAND_PRELOAD_HIGH_0},
            $dram_ranges_h{MMIO_RAND_PRELOAD_HIGH_1},
            $dram_ranges_h{MMIO_RAND_NON_PRELOAD_HIGH_0},
            $dram_ranges_h{MMIO_RAND_NON_PRELOAD_HIGH_1},
        ],
    ];

    if($argv{skip_mmio_chk}) {
        push @not_dram_ranges_l,@$mmio_l;
    } else {
        # create the valid ranges for MMIO
        my $mmio_exclude_l = [ ];
        for my $i (0,1) {
            my @ranges_l = @{ $mmio_ioc_range_l->[$i] };
            @ranges_l = sort { $a->{BASE} <=> $b->{BASE} } @ranges_l;
            my $addr = $mmio_l->[$i]->{BASE};
            push @{$mmio_exclude_l} , {BASE=>$addr};
            for my $range (@ranges_l) {
                if($addr<$range->{BASE}) {
                    $mmio_exclude_l->[-1]->{LIMIT } = $range->{BASE} ;
                    $mmio_exclude_l->[-1]->{MASK  } = 0xFFFFFFFF_FFFFFFFF ;
                    $mmio_exclude_l->[-1]->{region} = $mmio_l->[$i]->{name} ;
                    $mmio_exclude_l->[-1]->{name  } = "BEFORE_".$range->{name} ;
                    $addr = $range->{LIMIT};
                    push @{$mmio_exclude_l} , {BASE=>$addr};
                }
            }
            if($addr<$mmio_l->[$i]->{LIMIT}) {
                $mmio_exclude_l->[-1]->{LIMIT } = $mmio_l->[$i]->{LIMIT};
                $mmio_exclude_l->[-1]->{MASK  } = 0xFFFFFFFF_FFFFFFFF ;
                #$mmio_exclude_l->[-1]->{region} = $mmio_l->[$i]->{range} ;
                $mmio_exclude_l->[-1]->{name  } = "END_".$mmio_l->[$i]->{name};
            } else {
                pop @{$mmio_exclude_l};
            }
        }

        push @not_dram_ranges_l,@$mmio_exclude_l;
    }

}

sub get_rec_tick($) {
    $_[0]->{tick}
}

sub get_rec_tick_go($) {
    my $rec_ptr = shift;
    if($rec_ptr->{cmd}=~/WCIL/) {
        return $rec_ptr->{tick_go_writepull} or $rec_ptr->{tick_go};
    } elsif(defined($rec_ptr->{tick_go})) {
        return $rec_ptr->{tick_go};
    } else {
        die_ERROR("191 ERROR: tick_go is not defined for merge");
    }
}

sub merge_two_sorted_lists($$$) {
    # This  function merge two sorted list of the prelaod transactions.
    my $get_func = shift;
    my @trans_l = @_;
    my @idx_l;
    my @tot_trans_l = ();
    for my $i (0..$#trans_l) { 
        push @idx_l,0; 
    }
    my $i=0;
    if($idx_l[0]<@{$trans_l[0]} && $idx_l[0]<@{$trans_l[1]}) {
        while(1) {
            if(&$get_func($trans_l[0]->[$idx_l[0]])<=&$get_func($trans_l[1]->[$idx_l[1]])) {
                $i = 0;
            } else { 
                $i = 1
            }
            push @tot_trans_l,$trans_l[$i]->[$idx_l[$i]];
            $idx_l[$i]+=1;
            if($idx_l[$i]>=@{$trans_l[$i]}) {
                $i = !$i;
                last;
            }
        }
    } elsif($idx_l[0]<@{$trans_l[0]}) {
        $i=0;
    } else {
        $i=1;
    }
    # put the remaining transactions pf one of the lists to @tot_trans_l
    for(;$idx_l[$i]<@{$trans_l[$i]};$idx_l[$i]+=1) { 
        push @tot_trans_l,$trans_l[$i]->[$idx_l[$i]];
    }
    return \@tot_trans_l;
}

sub merge_preload_scbd_lists(@) {
    # This  function merge two sorted list of the prelaod transactions.
    my @scbd_l = @_;
    $scbd_l[0]->{U}->{all} = merge_two_sorted_lists(\&get_rec_tick,$scbd_l[0]->{U}->{all},$scbd_l[1]->{U}->{all});
    $scbd_l[0]->{filename} .= " and " . $scbd_l[1]->{filename};
}

sub filter_preload_for_ccf_LLC($) {
    # if a addr was preloaded into LLC, then drop all the next preload transaction to the same address.
    my $scbd = shift;
    my $trans_l = [];
    my $llc_addr_h;
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        my $skip_rec;
        my $addr6 = ($rec_ptr->{address} >> 6);
        if($rec_ptr->{Unit}=~/^LLC/) {
            $llc_addr_h->{$addr6} = 1;
        } else {
            if($llc_addr_h->{$addr6}) {
                $skip_rec = 1;
            }
        }
        if(!$skip_rec) {
            push @$trans_l,$rec_ptr;
        }
    }
    $scbd->{U}->{all} = $trans_l;
    return $scbd;
}

sub parse_mcc_preloader_file($) {
    local %mcc_preloader_h = ();
    if($systeminit_file_exist and system("zgrep -q '/SOC_MC[01]_EN *:= *1' $systeminit_file")) { return undef; } # the mc is not working
    
    my $fd;
    local $_ = $_[0];
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $mcc_preloader_file_scbd = {};
    $mcc_preloader_file_scbd->{filename} = $filename;

    mcc_preloader_file_reader($fd,$mcc_preloader_file_scbd);

    if(@{$mcc_preloader_file_scbd->{U}->{all}}) {
        push @$mcc_preloader_file_scbd_l,$mcc_preloader_file_scbd;
    }
    close $fd;
    return $mcc_preloader_file_scbd;
}

sub parse_ccf_preloader_file($) {

    local $local_src_ch = get_ch_id("mcc_preloader");

    my $fd;
    local $_ = $_[0];
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $scbd = {};
    $scbd->{filename} = $filename;

    ccf_preloader_file_reader($fd,$scbd);
    close $fd;
    if(@{$scbd->{U}->{all}}) {
        $ccf_preloader_file_scbd = $scbd;
    }

    return $scbd;
}

sub parse_ccf_llc_file($) {

    local $local_src_ch = get_ch_id("mcc_preloader");
    local %mcc_preloader_h;

    my $fd;
    local $_ = $_[0];
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $llc_file_scbd = {};
    $llc_file_scbd->{filename} = $filename;

    ccf_llc_file_reader($fd,$llc_file_scbd);
    close $fd;
    return $llc_file_scbd;
}

sub parse_cxm_preloader_file($) {

    my $fd;
    local $_ = $_[0];
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $cxm_preloader_file_scbd = {};
    $cxm_preloader_file_scbd->{filename} = $filename;

    cxm_preloader_file_reader($fd,$cxm_preloader_file_scbd);

    if(@{$cxm_preloader_file_scbd->{U}->{all}}) {
        push @$mcc_preloader_file_scbd_l,$cxm_preloader_file_scbd;
    }

    return $cxm_preloader_file_scbd;
}

sub parse_astro_preloader_file($) {

    my $fd;
    local $_ = $_[0];
    open_gz(\$fd,$_,0) or return 0;
    my $filename = (-e "$_.gz" ? "$_.gz" : $_);

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $astro_preloader_file_scbd = {};
    $astro_preloader_file_scbd->{filename} = $filename;

    astro_preloader_file_reader($fd,$astro_preloader_file_scbd);

    if(@{$astro_preloader_file_scbd->{U}->{all}}) {
        push @$mcc_preloader_file_scbd_l,$astro_preloader_file_scbd;
    }

    return $astro_preloader_file_scbd;
}

sub emu_obj_file_reader($$$) {
    my $fd = shift;
    local $scbd = shift;
    my $all_tick = shift;
    my $addr,$last_addr;
    my $last_rec_ptr;
    my $count;
    local $local_src_ch = get_ch_id("mcc_preloader");

    $scbd->{read_record_func} = \&mcc_preloader_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    while(<$fd>) {
        chomp; if(substr($_,-1,1) eq "\r") { chop; }
        my $line = $_;
        if(m/\/origin\s+(\w+)/) {
            $addr = big_hex($1);
        } elsif(/^\w/) {
          my $align_addr = (($addr>>6)<<6);
          my @a = split / +/,lc($_);
          while( (1*@a) && length($a[(1*@a)-1])!=2 ) { pop @a; }
          while(@a) {
            my $next_addr = $addr+(1*@a);
            my @new_remain_a =();
            while($next_addr-$align_addr>64) {
                unshift @new_remain_a,(pop @a);
                $next_addr-=1;
            }
            my $data_str = join("",reverse(@a));
            my $rec_ptr;
            if(defined($last_addr) and $addr==$last_addr and ($addr>>6)==($last_rec_ptr->{address}>>6)) {
                $rec_ptr = $last_rec_ptr;
                $rec_ptr->{data} = $data_str . $rec_ptr->{data};
            } else {
                $rec_ptr = {
                    data=> ($data_str.("x" x (($addr&63)*2))),
                    direction=>"U",
                    cmd=>"MWr",
                    rec_type=>"mcc_preloader",
                    typ=>$typ,
                    count=>++$count,
                    tick=>$all_tick,
                    address => (($addr>>6)<<6),
                    src_ch_tc => $local_src_ch,
                };
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                $rec_ptr->{tick_end} = $rec_ptr->{tick};
                $rec_ptr->{tick_go} = $rec_ptr->{tick};
                $rec_ptr->{tick_mc} = $rec_ptr->{tick};
                push @{$scbd->{U}->{all}} , $rec_ptr;
            }

            $rec_ptr->{line} .= $line;

            @a = @new_remain_a;
            $addr = $next_addr;
            $align_addr = (($addr>>6)<<6);
            $last_addr = $next_addr;
            $last_rec_ptr = $rec_ptr;
          }
        }
    }
    for my $rec_ptr (@{$scbd->{U}->{all}}) {
        $rec_ptr->{line} .= "\n";
        if($debug>=7) {
            print " addr=".addr_str($rec_ptr->{address}).": data=".(" " x (128-length($rec_ptr->{data})))."$rec_ptr->{data} line=$rec_ptr->{line}";
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});
}

sub parse_emu_preloader_file($$) {
    my $fd;
    local ($_,$tick) = @_;
    return undef unless defined $_;

    my $filename = open_gz(\$fd,$_,0) or return 0;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my $mcc_preloader_file_scbd = {};

    $mcc_preloader_file_scbd->{filename} = $filename;

    emu_obj_file_reader($fd,$mcc_preloader_file_scbd,$tick);

    close $fd;   
   
  

    return $mcc_preloader_file_scbd;

}

sub parse_emu_preloader_both_files($$) {
    my $fd;
    local ($_,$all_tick) = @_;
    return unless defined $_;

    my $MiniBios_scbd = parse_emu_preloader_file("MiniBios.obj",1);
    
    my $test_obj_scbd = parse_emu_preloader_file($emulation_obj_file,$all_tick);

    if(!$test_obj_scbd) { return undef; }

    push @$mcc_preloader_file_scbd_l,$MiniBios_scbd;

    # Fill zero pad zero ll minibios overlaping transactions 
    my %MiniBios_addr_h;
    for my $rec_ptr (@{$MiniBios_scbd->{U}->{all}}) {
        $MiniBios_addr_h{$rec_ptr->{address}>>6} = $rec_ptr;
    }
    my $zero_preload_scbd = { filename=>"Mini_bios_zero_overide" };
    if($debug>=1) {
        print "Reading file $zero_preload_scbd->{filename}\n";
    }

    local $local_src_ch = get_ch_id("mcc_preloader");

    for my $rec_ptr (@{$test_obj_scbd->{U}->{all}}) {
        if(defined(my $MiniBios_rec = $MiniBios_addr_h{$rec_ptr->{address}>>6})) {
                my $data = $MiniBios_rec->{data};
                $data=~s/[0-9a-fA-F]/0/g;
                my $zero_rec_ptr = {
                    data=> $data,
                    direction=>"U",
                    cmd=>"MWr",
                    rec_type=>"mcc_preloader",
                    typ=>$typ,
                    count=>++$count,
                    tick=>$all_tick,
                    tick_beg=>$all_tick,
                    tick_end=>$all_tick,
                    tick_go=>$all_tick,
                    tick_mc=>$all_tick,
                    address => (($rec_ptr->{address}>>6)<<6),
                    src_ch_tc => $local_src_ch,
                    line=>"zero_line\n",
                };
                push @{$zero_preload_scbd->{U}->{all}} , $zero_rec_ptr;
                if($debug>=7) {
                    print " addr=".addr_str($zero_rec_ptr->{address}).": data=".(" " x (128-length($zero_rec_ptr->{data})))."$zero_rec_ptr->{data} line=$zero_rec_ptr->{line}";
                }
        }
    }

    assign_rec_parent_idx($test_obj_scbd->{U}->{all});
    assign_rec_parent_idx($zero_preload_scbd->{U}->{all});
    push @$mcc_preloader_file_scbd_l,$zero_preload_scbd,$test_obj_scbd;


    # Fill zero pad 

    if(@{$mcc_preloader_file_scbd->{U}->{all}}) {
        push @$mcc_preloader_file_scbd_l,$mcc_preloader_file_scbd;
    }

    return $mcc_preloader_file_scbd_l;

}

sub create_preload_from_cmi($$$) {
    my ($cmi_scbd,$read_addr_h,$write_addr_h) = @_;
    my $scbd = { filename=>$cmi_scbd->{filename}, };
    for my $dir ("D") {
        my ($i1) = (0);
        my $trans_l1 = ($cmi_scbd->{$dir}->{all} or []);
        for(my $i1=0; $i1<@$trans_l1 ; $i1+=1) {
            my $rec_ptr = $trans_l1->[$i1];
            my $is_read   = $rec_ptr->{cmd}=~/MRd/;
            my $addr6 = ($rec_ptr->{address}>>6);
            if($is_read && (!defined($read_addr_h->{$addr6}) or $rec_ptr->{tick_beg}<$read_addr_h->{$addr6}->{tick_beg})) {
                $addr_h->{$addr6}=$rec_ptr;
            }
        }
    }
    return $scbd;
}

sub parse_TCSS_PCIExBFM_files() {

    my $fd;

    opendir(D,".");

    while($_ = readdir(D)) {
        next unless /^TCSS_PCIEBFM(\d+)_trk.out(|.gz)$/;
        my $file_idx = 0+$1;
        if((-f "TCSS_PCIEBFM0_trk.out") or (-f "TCSS_PCIEBFM0_trk.out.gz")) { }
        else { $file_idx-=1; }
        if($file_idx<0 || $file_idx>10000) {
            die_ERROR("087 ERROR: Bad file index in file $_");
        }
        local $local_src_ch = "pcie_link$file_idx";
        my $filename;
        $filename = open_gz(\$fd,$_,0) or return 0;
 
        if($debug>=1) {
            print "Reading file $_\n";
        }
 
        my %file_scbd;
 
        $file_scbd{filename} = $filename;
 
        pcie_link_file_reader($fd,\%file_scbd);
        #psf_file_post_process(\%file_scbd);
 
        $pcie_link_file_scbd_l[$file_idx] = \%file_scbd;
    }
}

sub parse_PEG_PCIExBFM_files() {


    opendir(D,".");

    while($_ = readdir(D)) {
        my $fd;
        my $file_idx;
        if(/(SIPPCIE2_PEXP1_trk.out|PEG60_pkt_trk.log)(|\.gz)$/  && !/dbg/ && ($cpu_proj eq "rkl" || $cpu_proj eq "adl")) { 
            $file_idx=60; 
        } elsif(/(SIPPCIE2_PEXP2_trk.out|PEG62_pkt_trk.log)(|\.gz)$/  && !/dbg/ && ($cpu_proj eq "rkl" || $cpu_proj eq "adl")) { 
            $file_idx=62; 
        } elsif(/SIPPCIE_PEXP1_trk.out(|\.gz)$/  && !/dbg/ && $cpu_proj_step eq "rkl-p") { 
            $file_idx=10; 
        } elsif(/(SIPPCIE_PEXP_0_p1_trk.out|SIPPCIE1X8_PEXP_0_p1_trk.out)(|\.gz)$/  && !/dbg/ && $cpu_proj eq "adl") { 
            $file_idx=10; 
        } elsif(/SIPPCIE3_PEXP1_trk.out(|\.gz)$/  && !/dbg/ && $cpu_proj_step eq "rkl-p") { 
            $file_idx=11; 
        } elsif(/SIPPCIE_PEXP_0_p2_trk.out(|\.gz)$/  && !/dbg/ && $cpu_proj eq "adl") { 
            $file_idx=11; 
        } elsif(/^pcie_bfm_peg(\d+)_trk.out/) {
            $file_idx = 0+$1;
            if($file_idx<10 || $file_idx>60) {
                die_ERROR("088 ERROR: Bad file index in file $_");
            }
        } else {
            next;
        }
        local $local_src_ch = "peg_bfm$file_idx";
        open_gz(\$fd,$_,0) or return 0;
        my $filename = $_;
 
        if($debug>=1) {
            Reading_file_dump($_);
        }
 
        my %file_scbd;
 
        $file_scbd{filename} = $filename;
 
        pcie_link_file_reader($fd,\%file_scbd);
 
        $pcie_link_file_scbd_l[$file_idx] = \%file_scbd;
    }
}

sub parse_DMI_PCIExBFM_files() {


    opendir(D,".");

    while($_ = readdir(D)) {
        my $fd;
        next unless /^pcie_bfm_dmi_trk.out/ || /^DMI_pkt_trk.log/ 
            || ($cpu_proj eq "adl" && /^SIPPDMI_trk.out/ && !/dbg/);
        my $file_idx = 9;
        local $local_src_ch = "dmi_link";
        my $filename;
        $filename = open_gz(\$fd,$_,0) or return 0;
 
        if($debug>=1) {
            Reading_file_dump($_);
        }
 
        my %file_scbd;
 
        $file_scbd{filename} = $filename;
 
        if($filename=~/^DMI_pkt_trk.log/) {  # do iommu convertion for LNL project
            $iommu_scbd_ptr = $ioc_iommu_file_scbd; 
        }

        pcie_link_file_reader($fd,\%file_scbd);
        #psf_file_post_process(\%file_scbd);
 
        if($cpu_proj_step eq "rkl-a") {
            $opio_link_file_scbd = \%file_scbd;
        } else {
            $dmi_link_file_scbd = \%file_scbd;
        }
    }
}

sub mcc_prepare_data_and_be_string($$) {
    my $orig_data = shift;
    my $orig_be = shift;
    my $data = $orig_data;
    my $be = big_hex($orig_be);
    my $is_pcie_data;

    # Joins all data chucks
    my @data_l;
    my @data_be_out_l;
    if($is_pcie_data) {
    } elsif($data=~/[:_]/) { 
        # handle probably PSF data
        @data_l = split /\s*[:_]\s*/,$data;
    } elsif($data=~/ /) { 
        # handle probably PSF data
        @data_l = split /\s+/,$data;
    } else {
        @data_l = ($data);
    }
    my $d;
    while(defined($d = pop @data_l)) { 
        while($d=~s/([_\s]*)([0-9A-Fa-f][0-9A-Fa-f])$//) { 
            if($be&1) { push @data_be_out_l,$2; }
            else { push @data_be_out_l,"xx"; }
            $be >>= 1;
        }
        if(length($d)) { 
            die_ERROR("011 ERROR: parsing data $orig_data. Can not decode $d.");
        }
    }
    return join("",reverse(@data_be_out_l));
}


sub mcc_trans_file_read_record($) {
    local $_ = shift;
    my $sys_addr;
    if(/^\d+\s.*FULL-SYS_ADDR=(0x)?(\w+)/) {
        $sys_addr = big_hex($2);
    }

    my @a = split /\s*\|\s*/;

    my $trans_type = $a[4];

    my %rec = ( 
        id=>lc($a[6]), 
        uri=>$a[15] ,
        direction=>"D" , 
        cmd=>$a[4],
        rec_type=>"mcc",
        mcc_srcid=>$a[7],
        src_ch_tc=>$local_src_ch,
        tick=>$a[0],
    );

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});

    return undef unless ($trans_type=~/RTL-DATA/ || defined($sys_addr));

    $a[4] =~ s/\s+REQ$//; 
    $rec{address} = $sys_addr if(defined($sys_addr)); 

    if($trans_type=~/RTL-DATA/) {
        my $data = $a[14];
        my $be   = $a[13];
        $rec{data} = mcc_prepare_data_and_be_string($data,$be);
    }

    return \%rec;
}

sub mcc_trans_file_reader($$) {
    my $fd = shift;
    local $scbd = shift;
    my $last_cmd_line;
    my %rec_uri_h;
    my $count=0;
    my $mc_idx;
    local $local_src_ch = get_ch_id("mc");

    $scbd->{read_record_func} = \&mcc_trans_file_read_record;
    $scbd->{tick_mul}=$tick_mul*1000.0;

    if($scbd->{filename}=~/mcc_env(\d)/ && !$soc_mc_hash_disable) {
        $mc_idx = 1*$1;
    }

    while(<$fd>) {
        if(/FULL-SYS_ADDR|RTL-DATA/) { #FIXME:Currently checking only transaction from IOP ( DMI* URI)
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($_) or next;
            $rec_ptr->{line} = $line;

            my $is_wr_opcode = ($rec_ptr->{cmd} =~ /^([FP]-WR).*REQ/);

            if($is_wr_opcode) {
                if(defined($mc_idx)) {
                    $rec_ptr->{address} = cmi_hash_mc_addr_uncompress($rec_ptr->{address},$mc_idx);
                }
                my $idi_rec = get_trans_by_uri($idi_file_scbd->{UC_WR_cmd}->{$rec_ptr->{uri}},$rec_ptr,"tick");
                if(defined($idi_rec) and ($idi_rec->{address}>>6)==($rec_ptr->{address}>>6)) {
                    $idi_rec->{parent_tick_mc} = $rec_ptr->{tick};
                    check_trans_uri($idi_rec,$rec_ptr);
                }
            }

            if(!($rec_ptr->{mcc_srcid}=~/^(0x)?0*2$/)) {  # Make sure srcid==0x2 which is IOP source
                # Currently paring only transaciton from IOP, which is srcid==2
                next; 
            }

            if($is_wr_opcode) {
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                if($rec_ptr->{cmd} =~/REQ/) {
                    $count+=1;
                    push @{$scbd->{ $rec_ptr->{direction} }->{ $rec_ptr->{id} }} , $rec_ptr;
                    push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                    $last_cmd_line = $line;
                    $rec_uri_h{$rec_ptr->{uri}} = $rec_ptr;
                } elsif($rec_ptr->{cmd}=~/RTL-DATA/) {
                    my $req_rec = $rec_uri_h{$rec_ptr->{uri}} or die_ERROR("061 ERROR: Can not find REQ trans for URI=$rec_ptr->{uri} line=$line");
                    $req_rec->{data} =  $rec_ptr->{data};
                    $req_rec->{line} .= $line;
                }
            } elsif($rec_ptr->{cmd} =~ /^Cpl/) {
                my $other_direction = ($rec_ptr->{direction} eq "U" ? "D" : "U");
                my $tr = shift @{$scbd ->{$other_direction} -> { $rec_ptr->{id} }};
                if($tr) {
                    if($debug>=3) {
                        print "In   :id=$id: ".$tr->{line};
                        print " Out :id=$id: ".$_; 
                    }
                } else {
                    print_ERROR("012 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
            } elsif($rec_ptr->{cmd}=~/^(Msg|MWr)/) {
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
            } elsif($rec_ptr->{cmd}=~/^[FP]-WR.*RTL-DATA/ && length($rec_ptr->{direction})>=1) {
                # This code join all data from the next lines  
                my $fix_rec_ptr = $rec_uri_h{$rec_ptr->{uri}} or die_ERROR("089 ERROR: Can not find REQ trans for DATA trans: $line");
                my $fix_line = $fix_rec_ptr->{line};
                if($fix_rec_ptr->{data}) { $fix_rec_ptr->{data} .= " "; }
                $fix_rec_ptr->{data} .= $rec_ptr->{data};
                #print "is_join=$is_join last_cmd_line=$last_cmd_line fix_line=$fix_line\n"; #FIXME:
                print "";
            } else {
                undef $last_cmd_line;
            }
        }
    }
    assign_rec_parent_idx($scbd->{D}->{all});
    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub parse_mcc_trans_file($) {

    my $fd;
    local $_ = shift;
    my $filename;
    $filename = open_gz(\$fd,$_,0) or return undef;

    if($debug>=1) {
        Reading_file_dump($_);
    }

    my %psf_file_scbd;

    $psf_file_scbd{filename} = $filename;

    mcc_trans_file_reader($fd,\%psf_file_scbd);
    #psf_file_post_process(\%psf_file_scbd);

    return \%psf_file_scbd;
}

sub cmi_prepare_data_and_be_string($) {
    my $orig_data = shift;
    my $data = $orig_data;

    # Joins all data chucks
    my @data_l = ($data);
    my @data_be_out_l;
    my $d;
    while(defined($d = pop @data_l)) { 
        while($d=~s/([_\s]*)([0-9A-Fa-f][0-9A-Fa-f]|--)$//) { 
            push @data_be_out_l,($2 eq "--" ? "xx" : lc($2));
        }
        if(length($d)) { 
            die_ERROR("011 ERROR: parsing data $orig_data. Can not decode $d.");
        }
    }
    return join("",reverse(@data_be_out_l));
}

sub cmi_trans_file_read_record($$) {
    local $_ = shift;

    my @a = split /\s*\|\s*/;

    my $trans_type = $a[4];

    my %rec = ( 
        id=>$a[$cmi_header_h{TID}], 
        uri=>$a[$cmi_header_h{e2e_cmi_uri}] ,
        direction=>"D" , 
        cmd=>$a[$cmi_header_h{OPCODE}],
        cmi_type=>$a[$cmi_header_h{TYPE}],
        rec_type=>"mcc", # The cmi command is marked as mcc because it is used instead of the mcc_trans log
        cmi_srcid=>$a[$cmi_header_h{SrcID}],
        address=>big_hex($a[$cmi_header_h{SYS_ADDRESS}]),
        tick=>($tick_mul*$a[$cmi_header_h{TIME}]),
        src_ch_tc=>$local_src_ch,
    );

    if($a[$cmi_header_h{TYPE}]=~/^WR_DATA|^CPL_DAT/) {
        $tmp_data = $a[$cmi_header_h{DATA}]; $tmp_data =~ s/\s+$//;
        $rec{cmd} = $a[$cmi_header_h{TYPE}];
        $rec{data} = cmi_prepare_data_and_be_string($tmp_data);
    }
    if($a[$cmi_header_h{CPL_OFST}] ne "-") {
        $rec{CPL_num} = $a[$cmi_header_h{CPL_OFST}];
    }

    return \%rec;
}

sub cmi_trans_file_reader($$@) {
    my $fd = shift;
    my $scbd = shift;
    my %parms = @_;
    my $last_cmd_line;
    my %rec_uri_h;
    my $is_tick_mc = $parms{tick_mc};
    my $preload_read_addr_h = { };
    my $read_uri_h = { };
    my $count=0;
    local $tick_mul = 1.0;
    local $local_src_ch = get_ch_id("cmi");
    local $local_preload_src_ch = get_ch_id("mcc_preloader");
    if($emulation_obj_file) { $tick_mul=1000.0; }

    while(<$fd>) {
        if(/^TIME/) {
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { 
                s/[,:].*//; 
                s/\s+$//; 
                s/SYS_ADDRESS_MSB/SYS_ADDRESS/;
                $cmi_header_h{$_} = $i++; 
            }
            last;
        }
    }

    if($cpu_proj eq "adl" and $scbd->{filename}=~/iop/) {
        $cmi_header_h{e2e_cmi_uri} = $cmi_header_h{URI_PID_HDR} or die_ERROR("090 ERROR: Bug cmi header");
    } else {
        $cmi_header_h{e2e_cmi_uri} = $cmi_header_h{URI_LID_HDR} or die_ERROR("091 ERROR: Bug cmi header");
    }

    if($cmi_header_h{TIME}) { return undef; }

    $scbd->{read_record_func} = \&cmi_trans_file_read_record;

    while(<$fd>) {
        if(/^\d/) { #FIXME:Currently checking only transaction from IOP ( DMI* URI)
            my $line = $_;

            if(index($_," MEE_")>=0) { next } # Skip transactions from MEE

            my $rec_ptr = &{$scbd->{read_record_func}}($_) or next;

            if(!($rec_ptr->{cmi_srcid}=~/^(IOP|IDP)/ || $rec_ptr->{cmd} eq "WR_DATA" || $rec_ptr->{cmi_type}=~/^RD_CPL|^CPL_DAT/)) {  # Make sure srcid==0x2 which is IOP source
                # Currently paring only transaciton from IOP, which is srcid==2
                next; 
            }

            if($is_tick_mc) {
                my $is_wr_opcode = ($rec_ptr->{cmd} =~ /^MWr/);
                if($is_wr_opcode) {
                    my $idi_rec = get_trans_by_uri($idi_file_scbd->{UC_WR_cmd}->{$rec_ptr->{uri}},$rec_ptr,"tick");
                    if(defined($idi_rec) and ($idi_rec->{address}>>6)==($rec_ptr->{address}>>6)) {
                        $idi_rec->{parent_tick_mc} = $rec_ptr->{tick};
                        check_trans_uri($idi_rec,$rec_ptr);
                        #print "EYAL10: tick_mc=$idi_rec->{tick_mc} $rec_ptr->{line}";
                    }
                }
            }

            if($rec_ptr->{cmd} =~ /^MWr/) {
                $count+=1;
                $rec_ptr->{line} = $line;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                #push @{$scbd->{ $rec_ptr->{direction} }->{ 0 }} , $rec_ptr, $rec_ptr;
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $last_cmd_line = $line;
                $rec_uri_h{$rec_ptr->{uri}} = $rec_ptr;
            } elsif($rec_ptr->{cmd}=~/^WR_DATA/) {
                my $req_rec = $rec_uri_h{$rec_ptr->{uri}} or die_ERROR("062 ERROR: Can not find REQ trans for URI=$rec_ptr->{uri} line=$line");
                if($req_rec->{data}) { $req_rec->{data} = $rec_ptr->{data}." ".$req_rec->{data}; }
                else { $req_rec->{data} = $rec_ptr->{data}; }
                $req_rec->{tick_end} = $rec_ptr->{tick};
                print "In : ".$req_rec->{line} if $debug>=9;
            } elsif($create_cmi_preload) {
                if($rec_ptr->{cmd} =~ /^MRd/) {
                    $rec_ptr->{line} = $line if $debug>=3;
                    my $addr6 = ($rec_ptr->{address}>>6);
                    if(!exists($preload_read_addr_h->{$addr6})) {
                        $preload_read_addr_h->{$addr6}= { 
                            address=>($addr6<<6),
                            tick_beg=>($rec_ptr->{tick}) , 
                            uri=>($rec_ptr->{uri}),
                            cmd=>"MWr",
                            rec_type=>"mcc_preloader",
                            src_ch_tc=>$local_preload_src_ch,
                            cnt=>0,
                        };
                        $preload_read_addr_h->{$addr6}->{line} =$line if $debug>=3; 
                        $read_uri_h->{$rec_ptr->{uri}} = $preload_read_addr_h->{$addr6};
                    }
                } elsif($rec_ptr->{cmi_type} =~ /^RD_CPL/ && $read_uri_h->{$rec_ptr->{uri}}) {
                    $read_uri_h->{$rec_ptr->{uri}}->{CPL_num}  = $rec_ptr->{CPL_num};
                } elsif($rec_ptr->{cmd} =~ /^CPL_DAT/ && $read_uri_h->{$rec_ptr->{uri}}) {
                     my $first_rec = $read_uri_h->{$rec_ptr->{uri}};
                     if(++$first_rec->{cnt}==1) {
                        $first_rec->{data} = $rec_ptr->{data};
                     } elsif($first_rec->{cnt}==2) {
                        $first_rec->{data} = ( $first_rec->{CPL_num} ? $rec_ptr->{data}." ".$first_rec->{data} : $first_rec->{data}." ".$rec_ptr->{data});
                        delete $first_rec->{CPL_num};
                        delete $first_rec->{cnt};
                     }
                }
            }
        }
    }
    assign_rec_parent_idx($scbd->{D}->{all});
    $scbd->{preload_read_addr_h} = $preload_read_addr_h;
    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub cmi_hash_init() {
    my $hash_reg_val = ($cpu_proj eq "adl" ? $PCIE_CFG_SPACE->{0}->{0}->{"MEMORY_SLICE_HASH"} : $PCIE_CFG_SPACE->{0}->{0}->{"HASH_CONFIG"});
    return unless defined($hash_reg_val);
    my $HASH_CONFIG = Dump_BIOS_register("HASH_CONFIG",$hash_reg_val,undef,$debug>=2);
    if($HASH_CONFIG) {
        $soc_mc_hash_disable   = ($cpu_proj eq "adl" ? 0 : get_field($HASH_CONFIG,31,31));
        $soc_mc_hash_lsb       = get_field($HASH_CONFIG,26,24)+6;
        $soc_mc_hash_lsb_mask  = 0-(1<<$soc_mc_hash_lsb);
        $soc_mc_hash_mask      = get_field($HASH_CONFIG,19,6);
        printf("connect och mc hash dec=%1d hex=%1Xh lsb=%1d lsb_mask=%1X disable=%1d\n",$soc_mc_hash_mask,$soc_mc_hash_mask, $soc_mc_hash_lsb, $soc_mc_hash_lsb_mask,$soc_mc_hash_disable) if $debug>=1;
    }
}

sub cmi_hash_get_mc_idx($) {
    if($soc_mc_hash_disable) { return 0; }
    else {
        $xor = 0;
        my $val = ($_[0]>>6) & $soc_mc_hash_mask;
        for(my $i=0; $i<14; $i+=1) {
            $xor = $xor ^ ($val&1);
            $val = ($val>>1);
        }
        return $xor&1;
    }
}

sub hbo_hash_get_idx($) {
    if($soc_hbo_hash_disable) { return 0; }
    else {
        $xor = 0;
        my $val = ($_[0]>>$soc_hbo_hash_lsb) & $soc_hbo_hash_mask;
        for(my $i=0; $i<14; $i+=1) {
            $xor = $xor ^ ($val&1);
            $val = ($val>>1);
        }
        return $xor&1;
    }
}

sub lnl_hbo_hash_filter($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    my $idx = $parms{hash_idx};
    if(hbo_hash_get_idx($rec_ptr->{address})==$idx) {
        return 1;
    } else {
        return 0;
    }
}

sub cmi_hash_mc_addr_uncompress($$) {
    my ($addr,$idx)  = @_;
    if($soc_mc_hash_disable) { return $_[0]; }
    else {
        my $shift_idx;
        my $orig_addr;
        $shift_idx = $idx; $shift_idx<<=$soc_mc_hash_lsb;
        $orig_addr = (($addr & $soc_mc_hash_lsb_mask)<<1) | ($addr & ~$soc_mc_hash_lsb_mask) | $shift_idx;
        if(cmi_hash_get_mc_idx($orig_addr)== $idx) { return $orig_addr; }
        else { return $orig_addr ^ (1<<$soc_mc_hash_lsb); }
    }
}

sub parse_cmi_trans_file($@) {
    local %cmi_header_h;

    my $fd;
    my $filename = shift(@_);
    my @parms = @_;
    $filename = open_gz(\$fd,$filename,0) or return undef;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    my %psf_file_scbd;

    $psf_file_scbd{filename} = $filename;

    cmi_trans_file_reader($fd,\%psf_file_scbd,@parms);
    #psf_file_post_process(\%psf_file_scbd);

    print "Found $count transactions in ".$psf_file_scbd->{filename}."\n" if $debug>=1; 

    \%psf_file_scbd;
}

sub mufasa_trk_file_read_record($) {
    local $_ = shift;
    if(!m/\s*\d+/) { return undef; }
    if(!m/$cfi_filter/) { return undef; }
    chomp;
    my @a = split /\s*\|\s*/;
    my %rec = ( 
        uri=>uc($a[$idi_header_h{LID}]),
        uri_pid=>uc($a[$idi_header_h{PID}]),
        uid=>sprintf("%1x",$a[$idi_header_h{EntryId}]),
        cmd=>$a[$idi_header_h{Packet_Type}],
        rec_type=>"mfs",
        count=>++$idi_header_h{count},
        tick=>$a[$idi_header_h{Time}], # Simulatiopn time
        hbo_id=>$a[$idi_header_h{HBO_IDX}],
    );
    my $hbo_mem_data = $a[$idi_header_h{Data}];
    $hbo_mem_data =~ s/[\s-]*//;
    $rec{hbo_mem_data} = $hbo_mem_data if length $hbo_mem_data;
    my $hbo_address;
    if(defined($idi_header_h{Address}) and defined($hbo_address = $a[$idi_header_h{Address}]) && $hbo_address ne "-") {
        $rec{hbo_address} = big_hex($hbo_address);
    }

    $rec{tick} = scbd_tick_tunings($scbd,$rec{tick});
    $rec{tick_beg} = $rec{tick};
    $rec{tick_end} = $rec{tick};
    if($debug>=3) { 
        $rec{line} = $_."\n";
    }

    return \%rec;
}

sub mufasa_trans_file_reader($$@) {
    my $fd = shift;
    my $scbd = shift;
    my %parms = @_;
    my $last_cmd_line;
    my %cid_h;
    my $is_tick_mc = $parms{tick_mc};
    my $preload_read_addr_h = { };
    my $read_uri_h = { };
    my $count=0;
    local $tick_mul = 1.0;
    local $local_src_ch = get_ch_id("cmi");
    local $local_preload_src_ch = get_ch_id("mcc_preloader");
    if($emulation_obj_file) { $tick_mul=1000.0; }

    while(<$fd>) {
        if(/^\d/) { #FIXME:Currently checking only transaction from IOP ( DMI* URI)
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($_) or next;
            $req_rec->{line}=$line if $debug>=9;

            if($rec_ptr->{cmd} eq "MFS_IFC_WRITE_REQ") {
                    push @{$scbd->{ all }} , $rec_ptr;
                    print "In : ".$req_rec->{line} if $debug>=9;
            }
        }
    }
    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub parse_mufasa_trans_file($@) {
    local %idi_header_h;
    local $cfi_filter;
  
    my $fd;
    my $filename = shift(@_);
    my @parms = @_;
    $filename = open_gz(\$fd,$filename,0) or return undef;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    local %scbd;

    $scbd{filename} = $filename;
    $scbd->{tick_mul} = $tick_mul*1000.0;

    $scbd{read_record_func} = \&mufasa_trk_file_read_record;

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $idi_header_h{$_} = $i++; }
            last;
        }
    }

    mufasa_trans_file_reader($fd,\%scbd,@parms);

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
    close $fd;
    \%scbd;
}

sub hbo_find_by_uri() {
}

sub hbo_write_and_snoop_data($) {
    my $rec_ptr = shift;
    print "hbo_write_and_snoop_data: $rec_ptr->{line}" if($debug>=9);
    my $idi_wr = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}};
    my $gowritepull_rec;
    my @data_l;
    my @ret_l;
    my $data_chk_str;
    if(defined($idi_wr) and defined($idi_wr->{cmd})) {
        if($idi_wr->{uri} ne $rec_ptr->{uri} && $idi_wr->{uri_pid} ne $rec_ptr->{uri} && length($idi_wr->{data}) && !$skip_uri_chk) {
            # fixme: remove these when SOC_EMU_URI_STITCH uri bug in the second data chunk is fixed : !length($rec_req->{data})
            die_ERROR("142 ERROR: bad uri $rec_ptr->{uri}!=$idi_wr->{uri_pid} for  : $rec_ptr->{line}");
        }
        if(defined($idi_wr->{address}) and defined($rec_ptr->{address}) and defined($idi_wr->{data}) and length($idi_wr->{data})) {
            if(($idi_wr->{address}>>6) != ($rec_ptr->{address}>>6)) {
                die_ERROR("149 ERROR: bad previous snoop address=".addr_str($idi_wr->{address})." for trans : ".trans_str($rec_ptr));
            }
        }
        my $len = length($idi_wr->{data});
        if($len == 128) {
            push @data_l,$idi_wr->{data};
            #$data_chk_str = $idi_wr->{data};
        } elsif($len==256) {
            push @data_l,substr($idi_wr->{data},128,128);
            push @data_l,substr($idi_wr->{data},0,128);
            $data_chk_str = $data_l[0];
            merge_two_cl_data(\$data_chk_str,$data_l[1]);
        } elsif($len==0) {
        } else {
            die_ERROR("129 ERROR: Bad data size for $rec_ptr->{line}");
        }
        if(defined($data_chk_str) && length($rec_ptr->{data})) {
            if($data_chk_str ne $rec_ptr->{data}) {
                die_ERROR("133 ERROR: Bad data compare $data_chk_str!=$rec_ptr->{data} for $rec_ptr->{line}");
            }
        }
        for (my $data_i=0; $data_i<@data_l ;$data_i+=1) {
            my $new_rec = {
                address=>$idi_wr->{address},
                data=>$data_l[$data_i],
                tick_beg=>($rec_ptr->{tick_beg}) , 
                tick_end=>($rec_ptr->{tick_end}) , 
                uri=>($rec_ptr->{uri}),
                cmd=>"MWr",
                rec_type=>($rec_ptr->{rec_type}),
                src_ch_tc=>($rec_ptr->{src_ch_tc}),
             };
             if(!($data_i==0 && 2<=@data_l)) { 
                # only performs mufasa write checks when there is a real MWr and not for SNP
                $new_rec->{hbo_mem_data} = $rec_ptr->{hbo_mem_data}; $new_rec->{hbo_address} = $rec_ptr->{hbo_address}; 
                $new_rec->{tick_beg} += 1; # Ensure that the MWR: will always be after the SNP:
             } else { 
                # this write is not real and match a snoop (that was merged with the next MWr)
                $new_rec->{cmd} = "SNP_MWr"; 
                $new_rec->{address} &= 0xFFFFFFFF_FFFFFFC0; 
             }
             if($debug>=3) { 
                if($data_i==0 && 2<=@data_l) {
                    $new_rec->{line} = "SNP:";
                } else {
                    $new_rec->{line} = "MWR:";
                }
                $new_rec->{line} .= $rec_ptr->{line}; 
             }
             push @ret_l,$new_rec;
        }
        if($idi_wr->{cmd}=~/^(WIL)/) {
            # this it the end or the write command
            delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
        }
    }
    if(defined($gowritepull_rec=$cmp_expected_l->{$rec_ptr->{uri}})) {
        if($gowritepull_rec->{cmd}=~/GO.*WRITEPULL|IDI_GO|FAST_GO/) {
            # we got GO fot this transaction, so there will be no CMP
            if(!($gowritepull_rec->{cmd}=~/FAST_GO/)) {
                delete $cmp_expected_l->{$rec_ptr->{uri}};
            }
        } else {
            die_ERROR("141 ERROR: Unexpeded uri=$rec_ptr->{uri} trans: ".trans_str($rec_ptr));
        }
    }

    if(!defined($gowritepull_rec)) {
        my $mfs_exp_rec;
        my $new_rec = {
            #these fields will get thier vause when the cmp comes. if for CXM MemWr and CXM FMemWr commands which does not have uri
            #address=>$idi_wr->{address}, 
            #data=>$data_l[$data_i],
            tick_beg=>($rec_ptr->{tick_beg}) , 
            tick_end=>($rec_ptr->{tick_end}) , 
            uri=>($rec_ptr->{uri}),
            cmd=>"MWr",
            rec_type=>($rec_ptr->{rec_type}),
            src_ch_tc=>($rec_ptr->{src_ch_tc}),
            hbo_mem_data=>($rec_ptr->{hbo_mem_data}), hbo_address => $rec_ptr->{hbo_address}, 
         };
         if(defined(my $mfs_exp_rec=$mfs_expected_l->{$rec_ptr->{uri}})) {
             # there was a HBOIO complete for this $mfs_exp_rec transacion. so take the data from there. It can happen for WbMtoIES
             $new_rec->{address} = $mfs_exp_rec->{address};
             $new_rec->{data}    = $mfs_exp_rec->{data};
             delete $mfs_expected_l->{$rec_ptr->{uri}};
         } else {
             # the data and address should come from the Cmp on HBOIO that should come later. record this transaction on $cmp_expected_l->{$new_rec->{uri}} for it
             if(defined($cmp_expected_l->{$new_rec->{uri}})) {
                 die_ERROR("136 ERROR: there was previous trasaction with that uri=$rec_ptr->{uri} for trans: ".trans_str($rec_ptr));
             }
             if(($mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}})=~/^(SNPINV_RspIFwdMO)/) { 
                # This is order to hanble the FlOwn from IOC flow. The Flown and the EMemWr later comes with the same URI. hence we need to delete it. 
                # But the flown will have a IDI_GO , so we need to set the $cmp_expected_l
                delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                $cmp_expected_l->{$new_rec->{uri}} = $new_rec; 
             } elsif(($mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}})=~/^(BACKINV_RspIFwdMO)/) { 
                # This to support PRD that gets BACKINV_RspIFwdMO. it will have IDI_GO. So we need to set $cmp_expected_l
                delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                $cmp_expected_l->{$new_rec->{uri}} = $new_rec; 
             } elsif(($mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}})=~/^(BACKINV)/) { 
                # we got mufasa write for this snoop. so there is no need to wait for cmp (there won't be)
                delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}} 
             } else { 
                # remeber that we are waitin for cmp for this transactin.
                $cmp_expected_l->{$new_rec->{uri}} = $new_rec; 
                if($idi_wr->{snp_cmd}=~/SNPCURR/) { 
                    # since we have a SNPCURR, we know it was initaited by RDCURR that has no GO. So we delete the mfs uri here
                    delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}} 
                }
             }
             if(defined($idi_wr) and defined($idi_wr->{data})) { 
                # when IDI_GO comes it will be used snp_data ad the transaction data
                if($idi_wr->{snp_rsp}=~/Rsp.FwdMO/ and (
                        $idi_wr->{snp_cmd}=~/SNPCURR/ 
                        or ($idi_wr->{snp_cmd}=~/^(SNPINV|BACKINV)/ and $idi_wr->{req_cmd}=~/^(DRD|UcRdF|RdCode|InvItoE)/ and $idi_wr->{got_go}) # this snp got_go for the original req_cmd that initataed it
                        or ($idi_wr->{snp_cmd}=~/^(SNPINV)/ and $idi_wr->{req_cmd}=~/^(SetMonitor|RdOwnNoData)/)
                        or ($idi_wr->{snp_cmd}=~/^(SNPINV)/  and $idi_wr->{snp_rsp} eq "RspIFwdMO" and $rec_ptr->{uri}=~/^(HBO_SMA_000_|HBO_SMA_002_)/) # when there is a RdOwn that do a victim on snoop filter. It might do a SNPINV  snoop and get RspIFwdMO which will be written to mufasa with HBO_SMA_000_|HBO_SMA_002_
                        or ($idi_wr->{snp_cmd}=~/^(BACKINV)/ and $idi_wr->{snp_rsp} eq "RspIFwdMO" and $rec_ptr->{uri}=~/^(HBO_SMA_000_|HBO_SMA_002_)/) # when there is a RdOwn that do a victim on snoop filter. It might do a BACKINV snoop and get RspIFwdMO which will be written to mufasa with HBO_SMA_000_|HBO_SMA_002_
                )) { 
                    # in case of SNPCURR, I know it is related to RDCURR and there is no write data after it. so i end the snp write here
                    $new_rec->{data} = $idi_wr->{data}; 
                    $new_rec->{address} = $idi_wr->{address}; 
                    $new_rec->{cmd} = $idi_wr->{snp_cmd}; 
                    delete $cmp_expected_l->{$new_rec->{uri}}; # no cmp is expected to RDCURR. Only the data returns, but i don't monitor this read data`
                    if($idi_wr->{got_go}) { 
                        # since we got GO for this transaction the caused the snoop, this is the last station of it and I need to delete it from the list:
                        $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}} = undef; 
                    }
                } else {
                    $new_rec->{snp_data} = $idi_wr->{data}; 
                    $new_rec->{snp_address} = $idi_wr->{address}; 
                    $new_rec->{snp_uid} = $idi_wr->{uid}; 
                } 
                $idi_wr->{mfs_written}=1;
             }
         }
         if($debug>=3) { 
            $new_rec->{line} = "MWR:";
            $new_rec->{line} .= $rec_ptr->{line}; 
         }
         push @ret_l,$new_rec;
    }
    return @ret_l;
}

sub handle_mfs_rec($$) {
                    my ($mfs_rec,$scbd) = @_;
                    my $delete_uid_req;

                    if(defined($mfs_uri_h->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uri}}) and $mfs_uri_h->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uri}} ne "FlOwn") {
                        die_ERROR("120 ERROR: Non uniq URI=".$mfs_rec->{uri}." in mufasa file at line:".$mfs_rec->{line});
                    }

                    my $req_rec; # = $hboio_uid_l->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uid}};
                    #fixme: temporarily search both hbo until hbo_idx in mufasa files will be fixed (then there won't be need to $delete_uid_req too
                    for my $hbo_id (0,1) {
                        $req_rec = $hboio_uid_l->{$hbo_id}->{$mfs_rec->{uid}};
                        if(!defined($req_rec) or $req_rec->{uri} ne $mfs_rec->{uri} && $req_rec->{uri_pid} ne $mfs_rec->{uri}) {
                        } else { 
                            $mfs_rec->{hbo_id} = $hbo_id;
                            last; 
                        };
                    }
                    my $is_FlOwn;
                    if(defined($req_rec) and defined($req_rec->{snp_cmd})) {
                        # find the original transaction  and check whether it is flown
                        for my $ioc_ch ("IOC_0_L0(48)","IOC_1_L0(49)","IOC_0_L0_N1(4a)","IOC_0_L1_N1(4b)") {
                            my $ioc_trans_h = $hboio_cid_l->{$mfs_rec->{hbo_id}}->{$ioc_ch} or next;
                            for my $cid (keys %$ioc_trans_h) {
                                my $rec = $ioc_trans_h->{$cid};
                                if(defined($rec) and $rec->{cmd} eq "FlOwn" and $rec->{uri} eq $mfs_rec->{uri}) {
                                    $is_FlOwn =1; 
                                    last;
                                }
                            }
                            if($is_FlOwn) { last }
                        }
                    }
                    $mfs_uri_h->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uri}} = ($is_FlOwn ? "FlOwn" : 1);
                    if(!defined($req_rec) or $req_rec->{uri} ne $mfs_rec->{uri} && $req_rec->{uri_pid} ne $mfs_rec->{uri}) {
                        #die_ERROR("132 ERROR: Can not match transaction : $mfs_rec->{line}");
                    } else {
                        $mfs_rec->{src_ch_tc} = $req_rec->{src_ch_tc}; 
                        $mfs_rec->{src_ch_tc} = $req_rec->{src_ch_tc}; 
                        $delete_uid_req = 1; 
                        if($req_rec->{snp_cmd}=~/^(BACKINV|SNPINV)/) { 
                            if($mfs_uri_h->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uri}}) {
                                $mfs_uri_h->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uri}} = "$req_rec->{snp_cmd}_$req_rec->{snp_rsp}";
                            }
                        }
                    }

                    $mfs_rec->{cid} = $mfs_rec->{uid}; 
                    push @{$scbd->{"U2C DATA"}->{ all }} , hbo_write_and_snoop_data($mfs_rec);

                    if($delete_uid_req) {
                        $hboio_uid_l->{$mfs_rec->{hbo_id}}->{$mfs_rec->{uid}} = undef; # write is done. delete it from the list.
                    }

                    if(++$mfs_index>=1*@{$mufasa_file_scbd->{all}}) {
                        undef $mfs_index; 
                    }
}

sub cxm_cfi_trans_file_reader($$@) {
    my $fd = shift;
    my $scbd = shift;
    my %parms = @_;
    my $last_cmd_line;
    my %cid_h;
    my %sys_pref_idi_cid_h;
    local $hboio_cid_l;
    my $cmp_cid_l = {};
    local $cmp_expected_l = {}; local $mfs_expected_l = {};
    local $hboio_uid_l;
    my $is_tick_mc = $parms{tick_mc};
    my $preload_read_addr_h = { };
    my $read_uri_h = { };
    my $count=0;
    local $mfs_index = (defined ($mufasa_file_scbd) && 1*@{$mufasa_file_scbd->{all}} ? 0 : undef);
    local $mfs_uri_h = {};

    local $tick_mul = 1.0;
    local $local_src_ch = get_ch_id("cmi");
    local $local_preload_src_ch = get_ch_id("mcc_preloader");
    if($emulation_obj_file) { $tick_mul=1000.0; }

    $cmi_header_h{e2e_cmi_uri} = $cmi_header_h{URI_LID} or die_ERROR("090 ERROR: Bug cxm header");

    if($cmi_header_h{TIME}) { return undef; }

    while(<$fd>) {
        if(/^\d/) { #FIXME:Currently checking only transaction from IOP ( DMI* URI)
            my $line = $_;

            my $rec_ptr = &{$scbd->{read_record_func}}($_) or next;
            $rec_ptr->{line} = $line if $debug>=9;

            while(defined($mfs_index)) {
                my $mfs_rec=$mufasa_file_scbd->{all}->[$mfs_index];
                if($mfs_rec->{tick}<$rec_ptr->{tick}) {
                    handle_mfs_rec($mfs_rec,$scbd);
                } else {
                    last;
                }
            }


            if($is_tick_mc) {
                my $is_wr_opcode = ($rec_ptr->{cmd} =~ /^MWr/);
                if($is_wr_opcode) {
                    my $idi_rec = get_trans_by_uri($idi_file_scbd->{UC_WR_cmd}->{$rec_ptr->{uri}},$rec_ptr,"tick");
                    if(defined($idi_rec) and ($idi_rec->{address}>>6)==($rec_ptr->{address}>>6)) {
                        $idi_rec->{parent_tick_mc} = $rec_ptr->{tick};
                        check_trans_uri($idi_rec,$rec_ptr);
                        #print "EYAL10: tick_mc=$idi_rec->{tick_mc} $rec_ptr->{line}";
                    }
                }
            }

            if($rec_ptr->{Unit} eq "SOC_HBOMC0" || $rec_ptr->{Unit} eq "SOC_HBOMC1" and $rec_ptr->{cmd}=~/^MemWr/) {
                my $req_rec = $cid_h{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}};
                if($global_remap_range) {
                    if($rec_ptr->{address}>=$sm_TOLUD_addr and $rec_ptr->{address} < $sm_TOLUD_addr + $global_remap_range->{SIZE}) {
                        $rec_ptr->{address} = $rec_ptr->{address} - $sm_TOLUD_addr + $global_remap_range->{BASE};
                    }
                }
                if(!$req_rec) {
                    $count+=1;
                    $rec_ptr->{line} = $line;
                    $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                    #push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                    $last_cmd_line = $line;
                    $cid_h{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}} = $rec_ptr;
                } else {
                    if($req_rec->{data}) { $req_rec->{data} = $rec_ptr->{data}.$req_rec->{data}; }
                    else { $req_rec->{data} = $rec_ptr->{data}; }
                    $req_rec->{tick_end} = $rec_ptr->{tick};
                    $cid_h{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}} = undef;
                    if(!($req_rec->{uri}=~/^HBO_SMA_/)) { # Ignore HBO smartut transactions
                        push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , hbo_write_and_snoop_data($req_rec);
                    }
                    $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{cid}} = undef; # write is done. delete it from the list.
                }
                if($debug>=9) {
                    print "In   : ".$rec_ptr->{line};
                    print "  MWr: ".$req_rec->{line} ;
                }
            } elsif($rec_ptr->{direction} eq "C2U REQ" and ($rec_ptr->{prot} eq "IDI.C" or $rec_ptr->{prot} eq "UPI.C")) {
              if($rec_ptr->{cmd} eq "PrefetchToSysCache") {
                   $sys_pref_idi_cid_h{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} += 1;
              } else {
                # capture the incoming write to HBOIO in order to match it to mufasa writes
                $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} = $rec_ptr;
                if($line=~/abort=1/ and !($line=~/RdCurr/i)) {
                    die_ERROR("144 ERROR: not supporting transction with abort=1 line this: $line");
                }
                if(my $prev_rec = $cmp_cid_l->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} and defined($prev_rec) and !($prev_rec->{cmd}=~/RDCURR/)) {
                    die_ERROR("146 ERROR: this new trasaction arrived with cid=$rec_ptr->{cid} before the previous completed : $rec_ptr->{line}");
                } else {
                    $cmp_cid_l->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} = $rec_ptr;
                }
              }
            } elsif($rec_ptr->{direction} eq "U2C REQ" and ($rec_ptr->{prot} eq "IDI.C" || $rec_ptr->{prot} eq "UPI.C")) {
                my $old_snoop;
                if(defined($old_snoop = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}}) and $old_snoop->{snp_cnt}) {
                    if($old_snoop->{address} == $rec_ptr->{address}) {
                        # A second snoop happens when there is also monitor on this line. the monitor snoop is SnpLInv
                        $old_snoop->{snp_cnt}+=1;
                        if($rec_ptr->{cmd} ne "SnpLInv") {
                            $old_snoop->{uri}     = $rec_ptr->{uri};
                            $old_snoop->{snp_cmd} = $rec_ptr->{cmd};
                        }
                    } else {
                        die_ERROR("178 ERROR: Bad second snoop : ".trans_str($rec_ptr));
                    }
                } else {
                    $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = { uri=>$rec_ptr->{uri}, uri_pid=>$rec_ptr->{uri_pid}, uid=>$rec_ptr->{uid}, address=>$rec_ptr->{address}, snp_cmd=>$rec_ptr->{cmd} , snp_cnt=>1 };
                }
            } elsif($rec_ptr->{direction} eq "U2C RSP" && $rec_ptr->{cmd}=~/^Cmp/) {
                if(defined(my $req_rec = $cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}})) {
                    if(my $wr_rec = $cmp_expected_l->{$rec_ptr->{uri}}) {
                        $wr_rec->{address} = $req_rec->{address} unless defined($wr_rec->{address});
                        $wr_rec->{data} = $req_rec->{data} unless defined($wr_rec->{data});
                        if($req_rec->{cmd} =~ /MemWr32B|MemWrPtl32B/i) {
                            if(($wr_rec->{address}&0x3f)>=32) {
                                # in case MemWr32B and we have a second CL chuck add xx-es before
                                $wr_rec->{data} =~ s/^xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx//;
                                $wr_rec->{data}.= "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; 
                                $wr_rec->{address} &= 0xFFFFFFFF_FFFFFFC0; # since i see that this is a 64B write then make the address 64B alligned
                            }
                        }
                        delete $cmp_expected_l->{$rec_ptr->{uri}};
                        delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                    } elsif($req_rec->{cmd}=~/WbMtoI|WbMtoE|WbMtoS/i) {
                        # Since there was no mfs write to this this opcode so far, I expect to to be later so I mark it in mfs_expect_l
                        $mfs_expected_l->{$rec_ptr->{uri}} = $req_rec;
                    }
                    $cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                    if(defined($req_rec->{uid})) {
                        $hboio_uid_l->{$req_rec->{hbo_id}}->{$req_rec->{uid}} = undef; # the FlushOpt is done
                    }
                } else {
                    die_ERROR("135 ERROR: this new cmp arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                }
                my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}};
                if(defined($req_rec)) {
                    $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                } else {
                    die_ERROR("139 ERROR: this new cmp arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                }
            } elsif($rec_ptr->{direction} eq "U2C RSP" && $rec_ptr->{cmd}=~/^EXTCMP/) {
                if(my $wr_rec = $cmp_expected_l->{$rec_ptr->{uri}}) {
                    $wr_rec->{address} = $req_rec->{address} unless defined($wr_rec->{address});
                    $wr_rec->{data} = $req_rec->{data} unless defined($wr_rec->{data});
                    delete $cmp_expected_l->{$rec_ptr->{uri}};
                    delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                } else {
                    die_ERROR("151 ERROR: this new EXTCMP arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                }
                if(defined($wr_rec->{uid})) {
                    $hboio_uid_l->{$wr_rec->{hbo_id}}->{$wr_rec->{uid}} = undef; # the FlushOpt is done
                }
            } elsif($rec_ptr->{direction} eq "C2U RSP") {
                if($rec_ptr->{cmd} =~ /^(RspVFwdV|RspS|RspI|RspE|RspIHitI|RspSHitFSE|RspIHitFSE|RspIFwdMO|RspVHitV)$/) {
                    my $req_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                    if(defined($req_rec)) {
                        $req_rec->{snp_rsp} = $rec_ptr->{cmd};
                        if(length($req_rec->{data}) >= 128 or ($rec_ptr->{cmd} =~ /^(RspS|RspI|RspE|RspIHitI|RspSHitFSE|RspIHitFSE|RspVHitV)$/)) {
                            if((!$req_rec->{snp_cnt} or !--$req_rec->{snp_cnt}) and !($rec_ptr->{cmd}=~/RspIFwdMO/)) {
                                $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = undef; # the RspVFwdV never writes to memory. so free the uid now
                            }
                        }
                    }
                }
            } elsif($rec_ptr->{direction} eq "U2C RSP" and ($rec_ptr->{prot} eq "IDI.C" or $rec_ptr->{prot} eq "UPI.C")) {
                if($rec_ptr->{cmd} =~/^(GO_WRITEPULL|WRITEPULL|FAST_GO_WRITEPULL|FAST_GO)/) {
                    # capture the incoming write to HBOIO in order to match it to mufasa writes
                    my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}};
                    if(!defined($req_rec)) {
                        die_ERROR("128 ERROR: Can not match transaction : $rec_ptr->{line}");
                    }
                    $req_rec->{uid} = $rec_ptr->{uid};
                    $req_rec->{uri} = $rec_ptr->{uri};
                    if($rec_ptr->{cmd} =~/^(GO_WRITEPULL|FAST_GO)/ and !($req_rec->{cmd}=~/CleanEvict/)) {
                        if(!defined($cmp_expected_l->{$rec_ptr->{uri}})) {
                            $cmp_expected_l->{$rec_ptr->{uri}} = $rec_ptr; # this will be undef when the data will be sent to MC or MUFASA
                        } elsif(($cmp_expected_l->{$rec_ptr->{uri}}->{snp_address}>>6)==($rec_ptr->{address}>>6) and ($cmp_expected_l->{$rec_ptr->{uri}}->{snp_uid}) eq ($rec_ptr->{uid})) {
                            # this CLWb or CLFlush_Opt already got snoop with data before. so it already got expected_cmp
                        } else {
                            die_ERROR("140 ERROR: unexpected URI=$rec_ptr{uri} in array for trans: $rec_ptr->{line}");
                        }
                        if($rec_ptr->{cmd} =~/^(FAST_GO)/ and ($req_rec->{cmd}=~/CLWb|CLFlush_Opt/i)) {
                            $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                        }
                    }

                    my $uid_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                    if(!defined($uid_rec)) {
                        $uid_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = { uri=>$rec_ptr->{uri}, uri_pid=>$rec_ptr->{uri_pid}, uid=>$rec_ptr->{uid}, };
                    } else {
                        $uid_rec->{uri} = $rec_ptr->{uri};
                    }
                    $uid_rec->{address} = ($req_rec->{address} & 0xFFFFFFFF_FFFFFFFF);
                    $uid_rec->{cmd} = $req_rec->{cmd};
                    if(($rec_ptr->{cmd}=~/GO_WRITEPULL_DROP/) # this might come for CleanEvict
                        or ($rec_ptr->{cmd} eq "FAST_GO" and $uid_rec->{snp_rsp} eq "RspI" and $req_rec->{cmd}=~/CLWb|CLFlush_Opt/i) # CLWb|CLFlush_Opt which does not write data
                        ) { $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = undef; }
                } elsif($rec_ptr->{cmd} =~/^(IDI_GO)/) {
                  if($sys_pref_idi_cid_h{$rec_ptr->{dst}}->{$rec_ptr->{cid}}) {
                      $sys_pref_idi_cid_h{$rec_ptr->{dst}}->{$rec_ptr->{cid}} -= 1;
                      if($mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}}) {
                          delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                          delete $cmp_expected_l->{$rec_ptr->{uri}};
                      }
                  } else {
                    # a read command was finished hence free its uid.
                    my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}};
                    if(!defined($req_rec)) {
                        die_ERROR("131 ERROR: Can not match transaction : $rec_ptr->{line}");
                    } 
                    my $snp_rec;
                    if($snp_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}}) { 
                        $snp_rec->{req_cmd} = $req_rec->{cmd}; 
                    } 
                    if($snp_rec and !($req_rec->{cmd}=~/Wr|WIL|SetMonitor|RdOwnNoData/)) {
                        # don't indef and write transaction, because we might need to get the data written to memory first.
                        if(    $snp_rec->{snp_rsp} eq "RspIFwdMO" and !$snp_rec->{mfs_written}         and $rec_ptr->{go_state} ne "M" # we are still expecting this snoop FwdMO to be written to Mofasa. Hence I don't delete it.
                            or $snp_rec->{req_cmd}=~/^(DRD|UcRdF)/ and $snp_rec->{snp_rsp}=~/^(RspIWb|RspSWb)/ and $rec_ptr->{go_state} ne "M" # I this case we still expect data to be written to MFS or MC 
                        ) {
                            $snp_rec->{got_go} = $rec_ptr->{cmd}; # signal that we got go to it will be deleteed when the Mufasa write comes.
                        } else {
                            $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = undef;
                        }
                    }
                    if(!defined(my $snooped_rec = $cmp_expected_l->{$rec_ptr->{uri}}) && !($req_rec->{cmd}=~/SpecFlOwn|E:1e|FlOwn|DRD|UcRdF|CLFlush|SetMonitor|RdOwnNoData$/)) {
                        $cmp_expected_l->{$rec_ptr->{uri}} = $req_rec; # this will be undef when the data will be sent to MC or MUFASA
                    } else {
                        if($req_rec->{cmd}=~/^(SpecFlOwn|E:1e|FlOwn|DRD|UcRdF)/ and defined($snooped_rec->{snp_data})) {
                            $snooped_rec->{data} = $snooped_rec->{snp_data};
                            $snooped_rec->{address} = $req_rec->{address};
                            if(($snooped_rec->{address}>>6) != ($snooped_rec->{snp_address}>>6)) {
                                die_ERROR("156 ERROR: this bad snoop address for : ".trans_str($req_rec));
                            } $snooped_rec->{address} &= 0xFFFFFFFF_FFFFFFC0;
                            delete $snooped_rec->{snp_data};
                            delete $snooped_rec->{snp_address};
                        }
                        # the mc or mofasa write was sent before so this idi_go is the end of the trasaction. no cmp is expected
                        delete $cmp_expected_l->{$rec_ptr->{uri}};
                    }
                    if(defined($cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}})) {
                        $cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                    } else {
                        die_ERROR("147 ERROR: this new IDI_GO arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                    }
                  }
                } elsif($rec_ptr->{cmd} =~/^(M_CmpO)/) {
                    # a read command was finished hence free its uid.
                    my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}};
                    my $uid;
                    if(!defined($req_rec)) {
                        die_ERROR("131 ERROR: Can not match transaction : $rec_ptr->{line}");
                    }
                    my @uid_l = keys %{$hboio_uid_l->{$rec_ptr->{hbo_id}}};
                    for my $uid (@uid_l) {
                        if($hboio_uid_l->{$rec_ptr->{hbo_id}}->{$uid}->{uri_pid} eq $rec_ptr->{uri}) {
                            $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$uid} = undef;
                        }
                    }
                    if(defined($cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}})) {
                        $cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                    } else {
                        die_ERROR("147 ERROR: this new IDI_GO arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                    }
                    delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                } elsif($rec_ptr->{cmd} =~/^(E_CmpO|SI_CmpO)/) {
                    # a read command was finished hence free its uid.
                    my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{dst}}->{$rec_ptr->{cid}};
                    my $uid;
                    if(!defined($req_rec)) {
                        die_ERROR("161 ERROR: Can not match transaction : $rec_ptr->{line}");
                    }
                    my @uid_l = keys %{$hboio_uid_l->{$rec_ptr->{hbo_id}}};
                    for my $uid (@uid_l) { 
                        # we found that there was a snoop on this transaction, so we update the data for it here
                        my $snp_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$uid};
                        if($snp_rec->{uri_pid} eq $rec_ptr->{uri}) {
                            if($snp_rec->{snp_rsp} eq "RspIFwdMO" and $snp_rec->{snp_cmd}=~/^(SNPINV)/) {
                                # if the snoop got FwdMO then it should got to mufasa and get freed there.
                                $snp_rec->{got_go} = $rec_ptr->{cmd}; 
                                $snp_rec->{req_cmd} = $req_rec->{cmd};
                            } else {
                                # if the snoop did not got FwdMO then we end it here because it will not get to mufasa or memory
                                $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$uid} = undef;
                            }
                        }
                    }
                    if(defined($cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}})) {
                        $cmp_cid_l->{$rec_ptr->{dst}}->{$rec_ptr->{cid}} = undef;
                    } else {
                        die_ERROR("162 ERROR: this new IDI_GO arrived with cid=$rec_ptr->{cid} but there was no request before : $rec_ptr->{line}");
                    }
                    if(defined($cmp_expected_l->{$rec_ptr->{uri}})) {
                        delete $cmp_expected_l->{$rec_ptr->{uri}};
                    }
                    delete $mfs_uri_h->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uri}};
                }
            } elsif($rec_ptr->{cmd} =~/^(RspCurData)/ and $rec_ptr->{direction} eq "C2U DATA" and !$rec_ptr->{eop}) {
                # I capture the RspCurData and end the snoop flow. No need for the data. parse only the first RspCurData (eop=0)
                my $req_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                if(defined($req_rec)) {
                    if(!$req_rec->{snp_cnt} or !--$req_rec->{snp_cnt}) {
                        $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = undef; # the RspVFwdV never writes to memory. so free the uid now
                    }
                }
            } elsif($rec_ptr->{cmd} =~/^(DATA_0|DATA_1|RspSWb|RspIWb)/ and $rec_ptr->{direction} eq "C2U DATA") {
                # capture the incoming write to HBOIO in order to match it to mufasa writes
                my $req_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}};
                if(!defined($req_rec)) {
                    $req_rec = $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = { uri=>$rec_ptr->{uri}, uri_pid=>$rec_ptr->{uri_pid}, uid=>$rec_ptr->{uid}, };
                }
                if($req_rec->{data}) { 
                    $req_rec->{data} = $rec_ptr->{data}.$req_rec->{data}; 
                    if(($req_rec->{cmd}=~/CleanEvict/) or ($req_rec->{snp_rsp} eq "RspVFwdV") or ($req_rec->{snp_rsp} eq "RspCurData")
                        or ($req_rec->{cmd}=~/DirtyEvict|^WIL/ and $req_rec->{bogus})
                    ) {
                        $hboio_uid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{uid}} = undef; # This is the End of CleanEvict,RspVFwdV,RspCurData - data will not be sent to MC for it.
                        delete $cmp_expected_l->{$req_rec->{uri}};
                    }
                    if($rec_ptr->{cmd} =~/^(RspSWb|RspIWb)/ and $req_rec->{snp_cmd} and !$req_rec->{snp_rsp}) {
                        $req_rec->{snp_rsp} = $rec_ptr->{cmd}; # set the snp_rsp for RspSWb,RspIWb
                    }
                } else { 
                    $req_rec->{data} = $rec_ptr->{data}; 
                    if($rec_ptr->{bogus}) { $req_rec->{bogus}=1; }
                }
                if($debug>=3) {
                    print "In   :cid=$req_rec->{cid}:uid=$req_rec->{uid}: ".$req_rec->{line};
                    print " Out :cid=$rec_ptr->{cid}:uid=$rec_ptr->{uid}: ".$line; 
                }
            } elsif($rec_ptr->{cmd} =~/^(MemWr|FMemWr|EMemWr|WbMtoI|WbMtoE|WbMtoS|WbEtoI)/ and $rec_ptr->{direction} eq "C2U DATA" and ($rec_ptr->{prot} eq "CXM" || $rec_ptr->{prot} eq "UPI.C")) {
                # capture the incoming cxm write to HBOIO
                if($line=~/abort=1/) {
                    die_ERROR("144 ERROR: not supporting transction with abort=1 line this: $line");
                }
                my $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}};
                if(!defined($req_rec) or $req_rec->{cmd}=~/SpecFlOwn|E:1e|FlOwn|DRD|UcRdF|RDCURR/) {
                    $req_rec = $hboio_cid_l->{$rec_ptr->{hbo_id}}->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} = $rec_ptr;
                    if(my $prev_rec = $cmp_cid_l->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} and defined($prev_rec) and !($prev_rec->{cmd}=~/RDCURR/)) {
                        die_ERROR("137 ERROR: this new trasaction arrived with cid=$rec_ptr->{cid} before the previous completed : $rec_ptr->{line}");
                    } else {
                        $cmp_cid_l->{$rec_ptr->{rsp}}->{$rec_ptr->{cid}} = $rec_ptr;
                    }
                } else {
                    if($req_rec->{cmd}=~/^F?MemWrCompress/) {
                        $rec_ptr->{data} = "0000000000000000000000000000000000000000000000000000000000000000";
                    }
                    $req_rec->{data} = $rec_ptr->{data}.$req_rec->{data};
                }
                if(!defined($req_rec)) {
                    die_ERROR("138 ERROR: Can not match transaction : $rec_ptr->{line}");
                }
                if($debug>=3) {
                    print "In   :cid=$req_rec->{cid}:uid=$req_rec->{uid}: ".$req_rec->{line};
                    print " Out :cid=$rec_ptr->{cid}:uid=$rec_ptr->{uid}: ".$line; 
                }
            } elsif($create_cmi_preload) {
                if($rec_ptr->{cmd} =~ /^MRd/) {
                    $rec_ptr->{line} = $line if $debug>=3;
                    my $addr6 = ($rec_ptr->{address}>>6);
                    if(!exists($preload_read_addr_h->{$addr6})) {
                        $preload_read_addr_h->{$addr6}= { 
                            address=>($addr6<<6),
                            tick_beg=>($rec_ptr->{tick}) , 
                            uri=>($rec_ptr->{uri}),
                            cmd=>"MWr",
                            rec_type=>"mcc_preloader",
                            src_ch_tc=>$local_preload_src_ch,
                            cnt=>0,
                        };
                        $preload_read_addr_h->{$addr6}->{line} =$line if $debug>=3; 
                        $read_uri_h->{$rec_ptr->{uri}} = $preload_read_addr_h->{$addr6};
                    }
                } elsif($rec_ptr->{cmi_type} =~ /^RD_CPL/ && $read_uri_h->{$rec_ptr->{uri}}) {
                    $read_uri_h->{$rec_ptr->{uri}}->{CPL_num}  = $rec_ptr->{CPL_num};
                } elsif($rec_ptr->{cmd} =~ /^CPL_DAT/ && $read_uri_h->{$rec_ptr->{uri}}) {
                     my $first_rec = $read_uri_h->{$rec_ptr->{uri}};
                     if(++$first_rec->{cnt}==1) {
                        $first_rec->{data} = $rec_ptr->{data};
                     } elsif($first_rec->{cnt}==2) {
                        $first_rec->{data} = ( $first_rec->{CPL_num} ? $rec_ptr->{data}." ".$first_rec->{data} : $first_rec->{data}." ".$rec_ptr->{data});
                        delete $first_rec->{CPL_num};
                        delete $first_rec->{cnt};
                     }
                }
            }
        }
    }

    while(defined($mfs_index)) {
        my $mfs_rec=$mufasa_file_scbd->{all}->[$mfs_index];
        handle_mfs_rec($mfs_rec,$scbd);
    }

    for my $hboid (keys %$mfs_uri_h) {
        for my $uri (keys %{$mfs_uri_h->{$hboid}}) {
            if(defined(my $rec_ptr=$mfs_uri_h->{$hboid}->{$uri})) {
                #fixme: need to acivate and clean this check
                #print_ERROR("184 ERROR: transction  with uri=$uri was not completed in mfs_uri_h. trans: $rec_ptr->{line}\n");
                #$exit_code = 1;
            }
        }
    }

    for my $uri (keys %$cmp_expected_l) {
        if(defined(my $rec_ptr=$cmp_expected_l->{$uri})) {
            #fixme: need to acivate and clean this check
            #print_ERROR("143 ERROR: transction  with uri=$uri was not completed. trans: $rec_ptr->{line}\n");
            #$exit_code = 1;
        }
    }

    $scbd->{D} = $scbd->{"U2C DATA"}; $scbd->{"U2C DATA"} = undef;

    for my $rec_ptr (@{$scbd->{D}->{all}}) {
        $rec_ptr->{idx} = $parent_idx_count++;
        if(exists($rec_ptr->{hbo_mem_data})) {
            if(length($rec_ptr->{hbo_mem_data}) and defined($rec_ptr->{data}) and length($rec_ptr->{data})) {
                if(!cl_data_cmp($rec_ptr->{data},$rec_ptr->{hbo_mem_data})) {
                    die_ERROR("157 ERROR: data differs from mfs data for : ".trans_str($rec_ptr));
                } 
                if(defined($rec_ptr->{hbo_address}) and $rec_ptr->{hbo_address} != $rec_ptr->{address}) { 
                    die_ERROR("177 ERROR: address differs from mfs address=".addr_str($rec_ptr->{hbo_address})." for : ".trans_str($rec_ptr)); 
                }
            }
            delete $rec_ptr->{hbo_mem_data};
        } 
        delete $rec_ptr->{snp_cmd};
    }

    assign_rec_parent_idx($scbd->{D}->{all});
    $scbd->{preload_read_addr_h} = $preload_read_addr_h;
    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
}

sub parse_cxm_cfi_trans_file($@) {
    local %cmi_header_h;
    local %idi_header_h;
    local $cfi_filter;
    local %cfi_trk_typ_conv;
  
    if($lnl_use_mc_vs_hbomc) {
        # this was the transactions on the m/SOC_MC_IBECC|SOC_MEM[01]|SOC_CCEIO/ interface
        %cfi_trk_typ_conv = (
            "VC0_DRS"       => { TRANSMIT_DATA => "C2U DATA" },
            "VC0_RwD"       => { TRANSMIT_DATA => "C2U DATA" ,RECEIVE_DATA  => "U2C DATA" },
            "VC0_REQ"       => { RECEIVE_REQ  => "U2C REQ" },
            "VC0_NDR"       => { TRANSMIT_RSP  => "C2U RSP" },
        );
        $cfi_filter = "SOC_MC_IBECC|SOC_MEM[01]|SOC_CCEIO";
    } else {
        # this is the transactions on the m/SOC_HBOMC/ interface
        %cfi_trk_typ_conv = (
            "VC0_RwD"       => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
            "VC1_RwD"       => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
            "VC0_WUO"       => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
            "VC0_REQ"       => { TRANSMIT_REQ  => "U2C REQ" ,RECEIVE_REQ  => "C2U REQ" },
            "VC1_REQ"       => { TRANSMIT_REQ  => "U2C REQ" ,RECEIVE_REQ  => "C2U REQ" },
            "VC1_NDR"       => { TRANSMIT_RSP   => "U2C RSP" , RECEIVE_RSP  => "C2U RSP" },

            "IDI_REQ"       => { RECEIVE_REQ  => "C2U REQ" },
            "UPI_REQ"       => { RECEIVE_REQ  => "C2U REQ" },
            "UPI_SNP"       => { TRANSMIT_REQ  => "U2C REQ" },
            "IDI_SNP"       => { TRANSMIT_REQ  => "U2C REQ" },
            "VC0_NDR"       => { TRANSMIT_RSP   => "U2C RSP" , RECEIVE_RSP  => "C2U RSP" },
            "VC0_DRS"       => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
            "VC1_DRS"       => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
            "UPI_WB"        => { RECEIVE_DATA => "C2U DATA" ,TRANSMIT_DATA  => "U2C DATA" },
        );
        $cfi_filter = "SOC_HBOMC|SOC_HBOIO";
    }

    my $fd;
    my $filename = shift(@_);
    my @parms = @_;
    $filename = open_gz(\$fd,$filename,0) or return undef;

    if($debug>=1) {
        Reading_file_dump($filename);
    }

    local %scbd;

    $scbd{filename} = $filename;
    $scbd->{tick_mul} = $tick_mul*1000.0;

    $scbd{read_record_func} = \&mc_cxm_cfi_trk_file_read_record_CFI45;

    while(<$fd>) {
        if(/^\s*Time/i) {
            s/\s*$//;
            my @a = split /\s*\|\s*/;
            my $i = 0;
            for(@a) { s/:\d+$//; $idi_header_h{$_} = $i++; }
            last;
        }
    }

    local %cmi_header_h = (%idi_header_h);
    $debug_scbd = \%scbd;
    cxm_cfi_trans_file_reader($fd,\%scbd,@parms);

    print "Found $count transactions in ".$scbd->{filename}."\n" if $debug>=1; 
    close $fd;
    \%scbd;
}

 #To make this function run faster do : zcat ral_monitor_reg_trk.out.gz | grep -i -e iop_memap_init_seq -e tolud_0_0_0_mchbar -e TSEGMB_0_0_0_PCI -e DPRSIZE_0_0_0_PCI -e OPI_SAIFILTER_AC > ral_monitor_reg_trk.out

sub parse_ral_mon_file() {
    my $fd;
    local $_ = "ral_monitor_reg_trk.out";
    my $filename;
    $filename = open_gz(\$fd,$_,0) or return 0;

    if($debug>=1) {
        print "Reading file $_\n";
    }

    while(<$fd>) {
        if(index($_," W ")<0 && index($_,"OPI_SAIFILTER_AC")<0) { next }
        my ($D,$F);
        my $reg_name;
        my $reg_val;
        if(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.MBASE_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            my $BASE = big_hex($3);
            $reg_name = "MBASE";
            $reg_val = $BASE = ($BASE<<16) & 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.MLIMIT_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            my $LIMIT = big_hex($3);
            $reg_name = "MLIMIT";
            $reg_val = $LIMIT = ($LIMIT<<16) | 0xFFFFF; # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.PMBASE_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            # FIXME:esinuani: Need to make this a 64bit bar
            ($D,$F) = (1*$1,1*$2);
            my $PMBASE = big_hex($3);
            $reg_name = "PMBASE";
            $reg_val = $PMBASE = ($PMBASE<<16) & 0xFFFFFFFFFFF00000; # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.PMLIMIT_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            my $LIMIT = big_hex($3);
            $reg_name = "PMLIMIT";
            $reg_val = $LIMIT = ($LIMIT<<16) | 0xFFFFF; # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.PMBASEU_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            # FIXME:esinuani: Need to make this a 64bit bar
            ($D,$F) = (1*$1,1*$2);
            my $PMBASEU = big_hex($3);
            $reg_name = "PMBASE";
            $reg_val = $PMBASEU = ($PMBASEU<<32); # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.PMLIMITU_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            my $LIMITU = big_hex($3);
            $reg_name = "PMLIMIT";
            $reg_val = $LIMITU = ($LIMITU<<32); # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.SBUSN_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            $reg_name = "SBUSN";
            $reg_val = big_hex($3); # Register is always 1MB alligned
        } elsif(/ W .*iop_memap_init_seq.*IOP_SNIF_REGS\.SUBUSN_0_(\d)_(\d)_PCI[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$1,1*$2);
            $reg_name = "SUBUSN";
            $reg_val = big_hex($3); # Register is always 1MB alligned
        } elsif(/ W .*IOP_SNIF_REGS\.(PCICMD|PMCS|BCTRL)_0_(\d)_(\d)_[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (1*$2,1*$3);
            $reg_name = ($1 eq "PCICMD") ? "GCMD" : $1;
            $reg_val = big_hex($4); # Register is always 1MB alligned
        } elsif(/ W .*iop_registers_bank.IMR(\d+)(MASK|WAC|RAC|BASE)_0_0_0_MCHBAR_IMPH[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (0,0);
            $reg_name = "IMR$1$2";
            $reg_val = big_hex($3); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*iop_registers_bank.IOP_IMR_RS0_EN[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (0,0);
            $reg_name = "IOP_IMR_RS0_EN";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*ncevents.TME_ACTIVATE[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (0,0);
            $reg_name = "tme_activate";
            $reg_val = big_hex($1); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*ibecc_cr.*ibecc_activate[^\|]*\|\s*0*(\w+)\s*\|/) {
            ($D,$F) = (0,0);
            $reg_name = "ibecc_activate";
            $reg_val = big_hex($1); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*ibecc_cr.*(ibecc_activate)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = lc($1);
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*IOP_REGISTERS_BANK.*(WRC_VC_ENABLE)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = lc($1);
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*ibecc_cr.*(ECC_STORAGE_ADDR)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc($1);
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*cmf0_mem.(HASH_CONFIG)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc($1);
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*cmf_fast_mem.(MEMORY_SLICE_HASH)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc($1);
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*(lac_0_0_0_pci)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc("LAC");
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ W .*(tolud|touud|remapbase|remaplimit)_0_0_0_(pci)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc($1);
            $reg_val = big_hex($3); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*(tolud|touud|remapbase|remaplimit)_0_0_0_(mchbar)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = uc($1."_0_0_0_".$2);
            $reg_val = big_hex($3); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*DEVEN_0_0_0_PCI[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = "DEVEN";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*TSEGMB_0_0_0_PCI[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = "TSEGMB";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ W .*DPR_0_0_0_PCI[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = "DPR";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ [WR] .*(OPI_SAIFILTER_AC[HL])[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ [WR] .*iop_registers_bank.(PRMRR_BASE)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ [WR] .*iop_registers_bank.(PRMRR_MASK)[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ [WR] .*iop_registers_bank.(MAD_SLICE)_MCHBAR_IMPH[^\|]*\|\s*0*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        }

        if(defined($reg_name) && defined($reg_val) && defined($F)) {
            $PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name} = $reg_val;
            printf("RAL REG: %-8s=%08X $_",$reg_name,$PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name}) if $debug>=5;
        }
    }
    close $fd;
}

sub parse_LNL_RAL_file() {

    my $fd;
    local $_ = "RAL_access_trk_uvm.log";
    my $filename;
    $filename = open_gz(\$fd,$_,0) or return 0;

    if($debug>=1) {
        print "Reading file $_\n";
    }

    while(<$fd>) {
        my ($D,$F);
        my $reg_name;
        my $reg_val;
        if(/ Wr .* (memory_slice_hash) [^\|]*\|\s*0x*(\w+)\s*\|/i) {
            ($D,$F) = (0,0);
            $reg_name = "HASH_CONFIG";
            $reg_val = big_hex($2); 
            #printf "regname=$reg_name %X\n",$reg_val;
        }

        if(/ Wr .* (local_home_slice_hash).*hash_bit0_lsb=([0-9a-f]+).*hash_bit0_mask=([0-9a-f]+)/i) {
            ($D,$F) = (0,0);
            $reg_name = "LOCAL_HOME_SLICE_HASH";
            $soc_hbo_hash_lsb = 6+hex($2);
            $soc_hbo_hash_mask = (hex($3)>>($soc_hbo_hash_lsb-6));
            $reg_val = (hex($2)<<1) | (hex($3)>>6); 
            #printf "regname=$reg_name %X\n",$reg_val;
        } elsif(/ Wr .*hbo_tractor.*PRMRR_BASE.*range_base=(\w+)\s*\|/i) {
            $lnl_prmrr_ranges_l[0]->{BASE} = hex($1)<<12;
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/ Wr .*hbo_tractor.*PRMRR_MASK.*range_en=(\d).*range_mask=(\w+)\s*\|/i) {
            $lnl_prmrr_ranges_l[0]->{MASK} = (hex($2)<<12);
            $lnl_prmrr_ranges_l[0]->{en} = hex($1);
            $reg_name = $1;
            $reg_val = big_hex($2); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/^(\d+) .* Wr .*(CCE_SEAM_CONFIG)\s*\|\s*.*act_enable=(\d+)\s*\|/i) {
            ($D,$F) = (0,0);
            #$reg_name = "CCE_SEAM_CONFIG";
            my $t = 1*$1;
            $reg_val = big_hex($3); 
            my $space_ptr = $PCIE_CFG_SPACE->{$D}->{$F};
            if(!defined($PCIE_CFG_SPACE->{0}->{0}->{CCE_SEAM_CONFIG})) {
                push_reg_and_tick($PCIE_CFG_SPACE->{0}->{0},"CCE_SEAM_CONFIG",1,1,0);
            }
            push_reg_and_tick($space_ptr,"CCE_SEAM_CONFIG",$t,$reg_val,0);
            printf "regname=$reg_name %X\n",$reg_val;
        }

        if(defined($reg_name) && defined($reg_val) && defined($F)) {
            $PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name} = $reg_val;
            #printf("RAL REG: %-8s=%08X $_",$reg_name,$PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name}) if $debug>=5;
        }
    }

    if($lnl_prmrr_ranges_l[0]->{en} and defined($lnl_prmrr_ranges_l[0]->{BASE}) and defined($lnl_prmrr_ranges_l[0]->{MASK}) and ($lnl_prmrr_ranges_l[0]->{BASE}>>12)<=($lnl_prmrr_ranges_l[0]->{MASK}>>12)) {
        $lnl_prmrr_ranges_l[0]->{LIMIT} = ((~$lnl_prmrr_ranges_l[0]->{MASK}) & 0x3FFFFFFFFF) | $lnl_prmrr_ranges_l[0]->{BASE}; 
    } else {
        @lnl_prmrr_ranges_l = (); 
    }
    close $fd;
}

sub parse_emu_minibios_file() {

    my $fd;
    local $_ = "test_cfg/minibios_memmap_config_writes.csv";
    my $filename;
    $filename = open_gz(\$fd,$_,0) or return 0;

    if($debug>=1) {
        print "Reading file $_\n";
    }

    while(<$fd>) {
        if(/^\s*#/) { next }

        my ($D,$F);
        my $reg_name;
        my $reg_val;
        if(/TOLUD_0_0_0_PCI,\w+,(\w+)/i) {
            ($D,$F) = (0,0);
            $reg_name = "TOLUD";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/TOUUD_0_0_0_PCI,\w+,(\w+)/i) {
            ($D,$F) = (0,0);
            $reg_name = "TOUUD";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/TSEGMB_0_0_0_PCI,\w+,(\w+)/i) {
            ($D,$F) = (0,0);
            $reg_name = "TSEGMB";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        } elsif(/DPRSIZE_0_0_0_PCI,\w+,(\w+)/i) {
            ($D,$F) = (0,0);
            $reg_name = "DPRSIZE";
            $reg_val = big_hex($1); # Register is always 1MB alligned
            #print "regname=$regname %X\n",$reg_val;
        }

        if(defined($reg_name) && defined($reg_val) && defined($F)) {
            $PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name} = $reg_val;
            printf("EMU test cfg REG: %-8s=%08X $_",$reg_name,$PCIE_CFG_SPACE->{$D}->{$F}->{$reg_name}) if $debug>=5;
        }
    }
}


%svt_link_header_h = (TIME_BEG=>1,TIME_END=>2,DIR=>3,CMD=>4,ID_TAG=>5);

sub svt_link_file_read_record($) {
    local $_ = shift;

    my @a = split /\s+/;
    my %rec = ( 
        id => $a[$svt_link_header_h{ID_TAG}],
        direction=>($a[$svt_link_header_h{DIR}] eq "T" ? "U" : "D") , # cerfull . I invert the direction here. Because is SOC we need it inverted.
        cmd=>$a[$svt_link_header_h{CMD}],
        length=>$a[15],
        rec_type=>"svt",
        src_ch_tc=>$local_src_ch,
        );

    if(/\sBDF:0x0*(\w\w\w\w)\s/) {
        $rec{BDF} = $1;
    }

    if(/\sR:0x0*([0-9a-f]+)\s/) {
        $rec{address} = hex($1);
    } elsif($a[12]=~/0x([0-9a-f]+)_([0-9a-f]+)$/i) {
        $rec{address} = ((hex($1)<<32) +hex($2));
    } elsif($a[12]=~/0x([0-9a-f]+)$/i) {
        $rec{address} = hex($1);
    }

    if(/\s(\w)\s+(\w)\s+(\w+)\s+\([H]\)/) {
        $rec{fbe_lbe} = sprintf("%04b_%04b",hex($2),hex($1));
        $rec{length} = $3;
    }

    my $tick = ( ($rec{cmd}=~/^Cpl/i) ? $a[2] : $a[1] );
    if($tick=~m/^([0-9][0-9\.]+)/) {
        $rec{tick} = $tick_mul*1000.0*$1;
    }

    return \%rec;
}

sub svt_link_file_reader($$) {
    my $fd = shift;
    my $scbd = shift;
    my $rec_ptr;
    my $next_line;
    local $local_src_ch = get_ch_id("pep");

    $scbd->{read_record_func} = \&svt_link_file_read_record;

    my $start_header = 0;

    while(<$fd>) {
        if(/^-----/) { last; }
    }

    $next_line = <$fd>;

    while(1) {
        if($next_line=~/\s\(H\)\s/) {
            if(defined($rec_ptr)) {
                # Goto analysing this record
            } else {

                $rec_ptr = &{$scbd->{read_record_func}}($next_line) or next;

                if($next_line=~/\sT\s+MWr/) {
                    $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id("PEP_HOST_direct");
                } elsif($next_line=~/\sR\s+MRd/) {
                    $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch} = get_ch_id("PEP_HOST_dma");
                }

                $rec_ptr->{line} = $next_line;
                $next_line = <$fd>;
                next;
            }
        } elsif($next_line=~/\(D\)\s*(.*\w)/) {
            if(!defined($rec_ptr)) { die_ERROR("092 ERROR: ");}
            $rec_ptr->{data} .= ":" if defined($rec_ptr->{data});
            $rec_ptr->{data} .= fix_little_indian($1);
            $next_line = <$fd>;
            next;
        } elsif(defined($next_line)) {
            if(!defined($rec_ptr)) {
                $next_line = <$fd>;
                next;
            }
        } else { # if not defined($next_line)
            if(!defined($rec_ptr)) { last }
        }

        if(defined($rec_ptr)) {
            my $is_join = 0;
            my $line = $rec_ptr->{line};

            if($rec_ptr->{cmd} =~ /^(IOWr|IORd|MRd|CfgRd|CfgWr|LTMRd32)/) {
                # We expect a cpl with length 0 or all Wr cmd and length fo Rd cmd
                $rec_ptr->{length_cpl} = ($rec_ptr->{cmd}=~/Wr/ ? 0 : $rec_ptr->{length});
                push @{$scbd->{ $rec_ptr->{direction} }->{ $rec_ptr->{id} }} , $rec_ptr;
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
            } elsif($rec_ptr->{cmd} =~ /^Cpl/) {
                my $other_direction = ($rec_ptr->{direction} eq "U" ? "D" : "U");
                my $id_list_ptr = $scbd ->{$other_direction} -> { $rec_ptr->{id} };
                my $tr = $id_list_ptr->[0];
                if(defined($tr)) {
                    if($debug>=3) {
                        print "In   :id=".$rec_ptr->{id}.": ".$tr->{line};
                        print " Out :id=".$rec_ptr->{id}.": ".$line; 
                    }
                    $tr->{length_recv} += $rec_ptr->{length};
                    if(!defined($tr->{data})) { 
                        $tr->{data} = $rec_ptr->{data};
                    } else {
                        $tr->{data} .= ":".$rec_ptr->{data};
                    }
                    if(/UNSUP_REQ/) {
                        shift @$id_list_ptr;
                        $tr->{is_UR}="OPIO_UR";
                    } elsif($tr->{length_recv} == $tr->{length_cpl}) {
                        shift @$id_list_ptr;
                        $tr->{tick_end} = $rec_ptr->{tick};
                        if($tr->{is_UR}) {
                            $exit_code=1;
                            print_ERROR("040 ERROR: This transaction shoulg get UR $tr->{is_UR} : $tr->{line}");
                        }
                    } elsif($tr->{length_recv} > $tr->{length_cpl}) {
                        print_ERROR("049 ERROR: Too many data DW received by this transaction: $line");
                        $exit_code=1;
                    }
                } else {
                    print_ERROR("050 ERROR: unmatch transaction: $line");
                    $exit_code = 1;
                }
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
            } elsif($rec_ptr->{cmd}=~/^(Msg|MWr)/) {
                push @{$scbd->{ $rec_ptr->{direction} }->{ all }} , $rec_ptr;
                $rec_ptr->{tick_beg} = $rec_ptr->{tick};
                if($debug>=3) {
                    print "In P :id=".$rec_ptr->{id}.": ".$rec_ptr->{line};
                }
            }

            undef $rec_ptr;
        }
    }

    assign_rec_parent_idx($scbd->{U}->{all});
    assign_rec_parent_idx($scbd->{D}->{all});
    psf_check_all_Cpl($scbd);
}

sub parse_svt_LINK_file() {

    my $fd;
    local $_ = "pcie_vip_trans.log";
    my $filename;
    $filename = open_gz(\$fd,$_,0) or return 0;

    if($debug>=1) {
        print "Reading file $filename\n";
    }

    my %link_file_scbd;

    $link_file_scbd{filename} = $filename;

    svt_link_file_reader($fd,\%link_file_scbd);
    #psf_file_post_process(\%link_file_scbd);

    if($filename =~/^pcie_vip_trans/) {
        $pep_svt_link_file_scbd = \%link_file_scbd;
    }
}


# Drop this functions because there is a time that "leraxed ordering transactions" change order in ADL.
sub merge_hashed_scbd($$) {
    my ($scbd1,$scbd2) = @_; 
    my $scbd = { filename=> ($scbd1->{filename}) };
    my $trans_l2;
    for my $dir ("D") {
        my ($i1,$i2) = (0,0);
        my $trans_l1 = ($scbd1->{$dir}->{all} or []);
        my $trans_l2 = ($scbd2->{$dir}->{all} or []);
        my $trans_l = [];
        while(1) {
            if(($i1<@$trans_l1) && ($i2<@$trans_l2)) {
                if($trans_l1->[$i1]->{tick_beg}<=$trans_l2->[$i2]->{tick_beg}) {
                    push @$trans_l,$trans_l1->[$i1];
                    $i1+=1;
                } else {
                    push @$trans_l,$trans_l2->[$i2];
                    $i2+=1;
                }
            } else {
                if($i1<@$trans_l1) {
                    for(;$i1<@$trans_l1;$i1+=1) {
                        push @$trans_l,$trans_l1->[$i1];
                    }
                } elsif($i2<@$trans_l2) {
                    for(;$i2<@$trans_l1;$i2+=1) {
                        push @$trans_l,$trans_l2->[$i2];
                    }
                }
                last;
            }
        }
        $scbd->{$dir}->{all} = $trans_l;
    }
    return $scbd;
}

sub create_ADL_cmi_addr_h($) {
    my ($scbd) = @_; 
    my $addr_h = { };
    for my $dir ("D") {
        my ($i1,$i2) = (0,0);
        my $trans_l1 = ($scbd->{$dir}->{all} or []);
        for(my $i1=0; $i1<@$trans_l1 ; $i1+=1) {
            my $rec_ptr = $trans_l1->[$i1];
            if($rec_ptr->{cmd}=~/MWr/) {
                $addr_h->{$rec_ptr->{address}>>6}=1;
            }
        }
    }
    return $addr_h;
}

sub build_base_limit_range($$$) {
    my ($space,$base_name,$limit_name) = @_;
    if(defined($space->{$base_name}) && defined($space->{$limit_name}) && $space->{$base_name} < $space->{$limit_name}) {
        return ({BASE=>$space->{$base_name},LIMIT=>$space->{$limit_name}});
    } else {
        return ();
    }
}

sub get_pcie_mbase_ranges() {
    my @ranges_l = ();
    for my $D (keys %$PCIE_CFG_SPACE) {
        if($D==9) { next }
        if(!length($D)) { next }
        for my $F (keys %{$PCIE_CFG_SPACE->{$D}}) {
            if(!length($F)) { next }
            my $space = $PCIE_CFG_SPACE->{$D}->{$F};
            push @ranges_l,build_base_limit_range($space,"MBASE","MLIMIT");
            push @ranges_l,build_base_limit_range($space,"PMBASE","PMLIMIT");
        }
    }
    return @ranges_l;
}

sub get_pcie_D_exlude_range_l(@) {
    my %parms=@_;
    my @exclude_range_l = ();
    my $D=$parms{PCIE_DEVICE};
    my $F=$parms{PCIE_FUNCTION};
    if(defined($D) && defined($F)) {
        my $space = $PCIE_CFG_SPACE->{$D}->{$F};
        if(defined($space) && defined($space->{VTD_BASE})) {
            push @exclude_range_l,build_base_limit_range($space,"VTD_BASE","VTD_LIMIT");
        }
    }
    return @exclude_range_l;
}

sub get_pcie_space_var(@) {
    my %parms = @_;
    return 0 unless defined($parms{D}) && defined($parms{F});
    my $space = $PCIE_CFG_SPACE->{$parms{D}}->{$parms{F}} or return 0;
    return ($space->{$parms{var_name}} or 0);
}


sub check_bus_range(@) {
    my %parms = @_;
    my $space  =  $PCIE_CFG_SPACE->{$parms{D}}->{$parms{F}} or return 0;
    my $SBUSN   = ($space->{SBUSN}  and get_reg_val_in_tick($space->{SBUSN} ,$parms{tick}))  or return 0;
    my $SUBUSN  = ($space->{SUBUSN} and get_reg_val_in_tick($space->{SUBUSN},$parms{tick}))  or return 0;
    my $bus = $parms{bus};
    return 0 unless ($bus>=$SBUSN && $bus<=$SUBUSN);
    return 1;
}

sub filter_MCTP_MsgD($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    my $is_from_pch = $parms{is_from_pch};
    my $tlp_l   = $rec_ptr->{tlp} or return 0;
    return 0 unless ($rec_ptr->{cmd}=~/Msg/ && (3<=@$tlp_l));
    my $MsgType = ($tlp_l->[0]>>24);
    return 0 unless (($tlp_l->[1]&0xFF) == 0x7F); # Make sure it is MCTP
    if($MsgType == 0x72) { # Its MsgD2 opcode
        if($is_from_pch) {
            if(defined($parms{D}) && defined($parms{F})) {
                return 0 unless check_bus_range(bus=>($tlp_l->[2]>>24),D=>$parms{D},F=>$parms{F},tick=>$rec_ptr->{tick});
            }
        } else {
            if($rec_ptr->{direction} eq "D") {
                return check_bus_range(bus=>(hex($rec_ptr->{BDF})>>8),D=>$parms{D},F=>$parms{F},tick=>$rec_ptr->{tick});
            } else {
                if($parms{D}!=6 && $parms{D}!=1) { # Not relevant for PEG60,PEG10,PEG11,PEG12
                    return 0 if check_bus_range(bus=>($tlp_l->[2]>>24),D=>$parms{D},F=>$parms{F},tick=>$rec_ptr->{tick});
                }
                return 0 if !check_bus_range(bus=>(hex($rec_ptr->{BDF})>>8),D=>$parms{D},F=>$parms{F},tick=>$rec_ptr->{tick});
                return 1; # Accept
            }
        }
    } elsif($MsgType == 0x73) { # Its MsgD3 (BroadCast)
        if($is_from_pch) { 
            return 0 unless $rec_ptr->{length} == 1;
        } else { return 0 };
    } elsif($MsgType == 0x70) {
        if($is_from_pch) { return 0; }
        else {
            if(defined($parms{D}) && defined($parms{F})) {
                return 0 unless check_bus_range(bus=>(hex($rec_ptr->{BDF})>>8),D=>$parms{D},F=>$parms{F},tick=>$rec_ptr->{tick});
            }
        }
    } else {
        return 0; # Reject
    }
    return 1; # Accept
}

sub check_pcie_hub_bus_range(@) {
    my %parms = @_;
    my $space  =  $PCIE_CFG_SPACE->{$parms{D}}->{$parms{F}} or return 0;
    my $SBUSN   = ($space->{SBUSN}  and get_reg_val_in_tick($space->{SBUSN} ,$parms{tick}))  or return 0;
    my $SUBUSN  = ($space->{SUBUSN} and get_reg_val_in_tick($space->{SUBUSN},$parms{tick}))  or return 0;
    my $bus = $parms{bus};
    return 0 unless ($bus>=$SBUSN && $bus<=$SUBUSN); #FIXME: This is temporarily : $SBUSN+2. Need to better calculate the $SBUSN
    return 1;
}

sub cmi_hash_filter($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    my $idx = $parms{hash_idx};
    if(cmi_hash_get_mc_idx($rec_ptr->{address})==$idx) {
        return 1;
    } else {
        return 0;
    }
}

# Hash faction based on list
sub ADL_cmi_hash_filter($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    my $idx = $parms{hash_idx};
    my $ret;
    if($parms{addr_h}->{$rec_ptr->{address}>>6}) {
        $ret = 0;
    } else {
        $ret = 1;
    }
    return ($ret ^ ($parms{hash_idx}!=0));
}

# Hash faction based on list
sub ADL_DMI_VCm_filter($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    if($rec_ptr->{vc}==2 and !$rec_ptr->{ns}) {
        # Skep these transaction that comes from DMI : src_ch==302 vc==5 and ns==0
        return 0;
    }
    return 1;
}

sub ADL_IOP_DMI_VCm_filter($) {
    # exclude_func_l
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    if($ch_name_l[$rec_ptr->{src_ch}] == 302 and $rec_ptr->{vc}==5 and !$rec_ptr->{ns}) {
        # Skep these transaction that comes from DMI : src_ch==302 vc==5 and ns==0
        return 0;
    }
    return 1;
}

sub compare_read_byte_stream__create_ch($) {
    my ($src_ch_tc) = @_;
    my %new_ch_rec_l;
    $new_ch_rec_l{rec_l} = [];
    #$new_ch_rec_l{write_refmem_h} = [];
    $new_ch_rec_l{rec_l_index}=0; #init the index to its rec_l
    $new_ch_rec_l{src_ch_tc_key}=$src_ch_tc;
    $new_ch_rec_l{attr}=0;
    return \%new_ch_rec_l;
}

sub get_src_ch_tc($) {
    return ($_[0]->{parent} ? $_[0]->{parent}->{src_ch_tc} : $_[0]->{src_ch_tc});
}

# Compare transactions byte by byte
sub source_split_read_byte_stream_l(@) {
    my %parms = @_;
    my $trans_l = $parms{trans_l} or die_ERROR("093 ERROR: ");
    #Virtual channel hash
    my $index1 = 0;

    my %source_split_h;
    my @source_split_l;

    # split the first (write) stream to source channels
    for $index1 (0..(+@$trans_l-1)) {
        my $rec_ptr1 = $trans_l->[$index1];
        my %ch_rec_h;
        my $src_ch_tc = get_src_ch_tc($rec_ptr1) or die_ERROR("094 ERROR: ");
        push @{$source_split_h{$src_ch_tc}},$rec_ptr1;
    }

    while(my ($name,$trans_l) = each(%source_split_h)) {
        if(defined($trans_l)) {
            push @source_split_l,$trans_l;
        }
    }

    @source_split_l = sort { $ch_name_l[get_src_ch_tc($a->[0])] cmp $ch_name_l[get_src_ch_tc($b->[0])] } @source_split_l;
   
    return \@source_split_l;
}

sub recalculate_all_write_refmem($$$) {
    my $write_refmem_h = []; # FIXME: Need to undef all elements instead of this. Ensure the this improves performance.
    $write_refmem_h->[$smart_hash_index-1] = undef;
    my ($all_ch_ptr_l1,$all_write_order_l,$max_index2) = @_;
    my $write_idx=0;
    # print "EYAL1:recalculate_all_write_refmem to index2=$max_index2\n";
    # FIXME: Need to find a way to only partially recalculate refmem and avoid reseting all indexes here:
    for my $ch_ptr (@$all_ch_ptr_l1) { 
        $ch_ptr->{write_refmem_h_index1} = 0;
    }

    for(my $write_idx=0; $write_idx<$max_index2 ; $write_idx++) {
        if(!defined($all_write_order_l->[1+$write_idx])) { next; }
        my $sub_order_idx = -1;
        for my $sub_order_l (@{$all_write_order_l->[1+$write_idx]}) {
        $sub_order_idx+=1;
        if(!defined($sub_order_l)) { next }
        my $max_idx = 1*@$sub_order_l;
        for(my $idx=0; $idx+1 < $max_idx ; $idx+=4 ) { 
            my $ch_ptr = $all_ch_ptr_l1->[$sub_order_l->[$idx  ]];
            my $index1 =                  $sub_order_l->[$idx+1];
            my $override_index1 =         $sub_order_l->[$idx+2];
            if($index1 <= $ch_ptr->{rec_l_index})  {
                my $index2 = $sub_order_idx==0 ? $write_idx-1 : $write_idx;
                update_write_refmem($write_refmem_h,$ch_ptr,$index1,$index2,$override_index1,$sub_order_idx);
            } else {
                die_ERROR("095 ERROR: FATAL index1 is bigger that ch_ptr->rec_l_index!!");
            }
        }
        } # for my $sub_order_l
    }
    return $write_refmem_h;
}

sub reverse_refmem_address($$$) {
    $e2e_refmem_reverse_count+=1;;
    my ($refmem_ptr,$index2,$commit_stage) = @_;
    my $max_idx = (@$refmem_ptr-1);
    for(;$max_idx>=0;$max_idx-=1) {
        if($refmem_ptr->[$max_idx]->[1]>=$index2) {
            if(!defined($commit_stage) or $commit_stage == $refmem_ptr->[$max_idx]->[3]) {
                pop @$refmem_ptr;
            }
        } else {
            last;
        }
    }
}

sub get_top_refmem($) {
    my $refmem_ptr = $_[0];
    my $max_idx = (@$refmem_ptr-1);
    if($max_idx>=0) {
        return $refmem_ptr->[$max_idx];
    } else {
        return undef;
    }
}

sub update_write_refmem($$$$$$) {
    my ($all_write_refmem_h,$ch_ptr,$new_index1,$index2,$override_index1,$commit_stage) = @_;
    my $data;
    my $rec_offset;
    my $shash_index,$shash_index_size;
    my $debug = $::debug;

    my $try_index1=($ch_ptr->{write_refmem_h_index1} or 0);

    for( ; $try_index1 < $new_index1; $try_index1+=1)  {
      my $rec_ptr1 = $ch_ptr->{rec_l}->[$try_index1]->[OBJ_REC];
      my $address1;
      for($rec_offset = 0 ; $rec_offset<=$#{$rec_ptr1->{join_l}} ; $rec_offset+=1) {
        $shash_index  = $rec_ptr1->{join_l}->[$rec_offset];
        $address1 = $rec_ptr1->{address} + get_word2($shash_index);
        $shash_index_size = ((get_word3($shash_index)+1)<<1); $shash_index &= 0xFFFFFFFF;
        my $address1_str;
        my $refmem_rec_l = get_top_refmem($all_write_refmem_h->[$shash_index]);
        my $is_refmem_rec_l = (1<=$#$refmem_rec_l);
        if($debug and (defined($debug_shash_index) and $debug_shash_index->{$shash_index&0xFFFFFFFF} and defined($address1_str=addr_str($address1)))) {
            $data = substr($rec_ptr1->{data},-(($address1-$rec_ptr1->{address})<<1)-2,2);
            print "EYAL9:check__refmem: address=$address1_str data=$data ch_idx1=$ch_ptr->{ch_idx} index1=$try_index1 go=$rec_ptr1->{tick_go} end=$rec_ptr1->{tick_end} mc=$rec_ptr1->{tick_mc} write_refmem_h_index1=$ch_ptr->{write_refmem_h_index1} line=$rec_ptr1->{parent}->{line}";
            if($#{$log_err_data->{wr_l}}>=6) { shift @{$log_err_data->{wr_l}}; }
            push @{$log_err_data->{wr_l}} , $rec_ptr1;
        }
        if(!$skip_e2e_write_chk and !defined($rec_ptr1->{tick_go})) {
            die_ERROR("111 ERROR: This transaction does not have tick_go address=".addr_str($address1)." data=$rec_ptr1->{data} ch_idx1=$ch_ptr->{ch_idx} index1=$try_index1 end_time=$rec_ptr1->{tick_end} line=$rec_ptr1->{parent}->{line}");
        }
        $e2e_refmem_update_count += 1;
        my $is_tick_mc = defined($rec_ptr1->{tick_mc}) && ($is_refmem_rec_l and defined($refmem_rec_l->[REFMEM_REC]->{tick_mc}));
        if(!$is_refmem_rec_l or $rec_ptr1->{parent}->{src_ch_tc} == $refmem_rec_l->[REFMEM_REC]->{parent}->{src_ch_tc}
            or defined($override_index1) && $override_index1==$try_index1
            or $refmem_rec_l->[REFMEM_REC]->{parent}->{src_ch_tc} == $mcc_preloader_ch_id # If the ref_mem is preload line, then always overite it.
            or $rec_ptr1->{parent}->{src_ch_tc} != $mcc_preloader_ch_id && ( # If rec_ptr1 is from preload, and the refmem is not from preload the ref_mem override it.
                   $is_tick_mc  && $rec_ptr1->{tick_mc}>$refmem_rec_l->[REFMEM_REC]->{tick_mc}
                or !$is_tick_mc && $rec_ptr1->{tick_go} > $refmem_rec_l->[REFMEM_REC]->{tick_go} 
            )
        ) {
            $data = substr($rec_ptr1->{data},-(($address1-$rec_ptr1->{address})<<1)-$shash_index_size,$shash_index_size);
            if($debug and defined($address1_str)) {
                print "EYAL2:update_refmem: address=$address1_str data=$data ch_idx1=$ch_ptr->{ch_idx} index1=$try_index1 go=$rec_ptr1->{tick_go} end=$rec_ptr1->{tick_end} line=$rec_ptr1->{parent}->{line}";
            }
            push @{$all_write_refmem_h->[$shash_index]},[$rec_ptr1,$index2,$try_index1,$commit_stage,$data];
        }
      } # for( ; $rec_offset ...)
    }
    $ch_ptr->{write_refmem_h_index1} = $new_index1;
}

sub reverse_all_write_refmem($$$$$$) {
    my ($all_ch_ptr_l1,$all_write_refmem_h,$all_write_order_l,$new_index2,$last_index2,$is_only_1) = @_;
    my $write_idx=0; my $shash_index; my $rec_offset;
    print "EYAL1:recalculate_all_write_refmem to index2=$new_index2 - revert from last_index2=$last_index2\n" if $debug>=5;

    my $write_order_index2_0 = $all_write_order_l->[1+$new_index2]->[0]; # Save this because I need to restore them.

    for(my $write_idx=$last_index2; $write_idx>=$new_index2 ; $write_idx--) {
        if(!defined($all_write_order_l->[1+$write_idx])) { next; }
        my $sub_order_idx = 1*@{$all_write_order_l->[1+$write_idx]}-1;
        for ( ; $sub_order_idx>=$is_only_1 ; $sub_order_idx-=1) {
            my $sub_order_l = $all_write_order_l->[1+$write_idx]->[$sub_order_idx];
            if(!defined($sub_order_l)) { next }
            my $max_idx = 1*@$sub_order_l;
            for(my $idx=$max_idx; $idx > 1 ; $idx-=4 ) { 
                my $ch_ptr = $all_ch_ptr_l1->[$sub_order_l->[$idx-4]];
                my $index1 =                  $sub_order_l->[$idx-3];
                my $override_index1 =         $sub_order_l->[$idx-2];
                my $write_refmem_h_index1 =   $sub_order_l->[$idx-1];
                for(my $try_index1=$write_refmem_h_index1; $try_index1 < $index1 ;$try_index1+=1) {
                    my $rec_ptr1 = $ch_ptr->{rec_l}->[$try_index1]->[OBJ_REC];
                    my $commit_stage = ($new_index2==$write_idx ? 1 : undef); # If we are at $new_index2 then revert only commits at $all_write_order_l->[$write_idx]->[1]
                    for($rec_offset = 0 ; $rec_offset<=$#{$rec_ptr1->{join_l}} ; $rec_offset+=1) {
                        $shash_index  = $rec_ptr1->{join_l}->[$rec_offset] & 0xFFFFFFFF; reverse_refmem_address($all_write_refmem_h->[$shash_index],$new_index2,$commit_stage); 
                    }
                }
                $ch_ptr->{write_refmem_h_index1} = $write_refmem_h_index1;
            }
        } # for my $sub_order_l
        $all_write_order_l->[1+$write_idx] = undef;
    }
}

sub does_it_write_at_addr($$$$) {
    my ($top_wr_rec,$address2,$index1,$ch_ptr) = @_;
    my $parent_idx1 = $top_wr_rec->{parent}->{idx};
    my $top_index1 = 1*@{$ch_ptr->{rec_l}};
    for($next_index1=$index1+1; $next_index1<$top_index1 ; $next_index1++) {
        my $rec_ptr1 = $ch_ptr->{rec_l}->[$next_index1]->[OBJ_REC];
        last unless $parent_idx1==$rec_ptr1->{parent}->{idx};
        my $addr1 = $rec_ptr1->{address};
        if($address2==$addr1) {
            return 1;
        } elsif($address2<$addr1) {
            last;
        }
    }
    return 0;
}

sub is_there_previous_match_wr($$$$) {
    my ($trans_l2,$ch_ptr,$index2,$index1) = @_;
    # If this $index2 is related to a transaction that has match this write, then skip it. 
    # This because the match should happen on a previous read.
    if(!$skip_CL_recheck) {
        my $rec_ptr2 = $trans_l2->[$index2];
        my $parent_idx2    = $rec_ptr2->{parent}->{idx};
        my $address1_match = $rec_ptr2->{address}>>6;
        my $rechk_index1 = $index1-1;
        my $parent_idx = $ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{parent}->{idx};
        for(my $rechk_index2 = $index2-1; $rechk_index2>=0 ; $rechk_index2-=1) {
            my $rechk_rec_ptr2 = $trans_l2->[$rechk_index2];
            last unless $parent_idx2==$rechk_rec_ptr2->{parent}->{idx}; # We are in the same read
            my $address2 = $rechk_rec_ptr2->{address};
            last unless ($address2>>6) == $address1_match; # Check that we are still in the same CL
            #my $rechk_rec_ptr1;
            while($rechk_index1>=0) {
                my $tmp_rec_ptr1 = $ch_ptr->{rec_l}->[$rechk_index1]->[OBJ_REC];
                last unless $tmp_rec_ptr1->{parent}->{idx}==$parent_idx;
                my $addr1 = $tmp_rec_ptr1->{address};
                if($addr1==$address2) {
                    # Found that we have a write from the same CL and the match address. It's in $rechk_rec_ptr1. Next will compare it to top refmem
                    my $top_refmem = get_top_refmem($all_write_refmem_h->[$rechk_rec_ptr2->{shash_index}]);
                    my $top_wr_rec = $top_refmem->[REFMEM_REC];
                    if(does_it_write_at_addr($top_wr_rec,$rec_ptr2->{address},$top_refmem->[REFMEM_INDEX1],$ch_h1{$top_wr_rec->{parent}->{src_ch_tc}})) {
                        return $tmp_rec_ptr1;

                    }
                } elsif($addr1<$address2) {
                    last;
                }
                $rechk_index1 -= 1;
            }
        }
    }
    return undef;
}

sub is_there_previous_match_wr_join($$$$) {
    my ($trans_l2,$ch_ptr,$index2,$index1) = @_;
    # If this $index2 is related to a transaction that has match this write, then skip it. 
    # This because the match should happen on a previous read.
    if(!$skip_CL_recheck) { my $sz;
        my $rec_ptr2 = $trans_l2->[$index2];
        my $parent_idx2    = $rec_ptr2->{parent}->{idx};
        my $address1_match = $rec_ptr2->{address}>>6;
        my $parent_idx = $ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{parent}->{idx};
        my $tmp_rec_ptr1 = $ch_ptr->{rec_l}->[$index1]->[OBJ_REC];
        for(my $rechk_index2 = $index2-1; $rechk_index2>=0 ; $rechk_index2-=1) {
            my $rechk_rec_ptr2 = $trans_l2->[$rechk_index2];
            last unless $parent_idx2==$rechk_rec_ptr2->{parent}->{idx}; # We are in the same read
            my $address2 = $rechk_rec_ptr2->{address};
            last unless ($address2>>6) == $address1_match; # Check that we are still in the same CL
            {
                my $addr1 = $tmp_rec_ptr1->{address};
                last unless $addr1<=$address2; # no need to check the upper address because we are in the same cache line
                if("xx" ne ($sz=substr($tmp_rec_ptr1->{data},-(($address2-$addr1)<<1)-2,2)) and length($sz)) {
                    # Found that we have a write from the same CL and the match address. It's in $rechk_rec_ptr1. Next will compare it to top refmem
                    # return 1;
                    my $top_refmem = get_top_refmem($all_write_refmem_h->[$rechk_rec_ptr2->{shash_index}]);
                    my $top_wr_rec = $top_refmem->[REFMEM_REC];
                    # Found that we have a write in refmem same CL and the match address2. 
                    if("xx" ne ($sz=substr($top_wr_rec->{data},-(($rec_ptr2->{address}-$top_wr_rec->{address})<<1)-2,2)) and length($sz)) {
                        return 1; # this will cancel the match because it did not match in all the previous byte
                    }
                }
            }




        }
    }
    return undef;
}

sub find_byte_match_in_ch($$$$$$) {
    my ($trans_l2,$ch_ptr,$rec_ptr2,$index2,$try_index1,$trans_l2) = @_;
    my $top_index1 = 1*@{$ch_ptr->{rec_l}};
    my ($err_code,$log_str,$err_str);
    my @match_l;

    if(!defined($try_index1)) {
        $try_index1=$ch_ptr->{rec_l_index};
    }

    my $first_try_index1 = $try_index1;

    for(; $try_index1<=$top_index1 ; $try_index1+=1)  {
        my $address2 = $rec_ptr2->{address};

        # If no address match, try to match with previous write in write_refmem_h
        if($try_index1<$top_index1) {
            $rec_ptr1 = $ch_ptr->{rec_l}->[$try_index1]->[OBJ_REC];

            if(defined($rec_ptr2->{tick_end}) && defined($rec_ptr1->{tick_beg})
                && ($rec_ptr1->{tick_beg} > $rec_ptr2->{tick_end})) {
                # No need to check transactions later than the read time
                ($err_code,$log_str,$err_str) = (1,"","Got to rec_ptr2 tick of channel and found no matching write address=".addr_str($address2)." data=$rec_ptr2->{data} src_ch_tc_key=$ch_name_l[$ch_ptr->{src_ch_tc_key}] ch_idx1=$ch_ptr->{ch_idx} index1=$try_index1 index2=$index2 \n  to rec2 src_ch_tc=$ch_name_l[$rec_ptr2->{parent}->{src_ch_tc}] $rec_ptr2->{parent}->{line}\n");
                $try_index1 = $top_index1+10; # Make loop exit
            } else {
                $e2e_read_compare_count++;
                ($err_code,$log_str,$err_str) = fast_compare_byte_rec($rec_ptr1,$rec_ptr2); # compare_byte_rec($rec_ptr1,$rec_ptr2);
                if(!$err_code and is_there_previous_match_wr_join($trans_l2,$ch_ptr,$index2,$try_index1)) {
                    ($err_code,$log_str,$err_str) = (2,"","Skip this match because it should also match a previous wr in this CL\n");
                }
            }
            
        } else {
            ($err_code,$log_str,$err_str) = (1,"","Got to end of channel and found no matching write address=".addr_str($address2)." data=$rec_ptr2->{data} src_ch_tc_key=$ch_name_l[$ch_ptr->{src_ch_tc_key}] ch_idx1=$ch_ptr->{ch_idx} try_index1=$first_try_index1..$try_index1 index2=$index2\n  to rec2 src_ch_tc=$ch_name_l[$rec_ptr2->{parent}->{src_ch_tc}]  $rec_ptr2->{parent}->{line}\n");
        }
        if($err_code) {
            $ch_ptr->{err_code} = $err_code;
            $ch_ptr->{err_str} = $err_str;
            $ch_ptr->{log_str} = $log_str;
        } else {
            my %match_case_h = (
                log_str => $log_str,
                index1 => $try_index1,
                ch_ptr => $ch_ptr,
                is_match_previous_write => 0,
            );
            print "Got possibble index2=$index2 address=".addr_str($rec_ptr2->{address})." ch=$ch_name_l[$ch_ptr->{src_ch_tc_key}] ch_idx1=$ch_ptr->{ch_idx} index1=$try_index1\n" if($debug>=8);
            push @match_l,\%match_case_h;
        }
    }

    return @match_l;
}

sub should_I_got_back($$) {
    my ($tick_beg,$posibility_h_ptr) = @_;
        for my $case_ptr (@{$posibility_h_ptr->{match_case_l}}) {
            if($tick_beg<=$case_ptr->{ch_ptr}->{rec_l}->[$case_ptr->{index1}]->[OBJ_REC]->{tick_end} or
                $tick_beg<=$case_ptr->{ch_ptr}->{rec_l}->[$case_ptr->{index1}]->[OBJ_REC]->{parent}->{tick_EXTCMP}) {
                    return 1;
            }
        }
    return 0;
}

# Compare transactions byte by byte
sub compare_read_byte_stream_l(@) {
    my %parms = @_;
    my $trans_l1 = $parms{trans_l1} or die_ERROR("096 ERROR: ");
    my $trans_l2 = $parms{trans_l2} or die_ERROR("097 ERROR: ");
    local $iommu_scbd_h = $parms{iommu_scbd_h};
    local $field_l = ($parms{field_l} or ["data","cmd","id","address","fbe_lbe"]);
    my $count=0; my $time_cnt = 0;
    #Virtual channel hash
    local %ch_h1;
    my $index1 = 0;
    my $index2 = 0;
    my $index1_vc;
    my @recompare_posibilities_l;
    my %read_addr_h = ();
    my %read_cl_addr_h;
    local $smart_hash_index = 1;
    local $mcc_preloader_ch_id = get_ch_id("mcc_preloader");
    my %mcc_zero_preloader_h;
    my $all_write_order_l; $all_write_order_l->[1*@$trans_l2] = undef; # allocate the full array size.
    local $all_write_refmem_h;
    my $do_recalculate_all_write_refmem = undef;
    my $debug = $::debug;
    my $e2e_read_compare_count = $::e2e_read_compare_count;
    my $last_e2e_read_compare_count = $e2e_read_compare_count;
    my $last_RDCURR_state = undef;
    # If its a pcie read channel, then do pcie ordering rules (very loosed ordering)
    my $mine_src_ch_tc_name = $ch_name_l[$trans_l2->[0]->{parent}->{src_ch_tc}];
    my $is_pcie_order = (@$trans_l2 && ($mine_src_ch_tc_name =~ /pep|opio|_psf/) ? 1 : 0);
    my $pcie_last_parent_idx2 = -1;
    my $pcie_last_parent_address = -1;
    my $pcie_last_posibility = undef;
    my $is_core_idi_reads = $mine_src_ch_tc_name =~ /(IA_IDI_|AT_IDI_|^MEDIA|^GT|^IAX)/;
    my $full_wr_ch_byte_l = []; my $full_shrink_wr_ch_byte_l = [];

    # Scan all read stream, and put all addresses in mcc_preloader_ch with zero data value
    $index2 = 0;
    my $zero_preloader_src_ch_tc = get_ch_id("mcc_preloader");
    my $is_zero_init = !($ACERUN_CLUSTER=~/^(idi_bridge|ccf)/); # in case of ccf cte do ZZ init instead of zero init.
    my $init_line_str = ($is_zero_init ? "e2e_preloader_zero_init\n" : "e2e_preloader_ZZ_init\n");
    my $preload_CL_idx_h = { };
    while($index2<+@$trans_l2) { # FIXME: Maybe not need all this preload to zero.
        my $rec_ptr2 = $trans_l2->[$index2];
        my $address = $rec_ptr2->{address};
        my $my_is_zero_init = $is_zero_init && !is_addr_in_range_l_fast($address,\@mmio_ranges_l);
        my $zero_preloader_init_dumy_parent = $preload_CL_idx_h->{$address>>6};
        if(!defined($zero_preloader_init_dumy_parent)) {
            $preload_CL_idx_h->{$address>>6} = $zero_preloader_init_dumy_parent 
                = { line=>$init_line_str, src_ch_tc=>$zero_preloader_src_ch_tc,tick_beg=>0,tick_go=>0,tick_end=>0,tick_mc=>0, idx=>$parent_idx_count++};
        }
        # This creates a smart hash that uses actually $write_refmem_h as array instead of a hash. 
        # This will make run faster, since we are not using hash when running the heavby e2e_read_chk that sman all wr channels agains alll reads
        if(!defined($read_addr_h{$address})) { $read_addr_h{$address} = $smart_hash_index++; $read_cl_addr_h{$address>>6}=1; }
        $rec_ptr2->{shash_index} = $read_addr_h{$address};
        $mcc_zero_preloader_h{$address} = {address=>$address,data=>($my_is_zero_init?"00":"ZZ"),parent=>$zero_preloader_init_dumy_parent
            ,tick_beg=>0,tick_go=>0,tick_end=>0,tick_mc=>0,shash_index=>($read_addr_h{$address})} unless defined($mcc_zero_preloader_h{$address});
        $index2++;
    }
    undef $preload_CL_idx_h;

    # split the first (write) stream to source channels
    $index1 = -1;
    for $wr_ch_trans_l (@$trans_l1) {
      my $wr_ch_byte_l = $wr_ch_trans_l;
      if(!@$wr_ch_trans_l) { next }
      if(!defined($wr_ch_trans_l->[0]->{parent})) {
        # If this is a transaction array convert it to byte_stream
        # But first filter the addresses not in $read_cl_addr_h 
        my $wr_ch_trans_filter_l = [ ];
        for my $rec_ptr1 (@$wr_ch_trans_l) {
            if($read_cl_addr_h{$rec_ptr1->{address}>>6}) {
                push @$wr_ch_trans_filter_l,$rec_ptr1;
            }
            if($verify_parent_index and !defined($rec_ptr1->{idx})) {
                die_ERROR("152 ERROR: This transaction does not have parent index: ".trans_str($rec_ptr1));
            }
        }
        $wr_ch_byte_l = create_byte_stream(trans_l=>$wr_ch_trans_filter_l,label=>"Convert writes for 017.1 COMP_FLOW:");
      } else {
        for my $rec_ptr1 (@$wr_ch_trans_l) {
            if($verify_parent_index and !defined($rec_ptr1->{parent}->{idx})) {
                die_ERROR("153 ERROR: This transaction does not have parent index: ".trans_str($rec_ptr1));
            }
        }
      }

      # filter the write addresses that does not get t0 read
      $wr_ch_byte_l = [ grep { $read_addr_h{$_->{address}} }  @$wr_ch_byte_l];

      push @$full_wr_ch_byte_l,$wr_ch_byte_l unless $argv{skip_group_ref_mem};

      # assign shash_index to all transactions
      for my $rec_ptr1 (@$wr_ch_byte_l) {
        $rec_ptr1->{shash_index} = $read_addr_h{$rec_ptr1->{address}};
      }

      $wr_ch_byte_l = shrink_trans_l($wr_ch_byte_l);
      push @$full_shrink_wr_ch_byte_l,$wr_ch_byte_l unless $argv{skip_group_ref_mem};
      for my $rec_ptr1 (@$wr_ch_byte_l) {
        $index1+=1;
        my @ch_rec_a;
        my $src_ch_tc = $rec_ptr1->{parent}->{src_ch_tc} or die_ERROR("098 ERROR: ");
        if(!defined($ch_h1{$src_ch_tc})) {
            $ch_h1{$src_ch_tc} = compare_read_byte_stream__create_ch($src_ch_tc);
            $ch_h1{$src_ch_tc}->{attr} |= CH_ATTR_MINE      if $ch_name_l[$src_ch_tc] =~ $mine_src_ch_tc_name;
            $ch_h1{$src_ch_tc}->{attr} |= CH_ATTR_WCIL      if $rec_ptr1->{parent}->{cmd}=~/WCIL/;
            $ch_h1{$src_ch_tc}->{attr} |= CH_ATTR_CXL       if $ch_name_l[$src_ch_tc] =~ /^(MEDIA|GT|IAX)/;
        } else { # Support here a case where no src_ch defined
        }
        $ch_rec_a[OBJ_INDEX] = $index1;
        $ch_rec_a[OBJ_REC] = $rec_ptr1;
        push @{$ch_h1{$src_ch_tc}->{rec_l}},\@ch_rec_a;
      }
    }

    %read_cl_addr_h = ( ); # No need in this hash any more

    # Make sure mcc_preload channel is first
    my @trans_ch_l1;
    my @preload_trans_ch_l1;
    for my $src_ch_tc (sort { $ch_name_l[$a] cmp $ch_name_l[$b] } keys %ch_h1) { 
        if($src_ch_tc == $mcc_preloader_ch_id) {
            push @preload_trans_ch_l1,$ch_h1{$src_ch_tc}; 
        } else {
            push @trans_ch_l1,$ch_h1{$src_ch_tc}; 
        }
    }
    # put all zero preloader in the beginning of mcc_preload channel
    for my $preload_ch_l (@preload_trans_ch_l1) {
        # Create a hash of all addresses that has preload
        my %preload_addr_h;
        for my $rec_ptr (@{$preload_ch_l->{rec_l}}) { 
            # Clean all preloaded addresses from the zero_preload list
            for my $address (get_trans_addresses($rec_ptr->[OBJ_REC])) {
                delete $mcc_zero_preloader_h{$address};
            }
        }
    }

    # Now put all zero preload in th beginning of  the preload channel;
    my @filter_mcc_zero_preloader_l;
    while(my ($address,$rec_ptr) = each(%mcc_zero_preloader_h)) {
        if(defined($rec_ptr)) {
            push @filter_mcc_zero_preloader_l,$rec_ptr;
        }
    }
    %mcc_zero_preloader_h = (); # Free memory
    
    # If there is no preload channel , then create one.
    if(!@preload_trans_ch_l1 and @filter_mcc_zero_preloader_l) {
        my $rec_ptr1 = $filter_mcc_zero_preloader_l[0];
        my $src_ch_tc = $rec_ptr1->{parent}->{src_ch_tc} or die_ERROR("099 ERROR: ");
        if(!defined($ch_h1{$src_ch_tc})) {
            $ch_h1{$src_ch_tc} = compare_read_byte_stream__create_ch($src_ch_tc);
        }
        unshift @preload_trans_ch_l1,$ch_h1{$src_ch_tc};
    }

    @filter_mcc_zero_preloader_l = sort { $a->{address} <=> $b->{address} } @filter_mcc_zero_preloader_l;

    my $shash_index_h = { };
    $debug_shash_index = undef;
    if(!$argv{skip_group_ref_mem}) {
        # group the writes to smaller transactions
        # this will assign shash_index to the grouped wr and will make ref_mem more effcient
        my $grouped_wr_ch_byte_l = group_write_check_trans([@$full_wr_ch_byte_l,\@filter_mcc_zero_preloader_l],$shash_index_h) unless $argv{skip_group_ref_mem};

        if($argv{skip_group_reads}) {
            update_reads_shash_index($trans_l2,$shash_index_h);
        } else {
            $trans_l2 = optimize_reads_shash_index($trans_l2,$shash_index_h);
        }
        optimize_ref_mem_shash_index($full_shrink_wr_ch_byte_l,$shash_index_h) unless $argv{skip_group_ref_mem};
        if(defined($argv{rerun_failure_address})) {
            if(defined(my $debug_shash_index_0 = $shash_index_h->{$argv{rerun_failure_address}})) { $debug_shash_index->{$debug_shash_index_0&0xFFFFFFFF}=1; }
        }
        if(defined($argv{debug_address})) { for my $address (split /[|,]/,$argv{debug_address}) {
            if(defined(my $debug_shash_index_0 = $shash_index_h->{big_hex($address)})) { $debug_shash_index->{$debug_shash_index_0&0xFFFFFFFF}=1; }
        } }
    } else {
        if(defined($argv{rerun_failure_address})) {
            if(defined(my $debug_shash_index_0 = $read_addr_h{$argv{rerun_failure_address}})) { $debug_shash_index->{$debug_shash_index_0&0xFFFFFFFF}=1; }
        }
        if(defined($argv{debug_address})) { for my $address (split /[|,]/,$argv{debug_address}) {
            if(defined(my $debug_shash_index_0 = $read_addr_h{big_hex($address)})) { $debug_shash_index->{$debug_shash_index_0&0xFFFFFFFF}=1; }
        } }
    }
    undef $full_wr_ch_byte_l; undef $full_shrink_wr_ch_byte_l;
    %read_addr_h = ( ); # No need in this hash any more

    my $filter_mcc_zero_preloader_l_ptr = shrink_trans_l(\@filter_mcc_zero_preloader_l);
    optimize_ref_mem_shash_index([$filter_mcc_zero_preloader_l_ptr],$shash_index_h) unless $argv{skip_group_ref_mem};
    undef $shash_index_h;
    my @filter_mcc_zero_preloader_l2 ;
    for (@$filter_mcc_zero_preloader_l_ptr) {
        my @ch_rec_a;
        $ch_rec_a[OBJ_INDEX] = 0;
        $ch_rec_a[OBJ_REC]   = $_;
        push @filter_mcc_zero_preloader_l2, \@ch_rec_a;
    }
    
    unshift @{$preload_trans_ch_l1[0]->{rec_l}},@filter_mcc_zero_preloader_l2;
    @filter_mcc_zero_preloader_l = (); # Free memory
    undef $filter_mcc_zero_preloader_l_ptr;
    $filter_mcc_zero_preloader_l2 = ();

    # Put all preload channels in the beginning of the wr channels list.
    unshift @trans_ch_l1,@preload_trans_ch_l1;
    for(my $i=0; $i<1*@trans_ch_l1 ;$i++) { $trans_ch_l1[$i]->{ch_idx} = $i; }  

    if($debug>=2) {
        print "017.2 COMP_FLOW: Write channel list : total ".(1*@trans_ch_l1)."\n";
        for my $ch_ptr (@trans_ch_l1) {
            print "write_ch1: ch_idx1=$ch_ptr->{ch_idx} name=$ch_name_l[$ch_ptr->{src_ch_tc_key}] trans_count=".(1*@{$ch_ptr->{rec_l}})."\n";
        }
        STDOUT->flush();
    }


    # Initially reset the refmem array
    undef $all_write_refmem_h;
    $all_write_refmem_h->[$smart_hash_index-1] = undef;

    # corelate the MWr
    $index2 = 0;
    if($debug_start_time) {
        while($count<+@$trans_l2) {
            local $rec_ptr1;
            my $rec_ptr2 = $trans_l2->[$index2];
            if($rec_ptr2->{tick_beg}<$debug_start_time) {
                #this is a debug option only
                $count += 1;
                $index2+=1;
            } else { last }
        }
    }
    while($count<+@$trans_l2) {
        local $rec_ptr1;
        my $rec_ptr2 = $trans_l2->[$index2];
        local %field_comperator_l = defined($parms{field_comperator_l}) ? @{$parms{field_comperator_l}} : ();
        my $refmem_rec_l;

        my $match_case_l_ptr = [];

        if($debug>=2 and $e2e_read_compare_count-$last_e2e_read_compare_count>1000000) {
            my $time_str = "";
            if($is_dump_time) { $time_str = "pid=$$ time=".time(); }
            print "Run status: index2=$index2 read_ch_scan_count=$e2e_read_ch_scan_count read_compare_count=$e2e_read_compare_count read_retry_count=$e2e_read_retry_count refmem_update_count=$e2e_refmem_update_count refmem_reverse_count=$e2e_refmem_reverse_count$time_str\n";
            STDOUT->flush();
            $last_e2e_read_compare_count = $e2e_read_compare_count;
        }

        my ($err_code,$log_str,$err_str,$is_match_previous_write);

        if(!(++$time_cnt&0x1FF)) {
            script_timeout_chk(); if($script_timeout) { return; }
        }

        if(defined($last_RDCURR_state) and $last_RDCURR_state->{posibility} and ($trans_l2->[$last_RDCURR_state->{index2}]->{parent}->{idx}!= $rec_ptr2->{parent}->{idx} or ($trans_l2->[$last_RDCURR_state->{index2}]->{address}>>6) != ($rec_ptr2->{address}>>6))) {
            # restore the refmem and write list after the finish of a RDCURR
            reverse_all_write_refmem(\@trans_ch_l1,$all_write_refmem_h,$all_write_order_l,$last_RDCURR_state->{index2},$index2,1); #FIXME: Need to recalculae only channels that channges thier inder;`
            for my $ch_ptr (@trans_ch_l1) {
                $ch_ptr->{rec_l_index} = $last_RDCURR_state->{posibility}->{save_src_ch_tc_point_h}->{$ch_ptr->{src_ch_tc_key}}->{rec_l_index};
            }
            # reset the last read curr state to enable next RDCURR to be captured
            $last_RDCURR_state = undef;
        }

        # Add to refmem all transactions that finished before this $rec_ptr2 read transaction
        for my $ch_ptr (@trans_ch_l1) {
            #my $write_refmem_h = $ch_ptr->{write_refmem_h};
            my $top_index1 = 1*@{$ch_ptr->{rec_l}};
            my $try_index1=$ch_ptr->{rec_l_index};
            my $new_index1;
            for(; $try_index1<=$top_index1 ; $try_index1+=1)  {
                my $address2 = $rec_ptr2->{address};

                # If no address match, try to match with previous write in write_refmem_h
                if($try_index1<$top_index1) {
                    $rec_ptr1 = $ch_ptr->{rec_l}->[$try_index1]->[OBJ_REC];

                    # Check if we can return this:
                    if(defined($rec_ptr2->{tick_beg}) && defined($rec_ptr1->{tick_end})) {
                        if($rec_ptr2->{tick_beg}>$rec_ptr1->{tick_end}) {
                            if(($ch_ptr->{attr}& CH_ATTR_CXL) ) {
                                # For CXL channels the GO is not global (because it can be delated in NOC
                                # i never allow this transaction to get to refmem because it does not have global go
                                # but if it is order that top-refmem-trans I will let it overite it 
                                $refmem_rec_l = get_top_refmem($all_write_refmem_h->[$rec_ptr1->{shash_index}&0xFFFFFFFF]);
                                if(defined($refmem_rec_l) and (
                                        defined($rec_ptr1->{tick_mc}) and defined($refmem_rec_l->[REFMEM_REC]->{tick_mc}) and ($refmem_rec_l->[REFMEM_REC]->{tick_mc} > $rec_ptr1->{tick_mc}) 
                                    or  defined($rec_ptr1->{tick_mc}) and ($refmem_rec_l->[REFMEM_REC]->{tick_beg} > $rec_ptr1->{tick_mc}) 
                                    ) ) {
                                    print "COMP_FLOW: continue beyond this write: ".trans_str($rec_ptr1)."\n" if $debug>=8;
                                    # if the refmem has a newer write that this Write, then let it overite it.
                                } else {
                                    last; 
                                }
                            }
                            if(!defined($rec_ptr1->{tick_mc}) and defined($rec_ptr1->{attr}) and $rec_ptr1->{attr}& REC_ATTR_WCIL ) {
                                # WCIL from CCF does not have tick_mc so we can not commit them in this way.
                                $refmem_rec_l = get_top_refmem($all_write_refmem_h->[$rec_ptr1->{shash_index}&0xFFFFFFFF]);
                                if(defined($refmem_rec_l) and ($refmem_rec_l->[REFMEM_REC]->{tick_beg} > $rec_ptr1->{tick_end})) {
                                    # if the refmem has a newer write that this WCIL, then let it overite it.
                                } else {
                                    last; 
                                }
                            }
                            $new_index1 = $try_index1;
                        } else {
                            last;
                        }
                    }
                }
            }
            if(defined($new_index1) && $ch_ptr->{rec_l_index} < $new_index1+1) {
                if(defined($debug_shash_index)) {
                    print "EYAL5: Add refmem these finished writes before : ch_idx1=$ch_ptr->{ch_idx} index1=$new_index1 index2=$index2 beg=$rec_ptr2->{tick_beg}\n";
                }
                push @{$all_write_order_l->[1+$index2]->[0]},$ch_ptr->{ch_idx},$new_index1+1,undef,$ch_ptr->{write_refmem_h_index1}; # recording only the first index in the whole parent record (of parend_idx)
                $ch_ptr->{rec_l_index} = $new_index1+1;
                update_write_refmem($all_write_refmem_h,$ch_ptr,$new_index1+1,$index2-1,undef,0);
            }
        }

        my $cmd2=$rec_ptr2->{parent}->{cmd};
        if(($cmd2 eq "RDCURR" or $cmd2 eq "PRD" or $cmd2 eq "ARADDR" or $is_pcie_order)
            and (!defined($last_RDCURR_state) or $trans_l2->[$last_RDCURR_state->{index2}]->{parent}->{idx}!= $rec_ptr2->{parent}->{idx} or (($trans_l2->[$last_RDCURR_state->{index2}]->{address})>>6)!=($rec_ptr2->{address}>>6))) {
            #when finishing a read curr, we need to restore the write pointers
            {
                my %posibility_h = (
                    index2 => $index2,
                    count  => $count,
                    save_src_ch_tc_point_h => {},
                );
                for my $ch_ptr (@trans_ch_l1) {
                    $posibility_h{save_src_ch_tc_point_h}->{$ch_ptr->{src_ch_tc_key}}->{rec_l_index} = $ch_ptr->{rec_l_index};
                }
                $last_RDCURR_state = { parent_index2 => $rec_ptr2->{parent}->{idx},
                    index2   => $index2,
                    address2   => $rec_ptr2->{address},
                    posibility => \%posibility_h,
                };
            }
        }

        $refmem_rec_l = get_top_refmem($all_write_refmem_h->[$rec_ptr2->{shash_index}&0xFFFFFFFF]);
        if(defined($refmem_rec_l) and rec_2_refmem_cmp($rec_ptr2,$refmem_rec_l)) {
            ($err_code,$log_str,$err_str) = (0,undef,"");
            if($debug>=3) { 
                if($argv{split_reads_dump}) {
                    my $i; my $data; $address2 = $rec_ptr2->{address}; my $i_max = length($rec_ptr2->{data});
                    for($i=0; $i<$i_max and $data = substr($rec_ptr2->{data},-2-$i,2) ; $address2+=1, $i+=2) {
                        $log_str .= "match previous write address=".addr_str($address2)." data=$data ch1=$ch_name_l[$refmem_rec_l->[0]->{parent}->{src_ch_tc}] $refmem_rec_l->[0]->{parent}->{line} index2=$index2 rec2 src_ch_tc=$ch_name_l[$rec_ptr2->{parent}->{src_ch_tc}]  $rec_ptr2->{parent}->{line}\n";
                    }
                } else {
                    $log_str = "match previous write address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data} ch1=$ch_name_l[$refmem_rec_l->[0]->{parent}->{src_ch_tc}] $refmem_rec_l->[0]->{parent}->{line} index2=$index2 rec2 src_ch_tc=$ch_name_l[$rec_ptr2->{parent}->{src_ch_tc}]  $rec_ptr2->{parent}->{line}\n";
                }
            }
            my %match_case_h = (
                log_str => $log_str,
                is_match_previous_write => 1,
            );
            push @$match_case_l_ptr,\%match_case_h;
            print "Got possibble index2=$index2 address=".addr_str($rec_ptr2->{address})." matching previous write\n" if($debug>=8);
        }

        # Try to find a write transaction in all channels that matches the $rec_ptr2 read
        for my $ch_ptr (@trans_ch_l1) {
            push @$match_case_l_ptr,find_byte_match_in_ch($trans_l2,$ch_ptr,$rec_ptr2,$index2,undef,$trans_l2);
        }

        my $is_match_again = 1;
        while($is_match_again==1) { # Matching loop
            if(1<=@$match_case_l_ptr) {
                my $match_case_ptr = shift @$match_case_l_ptr;

                print $match_case_ptr->{log_str} if($debug>=3); 
                $err_code = 0;
                if(1<=@$match_case_l_ptr) {
                    # If there are move possible match - save this compare point for future re-compare in case of future mismatch
                    my %posibility_h = (
                        match_case_l => $match_case_l_ptr , ### \@retry_match_case_l_ptr,
                        index2 => $index2,
                        count  => $count,
                    );
                    $posibility_h{last_RDCURR_state} = $last_RDCURR_state if defined($last_RDCURR_state);
                    for my $ch_ptr (@trans_ch_l1) {
                        $posibility_h{save_src_ch_tc_point_h}->{$ch_ptr->{src_ch_tc_key}}->{rec_l_index} = $ch_ptr->{rec_l_index};
                    }
                    push @recompare_posibilities_l,\%posibility_h;
                }
                my $save_rec_l_index_for_revert;
                # Setup the first matching case and continue the compare next transaction in $treas_l2
                if(!$match_case_ptr->{is_match_previous_write}) {
                    # Record that this write was accepted now into the refmem;
                    my $ch_ptr = $match_case_ptr->{ch_ptr};
                    my $index1 = $match_case_ptr->{index1};
                    $rec_ptr1 = $ch_ptr->{rec_l}->[$index1]->[OBJ_REC];
                    $rec_ptr2 = $trans_l2->[$index2];
                    my $parent_idx = $rec_ptr1->{parent}->{idx};
                    my $src_ch_tc_1= $rec_ptr1->{parent}->{src_ch_tc};
                    my $address1 = $ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{address};
                    my $address1_match = ($address1>>6);
                    my $override_index1 = $index1;
                    my $top_index1 = 1*@{$ch_ptr->{rec_l}};
                    {
                       if(defined($debug_shash_index)) {
                           print "EYAL3: Add all_write_order_l : index2=$index2 index1=$index1 ch=$ch_name_l[$ch_ptr->{src_ch_tc_key}]\n";
                       }
                       while($index1<$top_index1 and $ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{parent}->{idx}==$parent_idx
                               and (($ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{address})>>6) <= $address1_match  # Only commit antil the matching cache line address
                           ) {
                           $index1++;
                       }
                       if($is_core_idi_reads && ($ch_ptr->{attr} & CH_ATTR_MINE)) {
                           # In case the writes in the same channel of the reads
                           # them commits all write that got GO before $rec_ptr2 read was sent
                           # Also commit WCIL that got FAST GO before $rec_ptr2 read was sent
                           while($index1<$top_index1
                                       # and ($ch_ptr->{attr} & CH_ATTR_WCIL)
                                       and defined($ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{tick_go})
                                   and ($ch_ptr->{rec_l}->[$index1]->[OBJ_REC]->{tick_go}) <= $rec_ptr2->{tick_beg}
                               ) {
                               print "COMP_FLOW: continue to this write: ".trans_str($ch_ptr->{rec_l}->[$index1]->[OBJ_REC])."\n" if $debug>=8;
                               $index1++;
                           }
                       }
                       $save_rec_l_index_for_revert = $ch_ptr->{rec_l_index};
                       push @{$all_write_order_l->[1+$index2]->[1]},$ch_ptr->{ch_idx},$index1,$override_index1,$ch_ptr->{write_refmem_h_index1}; # recording only the first index in the whole parent record (of parend_idx)
                       $ch_ptr->{rec_l_index} = $index1;
                       update_write_refmem($all_write_refmem_h,$ch_ptr,$index1,$index2,undef,1); ## $override_index1);
                       # Need to compare to previous accept in the same CL
    
                       my $revert_index2;
                       my $next_posibility;
    
                       # Check that after the update_write_refmem we still have our commited write at top of mem.
                       my $tmp_top_refmem = get_top_refmem($all_write_refmem_h->[$trans_l2->[$index2]->{shash_index}&0xFFFFFFFF]);
                       if($tmp_top_refmem->[0]->{parent}->{idx}!=$parent_idx) {
                           $revert_index2 = $index2; # Must revert !!
                           if($debug>=5) {
                               print "Bad match of read address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data} rec2=$rec_ptr2->{parent}->{line} "
                               . "with write ch=$ch_name_l[$rec_ptr1->{parent}->{src_ch_tc}] $rec_ptr1->{parent}->{line} "
                               . "Because it is overwritten by write ch=$ch_name_l[$tmp_top_refmem->[0]->{parent}->{src_ch_tc}] $tmp_top_refmem->[0]->{parent}->{line}\n";
                           }
                       }
    
                       my $parent_idx2 = $trans_l2->[$index2]->{parent}->{idx};
                       if(!$skip_CL_recheck && !defined($revert_index2)) {
    
                           my $rechk_index1 = $match_case_ptr->{index1}-1;
                           for(my $rechk_index2 = $index2-1; $rechk_index2>=0 ; $rechk_index2-=1) {
                               my $rechk_rec_ptr2 = $trans_l2->[$rechk_index2];
                               last unless $parent_idx2==$rechk_rec_ptr2->{parent}->{idx}; # We are in the same read
                               my $address2 = $rechk_rec_ptr2->{address};
                               last unless ($address2>>6) == $address1_match; # Check that we are still in the same CL
                               my $rechk_rec_ptr1;
                               while($rechk_index1>=0) {
                                   my $tmp_rec_ptr1 = $ch_ptr->{rec_l}->[$rechk_index1]->[OBJ_REC];
                                   last unless $tmp_rec_ptr1->{parent}->{idx}==$parent_idx;
                                   my $addr1 = $tmp_rec_ptr1->{address};
                                   if($addr1==$address2) {
                                       # Found that we have a write from the same CL and the match address. It's in $rechk_rec_ptr1. Next will compare it to top refmem
                                       $rechk_rec_ptr1 = $tmp_rec_ptr1;
                                       last;
                                   } elsif($addr1<$address2) {
                                       last;
                                   }
                                   $rechk_index1 -= 1;
                               }
                               my $top_refmem = get_top_refmem($all_write_refmem_h->[$rechk_rec_ptr2->{shash_index}&0xFFFFFFFF]);
                               my $top_wr_rec = $top_refmem->[0];
                               if(!defined($top_wr_rec)) {
                                   print_ERROR("057 ERROR: Can not find ref_mem entry for address ".addr_str($addr1)."\n");
                                   $exit_code=1;
                                   return;
                               } elsif(defined($rechk_rec_ptr1)) {
                                   if(!($parent_idx==$top_wr_rec->{parent}->{idx} && $src_ch_tc_1 == $top_wr_rec->{parent}->{src_ch_tc})# if top refmem is not out matched write
                                           and does_it_write_at_addr($top_wr_rec,$address1,$top_refmem->[2],$ch_h1{$top_wr_rec->{parent}->{src_ch_tc}})
                                           ) {
                                       $revert_index2 = $rechk_index2; # Need to revert!!!!
                                       last;
                                   }
                               }
    
                               if(!rec_2_refmem_cmp($rechk_rec_ptr2,$top_refmem)) { # Check that we we still have the expected data
                                   $revert_index2 = $rechk_index2;
                                   last;
                               }
                           }
                       }
    
                       if(defined($revert_index2) && !defined($next_posibility)) {
                           #So we decided to revert to index2 = $revert_index2
                           ##$all_write_order_l->[$index2]->[1] = undef;
                           $do_recalculate_all_write_refmem = $index2;
                           print "Due to commit of read address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data} rec2=$rec_ptr2->{parent}->{line}\nRevert to another possibility. Returning to index2=$index2\n" if $debug>=5;
                           $ch_ptr->{rec_l_index} = $save_rec_l_index_for_revert;
                           $e2e_read_retry_count += 1;
                           $is_match_again = 1; # Got to remap
    
                           # Now recalculate refmem to previous case
                           if(defined($do_recalculate_all_write_refmem)) {
                               if($use_refmem_recalc) {
                                   $all_write_order_l->[1+$do_recalculate_all_write_refmem]->[1] = undef;
                                   undef $all_write_refmem_h;
                                   $all_write_refmem_h = recalculate_all_write_refmem(\@trans_ch_l1,$all_write_order_l,$index2); #FIXME: Need to recalculae only channels that channges thier inder;`
                                   $do_recalculate_all_write_refmem = undef;
                               } else {
                                   reverse_all_write_refmem(\@trans_ch_l1,$all_write_refmem_h,$all_write_order_l,$index2,$do_recalculate_all_write_refmem,0); #FIXME: Need to recalculae only channels that channges thier inder;`
                                   $do_recalculate_all_write_refmem = undef;
                               }
                           }
    
                           if(!(++$time_cnt&0x1FF)) {
                               script_timeout_chk(); if($script_timeout) { return; }
                           }
                       } else {
                           if(defined($revert_index2)) {
                               $is_match_again = 1; # Cancel the last match, and search for another match on.
                           } else {
                               $is_match_again = 0;
                           }
                       }
                   }

                } else {
                    if($do_recalculate_all_write_refmem) { die_ERROR("100 ERROR: FATAL Can not take a retry that match previous memory!"); }
                $is_match_again = 0;
                }
            } elsif(0==@$match_case_l_ptr) {
                my $posibility_h_ptr = pop @recompare_posibilities_l;
                if(defined($posibility_h_ptr) 
                        and defined($posibility_h_ptr->{index2})
                        and ($trans_l2->[$index2]->{tick_beg}<=$trans_l2->[$posibility_h_ptr->{index2}]->{tick_end} # No point to return to an earlier transaction than that.
                            or should_I_got_back($trans_l2->[$index2]->{tick_beg},$posibility_h_ptr))
                        ) {
                    # Clean the $all_write_order_l until the new $index2
                    $do_recalculate_all_write_refmem = $index2;
                    ##for(my $idx = $posibility_h_ptr->{index2}+1 ; $idx<=$index2 ; $idx++) { $all_write_order_l->[$idx] = undef; }; # FIXME: I think that this can be remove. I inly put it to be in the safe side
                    $index2 = $posibility_h_ptr->{index2};
                    $count  = $posibility_h_ptr->{count};
                    $last_RDCURR_state = $posibility_h_ptr->{last_RDCURR_state};
                    for my $ch_ptr (@trans_ch_l1) {
                        $ch_ptr->{rec_l_index} = $posibility_h_ptr->{save_src_ch_tc_point_h}->{$ch_ptr->{src_ch_tc_key}}->{rec_l_index};
                    }
                    ##$all_write_order_l->[$index2]->[1] = undef;
                    $match_case_l_ptr = $posibility_h_ptr->{match_case_l};
                    print "Mismatch on read address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data} rec2=$rec_ptr2->{parent}->{line}\nbut I am trying another possibility. Returning to index2=$index2\n" if $debug>=5;
                    $rec_ptr2 = $trans_l2->[$index2];
                    $e2e_read_retry_count += 1;
                    $is_match_again = 1; # Got to remap

                    # Now recalculate refmem to drop the previous case
                    if(defined($do_recalculate_all_write_refmem)) {
                        if($use_refmem_recalc) {
                            for(my $idx = $posibility_h_ptr->{index2}+1 ; $idx<=$do_recalculate_all_write_refmem ; $idx++) { $all_write_order_l->[1+$idx] = undef; }; # FIXME: I think that this can be remove. I inly put it to be in the safe side
                            $all_write_order_l->[1+$index2]->[1] = undef;
                            undef $all_write_refmem_h;
                            $all_write_refmem_h = recalculate_all_write_refmem(\@trans_ch_l1,$all_write_order_l,$index2+1); #FIXME: Need to recalculae only channels that channges thier inder;`
                            $do_recalculate_all_write_refmem = undef;
                        } else {
                            reverse_all_write_refmem(\@trans_ch_l1,$all_write_refmem_h,$all_write_order_l,$index2,$do_recalculate_all_write_refmem,0); #FIXME: Need to recalculae only channels that channges thier inder;`
                            $do_recalculate_all_write_refmem = undef;
                        }
                    }

                    if(!(++$time_cnt&0x1FF)) {
                        script_timeout_chk(); if($script_timeout) { return; }
                    }
                } else {

                    my $dump_mismatch_str;
                    # Dump compare error from all channles
                    for my $ch_ptr (@trans_ch_l1) {
                        if($ch_ptr->{err_code}) {
                            $dump_mismatch_str .= "mismatch in src_ch_tc=".$ch_name_l[$ch_ptr->{src_ch_tc_key}]." index2=$index2 : ".$ch_ptr->{err_str}."\n";
                        }
                    }

                    if($dump_mismatch_str) {
                        if(!$log_err_data->{rec}) { $log_err_data->{rec} = $rec_ptr2; }
                        print_ERROR("035 ERROR in comparing all channels for index2=$index2 address=".addr_str($rec_ptr2->{address})." data=$rec_ptr2->{data}. Below I list the mismatched of ever channel. You probably need to review them all and see why there is no match with the correct channel.\n");
                        print $dump_mismatch_str;
                    } else {
                        print_ERROR("036 ERROR there is transaction #$count in trans_l2 but no transaction in trans_l1. rec_ptr2: ".trans_str($rec_ptr2)."\n");
                    }
                    $is_match_again = 2; # exit loop
                    $exit_code = 1;
                }
            } else {
                 die_ERROR("037 ERROR: Bad match case. Never suppose to get to here.");
            }
         
            if(!$is_match_again) {
                $count += 1;
                $index2+=1;
                undef $all_write_order_l->[1+$index2];
            }
        } # Matching loop
        if($is_match_again==2) { 
            last; # I got error. Not comparing any more
        }

        $e2e_read_ch_scan_count+=1; # This count the performance of the algorith.
    }
    print "  Compared $count transactions\n" if $debug>=1;

    if(!+@{$trans_l1} and $parms{fail_count_zero}) {
        print_ERROR(sprintf("038 ERROR: list sizes to compare don't match - %d != %d\n",@{$trans_l1}*1,@{$trans_l2}*1));
        $exit_code = 1;
    }
}

sub filter_slfsnp_bad_and_ACF_IDI(@) {
    # exclude_func_l
    # CSME Can access almost every region
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 1;
    if(defined($rec_ptr->{slfsnp_bad}) && $rec_ptr->{slfsnp_bad} or $rec_ptr->{canceled}) {
        return 0;
    }
    if($skip_ACF_IDI_chk and $ch_name_l[$rec_ptr->{src_ch_tc}]=~/ACF_IDI/) {
        return 0;
    }
    return 1;
}

sub filter_WRC_IDI(@) {
    # exclude_func_l
    # CSME Can access almost every region
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    if($rec_ptr->{Unit}=~/^WRC_IDI/ && $rec_ptr->{PID}=~/IOP_CII/) {
        return 1;
    }
    return 0;
}

sub filter_not_WRC_IDI(@) {
    # exclude_func_l
    # CSME Can access almost every region
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    if($rec_ptr->{Unit}=~/^WRC_IDI/) {
        return 0;
    }
    return 1;
}

sub filter_WRC_psf_vc($$) {
    my ($rec_ptr,$VC_h) = @_;
    if($to_WRC_VC_h->{$VC_h->{$rec_ptr->{vc}}}) {
        return 1;
    }
    return 0;
}

sub filter_WRC_psf_vc_func(@) {
    my %parms = @_;
    return filter_WRC_psf_vc($parms{rec_ptr},$parms{VC_h}) ^ $parms{is_not};
}

sub filter_CSME_trans(@) {
    # exclude_func_l
    # CSME Can access almost every region
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;

    if(hex($rec_ptr->{sai}) == $CSME_SAI && ($rec_ptr->{rs} == 3)) {
        return 1;
    }
    return 0;
}

sub filter_IOP_IMR_RS0_trans(@) {
    # exclude_func_l
    # CSME Can access almost every region
    # if(filter_CSME_trans(@_)) { return 1; }
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;

    for my $range (@IMR_exclude_range_l) {
        if(is_addr_in_range(($rec_ptr->{address}),$range,$rec_ptr->{tick_beg})) {
            if($rec_ptr->{rs} == 0) {
                if($range->{IMR_en}) { return 1; }
                if($IOP_IMR_RS0_EN_val & (1<<$range->{IMR_i})) { return 1; }
                else { return 0; }
            } elsif($rec_ptr->{rs} == 3) {
                my $sai6 = $convert_8bit_sai_to_6bit{hex($rec_ptr->{sai})};
                my $pass = 0;
                my $cmd = defined($rec_ptr->{parent}) ? $rec_ptr->{parent}->{cmd} : $rec_ptr->{cmd};
                if($cmd=~/MWr/i) {
                    $pass = (($range->{WAC}>>$sai6)&1);
                } elsif($cmd=~/MRd/i) {
                    $pass = (($range->{RAC}>>$sai6)&1);
                }
                return $pass;
            }
        }
    }
    if($rec_ptr->{rs} == 0) {
        return 1;
    } elsif($rec_ptr->{rs} == 3) {
        return 0;
    }
    return 0;
}

sub filter_UR_trans(@) {
    # exclude_func_l
    # CSME Can access almost every region
    my %parms = @_;
    my $rec_ptr = $parms{rec_ptr} or return 0;
    if($rec_ptr->{is_UR}) {
        return 0;
    }
    return 1;
}

sub filter_pcie_ns_read_trans(@) {
    my $trans_l = shift;
    my $out_trans_l = [];

    for my $rec_ptr (@$trans_l) {
        my $addr6 = ($rec_ptr->{address}>>6);
        my $is_snoop = ($pch_non_snoop_addr_h{$addr6} or 0);
        # Skip data check for this pcie read if:
        # - This pcie read is ns and there was a idi write to this address.
        # - There was a pcie ns write ands also idi write to this address.
        if($rec_ptr->{parent}->{ns} && ($is_snoop&4) or ($is_snoop&5)) {
        } else {
            push @$out_trans_l , $rec_ptr;
        }
    }

    return $out_trans_l;
}

sub iommu_msi_conv_upstream(@) {
    # Functions Put converted address & data, and also preserve the non-converted address and data
    # So functions let us decide later whether this transaction was converted or not.
    my %parms=@_;
    my $last_src_ch = 0; # invalid channel id
    my $IntTable;
    my $CFIS_mode = 1;

    if(defined($parms{iommu_scbd_h})) {
    } else { return $parms{trans_l}; }

    my $trans_l = $parms{trans_l} or die_ERROR("101 ERROR: ");
    my $beg_addr;
    my $end_addr;

    my $conv_trans_l = [];
    my $count=0;
    # corelate the MWr
    for my $i (0..((+@{$trans_l})-1)) {
        my $rec_ptr = $trans_l->[$i];
        my $addr = ($rec_ptr->{address});
        my $data = big_hex($rec_ptr->{data});
        if($rec_ptr->{src_ch} != $last_src_ch) {
            $last_src_ch = $rec_ptr->{src_ch};
            $IntTable = $parms{iommu_scbd_h}->{$ch_name_l[$last_src_ch]}->{IntTable};
            if(defined($IntTable )) {
                $beg_addr = $IntTable->{beg_addr};
                $end_addr = $IntTable->{end_addr};
            } else {
                undef $beg_addr;
                undef $end_addr;
            }
        }
        if($rec_ptr->{BDF}=~/03da/i) {
            $CFIS_mode*=1;    
        }


        my $EntryAddr;
        $EntryAddr = (get_field($addr,19,5)+(($addr&4)<<13))*16 + $beg_addr if defined($beg_addr) && defined($end_addr);
 
        my $conv_rec_ptr;
        for(keys %$rec_ptr) { $conv_rec_ptr->{$_} = $rec_ptr->{$_} }
        $conv_rec_ptr->{address} = ($conv_rec_ptr->{address});
        $conv_rec_ptr->{skip_conds}->{VTD_IRE} = 1; # Initially, this transaction will be blocked. I might remove it later.
        push @$conv_trans_l,$conv_rec_ptr;

        if($rec_ptr->{length}!=1) { next; }
        if(get_field($addr,4,4)!=1) { 
            if($CFIS_mode) {
            } else { next; }
            undef $conv_rec_ptr->{skip_conds}->{VTD_IRE}; # This transaction will not be block.
            $conv_rec_ptr->{skip_conds}->{VTD_IRE}->{1}->{VTD_EIME} = 1;
            #push @$conv_trans_l,$rec_ptr;
        } else {
            if(get_field($addr,31,20)!=0xFEE) { next; }
            if(get_field($data,31,16)!=0) { next; }
            if(defined($EntryAddr) && $EntryAddr<$end_addr) {
                my $entry = $IntTable->{$EntryAddr};
                if(!defined($entry) || !$entry->{P}) { next }
                my $BDF = big_hex($rec_ptr->{BDF});
                if($entry->{SVT}==1) { 
                    if($entry->{SQ}==0) {
                        if($entry->{SID}!=$DBF) { next }
                    }
                    if($entry->{SQ}==1) {
                        if(($entry->{SID}&0xFFFB)!=($DBF&0xFFFB)) { next }
                    }
                    if($entry->{SQ}==2) {
                        if(($entry->{SID}&0xFFF9)!=($DBF&0xFFF9)) { next }
                    }
                    if($entry->{SQ}==3) {
                        if(($entry->{SID}&0xFFF8)!=($DBF&0xFFF8)) { next }
                    }
                }
                if($entry->{SVT}==2) { 
                    if(get_field($entry->{SID},15,8)>($BDF>>8)) { next }
                    if(get_field($entry->{SID}, 7,0)<($BDF>>8)) { next }
                }
                # Put converted address & data, and also preserve the non-converted address and data
                my $new_data;
                $new_data->{VTD_IRE}->{0} = $conv_rec_ptr->{data};
                $new_data->{VTD_IRE}->{1} = (($entry->{TRG}<<15)|(1<<14)|($entry->{DLV}<<8)|($entry->{VECTOR}));
                $conv_rec_ptr->{data} = $new_data;

                my $new_address;
                $new_address->{VTD_IRE}->{0} = $conv_rec_ptr->{address};
                $new_address->{VTD_IRE}->{1}->{VTD_EIME}->{1} = ((0xFEE00000)|(get_field($entry->{DEST_ID},31,8)<<40)|(get_field($entry->{DEST_ID},7,0)<<12)|($entry->{RDH}<<3)|($entry->{DST}<<2));
                $new_address->{VTD_IRE}->{1}->{VTD_EIME}->{0} = ((0xFEE00000)|($entry->{DEST_ID}<<4)|($entry->{RDH}<<3)|($entry->{DST}<<2));
                $conv_rec_ptr->{address} = $new_address;

                undef $conv_rec_ptr->{skip_conds}->{VTD_IRE}; # This transaction will not be block.

            }
        }
    }

    return $conv_trans_l;
}

sub read_SOC_MC_file($) {
    my $fd;
    my $found_all = 0;
    my $scbd = undef;
    my $mcc_preloader_file_scbd_l = shift;
    if(open_gz(\$fd,"SOC_MC.log",0)) {
        my $addr;
        my $data;
        while(<$fd>) {
            if(index($_,"crypted write_backdoor_mem to addr")>0) {
                if(/decrypted write_backdoor_mem to .*addr=(\w+) .*data=(\w+)/) {
                    if(defined($addr)) {
                        die;
                    } else {
                        $addr = (big_hex($1) & $sys_addr_mask);
                        $data = $2;
                    }
                } elsif(/encrypted write_backdoor_mem to .*addr=(\w+) .*data=(\w+)/) {
                    if(defined($addr)) {
                        if($addr==(big_hex($1) & $sys_addr_mask)) {
                            $scbd->{$addr}->{$2} = $data;
                            $data = undef;
                            $addr = undef;
                        } else {
                            die;
                        }
                    } else {
                        die;
                    }
                }
            }
        }
        close $fd;
    }

    for my $mcc_preloader_file_scbd (@$mcc_preloader_file_scbd_l) {
        next unless is_scbd_exists($mcc_preloader_file_scbd);
        for my $rec_ptr (@{$mcc_preloader_file_scbd->{U}->{all}}) {
            my $enc = $scbd->{$rec_ptr->{address}};
            if($enc and (my $d=$enc->{$rec_ptr->{data}})) {
                $rec_ptr->{data} = $d;
            }
        }
    }

    return $scbd;
}

sub iommu_msi_conv_downstream(@) {
    my %parms=@_;

    my $trans_l = $parms{trans_l} or die_ERROR("102 ERROR: ");

    my $space = $PCIE_CFG_SPACE->{$parms{D}}->{$parms{F}};

    my $VTD_GCMD_REG_addr;
    my $VTD_IRTA_REG_addr;
    my $VTD_PMEN_REG_addr;
    if($space->{VTD_BASE}<=$space->{VTD_LIMIT} && $space->{VTD_BASE_be} && $space->{VTD_LIMIT_be}) {
        $VTD_GCMD_REG_addr = $space->{VTD_BASE} + 0x18;
        $VTD_IRTA_REG_addr = $space->{VTD_BASE} + 0xb8;
        $VTD_PMEN_REG_addr = $space->{VTD_BASE} + 0x64;
    }
    my $VTD_GCMD_REG_val = 0;
    my $VTD_GCMD_REG_new_val = 0;
    my $VTD_PMEN_REG_val = 0;
    my $VTD_PMEN_REG_new_val = 0;
    my $VTD_IRTA_REG_val = 0;
    my $was_VTD_IRE_convert_mode_change = 0;
    my $was_VTD_TE_convert_mode_change = 0;
    my $wait_for_ZLR = 0;

    my $conv_trans_l = [];
    my $count=0;
    # corelate the MWr
    for my $i (0..((+@{$trans_l})-1)) {
        my $rec_ptr = $trans_l->[$i];
        my $addr = ($rec_ptr->{address});

        if($rec_ptr->{direction} eq "D" and $rec_ptr->{cmd}=~/^MWr/) {
            if(defined($VTD_GCMD_REG_addr) && $addr==$VTD_GCMD_REG_addr) {
                $VTD_GCMD_REG_new_val = big_hex($rec_ptr->{data});
                if(get_field($VTD_GCMD_REG_val,25,25)!=get_field($VTD_GCMD_REG_new_val,25,25)) { 
                    $was_VTD_IRE_convert_mode_change = 1;
                    $wait_for_ZLR += 1;
                }
                if(get_field($VTD_GCMD_REG_val,31,31)!=get_field($VTD_GCMD_REG_new_val,31,31)) { 
                    $was_VTD_TE_convert_mode_change = 1;
                    $wait_for_ZLR += 1;
                    $skip_e2e_read_chk = 1; #FIXME: Temporarily disable read check for all tests that do IOMMU.
                }
                next;
            }
            if(defined($VTD_PMEN_REG_addr) && $addr==$VTD_PMEN_REG_addr) {
                $VTD_PMEN_REG_new_val = big_hex($rec_ptr->{data});
                if(get_field($VTD_PMEN_REG_val,31,31)!=get_field($VTD_PMEN_REG_new_val,31,31)) { 
                    $wait_for_ZLR += 1;
                }
                next;
            }
            if(defined($VTD_IRTA_REG_addr) && $addr==$VTD_IRTA_REG_addr) {
                $VTD_IRTA_REG_val = big_hex($rec_ptr->{data});
                next;
            }
        }
        if($rec_ptr->{direction} eq "U" and $rec_ptr->{cmd}=~/^MRd/ && $addr==0xFEE00000) {
            $VTD_GCMD_REG_val = $VTD_GCMD_REG_new_val;   
            if($was_VTD_IRE_convert_mode_change) { $was_VTD_IRE_convert_mode_change++; }
            if($was_VTD_TE_convert_mode_change) { $was_VTD_TE_convert_mode_change++; }
            if(--$wait_for_ZLR<0) {
                print_ERROR("030 ERROR: - Too many ZLR. line: $rec_ptr->{line}");
                $exit_code = 1;
            }
            next;
        }

        if($rec_ptr->{direction} eq "U" and $rec_ptr->{cmd}=~/^MWr/ 
                && is_addr_in_range($addr,$msi_range,undef) && hex($rec_ptr->{BDF})>=0x100
                && hex($rec_ptr->{sai})!=$IOMMU_SAI) {
            if($was_VTD_IRE_convert_mode_change==1) {
                next; # These transaction in the middle of the mode change, I don't if the be converted or not, hence I drop them
            } elsif($was_VTD_IRE_convert_mode_change>=2) {
                $rec_ptr->{modes}->{convert_mode_change} = 1;
                $was_VTD_IRE_convert_mode_change = 0;
            }
            if($was_VTD_TE_convert_mode_change>=2) {
                $was_VTD_TE_convert_mode_change = 0;
            }
            $rec_ptr->{modes}->{VTD_IRE} = get_field($VTD_GCMD_REG_val,25,25);
            $rec_ptr->{modes}->{VTD_EIME} = get_field($VTD_IRTA_REG_val,11,11);
            push @$conv_trans_l,$rec_ptr;
        }

    }

    if($wait_for_ZLR!=0) {
        print_ERROR("031 ERROR: - Too many ZLR. line: $rec_ptr->{line}");
        $exit_code = 1;
    }

    return $conv_trans_l;
}

sub filter_byte_stream_range_and_convert($$) {
    my $trans_l = shift;
    my $range_l = shift;
    my $out_trans_l = [];

    for my $rec_ptr (@$trans_l) {
        for my $range (@$range_l) {
            if(is_addr_in_range(($rec_ptr->{address}),$range->{host},undef)) {
                $rec_ptr->{address} = (($rec_ptr->{address}) - $range->{host}->{BASE} + $range->{guest}->{BASE});
                push @$out_trans_l , $rec_ptr;
                last;
            }
        }
    }

    return $out_trans_l;

}

sub filter_byte_stream_non_snoop($) {
    my $trans_l = shift;
    my $out_trans_l = [];

    for my $rec_ptr (@$trans_l) {
        my $addr = ($rec_ptr->{address});
        if(!($pch_non_snoop_addr_h{$addr>>6}&1)) {
            push @$out_trans_l , $rec_ptr;
        }
    }

    return $out_trans_l;

}

sub filter_canceled_writes($) {
    my $trans_l = shift;
    my $out_trans_l = [];
    for my $wr_l (@$trans_l) {
        my $new_wr_l = [ ];
        for my $rec_ptr (@$wr_l) {
            if(!$rec_ptr->{canceled}) {
                push @$new_wr_l, $rec_ptr;
            }
        }
        push @$out_trans_l , $new_wr_l;;
    }
    return $out_trans_l;
}

sub filter_IMR_and_RS0($) {
    my $trans_l = shift;
    my $out_trans_l = [];

    for my $rec_ptr (@$trans_l) {
        my $addr = ($rec_ptr->{address});
        if(!($pch_non_snoop_addr_h{$addr>>6}&1)) {
            push @$out_trans_l , $rec_ptr;
        }
    }

    return $out_trans_l;

}

sub if_iocce_no_e2e_write_chk {
    $skip_e2e_write_chk=1 unless defined($skip_e2e_write_chk);
    return 0;
}

sub make_FMemWrCompress_data_ZZ($) {
    my ($all_write_byte_stream_l) = @_;
    my $rec_ptr1;

    for my $byte_stream_l (@$all_write_byte_stream_l) {
        for $rec_ptr1 (@$byte_stream_l) {
            if(defined($rec_ptr1->{parent}) and defined($rec_ptr1->{parent}->{cmd}) and $rec_ptr1->{parent}->{cmd} =~ /^F?MemWrCompress/ and ($rec_ptr1->{address}&0x3f)>=0x20 ) {
                $rec_ptr1->{data} = "ZZ";
            }
        }
    }
}

# this function 
sub shrink_trans_l($) {
    my $byte_trans_l = shift;
    my $shrink_trans_l = [ ];
    my $rec_ptr1;
    my $last_parent_idx = -1;
    my $new_rec;
    my $last_addr6 = -1;

    for (my $i=0; $i<=$#$byte_trans_l ; $i++) {
        $rec_ptr1 = $byte_trans_l->[$i];
        if($rec_ptr1->{parent}->{idx}!=$last_parent_idx or ($rec_ptr1->{address}>>6)!=$last_addr6 or ($rec_ptr1->{address}<=$new_rec->{address})) {
            $new_rec = {
                address   => $rec_ptr1->{address},
                data      => $rec_ptr1->{data},
                parent    => $rec_ptr1->{parent},
                tick_beg  => $rec_ptr1->{tick_beg},
                tick_end  => $rec_ptr1->{tick_end},
                tick_go   => $rec_ptr1->{tick_go },
                tick_mc   => $rec_ptr1->{tick_mc },
                join_l    => [$rec_ptr1->{shash_index}&0xFFFFFFFF],
            };
            $new_rec->{tick_mc}  = $rec_ptr1->{tick_mc}  if defined($rec_ptr1->{tick_mc});
            $new_rec->{tick_go}  = $rec_ptr1->{tick_go}  if defined($rec_ptr1->{tick_go});
            $new_rec->{tick_end} = $rec_ptr1->{tick_end} if defined($rec_ptr1->{tick_end});
            $new_rec->{attr}     = $rec_ptr1->{attr}     if defined($rec_ptr1->{attr});
            push @$shrink_trans_l,$new_rec;
        } else {
            my $inc = $rec_ptr1->{address}-$new_rec->{address} - (length($new_rec->{data})>>1);
            $new_rec->{data} = $rec_ptr1->{data} . ("xx" x ($inc)) . $new_rec->{data};
            push @{$new_rec->{join_l}},(($rec_ptr1->{shash_index}&0xFFFFFFFF)+(($rec_ptr1->{address}-$new_rec->{address})<<32));
        }
        #$byte_trans_l->[$i] = undef unless $debug>=8;
        $last_addr6 = ($rec_ptr1->{address}>>6);
        $last_parent_idx = $rec_ptr1->{parent}->{idx};
    } 
    return $shrink_trans_l;
}

sub merge_trans_to_group($group,$rec_ptr1->{parent}) {
    my ($group,$rec_ptr1)  = @_;
    my $addr6 = ($rec_ptr1->{address}>>6);
    my $off = $rec_ptr1->{address} - ($addr6<<6);
}

# group transactions in one CL beggest data chunk which are always accessed together
# I assime that transctions are all one byte data size
sub group_CL_trans($$$) {
    my ($CL_l,$shash_index_ptr,$shash_index_h) = @_;
    my $grouped_trans_h = { };
    my $addr_off_h; my $last_shash_index;
    for my $rec_ptr (@$CL_l) {
        # marks which addresss offsets are uses by which parent transaction
        $addr_off_h->{$rec_ptr->{address}&0x3F}->{$rec_ptr->{parent}->{idx}} = $rec_ptr;
    }
    for my $addr_off (sort {$a <=> $b} (keys %$addr_off_h)) {
        my @parent_idx_l   = (sort {$a<=>$b} (keys %{$addr_off_h->{$addr_off}}));
        my $parent_idx_str = join(",",@parent_idx_l);
        my $new_shash_index;
        for my $idx (@parent_idx_l) {
            my $rec_ptr = $addr_off_h->{$addr_off}->{$idx};
            my $new_rec = ( $grouped_trans_h->{$idx} ? $grouped_trans_h->{$idx}->[-1] : undef );
            if(!defined($new_rec) or $new_rec->{parent_idx_str} ne $parent_idx_str or defined($shash_index_h) && ($last_shash_index&0xFFFFFFFF) != ($new_rec->{shash_index}&0xFFFFFFFF) ) {
                $new_rec = {
                    address   => $rec_ptr->{address},
                    data      => $rec_ptr->{data},
                    parent    => $rec_ptr->{parent},
                    tick_beg  => $rec_ptr->{tick_beg},

                    parent_idx_str => $parent_idx_str,
                };
                if(!defined($new_shash_index)) { $new_shash_index = $$shash_index_ptr; $$shash_index_ptr += 1; }
                $new_rec->{shash_index} = $new_shash_index;
                $new_rec->{tick_mc}  = $rec_ptr->{tick_mc}  if defined($rec_ptr->{tick_mc});
                $new_rec->{tick_go}  = $rec_ptr->{tick_go}  if defined($rec_ptr->{tick_go});
                $new_rec->{tick_end} = $rec_ptr->{tick_end} if defined($rec_ptr->{tick_end});
                $new_rec->{attr}     = $rec_ptr->{attr}     if defined($rec_ptr->{attr});
                push @{$grouped_trans_h->{$idx}},$new_rec;
            } else {
                my $inc = $rec_ptr->{address}-$new_rec->{address} - (length($new_rec->{data})>>1);
                $new_rec->{data} = $rec_ptr->{data} . ("xx" x ($inc)) . $new_rec->{data};
            }
            $shash_index_h->{$rec_ptr->{address}} = $last_shash_index = ($new_rec->{shash_index} + (($rec_ptr->{address}-$new_rec->{address})<<32)) if defined($shash_index_h);
        } # for(@parent_idx_l)
    } # for my $addr_off

    # clean not needed variables
    for my $idx (keys %{$grouped_trans_h}) {
        for my $rec_ptr (@{$grouped_trans_h->{$idx}}) {
            delete $rec_ptr->{parent_idx_str};
            delete $rec_ptr->{shash_idx};
        }
    }
    return $grouped_trans_h;
}

sub join_to_hash($$) {
    my ($joined_h,$h) = @_;
    for my $k (keys %$h) {
        if(defined($joined_h->{$k})) {
            die_ERROR("188 ERROR: Joined hash already has this key $k");
        } else {
            if(defined($h->{$k})) {
                $joined_h->{$k} = $h->{$k};
            } else {
                die_ERROR("189 ERROR: This key is not defined $k");
            }
        }
    }
}

# this function 
sub group_trans($$) {
    my $stream_trans_l = shift;
    my $shash_index_h  = shift; # in case i want to save the shash_index for ref_mem use
    my $group_CL_h;
    my $shrink_trans_l = [ ];
    my $last_parent_idx = -1;
    my $shash_index = 1;
    my $last_addr6 = -1;
    my $parent_idx_h = { };

    # group all transactions per CL.
    for my $byte_trans_l(@$stream_trans_l) { 
        for (my $i=0; $i<=$#$byte_trans_l ; $i++) {
            my $rec_ptr = $byte_trans_l->[$i];
            my $addr6 = ($rec_ptr->{address}>>6);
            push @{$group_CL_h->{$addr6}} , $rec_ptr;
        } 
    }

    # take each CL and group it to biggest data elements
    for my $addr6 (sort { $a <=> $b } (keys %$group_CL_h)) {
        # for each CL sort the addresses
        my $CL_l = $group_CL_h->{$addr6};
        $CL_l = [ sort { $a->{address} <=> $b->{address} } @$CL_l];

        my $grouped_trans_h = group_CL_trans($CL_l,\$shash_index,$shash_index_h);

        join_to_hash($parent_idx_h,$grouped_trans_h);
    }

    # returns a grouped transactions for each parent idx
    return $parent_idx_h;
}

sub group_write_check_trans($$) {
    my $in_write_byte_l  = shift;
    my $shash_index_h  = shift; # in case i want to save the shash_index for ref_mem use
    my $out_grouped_write_byte_l = [ ];

    my $parent_idx_h = group_trans($in_write_byte_l,$shash_index_h);

    for my $trans_l (@$in_write_byte_l) {
        my $grouped_byte_l = [ ];
        for my $rec_ptr (@$trans_l) {
            my $grouped_l = $parent_idx_h->{$rec_ptr->{parent}->{idx}};
            if($grouped_l and $#$grouped_l>=0) {
                # push the group only if this $rec_ptr address is the first in the group
                push @$grouped_byte_l , @$grouped_l if($rec_ptr->{address}==$grouped_l->[0]->{address});
            } else {
                die_ERROR("190 ERROR: Bad transaction group.");
            }
        }
        push @$out_grouped_write_byte_l , $grouped_byte_l;
    }
    
    return $out_grouped_write_byte_l;
}

# Make the join_l of the transactios, be grouped to a biggest group that has the sane shash_index
sub optimize_ref_mem_shash_index($$) {
    my $in_write_byte_l  = shift;
    my $shash_index_h  = shift; # in case i want to save the shash_index for ref_mem use
    my $rec_offset;
    my $shash_index;
    my $last_shash_index = -10;
    my $new_shash_index;
    my $address1,$last_address1;

    for my $trans_l (@$in_write_byte_l) {
        for my $rec_ptr1 (@$trans_l) {
            my @new_join_l = (); $last_shash_index = -10;
            for($rec_offset = 0 ; $rec_offset<=$#{$rec_ptr1->{join_l}} ; $rec_offset+=1) {
                $shash_index  = $rec_ptr1->{join_l}->[$rec_offset];
                $address1 = $rec_ptr1->{address} + ($shash_index>>32);

                if(defined($new_shash_index = $shash_index_h->{$address1}&0xFFFFFFFF)) { 
                    if($new_shash_index != $last_shash_index) {
                        $last_shash_index = $new_shash_index;
                        if($#new_join_l>=0) {
                            # update the size of previous shash_index in its word3
                            $new_join_l[-1] |= (( $last_address1-$rec_ptr1->{address} - get_word2($new_join_l[-1]) ) << 48);
                        }
                        # create a new shash_index in the new_join_l and update its start address in ites word2
                        push @new_join_l , $new_shash_index + (($address1 - $rec_ptr1->{address})<<32);
                    }
                    $last_address1 = $address1;
                } else {
                    die_ERROR("192 ERROR: This addresss=".addr_str($address1)." does not have shash_index");
                }
            }
            if($#new_join_l>=0) {
                # update the size of previous shash_index in its word3
                $new_join_l[-1] |= ( $address1-$rec_ptr1->{address} - get_word2($new_join_l[-1]) ) << 48;
            }
            $rec_ptr1->{join_l} = \@new_join_l;
        }
    }
    
}

# Make the join_l of the transactios, be grouped to a biggest group that has the sane shash_index
sub update_reads_shash_index($$) {
    my ($trans_l2,$shash_index_h) = @_;
    # now assigh the optimized shash_index to the read transactions
    for my $rec_ptr2 (@$trans_l2) { # FIXME: Maybe not need all this preload to zero.
        my $address = $rec_ptr2->{address};
        # This creates a smart hash that uses actually $write_refmem_h as array instead of a hash. 
        # This will make run faster, since we are not using hash when running the heavby e2e_read_chk that sman all wr channels agains alll reads
        if(defined(my $shash_index = $shash_index_h->{$rec_ptr2->{address}})) { 
            $rec_ptr2->{shash_index} = $shash_index;
        } else {
            die_ERROR("193 ERROR: This addresss=".addr_str($rec_ptr2->{address})." does not have shash_index");
        }
    }
}

# Make the join_l of the transactios, be grouped to a biggest group that has the sane shash_index
sub optimize_reads_shash_index($$) {
    my $trans_l2  = shift;
    my $shash_index_h  = shift; # in case i want to save the shash_index for ref_mem use
    my $new_trans_l2  = [ ];
    my $shash_index;
    my $last_shash_index = -10;
    my $new_shash_index;
    my $address1;
    my $joined_rec;

    for my $rec_ptr2 (@$trans_l2) {
        $address1 = $rec_ptr2->{address};
        if(defined($new_shash_index = $shash_index_h->{$address1})) { 
            if(($new_shash_index&0xFFFFFFFF) != $last_shash_index or $joined_rec->{parent}->{idx} != $rec_ptr2->{parent}->{idx} or ($joined_rec->{address}+length($joined_rec->{data})>>1)>$address1) {
                $joined_rec = $rec_ptr2;
                $joined_rec->{shash_index} = $new_shash_index;
                push @$new_trans_l2,$joined_rec;
            } else {
                # pad with "xx" if there is a space
                $joined_rec->{data} = $rec_ptr2->{data} . ("xx" x ($address1 - ($joined_rec->{address}+(length($joined_rec->{data})>>1)))) . $joined_rec->{data};
                # joind the data

            }
            $last_shash_index = $new_shash_index&0xFFFFFFFF;
        } else {
            die_ERROR("194 ERROR: This addresss=".addr_str($address1)." does not have shash_index");
        }
    }
    return $new_trans_l2;
}


if(defined($argv{rerun_failure_log})) {
    rerun_failure_parms($argv{rerun_failure_log});
}

{
    my $fd;
    my $found_all = 0;
    if(open_gz(\$fd,"dumpenv_zebu_submit",0)) {
        while(<$fd>) {
            if(index($_,"STEPPING ")==0 && !defined($ACERUN_STEPPING)) {
                if(/STEPPING\s+==\s+(\S+)/) {
                    $ACERUN_STEPPING = $1;
                }
            }
        }
        close $fd;
    }
}
{
    my $fd;
    my $found_all = 0;
    my $ACERUN_CLUSTER_cbb;
    if(open_gz(\$fd,".trex.env",0)) {

        my @grep_result = `zgrep "^STEPPING=" .trex.env* |cut -d"'" -f2`;
        chomp(@grep_result);
        if(scalar(@grep_result) > 0){
            $ACERUN_STEPPING = $grep_result[0];
        }

        my @grep_result = `zgrep "^DUT=" .trex.env* |cut -d"'" -f2`;
        chomp(@grep_result);
        if(scalar(@grep_result) > 0){
            $ACERUN_CLUSTER_cbb = $grep_result[0];
        }

        close $fd;
    }

    print "stepping1: $ACERUN_STEPPING\n" if $debug>=3; 
    $ACERUN_CLUSTER  = $ACERUN_CLUSTER_cbb if $ACERUN_CLUSTER_cbb and $ACERUN_STEPPING=~/^cbb/;
    print "cluster1: $ACERUN_CLUSTER\n" if $debug>=3;
}

#{
#print "Xs_RES :".e2e_XS::my_xs_IV_function("test1");
#print "\n";
#my $res=1;
#for(1..10) {
#    $res *= e2e_XS::my_xs_function("test1");
#    print "Res=".$res."\n";
#}
#}
#exit;

parse_logbook_log("logbook.log");
print "cluster: $ACERUN_CLUSTER\n" if $debug>=3;

my $fd;
if(open_gz(\$fd,"zeburun.log",0) or open_gz(\$fd,"emurun.log",0)) {
    #if($cpu_proj eq "lnl") {
        $emulation_obj_load_time = 2; # fixme: need to read the it from emurun.log
    #}
    $idi_log_file = "merged_idi.log" if (-e "merged_idi.log") or (-e "merged_idi.log.gz");
    while(<$fd>) {
        if(index($_,"completed loading test image memory")>0 && !$emulation_obj_load_time) {
            if(/^\s*\[\s*(\d+)\s*\].*completed loading test image memory/) {
                 $emulation_obj_load_time = $1*1000;
                 print "emulation_obj_load_time=$emulation_obj_load_time\n" if $debug;
            }
        } elsif(index($_,"All active threads halted, final result ACED")>0) {
            if(/\[\s*(\d+)\s*\].*All active threads halted, final result ACED/) {
                $emulation_tick_eot = $1*1;
            }
        } else {
            next;
        }

        if($emulation_obj_load_time && $emulation_tick_eot) {
            last;
        }
    }
    close $fd;
}

if($emulation_obj_load_time) {
    $skip_psf_Cplt_chk = 1 unless defined($skip_psf_Cplt_chk); # Skip this check in emulation tests.
    my $fd;
    if(open_gz(\$fd,"reset.log",0)) {
        while(<$fd>) {
            if(/xxreset asserted/ and (!/RESET COLD 1/)) {
                print "WARNNING: Skip this emulation test because it has reset in it!";
                exit 0;
            }
        }
        close $fd;
    }

    #if(open_gz(\$fd,"perspec_test.c",0)) {
    #    close $fd;
    #} else {
    #    print "WARNNING: Skip this emulation non-perspec_test!";
    #    exit 0;
    #}

    if((!$emulation_tick_eot) and (not defined $run_in_failed_test)) {
        print "WARNNING: Skip this emulation test because it does not have the final.result.ACED line in zeburun.log file, so it did not finished successfully!";
        exit 0;
    }

    $skip_timeout_err = 1 unless defined($skip_timeout_err); # Emulation test can be very long so skip timeout error
}

if((-f "acerun.log" || -f "acerun.log.gz") and (not $emulation_obj_load_time)) {
    my $fd;
    my $found_all = 0;
    if(open_gz(\$fd,"acerun.log",1)) {
        while(<$fd>) {
            if(index($_,"TESTNAME=")==0 || index($_,"Setting ACE_SIMPLE_TESTNAME=")>=0 && !defined($ACERUN_TESTNAME)) {
                if(/TESTNAME=(\S+)/) {
                    $ACERUN_TESTNAME = $1;
                }
            } elsif(index($_,"MODEL = ")==0 && !defined($ACERUN_SYSTEM_MODEL)) {
                if(/MODEL = (\S+)/) {
                    $ACERUN_SYSTEM_MODEL = $1;
                }
            } elsif(index($_,"# MODEL (DIE) = ")==0 && !defined($ACERUN_SYSTEM_MODEL)) {
                if(/MODEL *\(DIE\)* = (\S+)/) {
                    $ACERUN_SYSTEM_MODEL = $1;
                }
            } elsif(index($_,"TEST_WORK_AREA=")==0 && !defined($ACERUN_TEST_WORK_AREA)) {
                if(/TEST_WORK_AREA=(\S+)/) {
                    $ACERUN_TEST_WORK_AREA = $1;
                }
            } elsif(index($_,"# Setting ACE_MODEL=")==0 && !defined($ACERUN_SYSTEM_MODEL)) {
                if(/MODEL=(\S+)/) {
                    $ACERUN_SYSTEM_MODEL = $1;
                }
            } elsif(index($_,"STEPPING=")==0 && !defined($ACERUN_STEPPING)) {
                if(/STEPPING=(\S+)/) {
                    $ACERUN_STEPPING = $1;
		            print "stepping2: $ACERUN_STEPPING\n" if $debug>=3;
                }
            } elsif(index($_,"time.pl")>=0 and /time\.pl .*\.simv / and !defined($ACERUN_ELABCMD)) {
                #if(/STEPPING=(\S+)/) {
                    $ACERUN_ELABCMD = $_;
                #}
            }
            if(defined($ACERUN_TESTNAME) && defined($ACERUN_SYSTEM_MODEL) && defined($ACERUN_STEPPING) && defined($ACERUN_ELABCMD)) { $found_all=1; last };
        }
    }
    close $fd;
    if($ACERUN_TESTNAME=~/_iommu_queue_inv_test|_iommu_fault_test/) {
        printf("Exit soc_e2e_checker because I am not supporting _iommu_queue_inv_test test\n");
        exit(0);
    } elsif($ACERUN_TESTNAME=~/(soc_imr_ia_gt_access|iommu_pi_test|iop_integ_pi_fault_test|_posted_interrupt_test)/) {
        # Need to implement support for imrgtexcbase & imrgtexclimit registers to support this test (GT is blocked from accessign these registerss.)
        printf("Exit soc_e2e_checker because I am not supporting $1 ADL test\n");
        exit(0);
    } elsif($ACERUN_TESTNAME=~/soc_smr_access/) {
        # Need to implement support for GT being block from accessing TSEG, DPR, PAM, PRMRR, VGA & MMIO
        printf("Exit soc_e2e_checker because I am not supporting soc_smr_access ADL test\n");
        exit(0);
    } elsif($ACERUN_SYSTEM_MODEL=~/^(soc_rtl_cores|memss|idimss|psf0ss)/) {
        printf("Exit soc_e2e_checker because I am not supporting $1 yet test\n");
        exit(0);
    } elsif($ACERUN_SYSTEM_MODEL=~/^(sc_model|chassis_core_model|nc_model)/) {
        # Skipping these ADL models because they have  no OPI or DMI (like memss)
        printf("Exit soc_e2e_checker because I am not supporting $1 yet test\n");
        exit(0);
    } elsif($ACERUN_SYSTEM_MODEL=~/^(chassis_pciessu42_model)/) {
        # FIXME: Skipping this model because they are sending out of range addresses from PEG60.
        printf("Exit soc_e2e_checker because I am not supporting $1 model in adl-b0 yet \n");
        exit(0);
    } elsif(!defined($ACERUN_ELABCMD)) {
        printf("Exit soc_e2e_checker because this test did not do elaboration\n");
        exit(0);
    } elsif($ACERUN_ELABCMD=~/\+SOC_CFG_DFX_TEST=1|\+DFX_TEST\b/) {
        printf("Exit soc_e2e_checker because I am not supporting DFX tests\n");
        exit(0);
    } elsif($ACERUN_ELABCMD=~/SOC_PEP_TEST_CASE=\w*(PEP_Cfg_err|PEP_IORd_err|DIS_UR)/) {
        printf("Exit soc_e2e_checker because I am not supporting PEP err test\n");
        exit(0);
    }
}

    if($ACERUN_STEPPING=~"rkl-p") {
        $cpu_proj = "rkl";
        $cpu_proj_step = "rkl-p";
        $is_scbd_tick_tunings = 1;
        $skip_e2e_pcie_read_chk = 1 unless defined($skip_e2e_pcie_read_chk);
    } elsif($ACERUN_STEPPING=~"rkl-") {
        $cpu_proj = "rkl";
        $cpu_proj_step = "rkl-a";
        $is_scbd_tick_tunings = 1;
        $skip_e2e_pcie_read_chk = 1 unless defined($skip_e2e_pcie_read_chk);
    } elsif($ACERUN_STEPPING=~"och-") {
        $cpu_proj = "och";
        $cpu_proj_step = "och-a";
        $is_scbd_tick_tunings = 1;
        $DID_info_h{$PEP_DID}->{BAR_MASK}  = { 0=>0x7FF_FFFF }; 
    } elsif($ACERUN_STEPPING=~/^(cbb-)/) {
        $cpu_proj = "cbb";
        $sys_addr_mask      = 0x1FFFFFFFFC0;
        $sys_full_addr_mask = 0x1FFFFFFFFFF; # mask ptl MKTME bits
        if($ACERUN_CLUSTER=~/^(ccf)/) {
        } else {
            $idi_log_file = "core_idi.log";
        }
    } elsif($ACERUN_STEPPING=~/^(lnl-.|ptl-.|wcl-)/) {
        $cpu_proj = "lnl";
        if($ACERUN_STEPPING=~/^(ptl-.|wcl-.)/) {
            if($ACERUN_CLUSTER=~/^(idi_bridge|ccf|cbb)/ or $ACERUN_STEPPING=~/^cbb/) {
                # for ccf cte include the mktme bits in the address
                $sys_addr_mask      = 0x3FFFFFFFFFC0;
                $sys_full_addr_mask = 0x3FFFFFFFFFFF; # mask ptl MKTME bits
            } else {
                $sys_addr_mask      = 0x03FFFFFFFFC0;
                $sys_full_addr_mask = 0x03FFFFFFFFFF; # mask ptl MKTME bits
            }
            $sys_addr_mktme_mask = 0x3C0000000000;
            $sys_addr_mktme_bit = 42;
        } else {
            if($ACERUN_CLUSTER=~/^(idi_bridge|ccf|cbb)/ or $ACERUN_STEPPING=~/^cbb/) {
                # for ccf cte include the mktme bits in the address
                $sys_addr_mask      = 0x03FFFFFFFFC0;
                $sys_full_addr_mask = 0x03FFFFFFFFFF; # mask lnl MKTME bits
            } else {
                $sys_addr_mask      = 0x003FFFFFFFC0;
                $sys_full_addr_mask = 0x003FFFFFFFFF; # mask lnl MKTME bits
            }
            $sys_addr_mktme_bit = 38; $sys_addr_mktme_mask = 0x3C000000000;
        }
        if($ACERUN_STEPPING=~/^(lnl-.)/) {
            $argv{skip_PAM_range} = 1 unless defined($argv{skip_PAM_range}) or $emulation_obj_file;
        }
        if($emulation_obj_file) {
            $ICELAND_IDI = "AT_IDI_[0]"; # this is for lnl emulation
        }
        $cpu_proj_step = $1;
        $DID_info_h{$PEP_DID}->{BAR_MASK}  = { 0=>0x7FF_FFFF }; 
        $mcc_preloader_ver = 1;
        $is_e2e_monitor_read = 1;
        $is_e2e_advane_WCIL = 1;
        $skip_psf_long_trans_chk = 1;
        $verify_write_time=1 unless defined $verify_write_time;
        $verify_parent_index = 1; $lnl_mc_tick_update = 1;
        $iocce_mktme_range = {BASE=>0x0010000000000000,LIMIT=>0xFFFFFFFFFFFFFFFF,MASK=>0xFFF0000000000000}; #fixme: temporarily filter all iocce transactions
        push @{$iocce_mktme_range->{pass_func_l}},{func=>\&if_iocce_no_e2e_write_chk};

    } elsif($ACERUN_STEPPING=~/(adl-.)/) {
        $cpu_proj = "adl";
        $cpu_proj_step = $1;
        $is_scbd_tick_tunings = -1;
        $DID_info_h{$PEP_DID}->{BAR_MASK}  = { 0=>0x7FF_FFFF }; 
        $create_cmi_preload = 1 unless defined($create_cmi_preload);
    } elsif($ACERUN_STEPPING && ($ACERUN_STEPPING=~/icl-l/)) {
        # icl-l has bad cmi log, so don;t use it.
        $skip_iop_cmi_log=1;
        $skip_e2e_pcie_read_chk = 1 unless defined($skip_e2e_pcie_read_chk);
        $argv{skip_mmio_chk} = 1 unless defined($argv{skip_mmio_chk}); #FIXME: need to remove it
    } elsif($cpu_proj =~/icl/) {
        $skip_e2e_pcie_read_chk = 1 unless defined($skip_e2e_pcie_read_chk);
        $argv{skip_group_trans_bytes} = 1 unless defined($argv{skip_group_trans_bytes});
        $argv{skip_group_ref_mem} = 1 unless defined($argv{skip_group_ref_mem});
        $argv{skip_mmio_chk} = 1 unless defined($argv{skip_mmio_chk}); #FIXME: need to remove it
    }

    if($ACERUN_STEPPING=~/^(adl-.|icl|och|rkl)/) {
        # old projects did not supported NC writes and read so we need to skip all non-snoop addresses
        $argv{skip_if_non_snoop} = 1 unless defined $argv{skip_if_non_snoop};
        $args{skip_idi_dup_filter} = 1;
        $argv{skip_group_trans_bytes} = 1 unless defined($argv{skip_group_trans_bytes});
        $argv{skip_group_ref_mem} = 1 unless defined($argv{skip_group_ref_mem});
        $argv{skip_wcil_for_dram} = 1; # in these projects the wcil was strictly ordered in dram
        $argv{skip_PAM_range} = 1 unless defined($argv{skip_PAM_range});
    }

    print "STEPPING3=$ACERUN_STEPPING\n" if $debug>=1;

if($cpu_proj_step eq "rkl-a") {
    push_reg_and_tick($PCIE_CFG_SPACE->{0}->{0},"DEVEN",0,0xf1,0); # Set DEVEN default value for rkl-a0
    push_reg_and_tick($PCIE_CFG_SPACE->{0}->{0},"DEVEN",0,0xbb,1); # Set DEVEN default value for rkl-a0
}

if(-f "sequence_trk.log" || -f "sequence_trk.log.gz") {
    if($cpu_proj eq "adl" && my_grep_gz("sequence_trk.log",[" chassis_iommu_pi_test_seq"])==1) {
        print "WARNING: Skip checking because there are unsupport iommu sequence\n" if $debug>=1;
        exit 0;
    }
}

if(my_grep_gz("sequence_trk_uvm.log",[" soc_pm_pkgs_seq"])==1) {
    print "INFO: Skip checking because test has warm reset that might corrupt the data in the cache.\n" if $debug>=1;
    exit 0;
}


if($is_e2e_advane_WCIL) {
    $idi_file_scbd->{MemWr_chs_Atom}      = { count => 0 , prefix=>"_WO" }; #Give Atom transactions merge_ns_write_channels(tick_go)
    $idi_file_scbd->{MemWr_chs_Atom_WCIL} = { count => 0 , prefix=>"_ATWC" }; #Give Atom transactions merge_ns_write_channels(tick_go)
    $idi_file_scbd->{MemWr_chs_CCF_WCIL}  = {                                 #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_0"   => { count => 0 , prefix=>"_IA0WC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_1"   => { count => 0 , prefix=>"_IA1WC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_2"   => { count => 0 , prefix=>"_IA2WC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_3"   => { count => 0 , prefix=>"_IA3WC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "AT_IDI_0"   => { count => 0 , prefix=>"_AT0WC" }, #This is for Atom in emulation
                                  "AT_IDI_4"   => { count => 0 , prefix=>"_AT0WC" }, #This is for Atom in emulation
                                  "AT_IDI_5"   => { count => 0 , prefix=>"_AT0WC" }, #This is for Atom in emulation
                                  "AT_IDI_6"   => { count => 0 , prefix=>"_AT0WC" }, #This is for Atom in emulation
    };
    $idi_file_scbd->{MemRd_chs_Atom}      = { count => 0 , prefix=>"_RO" }; #Give Atom transactions merge_ns_write_channels(tick_go)
    $idi_file_scbd->{MemRd_chs_Atom_WCIL} = { count => 0 , prefix=>"_ATRC" }; #Give Atom transactions merge_ns_write_channels(tick_go)
    $idi_file_scbd->{MemRd_chs_CCF_WCIL}  = {                                 #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_0"   => { count => 0 , prefix=>"_IA0RC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_1"   => { count => 0 , prefix=>"_IA1RC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_2"   => { count => 0 , prefix=>"_IA2RC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "IA_IDI_3"   => { count => 0 , prefix=>"_IA3RC" }, #Give Atom transactions merge_ns_write_channels(tick_go)
                                  "AT_IDI_0"   => { count => 0 , prefix=>"_AT0RC" }, #This is for Atom in emulation
                                  "AT_IDI_4"   => { count => 0 , prefix=>"_AT0RC" }, #This is for Atom in emulation
                                  "AT_IDI_5"   => { count => 0 , prefix=>"_AT0RC" }, #This is for Atom in emulation
                                  "AT_IDI_6"   => { count => 0 , prefix=>"_AT0RC" }, #This is for Atom in emulation
    };
};

##
## Parsing all needed log files.
##

parse_sm_file();

parse_svt_LINK_file() unless $skip_pep_svt_file;

if($cpu_proj eq "lnl") {
    parse_LNL_RAL_file(); # FIXME: This code if not working.
} else {
    parse_ral_mon_file();
}

if($cpu_proj eq "adl") {
    if($PCIE_CFG_SPACE->{0}->{0}->{MAD_SLICE}&0x100) {
        print "Set skip_e2e_write_chk=1 & skip_e2e_read_chk=1 because I am not support Stack mode.\n" if $debug>=1;
        $skip_e2e_write_chk = 1;
        $skip_e2e_read_chk = 1;
    }
}

if($pcu_proj eq "adl") {
    $soc_mc_hash_disable   = 1;
} else {
    cmi_hash_init();
}

if($cpu_proj eq "lnl") {
    if(!$systeminit_file_exist) {
        die_ERROR("117 ERROR: Can not open systeminit.dut_cfg.");
    }
    if(!-e ($push_cmd_file = "systeminit/push_command_file") and !-e ($push_cmd_file = "systeminit/push_command_file.gz") and
	   !-e ($push_cmd_file = "test_cfg/push_command_file") and !-e ($push_cmd_file = "test_cfg/push_command_file.gz")) {
        die_ERROR("118 ERROR: Can not open push_command_file.");
    }
    if(!system("zgrep -q 'SOC_URI_STITCH *:= *0' $systeminit_file")) {
        $skip_uri_chk = 1; # There no URI in this LNL simulation, so skip the URI checking.
    }
    if(!system("zgrep -q 'HBO_MC_STRUCTURE *:= *SINGLE' $systeminit_file")) {
        $sysinit{HBO_SINGLE_MC} = 1;
    }
    #if(!system("zgrep -q 'HBO_MC_HASH_DISABLE *:= *1' $systeminit_file")) {
    #    $soc_hbo_hash_disable = 1;
    #} elsif(!system("zgrep -q 'HBO_MC_HASH_DISABLE *:= *0' $systeminit_file")) {
    #    $soc_hbo_hash_disable = 0;
    #} els
    if(!system("zgrep -q 'SOC_HBO_HASH *:= *1' $systeminit_file")) {
        $soc_hbo_hash_disable = 0;
    }
    if(!system("zgrep -q 'VTU_FORCE_SCALABLE_NESTED *:= *1' $systeminit_file")) {
        $is_scalable_nested = 1;
    }
    if($emulation_obj_load_time) {
        # emulation uses these default value
        $soc_hbo_hash_disable = 0;
        $soc_hbo_hash_mask = (0x2094>>2);
        $soc_hbo_hash_lsb = 2+6;
    }
    if(!system("zgrep -q 'SOC_TME_EN *:= *1' $systeminit_file")) {
        $do_e2e_preload_encrypt = 1;
    }
    if(system("zgrep -q 'CCF_ATOM_MASK *:=' $systeminit_file")) {
        # if no CCF_IA_MASK this is an old test. ok.
    } elsif(system("zgrep -q 'CCF_IA_MASK *:= *15\\>' $systeminit_file")) {
        die_ERROR("183 ERROR: Unsupported CCF_IA_MASK configuration");
    }
    if(!system("zgrep -q 'CCF_ATOM_MASK *:= *48\\>' $systeminit_file")) {
        $ICELAND_IDI = "AT_IDI_[6]";
    } elsif(!system("zgrep -q 'CCF_ATOM_MASK *:= *0\\>' $systeminit_file")) {
    } elsif(system("zgrep -q 'CCF_ATOM_MASK *:=' $systeminit_file")) {
        # if no CCF_ATOM_MASK this is an old test. ok.
    } else {
        die_ERROR("183 ERROR: Unsupported CCF_ATOM_MASK configuration");
    }
    if(`zgrep 'CCF_MKTME_EN *:= *1' $systeminit_file`=~/CCF_MKTME_EN *:= *(\d+)/) {
        $CCF_MKTME_EN = 1*$1;
    }
    if(`zgrep 'CCF_MKTME_MASK *:= *[0-9]' $systeminit_file`=~/CCF_MKTME_MASK *:= *(\d+)/) {
        $CCF_MKTME_MASK = 1*$1;
    }
    if(`zgrep 'SOC_MKTME_EN *:= *[0-9]' $systeminit_file`=~/SOC_MKTME_EN *:= *(\d+)/) {
        $sysinit{SOC_MKTME_EN} = 1*$1;
    }
    if(`zgrep 'SOC_TDX_EN *:= *[0-9]' $systeminit_file`=~/SOC_TDX_EN *:= *(\d+)/) {
        $sysinit{TDX_EN} = 1*$1;
    }
    if(`zgrep 'SOC_MK_TME_KEYID_BITS *:= *[0-9]' $systeminit_file`=~/SOC_MK_TME_KEYID_BITS *:= *(\d+)/) {
        $sysinit{MKTME_KEYID_BITS} = 1*$1;
    }
    if(`zgrep 'SOC_TDX_KEYID_BITS *:= *[0-9]' $systeminit_file`=~/SOC_TDX_KEYID_BITS *:= *(\d+)/) {
        $sysinit{TDX_KEYID_BITS} = 1*$1;
        create_TDX_MKTME_info();
    }
    if(!system("zgrep -q 'SOC_IBECC_TEST *:= *1' $systeminit_file")) {
        $lnl_ibecc_en = 1;
    }
    if(!system("zgrep -q 'HBO_MUFASA_EN *:= *1' $systeminit_file")) {
        $hbo_mufasa_en= 1;
    } elsif(!system("zgrep -q 'HBO_MUFASA_EN *:= *0' $systeminit_file")) {
        $hbo_mufasa_en= 0;
    }
    if(!system("zgrep -q 'SOC_HBO_FULL_CL_EN *:= *0' $systeminit_file") and $ACERUN_TESTNAME =~ /\bsoc_hbo_alive_test$/) {
        print "Skip checking because i am not supporting soc_hbo_alive test that send non por unallign transactions to vpu and ipu\n" if $debug>=1;
        exit; 
    }
    if($ACERUN_TEST_WORK_AREA =~ /\bsoc_pv_test_Real_MC_high_wp_CCF/) {
        $no_CCF_write_merge = 1 unless defined($no_CCF_write_merge);
    }
    if($ACERUN_TESTNAME =~ /\bsoc_hbo_alive_test$/) {
        $e2e_write_chk_use_uri = 10 unless defined($e2e_write_chk_use_uri);
    }
    if(!system("zgrep -q 'SOC_CFI_STANDALONE *:= *1' $systeminit_file")) {
        print "Skip checking because i am not supporting SOC_CFI_STANDALONE mode\n" if $debug>=1;
        exit; 
    }
    if(!system("zgrep -q 'SOC_CFG_XPROP *:= *1' $systeminit_file") and !(-e "SOC_CFI_trk.log") and !(-e "SOC_CFI_trk.log.gz")) {
        print "Skip checking because i am not supporting SOC_CFG_XPROP test that does not have SOC_CFI_trk.log file\n" if $debug>=1;
        exit; 
    }
    if(!system("zgrep -q 'MEMSS_STUB *:= *1' $systeminit_file")) {
        print "Skip checking because i am not supporting MEMSS_STUB mode\n" if $debug>=1;
        exit; 
    }
    #if((-e "ccf_preload_trk.log" or -e "ccf_preload_trk.log.gz") and !system("zgrep -q ' | *M *| ' ccf_preload_trk.log")) {
    #    print "Skip checking if there is a ccf_preload in M state becuse we don;t supprot it yet\n" if $debug>=1;
    #    exit; # fix: need to support ccf_preload_trk.log.gz parseing and remove this skip
    #}
    if(!system("zgrep -q 'D2D_CNOC_STUB := 0' $systeminit_file") && !($ACERUN_SYSTEM_MODEL=~/^soc_c2saf_model_compute/)) {
        push @gtcxl_idi_filter_l,"IOC"; # in this mode the IOC trasaction also appears as D2D transactions. so I remove the IOC.
    }
    if(!system("zgrep -q 'SOC_MEDIA_CXL_IDI_VC *:= *3' $systeminit_file") && !system("zgrep -q 'MEDIA_VC_CONNECTED *:= *1' $systeminit_file")) {
    } else {
        push @CXL_CFI_FILTER_STR_l,"SOC_MEDIA";
        push @gtcxl_idi_filter_l,"GT_IDI_6","GT_IDI_7";
        push @gtcxl_idi_filter_l,"NOC_IDI_6","NOC_IDI_7";
        push @gtcxl_idi_filter_l,"MEDIA_0","MEDIA_1";
    }
    if(!system("zgrep -q 'SOC_IAX_CXL_IDI_VC *:= *1' $systeminit_file") && !system("zgrep -q 'IAX_VC_CONNECTED *:= *1' $systeminit_file")) {
    } else {
        push @CXL_CFI_FILTER_STR_l,"SOC_IAX";
        push @gtcxl_idi_filter_l,"GT_IDI_8";
        push @gtcxl_idi_filter_l,"NOC_IDI_8";
        push @gtcxl_idi_filter_l,"IAX";
    }
}

if($PCIE_CFG_SPACE->{0}->{0}->{ibecc_activate}&1 && !$skip_iop_cmi_log) {
    #$skip_e2e_write_chk=1; # FIXME: Need to remove that once IBECC support is implemented.
    $ibecc_act = 1;
    print "Set skip_e2e_write_chk=1 because IBECC is activate.\n" if $debug>=1;
}

sub set_and_verify_not_dram_ranges() { # Verify that TOLUD & TOUUD are correct:
    my $tolud = Dump_BIOS_register("TOLUD",$PCIE_CFG_SPACE->{0}->{0}->{"TOLUD"},undef,$debug>=2);
    my $touud = Dump_BIOS_register("TOUUD",$PCIE_CFG_SPACE->{0}->{0}->{"TOUUD"},undef,$debug>=2);
    my $remap_base  = Dump_BIOS_register("REMAPBASE",$PCIE_CFG_SPACE->{0}->{0}->{REMAPBASE},undef,$debug>=2);
    my $remap_limit = Dump_BIOS_register("REMAPLIMIT",$PCIE_CFG_SPACE->{0}->{0}->{REMAPLIMIT},undef,$debug>=2);
    my $ecc_storage_addr = Dump_BIOS_register("ECC_STORAGE_ADDR",$PCIE_CFG_SPACE->{0}->{0}->{ECC_STORAGE_ADDR},undef,$debug>=2);

    if(!$sm_TOLUD_addr && !$sm_TOUUD_addr) {
        # If the sm.out file was not read, need to set DRAM_LOW and DRAM_HIGH ranges my self.
        if($tolud) {
            my %mmio_low;
            $sm_TOLUD_addr = $mmio_low{BASE} = $tolud;
            $mmio_low{LIMIT} = 0xFFFFFFFF;
            $mmio_low{MASK} = 0xFFFFFFFF_FFFFFFFF;
            push @not_dram_ranges_l,\%mmio_low;
            push @IOP_not_dram_ranges_l,\%mmio_low;
        } else {
            print_ERROR("059 ERROR: Bad TOLUD register Value\n");
        }
    
        if($touud) {
            my $dram_high = $touud;
            if($ecc_storage_addr && $ibecc_act) {
                $dram_high = ($ecc_storage_addr<<24);
            } elsif(defined($remap_base) && defined($remap_limit) && $remap_base<$remap_limit) {
                $dram_high = $remap_base;
            }
            my %mmio_high;
            $sm_TOUUD_addr = $mmio_high{BASE} = $dram_high;
            $mmio_high{LIMIT} = 0x7FFFFFFF_FFFFFFFF;
            $mmio_high{MASK} = 0xFFFFFFFF_FFFFFFFF;
            push @not_dram_ranges_l,\%mmio_high;
            push @IOP_not_dram_ranges_l,\%mmio_high;
        } else {
            print_ERROR("059 ERROR: Bad TOUUD register Value\n");
        }
    }
    
    if($sm_TOLUD_addr && $sm_TOUUD_addr) {
        # Now I am verifying the sm_TOLUD_addr & sm_TOUUD_addr
        print "sm_TOLUD_addr=".addr_str($sm_TOLUD_addr)."\n" if $debug>=2;
        print "sm_TOUUD_addr=".addr_str($sm_TOUUD_addr)."\n" if $debug>=2;
        if(defined($tolud) && $tolud!=$sm_TOLUD_addr) {
            die_ERROR("103 ERROR: Bad TOLUD register Value : ");
        }
    
        if($ecc_storage_addr && $ibecc_act) {
            if(($soc_mc_hash_disable ? $ecc_storage_addr : $ecc_storage_addr*2)!=$sm_TOUUD_addr>>24 && ($sm_TOUUD_addr&0xFFFFFF)==0) {
                print_ERROR("058 WARNING: Bad ECC_STORAGE_ADDR register Value\n");
            }
        } elsif(defined($remap_base) && defined($remap_limit) && $remap_base<$remap_limit) {
            if($remap_base!=$sm_TOUUD_addr) {
                print_ERROR("058 WARNING: Bad REMAPBASE register Value\n");
            }
        } else {
            if(defined($touud) && $touud!=$sm_TOUUD_addr && ($cpu_proj ne "adl") && !$lnl_ibecc_en) {
                print_ERROR("058 WARNING: Bad TOUUD register Value\n");
            }
        }
    } else {
        print "058 WARNING: Bad sm_TOLUD_addr or sm_TOUUD_addr Value\n";
    }

} # Verify that TOLUD & TOUUD are correct.

parse_emu_minibios_file();

if(defined($PCIE_CFG_SPACE->{0}->{0}->{PRMRR_MASK}) and defined($PCIE_CFG_SPACE->{0}->{0}->{PRMRR_BASE}) and $PCIE_CFG_SPACE->{0}->{0}->{PRMRR_MASK}&0x800) {
    my %prmrr_range;
    my $mask = (($PCIE_CFG_SPACE->{0}->{0}->{PRMRR_MASK}>>12)<<12) & 0x7FFFFFF000;
    $prmrr_range{BASE} = (($PCIE_CFG_SPACE->{0}->{0}->{PRMRR_BASE}>>12)<<12);
    $prmrr_range{LIMIT} = ((~$mask) & 0x7FFFFFFFFF) | $prmrr_range{BASE}; 
    $mmio_low{MASK} = 0xFFFFFFFF_FFFFFFFF;
    push @prmrr_ranges_l,\%prmrr_range;
    printf("Set PRMRR_RANGE : BASE=%012X LIMIT=%012X.\n",$prmrr_range{BASE},$prmrr_range{LIMIT}) if $debug>=1;
}

# Parge IOMMU page builder.
parse_iommu_page_builder_file();

if(defined($tbtpcie_iommu_scbd_h) && $tbtpcie_iommu_scbd_h->{dmi_link}) {
    for my $sai ("0001","0003","0005","0007","0009","000b","000d","000f","0010","0012","0014","0016","001a","001c","001e","0020","0022","0024","0026","0028","002a","002c","002e","0030","0032","0034","0036","0038","003a","003c","003e","0040","0042","0044","0046","0048","004a","004c","004e","0052","0054","0056","005a","005c","0060","0062","0064","0066","0068","006a","006e","0070","0072","0074","0076","0078","007a","007c","0000") {
        $IOP_iommu_scbd_h->{"sai_$sai"} = $tbtpcie_iommu_scbd_h->{dmi_link};
    }
}


parse_lnl_vtu_address_translation_trk("vtu_trackers/vtu_addr_translation_trk.log") or parse_lnl_vtu_address_translation_trk("vtu_addr_translation_trk.log");

# Parge ALL PSF log files.
parse_all_psf_files_in_dir();

# Make sure we have GNA psf scbd or GMM psf scbd but not both
{
    my $GMM_scbd;
    my $GNA_scbd;
    my @non_GMM_more_psf_file_scbd;
    for my $scbd (@more_psf_file_scbd) {
        if($scbd->{filename}=~/^GMM/) {
            $GMM_scbd = $scbd;
        } elsif($scbd->{filename}=~/^GNA/) {
            $GNA_scbd = $scbd;
            push @non_GMM_more_psf_file_scbd,$scbd;
        } else {
            push @non_GMM_more_psf_file_scbd,$scbd;
        }
    }
    if($GMM_scbd && $GNA_scbd) {
        @more_psf_file_scbd = @non_GMM_more_psf_file_scbd;
    }
}

# Parse OPIO LINK or DMI LINK log file.
if($is_parse_OPIO_LINK_file) {
    parse_OPIO_LINK_file();
}

parse_gtcxl_file() if(!$skip_gtcxl_file);
if(1*@gtcxl_file_scbd_l and is_scbd_exists($gtcxl_file_scbd_l[0])) { 
    if(!system("zgrep -q 'PVALUE: *SOC_CFI_C_D2D0_IS_ACTIVE=1' $push_cmd_file")) {
    } else {
        push @gtcxl_idi_filter_l,"NOC_IDI_[12]"; # This filters GT transaction from cxl.log becuase there are taken from gtcxl cxl*_d2h_requests files
    }
}

if($systeminit_file_exist and system("zgrep -q '/SOC_CFG_MODEL *:= *soc_validation_model_compute' $systeminit_file")) {
    push @gtcxl_idi_filter_l,"NOC_IDI_4"; # INOC
}

parse_idi_file($idi_log_file,$idi_file_scbd,0) if(!$skip_e2e_read_chk || $emulation_obj_load_time and !($ACERUN_CLUSTER=~/^ioc/));

for my $i (0..8) {
    parse_ccf_llc_file("tlm_post/ccf_replay_base_env/llc_${i}_pp_trk.log");
}

parse_idi_file("cxl.log",$cxl_idi_file_scbd,1) if(!$skip_e2e_read_chk || $emulation_obj_load_time) && ($cpu_proj eq "lnl") && !($ACERUN_CLUSTER=~/^(idi_bridge|ccf|cbb)/) && !($ACERUN_STEPPING=~/^cbb/);

parse_cfi_trk_file() if(!$skip_e2e_read_chk || $emulation_obj_load_time);

parse_ufi_trk_file() if(!$skip_e2e_read_chk || $emulation_obj_load_time);

parse_axi_all_files() if(!$skip_axi_file);

sub filter_coh_and_non_coh_conflicts {
    my $coh_trans_l;
    my $idi_trans_l = [grep {!($_->{cmd}=~/RDCURR/)} @{$idi_file_scbd->{U}->{all}}];
    my $cxl_trans_l = [grep {!($_->{cmd}=~/RDCURR/)} @{$cxl_idi_file_scbd->{U}->{all}}];
    my $coh_trans_l = merge_two_sorted_lists(\&get_rec_tick_go,$idi_trans_l,$cxl_trans_l);
    my $EMemWr_tr_l = [];
    if($cfi_trk_file_scbd and $cfi_trk_file_scbd->{filename}) {
        $EMemWr_tr_l =  get_filtered_cmds($cfi_trk_file_scbd,"U",undef,cmd=>'EMemWr',Unit=>'D2D',label=>"find all EMemWr in cfi ioc to filter checking if it contradicts with coherent commands");
        $coh_trans_l = merge_two_sorted_lists(\&get_rec_tick_go,$EMemWr_tr_l,$coh_trans_l);
    }
    my @preload_M_lines = grep { $_->{state} eq "M" }  @{$mcc_preloader_file_scbd_l->[0]->{U}->{all}};
    if(@preload_M_lines) {
        unshift @$coh_trans_l,@preload_M_lines;
    }
    my $idi_owned_slots = get_owned_slots($coh_trans_l);
    for my $scbd (@axi_file_scbd_l) {
        find_non_coh_writes($idi_owned_slots,$scbd->{U}->{all});
   }
   my $wcil_tr_l;
   $wcil_tr_l =  get_filtered_cmds($idi_file_scbd,"U",undef,cmd=>'WCIL',label=>"find all WCIL in idi to filter checking if it contradicts with coherent commands");
   if($argv{skip_wcil_for_dram}) {
       # for projects older than lnl there wcil was strictly order
       # so there was no need for that filter dram range
       # it is only needed for mmio region
       $wcil_tr_l = [grep { is_addr_in_range_l_fast($_->{address},\@mmio_ranges_l) } @$wcil_tr_l];
   }
   find_non_coh_writes($idi_owned_slots,$wcil_tr_l) if $wcil_tr_l;

   my $CFI_NC_wr_tr_l;
   if($cfi_trk_file_scbd and $cfi_trk_file_scbd->{filename}) {
       $CFI_NC_wr_tr_l =  get_filtered_cmds($cfi_trk_file_scbd,"U",undef,cmd=>'^MemWr$',Unit=>'^(SOC_DEIOSF|SOC_DISP|SOC_MEDIA|SOC_IPU)',label=>"find all MEDIA MemWr in idi to filter checking if it contradicts with coherent commands");
       find_non_coh_writes($idi_owned_slots,$CFI_NC_wr_tr_l) if $CFI_NC_wr_tr_l;
   }

   if($cfi_trk_file_scbd and $cfi_trk_file_scbd->{filename}) {
       my $coh_trans_and_CCF_l;
       my $CCF_WB_tr_l =  get_filtered_cmds($cfi_trk_file_scbd,"U",undef,cmd=>'^(SnpL|WbMtoI|WbEtoI)',Unit=>'SOC_CCF_LINK',label=>"find all CCF drop ownership in cfi ioc to filter checking if it contradicts with coherent commands");
       $coh_trans_and_CCF_l = merge_two_sorted_lists(\&get_rec_tick_go,$CCF_WB_tr_l,$coh_trans_l);
       my $CCF_owned_slots = get_owned_slots_CCF($coh_trans_and_CCF_l);
       find_non_coh_writes($CCF_owned_slots,$CFI_NC_wr_tr_l) if $CFI_NC_wr_tr_l;
       for my $scbd (@axi_file_scbd_l) {
            find_non_coh_writes($CCF_owned_slots,$scbd->{U}->{all});
       }
   }

}

if($emulation_obj_load_time && !defined($emulation_obj_file) && (-e "rand_metro.obj" or -e "rand_metro.obj.gz")) {
    $emulation_obj_file = "rand_metro.obj";
}

parse_ccf_preloader_file("ccf_preload_trk.log");

if(!$create_cmi_preload) {
parse_astro_preloader_file("astro_preload_trk.log") or 
parse_mcc_preloader_file("mc0_preloader.log") or 
parse_mcc_preloader_file("mc_trackers/mc0_preloader.log") or 
parse_cxm_preloader_file("cxm_trackers/soc_mc0_cxm_responder_memory_model_memory_tracker.log") or 
parse_mcc_preloader_file("mcc_preloader.trk") or parse_mcc_preloader_file("mcc_env0_mcc_preloader.trk") or(parse_emu_preloader_both_files($emulation_obj_file,$emulation_obj_load_time));

if(parse_mcc_preloader_file("mc1_preloader.log") or 
    parse_mcc_preloader_file("mc_trackers/mc1_preloader.log") or
    parse_mcc_preloader_file("mcc_env1_mcc_preloader.trk") or parse_cxm_preloader_file("cxm_trackers/soc_mc1_cxm_responder_memory_model_memory_tracker.log")) {
    if($mcc_preloader_file_scbd_l->[0]->{filename}=~/mcc_env0_mcc_preloader.trk/ && $mcc_preloader_file_scbd_l->[1]->{filename}=~/mcc_env1_mcc_preloader.trk/ or
            $mcc_preloader_file_scbd_l->[0]->{filename}=~/mc0_preloader.log/ && $mcc_preloader_file_scbd_l->[1]->{filename}=~/mc1_preloader.log/ or
            $mcc_preloader_file_scbd_l->[0]->{filename}=~/soc_mc0_cxm_responder_memory_model_memory/ && $mcc_preloader_file_scbd_l->[1]->{filename}=~/soc_mc1_cxm_responder_memory_model_memory/) {
        # combile both first preload scbdd to one scbd.
        merge_preload_scbd_lists($mcc_preloader_file_scbd_l->[0],$mcc_preloader_file_scbd_l->[1]);
        my $scbd = shift @$mcc_preloader_file_scbd_l;
        shift @$mcc_preloader_file_scbd_l;
        unshift @$mcc_preloader_file_scbd_l, $scbd;
    }
}
if($ccf_preloader_file_scbd && @$mcc_preloader_file_scbd_l) {
    merge_preload_scbd_lists($mcc_preloader_file_scbd_l->[0],$ccf_preloader_file_scbd);
    filter_preload_for_ccf_LLC($mcc_preloader_file_scbd_l->[0]);
} elsif($ccf_preloader_file_scbd && ($ACERUN_CLUSTER=~/^(idi_bridge|ccf|cbb)/ or $ACERUN_STEPPING=~/^cbb/)) {
    # in ccf CTE use only the ccf_preload file
    @$mcc_preloader_file_scbd_l = ($ccf_preloader_file_scbd);
}
} # if(!$create_cmi_preload)

read_SOC_MC_file($mcc_preloader_file_scbd_l) if $do_e2e_preload_encrypt;

if(!$skip_e2e_read_chk and (is_scbd_exists($idi_file_scbd) || is_scbd_exists($cxl_idi_file_scbd))) {
    &filter_coh_and_non_coh_conflicts();
}

# Parse PEGs and Type-C log LINK files.
parse_TCSS_PCIExBFM_files();
parse_PEG_PCIExBFM_files();
parse_DMI_PCIExBFM_files();

if($cpu_proj eq "adl" && (-f "astro_preload_trk.log" or -f "astro_preload_trk.log.gz")) {
    # If the is ASTRO then it uses peg60 a disk. So peg60 is no connected to IOP.
    ###$pcie_link_file_scbd_l[60] = undef;
}

if($cpu_proj eq "lnl") {
    $mufasa_file_scbd = (parse_mufasa_trans_file("tlm_post/hbo_replay_env/hbo_mfs_ifc_trk.log") or parse_mufasa_trans_file("hbo_trackers/hbo_mfs_ifc_trk.log") or parse_mufasa_trans_file("hbo_mfs_ifc_trk.log"));
    #if(!defined($mufasa_file_scbd) and $hbo_mufasa_en) {
    #    $skip_e2e_write_chk = 1 unless defined($skip_e2e_write_chk);
    #}
}

# Parse MC log file.
if($ibecc_act or $cpu_proj eq "adl" or $cpu_proj eq "lnl") {
    if($cpu_proj eq "och") {
        $cmi_ibecc_trans_file_scbd = (parse_cmi_trans_file("cmi_env.iop_cmi_vc2_agt_req_0_cmi_txn_tracker.log",tick_mc=>1) or parse_cmi_trans_file("req_port_iop_cmi_txn_tracker.log",tick_mc=>1));
        $cmi_ibecc_trans_file_scbd_l[0] = $cmi_ibecc_trans_file_scbd;
        # The above cmi file contains only the IOP transactions,
        # So parse also the below fie that has IDI WR transaction and can assign tick_mc for them
        parse_cmi_trans_file("cmi_env.idp0_cmi_vc2_agt_req_1_cmi_txn_tracker.log",tick_mc=>1);
        parse_cmi_trans_file("cmi_env.idp1_cmi_vc2_agt_req_2_cmi_txn_tracker.log",tick_mc=>1);
        parse_cmi_trans_file("idp_ip_cmi_vc2_responder_0_cmi_txn_tracker.log",tick_mc=>1); # This is the same file as 2 lines above by in OCH
        parse_cmi_trans_file("idp_ip_cmi_vc2_responder_1_cmi_txn_tracker.log",tick_mc=>1); # This is the same file as 2 lines above by in OCH
    } elsif($ACERUN_CLUSTER=~/^ioc/) {
    } elsif($cpu_proj eq "lnl") {
      if(!$skip_e2e_write_chk) {
        $cmi_ibecc_trans_file_scbd_l[0] = $cmi_ibecc_trans_file_scbd = parse_cxm_cfi_trans_file("SOC_CFI_trk.log",tick_mc=>1);
        if(!$soc_hbo_hash_disable) {
            # if hbo_hash is active, then split to two mc lists
            for(keys %{$cmi_ibecc_trans_file_scbd_l[0]}) { $cmi_ibecc_trans_file_scbd_l[1]->{$_} = $cmi_ibecc_trans_file_scbd_l[0]->{$_}; }
            my $new_trans_l;
            for my $rec_ptr (@{$cmi_ibecc_trans_file_scbd->{D}->{all}}) {
                my $hboid = hbo_hash_get_idx($rec_ptr->{address});
                push @{$new_trans_l->[$hboid]},$rec_ptr;
            }
            undef $cmi_ibecc_trans_file_scbd_l[0]->{D};
            undef $cmi_ibecc_trans_file_scbd_l[1]->{D};
            $cmi_ibecc_trans_file_scbd_l[0]->{D}->{all} = $new_trans_l->[0];
            $cmi_ibecc_trans_file_scbd_l[1]->{D}->{all} = $new_trans_l->[1];
        }
      }
    } elsif($cpu_proj eq "adl") {
        $cmi_ibecc_trans_file_scbd_l[0] = $cmi_ibecc_trans_file_scbd = parse_cmi_trans_file("cmi_slow0_req_iop0_cmi_txn_tracker.log",tick_mc=>1);
        if(my $scbd = parse_cmi_trans_file("cmi_slow1_req_iop1_cmi_txn_tracker.log",tick_mc=>1) or undef) {
            $cmi_ibecc_trans_file_scbd_l[1] = $scbd;
        }
        push @cmi_idp_trans_file_scbd_l,parse_cmi_trans_file("cmi_fast_req_idp0_cmi_txn_tracker.log",tick_mc=>1);
        push @cmi_idp_trans_file_scbd_l,parse_cmi_trans_file("cmi_fast_req_idp1_cmi_txn_tracker.log",tick_mc=>1);
    } else {
        $cmi_ibecc_trans_file_scbd = parse_cmi_trans_file("icl_m0_env_soc.ibecc_cmi_vc2_agt_rsp_0_cmi_txn_tracker.log",tick_mc=>1);
    }
    if($cmi_ibecc_trans_file_scbd) {
        $mcc_trans_file_scbd = $cmi_ibecc_trans_file_scbd;
        @mcc_trans_file_scbd_l = @cmi_ibecc_trans_file_scbd_l;

    } elsif($ACERUN_CLUSTER=~/^(ioc|idi_bridge|ccf|cbb)/ or $ACERUN_STEPPING=~/^cbb/) {
    } elsif(!$skip_e2e_write_chk) {
        die_ERROR("104 ERROR: Fail to parse icl_m0_env_soc.ibecc_cmi_vc2_agt_rsp_0_cmi_txn_tracker.log in this IBECC test.");
    }
} else {
    $mcc_trans_file_scbd  = (parse_mcc_trans_file("mcc_trans.trk") or parse_mcc_trans_file("mcc_env0_mcc_trans.trk") or undef);
    if($mcc_trans_file_scbd) {
        $mcc_trans_file_scbd_l[0] = $mcc_trans_file_scbd;
        if(my $scbd  = (parse_mcc_trans_file("mcc_env1_mcc_trans.trk") or undef)) {
            $mcc_trans_file_scbd_l[1] = $scbd;
        }
    }

    if(!defined($mcc_trans_file_scbd)) {
        # Check if we can use emulation cmi file instead
        $cmi_mc_trans_file_scbd = (parse_cmi_trans_file("cmi_env.mc_cmi_vc2_agt_rsp_2_cmi_txn_tracker.log",tick_mc=>1) 
            or parse_cmi_trans_file("ovm_test_top.env.cmi_env.cmi_env.mc_cmi_vc2_agt_rsp_2_cmi_txn_tracker.log",tick_mc=>1)
            or parse_cmi_trans_file("cmi_env.mc0_cmi_vc2_agt_rsp_0_cmi_txn_tracker.log",tick_mc=>1)
        );
        if($cmi_mc_trans_file_scbd) {
            $mcc_trans_file_scbd = $cmi_ibecc_trans_file_scbd;
        }
    }
}

if($create_cmi_preload) {
    my $read_addr_h = { };
    my $write_addr_h = { };
    for my $scbd (@cmi_ibecc_trans_file_scbd_l,@cmi_idp_trans_file_scbd_l) {
        my $preload_read_addr_h = $scbd->{preload_read_addr_h};
        while(my ($addr6,$rec_ptr) = each %$preload_read_addr_h) {
            if(exists($read_addr_h->{$addr6})) {
                if($read_addr_h->{$addr6}->{tick_beg} > $rec_ptr->{tick_beg}) {
                    $read_addr_h->{$addr6} = $rec_ptr;
                }
            } else {
                $read_addr_h->{$addr6} = $rec_ptr;
            }
        }
    }

    for my $scbd (@cmi_ibecc_trans_file_scbd_l,@cmi_idp_trans_file_scbd_l) {
        for my $rec_ptr (@{$scbd->{D}->{all}}) {
            my $pre_rec = $read_addr_h->{$rec_ptr->{address}>>6};
            if($pre_rec and $pre_rec->{tick_beg}>=$rec_ptr->{tick_beg}) {
                if($rec_ptr->{cmd}=~/^MWrPtl/) { 
                    merge_preload_cl_data(\$pre_rec->{data},$rec_ptr->{data});
                } else {
                    delete $read_addr_h->{$rec_ptr->{address}>>6};
                }
            }
        }
    }

    my $preload_trans_l = [ ];
    while(my ($addr6,$rec_ptr) = each %$read_addr_h) {
        $rec_ptr->{tick_end} = $rec_ptr->{tick_go} = $rec_ptr->{tick_beg} = 1;
        push @$preload_trans_l , $rec_ptr;
    }
    #  @$preload_trans_l = sort { $a->{tick_beg} < $b->{tick_beg} } @$preload_trans_l;

    push @$mcc_preloader_file_scbd_l , {
        filename => "cmi_MRd_preloader",
        U => { all => $preload_trans_l },
    };
}

undef @cmi_idp_trans_file_scbd_l;
undef @cmi_ibecc_trans_file_scbd_l;

# Parse MC log file.
$cmi_iop_trans_file_scbd = (parse_cmi_trans_file("cmi_env.iop_cmi_vc2_agt_req_2_cmi_txn_tracker.log") or parse_cmi_trans_file("ovm_test_top.env.cmi_env.cmi_env.iop_cmi_vc2_agt_req_2_cmi_txn_tracker.log")) if(!$skip_iop_cmi_log);

$idi_file_scbd->{UC_WR_cmd} = undef; # Free huge about of memory of this IDI URI hash.

#parse_svt_LINK_file();

# Analyze the PCIE CfgWr to find MTB PMBASE/LIMIT registers
if($npk_psf_file_scbd) {
    pcie_registers_parse(PCIE_DEVICE=>$NPK_DID,PCIE_FUNCTION=>0,trans_l1=>get_filtered_cmds($npk_psf_file_scbd,"D",'(CfgWr)'));
}
if($pep_psf_file_scbd) {
    pcie_registers_parse(PCIE_DEVICE=>$PEP_DID,PCIE_FUNCTION=>0,trans_l1=>get_filtered_cmds($pep_psf_file_scbd,"D",'(CfgWr)'));
}
for(@more_psf_file_scbd) {
    pcie_registers_parse(PCIE_DEVICE=>$_->{DID},PCIE_FUNCTION=>0,trans_l1=>get_filtered_cmds($_,"D",'(CfgWr)'));
}

if(is_scbd_exists($idi_file_scbd)) {
    idi_registers_parse(PCIE_DEVICE=>0,PCIE_FUNCTION=>0,trans_l1=>get_filtered_cmds($idi_file_scbd,"U",undef,cmd=>'(PORT_OUT|WIL)'));
    if($sysinit{TDX_EN} and defined($ACTRR_DATA_range_l)) {
        my $ACTRR_DATA_h = { };
        idi_ACTRR_range_parse(get_filtered_cmds($idi_file_scbd,"U",undef,cmd=>'(WOWrInv|WIL|WBMTOI|WBMTOE|WCIL|ITOMWR|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SELFSNPINV|ITOMWR_WT|SNPCURR)'),$ACTRR_DATA_h);
        if($ACTRR_DATA_h and keys(%$ACTRR_DATA_h)) {
            idi_ACTRR_filter($idi_file_scbd->{U}->{all},$ACTRR_DATA_h);
        }
    }
}

set_and_verify_not_dram_ranges();

#if($emulation_obj_load_time and my $VTDPVC0_GCMD = $PCIE_CFG_SPACE->{0}->{0}->{"VTDPVC0_GCMD"}) {
#    for my $samp (@$VTDPVC0_GCMD) {
#        if($samp->[0] and get_field($samp->[1],31,31)) {
#            print "WARNING: Skip checking of this emulation test because it has VTD.\n";
#            $skip_e2e_read_chk=1;
#            $skip_e2e_write_chk=1;
#            last;
#        }
#    }
#}

@IMR_exclude_range_l = get_IMR_exclude_range_l();
{
my @TSEG_DSM_GSM_exclude_range_l = (get_TSEG_DSM_GSM_exclude_range_l());
push @not_dram_ranges_l,@skip_DPR_changing_range;
push @IOP_not_dram_ranges_l,@skip_DPR_changing_range;
push @not_dram_ranges_l,@TSEG_DSM_GSM_exclude_range_l;
push @IOP_not_dram_ranges_l,@TSEG_DSM_GSM_exclude_range_l;
}

if($tbtpcie_iommu_scbd_h) {
    # In case the we have iommu, disable the IPO_not_dram filtering (which is mainly meant to handle the IOP DPR range).
    # In IOMMU mode, the address can be out of DRAM range, because it is doing VTD convertion first.
    @IOP_not_dram_ranges_l = ();
}

if($emulation_obj_file) {
    # Amos says that this are sends commands to the transactions and is not interesting 
    $emu_transactor_cmd_range = { };
    $emu_transactor_cmd_range->{BASE} = 0x1234000;
    $emu_transactor_cmd_range->{LIMIT} = 0x1234FFF;
    $emu_transactor_cmd_range->{MASK} = 0xFFFFFFFF_FFFFFFFF;
    push @not_dram_ranges_l,$emu_transactor_cmd_range;
    push @IOP_not_dram_ranges_l,$emu_transactor_cmd_range;
}

#FIXME:Temporarily removing check from all PAM range. Need to remove only PAM the enalbed to go to IOMMU
if($argv{skip_PAM_range}) {
    my %mmio_pam_all;
    $mmio_pam_all{BASE} = 0xC0000;
    $mmio_pam_all{LIMIT} = 0xFFFFF;
    $mmio_pam_all{MASK} = 0xFFFFFFFF_FFFFFFFF;
    push @not_dram_ranges_l,\%mmio_pam_all;
}

if($PCIE_CFG_SPACE->{0}->{0}->{LAC}&0x80) {
    # Add ISA hole if enabled.
    my %mmio_pam_all;
    $mmio_pam_all{BASE}  = 0xF00000;
    $mmio_pam_all{LIMIT} = 0xFFFFFF;
    $mmio_pam_all{MASK} = 0xFFFFFFFF_FFFFFFFF;
    push @not_dram_ranges_l,\%mmio_pam_all;
}

# For IDI I always filter the VGA range because it always go ti MMIO (either DISPLAY or OPIO).
@idi_vga_ranges_l = (
    { BASE=>0xA0000, LIMIT=>0xBFFFF, MASK=>0xFFFFFFFF_FFFFFFFF, },
);

my $WRC_VC_filter;

my @WRC_VC_filter_func_l     = ();
my @WRC_VC_filter_not_func_l = ();

if($cpu_proj eq "adl") {

        if($opio_psf_file_scbd)       { $opio_psf_file_scbd->{VC_h}         = { 0=>"VC0b", 1=>"VCrt", 2=>"VCm" }; };
        if($dmi_psf_file_scbd)        { $dmi_psf_file_scbd->{VC_h}          = { 0=>"VC0b", 1=>"VCrt", 2=>"VCm" }; };
        if($pcie_psf_file_scbd_l[10]) { $pcie_psf_file_scbd_l[10]->{VC_h}   = { 0=>"VC0c", 1=>"VCrt", }; };
        if($pcie_psf_file_scbd_l[11]) { $pcie_psf_file_scbd_l[11]->{VC_h}   = { 0=>"VC0d", 1=>"VCrt", }; };
        if($pcie_psf_file_scbd_l[12]) { $pcie_psf_file_scbd_l[12]->{VC_h}   = { 0=>"VC0e", 1=>"VCrt", }; };
        if($pcie_psf_file_scbd_l[60]) { $pcie_psf_file_scbd_l[60]->{VC_h}   = { 0=>"VC0f", 1=>"VCrt", }; };
        if($pcie_psf_file_scbd_l[62]) { $pcie_psf_file_scbd_l[62]->{VC_h}   = { 0=>"VC0d", 1=>"VCrt", }; };
        if($pcie_psf_file_scbd_l[ 0]) { $pcie_psf_file_scbd_l[ 0]->{VC_h}   = { 0=>"VC0h", }; };
        if($pcie_psf_file_scbd_l[ 1]) { $pcie_psf_file_scbd_l[ 1]->{VC_h}   = { 0=>"VC0h", }; };
        if($pcie_psf_file_scbd_l[ 2]) { $pcie_psf_file_scbd_l[ 2]->{VC_h}   = { 0=>"VC0h", }; };
        if($pcie_psf_file_scbd_l[ 3]) { $pcie_psf_file_scbd_l[ 3]->{VC_h}   = { 0=>"VC0h", }; };

        if($opio_link_file_scbd)       { $opio_link_file_scbd->{VC_h}       = { 0=>"VC0b", 1=>"VCrt", 2=>"VCm" }; };
        if($dmi_link_file_scbd)        { $dmi_link_file_scbd->{VC_h}        = { 0=>"VC0b", 1=>"VCrt", 2=>"VCm" }; };
        if($pcie_link_file_scbd_l[10]) { $pcie_link_file_scbd_l[10]->{VC_h} = { 0=>"VC0c", 1=>"VCrt", }; };
        if($pcie_link_file_scbd_l[11]) { $pcie_link_file_scbd_l[11]->{VC_h} = { 0=>"VC0d", 1=>"VCrt", }; };
        if($pcie_link_file_scbd_l[12]) { $pcie_link_file_scbd_l[12]->{VC_h} = { 0=>"VC0e", 1=>"VCrt", }; };
        if($pcie_link_file_scbd_l[60]) { $pcie_link_file_scbd_l[60]->{VC_h} = { 0=>"VC0f", 1=>"VCrt", }; };
        if($pcie_link_file_scbd_l[62]) { $pcie_link_file_scbd_l[62]->{VC_h} = { 0=>"VC0d", 1=>"VCrt", }; };
        if($pcie_link_file_scbd_l[ 0]) { $pcie_link_file_scbd_l[ 0]->{VC_h} = { 0=>"VC0h", }; };
        if($pcie_link_file_scbd_l[ 1]) { $pcie_link_file_scbd_l[ 1]->{VC_h} = { 0=>"VC0h", }; };
        if($pcie_link_file_scbd_l[ 2]) { $pcie_link_file_scbd_l[ 2]->{VC_h} = { 0=>"VC0h", }; };
        if($pcie_link_file_scbd_l[ 3]) { $pcie_link_file_scbd_l[ 3]->{VC_h} = { 0=>"VC0h", }; };

        $iop_psf_file_scbd->{VC_h} = { 0=>"VC0a", 1=>"VC0b", 2=>"VC0c", 3=>"VC0d", 4=>"VC0f", 5=>"VCm", 6=>"VCbr", 7=>"VCrt", 9=>"VC0h", a=>"VC1b", "b"=>"VC2a" };

        # FIXME: Need to use compare_write_byte_stream_l her eand mack sure that is update the tick_mc field
        my @VC_l;
        my $WRC_VC_ENABLE = $PCIE_CFG_SPACE->{0}->{0}->{wrc_vc_enable};
        $to_WRC_VC_h->{VC0a}  = 1, push @VC_l,"0" if $WRC_VC_ENABLE & (1<<0); # VC0a
        $to_WRC_VC_h->{VC0b}  = 1, push @VC_l,"1" if $WRC_VC_ENABLE & (1<<1); # VC0b
        $to_WRC_VC_h->{VC0c}  = 1, push @VC_l,"2" if $WRC_VC_ENABLE & (1<<2); # VC0c
        $to_WRC_VC_h->{VC0d}  = 1, push @VC_l,"3" if $WRC_VC_ENABLE & (1<<3); # VC0d
        #$to_WRC_VC_h->{VC0e}  = 1, push @VC_l,"3" if $WRC_VC_ENABLE & (1<<4); # VC0e
        $to_WRC_VC_h->{VC0f}  = 1, push @VC_l,"4" if $WRC_VC_ENABLE & (1<<5); # VC0f
        $to_WRC_VC_h->{VCm}  = 1, push @VC_l,"5" if $WRC_VC_ENABLE & (1<<21);# VCm
        $to_WRC_VC_h->{VCbr} = 1, push @VC_l,"6" if $WRC_VC_ENABLE & (1<<20);# VCbr
        $to_WRC_VC_h->{VCrt} = 1, push @VC_l,"7" if $WRC_VC_ENABLE & (1<<18);# VCrt
        $to_WRC_VC_h->{VC0h}  = 1, push @VC_l,"9" if($WRC_VC_ENABLE & (1<<7));# VC0h
        $to_WRC_VC_h->{VC1b}  = 1, push @VC_l,"a" if($WRC_VC_ENABLE & (1<<17));# VC1b
        $to_WRC_VC_h->{VC2a}  = 1, push @VC_l,"b" if($WRC_VC_ENABLE & (1<<19));# VC2a
        $WRC_VC_filter = '\|('.join('|',@VC_l).')/' if  @VC_l;

        push @WRC_VC_filter_func_l     , {func=>\&filter_WRC_psf_vc_func,is_not=>1};
        push @WRC_VC_filter_not_func_l , {func=>\&filter_WRC_psf_vc_func,is_not=>0};
}

if($opio_link_file_scbd && !$skip_OPIO_LINK_err) {
    #FIXME:Need to support also DMI log file for ICL-P0.
    compare_trans_l(
        trans_l1 => get_filtered_cmds($opio_psf_file_scbd,"U",'(Msg).*\|1111_0111\|'),
        trans_l2 => get_filtered_cmds($opio_link_file_scbd,"U",'(Msg|MSG_D).*(\|0111 1111\||     7f )'),
        field_l  => ["id","data"], # FIXME: Add : data
        fail_count_zero => $has_OPIO_MCTP,
        field_comperator_l => ["id",\&big_hex_compare_func],
    );
}

if($skip_OPIO_LINK_err && $ACERUN_TESTNAME=~/\bPKGC1[012]\b/) {
    #FIXME: Skip OPIO_LINK checking for PKGC10 tests untill I will debug & fix the OPIO_LINK tracker.
    undef $opio_link_file_scbd;
}

my @DMI_or_OPIO_parms;

if($cpu_proj eq "adl") {
    if($opio_psf_file_scbd && !$opio_link_file_scbd) {
        # This is for ADL model that does not have OPIO_LINK file.
        $pcie_link_file_scbd_l[9] = $pcie_psf_file_scbd_l[9]  = $opio_psf_file_scbd;

        my $adl_fix = "";
        if($ACERUN_SYSTEM_MODEL=~/^(chassis_model_u42|chassis_mem_model_u42)$/) { 
            # This fix a problem is pkgc Osama tests in chassis_model_u42, were they write to the from opi with bad pcie_src. Osama did not fix it.
            $adl_fix = "|0000|   0"; 
        }
        @DMI_or_OPIO_parms = (
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"([40 ]900$adl_fix)",iop_pcie_src=>'[0 ]900',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"([40 ]901)",iop_pcie_src=>'[0 ]901',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"([40 ]902)",iop_pcie_src=>'[0 ]902',pcie_bus=>'undefdmi.'], # The DMI source
        );
     } elsif($dmi_psf_file_scbd && !$dmi_link_file_scbd) {
        # This is for ADL model that does not have OPIO_LINK file.
        $pcie_link_file_scbd_l[9] = $pcie_psf_file_scbd_l[9]  = $dmi_psf_file_scbd;

        @DMI_or_OPIO_parms = (
            [pcie_idx=>9,pcie_dst=>'[64]30[0-2]',pcie_src=>"....",iop_pcie_src=>'[ 04]30[0-2]',pcie_bus=>'undefdmi.'], # The DMI source
        );
     }

} elsif($opio_link_file_scbd) {
    my $rst_trans_l = get_filtered_cmds($opio_psf_file_scbd,"U",'(MSG|Msg).*(CPU_RST)');
    if(+@$rst_trans_l) {
        $pcie_psf_file_scbd_l[9]  = $opio_psf_file_scbd;
        print "pch_psf_file_scbd is active\n" if $debug>=3;
    }
    my $rst_trans_l = get_filtered_cmds($opio_link_file_scbd,"U",'(MSG|Msg).*(CPU_RST|8E20002A|8e20002a)');
    if(+@$rst_trans_l) {
        $pcie_link_file_scbd_l[9] = $opio_link_file_scbd;
        print "pch_link_file_scbd is active\n" if $debug>=3;
    }
    if($cpu_proj eq "rkl") {
      if($emulation_obj_file) {
        @DMI_or_OPIO_parms = (
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"0000",iop_pcie_src=>'0500',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"0001",iop_pcie_src=>'0501',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"0002",iop_pcie_src=>'0502',pcie_bus=>'undefdmi.'], # The DMI source
        );
      } else {
        @DMI_or_OPIO_parms = (
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"2480",iop_pcie_src=>'0500',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"2481",iop_pcie_src=>'0501',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4500)',pcie_src=>"2482",iop_pcie_src=>'0502',pcie_bus=>'undefdmi.'], # The DMI source
        );
      }
    } else {
        @DMI_or_OPIO_parms = (
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"2480",iop_pcie_src=>'[0 ]900',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"2481",iop_pcie_src=>'[0 ]901',pcie_bus=>'undefdmi.'], # The DMI source
            [pcie_idx=>9,pcie_dst=>'(6300|4900)',pcie_src=>"2482",iop_pcie_src=>'[0 ]902',pcie_bus=>'undefdmi.'], # The DMI source
        );
    }
} elsif($dmi_link_file_scbd) {
    if($cpu_proj ne "lnl") {
        my $rst_trans_l = get_filtered_cmds($dmi_psf_file_scbd,"U",'(MSG|Msg).*CPU_RST');
        if(+@$rst_trans_l) {
            $pcie_psf_file_scbd_l[9]  = $dmi_psf_file_scbd;
            print "pch_psf_file_scbd is active\n" if $debug>=3;
        }
    }
    my $rst_trans_l = get_filtered_cmds($dmi_link_file_scbd,"U",'(MSG|Msg).*CPU_RST');
    if(+@$rst_trans_l or $cpu_proj eq "lnl") {
        $pcie_link_file_scbd_l[9] = $dmi_link_file_scbd;
        print "pch_psf_file_scbd is active\n" if $debug>=3;
    }
    @DMI_or_OPIO_parms = (
        [pcie_idx=>9,pcie_dst=>'[64]30[0-2]',pcie_src=>"....",iop_pcie_src=>'[ 04]30[0-2]',pcie_bus=>'undefdmi.'], # The DMI source
    );
}

$pch_pcie_link_file_scbd = $pcie_link_file_scbd_l[9]; # This is the DMI or OPIO link log file

#
# This loop all PCIE channels. Each chennel has source & dest ID and it bus ranges.

my @PEGS_parms;

if($cpu_proj eq "rkl") {
    if($cpu_proj_step eq "rkl-p") {
        @PEGS_parms = (
            [pcie_idx=>10,pcie_dst=>'450[10]',pcie_src=>"....",iop_pcie_src=>'050[01]',pcie_bus=>'10.',D=>1,F=>0],
            [pcie_idx=>11,pcie_dst=>'451[10]',pcie_src=>"....",iop_pcie_src=>'051[01]',pcie_bus=>'undef11.',D=>1,F=>1],
            [pcie_idx=>12,pcie_dst=>'4920',pcie_src=>"....",iop_pcie_src=>'0920',pcie_bus=>'undef12.',D=>1,F=>2],
            [pcie_idx=>60,pcie_dst=>'452[10]',pcie_src=>"....",iop_pcie_src=>'052[01]',pcie_bus=>'undef60.',D=>6,F=>0],
        );
    } else {
    @PEGS_parms = (
        [pcie_idx=>10,pcie_dst=>'4900',pcie_src=>"....",iop_pcie_src=>'[0 ]900',pcie_bus=>'10.',D=>1,F=>0],
        [pcie_idx=>11,pcie_dst=>'4910',pcie_src=>"....",iop_pcie_src=>'[0 ]910',pcie_bus=>'undef11.',D=>1,F=>1],
        [pcie_idx=>12,pcie_dst=>'4920',pcie_src=>"....",iop_pcie_src=>'[0 ]920',pcie_bus=>'undef12.',D=>1,F=>2],
        [pcie_idx=>60,pcie_dst=>'412[10]',pcie_src=>"....",iop_pcie_src=>'[0 ]12[01]',pcie_bus=>'undef60.',D=>6,F=>0],
    );
    }
} elsif($cpu_proj eq "adl") {
    if($dmi_link_file_scbd || $dmi_psf_file_scbd) {
        @PEGS_parms = (
            [pcie_idx=>10,pcie_dst=>'590[10]',pcie_src=>"....",iop_pcie_src=>'190[01]',pcie_bus=>'10.',D=>1,F=>0],
            [pcie_idx=>11,pcie_dst=>'591[10]',pcie_src=>"....",iop_pcie_src=>'191[01]',pcie_bus=>'undef11.',D=>1,F=>1],
            [pcie_idx=>12,pcie_dst=>'592[01]',pcie_src=>"....",iop_pcie_src=>'192[01]',pcie_bus=>'undef12.',D=>1,F=>2],
            [pcie_idx=>60,pcie_dst=>'593[10]',pcie_src=>"....",iop_pcie_src=>'193[01]',pcie_bus=>'undef60.',D=>6,F=>0],
            [pcie_idx=>62,pcie_dst=>'591[10]',pcie_src=>"....",iop_pcie_src=>'193[01]',pcie_bus=>'undef62.',D=>6,F=>2],
        );
    } else {
       @PEGS_parms = (
           [pcie_idx=>10,pcie_dst=>'4900',pcie_src=>"....",iop_pcie_src=>'[10 ]900',pcie_bus=>'10.',D=>1,F=>0],
           [pcie_idx=>11,pcie_dst=>'4910',pcie_src=>"....",iop_pcie_src=>'[10 ]910',pcie_bus=>'undef11.',D=>1,F=>1],
           [pcie_idx=>12,pcie_dst=>'4920',pcie_src=>"....",iop_pcie_src=>'[10 ]920',pcie_bus=>'undef12.',D=>1,F=>2],
           [pcie_idx=>60,pcie_dst=>'493[10]',pcie_src=>"....",iop_pcie_src=>'[10 ]93[01]',pcie_bus=>'undef60.',D=>6,F=>0],
           [pcie_idx=>62,pcie_dst=>'491[10]',pcie_src=>"....",iop_pcie_src=>'[10 ]91[01]',pcie_bus=>'undef62.',D=>6,F=>2],
       );
    }
} else {
    @PEGS_parms = (
        [pcie_idx=>10,pcie_dst=>'4900',pcie_src=>"....",iop_pcie_src=>'[0 ]900',pcie_bus=>'10.',D=>1,F=>0],
        [pcie_idx=>11,pcie_dst=>'4910',pcie_src=>"....",iop_pcie_src=>'[0 ]910',pcie_bus=>'undef11.',D=>1,F=>1],
        [pcie_idx=>12,pcie_dst=>'4920',pcie_src=>"....",iop_pcie_src=>'[0 ]920',pcie_bus=>'undef12.',D=>1,F=>2],
        [pcie_idx=>60,pcie_dst=>'4930',pcie_src=>"....",iop_pcie_src=>'[0 ]930',pcie_bus=>'undef60.',D=>6,F=>0],
    );
}

for my $pcie_parms (
        # PCIE TBT parms:
        [pcie_idx=>0 ,pcie_dst=>'4700',pcie_src=>"....",iop_pcie_src=>'0700',pcie_bus=>'1.',D=>7,F=>0],
        [pcie_idx=>1 ,pcie_dst=>'4710',pcie_src=>"....",iop_pcie_src=>'0710',pcie_bus=>'2.',D=>7,F=>1],
        [pcie_idx=>2 ,pcie_dst=>'4730',pcie_src=>"....",iop_pcie_src=>'0730',pcie_bus=>'3.',D=>7,F=>2],
        [pcie_idx=>3 ,pcie_dst=>'4740',pcie_src=>"....",iop_pcie_src=>'0740',pcie_bus=>'4.',D=>7,F=>3],
        @PEGS_parms,
        @DMI_or_OPIO_parms,
        ) {

    my %pcie_hash = @$pcie_parms;
    my $pcie_idx = $pcie_hash{pcie_idx};
    my $pcie_dst = $pcie_hash{pcie_dst}   or die_ERROR("104 ERROR: ");
    my $pcie_src = $pcie_hash{pcie_src}   or die_ERROR("105 ERROR: ");
    my $iop_pcie_src = $pcie_hash{iop_pcie_src}   or die_ERROR("106 ERROR: ");
    my $pcie_bus = $pcie_hash{pcie_bus}   or die_ERROR("107 ERROR: ");
    my $this_pcie_psf_file_scbd = $pcie_psf_file_scbd_l[0+$pcie_idx];
    my $this_pcie_link_file_scbd = $pcie_link_file_scbd_l[0+$pcie_idx];
    my $is_pch  = ($pcie_idx==9); # is opio or dmi
    my @EXCLUDE_FOR_OPIO1 = ();
    my @EXCLUDE_FOR_OPIO2 = ();
    my @ADL_EXCLUDE_FOR_OPIO3 = ();
    my $skip_psf_to_link_chk = ($cpu_proj eq "adl" and $pcie_idx=~/^(10|11|12|60|62|9)$/);
    if(!defined($this_pcie_psf_file_scbd) && !defined($this_pcie_link_file_scbd)) { next }

    if($is_pch ) {
        #filter the NPK MTB range
        my $exclude_range_l = [
                {BASE=>$PCIE_CFG_SPACE->{$NPK_DID}->{0}->{RTIT_BASE},LIMIT=>$PCIE_CFG_SPACE->{$NPK_DID}->{0}->{RTIT_LIMIT}},
        ];
        my @exclude_devices;
        while(my ($D_name,$DID_FID) = each(%all_DID_h)) { 
            if($D_name && $DID_FID) { 
                my ($DID,$FID,$DEVEN_bit) = @$DID_FID;
                # Skip all CfgWr to all knows devices
                if(!defined($DEVEN_bit) or !defined($PCIE_CFG_SPACE->{0}->{0}->{DEVEN}) or get_field(chkget_reg_val_in_tick($PCIE_CFG_SPACE->{0}->{0}->{DEVEN},undef),$DEVEN_bit,$DEVEN_bit)) {
                    push @exclude_devices,sprintf("00:0%1x:0 ",$DID); 
                }
                # Skip MWr & MRd to BARs of known devices
                for my $bar_index (0..$bar_max_index) {
                    if($PCIE_CFG_SPACE->{$DID}->{$FID}->{$bar_index}->{BASE} && $PCIE_CFG_SPACE->{$DID}->{$FID}->{$bar_index}->{LIMIT}) {
                        my $h = {BASE=>$PCIE_CFG_SPACE->{$DID}->{$FID}->{$bar_index}->{BASE},LIMIT=>$PCIE_CFG_SPACE->{$DID}->{$FID}->{$bar_index}->{LIMIT}};
                        if($PCIE_CFG_SPACE->{$DID}->{$FID}->{PMCS}) { $h->{PMCS} = $PCIE_CFG_SPACE->{$DID}->{$FID}->{PMCS}; }
                        if($PCIE_CFG_SPACE->{$DID}->{$FID}->{GCMD}) { $h->{GCMD} = $PCIE_CFG_SPACE->{$DID}->{$FID}->{GCMD}; }
                        my $is_DEVEN = 1;
                        push @$exclude_range_l , $h;
                    }
                }
            } 
        }
        push @EXCLUDE_FOR_OPIO1,( exclude_range_l => $exclude_range_l );
        my $exclude_str = join("|",("00:00:[0-7] ",@exclude_devices));
        push @EXCLUDE_FOR_OPIO2,(exclude=>"($exclude_str)");

        push @ADL_EXCLUDE_FOR_OPIO3,(exclude => '\|4009/');
    }

    # Analyze the PCIE CfgWr to find PCIE PMBASE/LIMIT registers
    if(defined($this_pcie_psf_file_scbd)) {
        pcie_registers_parse(PCIE_DEVICE=>$pcie_hash{D},PCIE_FUNCTION=>$pcie_hash{F},trans_l1=>get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"D",'(CfgWr)'));
    } elsif($cpu_proj eq "lnl" and $emulation_obj_file) {
    } else {
        pcie_registers_parse(PCIE_DEVICE=>$pcie_hash{D},PCIE_FUNCTION=>$pcie_hash{F},trans_l1=>get_filtered_cmds($iop_psf_file_scbd,"U",'(CfgWr)'));
    }
    my $is_pcie_GCMD_MBE   = get_reg_val_in_tick($PCIE_CFG_SPACE->{$pcie_hash{D}}->{$pcie_hash{F}}->{GCMD},0xFFFF_FFFF) & 2; # Check whether This PCIE ROOT has BUS-MASTER-ENABLED.
    my $is_pcie_MPC_MCTPSE = get_reg_val_in_tick($PCIE_CFG_SPACE->{$pcie_hash{D}}->{$pcie_hash{F}}->{MPC} ,0xFFFF_FFFF) & 8; # 

    if($pch_pcie_link_file_scbd && $this_pcie_link_file_scbd && !$is_pch
            && ($dmi_link_file_scbd || $opio_link_file_scbd) # It must be a read DMI or OPI link file in order to do these MCTP checks.
            # Enable rkl MCTP #&& $cpu_proj ne "rkl" #FIXME:esinuani: Temporarily diable MCTP checking in rkl
        ) {
        #FIXME:Need to support also DMI log file for ICL-P0.

        print "001 COMP_FLOW: Comparing U MsgD transaction from PCH to pcie$pcie_idx\n" if $debug >= 1;

        my $mctp_exclude_func_U_l =     [{func=>\&filter_MCTP_MsgD,is_from_pch=>1}];
        my $mctp_exclude_func_U_pch_l = [{func=>\&filter_MCTP_MsgD,is_from_pch=>1,D=>$pcie_hash{D},F=>$pcie_hash{F}}];

        compare_trans_l(
            trans_l1 => get_filtered_cmds($pch_pcie_link_file_scbd ,"U",'(Msg|MSG)',exclude_func_l=>$mctp_exclude_func_U_pch_l),
            trans_l2 => get_filtered_cmds($this_pcie_link_file_scbd,"D",'(Msg|MSG)',exclude_func_l=>$mctp_exclude_func_U_l),
            field_l  => ["BDF","length","cmd","id","data"],
        ) if($is_pcie_GCMD_MBE && $is_pcie_MPC_MCTPSE);

        print "014 COMP_FLOW: Comparing D MsgD transaction from pcie$pcie_idx to PCH\n" if $debug >= 1;

        my $mctp_exclude_func_D_l     = [{func=>\&filter_MCTP_MsgD,is_from_pch=>0,D=>$pcie_hash{D},F=>$pcie_hash{F}}];
        my $mctp_exclude_func_D_pch_l = [{func=>\&filter_MCTP_MsgD,is_from_pch=>0,D=>$pcie_hash{D},F=>$pcie_hash{F}}];

        compare_trans_l(
            trans_l1 => get_filtered_cmds($this_pcie_link_file_scbd,"U",'(Msg|MSG)',exclude_func_l=>$mctp_exclude_func_D_l),
            trans_l2 => get_filtered_cmds($pch_pcie_link_file_scbd ,"D",'(Msg|MSG)',exclude_func_l=>$mctp_exclude_func_D_pch_l),
            field_l  => ["BDF","length","cmd","id","data"],
        ) if($is_pcie_GCMD_MBE && $is_pcie_MPC_MCTPSE);

    }

    # Enable rkl MCTP #if($cpu_proj ne "rkl") { #FIXME:esinuani: Temporarily diable MCTP checking in rkl until PEG60 will work.
    if($opio_link_file_scbd && !$is_pch && $this_pcie_psf_file_scbd) {

        print "002 COMP_FLOW: Comparing U MsgD3 transaction from OPIO to pcie$pcie_idx\n" if $debug >= 1;

        compare_trans_l(
            trans_l1 => get_filtered_cmds($this_pcie_psf_file_scbd,"D",'(MsgD3).*\|1111_0111\|'),
            trans_l2 => get_filtered_cmds($opio_link_file_scbd,"U",'(MsgD3).*\|0111 1111\|'),
            field_l  => ["data","cmd","id"],
        );

    }
    # Enable rkl MCTP #}

    my $iop_or_PCF5_psf_file_scbd_or = $iop_psf_file_scbd;
    $iop_or_PSF5 = 1;

    if(defined($PSF5_psf_file_scbd) && !defined($iop_psf_file_scbd)) {
        $iop_or_PCF5_psf_file_scbd_or = $PSF5_psf_file_scbd;
        $iop_or_PSF5 = 0;
    }

    if($this_pcie_psf_file_scbd && !$skip_psf_to_link_chk) {

    print "003 COMP_FLOW: Comparing U MWr transaction between pcie$pcie_idx ti IOP\n" if $debug >= 1;

    compare_trans_l(
        trans_l1 => get_filtered_cmds($this_pcie_psf_file_scbd,"U",'\| *(MWr).*/'.$pcie_src.'\|',@ADL_EXCLUDE_FOR_OPIO3),
        trans_l2 => get_filtered_cmds($iop_or_PCF5_psf_file_scbd_or,($iop_or_PSF5?"D":"U"),'\| *(MWr).*/'.$iop_pcie_src.'\|'),
        field_l  => \@pcie_compare_field_l,
    );

    print "004 COMP_FLOW: Comparing U MRd transaction between pcie$pcie_idx ti IOP\n" if $debug >= 1;

    compare_trans_l(
        trans_l1 => get_filtered_cmds($this_pcie_psf_file_scbd,"U",'(MRd).*/'.$pcie_src.'\|'),
        trans_l2 => get_filtered_cmds($iop_or_PCF5_psf_file_scbd_or,($iop_or_PSF5?"D":"U"),'(MRd).*/'.$iop_pcie_src.'\|'),
        field_l  => \@pcie_compare_field_l,
    );
    
    print "006 COMP_FLOW: Comparing D MWr transaction between IOP to PCIE$pcie_idx\n" if $debug >= 1;

    compare_trans_l(
        trans_l1 => get_filtered_cmds($iop_or_PCF5_psf_file_scbd_or,($iop_or_PSF5?"U":"D"),'\| *(MWr).*\|'.$pcie_dst.'/',@EXCLUDE_FOR_OPIO1),
        trans_l2 => get_filtered_cmds($this_pcie_psf_file_scbd,"D",'\| *(MWr)'),
        field_l  => \@pcie_compare_field_l,
    )  if !$skip_iop_D_mem_chk;

    if(!$emulation_obj_load_time) { #FIXME: Exclude this check from emulation because GMM CfgWr transactions used to because emulation switch DEVEN.D8EN during the test. Maybe re-enable it

    print "013 COMP_FLOW: Comparing D MRd transaction between IOP to PCIE$pcie_idx\n" if $debug >= 1;

    compare_trans_l(
        trans_l1 => get_filtered_cmds($iop_or_PCF5_psf_file_scbd_or,($iop_or_PSF5?"U":"D"),'\| *(CAS|Swap|FAdd|IOWr|IORd|MRd|CfgWr|CfgWr).*\|'.$pcie_dst.'/',@EXCLUDE_FOR_OPIO2,@EXCLUDE_FOR_OPIO1),
        trans_l2 => get_filtered_cmds($this_pcie_psf_file_scbd,"D",'\| *(CAS|Swap|FAdd|IOWr|IORd|MRd|CfgWr|CfgWr)',exclude=>"(00:00:[0-7] )"),
        field_l  => \@pcie_compare_field_l,
    );

    }

    if(!$is_pch and $cpu_proj ne "adl") { # Drop this check in ADL.

    print "007 COMP_FLOW: Comparing D Cpl transaction between IOP to PCIE$pcie_idx\n" if $debug >= 1;

    compare_trans_l(
        trans_l1 => get_filtered_cmds($iop_or_PCF5_psf_file_scbd_or,($iop_or_PSF5?"U":"D"),'(Cpl).*\|'.$pcie_dst.'/'),
        trans_l2 => get_filtered_cmds($this_pcie_psf_file_scbd,"D",'(Cpl)'),
        field_l  => \@pcie_compare_field_l,
    );

    } # if($is_pch and $cpu_proj ne "adl) 

    } # if($this_pcie_psf_file_scbd && !$skip_psf_to_link_chk)

    my $pcie_link_read__byte_stream_l;

    if(defined($pcie_link_file_scbd_l[$pcie_idx])&& defined($pcie_psf_file_scbd_l[$pcie_idx]) && $pcie_link_file_scbd_l[$pcie_idx]->{filename} ne $pcie_psf_file_scbd_l[$pcie_idx]->{filename} && $cpu_proj ne "adl") {

        print "009 COMP_FLOW: Compare all D MWr from TBT PCIE PSF to TBT PCIE LINK\n" if $debug >= 1;

        my @D_exclude_range_l = get_pcie_D_exlude_range_l(PCIE_DEVICE=>$pcie_hash{D}, PCIE_FUNCTION=>$pcie_hash{F});

        compare_write_byte_stream_l(
            trans_l1 => create_byte_stream(trans_l=>get_filtered_cmds($pcie_link_file_scbd_l[$pcie_idx],"D",'(MEM_WR|MWr).*')),
            trans_l2 => create_byte_stream(trans_l=>get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"D",'\| *(MWr).*',PCIE_DEVICE=>$pcie_hash{D}, PCIE_FUNCTION=>$pcie_hash{F},exclude_range_l=>[@D_exclude_range_l])),
            field_l  => ["id","data","address"], #FIXME: Need to finish All PCIE BFM checkings later.
            #fail_count_zero => 1,
        );
    } # if(defined($pcie_link_file_scbd_l[$pcie_idx])&& defined($pcie_psf_file_scbd_l[$pcie_idx]))

    my $pcie_link_byte_trans_l_;

    if(is_scbd_exists($pcie_link_file_scbd_l[$pcie_idx])) {
       my $pcie_link_write_byte_trans_l  = get_filtered_cmds($pcie_link_file_scbd_l[$pcie_idx],"U",'(MEM_WR|MWr|SWAP|Swap|FETCH_ADD|FAdd|CAS).*',cmd=>"MWr",exclude_range_l=>[$msi_range],exclude_func_l=>[{func=>\&filter_UR_trans}]);
       my $pcie_link_read__byte_trans_l  = get_filtered_cmds($pcie_link_file_scbd_l[$pcie_idx],"U",'(MEM_RD|MRd).*',exclude_range_l=>[$msi_range,@skip_DPR_changing_range],exclude_func_l=>[{func=>\&filter_UR_trans}]);
       $pcie_link_byte_trans_l_       = filter_cmd_l(trans_l=>$pcie_link_write_byte_trans_l,skip_iommu_no_conv=>1,iommu_scbd_h => $tbtpcie_iommu_scbd_h);
       my $pcie_link_read__byte_trans_l_ = filter_cmd_l(trans_l=>$pcie_link_read__byte_trans_l,skip_iommu_no_conv=>1,iommu_scbd_h => $tbtpcie_iommu_scbd_h);
       if($is_pch) {
           $pcie_link_byte_trans_l_      = $pcie_link_write_byte_trans_l;
           $pcie_link_read__byte_trans_l_= $pcie_link_read__byte_trans_l;
       } else {
           $pcie_link_byte_trans_l_      = filter_cmd_l(trans_l=>$pcie_link_write_byte_trans_l,skip_iommu_no_conv=>1,iommu_scbd_h => $tbtpcie_iommu_scbd_h);
           $pcie_link_read__byte_trans_l_= filter_cmd_l(trans_l=>$pcie_link_read__byte_trans_l,skip_iommu_no_conv=>1,iommu_scbd_h => $tbtpcie_iommu_scbd_h);
       }
       $pcie_link_write_byte_stream_l = create_byte_stream(trans_l=>$pcie_link_byte_trans_l_,PCIE_DEVICE=>7, PCIE_FUNCTION=>$pcie_idx );
       $pcie_link_read__byte_stream_l = create_byte_stream(trans_l=>$pcie_link_read__byte_trans_l_,PCIE_DEVICE=>7, PCIE_FUNCTION=>$pcie_idx );
    } # if(defined($pcie_link_file_scbd_l[$pcie_idx]))

    if(is_scbd_exists($pcie_link_file_scbd_l[$pcie_idx]) && is_scbd_exists($pcie_psf_file_scbd_l[$pcie_idx]) && !$skip_psf_to_link_chk) {

        print "010 COMP_FLOW: Compare TBT PCIE U input and outputs (Only MEM write opcodes)\n" if $debug >= 1;
        my $pcie_psf_write_byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"U",'\| *(MWr|SWAP|Swap|FAdd|CAS).*0...\|',cmd=>"MWr",exclude_range_l=>[$msi_range],exclude_func_l=>[{func=>\&filter_UR_trans}]));
        my $pcie_link_write_byte_stream_l = create_byte_stream(trans_l=>$pcie_link_byte_trans_l_,PCIE_DEVICE=>7, PCIE_FUNCTION=>$pcie_idx );
        compare_write_byte_stream_l(
            trans_l1 => $pcie_link_write_byte_stream_l,
            trans_l2 => $pcie_psf_write_byte_stream_l,
            field_l  => ["BDF","address","data"],
            field_comperator_l  => [ ],
            iommu_scbd_h => ($is_pch ? undef : $tbtpcie_iommu_scbd_h),
            #fail_count_zero => 1,
        ) ;

    } # if(defined($pcie_link_file_scbd_l[$pcie_idx] && $pcie_psf_file_scbd_l[$pcie_idx]))

    if(is_scbd_exists($pcie_link_file_scbd_l[$pcie_idx])&& is_scbd_exists($pcie_psf_file_scbd_l[$pcie_idx])) {

        print "015 COMP_FLOW: Compare TBT PCIE U input and outputs (Only MSI )\n" if $debug >= 1;
        compare_trans_l(
            trans_l1 => iommu_msi_conv_upstream(iommu_scbd_h => $tbtpcie_iommu_scbd_h,trans_l=>get_filtered_cmds($pcie_link_file_scbd_l[$pcie_idx],"U",'(MEM_WR|MWr).*',exclude_range_l=>[$low_non_msi_range,$high_non_msi_range])),
            #trans_l2 => get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"U",'\| *(MWr).*0...\|',exclude_range_l=>[$low_non_msi_range,$high_non_msi_range],exclude=>'\|0038_00\|'),
            trans_l2 => iommu_msi_conv_downstream(D=>$pcie_hash{D},F=>$pcie_hash{F},trans_l=>get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"A",'(MRd|MWr).*')),
            field_l  => ["BDF","id","data","address"],
            #field_comperator_l  => [ ],
            iommu_scbd_h => $tbtpcie_iommu_scbd_h,
            convert_flag=>"VTD_IRE",
            disable_size_check=>1,
            #fail_count_zero => 1,
        ) if($check_iommu_msi_conv && !$is_pch);

    } # if(defined($pcie_link_file_scbd_l[$pcie_idx])&& defined($pcie_psf_file_scbd_l[$pcie_idx]))

    # Make sure to add eacn pcie input stream only once.
    if(1==++$all_pcie_link_byte_stream_l_use_hash{$pcie_idx}) {

        if($cpu_proj eq "adl" && $pcie_idx==9 && $ACERUN_SYSTEM_MODEL=~/^chassis_model/) {
            # In ADL there is a DMI BFM bug were it sent bad transaction to IOP
            $pcie_link_byte_trans_l_ = filter_cmd_l(trans_l=>$pcie_link_byte_trans_l_ ,exclude_func_l=>[{func=>\&ADL_DMI_VCm_filter,label=>"filter DMI_VCm amd non-snoop transactions from DMI psf or link"}]);
        }

        if($pcie_link_byte_trans_l_) {
            my $non_WRC_pcie_link_byte_trans_l_ = [];
            my $to_WRC_pcie_link_byte_trans_l_ = [];
            # Split between ADL psf trnasactions that goes to WRC_IDI, and other psf transactions that goes to psf
            if($to_WRC_VC_h) {
                for my $rec_ptr (@$pcie_link_byte_trans_l_) {
                    my $VC_h = $pcie_link_file_scbd_l[$pcie_idx]->{VC_h};
                    if(!$VC_h) {
                        die_ERROR("108 ERROR: Can not find VC_h for $pcie_link_file_scbd_l[$pcie_idx]->{filename}.");
                    }
                    if(filter_WRC_psf_vc($rec_ptr,$VC_h)) {
                        push @$to_WRC_pcie_link_byte_trans_l_,$rec_ptr;
                    } else {
                        push @$non_WRC_pcie_link_byte_trans_l_,$rec_ptr;
                    }
                }
            } else {
                $non_WRC_pcie_link_byte_trans_l_ = $pcie_link_byte_trans_l_;
            }
            push @$all_pcie_link_write_byte_stream_l     , @{create_byte_stream(trans_l=>$non_WRC_pcie_link_byte_trans_l_,PCIE_DEVICE=>7, PCIE_FUNCTION=>$pcie_idx )};
            push @$all_WRC_pcie_link_write_byte_stream_l , @{create_byte_stream(trans_l=>$to_WRC_pcie_link_byte_trans_l_ ,PCIE_DEVICE=>7, PCIE_FUNCTION=>$pcie_idx )};
        }

        if($pcie_link_read__byte_stream_l) {
            push @$all_pcie_link_read__byte_stream_l , @$pcie_link_read__byte_stream_l;
        } elsif($pcie_psf_file_scbd_l[$pcie_idx]) {
            my $pcie_psf_read__byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($pcie_psf_file_scbd_l[$pcie_idx],"U",'\| *(MRd).*0...\|',exclude_range_l=>[$msi_range,@skip_DPR_changing_range]));
            push @$all_pcie_link_read__byte_stream_l , @$pcie_psf_read__byte_stream_l;
        }
    }

} # for my $pcie_parms

#for my $rec_ptr1 (@$all_pcie_link_write_byte_stream_l) {
#    print "EYAL1: address=$rec_ptr1->{address} data=$rec_ptr1->{data} : $rec_ptr1->{parent}->{line}";
#}

# Filter VGA P2P ranges
@vga_ranges_l = get_VGA_exclude_range_l();

if(+@vga_ranges_l) {
    print "Start  Filtering write transactions to VGA range.\n" if $debug>=3;
    if($all_pcie_link_write_byte_stream_l) {
        $all_pcie_link_write_byte_stream_l = filter_cmd_l(trans_l=>$all_pcie_link_write_byte_stream_l,exclude_range_l=>[@vga_ranges_l]);
    }
    print "Finish Filtering write transactions to VGA range.\n" if $debug>=3;
}


my $FILTER_MCC_WR_TRANS_FROM_IOP = '[FP]-WR';
my $FILTER_CMI_WR_TRANS_FROM_IOP = 'MWr.*IOP';
if(defined($mcc_trans_file_scbd) and $mcc_trans_file_scbd->{filename}=~/cmi/) {
    $FILTER_MCC_WR_TRANS_FROM_IOP= $FILTER_CMI_WR_TRANS_FROM_IOP;
}
if($cpu_proj eq "lnl") {
    $FILTER_MCC_WR_TRANS_FROM_IOP = undef;
}

# Exclude MBASE & PMBASE ranges because them will do p2p and not go to memory
my @EXCLUDE_PCIE_MBASE_RANGES = get_pcie_mbase_ranges();

if($use_iop_cmi_log) {
    $mcc_trans_file_scbd = $cmi_iop_trans_file_scbd;
}

my @hash_fliter_func_l = ();

my @DMI_VCm_fliter_func_l;

if($cpu_proj eq "adl" && $ACERUN_SYSTEM_MODEL=~/^chassis_model/) {
    # In ADL there is a DMI BFM bug were it sent bad transaction to IOP (were ch=VCm and non-snoop=0)
    push @DMI_VCm_fliter_func_l,{func=>\&ADL_IOP_DMI_VCm_filter};
}

if(@mcc_trans_file_scbd_l>=2) {
    if($cpu_proj eq "adl") {
        $ADL_cmi_addr_h = create_ADL_cmi_addr_h($mcc_trans_file_scbd_l[1]);
        push @hash_fliter_func_l,{func=>\&ADL_cmi_hash_filter,hash_idx=>99,addr_h=>$ADL_cmi_addr_h};
    } elsif($cpu_proj eq "lnl") {
        push @hash_fliter_func_l,{func=>\&lnl_hbo_hash_filter};
    } else {
        if(!$soc_mc_hash_disable) { push @hash_fliter_func_l,{func=>\&cmi_hash_filter,hash_idx=>99}; }
    }
}

if(defined($mcc_trans_file_scbd) && !$skip_IOP_to_mcc_check && !$skip_e2e_write_chk) {

    if($cpu_proj eq "adl") {
        print "011.1 COMP_FLOW: Compare all kind of IDI_WRC to IOP_soc upstream writes.\n" if $debug >= 1;
        # FIXME: Need to use compare_write_byte_stream_l her eand mack sure that is update the tick_mc field
        if($WRC_VC_filter) {
            my $trans_l1 = get_filtered_cmds($iop_psf_file_scbd,"D",'\| *(MWr|Swap|FAdd).*'.$WRC_VC_filter,cmd=>"MWr",label=>"Filter IOP MWr PSF for 011.1 COMP_FLOW:",exclude_range_l => [$msi_range,$all_imr_range,@EXCLUDE_PCIE_MBASE_RANGES,@vga_ranges_l,@IOP_not_dram_ranges_l]);
            my $trans_l2 = sort_WRC_trans_l(get_filtered_cmds($idi_file_scbd,"U",undef,cmd=>'(RFO|RDCURR|SPEC_ITOM)',label=>"Filter IDI_WRC for 011.1 COMP_FLOW:",exclude_func_l=>[{func=>\&filter_WRC_IDI}]));
            filter_cmd_l(trans_l=>$trans_l2,label=>"Filter after sort IDI_WRC for 011.1 COMP_FLOW:") if $debug>=9; # FIXME: Need to review

            compare_write_byte_stream_l(
                trans_l1 => $trans_l1,
                trans_l2 => $trans_l2,
                field_l  => ["address"],
                field_comperator_l  => [ "address"=>\&cl_address_cmp_func],
                add_self_parent => 1,
            );
        }

        if(@$trans_l1 == @$trans_l2) {
            for(my $i=0; $i<@$trans_l1; $i++) {
                $trans_l1->[$i]->{tick_go}  = $trans_l2->[$i]->{tick_go};
                $trans_l1->[$i]->{tick_end} = $trans_l2->[$i]->{tick_end};
            }
        }

    }

    print "011 COMP_FLOW: Compare all kind of WR in mcc_trans to IOP_soc upstream writes.\n" if $debug >= 1;

    for my $hash_idx (0..$#mcc_trans_file_scbd_l) {

        if($cpu_proj eq "lnl") { next }

        print "011.2 COMP_FLOW: Compare all kind of WR in mcc_trans to IOP_soc upstream writes.\n" if $debug >= 1;
        if(@hash_fliter_func_l) {
            $hash_fliter_func_l[0]->{hash_idx} = $hash_idx;
        } else {
            push @hash_fliter_func_l , {func=>\&filter_UR_trans};
        }

        if(@WRC_VC_filter_func_l) {
            $WRC_VC_filter_func_l[0]->{VC_h}     = $iop_psf_file_scbd->{VC_h}; 
            $WRC_VC_filter_not_func_l[0]->{VC_h} = $iop_psf_file_scbd->{VC_h}; 
        }

        my $trans_l1 = get_filtered_cmds($iop_psf_file_scbd,"D",'\| *(MWr|Swap|FAdd|CAS).*0...\|',cmd=>"MWr",label=>"Filter IOP PSF MWr for 011.2 COMP_FLOW:",exclude=>$WRC_VC_filter,exclude_range_l => [$msi_range,$all_imr_range,@EXCLUDE_PCIE_MBASE_RANGES,@vga_ranges_l,@IOP_not_dram_ranges_l],exclude_func_l=>[@hash_fliter_func_l,@DMI_VCm_fliter_func_l]);
        my $trans_l2 = get_filtered_cmds($mcc_trans_file_scbd_l[$hash_idx],"D",$FILTER_MCC_WR_TRANS_FROM_IOP,label=>"Filter CMI MWr for 011.2 COMP_FLOW:",exclude_range_l => [$mc_abort_range,@skip_DPR_changing_range]);

        compare_write_byte_stream_l(
            trans_l1 => $trans_l1,
            trans_l2 => $trans_l2,
            field_l  => ["address","data"],
            field_comperator_l  => [ "address"=>\&cl_address_cmp_func, "data"=>\&cl_data_cmp_func ],
            iommu_scbd_h => $IOP_iommu_scbd_h,
            link_to => "cmi_trans",
            add_self_parent => 1,
        );

        if(!$exit_code && $cpu_proj eq "adl") {
            # This loop fix the PCIE Atomic (FAdd,SWAP,CAS) handling of ADL when it writes full cache line while we need only 4 or 8 bytes).
            for my $rec_ptr (@$trans_l1) {
                if($rec_ptr->{cmi_trans}) {
                    ADL_fix_cl_data_func($rec_ptr,$rec_ptr->{cmi_trans});
                    delete $rec_ptr->{cmi_trans};
                } else {
                    die_ERROR("070 ERROR: No cmi_link for ".trans_str($rec_ptr));
                }
            } 
        }

    }

}

# Compare all kind of WR in mcc_trans to PCIE LINK inputs upstream writes

# Since many test has TBT DMA stimuli, I add a TBT DMA stimuli to the list
if($skip_TBTDMA_PSF) {
    # Add TBT DMA stimuli from PSF5 log (this is in order to workaround a bug of bad TBT DMA PSF log file).
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($PSF5_psf_file_scbd,"U",'\| *(MWr).*\|\d\d\d\d/07[25]0\|',exclude_range_l=>[$msi_range]) );
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
} else {
    # Add TBT DMA stimuli from DMA PSF log
    for my $scbd (@tbtdma_psf_file_scbd_l) {
        my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",'\| *(MWr).*\|',exclude_range_l=>[$msi_range]) );
        push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
    }
}

if($skip_pep_svt_file) {
    $pep_svt_link_file_scbd = undef;
} else {
    $pep_psf_file_scbd = undef;
}

# Add GMM stream
for my $scbd (@more_psf_file_scbd,$npk_psf_file_scbd,$pep_psf_file_scbd,$pegs_psf_file_scbd,$tcss_psf_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    if(@WRC_VC_filter_func_l) {
        $WRC_VC_filter_func_l[0]->{VC_h}     = $scbd->{VC_h}; 
        $WRC_VC_filter_not_func_l[0]->{VC_h} = $scbd->{VC_h}; 
    }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",'\| *(MWr|Swap|FAdd|CAS).*0...\|',cmd=>"MWr",label=>"FILTER_IO_WR_to_CMI:",exclude_range_l=>[$msi_range,$iocce_mktme_range],exclude_func_l=>[@WRC_VC_filter_func_l]));
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
    if(@WRC_VC_filter_not_func_l) {
        my $WRC_byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",'\| *(MWr|Swap|FAdd|CAS).*0...\|',cmd=>"MWr",label=>"FILTER_IO_WR_to_WRC_IDI:",exclude_range_l=>[$msi_range],exclude_func_l=>[@WRC_VC_filter_not_func_l]));
        push @$all_WRC_pcie_link_write_byte_stream_l , @$WRC_byte_stream_l;
    }
}

# Add Writes from LNL CXL logs
for my $scbd ($cxl_idi_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>"(DirtyEvict|WOWrInv|WIL|SNPINV|SNPDATA|SNPCURR|BACKINV)",exclude_range_l=>[$msi_range],label=>"writes in cxl.log scbd"),label=>"writes in cxl.log scbd"); # , src_ch=>"PEP_HOST_dma"
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
}

# Assign URI to AXI AWADDR transactions by matching AXI to CFI writes
if(!$skip_e2e_write_chk && !$skip_e2e_axi_write_chk) {
for my $axi_port ("IPU","VPU") {
    my $axi_trans_l1; 
    my $axi_trans_l2; 
    my $axi_byte_l1; 
    my $axi_byte_l2; 
    print "015.1 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI. prapare l1\n" if $debug >= 1;
    for my $scbd (@axi_file_scbd_l) {
        if(!is_scbd_exists($scbd)) { next; }
        next unless (($scbd->{axi_port}=~/$axi_port/i));
        my $trans_l1 = get_filtered_cmds($scbd,"U",undef,cmd=>"AWADDR",exclude_range_l=>[$msi_range],label=>"Filter writes in axi scbd for URI match");
        push @$axi_trans_l1,@$trans_l1;
        my $byte_l1 = create_byte_stream(trans_l=>$trans_l1,label=>"writes in axi scbd for 015.1 COMP");
        push @$axi_byte_l1 , @$byte_l1;
    }
    print "015.2 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI. prapare l2\n" if $debug >= 1;
    for my $scbd ($cfi_trk_file_scbd) {
        if(!is_scbd_exists($scbd)) { next; }
        my $trans_l2 = get_filtered_cmds($scbd,"U",undef,cmd=>'(MemWrPtl|MemWr)',Unit=>"^(SOC_$axi_port)",exclude_range_l=>[$msi_range],label=>"List of SOC_VPU write command for URI match");
        push @$axi_trans_l2,@$trans_l2;
        my $byte_l2 = create_byte_stream(trans_l=>$trans_l2,label=>"List of VPU CFI write command that was sent to HBO for 015.2 COMP");
        push @$axi_byte_l2, @$byte_l2;
    }

    print "015.3 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI.\n" if $debug >= 1;

    #local $skip_uri_chk=1; # disable use check only for this compare.

    if(defined($axi_byte_l1) and defined($axi_byte_l2)) {
        my $grouped_axi_byte_l = [$axi_byte_l1,$axi_byte_l2];
        $grouped_axi_byte_l = group_write_check_trans($grouped_axi_byte_l,undef) unless $argv{skip_group_trans_bytes};

        compare_write_byte_stream_l(
            trans_l1 => $grouped_axi_byte_l->[0],
            trans_l2 => $grouped_axi_byte_l->[1],
            field_l  => ($argv{skip_axi_compare_timing_chk} ? ["address","data"] : ["address","data","timing"]),
            field_comperator_l  => [ "timing"=>\&axi_timing_compare_func ],
            update_func => \&axi_uri_update_func,
        ) if(defined($axi_byte_l1));

        # set URI for al AXI transctions
        if(!$exit_code && $debug>=3) {
            for my $rec_ptr1 (@$axi_trans_l1) {
                if(defined $rec_ptr1->{uri}) {
                    $rec_ptr1->{line} = $rec_ptr1->{uri}.":".$rec_ptr1->{line};
                }
            }
        }

        print "015.4 COMP_FLOW: DONE. Compare AXI to CFI transactions in order to match the URI.\n" if $debug >= 1;

    } # if(defined($axi_byte_l1) and defined($axi_byte_l2))
} # for ...
} # if(!$skip_e2e_write_chk && !$skip_e2e_axi_write_chk)

# Assign URI to AXI ARADDR transactions by matching AXI to CFI writes
if(0 && !$skip_e2e_write_chk && !$skip_e2e_axi_write_chk && $debug>=3) {
    my $axi_trans_l1; 
    my $axi_trans_l2; 
    my $axi_byte_l1; 
    my $axi_byte_l2; 
    local $skip_timeout_err = 0;
    local $do_e2e_warning_only = 1;
    local $exit_code = 0;
    local $script_max_time = time()+540; # give this check to run only 9 minutes
    
    
    print "015.5 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI. prapare l1\n" if $debug >= 1;
    for my $scbd (@axi_file_scbd_l) {
        if(!is_scbd_exists($scbd)) { next; }
        my $trans_l1 = get_filtered_cmds($scbd,"U",undef,cmd=>"ARADDR",exclude_range_l=>[$msi_range],label=>"Filter writes in axi scbd for URI match");
        push @$axi_trans_l1,@$trans_l1;
        my $byte_l1 = create_byte_stream(trans_l=>$trans_l1,label=>"writes in axi scbd for 015.1 COMP");
        push @$axi_byte_l1 , @$byte_l1;
    }
    print "015.6 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI. prapare l2\n" if $debug >= 1;
    for my $scbd ($cfi_trk_file_scbd) {
        if(!is_scbd_exists($scbd)) { next; }
        my $byte_l2 = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(RdCurr|MemRd)',Unit=>'^(SOC_VPU)',exclude_range_l=>[$msi_range],label=>"List of SOC_VPU write command for URI match"),label=>"List of VPU CFI write command that was sent to HBO for 015.2 COMP");
        push @$axi_byte_l2, @$byte_l2;
    }

    print "015.7 COMP_FLOW: Compare AXI to CFI transactions in order to match the URI.\n" if $debug >= 1;

    #local $skip_uri_chk=1; # disable use check only for this compare.

    compare_write_byte_stream_l(
        trans_l1 => $axi_byte_l1,
        trans_l2 => $axi_byte_l2,
        field_l  => ["address","data"],
        field_comperator_l  => [], #[ "address"=>\&mcc_address_compare_func ],
        update_func => \&axi_uri_update_func,
    ) if(defined($axi_byte_l1));

    # set URI for al AXI transctions
    if($debug>=3) {
        for my $rec_ptr1 (@$axi_trans_l1) {
            if(defined $rec_ptr1->{uri}) {
                $rec_ptr1->{line} = " ".$rec_ptr1->{uri}." ".$rec_ptr1->{line};
            }
        }
    }

    print "015.8 COMP_FLOW: DONE. Compare AXI to CFI transactions in order to match the URI.\n" if $debug >= 1;
}

# Add Writes from LNL AXI logs
for my $scbd (@axi_file_scbd_l) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>"AWADDR",exclude_range_l=>[$msi_range],label=>"writes in axi scbd"),label=>"writes in axi scbd"); # , src_ch=>"PEP_HOST_dma"
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
    @IOP_not_dram_ranges_l = (); #fixme: need to remove this.
}

# Add Writes from LNL GTCXL logs
for my $scbd (@gtcxl_file_scbd_l) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(MemWr|WrInv|ItoMWr|PushWr|_Snp)',exclude_range_l=>[$msi_range],label=>"writes in gtcxl scbd"),label=>"writes in gtcxl scbd"); # , src_ch=>"PEP_HOST_dma"
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
}

# Add CBB ufi agent writes
for my $scbd ($ufi_trk_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(WbMtoI|WbMtoE|WbMtoS|WbEtoI|SnpLInv|SnpLData|SnpLCode|SnpLFlush|SNPINV|SNPCODE|SnpData|SnpCode|SnpInvOwn)',exclude_range_l=>[$msi_range],exclude_func_l=>[{func=>\&filter_slfsnp_bad_and_ACF_IDI}],label=>"List of UFI agent write iMH"),label=>"List of UFI write command that was sent to iMC"); # , src_ch=>"PEP_HOST_dma"
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
}

# Add LNL MEDIA and IPU
for my $scbd ($cfi_trk_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(MemWrPtl|MemWr|DirtyEvict|WOWrInv|WIL|SNPINV|SNPDATA|SNPCURR|BACKINV)',Unit=>('^('.join("|",@CXL_CFI_FILTER_STR_l).')'),exclude_range_l=>[$msi_range],label=>"List of MEDIA write command that was sent to HBO"),label=>"List of MEDIA write command that was sent to HBO"); # , src_ch=>"PEP_HOST_dma"
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
}

# in compute mode add also writes that comes from d2d:
if($ACERUN_SYSTEM_MODEL=~/^soc_validation_model_compute/) {
    for my $scbd ($cfi_trk_file_scbd) {
        if(!is_scbd_exists($scbd)) { next; }
        my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(MemWrPtl|MemWr)',Unit=>'^(SOC_INOC_D2D)',exclude_range_l=>[$msi_range],label=>"List of D2D write command that was sent to HBO"),label=>"List of D2D write command that was sent to HBO"); # , src_ch=>"PEP_HOST_dma"
        push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
    }
}

my $ccf_write_byte_stream_l = []; 
my $atom_write_byte_stream_l = [];

# Add LNL CCF CFI writes
for my $scbd ($cfi_trk_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(WbMtoI|WbMtoE|WbMtoS|WbEtoI|SnpLInv|SnpLData|SnpLCode|SnpLFlush|SNPINV|SNPCODE)',src_ch_tc=>'SOC_CCF_LINK',exclude_range_l=>[$msi_range],label=>"List of CCF write command that was sent to HBO"),label=>"List of CCF write command that was sent to HBO"); # , src_ch=>"PEP_HOST_dma"
    push @$ccf_write_byte_stream_l , @$byte_stream_l;
}

# Add LNL atom transactions
if($cpu_proj eq "lnl") { for my $scbd ($idi_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    $atom_write_byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",undef,cmd=>'(WOWrInv|WIL|WBMTOI|WBMTOE|WCIL|ITOMWR|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SELFSNPINV|ITOMWR_WT|SNPCURR)',Unit=>$ICELAND_IDI,exclude_range_l=>[$msi_range,@not_dram_ranges_l,@prmrr_ranges_l,@idi_vga_ranges_l],label=>"List of ATOM write command that was sent to HBO"),label=>"List of ATOM write command that was sent to HBO"); # , src_ch=>"PEP_HOST_dma"
    push @$ccf_write_byte_stream_l , @$atom_write_byte_stream_l;
} }

# Add PEP link stream unless $skip_pep_svt_file
for my $scbd ($pep_svt_link_file_scbd) {
    if(!is_scbd_exists($scbd)) { next; }
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"D",'\sR\s+MRd',exclude_range_l=>[$msi_range])); # , src_ch=>"PEP_HOST_dma"
    #for my $rec_ptr1 (@$byte_stream_l) {
    #    print "EYAL5: address=$rec_ptr1->{address} data=$rec_ptr1->{data} : $rec_ptr1->{parent}->{line}";
    #}
    $byte_stream_l = filter_byte_stream_range_and_convert($byte_stream_l,\@pep_host_dma_range_l);
    #for my $rec_ptr1 (@$byte_stream_l) {
    #    print "EYAL6: address=$rec_ptr1->{address} data=$rec_ptr1->{data} : $rec_ptr1->{parent}->{line}";
    #}
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
    my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",'\sT\s+MWr')); # ,src_ch=>"PEP_HOST_direct")
    $byte_stream_l = filter_byte_stream_range_and_convert($byte_stream_l,\@pep_host_direct_range_l);
    push @$all_pcie_link_write_byte_stream_l , @$byte_stream_l;
}

# if we ar ein PV tests and no cfi file, then disable ther write check (because it needs the CFI file):
if(!($cfi_trk_file_scbd and $cfi_trk_file_scbd->{filename}) and $ACERUN_TESTNAME=~/soc_idle_power_test/) {
    $skip_e2e_write_chk = 1;
}

if(+@$all_pcie_link_write_byte_stream_l && !$skip_e2e_write_chk) {

    print "012 COMP_FLOW: Compare all kind of WR in mcc_trans to All PCIE link  inputs upstream writes.\n" if $debug >= 1;

    my $all_pcie_link_and_ccf_write_byte_stream_l = [];
    push @$all_pcie_link_and_ccf_write_byte_stream_l,@$all_pcie_link_write_byte_stream_l;
    push @$all_pcie_link_and_ccf_write_byte_stream_l,@$ccf_write_byte_stream_l;

    my $trans_l1_l;
    my $trans_l2_l;

    if(defined($use_write_update_file) && defined($gen_write_update_fie)) {
        die_ERROR("166 ERROR: you can not hane both use_write_update_file=$use_write_update_file and gen_write_update_file=$gen_write_update_file.");
    }
    
    while(!$exit_code) { # trying loop for $e2e_write_chk_use_uri
        my $commit_write_updates_l_l;
        local $skip_timeout_err = $skip_timeout_err;
        local $script_max_time  = $script_max_time;
        local $script_timeout = 0;
        my $grouped_byte_l = [ [] , [] ];

        if($e2e_write_chk_use_uri==10 && !$exit_code && !defined($use_write_update_file)) { # retry without $e2e_write_chk_use_uri
            $skip_timeout_err = 0;
            $script_max_time = time()+540; # give this check to run only 9 minutes
        }

        try {
            local $use_die_for_error = 1;

            for my $hash_idx (0..$#mcc_trans_file_scbd_l) {
                $hash_fliter_func_l[0]->{hash_idx} = $hash_idx if @hash_fliter_func_l;
                $grouped_byte_l->[$hash_idx]->[0]   = filter_cmd_l(trans_l=>$all_pcie_link_and_ccf_write_byte_stream_l,label=>"Filter All PCIE MWr for 012 COMP_FLOW:",exclude_range_l=>[$msi_range,get_pcie_exclude_range_l(),$all_imr_range,@IOP_not_dram_ranges_l,@mmio_ranges_l],iommu_scbd_h => $tbtpcie_iommu_scbd_h,exclude_func_l=>[@hash_fliter_func_l],is_full_dump=>($debug>=10)) unless $trans_l1_l->[$hash_idx];
                $trans_l1_l->[$hash_idx] = $grouped_byte_l->[$hash_idx]->[0];
                my $parent_trans_l2 = get_filtered_cmds($mcc_trans_file_scbd_l[$hash_idx],"D",$FILTER_MCC_WR_TRANS_FROM_IOP,label=>"Filter CMI MWr for 012 COMP_FLOW:",exclude_range_l=>[@skip_DPR_changing_range,$emu_transactor_cmd_range]);
                $grouped_byte_l->[$hash_idx]->[1]   = create_byte_stream(trans_l=>$parent_trans_l2,label=>"Convert CMI MWr for 012 COMP_FLOW:") unless $trans_l2_l->[$hash_idx];
                $trans_l2_l->[$hash_idx] = $grouped_byte_l->[$hash_idx]->[1];
                $grouped_byte_l->[$hash_idx] = group_write_check_trans($grouped_byte_l->[$hash_idx],undef) unless $argv{skip_group_trans_bytes};
                $commit_write_updates_l_l->[$hash_idx] = [];
                compare_write_byte_stream_l(
                    trans_l1 => $grouped_byte_l->[$hash_idx]->[0],
                    trans_l2 => $grouped_byte_l->[$hash_idx]->[1],
                    field_l  => ($e2e_write_chk_use_uri ? ["address","data","uri_if_any"] : ["address","data"]),
                    field_comperator_l  => [], #[ "address"=>\&mcc_address_compare_func ],
                    iommu_scbd_h => $tbtpcie_iommu_scbd_h,
                    is_mcc_log=>1,
                    write_updates_l=>($commit_write_updates_l_l->[$hash_idx]),
                    #fail_count_zero => 1,
                ) unless $use_write_update_file;

                use_update_write_file($use_write_update_file.$hash_idx,$commit_write_updates_l_l->[$hash_idx]) if $use_write_update_file;
                gen_update_write_file($gen_write_update_file.$hash_idx,$commit_write_updates_l_l->[$hash_idx]) if $gen_write_update_file && !$exit_code;

                last if($exit_code);
            }

        } catch {
            $exit_code = 1;

            if($e2e_write_chk_use_uri==10) {
                # use we are in the use-uri try , print the error as a warning
                local $do_e2e_warning_only = 1;
                print_ERROR($_);
            } else {
                # if we are not in the use uei trying mode, report error here 
                die_ERROR($_);
            }
        };

        if($e2e_write_chk_use_uri==10 && $exit_code) { # retry without $e2e_write_chk_use_uri
            $exit_code = 0;
            $e2e_write_chk_use_uri = 0;  undef $trans_l1_l; undef $trans_l2_l;
            print "WARNINIG: After e2e_write_chk_use_uri=1 failed, trying e2e_write_chk_use_uri=0\n";
            redo;
        }

        if($exit_code) { break; }

        # all ok by now, so commit the write changes
        for my $hash_idx (0..$#mcc_trans_file_scbd_l) {
            exec_update_write_l1($grouped_byte_l->[$hash_idx]->[0],$commit_write_updates_l_l->[$hash_idx]);
        }

        if(!$argv{skip_group_trans_bytes}) {
            # copy all the updates from $grouped_byte_l to 
            my $rec_ptr;
            my $parent_idx_h;
            my $par;
            for my $hash_idx (0..$#mcc_trans_file_scbd_l) {
                for $rec_ptr (@{$grouped_byte_l->[$hash_idx]->[0]}) {
                    if($rec_ptr->{parent}) {
                        $parent_idx_h->{$rec_ptr->{parent}->{idx}}->{tick_go}  = $rec_ptr->{tick_go}  if defined($rec_ptr->{tick_go});
                        $parent_idx_h->{$rec_ptr->{parent}->{idx}}->{tick_mc}  = $rec_ptr->{tick_mc}  if defined($rec_ptr->{tick_mc});
                        $parent_idx_h->{$rec_ptr->{parent}->{idx}}->{tick_end} = $rec_ptr->{tick_end} if defined($rec_ptr->{tick_end});
                    }
                }
            }
            for my $hash_idx (0..$#mcc_trans_file_scbd_l) {
                for $rec_ptr (@{$trans_l1_l->[$hash_idx]}) {
                    if($rec_ptr->{parent} and ($par = $parent_idx_h->{$rec_ptr->{parent}->{idx}})) {
                        $rec_ptr->{tick_go}  = $par->{tick_go}  if defined($par->{tick_go} );
                        $rec_ptr->{tick_mc}  = $par->{tick_mc}  if defined($par->{tick_mc} );
                        $rec_ptr->{tick_end} = $par->{tick_end} if defined($par->{tick_end});
                    }
                }
            }
        }

        # finish ok. do cleanups

        undef $trans_l1_l;
        undef $trans_l2_l;

        last; # finish ok. continue

    } # retry loop for $e2e_write_chk_use_uri



    if(defined($cmi_iop_trans_file_scbd)) {
        print "012 COMP_FLOW: Compare all kind of WR in cmi-iop-log to All PCIE link inputs upstream writes.\n" if $debug >= 1;
        
        compare_write_byte_stream_l(
            trans_l1 => filter_cmd_l(trans_l=>$all_pcie_link_and_ccf_write_byte_stream_l,exclude_range_l=>[$msi_range,get_pcie_exclude_range_l(),$all_imr_range,@IOP_not_dram_ranges_l],iommu_scbd_h => $tbtpcie_iommu_scbd_h),
            trans_l2 => create_byte_stream(trans_l=>get_filtered_cmds($cmi_iop_trans_file_scbd,"D",$FILTER_CMI_WR_TRANS_FROM_IOP,label=>"Filter CMI MWr for 012.3 COMP_FLOW:"),label=>"Convert CMI MWr for 012.3 COMP_FLOW:"),
            field_l  => ["address","data"],
            field_comperator_l  => [], #[ "address"=>\&mcc_address_compare_func ],
            iommu_scbd_h => $tbtpcie_iommu_scbd_h,
            is_cmi_log=>1,
            is_mcc_log=>($emulation_obj_file ? 1 : undef), # If we are in emulation, so there is no mcc)log file. So make cmi_log looks like MC, so it will update tick_mc and tick_end
            #fail_count_zero => 1,
        );

    }

    if(!$skip_e2e_pcie_read_chk && $argv{skip_if_non_snoop}) {
        # If we plan to check pcie, we need to find out which transaction has pcie non-snoop wr , and also any idi transaction
        for my $i (0..((+@$all_pcie_link_write_byte_stream_l)-1)) {
            my $rec_ptr = $all_pcie_link_write_byte_stream_l->[$i];
            if($rec_ptr->{parent}->{ns}) {
                mark_non_snoop_addr($rec_ptr->{parent});
            }
        }
    }
}

undef $ccf_write_byte_stream_l;

if(+@$all_WRC_pcie_link_write_byte_stream_l && !$skip_e2e_write_chk) {

    # This 012.2 COMP flow support ADL IOP-to-WRC_IDI transaction. 
    # (The ADL IOP-to-CMI transactions are handled by 012 COMP flow.)

    print "012.2 COMP_FLOW: Compare all kind of WR in IOP PSF to PCIE link inputs upstream writes that go to WRC_IDI.\n" if $debug >= 1;

    # This will give tick_go time to transaction in the $all_WRC_pcie_link_write_byte_stream_l for the soc_e2e_read_chk
    
    compare_write_byte_stream_l(
        trans_l1 => filter_cmd_l(trans_l=>$all_WRC_pcie_link_write_byte_stream_l
            ,label=>"Filter PCIE MWr PSF for 012.2 COMP_FLOW:"
            ,exclude_range_l=>[$msi_range,get_pcie_exclude_range_l(),$all_imr_range],iommu_scbd_h => $tbtpcie_iommu_scbd_h),
        trans_l2 => create_byte_stream(trans_l=>get_filtered_cmds($iop_psf_file_scbd,"D",'\| *(MWr|Swap|FAdd).*'.$WRC_VC_filter,cmd=>"MWr"
            ,label=>"Filter IOP MWr PSF for 012.2 COMP_FLOW:"
            ,exclude_range_l => [$msi_range,$all_imr_range,@EXCLUDE_PCIE_MBASE_RANGES]) ,label=>"Convert IOP MWr PSF for 012.2 COMP_FLOW:"),
        field_l  => ["address","data"],
        field_comperator_l  => [], #[ "address"=>\&mcc_address_compare_func ],
        iommu_scbd_h => $tbtpcie_iommu_scbd_h,
        is_cmi_log=>1,
        is_mcc_log=>($emulation_obj_file ? 1 : undef), # If we are in emulation, so there is no mcc)log file. So make cmi_log looks like MC, so it will update tick_mc and tick_end
        #fail_count_zero => 1,
    );

    # All transaction here, are considered idi writes. So they might affect NS checks
    if(!$skip_e2e_pcie_read_chk) {
        my $idi_trans_l = $all_WRC_pcie_link_write_byte_stream_l;
        # If we plan to check pcie, we need to find out which transaction has pcie non-snoop wr , and also any idi transaction
        for my $i (0..((+@$idi_trans_l)-1)) {
            my $rec_ptr = $idi_trans_l->[$i];
            my $addr6 = ($rec_ptr->{address}>>6);
            if($pch_non_snoop_addr_h{$addr6} and $rec_ptr->{data}) {
                $pch_non_snoop_addr_h{$addr6} |= 4; # Marck that there is an IDI write on this address
            }
        }
    }

}

undef @hash_fliter_func_l;
undef $ADL_cmi_addr_h;

$idi_file_scbd->{DMI_snp_h} = undef; # Free huge about of memory of this IDI URI hash.

sub compare_read_byte_channel($$$) {
        my ($filename,$read_byte_stream_l,$all_write_byte_stream_l) = @_;
        my $fork_pid_h;
        my $fork_core_l = ["0,4,8,16","1,5,9,17","2,6,10,18","3,7,11,19"];

        print "016 COMP_FLOW: Compare all Read from $filename against IDI & IO writes.\n" if $debug >= 1;

        my $source_split_read_l = source_split_read_byte_stream_l(trans_l=>$read_byte_stream_l);
        print "016.1 READ_CHs: Here are my read channels:\n" if $debug >= 2;
        for my $per_source_read_byte_stream_l (@$source_split_read_l) {
            if(@$per_source_read_byte_stream_l) { 
                my $rec_ptr1 = $per_source_read_byte_stream_l->[0];
                my $src_ch_tc = get_src_ch_tc($rec_ptr1) or die_ERROR("109 ERROR: ");
                print "016.2 READ_CH: read_ch:$ch_name_l[$src_ch_tc] trans_count=".(1*@$per_source_read_byte_stream_l)."\n" if $debug >= 2;
            }
        }
        my $src_ch_tc_idx=-1;
        for my $per_source_read_byte_stream_l (@$source_split_read_l) {
            $src_ch_tc_idx+=1;
            my $src_ch_tc;
            my $per_source_read_byte_stream_l_;
            if(@$per_source_read_byte_stream_l) { 
                if(!@$per_source_read_byte_stream_l) { next }
                my $rec_ptr1 = $per_source_read_byte_stream_l->[0];
                $src_ch_tc = get_src_ch_tc($rec_ptr1) or die_ERROR("110 ERROR: ");
                if(defined($do_e2e_read_channel) and !$do_e2e_read_channel->{$ch_name_l[$src_ch_tc]} and !$do_e2e_read_channel->{sprintf("%1d",$src_ch_tc_idx)}) {
                    next; 
                }
                if($skip_e2e_read_channel->{$ch_name_l[$src_ch_tc]} or $skip_e2e_read_channel->{sprintf("%1d",$src_ch_tc_idx)}) {
                    next; 
                }
                if($exit_code) {
                    print "017 COMP_FLOW: Skip src_ch_tc=$ch_name_l[$src_ch_tc] because exit code not zero\n"; 
                    next
                }
                if(!defined($rec_ptr1->{parent})) {
                    $per_source_read_byte_stream_l_ = create_byte_stream(trans_l=>$per_source_read_byte_stream_l,label=>"Convert 016.2 READ_CH: read_ch:$ch_name_l[$src_ch_tc]");
                    for my $rec_ptr (@$per_source_read_byte_stream_l) {
                        if($verify_parent_index and !defined($rec_ptr->{idx})) {
                            die_ERROR("154 ERROR: This transaction does not have parent index: ".trans_str($rec_ptr));
                        }
                    }
                } else {
                    $per_source_read_byte_stream_l_ = $per_source_read_byte_stream_l;
                    for my $rec_ptr (@$per_source_read_byte_stream_l) {
                        if($verify_parent_index and !defined($rec_ptr->{parent}->{idx})) {
                            die_ERROR("155 ERROR: This transaction does not have parent index: ".trans_str($rec_ptr));
                        }
                    }
                }
            }
            print "017 COMP_FLOW: Compare channel src_ch_tc=$ch_name_l[$src_ch_tc] all Read from $filename against IDI & IO writes. trans_count=".(1*@$per_source_read_byte_stream_l_)."\n" if $debug >= 0;
            if($is_nbace) {
                print "nbace '$0 -timeout=$script_timeout_param -cd $my_PWD -debug=2 -src_ch_tc=$ch_name_l[$src_ch_tc]'\n";
                next;
            }
            my $pid = -1;
            if(($debug==0 or $debug==2 && $is_dump_time)and !$do_e2e_read_channel) {
                while($fork_proc_count>=$argv{max_proc}) {
                    my $p = waitpid(-1,0);
                    if($fork_pid_h->{$p}) {
                        push @$fork_core_l,$fork_pid_h->{$p};
                        delete $fork_pid_h->{$p};
                        if($?>>8) { $exit_code=1; }
                        $fork_proc_count -= 1;
                        #print time().": process $p done exit=".$?."\n";
                        STDOUT->flush();
                    }
                }
                STDOUT->flush();
                $pid = fork();
                if(!defined($pid)) {
                    die_ERROR("173 ERROR: Bad fork");
                } if($pid==0) {
                    # this is the child process
                } else {
                    $fork_proc_count+=1;
                    $fork_pid_h->{$pid}=shift(@$fork_core_l);
                    #system("settask -c $fork_pid_h->{$pid} $pid");
                    #print time().": process $pid started cores=$fork_pid_h->{$pid} ".$ch_name_l[$src_ch_tc]."\n";
                    STDOUT->flush();
                    next;
                }
            }

            compare_read_byte_stream_l(
                trans_l1 => $all_write_byte_stream_l,
                trans_l2 => $per_source_read_byte_stream_l_,
                field_l  => ["address","data"],
                field_comperator_l  => [], #[ "address"=>\&mcc_address_compare_func ],
                #fail_count_zero => 1,
            );
            my $script_time = script_timeout_chk();
            my $ec = (defined($pid) and $pid==0) ? " pid=$$ ec=$exit_code run_time=$script_time" : "";
            print "017 END_COMP_FLOW: Compare channel src_ch_tc=$ch_name_l[$src_ch_tc] all Read from $filename against IDI & IO writes.$ec Compare count=$e2e_read_compare_count\n";
            STDOUT->flush();
            if(defined($pid) and $pid==0) {
                exit $exit_code;
            }
        }


        while($fork_proc_count>0) {
            my $p = waitpid(-1,0);
            if($fork_pid_h->{$p}) {
                push @$fork_core_l,$fork_pid_h->{$p};
                delete $fork_pid_h->{$p};
                if($?>>8) { $exit_code=1; }
                $fork_proc_count -= 1;
                #print time().": process $p done exit=$?\n";
                STDOUT->flush();
            }
        }

        return 1;
}

#for my $rec_ptr1 (@$all_pcie_link_write_byte_stream_l) {
#    print "EYAL2: address=$rec_ptr1->{address} data=$rec_ptr1->{data} : $rec_ptr1->{parent}->{line}";
#}

if(!$skip_e2e_read_chk) {

    # Add the traffic to WRC now.
    push @$all_pcie_link_write_byte_stream_l , @$all_WRC_pcie_link_write_byte_stream_l;

    for my $scbd ($idi_file_scbd,$cxl_idi_file_scbd) { 
      if(!$skip_e2e_pcie_read_chk && is_scbd_exists($scbd)) {
        my $idi_trans_l = $scbd->{U}->{all};
        # If we plan to check pcie, we need to find out which transaction has pcie non-snoop wr , and also any idi transaction
        for my $i (0..((+@$idi_trans_l)-1)) {
            my $rec_ptr = $idi_trans_l->[$i];
            my $addr6 = ($rec_ptr->{address}>>6);
            if($pch_non_snoop_addr_h{$addr6} and $rec_ptr->{data}) {
                $pch_non_snoop_addr_h{$addr6} |= 4; # Marck that there is an IDI write on this address
            }
            # move the src_ch_rd to be over the src_ch_tv
            if(defined($rec_ptr->{src_ch_rd})) {
                $rec_ptr->{src_ch_tc} = $rec_ptr->{src_ch_rd};
            }
        }
      } 
    }

    print "018 COMP_FLOW: Compare all Read from PEP against IDI & IO writes.\n" if $debug >= 1;

    my $all_write_byte_stream_l = [];

    for my $scbd ($idi_file_scbd) { 
      if(is_scbd_exists($scbd)) {
        print "001 CREATE_LIST: of WR from $scbd->{filename}.\n" if $debug >= 2;
        my $idi_trans_l  = get_filtered_cmds($scbd,"U",undef,cmd=>'(DirtyEvict|WOWrInv|WIL|WBMTOI|WBMTOE|WCIL|ITOMWR|BACKINV|MEMPUSHWR|SNPCODE|SNPDATA|SNPINV|SELFSNPINV|ITOMWR_WT|SNPCURR)'
            ,exclude_range_l=>[@not_dram_ranges_l,@prmrr_ranges_l,@idi_vga_ranges_l]
            ,exclude_func_l=>[{func=>\&filter_not_WRC_IDI}]);
        push @$all_write_byte_stream_l,$idi_trans_l;
      }
    }

    for my $mcc_preloader_file_scbd (@$mcc_preloader_file_scbd_l) {
        next unless is_scbd_exists($mcc_preloader_file_scbd);
        print "003 CREATE_LIST: of WR from $mcc_preloader_file_scbd->{filename}.\n" if $debug >= 2;
        my $mcc_preloader_trans_l  = get_filtered_cmds($mcc_preloader_file_scbd,"U",undef);
        push @$all_write_byte_stream_l,$mcc_preloader_trans_l;
    }

    if(1*@$all_pcie_link_write_byte_stream_l) {
        push @$all_write_byte_stream_l,$all_pcie_link_write_byte_stream_l;
    }

    my @more_psf_file_scbd2 = ();
    if(!$skip_e2e_pcie_read_chk) {
        push @more_psf_file_scbd2,@more_psf_file_scbd;
    }


    $all_write_byte_stream_l = filter_canceled_writes($all_write_byte_stream_l);

    for my $scbd (@more_psf_file_scbd2,$pep_psf_file_scbd,$pep_svt_link_file_scbd,$cxl_idi_file_scbd,$idi_file_scbd,@axi_file_scbd_l,@gtcxl_file_scbd_l,$pegs_psf_file_scbd) {
        next unless is_scbd_exists($scbd);
        print "004 CREATE_LIST: of RD from $scbd->{filename}.\n" if $debug >= 2;
        my $read_trans_l;
        my $read_byte_stream_l;
        my $MONITOR_read = ($is_e2e_monitor_read ? "^MONITOR|" : "");
        if($scbd->{filename}=~/^(merged_idi|idi|core_idi|cbo_idi|xbar_idi|SOC_CFI_trk|cxl.log)/) {
            $read_trans_l = get_filtered_cmds($scbd,"U",undef,cmd=>"^(${MONITOR_read}RDCURR|PRD|RFO|DRD|CRD|UCRDF)",exclude_range_l=>[@not_dram_ranges_l,@prmrr_ranges_l,@idi_vga_ranges_l]
                ,exclude_func_l=>[{func=>\&filter_slfsnp_bad_and_ACF_IDI}]); #FIXME: Try to add PRD here and more new IDI opcodes
            $read_byte_stream_l = $read_trans_l; # create_byte_stream(trans_l=>$read_trans_l);
        } elsif($scbd->{filename}=~/^pcie_vip_trans/) {

            my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"D",'\sR\s+MWr',exclude_range_l=>[$msi_range])); # , src_ch=>"PEP_HOST_dma")
            $byte_stream_l = filter_byte_stream_range_and_convert($byte_stream_l,\@pep_host_dma_range_l);
            push @$read_byte_stream_l , @$byte_stream_l;
            my $byte_stream_l = create_byte_stream(trans_l=>get_filtered_cmds($scbd,"U",'\sT\s+MRd')); # ,src_ch=>"PEP_HOST_direct")
            $byte_stream_l = filter_byte_stream_range_and_convert($byte_stream_l,\@pep_host_direct_range_l);
            push @$read_byte_stream_l , @$byte_stream_l;

        } elsif($scbd->{filename}=~/axi/) {
            $read_trans_l = get_filtered_cmds($scbd,"U",undef,cmd=>"ARADDR",exclude_range_l=>[$msi_range,@IOP_not_dram_ranges_l],exclude_func_l=>[{func=>\&filter_slfsnp_bad_and_ACF_IDI}]);
            $read_byte_stream_l = create_byte_stream(trans_l=>$read_trans_l); # , src_ch=>$scbd->{file_src_ch}
        } elsif($scbd->{filename}=~/cxl.*d2h/) {
            $read_trans_l = get_filtered_cmds($scbd,"U",'\| *(CXL2UFI_Rd|CXL2UFI_Read).*\|',exclude_range_l=>[$msi_range,@IOP_not_dram_ranges_l]);
            $read_byte_stream_l = create_byte_stream(trans_l=>$read_trans_l); # , src_ch=>$scbd->{file_src_ch}
        } else {
            $read_trans_l = get_filtered_cmds($scbd,"U",'\| *(MRd).*\|',exclude_range_l=>[$msi_range,@IOP_not_dram_ranges_l,$iocce_mktme_range]);
            $read_byte_stream_l = create_byte_stream(trans_l=>$read_trans_l); # , src_ch=>$scbd->{file_src_ch}
        }
        $read_byte_stream_l = filter_byte_stream_non_snoop($read_byte_stream_l); # if $argv{skip_if_non_snoop};

        make_FMemWrCompress_data_ZZ($all_write_byte_stream_l);

        compare_read_byte_channel($scbd->{filename},$read_byte_stream_l,$all_write_byte_stream_l);

        if($exit_code) { last };
    }

    if(!$exit_code && !$skip_e2e_pcie_read_chk) {
        my $all_pcie_link_read__byte_stream_l = filter_pcie_ns_read_trans($all_pcie_link_read__byte_stream_l);
        compare_read_byte_channel("All_pcie_upstream_logs",$all_pcie_link_read__byte_stream_l,$all_write_byte_stream_l);
    }

} # if(!$skip_e2e_read_chk)

# Return exit code (PASS it FAIL)
# Also support -fail2pass switch to invert the response.

use Proc::ProcessTable;

sub memory_usage() {
    my $t = new Proc::ProcessTable;
    foreach my $got (@{$t->table}) {
        next
            unless $got->pid eq $$;
        return $got->size;
    }
}

sub ending() {

my $script_time = script_timeout_chk();
my $my_path = "path : $my_PWD\n";

my $perf_info = 
"  e2e: read_ch_scan_count=$e2e_read_ch_scan_count read_compare_count=$e2e_read_compare_count read_retry_count=$e2e_read_retry_count refmem_update_count=$e2e_refmem_update_count refmem_reverse_count=$e2e_refmem_reverse_count write_compare_count=$e2e_write_compare_count write_retry_count=$e2e_total_write_retry_count \n".
"  skip_e2e_write_chk=$skip_e2e_write_chk skip_e2e_read_chk=$skip_e2e_read_chk skip_e2e_pcie_read_chk=$skip_e2e_pcie_read_chk do_e2e_warning_only=$do_e2e_warning_only skip_timeout_err=$skip_timeout_err";

print $e2e_command_line;

my $mem_used = int(memory_usage()/1000000) . "MB";

if($is_fail_2_pass ? !$exit_code : $exit_code) {
    print_ERROR("013 ERROR: Finish soc e2e checking version $version. exit_code=$exit_code mem_size=$mem_used run_time=$script_time\n\nFailure $my_path\n$perf_info\n\n");
    regression_report(0,$script_time);
    create_debug_rc_file();
    if($do_e2e_warning_only) {
        exit(0);
    } else {
        exit($exit_code ? $exit_code : 1);
    }
} else {
    print("\nFinish soc e2e checking version $version. exit_code=$exit_code. mem_size=$mem_used run_time=$script_time\n\nSimulation $my_path\n$perf_info\n\n");
    regression_report(1,$script_time);
    exit(0);
}
} # sub ending()

ending();

1;
