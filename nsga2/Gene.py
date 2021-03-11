import FileUtil
import Paths


class Gene:
    
    def __init__(self, req_name, code_name, fitness_dict= {}):
        self.req_name = req_name
        self.code_name = code_name
        self._fitness_dict = fitness_dict
        
    def get_fitness(self, dimension):
        return self._fitness_dict[dimension]
    
    def add_fitness(self, dimension, value):
        self._fitness_dict[dimension] = value
    
    def __eq__(self, other):
        return self.req_name == other.req_name and self.code_name == other.code_name
    
    def __repr__(self):
        return f"{self.req_name}, {self.code_name} {self._fitness_dict}"
    
    def __hash__(self):
        return hash(self.__repr__())
    
    @classmethod
    def load_precalculated_tracelinks_into_genes(cls, file_path, seed_data, req_ext=None, code_ext=None):
        trace_link_list = FileUtil.read_csv_to_list(file_path)
        genes = []
        for req_name, code_name in trace_link_list[1:]:
            if req_ext is not None:
                req_name = FileUtil.set_extension(req_name, req_ext)
            if code_ext is not None:
                code_name = FileUtil.set_extension(code_name, code_ext)
            genes.append(Gene(req_name, code_name, seed_data.get_all_similarities_as_dict(req_name, code_name)))
        return genes
