
// msv_voltage_gen.sv originally extended by Dave Purvis from uvm_ams.sv provided by Synopsys, copyright for original material is as follows:
//-----------------------------------------------------------------------------
// This confidential and proprietary software may be used only as authorized
// by a licensing agreement from Synopsys Inc. In the event of publication,
// the following notice is applicable:
//
// (C) COPYRIGHT 2013 SYNOPSYS INC.  ALL RIGHTS RESERVED
//
// The entire notice above must be reproduced on all authorized copies.
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
//
// SV-AMS Source Generators
//
//-----------------------------------------------------------------------------

////////////////////////////////////////////////////////////
`ifndef _MSV_VOLTAGE_GEN_SV
`define _MSV_VOLTAGE_GEN_SV

`define _MSV_REPORT(a,b) \
        `msvxvm_info(a, b, `MSVXVM_HIGH)


////////////////////////////////////////////////////////////
// Class: msv_generic_src
//
//    The <msv_generic_src> virtual class provides the foundation for
//    implementing AMS source generators, such as voltage or current injectors.
//
//    It is *virtual* and should be *extended*.
//
//    Note that it can be used for implementing custom source generators

virtual class msv_generic_src extends `msvxvm_driver #(sv_ams_real);

    // class variables
    // set WIDTH to 1 as voltage sources are only set up for 1 output
    protected virtual ams_src_if #(1) /*.drive*/ aif; //AK: modport gives VCS issues
    `msvxvm_seq_item_pull_port #(sv_ams_real) msv_pull_port;

    // Knobs (to be replaced or augmented by autoknobs)
    string S_intf_name = "ams_src_if";          // name of interface to get from the config DB

    // Real: v
    //   Holds the analog value of <msv_generic_src> object.
    //   This member is aimed at retaining a  voltage node.
    //   This member is supposed to be updated by the <get_voltage> method
    rand sv_ams_real v;

    // Real: v_min
    //   Holds the minimum voltage of <msv_generic_src> object
    sv_ams_real v_min;

    // Real: v_max
    //   Holds the maximum voltage of <msv_generic_src> object
    sv_ams_real v_max;

    real accuracy;
    real last_time;
    real half_period=999999999999.9;
    real time_precision=1.0E-12;

    // Function: new
    //
    // The <new> function is used to construct <msv_generic_checker> object derivatives.
    //
    // Arguments:
    //  - *name* defines the transactor instance name
    //  - *parent* defines the transactor parent
    function new(string name="", `msvxvm_component parent=null);
        super.new(name, parent);
        this.v = new();
        msv_pull_port = new("msv_pull_port", this);
    endfunction

    function void connect();
        string tmp_name ;
        `msvxvm_object temp ;
        msv_vif_container #(virtual ams_src_if#(1)) _ams_src_if ;

        super.connect();

        // retrieve a virtual interface from the resource database by name.
        tmp_name = S_intf_name ;
       // if (! get_config_object(tmp_name, temp)) begin
        if (! uvm_config_db#(uvm_object)::get(null, tmp_name, "config", temp)) begin     
            `msvxvm_fatal(get_name(), $psprintf("Could not find an interface named %s!", tmp_name))
        end
        $cast(_ams_src_if, temp);
        this.aif = _ams_src_if.get_v_if();
    endfunction

    // Function: set_time_precision
    //
    //  This function sets the time precision of the source generator.
    //  It must be called to ensure the source generator time precision
    //  is consistent with its enclosing module/class.
    //
    // Arguments:
    // - *p* defines the time precision in second, you should constants as defined in <msv_units>
    //   such as <msv_units::one_us> for 1us, etc.
    //
    //  Following examples shows how to construct a <msv_sawtooth_voltage_gen>
    //  object that extends <msv_generic_src>. Since the module time precision
    //  is changed to 1us, the <set_time_precision> is called with a value of 1E-6.
    //
    //| `timescale 1us/1ns
    //| module top;
    //|   // Construct a sawtooth generator that ranges between -1.25V to +1.25V at 2.5MHz
    //|   msv_sawtooth_voltage_gen saw_gen = new(-1.25, +1.25, 2.5E3);
    //|   initial begin
    //|      saw_gen.set_time_precision(msv_units::one_us);
    //|   end
    //| endmodule
    //|
    virtual function void set_time_precision(real p);
        this.time_precision = p;
    endfunction

    // Function: set_v_range
    //
    //  This function sets the min/max voltages of the source generator.
    //  It can be called to override the default min/max voltages that are passed during
    //  the source generator construction
    //
    // Arguments:
    // - *min* defines the min voltage of the source generator. It is expressed in V
    // - *max* defines the max voltage of the source generator. It is expressed in V
    //
    virtual function void set_v_range(real v_min, real v_max);
      `ifdef UVM_SV_REAL_COMPAT_MODE
        this.v_min = new(v_min,this.accuracy);
        this.v_max = new(v_max,this.accuracy);
        this.v = new(0.0);
      `else
        this.v_min = new("v_min",v_min,this.accuracy);
        this.v_max = new("v_max",v_max,this.accuracy);
        this.v = new("",0.0);
      `endif
    endfunction

    // Function: get_v_range
    //
    //  This function returns the min/max voltages of the source generator.
    //
    // Arguments:
    // - *min* returns the min voltage of the source generator. It is expressed in V
    // - *max* returns the max voltage of the source generator. It is expressed in V
    //
    virtual function void get_v_range(output real min, output real max);
        min = this.v_min.get_real();
        max = this.v_max.get_real();
    endfunction

    // Function: get_time
    //
    //  This function returns the current simulator time (in s).
    //  Note that it is factored with the simulator time precision that
    //  can be overriden with the <set_time_precision> function
    //
    virtual function real get_time();
        return ($realtime - this.last_time) * this.time_precision;
    endfunction

    // Function: set_half_period
    //
    //  This function sets the source generator half period.
    //  You simply need to pass the source generator frequency
    //
    // Arguments:
    // - *f* defines the source generator frequency. It is expressed in Hz
    //
    virtual function real set_half_period(real f);
        this.half_period = 0.5 / (f*time_precision);
    endfunction

    // Function: get_half_period
    //  This function returns the source generator half period (in s).
    virtual function real get_half_period();
        return half_period;
    endfunction

    // Function: reset
    //  This function reset the source generator.
    //  This is necessry when the source generator paramenters have been
    //  modified or when it has been stopped before
    virtual function void reset();
        this.last_time = $realtime;
    endfunction

    // Function: get_voltage
    //
    //  This function returns the source voltage generator (in V).
    //  It should be overwritte with the source generator equation
    virtual function real get_voltage();
        return this.v.get_real();
    endfunction

    virtual task run();
        real v;
        fork
            while(1) begin
                @(this.aif.dck);
                v = get_voltage();
                this.aif.dck.v[0] <= v;
                `_MSV_REPORT(get_full_name(), $psprintf("Driving V=%f", this.aif.v[0]))
            end
        join_none
    endtask

