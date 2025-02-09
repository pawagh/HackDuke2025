`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/08/2025 11:01:34 PM
// Design Name: 
// Module Name: display8bit
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


`default_nettype none

module display8digit(
    input wire [31:0] val,
    input wire clk, 					// 100 MHz clock
    output wire [15:0] segments,
    output wire [7:0] digitselect
    );

	logic [31:0] c = 0;				// Counter variable to help cycle through digits on segmented display
	wire [2:0] roundrobin; 				// Bits extracted from counter for round-robin digit selection
	wire [7:0] value8bit; 				// Hexit shown on the currently selected digit of display
	
	always_ff @(posedge clk)
		c <= c + 1'b 1; 				// This will be a fast changing counter
	
	assign roundrobin = c[18:16];		// Select somewhat slower bits from the counter
	// assign roundrobin = c[23:22]; 	// Try this instead to slow things down even more!

	
	assign digitselect[7:0] = ~ (  			// Note inversion
				      roundrobin == 3'b000 ? 8'b 00000001  
				    : roundrobin == 3'b001 ? 8'b 00000010
				    : roundrobin == 3'b010 ? 8'b 00000100
				    : roundrobin == 3'b011 ? 8'b 00001000
				    : roundrobin == 3'b100 ? 8'b 00010000
				    : roundrobin == 3'b101 ? 8'b 00100000
				    : roundrobin == 3'b110 ? 8'b 01000000
				    : 8'b 10000000 );


		
	assign value8bit   =   (			// Value shown on the currently selected digit
				  roundrobin == 3'b000 ? val[3:0]
				: roundrobin == 3'b001 ? val[7:4]
				: roundrobin == 3'b010 ? val[11:8]
				: roundrobin == 3'b011 ? val[15:12]
				: roundrobin == 3'b100 ? val[19:16]
				: roundrobin == 3'b101 ? val[23:20]
				: roundrobin == 3'b110 ? val[27:24]
				: val[31:28]);
	
	hexto7seg myhexencoder(value8bit, segments);

endmodule

