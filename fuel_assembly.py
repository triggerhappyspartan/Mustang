# fuel_assembly.py
#A method for organizing all information related to analyzing fuel assemblies.
import sys
import os
import os.path
import numpy as np
import random
import time
import math
import reproduction
import metrics

#############################################################
#2D assembly cost function calculations
############################################################
def search_for_k_inf(file_lines):
#A function to determine the values of K_inf at the different statepoints within the output Casmo File
    kinf_list = []
    search_line = '--------------------  C A S M O - 4     S U M M A R Y   ----------------------'
    search_elems = search_line.strip().split()
    line_count = 1000
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) == len(search_elems)):
        elemcount = 0
        nmatch = 0
        for el in elems:
          if(el == search_elems[elemcount]):
            nmatch+=1
          elemcount+=1
        if(nmatch == len(search_elems)):
          line_count = 0
      if(line_count == 1):
        temp = elems[6]
        kinf_list.append(float(temp))
      line_count+=1
    return kinf_list

def search_for_peak_power(file_lines):
#A function for determining the values of the power peaking factor at different statepoints within the output Casmo
#File
    FDH_list = []
    string = ['*','POWER','DISTRIBUTION']
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) > 5):
        count = 0
        nmatch = 0
        for el in string:
          if(el == elems[count]): nmatch+=1
          count+=1
        if(nmatch == 3):
          FDH_list.append(float(elems[6]))
    return FDH_list

def search_for_average_burnup(file_lines):
#A function for determining the average burnup at different statepionts within the output file
    average_burnup = []
    string = ['*','BURNUP','=']
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) > 3):
        count = 0
        nmatch = 0
        for el in string:
          if(el == elems[count]): nmatch+=1
          count+=1
        if(nmatch == len(string)):
          average_burnup.append(float(elems[3]))
    return average_burnup

def search_maximum_burnup(file_lines):
#A function for dertmining the maximum burnup at different statepoints within the output file
    max_burnup = []
    string = ['BURNUP','IN','MWD/KG']
    line_count = 1000
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) > 3):
        count = 0
        nmatch = 0
        for el in string:
          if(el == elems[count]): nmatch+=1
          count+=1
          if(nmatch == len(string)):
            line_count = 0
      if(line_count == 10):
        temp = elems[2]
        temp_list = list(temp)
        foo_burn = ''
        for foostuff in temp_list:
          if(foostuff == '*'):
            pass
          else:
            foo_burn = foo_burn + foostuff
        max_burnup.append(float(foo_burn))
      line_count+=1
    return max_burnup

def calculate_cost(k_inf, FdH):
#This function calculates the 'cost' of a fuel assembly. Cost is based on the value of K-infinity, burnup
# and includes a penalty for FdH being hirer than 1.25. It is the value of K-inf minus the differenge of
# the max burnup and the average burnup, divided by average burnup. Total Cost is the sum of these calculations.
    total_cost = 0.0
    depletion_state = 0
    ideal_k = 1.200000000
    for state in k_inf:
      k_value = k_inf[depletion_state]
      FdH_penalty = FdH[depletion_state]
      if(FdH_penalty < 1.5): power_penalty = 1.0
      else: power_penalty = 0.5
      total_cost = total_cost + power_penalty/((k_value - ideal_k)**2)
      depletion_state+=1
    return total_cost 

########################################################################################
#3D Assembly Cost Function Calculations
#####################################################################
def search_power_distributions(file_lines):
#A function to extract the power distributions from Assemblies. Returns a LIST of MATRICES.
#Lattice is assumed to be in Half-Core Symmetry.
    power_matrix_list = []
    line_count = 1000
    want_string_to_say =  ['*', 'POWER', 'DISTRIBUTION',    'PEAK:', 'LL', '=']
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) > len(want_string_to_say)):
        elem_count = 0
        match_count = 0
        for foo in want_string_to_say:
          if(elems[elem_count] == foo): match_count+=1
          elem_count+=1
        if(match_count == len(want_string_to_say)):
          line_count = 0
          temp_power_list = []
      if(line_count > 0 and line_count < 11):
        for el in elems:
          word_list = list(el)
          true_word = ''
          for letter in word_list:
            if(letter == '*'):
              pass
            else:
              true_word = true_word + letter
          temp_power_list.append(float(true_word))
      if(line_count == 11):
        row = 0  
        column = 0
        power_matrix = np.zeros((11,11),dtype=np.float)
        for el in temp_power_list:
          power_matrix[row][column] = el
          if(row == column): pass
          else: power_matrix[column][row] = el
          column+=1
          if(column > row):
            row+=1
            column = 0
        power_matrix_list.append(power_matrix)
      line_count+=1
    return power_matrix_list  

