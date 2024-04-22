import uvm_pkg::*;
import aupi_pkg::*;
import uxi_env_pkg::*;
import aufi_pkg::*;
import auvm_pkg::*;
import auvm_cache_pkg::*;
import uri_types_pkg::*;

`include "smart_uxi_uri_maker.sv"
`include "hw_mon/ufi_vc_hw_structs.sv"
`include "hw_mon/ufi_vc_hw_collector_recording_macros.sv"
`include "slu_rtl_tlm_macros.svh"

module avery_uxi_ti#(
        parameter string UXI_ENV_NAME = "uxi_cbb0",
        parameter bit GEN_HW_COLLECTOR = 1,
        parameter bit USE_HW_URI_GENERATOR = 1,
        parameter bit USE_AVERY_SAM = 1,
        parameter bit RTL_CONNECTED = 1,
        parameter bit RTL_IS_AGENT = 0,
        parameter bit RTL_TWO_LAYERS_MODE = 1,
        parameter int unsigned NUM_OF_CLUSTERS = 1,
        parameter int unsigned NUM_OF_UXI_CA_NODES = 2,
        parameter int unsigned NUM_OF_UXI_IO_NODES = 3,
        parameter int unsigned NUM_OF_UXI_HA_NODES = 1,
        parameter int unsigned CA_NODE_IDS_VALUES[NUM_OF_UXI_CA_NODES] = '{ 'h4, 'h3 },
        parameter int unsigned IO_NODE_IDS_VALUES[NUM_OF_UXI_IO_NODES] = '{ 'h7, 'h8, 'h9 },
        parameter int unsigned HA_NODE_IDS_VALUES[NUM_OF_UXI_HA_NODES] = '{ 'h1 }
    )(
        input logic clk,
        input logic rst
    );

    parameter INTEL_TOPOLOGY = 1;
    parameter int unsigned NUM_OF_UXI_NODES = NUM_OF_UXI_CA_NODES + NUM_OF_UXI_IO_NODES + NUM_OF_UXI_HA_NODES;
    parameter int unsigned NUM_OF_UXI_IFC = (NUM_OF_UXI_CA_NODES * 2) + (NUM_OF_UXI_IO_NODES * 2);
    parameter int unsigned NUM_OF_RTL_LAYERS = RTL_TWO_LAYERS_MODE ? 2 : 1;
    parameter int unsigned NUM_OF_UFI_LINKS =  (NUM_OF_CLUSTERS * NUM_OF_RTL_LAYERS) /*RTL CA*/ + (NUM_OF_UXI_CA_NODES - 1) /*Avery CAs*/ +  NUM_OF_UXI_IO_NODES /*IO Agent*/;
    parameter int unsigned NODE_IDS_VALUES[NUM_OF_UXI_NODES] = { CA_NODE_IDS_VALUES, IO_NODE_IDS_VALUES, HA_NODE_IDS_VALUES};
    
    aupi_if uxi_ifs[NUM_OF_UXI_IFC]();
    aupi_if uxi_mon_if();

    aufi_a2f_intf a2f_if[NUM_OF_UFI_LINKS](clk, rst);
    aufi_f2a_intf f2a_if[NUM_OF_UFI_LINKS](clk, rst);

    uri_if#(.NUM_PORTS(3)) a2f_uri_ifc[NUM_OF_UFI_LINKS]();
    uri_if#(.NUM_PORTS(3)) f2a_uri_ifc[NUM_OF_UFI_LINKS]();

    valid_uri_if a2f_valid_uri_if[NUM_OF_UFI_LINKS]();
    valid_uri_if f2a_valid_uri_if[NUM_OF_UFI_LINKS]();

    topology topo;
    auvm_cache_env_cfg cache_env_cfg;

    initial begin
        topo = new();
        topo.rtl_connected = RTL_CONNECTED;
        topo.rtl_is_agent = RTL_IS_AGENT;
        topo.rtl_two_layes_mode = RTL_TWO_LAYERS_MODE;
        topo.num_of_clusters = NUM_OF_CLUSTERS;
        topo.num_of_rtl_layers = NUM_OF_RTL_LAYERS;
        topo.use_avery_sam = USE_AVERY_SAM;
        topo.use_hw_uri_generator = USE_HW_URI_GENERATOR;

        topo.num_of_cache_agents_nodes = NUM_OF_UXI_CA_NODES;
        topo.num_of_io_agents_nodes = NUM_OF_UXI_IO_NODES;
        topo.num_of_home_agents_nodes = NUM_OF_UXI_HA_NODES;
        topo.num_of_uxi_nodes = NUM_OF_UXI_NODES;
        topo.num_of_ufi_links = NUM_OF_UFI_LINKS;
        topo.num_of_uxi_ifc = NUM_OF_UXI_IFC;
        topo.cache_agents_node_ids = CA_NODE_IDS_VALUES;
        topo.io_agents_node_ids = IO_NODE_IDS_VALUES;
        topo.home_agents_node_ids = HA_NODE_IDS_VALUES;
        topo.all_node_ids = NODE_IDS_VALUES;

        foreach(topo.cache_agents_node_ids[i]) begin
            topo.cache_agents_idxs.push_back(i);
        end
        foreach(topo.io_agents_node_ids[i]) begin
            topo.io_agents_idxs.push_back(i + topo.num_of_cache_agents_nodes);
        end
        foreach(topo.home_agents_node_ids[i]) begin
            topo.home_agents_idxs.push_back(i + topo.num_of_cache_agents_nodes + topo.num_of_io_agents_nodes);
        end

        foreach(topo.all_node_ids[i]) begin
            if(topo.all_node_ids[i] inside { topo.home_agents_node_ids }) begin
                topo.num_of_ports_per_node.push_back(topo.num_of_cache_agents_nodes + topo.num_of_io_agents_nodes);
            end
            else begin
                topo.num_of_ports_per_node.push_back(1);
            end
        end

        uvm_config_db #(topology)::set(uvm_root::get(), UXI_ENV_NAME, "topology", topo);
    end

    for (genvar node_idx = 0; node_idx < NUM_OF_UXI_NODES; node_idx++) begin
        if(node_idx < NUM_OF_UXI_CA_NODES + NUM_OF_UXI_IO_NODES) begin
            initial begin
                uvm_config_db #(int)::set(uvm_root::get(), {UXI_ENV_NAME, "_upi_env"}, $psprintf("upi_n%0d_port_num", node_idx), 1);
                uvm_config_db #(virtual aupi_if)::set(uvm_root::get(), {UXI_ENV_NAME, "_upi_env"}, $psprintf("if_upi_n%0d_p%0d", node_idx, 0), uxi_ifs[node_idx]);
            end
        end
        else begin
            initial begin
                uvm_config_db #(int)::set(uvm_root::get(), {UXI_ENV_NAME, "_upi_env"}, $psprintf("upi_n%0d_port_num", node_idx), NUM_OF_UXI_CA_NODES + NUM_OF_UXI_IO_NODES);
            end
            for (genvar port = 0; port < NUM_OF_UXI_CA_NODES + NUM_OF_UXI_IO_NODES; port++) begin
                initial begin
                    uvm_config_db #(virtual aupi_if)::set(uvm_root::get(), {UXI_ENV_NAME, "_upi_env"}, $psprintf("if_upi_n%0d_p%0d", node_idx, port), uxi_ifs[node_idx+port]);
                end
            end
        end
    end

    logic a2fdelay1psclk;
    logic f2adelay1psclk;
    assign #1ps a2fdelay1psclk = clk;
    assign #1ps f2adelay1psclk = clk;

    for (genvar link = 0; link < NUM_OF_UFI_LINKS; link++) begin
        initial begin
            uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), {UXI_ENV_NAME, "_uri_manager"}, $psprintf("a2f_if[%0d]", link), a2f_if[link]);
            uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), {UXI_ENV_NAME, "_uri_manager"}, $psprintf("f2a_if[%0d]", link), f2a_if[link]);

            uvm_config_db #(virtual uri_if#(.NUM_PORTS(3)))::set(uvm_root::get(),       {UXI_ENV_NAME, "_uri_manager"}, $psprintf("a2f_uri_ifc[%0d]", link), a2f_uri_ifc[link]);
            uvm_config_db #(virtual uri_if#(.NUM_PORTS(3)))::set(uvm_root::get(),       {UXI_ENV_NAME, "_uri_manager"}, $psprintf("f2a_uri_ifc[%0d]", link), f2a_uri_ifc[link]);

            uvm_config_db #(virtual valid_uri_if)::set(uvm_root::get(), {UXI_ENV_NAME, "_uri_manager"}, $psprintf("a2f_valid_uri_if[%0d]", link), a2f_valid_uri_if[link]);
            uvm_config_db #(virtual valid_uri_if)::set(uvm_root::get(), {UXI_ENV_NAME, "_uri_manager"}, $psprintf("f2a_valid_uri_if[%0d]", link), f2a_valid_uri_if[link]);

            assign a2f_valid_uri_if[link].valid = a2fdelay1psclk & (a2f_if[link].req_is_valid | a2f_if[link].rsp_is_valid | a2f_if[link].data_is_valid);
            assign f2a_valid_uri_if[link].valid = f2adelay1psclk & (f2a_if[link].req_is_valid | f2a_if[link].rsp_is_valid | f2a_if[link].data_is_valid);
        end
    end

    for (genvar clstr = 0; clstr < NUM_OF_CLUSTERS; clstr++) begin
        for (genvar link = 0; link < NUM_OF_RTL_LAYERS; link++) begin
            initial begin
                uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_CA_UFI_LINK%0d", clstr)},  $sformatf("a2f_if[%0d]", link), a2f_if[(clstr * NUM_OF_RTL_LAYERS) + link]);
                uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_CA_UFI_LINK%0d", clstr)},  $sformatf("f2a_if[%0d]", link), f2a_if[(clstr * NUM_OF_RTL_LAYERS) + link]);
            end
        end
    end

    for (genvar link = 0; link < (NUM_OF_UXI_CA_NODES - 1); link++) begin
        initial begin
            uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_AVERY_CA_UFI_LINK%0d", link)}, "a2f_if[0]", a2f_if[link + (NUM_OF_CLUSTERS * NUM_OF_RTL_LAYERS)]);
            uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_AVERY_CA_UFI_LINK%0d", link)}, "f2a_if[0]", f2a_if[link + (NUM_OF_CLUSTERS * NUM_OF_RTL_LAYERS)]);
        end
    end

    for (genvar link = 0; link < NUM_OF_UXI_IO_NODES; link++) begin
        initial begin
            uvm_config_db #(virtual aufi_a2f_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_IO_UFI_LINK%0d", link)}, "a2f_if[0]", a2f_if[link + (NUM_OF_CLUSTERS * NUM_OF_RTL_LAYERS) + NUM_OF_UXI_CA_NODES - 1]);
            uvm_config_db #(virtual aufi_f2a_intf)::set(uvm_root::get(), {UXI_ENV_NAME, $sformatf("_ufi_env_IO_UFI_LINK%0d", link)}, "f2a_if[0]", f2a_if[link + (NUM_OF_CLUSTERS * NUM_OF_RTL_LAYERS) + NUM_OF_UXI_CA_NODES - 1]);
        end
    end

    initial begin
        //config
        uvm_config_db #(bit     )::set(uvm_root::get(), UXI_ENV_NAME,      "is_intel_topology",  INTEL_TOPOLOGY);

        //mon FIXME: oohayon see what we do with monitor
        uvm_config_db #(virtual aupi_if)::set(uvm_root::get(), {UXI_ENV_NAME, "_upi_env"}, "if_upi_mon", uxi_mon_if);

         //routing table
        for (int node = 0; node < NUM_OF_UXI_NODES; node++) begin
            aupi_rt_tab   tab;
            tab = new($psprintf("n%0d_rt_tab",node));
            for (int other = 0; other < NUM_OF_UXI_NODES; other++) begin
                if(node != other) begin
                    aupi_rt_entry ent;
                    aupi_port_id_t port;

                    if(node < NUM_OF_UXI_CA_NODES + NUM_OF_UXI_IO_NODES) begin
                        port = aupi_port_id_t'(0);
                        ent = new($psprintf("n%0d_n%0d",node,other), NODE_IDS_VALUES[other]);
                    end
                    else begin
                        port = aupi_port_id_t'(other);
                        ent = new($psprintf("n%0d_n%0d",node,other), NODE_IDS_VALUES[other]);
                    end

                    ent.add_rt_port(port);
                    tab.add_rt_ent(ent);
                end
            end
            uvm_config_db #(aupi_rt_tab)::set(uvm_root::get(),{UXI_ENV_NAME, "_upi_env"},$psprintf("%s_upi_node%0d_rt_tab", {UXI_ENV_NAME, "_upi_env"}, node), tab);
        end

    end

    initial begin
        cache_env_cfg = new();

        for(int node = 0; node < topo.num_of_cache_agents_nodes; node++) begin
            cache_env_cfg.ca_node_id_q.push_back(topo.cache_agents_node_ids[node]);
        end

        for(int node = 0; node < topo.num_of_home_agents_nodes; node++) begin
            cache_env_cfg.ha_node_id_q.push_back(topo.home_agents_node_ids[node]);
        end

        cache_env_cfg.num_ca = topo.num_of_cache_agents_nodes;
        cache_env_cfg.num_ha = topo.num_of_home_agents_nodes;

        if (cache_env_cfg.num_ha > 0) begin
            foreach (cache_env_cfg.ha_node_id_q[i])
                cache_env_cfg.ha_cluster_a[cache_env_cfg.ha_node_id_q[i]]= cache_env_cfg.ca_node_id_q;
        end

        uvm_config_db #(auvm_cache_env_cfg)::set(uvm_root::get(), UXI_ENV_NAME, "auvm_cache_env_cfg", cache_env_cfg);
    end

    // generate  if(USE_HW_URI_GENERATOR==1) begin : avery_uxi_uri_maker
    //         `AVERY_UXI_CREATE_URI_MAKER((NUM_OF_UFI_LINKS * 2), clk,rst, 4'd1)
    //         for(genvar i = 0; i < NUM_OF_UFI_LINKS; i++) begin
    //             if(RTL_IS_AGENT == 0) begin
    //                 `AVERY_UXI_CONNECT_URI_MAKER(((i*2) + 1), (i*2), f2a_if[i], a2f_if[i], f2a_uri_ifc[i].uri, a2f_uri_ifc[i].uri)
    //             end
    //             else begin
    //                 `AVERY_UXI_CONNECT_URI_MAKER(((i*2) + 1), (i*2), a2f_if[i], f2a_if[i], a2f_uri_ifc[i].uri, f2a_uri_ifc[i].uri)
    //             end
    //         end
    //     end
    // endgenerate

    generate
        if(GEN_HW_COLLECTOR) begin
            logic [31:0] clock_a2f_counter;
            logic [31:0] clock_f2a_counter;

            ufi_req_rec_struct  ufi_req_a2f_struct[NUM_OF_UFI_LINKS];
            ufi_rsp_rec_struct  ufi_rsp_a2f_struct[NUM_OF_UFI_LINKS];
            ufi_data_rec_struct ufi_data_a2f_struct[NUM_OF_UFI_LINKS];

            ufi_req_rec_struct  ufi_req_f2a_struct[NUM_OF_UFI_LINKS];
            ufi_rsp_rec_struct  ufi_rsp_f2a_struct[NUM_OF_UFI_LINKS];
            ufi_data_rec_struct ufi_data_f2a_struct[NUM_OF_UFI_LINKS];

            `UFI_VC_CLOCK_COUNT(clock_a2f_counter,(clock_a2f_counter + 32'h1), clk, ~rst)
            `UFI_VC_CLOCK_COUNT(clock_f2a_counter,(clock_f2a_counter + 32'h1), clk, ~rst)
             for(genvar i = 0; i < NUM_OF_UFI_LINKS; i++) begin
                `ufi_vc_assign_interface_to_txn_struct (a2f_if[i], a2f_uri_ifc[i], ufi_req_a2f_struct[i], ufi_rsp_a2f_struct[i], ufi_data_a2f_struct[i], clock_a2f_counter)
                `ufi_vc_assign_interface_to_txn_struct (f2a_if[i], f2a_uri_ifc[i], ufi_req_f2a_struct[i], ufi_rsp_f2a_struct[i], ufi_data_f2a_struct[i], clock_f2a_counter)
             end        
            ufi_vc_hw_collector_wrapper #(
                .VC_NAME("UFI_HW_COL"),
                .NUM_OF_UFI_LINKS(NUM_OF_UFI_LINKS)
            ) ufi_bfm_hw_collector(
                .clk(clk),
                .rst(rst),
                .ufi_req_a2f_struct(ufi_req_a2f_struct),
                .ufi_rsp_a2f_struct(ufi_rsp_a2f_struct),
                .ufi_data_a2f_struct(ufi_data_a2f_struct),
                .ufi_req_f2a_struct(ufi_req_f2a_struct),
                .ufi_rsp_f2a_struct(ufi_rsp_f2a_struct),
                .ufi_data_f2a_struct(ufi_data_f2a_struct)
            );
        end
    endgenerate

endmodule
