; can sub be replaced with xor?
; how many rotr
; reduce ACCs from 2 to 1
; xor.W operand must be from regfile
; check operands, register file versus immediate
;       immediate has 8bit limit, if exceeded place into regfile
;
; change add-indirect to two instructions.  lda,I and addW
;   ie make indirect more general purpose instruction
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; tcp/ip frame processing;
;
; respond to arp, and ping
;
;
; assumes L2 frame filter before receive fifo
; frame filter based on addr, maxlength
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; written by: lhasley@smu.edu
; April 2025
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; instruction definitions
;       if cycles=0 then not real instructions
;
;       name       value   operand pos length  cycles   handler
inst    rom         0       2       16   0       0      --
inst    org         0       1       16   0       0      --
inst    nop         0       0       9   1       1       nop
;
inst    lda.B       8       1       9   1       2       ldaB
inst    lda.W       9       1       9   1       2       ldaW
inst    ldi.B       10      1       9   1       1       ldiB
inst    ldi.W       11      1       9   1       1       ldiW
inst    sta.B       12      1       9   1       1       staB
inst    sta.W       13      1       9   1       1       staW

inst    subi.B      6       1       9   1       1       subiB
inst    rotri.W     16      1       9   1       1       rotrIW
inst    rotli.W     17      1       9   1       1       rotlIW

inst    xor.W       4       1       9   1       1       xorW
inst    xori.B      5       1       9   1       1       xorIB

inst    jnz         20       1       9  1       2       jnz
inst    jz          21       1       9  1       2       jz
inst    jneg        22       1       9  1       2       jneg
inst    jmp         24       1       9  1       2       jmp
inst    jmp.I       25       1       9  1       3       jmpI

inst    add.W       28      1       9  1       1        addW
inst    addi.W      29      1       9  1       1        addIW
inst    add.WI      30      1       9  1       2        addWI
;
; end of machine specification
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; begin user constants
;
; define base addresses for the two principal blocks on the bus.
;
Regs    equ     0x00        ; up to 128 registers
RFifo   equ     0x80        ; can extract bytes up to 128 bytes into a frame
;
; register block definitions
;
Regs.CNTRL                equ 0x000
Regs.FifoStatus           equ 0x004
Regs.ADDR_SEND_FRAME      equ 0x008
Regs.FRAME_DONE           equ 0x00a
Regs.EatFrame             equ 0x00c

Regs.ADDR_OUR_IP_ADDR_L   equ 0x010
Regs.ADDR_OUR_IP_ADDR_H   equ 0x012
Regs.ADDR_OUR_MAC_ADDR_L  equ 0x018
Regs.ADDR_OUR_MAC_ADDR_M  equ 0x01a
Regs.ADDR_OUR_MAC_ADDR_H  equ 0x01c

Regs.Mark               equ 0x020
Regs.StartAddress       equ 0x022
Regs.EndAddress         equ 0x024
Regs.Temp               equ 0x026
Regs.MINUS_1            equ 0x028       ; 0xffff
Regs.FRAMETYPEARP       equ 0x02a       ; 0x0806
Regs.PROTTYPE           equ 0x02c       ; 0x0800
Regs.FRAME_TYPE_IP      equ 0x02e       ;0x800
Regs.Checksum           equ 0x030
;
; MAC layer frame field addresses (offsets into frame)
;
ADDR_MAC_START      equ Rfifo

RFifo.ADDR_MAC_DA_L   equ ADDR_MAC_START + 0
RFifo.ADDR_MAC_DA_M   equ ADDR_MAC_START + 2
RFifo.ADDR_MAC_DA_H   equ ADDR_MAC_START + 4
RFifo.ADDR_MAC_SA_L   equ ADDR_MAC_START + 6
RFifo.ADDR_MAC_SA_M   equ ADDR_MAC_START + 8
RFifo.ADDR_MAC_SA_H   equ ADDR_MAC_START + 10
RFifo.ADDR_MAC_TYPE   equ ADDR_MAC_START + 12
;
; arp layer frame fields (offsets into frame)
;
RFifo.ADDR_MAC_LEN    equ ADDR_MAC_START + 14
ADDR_ARP_START  equ RFifo.ADDR_MAC_LEN

