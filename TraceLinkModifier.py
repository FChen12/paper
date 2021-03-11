import abc
from TraceLink import CodeToRequirementsCandidates

class TraceLinkEvolutionPipeline:
    
    

class TraceLinkModifier:
    
    @abc.abstractmethod
    def modify_tracelinks(self, trace_link_candidates: CodeToRequirementsCandidates):
        pass
    