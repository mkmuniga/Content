//------------------------------------------------------------------------------
//
//  INTEL CONFIDENTIAL
//
//  Copyright 2009 Intel Corporation All Rights Reserved.
//
//  The source code contained or described herein and all documents related
//  to the source code (Material) are owned by Intel Corporation or its
//  suppliers or licensors. Title to the Material remains with Intel
//  Corporation or its suppliers and licensors. The Material contains trade
//  secrets and proprietary and confidential information of Intel or its
//  suppliers and licensors. The Material is protected by worldwide copyright
//  and trade secret laws and treaty provisions. No part of the Material may
//  be used, copied, reproduced, modified, published, uploaded, posted,
//  transmitted, distributed, or disclosed in any way without Intel's prior
//  express written permission.
//
//  No license under any patent, copyright, trade secret or other intellectual
//  property right is granted to or conferred upon you by disclosure or
//  delivery of the Materials, either expressly, by implication, inducement,
//  estoppel or otherwise. Any license under such intellectual property rights
//  must be express and approved by Intel in writing.
//
//------------------------------------------------------------------------------
//
//  Collateral Description:
//  IOSF - Sideband Channel IP
//
//  Source organization:
//  SEG / SIP / IOSF IP Engineering
//
//  Support Information:
//  WEB: http://moss.amr.ith.intel.com/sites/SoftIP/Shared%20Documents/Forms/AllItems.aspx
//  HSD: https://vthsd.fm.intel.com/hsd/seg_softip/default.aspx
//
//  Revision:
//  IOSF_SVC_2021WW24
//
//------------------------------------------------------------------------------
`ifndef INC_DEFS
`define INC_DEFS
/**
 * Testbench wide definitions
 */
// ============================================================================
// Type definitions 
// ============================================================================
// Xaction related enum defs
typedef enum {IOSF_081, IOSF_082, IOSF_083, IOSF_090, IOSF_1, IOSF_11, IOSF_12} iosf_sb_spec_ver_e;
typedef enum {SIMPLE, MSGD, REGIO, COMP, BULK_REGIO} xaction_type_e;
typedef enum {POSTED, NON_POSTED} xaction_class_e;
typedef enum {UNICAST, MULTICAST, BROADCAST} xaction_tx_type_e;

typedef enum {LEGACY_RTR, SEGMENT_RTR, INTER_SEGMENT_RTR, SINGLE_NETWORK_RTR} rtr_type_e;
typedef enum {LEGACY_EP, SEGMENT_EP, INTER_SEGMENT_EP} ep_type_e;

//typedef for tracker format
typedef enum {SIP_FMT, MOAT_FMT, BOTH_FMT} trk_fmt_e;

// Link related enum defs
typedef enum {RTR_2_RTR, RTR_2_EP} connection_type_e;
typedef enum {DATA_CHANNEL_FWD, DATA_CHANNEL_BWD, DATA_NP_CHANNEL_BWD, DATA_CHANNEL_AF_BWD,PWR_CHANNEL_FWD, PWR_CHANNEL_BWD, PM_CHANNEL_FWD, PM_CHANNEL_BWD} channel_type_e;
typedef enum {TX, RX} link_type_e;

