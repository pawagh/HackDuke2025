`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 02/08/2025 10:01:40 PM
// Design Name: 
// Module Name: counter
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
module counter (
input wire clk,
output wire [15:0] value
    );
    logic [64:0] count = 0;
    
    always @(posedge clk) begin
    count <= count + 1;
    end
    
    assign value = count[41:26];
    
endmodule