import pyautogui
import time

delay = 0.01
time.sleep(2.7)  # Time to switch to TunerPro and select top-left cell

table = [
    [-6, -8, -12, -16, -18, -20, -18, -18],
    [-8, -10, -12, -16, -18, -20, -18, -18],
    [-10, -12, -16, -18, -20, -20, -18, -18],
    [-12, -16, -18, -20, -20, -20, -18, -18],
    [-12, -16, -18, -20, -20, -20, -18, -18],
    [-10, -14, -16, -18, -18, -18, -16, -16],
    [-8, -12, -14, -16, -16, -16, -14, -14],
    [-6, -10, -12, -14, -14, -14, -12, -12]
]

for row in table:
    for value in row:
        pyautogui.write(str(value))
        time.sleep(delay)
        pyautogui.press('right')
    # Move to the start of the next row:
    for _ in range(len(row)):
        pyautogui.press('left')
    pyautogui.press('down')
    time.sleep(delay)