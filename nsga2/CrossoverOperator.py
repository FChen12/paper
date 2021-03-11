import abc
import random
import Util, logging
from nsga2.Individual import Individual

log = logging.getLogger(__name__)

class CrossoverOperator(abc.ABC):
    
    def __init__(self, crossover_probability):
        self._crossover_probability = crossover_probability
        
    
    def crossover(self, parent_1, parent_2) -> (Individual, Individual):
        if random.random() < self._crossover_probability:
            return self._do_crossover(parent_1, parent_2)
        return parent_1, parent_2
    
    @abc.abstractmethod
    def _do_crossover(self, parent_1, parent_2):
        pass
    
    @abc.abstractmethod
    def config_print(self):
        pass
    
class BinaryCrossover(CrossoverOperator):
    
    def __init__(self, crossover_probability, max_crossover_size=None):
        super(BinaryCrossover, self).__init__(crossover_probability)
        self._max_crossover_size = max_crossover_size
        
    def _do_crossover(self, parent_ind_1, parent_ind_2):
        child_1, child_2 = Util.deep_copy(parent_ind_1), Util.deep_copy(parent_ind_2)
        parent_1_selection_pool, parent_2_selection_pool = [], [] # pools from which crossover trace links are selected
        
        if parent_ind_1.duplicate_genes_allowed():
            parent_1_selection_pool = parent_ind_1.get_all_genes()
        else:
            # pool must contain only distinct links to avoid duplicates
            parent_1_selection_pool = list(parent_ind_1.difference_ignoring_duplicates(parent_ind_2))
            
        if parent_ind_2.duplicate_genes_allowed():
            parent_2_selection_pool = parent_ind_2.get_all_genes()
        else:
            # parent_1_selection_pool is not equal parent_2_selection_pool if parents have different sizes
            parent_2_selection_pool = list(parent_ind_2.difference_ignoring_duplicates(parent_ind_1))
                
        min_parent_selection_size = min(len(parent_1_selection_pool), len(parent_2_selection_pool))        
        if min_parent_selection_size == 0:
            log.info(f"Returning unchanged childs for crossover: parents have no differences")
            return child_1, child_2
        exchange_size = 1 if min_parent_selection_size == 1 else random.randrange(1, min(min_parent_selection_size, self._max_crossover_size + 1))
                
        random.shuffle(parent_1_selection_pool)
        random.shuffle(parent_2_selection_pool)
        while exchange_size > 0:
            child_1_gene = parent_1_selection_pool.pop(0)
            child_2_gene = parent_2_selection_pool.pop(0)
            child_1.add_gene(child_2_gene)
            child_1.remove_gene(child_1_gene)
            child_2.add_gene(child_1_gene)
            child_2.remove_gene(child_2_gene)
            exchange_size -= 1    
        
        return child_1, child_2

    def config_print(self):
        return f"Crossover = BinaryCrossover(prob={self._crossover_probability}, max_size={self._max_crossover_size})"