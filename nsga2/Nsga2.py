from nsga2.Population import Population
import logging
import Util
import collections
from nsga2.Individual import Individual
import Evaluator

log = logging.getLogger(__name__)

class Nsga2:
    
    def __init__(self, initial_population, termination_criterion, selection_operator, crossover_operator, mutation_operator, 
                 solution_matrix, child_population_size=None):
        self._population = initial_population
        self._child_population_size = child_population_size if child_population_size else initial_population.actual_population_size()
        self._termination_criterion = termination_criterion
        self._selection_operator = selection_operator
        self._crossover_operator = crossover_operator
        self._mutation_operator = mutation_operator
        self._solution_matrix = solution_matrix
        
    def run(self):
        """
        Starting point
        """
        generation_count = 1
        self._population.calculate_aggregated_similarities()
        all_individuals = self._population.get_all_individuals_as_list()
        fronts = self.nondominated_sorting(all_individuals)
        
        self.evaluate_and_print(fronts[0], "initial first front")
        while not self._termination_criterion.is_fullfilled():
            self.print_progress(generation_count)
            child_population = self.create_child_population()
            self._population.merge(child_population)
            assert self._population.expected_population_size() <= self._population.actual_population_size()
            
            self._population.calculate_aggregated_similarities()
            all_individuals = self._population.get_all_individuals_as_list()
            fronts = self.nondominated_sorting(all_individuals)
            fronts = self.calculate_crowding_distance(fronts, self._population.get_similarity_dimensions())
            self.create_next_population(fronts)
            self._termination_criterion.update(self._population)
            generation_count += 1
            self.evaluate_and_print(self._population.first_front, "first front")
        self.print_config()
            
    def print_progress(self, generation_count):
        print_str = f"\n#########################################################\n{Util.curr_time()}: Generation {generation_count} "
        
        log.info(print_str)
        
    def print_config(self):
        print_str = f"Config:\n"
        print_str += self._population.config_print() + "\n"
        print_str += f"child population size = {self._child_population_size}\n"
        print_str += self._termination_criterion.config_print() + "\n"
        print_str += self._selection_operator.config_print() + "\n"
        print_str += self._crossover_operator.config_print() + "\n"
        print_str += self._mutation_operator.config_print() + "\n"
        print_str += f"Final first front size = {len(self._population.first_front)}"
        log.info(print_str)
        
    def evaluate_and_print(self, ind_list: [Individual], description):
        to_print = "\n================================\n"
        to_print += f"Evaluate {description} with {len(ind_list)} individuals\n"
        to_print += "================================\n"
        ind_print_str = []
        for ind in ind_list:
            trace_link_tuples = [(gene.req_name, gene.code_name, -1) for gene in ind.get_all_genes()]
            precision, recall, f_1, print_str = Evaluator.evaluate_tuple_list(trace_link_tuples, self._solution_matrix)
            ind_print_str.append(print_str + f"\n{ind.get_similarities_as_dict()}")
        to_print += "\n------------------------\n".join(ind_print_str)
        to_print += "\n================================"
        log.info(to_print)
        
        
    def create_next_population(self, fronts):
        target_population_size = self._population.expected_population_size()
        chosen_individuals = []
        chosen_individuals_size = 0
        while chosen_individuals_size < target_population_size:
            for front in fronts:
                if chosen_individuals_size + len(front) < target_population_size:
                    chosen_individuals += front
                    chosen_individuals_size = len(chosen_individuals)
                else:
                    s = (self.sort_front_according_to_crowding_distance(front))
                    k = (target_population_size - chosen_individuals_size)
                    chosen_individuals += s[:k]
                    chosen_individuals_size = len(chosen_individuals)
        
        self._population.replace_individuals_with(chosen_individuals)
        if len(fronts[0]) >= target_population_size:
            self._population.first_front = chosen_individuals
            
        else:
            self._population.first_front = fronts[0]
    
    @staticmethod    
    def sort_front_according_to_crowding_distance(front: [Individual]):
        return sorted(front, key=lambda ind: ind.crowding_distance, reverse=True)
    
    def create_child_population(self):
        child_individuals = []
        while len(child_individuals) < self._child_population_size:
            child_individuals += self.apply_operators()
            child_individuals = child_individuals[:self._child_population_size]
            
        # creates child population and if set to True: removes duplicates & fills up with random individuals
        child_population = Population.create_population_from_individuals(self._child_population_size, child_individuals, 
                                    self._population.individual_size, self._population.seed_data, self._population.aggregator,
                                    self._population.duplicate_individuals_allowed(), self._population._duplicate_genes_allowed)
        return child_population
    
    def apply_operators(self):
        selected_ind_1, selected_ind_2  = self._selection_operator.select_from(self._population, (not self._population.duplicate_individuals_allowed()))
        selected_ind_1_copy = Util.deep_copy(selected_ind_1)
        selected_ind_2_copy = Util.deep_copy(selected_ind_2)
        crossovered_individuals = self._crossover_operator.crossover(selected_ind_1_copy, selected_ind_2_copy)
        mutated_individuals = self._mutation_operator.mutate(crossovered_individuals)
        return  mutated_individuals
    
    @staticmethod        
    def calculate_crowding_distance(fronts, dimensions): # fronts = [[front_1], .., [front_n]]
        num_dimensions = len(dimensions)
        for front in fronts:
            all_similarities = [(index, ind.get_similarities_as_dict()) for index, ind in enumerate(front)]
            for individual in front:
                individual.crowding_distance = 0.0
            for dim in dimensions:
                all_similarities.sort(key=lambda elem: elem[1][dim]) # sort by fitness value of the dimension
                
                index_of_first_ind = all_similarities[0][0]
                front[index_of_first_ind].crowding_distance = float("inf")
                index_of_last_ind = all_similarities[-1][0]
                front[index_of_last_ind].crowding_distance = float("inf")
                
                if all_similarities[0][1][dim] == all_similarities[-1][1][dim]:
                    # all distances of individuals between the first and last one are equal to zero
                    continue
                        
                norm = num_dimensions * float(all_similarities[-1][1][dim] - all_similarities[0][1][dim])
                for prev, curr, next in zip(all_similarities[:-2], all_similarities[1:-1], all_similarities[2:]):
                    front[curr[0]].crowding_distance += (next[1][dim] - prev[1][dim]) / norm
        return fronts
        
    @staticmethod
    def nondominated_sorting(individuals_list):
        # use index of the for loop as temporary unique identifier for the individuals
        
        individual_dict = {} # individual_dict[index] = individual object
        sim_dicts = {} # sim_dicts[index] = sim_dict (values for each similarity dimension)
        
        for index, ind in enumerate(individuals_list):
            individual_dict[index] = ind
            sim_dicts[index] = ind.get_similarities_as_dict()
            
        domination_count = {} # domination_count[index] = number of other individuals that dominate this individual
        dominate_list = {} # dominate_list[index] = list of individual (indices) that are dominated by this individual
        all_indices = list(individual_dict.keys())
        for index in all_indices:
            domination_count[index] = 0
            dominate_list[index] = []
            
        current_front_indices = [] # list of individual represented by their index that belong to the same front
        current_front = []
        front_nr = 1
        for index in all_indices:
            this_similarities = sim_dicts[index]
            for index_2 in all_indices[index+1:]:
                other_similarities = sim_dicts[index_2]
                if Nsga2.dominates(this_similarities, other_similarities):
                    domination_count[index_2] += 1
                    dominate_list[index].append(index_2)
                elif Nsga2.dominates(other_similarities, this_similarities):
                    domination_count[index] += 1
                    dominate_list[index_2].append(index)
            if domination_count[index] == 0: # individual belong to the first front
                current_front_indices.append(index)
                individual_dict[index].front_nr = front_nr
                current_front.append(individual_dict[index])
                
        num_sorted_individuals = len(current_front_indices)
        all_fronts = [current_front] # list of all fronts. Index is front number, index == 1 is first front
        while num_sorted_individuals < len(all_indices): # while not all individuals sorted
            next_front = []
            next_front_indices = []
            front_nr += 1
            for index in current_front_indices:
                for dominated_index in dominate_list[index]:
                    domination_count[dominated_index] -= 1
                    if domination_count[dominated_index] == 0: # individual belongs to next front
                        individual_dict[dominated_index].front_nr = front_nr
                        next_front.append(individual_dict[dominated_index])
                        next_front_indices.append(dominated_index)
            num_sorted_individuals += len(next_front)
            all_fronts.append(next_front)
            current_front_indices = next_front_indices
            
        return all_fronts # [[front_1], .., [front_n]]
    
    @staticmethod
    def dominates(this_sims: dict(), other_sims: dict()):
        """
        this_sim corresponds to [x1, .., xn]
        other_sims corresponds to [y1, .., yn]
        with n dimensions
        
        dominates(this_sim, other_sims) == True 
        <=> x_i >= y_i for all i and
            x_i > y_i for at least one i
        """
        # assert both have same front_nr dimensions
        assert collections.Counter(this_sims.keys()) == collections.Counter(other_sims.keys())
        at_least_one_dimension_truly_bigger = False
        for dimension in this_sims.keys():
            this_sim, other_sim = this_sims[dimension], other_sims[dimension]
            if this_sim > other_sim:
                at_least_one_dimension_truly_bigger = True
            elif this_sim < other_sim:
                return False
        return at_least_one_dimension_truly_bigger

    @staticmethod 
    def crowded_compare(ind_1, ind_2):
        if ind_1.front_nr < ind_2.front_nr:
            return ind_1
        elif ind_1.front_nr > ind_2.front_nr:
            return ind_2
        elif ind_1.crowding_distance < ind_2.crowding_distance:
            return ind_2
        else:
            return ind_1
        