// Power related enum defs
typedef enum {AGENT_INTF, FABRIC_INTF} ism_intf_type_e;
typedef enum bit [1:0]{
              ISMSM_ACTIVE=2'b00, 
              ISMSM_IDLE=2'b01, 
              ISMSM_OFF=2'b10, 
              ISMSM_CRDREINIT=2'b11} ismsm_state_e;

typedef enum bit [2:0]{
              ISM_WAKE=3'b000, 
              ISM_SLEEP=3'b001, 
              ISM_SHUTDOWN=3'b010, 
              ISM_CRD_REINIT=3'b011,
              ISM_ACK_WAKE=3'b100, 
              ISM_ACK_SLEEP=3'b101, 
              ISM_ACK_SHUTDOWN=3'b110, 
              ISM_ACK_CRD_REINIT=3'b111
              } ism_cmd_e;

typedef enum bit [1:0]{
              PWRDWN_OFF=2'b00, 
              PWRDWN_REQ=2'b01, 
              PWRDWN_REQ_GRANT=2'b10, 
              PWRDWN_ON=2'b11} pm_state_e;
typedef enum bit [2:0]{
              PM_PWDN_REQ=3'b000, 
              PM_PWDN_CMD=3'b001, 
              PM_PWRUP_CMD=3'b010, 
              PM_PWDN_REQ_ACK=3'b011, 
              PM_PWDN_CMD_ACK=3'b100, 
              PM_PWRUP_CMD_ACK=3'b101
} pm_cmd_e;

//Credit related enum
typedef enum bit [1:0]{
              CRD_NOT_INIT=2'b00, 
              CRD_DONE_INIT=2'b01, 
              CRD_REINIT=2'b10} crd_state_e;

// ISM related enum defs
typedef enum logic [2:0] {
			  AGENT_UNDEF       = 3'bxxx,
			  AGENT_CREDIT_REQ  = 3'b100,
			  AGENT_CREDIT_INIT = 3'b101,
			  AGENT_CREDIT_DONE = 3'b110,
			  AGENT_ACTIVE      = 3'b011, 
			  AGENT_IDLE_REQ    = 3'b001, 
			  AGENT_IDLE        = 3'b000, 
			  AGENT_ACTIVE_REQ  = 3'b010
			  } agent_ism_type_e;

typedef enum logic [2:0] {
			  FABRIC_UNDEF       = 3'bxxx,
			  FABRIC_CREDIT_REQ  = 3'b100,
			  FABRIC_CREDIT_ACK  = 3'b110,
			  FABRIC_CREDIT_INIT = 3'b101,
			  FABRIC_ACTIVE      = 3'b011, 
			  FABRIC_IDLE_NAK    = 3'b001, 
			  FABRIC_IDLE        = 3'b000, 
			  FABRIC_ACTIVE_REQ  = 3'b010
			  } fabric_ism_type_e;

typedef enum logic {
             POK_UNDEF  = 1'bx,
             POK_ASSERTED   = 1'b1,
             POK_DEASSERTED = 1'b0
             } pok_type_e;

typedef enum bit {
             STALL_CRD = 1'b1,
             UNSTALL_CRD = 1'b0
             } stall_type_e;

const int ism_idle_cnt_t = 16;
const int min_req_credit_t = 1;
//Number of clocks to wait before issuing ack to the pwrdwn request from the 
//power manager from ep_tlm
const int pwrdwn_cmd_ack_clocks_t = 2000;

// Configuration related enum defs
typedef enum {ABS_TLM, ABS_RTL} abstraction_level_e;

// Field related defs
typedef logic[7:0]  flit_t;
typedef bit[7:0]    pid_t;
typedef bit[15:0]   epid_t;
typedef int       nid_t;  
typedef flit_t    opcode_t;
typedef logic [2:0] tag_t;
typedef logic [1:0] rsp_t;
typedef logic       sai_t;

// ============================================================================
// Constants
// ============================================================================

typedef enum opcode_t { 

    // Opcode ranges

    REGIO_GLOBAL_OPCODE_START  = 8'b0000_0000,
    REGIO_GLOBAL_OPCODE_END    = 8'b0000_1111,
    REGIO_EPSPEC_OPCODE_START  = 8'b0001_0000,
    REGIO_EPSPEC_OPCODE_END    = 8'b0001_1111,

    COMP_GLOBAL_OPCODE_START   = 8'b0010_0000,
    COMP_GLOBAL_OPCODE_END     = 8'b0010_0001,

    RESERVED_OPCODE_START      = 8'b0010_0010,
    RESERVED_OPCODE_END        = 8'b0010_0111,                 
    
    COMMON_USAGE_OPCODE_START  = 8'b0010_1000,
    COMMON_USAGE_OPCODE_END    = 8'b0011_1111,

                        
    MSGD_GLOBAL_OPCODE_START   = 8'b0100_0000,
    MSGD_GLOBAL_OPCODE_END     = 8'b0101_1111,
    MSGD_EPSPEC_OPCODE_START   = 8'b0110_0000,
    MSGD_EPSPEC_OPCODE_END     = 8'b0111_1111,

    SIMPLE_GLOBAL_OPCODE_START = 8'b1000_0000,
    SIMPLE_GLOBAL_OPCODE_END   = 8'b1001_1111,
    SIMPLE_EPSPEC_OPCODE_START = 8'b1010_0000,
    SIMPLE_EPSPEC_OPCODE_END   = 8'b1111_1111

} opcode_range_e;

typedef enum opcode_t { 

  // Global simple messages opcodes
   
    OP_ASSERT_INTA     = 8'b1000_0000,
    OP_ASSERT_INTB     = 8'b1000_0001,
    OP_ASSERT_INTC     = 8'b1000_0010,
    OP_ASSERT_INTD     = 8'b1000_0011,

    OP_DEASSERT_INTA   = 8'b1000_0100,
    OP_DEASSERT_INTB   = 8'b1000_0101,
    OP_DEASSERT_INTC   = 8'b1000_0110,
    OP_DEASSERT_INTD   = 8'b1000_0111,   
    OP_DO_SERR         = 8'b1000_1000, 
    OP_ASSERT_SCI      = 8'b1000_1001,
    OP_DEASSERT_SCI    = 8'b1000_1010,
    OP_ASSERT_SSMI     = 8'b1000_1011,
    OP_ASSERT_SMI      = 8'b1000_1100,
    OP_DEASSERT_SSMI   = 8'b1000_1101,
    OP_DEASSERT_SMI    = 8'b1000_1110,
    OP_SMI_ACK         = 8'b1000_1111,
    OP_ASSERT_PME      = 8'b1001_0000,
    OP_DEASSERT_PME    = 8'b1001_0001,
    OP_SYNCCOMP        = 8'b1001_0010, 
    OP_ASSERT_NMI      = 8'b1001_0011,
    OP_DEASSERT_NMI    = 8'b1001_0100,

   //Global common usage message opcodes
    OP_BOOTPREP          =  8'b0010_1000,
    OP_BOOTPREP_ACK      =  8'b0010_1001,
    OP_RESETPREP         =  8'b0010_1010,
    OP_RESETPREP_ACK     =  8'b0010_1011,
    OP_RST_REQ           =  8'b0010_1100,
    OP_VIRTUAL_WIRE      =  8'b0010_1101,
    OP_FORCE_PWRGATE_POK =  8'b0010_1110,
    OP_DVFS_WORKPOINT    =  8'b0010_1111,
                     

    // Global messages with data opcodes
  
    OP_PM_REQ          = 8'b0100_0000,
    OP_PM_DMD          = 8'b0100_0001,
    OP_PM_RSP          = 8'b0100_0010,
    OP_LTR             = 8'b0100_0011,
    OP_DOPME           = 8'b0100_0100,
	FUSE_MSG		   = 8'b0100_0101,	
	OP_MCA		   = 8'b0100_0110,	
	OP_PMON		   = 8'b0100_0111,	
    `ifdef SVC_USE_OLD_OPCODE
    OP_PCI_PM         = 8'b0100_1000,
    `else
    OP_PCIE_PM         = 8'b0100_1000,
    `endif
    OP_PCI_ERROR       = 8'b0100_1001,
    OP_SYNCSTARTCMD    = 8'b0101_0000,
    OP_LOCALSYNC       = 8'b0101_0001, 
    OP_ASSERT_PME_WITHDATA = 8'b0101_0010,
    OP_DEASSERT_PME_WITHDATA = 8'b0101_0011,
    OP_ASSERT_IRQN    = 8'b0101_0100,
    OP_DEASSERT_IRQN  = 8'b0101_0101,
    OP_SLEEP_LEVEL_REQ = 8'b0101_0110,
    OP_SLEEP_LEVEL_RSP = 8'b0101_0111,
    OP_QOS_DMD         = 8'b0101_1000,
    OP_QOS_RSP         = 8'b0101_1001,
    // these are EP specific opcodes and configurable cfg_objects in iosf_sb_cfg.svh 
    //OP_SPI_READ        = 8'b0110_0001, 
    //OP_SPI_WRITE       = 8'b0110_0010,
    //OP_SPI_ERASE       = 8'b0110_0100,

    // CBB hotfix (grath)                                                
	IP_READY		   = 8'b1101_0000,	
	FUSE_PULL    	   = 8'b1011_1000,
                        
    // Global completions message opcodes
    OP_CMP             = 8'b0010_0000,
    OP_CMPD            = 8'b0010_0001,

    // CBB hotfix (grath)                        
    PM2IP              = 8'b0110_1000,
    IP2PM              = 8'b0111_1110,
                        
    // Global register access messages opcodes

    OP_MRD             = 8'b0000_0000,
    OP_MWR             = 8'b0000_0001,
    OP_IORD            = 8'b0000_0010,
    OP_IOWR            = 8'b0000_0011, 
    OP_CFGRD           = 8'b0000_0100,
    OP_CFGWR           = 8'b0000_0101,
    OP_CRRD            = 8'b0000_0110,
    OP_CRWR            = 8'b0000_0111, 
    BULK_RD            = 8'b0000_1000,
    BULK_WR            = 8'b0000_1001
} opcode_e;

typedef enum logic[1:0] {
    RSP_SUCCESSFUL     = 2'b00,
    RSP_NOTSUPPORTED   = 2'b01,
    RSP_POWEREDDOWN    = 2'b10,
    RSP_MCASTMIXED     = 2'b11
} rsp_value_e;

/**************************************************************************
 * 
 * ovm_verbosity:
 * OVM_NONE=0, OVM_LOW=100, _MEDIUM=200, _HIGH=300, _FULL=400, _DEBUG=500
 * 
 * So, setting +OVM_VERBOSITY means
 * OVM_NONE(0)   enables VERBOSITY_FATAL, VERBOSITY_ERROR
 * OVM_LOW(100)    enables OVM_NONE   plus  VERBOSE_WARNING
 * OVM_MEDIUM(200) enables OVM_LOW    plus  VERBOSE_PROGRESS
 * OVM_HIGH(300)   enables OVM_MEDIUM plus  VERBOSE_TX_RX
 * OVM_FULL(400)   enables OVM_HIGH   plus  VERBOSE_DEBUG_2
 * OVM_DEBUG(500)  enables OVM_FULL   plus  OVM debug messages
 **************************************************************************/

typedef enum int {
    VERBOSE_DEBUG_2     = 400, // Print more debug messages
    VERBOSE_PATH        = 300, // Print path information (each component receives or sends the xaction prints the xaction information)
    VERBOSE_TX_RX       = 250, // Print an info message whenever a xaction is sent or received (end to end) +API
    VERBOSE_PROGRESS    = 200, // Print an info message whenever monitor/scoreboard receives it
    VERBOSE_WARNING     = 100, // VC warning messages
    VERBOSE_NONE        = 0  // Print final scoreboard report                  
} verbosity_level_e;

const static int VERBOSE_ERROR = 0;     // DUT produced unexpected behavior

// command queues to drive constraints

const opcode_t DEFAULT_SIMPLE_OPCODES[$] = '{
  OP_ASSERT_INTA,   OP_ASSERT_INTB,   OP_ASSERT_INTC,   OP_ASSERT_INTD,
  OP_DEASSERT_INTA, OP_DEASSERT_INTB, OP_DEASSERT_INTC, OP_DEASSERT_INTD, OP_DO_SERR,
  OP_ASSERT_SCI, OP_DEASSERT_SCI, OP_ASSERT_SSMI, OP_ASSERT_SMI, OP_DEASSERT_SSMI,
  OP_DEASSERT_SMI, OP_SMI_ACK, OP_ASSERT_PME, OP_DEASSERT_PME, OP_SYNCCOMP,OP_ASSERT_NMI,  
  OP_DEASSERT_NMI   
};

const opcode_t DEFAULT_MSGD_OPCODES[$] = '{OP_PM_REQ, OP_PM_DMD, OP_PM_RSP,
                                           OP_LTR,OP_DOPME, OP_PMON, OP_MCA ,FUSE_MSG, 
                                           `ifdef SVC_USE_OLD_OPCODE
                                           OP_PCI_PM, 
                                           `else
                                           OP_PCIE_PM, 
                                           `endif
                                           OP_PCI_ERROR,
                                           OP_SYNCSTARTCMD, OP_LOCALSYNC,OP_ASSERT_PME_WITHDATA,
                                           OP_DEASSERT_PME_WITHDATA,OP_ASSERT_IRQN
                                           ,OP_DEASSERT_IRQN,//OP_SPI_WRITE,OP_SPI_READ,OP_SPI_ERASE,
                                           OP_SLEEP_LEVEL_REQ,OP_SLEEP_LEVEL_RSP,OP_QOS_DMD,OP_QOS_RSP,
                                           OP_BOOTPREP ,OP_BOOTPREP_ACK,OP_RESETPREP,OP_RESETPREP_ACK,OP_RST_REQ,
                                           OP_VIRTUAL_WIRE,
                                           OP_FORCE_PWRGATE_POK,OP_DVFS_WORKPOINT };

const opcode_t DEFAULT_COMP_OPCODES[$] = '{OP_CMP, OP_CMPD};

const opcode_t DEFAULT_REGIO_OPCODES[$] = '{
  OP_MRD, OP_MWR, OP_IORD, OP_IOWR, 
  OP_CFGRD, OP_CFGWR, OP_CRRD, OP_CRWR
};


/*const opcode_t DEFAULT_OPCODES[$] = {
  DEFAULT_SIMPLE_OPCODES, DEFAULT_MSGD_OPCODES,
  DEFAULT_COMP_OPCODES,   DEFAULT_REGIO_OPCODES
};*/


const opcode_t DEFAULT_OPCODES[$] = {
  DEFAULT_SIMPLE_OPCODES, DEFAULT_MSGD_OPCODES,
  8'd32, 8'd33,   DEFAULT_REGIO_OPCODES
};

typedef bit[1:0] addrlen_e;
typedef bit[2:0] bar_e;
typedef bit[1:0] sb_space_e;

typedef enum addrlen_e {

    ADDR_16_bit = 'b0,
    ADDR_48_bit = 'b1
   // ADDR_rsvd_1 = 2'b10,
   // ADDR_rsvd_2 = 2'b11

} addrlen_modes;

typedef enum bar_e {

    BAR_0 = 3'b000,
    BAR_1 = 3'b001,
    BAR_2 = 3'b010,
    BAR_3 = 3'b011,
    BAR_4 = 3'b100,
    BAR_5 = 3'b101,
    BAR_6 = 3'b110,
    BAR_7 = 3'b111

} bar_number;

typedef enum sb_space_e {
    MEM_SPACE = 2'b00,
    IO_SPACE  = 2'b01,
    PCI_SPACE = 2'b10,
    CR_SPACE  = 2'b11
} addr_space;

//xaction supported per dest-pid for EP
typedef enum {P_MSG,NP_MSG,PNP_MSG} supp_xact_e;

typedef enum {SEG_RTR, NTC_RTR} rtr_table_map_e;

typedef enum {LOCAL_PID, GLOBAL_PID, LOCAL_GLOBAL_PID, GLOBAL_LOCAL_PID} mcast_type;

typedef enum int {AGENT=0, FABRIC=1, RATA=2} sb_vc_t;
`endif
