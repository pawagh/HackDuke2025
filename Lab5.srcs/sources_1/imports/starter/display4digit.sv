//////////////////////////////////////////////////////////////////////////////////
// Montek Singh
// 2/5/2025
//////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps
`default_nettype none

module display4digit(
    input wire [15:0] val,
    input wire clk, 					// 100 MHz clock
    output wire [7:0] segments,
    output wire [7:0] digitselect
    );

	logic [31:0] c = 0;				// Counter variable to help cycle through digits on segmented display
	wire [1:0] roundrobin; 				// Bits extracted from counter for round-robin digit selection
	wire [3:0] value4bit; 				// Hexit shown on the currently selected digit of display
	
	always_ff @(posedge clk)
		c <= c + 1'b 1; 				// This will be a fast changing counter
	
	assign roundrobin = c[18:17];		// Select somewhat slower bits from the counter
	// assign roundrobin = c[23:22]; 	// Try this instead to slow things down even more!

	
	assign digitselect[3:0] = ~ (  			// Note inversion
				      roundrobin == 2'b00 ? 4'b 0001  
				    : roundrobin == 2'b01 ? 4'b 0010
				    : roundrobin == 2'b10 ? 4'b 0100
				    : 4'b 1000 );

	assign digitselect[7:4] = ~ 4'b 0000; 	// Since we are not using the left half of the display
		
	assign value4bit   =   (			// Value shown on the currently selected digit
				  roundrobin == 2'b00 ? val[3:0]
				: roundrobin == 2'b01 ? val[7:4]
				: roundrobin == 2'b10 ? val[11:8]
				: val[15:12] );
	
	hexto7seg myhexencoder(value4bit, segments);

endmodule
