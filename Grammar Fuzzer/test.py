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
                    return
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
                    return
                else:
                    constraint_table[field]['eq'] = val
            elif comp == '<>':
                if val not in constraint_table[field]['neq']:
                    constraint_table[field]['neq'].append(val)

    # print(constraint_table)
    return constraint_table


def generate_values_from_constraints(constraints):
    # TODO
    return


def generate_values(sql):
    conds = extract_conditions(sql)
    constraints = generate_constraints_from_conditions(conds)
    return generate_values_from_constraints(constraints)


for i in range(3):
    sql = fuzzer.fuzz()
    print(f'#{i}: \t{sql}')
    c = generate_constraints_from_conditions(extract_conditions(sql))