RFifo.ADDR_ARP_HARDTYPE           equ ADDR_ARP_START + 0
RFifo.ADDR_ARP_PROTTYPE           equ ADDR_ARP_START + 2
RFifo.ADDR_ARP_HARDSIZE           equ ADDR_ARP_START + 4
RFifo.ADDR_ARP_PROTSIZE           equ ADDR_ARP_START + 5
RFifo.ADDR_ARP_OP                 equ ADDR_ARP_START + 6
RFifo.ADDR_ARP_MAC_ADDR_SENDER_L  equ ADDR_ARP_START + 8
RFifo.ADDR_ARP_MAC_ADDR_SENDER_M  equ ADDR_ARP_START + 10
RFifo.ADDR_ARP_MAC_ADDR_SENDER_H  equ ADDR_ARP_START + 12
RFifo.ADDR_ARP_IP_ADDR_SENDER_L   equ ADDR_ARP_START + 14
RFifo.ADDR_ARP_IP_ADDR_SENDER_H   equ ADDR_ARP_START + 16
RFifo.ADDR_ARP_MAC_ADDR_TARGET_L  equ ADDR_ARP_START + 18
RFifo.ADDR_ARP_MAC_ADDR_TARGET_M  equ ADDR_ARP_START + 20
RFifo.ADDR_ARP_MAC_ADDR_TARGET_H  equ ADDR_ARP_START + 22
RFifo.ADDR_ARP_IP_ADDR_TARGET_L   equ ADDR_ARP_START + 24
RFifo.ADDR_ARP_IP_ADDR_TARGET_H   equ ADDR_ARP_START + 26
;
; IP layer frame fields (offsets into frame)
;
ADDR_IP_START  equ RFifo.ADDR_MAC_LEN

RFifo.ADDR_IP_HDR_LENGTH             equ ADDR_IP_START + 0
RFifo.ADDR_IP_VERSION                equ ADDR_IP_START + 0
RFifo.ADDR_IP_TOS                    equ ADDR_IP_START + 1
RFifo.ADDR_IP_LENGTH                 equ ADDR_IP_START + 2
RFifo.ADDR_IP_ID                     equ ADDR_IP_START + 4
RFifo.ADDR_IP_FLAGS                  equ ADDR_IP_START + 6
RFifo.ADDR_IP_FRAG_OFFSET            equ ADDR_IP_START + 7

RFifo.ADDR_IP_TTL                    equ ADDR_IP_START + 8
RFifo.ADDR_IP_PROTOCOL               equ ADDR_IP_START + 9
RFifo.ADDR_IP_HDR_CHKSUM             equ ADDR_IP_START + 10
RFifo.ADDR_IP_SRC_IP_L               equ ADDR_IP_START + 12
RFifo.ADDR_IP_SRC_IP_H               equ ADDR_IP_START + 14
RFifo.ADDR_IP_DEST_IP_L              equ ADDR_IP_START + 16
RFifo.ADDR_IP_DEST_IP_H              equ ADDR_IP_START + 18

ADDR_IP_LEN  equ 20
;
; ICMP layer frame fields
;
ADDR_ICMP_START                 equ ADDR_IP_START + ADDR_IP_LEN
RFifo.ADDR_ICMP_START           equ ADDR_ICMP_START

RFifo.ADDR_ICMP_TYPE                  equ ADDR_ICMP_START + 0
RFifo.ADDR_ICMP_CODE                  equ ADDR_ICMP_START + 1
RFifo.ADDR_ICMP_CHKSUM                equ ADDR_ICMP_START + 2

;
; ip frame breakdown
;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; constants to be hardcoded in instructions
;   note: these constants must be < 2**8
CONSTANT_1          equ 0x0001
ADDR_CONSTANT_MINUS_1    equ Regs.MINUS_1

;
; ARP Frame contents
;
ADDR_FRAMETYPEARP    equ Regs.FRAMETYPEARP
HARDTYPE        equ 1
ADDR_PROTTYPE        equ Regs.PROTTYPE
HARDSIZE        equ 6
PROTSIZE        equ 4

ARP_OP_RQST     equ 1       ; request
ARP_OP_RESPONSE equ 2       ; response
;
; IP Frame Type
;
ADDR_FRAME_TYPE_IP   equ    Regs.FRAME_TYPE_IP
TPCIP_4BYTE     equ 4
;
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
; echo layer frame fields (offsets into frame)
; below assumes all fields are 16 bits which is not true.
;
    rom     21x256
    org     0
