import abc, logging
import pathlib
from _operator import sub
import FileUtil
import Util

log = logging.getLogger(__name__)

class Embedding(abc.ABC):
    """
    An abstract base class to represent embeddings as objects
    
    Attributes
    ----------
    emb_id : int 
        id that identifies the embbedding
        
    file_path : str
        the file_path of the file that is represented with this embedding
        
    vector : ndarray
        The embedding vector for the file
        
    sub_vectors : [ndarray]
        possible sub vectors which can be used to calculate the embedding vector
        (e. g. method vectors for majority decision)
    """
    
    FILE_PATH = "file_path"
    VECTOR = "vector"
    SUB_VECTORS = "sub_vectors"
    
    
    def __init__(self, file_path, vector= None, sub_vectors=[]):
        self.file_path = file_path
        self.vector = vector
        self.sub_vectors = sub_vectors
        self.file_name = FileUtil.get_filename_from_path(self.file_path)
        self.file_name_without_extension = FileUtil.get_filename_without_extension__from_path(self.file_path)
    
    def get_key(self):
        return self.file_name_without_extension
    def __repr__(self):
        return str(self.file_name) + " " + str(self.vector)
    
    def to_json(self):
        emb_dict = {}
        emb_dict[self.FILE_PATH] = str(self.file_path)
        emb_dict[self.VECTOR] = self.vector.tolist() if self.vector is not None else None
        emb_dict[self.SUB_VECTORS] = [vec.tolist() for vec in self.sub_vectors]
        return emb_dict
        
    @classmethod
    def from_json(cls, emb_dict):
        vector = Util.numpy_array(emb_dict[cls.VECTOR]) if emb_dict[cls.VECTOR] else None
        sub_vectors = [Util.numpy_array(v) for v in emb_dict[cls.SUB_VECTORS]]
        return cls(pathlib.Path(emb_dict[cls.FILE_PATH]), vector, sub_vectors)
        
    

class RequirementEmbedding(Embedding):
    """
    Represents a requirement file
    """
    pass

class MockEmbedding(Embedding):
    pass
   
    
class CodeEmbedding(Embedding):
    """
    Each code file gets one CodeEmbedding that contains its class embedding and/or the unordered sub vectors (vectors of its class elements)
    """
    def __init__(self, file_path, vector=None, sub_vectors=[]):
        self.class_name = None
        super(CodeEmbedding, self).__init__(file_path, vector, sub_vectors)
    
    
