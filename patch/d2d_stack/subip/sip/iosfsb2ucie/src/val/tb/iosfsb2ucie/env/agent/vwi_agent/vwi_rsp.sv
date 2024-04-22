//   `include "iosfsb2ucie_defines.vh"
class vwi_rsp extends uvm_sequence_item;
    `uvm_object_utils(vwi_rsp)
    bit [`V_WIRES_OUT-1:0] b_async_virt_out;

    function new(string name = "vwi_rsp");
        super.new(name);
    endfunction: new

    virtual function string convert2string();
        return $psprintf("virtual_in value: %b", b_async_virt_out );
    endfunction: convert2string

    virtual function void do_copy (uvm_object rhs);
        vwi_rsp rhs_1;
        if(!$cast(rhs_1, rhs)) begin
            uvm_report_error("do_copy:", "Cast failed");
            return;
        end
        super.do_copy(rhs);
        b_async_virt_out = rhs_1.b_async_virt_out;
    endfunction: do_copy    

    virtual function bit do_compare (uvm_object rhs, uvm_comparer comparer);
        vwi_rsp rhs_2;
        if(!$cast(rhs_2, rhs)) begin
            uvm_report_error("do_compare:", "Cast failed");
            return 0; //cbb hotfix
        end else begin
           return ((super.do_compare(rhs_2, comparer)) && (b_async_virt_out == rhs_2.b_async_virt_out));
	end
    endfunction: do_compare 
endclass
