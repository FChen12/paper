import abc
import random
import Util, logging
from nsga2.Individual import Individual

log = logging.getLogger(__name__)

class MutationOperator(abc.ABC):
    
    def __init__(self, mutation_probability):
        self._mutation_probability = mutation_probability
        
    
    def mutate(self, individuals) -> [Individual]:
        if random.random() < self._mutation_probability:
            return [self._do_mutation(individual) for individual in individuals]
        return individuals
    
    @abc.abstractmethod
    def _do_mutation(self, individual):
        pass
    
    @abc.abstractmethod
    def config_print(self):
        pass
    
class RandomMutation(MutationOperator):
    
    def __init__(self, mutation_probability, seed_data, max_mutation_size=None):
        super(RandomMutation, self).__init__(mutation_probability)
        self._seed_data = seed_data
        self._max_mutation_size = max_mutation_size
        
    def _do_mutation(self, individual):
        num_links_before_mutation = individual.size()
        assert num_links_before_mutation > 0, f"Individual has {num_links_before_mutation} trace links!"
        mutation_size = 1 if num_links_before_mutation == 1 else random.randrange(1, min(self._max_mutation_size + 1, num_links_before_mutation))
        removed_elems = []
        for _ in range(mutation_size):
            removed_elems.append(individual.remove_random_gene())
            
        while individual.size() < num_links_before_mutation:
            to_add = self._seed_data.get_random_gene()
            if to_add not in removed_elems:
                individual.add_gene(to_add)
        return individual
    
    def config_print(self):
        return f"Mutation = RandomMutation(prob={self._mutation_probability}, max_size={self._max_mutation_size})"
        