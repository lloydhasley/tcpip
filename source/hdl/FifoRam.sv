///////////////////////////////////////
//
// Vanilla RAM definition
//
///////////////////////////////////////

`timescale 1 ns / 10 ps
`include "Defines.svh"


module FifoRam #(
    parameter SIZE = 512,
    parameter WIDTH = 64,
    //
    parameter SBITS1 = $clog2(SIZE)-1
)(
    input                       clk,
    input                       wen,
    input           [SBITS1:0]  waddr,
    input           [WIDTH-1:0] wdata,
    input                       ren,
    input           [SBITS1:0]  raddr,
    output  logic   [WIDTH-1:0] rdata
);
logic   [WIDTH-1:0]  RAM [0:SIZE];
logic   [WIDTH-1:0]     readdata;


always_ff @(posedge clk)
    if(wen)
        RAM[waddr] <= wdata;
        
always_ff @(posedge clk)
    readdata <= RAM[raddr];

assign rdata = readdata;        
endmodule















endmodule



