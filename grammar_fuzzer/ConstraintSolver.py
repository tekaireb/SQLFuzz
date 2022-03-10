from config import Config
import random

from random_utils import *
from database import *

# Helper functions


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


# Create values that satisfy search constraints specified in SQL query


class ConstraintSolver(object):

    def __init__(self, config: Config):
        self.config = config

        self.fields = config.fields
        self.comparators = config.comparators
        self.types = config.types

    def generate_constraints_from_conditions(self, conditions):
        constraint_table = dict([(field, {'max': None, 'min': None, 'eq': None, 'neq': []}) if comp == '<Comparator>'
                                else (field, {'eq': None, 'neq': []})
                                for field, comp in zip(self.fields, self.comparators)])

        condition = random.choice(conditions)
        # print('Selected condition:', condition)

        for terms in condition.split('AND'):
            # print('Terms:', terms)
            # print('Terms (split):', terms.strip().split(' '))
            field, comp, val = terms.strip().split(' ')
            val = val[1:-1]  # Remove extraneous quotes

            # Integer
            if self.comparators[self.fields.index(field)] == '<Comparator>':
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

            # String
            elif self.comparators[self.fields.index(field)] == '<StringComparator>':
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

    def generate_values_from_constraints(self, constraints):
        values = {}

        def generate_value_of_type(field):
            global generatedSSNs
            t = self.types[self.fields.index(field)]

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

            # Integer
            if self.comparators[self.fields.index(field)] == '<Comparator>':
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

    def generate_values(self, sql):
        conds = extract_conditions(sql)
        constraints = self.generate_constraints_from_conditions(conds)
        return self.generate_values_from_constraints(constraints) if constraints else None
