//-----------------------------------------------------------------------------
// Title         : DMR D2D Stack Test Island module file
// Project       : *Valley
//-----------------------------------------------------------------------------
// File          : d2d_bind_mod.sv
// Author        : floydcma
// Created       : 9/19/2022
//-----------------------------------------------------------------------------
// Description :
// This is the test island module of the D2D testbench, includes all intfs
// and registers them to the appropriate tb hierarchy.
//-----------------------------------------------------------------------------
// Copyright (c) 2022 by Intel Corporation This model is the confidential and
// proprietary property of Intel Corporation and the possession or use of this
// file requires a written license from Intel Corporation.
//
// The source code contained or described herein and all documents related to
// the source code ("Material") are owned by Intel Corporation or its suppliers
// or licensors. Title to the Material remains with Intel Corporation or its
// suppliers and licensors. The Material contains trade secrets and proprietary
// and confidential information of Intel or its suppliers and licensors. The
// Material is protected by worldwide copyright and trade secret laws and
// treaty provisions. No part of the Material may be used, copied, reproduced,
// modified, published, uploaded, posted, transmitted, distributed, or
// disclosed in any way without Intel's prior express written permission.
//
// No license under any patent, copyright, trade secret or other intellectual
// property right is granted to or conferred upon you by disclosure or delivery
// of the Materials, either expressly, by implication, inducement, estoppel or
// otherwise. Any license under such intellectual property rights must be
// express and approved by Intel in writing.
//
//------------------------------------------------------------------------------
`define UFI_CONN_BFM_A2F_2_RTL_A2F(SIG2, SIG1)\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_txcon_req 		 = SIG2.txcon_req;\
  force SIG2.rxcon_ack 					 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxcon_ack;\
  force SIG2.rxdiscon_nack				 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxdiscon_nack;\
  force SIG2.rx_empty					 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rx_empty;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_coh_conn_req	 = SIG2.coh_conn_req;\
  force SIG2.coh_conn_ack				 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_coh_conn_ack;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_local_fatal		 = SIG2.local_fatal;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_local_viral		 = SIG2.local_viral;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_level	 = SIG2.distress_level;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_resource  	 = SIG2.distress_resource;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_nid	 = SIG2.distress_nid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_is_valid		 = SIG2.req_is_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_early_valid	 = SIG2.req_early_valid;\
  force SIG2.req_block					 = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_block;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_cancel_valid	 = SIG2.req_cancel_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_cancel_status	 = SIG2.req_cancel_status;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_protocol_id	 = SIG2.req_protocol_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_vc_id		 = SIG2.req_vc_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_shared_credit	 = SIG2.req_shared_credit;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_header		 = SIG2.req_header;\
  force SIG2.req_rxcrd_valid				 = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_valid;\
  force SIG2.req_rxcrd_protocol_id			 = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_protocol_id;\
  force SIG2.req_rxcrd_vc_id				 = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_vc_id;\
  force SIG2.req_rxcrd_shared				 = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_shared;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_txblock_crd_flow	 = SIG2.req_txblock_crd_flow;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_is_valid		 = SIG2.data_is_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_early_valid	 = SIG2.data_early_valid;\
  force SIG2.data_block					 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_block;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_cancel_valid	 = SIG2.data_cancel_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_cancel_status	 = SIG2.data_cancel_status;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_protocol_id	 = SIG2.data_protocol_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_vc_id		 = SIG2.data_vc_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_shared_credit	 = SIG2.data_shared_credit;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_header 		 = SIG2.data_header;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_eop		 = SIG2.data_eop;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_payload		 = SIG2.data_payload;\
  force SIG2.data_rxcrd_valid				 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_valid;\
  force SIG2.data_rxcrd_protocol_id			 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_protocol_id;\
  force SIG2.data_rxcrd_vc_id				 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_vc_id;\
  force SIG2.data_rxcrd_shared				 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_shared;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_txblock_crd_flow	 = SIG2.data_txblock_crd_flow;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_is_valid		 = SIG2.rsp_is_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_early_valid	 = SIG2.rsp_early_valid;\
  force SIG2.rsp_block					 = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_block;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_cancel_valid	 = SIG2.rsp_cancel_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_cancel_status	 = SIG2.rsp_cancel_status;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_protocol_id	 = SIG2.rsp_protocol_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_vc_id		 = SIG2.rsp_vc_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_shared_credit	 = SIG2.rsp_shared_credit;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_header		 = SIG2.rsp_header;\
  force SIG2.rsp_rxcrd_valid				 = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_valid;\
  force SIG2.rsp_rxcrd_protocol_id			 = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_protocol_id;\
  force SIG2.rsp_rxcrd_vc_id				 = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_vc_id;\
  force SIG2.rsp_rxcrd_shared				 = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_shared;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_txblock_crd_flow	 = SIG2.rsp_txblock_crd_flow;

`define UFI_CONN_RTL_F2A_2_BFM_F2A(SIG1, SIG2)\
  force SIG2.data_dst_id					 = 13'b0;\
  force SIG2.data_src_id					 = 13'b0;\
  force SIG2.data_parity					 = 1'b0;\
  force SIG2.rsp_dst_id					 = 13'b0;\
  force SIG2.rsp_src_id					 = 13'b0;\
  force SIG2.rsp_parity					 = 1'b0;\
  force SIG2.req_dst_id					 = 13'b0;\
  force SIG2.req_src_id					 = 13'b0;\
  force SIG2.req_parity					 = 1'b0;\
  force SIG2.data_half_line_valid			 = 1'b1;\
  force SIG2.txcon_req					 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_txcon_req;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxcon_ack		 = SIG2.rxcon_ack;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxdiscon_nack	 = SIG2.rxdiscon_nack;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rx_empty		 = SIG2.rx_empty;\
  force SIG2.global_fatal				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_fatal;\
  force SIG2.global_viral				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_viral;\
  force SIG2.distress_level				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_level;\
  force SIG2.distress_resource				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_resource;\
  force SIG2.distress_nid				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_nid;\
  force SIG2.req_is_valid				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_is_valid;\
  force SIG2.req_early_valid				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_early_valid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_block		 = SIG2.req_block;\
  force SIG2.req_protocol_id				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_protocol_id;\
  force SIG2.req_vc_id					 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_vc_id;\
  force SIG2.req_shared_credit				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_shared_credit;\
  force SIG2.req_header					 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_header;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_valid	 = SIG2.req_rxcrd_valid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_protocol_id	 = SIG2.req_rxcrd_protocol_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_vc_id	 = SIG2.req_rxcrd_vc_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_shared	 = SIG2.req_rxcrd_shared;\
  force SIG2.req_txblock_crd_flow			 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_txblock_crd_flow;\
  force SIG2.data_is_valid				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_is_valid;\
  force SIG2.data_early_valid				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_early_valid;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_block		 = SIG2.data_block;\
  force SIG2.data_protocol_id				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_protocol_id;\
  force SIG2.data_vc_id					 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_vc_id;\
  force SIG2.data_shared_credit				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_shared_credit;\
  force SIG2.data_header				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_header;\
  force SIG2.data_eop					 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_eop;\
  force SIG2.data_payload				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_payload;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_valid	 = SIG2.data_rxcrd_valid;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_protocol_id = SIG2.data_rxcrd_protocol_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_vc_id	 = SIG2.data_rxcrd_vc_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_shared	 = SIG2.data_rxcrd_shared;\
  force SIG2.data_txblock_crd_flow			 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_txblock_crd_flow;\
  force SIG2.rsp_is_valid				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_is_valid;\
  force SIG2.rsp_early_valid				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_early_valid;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_block		 = SIG2.rsp_block;\
  force SIG2.rsp_protocol_id				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_protocol_id;\
  force SIG2.rsp_vc_id					 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_vc_id;\
  force SIG2.rsp_shared_credit				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_shared_credit;\
  force  SIG2.rsp_header				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_header;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_valid	 = SIG2.rsp_rxcrd_valid;\
  force  ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_protocol_id	 = SIG2.rsp_rxcrd_protocol_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_vc_id	 = SIG2.rsp_rxcrd_vc_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_shared	 = SIG2.rsp_rxcrd_shared;\
  force SIG2.rsp_txblock_crd_flow			 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_txblock_crd_flow;



