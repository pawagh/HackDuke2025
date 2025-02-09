`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/08/2025 11:03:34 PM
// Design Name: 
// Module Name: counter8digit
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
module counter8digit(
    input wire clk,
    output wire [7:0] digitselect,
    output wire [7:0] segments
);
    
    wire [15:0] value;
    counter my_counter (
        .clk(clk),
        .value(value)
    );

    display8digit my_8digdisplay (
        .clk(clk),     
        .val(value),
        .segments(segments),
        .digitselect(digitselect) 
    );
   
endmodule