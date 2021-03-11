import logging, abc

class TerminationCriterion(abc.ABC):
    
    @abc.abstractmethod
    def update(self, population):
        pass
    
    @abc.abstractmethod
    def is_fullfilled(self):
        pass
    
    @abc.abstractmethod
    def config_print(self):
        pass
    
    
class MaxGenerationsCriterion(TerminationCriterion):
    
    def __init__(self, max_generations):
        assert max_generations >= 1
        self._max_generations = max_generations
        self._current_generations = 1
        
    def update(self, population):
        self._current_generations += 1
    
    def is_fullfilled(self):
        return self._current_generations > self._max_generations
    
    def config_print(self):
        return f"Termination = After {self._max_generations} generations"