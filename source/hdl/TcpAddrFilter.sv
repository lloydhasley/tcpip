//
// tcp/ip echo responder
//


`timescale 1 ns / 10 ps
`include "Defines.svh"


module TcpAddrFilter (
	input				Clock,
	input				Reset,
	//
	Axis64.s 			AxisIn,
	Axis64.m 			AxisOut.
	//
	input		[47:0]	OurMacAddr
);

logic	TakenIn;			// data movement on AxisIn interface
logic	TakenOut;			// data movement on AxisOut interface
logic	First;				// next transfer is first word of a packet
logic	PacketAddrDirect;	// packet is address to us
logic	PacketAddrBroadcast;// packet is a broadcast packet
logic	PacketAddrMatch;	// packet is for us (addressed or broadcast)
logic	OurPacket;			// strobed version of PacketAddrMatch

wire	TakenIn = AxisIn.Valid && AxisIn.Ready;
wire	TakenOut = AxisOut.Valid && AxisOut.Ready;


always_ff @(posedge Clock)
	if(Reset)
		First <= 1'b1;
	else
	if(TakenIn)
		if(AxisIn.Last)
			First <= 1'b1;
		else
			First <= 1'b0;

wire	PacketAddrDirect = AxisIn.Data[47:0] == OurMacAddr;
wire	PacketAddrBroadcast = AxisIn.Data[47:0] == 48'hffff_ffff_ffff
wire	PacketAddrMatch = PacketAddrDirect | PacketAddrBroadcast;

always_ff @(posedge Clock)
	if(Reset)
		OurPacket <= 1'b0;
	else
	if(First && TakenIn)
		OurPacket <= PacketAddrMatch;

always_ff @(posedge Clock)
	if(TakenIn)
	begin
		AxisOut.Data <= AxisIn.Data;
		AxisOut.Keep <= AxisIn.Keep;
		AxisOut.User <= AxisIn.User;
	end

always_ff @(posedge Clock)
	if(Reset || TakenOut)
		AxisOut.Valid <= 1'b0;
	else
	if(TakenIn)
		AxisOutValid <= 1'b1;


endmodule


// Packet Fifo with reject and random access
// local bus has byte enables
module TcpIpFifo (
	input				Clock,
	input				Reset,
	//
	Axis64.s 			AxisIn,
	Axis64.m 			AxisOut.
	//
	Bus16.s 			Bus
);
localparameter 	RAMWIDTH = 64 + 8 + 1;
localparameter	RAMLENGTH = 64;

reg 	[RAMWIDTH-1:0]	RAM 	[0:RAMLENGTH-1];



endmodule


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
/*
always_ff @(posedge clk)
    if(ren)
        rdata <= readdata;
*/
assign rdata = readdata;        
endmodule















endmodule



