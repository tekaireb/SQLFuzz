from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from typing import Dict, Union, Any, Tuple, List
import string
import random
import sys

from random_utils import *

# Specify database configuration

db = 'Users_DB'
fields = ['name', 'age', 'email_address', 'phone_number', 'ssn']
# TODO: Allow passing of params to specify additional constraints (e.g., numerical ranges, age should be 1 to 100)
types = ['<Name>', '<Integer>', '<Email>', '<Phone>', '<SSN>']
comparators = ['<StringComparator>', '<Comparator>',
               '<StringComparator>', '<StringComparator>', '<StringComparator>']

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
    # '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
    '<Integer>': ['<Digit>', '<Integer><Digit>'],  # Only positive numbers
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
                # TODO: Add validity checking (e.g., warn/terminate if less than and greater than values have no overlapping range)
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
                constraint_table[field]['min'] = min(
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
        if c['min'] > c['max']:
            print(
                'INVALID CONSTRAINTS: specified minimum greater than maximum')
            return None
        if c['eq'] < c['min'] or c['eq'] > c['max']:
            print(
                'INVALID CONSTRAINTS: specified equals that exceeds min/max bounds')
            return None

    # print(constraint_table)
    return constraint_table


def generate_values_from_constraints(constraints):
    values = {}

    def generate_value_of_type(field):
        t = types[fields.index(field)]

        # if t == '<String>':
        #     return random_string(10)
        # if t == '<Name>':
        #     return random_name()
        # if t == '<Email>':
        #     return random_email()
        # if t == '<Phone>':
        #     return random_phone()

        return (random_name() if t == '<Name>' else
                random_email() if t == '<Email>' else
                random_phone() if t == '<Phone>' else
                random_ssn() if t == '<SSN>' else
                random_string(10))

    for field, constraint in constraints.items():
        # If there is an `equals` constraint, set the value to it
        if constraint['eq']:
            values[field] = constraint['eq']
            continue

        if comparators[fields.index(field)] == '<Comparator>':  # Integer
            max_val = constraint['max'] if constraint['max'] else 100
            min_val = constraint['min'] if constraint['min'] else 0
            val = random.randrange(min_val, max_val + 1)

            # Find new random value if value is specified under `not equals`
            while val in constraint['neq']:
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


def insert_from_values(vals):
    insert = f'INSERT INTO {db} (' + ', '.join(vals.keys()) + ')\n'
    insert += 'VALUES (' + ', '.join([f'"{v}"' for v in vals.values()]) + ')'
    return insert


def insert_from_query(sql):
    v = generate_values(sql)
    return insert_from_values(v) if v else None


for i in range(6):
    print(f'\n#{i}:\n')
    insert = None
    while not insert:
        select = fuzzer.fuzz()
        insert = insert_from_query(select)

    print(select)
    # TODO: execute query on database, save results
    print(insert)
    # TODO: execute insert on database
    print(select)
    # TODO: execute query again, perform set subtraction and verify that properties hold