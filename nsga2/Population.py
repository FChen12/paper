from nsga2.Individual import Individual
from nsga2.Container import Container

class Population:
    
    def __init__(self, expected_population_size, individuals_container, individual_size, seed_data, aggregator, duplicate_genes_allowed=False):
        self._expected_population_size = expected_population_size
        self.individual_size = individual_size
        self.seed_data = seed_data
        self._individuals_container = individuals_container
        self._duplicate_genes_allowed = duplicate_genes_allowed
        self.aggregator = aggregator
        self.first_front = None
        
    @classmethod
    def create_population(cls, initial_population_size, individual_size, seed_data, aggregator, duplicate_individuals_allowed=False, duplicate_genes_allowed=False, precalculated_genes=[]):
        individuals_container = Container(duplicate_individuals_allowed) # Doesn't add duplicates when duplicates are not allowed
        while individuals_container.size() < initial_population_size and len(precalculated_genes) > 0:
            genes = precalculated_genes.pop(0)
            individuals_container.add(Individual.create_individual_from_precalculated(genes, seed_data, individual_size, duplicate_genes_allowed))
            
        # Fill up with random individuals after all precalculated have been added
        instance = cls(initial_population_size, individuals_container, individual_size, seed_data, aggregator, duplicate_genes_allowed)
        instance.fill_up_with_random_individuals_until_pop_size()
        
        return instance
    
    @classmethod
    def create_population_from_individuals(cls, expected_population_size, individuals, individual_size, seed_data, aggregator, 
                                           duplicate_individuals_allowed=False, duplicate_genes_allowed=False):
        individuals_container = Container(duplicate_individuals_allowed) # Doesn't add duplicates when duplicates are not allowed
        individuals_container.add_all(individuals)
        instance = cls(expected_population_size, individuals_container, individual_size, seed_data, aggregator, duplicate_genes_allowed)
        instance.fill_up_with_random_individuals_until_pop_size()
        return instance
    
    
    @classmethod
    def create_empty_population(cls, initial_population_size, individual_size, seed_data, aggregator, duplicate_individuals_allowed=False, duplicate_genes_allowed=False):
        individuals_container = Container(duplicate_individuals_allowed)
        return cls(initial_population_size, individuals_container, individual_size, seed_data, aggregator, duplicate_genes_allowed)

    def calculate_aggregated_similarities(self):
        for ind in self._individuals_container.get_all_elems_as_list():
            ind.aggregate_gene_similarities(self.seed_data, self.aggregator)
             
    def get_all_individuals_as_list(self):
        return self._individuals_container.get_all_elems_as_list()
        
    def actual_population_size(self):
        return self._individuals_container.size()
    
    def expected_population_size(self):
        return self._expected_population_size 
    
    def fill_up_with_random_individuals_until_pop_size(self):
        while self._individuals_container.size() < self._expected_population_size:
            self._individuals_container.add(Individual.create_random_individual(self.seed_data, self.individual_size, 
                                                                                           self._duplicate_genes_allowed))
    
    def add(self, element):
        return self._individuals_container.add(element)
    
    def add_all(self, element_list):
        return self._individuals_container.add_all(element_list)
    
    def replace_individuals_with(self, new_individuals_list):
        self._individuals_container.empty()
        self.add_all(new_individuals_list)
        
    def get_two_random_elements(self):
        return self._individuals_container.get_two_random_elements()
    
    def get_random_individual(self):
        return self._individuals_container.get_random_element()
    
    def remove_duplicates(self):
        self._individuals_container.remove_duplicates()
        
    def duplicate_individuals_allowed(self):
        return self._individuals_container.allows_duplicates()
    
    def merge(self, other_population):
        self._individuals_container.merge(other_population._individuals_container)
        return self
    
    def get_similarity_dimensions(self):
        return self.seed_data.get_similarity_keys()
    def config_print(self):
        ind = self.get_random_individual()
        return (f"Population size = initial: {self._expected_population_size}, actual: {self.actual_population_size()}\n"
                f"Individual size = {ind.size()}\n"
                f"Duplicate individuals = {self.duplicate_individuals_allowed()}\n"
                f"Duplicate genes = {self._duplicate_genes_allowed}\n"
                f"{self.seed_data.config_print()}\n"
                f"{self.aggregator.config_print()}")
    