`define UFI_CONN_BFM_A2F_2_RTL_F2A(SIG1, SIG2)\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_txcon_req 		 = SIG2.txcon_req;\
  force SIG2.rxcon_ack 					 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxcon_ack;\
  force SIG2.rxdiscon_nack				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxdiscon_nack;\
  force SIG2.rx_empty					 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rx_empty;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_fatal		 = SIG2.local_fatal;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_viral		 = SIG2.local_viral;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_level	 = SIG2.distress_level;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_resource  	 = SIG2.distress_resource;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_nid	 = SIG2.distress_nid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_is_valid		 = SIG2.req_is_valid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_early_valid	 = SIG2.req_early_valid;\
  force SIG2.req_block					 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_block;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_protocol_id	 = SIG2.req_protocol_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_vc_id		 = SIG2.req_vc_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_shared_credit	 = SIG2.req_shared_credit;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_header		 = SIG2.req_header;\
  force SIG2.req_rxcrd_valid				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_valid;\
  force SIG2.req_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_protocol_id;\
  force SIG2.req_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_vc_id;\
  force SIG2.req_rxcrd_shared				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_txblock_crd_flow	 = SIG2.req_txblock_crd_flow;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_is_valid		 = SIG2.data_is_valid;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_early_valid	 = SIG2.data_early_valid;\
  force SIG2.data_block					 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_block;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_protocol_id	 = SIG2.data_protocol_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_vc_id		 = SIG2.data_vc_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_shared_credit	 = SIG2.data_shared_credit;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_header 		 = SIG2.data_header;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_eop		 = SIG2.data_eop;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_payload		 = SIG2.data_payload;\
  force SIG2.data_rxcrd_valid				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_valid;\
  force SIG2.data_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_protocol_id;\
  force SIG2.data_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_vc_id;\
  force SIG2.data_rxcrd_shared				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_txblock_crd_flow	 = SIG2.data_txblock_crd_flow;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_is_valid		 = SIG2.rsp_is_valid;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_early_valid	 = SIG2.rsp_early_valid;\
  force SIG2.rsp_block					 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_block;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_protocol_id	 = SIG2.rsp_protocol_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_vc_id		 = SIG2.rsp_vc_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_shared_credit	 = SIG2.rsp_shared_credit;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_header		 = SIG2.rsp_header;\
  force SIG2.rsp_rxcrd_valid				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_valid;\
  force SIG2.rsp_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_protocol_id;\
  force SIG2.rsp_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_vc_id;\
  force SIG2.rsp_rxcrd_shared				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_txblock_crd_flow	 = SIG2.rsp_txblock_crd_flow;

`define UFI_CONN_BFM_F2A_2_RTL_F2A(SIG1, SIG2)\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_txcon_req 		 = SIG2.txcon_req;\
  force SIG2.rxcon_ack 					 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxcon_ack;\
  force SIG2.rxdiscon_nack				 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rxdiscon_nack;\
  force SIG2.rx_empty					 = ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_rx_empty;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_fatal		 = SIG2.global_fatal;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_global_viral		 = SIG2.global_viral;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_level	 = SIG2.distress_level;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_resource  	 = SIG2.distress_resource;\
  force ``SIG1``_ufi_f2a_global_ula_d2d_ufi_f2a_global_F2A_distress_nid	 = SIG2.distress_nid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_is_valid		 = SIG2.req_is_valid;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_early_valid	 = SIG2.req_early_valid;\
  force SIG2.req_block					 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_block;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_protocol_id	 = SIG2.req_protocol_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_vc_id		 = SIG2.req_vc_id;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_shared_credit	 = SIG2.req_shared_credit;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_header		 = SIG2.req_header;\
  force SIG2.req_rxcrd_valid				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_valid;\
  force SIG2.req_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_protocol_id;\
  force SIG2.req_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_vc_id;\
  force SIG2.req_rxcrd_shared				 = ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_req_ula_d2d_layer0_ufi_f2a_req_F2A_req_txblock_crd_flow	 = SIG2.req_txblock_crd_flow;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_is_valid		 = SIG2.data_is_valid;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_early_valid	 = SIG2.data_early_valid;\
  force SIG2.data_block					 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_block;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_protocol_id	 = SIG2.data_protocol_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_vc_id		 = SIG2.data_vc_id;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_shared_credit	 = SIG2.data_shared_credit;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_header 		 = SIG2.data_header;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_eop		 = SIG2.data_eop;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_payload		 = SIG2.data_payload;\
  force SIG2.data_rxcrd_valid				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_valid;\
  force SIG2.data_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_protocol_id;\
  force SIG2.data_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_vc_id;\
  force SIG2.data_rxcrd_shared				 = ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_data_ula_d2d_layer0_ufi_f2a_data_F2A_data_txblock_crd_flow	 = SIG2.data_txblock_crd_flow;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_is_valid		 = SIG2.rsp_is_valid;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_early_valid	 = SIG2.rsp_early_valid;\
  force SIG2.rsp_block					 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_block;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_protocol_id	 = SIG2.rsp_protocol_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_vc_id		 = SIG2.rsp_vc_id;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_shared_credit	 = SIG2.rsp_shared_credit;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_header		 = SIG2.rsp_header;\
  force SIG2.rsp_rxcrd_valid				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_valid;\
  force SIG2.rsp_rxcrd_protocol_id			 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_protocol_id;\
  force SIG2.rsp_rxcrd_vc_id				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_vc_id;\
  force SIG2.rsp_rxcrd_shared				 = ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_rxcrd_shared;\
  force ``SIG1``_ufi_f2a_rsp_ula_d2d_layer0_ufi_f2a_rsp_F2A_rsp_txblock_crd_flow	 = SIG2.rsp_txblock_crd_flow;



