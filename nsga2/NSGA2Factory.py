import logging, abc
from nsga2.Population import Population
from nsga2.CrossoverOperator import BinaryCrossover
from nsga2.Nsga2 import Nsga2
from nsga2.SelectionOperator import BinaryTournamentSelection
from nsga2.MutationOperator import RandomMutation
from nsga2.TerminationCriterion import MaxGenerationsCriterion
from nsga2.Aggregator import SumAggregator, AverageAggregator
from nsga2.SeedData import TraceLinkSeedData
import Paths
from nsga2.Gene import Gene

class NSGA2Factory(abc.ABC):
    
    def __init__(self, population_size, initial_individual_size, seed_data,duplicate_individuals_allowed, duplicate_genes_allowed,
                 solution_matrix, precalculated_genes=[], child_population_size=None):
        
        aggregator = self.create_aggregator()
        initial_pop = Population.create_population(population_size, initial_individual_size, seed_data, aggregator, 
                                    duplicate_individuals_allowed, duplicate_genes_allowed, precalculated_genes)
        
        selection = self.create_selection_operator()
        crossover = self.create_crossover_operator()
        mutation = self.create_mutation_operator()
        termination = self.create_termination_criterion()
        self.ngsa2 = Nsga2(initial_pop, termination, selection, crossover, mutation, solution_matrix, child_population_size)
    
    
    def create_nsga2_instance(self):
        return self.ngsa2
    
    @abc.abstractmethod
    def create_selection_operator(self):
        pass
    
    @abc.abstractmethod
    def create_crossover_operator(self):
        pass
    
    @abc.abstractmethod
    def create_mutation_operator(self):
        pass
    
    @abc.abstractmethod
    def create_termination_criterion(self):
        pass
    
    @abc.abstractmethod
    def create_aggregator(self):
        pass
    
class StandardNSGA2Factory(NSGA2Factory):
    def __init__(self, population_size, initial_individual_size, dataset, duplicate_individuals_allowed, duplicate_genes_allowed,
                 max_generations, crossover_probability, max_crossover_size, mutation_probability, max_mutation_size, precalculated_genes_files=[], 
                 child_population_size=None):
        
        self.seed_data = TraceLinkSeedData()
        #self.seed_data.add_seed_data(Paths.precalculated_all_filelevel_sims_csv_filename(dataset, "FastTextUCNameDescFlowRodriguezIdentifierWMDTLP"), "wmd", True, req_file_ext="TXT", code_file_ext="java")
        self.seed_data.add_seed_data(Paths.precalculated_req_code_tfidf_cos_sim_filename(dataset, "UCNameDescFlowChooser", "RodriguezCodeChooser"), "tfidf-cossim")
        self.seed_data.add_seed_data(Paths.precalculated_jaccard_sims_csv_filename(dataset, "UCNameDescFlowChooser", "RodriguezCodeChooser"), "jaccard")
        precalculated_genes = []
        for file_path in precalculated_genes_files:
            precalculated_genes.append(Gene.load_precalculated_tracelinks_into_genes(file_path, self.seed_data, "TXT", "java"))
        self.max_generations = max_generations
        self.mutation_probability = mutation_probability
        self.max_mutation_size = max_mutation_size
        self.crossover_probability = crossover_probability
        self.max_crossover_size = max_crossover_size
        
        super(StandardNSGA2Factory, self).__init__(population_size, initial_individual_size, self.seed_data, duplicate_individuals_allowed, 
                                                   duplicate_genes_allowed, dataset.solution_matrix("TXT", "java"), precalculated_genes, child_population_size)
        
    def create_selection_operator(self):
        return BinaryTournamentSelection(Nsga2.crowded_compare)
    
    def create_crossover_operator(self):
        return BinaryCrossover(self.crossover_probability, self.max_crossover_size)
    
    def create_mutation_operator(self):
        return RandomMutation(self.mutation_probability, self.seed_data, self.max_mutation_size)
    
    def create_termination_criterion(self):
        return MaxGenerationsCriterion(self.max_generations)
        
    def create_aggregator(self):
        return AverageAggregator()