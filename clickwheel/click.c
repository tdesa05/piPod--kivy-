// Compile: gcc -Wall -pthread -o click click.c -lpigpio -lrt
// Run:     sudo ./click

#include <pigpio.h> 
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h> 
#include <string.h> 
#include <sys/types.h> 
#include <sys/socket.h> 
#include <arpa/inet.h> 
#include <netinet/in.h> 

// --- Configuration ---
#define CLOCK_PIN 23    // GPIO 23 (Physical Pin 16)
#define DATA_PIN 22     // GPIO 22 (Physical Pin 15) <- UPDATED TO YOUR WORKING PIN
#define BIT_COUNT 32
#define PORT 9090 
#define BUFFER_SIZE 3

#define CENTER_BUTTON_BIT 8
#define LEFT_BUTTON_BIT 10
#define RIGHT_BUTTON_BIT 9
#define UP_BUTTON_BIT 12
#define DOWN_BUTTON_BIT 11
#define WHEEL_TOUCH_BIT 29

#define BUTTON_INDEX 0
#define BUTTON_STATE_INDEX 1
#define WHEEL_POSITION_INDEX 2

// --- Globals ---
uint32_t bits = 0;
uint32_t lastBits = 0;
uint8_t bitIndex = 0;
uint8_t oneCount = 0;
uint8_t recording = 0;
uint8_t dataBit = 1;

// *** THE FIX *** // Your wheel sends 0-1-0-1-1. 
// In LSB-first binary logic, that equals 26 (0b11010).
// We verify bits 0, 1, 2, 3, 4.
const uint32_t PACKET_HEADER_MASK = 0b11111; // Check first 5 bits
const uint32_t PACKET_HEADER_VAL  = 0b11010; // Expected pattern

char buttons[] = { 
    CENTER_BUTTON_BIT, LEFT_BUTTON_BIT, RIGHT_BUTTON_BIT, 
    UP_BUTTON_BIT, DOWN_BUTTON_BIT, WHEEL_TOUCH_BIT
};

int sockfd; 
char buffer[BUFFER_SIZE]; 
char prev_buffer[BUFFER_SIZE];
struct sockaddr_in servaddr; 

// --- Helper Functions ---

uint32_t setBit(uint32_t n, int k) { 
    return (n | (1 << k)); 
} 
  
uint32_t clearBit(uint32_t n, int k) { 
    return (n & (~(1 << k))); 
} 

// --- Core Logic ---

void sendPacket() {
    // Check if the first 5 bits match your specific wheel's header
    if ((bits & PACKET_HEADER_MASK) != PACKET_HEADER_VAL) {
        // If header is wrong, ignore this packet (noise)
        return;
    }

    memset(buffer, -1, BUFFER_SIZE);
    
    // 1. Detect Buttons
    for (size_t i = 0; i < sizeof(buttons); i++) {
        char buttonIndex = buttons[i];
        
        // Button Pressed?
        if ((bits >> buttonIndex) & 1 && !((lastBits >> buttonIndex) & 1)) {
            buffer[BUTTON_INDEX] = buttonIndex;
            buffer[BUTTON_STATE_INDEX] = 1;
            printf(">> Button PRESSED: ID %d\n", buttonIndex);
        } 
        // Button Released?
        else if (!((bits >> buttonIndex) & 1) && (lastBits >> buttonIndex) & 1) {
            buffer[BUTTON_INDEX] = buttonIndex;
            buffer[BUTTON_STATE_INDEX] = 0;
            printf(">> Button RELEASED: ID %d\n", buttonIndex);
        }
    }

    // 2. Detect Wheel Position
    // The position is stored in bits 16-23
    uint8_t wheelPosition = (bits >> 16) & 0xFF;
    buffer[WHEEL_POSITION_INDEX] = wheelPosition;

    // Only send UDP if something changed
    if (memcmp(prev_buffer, buffer, BUFFER_SIZE) != 0) {
        
        // Print position only if it changed (avoids spam)
        if (prev_buffer[WHEEL_POSITION_INDEX] != (char)wheelPosition) {
             printf("Wheel Position: %d\n", wheelPosition);
        }

        lastBits = bits;

        // Send to Socket (Python script can listen to this)
        sendto(sockfd, (const char *)buffer, BUFFER_SIZE, 
            MSG_CONFIRM, (const struct sockaddr *) &servaddr,  
                sizeof(servaddr)); 
        
        memcpy(prev_buffer, buffer, BUFFER_SIZE);
    }
    
    // Always update lastBits so button release logic works
    lastBits = bits;
}

void onClockEdge(int gpio, int level, uint32_t tick) {
    if (!level) return; // Only rising edge

    // Packet start detection
    if (dataBit == 0) {
        recording = 1;
        oneCount = 0;
    } else {
        // Reset if line stays high (idle)
        if (++oneCount >= BIT_COUNT) {
            recording = 0;
            bitIndex = 0;
        }
    }

    if (recording == 1) {
        if (dataBit) {
            bits = setBit(bits, bitIndex);
        } else {
            bits = clearBit(bits, bitIndex);
        }

        if (++bitIndex == 32) {
            bitIndex = 0;
            sendPacket();
        }
    }
}

void onDataEdge(int gpio, int level, uint32_t tick) {
    dataBit = level;
}

int main(void){
    // Socket Setup
    if ( (sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ) { 
        perror("socket creation failed"); 
        exit(EXIT_FAILURE); 
    } 
    memset(&servaddr, 0, sizeof(servaddr)); 
    servaddr.sin_family = AF_INET; 
    servaddr.sin_port = htons(PORT); 
    servaddr.sin_addr.s_addr = INADDR_ANY; 

    // GPIO Setup
    if (gpioInitialise() < 0) exit(1);

    gpioSetMode(CLOCK_PIN, PI_INPUT);
    gpioSetMode(DATA_PIN, PI_INPUT);
    gpioSetPullUpDown(CLOCK_PIN, PI_PUD_UP);
    gpioSetPullUpDown(DATA_PIN, PI_PUD_UP);

    gpioSetAlertFunc(CLOCK_PIN, onClockEdge);
    gpioSetAlertFunc(DATA_PIN, onDataEdge);

    printf("--- DRIVER LIVE ---\n");
    printf("Listening on GPIO %d (Clock) and GPIO %d (Data)\n", CLOCK_PIN, DATA_PIN);
    printf("Sending UDP to Port %d\n", PORT);
    printf("Touch the wheel!\n");

    while(1) {
        sleep(1); 
    };

    gpioTerminate();
    return 0;
}