def calculate_btf(average_kinf,power_list_one, power_list_two,power_list_three, power_list_four,power_list_five, power_list_six):
#A function to calculate the BTF value for the assembly uses the power distribution from the Casmo lattice files and 
#the power map distribution.
#    lattice_location_one = 9 #inches    
#    lattice_location_two = 64
#    lattice_location_three = 140
    lattice_locations = read_lattice_locations('input_data.txt') 
#    additive_constants = np.matrix([[ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
#                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20]])
#    
    additive_constants = np.matrix([[-0.061,-0.078,-0.084,-0.083,-0.073,-0.074,-0.095,-0.084,-0.104,-0.086,0],
                                    [-0.078,-0.02,-0.016, -0.020,-0.007,-0.003,-0.020,-0.055,-0.020,-0.116,0],
                                    [-0.084,-0.016,-0.025, 0.005,-0.003,-0.031,-0.049,-0.020,-0.066,-0.113,0],
                                    [-0.083,-0.020, 0.005,-0.008,-0.011, 0.000, 0.000,-0.058,-0.020,-0.134,0],
                                    [-0.073,-0.007,-0.003,-0.011,-0.020, 0.000, 0.000,-0.041,-0.043,-0.122,0],
                                    [-0.074,-0.003,-0.031, 0.000, 0.000,-0.020,-0.022,-0.041,-0.042,-0.127,0],
                                    [-0.095,-0.020,-0.049, 0.000, 0.000,-0.022,-0.023,-0.031,-0.020,-0.148,0],
                                    [-0.084,-0.055,-0.020,-0.058,-0.041,-0.041,-0.031,-0.042,-0.083,-0.138,0],
                                    [-0.104,-0.020,-0.066,-0.020,-0.043,-0.042,-0.020,-0.083,-0.020,-0.150,0],
                                    [-0.086,-0.116,-0.113,-0.134,-0.122,-0.127,-0.148,-0.138,-0.150,-0.131,0],
                                    [0,0,0,0,0,0,0,0,0,0,0]])
          
    weight_side = 0.2
    weight_corner = 0.05  
    axial_power_distribution_file = open('axial_power_distribution.txt','r')
    axial_power_lines = axial_power_distribution_file.readlines()
    axial_power_distribution_file.close()
    axial_power_list = []
    number_powers = 0
    power_sum = 0
    for line in axial_power_lines:
      temp_power = line.strip().split()
      power = float(temp_power[0])
#      power = 1
      axial_power_list.append(power)
      power_sum+=power
    number_depletion_steps = len(average_kinf)
    number_axial_positions = len(axial_power_lines)
 
    btf_matrix     = np.zeros((11,11, number_depletion_steps))
    number_corners = np.zeros((11,11, number_depletion_steps))
    number_sides   = np.zeros((11,11, number_depletion_steps))
    square_corner  = np.zeros((11,11, number_depletion_steps))
    square_sides   = np.zeros((11,11, number_depletion_steps))
    power_zones    = np.zeros((11,11, number_depletion_steps))  
    kinf_matrix    = np.zeros((number_depletion_steps))
    power_matrix   = np.zeros((11,11,number_axial_positions, number_depletion_steps))
    power_lattice  = np.zeros((11,11, number_depletion_steps))    
    
