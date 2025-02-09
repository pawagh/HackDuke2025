//////////////////////////////////////////////////////////////////////////////////
//
// Montek Singh
// 2/6/2025
//
// This is a quick demo to show how to use my tone generator.
//   The sound will cycle from C4 to C5, over and over, with each
//   note being played for approx 1 second.
//
//////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps
`default_nettype none

module montek_sound_test(
    input wire clk,         // 100 MHz clock
    output wire audPWM,
    output wire audEn
    );
    
    assign audEn = 1;       // Always on; could be turned off
    
    logic [31:0] count=0;   // A counter to help cycle through notes to play
    always_ff @(posedge clk)
        count <= count + 1;
        
    // These are periods (in units of 10 ns) for the notes on the normal C4 scale,
    //   i.e.:  C4, D4, E4, F4, G4, A4, B4, C5
    //
    // Here is how to calculate these numbers for each note.
    //   Use https://en.wikipedia.org/wiki/Piano_key_frequencies or another resource to look up
    //   the frequency of a particular musical note.  For example, note C4 ("middle C") has
    //   a frequency of 261.6256 Hz.  The clock on our Nexys boards has a frequency of 100 MHz.
    //   Thus, there are 100e6 / 261.6256 clock cycles for each cycle of a C4 note.  This ratio
    //   equals 382226 (rounded to integer), and is the first number listed in the array below.
    //   Likewise, numbers of the other notes, from D4 to C5 are also populated in the array.
    //   You are welcome to change or add to these notes.

    wire [31:0] notes_periods[0:7] = {382226, 340524, 303373, 286346, 255105, 227273, 202477, 191113};
    
    // cycle through note 0 to 7, over and over, in approx. 1 sec increments
    wire [2:0] note_to_play = count[29:27];
    wire [31:0] period = notes_periods[note_to_play];
    
    montek_sound_generator snd(
       clk,             // 100 MHz clock
       period,          // sound period in tens of nanoseconds
                        // period = 1 means 10 ns (i.e., 100 MHz)      
       audPWM);
       
endmodule
