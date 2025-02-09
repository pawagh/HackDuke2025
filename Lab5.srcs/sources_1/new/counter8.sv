`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/09/2025 12:01:59 AM
// Design Name: 
// Module Name: counter8
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
module counter8 (
input wire clk,
output wire [31:0] value
    );
    logic [64:0] count = 0;
    
    always @(posedge clk) begin
    count <= count + 1;
    end
    
    assign value = count[55:24];
    
endmodule