#Makes power matrix lattice for calculating BTF              
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        #Bottom Lattice Calculations
        if(z <= lattice_locations[0]):
          power_matrix[:,:,z,w] = power_list_one[w][:,:]
        elif(z > lattice_locations[0] and z <= lattice_locations[1]):
          interpolate = (z - lattice_locations[0])/(lattice_locations[1] - lattice_locations[0])
          temp_one = power_list_two[w][:,:]
          temp_two = power_list_three[w][:,:]
          power_matrix[:,:,z,w] = temp_one + (temp_two - temp_one)*interpolate
        elif(z > lattice_locations[1] and z < lattice_locations[2]):
          interpolate = (z - lattice_locations[1])/(lattice_locations[2] - lattice_locations[1])
          temp_one = power_list_three[w][:,:]
          temp_two = power_list_four[w][:,:]
          power_matrix[:,:,z,w] = temp_one + (temp_two - temp_one)*interpolate
        elif(z > lattice_locations[2] and z < lattice_locations[3]):
          interpolate = (z - lattice_locations[2])/(lattice_locations[3] - lattice_locations[2])
          temp_one = power_list_four[w][:,:]
          temp_two = power_list_five[w][:,:]
          power_matrix[:,:,z,w] = temp_one + (temp_two - temp_one)*interpolate
        else:
          power_matrix[:,:,z,w] = power_list_six[w][:,:]
                
    for w in xrange(number_depletion_steps):
      for x in xrange(10):
        for y in xrange(10):
          rod_sum = 0
          for z in xrange(number_axial_positions):
            rod_sum+= power_matrix[x,y,z,w]*axial_power_list[z]
          power_lattice[x,y,w] = rod_sum/power_sum
    for w in xrange(number_depletion_steps):
      for x in xrange(11):
        for y in xrange(11):
          if(power_lattice[x,y,w] > 0):
            power_zones[x,y,w] = 1
           
    for w in xrange(number_depletion_steps):
      for x in xrange(10):
        for y in xrange(10):
          if(x == 0):
            pass
          elif(x == 10):
            pass
          elif(y == 0):
            pass
          elif(y == 10):
            pass
          else:
            number_corners[x,y,w] = power_zones[x-1,y-1,w] +  power_zones[x-1,y+1,w] + power_zones[x+1,y-1,w] + power_zones[x+1,y+1,w]
            number_sides[x,y,w] = power_zones[x-1,y-1,w] +  power_zones[x-1,y+1,w] + power_zones[x+1,y-1,w] + power_zones[x+1,y+1,w]

    for w in xrange(number_depletion_steps):
      for x in xrange(11):
        for y in xrange(11):
          if(x == 0):
            pass
          elif(x == 10):
            pass
          elif(y == 0):
            pass
          elif(y == 10):
            pass
          else:
            square_corner[x,y,w] = power_lattice[x-1,y-1,w]**0.5 + power_lattice[x-1,y+1,w]**0.5 + power_lattice[x+1,y-1,w]**0.5 + power_lattice[x+1,y+1,w]**0.5
            square_sides[x,y,w] = power_lattice[x-1,y-1,w]**0.5 +  power_lattice[x-1,y+1,w]**0.5 + power_lattice[x+1,y-1,w]**0.5 + power_lattice[x+1,y+1,w]**0.5

    for w in xrange(number_depletion_steps):
      for x in xrange(11):
        for y in xrange(11):
          if(power_lattice[x,y,w] > 0):
            numerator = power_lattice[x,y,w]**0.5 + square_corner[x,y,w]*weight_corner + square_sides[x,y,w]*weight_side
            denominator = 1 + number_sides[x,y,w]*weight_side + number_corners[x,y,w]*weight_corner
            btf_matrix[x,y,w] = (numerator/denominator) + additive_constants[x,y]
    
    maxx = 0
    for w in xrange(number_depletion_steps):
      for x in xrange(11):
        for y in xrange(11):
          if(btf_matrix[x,y,w] > maxx):
            maxx = btf_matrix[x,y,w]

    print maxx
    return maxx


 
def average_kinf_values_over_burnup(kinf_one, kinf_two, kinf_three, kinf_four, kinf_five, kinf_six):
#Averages the values of Kinf over the bundle, then calculates an average bundle K-infinity value for each timestep.
    average_kinf = 0
    average_kinf_list = []
    number_depletion_steps = len(kinf_two)
