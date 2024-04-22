// -*- mode: Verilog; verilog-indent-level: 3; -*-
//-----------------------------------------------------------------
// Intel Proprietary -- Copyright 2022 Intel -- All rights reserved
//-----------------------------------------------------------------
// Author       : 
// Date Created : Apr 2022
//-----------------------------------------------------------------
// Description:
// The uciedda uvm environment file. -- Base Layer -- Exported to SoC
//------------------------------------------------------------------

// VIP-Dieting: Base-Layer Environment. Light-weight and helps in compile time.
// Code should be added in this file only if it is absolutely required for consumption by SoC
// Most of the user components (such as checkers, sw mons) should go inside the typical layer env (uciedda_typ_env)

class uciedda_base_env extends uvm_env;

   // Handle to the uvm config-db object defined at the ss-level..
   uciedda_cfg   uciedda_cfg_h;

   // Inst-suffix: the unique instance suffix for the env.
    string inst_suffix;

   // variable that holds the top level rtl-path of the uciedda
    string ip_rtl_top_path;

   // Register the component into the UVM factory
   `uvm_component_utils_begin(uciedda_base_env)
      `uvm_field_object(uciedda_cfg_h, UVM_ALL_ON)
   `uvm_component_utils_end

   ///////////////////////////////////////////////////////////////////////////
   // Name : new()
   ///////////////////////////////////////////////////////////////////////////
   function new(string name = "uciedda_base_env", uvm_component parent = null);
      super.new(name, parent);
   endfunction : new

   ///////////////////////////////////////////////////////////////////////////
   // Name : build()
   ///////////////////////////////////////////////////////////////////////////
   function void build_phase(uvm_phase phase);

       super.build_phase(phase);

      // Obtain an existing cfg-object handle only in normal runs.
      // In TE_REPLAY runs, the cfg object should be created and restored from saved cfg-data file.
`ifdef UCIEDDA_TE_REPLAY
       uciedda_cfg_h = uciedda_cfg::type_id::create("uciedda_cfg_h");
       `uvm_info(get_name(), "Creating a new object of uciedda_cfg for replay that will be restored from saved cfg-data file", UVM_LOW)
       
`else
       // Make sure that the config-object is already created and passed down to the env.
       if(!uvm_config_db#(uciedda_cfg)::get(this,"", "uciedda_cfg", uciedda_cfg_h)) begin
           `uvm_fatal(get_name(), "uciedda_cfg not found in config_db")
       end
`endif

       // Get the INST_SUFFIX that is unique to this uciedda_base_env
       void'(uvm_config_string::get(this, "", "INST_SUFFIX", inst_suffix));

       if(inst_suffix == "") begin
           `uvm_fatal(get_name(), "INST_SUFFIX is not passed down to the uciedda_base_env.")
       end

      uvm_config_db#(string)::set(this, "*", "INST_SUFFIX", inst_suffix);
//cbb hotfix      set_config_string("*","INST_SUFFIX",inst_suffix); // for downstream components..

       save_restore();

       `uvm_info(get_name(), "UCIEDDA UVM Environment build completed", UVM_HIGH)
   endfunction : build_phase


   function void save_restore();

       string filename;

      if (!uvm_config_db#(string)::get(null , "*", "cfg_filename", filename)) begin
//cbb hotfix      if (!get_config_string("cfg_filename", filename)) begin
         filename = "./uciedda_cfg.data";
      end

      `uvm_info(get_name(), $sformatf("The file-name is : %s", filename), UVM_MEDIUM)

      // In-case if we in live-mode (not in replay), then
      // save the cfg-information to a file.
`ifndef UCIEDDA_TE_REPLAY

      save(filename);

      // In-case if we are in replay-mode, then restore the
      // cfg-information from the save file during the live simulation
`else

      restore(filename);

`endif

   endfunction : save_restore

   function void save(string filename);
      // Open file to append more info
       int fd = $fopen(filename, "a+");


      // Save Unique ID for IP (inst ID)
      $fdisplay(fd, "***UCIEDDA: %0s", inst_suffix);

      // Save cfg object
      uciedda_cfg_h.save_to_file(fd);

      $fclose(fd);
   endfunction : save

   function void restore(string filename);

       string uid, buff;
       int    code;
       int    fd = $fopen(filename, "r");

      if(!fd) begin
         `uvm_fatal(get_name(), $sformatf("Unable to get config-file location from: %s", filename))
      end

      // Fast forward in file to UID location
      void'(uvm_config_string::get(this, "", "uid", uid));
      `uvm_info(get_name(), $sformatf("Fast Forward to the location with UID: %s", uid), UVM_HIGH)

      uid = $sformatf("***UCIEDDA: %0s\n", uid);
      while($fgets(buff, fd) && buff != uid) begin 
      end 

      if ($feof(fd)) begin
         `uvm_error(get_name(), $sformatf("Couldn't find cfg restore record with uid %s", uid))
      end

      // Read in cfg obj data
      uciedda_cfg_h.restore_from_file(fd);

      $fclose(fd);

      `uvm_info(get_name(), "Saving the restored cfg-file as restored_uciedda_cfg.data in the replay run dir for debug", UVM_LOW)

      // The below call is a debug-hook which will be helpful
      // to check if the restore of the cfg-object has been successful.
      save("restored_uciedda_cfg.data");

   endfunction : restore

endclass : uciedda_base_env

