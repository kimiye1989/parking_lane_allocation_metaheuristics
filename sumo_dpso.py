#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 17:04:57 2020
@author: qmy
"""

import os.path
from random import sample
from xml.dom.minidom import parse

import runner
import vehicle_stops
import numpy as np
import pandas as pd
import generate_flows as gf

import time


##################################################################################
############################      Initiate        ################################
##################################################################################
class Swarm:
    particles = None
    bpos = None
    bfit = None
    
    def __init__(self):
        self.particles = []
        self.bpos = None
        self.bfit = None
        
class Particle:
    pos = None
    velo = None
    bpos = None
    fit = None
    bfit = None

    def __init__(self):
        self.pos = None
        self.velo = None
        self.bpos = None
        self.fit = None
        self.bfit = None


def Init_swarm(pop, dim):    
    swarm = Swarm()
    for i in range(pop):                                       
        new_par = Particle()                                              # Generate a particle
        new_par = Init_particles(new_par, dim)                            # Value this particle
        swarm.particles.append(new_par)
    return swarm


def Init_particles(par, dim):
    p = np.random.randint(2, size = dim)                                  # Create position array
    par.pos = p.tolist()

    if par.velo == None:
        par.velo = np.random.uniform(-1,1, size=dim)*0.5
    
    if par.bpos == None:
        par.bpos = np.copy(par.pos)                                       # init bpos for a particle
    
    if par.fit == None:
        par.fit = 0                                                       # init fit for a particle
    
    if par.bfit == None:
        par.bfit = 0                                                      # init bfit for a particle
    return par


def init_population(n, s):
    s2 = int(s * PROVISION_RATE)
    population = []
    for i in range(n):
        individual = [False for _ in range(s)]
        for index in sample(range(s), s2):
            individual[index] = True
        population.append(individual)

    return population


##################################################################################
############################      Translate       ################################
##################################################################################

def Init_Translate(population, swarm, scores):
    swarm.bfit = min(scores)
    swarm.bpos = population[0]
    
    for (idx, par) in enumerate(swarm.particles):
        par.pos = population[idx]
        par.fit = scores[idx]
        par.bpos = par.pos
        par.bfit = par.fit
    
    return swarm


def Update_P_G(swarm, scores):
    for (idx, par) in enumerate(swarm.particles):
        par.fit = scores[idx]
        
        if par.bfit > scores[idx]:
            par.bfit = np.copy(scores[idx])
            par.bpos = np.copy(par.pos)
      
    # update bpos and bfit for a swarm #
    bestfit = min(scores)
    
    for (i, j) in enumerate(scores):
        if j == bestfit:
            bidx = i
            bestpos = swarm.particles[bidx].pos   
            
    if swarm.bfit > bestfit:
        swarm.bfit = np.copy(bestfit)
        swarm.bpos = np.copy(bestpos)

    return swarm


def Update_Velo_Pos(itera, w, swarm, c1, c2, alpha, total):
    g_bp = swarm.bpos
    
    e1 = np.random.rand()
    e2 = np.random.rand()
    e3 = np.random.rand()
    e4 = np.random.rand()
            
    for (j, par) in enumerate(swarm.particles):
        p_bp = par.bpos
        
        for (i, v) in enumerate(par.velo):
            
            if itera <= 3:
                e3 = 1
            if itera <= 5:
                e4 = 1
            
            par.velo[i] = w*v + c1*e1*(e3*p_bp[i] - par.pos[i]) + c2*e2*(e4*g_bp[i] - par.pos[i])
            par.pos[i] = w*par.pos[i] + c1*e1*(e3*p_bp[i] - par.pos[i]) + c2*e2*(e4*g_bp[i] - par.pos[i])
            top_k= int(alpha * total)
            
        arr = np.array(par.pos)
        top_k_idx=arr.argsort()[::-1][0:top_k]
            
        for i in top_k_idx:
            par.pos[i] = 1
            par.pos[not i] =0
            
    return swarm


def Forward_Translate(swarm):
    pop=[]
    for par in swarm.particles:
        pop.append(par.pos)
    return pop
    

##################################################################################
############################      Evaluate       #################################
##################################################################################
    
def hash_individual(individual):
    return str(hash(tuple(individual)))

individuals_count = 0

def evaluate(individual):
    h = hash_individual(individual)
    try:
        return evaluations[h]
    except KeyError:
        global individuals_count
        individuals_count += 1
        print(f'Evaluating individual #{individuals_count}')
        vehicle_stops.remove_stops(individual)
        runner.start(h)
        eval = evaluations[h] = vehicle_stops.total_delay(h)
        return eval


def eval_population(population):
    return [evaluate(individual) for individual in population]
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    #     futures = [executor.submit(evaluate, individual) for individual in population]
    #     concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    #     for future in futures:
    #         evals.append(future.result())
    #
    # return evals

def quality_check(partic, alpha):
    s = len(partic)
    d = sum(partic) - int(s * alpha)
    if d > 0:
        # too many 1s
        indices = filter(lambda i: partic[i], range(s))
    else:
        # too many 0s
        indices = filter(lambda i: not partic[i], range(s))
        d = -d

    indices = list(indices)
    s = sample(indices, d)
    for index in s:
        partic[index] = not partic[index]
        
    return partic

def Calculate(sw):
    pop = Forward_Translate(sw)
    evals = eval_population(pop)
    return evals

##################################################################################
############################      Read & Write      ##############################
##################################################################################

def str_individual(individual):
    return ''.join(map(lambda pa: '1' if pa else '0', individual))



def print_population(population, evals, file):
    new_eval_list = []
    indices = sorted(range(len(population)), key=lambda i: evals[i])
    for i in indices:
        individual = str_individual(population[i])
        eval = '{:.2f}'.format(evals[i])
        file.write(f'{eval}: {individual} ({i})\n')
        
        new_eval_list.append(eval)
    return new_eval_list


def read_input(filename):
    generation = None
    with open(filename, 'rt') as file:
        for line in file:
            if line.endswith('\n'):
                line = line[:-1]
            if line == '':
                pass
            elif line.startswith('generation'):
                gen = int(line.split(' ')[1][:-1])
                generation = generations[gen]
            else:
                eval, indiv, index = line.split(' ')
                eval = float(eval[:-1])
                index = int(index[1:-1])
                indiv = list(map(lambda c: True if c == '1' else False, indiv))
                generation[index] = indiv
                evaluations[hash_individual(indiv)] = eval


def count_veh():
    doc = parse('grid.rou.xml')
    return len(doc.getElementsByTagName('vehicle'))

##################################################################################
########################      Test Experiement      ##############################
##################################################################################

Veh_number = gf.all_vehi
GENERATIONS = 100
POPULATION_COUNT = 12
PA_COUNT = 80
PROVISION_RATE = 0.8
WORK_FILENAME = 'Logs_DPSO[%.2f,%d].txt'%(PROVISION_RATE,gf.MaxFlow)
Converge_filename = 'Results_DPSO[%.2f,%d].csv'%(PROVISION_RATE,gf.MaxFlow)
VEHICLE_COUNT_FILENAME = 'vehicle_count_DPSO'
generations = [[None for j in range(POPULATION_COUNT)] for i in range(GENERATIONS)]
evaluations = {}

c1   = 2
c2   = 2
w = 0.8


if __name__ == '__main__':
    if os.path.isfile(WORK_FILENAME):
        read_input(WORK_FILENAME)
    with open(VEHICLE_COUNT_FILENAME, 'wt') as file:
        n = count_veh()
        file.write(str(n))
    with open(WORK_FILENAME, 'at', buffering=1) as file:
        vehicle_stops.load_parking_areas()
        value_list = []
        
        if generations[0][0] is None:
            
            start_time = time.time()
            
            sw = Init_swarm(POPULATION_COUNT, PA_COUNT)
            generations[0] = init_population(POPULATION_COUNT, PA_COUNT)
            
            scores = eval_population(generations[0])
            
            sw = Init_Translate(generations[0], sw, scores)
            
            file.write(f'Vehicle Number: {Veh_number}\n')
            file.write(f'Max_flowrate: {gf.MaxFlow}\n')
            file.write(f'Parking Service Rate: {PROVISION_RATE}; \n')
            file.write(f'\n')
            file.write(f'generation 0:\n')
            
            s = print_population(generations[0], scores, file)
            file.write('\n')
            
            value_list.append(s)   # store the delays as a list of list
            
            

        for i in range(1, GENERATIONS):
            if generations[i][0] is None:
                sw = Update_Velo_Pos(i, w, sw, c1, c2, PROVISION_RATE, PA_COUNT)
                
                scores = Calculate(sw)
                sw = Update_P_G(sw, scores)
            
                generations[i] = Forward_Translate(sw)
                file.write(f'generation {i}:\n')
                s = print_population(generations[i], scores, file)
                file.write('\n')
                
                value_list.append(s)   # store the delays as a list of list
                
            if i == GENERATIONS-1:
                end_time = time.time()
                execution_time = end_time - start_time
                file.write(f'Total Running Time: {execution_time}')
                
                pd.DataFrame(np.array(value_list)).to_csv(Converge_filename)
                