Start:
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; WAIT FOR FRAME IN RECEIVE FIFO
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
Wait:
    lda.B   Regs.FifoStatus
    jnz     Wait
    ; have a frame, fall through to ARP processing
    
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; L2 frame address filtering
    ;;     note: to be put in hardware
    ;;     in front of receive fifo
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
 
    lda.W   RFifo.ADDR_MAC_DA_L
    xor.W   Regs.ADDR_OUR_MAC_ADDR_L
    jnz MacFilter
    lda.W   RFifo.ADDR_MAC_DA_M
    xor.W   Regs.ADDR_OUR_MAC_ADDR_M
    jnz MacFilter
    lda.W   RFifo.ADDR_MAC_DA_H
    xor.W   Regs.ADDR_OUR_MAC_ADDR_H
    jz  TestArp      ; have a match of our direct address
    
MacFilter:
    lda.W   RFifo.ADDR_MAC_DA_L
    xor.W   ADDR_CONSTANT_MINUS_1
    jnz     ThrowFrameAway
    lda.W   RFifo.ADDR_MAC_DA_M
    xor.W   ADDR_CONSTANT_MINUS_1
    jnz     ThrowFrameAway
    lda.W   RFifo.ADDR_MAC_DA_H
    xor.W   ADDR_CONSTANT_MINUS_1
    jnz     ThrowFrameAway
    ; matches broadcast address
    ; fall through to Arp frame recognition
    
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; ARP FRAME processing
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
TestArp:
    ;
    ; test Ethernet Frame Type
    lda.W   RFifo.ADDR_MAC_TYPE
    xor.W   Regs.FRAMETYPEARP
    jnz     NotArp
    ;
    ; test hard Type
    lda.W   RFifo.ADDR_ARP_HARDTYPE
    xor.W   HARDTYPE
    jnz     NotArp
    ;
    ; test protocol Type
    lda.W   RFifo.ADDR_ARP_PROTTYPE
    xor.W   ADDR_PROTTYPE
    jnz     NotArp
    ;
    ; test hard size
    lda.B   RFifo.ADDR_ARP_HARDSIZE
    xori.B  HARDSIZE
    jnz     NotArp
    ;
    ; test protocol size
    lda.B   RFifo.ADDR_ARP_PROTSIZE
    xori.B  PROTSIZE
    jnz     NotArp
    ;
    ; test arp operation code
    lda.W   RFifo.ADDR_ARP_OP
    xori.B  ARP_OP_RQST     ; will zero extend
    jnz     NotArp
    
    ; have a valid ARP FRAME
    ; may or may not be our IP address
    lda.W   RFifo.ADDR_ARP_IP_ADDR_TARGET_L
    xor.W   Regs.ADDR_OUR_IP_ADDR_L
    jnz     NotArp
    lda.W   RFifo.ADDR_ARP_IP_ADDR_TARGET_H
    xor.W   Regs.ADDR_OUR_IP_ADDR_H
    jnz     NotArp
    ;
    ; have a valid ARP FRAME
    ; it IS OUR IP ADDRESS
    ; transform receive buffer into transmit buffer
    ;
