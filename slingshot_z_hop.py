#!/usr/bin/env python
import sys
import re
import math
import configparser
import os

#VERSION 1.1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~static variables~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#find config.ini
script_directory = None
# Determine the script's directory
if getattr(sys, 'frozen', False):  # Executable (pyinstaller)
    script_directory = os.path.dirname(sys.executable)
else:  # Script (Python interpreter)
    script_directory = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(script_directory, 'config.ini')
#read config.ini
config = configparser.ConfigParser()
config.read(config_file_path)

#the smallest zhop height to use
min_zhop = float(config.get('Settings', 'min_zhop'))

#the largest zhop height to use
max_zhop = float(config.get('Settings', 'max_zhop'))

#distances larger than this will use the max_zhop value,
#smaller distances will interpolate between the min and max values.
max_zhop_distance_threshold = float(config.get('Settings', 'max_zhop_distance_threshold'))

#the feedrate at which the z axis will be lowered after zhop
#the zhop itself takes the feedrate from your gcode
z_lower_feedrate = int(config.get('Settings', 'z_lower_feedrate'))

#horizontal distance of the final travel/drop move. converted from percentage to decimal.
second_distance_factor = int(config.get('Settings', 'second_move_percent')) * 0.01

#this is used for easier reading.
first_distance_factor = 1.0 - second_distance_factor



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~helper functions~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def calculate_distance(x1, y1, x2, y2):
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def linear_interpolation(value, minimum, maximum, start_value, end_value):
    if value >= maximum:
        return end_value
    if value <= minimum:
        return start_value
    # Normalize the value within the range
    normalized_value = (value - minimum) / (maximum - minimum)

    # Calculate the interpolated value
    interpolated_value = start_value + (end_value - start_value) * normalized_value

    return interpolated_value

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gcode_lines = []

#check for env variable
gcode_file_path = ''
if len(sys.argv) > 1:
    gcode_file_path = sys.argv[1]
else:
    gcode_file_path = 'input.gcode'

with open(gcode_file_path, 'r') as gcode_file:
    gcode_lines = gcode_file.readlines()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~ main script body ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#initialize script variables
current_z_height = 0
modified_gcode = []
current_feedrate = 1
target_x = 0
target_y = 0
prev_x = 0
prev_y = 0

#how many travel moves are chained in a row after the current travel move. 
#this is useful so we can treat many short moves as a single travel move.
num_travel_moves = 0
#how many in the current set we have done so far
num_travel_moves_done = 0

target_zhop_height = 0

#iterate over every line in gcode
#we use an index so that we can easily look ahead (or back) in the code. 
for index in range(0,len(gcode_lines)):
    
    #store the current line, for easier to read code
    current_line = gcode_lines[index]

    # Define the pattern for extracting the values
    pattern = r'G1(?: X([\d.]+))?(?: Y([\d.]+))?(?: Z([\d.]+))?(?: F(\d+))?'

    # Use regex to extract the values
    match = re.match(pattern, current_line)

    #if pattern matches, store values contained in the gcode line.
    if match:
        x_coordinate = float(match.group(1)) if match.group(1) else None
        y_coordinate = float(match.group(2)) if match.group(2) else None
        z_coordinate = float(match.group(3)) if match.group(3) else None
        feedrate = int(match.group(4)) if match.group(4) else None

        #before changing our coordinates, we should save our previous location, so we can calculate the distance between them. 
        if target_x != None or target_y != None:
            prev_x = target_x
            prev_y = target_y

        #dont store None values. 
        if x_coordinate != None:
            target_x = x_coordinate
        if y_coordinate != None:
            target_y = y_coordinate
        if z_coordinate != None:
            current_z_height = z_coordinate
        if feedrate != None:
            current_feedrate = feedrate

    #just for testing!
    #modified_gcode.append('; X: ' + str(target_x) + ' Y: ' + str(target_y) + ' Z: ' + str(current_z_height) + ' F: ' + str(current_feedrate) + '\n')
    #modified_gcode.append(current_line)

    #find travel moves
    #if we move without extruding, we assume it's a travel move
    #But only if we are moving x or y. This could probably use RE, but this is easier to read for me.
    if ('G1' in current_line) and ('E' not in current_line) and ('X' in current_line or 'Y' in current_line):

        #check how many travel moves exist in a row after this one
        if num_travel_moves == 0:
            num_travel_moves = 1
            for i in range(index + 1, len(gcode_lines)):
                future_line = gcode_lines[i]
                #if the next line is a travel move too, count it. When we find another non-travel move, stop counting. 
                if ('G1' in future_line) and ('E' not in future_line) and ('X' in future_line or 'Y' in future_line):
                    num_travel_moves += 1
                else:
                    break





        distance = calculate_distance(prev_x,prev_y,target_x,target_y)
            
        if num_travel_moves_done == 0:
            target_zhop_height = current_z_height + linear_interpolation(distance, 0, max_zhop_distance_threshold, min_zhop, max_zhop)

        #set our z hop height, or if we are in the middle of a multi-move travel, calculate what the current height should be
        zhop_height = 0
        if num_travel_moves > 1:
            #when we have multiple travel moves in a row
            zhop_height = linear_interpolation(num_travel_moves_done, 0, num_travel_moves, current_z_height, target_zhop_height)
        else: #only one travel move
            zhop_height = target_zhop_height

        #the travel moves should z hop to a peak partway through the total travel. Calculate the location of that peak.
        delta_x = target_x - prev_x
        peak_x = prev_x + (delta_x * first_distance_factor)
        delta_y = target_y - prev_y
        peak_y = prev_y + (delta_y * first_distance_factor)

        #zhop
        modified_gcode.append('G1 X' + str(round(peak_x, 5)) + ' Y' + str(round(peak_y, 5)) + ' Z' + str(round(zhop_height, 5)) + ' F' + str(current_feedrate) + ' ; custom zhop\n')
        
        #increment to keep track of how many travel moves we have completed in this set
        num_travel_moves_done += 1
        
        if num_travel_moves_done == num_travel_moves: #if we completed all the moves in this set
            #lower to z height
            modified_gcode.append('G1 X' + str(target_x) + ' Y' + str(target_y) + ' Z' + str(current_z_height) + ' F' + str(z_lower_feedrate) + ' ; custom zhop lower \n')
            #old# modified_gcode.append('G1 Z' + str(current_z_height) + ' F' + str(z_lower_feedrate) + ' ; custom zhop lower \n')

            #reset these counters for reuse
            num_travel_moves = 0
            num_travel_moves_done = 0
        


    else:
        #place unmodified code back into the file
        modified_gcode.append(current_line)

        #im paranoid so I'll just make sure these are correct
        num_travel_moves_done = 0
        num_travel_moves = 0






#save modified gcode file over original gcode file.
with open(gcode_file_path, 'w') as gcode_file:
    gcode_file.writelines(modified_gcode)
    