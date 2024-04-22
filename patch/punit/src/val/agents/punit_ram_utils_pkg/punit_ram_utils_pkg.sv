
//=====================================================================================================================
// Module Name:        punit_ram_utils_pkg.sv   
//
// Primary Contact:    Oshik 
// Last Review Date:
// Creation Date:      01/2021
// Last Review Date:
//
// Copyright (c) 2020-2030 Intel Corporation
// Intel Proprietary and Top Secret Information
//---------------------------------------------------------------------------------------------------------------------
// Description:
//		
//
//=====================================================================================================================


`ifndef PUNIT_RAM_UTILS
    `define PUNIT_RAM_UTILS


package punit_ram_utils_pkg;

  import sla_pkg::*;
  import uvm_pkg::*;

  import "DPI-C" function string getenv(input string env_name);

  typedef enum bit [1:0]  {
    INIT_TO_ZEROS          = 'h0, // for ram testing
    INIT_TO_RANDOM         = 'h1, // for ram testing
    INIT_TEST_FW           = 'h2, // local C file compiled image 
    INIT_PCODE             = 'h3 // real pcode
//    INIT_RECIPE            = 'h4  // for crashlog recipe init, ONLY backdoor
  } fw_init_source_e;

  typedef enum bit {
    BACKDOOR_LOAD = 0,
    ESE_DOWNLOAD   = 1
  } fw_init_method_e;

  typedef struct {
    bit [31:0] offset;
    int unsigned number_of_dwords;
    bit [7:0] data [64];
  } load_patch_content_e;

// oshikbit - from mail: 
//Anyway, please use this to get the non-persistent part:
//head -n 45056 $PCODE_ROOT/target/pcode/sim/mem/dram.mem
//
//And this for the persistent:
//tail -n 4096 $PCODE_ROOT/target/pcode/sim/mem/dram.mem
  

  typedef enum bit [2:0] {
    PCODE_IRAM    = 0,
    PCODE_DRAM    = 1,
    SUSTAIN_DRAM  = 2, // subset of dram - used by fw dl fsm
    CRASHLOG_RAM  = 3,
    TELEMETRY_RAM = 4,
    CL_RECIPE_RAM = 5, // subset of crashlog
    VOLATILE_DRAM = 6, // subset of dram
    CL_RECORD_RAM = 7 // subset of crashlog
  } punit_ram_sel_e;

  // ecc injections enums
  typedef enum bit[2:0] {
    SINGLE_DATA = 0,
    SINGLE_ECC = 1,
    DOUBLE_DATA = 2,
    DOUBLE_ECC = 3,
    DOUBLE_SPLIT = 4
  } ecc_corruption_dist_e;

  typedef enum bit {
    INJECT_BY_ADDR = 0,       // const corruption of the ram entry, till overwritten by hw
    INJECT_ON_NEXT_READ   = 1 // volatile, will defect the outgoing bus on next read completion, unimplemented
  } ecc_corruption_mode_e;

  string pkg_id = "PUNIT_RAM_UTILS";


//======== GENERAL ===============

  parameter NUM_ENTRIES_PER_BANK = 256;
  parameter NUM_COL_PER_BANK = 4;

    // template struct:
    //  256 lines in 4 columns => 1K
    //  mult by 4  (2 super bks * 2 bk each) => 4K
    //  *NUM_BANKS == number of 4K templates
  parameter IRAM_NUM_ENTRIES = 2*1024;
  parameter DRAM_NUM_ENTRIES = 2*1024;
  parameter SRAM_NUM_ENTRIES = 2*1024; // 64bits or 8bytes per entry (entry == line)

  parameter RECIPE_OFFSET = 32'h4C00; // crashlog recipe offset, in byte offset  - to translate to line offset divide by 8 (8bytes per line)
  parameter RECIPE_NUM_ENTRIES = 1536; // 12KB/8Bytes 
  parameter RECORD_OFFSET = 32'h50; // crashlog recipe offset, in byte offset  - to translate to line offset divide by 8 (8bytes per line)
  parameter RECORD_NUM_ENTRIES = 2422; // 19376B/8Bytes 


  parameter IRAM_NUM_BANKS   = 32; //ram-inc
  parameter DRAM_NUM_BANKS   = 32; //ram-inc
  parameter SRAM_NUM_BANKS   = 8; // 2 for crashlog, 2 for telemetry
  parameter CL_NUM_BANKS   = 6; // 2 for crashlog, 2 for telemetry
  parameter TELEM_NUM_BANKS   = 2; // 2 for crashlog, 2 for telemetry

  parameter DRAM_ECC_WIDTH   = 8; //7
  parameter DRAM_ADDR_WIDTH  = 16; //ram-inc
  parameter DRAM_DATA_WIDTH  = 32;

  parameter IRAM_ECC_WIDTH   = 8;
  parameter IRAM_ADDR_WIDTH  = 16;
  parameter IRAM_DATA_WIDTH  = 64;

  parameter SDRAM_NUM_BANKS  = 1;
  parameter SDRAM_SIZE  = DRAM_NUM_ENTRIES*SDRAM_NUM_BANKS;
  parameter VDRAM_SIZE  = DRAM_NUM_ENTRIES*(DRAM_NUM_BANKS-SDRAM_NUM_BANKS);

  parameter DRAM_OFFSET = 32'h0;
  parameter PERSIST_DRAM_OFFSET = DRAM_OFFSET + 32'hB000; // 0x2C00/4;
  parameter IRAM_OFFSET = 32'h20000;
  parameter SRAM_OFFSET = 32'h40000;

  `ifndef PUNIT_SRAM_BIST_WRAPPER 
    `define PUNIT_SRAM_BIST_WRAPPER  `PATH_TO_PUNIT.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
    //`define PUNIT_SRAM_BIST_WRAPPER   `PUNIT_TOP.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
    //`define PUNIT_SRAM_BIST_WRAPPER   punit_tb.punit_top_wrap.punit.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
  `endif

  `ifdef IP_HW_TE
    `define PUNIT_SRAM_BIST_WRAPPER   punit_tb.punit_top_wrap.punit.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
  `elsif IP_TYP_TE
    `define PUNIT_SRAM_BIST_WRAPPER   punit_tb.punit_top_wrap.punit.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
  `else
    `define PUNIT_SRAM_BIST_WRAPPER   soc_tb.soc.cbb_base.par_base_punit.punit.punit_inst.punit_gated_top.punit_uc_subsystem.punit_sram_bist_wrapper
  `endif
