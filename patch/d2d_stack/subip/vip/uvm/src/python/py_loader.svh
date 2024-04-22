//Function to invoke python interpreter
import "DPI-C" pure function void init_py(string sv_caller_name,string python_path, string py_script);
import "DPI-C" pure function void terminate_py(string script_name="");
import "DPI-C" context task py_invoke_func(string script_name, string func="main");

//Generic functions
import "DPI-C" getenv = function string get_env_var(input string env_name);
import "DPI-C" context function bit py_is_ral_stim_complete();

// These functions can be imported from ML library eventually
export "DPI-C" task sv_interactive;
export "DPI-C" function sv_get_time;
export "DPI-C" task sv_wait_time;
////

task sv_interactive(bit suspend_simulation);
    if(suspend_simulation) begin
        $display("Suspending simulation to enter UCLI mode");
        $stop;
    end
endtask

function int sv_get_time();
    return int'($time);
endfunction

task sv_wait_time(longint wait_t);
    #(wait_t);
endtask


class py_loader extends uvm_component;
    `uvm_component_utils(py_loader)

    static bit invoked_modules[string];

    function new(string name="py_loader",uvm_component parent);
        super.new(name,parent);
    endfunction

    static  py_loader py_singleton;

    static function py_loader get();
        return py_singleton;
    endfunction

    static function py_loader init(uvm_component parent, string python_script_dir, string python_script);
        string python_script_path;
        if(py_singleton==null) begin
            py_singleton = new("py_loader",parent);
        end

        python_script_path = {python_script_dir,"/",python_script};
        if(python_script=="" || python_script_dir=="") begin
            uvm_pkg::uvm_report_error("UVMPyLoader/ERR",$sformatf("Incomplete Python script path : %s", python_script_path));
            return null;
        end
        uvm_pkg::uvm_report_info("UVMPyLoader",$sformatf("Starting python script ::\n Script = %s.py \n Time   = %0t",python_script_path,$time), UVM_MEDIUM);
        init_py(`__FILE__,python_script_dir,python_script);
        invoked_modules[python_script]=1;
        return py_singleton;
    endfunction


    function bit invoke_py_func(string script_name, string python_func="main", uvm_object return_val=null);
        if (invoked_modules[script_name]==1)  begin
            `uvm_info("", $sformatf("Invoking python function [%s] from script [%s].", python_func, script_name), UVM_LOW)
            fork
               py_invoke_func(script_name, python_func);
            join_none 
            return 1;
        end else begin
            `uvm_warning("UVMPyLoader", $sformatf("Cannot invoke python function [%s] from script [%s] since no there is no active Python module of that name. Launch python script using py_loader::init() before invoking python function", python_func, script_name))
            return 0;
        end

    endfunction
    
    task invoke_py_task(string script_name,string python_func="main", uvm_object return_val=null);
        if (invoked_modules[script_name]==1)  begin
            `uvm_info("", $sformatf("Invoking python function [%s] from script [%s].", python_func, script_name), UVM_LOW)
            py_invoke_func(script_name,python_func);
            return;
        end else begin
            `uvm_warning("", $sformatf("Cannot invoke python function [%s] from script [%s] since no there is no active Python module of that name. Launch python script using py_loader::init() before invoking python function", python_func, script_name))
            return;
        end

    endtask


    function void terminate_py_interpreter(string script_name="");
        if (invoked_modules[script_name]==1) begin
            `uvm_info(get_name(), $sformatf("Terminating python interpreter for script [%s]",script_name), UVM_LOW)
            terminate_py(script_name);
            invoked_modules[script_name]=0;
        end else
            `uvm_info(get_name(), $sformatf("No python interpreter is active for script [%s]. Ignoring %m", script_name), UVM_LOW)
    endfunction

    // If any outstanding python script is not terminated, then terminate it in final phase
    function void final_phase(uvm_phase phase);
        int active_py_modules=0;
        super.final_phase(phase);
        foreach(invoked_modules[i])
            active_py_modules += invoked_modules[i];
        `uvm_info("", $sformatf("There are [%0d] active python modules in uvm_final_phase. Terminating them all.", active_py_modules), UVM_MEDIUM)
        if (active_py_modules>0)
            foreach(invoked_modules[s])
                terminate_py_interpreter(s);
    endfunction : final_phase


endclass : py_loader

