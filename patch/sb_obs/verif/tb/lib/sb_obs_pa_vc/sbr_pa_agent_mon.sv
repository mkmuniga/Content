///=====================================================================================================================
/// Module Name:        sbr_pa_agent_mon.sv
///
/// Primary Contact:    dgluzer
/// Secondary Contact:
/// Creation Date:      21/10/2021
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
//  PA monitor
///
///=====================================================================================================================

`define sample_ifc(IFC_SIG,mux_sel)\
   (mux_sel == 0) ?  pa_if.monitor_cb_clk0.IFC_SIG : pa_if.monitor_cb_clk1.IFC_SIG;\

typedef enum int {
    SEL0=0,
    SEL1=1,
    SEL2=2,
    SEL3=3
      } dfd_sbr_sa_mux;

class sbr_pa_monitor extends uvm_monitor implements val_svtb_common_uvm_pkg::rcu_interface;
    sbr_pa_pkt_item_XXX pa_np_pkt;
    sbr_pa_pkt_item_XXX pa_pc_pkt;
    sbr_pa_pkt_item_XXX first_pkt_pa_pc_pkt;
    sbr_pa_pkt_item_XXX first_pkt_pa_np_pkt;
    sbr_pa_pkt_item_XXX second_pkt_pa_pc_pkt;
    sbr_pa_pkt_item_XXX second_pkt_pa_np_pkt;
    uvm_analysis_port  #(sbr_pa_pkt_item_XXX)  pa_ch0_injected_items_port;
    uvm_analysis_port  #(sbr_pa_pkt_item_XXX)  pa_ch1_injected_items_port;
    uvm_analysis_port  #(bit)  pa_bus_sel_change;

    int  ch_width [];
    bit [1:0] bus_select;
    bit [7:0] source16 = 0;
    bit [7:0] dest16 = 0;
    bit [7:0] np_source16, pc_source16, np_dest16, pc_dest16;
    bit np_ep_gbl_done, pc_ep_gbl_done, ep_gbl_done;
    bit [31:0] ep_glb_first_pkt, pc_ep_glb_first_pkt, np_ep_glb_first_pkt, pa_payload;
    int ep_current_size, pc_ep_current_size, np_ep_current_size;
    bit pc_put,np_put,eom;
    bit [63:0] src_dest_payload;
    virtual pa_vc_if pa_if;
    int ch_width_0,ch_width_1,ch_width_2,ch_width_3;
    int num_of_clk;
    string sbr_type;
    bit sb_obs_vc_internal_cov_en = 0;
    bit sb_obs_std_alone_vc_internal_cov_en = 0;
    int sb_clk0_freq, sb_clk1_freq, sb_clks_skew;
    bit [1:0] length_of_completion_data;
    logic [7:0] ch0_opcode_pc, ch0_opcode_np, ch2_opcode_pc, ch2_opcode_np;
    bit eh, ch0_eh_pc, ch0_eh_np, ch2_eh_pc, ch2_eh_np, ch0_length_of_address_pc, ch0_length_of_address_np, ch2_length_of_address_pc, ch2_length_of_address_np, length_of_address, length_of_data;
    int num_of_chunks_pc = 0;
    int num_of_chunks_np = 0;
    dfd_sbr_sa_mux sbr_pa_mux_cov;
    bit PA_chk_en=0;
    bit [3:0] ch_toggle;
    string                 SB_OBS_RCU_NAME = "";
    string                 cfg_path="main";
    string cfgdb_filename;
    int pc_num_of_transactions, np_num_of_transactions;
    bit address_filter_en, pc_eh, pc_addr_len, np_eh, np_addr_len, pc_not_valid, np_not_valid, pc_wait_send, np_wait_send, pc_data_64, np_data_64, pc_sop, np_sop;
    bit [7:0] np_opcode, pc_opcode;
    bit [15:0] pc_filter_results_0_15, np_filter_results_0_15, filter_results_0_15;
    bit [31:0] pc_filter_results_16_47, np_filter_results_16_47, filter_results_16_47;
    bit pc_filter_pass_0_15=1;
    bit np_filter_pass_0_15=1;
    bit filter_pass_0_15=1;
    bit filter_pass_16_47=1;
    bit pc_filter_pass_16_47=1;
    bit np_filter_pass_16_47=1;
    bit [3:0] ep_global, sb_swap;

    `uvm_component_utils_begin(sbr_pa_monitor)
        `uvm_field_int(sb_obs_vc_internal_cov_en, UVM_ALL_ON)
        `uvm_field_int(sb_obs_std_alone_vc_internal_cov_en, UVM_ALL_ON)
        `uvm_field_string(SB_OBS_RCU_NAME, UVM_ALL_ON)
        `uvm_field_string(cfg_path, UVM_ALL_ON)
    `uvm_component_utils_end
 
    covergroup sbr_mux_sel_cg;
        sbr_mux_cp : coverpoint sbr_pa_mux_cov;
        option.per_instance = 1;

    endgroup

    covergroup clk_1_freq_cg;
    FRQ_400MHZ : coverpoint sb_clk1_freq {
     bins freq = {[2300:2550]};
      }
    FRQ_100MHZ : coverpoint sb_clk1_freq {
     bins freq = {[3000:20000]};
      }
      option.per_instance = 1;
    endgroup 

    covergroup clks_skew_cg;
    NO_SKEW : coverpoint sb_clks_skew {
     bins skew = {[2000:150000]};
      }
    IS_SKEW : coverpoint sb_clks_skew {
     bins skew = {[1:200]};
      }
      option.per_instance = 1;
    endgroup

    `SB_OBS_BITWISE_N_COVGROUPS_32(data_input_toggle_ch0_cg,pa_if.ch_payload,0,TOGGLE);
    `SB_OBS_BITWISE_N_COVGROUPS_32(data_input_toggle_ch1_cg,pa_if.ch_payload,1,TOGGLE);
    `SB_OBS_BITWISE_N_COVGROUPS_32(data_input_toggle_ch2_cg,pa_if.ch_payload,2,TOGGLE);
    `SB_OBS_BITWISE_N_COVGROUPS_32(data_input_toggle_ch3_cg,pa_if.ch_payload,3,TOGGLE);
    covergroup cross_ch_toggle_cg;
    ch0_toggle : coverpoint ch_toggle {
     bins only_ch0_toggle = {4'b0001};
     bins only_ch1_toggle = {4'b0010};
     bins ch0_ch1_toggle = {4'b0011};
     bins only_ch2_toggle = {4'b0100};
     bins ch0_ch2_toggle = {4'b0101};
     bins ch1_ch2_toggle = {4'b0110};
     bins ch0_ch1_ch2_toggle = {4'b0111};
     bins only_ch3_toggle = {4'b1000};
     bins ch0_ch3_toggle = {4'b1001};
     bins ch1_ch3_toggle = {4'b1010};
     bins ch0_ch1_ch3_toggle = {4'b1011};
     bins ch2_ch3_toggle = {4'b1100};
     bins ch0_ch2_ch3_toggle = {4'b1101};
     bins ch1_ch2_ch3_toggle = {4'b1110};
     bins ch0_ch1_ch2_ch3_toggle = {4'b1111};
      }
      option.per_instance = 1;
    endgroup
        
    covergroup ifc_toggle_cg;
        sbr_ifc_toggle_eom_cp : coverpoint pa_if.eom{
            bins eom_ch0  = {4'h1};
            bins eom_ch1  = {4'h2};
            bins eom_ch2  = {4'h4};
            bins eom_ch3  = {4'h8};
        }
        sbr_ifc_toggle_pc_put_cp : coverpoint pa_if.pc_put{
            bins pc_put_ch0  = {4'h1};
            bins pc_put_ch1  = {4'h2};
            bins pc_put_ch2  = {4'h4};
            bins pc_put_ch3  = {4'h8};
        }
        sbr_ifc_toggle_np_put_cp : coverpoint pa_if.np_put{
            bins np_put_ch0  = {4'h1};
            bins np_put_ch1  = {4'h2};
            bins np_put_ch2  = {4'h4};
            bins np_put_ch3  = {4'h8};
        }
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch1  = {4'h2};
            bins ep_global_ch2  = {4'h4};
            bins ep_global_ch3  = {4'h8};
        }
        option.per_instance = 1;
    endgroup

     covergroup sbr_payload_width_cg;
        payload_width_cg_ch0 : coverpoint ch_width[0]{
            bins cho_width_32  = {'h20};
            bins cho_width_16  = {'h10};
            bins cho_width_8   = {'h8};
        }
        payload_width_cg_ch1 : coverpoint ch_width[1]{
            bins cho_width_32  = {'h20};
            bins cho_width_16  = {'h10};
            bins cho_width_8   = {'h8};
        }
        payload_width_cg_ch2 : coverpoint ch_width[2]{
            bins cho_width_32  = {'h20};
            bins cho_width_16  = {'h10};
            bins cho_width_8   = {'h8};
        }
        payload_width_cg_ch3 : coverpoint ch_width[3]{
            bins cho_width_32  = {'h20};
            bins cho_width_16  = {'h10};
            bins cho_width_8   = {'h8};
        }
        option.per_instance = 1;
    endgroup

    covergroup simple_traffic_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        simple_traffic_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins simple_traffic_wo_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins simple_traffic_wo_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins simple_traffic_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins simple_traffic_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup read_register_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        address_length : coverpoint length_of_address{
            bins address_16bit = {0};
            bins address_48bit = {1};
        }
        read_register_format: cross sbr_ifc_toggle_ep_global_cp, extended_header, address_length{
            bins read_register_wo_eh_addr_16b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins read_register_wo_eh_addr_16b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins read_register_wo_eh_addr_48b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins read_register_wo_eh_addr_48b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins read_register_eh_addr_16b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins read_register_eh_addr_16b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins read_register_eh_addr_48b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins read_register_eh_addr_48b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);

            }
        option.per_instance = 1;
    endgroup
    covergroup write_register_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        address_length : coverpoint length_of_address{
            bins address_16bit = {0};
            bins address_48bit = {1};
        }
        data_length : coverpoint length_of_data{
            bins data_32bit = {0};
            bins data_64bit = {1};
        }
        write_register_format: cross sbr_ifc_toggle_ep_global_cp, extended_header, address_length, data_length{
            bins write_register_wo_eh_addr_16b_data_32b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_wo_eh_addr_16b_data_32b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins write_register_wo_eh_addr_48b_data_32b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_wo_eh_addr_48b_data_32b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins write_register_eh_addr_16b_data_32b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins write_register_eh_addr_16b_data_32b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins write_register_eh_addr_48b_data_32b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_eh_addr_48b_data_32b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_32bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins write_register_wo_eh_addr_16b_data_64b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_wo_eh_addr_16b_data_64b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins write_register_wo_eh_addr_48b_data_64b_no_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_wo_eh_addr_48b_data_64b_ep = binsof(extended_header.without_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins write_register_eh_addr_16b_data_64b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_eh_addr_16b_data_64b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_16bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins write_register_eh_addr_48b_data_64b_no_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins write_register_eh_addr_48b_data_64b_ep = binsof(extended_header.with_extended_header) && binsof(address_length.address_48bit) && binsof(data_length.data_64bit) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup completion_wo_data_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        completion_wo_data_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
        bins completion_wo_data_wo_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_wo_data_wo_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins completion_wo_data_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_wo_data_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup completion_with_data_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        data_length : coverpoint length_of_completion_data{
            bins data_32bit = {2'h0};
            bins data_64bit = {2'h1};
            bins data_96bit = {2'h2};
            bins data_128bit = {2'h3};
        }
        completion_with_data_format: cross sbr_ifc_toggle_ep_global_cp, extended_header, data_length{
            bins completion_with_data_32b_data_no_eh_no_ep = binsof(data_length.data_32bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_32b_data_no_eh_ep = binsof(data_length.data_32bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins completion_with_data_64b_data_no_eh_no_ep = binsof(data_length.data_64bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_64b_data_no_eh_ep = binsof(data_length.data_64bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins completion_with_data_96b_data_no_eh_no_ep = binsof(data_length.data_96bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_96b_data_no_eh_ep = binsof(data_length.data_96bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins completion_with_data_128b_data_no_eh_no_ep = binsof(data_length.data_128bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_128b_data_no_eh_ep = binsof(data_length.data_128bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins completion_with_data_32b_data_eh_no_ep = binsof(data_length.data_32bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_32b_data_eh_ep = binsof(data_length.data_32bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins completion_with_data_64b_data_eh_no_ep = binsof(data_length.data_64bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_64b_data_eh_ep = binsof(data_length.data_64bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins completion_with_data_96b_data_eh_no_ep = binsof(data_length.data_96bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_96b_data_eh_ep = binsof(data_length.data_96bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins completion_with_data_128b_data_eh_no_ep = binsof(data_length.data_128bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins completion_with_data_128b_data_eh_ep = binsof(data_length.data_128bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
        }
        option.per_instance = 1;
    endgroup
    covergroup message_with_data_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        data_length : coverpoint length_of_data{
            bins data_32bit = {0};
            bins data_64bit = {1};
        }
        message_with_data_format: cross sbr_ifc_toggle_ep_global_cp, extended_header, data_length{
            bins message_with_data_32b_data_no_eh_no_ep = binsof(data_length.data_32bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins message_with_data_32b_data_no_eh_ep = binsof(data_length.data_32bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins message_with_data_64b_data_no_eh_no_ep = binsof(data_length.data_64bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins message_with_data_64b_data_no_eh_ep = binsof(data_length.data_64bit) && binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins message_with_data_32b_data_eh_no_ep = binsof(data_length.data_32bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins message_with_data_32b_data_eh_ep = binsof(data_length.data_32bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            bins message_with_data_64b_data_eh_no_ep = binsof(data_length.data_64bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins message_with_data_64b_data_eh_ep = binsof(data_length.data_64bit) && binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup bootPrep_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        bootPrep_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins bootprep_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins bootprep_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins bootprep_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins bootpre_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup bootPrepAck_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        bootPrepAck_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins bootprepAck_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins bootprepAck_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins bootprepAck_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins bootprepAck_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup resetPrep_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        resetPrep_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins resetPrep_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetPrep_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins resetPrep_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetPrep_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup resetPrepAck_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        resetPrepAck_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins resetPrepAck_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetPrepAck_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins resetPrepAck_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetPrepAck_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup resetReq_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        resetReq_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins resetReq_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetReq_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins resetReq_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins resetReq_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup forcePWRGatePok_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        forcePWRGatePok_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins forcePWRGatePok_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins forcePWRGatePok_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins forcePWRGatePok_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins forcePWRGatePok_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup
    covergroup virtualWire_cp;
        sbr_ifc_toggle_ep_global_cp : coverpoint ep_global{
            bins no_ep_global   = {4'h0};
            bins ep_global_ch0  = {4'h1};
            bins ep_global_ch2  = {4'h4};
        }
        extended_header : coverpoint eh{
            bins without_extended_header = {0};
            bins with_extended_header = {1};
        }
        virtualWire_format: cross sbr_ifc_toggle_ep_global_cp, extended_header{
            bins virtualWire_no_eh_no_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins virtualWire_no_eh_ep = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            bins virtualWire_eh_no_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.no_ep_global);
            bins virtualWire_eh_ep = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            ignore_bins ignore_eh_ep_global_ch2 = binsof(extended_header.with_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch2);
            ignore_bins ignore_no_eh_ep_global_ch0 = binsof(extended_header.without_extended_header) && binsof(sbr_ifc_toggle_ep_global_cp.ep_global_ch0);
            }
        option.per_instance = 1;
    endgroup

    // ----------------------------------------------------------
    task pa_mon_main();
        pa_pc_pkt = new();
        pa_np_pkt = new();
        pa_np_pkt.sop=1;
        pa_pc_pkt.sop=1;
        pa_pc_pkt.data_size=1; //32
        pa_np_pkt.data_size=1; //32
     
        `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON: start PA mon task")); //was HIGH
        forever begin
            
            wait (pa_if.obs_en==1);

            if ((pa_if.addr_filter_mask_0_15 != 16'h0) || (pa_if.addr_filter_mask_16_47 != 32'h0))
                address_filter_en = 1;

            //if bus select was changed we need to start new pkt
            if (bus_select!=pa_if.bus_select) begin
                `slu_msg(UVM_HIGH, "SOC_DBG", ("SBR_PA_MON :found bus select change")) //was HIGH
                pa_pc_pkt = new ();
                pa_np_pkt = new ();
                pa_np_pkt.sop=1;
                pa_pc_pkt.sop=1;
                pa_pc_pkt.data_size=1; //32
                pa_np_pkt.data_size=1; //32
                pa_bus_sel_change.write(1'b1);
            end
            bus_select=pa_if.bus_select;
           
            //wait (pa_if.power==1);
            //wait (pa_if.gs_power==1);             
            if (num_of_clk == 2) begin
                if (bus_select==0) begin
                    @(posedge pa_if.pa_clock_0);
                end else begin
                    @(posedge pa_if.pa_clock_1);
                end
            end else begin
                @(posedge pa_if.pa_clock_0);
            end

            if (sb_obs_vc_internal_cov_en) begin
                sbr_pa_mux_cov = dfd_sbr_sa_mux'(bus_select);
                sbr_mux_sel_cg.sample();
                ifc_toggle_cg.sample();
            end
            if (sb_obs_std_alone_vc_internal_cov_en) begin
                sbr_payload_width_cg.sample();
                `slu_msg(UVM_HIGH, "SOC_DBG", ("SBR_PA_MON : coverage payload_width[0] = %h payload_width[1] = %h payload_width[2] = %h payload_width[3] = %h", ch_width[0], ch_width[1],ch_width[2],ch_width[3]))
            end
                
            if (num_of_clk == 2) begin
                pc_put = `sample_ifc(pc_put[bus_select],bus_select);
                np_put = `sample_ifc(np_put[bus_select],bus_select);
                pa_payload = `sample_ifc(ch_payload[bus_select],bus_select);
                eom = `sample_ifc(eom[bus_select],bus_select);
            end else begin 
                pc_put     = pa_if.monitor_cb_clk0.pc_put[bus_select];
                np_put     = pa_if.monitor_cb_clk0.np_put[bus_select];
                pa_payload = pa_if.monitor_cb_clk0.ch_payload[bus_select];
                eom        = pa_if.monitor_cb_clk0.eom[bus_select];
            end

                if (pc_put) begin
                    if ((ep_global[bus_select] == 1) && (pc_ep_current_size != 32))
                        get_ep_fisrt_pkt();
                    else begin
                        pa_pc_pkt=get_payload(pa_pc_pkt,bus_select);
                        if ((pa_pc_pkt.current_size==32) || (pa_pc_pkt.current_size==64))
                            begin
                            if (PA_chk_en)
                                `slu_msg(UVM_LOW, "SOC_DBG", ("PA PC found pkt with bus_select %3b bus_sel %2b payload %8h ",bus_select,pa_if.bus_select,pa_pc_pkt.payload)); //was HIGH
                            if (pa_pc_pkt.sop==1)
                                begin
                                if(sb_swap[bus_select])
                                    src_dest_payload = {pa_pc_pkt.payload[31:16],pa_pc_pkt.payload[15:8],pc_source16,pa_pc_pkt.payload[7:0],pc_dest16,16'b0};
                                else
                                    src_dest_payload = {pa_pc_pkt.payload[31:16],pc_source16,pa_pc_pkt.payload[15:8],pc_dest16,pa_pc_pkt.payload[7:0],16'b0};
                                pc_opcode = pa_pc_pkt.payload[23:16];
                                pc_addr_len = pa_pc_pkt.payload[30];
                                pc_eh = pa_pc_pkt.payload[31];
                                pa_pc_pkt.payload = src_dest_payload;
                                pa_pc_pkt.data_size=0;
                                if((address_filter_en)&&((pc_opcode==8'h1)||(pc_opcode==8'h3)||(pc_opcode==8'h5)||(pc_opcode==8'h7)||(pc_opcode==8'h0)||(pc_opcode==8'h2)||(pc_opcode==8'h4)||(pc_opcode==8'h6)))
                                    first_pkt_pa_pc_pkt = new pa_pc_pkt;
                                else if (!address_filter_en)
                                    pa_ch0_injected_items_port.write(pa_pc_pkt);
                                if(pa_pc_pkt.eop==1) begin
                                    pc_sop=1;
                                    pc_ep_current_size = 0;
                                    pc_ep_gbl_done = 0;
                                    pc_ep_glb_first_pkt = 0;
                                    pc_eh = 0;
                                    pc_addr_len = 0;
                                    pc_opcode = 0;
                                    pc_num_of_transactions=0;
                                end
                                pa_pc_pkt=new();
                                pa_pc_pkt.data_size=1; //32
                                if(pc_sop==1)
                                    pa_pc_pkt.sop=1;
                                pc_sop=0;
                                pc_num_of_transactions = pc_num_of_transactions + 1;
                                `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :pc_num_of_transactions=%d opcode=%h eh=%b addr_len=%b pc_not_valid=%b payload=%h pc_wait_send=%h",pc_num_of_transactions,pc_opcode,pc_eh,pc_addr_len,pc_not_valid,pa_pc_pkt.payload,pc_wait_send));
                            end
                            if ((pa_pc_pkt.sop==0) && (pa_pc_pkt.eop==0))
                                begin                         
                                if (pa_pc_pkt.current_size==64)
                                    begin
                                    pc_num_of_transactions = pc_num_of_transactions + 1;
                                    pa_pc_pkt.data_size=0; //64
                                    if(address_filter_en) begin
                                        `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :pc_num_of_transactions=%d opcode=%h eh=%b addr_len=%b pc_not_valid=%b payload=%h pc_wait_send=%h",pc_num_of_transactions,pc_opcode,pc_eh,pc_addr_len,pc_not_valid,pa_pc_pkt.payload,pc_wait_send));
                                        if ((pc_opcode==8'h1)||(pc_opcode==8'h3)||(pc_opcode==8'h5)||(pc_opcode==8'h7)) begin //opc of write reg
                                            case ({pc_eh,pc_addr_len})
                                                2'b00: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[31:16]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            if((pc_filter_pass_0_15)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b01: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[31:16]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            check_pattern_16_47(pa_pc_pkt.payload[63:32]);
                                                            pc_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) || ((pc_filter_pass_0_15)&&(!pc_filter_pass_16_47)))) begin
                                                                pc_filter_pass_0_15 = 1;
                                                                pc_filter_pass_16_47 = 1;
                                                            end
                                                            if((pc_filter_pass_0_15)&&(pc_filter_pass_16_47)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b10: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[63:48]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            if((pc_filter_pass_0_15)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b11: begin
                                                            if(pc_num_of_transactions==2) begin
                                                                check_pattern_0_15(pa_pc_pkt.payload[63:48]);
                                                                pc_filter_pass_0_15=filter_pass_0_15;
                                                            end 
                                                            if(pc_num_of_transactions==3) begin
                                                                check_pattern_16_47(pa_pc_pkt.payload[31:0]);
                                                                pc_filter_pass_16_47=filter_pass_16_47;
                                                                if ((pa_if.addr_filter_inv) && (((!pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) || ((pc_filter_pass_0_15)&&(!pc_filter_pass_16_47)))) begin
                                                                    pc_filter_pass_0_15 = 1;
                                                                    pc_filter_pass_16_47 = 1;
                                                                end
                                                            end
                                                            if(pc_num_of_transactions==2) begin
                                                                second_pkt_pa_pc_pkt = new pa_pc_pkt;
                                                                pc_wait_send = 1;
                                                                if(pa_pc_pkt.payload[7:4]==1)
                                                                    pc_data_64=1;
                                                            end else if ((pc_filter_pass_0_15)&&(pc_filter_pass_16_47)&&(pc_num_of_transactions==3)&&(pc_data_64==1)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                pa_ch0_injected_items_port.write(second_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                            endcase
                                        end else if ((pc_opcode==8'h0)||(pc_opcode==8'h2)||(pc_opcode==8'h4)||(pc_opcode==8'h6)) begin //opc of read reg
                                            if((pc_eh==1)&&(pc_addr_len==1)&&(pc_num_of_transactions==2)) begin
                                                check_pattern_0_15(pa_pc_pkt.payload[63:48]);
                                                pc_filter_pass_0_15=filter_pass_0_15;
                                                second_pkt_pa_pc_pkt = new pa_pc_pkt;
                                                pc_wait_send = 1;
                                            end
                                        end else begin
                                            pc_not_valid =1;
                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                        end
                                        filter_pass_0_15=1;
                                        filter_pass_16_47=1;
                                    end //if (address_filter_en)
                                    if((pc_not_valid !=1)&&(pc_wait_send!=1))
                                        pa_ch0_injected_items_port.write(pa_pc_pkt);
                                    pa_pc_pkt=new();
                                    pa_pc_pkt.data_size=1; //32
                                end //if (pa_pc_pkt.current_size==64)        
                            end //if ((pa_pc_pkt.sop==0) && (pa_pc_pkt.eop==0))
                            if (pa_pc_pkt.eop==1)
                                begin
                                pc_num_of_transactions = pc_num_of_transactions + 1;
                                if (pa_pc_pkt.current_size==64)
                                    pa_pc_pkt.data_size=0; //64   
                                if(address_filter_en) begin
                                         `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :pc_num_of_transactions=%d opcode=%h eh=%b addr_len=%b pc_not_valid=%b payload=%h pc_wait_send=%h",pc_num_of_transactions,pc_opcode,pc_eh,pc_addr_len,pc_not_valid,pa_pc_pkt.payload,pc_wait_send));
                                        if ((pc_opcode==8'h0)||(pc_opcode==8'h2)||(pc_opcode==8'h4)||(pc_opcode==8'h6)) begin //opc of read reg
                                            case ({pc_eh,pc_addr_len})
                                                2'b00: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[31:16]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            if((pc_filter_pass_0_15)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b01: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[31:16]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            check_pattern_16_47(pa_pc_pkt.payload[63:32]);
                                                            pc_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) || ((pc_filter_pass_0_15)&&(!pc_filter_pass_16_47)))) begin
                                                                pc_filter_pass_0_15 = 1;
                                                                pc_filter_pass_16_47 = 1;
                                                            end
                                                            if((pc_filter_pass_0_15)&&(pc_filter_pass_16_47)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b10: begin
                                                            check_pattern_0_15(pa_pc_pkt.payload[63:48]);
                                                            pc_filter_pass_0_15=filter_pass_0_15;
                                                            if((pc_filter_pass_0_15)&&(pc_num_of_transactions==2)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b11: begin
                                                            check_pattern_16_47(pa_pc_pkt.payload[31:0]);
                                                            pc_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) || ((pc_filter_pass_0_15)&&(!pc_filter_pass_16_47)))) begin
                                                                pc_filter_pass_0_15 = 1;
                                                                pc_filter_pass_16_47 = 1;
                                                            end
                                                            if ((pc_filter_pass_0_15)&&(pc_filter_pass_16_47)&&(pc_num_of_transactions==3)) begin
                                                                pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                                pa_ch0_injected_items_port.write(second_pkt_pa_pc_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                                            end else begin
                                                                pc_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                            endcase
                                       end else if ((pc_opcode==8'h1)||(pc_opcode==8'h3)||(pc_opcode==8'h5)||(pc_opcode==8'h7)) begin //opc of write reg
                                           if((pc_eh==0)&&(pc_addr_len==0)&&(pc_num_of_transactions==2)) begin
                                                check_pattern_0_15(pa_pc_pkt.payload[31:16]);
                                                pc_filter_pass_0_15=filter_pass_0_15;
                                                if((pc_filter_pass_0_15)) begin
                                                    pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                    `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                end else begin
                                                    pc_not_valid =1;
                                                    `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                end
                                           end else if((pc_eh==1)&&(pc_addr_len==1)&&(pc_num_of_transactions==3)&&(pc_data_64==0)) begin
                                                check_pattern_16_47(pa_pc_pkt.payload[31:0]);
                                                pc_filter_pass_16_47=filter_pass_16_47;
                                                if ((pa_if.addr_filter_inv) && (((!pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) || ((pc_filter_pass_0_15)&&(!pc_filter_pass_16_47)))) begin
                                                    pc_filter_pass_0_15 = 1;
                                                    pc_filter_pass_16_47 = 1;
                                                end
                                                if((pc_filter_pass_0_15)&&(pc_filter_pass_16_47)) begin
                                                    pa_ch0_injected_items_port.write(first_pkt_pa_pc_pkt);
                                                    pa_ch0_injected_items_port.write(second_pkt_pa_pc_pkt);
                                                    `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                                end else begin
                                                    pc_not_valid =1;
                                                    `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                end
                                           end
                                        end else begin //opc of write reg
                                            pc_not_valid =1;
                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                        end
                                end //if (address_filter_en)
                                if(pc_not_valid !=1)
                                    pa_ch0_injected_items_port.write(pa_pc_pkt);
                                pa_pc_pkt.data_size=1; //32
                                pc_filter_pass_0_15=1;
                                pc_filter_pass_16_47=1;
                                pa_pc_pkt=new();
                                pa_pc_pkt.sop=1;
                                pc_ep_current_size = 0;
                                pc_ep_gbl_done = 0;
                                pc_ep_glb_first_pkt = 0;
                                pc_eh = 0;
                                pc_addr_len = 0;
                                pc_opcode = 0;
                                pc_not_valid = 0;
                                pc_wait_send = 0;
                                pc_data_64 = 0;
                                pc_num_of_transactions=0;
                                filter_pass_0_15=1;
                                filter_pass_16_47=1;
                            end //if (pa_pc_pkt.eop==1)
                        end else if (pa_pc_pkt.eop==1) begin //if ((pa_pc_pkt.current_size==32) || (pa_pc_pkt.current_size==64))
                            if(pc_not_valid !=1)
                                pa_ch0_injected_items_port.write(pa_pc_pkt);
                            pa_pc_pkt.data_size=1; //32
                            pc_filter_pass_0_15=1;
                            pc_filter_pass_16_47=1;
                            pa_pc_pkt=new();
                            pa_pc_pkt.sop=1;
                            pc_ep_current_size = 0;
                            pc_ep_gbl_done = 0;
                            pc_ep_glb_first_pkt = 0;
                            pc_eh = 0;
                            pc_addr_len = 0;
                            pc_opcode = 0;
                            pc_not_valid = 0;
                            pc_wait_send = 0;
                            pc_data_64 = 0;
                            pc_num_of_transactions=0;
                            filter_pass_0_15=1;
                            filter_pass_16_47=1;
                         end
                    end //else if((ep_current_size==16) && (!ep_gbl_done))
                end //if (pc_put)
                        else
                if  (np_put) begin
                    if (PA_chk_en)
                        `slu_msg(UVM_LOW, "SOC_DBG", ("input=%h", pa_payload));
                    if ((ep_global[bus_select] == 1) && (np_ep_current_size != 32))
                        get_ep_fisrt_pkt();
                    else begin
                        pa_np_pkt=get_payload(pa_np_pkt,bus_select);
                        if ((pa_np_pkt.current_size==32) || (pa_np_pkt.current_size==64))
                            begin
                            if (PA_chk_en)
                                `slu_msg(UVM_LOW, "SOC_DBG", ("PA NP found pkt with bus_select %3b bus_sel %2b payload %8h ",bus_select,pa_if.bus_select,pa_np_pkt.payload)); //was HIGH              
                            if (pa_np_pkt.sop==1)
                                begin
                                if(sb_swap[bus_select])
                                    src_dest_payload = {pa_np_pkt.payload[31:16],pa_np_pkt.payload[15:8],np_source16,pa_np_pkt.payload[7:0],np_dest16, 16'b0};
                                else
                                    src_dest_payload = {pa_np_pkt.payload[31:16],np_source16,pa_np_pkt.payload[15:8],np_dest16,pa_np_pkt.payload[7:0], 16'b0};
                                np_opcode = pa_np_pkt.payload[23:16];
                                np_addr_len = pa_np_pkt.payload[30];
                                np_eh = pa_np_pkt.payload[31];
                                pa_np_pkt.payload = src_dest_payload;
                                pa_np_pkt.data_size=0;
                                if((address_filter_en)&&((np_opcode==8'h1)||(np_opcode==8'h3)||(np_opcode==8'h5)||(np_opcode==8'h7)||(np_opcode==8'h0)||(np_opcode==8'h2)||(np_opcode==8'h4)||(np_opcode==8'h6)))
                                    first_pkt_pa_np_pkt = new pa_np_pkt;
                                else if (!address_filter_en)
                                    pa_ch1_injected_items_port.write(pa_np_pkt);
                                if (pa_np_pkt.eop==1) begin
                                    np_sop=1;
                                    np_ep_current_size = 0;
                                    np_ep_gbl_done = 0;
                                    np_ep_glb_first_pkt = 0;
                                    np_eh = 0;
                                    np_addr_len = 0;
                                    np_opcode = 0;
                                    np_num_of_transactions=0;
                                end
                                pa_np_pkt=new();
                                pa_np_pkt.data_size=1; //32
                                if(np_sop==1)
                                    pa_np_pkt.sop=1;
                                np_sop=0;
                                np_num_of_transactions = np_num_of_transactions + 1;
                                `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :np_num_of_transactions=%d opcode=%h eh=%b addr_len=%b np_not_valid=%b payload=%h np_wait_send=%h",np_num_of_transactions,np_opcode,np_eh,np_addr_len,np_not_valid,pa_np_pkt.payload,np_wait_send));
                            end
                            if ((pa_np_pkt.sop==0) && (pa_np_pkt.eop==0))
                                begin                         
                                if (pa_np_pkt.current_size==64)
                                    begin
                                    np_num_of_transactions = np_num_of_transactions + 1;
                                    pa_np_pkt.data_size=0; //64
                                    if(address_filter_en) begin
                                        `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :np_num_of_transactions=%d opcode=%h eh=%b addr_len=%b np_not_valid=%b payload=%h np_wait_send=%h",np_num_of_transactions,np_opcode,np_eh,np_addr_len,np_not_valid,pa_np_pkt.payload,np_wait_send));
                                        if ((np_opcode==8'h1)||(np_opcode==8'h3)||(np_opcode==8'h5)||(np_opcode==8'h7)) begin //opc of write reg
                                            case ({np_eh,np_addr_len})
                                            2'b00: begin
                                                        check_pattern_0_15(pa_np_pkt.payload[31:16]);
                                                        np_filter_pass_0_15=filter_pass_0_15;
                                                        if((np_filter_pass_0_15)&&(np_num_of_transactions==2)) begin
                                                            pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                        end else begin
                                                            np_not_valid = 1;
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                        end
                                                    end
                                             2'b01: begin
                                                        check_pattern_0_15(pa_np_pkt.payload[31:16]);
                                                        np_filter_pass_0_15=filter_pass_0_15;
                                                        check_pattern_16_47(pa_np_pkt.payload[63:32]);
                                                        np_filter_pass_16_47=filter_pass_16_47;
                                                        if ((pa_if.addr_filter_inv) && (((!np_filter_pass_0_15)&&(np_filter_pass_16_47)) || ((np_filter_pass_0_15)&&(!np_filter_pass_16_47)))) begin
                                                            np_filter_pass_0_15 = 1;
                                                            np_filter_pass_16_47 = 1;
                                                        end
                                                        if((np_filter_pass_0_15)&&(np_filter_pass_16_47)&&(np_num_of_transactions==2)) begin
                                                            pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                        end else begin
                                                            np_not_valid = 1;
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                        end
                                                    end
                                             2'b10: begin
                                                        check_pattern_0_15(pa_np_pkt.payload[63:48]);
                                                        np_filter_pass_0_15=filter_pass_0_15;
                                                        if((np_filter_pass_0_15)&&(np_num_of_transactions==2)) begin
                                                            pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                        end else begin
                                                            np_not_valid = 1;
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                        end
                                                    end
                                              2'b11: begin
                                                        if(np_num_of_transactions==2) begin
                                                            check_pattern_0_15(pa_np_pkt.payload[63:48]);
                                                            np_filter_pass_0_15=filter_pass_0_15;
                                                        end
                                                        if(np_num_of_transactions==3) begin
                                                            check_pattern_16_47(pa_np_pkt.payload[31:0]);
                                                            np_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!np_filter_pass_0_15)&&(np_filter_pass_16_47)) || ((np_filter_pass_0_15)&&(!np_filter_pass_16_47)))) begin
                                                                np_filter_pass_0_15 = 1;
                                                                np_filter_pass_16_47 = 1;
                                                            end
                                                        end
                                                        if(np_num_of_transactions==2) begin
                                                            second_pkt_pa_np_pkt = new pa_np_pkt;
                                                            np_wait_send = 1;
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("wait for the next pkt"));
                                                            if(pa_np_pkt.payload[7:4]==1)
                                                                np_data_64=1;
                                                        end else if ((np_filter_pass_0_15)&&(np_filter_pass_16_47)&&(np_num_of_transactions==3)&&(np_data_64==1)) begin
                                                            pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                            pa_ch1_injected_items_port.write(second_pkt_pa_np_pkt);
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                                        end else begin
                                                            np_not_valid = 1;
                                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                        end
                                                   end
                                            endcase
                                        end else if ((np_opcode==8'h0)||(np_opcode==8'h2)||(np_opcode==8'h4)||(np_opcode==8'h6)) begin //opc of read reg
                                           if((np_eh==1)&&(np_addr_len==1)&&(np_num_of_transactions==2)) begin
                                               check_pattern_0_15(pa_np_pkt.payload[63:48]);
                                               np_filter_pass_0_15=filter_pass_0_15;
                                               second_pkt_pa_np_pkt = new pa_np_pkt;
                                               np_wait_send = 1;
                                               `slu_msg(UVM_LOW, "SOC_DBG", ("wait for the next pkt"));
                                           end
                                       end else begin
                                            np_not_valid =1;
                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                       end 
                                       filter_pass_0_15=1;
                                       filter_pass_16_47=1;
                                    end //if (address_filter_en)
                                    if((np_not_valid !=1)&&(np_wait_send!=1))
                                        pa_ch1_injected_items_port.write(pa_np_pkt);
                                    pa_np_pkt=new();
                                    pa_np_pkt.data_size=1; //32
                                end //if (pa_np_pkt.current_size==64)   
                            end //if ((pa_np_pkt.sop==0) && (pa_np_pkt.eop==0))
                            if (pa_np_pkt.eop==1)
                                begin
                                np_num_of_transactions = np_num_of_transactions + 1;
                                if (pa_np_pkt.current_size==64)
                                    pa_np_pkt.data_size=0; //64   
                                `slu_msg(UVM_LOW, "SOC_DBG", ("SBR_PA_MON :np_num_of_transactions=%d opcode=%h eh=%b addr_len=%b np_not_valid=%b payload=%h np_wait_send=%h",np_num_of_transactions,np_opcode,np_eh,np_addr_len,np_not_valid,pa_np_pkt.payload,np_wait_send));
                                if(address_filter_en) begin
                                    if ((np_opcode==8'h0)||(np_opcode==8'h2)||(np_opcode==8'h4)||(np_opcode==8'h6)) begin //opc of read reg
                                            case ({np_eh,np_addr_len})
                                                2'b00: begin
                                                            check_pattern_0_15(pa_np_pkt.payload[31:16]);
                                                            np_filter_pass_0_15=filter_pass_0_15;
                                                            if((np_filter_pass_0_15)&&(np_num_of_transactions==2)) begin
                                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                np_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b01: begin
                                                            check_pattern_0_15(pa_np_pkt.payload[31:16]);
                                                            np_filter_pass_0_15=filter_pass_0_15;
                                                            check_pattern_16_47(pa_np_pkt.payload[63:32]);
                                                            np_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!np_filter_pass_0_15)&&(np_filter_pass_16_47)) || ((np_filter_pass_0_15)&&(!np_filter_pass_16_47)))) begin
                                                                np_filter_pass_0_15 = 1;
                                                                np_filter_pass_16_47 = 1;
                                                            end
                                                            if((np_filter_pass_0_15)&&(np_filter_pass_16_47)&&(np_num_of_transactions==2)) begin
                                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                np_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b10: begin
                                                            check_pattern_0_15(pa_np_pkt.payload[63:48]);
                                                            np_filter_pass_0_15=filter_pass_0_15;
                                                            if((np_filter_pass_0_15)&&(np_num_of_transactions==2)) begin
                                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                                            end else begin
                                                                np_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                                2'b11: begin
                                                            check_pattern_16_47(pa_np_pkt.payload[31:0]);
                                                            np_filter_pass_16_47=filter_pass_16_47;
                                                            if ((pa_if.addr_filter_inv) && (((!np_filter_pass_0_15)&&(np_filter_pass_16_47)) || ((np_filter_pass_0_15)&&(!np_filter_pass_16_47)))) begin
                                                                np_filter_pass_0_15 = 1;
                                                                np_filter_pass_16_47 = 1;
                                                            end
                                                            if ((np_filter_pass_0_15)&&(np_filter_pass_16_47)&&(np_num_of_transactions==3)) begin
                                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                                pa_ch1_injected_items_port.write(second_pkt_pa_np_pkt);
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                                            end else begin
                                                                np_not_valid = 1;
                                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                                            end
                                                       end
                                            endcase
                                    end else if ((np_opcode==8'h1)||(np_opcode==8'h3)||(np_opcode==8'h5)||(np_opcode==8'h7)) begin //opc of write reg
                                        if((np_eh==0)&&(np_addr_len==0)&&(np_num_of_transactions==2)) begin
                                            check_pattern_0_15(pa_np_pkt.payload[31:16]);
                                            np_filter_pass_0_15=filter_pass_0_15;
                                            if (np_filter_pass_0_15) begin
                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first pkt"));
                                            end else begin 
                                                np_not_valid = 1;
                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                            end
                                        end else if((np_eh==1)&&(np_addr_len==1)&&(np_num_of_transactions==3)&&(np_data_64==0)) begin
                                            check_pattern_16_47(pa_np_pkt.payload[31:0]);
                                            np_filter_pass_16_47=filter_pass_16_47;
                                            if ((pa_if.addr_filter_inv) && (((!np_filter_pass_0_15)&&(np_filter_pass_16_47)) || ((np_filter_pass_0_15)&&(!np_filter_pass_16_47)))) begin
                                                np_filter_pass_0_15 = 1;
                                                np_filter_pass_16_47 = 1;
                                            end
                                            if((np_filter_pass_0_15)&&(np_filter_pass_16_47)) begin
                                                pa_ch1_injected_items_port.write(first_pkt_pa_np_pkt);
                                                pa_ch1_injected_items_port.write(second_pkt_pa_np_pkt);
                                                `slu_msg(UVM_LOW, "SOC_DBG", ("print first and second pkt"));
                                            end else begin 
                                                np_not_valid = 1;
                                                `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                            end
                                        end
                                    end else begin //opc of write reg
                                            np_not_valid =1;
                                            `slu_msg(UVM_LOW, "SOC_DBG", ("filter pkt"));
                                    end 
                                end//if (address_filter_en)
                                if(np_not_valid !=1)
                                    pa_ch1_injected_items_port.write(pa_np_pkt);
                                pa_np_pkt.data_size=1; //32
                                pa_np_pkt=new();
                                pa_np_pkt.sop=1;
                                np_ep_current_size = 0;
                                np_ep_gbl_done = 0;
                                np_ep_glb_first_pkt = 0;
                                np_eh = 0;
                                np_addr_len = 0;
                                np_opcode = 0;
                                np_not_valid = 0;
                                np_wait_send = 0;
                                np_data_64 = 0;
                                np_filter_pass_0_15=1;
                                np_filter_pass_16_47=1;
                                np_num_of_transactions=0;
                                filter_pass_0_15=1;
                                filter_pass_16_47=1;
                            end //if (pa_np_pkt.eop==1)]
                        end else if (pa_np_pkt.eop==1) begin //if ((pa_np_pkt.current_size==32) || (pa_np_pkt.current_size==64))
                            if(np_not_valid !=1)
                                pa_ch1_injected_items_port.write(pa_np_pkt);
                            pa_np_pkt.data_size=1; //32
                            pa_np_pkt=new();
                            pa_np_pkt.sop=1;
                            np_ep_current_size = 0;
                            np_ep_gbl_done = 0;
                            np_ep_glb_first_pkt = 0;
                            np_eh = 0;
                            np_addr_len = 0;
                            np_opcode = 0;
                            np_not_valid = 0;
                            np_wait_send = 0;
                            np_data_64 = 0;
                            np_filter_pass_0_15=1;
                            np_filter_pass_16_47=1;
                            np_num_of_transactions=0;
                            filter_pass_0_15=1;
                            filter_pass_16_47=1;
                         end
                    end //else if((ep_current_size==16) && (!ep_gbl_done))
                end //if (np_put)       
        end //forever
    endtask:pa_mon_main
    // ----------------------------------------------------------
    function sbr_pa_pkt_item_XXX get_payload (  sbr_pa_pkt_item_XXX pkt , bit [1:0] bus_select);
        bit [63:0] tmp;
        int current_size=pkt.current_size;
        case (ch_width[bus_select])
        32'd32: begin
                tmp= pa_payload;
                pkt.current_size=pkt.current_size+32;
        end
        32'd16: begin
                tmp= pa_payload;
                pkt.current_size=pkt.current_size+16;
                end
        32'd8: begin
                tmp= pa_payload;
                pkt.current_size=pkt.current_size+8;
        end
        endcase
        
        pkt.payload=(pkt.payload|(tmp<<current_size));
        pkt.eop= eom;
        if (PA_chk_en)
            `slu_msg(UVM_LOW, "SOC_DBG", ("PA payload is %8h tmp is %8h eom is %8h",pkt.payload,tmp,pkt.eop)); // was HIGH
        return pkt;
    endfunction
    
    // ----------------------------------------------------------
    function void get_ep_fisrt_pkt ();
        bit [31:0] tmp;
        if (np_put) begin
            ep_current_size = np_ep_current_size;
            ep_glb_first_pkt = np_ep_glb_first_pkt;
            ep_gbl_done = np_ep_gbl_done;
        end else begin
            ep_current_size = pc_ep_current_size;
            ep_glb_first_pkt = pc_ep_glb_first_pkt;
            ep_gbl_done = pc_ep_gbl_done;
        end
        case (ch_width[bus_select])
        32'd32: begin
                tmp=pa_payload;
                ep_glb_first_pkt=tmp;
                ep_current_size=ep_current_size+32;
        end
        32'd16: begin
                tmp=pa_payload;
                ep_glb_first_pkt=(ep_glb_first_pkt|(tmp<<ep_current_size));
                ep_current_size=ep_current_size+16;
                end
        32'd8: begin
                tmp=pa_payload;
                ep_glb_first_pkt=(ep_glb_first_pkt|(tmp<<ep_current_size));
                ep_current_size=ep_current_size+8;
        end
        endcase
        
        if (PA_chk_en)
            `slu_msg(UVM_LOW, "SOC_DBG", ("Ep global first payload is %h current_payload=%h current_size=%d",ep_glb_first_pkt,pa_payload,ep_current_size)); // was HIGH
        if((ep_current_size==32) && (!ep_gbl_done)) begin
           source16 = ep_glb_first_pkt[15:8];
           dest16   = ep_glb_first_pkt[7:0];
           if (np_put)
               pa_np_pkt.sop=1;
           else
               pa_pc_pkt.sop=1;
           ep_gbl_done = 1;
           if (PA_chk_en)
               `slu_msg(UVM_LOW, "SOC_DBG", ("done first pkt of ep"));
        end else if (np_put)
            np_ep_glb_first_pkt = ep_glb_first_pkt;
        else
            pc_ep_glb_first_pkt = ep_glb_first_pkt;
        if (np_put) begin
            np_ep_current_size = ep_current_size;
            np_source16 = source16;
            np_dest16 = dest16;
            np_ep_gbl_done = ep_gbl_done;
        end else begin
            pc_ep_current_size = ep_current_size;
            pc_source16 = source16;
            pc_dest16 = dest16;
            pc_ep_gbl_done = ep_gbl_done;
        end
    endfunction

    // ----------------------------------------------------------

    task check_pattern_0_15(bit[15:0] payload);
    begin
        filter_results_0_15=0;
        for (int i = 2;i<16;i++) begin
            filter_results_0_15[i] = (pa_if.addr_filter_mask_0_15[i]) ? ((pa_if.addr_filter_match_0_15[i]==payload[i]) ? 1'b1:1'b0) : 1'b1;
            if((!filter_results_0_15[i])&&(!pa_if.addr_filter_inv)) begin
                `slu_msg(UVM_LOW, "SOC_DBG", ("filter not pass at %d",i));
                filter_pass_0_15 = 0;
                break;
            end
         end
         if ((pa_if.addr_filter_inv)&&(filter_results_0_15==16'b1111_1111_1111_1100)) begin
             `slu_msg(UVM_LOW, "SOC_DBG", ("filter not pass because of the inv"));
             filter_pass_0_15 = 0;
         end
    end
    endtask

    task check_pattern_16_47(bit[31:0] payload);
    begin
        filter_results_16_47=0;
        for (int i = 0;i<32;i++) begin
            filter_results_16_47[i] = (pa_if.addr_filter_mask_16_47[i]) ? ((pa_if.addr_filter_match_16_47[i]==payload[i]) ? 1'b1:1'b0) : 1'b1;
            if((!filter_results_16_47[i])&&(!pa_if.addr_filter_inv)) begin
                `slu_msg(UVM_LOW, "SOC_DBG", ("filter not pass at %d",i));
                filter_pass_16_47 = 0;
                break;
            end
         end
         if ((pa_if.addr_filter_inv)&&(filter_results_16_47==32'b1111_1111_1111_1111_1111_1111_1111_1111)) begin
             `slu_msg(UVM_LOW, "SOC_DBG", ("filter not pass because of the inv"));
             filter_pass_16_47 = 0;
         end
    end
    endtask

     // ----------------------------------------------------------

    task run();
        begin
        super.run();
        wait (pa_if.obs_en==1);
        if (sb_obs_std_alone_vc_internal_cov_en) begin
            fork
                data_toggle_task();
                sb_obs_pkt_format_cov();
                sb_clk_check();
            join_none
        end
        pa_mon_main();
        end
    endtask

    // ----------------------------------------------------------
    function new(string name ="sbr_pa_monitor", uvm_component parent = null);
        super.new(name,parent);
        pa_ch0_injected_items_port      = new("pa_ch0_injected_items_port",this);
        pa_ch1_injected_items_port      = new("pa_ch1_injected_items_port",this);
        void'(uvm_config_int::get(this,"*","sb_obs_vc_internal_cov_en", sb_obs_vc_internal_cov_en));
        void'(uvm_config_int::get(this,"*","sb_obs_std_alone_vc_internal_cov_en", sb_obs_std_alone_vc_internal_cov_en));
        pa_bus_sel_change               = new("pa_bus_sel_change",this);
        if (sb_obs_vc_internal_cov_en) begin
            sbr_mux_sel_cg = new;
            sbr_mux_sel_cg.set_inst_name({this.get_full_name(), ".sbr_mux_sel_cg.cov"});
            ifc_toggle_cg = new;
            ifc_toggle_cg.set_inst_name({this.get_full_name(), ".ifc_toggle_cg.cov"});
        end
        if (sb_obs_std_alone_vc_internal_cov_en) begin
            sbr_payload_width_cg = new;
            clk_1_freq_cg = new;
            clks_skew_cg = new;
            data_input_toggle_ch0_cg = new;
            data_input_toggle_ch1_cg = new;
            data_input_toggle_ch2_cg = new;
            data_input_toggle_ch3_cg = new;
            simple_traffic_cp = new;
            read_register_cp = new;
            write_register_cp = new;
            completion_wo_data_cp = new;
            completion_with_data_cp = new;
            message_with_data_cp = new;
            bootPrep_cp = new;
            bootPrepAck_cp = new;
            resetPrep_cp = new;
            resetPrepAck_cp = new;
            resetReq_cp = new;
            forcePWRGatePok_cp = new;
            virtualWire_cp = new;
            cross_ch_toggle_cg = new;
        end
    endfunction



    virtual function void build();
        int ch_width_0,ch_width_1,ch_width_2,ch_width_3;
        super.build();
     
        void'(uvm_config_int::get(this, "",  "SB_OBS_CH0_WIDTH"  ,ch_width_0));
        void'(uvm_config_int::get(this, "",  "SB_OBS_CH1_WIDTH"  ,ch_width_1));
        void'(uvm_config_int::get(this, "",  "SB_OBS_CH2_WIDTH"  ,ch_width_2));
        void'(uvm_config_int::get(this, "",  "SB_OBS_CH3_WIDTH"  ,ch_width_3));
        void'(uvm_config_int::get(this, "",  "NUM_DIFF_BRANCH_CLOCKS"  ,num_of_clk));
        void'(uvm_config_int::get(this, "",  "EXTENDED_EP_CH0"  , ep_global[0]));
        void'(uvm_config_int::get(this, "",  "EXTENDED_EP_CH1"  , ep_global[1]));
        void'(uvm_config_int::get(this, "",  "EXTENDED_EP_CH2"  , ep_global[2]));
        void'(uvm_config_int::get(this, "",  "EXTENDED_EP_CH3"  , ep_global[3]));
        void'(uvm_config_int::get(this, "",  "SB_SWAP_CH0"  , sb_swap[0]));
        void'(uvm_config_int::get(this, "",  "SB_SWAP_CH1"  , sb_swap[1]));
        void'(uvm_config_int::get(this, "",  "SB_SWAP_CH2"  , sb_swap[2]));
        void'(uvm_config_int::get(this, "",  "SB_SWAP_CH3"  , sb_swap[3]));
        ch_width = {ch_width_0,ch_width_1,ch_width_2,ch_width_3};
        if ($value$plusargs("USE_CFGDB=%s", cfgdb_filename))
                PA_chk_en          = getConfigValAndCheckBool({cfg_path, "::sb_obs::SB_OBS_CHK_EN"});
        PA_chk_en = PA_chk_en || ( $test$plusargs("SB_OBS_CHK_EN"));

        for (int i=0; i<4; i++)
            if (PA_chk_en)
                `slu_msg(UVM_LOW, "SOC_DBG", ("SB_OBS_CH%d_WIDTH is %8d num_of_clk=%d sb_swap=%b",i,ch_width[i],num_of_clk,sb_swap));                

    endfunction

    //connect
    // ----------------------------------------------------------
    function void connect();
        super.connect();
        val_svtb_common_uvm_pkg::rcu_base::add_to_rcu(.rcu_name(SB_OBS_RCU_NAME),.comp(this), .name(this.get_full_name()));    // register to local RCU
    endfunction
    //----------------------------------------------------------------
    // powergood_raise
    //----------------------------------------------------------------
    virtual function void powergood_raise();
    endfunction

    //----------------------------------------------------------------
    // powergood_drop
    //----------------------------------------------------------------
    virtual function void powergood_drop();
    endfunction
    //----------------------------------------------------------------
    // reset_raise
    //----------------------------------------------------------------
    virtual function void reset_raise();
    endfunction
    // reset_drop
    //----------------------------------------------------------------
    virtual function void reset_drop();
        pa_pc_pkt = new();
        pa_pc_pkt.sop=1;
        pc_ep_current_size = 0;
        pc_ep_gbl_done = 0;
        pc_ep_glb_first_pkt = 0;
        pa_np_pkt = new();
        pa_np_pkt.sop=1;
        np_ep_current_size = 0;
        np_ep_gbl_done = 0;
        np_ep_glb_first_pkt = 0;

    endfunction
    //----------------------------------------------------------------

    task sb_clk_check;
        time clk0_time1;
        time clk0_time2;
        time clk1_time1;
        time clk1_time2;
        repeat (1) @(posedge pa_if.pa_clock_0);
        clk0_time1 = $time;
        repeat (1) @(posedge pa_if.pa_clock_0);
        clk0_time2 = $time;
        repeat (1) @(posedge pa_if.pa_clock_1);
        clk1_time1 = $time;
        repeat (1) @(posedge pa_if.pa_clock_1);
        clk1_time2 = $time;
        sb_clk1_freq=clk1_time2-clk1_time1;
        clk_1_freq_cg.sample();
        repeat (1) @(posedge pa_if.pa_clock_0);
        clk0_time1 = $time;
        repeat (1) @(posedge pa_if.pa_clock_1);
        clk1_time1 = $time;
        sb_clks_skew=clk1_time1-clk0_time1;
        clks_skew_cg.sample();
    endtask

    task data_toggle_task;
        fork
        begin
            forever 
                begin
                @(posedge pa_if.eom[0]) begin
                    data_input_toggle_ch0_cg.sample();
                end
            end
        end
        begin
            forever 
                begin
                @(posedge pa_if.eom[1]) begin
                    data_input_toggle_ch1_cg.sample();
                end
            end
        end
        begin
            forever 
                begin
                @(posedge pa_if.eom[2]) begin
                    data_input_toggle_ch2_cg.sample();
                end
            end
        end
        begin
            forever 
                begin
                @(posedge pa_if.eom[3]) begin
                    data_input_toggle_ch3_cg.sample();
                end
            end
        end
        begin
            forever 
                begin
                @(posedge pa_if.pa_clock_0) begin
                    if((pa_if.pc_put[0]==1)||(pa_if.np_put[0]==1))
                        ch_toggle[0] = 1;
                    if((pa_if.pc_put[1]==1)||(pa_if.np_put[1]==1))
                        ch_toggle[1] = 1;
                    if((pa_if.pc_put[2]==1)||(pa_if.np_put[2]==1))
                        ch_toggle[2] = 1;
                    if((pa_if.pc_put[3]==1)||(pa_if.np_put[3]==1))
                        ch_toggle[3] = 1;
                    cross_ch_toggle_cg.sample();
                    ch_toggle = 0;
               end
           end               
        end
        join_none
    endtask

    task sb_obs_pkt_format_cov;
        fork
        begin
        forever
            begin
            wait (pa_if.obs_en==1);
            @(posedge pa_if.pc_put[0]) 
                if (ep_global==4'h1) 
                    @(posedge pa_if.pc_put[0]);
                ch0_opcode_pc = pa_if.ch_payload[0][23:16];
                ch0_eh_pc = pa_if.ch_payload[0][31];
                ch0_length_of_address_pc = pa_if.ch_payload[0][30];
                while (pa_if.eom[0]==0) begin
                    if (((num_of_chunks_pc == 2) && (ch0_eh_pc == 1)) || ((num_of_chunks_pc == 1) && (ch0_eh_pc == 0)))
                        length_of_data = pa_if.ch_payload[0][7:4];
                    num_of_chunks_pc = num_of_chunks_pc+1;
                    @(posedge pa_if.pc_put[0]);
                end 
                num_of_chunks_pc = num_of_chunks_pc+1;
                eh = ch0_eh_pc;
                length_of_address = ch0_length_of_address_pc;
                case (ch0_opcode_pc)
                    8'h80 :begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc simple_traffic_cp ep_global %h eh %h",ep_global, eh ))
                        simple_traffic_cp.sample();
                    end
                    8'h0 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc read_register_cp ep_global %h eh %h",ep_global, eh ))
                      read_register_cp.sample();
                    end
                    8'h1 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc write_register_cp ep_global %h eh %h",ep_global, eh ))
                      write_register_cp.sample();
                    end
                    8'h20 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc completion_wo_data_cp ep_global %h eh %h",ep_global, eh ))
                      completion_wo_data_cp.sample();
                    end
                    8'h21 : begin
                        `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc completion_with_data_cp ep_global %h eh %h num_of_chunks_pc %d",ep_global, eh, num_of_chunks_pc ))
                      case (num_of_chunks_pc)
                      3 : length_of_completion_data = 2'h0;
                      4 : if(!eh)
                            length_of_completion_data = 2'h1;
                        else
                            length_of_completion_data = 2'h0;
                      5 : if(!eh)
                            length_of_completion_data = 2'h2;
                        else
                            length_of_completion_data = 2'h1;
                      6 : if(!eh)
                            length_of_completion_data = 2'h3;
                        else
                            length_of_completion_data = 2'h2;
                      7: length_of_completion_data = 2'h3;
                      endcase
                    completion_with_data_cp.sample();
                    end
                    8'h40 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc message_with_data_cp ep_global %h eh %h",ep_global, eh ))
                      case (num_of_chunks_pc)
                      2 : length_of_data = 0;
                      3 : begin
                        if(!eh)
                            length_of_data = 1;
                        else
                            length_of_data = 0;
                      end
                      4 : length_of_data = 1;
                      endcase
                      message_with_data_cp.sample();
                    end
                    8'h28 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc bootPrep_cp ep_global %h eh %h",ep_global, eh ))
                      bootPrep_cp.sample();
                    end
                    8'h29 : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc bootPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                      bootPrepAck_cp.sample();
                    end
                    8'h2a : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc resetPrep_cp ep_global %h eh %h",ep_global, eh ))
                      resetPrep_cp.sample();
                    end
                    8'h2b : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc resetPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                      resetPrepAck_cp.sample();
                    end
                    8'h2c : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc resetReq_cp ep_global %h eh %h",ep_global, eh ))
                      resetReq_cp.sample();
                    end
                    8'h2e : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc forcePWRGatePok_cp ep_global %h eh %h",ep_global, eh ))
                      forcePWRGatePok_cp.sample();
                    end
                    8'h2d : begin
                      `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_pc virtualWire_cp ep_global %h eh %h",ep_global, eh ))
                      virtualWire_cp.sample();
                    end
                endcase
                num_of_chunks_pc = 0;
             end //forever
         end
         begin
         forever 
            begin
            @(posedge pa_if.np_put[0]) 
                if (ep_global==4'h1) 
                    @(posedge pa_if.np_put[0]);
                ch0_opcode_np = pa_if.ch_payload[0][23:16];
                ch0_eh_np = pa_if.ch_payload[0][31];
                ch0_length_of_address_np = pa_if.ch_payload[0][30];
                while (pa_if.eom[0]==0) begin
                    if ((num_of_chunks_np == 2) && (ch0_eh_np == 1) || (num_of_chunks_np == 1) && (ch0_eh_np == 0))
                        length_of_data = pa_if.ch_payload[0][7:4];
                    num_of_chunks_np = num_of_chunks_np+1;
                    @(posedge pa_if.np_put[0]);
                end 
                num_of_chunks_np = num_of_chunks_np+1;
                eh = ch0_eh_np;
                length_of_address = ch0_length_of_address_np;
                case (ch0_opcode_np)
                    8'h80 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np simple_traffic_cp ep_global %h eh %h",ep_global, eh ))

                        simple_traffic_cp.sample();
                    end
                    8'h0 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np read_register_cp ep_global %h eh %h",ep_global, eh ))
                       read_register_cp.sample();
                    end
                    8'h1 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np write_register_cp ep_global %h eh %h",ep_global, eh ))
                       write_register_cp.sample();
                    end
                    8'h20 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np completion_wo_data_cp ep_global %h eh %h",ep_global, eh ))
                       completion_wo_data_cp.sample();
                    end
                    8'h21 : begin
                        `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np completion_with_data_cp ep_global %h eh %h num_of_chunks_pc %d",ep_global, eh, num_of_chunks_np ))
                      case (num_of_chunks_np)
                      3 : length_of_completion_data = 2'h0;
                      4 : if(!eh)
                            length_of_completion_data = 2'h1;
                        else
                            length_of_completion_data = 2'h0;
                      5 : if(!eh)
                            length_of_completion_data = 2'h2;
                        else
                            length_of_completion_data = 2'h1;
                      6 : if(!eh)
                            length_of_completion_data = 2'h3;
                        else
                            length_of_completion_data = 2'h2;
                      7: length_of_completion_data = 2'h3;
                      endcase
                    completion_with_data_cp.sample();
                    end
                    8'h40 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np message_with_data_cp ep_global %h eh %h",ep_global, eh ))
                       case (num_of_chunks_np)
                      3 : length_of_data = 0;
                      4 : begin
                        if(!eh)
                            length_of_data = 1;
                        else
                            length_of_data = 0;
                      end
                      5 : length_of_data = 1;
                      endcase
                       message_with_data_cp.sample();
                    end
                    8'h28 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np bootPrep_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrep_cp.sample();
                    end
                    8'h29 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np bootPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrepAck_cp.sample();
                    end
                    8'h2a : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np resetPrep_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrep_cp.sample();
                    end
                    8'h2b : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np resetPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrepAck_cp.sample();
                    end
                    8'h2c : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np resetReq_cp ep_global %h eh %h",ep_global, eh ))
                       resetReq_cp.sample();
                    end
                    8'h2e : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np forcePWRGatePok_cp ep_global %h eh %h",ep_global, eh ))
                       forcePWRGatePok_cp.sample();
                    end
                    8'h2d : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch0_opcode_np virtualWire_cp ep_global %h eh %h",ep_global, eh ))
                       virtualWire_cp.sample();
                    end
                endcase
                num_of_chunks_np = 0;
            end //forever
        end
        begin
        forever
            begin 
            @(posedge pa_if.pc_put[2]) 
                if (ep_global==4'h4)
                    @(posedge pa_if.pc_put[2]);
                ch2_opcode_pc = pa_if.ch_payload[2][23:16];
                ch2_eh_pc = pa_if.ch_payload[2][31];
                ch2_length_of_address_pc = pa_if.ch_payload[2][30];
                while (pa_if.eom[2]==0) begin
                    if ((num_of_chunks_pc == 2) && (ch2_eh_pc == 1) || (num_of_chunks_pc == 1) && (ch2_eh_pc == 0))
                        length_of_data = pa_if.ch_payload[2][7:4];
                    num_of_chunks_pc = num_of_chunks_pc+1;
                    @(posedge pa_if.pc_put[2]);
                end
                num_of_chunks_pc = num_of_chunks_pc+1;
                eh = ch2_eh_pc;
                length_of_address = ch2_length_of_address_pc;
                case (ch2_opcode_pc)
                    8'h80 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc simple_traffic_cp ep_global %h eh %h",ep_global, eh ))
                        simple_traffic_cp.sample();
                    end
                    8'h0 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc read_register_cp ep_global %h eh %h",ep_global, eh ))
                       read_register_cp.sample();
                    end
                    8'h1 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc write_register_cp ep_global %h eh %h",ep_global, eh ))
                       write_register_cp.sample();
                    end
                    8'h20 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc completion_wo_data_cp ep_global %h eh %h",ep_global, eh ))
                       completion_wo_data_cp.sample();
                    end
                    8'h21 : begin
                        `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc completion_with_data_cp ep_global %h eh %h num_of_chunks_pc %d",ep_global, eh, num_of_chunks_pc ))
                      case (num_of_chunks_pc)
                      3 : length_of_completion_data = 2'h0;
                      4 : if(!eh)
                            length_of_completion_data = 2'h1;
                        else
                            length_of_completion_data = 2'h0;
                      5 : if(!eh)
                            length_of_completion_data = 2'h2;
                        else
                            length_of_completion_data = 2'h1;
                      6 : if(!eh)
                            length_of_completion_data = 2'h3;
                        else
                            length_of_completion_data = 2'h2;
                      7: length_of_completion_data = 2'h3;
                      endcase
                      completion_with_data_cp.sample();
                      end
                    8'h40 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc message_with_data_cp ep_global %h eh %h",ep_global, eh ))
                       case (num_of_chunks_pc)
                      3 : length_of_data = 0;
                      4 : begin
                        if(!eh)
                            length_of_data = 1;
                        else
                            length_of_data = 0;
                      end
                      5 : length_of_data = 1;
                      endcase
                       message_with_data_cp.sample();
                    end
                    8'h28 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc bootPrep_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrep_cp.sample();
                    end
                    8'h29 : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc bootPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrepAck_cp.sample();
                    end
                    8'h2a : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc resetPrep_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrep_cp.sample();
                    end
                    8'h2b : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc resetPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrepAck_cp.sample();
                    end
                    8'h2c : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc resetReq_cp ep_global %h eh %h",ep_global, eh ))
                       resetReq_cp.sample();
                    end
                    8'h2e : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc forcePWRGatePok_cp ep_global %h eh %h",ep_global, eh ))
                       forcePWRGatePok_cp.sample();
                    end
                    8'h2d : begin 
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_pc virtualWire_cp ep_global %h eh %h",ep_global, eh ))
                       virtualWire_cp.sample();
                    end
                endcase
                num_of_chunks_pc = 0;
             end //forever
         end
         begin
         forever 
            begin
            @(posedge pa_if.np_put[2]) 
                if (ep_global==4'h4)
                    @(posedge pa_if.np_put[2]);
                ch2_opcode_np = pa_if.ch_payload[2][23:16];
                ch2_eh_np = pa_if.ch_payload[2][31];
                ch2_length_of_address_np = pa_if.ch_payload[2][30];
                while (pa_if.eom[2]==0) begin
                    if ((num_of_chunks_np == 2) && (ch2_eh_np == 1) || (num_of_chunks_np == 1) && (ch2_eh_np == 0))
                        length_of_data = pa_if.ch_payload[2][7:4];
                    num_of_chunks_np = num_of_chunks_np+1;
                    @(posedge pa_if.np_put[2]);
                end
                num_of_chunks_np = num_of_chunks_np+1;
                eh = ch2_eh_np;
                length_of_address = ch2_length_of_address_np;
                case (ch2_opcode_np)
                    8'h80 :begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np simple_traffic_cp ep_global %h eh %h",ep_global, eh ))                    
                        simple_traffic_cp.sample();
                    end
                    8'h0 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np read_register_cp ep_global %h eh %h",ep_global, eh ))
                       read_register_cp.sample();
                    end
                    8'h1 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np write_register_cp ep_global %h eh %h length_of_address %h length_of_data %h",ep_global, eh, length_of_address, length_of_data ))
                       write_register_cp.sample();
                    end
                    8'h20 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np completion_wo_data_cp ep_global %h eh %h",ep_global, eh ))
                       completion_wo_data_cp.sample();
                    end
                    8'h21 : begin
                        `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np completion_with_data_cp ep_global %h eh %h num_of_chunks_pc %d",ep_global, eh, num_of_chunks_pc ))
                      case (num_of_chunks_pc)
                      3 : length_of_completion_data = 2'h0;
                      4 : if(!eh)
                            length_of_completion_data = 2'h1;
                        else
                            length_of_completion_data = 2'h0;
                      5 : if(!eh)
                            length_of_completion_data = 2'h2;
                        else
                            length_of_completion_data = 2'h1;
                      6 : if(!eh)
                            length_of_completion_data = 2'h3;
                        else
                            length_of_completion_data = 2'h2;
                      7: length_of_completion_data = 2'h3;
                      endcase
                      completion_with_data_cp.sample();
                      end
                    8'h40 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np message_with_data_cp ep_global %h eh %h",ep_global, eh ))
                       case (num_of_chunks_np)
                      3 : length_of_data = 0;
                      4 : begin
                        if(!eh)
                            length_of_data = 1;
                        else
                            length_of_data = 0;
                      end
                      5 : length_of_data = 1;
                      endcase
                       message_with_data_cp.sample();
                    end
                    8'h28 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np bootPrep_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrep_cp.sample();
                    end
                    8'h29 : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np bootPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       bootPrepAck_cp.sample();
                    end
                    8'h2a : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np resetPrep_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrep_cp.sample();
                    end
                    8'h2b : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np resetPrepAck_cp ep_global %h eh %h",ep_global, eh ))
                       resetPrepAck_cp.sample();
                    end
                    8'h2c : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np resetReq_cp ep_global %h eh %h",ep_global, eh ))
                       resetReq_cp.sample();
                    end
                    8'h2e : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np forcePWRGatePok_cp ep_global %h eh %h",ep_global, eh ))
                       forcePWRGatePok_cp.sample();
                    end
                    8'h2d : begin
                       `slu_msg(UVM_LOW, "SOC_DBG", ("ch2_opcode_np virtualWire_cp ep_global %h eh %h",ep_global, eh ))
                       virtualWire_cp.sample();
                    end
                endcase
                num_of_chunks_np = 0;
            end //forever
        end
        join_none
    endtask


endclass:sbr_pa_monitor
