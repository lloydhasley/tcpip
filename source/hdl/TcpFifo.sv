//
// packet Fifo
//
// permits both axis read, and bus write/read
//

`timescale 1 ns / 10 ps
`include "Defines.svh"


// Packet Fifo with reject and random access
// local bus has byte enables
module TcpFifo (
	input				Clock,
	input				Reset,
	input				Mode,		// 1=Axis, 0=Bus (port #2)
	//
	Axis64.s 			AxisIn,
	Axis64.m 			AxisOut,
	//
	Bus16.s 			Bus
);
localparameter 	RAMWIDTH = 64 + 8 + 1;
localparameter	RAMLENGTH = 64;
localparameter	ADDR_SIZE = $clog2(RAMLENGTH);

(* max_fanout = 2000 *)
logic 	[ADDR_SIZE:0]  	WritePointer;    			// pointers are kept 1bit larger
logic 	[ADDR_SIZE:0]  	WritePointerIncremented;    // pointers are kept 1bit larger
logic 	[ADDR_SIZE:0]  	LagPointer;    			// pointers are kept 1bit larger
(* max_fanout = 2000 *)
logic 	[ADDR_SIZE:0]  	ReadPointer;    			// pointers are kept 1bit larger
logic 	[WIDTH-1:0]		WriteData;
logic 	[WIDTH-1:0]		ReadData;
logic 					DoRead;
logic 					WriteEn;
logic 					LastBit;
logic 					Error;


	FifoRam #(
		.SIZE(RAMLENGTH),
		.WIDTH(RAMWIDTH)
	) ifr (
		.clk(Clock),
		.wen(WriteEn),
		.waddr(WritePointer[ADDR_SIZE-1:0]),
		.wdata(WriteData),
		.ren(DoRead),
		.raddr(ReadPointer[ADDR_SIZE-1:0]),
		.rdata(ReadData)
	);
	
assign LastBit = AxisIn.Last;

	//////////////////////////////
	// write control
	//////////////////////////////
	
assign WriteEn = AxisIn.Valid && AxisIn.Ready && (!Reset);
assign WriteData = {AxisIn.Last, AxisIn.Keep, AxisIn.Data};
assign Error = AxisIn.User;
      
assign WritePointerIncremented = WritePointer + 'b1;

always_ff @(posedge Clock)
    if(Reset)
    begin
		WritePointer <= 1'b0;
		LagPointer <= 1'b0;
	end
    else
    if(WriteEn)
    	if(LastBit)
	    	if(Error)
    		begin
	    	    WritePointer <= LagPointer;
			end
	    	else
			begin
	    	    WritePointer <= WritePointerIncremented;
				LagPointer <= WritePointerIncremented;
			end	    
		else
	    	WritePointer <= WritePointerIncremented;

	//////////////////////////////
	// read control
	//////////////////////////////

assign DoRead = Mode && (!Reset) && (!Empty) && (AxisOut.Ready ||(!AxisOut.Valid));

always_ff @(posedge Clock)
    if(Reset)
        ReadPointer <= 'b0;
    else
  	if(DoRead)  
        ReadPointer <= ReadPointer + 'b1;

always_ff @(posedge Clock)
	if(Reset)
		AxisOut.Valid <= 1'b0;
	else
	if(DoRead)
		AxisOut.Valid <= 1'b1;
	else
	if(AxisOut.Ready)
		AxisOut.Valid <= 1'b0;
	
	
assign {AxisOut.Last, AxisOut.Keep, AxisOut.Data} = ReadData;

assign Empty = (PACKET_MODE) ? 
            ReadPointer == LagPointer   : 
            ReadPointer == WritePointer ; 

assign Full = !(|(WritePointer ^ ReadPointer ^ (32'h1 << ADDR_SIZE)));


endmodule





