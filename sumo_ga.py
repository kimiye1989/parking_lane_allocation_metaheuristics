import os.path
from random import randrange, sample
from xml.dom.minidom import parse
from xml.etree import ElementTree as ET

import runner
import vehicle_stops

import numpy as np
import pandas as pd
import time



##################################################################################
#########################      GA_Main Algorithm       ###########################
##################################################################################

def init_population(n, s):
    s2 = int(s * PROVISION_RATE)
    population = []
    for i in range(n):
        individual = [False for _ in range(s)]
        for index in sample(range(s), s2):
            individual[index] = True
        population.append(individual)
    return population

def read_xml(ori_file):
    tree = ET.parse(ori_file)
    root = tree.getroot()
    return tree, root


def crossover(i0, i1):
    individuals = [i0, i1]
    s = len(i0)
    child = [individuals[randrange(2)][i] for i in range(s)]

    d = sum(child) - int(s * PROVISION_RATE)
    if d > 0:
        # too many 1s
        indices = filter(lambda i: child[i], range(s))
    else:
        # too many 0s
        indices = filter(lambda i: not child[i], range(s))
        d = -d

    indices = list(indices)
    s = sample(indices, d)
    for index in s:
        child[index] = not child[index]

    # DEBUG
    # print(str_individual(i0) + '\n' + str_individual(i1))
    # c = child.copy()
    # for index in s:
    #     c[index] = 'X'
    # for i in range(len(c)):
    #     if c[i] != 'X':
    #         if c[i]:
    #             c[i] = '1'
    #         else:
    #             c[i] = '0'
    # print(''.join(map(str, c)))
    # print()

    return child


def eval_population(population):
    return [evaluate(individual) for individual in population]
    # with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    #     futures = [executor.submit(evaluate, individual) for individual in population]
    #     concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    #     for future in futures:
    #         evals.append(future.result())
    #
    # return evals


def mate(population):
    evals = eval_population(population)
    indices = sorted(range(len(population)), key=lambda i: evals[i])

    # produce 2 children per couple
    
    ranked_population = [x for _,x in sorted(zip(evals,population))]
    
    good_parents = ranked_population[:20]
    
    elit_parents = ranked_population[:10]
    
    next_gen = [item for item in elit_parents]
    
    n2 = len(good_parents) // 2
    
    for i in range(n2):
        parent0 = good_parents[i]
        parent1 = good_parents[i+10]
        for j in range(4):
            child = crossover(parent0, parent1)
            next_gen.append(child)

    return next_gen


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


def str_individual(individual):
    return ''.join(map(lambda pa: '1' if pa else '0', individual))


def hash_individual(individual):
    return str(hash(tuple(individual)))


def print_population(population, file):
    new_eval_list = []
    
    evals = eval_population(population)   # a list of delay values #
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
    doc = parse('meta.rou.xml')
    return len(doc.getElementsByTagName('vehicle'))


##################################################################################
########################      Test Experiement      ##############################
##################################################################################

treex, rootx = read_xml('meta_stops.rou.xml')
lis = rootx.findall(".//vehicle")
Veh_number = len(lis)

fff = pd.read_csv('input.csv',header=None)
PROVISION_RATE = float(fff.iloc[1,1])
MaxFlow = int(fff.iloc[0,1])

GENERATIONS = 3
POPULATION_COUNT = 50
PA_COUNT = 80

WORK_FILENAME = 'output/Logs_GA[%.2f,%d].txt'%(PROVISION_RATE,MaxFlow)
Converge_filename = 'output/Results_GA[%.2f,%d].csv'%(PROVISION_RATE,MaxFlow)
VEHICLE_COUNT_FILENAME = 'output/vehicle_count[%.2f,%d].csv'%(PROVISION_RATE,MaxFlow)
generations = [[None for j in range(POPULATION_COUNT)] for i in range(GENERATIONS)]
evaluations = {}

if __name__ == '__main__':
    if os.path.isfile(WORK_FILENAME):
        read_input(WORK_FILENAME)
    with open(VEHICLE_COUNT_FILENAME, 'wt') as file:
        n = count_veh()
        file.write(str(n))
    with open(WORK_FILENAME, 'at', buffering=1) as file:
        vehicle_stops.load_parking_areas()
        value_list = []
        start_time = time.time()
        if generations[0][0] is None:
            pop = generations[0] = init_population(POPULATION_COUNT, PA_COUNT)
            
            file.write(f'Vehicle Number: {Veh_number}\n')
            file.write(f'Max_flowrate: {MaxFlow}\n')
            file.write(f'Parking Service Rate: {PROVISION_RATE}\n')
            file.write(f'\n')
            file.write(f'generation 0:\n')
            
            score_list = print_population(pop, file)
            file.write('\n')
            
            value_list.append(score_list)   # store the delays as a list of list

        for i in range(1, GENERATIONS):
            if generations[i][0] is None:
                
                pop = generations[i - 1]
                pop = generations[i] = mate(pop)
                file.write(f'generation {i}:\n')
                score_list = print_population(pop, file)
                file.write('\n')
                
                value_list.append(score_list)
                
            if i == GENERATIONS-1:
                end_time = time.time()
                execution_time = end_time - start_time
                file.write(f'Total Running Time: {execution_time}')
                
                pd.DataFrame(np.array(value_list)).to_csv(Converge_filename)
