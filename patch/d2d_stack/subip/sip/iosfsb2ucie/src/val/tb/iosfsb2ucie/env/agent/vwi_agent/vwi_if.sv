//   `include "iosfsb2ucie_defines.vh"
interface vwi_if(
output logic [`V_WIRES_IN-1:0] async_virt_in,
input logic [`V_WIRES_IN-1:0]  async_virt_in_s,
input logic [`V_WIRES_OUT-1:0] async_virt_out,
input logic [`V_WIRES_IN-1:0] strap_default_wires_in,
input logic [`V_WIRES_IN-1:0] strap_default_wires_out,
input logic        d2d_sb_clk,
input logic        async_clk,
input logic        ip_ready,
input logic [`MAX_LANES-1:0] tb_reset);
/*
   modport dut_signal ( 
       input async_virt_in,
       output async_virt_out

   modport tb_signal ( 
       output async_virt_in,
       input async_virt_out
       );
*/

//   assign async_virt_out = async_virt_in;

endinterface   
