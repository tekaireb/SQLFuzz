from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from typing import Dict, Union, Any, Tuple, List
from database import Query
from tqdm import tqdm
import string
import random
import sys
import os
import time
import json

from random_utils import *


CONFIG_PATH = 'config.json'


class Config(object):
    def __init__(self, config_path):
        self.num_tests = 0

        self.db = None

        self.fields = None
        self.types = None
        self.comparators = None

        self.insert_fault_probability = 0
        self.delete_fault_probability = 0

        # Load values from configuration file
        with open(config_path, 'r') as f:
            cfg = json.loads(f.read())

            # Check validity
            assert 'database' in cfg, 'Config file must specify database properties'
            assert 'num_tests' in cfg, 'Config file must specify number of tests ("num_tests": x)'
            for prop in ['name', 'fields', 'types', 'comparators']:
                assert prop in cfg['database'], f'Config file must specify database {prop}'

            # Load number of tests
            self.num_tests = int(cfg['num_tests'])

            # Load database properties
            self.db = cfg['database']['name']
            self.fields = cfg['database']['fields']
            self.types = cfg['database']['types']
            self.comparators = cfg['database']['comparators']

            # Load fault probabilities (if specified)
            if 'fault_probabilities' in cfg:
                if 'insert' in cfg['fault_probabilities']:
                    self.insert_fault_probability = float(
                        cfg['fault_probabilities']['insert'])
                if 'delete' in cfg['fault_probabilities']:
                    self.delete_fault_probability = float(
                        cfg['fault_probabilities']['delete'])


config = Config(CONFIG_PATH)

# Specify database configuration

# db = 'Users_DB'
db = config.db
generatedSSNs = set()

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
# fields = ['name', 'age', 'email_address', 'phone_number', 'ssn']
# # TODO: Allow passing of params to specify additional constraints (e.g., numerical ranges, age should be 1 to 100)
# types = ['<Name>', '<Age>', '<Email>', '<Phone>', '<SSN>']
# comparators = ['<StringComparator>', '<Comparator>',
#                '<StringComparator>', '<StringComparator>', '<StringComparator>']

fields = config.fields
types = config.types
comparators = config.comparators

# Specify SQL Grammar for grammar-based fuzzer to generate SQL queries

Option = Dict[str, Any]
Expansion = Union[str, Tuple[str, Option]]
Grammar = Dict[str, List[Expansion]]

SQL_GRAMMAR: Grammar = {
    '<Query>':
        ['SELECT <SelList> FROM <FromList> WHERE <Condition>'],
    #  'SELECT <SelList> FROM <FromList>',
    #  'SELECT * FROM <FromList>',
        #  'INSERT INTO <FromList> VALUES ("' + '", "'.join(types) + '")'],

    '<SelList>':
        ['<Attribute>', '<SelList>, <Attribute>'],

    '<FromList>':
        ['<Relation>'],

    '<Condition>':
        ['<Comparison>', '<Condition> AND <Comparison>',
            '<Condition> OR <Comparison>'],

    '<Comparison>':
        [f'{f} {c} "{t}"' for f, c, t in zip(fields, comparators, types)],

    '<Comparator>':
        ['<', '<=', '=', '<LAngle><RAngle>', '>=', '>'],

    '<StringComparator>':
        ['=', '<LAngle><RAngle>'],

    '<LAngle>': ['<'],

    '<RAngle>': ['>'],

    '<Relation>': [db],

    '<Attribute>':
        fields,

    # Types:
    '<Name>': ['<String>'],
    '<String>': ['<Char>', '<String><Char>'],
    '<Char>': list(string.ascii_lowercase),
    '<Age>': [str(i) for i in range(2, 100)],
    # '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
    # '<Integer>': ['<Digit>', '<Integer><Digit>'],  # Only positive numbers
    '<Digit>': [str(i) for i in range(10)],
    '<Email>': ['<String>@<String>.com', '<String>@<String>.org', '<String>@<String>.edu'],
    '<Phone>': ['(<Area>)<Exchange>-<Line>'],
    '<Lead-Digit>': [str(i) for i in range(2, 10)],
    '<Area>': ['<Lead-Digit><Digit><Digit>'],
    '<Exchange>': ['<Lead-Digit><Digit><Digit>'],
    '<Line>': ['<Digit><Digit><Digit><Digit>'],
    '<SSN>': ['<Digit><Digit><Digit>-<Digit><Digit>-<Digit><Digit><Digit><Digit>']
}

fuzzer = GrammarFuzzer(grammar=SQL_GRAMMAR,
                       start_symbol='<Query>', max_nonterminals=5)


# Create values that satisfy search constraints specified in SQL query


def extract_type(sql):
    return sql[:sql.find(' ')]


def extract_column_names(selectSqlStatement):
    start = selectSqlStatement.find('SELECT')
    end = selectSqlStatement.find('FROM')
    return selectSqlStatement[start + 7:end-1].replace(',', '').split(' ')


def extract_conditions(sql):
    # Get full condition (everything after 'WHERE')
    condition_start = sql.find('WHERE')
    cond = sql[condition_start+6:] if condition_start != -1 else ''

    # Separate constraint possibilities
    conditions = cond.split(' OR ')
    if conditions == ['']:
        conditions = [cond]

    return conditions


