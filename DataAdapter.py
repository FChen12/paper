import abc, logging
from Embedding import Embedding, MockEmbedding
from TraceLink import CodeToRequirementsCandidates
import FileUtil
from TracePairPrecalculator import TracePairPrecalculator

log = logging.getLogger(__name__)

class DataAdapter(abc.ABC):
    """
    A data adapter can contain data from precalculated files or actual embedding objects.
    It encapsulates the source of the data.
    """
      
    @abc.abstractmethod
    def code_file_list(self, **kwargs):
        pass
    
    @abc.abstractmethod
    def code_element_list(self, code_file):
        pass
    
    @abc.abstractmethod
    def req_file_list(self, **kwargs):
        pass
    
    @abc.abstractmethod
    def req_element_list(self, req_file):
        pass
    
    @abc.abstractmethod
    def code_filename(self, code_file):
        pass
    
    @abc.abstractmethod
    def req_filename(self, req_file):
        pass
    
    @abc.abstractmethod
    def req_emb(self, req_file):
        pass
    
    @abc.abstractmethod
    def init_candidate_tracelink(self, code_file):
        pass
    
    @abc.abstractmethod
    def calculate_similarity(self, req_elem, code_elem, sim_func):
        pass
    
    @abc.abstractmethod
    def get_req_file(self, req_filename):
        pass
    
class EmbeddingsDataAdapter(DataAdapter):
    """
    Contains two lists of actual embedding objects
    """
    def __init__(self, req_embeddings, code_embeddings):
        self._req_embeddings = req_embeddings
        self._code_embeddings = code_embeddings
        
        
    def code_file_list(self, **kwargs):
        return self._code_embeddings
    
    def req_file_list(self, **kwargs):
        return self._req_embeddings

    def code_element_list(self, code_emb):
        return code_emb.sub_vectors
    
    def req_element_list(self, req_emb):
        return req_emb.sub_vectors
    
    def code_filename(self, code_file):
        return code_file.file_name_without_extension
    
    def req_filename(self, req_emb):
        return req_emb.file_name_without_extension
    
    def req_emb(self, req_file):
        return req_file
    
    def init_candidate_tracelink(self, code_file):
        return CodeToRequirementsCandidates(code_file)
    
    def calculate_similarity(self, req_elem, code_elem, sim_func):
        if isinstance(req_elem, Embedding) and isinstance(code_elem, Embedding):
            return sim_func(req_elem.vector, code_elem.vector)
        return sim_func(req_elem, code_elem) #req_elem and code_elem are numpy arrays
    
    def get_req_file(self, req_filename):
        for req in self._req_embeddings:
            if req.file_name  == req_filename:
                return req
        log.info("{} not in req file list of {}".format(req_filename, self.__class__.__name__))
    
class PrecalculatedTracePairDataAdapter(DataAdapter):
    """
    Data is loaded from a precalculated json file.
    """
    CODE_ENTRY = "code_elem"
    CODE_FILE = "code_file"
    def __init__(self, trace_pair_json_file):
        self._code_file_dict = FileUtil.read_dict_from_json(trace_pair_json_file)[TracePairPrecalculator.CODE_FILE_LIST]
        
    def change_to_dataset(self, dataset):
        pass
    def code_file_list(self, **kwargs):
        return self._code_file_dict
    
    def req_file_list(self, **kwargs):
        if self.CODE_ENTRY in kwargs:
            return kwargs[self.CODE_ENTRY][TracePairPrecalculator.REQUIREMENT_LIST]
        elif self.CODE_FILE in kwargs:
            return kwargs[self.CODE_FILE][TracePairPrecalculator.REQUIREMENT_LIST]
        else:
            log.error("Unexpected behaviour: req_file_list")
    
    def code_element_list(self, code_file):
        return code_file[TracePairPrecalculator.CODE_ELEMENT_LIST] if code_file else []
    
    def req_element_list(self, req_file):
        return req_file[TracePairPrecalculator.REQUIREMENT_ELEMENT_LIST]
    
    def code_filename(self, code_file):
        return code_file[TracePairPrecalculator.CODE_FILENAME]
    
    def req_filename(self, req_file):
        return req_file[TracePairPrecalculator.REQUIREMENT_FILENAME]
    
    def req_emb(self, req_file):
        return MockEmbedding(self.req_filename(req_file))
    
    def init_candidate_tracelink(self, code_file):
        return CodeToRequirementsCandidates(MockEmbedding(code_file[TracePairPrecalculator.CODE_FILENAME]))
                                                 
    def calculate_similarity(self, req_elem, code_elem, sim_func):
        # Ignore code_elem and sim func -> similarities are already pre-calculated
        if TracePairPrecalculator.SIMILARITY in req_elem: # req_elem is a requirement element
            return req_elem[TracePairPrecalculator.SIMILARITY]
        elif TracePairPrecalculator.REQUIREMENT_ELEMENT_LIST in req_elem: #req_elem is a requirement file
            return req_elem[TracePairPrecalculator.REQUIREMENT_ELEMENT_LIST][0][TracePairPrecalculator.SIMILARITY]
        
    def get_req_file(self, req_filename):
        log.error("get_req_file not supported for " + self.__class__.__name__)
        
class DataAdapterLoader(abc.ABC):
    """
    The subclasses distinguishes trace link processors.
    e. g. trace link processors who use precalculated data inherit from PrecalculatedTracePairProcessor
    """
    def __init__(self):
        self._data_adapter = None
        
        
class PrecalculatedTracePairProcessor(DataAdapterLoader):
    """
    precalculated file contains req-code trace pairs
    """
    def load_from_precalculated(self, precalculated_filename):
        if not FileUtil.file_exists(precalculated_filename):
            raise FileNotFoundError("Could not find file: " + str(precalculated_filename))
        self._data_adapter = PrecalculatedTracePairDataAdapter(precalculated_filename) 
    
    @abc.abstractclassmethod
    def precalculate_tracelinks(self, output_precalculated_filename):
        pass

class DualPrecalculatedTracePairProcessor(DataAdapterLoader):
    """
    using 2 precalculated files containing req-code trace pairs
    (used for trace link processors that combine 2 self trained bert models)
    """
    def __init__(self):
        super(DualPrecalculatedTracePairProcessor, self).__init__()
        self._data_adapter_2 = None
        
    def load_from_precalculated(self, precalculated_filename, precalculated_filename_2):
        if not FileUtil.file_exists(precalculated_filename):
            raise FileNotFoundError("Could not find file: " + str(precalculated_filename))
        if not FileUtil.file_exists(precalculated_filename_2):
            raise FileNotFoundError("Could not find file: " + str(precalculated_filename_2))
        self._data_adapter = PrecalculatedTracePairDataAdapter(precalculated_filename)
        self._data_adapter_2 = PrecalculatedTracePairDataAdapter(precalculated_filename_2) 
    
    @abc.abstractclassmethod
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None):
        pass
    
class PrecalculatedEmbeddingsProcessor(DataAdapterLoader):
    """
    separate precalculated files for req and code embeddings  
    """
    @abc.abstractclassmethod
    def load_from_precalculated(self, precalculated_req_filename, precalculated_code_filename):
        pass
    
    @abc.abstractclassmethod
    def precalculate_tracelinks(self, output_precalculated_req_filename, output_precalculated_code_filename):
        pass
    
class EmbeddingsProcessor(DataAdapterLoader):
    """
    Non-precalculated 
    """
    @abc.abstractclassmethod
    def load_from_embeddings(self, dataset, precalculated_filename):
        pass