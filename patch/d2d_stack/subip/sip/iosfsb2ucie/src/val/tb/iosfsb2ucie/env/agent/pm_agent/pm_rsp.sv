//   `include "iosfsb2ucie_defines.vh"
class pm_rsp extends uvm_sequence_item;
    `uvm_object_utils(pm_rsp)
	bit dvp_qch_active;
	bit dvp_qch_accept;
	bit dvp_qch_deny;

    function new(string name = "pm_rsp");
        super.new(name);
    endfunction: new

    function string convert2string();
        return $psprintf("qch active signal value: %b", dvp_qch_active );
        return $psprintf("qch accept signal value: %b", dvp_qch_accept );
        return $psprintf("qch deny signal value: %b", dvp_qch_deny );
    endfunction: convert2string

    function void copy (uvm_object rhs);                 
        pm_rsp rhs_1;
        if(!$cast(rhs_1, rhs)) begin
            uvm_report_error("do_copy:", "Cast failed");
            return;
        end
        super.copy(rhs);
        dvp_qch_active = rhs_1.dvp_qch_active;
        dvp_qch_accept = rhs_1.dvp_qch_accept;
        dvp_qch_deny = rhs_1.dvp_qch_deny;
    endfunction: copy    

    function bit compare (uvm_object rhs, uvm_comparer comparer);
        pm_rsp rhs_2;
        if(!$cast(rhs_2, rhs)) begin
            uvm_report_error("compare:", "Cast failed");
            return 0; //cbb hotfix
        end else begin
           return ((super.compare(rhs_2, comparer) && (dvp_qch_active == rhs_2.dvp_qch_active) && (dvp_qch_accept == rhs_2.dvp_qch_accept) && (dvp_qch_deny == rhs_2.dvp_qch_deny)));
	end
    endfunction: compare

endclass
