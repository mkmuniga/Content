///=====================================================================================================================
///
/// Primary Contact:
/// Creation Date:
/// Last Review Date:
///
/// Copyright (c) 2013-2014 Intel Corporation
/// Intel Proprietary and Top Secret Information
///---------------------------------------------------------------------------------------------------------------------
/// Description:
/// include macrose for VIP Layering
///=====================================================================================================================
`ifndef VIP_LAYERING_MACROS_SVH
  `define VIP_LAYERING_MACROS_SVH

// Typical layer inheriate MID layer
  `ifdef IP_TYP_TE
    `ifndef IP_MID_TE
      `define IP_MID_TE
    `endif
  `endif

// BASE layer import package
// Base layer code not enclose with layer define macro
// This macro is for uniform coding and optional future needs
  `define import_base(_pkg) \
import _pkg;

// MID layer import macro
  `define import_mid(_pkg) \
  `ifdef IP_MID_TE \
import _pkg; \
  `endif

// TYP layer import macro
  `define import_typ(_pkg) \
  `ifdef IP_TYP_TE \
import _pkg; \
  `endif

// BASE layer include file
// Base layer code not enclose with layer define macro
// This macro is for uniform coding and optional future needs
  `define include_base(_file) \
  `include _file

// MID layer include file
  `define include_mid(_file) \
  `ifdef IP_MID_TE \
    `include _file \
  `endif

// TYP layer include file
  `define include_typ(_file) \
  `ifdef IP_TYP_TE \
    `include _file \
  `endif


// Explictly decrale top environment type of the used layer
// This macro should be called in test declaration part
  `define declare_top_env(_name) \
  `ifdef IP_TYP_TE \
_name``_typ_env env; \
  `elsif IP_MID_TE \
_name``mid_env env; \
  `else \
_name``_env env; \
  `endif \

// Explictly create top environment type of the used layer
// This macro should be called from test build phase
// Example:
// class my_test ovm_test;
//     `declare_top_env(my_ip)
//
//     function void build();
//         `create_top_env(my_ip)
//     endfunction
// endclass
  `define create_top_env(_name, _instname="env", _parent=this) \
  `ifdef IP_TYP_TE \
env = _name``_typ_env::type_id::create(_instname, _parent); \
  `elsif IP_MID_TE \
env = _name``mid_env::type_id::create(_instname, _parent); \
  `else \
env = _name``_env::type_id::create(_instname, _parent); \
  `endif

// Control creation of BASE, MID, TYP sla_tb_env using ovm factory
// Using factory to implicily create the derived layer may required the
// use of "get_top_env_ptr" macro to access class memebr of the derived
// class
  `define override_top_env(_name) \
  `ifdef IP_TYP_TE \
factory.set_type_override_by_name(`"``_name``_env`", `"``_name``_typ_env`", 1);\
  `elsif IP_MID_TE \
factory.set_type_override_by_name(`"``_name``_env`", `"``_name``_mid_env`", 1);\
  `endif

  `define static_factory_override_mid(_newclass, _oldclass) \
  `ifndef IP_TYP_TE \
    `ifdef IP_MID_TE \
class _newclass``_registrar; \
    static _newclass``_registrar registrar = new; \
    function new(); \
        _oldclass::type_id::set_type_override(_newclass::get_type()); \
    endfunction : new \
endclass \
    `endif \
  `endif
  `define static_factory_override_typ(_newclass, _oldclass) \
  `ifdef IP_TYP_TE \
class _newclass``_registrar; \
    static _newclass``_registrar registrar = new; \
    function new(); \
        _oldclass::type_id::set_type_override(_newclass::get_type()); \
    endfunction : new \