HaveArp:
    ; switch MAC address
    lda.W   RFifo.ADDR_MAC_SA_L
    sta.W   RFifo.ADDR_MAC_DA_L       ; tmp in python architecture model
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_L
    lda.W   RFifo.ADDR_MAC_SA_M
    sta.W   RFifo.ADDR_MAC_DA_M
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_M
    lda.W   RFifo.ADDR_MAC_SA_H
    sta.W   RFifo.ADDR_MAC_DA_H
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_H
    lda.W   Regs.ADDR_OUR_MAC_ADDR_L
    sta.W   RFifo.ADDR_MAC_SA_L
    lda.W   Regs.ADDR_OUR_MAC_ADDR_M
    sta.W   RFifo.ADDR_MAC_SA_M
    lda.W   Regs.ADDR_OUR_MAC_ADDR_H
    sta.W   RFifo.ADDR_MAC_SA_H
    ;
    ; switch ARP layer DA, SA
    ;   note: mac_targets were set above
    lda.W   Regs.ADDR_OUR_MAC_ADDR_L
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_SENDER_L
    lda.W   Regs.ADDR_OUR_MAC_ADDR_M
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_SENDER_M
    lda.W   Regs.ADDR_OUR_MAC_ADDR_H
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_SENDER_H
    
    ; switch ARP layer IP 
    lda.W   RFifo.ADDR_ARP_IP_ADDR_SENDER_L
    sta.W   Regs.Temp
    lda.W   Regs.ADDR_OUR_MAC_ADDR_L
    sta.W   RFifo.ADDR_ARP_IP_ADDR_SENDER_L
    lda.W   Regs.Temp
    sta.W   RFifo.ADDR_ARP_IP_ADDR_TARGET_L
    lda.W   RFifo.ADDR_ARP_IP_ADDR_SENDER_H
    sta.W   Regs.Temp
    lda.W   Regs.ADDR_OUR_MAC_ADDR_H
    sta.W   RFifo.ADDR_ARP_IP_ADDR_SENDER_H
    lda.W   Regs.Temp
    sta.W   RFifo.ADDR_ARP_IP_ADDR_TARGET_H

    ; set op to ARP response
    ldi.B   ARP_OP_RESPONSE
    sta.B   RFifo.ADDR_ARP_OP
    
    ; add our mac to the ARP response   ??? CHECK LHC2 copy of python program
    ;                                    ??? undoes above writes
    ;                                    ??? seems it should to go sender, which was already done    
    lda.W   Regs.ADDR_OUR_MAC_ADDR_L
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_L
    lda.W   Regs.ADDR_OUR_MAC_ADDR_M
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_M
    lda.W   Regs.ADDR_OUR_MAC_ADDR_H
    sta.W   RFifo.ADDR_ARP_MAC_ADDR_TARGET_H
    ;
    ; ARP RESPONSE FRAME IS READIED
    ; let's send it
    jmp     SendFrame

    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; L3 packet processing
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
        
NotArp:
Check_L3:    
    ; check if L3_IP frame 
    lda.W   RFifo.ADDR_MAC_TYPE
    xor.W   Regs.FRAME_TYPE_IP               ; mac layer type/len field
    jnz     ThrowFrameAway
    
    lda.B   RFifo.ADDR_IP_VERSION       ; needs nibble not a byte
    rotri.W 4
    xori.B  TPCIP_4BYTE                 ; hard coded tcp/ip 4 byte
    jnz     ThrowFrameAway

    lda.W   RFifo.ADDR_IP_DEST_IP_L
    xor.W   Regs.ADDR_OUR_IP_ADDR_L
    jnz     ThrowFrameAway
    lda.W   RFifo.ADDR_IP_DEST_IP_H
    xor.W   Regs.ADDR_OUR_IP_ADDR_H
    jnz     ThrowFrameAway
    
    lda.B   RFifo.ADDR_IP_HDR_LENGTH
    xori.B  5
    jneg    ThrowFrameAway

    ;   Regs.Checksum       protocol supplied checksum
    ;   Regs.StartAddress   address of next word
    ;   Regs.EndAddress     (not inclusive)
    ;   Regs.Mark

    ; prepare IP checksum
    ldi.W   RFifo.ADDR_IP_HDR_LENGTH    ; starting address
    sta.W   Regs.StartAddress
    lda.B   RFifo.ADDR_IP_HDR_LENGTH    ; length (32bit words) w/ version #
    rotli.W 4
    rotri.W 1                           ; # of bytes to sum
    add.W  RFifo.ADDR_IP_HDR_LENGTH    ; ending address
    sta.W   Regs.EndAddress
    ldi.W   L3_ChecksumReturn
    jmp     Checksum

L3_ChecksumReturn:
    xor.W   ADDR_CONSTANT_MINUS_1
    jnz     ThrowFrameAway
    ;
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;; ICMP packet processing
    ;;   note; we only support ping type ICMP frames
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;Check_ICMP:
    ; valid L3_IP, check if ICMP - ping packet

    ; determine if this is a ping frame
