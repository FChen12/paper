import logging
from nsga2.Aggregator import Aggregator
from nsga2.SeedData import SeedData
from nsga2.Container import Container
from nsga2.Gene import Gene

log = logging.getLogger(__name__)

class Individual:
    
    def __init__(self, genes_container):
        self.front_nr = None
        self.crowding_distance = 0
        self._fitness_dict = {} # _fitness_dict[dimension] = aggregated similarity: aggregated similarity for each dimension
        self._genes_container = genes_container
        
    @classmethod
    def create_random_individual(cls, seed_data, individual_size, duplicate_genes_allowed=False):
        genes = Container(duplicate_genes_allowed)
        while genes.size() < individual_size:
            genes.add(seed_data.get_random_gene())
        return cls(genes)
           
    @classmethod 
    def create_individual_from_precalculated(cls, precalculated_genes: [Gene], seed_data, individual_size, duplicate_genes_allowed=False):
        genes = Container(duplicate_genes_allowed)
        genes.add_all(precalculated_genes)
        while genes.size() < individual_size:
            genes.add(seed_data.get_random_gene())
        while genes.size() > individual_size:
            genes.remove_random_element()
        return cls(genes)
    
    
    def aggregate_gene_similarities(self, seed_data: SeedData, aggregator: Aggregator):
        all_genes = self._genes_container.get_all_elems_as_list()
        for dimension in seed_data.get_similarity_keys():
            similarities = [gene.get_fitness(dimension) for gene in all_genes]
            self._fitness_dict[dimension] = aggregator.aggregate(similarities)
    
    def get_similarities_as_dict(self):
        return self._fitness_dict
    
    def difference_ignoring_duplicates(self, other_individual):
        return self._genes_container.difference_ignoring_duplicates(other_individual._genes_container)
    
    def duplicate_genes_allowed(self):
        return self._genes_container.allows_duplicates()
            
    def get_all_genes(self):
        return self._genes_container.get_all_elems_as_list()
    
    def add_gene(self, gene):
        self._genes_container.add(gene)
    
    def remove_random_gene(self):
        return self._genes_container.remove_random_element()
        
    def remove_gene(self, gene):
        self._genes_container.remove(gene)
        
    def size(self):
        return self._genes_container.size()
    
    def __eq__(self, other):
        # equal when genes are the same
        return self._genes_container == other._genes_container
    
    def __repr__(self):
        return str(self._genes_container)
    
    def __hash__(self):
        return hash(self.__repr__())
        