endclass \
  `endif


// get top SAOLA environment pointer of the used layer BASE, MID, TYP
// This should be use when using layer factory override (override_top_env)
// when there is a need to access the derived layred class members
// Should be use only form the non resusable code (tests)
// Example use with override_top_env
// class my_ip_base_test extends ovm_test;
//     my_ip_env env;
//
//     function void build();
//         `override_top_env(my_ip)
//         env = my_ip_env::type_id::create("env",this);
//     endfunction
// endclass
//
// In a derived layer test (as an example typical)
// class my_typ_test extends my_ip_base_test
//    function void connect();
//        super.connect();
//        // Accessing typ fields will restrict the test to the typical layer
//        get_top_env_ptr(my_ip).typ_class_member;
//    endfunction
// endclass
  `define get_top_env_ptr(_name) \
  `ifdef IP_TYP_TE \
_name``_typ_env``::get_ptr()\
  `elsif IP_MID_TE \
_name``_mid_env``::get_ptr()\
  `else\
_name``_env``::get_ptr()\
  `endif

// When get pointer function name is in the format "get_ipname_layer_env"
// It is recomended to replace all function to "get_ptr" and use "get_top_env_ptr" macro
  `define get_top_env_nptr(_name) \
  `ifdef IP_TYP_TE \
_name``_typ_env``::get_``_name``_typ_env()\
  `elsif IP_MID_TE \
_name``_mid_env``::get_``_name``_mid_env()\
  `else\
_name``_env``::get_``_name``_env()\
  `endif



//******************************
// Start of save/restore macros from UBOX team
//******************************

// write a string to file
`define write_info(FD, STR) $fwrite(FD, "%s", STR );

// scan a standard line from a file.
`define scan_info(FD, VAR, VAR_FMT) \
    begin \
        int cnt=$fscanf(FD, `"VAR = VAR_FMT`", VAR); \
        if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR didn't match any record`")); \
    end

// scanning a static array from a file.
`define scan_STATIC_ARR_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE=int unsigned) \
    begin \
        int size__; \
        int cnt; \
        cnt = $fscanf(FD, `"VAR.size() = %d`", size__); \
        if(cnt < 1) $display("WARNING- ", get_name(), $sformatf("`VAR.size() didn't match any record`")); \
        for(int unsigned t = 0; t < size__; t++) begin \
            INDEX_TYPE idx; \
            TYPE val; \
            cnt = $fscanf(FD, `"VAR[%d] = VAR_FMT`", idx, val); \
            if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR didn't match any record`")); \
            VAR[idx] = val; \
        end \
    end

// scan a HASH/associate array from a file.
`define scan_HASH_array_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE) `scan_STATIC_ARR_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE)

