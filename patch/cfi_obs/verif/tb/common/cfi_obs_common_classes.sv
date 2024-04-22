///=====================================================================================================================
/// Module Name:        cfi_obs_common_classes.sv
///
/// Primary Contact:    yuvalman
/// Secondary Contact:
/// Creation Date:      12/2020
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
///
/// This file should contain CFI_OBS common structs and classes
///
///=====================================================================================================================

//---------------------------------------------------------------- //
//                      CFI_OBS Common Structs                     //
//---------------------------------------------------------------- //

// Place holder for structs


//---------------------------------------------------------------- //
//                      CFI_OBS Common Classes                     //
//---------------------------------------------------------------- //

// Place holder for classes

//----------------------------------------------------------------
class UpiUtils implements uxi::AddressHash; //TODO yuvalman

    virtual function bit get_sr_o_network_id(uxi::address address);
      return ^address;
    endfunction : get_sr_o_network_id
    
    virtual function int get_home_agent_dest_id(uxi::address address);
        return 6;
    endfunction : get_home_agent_dest_id

endclass 

//----------------------------------------------------------------
class Tunneled_Response extends uvm_component implements uxi::UserTunneledResponder;
  `uvm_component_utils(Tunneled_Response)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction : new

  virtual function uxi::tunnel_data user_tunnel_data(uxi::tunnel_data tunnel_data);
  endfunction : user_tunnel_data

  virtual function uxi::UserTunneledResponder::p2p_msg_type user_tunnel_type(uxi::tunnel_data tunnel_data);
      int p2p_s_msg_type[$] = {uxi::IOSF_Posted_Short,uxi::IOSF_NonPosted_Short,uxi::IOSF_Cmp_Short,uxi::P2P_Generic_Short};
      int idx;
      std::randomize(idx) with {idx inside {[0:(p2p_s_msg_type.size()-1)]};};
       `slu_msg (UVM_LOW, get_name(), ("returning p2p_msg_type %0d", p2p_s_msg_type[idx]));
      return p2p_s_msg_type[idx];
      
  endfunction : user_tunnel_type

  virtual function uxi::data user_data(uxi::tunnel_data tunnel_data);
  endfunction : user_data

endclass: Tunneled_Response