`define UFI_CONN_RTL_A2F_2_BFM_A2F(SIG1, SIG2)\
  force SIG2.txcon_req                                   = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_txcon_req;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxcon_ack            = SIG2.rxcon_ack;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxdiscon_nack        = SIG2.rxdiscon_nack;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rx_empty             = SIG2.rx_empty;\
  force SIG2.coh_conn_req                                = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_coh_conn_req;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_coh_conn_ack         = SIG2.coh_conn_ack;\
  force SIG2.local_fatal                                 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_local_fatal;\
  force SIG2.local_viral                                 = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_local_viral;\
  force SIG2.distress_level                              = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_level;\
  force SIG2.distress_resource                           = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_resource;\
  force SIG2.distress_nid                                = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_nid;\
  force SIG2.req_is_valid                                = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_is_valid;\
  force SIG2.req_early_valid                             = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_early_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_block               = SIG2.req_block;\
  force SIG2.req_cancel_valid                            = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_cancel_valid;\
  force SIG2.req_cancel_status                           = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_cancel_status;\
  force SIG2.req_protocol_id                             = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_protocol_id;\
  force SIG2.req_vc_id                                   = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_vc_id;\
  force SIG2.req_shared_credit                           = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_shared_credit;\
  force SIG2.req_header                                  = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_header;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_valid         = SIG2.req_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_protocol_id   = SIG2.req_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_vc_id         = SIG2.req_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_shared        = SIG2.req_rxcrd_shared;\
  force SIG2.req_txblock_crd_flow                        = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_txblock_crd_flow;\
  force SIG2.data_is_valid                               = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_is_valid;\
  force SIG2.data_early_valid                            = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_early_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_block             = SIG2.data_block;\
  force SIG2.data_cancel_valid                           = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_cancel_valid;\
  force SIG2.data_cancel_status                          = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_cancel_status;\
  force SIG2.data_protocol_id                            = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_protocol_id;\
  force SIG2.data_vc_id                                  = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_vc_id;\
  force SIG2.data_shared_credit                          = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_shared_credit;\
  force SIG2.data_header                                 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_header;\
  force SIG2.data_eop                                    = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_eop;\
  force SIG2.data_payload                                = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_payload;\
  force SIG2.data_half_line_valid			 = 1'b1;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_valid       = SIG2.data_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_protocol_id = SIG2.data_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_vc_id       = SIG2.data_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_shared      = SIG2.data_rxcrd_shared;\
  force SIG2.data_txblock_crd_flow                       = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_txblock_crd_flow;\
  force SIG2.rsp_is_valid                                = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_is_valid;\
  force SIG2.rsp_early_valid                             = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_early_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_block               = SIG2.rsp_block;\
  force SIG2.rsp_cancel_valid                            = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_cancel_valid;\
  force SIG2.rsp_cancel_status                           = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_cancel_status;\
  force SIG2.rsp_protocol_id                             = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_protocol_id;\
  force SIG2.rsp_vc_id                                   = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_vc_id;\
  force SIG2.rsp_shared_credit                           = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_shared_credit;\
  force SIG2.rsp_header                                  = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_header;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_valid         = SIG2.rsp_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_protocol_id   = SIG2.rsp_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_vc_id         = SIG2.rsp_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_shared        = SIG2.rsp_rxcrd_shared;\
  force SIG2.rsp_txblock_crd_flow                        = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_txblock_crd_flow;

`define UFI_CONN_RTL_A2F_2_BFM_F2A(SIG1, SIG2)\
  force SIG2.txcon_req                                   = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_txcon_req;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxcon_ack            = SIG2.rxcon_ack;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rxdiscon_nack        = SIG2.rxdiscon_nack;\
  force ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_rx_empty             = SIG2.rx_empty;\
  force SIG2.distress_level                              = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_level;\
  force SIG2.distress_resource                           = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_resource;\
  force SIG2.distress_nid                                = ``SIG1``_ufi_a2f_global_ula_d2d_ufi_a2f_global_A2F_distress_nid;\
  force SIG2.req_is_valid                                = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_is_valid;\
  force SIG2.req_early_valid                             = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_early_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_block               = SIG2.req_block;\
  force SIG2.req_protocol_id                             = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_protocol_id;\
  force SIG2.req_vc_id                                   = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_vc_id;\
  force SIG2.req_shared_credit                           = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_shared_credit;\
  force SIG2.req_header                                  = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_header;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_valid         = SIG2.req_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_protocol_id   = SIG2.req_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_vc_id         = SIG2.req_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_rxcrd_shared        = SIG2.req_rxcrd_shared;\
  force SIG2.req_txblock_crd_flow                        = ``SIG1``_ufi_a2f_req_ula_d2d_layer0_ufi_a2f_req_A2F_req_txblock_crd_flow;\
  force SIG2.data_is_valid                               = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_is_valid;\
  force SIG2.data_early_valid                            = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_early_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_block             = SIG2.data_block;\
  force SIG2.data_protocol_id                            = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_protocol_id;\
  force SIG2.data_vc_id                                  = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_vc_id;\
  force SIG2.data_shared_credit                          = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_shared_credit;\
  force SIG2.data_header                                 = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_header;\
  force SIG2.data_eop                                    = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_eop;\
  force SIG2.data_payload                                = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_payload;\
  force SIG2.data_half_line_valid			 = 1'b1;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_valid       = SIG2.data_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_protocol_id = SIG2.data_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_vc_id       = SIG2.data_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_rxcrd_shared      = SIG2.data_rxcrd_shared;\
  force SIG2.data_txblock_crd_flow                       = ``SIG1``_ufi_a2f_data_ula_d2d_layer0_ufi_a2f_data_A2F_data_txblock_crd_flow;\
  force SIG2.rsp_is_valid                                = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_is_valid;\
  force SIG2.rsp_early_valid                             = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_early_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_block               = SIG2.rsp_block;\
  force SIG2.rsp_protocol_id                             = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_protocol_id;\
  force SIG2.rsp_vc_id                                   = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_vc_id;\
  force SIG2.rsp_shared_credit                           = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_shared_credit;\
  force SIG2.rsp_header                                  = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_header;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_valid         = SIG2.rsp_rxcrd_valid;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_protocol_id   = SIG2.rsp_rxcrd_protocol_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_vc_id         = SIG2.rsp_rxcrd_vc_id;\
  force ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_rxcrd_shared        = SIG2.rsp_rxcrd_shared;\
  force SIG2.rsp_txblock_crd_flow                        = ``SIG1``_ufi_a2f_rsp_ula_d2d_layer0_ufi_a2f_rsp_A2F_rsp_txblock_crd_flow;