endclass

////////////////////////////////////////////////////////////
// Class: msv_rand_voltage_gen
//
//  The <msv_rand_voltage_gen> class provides
//  constrained random generation
//  of real value that can be used to drive analog signals
//
//  It is a parameterized class with following parameters
//    - VMIN: Min random voltage value (default=0V)
//    - VMAX: Max random voltage value (default=1V)
//    - ACC:  Accuracy (default=1mV)
//      This parameter can be used to determine the internal
//      accuracy used for converting real to integer in the underlying <sv_ams_real>
//
class msv_rand_voltage_gen #(real VMIN=0.0,
                             real VMAX=1.0,
                             real ACC=`SV_AMS_REAL_DEF_ACCURACY)
    extends msv_generic_src;

    `msvxvm_component_param_utils_begin(msv_rand_voltage_gen#(VMIN, VMAX, ACC))
        `msvxvm_field_string(S_intf_name,       `MSVXVM_ALL_ON)
    `msvxvm_component_utils_end

    static string class_name = "Rand";

    //////////////////////////////////////////////////////
    // Function: new
    //
    // The <new> function is used to construct <msv_rand_voltage_gen> objects.
    //
    // Arguments:
    //  - *name* defines the transactor instance name
    //  - *parent* defines the transactor parent
    function new(string name="", `msvxvm_component parent=null);
        super.new(name, parent);
        this.v_min = new("0");//VMIN);
        this.v_max = new("1");//VMAX);
        this.accuracy =ACC;
    endfunction

    // Function: get_voltage
    //
    //  This function returns the random voltage generator (in V).
    //  The voltage is randomly generated to provide a value that is
    // comprised betwen *v_min* and *v_max*.
    virtual function real get_voltage();
        this.randomize();
        `_MSV_REPORT(class_name, $psprintf("Driving V=%f", this.v.get_real()))
        return this.v.get_real();
    endfunction

    constraint volt_range {
        this.v.i >= this.v_min.i;
        this.v.i <= this.v_max.i;
    }

endclass

////////////////////////////////////////////////////////////
// Class: msv_sawtooth_voltage_gen
//
//  The <msv_sawtooth_voltage_gen> class provides generation
//  of sawtooth-like real value that can be used to drive analog signals

class msv_sawtooth_voltage_gen #(real VMIN=0.0,
                                 real VMAX=1.0,
                                 real F=1.0E6,
                                 real ACC=`SV_AMS_REAL_DEF_ACCURACY)
    extends msv_generic_src;

    `msvxvm_component_param_utils_begin(msv_sawtooth_voltage_gen#(VMIN, VMAX, F, ACC))
        `msvxvm_field_string(S_intf_name,       `MSVXVM_ALL_ON)
    `msvxvm_component_utils_end

    static string class_name = "Sawtooth";

    local real vdd;
    local real delta;


    //////////////////////////////////////////////////////
    // Function: new
    //
    // The <new> function is used to construct <msv_sawtooth_voltage_gen>
    // objects.
    //
    // Arguments:
    //  - *name* defines the transactor instance name
    //  - *parent* defines the transactor parent
    function new(string name="", `msvxvm_component parent=null);
        super.new(name, parent);
        this.v_min = new("0");//VMIN);
        this.v_max = new("1");//VMAX);
        this.accuracy =ACC;
        this.set_frequency(F);
    endfunction

    // Function: get_voltage
    //
    //  This function returns the voltage of the _sawtooth_ generator (in V).
    //  The voltage is generated to provide a value that is
    //  comprised betwen *v_min* and *v_max* to follow a _sawtooth_ shape
    //  at a given frequency
    virtual function real get_voltage();
        real r = fmod(this.get_time() * delta, vdd) + this.v_min.get_real();
        this.v.set_real(r);
        `_MSV_REPORT(class_name, $psprintf("Driving V=%f", this.v.get_real()))
        return r;
    endfunction

    // Function: set_frequency
    //
    // The <set_frequency> function can
    // be used to change the sawtooth voltage generator frequency
    //
    // Arguments:
    // - *f* defines the new sawtooth voltage generator frequency
    virtual function void set_frequency(real f);
        this.vdd = this.v_max.get_real() - this.v_min.get_real();
        this.delta = this.vdd * f;
        this.set_half_period(f);
    endfunction


    // Function: set_v_range
    //
    //  This function sets the min/max voltages of the sawtooth source generator.
    //  It can be called to override the default min/max voltages that are passed during
    //  the source generator construction
    //
    // Arguments:
    // - *min* defines the min voltage of the source generator. It is expressed in V
    // - *max* defines the max voltage of the source generator. It is expressed in V
    //
    virtual function void set_v_range(real v_min, real v_max);
        super.set_v_range(v_min, v_max);
        this.vdd = this.v_max.get_real() - this.v_min.get_real();
    endfunction

endclass

////////////////////////////////////////////////////////////
// Class: msv_sine_voltage_gen
//
//  The <msv_sine_voltage_gen> class provides generation
//  of _sine-like_ real value that can be used to drive analog signals

class msv_sine_voltage_gen #(real VMIN=0.0,
                             real VMAX=1.0,
                             real F=1.0E6,
                             real ACC=`SV_AMS_REAL_DEF_ACCURACY)
    extends msv_generic_src;

    `msvxvm_component_param_utils_begin(msv_sine_voltage_gen#(VMIN, VMAX, F, ACC))
        `msvxvm_field_string(S_intf_name,       `MSVXVM_ALL_ON)
    `msvxvm_component_utils_end

    static string class_name = "Sine";
    local real omega;
    local real v_mid;
    local real last_phase;

    //////////////////////////////////////////////////////
    // Function: new
    //
    // The <new> function is used to construct <msv_sine_voltage_gen>
    // objects.
    //
    // Arguments:
    //  - *name* defines the transactor instance name
    //  - *parent* defines the transactor parent
    function new(string name="", `msvxvm_component parent=null);
        super.new(name, parent);
        this.v_min = new;
        this.v_max = new;
        this.accuracy = ACC;
        this.set_v_range(VMIN, VMAX);
        this.set_frequency(F);
        this.last_phase = 0.0;
    endfunction

    function real get_phase();
        return fmod(omega*this.get_time(),msv_const::TWO_PI);
    endfunction

    // Function: get_voltage
    //
    //  This function returns the voltage of _sine_ generator (in V).
    //  The voltage is generated to provide a value that is
    // comprised betwen *v_min* and *v_max* with a _sine_ shape at a given frequency *f*
    virtual function real get_voltage();
        real phase = get_phase() - this.last_phase;
        real r = (1+sin(phase))*v_mid+this.v_min.get_real();
        this.v.set_real(r);
        `_MSV_REPORT(class_name, $psprintf("Driving V=%f Ph=%f V=%f-%f", this.v.get_real(), phase, v_min.get_real(), v_mid))
        return r;
    endfunction

    // Function: set_frequency
    //
    // The <set_frequency> function changes the _sine_ generator frequency
    //
    // Arguments:
    // - *f* defines the new _sine_ generator frequency
    virtual function void set_frequency(real f);
        real phase = fmod(get_phase() - this.last_phase, msv_const::TWO_PI);
        this.omega = msv_const::TWO_PI*f;
        this.set_half_period(f);
        this.last_phase = fmod(get_phase() - phase, msv_const::TWO_PI);
    endfunction

    // Function: set_v_range
    //
    //  This function sets the min/max voltages of the _sine_ source generator.
    //  It can be called to override the default min/max voltages that are passed during
    //  the source generator construction
    //
    // Arguments:
    // - *min* defines the min voltage of the source generator. It is expressed in V
    // - *max* defines the max voltage of the source generator. It is expressed in V
    //
    virtual function void set_v_range(real v_min, real v_max);
        super.set_v_range(v_min, v_max);
        this.v_mid = (v_max-v_min)/2.0;
    endfunction

endclass

////////////////////////////////////////////////////////////
// Class: msv_square_voltage_gen
//
//  The <msv_square_voltage_gen> class provides generation
//  of _square-like_ real value that can be used to drive analog signals

class msv_square_voltage_gen #(real VMIN=0.0,
                               real VMAX=1.0,
                               real F=1.0E6,
                               real DUTY=0.5,
                               real ACC=`SV_AMS_REAL_DEF_ACCURACY)
    extends msv_generic_src;

    `msvxvm_component_param_utils_begin(msv_square_voltage_gen#(VMIN, VMAX, F, DUTY, ACC))
        `msvxvm_field_string(S_intf_name,       `MSVXVM_ALL_ON)
    `msvxvm_component_utils_end

    static string class_name = "Square";

    local real omega;
    local real v_mid;
    local real theta;

    //////////////////////////////////////////////////////
    // Function: new
    //
    // The <new> function is used to construct <msv_square_voltage_gen>
    // objects.
    //
    // Arguments:
    //  - *name* defines the transactor instance name
    //  - *parent* defines the transactor parent
    function new(string name="", `msvxvm_component parent=null);
        super.new(name, parent);
        this.v_min = new;
        this.v_max = new;
        this.accuracy = ACC;
        this.set_v_range(VMIN, VMAX);
        this.set_frequency(F,DUTY);
    endfunction

    function real sgn(real a);
        sgn=(a==0)?0:(a<0)?-1:+1;
    endfunction

    // Function: get_voltage
    //
    //  This function returns the _square_ voltage generator (in V).
    //  The voltage is generated to provide a value that is
    // comprised betwen *v_min* and *v_max* with a _square_ shape at a
    // given frequency *f* and duty cycle *duty*.
    virtual function real get_voltage();
        real r = (1+sgn(sin(omega*this.get_time())-sin(theta)))*v_mid +
        this.v_min.get_real();
        this.v.set_real(r);
        `_MSV_REPORT(class_name, $psprintf("Driving V=%f V=%f", this.v.get_real(), r))
        return r;
    endfunction

    // Function: set_frequency
    //
    // The <set_frequency> function changes
    // the frequency of the square voltage generator
    //
    // Arguments:
    // - *f* defines the new _square_ voltage generator frequency
    virtual function void set_frequency(real f, real duty);
        this.omega = msv_const::TWO_PI*f;
        this.theta = (duty == 0.5)? 0 : (duty <0.5)?msv_const::PI*(0.5-duty):msv_const::PI*(0.5+duty);
        this.set_half_period(f);
    endfunction

    // Function: set_v_range
    //
    //  This function sets the min/max voltages of the _square_ voltage generator.
    //  It can be called to override the default min/max voltages that are passed during
    //  the source generator construction
    //
    // Arguments:
    // - *min* defines the min voltage of the source generator. It is expressed in V
    // - *max* defines the max voltage of the source generator. It is expressed in V
    //
    virtual function void set_v_range(real v_min, real v_max);
        super.set_v_range(v_min, v_max);
        this.v_mid = (v_max-v_min)/2.0;
    endfunction

endclass

`endif // _MSV_VOLTAGE_GEN_SV
