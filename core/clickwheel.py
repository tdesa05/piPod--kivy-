import socket
import time
import threading
from kivy.app import App


# Gemini AI heavily helped with implementation of clickwheel components, based on Dupont's driver

# --- Configuration ---
UDP_IP = "127.0.0.1"  # Listen to localhost
UDP_PORT = 9090  # Same port as C driver

# Button mapping of click wheel (names used)
BUTTON_MAP = {8: "CENTER", 12: "MENU", 11: "PLAY", 10: "PREV", 9: "NEXT", 29: "TOUCH"}

# FUNCTION CAN NOT BE MANUALLY CALLED, USE OTHER FUNCTIONS TO STOP/START
# # Interprets data driver hosts on ip and port, triggers appropriate functions
# Pauses clickwheel input


class Clickwheel:
    def __init__(self, app):
        super().__init__()
        self.last_button_time = 0  # Tracks last time button was pressed
        self.last_touch_time = 0  # Last time wheel was touched
        self.last_action_time = 0  # Last time action was triggered
        self.app = app

        # A flag to control pausing.
        # set() = Running (True)
        # clear() = Paused (False)
        self.is_running = threading.Event()
        self.is_running.set()  # Start as "Running"

        # A flag to kill the thread completely when app closes
        self.should_exit = False

    def pause_input(self):
        print("Clickwheel Paused")
        self.is_running.clear()

    # Resumes clickwheel input
    def resume_input(self):
        print("Clickwheel Resumed")
        self.is_running.set()

    # Shuts down cw_handler function
    def stop_thread(self):
        self.should_exit = True

    def cw_button(self, btn_name, state_str):
        pass

    def cw_handler(self):
        # Create socket and bind to the ip + port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        print(sock)
        # Set timeout once every 100ms so loop doesnt freeze
        sock.settimeout(0.1)
        last_wheel_pos = -1

        while not self.should_exit:
            # Check if paused
            if not self.is_running.is_set():
                # Sleep and skip logic
                self.is_running.wait(timeout=0.1)
                continue

            try:
                # Buffer size is 3 because the C driver sends exactly 3 bytes
                data, addr = sock.recvfrom(3)
                if data:
                    # Poke out of idleness
                    lambda: self.event_generate("<<ClickwheelActivity>>")

                # Parse the bytes (Python treats bytes as integers 0-255)
                btn_id = data[0]
                btn_state = data[1]
                wheel_pos = data[2]

                # --- Handle Buttons ---
                # The C driver sends 255 (0xFF) if no button event occurred in this packet
                if btn_id != 255:
                    current_time = time.time()

                    if (
                        current_time - self.last_button_time > 0.15
                    ):  # 150ms between presses
                        btn_name = BUTTON_MAP.get(btn_id, f"Unknown ({btn_id})")
                        state_str = "PRESSED" if btn_state == 1 else "RELEASED"
                        print(f"[BUTTON] {btn_name} : {state_str}")
                        self.cw_button(btn_name, state_str)  # As it can change GUI
                        self.last_button_time = current_time
                    else:
                        pass  # Silently ignore input if last press was within 150ms

                # --- Handle Wheel ---
                print(f"[WHEEL]  Position: {wheel_pos}")

                # Initialise first wheel pos
                if last_wheel_pos == -1:
                    last_wheel_pos = wheel_pos
                    continue

                diff = wheel_pos - last_wheel_pos

                # Safety to ensure massive movements aren't recorded wrong
                # As the wheel is 0-256, this negates the chances of diff equalling number outside that range.
                if diff > 200:  # Moved clockwise a large amount
                    diff -= 256
                elif diff < -200:
                    diff += 256

                if diff != 0:
                    current_time = time.time()
                    if current_time - self.last_touch_time > 0.08:  # 80ms debounce
                        self.app.cw_interaction(diff)  # Safe call when touching GUI
                        self.last_touch_time = current_time
                last_wheel_pos = wheel_pos

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}")
                break
        sock.close()
