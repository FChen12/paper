import abc, logging

log = logging.getLogger(__name__)

class Aggregator(abc.ABC):
    
    @classmethod
    @abc.abstractmethod
    def aggregate(self, data: [float]):
        pass
    
    @classmethod
    @abc.abstractmethod
    def config_print(self):
        pass
    

class AverageAggregator(Aggregator):
    
    @classmethod
    def aggregate(self, data: [float]):
        if not data:
            log.error("Nothing to average")
        if len(data) == 1:
            return data[0]
        return sum(data) / len(data)
    
    @classmethod
    def config_print(cls):
        return f"Aggregation = Average"
    
class SumAggregator(Aggregator):
    
    @classmethod
    def aggregate(self, data: [float]):
        if not data:
            log.error("Nothing to sum up")
        return sum(data)
    
    @classmethod
    def config_print(cls):
        return f"Aggregation = Sum"
            
    
    