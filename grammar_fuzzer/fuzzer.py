from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from database import *
from tqdm import tqdm
import random
import sys
import os
import time
import datetime

from random_utils import *
from config import *
from grammar import *
from ConstraintSolver import *

DEFAULT_CONFIG = 'config.json'

# Use command argument as config file path if specified, otherwise use default
if len(sys.argv) == 1:
    print('Using default configuration file:', DEFAULT_CONFIG)
    CONFIG_PATH = DEFAULT_CONFIG
else:
    print('Using specified configuration file:', sys.argv[1])
    CONFIG_PATH = sys.argv[1]
config = Config(CONFIG_PATH)

# Use specified random seed if specified, otherwise use time
if config.seed:
    print('Using random seed specified in configuration file:', config.seed)
    random.seed(config.seed)
else:
    print('No random seed specified, defaulting to current timestamp as seed')
    now = datetime.now()
    random.seed(now)

# Specify database configuration
db = config.db

numInserts = 0
numSuccessesInsert = 0
numFailuresInsert = 0
totalInsertFaults = 0
numSwappedInsertFaults = 0
numNoopInsertFaults = 0

numDeletes = 0
numSuccessesDelete = 0
numFailuresDelete = 0
numNoopDeleteFaults = 0

dbInterface = Query()

fields = config.fields
types = config.types
comparators = config.comparators

fuzzer = GrammarFuzzer(grammar=sql_grammar(config),
                       start_symbol='<Query>', max_nonterminals=5)

solver = ConstraintSolver(config)


def generate_target(selectSqlStatement, vals):
    keys = extract_column_names(selectSqlStatement)
    return [tuple([vals[k] for k in keys])]


def generate_delete_from_ssn(ssnToDelete, probablityOfFault):
    global numNoopDeleteFaults
    global db
    shouldGenerateFaultyDelete = 0 < random.uniform(0, 1) < probablityOfFault
    if(shouldGenerateFaultyDelete):
        numNoopDeleteFaults += 1
        return ''
    else:
        return f'DELETE FROM "{db}" WHERE ssn = "{ssnToDelete}"'


def generate_insert_from_values(keys, vals, probablityOfFault):
    global totalInsertFaults
    global numNoopInsertFaults
    global numSwappedInsertFaults
    shouldGenerateFaultyInsert = 0 < random.uniform(0, 1) < probablityOfFault
    if(shouldGenerateFaultyInsert):
        totalInsertFaults += 1
        selectedFailure = random.sample(['noop', 'swapped_values'], 1)[0]
        if(selectedFailure == 'swapped_values'):
            numSwappedInsertFaults += 1
            insert = insert_from_swapped_values(keys, vals)
        elif(selectedFailure == 'noop'):
            numNoopInsertFaults += 1
            return ''
    else:
        insert = insert_from_values(vals)

    return insert


def insert_from_swapped_values(keys, vals):
    attributeToInjectFault = random.choice(keys)
    if(attributeToInjectFault == 'age'):
        vals[attributeToInjectFault] += random.randrange(1, 10)
    else:
        vals[attributeToInjectFault] = random_flip_char(
            vals[attributeToInjectFault])
    result = insert_from_values(vals)
    return result


def insert_from_values(vals):
    values = 'VALUES (' + ', '.join([f'"{v}"' for v in vals.values()]) + ')'
    insert = 'INSERT INTO {} {}'.format(db, values)
    return insert


def insert_from_query(sql):
    v = solver.generate_values(sql)
    return insert_from_values(v) if v else None


def consistency_checker_insert(testNum, select, insert, before, after, target):
    global numFailuresInsert, numSuccessesInsert
    difference = list_diff(after, before)
    isConsistent = difference == target

    outputToSuccessTxt = f'''
    #{testNum}:
        {select}
        {insert}
        Successful Insert \u2713\n
    '''
    outputToFailureTxt = f'''
    #{testNum}:
        Initial query result: {before}
        Final query result: {after}
        
        {select}
        {insert}
        Failed Insert \u274c
        Actual difference: {difference}
        Expected difference: {target}\n
    '''

    if(isConsistent):
        print('Successful Insert \u2713')
        successWriter = open('./output/insert/successes.txt', 'a')
        successWriter.write(outputToSuccessTxt)
        numSuccessesInsert += 1
        return True
    else:
        numFailuresInsert += 1
        print(
            f'Failed Insert \u274c\nactual difference: {difference} vs expected difference: {target}\n')
        failureWriter = open('./output/insert/failures.txt', 'a')
        failureWriter.write(outputToFailureTxt)
        return False


