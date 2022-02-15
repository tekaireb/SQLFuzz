from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from typing import Dict, Union, Any, Tuple, List
import string
import random
import sys

# Specify database configuration

db = 'Users_DB'
fields = ['name', 'age', 'email_address', 'phone_number']
# TODO: Allow passing of params to specify additional constraints (e.g., numerical ranges, age should be 1 to 100)
types = ['<String>', '<Integer>', '<Email>', '<Phone>']
comparators = ['<StringComparator>', '<Comparator>',
               '<StringComparator>', '<StringComparator>']

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
        ['<', '<=', '=', '<LAngle><RAngle>' '>=', '>'],

    '<StringComparator>':
        ['=', '<LAngle><RAngle>'],

    '<LAngle>': ['<'],

    '<RAngle>': ['>'],

    '<Relation>': [db],

    '<Attribute>':
        fields,

    # Types:
    '<String>': ['<Char>', '<String><Char>'],
    '<Char>': list(string.ascii_lowercase),
    '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
    '<Digit>': [str(i) for i in range(10)],
    '<Email>': ['<String>@<String>.com', '<String>@<String>.org', '<String>@<String>.edu'],
    '<Phone>': ['(<Area>) <Exchange>-<Line>'],
    '<Lead-Digit>': [str(i) for i in range(2, 10)],
    '<Area>': ['<Lead-Digit><Digit><Digit>'],
    '<Exchange>': ['<Lead-Digit><Digit><Digit>'],
    '<Line>': ['<Digit><Digit><Digit><Digit>']
}

fuzzer = GrammarFuzzer(grammar=SQL_GRAMMAR,
                       start_symbol='<Query>', max_nonterminals=5)


def extract_type(sql):
    return sql[:sql.find(' ')]


def extract_constraints(sql):
    # Get full condition (everything after 'WHERE')
    condition_start = sql.find('WHERE')
    cond = sql[condition_start+6:] if condition_start != -1 else ''

    # Separate constraint possibilities
    constraints = cond.split(' OR ')
    if constraints == ['']:
        constraints = [cond]

    return constraints


def generate_value_from_constraints(constraints):
    constraint_table = dict([(field, {'max': None, 'min': None, 'eq': None, 'neq': []}) if comp == '<Comparator>'
                             else (field, {'eq': None, 'neq': []})
                             for field, comp in zip(fields, comparators)])

    constraint = random.choice(constraints)

    # for conditions in constraint.split('AND'):
    #     for c in conditions:
    #         field, comp, val = c
    #         val = val[1:-1] # Remove extraneous quotes

    #         if comp == '<Comparison>':  # Integer
    #             if comp == '<':
    #                 constraint_table[field]['max'] = min(constraint_table[field]['max'], val - 1) if constraint_table[field]['max'] else val - 1
    #             if comp == '<=':
    #                 constraint_table[field]['max'] = min(constraint_table[field]['max'], val) if constraint_table[field]['max'] else val
    #             if comp == '=':
    #                 if constraint_table[field]['eq'] and constraint_table[field]['eq'] != val:
    #                     print('INVALID CONSTRAINTS: specified multiple non-equivalent equals')
    #                     return
    #                 else:

    #             if comp == '<>':
    #             if comp == '>=':
    #                 constraint_table[field]['min'] = max(constraint_table[field]['min'], val) if constraint_table[field]['min'] else val
    #             if comp == '>':
    #                 constraint_table[field]['min'] = min(constraint_table[field]['min'], val + 1) if constraint_table[field]['min'] else val + 1
    #             constraint_table[]

    #         elif comp == '<StringComparison>':  # String

    print(constraint_table)

    return


for i in range(5):
    sql = fuzzer.fuzz()
    print(f'#{i}: \t{sql}')
    c = generate_value_from_constraints(extract_constraints(sql))