`define RDI_CONN_RTL_2_BFM(PARTITION,SIG1, SIG2)\
  force SIG2.lp_irdy 						= ``PARTITION``.``SIG1``_RDI_Upper_lp_irdy;\
  force SIG2.lp_valid 						= ``PARTITION``.``SIG1``_RDI_Upper_lp_valid;\
  force SIG2.lp_data 						= ``PARTITION``.``SIG1``_RDI_Upper_lp_data;\
  force SIG2.lp_stallack 					= ``PARTITION``.``SIG1``_RDI_Upper_lp_stallack ;\
  force SIG2.lp_state_req 					= ``PARTITION``.``SIG1``_RDI_Upper_lp_state_req;\
  force SIG2.lp_linkerror 					= ``PARTITION``.``SIG1``_RDI_Upper_lp_linkerror;\
  force SIG2.lp_clk_ack						= ``PARTITION``.``SIG1``_RDI_Upper_lp_clk_ack ;\
  force SIG2.lp_wake_req					= ``PARTITION``.``SIG1``_RDI_Upper_lp_wake_req ;\
  force SIG2.lp_cfg						= ``PARTITION``.``SIG1``_RDI_Upper_lp_cfg ;\
  force SIG2.lp_cfg_vld						= ``PARTITION``.``SIG1``_RDI_Upper_lp_cfg_vld ;\
  force SIG2.lp_cfg_crd						= ``PARTITION``.``SIG1``_RDI_Upper_lp_cfg_crd ;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_trdy 		= SIG2.pl_trdy;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_valid 	= SIG2.pl_valid;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_data 		= SIG2.pl_data;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_state_sts  	= SIG2.pl_state_sts;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_inband_pres 	= SIG2.pl_inband_pres;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_error 	= SIG2.pl_error;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_cerror 	= SIG2.pl_cerror;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_nferror 	= SIG2.pl_nferror;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_trainerror 	= SIG2.pl_trainerror;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_phyinrecenter = SIG2.pl_phyinrecenter;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_stallreq  	= SIG2.pl_stallreq;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_speedmode 	= SIG2.pl_speedmode;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_lnk_cfg 	= SIG2.pl_lnk_cfg;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_clk_req   	= SIG2.pl_clk_req;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_wake_ack 	= SIG2.pl_wake_ack;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_cfg 		= SIG2.pl_cfg;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_cfg_vld 	= SIG2.pl_cfg_vld;\
  force ``PARTITION``.``SIG1``_RDI_Upper_pl_cfg_crd 	= SIG2.pl_cfg_crd;\

`define SIG_PAD(LEFT,PAD,RIGHT)\
    ``LEFT````PAD````RIGHT``\

