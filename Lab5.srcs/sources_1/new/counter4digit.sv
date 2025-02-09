`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/08/2025 09:38:58 PM
// Design Name: 
// Module Name: counter4digit
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
module counter4digit(
    input wire clk,
    output wire [7:0] digitselect,
    output wire [7:0] segments
);
    
    wire [15:0] value;
    counter my_counter (
        .clk(clk),
        .value(value)
    );

    display4digit my_4digdisplay (
        .clk(clk),     
        .val(value),
        .segments(segments),
        .digitselect(digitselect) 
    );
   
endmodule
