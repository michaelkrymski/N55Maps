# import pyautogui
# import time
# import re

# def input_to_tunerpro_from_string(input_str, columns):
#     """
#     Types values from a tab/space-separated string into TunerPro row by row.
#     Goes right for each column, then wraps left and down after each row.
#     """
#     # Clean and parse values
#     values = re.split(r'[\t ]+', input_str.strip())

#     print(f"Typing {len(values)} values with {columns} columns per row. Starting in 5 seconds...")
#     time.sleep(1.5)

#     for idx, val in enumerate(values):
#         pyautogui.typewrite(str(val))
#         pyautogui.press('right')

#         # At the end of a row, wrap to the next line
#         if (idx + 1) % columns == 0:
#             for _ in range(columns):
#                 pyautogui.press('left')
#             pyautogui.press('down')
# # Example usage:
# # Paste this into your script and replace the string below with your axis values
# input_to_tunerpro_from_string("3.061	4.332	4.410	4.555	4.601	4.710	4.950	5.275	5.800	7.530	13.248	24.712	38.084	52.443	63.280	73.227", columns=16)

# input_to_tunerpro_from_string("3.271	4.694	4.883	5.139	5.270	5.470	5.667	5.865	6.381	8.168	13.667	25.143	38.896	53.513	64.516	74.609", columns=16)

# input_to_tunerpro_from_string("3.554	5.112	5.339	5.640	5.779	5.992	6.180	6.349	7.042	9.010	14.182	25.726	39.835	54.651	65.765	75.948", columns=16)

# input_to_tunerpro_from_string("3.845	5.516	5.736	6.036	6.180	6.404	6.662	6.941	7.671	9.682	14.645	26.134	40.656	55.753	67.055	77.400", columns=16)

# input_to_tunerpro_from_string("4.073	5.785	5.922	6.152	6.412	6.746	7.069	7.384	8.246	10.301	15.060	26.471	41.460	56.863	68.379	78.912", columns=16)

# input_to_tunerpro_from_string("4.420	6.281	6.432	6.679	6.790	6.990	7.314	7.721	8.649	11.009	15.779	26.984	42.596	58.493	70.404	81.311", columns=16)

# import pyautogui
# import time
# import numpy as np

# pyautogui.PAUSE = 0.01

# # Define your breakpoints (for both axes)
# breaks = np.array([-12, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10])

# # Generate the D-factor table
# table = np.zeros((len(breaks), len(breaks)))
# for i, dev in enumerate(breaks):
#     for j, grad in enumerate(breaks):
#         if dev > 0 and grad > 0:
#             # Overboost and getting worse: decrease WGDC (negative D)
#             mag = max(abs(dev), abs(grad))
#             table[i, j] = -min(10, 0.7 * mag)
#         elif dev < 0 and grad < 0:
#             # Underboost and getting worse: increase WGDC (positive D)
#             mag = max(abs(dev), abs(grad))
#             table[i, j] = min(10, 0.7 * mag)
#         else:
#             table[i, j] = 0
# # Ensure the exact zero cell is zero
# ix0 = np.where(breaks == 0)[0][0]
# table[ix0, ix0] = 0

# def input_table_to_tunerpro(table_2d):
#     rows, cols = table_2d.shape
#     print(f"Switch to TunerPro in 5 seconds (top-left cell selected).")
#     time.sleep(5)
#     for r in range(rows):
#         for c in range(cols):
#             val = table_2d[r, c]
#             pyautogui.typewrite(str(round(val, 2)))
#             pyautogui.press('right')
#             time.sleep(0.05)
#         for _ in range(cols):
#             pyautogui.press('left')
#         pyautogui.press('down')

# # Run the auto-input
# input_table_to_tunerpro(table)

import numpy as np
import pyautogui
import time

pyautogui.PAUSE = 0.01

# Boost deviation Y-axis (rows), 14 breakpoints from -10 to 18
boost_deviation = np.array([-10.0, -7.8, -5.7, -3.5, -1.4, 0.0, 2.9, 5.1, 7.2, 9.4, 11.5, 13.7, 15.8, 18.0])
# RPM X-axis (columns), 16 breakpoints (update to your actual RPM axis if needed)
rpm_axis = np.array([0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500])

# Define one P-factor row for all columns (per your previous design)
p_row = [
    -25.0,   # -10.0
    -21.0,   # -7.8
    -17.0,   # -5.7
    -13.0,   # -3.5
    -6.0,    # -1.4
     0.0,    #  0.0
     7.0,    #  2.9
    14.0,    #  5.1
    23.0,    #  7.2
    28.0,    #  9.4
    34.0,    # 11.5
    36.0,    # 13.7
    37.0,    # 15.8
    38.0     # 18.0
]

# Build the table: 14 rows (boost deviation), 16 columns (RPM)
p_map = np.tile(np.array(p_row).reshape(-1, 1), (1, 16))

def input_table_to_tunerpro(table_2d):
    rows, cols = table_2d.shape
    print(f"Switch to TunerPro in 5 seconds (top-left cell selected).")
    time.sleep(5)
    for r in range(rows):
        for c in range(cols):
            val = table_2d[r, c]
            pyautogui.typewrite(str(round(val, 2)))
            pyautogui.press('right')
            time.sleep(0.05)
        for _ in range(cols):
            pyautogui.press('left')
        pyautogui.press('down')

# Auto-input into TunerPro
input_table_to_tunerpro(p_map)