//  =======================

  `ifndef STRINGIFY
    `define STRINGIFY(x) `"x`"
  `endif
  string punit_sram_bist_top = `STRINGIFY(`PUNIT_SRAM_BIST_WRAPPER); 

  `include "uvm_macros.svh"
  `include "slu_macros.svh"

  //======================================
  // ECC Calculation
  //======================================
  function automatic logic [7:0] calc_32bit_ecc (input [31:0] data);
    logic [7:0] ecc;
    begin
        ecc[0] = data[0] ^ data[1]  ^ data[2]  ^ data[3]  ^ data[4]  ^ data[5]  ^ data[6]  ^ data[7]  ^ data[14] ^ data[19] ^ data[22] ^ data[24] ^ data[30] ^ data[31];
        ecc[1] = data[4] ^ data[7]  ^ data[8]  ^ data[9]  ^ data[10] ^ data[11] ^ data[12] ^ data[13] ^ data[14] ^ data[15] ^ data[18] ^ data[21] ^ data[24] ^ data[29];
        ecc[2] = data[3] ^ data[11] ^ data[16] ^ data[17] ^ data[18] ^ data[19] ^ data[20] ^ data[21] ^ data[22] ^ data[23] ^ data[26] ^ data[27] ^ data[29] ^ data[30];
        ecc[3] = data[2] ^ data[6]  ^ data[10] ^ data[13] ^ data[15] ^ data[16] ^ data[24] ^ data[25] ^ data[26] ^ data[27] ^ data[28] ^ data[29] ^ data[30] ^ data[31];
        ecc[4] = data[1] ^ data[2]  ^ data[5]  ^ data[7]  ^ data[9]  ^ data[12] ^ data[15] ^ data[20] ^ data[21] ^ data[22] ^ data[23] ^ data[25] ^ data[26] ^  data[28];
        ecc[5] = data[0] ^ data[5]  ^  data[6] ^ data[8]  ^ data[12] ^ data[13] ^ data[14] ^ data[16] ^ data[17] ^ data[18] ^ data[19] ^ data[20] ^ data[28];
        ecc[6] = data[0] ^ data[1]  ^  data[3] ^ data[4]  ^ data[8]  ^ data[9]  ^ data[10] ^ data[11] ^ data[17] ^ data[23] ^ data[25] ^ data[27] ^ data[31];
        ecc[7] = 'b0;
    end
  return ecc;
  endfunction:calc_32bit_ecc

  //======================================
  // ECC Calculation
  //======================================
  // https://www.slideshare.net/SkCheah/memory-ecc-the-comprehensive-of-secded
  function automatic logic [7:0] calc_64bit_ecc (input [63:0] data);
    logic [7:0] ecc;
    begin
        ecc[7] = ^(data&64'b0000110100100011000110110010101010010001010110100010100110010010);
        //ecc[7] = data[1] ^ data[4]  ^ data[7]  ^ data[8]  ^ data[11]  ^ data[13]  ^ data[17]  ^ data[19]  ^ data[10] ^ data[22] ^ data[24] ^ data[28] ^ data[31] ^ data[33]  ^ data[35]  ^ data[37]  ^ data[40]  ^ data[41]  ^ data[43] ^ data[44] ^ data[48] ^ data[49] ^ data[53] ^ data[56] ^ data[58] ^ data[59];
        ecc[6] = data[2] ^ data[5]  ^ data[6]  ^ data[7]  ^ data[8]  ^ data[11]  ^ data[12]  ^ data[18]  ^ data[19] ^ data[21] ^ data[24] ^ data[25] ^ data[31] ^ data[32]  ^ data[34]  ^ data[35]  ^ data[38]  ^ data[40]  ^ data[42] ^ data[50] ^ data[51] ^ data[52] ^ data[54] ^ data[56] ^ data[59] ^ data[62];
        ecc[5] = data[1] ^ data[5]  ^ data[7]  ^ data[9]  ^ data[11]  ^ data[14]  ^ data[16]  ^ data[17]  ^ data[21] ^ data[23] ^ data[26] ^ data[30] ^ data[31] ^ data[33]  ^ data[35]  ^ data[38]  ^ data[39]  ^ data[44]  ^ data[46] ^ data[47] ^ data[49] ^ data[52] ^ data[54] ^ data[59] ^ data[61] ^ data[63];
        ecc[4] = data[0] ^ data[2]  ^ data[4]  ^ data[7]  ^ data[10]  ^ data[14]  ^ data[15]  ^ data[18]  ^ data[19] ^ data[20] ^ data[29] ^ data[30] ^ data[31] ^ data[34]  ^ data[35]  ^ data[37]  ^ data[44]  ^ data[45]  ^ data[47] ^ data[50] ^ data[52] ^ data[53] ^ data[55] ^ data[57] ^ data[59] ^ data[63];
        ecc[3] = data[0] ^ data[3]  ^ data[5] ^ data[9]  ^ data[12]  ^ data[15]  ^ data[16]  ^ data[20]  ^ data[23] ^ data[25] ^ data[27] ^ data[28] ^ data[30] ^ data[32]  ^ data[33]  ^ data[35]  ^ data[36]  ^ data[41]  ^ data[43] ^ data[45] ^ data[48] ^ data[50] ^ data[51] ^ data[56] ^ data[57] ^ data[61];
        ecc[2] = data[0] ^ data[3]  ^ data[4]  ^ data[10]  ^ data[13]  ^ data[14]  ^ data[15]  ^ data[16]  ^ data[17] ^ data[23] ^ data[26] ^ data[27] ^ data[29] ^ data[32]  ^ data[34]  ^ data[40]  ^ data[42]  ^ data[43]  ^ data[46] ^ data[48] ^ data[51] ^ data[54] ^ data[58] ^ data[59] ^ data[60] ^ data[62];
        ecc[1] = data[1] ^ data[3]  ^ data[6]  ^ data[9]  ^ data[13]  ^ data[15]  ^ data[18]  ^ data[22]  ^ data[23] ^ data[24] ^ data[25] ^ data[29] ^ data[31] ^ data[36]  ^ data[38]  ^ data[39]  ^ data[41]  ^ data[43]  ^ data[46] ^ data[47] ^ data[51] ^ data[53] ^ data[55] ^ data[57] ^ data[60] ^ data[62];
        ecc[0] = data[2] ^ data[6]  ^ data[7]  ^ data[8]  ^ data[10]  ^ data[12]  ^ data[15]  ^ data[21]  ^ data[22] ^ data[23] ^ data[26] ^ data[27] ^ data[28] ^ data[36]  ^ data[37]  ^ data[39]  ^ data[42]  ^ data[43]  ^ data[45] ^ data[49] ^ data[51] ^ data[55] ^ data[58] ^ data[60] ^ data[61] ^ data[63];
    end
    return ecc;
//    return 8'h0;
  endfunction:calc_64bit_ecc

  // get_dram_hdl_path 
  // - utility function for dumping the fw rams to array
  //======================================================
  function string get_dram_hdl_path(input int addr /*byte address*/);

	
//    string punit_sram_bist_top = `STRINGIFY(`PUNIT_SRAM_BIST_WRAPPER); 
	
    // 11:4  - set number 256
    // 3:2 - col internal
    // 0 - bk sel
    // 1 - super bk sel
     
    string hdl_path;
    string prefix;
    int row; 


    case ((addr>>2)/DRAM_NUM_ENTRIES) inside
      'd0:   prefix = $sformatf("%s.punit_dram_0.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd1:   prefix = $sformatf("%s.punit_dram_1.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd2:   prefix = $sformatf("%s.punit_dram_2.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd3:   prefix = $sformatf("%s.punit_dram_3.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd4:   prefix = $sformatf("%s.punit_dram_4.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd5:   prefix = $sformatf("%s.punit_dram_5.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd6:   prefix = $sformatf("%s.punit_dram_6.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd7:   prefix = $sformatf("%s.punit_dram_7.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd8:   prefix = $sformatf("%s.punit_dram_8.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd9:   prefix = $sformatf("%s.punit_dram_9.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd10:   prefix = $sformatf("%s.punit_dram_10.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd11:   prefix = $sformatf("%s.punit_dram_11.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd12:   prefix = $sformatf("%s.punit_dram_12.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd13:   prefix = $sformatf("%s.punit_dram_13.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd14:   prefix = $sformatf("%s.punit_dram_14.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd15:   prefix = $sformatf("%s.punit_dram_15.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd16:   prefix = $sformatf("%s.punit_dram_16.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd17:   prefix = $sformatf("%s.punit_dram_17.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd18:   prefix = $sformatf("%s.punit_dram_18.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd19:   prefix = $sformatf("%s.punit_dram_19.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd20:   prefix = $sformatf("%s.punit_dram_20.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd21:   prefix = $sformatf("%s.punit_dram_21.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd22:   prefix = $sformatf("%s.punit_dram_22.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd23:   prefix = $sformatf("%s.punit_dram_23.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd24:   prefix = $sformatf("%s.punit_dram_24.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd25:   prefix = $sformatf("%s.punit_dram_25.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd26:   prefix = $sformatf("%s.punit_dram_26.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd27:   prefix = $sformatf("%s.punit_dram_27.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd28:   prefix = $sformatf("%s.punit_dram_28.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd29:   prefix = $sformatf("%s.punit_dram_29.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd30:   prefix = $sformatf("%s.punit_dram_30.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd31:   prefix = $sformatf("%s.punit_dram_31.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array",punit_sram_bist_top);      
       default: `slu_error(pkg_id,("Unmatched Case statement"))
    endcase

    //row = (addr&16'b0011_1111_1111_1100)/4 ;
    row = ((addr>>2) % DRAM_NUM_ENTRIES);

    hdl_path = $sformatf("%s[%0d]",prefix,row);
    return hdl_path;

  endfunction:get_dram_hdl_path

  // get_iram_hdl_path 
  // - utility function for dumping the fw rams to array
  //======================================================
  function string get_iram_hdl_path(input int addr /*byte address*/, bit ecc_or_payload);

//    string punit_sram_bist_top = `STRINGIFY(`PUNIT_SRAM_BIST_WRAPPER); 

    // 11:4  - set number 256
    // 3:2 - col internal
    // 0 - bk sel
    // 1 - super bk sel
     
    string hdl_path;
    string prefix;
    int row, template_num;

    template_num = ((addr>>2)/IRAM_NUM_ENTRIES);
    prefix = $sformatf("%s.punit_iram_%0d.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top,template_num);

//    case ((addr>>2)/IRAM_NUM_ENTRIES) inside
//      'd0:  prefix = $sformatf("%s.punit_iram_0.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd1:  prefix = $sformatf("%s.punit_iram_1.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd2:  prefix = $sformatf("%s.punit_iram_2.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd3:  prefix = $sformatf("%s.punit_iram_3.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd4:  prefix = $sformatf("%s.punit_iram_4.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd5:  prefix = $sformatf("%s.punit_iram_5.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd6:  prefix = $sformatf("%s.punit_iram_6.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd7:  prefix = $sformatf("%s.punit_iram_7.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd8:  prefix = $sformatf("%s.punit_iram_8.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd9:  prefix = $sformatf("%s.punit_iram_9.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd10:  prefix = $sformatf("%s.punit_iram_10.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd11:  prefix = $sformatf("%s.punit_iram_11.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);
//      'd12:  prefix = $sformatf("%s.punit_iram_12.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);   // ram-inc
//      'd13:  prefix = $sformatf("%s.punit_iram_13.ipn3hcr1pm4 096x72m4i2k4b0r2c1.super_bank_gen[%0d].super_bank.bank_gen[%0d].bank.array.array",punit_sram_bist_top,super_bk_sel,bk_sel);   // ram-inc
//       default: `slu_error(pkg_id,("Unmatched Case statement"))
//    endcase

//    row = (addr&16'b0011_1111_1111_1100)/4 ;
    row = ((addr>>2) % IRAM_NUM_ENTRIES);

    if (!ecc_or_payload)
      hdl_path = $sformatf("%s[%0d][63:0]",prefix,row);
    else 
      hdl_path = $sformatf("%s[%0d][71:64]",prefix,row);
              
    return hdl_path;

  endfunction:get_iram_hdl_path


  // get_sram_hdl_path 
  // - utility function for dumping the fw rams to array
  //======================================================
  function string get_sram_hdl_path(input int addr /*byte address*/, bit ecc_or_payload);

//    string punit_sram_bist_top = `STRINGIFY(`PUNIT_SRAM_BIST_WRAPPER); 

    // 11:4  - set number 256
    // 3:2 - col internal
    // 0 - bk sel
    // 1 - super bk sel
     
    string hdl_path;
    string prefix;
    int row;

    
    case ((addr>>2)/SRAM_NUM_ENTRIES) inside
      'd0:  prefix = $sformatf("%s.punit_crashlog_ram_0.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd1:  prefix = $sformatf("%s.punit_crashlog_ram_1.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd2:  prefix = $sformatf("%s.punit_crashlog_ram_2.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd3:  prefix = $sformatf("%s.punit_crashlog_ram_3.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd4:  prefix = $sformatf("%s.punit_crashlog_ram_4.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
      'd5:  prefix = $sformatf("%s.punit_crashlog_ram_5.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);

//FIXME-CBB-A0-OSHIKBIT/NMATOT-14.03.23 - Enable telemetry arrays tests in CBB
//      'd2:  prefix = $sformatf("%s.punit_telemetry_ram_0.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
//      'd3:  prefix = $sformatf("%s.punit_telemetry_ram_1.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array",punit_sram_bist_top);
       default: `slu_error(pkg_id,("Unmatched Case statement"))
    endcase

   // row = (addr&16'b0011_1111_1111_1100)/4;
    row = ((addr>>2) % SRAM_NUM_ENTRIES);

    if (!ecc_or_payload)
      hdl_path = $sformatf("%s[%0d][63:0]",prefix,row);
    else 
      hdl_path = $sformatf("%s[%0d][71:64]",prefix,row);
              
    return hdl_path;

  endfunction:get_sram_hdl_path


// CHECKING METHODS
// ===========================

  // check_dram_line
  // - checking method - to be reused or copied to a checker/scoreboard
  // - this method receives an iram/dram address and expected value, and compares it to actual value in the ram
  // - it will also calculate the ecc based on expected value and compare it to actual ecc
  // - to be used mainly by direct test
  function void check_dram_line(input logic [31:0] exp_val, int address);
  
    logic [39:0] physical_data;
    
    physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(address));
	
    if (physical_data[31:0] !== exp_val[31:0])
      `slu_error(pkg_id,("compare missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h [dram path: %s]",address/4,exp_val[31:0],physical_data[31:0],get_dram_hdl_path(address)))
    else
     `slu_msg(UVM_LOW,pkg_id,("compare match on address 'h%0h. expected: 'h%0h, actual: 'h%0h [dram path: %s]",address/4,exp_val[31:0],physical_data[31:0],get_dram_hdl_path(address)));	               

    // compare the ecc bits
    if (physical_data[38:32] !== calc_32bit_ecc(exp_val))
      `slu_error(pkg_id,("ecc missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h",address/4,calc_32bit_ecc(exp_val),physical_data[39:32]))
    else
     `slu_msg(UVM_LOW,pkg_id,("ecc match on address 'h%0h. expected: 'h%0h, actual: 'h%0h",address/4,calc_32bit_ecc(exp_val),physical_data[39:32]));		
	 

  endfunction:check_dram_line
 


  // get_dram_line
  // - API for pcode tests - utility for reading (later overiding) pcode variables by injecting to Dram 
  // - this method receives dram and returns dram value in RAM
  // - requested by SOC team
  function logic[31:0] get_dram_line(input int unsigned  address);
  
    logic [39:0] physical_data;
    
    physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(address));

    `slu_msg(UVM_LOW,pkg_id,("get_dram_line summary: address 'h%0h. value: 'h%0h [dram path: %s]",address,physical_data[39:0],get_dram_hdl_path(address)));

    return physical_data[31:0];

  endfunction:get_dram_line



  // modify_dram_line
  // - API for pcode tests - overiding pcode variables by injecting to Dram 
  // - this method receives dram address and new value (int) offset and
  // varibale size
  // - requested by SOC team
  function void modify_dram_line(input int desired ,input int   address, int offset = -1,int  size = 8, bit fetch = 0);
  
    logic [39:0] physical_data;
    logic [39:0] new_data = 'h0;
    int byte_offset;
    int dw_aligned_address;
//    int allone = 32'hFFFFFFFF;
//    int mask, mask_b = 'h0;


    if ( (size > 32) | (offset > (32-size)) ) begin
        `slu_error(pkg_id,("modify_dram_line missconfiguration - check your values of offset and size"))
        $stacktrace;
    end

  byte_offset  = address % 4;
  dw_aligned_address = address - byte_offset;
  physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(dw_aligned_address));

//    new_data = desired<<offset;
//    mask = allone[]
//    new_data = (new_data & mask) | (physical_data & mask_b)

    if (offset == -1) begin
        offset = byte_offset * 8;
    end

    //new_data[offset+size-1:offset] = desired[size-1:0]
 // FIXME - ydror2 - beautify - 12.12.22  
    new_data[31:0] = physical_data[31:0];
    for (int k=offset ; k<(offset+size); k++) begin
        new_data[k] = desired[k-offset];
    end

    new_data[38:32] = calc_32bit_ecc(new_data[31:0]);

    `slu_msg(UVM_LOW,pkg_id,("modify_dram_line summary:  desired ='h%0h address 'h%0h. dw aligned address: 'h%0h  offset: 'd%0d, size: 'd%0d, original value: 'h%0h, new value: 'h%0h [dram path: %s]",desired,address,dw_aligned_address,offset,size,physical_data[39:0],new_data[39:0],get_dram_hdl_path(dw_aligned_address)));

    slu_vpi_put_value_by_name(get_dram_hdl_path(dw_aligned_address), new_data[39:0]);


  endfunction:modify_dram_line

    // Read-modify-write for DRAM lines, based on 32-bit values and byte-aligned addresses
    function void rmw_dram_line(longint unsigned new_data, int address, bit[31:0] bit_mask = 32'hffff, bit[31:0] bit_mask_hi = 32'hffff);
	int 	curr_data, write_data;
	int 	dw_aligned_address = address - (address % 4);

	curr_data  = get_dram_line(dw_aligned_address);
	write_data = (bit_mask & new_data[31:0]) | (!bit_mask & curr_data);
	modify_dram_line(.desired(write_data), .offset(0)/*offset*/, .size(32)/*size*/, .address(dw_aligned_address), .fetch(0)/*fetch*/);

	if ( (new_data >> 32) != 0) begin // data is more than 32 bits long, write to upper half
	    curr_data  = get_dram_line(dw_aligned_address + 4);
	    write_data = (bit_mask_hi & new_data[63:31]) | (!bit_mask_hi & curr_data);
	    modify_dram_line(.desired(write_data), .offset(0)/*offset*/, .size(32)/*size*/, .address(dw_aligned_address+4), .fetch(0)/*fetch*/);
	end

   endfunction : rmw_dram_line

  // check_iram_line
  // - checking method - to be reused or copied to a checker/scoreboard
  // - this method receives an iram/dram address and expected value, and compares it to actual value in the ram
  // - it will also calculate the ecc based on expected value and compare it to actual ecc
  // - to be used mainly by direct test
  function void check_iram_line(input logic [63:0] exp_val, int address);
  
    logic [71:0] physical_data;
    
    physical_data[63:0] = slu_vpi_get_value_by_name(get_iram_hdl_path(address,0));
	
    if (physical_data[63:0] !== exp_val[63:0])
      `slu_error(pkg_id,("compare missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h [iram path: %s]",address/2,exp_val[63:0],physical_data[63:0],get_iram_hdl_path(address,0)))
    else
     `slu_msg(UVM_LOW,pkg_id,("compare match on address 'h%0h. expected: 'h%0h, actual: 'h%0h [iram path: %s]",address/2,exp_val[63:0],physical_data[63:0],get_iram_hdl_path(address,0)));	               

    // compare the ecc bits
    physical_data[71:64] = slu_vpi_get_value_by_name(get_iram_hdl_path(address,1));
    if (physical_data[71:64] !== calc_64bit_ecc(exp_val))
      `slu_error(pkg_id,("ecc missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h",address/2,calc_64bit_ecc(exp_val),physical_data[71:64]))
    else
     `slu_msg(UVM_LOW,pkg_id,("ecc match on address 'h%0h. expected: 'h%0h, actual: 'h%0h",address/2,calc_64bit_ecc(exp_val),physical_data[71:64]));		
	 

  endfunction:check_iram_line

  // check_sram_line
  // - checking method - to be reused or copied to a checker/scoreboard
  // - this method receives an iram/dram address and expected value, and compares it to actual value in the ram
  // - it will also calculate the ecc based on expected value and compare it to actual ecc
  // - to be used mainly by direct test
  function void check_sram_line(input logic [63:0] exp_val, int address);
  
    logic [71:0] physical_data;
    
    physical_data[63:0] = slu_vpi_get_value_by_name(get_sram_hdl_path(address,0));
	
    if (physical_data[63:0] !== exp_val[63:0])
      `slu_error(pkg_id,("compare missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,exp_val[63:0],physical_data[63:0],get_sram_hdl_path(address,0)))
    else
     `slu_msg(UVM_LOW,pkg_id,("compare match on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,exp_val[63:0],physical_data[63:0],get_sram_hdl_path(address,0)));	               

    // compare the ecc bits
    physical_data[71:64] = slu_vpi_get_value_by_name(get_sram_hdl_path(address,1));
    if (physical_data[71:64] !== calc_64bit_ecc(exp_val))
      `slu_error(pkg_id,("ecc missmatch on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,calc_64bit_ecc(exp_val),physical_data[71:64],get_sram_hdl_path(address,1)))
    else
     `slu_msg(UVM_LOW,pkg_id,("ecc match on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,calc_64bit_ecc(exp_val),physical_data[71:64],get_sram_hdl_path(address,1)));		
	 

  endfunction:check_sram_line
  // check_sram_line_not_equal
  // - checking method - to be reused or copied to a checker/scoreboard
  // - this method receives an iram/dram address and expected value, and compares it to actual value in the ram
  // - it will also calculate the ecc based on expected value and compare it to actual ecc
  // - to be used mainly by direct test
  function void check_sram_line_not_equal(input logic [63:0] exp_val, int address);
  
    logic [71:0] physical_data;
    
    physical_data[63:0] = slu_vpi_get_value_by_name(get_sram_hdl_path(address,0));
	
    if (physical_data[63:0] === exp_val[63:0])
      `slu_error(pkg_id,("compare match (which is bad) on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,exp_val[63:0],physical_data[63:0],get_sram_hdl_path(address,0)))
    else
     `slu_msg(UVM_LOW,pkg_id,("compare mismatch (which is good) on address 'h%0h. expected: 'h%0h, actual: 'h%0h [sram path: %s]",address,exp_val[63:0],physical_data[63:0],get_sram_hdl_path(address,0)));	               
  endfunction:check_sram_line_not_equal

  // clone_ram
  // - cloning rams for future compare , for example after save-restore
  // - the cloning is done to a ref array and to dumped file-  indexed with timestamp
  // - after the array is cloned, user can use line-by-line comparison to the real rams, using 'check_ram_line'
  // or post test script dump compare
  // usage example
  //       logic [39:0] uc_mem [];
  //       uc_mem = new[total_rams_size_in_bytes/4];
  //       ram_utils.clone_ram(uc_mem,PCODE_DRAM);
  
  function void clone_ram(output logic [31:0] ref_array[$], input punit_ram_sel_e ram);
  
    logic [39:0] physical_data;
    int fileid;
    string filename = "temp_name";

    filename = $sformatf("%s_%0tps.dump",ram,$time);

    fileid = $fopen(filename,"w");
    `slu_assert((fileid != 0) , ($sformatf("%s can not open %s file ",pkg_id,filename)));

 	 
    for(int j=0; j < DRAM_NUM_BANKS*DRAM_NUM_ENTRIES; j=j+1) // 'h20000 represent the address of the 128K+1 byte
    begin
      physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(j));
      ref_array.push_back(physical_data);
      $fdisplay(fileid,$sformatf("%8h",physical_data[31:0]));
      $fflush(fileid);
    end
    `slu_msg(UVM_LOW,"CLONE_RAM",($sformatf("cloned %s to %s",ram,filename)));
   $fclose(fileid);

//   return ref_array;

  endfunction:clone_ram


  // corrupt_ecc
  // injects ecc error - select between the following modes
  //  - single or double
  //  - error on ecc or payload or distributed (in case of dbl)
  //  - error on specific addr or on next read
  //  - single occur or multiple  
  //  - ram selector - iram/dram/crashlog/telemetry
//                                               cram_flip_bit = sla_vpi_get_value_by_name(cram_rtl_path);
//                                                `sla_msg(OVM_LOW,m_id,("before flipping bits : %0b",cram_flip_bit));
//                                                sla_vpi_put_value_by_name(cram_rtl_path, 'b00100^cram_flip_bit);
//                                                cram_flip_bit = sla_vpi_get_value_by_name(cram_rtl_path);
  
  task corrupt_ecc (input punit_ram_sel_e ram, ecc_corruption_dist_e distribution, ecc_corruption_mode_e mode, int repeatition = 1, int address);

    logic [71:0] data_from_ram;
    logic [71:0] corruption_mask;

    if ((mode == INJECT_ON_NEXT_READ) && (repeatition == 0))
      `slu_error(pkg_id,("corrupt_ecc call error: does not make sense to use %s with %0d repeatitions",mode,repeatition))

    if (mode == INJECT_BY_ADDR) begin
      case (ram) inside
        PCODE_IRAM : begin
                    //create mask
                    corruption_mask = create_corrupt_mask(ram,distribution,address);
                    //corrupt the ram
                    data_from_ram[63:0] = slu_vpi_get_value_by_name(get_iram_hdl_path(address,0));
                    data_from_ram[71:64] = slu_vpi_get_value_by_name(get_iram_hdl_path(address,1));
                    slu_vpi_put_value_by_name(get_iram_hdl_path(address,0), data_from_ram[63:0]^corruption_mask[63:0]);
                    slu_vpi_put_value_by_name(get_iram_hdl_path(address,1), data_from_ram[71:64]^corruption_mask[71:64]);
                    `slu_msg(UVM_LOW,pkg_id,("entry on address 'h%0h [iram path: %s] is 'h%0h. corruption_mask == 'h%0h. data after corruption = 'h%0h",
                        address/2,get_iram_hdl_path(address,0),data_from_ram[71:0],corruption_mask,data_from_ram^corruption_mask));

                  end
        PCODE_DRAM : begin
                    //create mask
                    corruption_mask = create_corrupt_mask(ram,distribution,address);
                    //corrupt the ram
                    data_from_ram[39:0] = slu_vpi_get_value_by_name(get_dram_hdl_path(address));
                    slu_vpi_put_value_by_name(get_dram_hdl_path(address), data_from_ram[39:0]^corruption_mask[39:0]);
                    `slu_msg(UVM_LOW,pkg_id,("entry on address 'h%0h [dram path: %s] is 'h%0h. corruption_mask == 'h%0h. data after corruption = 'h%0h",
                        address,get_dram_hdl_path(address),data_from_ram[39:0],corruption_mask,data_from_ram^corruption_mask));
                  end
        CRASHLOG_RAM,TELEMETRY_RAM : begin
                    //create mask
                    corruption_mask = create_corrupt_mask(ram,distribution,address);
                    //corrupt the ram
                    data_from_ram[63:0] = slu_vpi_get_value_by_name(get_sram_hdl_path(address,0));
                    data_from_ram[71:64] = slu_vpi_get_value_by_name(get_sram_hdl_path(address,1));
                    slu_vpi_put_value_by_name(get_sram_hdl_path(address,0), data_from_ram[63:0]^corruption_mask[63:0]);
                    slu_vpi_put_value_by_name(get_sram_hdl_path(address,1), data_from_ram[71:64]^corruption_mask[71:64]);
                    `slu_msg(UVM_LOW,pkg_id,("entry on address 'h%0h [sram path: %s] is 'h%0h. corruption_mask == 'h%0h. data after corruption = 'h%0h",
                        address/2,get_sram_hdl_path(address,0),data_from_ram[71:0],corruption_mask,data_from_ram^corruption_mask));

                  end
        default: `slu_error(pkg_id,("corrupt_ecc call error: %s ram not supported yet",ram))
      endcase
    end

    else begin
      `slu_error(pkg_id,("corrupt_ecc call error: %s not supported yet",mode))
    end

  endtask:corrupt_ecc
  

  function bit[71:0] create_corrupt_mask (input punit_ram_sel_e ram, ecc_corruption_dist_e distribution, int addr);
//    SINGLE_DATA = 0,
//    SINGLE_ECC = 1,
//    DOUBLE_DATA = 2,
//    DOUBLE_ECC = 3,
//    DOUBLE_SPLIT = 4
    bit [72:0] mask = 'h0;
    int offset1,offset2;

    `slu_assert(std::randomize(offset1) with {distribution inside {SINGLE_DATA,DOUBLE_DATA,DOUBLE_SPLIT} & ram == PCODE_DRAM -> offset1 inside {[0:31]};
                                              distribution inside {SINGLE_DATA,DOUBLE_DATA,DOUBLE_SPLIT} & ram != PCODE_DRAM -> offset1 inside {[0:63]};
                                              distribution inside {SINGLE_ECC,DOUBLE_ECC} & ram == PCODE_DRAM -> offset1 inside {[32:38]};
                                              distribution inside {SINGLE_ECC,DOUBLE_ECC} & ram != PCODE_DRAM -> offset1 inside {[64:71]};
                                              },("Randomization Failed\n"));

    `slu_assert(std::randomize(offset2) with {distribution inside {DOUBLE_DATA} & ram == PCODE_DRAM -> offset2 inside {[0:31]};
                                              distribution inside {DOUBLE_DATA} & ram != PCODE_DRAM -> offset2 inside {[0:63]};
                                              distribution inside {DOUBLE_ECC,DOUBLE_SPLIT} & ram == PCODE_DRAM -> offset2 inside {[32:38]};
                                              distribution inside {DOUBLE_ECC,DOUBLE_SPLIT} & ram != PCODE_DRAM -> offset2 inside {[64:71]};
                                              offset2 != offset1;
                                              distribution inside {SINGLE_DATA,SINGLE_ECC} -> offset2 == 72;
                                              },("Randomization Failed\n"));


    
    mask = 1<<offset1 | 1<<offset2;
   
    `slu_msg(UVM_LOW,pkg_id,("create_corrupt_mask - corrupting mask for %s, address 'h%0h is 'h%0h",ram,addr,mask));		
    return mask[71:0];  


  endfunction:create_corrupt_mask

  task compare_iram(input punit_ram_sel_e ram_to_check = PCODE_IRAM , string src_to_compare = "",bit print2log = 0 );
  
      // <add descripton>
      // inputs:
      //     ram to check
      //     src file to compare to
      //     
    
      string tID = "RAM_COMPARE";
    
      int inst_mem[0:IRAM_NUM_ENTRIES*IRAM_NUM_BANKS*2-1];
      int data_mem[0:DRAM_NUM_ENTRIES*DRAM_NUM_BANKS-1];
      int crash_mem[0:IRAM_NUM_ENTRIES*1*2-1];
      int telem_mem[0:IRAM_NUM_ENTRIES*1*2-1];
    
      int recipe_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int sdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int vdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int record_mem[0:RECIPE_NUM_ENTRIES*2-1];
      //
     
      string dram_rtl_path;
    
      string iram_rtl_path;
      string iram_ecc_rtl_path;
    
      string sram_rtl_path;
      string sram_ecc_rtl_path;
    
      // Data to write to MEM
      bit [39:0] data_with_ecc;
    
      bit [31:0] iram_entry;
      byte iram_ecc = 'h0;
    
      bit [31:0] sram_entry;
      byte sram_ecc = 'h0;
    
      // to calcuate mem location
      int template_num = -1;
      int ram_row_number = 0;
      int ram_col_number = -1;
    
      int bk_sel, super_bk_sel;

      logic [71:0] physical_data;

      int unsigned number_of_errors = 0;
      string last_error_msg;
    
   
       
            last_error_msg = "";
            number_of_errors = 0;
          // init src to default
          if (src_to_compare == "") src_to_compare = "iram.mem";
          // init the image to compare to into local array
          $readmemh(src_to_compare, inst_mem);
          
          `slu_msg(UVM_LOW, tID, ($sformatf("RAM to check is %s, source to check is %s",ram_to_check,src_to_compare)));
   
          for(int i=0; i < IRAM_NUM_ENTRIES*IRAM_NUM_BANKS*2; i++) // number of lines in file
          begin
    
               
            template_num = ((i/2)/IRAM_NUM_ENTRIES);
            ram_row_number = ((i/2) % IRAM_NUM_ENTRIES);
    
            if ((i%2) == 0) begin
               iram_rtl_path = $sformatf("%s.punit_iram_%0d.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array[%0d][31:0]",punit_sram_bist_top,template_num,ram_row_number);
               physical_data[31:0] = slu_vpi_get_value_by_name(iram_rtl_path);
               // checking
               if (physical_data[31:0] !== inst_mem[i]) begin
                 // always print 1st and last error
                 if (print2log || (number_of_errors == 0))  `slu_error(tID,("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",inst_mem[i],physical_data[31:0],iram_rtl_path));
                 number_of_errors++;
                 last_error_msg = $sformatf("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",inst_mem[i],physical_data[31:0],iram_rtl_path);
               end
            end
            else begin
               iram_rtl_path = $sformatf("%s.punit_iram_%0d.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array[%0d][63:32]",punit_sram_bist_top,template_num,ram_row_number);
               iram_ecc_rtl_path = $sformatf("%s.punit_iram_%0d.ip764hsuspsr2048x72m4b2s0r2p1d0_upf_wrapper.ip764hsuspsr2048x72m4b2s0r2p1d0.ip764hsuspsr2048x72m4b2s0r2p1d0_bmod.ip764hsuspsr2048x72m4b2s0r2p1d0_array.array[%0d][71:64]",punit_sram_bist_top,template_num,ram_row_number);
               physical_data[63:32] = slu_vpi_get_value_by_name(iram_rtl_path);
               physical_data[71:64] = slu_vpi_get_value_by_name(iram_ecc_rtl_path);
               iram_ecc = calc_64bit_ecc({physical_data[63:32],physical_data[31:0]});
               // checking
               if (physical_data[71:32] !== {iram_ecc,inst_mem[i]}) begin
                 // always print 1st and last error
                 if (print2log || (number_of_errors == 0))  `slu_error(tID,("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",inst_mem[i],physical_data[63:32],iram_rtl_path));
                 number_of_errors++;
                 last_error_msg = $sformatf("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",inst_mem[i],physical_data[63:32],iram_rtl_path);
               end
                
            end

          end

          // print last error, in case print2log == 0
          if (!print2log && number_of_errors>1) `slu_error(tID,(last_error_msg));
     
          if (number_of_errors!=0)  `slu_error(tID, ($sformatf("RAM to check is %s, source to check is %s - Ended with %0d errors",ram_to_check,src_to_compare,number_of_errors)));

    
   
    endtask:compare_iram
 
  task compare_dram(input punit_ram_sel_e ram_to_check = PCODE_DRAM, string src_to_compare = "",bit print2log = 0 );
  
      // <add descripton>
      // inputs:
      //     ram to check
      //     src file to compare to
      //     
    
      string tID = "RAM_COMPARE";
    
      int inst_mem[0:IRAM_NUM_ENTRIES*IRAM_NUM_BANKS*2-1];
      int data_mem[0:DRAM_NUM_ENTRIES*DRAM_NUM_BANKS-1];
      int crash_mem[0:IRAM_NUM_ENTRIES*1*2-1];
      int telem_mem[0:IRAM_NUM_ENTRIES*1*2-1];
    
      int recipe_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int sdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int vdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int record_mem[0:RECIPE_NUM_ENTRIES*2-1];
      //
     
      string dram_rtl_path;
    
      string iram_rtl_path;
      string iram_ecc_rtl_path;
    
      string sram_rtl_path;
      string sram_ecc_rtl_path;
    
      // Data to write to MEM
      bit [39:0] data_with_ecc;
    
      bit [31:0] iram_entry;
      byte iram_ecc = 'h0;
    
      bit [31:0] sram_entry;
      byte sram_ecc = 'h0;
    
      // to calcuate mem location
      int template_num = -1;
      int ram_row_number = 0;
      int ram_col_number = -1;
    
      int bk_sel, super_bk_sel;

      logic [71:0] physical_data;

      int unsigned number_of_errors = 0;
      string last_error_msg;
    
   
       
    
          // init src to default
          if (src_to_compare == "") src_to_compare = "dram.mem";
          // init the image to compare to into local array
          $readmemh(src_to_compare, data_mem);
          
          `slu_msg(UVM_LOW, tID, ($sformatf("RAM to check is %s, source to check is %s",ram_to_check,src_to_compare)));
   
          for(int i=0; i < DRAM_NUM_ENTRIES*DRAM_NUM_BANKS; i++) // number of lines in file
          begin
    
        template_num = (i/DRAM_NUM_ENTRIES);
        ram_row_number = (i%DRAM_NUM_ENTRIES);

        // ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array

    
            dram_rtl_path = $sformatf("%s.punit_dram_%0d.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array[%0d][39:0]",punit_sram_bist_top,template_num,ram_row_number);
            physical_data[39:0] = slu_vpi_get_value_by_name(dram_rtl_path);
            data_with_ecc = {1'b0,calc_32bit_ecc(data_mem[i]), data_mem[i]};

            // checking
            if (physical_data[39:0] !== data_with_ecc) begin
              // always print 1st and last error
              if (print2log || (number_of_errors == 0))  `slu_error(tID,("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",data_mem[i],physical_data[39:0],dram_rtl_path));
              number_of_errors++;
              last_error_msg = $sformatf("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",data_mem[i],physical_data[39:0],dram_rtl_path);
            end
          end // for(int i=0; i < DRAM_NUM_ENTRIES*DRAM_NUM_BANKS; i

          // print last error, in case print2log == 0
          if (!print2log && number_of_errors>1) `slu_error(tID,(last_error_msg));
     
          if (number_of_errors!=0)  `slu_error(tID, ($sformatf("RAM to check is %s, source to check is %s - Ended with %0d errors",ram_to_check,src_to_compare,number_of_errors)));

    
    endtask:compare_dram

  task compare_vdram(input punit_ram_sel_e ram_to_check = VOLATILE_DRAM, string src_to_compare = "",bit print2log = 0 );
  
      // <add descripton>
      // inputs:
      //     ram to check
      //     src file to compare to
      //     
    
      string tID = "RAM_COMPARE";
    
      int inst_mem[0:IRAM_NUM_ENTRIES*IRAM_NUM_BANKS*2-1];
      int data_mem[0:DRAM_NUM_ENTRIES*DRAM_NUM_BANKS-1];
      int crash_mem[0:IRAM_NUM_ENTRIES*1*2-1];
      int telem_mem[0:IRAM_NUM_ENTRIES*1*2-1];
    
      int recipe_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int sdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int vdram_mem[0:RECIPE_NUM_ENTRIES*2-1];
      int record_mem[0:RECIPE_NUM_ENTRIES*2-1];
      //
     
      string dram_rtl_path;
    
      string iram_rtl_path;
      string iram_ecc_rtl_path;
    
      string sram_rtl_path;
      string sram_ecc_rtl_path;
    
      // Data to write to MEM
      bit [39:0] data_with_ecc;
    
      bit [31:0] iram_entry;
      byte iram_ecc = 'h0;
    
      bit [31:0] sram_entry;
      byte sram_ecc = 'h0;
    
      // to calcuate mem location
      int template_num = -1;
      int ram_row_number = 0;
      int ram_col_number = -1;
    
      int bk_sel, super_bk_sel;

      logic [71:0] physical_data;

      int unsigned number_of_errors = 0;
      string last_error_msg;
    
          // init src to default
          if (src_to_compare == "") src_to_compare = "dram.mem";
          // init the image to compare to into local array
          $readmemh(src_to_compare, data_mem);
          
          `slu_msg(UVM_LOW, tID, ($sformatf("RAM to check is %s, source to check is %s",ram_to_check,src_to_compare)));
   
          for(int i=0; i < VDRAM_SIZE; i++) // number of lines in file
          begin

            template_num = (i/DRAM_NUM_ENTRIES);
            ram_row_number = (i%DRAM_NUM_ENTRIES);

   
            dram_rtl_path = $sformatf("%s.punit_dram_%0d.ip764hduspsr2048x39m4b2s0r2p1d0_upf_wrapper.ip764hduspsr2048x39m4b2s0r2p1d0.ip764hduspsr2048x39m4b2s0r2p1d0_bmod.ip764hduspsr2048x39m4b2s0r2p1d0_array.array[%0d][39:0]",punit_sram_bist_top,template_num,ram_row_number);
            physical_data[39:0] = slu_vpi_get_value_by_name(dram_rtl_path);
            data_with_ecc = {1'b0,calc_32bit_ecc(data_mem[i]), data_mem[i]};

            // checking
            if (physical_data[39:0] !== data_with_ecc) begin
              // always print 1st and last error
              if (print2log || (number_of_errors == 0))  `slu_error(tID,("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",data_mem[i],physical_data[39:0],dram_rtl_path));
              number_of_errors++;
              last_error_msg = $sformatf("compare missmatch. expected: 'h%0h, actual: 'h%0h [hdl path: %s]",data_mem[i],physical_data[39:0],dram_rtl_path);
            end
          end // for(int i=0; i < DRAM_NUM_ENTRIES*DRAM_NUM_BANKS; i

          // print last error, in case print2log == 0
          if (!print2log && number_of_errors>1) `slu_error(tID,(last_error_msg));
     
          if (number_of_errors!=0)  `slu_error(tID, ($sformatf("RAM to check is %s, source to check is %s - Ended with %0d errors",ram_to_check,src_to_compare,number_of_errors)));
    
    endtask:compare_vdram
    
//  // store_cl_record 
//  // - cloning crashlog record into ref array
//  function automatic void store_cl_record(ref bit[63:0] ref_array[]);
//  
//    logic [71:0] physical_data;
//
//    for(int i=0; i<RECORD_NUM_ENTRIES ; i++) begin
//        physical_data[63:0] = slu_vpi_get_value_by_name(get_sram_hdl_path(RECORD_OFFSET + i*4,0));
//        ref_array[i] = physical_data[63:0];
//        `slu_msg(UVM_LOW,pkg_id,("store_cl_record index 'h%0h, address 'h%0h. data: 'h%0h [sram path: %s]",i,RECORD_OFFSET + i*4,physical_data[63:0],get_sram_hdl_path(RECORD_OFFSET + i*4,0)));	               
//    end
//
//  endfunction:store_cl_record
//
//  // compare_cl_record 
//  // - comparing crashlog record into ref array
//  function automatic void compare_cl_record(ref bit[63:0] ref_array[]);
//  
//    logic [63:0] physical_data;
//
//    for(int i=0; i<RECORD_NUM_ENTRIES ; i++) begin
//        physical_data[63:0] = slu_vpi_get_value_by_name(get_sram_hdl_path(RECORD_OFFSET + i*4,0));
//        if (ref_array[i] != physical_data[63:0]) begin
//            `slu_error(pkg_id, ($sformatf("compare_cl_record missmatch index 'h%0h, address 'h%0h. Expected - 'h%0h , Actual 'h%0h [path: %s]",i,RECORD_OFFSET + i*4,ref_array[i],physical_data,get_sram_hdl_path(RECORD_OFFSET + i*4,0))));
//            break;
//        end
//        else begin
//          `slu_msg(UVM_LOW,pkg_id,("compare_cl_record match - index 'h%0h, address 'h%0h. data: 'h%0h [sram path: %s]",i,RECORD_OFFSET + i*4,physical_data[63:0],get_sram_hdl_path(RECORD_OFFSET + i*4,0)));	               
//        end
//
//    end
//
//
//  endfunction:compare_cl_record
//
//  // store_sdram 
//  // - cloning sdram into ref array
//  function automatic void store_sdram(ref int ref_array[]);
//  
//    logic [31:0] physical_data;
//
//    for(int i=0; i<SDRAM_SIZE ; i++) begin
//        physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(PERSIST_DRAM_OFFSET + i*4));
//        ref_array[i] = physical_data[31:0];
//        `slu_msg(UVM_LOW,pkg_id,("store_sdram index 'h%0h, address 'h%0h. data: 'h%0h [dram path: %s]",i,PERSIST_DRAM_OFFSET + i*4,physical_data[31:0],get_dram_hdl_path(PERSIST_DRAM_OFFSET + i*4)));	               
//    end
//
//  endfunction:store_sdram
//
//  // compare_sdram 
//  // - comparing sdram into ref array
//  function automatic void compare_sdram(ref int ref_array[]);
//  
//    logic [31:0] physical_data;
//
//    for(int i=0; i<SDRAM_SIZE ; i++) begin
//        physical_data = slu_vpi_get_value_by_name(get_dram_hdl_path(PERSIST_DRAM_OFFSET + i*4));
//        if (ref_array[i] != physical_data[31:0]) begin
//            `slu_error(pkg_id, ($sformatf("compare_sdram missmatch Expected - 'h%0h , Actual 'h%0h [path: %s]",ref_array[i],physical_data,get_dram_hdl_path(PERSIST_DRAM_OFFSET + i*4))));
//            break;
//        end
//    end
//
//  endfunction:compare_sdram

  `include "punit_ram_utils_seqlib.sv" 

    
endpackage :punit_ram_utils_pkg

`endif
