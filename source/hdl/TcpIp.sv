//
// tcp/ip echo responder
//


`timescale 1 ns / 10 ps
`include "TcpDefines.svh"


module TcpIp (
	input				Clock,
	input				Reset,
	//
	Axis64.s 			AxisInN,	// network 10Gbps input
	Axis64.s 			AxisInL,	// LASP 10Gbps input
	Axis64.m 			AxisOut.	// network 10Gbps output 
	//
	input		[47:0]	OurMacAddr,
	input		[31:0]	OurIpAddr
	//	
);
	/////////////////////////
	// 10G input Stream
	/////////////////////////
	
	// addr filter
	TcpAddrFilter iaf(
		.Clock(Clock),
		.Reset(Reset),
		.AxisIn(AxisIn),
		.AxisOut(AxisOut),
		.OurMacAddr(OurMacAddr)
	);
	
	// input fifo
	//    fifo is both Axis and Bus16 readable
	
	
	
	//////////////////////////
	// processor
	//////////////////////////
	
	// fsm
	
	// datapath
	
	//////////////////////////
	// output stream
	//////////////////////////
	
	// LASP data mux


endmodule