def consistency_checker_delete(testNum, selectAll, delete, before, after, target):
    global numFailuresDelete, numSuccessesDelete
    difference = list_diff(before, after)
    isConsistent = difference == target

    outputToSuccessTxt = '\n#{}:\n\n{}\n{}\nSuccessful Delete \u2713\n\n'.format(
        testNum, selectAll, delete)
    outputToFailureTxt = '\n#{}:\n{}\n{}\n\n{}\n{}\nFailed Delete \u274c\nactual difference: {} vs expected difference: {}\n\n'.format(
        testNum, before, after, selectAll, delete, difference, target)

    if(isConsistent):
        print('Successful Delete \u2713')
        successWriter = open('./output/delete/successes.txt', 'a')
        successWriter.write(outputToSuccessTxt)
        numSuccessesDelete += 1
        return True
    else:
        print(
            f'Failed Delete \u274c\nactual difference: {difference} vs expected difference: {target}\n')
        failureWriter = open('./output/delete/failures.txt', 'a')
        failureWriter.write(outputToFailureTxt)
        numFailuresDelete += 1
        return False


def insert_runner(testNum, probablityOfFaults):
    vals = None
    while not vals:
        select = fuzzer.fuzz()
        vals = solver.generate_values(select)

    keys = extract_column_names(select)
    insert = generate_insert_from_values(keys, vals.copy(), probablityOfFaults)

    before = dbInterface.executeSelectStatement(select)
    dbInterface.executeSqlStatement(insert)
    after = dbInterface.executeSelectStatement(select)

    target = generate_target(select, vals)
    consistency_checker_insert(testNum, select, insert, before, after, target)


def delete_runner(testNum, probablityOfFaults):
    global db
    selectAll = f'SELECT * FROM {db}'

    before = dbInterface.executeSelectStatement(selectAll)

    if len(before) == 0:
        return 'EMPTY_DB'

    target = [random.choice(before)]

    delete = generate_delete_from_ssn(target[0][-1], probablityOfFaults)
    dbInterface.executeSqlStatement(delete)
    after = dbInterface.executeSelectStatement(selectAll)

    consistency_checker_delete(
        testNum, selectAll, delete, before, after, target)


numTests = config.num_tests
probabilityOfFaultsInsert = config.insert_fault_probability
probabilityOfFaultsDelete = config.delete_fault_probability

print('\n')
tic = time.perf_counter()

block_print()
for i in tqdm(range(numTests)):
    print(f'\n#{i+1}:\n')
    insertOrDelete = random.sample(['insert', 'delete'], 1)[0]
    forceInsert = False

    if insertOrDelete == 'delete':
        result = delete_runner(i+1, probabilityOfFaultsDelete)
        if(result == 'EMPTY_DB'):
            forceInsert = True
        else:
            numDeletes += 1
    if insertOrDelete == 'insert' or forceInsert:
        insert_runner(i+1, probabilityOfFaultsInsert)
        numInserts += 1
toc = time.perf_counter()
enable_print()


print('\n---------- SQLFUZZ RESULTS -------------\n')
print(f'{numTests} Total tests in {toc - tic:0.4f} seconds')
print(f'Generated {numInserts} Insert Tests')
print(f'{numSuccessesInsert} Succeeded\n{numFailuresInsert} Failed\n')
print(f'Generated {numDeletes} Delete Tests')
print(f'{numSuccessesDelete} Succeeded\n{numFailuresDelete} Failed\n')

print('--- INJECTED INSERT FAULTS RESULTS ---\n')
print(f'Probablity of insert fault: {probabilityOfFaultsInsert}')
print(
    f'Number of noop inserts injected: {numNoopInsertFaults}\nNumber of swapped values inserts injected : {numSwappedInsertFaults}\nTotal: {totalInsertFaults}')
try:
    print('Caught {}/{} -- {:.2f}%'.format(numFailuresInsert,
          totalInsertFaults, numFailuresInsert/totalInsertFaults * 100))
except ZeroDivisionError:
    print('No inserts faults injected, either increase number of tests or probablity of insert fault injected')

print('\n--- INJECTED DELETE FAULTS RESULTS ---\n')
print(f'Probablity of delete failure: {probabilityOfFaultsDelete}')
print(
    f'Number of noop deletes injected: {numNoopDeleteFaults}\nTotal: {numNoopDeleteFaults}')
try:
    print('Caught {}/{} -- {:.2f}%'.format(numFailuresDelete,
          numNoopDeleteFaults, numFailuresDelete/numNoopDeleteFaults * 100))
except ZeroDivisionError:
    print('No delete faults injected, either increase number of tests or probablity of delete fault injected')
print('\n----------------------------------------')