// scan a dynamic array from a file.
`define scan_DYN_ARR_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE=int unsigned) \
    begin \
        int size__; \
        int cnt; \
        cnt = $fscanf(FD, `"VAR.size() = %d`", size__); \
        if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR.size() didn't match any record`")); \
        VAR = new[size__]; \
        for(int unsigned t = 0; t < size__; t++) begin \
            INDEX_TYPE idx; \
            TYPE val; \
            cnt = $fscanf(FD, `"VAR[INDEX_TYPE] = VAR_FMT`", idx, val); \
            if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR didn't match any record`")); \
            VAR[idx] = val; \
        end \
    end

// scan a queue from a file.
`define scan_Q_ARR_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE=int unsigned) \
    begin \
        int size__; \
        int cnt; \
        cnt = $fscanf(FD, `"VAR.size() = %d`", size__); \
        if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR.size() didn't match any record`")); \
        VAR = {}; \
        for(int unsigned t = 0; t < size__; t++) begin \
            INDEX_TYPE idx; \
            TYPE val; \
            cnt = $fscanf(FD, `"VAR[%d] = VAR_FMT`", idx, val); \
            if(cnt < 1) $display("WARNING- ", get_name(), $sformatf(`"VAR didn't match any record`")); \
            VAR.push_back(val); \
        end \
    end


`define save_native_data_type_info(VAR, VAR_FMT,FD=fd) \
    begin \
        string s; \
        s = {s, $sformatf(`"VAR = VAR_FMT\n`",VAR)}; \
        `write_info(FD, s) \
    end

`define restore_native_data_type_info(VAR, VAR_FMT,FD) `scan_info(FD, VAR, VAR_FMT)

`define save_enum_type_info(VAR, VAR_FMT=%d,FD=fd) \
    begin \
        string s; \
        s = {s, $sformatf(`"VAR = VAR_FMT\n`",VAR)}; \
        `write_info(FD, s) \
    end
`define restore_enum_type_info(VAR,VAR_FMT=%d,FD) `restore_native_data_type_info(VAR, VAR_FMT,FD)


`define save_DYN_ARR_info(TYPE, VAR, VAR_FMT,INDEX_FMT=%d, FD=fd) \
    begin \
        string s; \
        s = {s, $sformatf(`"VAR.size() = %d\n`", VAR.size())}; \
        foreach(VAR[i]) begin \
            s = {s, $sformatf(`"VAR[INDEX_FMT] = VAR_FMT\n`",i, VAR[i])}; \
        end \
        `write_info(FD,s) \
    end


`define save_STATIC_ARR_info(VAR, VAR_FMT,INDEX_FMT=%d,FD=fd) \
    begin \
        string s; \
        s = {s, $sformatf(`"VAR.size() = %d\n`", $size(VAR))}; \
        foreach(VAR[i]) begin \
            s = {s, $sformatf(`"VAR[INDEX_FMT] = VAR_FMT\n`",i, VAR[i])}; \
        end \
        `write_info(FD,s) \
    end


`define SR_Q_info(TYPE, VAR, VAR_FMT,INDEX_FMT=%d,FD=fd, SAVE=save) \
    if(SAVE) \
    `save_DYN_ARR_info(TYPE, VAR, VAR_FMT,INDEX_FMT,FD) \
    else \
    `scan_Q_ARR_info(FD, TYPE, VAR, VAR_FMT, int unsigned)


`define SR_HASH_info(TYPE,VAR,VAR_FMT,INDEX_TYPE,INDEX_FMT, FD=fd, SAVE=save) \
    if(SAVE) \
    `save_DYN_ARR_info(TYPE, VAR, VAR_FMT,INDEX_FMT,FD) \
    else \
    `scan_HASH_array_info(FD, TYPE, VAR, VAR_FMT, INDEX_TYPE)

`define SR_DYN_ARR_info(TYPE, VAR, VAR_FMT,FD=fd, SAVE=save) \
    if(SAVE) \
    `save_DYN_ARR_info(TYPE, VAR, VAR_FMT,INDEX_FMT,FD) \
    else \
    `scan_DYN_ARR_info(FD, TYPE, VAR, VAR_FMT, int unsigned)

`define SR_STATIC_ARR_info(TYPE, VAR, VAR_FMT, SIZE, FD=fd, SAVE=save) \
    if(SAVE) \
    `save_STATIC_ARR_info(VAR,VAR_FMT,%d, FD) \
    else \
    `scan_STATIC_ARR_info(FD, TYPE, VAR, VAR_FMT, int unsigned)


`define SR_native_data_type_info(VAR, VAR_FMT,FD=fd, SAVE=save) \
    if(SAVE) \
        `save_native_data_type_info(VAR, VAR_FMT,FD) \
    else \
        `restore_native_data_type_info(VAR, VAR_FMT, FD)

`define SR_enum_type_info(VAR, VAR_FMT=%d,FD=fd, SAVE=save) \
    if(SAVE) \
        `save_enum_type_info(VAR, VAR_FMT,FD) \
    else \
        `restore_enum_type_info(VAR, VAR_FMT, FD)

`define SR_INT_info(VAR, FD=fd, SAVE=save, VAR_FMT=%d) `SR_native_data_type_info(VAR, VAR_FMT, FD, SAVE)
`define SR_STRING_info(VAR, FD=fd, SAVE=save,VAR_FMT=%s) `SR_native_data_type_info(VAR, VAR_FMT, FD, SAVE)



`endif //VIP_LAYERING_MACROS_SVH