`define SIG_A_PAD(LHS,EQ,LEFT,PAD,RIGHT)\
    ``LHS````EQ````LEFT````PAD````RIGHT``\

`define HIERARCHY(PATH)\
     ``PATH``\

module d2d0_bind_mod
  import uvm_pkg::*;
  import d2d_env_pkg::*;
  #(
    parameter ENV_INST      = 0,
    parameter string INST_SUFFIX  = "0",
    parameter uvm_pkg::uvm_active_passive_enum d2d_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter uvm_pkg::uvm_active_passive_enum d2d_mb_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter D2D_PHYLESS = 0,
    parameter D2D_MB_CONNECT_TYPE = d2d_pkg::NONE,
    parameter D2D_SPAD = 4, 
    parameter RDI_PORT_ID = 0
  )
  (
       `include "d2d0_bind_ports_include.sv"
  );
// EDIT_PORT END
    aucie_rdi_intf #() rdi_if1();
    aucie_rdi_intf #() rdi_if2();
    aucie_rdi_intf #() rdi_if3();
    aucie_rdi_intf #() rdi_if4();


//cbb hotfix  `include "por_forces_macro.sv"
//cbb hotfix  //Setting up force methodology
//cbb hotfix  `FORCE_SETUP
`include "d2d0_iosfsb_connect.sv"
`include "d2d_sb2ucie_connect.sv"
if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_B2B) begin
`include "d2d_mb_ufi_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::RTL_BFM) begin
`include "d2d_mb_ufi_connect_bfm.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_BYP) begin
`include "d2d_mb_ufi_byp_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UCIE_R2B) begin
`include "d2d_mb_ucie_connect.sv"
end
`ifndef D2D_PHYLESS
//cbb hotfix `include "d2d_intel_ucie_bfm_connect.sv"
`endif
`include "d2d_apb_connect.sv"
`include "d2d_reset_signal_if_connect.sv"
//uv3 integ `include "d2d_TFB_Bfm_if_connect.sv"
//uv3 integ `include "d2d_wb_if_connect.sv"
`include "d2d_bind_initial_cfg.sv"
endmodule: d2d0_bind_mod

module d2d1_bind_mod
  import uvm_pkg::*;
  import d2d_env_pkg::*;
  #(
    parameter ENV_INST      = 0,
    parameter string INST_SUFFIX  = "0",
    parameter uvm_pkg::uvm_active_passive_enum d2d_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter uvm_pkg::uvm_active_passive_enum d2d_mb_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter D2D_PHYLESS = 0,
    parameter D2D_MB_CONNECT_TYPE = d2d_pkg::NONE,
    parameter D2D_SPAD = 0, 
    parameter RDI_PORT_ID = 0
  )
  (
       `include "d2d1_bind_ports_include.sv"
  );
