import json


class Config(object):
    def __init__(self, config_path):
        # Load values from configuration file
        self.config_path = config_path
        with open(config_path, 'r') as f:
            self.cfg = json.loads(f.read())

        self.num_tests = 0
        self.db = None
        self.seed = None

        self.fields = None
        self.types = None
        self.comparators = None

        self.insert_fault_probability = 0
        self.delete_fault_probability = 0

        # Check validity
        self.validate()

        # Load number of tests
        self.num_tests = int(self.cfg['num_tests'])

        # Load random seed (if specified)
        self.seed = int(self.cfg['seed']) if self.cfg['seed'] else None

        # Load database properties
        self.db = self.cfg['database']['name']
        self.fields = self.cfg['database']['fields']
        self.types = self.cfg['database']['types']
        self.comparators = self.cfg['database']['comparators']

        # Load fault probabilities (if specified)
        if 'fault_probabilities' in self.cfg:
            if 'insert' in self.cfg['fault_probabilities']:
                self.insert_fault_probability = float(
                    self.cfg['fault_probabilities']['insert'])
            if 'delete' in self.cfg['fault_probabilities']:
                self.delete_fault_probability = float(
                    self.cfg['fault_probabilities']['delete'])

    def validate(self):
        # Ensure configuration file has all necessary keys
        assert 'database' in self.cfg, 'Config file must specify database properties'
        assert 'num_tests' in self.cfg, 'Config file must specify number of tests (e.g., "num_tests": x)'
        for prop in ['name', 'fields', 'types', 'comparators']:
            assert prop in self.cfg[
                'database'], f'Config file must specify database {prop}'

        # Check whether values are reasonable

        assert len(self.cfg['database']['fields']) == len(
            self.cfg['database']['types']), 'Length of fields and types must be equivalent (they are associated one-to-one)'
        assert len(self.cfg['database']['fields']) == len(
            self.cfg['database']['comparators']), 'Length of fields and comparators must be equivalent (they are associated one-to-one)'

        for t in self.cfg['database']['types']:
            assert t.startswith('<') and t.endswith(
                '>'), 'Each type must be a Grammar token (e.g., <Phone>)'

        for t in self.cfg['database']['comparators']:
            assert t.startswith('<') and t.endswith(
                '>'), 'Each comparator must be a Grammar token (e.g., <StringComparator>)'