class MethodCallGraphEmbedding(Embedding):
    
    CLASSNAME = "class_name"
    METHOD_DICT = "method_dict"
    METHOD_SIMS_DICT = "method_sims_dict"
    FILE_PATH = "file_path"
    NON_CG_DICT = "non_cg_dict"
    NON_CG_SIMS_DICT = "non_cg_sims_dict"
    CLASS_NAME_VOTER = "class_name_voter"
    
    def __init__(self, file_path, class_name, methods_dict):
        """
        contains additionally a dictionary that identifies the contained methods by their name and parameters:
        methods_dict["method_name(param_type_list)"] = method_vector
                                        }
        """
        super(MethodCallGraphEmbedding, self).__init__(file_path, None, [])
        self.class_name = class_name
        self.methods_dict = methods_dict # value is embedding vector of the method
        self.methods_sims_dict = {} # list of tuples (similarity, requirement_name) per method
        self.non_cg_dict = {}
        self.non_cg_sims_dict = {} # list of tuples (similarity, requirement_name) for code elements that take part in the
                                   # majority decision but have no call graph property e.g. class name
        
    def check_class_name(self, class_name):
        return self.class_name == class_name
    
    def get_method_vector(self, method_dict_key):
        if method_dict_key in self.methods_dict:
            return self.methods_dict[method_dict_key]
        log.debug("{} is not in {} methods_dict".format(method_dict_key, self.class_name))
        return None
    
    def get_method_sims(self, method_dict_key):
        if method_dict_key in self.methods_sims_dict:
            assert method_dict_key in self.methods_dict
            return self.methods_sims_dict[method_dict_key]
        log.debug("{} of is not in {} methods_sims_dict".format(method_dict_key, self.class_name))
        return None
    
    def add_method_sim(self, method_dict_key, similarity, req_name):
        if method_dict_key in self.methods_dict:
            if method_dict_key in self.methods_sims_dict:
                self.methods_sims_dict[method_dict_key].append((similarity, req_name))
            else:
                self.methods_sims_dict[method_dict_key] = [(similarity, req_name)]
        else:
            log.info("{} is not in {} methods_dict".format(method_dict_key, self.class_name))
    
    def add_method_vector_and_sim(self, method_dict_key, vector, similarity, req_name):
        self.methods_dict[method_dict_key] = vector
        self.add_method_sim(method_dict_key, similarity, req_name)
        
    def get_non_cg_sim(self, dict_key):
        if dict_key in self.non_cg_sims_dict:
            return self.non_cg_sims_dict[dict_key]
        log.info(f"No entry in non method dict with the key {dict_key}")
        return None
        
    def add_non_cg_sim(self, dict_key, similarity, req_name):
        if dict_key in self.non_cg_sims_dict:
            self.non_cg_sims_dict[dict_key].append((similarity, req_name))
        else:
            self.non_cg_sims_dict[dict_key] = [(similarity, req_name)]
            
    def add_non_cg_vector_and_sim(self, dict_key, vector, similarity, req_name):
        self.non_cg_dict[dict_key] = vector
        self.add_non_cg_sim(dict_key, similarity, req_name)
        
    def to_json(self):
        embedding_dict = {}
        embedding_dict[self.CLASSNAME] = self.class_name
        embedding_dict[self.FILE_PATH] = str(self.file_path)
        json_conform_sims_dict = {}
        for method_key in self.methods_sims_dict:
            json_conform_sims_dict[method_key] = [list(tup) for tup in self.methods_sims_dict[method_key]]
        embedding_dict[self.METHOD_SIMS_DICT] = json_conform_sims_dict
        
        json_conform_methods_dict = {}
        for method_key in self.methods_dict: # change ndarrays to list
            json_conform_methods_dict[method_key] = self.methods_dict[method_key].tolist()
        embedding_dict[self.METHOD_DICT] = json_conform_methods_dict
        
        json_conform_non_method_sims_dict = {}
        for key in self.non_cg_sims_dict:
            json_conform_non_method_sims_dict[key] = [list(tup) for tup in self.non_cg_sims_dict[key]]
        embedding_dict[self.NON_CG_SIMS_DICT] = json_conform_non_method_sims_dict
        
        json_conform_non_cg_dict = {}
        for key in self.non_cg_dict: # change ndarrays to list
            json_conform_non_cg_dict[key] = self.non_cg_dict[key].tolist()
        embedding_dict[self.NON_CG_DICT] = json_conform_non_cg_dict
        
        return embedding_dict
        
    @classmethod
    def from_json(cls, embedding_dict):
        method_dict = {}
        json_method_dict = embedding_dict[cls.METHOD_DICT]
        for method_key in json_method_dict:
            method_dict[method_key] = Util.numpy_array(json_method_dict[method_key])
        instance = cls(pathlib.Path(embedding_dict[cls.FILE_PATH]), embedding_dict[cls.CLASSNAME], method_dict)
        json_sims_dict = embedding_dict[cls.METHOD_SIMS_DICT]
        for method_key in json_sims_dict:
            for tup in json_sims_dict[method_key]:
                instance.add_method_sim(method_key, tup[0], tup[1])
        
        json_non_method_dict = {}        
        if cls.NON_CG_DICT in embedding_dict:
            json_non_method_dict = embedding_dict[cls.NON_CG_DICT]
            
        non_cg_dict = {}
        for key in json_non_method_dict:
            non_cg_dict[key] = Util.numpy_array(json_non_method_dict[key])
        instance.non_cg_dict = non_cg_dict
        if non_cg_dict:
            json_non_method_sims_dict = embedding_dict[cls.NON_CG_SIMS_DICT]
            for key in json_non_method_sims_dict:
                for tup in json_non_method_sims_dict[key]:
                    instance.add_non_cg_sim(key, tup[0], tup[1])
        return instance
    
class MethodCallGraphEmbeddingMultipleSims(MethodCallGraphEmbedding):
    """
    The methods_sims_dict can contain multiple similarities per requirement, e.g. similarities to the separate parts of
    the requirement
    
    methods_sims_dict = list of tuples ([sim_1, sim_2, ..], requirement_name) per method 
    """

    def add_method_sim(self, method_dict_key, similarity: list, req_name):
        assert isinstance(similarity, list)
        super(MethodCallGraphEmbeddingMultipleSims, self).add_method_sim(method_dict_key, similarity, req_name)
        
    def add_non_cg_sim(self, dict_key, similarity, req_name):
        assert isinstance(similarity, list)
        super(MethodCallGraphEmbeddingMultipleSims, self).add_non_cg_sim(dict_key, similarity, req_name)