do_PING:
    lda.B   RFifo.ADDR_ICMP_TYPE
    xori.B  8
    jnz     ThrowFrameAway
    lda.W   RFifo.ADDR_ICMP_CODE
    jnz     ThrowFrameAway

    ; we have a ping frame

    ; prepare checksum
    lda.W   RFifo.ADDR_ICMP_CHKSUM
    sta.W   Regs.Checksum
    lda.W   RFifo.ADDR_ICMP_START
    rotri.W  3
    sta.W   Regs.StartAddress
    lda.W   RFifo.ADDR_IP_LENGTH
    subi.B  20          ; python has 164>>3 => 20.5
    sta.W   Regs.EndAddress
    ldi.W   ICMP_ChecksumReturn
    jmp     Checksum

ICMP_ChecksumReturn:
    jz      icmp_keep
    xor.W   ADDR_CONSTANT_MINUS_1       ; if checksum == 0, then it is ok.
    jnz     ThrowFrameAway
icmp_keep:
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ; end of ICMP HEADER
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;



    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;;  PING ADDRESSED TO US
    ;;
    ;;  need to respond
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
doPing:
    lda.W   RFifo.ADDR_MAC_SA_L
    sta.W   RFifo.ADDR_MAC_DA_L
    lda.W   RFifo.ADDR_MAC_SA_M
    sta.W   RFifo.ADDR_MAC_DA_M
    lda.W   RFifo.ADDR_MAC_SA_H
    sta.W   RFifo.ADDR_MAC_DA_H

    lda.W   Regs.ADDR_OUR_MAC_ADDR_L
    sta.W   RFifo.ADDR_MAC_DA_L
    lda.W   Regs.ADDR_OUR_MAC_ADDR_M
    sta.W   RFifo.ADDR_MAC_DA_M
    lda.W   Regs.ADDR_OUR_MAC_ADDR_H
    sta.W   RFifo.ADDR_MAC_DA_H

    ldi.B   0
    sta.B   RFifo.ADDR_ICMP_TYPE

    lda.W   RFifo.ADDR_IP_DEST_IP_L
    sta.W   Regs.Temp
    lda.W   RFifo.ADDR_IP_SRC_IP_L
    sta.W   RFifo.ADDR_IP_DEST_IP_L
    lda.W   Regs.Temp
    sta.W   RFifo.ADDR_IP_SRC_IP_L

    lda.W   RFifo.ADDR_IP_DEST_IP_H
    sta.W   Regs.Temp
    lda.W   RFifo.ADDR_IP_SRC_IP_H
    sta.W   RFifo.ADDR_IP_DEST_IP_H
    lda.W   Regs.Temp
    sta.W   RFifo.ADDR_IP_SRC_IP_H

    ; ping packet ready to transmit
    jmp     SendFrame

    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    ;;  COMMON SUBROUTINES
    ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
Checksum:
    ; calling function initializes:
    ;   Acc = Return Address
    ;   Regs.Checksum       protocol supplied checksum
    ;   Regs.StartAddress   address of next word
    ;   Regs.EndAddress     (not inclusive)
    ;
    ; returns 0 in Acc if Checksum Passes
    sta.W   Regs.Mark
    ;
    lda.W   Regs.Checksum
    jz      ChksumPass      ; if 0, dont check checksum
    ; clear sum
    ldi.B   0
    sta.W   Regs.Checksum
ChksumLoop:
    lda.W   Regs.Checksum
    add.WI  Regs.StartAddress       ; StartAddress is really instantaneous address
    sta.W   Regs.Checksum
    lda.W   Regs.StartAddress
    addi.W  CONSTANT_1
    sta.W   Regs.StartAddress
    xor.W   Regs.EndAddress
    jnz     ChksumLoop
    ; checksum calculation complete
    lda.W   Regs.Checksum
ChksumPass:
    ; return to Mark
    jmp.I   Regs.Mark

    ;
    ; send frame called for both arp and ping frames
    ;   will send frame in buffer out the 10ge egress port
    ;
SendFrame:
    ldi.B   1           ; activate sendFrame state machine
    sta.W   Regs.ADDR_SEND_FRAME    ; gives a pulse, retained by the "smart" mux
WaitSendFrame:
    lda.B   Regs.FRAME_DONE
    jnz     WaitSendFrame
    jmp     Start

    ;
    ; throw lead frame in FIFO away
    ;
ThrowFrameAway:
    ldi.B   2               ; activate EatFrame state machine
    sta.W   Regs.EatFrame   ; triggers fifo to throw frame away
    jmp     Start
