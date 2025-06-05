//////////////////////////////////
//
// global defines/parameters for tcp/ip block
//
/////////////////////////////////
`ifndef __R_DEFINES__
`define __R_DEFINES__ 1

`ifdef __CADENCE__
`define __SIMULATION__
`define SIMULATION  1           // adjust reset sequence
`endif
`ifdef __XILINX__
`define __SIMULATION__
`define SIMULATION  1           // adjust reset sequence
`endif

//`define MARK_DEBUG_BER          (* mark_debug = "true" *)(* dont_touch = "true" *)
//`define MARK_DEBUG_I2C          (* mark_debug = "true" *)(* dont_touch = "true" *)

// basic axis stream
interface AXIS64 ;
    logic           Valid;
    logic           Ready;
    logic   [63:0]  Data;
    logic   [7:0]   Keep;
    logic           Last;

    modport m (output Valid,Data,Keep,Last, input Ready);
    modport s (input Valid,Data,Keep,Last, output Ready);
    modport t (input Valid,Data,Keep,Last, input Ready);
endinterface

// stream with user field (one bit)
interface AXIS64u ;
    logic           Valid;
    logic           Ready;
    logic   [63:0]  Data;
    logic   [7:0]   Keep;
    logic           Last;
    logic			User;

    modport m (output Valid,Data,Keep,Last,User, input Ready);
    modport s (input Valid,Data,Keep,Last,User, output Ready);
    modport t (input Valid,Data,Keep,Last, input Ready);
endinterface


// local bus 16-bit
interface BUS16 ;
    logic           Done;
    logic   [1:0]  	WriteEnable;
    logic           ReadEnable;
    logic   [15:0]  Address;
    logic   [15:0]  WriteData;
    logic   [15:0]  ReadData;

    modport m (input Done, ReadData, output WriteEnable, ReadEnable, Address, WriteData);
    modport s (output Done, ReadData, input WriteEnable, ReadEnable, Address, WriteData);
    modport t (input Done, ReadData, input WriteEnable, ReadEnable, Address, WriteData);
endinterface

`endif