def generate_constraints_from_conditions(conditions):
    constraint_table = dict([(field, {'max': None, 'min': None, 'eq': None, 'neq': []}) if comp == '<Comparator>'
                             else (field, {'eq': None, 'neq': []})
                             for field, comp in zip(fields, comparators)])

    condition = random.choice(conditions)
    # print('Selected condition:', condition)

    for terms in condition.split('AND'):
        # print('Terms:', terms)
        # print('Terms (split):', terms.strip().split(' '))
        field, comp, val = terms.strip().split(' ')
        val = val[1:-1]  # Remove extraneous quotes

        if comparators[fields.index(field)] == '<Comparator>':  # Integer
            val = int(val)
            if comp == '<':
                constraint_table[field]['max'] = min(
                    constraint_table[field]['max'], val - 1) if constraint_table[field]['max'] else val - 1
            elif comp == '<=':
                constraint_table[field]['max'] = min(
                    constraint_table[field]['max'], val) if constraint_table[field]['max'] else val
            elif comp == '=':
                if constraint_table[field]['eq'] and constraint_table[field]['eq'] != val:
                    print(
                        'INVALID CONSTRAINTS: specified multiple non-equivalent equals')
                    return None
                else:
                    constraint_table[field]['eq'] = val
            elif comp == '<>':
                if val not in constraint_table[field]['neq']:
                    constraint_table[field]['neq'].append(val)
            elif comp == '>=':
                constraint_table[field]['min'] = max(
                    constraint_table[field]['min'], val) if constraint_table[field]['min'] else val
            elif comp == '>':
                constraint_table[field]['min'] = max(
                    constraint_table[field]['min'], val + 1) if constraint_table[field]['min'] else val + 1

        elif comparators[fields.index(field)] == '<StringComparator>':  # String
            if comp == '=':
                if constraint_table[field]['eq'] and constraint_table[field]['eq'] != val:
                    print(
                        'INVALID CONSTRAINTS: specified multiple non-equivalent equals')
                    return None
                elif val in constraint_table[field]['neq']:
                    print(
                        'INVALID CONSTRAINTS: specified equivalent equals and not-equals')
                    return None
                else:
                    constraint_table[field]['eq'] = val
            elif comp == '<>':
                if val == constraint_table[field]['eq']:
                    print(
                        'INVALID CONSTRAINTS: specified equivalent equals and not-equals')
                    return None
                if val not in constraint_table[field]['neq']:
                    constraint_table[field]['neq'].append(val)

    for c in constraint_table.values():
        # Check min/max constraints (if they exist)
        if 'min' in c:
            if c['min'] != None and c['max'] != None and c['min'] > c['max']:
                print(
                    'INVALID CONSTRAINTS: specified minimum greater than maximum')
                return None
            # If equals is defined, ensure that it is between the min and max bounds (if each are also defined)
            if c['eq'] != None and ((c['min'] and c['eq'] < c['min']) or (c['max'] and c['eq'] > c['max'])):
                print(
                    'INVALID CONSTRAINTS: specified equals that exceeds min/max bounds')
                return None

    # print(constraint_table)
    return constraint_table


def generate_values_from_constraints(constraints):
    values = {}

    def generate_value_of_type(field):
        global generatedSSNs
        t = types[fields.index(field)]

        return (random_name() if t == '<Name>' else
                random_email() if t == '<Email>' else
                random_phone() if t == '<Phone>' else
                random_ssn(generatedSSNs) if t == '<SSN>' else
                random_string(10))

    for field, constraint in constraints.items():
        # print(f'field: {field} - constraint: {constraint}')

        # If there is an `equals` constraint, set the value to it
        if constraint['eq']:
            values[field] = constraint['eq']
            continue

        if comparators[fields.index(field)] == '<Comparator>':  # Integer
            max_val = constraint['max'] if constraint['max'] else 100
            min_val = constraint['min'] if constraint['min'] else 0
            if min_val == max_val + 1:
                val = min_val
            else:
                # print('min:', min_val, '- max:', max_val)
                val = random.randrange(min_val, max_val + 1)

            # Find new random value if value is specified under `not equals`
            while val in constraint['neq']:
                if min_val == max_val + 1:
                    val = min_val
                else:
                    # print('min:', min_val, '- max:', max_val)
                    val = random.randrange(min_val, max_val + 1)

            values[field] = val
            continue

        else:
            val = generate_value_of_type(field)

            while val in constraint['neq']:
                val = generate_value_of_type(field)

            values[field] = val

    return values


def generate_values(sql):
    conds = extract_conditions(sql)
    constraints = generate_constraints_from_conditions(conds)
    return generate_values_from_constraints(constraints) if constraints else None


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
    v = generate_values(sql)
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
        vals = generate_values(select)

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


# if(len(sys.argv) != 4):
#     print('USAGE: python3 fuzzer.py <number of tests> <probablity (0-1) of insert fault injected> <probablity (0-1) of delete fault injected>')
#     exit(0)


# numTests = int(sys.argv[1])
# probabilityOfFaultsInsert = float(sys.argv[2])
# probabilityOfFaultsDelete = float(sys.argv[3])

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