// EDIT_PORT END
    aucie_rdi_intf #() rdi_if1();
    aucie_rdi_intf #() rdi_if2();
    aucie_rdi_intf #() rdi_if3();
    aucie_rdi_intf #() rdi_if4();


//cbb hotfix  `include "por_forces_macro.sv"
//cbb hotfix  //Setting up force methodology
//cbb hotfix  `FORCE_SETUP
`include "d2d1_iosfsb_connect.sv"
`include "d2d1_sb2ucie_connect.sv"
if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_B2B) begin
`include "d2d1_mb_ufi_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::RTL_BFM) begin
`include "d2d1_mb_ufi_connect_bfm.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_BYP) begin
`include "d2d_mb_ufi_byp_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UCIE_R2B) begin
`include "d2d1_mb_ucie_connect.sv"
end
`ifndef D2D_PHYLESS
//`include "d2d1_intel_ucie_bfm_connect.sv"
`endif
`include "d2d_apb_connect.sv"
`include "d2d_reset_signal_if_connect.sv"
//uv3 integ `include "d2d1_TFB_Bfm_if_connect.sv"
//uv3 integ `include "d2d_wb_if_connect.sv"
`include "d2d_bind_initial_cfg.sv"
endmodule: d2d1_bind_mod

module d2d2_bind_mod
  import uvm_pkg::*;
  import d2d_env_pkg::*;
  #(
    parameter ENV_INST      = 0,
    parameter string INST_SUFFIX  = "0",
    parameter uvm_pkg::uvm_active_passive_enum d2d_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter uvm_pkg::uvm_active_passive_enum d2d_mb_active_passive = uvm_pkg::UVM_PASSIVE,
    parameter D2D_PHYLESS = 0,
    parameter D2D_MB_CONNECT_TYPE = d2d_pkg::NONE,
    parameter D2D_SPAD = 2, 
    parameter RDI_PORT_ID = 0
  )
  (
       `include "d2d2_bind_ports_include.sv"
  );
