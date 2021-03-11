import abc

class SelectionOperator(abc.ABC):
    
    @abc.abstractmethod
    def select_from(self, population):
        pass
    
    @abc.abstractmethod
    def config_print(self):
        pass
    
    
class BinaryTournamentSelection(SelectionOperator):
    
    def __init__(self, compare_function):
        self._compare_function = compare_function
        
    def select_from(self, population, unique=True):
        first = self._select(population)
        second = self._select(population)
        if unique:
            while first == second:
                second = self._select(population)
                
        return first, second
    
    def _select(self, population):
        ind_1, ind_2 = population.get_two_random_elements()
        return self._compare_function(ind_1, ind_2)
    
    def config_print(self):
        return f"Selection = BinaryTournamentSelection"
    
    
class RandomSelection(SelectionOperator):
    
        
    def select_from(self, population):
        return population.get_two_random_elements()[0]
    
    def config_print(self):
        return f"Selection = RandomSelection"
        
        