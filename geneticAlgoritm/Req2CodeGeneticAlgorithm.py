from pyeasyga import pyeasyga
import random
from pyeasyga.pyeasyga import Chromosome
from _operator import attrgetter
from SolutionTraceMatrix import SolutionTraceMatrix,\
    SolutionTraceMatrixWithDuplicates
import math
from enum import Enum
import copy, logging
import FileUtil
import Util
import Evaluator
import Paths
from zipfile import sizeEndCentDir

logging.basicConfig(level=logging.INFO, filename="log_output.txt", filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',)
log = logging.getLogger(__name__)

class Req2CodeGeneticAlgorithm(pyeasyga.GeneticAlgorithm):
    
    class ElitismMode(Enum):
        no_elite = 1 # next generation retains no individuals of the previous generation
        first_elite = 2 # next generation retains the fittest individual of the previous generation
        merge = 3 # next and previous generations are merged; choose the fittest individuals to form the next generation
                
    def __init__(self, similarity_csv_file, precalculated_individuals: [], individual_size = 348, population_size=120, generations=300, 
                 crossover_probability=0.5, mutation_probability=0.3, tournament_size=2, elitism_mode=ElitismMode.merge, maximise_fitness=True,
                 max_mutation_size=5, max_crossover_size=5, duplicate_individuals=False, constant_population_size=True, constant_individual_size=True, 
                 start_individual_sizes=[], random_seed=43):
        super(Req2CodeGeneticAlgorithm, self).__init__(None, population_size, generations, crossover_probability, mutation_probability, None, maximise_fitness)
        
        """
        constant_population_size
            True: ensures size of generation == population_size; fill up with random individuals/cut off individuals with lesser fitness if necessary
            False: ensures size of generation <= population_size
        """
        self._similarity_data = PrecalculatedSimilarityCSVDataReader(similarity_csv_file)# contains precalculted similarities between all req and code files
        self._seed_req_list = self._similarity_data.all_req_files()
        self._seed_code_list = self._similarity_data.all_code_files()
        self._precalculated_individuals = precalculated_individuals
        self._start_individual_sizes = start_individual_sizes
        self._individual_size = individual_size
        self._max_mutation_size = max_mutation_size
        self._max_crossover_size = max_crossover_size
        self._elitism_mode = elitism_mode
        self._duplicate_individuals = duplicate_individuals
        self._constant_population_size = constant_population_size # False: number of individuals can be lower than specified due to removal of duplicate individuals
        self._constant_individual_size = constant_individual_size # True: Number of trace links per individual before crossover/mutation and after are the same
         
        random.seed(random_seed)
        
        self.fitness_function = self.fitness_func
        self.tournament_selection = self.tournament_selection_func
        self.tournament_size = tournament_size 
        self.random_selection = self.random_selection_func
        self.create_individual = self.create_individual_func
        self.crossover_function = self.crossover
        self.mutate_function = self.mutate
        self.selection_function = self.tournament_selection_func
    
    
    def create_individual_func(self):
        """Create a candidate solution representation by combine randomly a req from the seed req list and a 
        code file from the seed code list.
        :returns: candidate solution representation as a list (genes)
        """
        return self._create_individual_of_size(self._individual_size)

    def _create_individual_of_size(self, size):
        individual = self.create_empty_individual()
        while individual._number_of_trace_links < size:
            individual.add_trace_pair(random.choice(self._seed_req_list), random.choice(self._seed_code_list))
        return individual
    
    def create_empty_individual(self):
        return SolutionTraceMatrix()
    
    def crossover(self, parent_ind_1, parent_ind_2):
        """Crossover two parents to produce two children.

        :param parent_ind_1: candidate solution representation 
        :param parent_ind_2: candidate solution representation 
        :returns: tuple containing two children

        """
        #log.info("crossover...")
        links_in_1_not_in_2 = parent_ind_1.difference_ignoring_duplicates(parent_ind_2)
        links_in_2_not_in_1 = parent_ind_2.difference_ignoring_duplicates(parent_ind_1)
        if self._skip_crossover_condition(links_in_1_not_in_2, links_in_2_not_in_1):
            log.info(f"p1_diff={len(links_in_1_not_in_2)}, p2_diff={len(links_in_2_not_in_1)} exchange size bigger than differences -> skipping crossover")
            return parent_ind_1, parent_ind_2
        
        exchange_size = self._get_exchange_size(parent_ind_1, parent_ind_2, links_in_1_not_in_2, links_in_2_not_in_1)
        
        
        #log.info(f"crossover exchange size = {exchange_size}")
        child_1, child_2 = Util.deep_copy(parent_ind_1), Util.deep_copy(parent_ind_2)
        size_before_crossover_1, size_before_crossover_2 = child_1._number_of_trace_links, child_2._number_of_trace_links
        while exchange_size > 0:
            #log.info(f"ex={exchange_size}, p1_diff={len(links_in_1_not_in_2)}, p2_diff={len(links_in_2_not_in_1)}, {self._duplicate_individuals}")
            child_1_req, child_1_code, child_2_req, child_2_code, links_in_1_not_in_2, links_in_2_not_in_1 = self.choose_genes_from_crossover_childs(child_1, child_2, links_in_1_not_in_2, links_in_2_not_in_1)
            child_1.add_trace_pair(child_2_req, child_2_code)
            child_1.remove_trace_pair(child_1_req, child_1_code)
            child_2.add_trace_pair(child_1_req, child_1_code)
            child_2.remove_trace_pair(child_2_req, child_2_code)
            ##og.info(f"Crossover: ({exchange_size}): ({child_1_req}, {child_1_code}) <-> ({child_2_req}, {child_2_code})")
            if self._constant_individual_size:
                assert child_1._number_of_trace_links == size_before_crossover_1
                assert child_2._number_of_trace_links == size_before_crossover_2
            exchange_size -= 1
            
        #log.info("Best size: {} {} {} {}".format(parent_ind_1._number_of_trace_links, parent_ind_2._number_of_trace_links, child_1._number_of_trace_links, child_2._number_of_trace_links))
        return child_1, child_2

    def _get_exchange_size(self, parent_1, parent_2, links_in_1_not_in_2, links_in_2_not_in_1):
        difference = min(len(links_in_1_not_in_2), len(links_in_2_not_in_1))
        return 1 if difference == 1 else random.randrange(1, min(difference, self._max_crossover_size + 1))
        
    def _skip_crossover_condition(self, links_in_1_not_in_2, links_in_2_not_in_1):
        return 0 == len(links_in_1_not_in_2) or 0 == len(links_in_2_not_in_1)
        
    def choose_genes_from_crossover_childs(self, child_1, child_2, links_in_1_not_in_2, links_in_2_not_in_1) -> (str, str, str, str, [(str,str)], [(str,str)]):
        random.shuffle(links_in_1_not_in_2)
        random.shuffle(links_in_2_not_in_1)
        child_1_req, child_1_code = links_in_1_not_in_2.pop()
        child_2_req, child_2_code = links_in_2_not_in_1.pop()
        return child_1_req, child_1_code, child_2_req, child_2_code, links_in_1_not_in_2, links_in_2_not_in_1
    
    def _choose_unique_gene(self, child_1, child_2) -> (str, str):
        # Chose random gene from child 1 that is not contained in child 2
        child_1_req, child_1_code = None, None
        while True: # simulate do while loop
            child_1_req, child_1_code = child_1.get_random_pair()
            # Ensure that random pair of child_1 is not already contained in child_2
            if not child_2.contains_req_code_pair(child_1_req, child_1_code): 
                break
        return child_1_req, child_1_code
                
    def mutate(self, individual):
        #log.info("mutate...")
        num_links_before_mutation = individual._number_of_trace_links
        mutation_size = random.randrange(1, min(self._max_mutation_size + 1, num_links_before_mutation))
        if num_links_before_mutation == mutation_size:
            # all entries are changed -> just create a completely random new individual instead
            return self._create_individual_of_size(num_links_before_mutation)
        entries_to_remove = self.create_empty_individual()
        while True: # choose entries to remove (mutate)
            req, code = individual.get_random_pair()
            if not entries_to_remove.contains_req_code_pair(req, code):
                entries_to_remove.add_trace_pair(req, code)
            if entries_to_remove._number_of_trace_links >= mutation_size:
                break
        
        for req, code in entries_to_remove.get_all_trace_links():
            individual.remove_trace_pair(req, code)
            
        assert individual._number_of_trace_links <= num_links_before_mutation
        if self._constant_individual_size:
            while individual._number_of_trace_links < num_links_before_mutation:
                individual = self.add_mutated_genes(individual)
        else:
            add_mutation_size = random.randrange(1, min(self._max_mutation_size + 1, num_links_before_mutation))
            new_size = individual._number_of_trace_links + add_mutation_size
            while individual._number_of_trace_links < new_size:
                individual = self.add_mutated_genes(individual)
        return individual

    def add_mutated_genes(self, individual):
        req, code = random.choice(self._seed_req_list), random.choice(self._seed_code_list) # randomly choose new entries
        if not individual.contains_req_code_pair(req, code):
            individual.add_trace_pair(req, code)
        return individual
    
    def random_selection_func(self, population):
        """Select and return a random member of the population."""
        return random.choice(population)

    def tournament_selection_func(self, population):
        """Select a random number of individuals from the population and
        return the fittest member of them all.
        """
        ##log.info("tournament selection...")
        members = random.sample(population, self.tournament_size)
        members.sort(key=attrgetter('fitness'), reverse=self.maximise_fitness)
        return members[0]

    def fitness_func(self, individual, data): # data parameter not needed / data is saved as attributes
        fitness = 0
        for req_elem, code_elem in individual.get_all_trace_links():
            fitness += self._similarity_data.get_similarity(req_elem, code_elem)
        return fitness / individual._number_of_trace_links

    def create_initial_population(self):
        initial_population = []
        a = 0
        b = 0
        if self._start_individual_sizes:
            if self._precalculated_individuals:
                genes = self._precalculated_individuals.pop(0)
                if genes._number_of_trace_links in self._start_individual_sizes:
                    self._start_individual_sizes.remove(genes._number_of_trace_links)
                individual = Chromosome(genes)
                initial_population.append(individual)
            for size in self._start_individual_sizes:
                initial_population.append(Chromosome(self._create_individual_of_size(size)))
        else:
            for _ in range(self.population_size):
                if self._precalculated_individuals:
                    a += 1
                    genes = self._precalculated_individuals.pop(0)
                    while genes._number_of_trace_links < self._individual_size: 
                        # Fill with random trace pairs
                        req, code = random.choice(self._seed_req_list), random.choice(self._seed_code_list)
                        if not genes.contains_req_code_pair(req, code):
                            genes.add_trace_pair(req, code)
                            
                    while genes._number_of_trace_links > self._individual_size: 
                        # remove trace pairs
                        req, code = genes.get_random_pair()
                        genes.remove_trace_pair(req, code)
                else:
                    b += 1
                    genes = self.create_individual()
                #log.info(genes.print_str() + "\n")
                individual = Chromosome(genes)
                initial_population.append(individual)
        self.current_generation = initial_population
        self.population_size = len(self.current_generation)
        if not self._duplicate_individuals:
            self.calculate_population_fitness()
            self._filter_out_duplicates_from_curr_gen()
            self._fill_curr_gen_with_random_individuals()

    def create_child_population(self):
        """Create a new population using the genetic operators (selection,
        crossover, and mutation) supplied.
        """
        
        new_population = []
        ###log.info("create_child_population...")
        if self._elitism_mode == Req2CodeGeneticAlgorithm.ElitismMode.merge:
            while len(new_population) < len(self.current_generation): # Per iteration there are up to 2 individuals created
                children_are_new, child_1, child_2 = self._create_children()
                if children_are_new:
                    new_population.append(child_1)
                    if len(new_population) < len(self.current_generation):
                        new_population.append(child_2)
            self.current_generation += new_population 
        elif self._elitism_mode == Req2CodeGeneticAlgorithm.ElitismMode.first_elite or self._elitism_mode == Req2CodeGeneticAlgorithm.ElitismMode.no_elite:
            while len(new_population) < len(self.current_generation):
                children_are_new, child_1, child_2 = self._create_children()
                new_population.append(child_1)
                if len(new_population) < len(self.current_generation):
                    new_population.append(child_2)
            if self._elitism_mode == Req2CodeGeneticAlgorithm.ElitismMode.first_elite:
                new_population.append(copy.deepcopy(self.current_generation[0])) # the elite of the current generation
            self.current_generation = new_population 
        else:
            log.error("Unknown ElitismMode enum constant: " + str(self._elitism_mode))
        
        
    def _create_children(self):
        selection = self.selection_function
        parent_1 = copy.deepcopy(selection(self.current_generation))
        parent_2_select = selection(self.current_generation)
        if not self._duplicate_individuals:
            while parent_1.genes.is_same(parent_2_select.genes):
                parent_2_select = selection(self.current_generation)
        parent_2 = copy.deepcopy(parent_2_select)

        child_1, child_2 = parent_1, parent_2
        child_1.fitness, child_2.fitness = 0, 0

        can_crossover = random.random() < self.crossover_probability
        can_mutate = random.random() < self.mutation_probability

        if can_crossover:
            child_1.genes, child_2.genes = self.crossover_function(parent_1.genes, parent_2.genes)

        if can_mutate:
            self.mutate_function(child_1.genes)
            self.mutate_function(child_2.genes)

        return can_crossover or can_mutate, child_1, child_2
            
    def rank_population(self):
        """Sort the population by fitness according to the order defined by
        maximise_fitness and choose the fittest individuals if the current population size exceeds
        the maximum population size
        """
        #log.info("rank_population...")
        self.current_generation.sort(key=attrgetter('fitness'), reverse=self.maximise_fitness)
        log.info(f"Current population size: {len(self.current_generation)}")
        if not self._duplicate_individuals:
            self._filter_out_duplicates_from_curr_gen()
            
        if self._constant_population_size and len(self.current_generation) < self.population_size:
            self._fill_curr_gen_with_random_individuals()
            assert len(self.current_generation) == self.population_size, f"num individuals in current gen = {len(self.current_generation)} != {self.population_size} = population size do not match"
        else:
            self.current_generation = self.current_generation[:self.population_size]
        log.info(f"Current population size: {len(self.current_generation)}")
    
    def _fill_curr_gen_with_random_individuals(self):
        while len(self.current_generation) < self.population_size:
            random_individual = Chromosome(self.create_individual())
            if not self._duplicate_individuals:
                duplicate_found = False
                for indivividual in self.current_generation:
                    if random_individual.genes.is_same(indivividual.genes):
                        duplicate_found = True
                        break # chose new random individual in next while iteration
                if not duplicate_found:
                    self.current_generation.append(random_individual)
            else:
                self.current_generation.append(random_individual)
                
            
    def _filter_out_duplicates_from_curr_gen(self):
        individual_representants = {} # index of individual -> index of its individual. Non-Duplicates are representants of themselves
        for loop_index, individual_1 in enumerate(self.current_generation):
            if not loop_index in individual_representants:
                individual_representants[loop_index] = loop_index
                for j, individual_2 in enumerate(self.current_generation[loop_index+1:]):
                    if math.isclose(individual_1.fitness, individual_2.fitness, rel_tol=1e-8):
                        if individual_1.genes.is_same(individual_2.genes):
                            individual_representants[loop_index + 1 + j] = loop_index # elem at loop_index is identical with this elem
                    else:
                        break; # individuals with fitness difference can't be the same individual
             
        self.current_generation = [x for (i,x) in enumerate(self.current_generation) if individual_representants[i] == i]
        
    def run(self, dataset):
        """Run (solve) the Genetic Algorithm."""
        log.info("{}: Generation {}/{}...".format(Util.curr_time(), 1, self.generations))
        self.create_first_generation()
        log.info(f"\nG=0\n{self._eval_best_individual(dataset)[3]}\nfitness: {self.best_individual()[0]}")
        for i in range(1, self.generations):
            log.info("{}: Generation {}/{}...".format(Util.curr_time(), i + 1, self.generations))
            self.create_next_generation()
            log.info("Best fitness: " + str(self.best_individual()[0]))
            log.info("f1: " + str(self._eval_best_individual(dataset)[2]))
            #log.info(f"Best #links: {self.best_individual()[1]._number_of_trace_links}")
            log.info(f"\n{[x.genes._number_of_trace_links for x in self.current_generation[:100]]}")
            #for j in self.current_generation[1:5]:
            #   log.info(f"\n{j.genes._number_of_trace_links}, {j.fitness}")
            #log.info("Best size: " + str(self.best_individual()[1]._number_of_trace_links))
            
    def start(self, dataset):
        self.run(dataset)
        num_links = ""
        if not self._constant_individual_size:
            num_links = f"\nnumber of trace links: {self.best_individual()[1]._number_of_trace_links}"
        log.info(f"\nG={self.generations}\n{self._eval_best_individual(dataset)[3]}\nfitness: {self.best_individual()[0]}" + num_links)
        log.info(self.param_print_str())
        
        
    def _eval_best_individual(self, dataset):
        trace_link_with_sims = []
        for req, code in self.best_individual()[1].get_all_trace_links():
            trace_link_with_sims.append((req, code, self._similarity_data.get_similarity(req, code)))
        return Evaluator.evaluate_tuple_list(trace_link_with_sims, dataset.solution_matrix())
    
    def param_print_str(self):
        print_str = (
            f"\nindividual_size={self._individual_size}\n"
            f"population_size={self.population_size}\n"
            f"generations={self.generations}\n"
            f"crossover_probability={self.crossover_probability}\n"
            f"mutation_probability={self.mutation_probability}\n"
            f"tournament_size={self.tournament_size}\n"
            f"elitism_mode={self._elitism_mode}\n"
            f"max_mutation_size={self._max_mutation_size}\n"
            f"max_crossover_size={self._max_crossover_size}\n"
            f"constant_population_size={self._constant_population_size}\n"
            f"constant_individual_size={self._constant_individual_size}\n"
            f"duplicate_individuals={self._duplicate_individuals}"
        )
        if not self._constant_population_size:
            print_str += f"\nfinal population size: {len(self.current_generation)}"
        return print_str
        
        
class Req2CodeGeneticAlgorithmWithDuplicates(Req2CodeGeneticAlgorithm):
    
    def __init__(self, similarity_csv_file, precalculated_individuals: [], individual_size = 348, population_size=120, generations=300, 
                 crossover_probability=0.5, mutation_probability=0.3, tournament_size=2, elitism_mode=Req2CodeGeneticAlgorithm.ElitismMode.merge, maximise_fitness=True,
                 max_mutation_size=5, max_crossover_size=5, duplicate_individuals=False, constant_population_size=True, constant_individual_size=True, start_individual_sizes=[], random_seed=43):
        super(Req2CodeGeneticAlgorithmWithDuplicates, self).__init__(similarity_csv_file, precalculated_individuals, individual_size, 
                                                    population_size, generations, crossover_probability, mutation_probability, 
                                                    tournament_size, elitism_mode, maximise_fitness, max_mutation_size, max_crossover_size, 
                                                    duplicate_individuals, constant_population_size, constant_individual_size,start_individual_sizes, random_seed)
    
        self._precalculated_individuals = [SolutionTraceMatrixWithDuplicates.convert_from_solution_matrix(sol_matrix) for sol_matrix in self._precalculated_individuals]
        
    def create_empty_individual(self):
        return SolutionTraceMatrixWithDuplicates()
    
    def fitness_func(self, individual, data): # data parameter not needed / data is saved as attributes
        fitness = 0
        unique_links = set(individual.get_all_trace_links()) # set(): Dont count duplicate twice
        for req_elem, code_elem in unique_links:
            fitness += self._similarity_data.get_similarity(req_elem, code_elem)
        return fitness / len(unique_links)
    
    def _get_exchange_size(self, parent_1, parent_2, links_in_1_not_in_2, links_in_2_not_in_1):
        return random.randrange(1, min(parent_1._number_of_trace_links, min(parent_2._number_of_trace_links, self._max_crossover_size + 1)))
    
    def _skip_crossover_condition(self, links_in_1_not_in_2, links_in_2_not_in_1):
        return False # Never skip, since duplicates are allowed
    
    def choose_genes_from_crossover_childs(self, child_1, child_2, links_in_1_not_in_2, links_in_2_not_in_1):
        child_1_req, child_1_code = child_1.get_random_pair()
        while True: # simulate do while loop
            # Ensure that random pair of child_1 is not the same as random pair of child_2
            # random pair can already be contained in child_2 (duplicates allowed)
            child_2_req, child_2_code = child_2.get_random_pair()
            if child_1_req != child_2_req and child_1_code != child_2_code: 
                break 
        return child_1_req, child_1_code, child_2_req, child_2_code, links_in_1_not_in_2, links_in_2_not_in_1

    def add_mutated_genes(self, individual):
        req, code = random.choice(self._seed_req_list), random.choice(self._seed_code_list) # randomly choose new entries
        individual.add_trace_pair(req, code)
        return individual
    
    def param_print_str(self):
        print_str = super(Req2CodeGeneticAlgorithmWithDuplicates, self).param_print_str()
        print_str += "\nDuplicated trace links per individual possible"
        return print_str
    
class PrecalculatedSimilarityCSVDataReader:
    
    def __init__(self, file_level_similarity_csv_file, reverse_similarity=False, req_file_ext=None, code_file_ext=None):
        """
        All similarities have to be between 0 and 1
        reverse_similarity=True if the smaller the better
        """
        self._similarity_dataframe = FileUtil.read_csv_to_dataframe(file_level_similarity_csv_file)
        self._file_path = file_level_similarity_csv_file
        self._reverse_similarity = reverse_similarity
        if req_file_ext is not None:
            modified_reqs = {}
            for req in self.all_req_files():
                modified_reqs[req] = FileUtil.set_extension(req, req_file_ext)
            self._similarity_dataframe.rename(index=modified_reqs, inplace=True)
        if code_file_ext is not None:
            modified_code = {}
            for code in self.all_code_files():
                modified_code[code] = FileUtil.set_extension(code, code_file_ext)
            self._similarity_dataframe.rename(columns=modified_code, inplace=True)
        
    def get_similarity(self, req_file, code_file):
        sim = self._similarity_dataframe.loc[req_file, code_file]
        return 1 - sim if self._reverse_similarity else sim
    
    def all_req_files(self):
        return list(self._similarity_dataframe.index.values)
    
    def all_code_files(self):
        return list(self._similarity_dataframe)
    
    def file_name(self):
        return FileUtil.get_filename_from_path(self._file_path)