// EDIT_PORT END
    aucie_rdi_intf #() rdi_if1();
    aucie_rdi_intf #() rdi_if2();
    aucie_rdi_intf #() rdi_if3();
    aucie_rdi_intf #() rdi_if4();


//cbb hotfix  `include "por_forces_macro.sv"
//cbb hotfix  //Setting up force methodology
//cbb hotfix  `FORCE_SETUP
`include "d2d2_iosfsb_connect.sv"
`include "d2d2_sb2ucie_connect.sv"
if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_B2B) begin
`include "d2d2_mb_ufi_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::RTL_BFM) begin
`include "d2d2_mb_ufi_connect_bfm.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UFI_BYP) begin
`include "d2d_mb_ufi_byp_connect.sv"
end
else if (D2D_MB_CONNECT_TYPE == d2d_pkg::UCIE_R2B) begin
`include "d2d2_mb_ucie_connect.sv"
end
`ifndef D2D_PHYLESS
//`include "d2d2_intel_ucie_bfm_connect.sv"
`endif
`include "d2d_apb_connect.sv"
`include "d2d_reset_signal_if_connect.sv"
//uv3 integ `include "d2d2_TFB_Bfm_if_connect.sv"
//uv3 integ `include "d2d_wb_if_connect.sv"
`include "d2d_bind_initial_cfg.sv"
endmodule: d2d2_bind_mod
