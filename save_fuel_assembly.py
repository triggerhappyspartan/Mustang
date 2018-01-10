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
    k_inf_list = []
    for line in file_lines:
      elems = line.strip().split()
      if(len(elems) == 3):
        if(elems[0] == '2D' and elems[1] == 'k-infinity:'):
          k_inf_list.append(float(elems[2]))
    return k_inf_list

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
        power_matrix = np.zeros((10,10),dtype=np.float)
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

def calculate_btf(k_inf_one,k_inf_two,k_inf_three,k_inf_four,power_list_one,power_list_two,power_list_three,power_list_four):
#A function to calculate the BTF value for the assembly uses the power distribution from the Casmo lattice files and 
#the power map distribution.
    lattice_location_one = 6 #inches    
    lattice_location_two = 40
    lattice_location_three = 108
    lattice_location_four = 142

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
    leng_one = len(power_list_one)
    leng_two = len(power_list_two)
    leng_three = len(power_list_three)
    leng_four = len(power_list_four)	
    number_depletion_steps = leng_one
    if(number_depletion_steps > leng_two):
      number_depletion_steps = leng_two
    if(number_depletion_steps > leng_three):
      number_depletion_steps = leng_three
    if(number_depletion_steps > leng_four):
      number_depletion_steps = leng_four

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
    kinf_matrix = np.zeros((number_axial_positions, number_depletion_steps))

#Makes power matrix lattice for calculating BTF              
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        #Bottom Lattice Calculations
        if(z <= lattice_location_one):
          power_matrix[:,:,z,w] = axial_power_list[z]*power_list_one[w][:,:]
        elif(z > lattice_location_one and z < lattice_location_two):
          interpolate = z - lattice_location_one
          interpolate = interpolate/(lattice_location_two-lattice_location_one)
          temp_one = power_list_one[w][:,:]
          temp_two = power_list_two[w][:,:]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          temp_matrix = axial_power_list[z]*temp_matrix
          power_matrix[:,:,z,w] = temp_matrix
        elif(z == lattice_location_two):
          power_matrix[:,:,z,w] = axial_power_list[z]*power_list_two[w][:,:]
        elif(z > lattice_location_two and z < lattice_location_three):      
          interpolate = z - lattice_location_two        
          interpolate = interpolate/(lattice_location_three - lattice_location_two)        
          temp_one = power_list_two[w][:,:]
          temp_two = power_list_three[w][:,:]        
          temp_matrix = temp_one + (temp_two - temp_one)*interpolate
          temp_matrix = axial_power_list[z]*temp_matrix
          power_matrix[:,:,z,w] = temp_matrix        
        elif(z == lattice_location_three):
          power_matrix[:,:,z,w] = axial_power_list[z]*power_list_three[w][:,:]
        elif(z > lattice_location_three and z < lattice_location_four):  
          interpolate = z - lattice_location_three        
          interpolate = interpolate/(lattice_location_four - lattice_location_three)        
          temp_one = power_list_three[w][:,:]        
          temp_two = power_list_four[w][:,:]
          temp_matrix = temp_one + (temp_two - temp_one)*interpolate        
          temp_matrix = axial_power_list[z]*temp_matrix        
          power_matrix[:,:,z,w] = temp_matrix
        elif(z >= lattice_location_four):
          power_matrix[:,:,z,w] = axial_power_list[z]*power_list_four[w][:,:]        
          
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
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        #Bottom Lattice Calculations
        if(z <= lattice_location_one):
          interpolate = z - 0
          interpolate = interpolate/lattice_location_one
          temp_matrix = k_inf_one[w]*interpolate
          kinf_matrix[z,w] = temp_matrix
        elif(z > lattice_location_one and z < lattice_location_two):
          interpolate = z - lattice_location_one
          interpolate = interpolate/(lattice_location_two-lattice_location_one)
          temp_one = k_inf_one[w]
          temp_two = k_inf_two[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          kinf_matrix[z,w] = temp_matrix
        elif(z == lattice_location_two):
          kinf_matrix[z,w] = k_inf_two[w]
        elif(z > lattice_location_two and z < lattice_location_three):
          interpolate = z - lattice_location_two
          interpolate = interpolate/(lattice_location_three - lattice_location_two)
          temp_one = k_inf_two[w]
          temp_two = k_inf_three[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          kinf_matrix[z,w] = temp_matrix
        elif(z == lattice_location_three):
          kinf_matrix[z,w] = k_inf_two[w]
        elif(z > lattice_location_three and z < lattice_location_four):
          interpolate = z - lattice_location_three
          interpolate = interpolate/(lattice_location_four - lattice_location_three)
          temp_one = k_inf_three[w]
          temp_two = k_inf_four[w]
          temp_matrix = temp_one +(temp_two-temp_one)*interpolate
          kinf_matrix[z,w] = temp_matrix
        elif(z >= lattice_location_four):
          interpolate = z - lattice_location_four
          interpolate = interpolate/(number_axial_positions - lattice_location_four)
          temp_matrix = k_inf_one[w]*interpolate
          kinf_matrix[z,w] = temp_matrix
    
#    for w in xrange(number_depletion_steps):
#      k_inf_sum = 0            
#      for z in xrange(number_axial_positions):
#        print btf_matrix[:,:,z,w]
#        print kinf_matrix[z,w]
#        btf_matrix[:,:,z,w] = kinf_matrix[z,w] * btf_matrix[:,:,z,w]   
#        k_inf_sum+= kinf_matrix[z,w]      
#      btf_matrix = btf_matrix[:,:,:,w]/k_inf_sum
#    print 'STill working'    
    max_btf_value = np.zeros(number_depletion_steps)
    for w in xrange(number_depletion_steps):
      for z in xrange(number_axial_positions):
        for x in xrange(10):
          for y in xrange(10):
            if(btf_matrix[x,y,z,w] > max_btf_value[w]):    
              max_btf_value[w] = btf_matrix[x,y,z,w]  
    return max_btf_value            
                
def average_kinf_values_over_burnup(kinf_one, kinf_two, kinf_three, kinf_four):
#Averages the values of Kinf over the bundle, then calculates an average bundle K-infinity value for each timestep.
    average_kinf = 0
    average_kinf_list = []
    number_depletion_steps = len(kinf_one)
    for k in xrange(number_depletion_steps):
      average_kinf+= kinf_one[k]/4
      average_kinf+= kinf_two[k]/4
      average_kinf+= kinf_three[k]/4
      average_kinf+= kinf_four[k]/4
      average_kinf_list.append(average_kinf)
	
    return average_kinf_list

def calculate_bundle_cost(lower_kinf_values, upper_kinf_values, btf_values):
#Calculates teh cost for bundles.                
    number_depletion_steps = len(btf_values)
    score = 0
    for w in xrange(number_depletion_steps):
      temp_one =  lower_kinf_values[w]*10
      temp_two =  upper_kinf_values[w]*10
      temp_two = btf_values[w]
      score+= temp_one
      score+= temp_two
      score+= 20/btf_values[w]
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
              max_btf_value[w] = btf_matrix[x,y,z,w]
    return max_btf_value
 