#    lattice_location_one = 9 #inches
#    lattice_location_two = 64
#    lattice_location_three = 140
    lattice_locations = read_lattice_locations('input_data.txt') 
    axial_power_distribution_file = open('axial_power_distribution.txt','r')
    axial_power_lines = axial_power_distribution_file.readlines()
    axial_power_distribution_file.close()
    axial_power_list = []
    number_powers = 0
    power_sum = 0
    number_axial_positions = 0
    for line in axial_power_lines:
      temp_power = line.strip().split()
      power = float(temp_power[0])
      axial_power_list.append(power)
      number_powers = number_powers+1
      power_sum+=power
      number_axial_positions+=1
    for w in xrange(number_depletion_steps):
      average_kinf = 0
      for z in xrange(number_axial_positions):
        if(z <= lattice_locations[0]):
          interpolate = z - 0
          interpolate = interpolate/lattice_locations[0]
          temp_matrix = kinf_one[w]+ (kinf_two[w]-kinf_one[w])*interpolate
          average_kinf += temp_matrix*axial_power_list[z]
        elif(z > lattice_locations[0] and z < lattice_locations[1]):
          interpolate = z - lattice_locations[0]
          interpolate = interpolate/(lattice_locations[1]-lattice_locations[0])
          temp_one = kinf_two[w]
          temp_two = kinf_three[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          average_kinf += temp_matrix*axial_power_list[z]
        elif(z == lattice_locations[1]):
          average_kinf += kinf_three[w]*axial_power_list[z]
        elif(z > lattice_locations[1] and z < lattice_locations[2]):
          interpolate = z - lattice_location_two
          interpolate = interpolate/(lattice_locations[2] - lattice_locations[1])
          temp_one = kinf_three[w]
          temp_two = kinf_four[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          average_kinf += temp_matrix*axial_power_list[z]
        elif(z == lattice_locations[2]):
          average_kinf += kinf_four[w]*axial_power_list[z]
        elif(z > lattice_locations[2] and z < lattice_locations[3]):
          interpolate = z - lattice_locations[2]
          interpolate = interpolate/(lattice_locations[3] - lattice_locations[2])
          temp_one = kinf_four[w]
          temp_two = kinf_five[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          average_kinf += temp_matrix*axial_power_list[z]
        elif(z == lattice_locations[3]):
          average_kinf += kinf_four[w]*axial_power_list[z]
        else:
          interpolate = z - lattice_locations[3]
          interpolate = interpolate/(number_axial_positions - lattice_locations[3])
          temp_matrix = kinf_five[w] + (kinf_six[w] - kinf_five[w])*interpolate
          average_kinf += temp_matrix*axial_power_list[z]
            
      average_kinf_list.append(average_kinf/power_sum)
	
    return average_kinf_list

def calculate_bundle_cost(average_kinf_values, btf_value):
#Calculates teh cost for bundles.                
    penalty = 0
    kinf_weight = 100
    temp_one =  average_kinf_values - 1.05
    if(abs(temp_one) > 0.005):
      penalty+= kinf_weight*abs(temp_one)
    score = (20/btf_value)-penalty
    return score  
                
def single_zone_btf_calculation(kinf_list_one, kinf_list_two, power_list_one, power_list_two,upper_lattice_location, lower_lattice_location):
#Calculates boiling transition factor for a single region.
     
    additive_constants = np.matrix([[ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20]])

    weight_side = 0.2
    weight_corner = 0.05

    axial_power_distribution_file = open('axial_power_distribution.txt','r')
    axial_power_lines = axial_power_distribution_file.readlines()
    axial_power_distribution_file.close()
    axial_power_list = []
    number_powers = 0
    power_sum = 0
    for line in axial_power_lines:
      temp_power = line.strip().split()
      power = float(temp_power[0])
      axial_power_list.append(power)
      number_powers = number_powers+1
      power_sum+=power
    average_power = power_sum/number_powers
    number_depletion_steps = len(kinf_list_one)
    number_axial_positions = len(axial_power_list)

    for i in xrange(number_axial_positions):
      temp_power = axial_power_list[i]
      temp_power = temp_power/average_power
      axial_power_list[i] = temp_power
    btf_matrix = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    power_matrix = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    number_corners = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    number_sides = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    square_corner = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    square_sides = np.zeros((10,10,number_axial_positions, number_depletion_steps))
    power_zones = np.zeros((10,10,number_axial_positions, number_depletion_steps))

    #Makes power matrix lattice for calculating BTF
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        #Bottom Lattice Calculations
        if(z >= lower_lattice_location and z <= upper_lattice_location):
          interpolate = z - lower_lattice_location
          interpolate = interpolate/(upper_lattice_location-lower_lattice_location)
          temp_one = power_list_one[w][:,:]
          temp_two = power_list_two[w][:,:]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          temp_matrix = axial_power_list[z]*temp_matrix
          power_matrix[:,:,z,w] = temp_matrix                                                                                                      
                                
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(power_matrix[x,y,z,w] > 0):
              power_zones[x,y,z,w] = 1

    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(x == 0):
              pass
            elif(x == 9):
              pass
            elif(y == 0):
              pass
            elif(y == 9):
              pass
            else:
              number_corners[x,y,z,w] = power_zones[x-1,y-1,z,w] +  power_zones[x-1,y+1,z,w] + power_zones[x+1,y-1,z,w] + power_zones[x+1,y+1,z,w]
              number_sides[x,y,z,w] = power_zones[x-1,y-1,z,w] +  power_zones[x-1,y+1,z,w] + power_zones[x+1,y-1,z,w] + power_zones[x+1,y+1,z,w]

    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(x == 0):
              pass
            elif(x == 9):
              pass
            elif(y == 0):
              pass
            elif(y == 9):
              pass
            else:
              square_corner[x,y,z,w] = power_matrix[x-1,y-1,z,w]**0.5 + power_matrix[x-1,y+1,z,w]**0.5 + power_matrix[x+1,y-1,z,w]**0.5 + power_matrix[x+1,y+1,z,w]**0.5
              square_sides[x,y,z,w] = power_matrix[x-1,y-1,z,w]**0.5 +  power_matrix[x-1,y+1,z,w]**0.5 + power_matrix[x+1,y-1,z,w]**0.5 + power_matrix[x+1,y+1,z,w]**0.5


    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(power_matrix[x,y,z,w] > 0):
              numerator = power_matrix[x,y,z,w]**0.5 + square_corner[x,y,z,w]*weight_corner + square_sides[x,y,z,w]*weight_side
              denominator = 1 + number_sides[x,y,z,w]*weight_side + number_corners[x,y,z,w]*weight_corner
              btf_matrix[x,y,z,w] = (numerator/denominator) + additive_constants[x,y]
#    print number_axial_positions
#    print number_depletion_steps 
    kinf_matrix = np.zeros((number_axial_positions,number_depletion_steps))
    kinf_sum = 0
    kinf_count = 0
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        if(z >= lower_lattice_location and z <= upper_lattice_location):
          interpolate = z - lower_lattice_location
          interpolate = interpolate/(upper_lattice_location-lower_lattice_location)
          temp_one = kinf_list_one[w]
          temp_two = kinf_list_two[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          kinf_matrix[z,w] = temp_matrix
          kinf_sum+=temp_matrix
          kinf_count+=1
        else: pass



    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(power_matrix[x,y,z,w] > 0):
              btf_matrix[x,y,z,w] = kinf_matrix[z,w]*kinf_count*btf_matrix[x,y,z,w]/kinf_sum

    print 'STill working'
    max_btf_value = np.zeros(number_depletion_steps)
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(btf_matrix[x,y,z,w] > max_btf_value[w]):
              max_btf_value[w] = btf_matrix[x,y,z,w]*100
    return max_btf_value
 
def average_btf_value(btf_list):
    btf_sum = 0
    btf_count = 0
    timestep_sum = 0
    for btf in btf_list:
      if(btf_count == 0): timestep = 0.1
      elif(btf_count == 1): timestep = 0.4
      else: timestep = 0.5
      btf_sum+=btf*timestep
      btf_count+=1
      timestep_sum+=timestep
    average_btf = btf_sum/timestep_sum
    return average_btf

def average_kinf_value(kinf_list):
    kinf_sum = 0
    kinf_count = 0
    timestep_sum = 0
    for kinf in kinf_list:
      if(kinf_count == 0): timestep = 0.1
      elif(kinf_count == 1): timestep = 0.4
      else: timestep = 0.5
      kinf_sum+=kinf*timestep
      kinf_count+=1
      timestep_sum+=timestep
    average_kinf = kinf_sum/timestep_sum
    return average_kinf

def read_lattice_locations(input_file_name):
    input_file = open(input_file_name,'r')
    input_lines = input_file.readlines()
    input_file.close()
    
    position_list = []
    for line in input_lines:
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Lattice_position'):
          position_list.append(float(elems[1]))
         
    return (position_list)
     
