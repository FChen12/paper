import abc
from geneticAlgoritm.Req2CodeGeneticAlgorithm import PrecalculatedSimilarityCSVDataReader
import random, logging
import collections
from nsga2.Gene import Gene

log = logging.getLogger(__name__)

class SeedData(abc.ABC):
    
    
    @abc.abstractmethod
    def get_random_gene(self):
        pass
    
    
class TraceLinkSeedData(SeedData):
    
    def __init__(self):
        self._similarity_data = {} # similarity_data["similarity_key_name"] = PrecalculatedSimilarityCSVDataReader()
        self._seed_req_list = None
        self._seed_code_list = None
        
    
    def add_seed_data(self, precalculated_sim_file, similarity_key_name: str, reverse_similarity=False, req_file_ext=None, code_file_ext=None):
        """
        similarity_key_name: arbitrary identifier for the precalculated sim file, e.g. "wmd" or "jaccard"
        """
        similarity_data = PrecalculatedSimilarityCSVDataReader(precalculated_sim_file, reverse_similarity, req_file_ext, code_file_ext)
        self._similarity_data[similarity_key_name] = similarity_data
        
        req_list = similarity_data.all_req_files()
        code_list = similarity_data.all_code_files()
        
        if self._seed_req_list:
            # assert lists are identical
            assert collections.Counter(req_list) == collections.Counter(self._seed_req_list)
        else:
            self._seed_req_list = req_list
            
        if self._seed_code_list:
            # assert lists are identical
            assert collections.Counter(code_list) == collections.Counter(self._seed_code_list)
        else:
            self._seed_code_list = code_list
    
    def get_random_gene(self):
        req, code = random.choice(self._seed_req_list), random.choice(self._seed_code_list)
        fitness_dict = self.get_all_similarities_as_dict(req, code)
        return Gene(req, code, fitness_dict)
    
    def get_similarity_keys(self):
        return self._similarity_data.keys()
    
    def get_similarity(self, similarity_key_name, req_key, code_key):
        return self._similarity_data[similarity_key_name].get_similarity(req_key, code_key)
    
    def get_all_similarities_as_dict(self, req_key, code_key):
        fitness_dict = {}
        for key in self.get_similarity_keys():
            fitness_dict[key] = self.get_similarity(key, req_key, code_key)
        return fitness_dict
    
    def config_print(self):
        key_filename_print = [f"{key}: {self._similarity_data[key].file_name()}" for key in self.get_similarity_keys()] 
        return f"Seed Data = {', '.join(key_filename_print)}"