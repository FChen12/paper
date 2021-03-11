from TraceLinkProcessor import TraceLinkProcessor, DEFAULT_REQ_PREPROCESSOR,\
    DEFAULT_CODE_PREPROCESSOR, RunConfiguration
from WordEmbeddingCreator.WordEmbeddingCreator import FastTextEmbeddingCreator,\
    MockWordEmbeddingCreator, FastTextAlignedEngItalEmbeddingCreator
from EmbeddingCreator import MockEmbeddingCreator
from Preprocessing.Tokenizer import WordTokenizer, WordAndSentenceTokenizer,\
    UCTokenizer
from Paths import PREPROCESSED_REQ_OUTPUT_DIR, PREPROCESSED_CODE_OUTPUT_DIR,\
    precalculated_json_filename
from Preprocessing.CodeASTTokenizer import JavaCodeASTTokenizer
from Dataset import Dataset, Smos, Libest
import Evaluator
from Embedding import MockEmbedding, RequirementEmbedding,\
    MethodCallGraphEmbedding, MethodCallGraphEmbeddingMultipleSims, Embedding
from _functools import partial
from TracePairPrecalculator import TracePairPrecalculator
import Util
from DataAdapter import PrecalculatedTracePairDataAdapter,\
    PrecalculatedTracePairProcessor, EmbeddingsDataAdapter
from TraceLinkCreator import TopNTraceLinkCreator, MajorityTraceLinkCreator
import abc, logging
import FileUtil
from Preprocessing.CallGraphUtil import build_method_param_dict_key
from nltk.classify.megam import numpy

log = logging.getLogger(__name__)

"""
Contains TraceLinkProcessors who work with WMD
"""


WMD_VALUE_MAP_FUNC = partial(Util.map_value_range, 0, 2)

class FastTextWMDTLP(TraceLinkProcessor, PrecalculatedTracePairProcessor):
    """
    Super class for fastText trace links with word mover's distance
    """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)  
    
    def _other_constructor_init(self):
        PrecalculatedTracePairProcessor.__init__(self)
        
    def _get_data_adapter(self):
        return self._data_adapter
    
    @classmethod
    def is_reverse_compare(cls):
        return True
    
    
    def build_precalculated_name_and_load(self, dataset = None, output_suffix = ""):
        self.reload_with_dataset(dataset, output_suffix)
        
    def build_precalculated_name_and_load_callgraph_wmd(self, dataset = None, output_suffix = ""):
        self.reload_with_dataset_callgraph_wmd(dataset, output_suffix)
        
    def reload_with_dataset(self, dataset, output_suffix = ""):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        self.load_from_precalculated(self.default_precalculated_filename(output_suffix))
        
    def reload_with_dataset_callgraph_wmd(self, dataset, output_suffix = ""):
        if dataset:
            self._dataset = dataset
            self._trace_link_creator.method_call_graph_dict = self._dataset.method_callgraph()
            if isinstance(dataset, Libest):
                self._trace_link_creator.no_classname_in_cg_key = True
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        precalculated_req_filename = self.default_precalculated_filename("_callgraph_req_file" + output_suffix)
        precalculated_code_filename = self.default_precalculated_filename("_callgraph_code_file" + output_suffix)

        req_json = FileUtil.read_dict_from_json(precalculated_req_filename)
        code_json = FileUtil.read_dict_from_json(precalculated_code_filename)
        req_embeddings = [Embedding.from_json(req_dict) for req_dict in req_json]
        code_embeddings = [MethodCallGraphEmbedding.from_json(code_dict) for code_dict in code_json]
        self._data_adapter = EmbeddingsDataAdapter(req_embeddings, code_embeddings)
        self._trace_link_creator.method_call_graph_dict = self._dataset.method_callgraph()
        if isinstance(self._dataset, Libest):
            self._trace_link_creator.no_classname_in_cg_key = True

    def default_precalculated_filename(self, output_name_suffix=""):
        return precalculated_json_filename(self._dataset, self.__class__.__name__, self.__class__.__name__ + output_name_suffix)
    
    
class FastTextFileLevelWMDTLP(FastTextWMDTLP):
    """
    Super class for fastText wmd that operates on file level.
    """
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, file_level_drop_thresholds, normalize, rule_applier): 
        # elem thresh, maj thresh, req and code req func have no effect here
        return super(FastTextFileLevelWMDTLP, cls).create(dataset, word_emb_creator, trace_link_creator, [1], [1], file_level_drop_thresholds,
                                            normalize, None, None, rule_applier)
    
class FastTextIdentifierWMDTLP(FastTextFileLevelWMDTLP):
    """  WMD distance: Req as word list, Class as unordered method signature and class name list """
        
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.token_list]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.token_list]   
        return req_dict
    
    def _fill_code_dict(self, code_emb):
        all_identifiers = []
        for cls in code_emb.vector.classifiers:
            all_identifiers += cls.get_name_words()
            for meth in cls.methods:
                all_identifiers += meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
        return all_identifiers
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        
        # convert embedding list into dictionary form (needed input format for TracePairPrecalculator)
        req_dict = dict()
        for req_emb in req_embeddings:
            req_dict = self._fill_req_dict(req_dict, req_emb)
                         
        code_dict = dict()
        for code_emb in code_embeddings:
            all_identifiers = self._fill_code_dict(code_emb)
            
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = [all_identifiers]
            else:
                code_dict[code_emb.file_name_without_extension] = [all_identifiers]
        
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos): # Ital Req, Eng identifier
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=False)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
            WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)

    def output_prefix(self):
        return "ft_Identifier_wmd"
    

class FastTextUCNameIdentifierWMDTLP(FastTextIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words]   
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_name_Identifier_wmd"
    
class FastTextUCNameDescIdentifierWMDTLP(FastTextIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words + req_emb.vector.description_words]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words + req_emb.vector.description_words]
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_namedesc_Identifier_wmd"
    
class FastTextUCNameDescFlowIdentifierWMDTLP(FastTextIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words + req_emb.vector.description_words + [word for group in req_emb.vector.flow_of_events_words for word in group]]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words + req_emb.vector.description_words + [word for group in req_emb.vector.flow_of_events_words for word in group]]
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_namedescflow_Identifier_wmd"
    
class FastTextUCNameDescFlowRodriguezIdentifierWMDTLP(FastTextUCNameDescFlowIdentifierWMDTLP):
    
    def _fill_code_dict(self, code_emb):
        all_identifiers = []
        for cls in code_emb.vector.classifiers:
            all_identifiers += cls.get_name_words()
            for meth in cls.methods:
                all_identifiers += meth.get_name_words()
                for param_tuple in meth.get_param_tuples():
                    if param_tuple and param_tuple[1]:
                        all_identifiers += param_tuple[1] # Only add the parameter names, not the types
                all_identifiers += meth.get_left_side_identifier_words()
        return all_identifiers
    
    def output_prefix(self):
        return "ft_UC_namedescflow_rodriguez_Identifier_wmd"
    
class FastTextCommentWMDTLP(FastTextFileLevelWMDTLP):
    """ WMD distance: Req as word list, Class as unordered comment word list"""

    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = [req_emb.vector.token_list]
            else:
                req_dict[req_emb.file_name_without_extension] = [req_emb.vector.token_list]
                
        code_dict = dict()
        for code_emb in code_embeddings:
            comm_list = code_emb.vector.get_all_comment_tokens_as_list()
            if comm_list:
                if self._dataset.keys_with_extension():
                    code_dict[code_emb.file_name] = [comm_list]
                else:
                    code_dict[code_emb.file_name_without_extension] = [comm_list]
        
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            self._word_emb_creator.word_movers_distance, 
            output_precalculated_filename,
            WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def output_prefix(self):
        return "ft_comment_wmd"

class FastTextCodeElementLevelWMDTLP(FastTextWMDTLP):
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, req_reduce_func, code_reduce_func, rule_applier):
        assert isinstance(trace_link_creator, MajorityTraceLinkCreator) or isinstance(trace_link_creator, TopNTraceLinkCreator), \
                                    "trace_link_creator has to be MajorityTraceLinkCreator or TopNTraceLinkCreator"
        return super(FastTextCodeElementLevelWMDTLP, cls).create(dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs,
                                                           file_level_drop_thresholds, normalize, req_reduce_func, code_reduce_func, rule_applier)
        
    def _calculate_req_and_code_embeddings(self, req_embedding_creator, code_embedding_creator):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        
        return req_embeddings, code_embeddings
    
    def precalculate_for_callgraph_files(self, output_precalculated_req_filename=None, output_precalculated_code_filename=None,
                                          req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not output_precalculated_req_filename:
            output_precalculated_req_filename = self.default_precalculated_filename("_callgraph_req_file" + output_name_suffix)
        if not output_precalculated_code_filename:
            output_precalculated_code_filename = self.default_precalculated_filename("_callgraph_code_file" + output_name_suffix)
            
        req_embeddings, code_embeddings = self._calculate_req_and_code_embeddings(req_embedding_creator, code_embedding_creator)
        
        code_emb_json_data = []
        for code_emb in code_embeddings:
            # transform MockEmbeddings into MethodCallGraphEmbeddingMultipleSims
            for cls in code_emb.vector.classifiers:
                class_name = cls.get_name_words()
                class_name_words = self._choose_classname_words(cls)
                cg_emb = MethodCallGraphEmbeddingMultipleSims(code_emb.vector.file_path, cls.get_original_name(), {})
                
                for meth in cls.methods:
                    
                    cls_prefixed_method_name = class_name + self._choose_method_words(meth) 
                    if isinstance(self._dataset, Libest):
                        method_dict_key = build_method_param_dict_key(meth.get_original_name(), []) 
                    else:
                        method_dict_key = build_method_param_dict_key(meth.get_original_name(),
                                   meth.get_original_param_type_list()) 
                    
                    if cg_emb.get_method_sims(method_dict_key) is not None:
                        log.info(f"SKIPPING: {method_dict_key} is multiple times in {cg_emb.file_name}")
                        continue
                    for req_emb in req_embeddings:
                        req_parts = self._choose_req_words(req_emb)
                        sims_of_all_parts = [self._word_emb_creator.word_movers_distance(req_part, cls_prefixed_method_name) for req_part in req_parts]
                        sims_of_all_parts = [Util.map_value_range(0, 2, sim) for sim in sims_of_all_parts]
                        cg_emb.add_method_vector_and_sim(method_dict_key, numpy.empty(0), sims_of_all_parts, req_emb.file_name) # []: We can't save a vector for wmd, only the similarities
                if self.cls_name_voter(cg_emb.methods_dict) and class_name_words:
                    for req_emb in req_embeddings:
                        req_parts = self._choose_req_words(req_emb)
                        sims_of_all_parts = [self._word_emb_creator.word_movers_distance(req_part, class_name_words) for req_part in req_parts]
                        sims_of_all_parts = [Util.map_value_range(0, 2, sim) for sim in sims_of_all_parts]
                        cg_emb.add_non_cg_vector_and_sim(MethodCallGraphEmbedding.CLASS_NAME_VOTER, numpy.empty(0), sims_of_all_parts, req_emb.file_name)
                if cg_emb.non_cg_dict or cg_emb.methods_dict: # class has valid elements
                    code_emb_json_data.append(cg_emb.to_json())
        req_emb_json_data = []
        for req_emb in req_embeddings:
            req_emb.vector = None
            req_emb.sub_vectors = []
            req_emb_json_data.append(req_emb.to_json())
            
        FileUtil.write_dict_to_json(output_precalculated_req_filename, req_emb_json_data)
        FileUtil.write_dict_to_json(output_precalculated_code_filename, code_emb_json_data)
        
    def _choose_classname_words(self, cls):
        return cls.get_name_words()
    def _choose_method_words(self, meth):
        return meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
    def _choose_req_words(self, req_emb):
        return None
    
    def cls_name_voter(self, m_dict):
        return True
    
class FastTextSentenceLevelIdentifierWMDTLP(FastTextCodeElementLevelWMDTLP):
    """  WMD distance: Req as sentence list, Class as method with class name prefix list 
        Calculate wmd distance between req sentence and method name
        aggregate wmd method name to all req sentences of a req with req_wmd_reduce_func
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = []
            else:
                req_dict[req_emb.file_name_without_extension] = []
            for req_sentence in req_emb.vector.grouped_token_list:
                if self._dataset.keys_with_extension():
                    req_dict[req_emb.file_name].append(req_sentence)
                else:
                    req_dict[req_emb.file_name_without_extension].append(req_sentence)
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for meth in cls.methods:
                    cls_prefixed_method_name = cls.get_name_words() + meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(cls_prefixed_method_name)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(cls_prefixed_method_name)
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos): # Ital Req, Eng identifier
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=False)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def _choose_req_words(self, req_emb):
        return req_emb.vector.grouped_token_list
    
    def output_prefix(self):
        return "ft_sentencelevel_Identifier_wmd"
    

class FastTextUCSentenceLevelIdentifierWMDTLP(FastTextSentenceLevelIdentifierWMDTLP):
    """  WMD distance: Req as sentence list, Class as method with class name prefix list 
        Calculate wmd distance between req sentence and method name
        aggregate wmd method name to all req sentences of a req with req_wmd_reduce_func
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        log.error("default req emb creator not supported for " + self.__class__.__name__)
        """if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, UCTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)"""
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    @abc.abstractmethod
    def _choose_req_words(self, req_emb):
        pass
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator, code_embedding_creator=None, output_name_suffix=""):
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
        req_embeddings, code_embeddings = self._calculate_req_and_code_embeddings(req_embedding_creator, code_embedding_creator)
        req_dict = dict()
        for req_emb in req_embeddings:
            req_key = req_emb.file_name_without_extension
            if self._dataset.keys_with_extension():
                req_key = req_emb.file_name
            req_dict[req_key] = []
            req_dict[req_key] += self._choose_req_words(req_emb)
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                class_name = cls.get_name_words()
                if self._dataset.keys_with_extension():
                    code_dict[code_emb.file_name].append(class_name)
                else:
                    code_dict[code_emb.file_name_without_extension].append(class_name)
                for meth in cls.methods:
                    cls_prefixed_method_name = class_name + meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(cls_prefixed_method_name)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(cls_prefixed_method_name)
                        
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos): # Ital Req, Eng identifier
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=False)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
        
    def output_prefix(self):
        return "ft_sentencelevel_Identifier_wmd"
    
class FastTextUCNameSentenceLevelIdentifierWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words]
    
    def output_prefix(self):
        return "ft_UC_name_sentencelevel_Identifier_wmd"
    
class FastTextUCNameDescSentenceLevelIdentifierWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words]
    def output_prefix(self):
        return "ft_UC_namedesc_sentencelevel_Identifier_wmd"
    
class FastTextUCNameDescFlowSentenceLevelIdentifierWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words, [word for group in req_emb.vector.flow_of_events_words for word in group]]
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencelevel_Identifier_wmd"
    
class FastTextUCNameDescFlowSentenceLevelIdentifierNoClassNameVoterWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words, [word for group in req_emb.vector.flow_of_events_words for word in group]]
    
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencelevel_Identifier_no_classname_voter_wmd"
    def cls_name_voter(self, m_dict):
        return False
    
class FastTextUCNameDescFlowSentenceSpecificIdentifierNoClassNameVoterWMDTLP(FastTextUCNameDescFlowSentenceLevelIdentifierNoClassNameVoterWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]
    
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencespecific_Identifier_no_classname_voter_wmd"
    
class FastTextUCNameDescFlowSentenceLevelIdentifierClassNameVoterOptionalWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words, [word for group in req_emb.vector.flow_of_events_words for word in group]]
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencelevel_Identifier_classname_voter_optional_wmd"
    def cls_name_voter(self, m_dict):
        return not m_dict
    
class FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencespecific_Identifier_classname_voter_optional_wmd"
    def cls_name_voter(self, m_dict):
        return not m_dict
    
class FastTextUCNameDescFlowSentenceSpecificIdentifierWMDTLP(FastTextUCSentenceLevelIdentifierWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]
    
    def output_prefix(self):
        return "ft_UC_namedescflow_sentencespecific_Identifier_wmd"
    
class FastTextAllCommentSentenceIdentifierWMDTLP(FastTextCodeElementLevelWMDTLP):
    def precalculate_tracelinks(self):
        pass
    
    def _choose_classname_words(self, cls):
        return cls.get_name_words() + cls.get_comment_tokens()
    
    def _choose_req_words(self, req_emb):
        return req_emb.vector.grouped_token_list
    
    def _choose_method_words(self, meth):
        return meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words() + meth.get_comment_tokens()
    
    def output_prefix(self):
        return "ft_all_comm_Identifier_sentence_wmd"
    
class FastTextAllCommentSentenceIdentifierClassNameVoterOptionalWMDTLP(FastTextAllCommentSentenceIdentifierWMDTLP):
    def cls_name_voter(self, m_dict):
        return not m_dict
    
class FastTextUCNameDescFlowAllCommentSentenceSpecificIdentifierWMDTLP(FastTextAllCommentSentenceIdentifierWMDTLP):
    
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]

class FastTextUCNameDescFlowAllCommentSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP(FastTextUCNameDescFlowAllCommentSentenceSpecificIdentifierWMDTLP):

    def cls_name_voter(self, m_dict):
        return not m_dict
    
class FastTextFileLevelIdentifierWMDTLP(FastTextCodeElementLevelWMDTLP):
    """  WMD distance: Req as word list, Class as methods with class name prefix list 
        Calculate wmd distance between req and method name
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, code_reduce_func, rule_applier): 
        #req reduce func has no effect here
        return super(FastTextFileLevelIdentifierWMDTLP, cls).create(dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, max, code_reduce_func, rule_applier)
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = [req_emb.vector.token_list]
            else:
                req_dict[req_emb.file_name_without_extension] = [req_emb.vector.token_list]
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for meth in cls.methods:
                    cls_prefixed_method_name = cls.get_name_words() + meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(cls_prefixed_method_name)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(cls_prefixed_method_name)
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos): # Ital Req, Eng identifier
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=False)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def output_prefix(self):
        return "ft_filelevel_Identifier_wmd"
    
class FastTextUCFileLevelIdentifierWMDTLP(FastTextFileLevelIdentifierWMDTLP):
    """  WMD distance: Req as UC name list, Class as methods with class name prefix list 
        Calculate wmd distance between req and method name
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        log.error("default req emb creator not supported for " + self.__class__.__name__)
        """
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, UCTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)"""
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    @abc.abstractmethod
    def _fill_req_dict(self, req_dict, req_emb):
        pass
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            req_dict = self._fill_req_dict(req_dict, req_emb)
            
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for meth in cls.methods:
                    cls_prefixed_method_name = cls.get_name_words() + meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(cls_prefixed_method_name)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(cls_prefixed_method_name)
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos): # Ital Req, Eng identifier
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=False)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def output_prefix(self):
        return "use a subclass of this class"
    

class FastTextUCNameFileLevelIdentifierWMDTLP(FastTextUCFileLevelIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words]
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_name_filelevel_Identifier_wmd"
    
class FastTextUCNameDescFileLevelIdentifierWMDTLP(FastTextUCFileLevelIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words + req_emb.vector.description_words]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words + req_emb.vector.description_words]
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_namedesc_filelevel_Identifier_wmd"
    
class FastTextUCNameDescFlowFileLevelIdentifierWMDTLP(FastTextUCFileLevelIdentifierWMDTLP):
    
    def _fill_req_dict(self, req_dict, req_emb):
        if self._dataset.keys_with_extension():
            req_dict[req_emb.file_name] = [req_emb.vector.name_words + req_emb.vector.description_words + [word for group in req_emb.vector.flow_of_events_words for word in group]]
        else:
            req_dict[req_emb.file_name_without_extension] = [req_emb.vector.name_words + req_emb.vector.description_words + [word for group in req_emb.vector.flow_of_events_words for word in group]]
        return req_dict
    
    def output_prefix(self):
        return "ft_UC_namedescflow_filelevel_Identifier_wmd"
    
    
class FastTextCommentIdentifierSentenceWMDTLP(FastTextCodeElementLevelWMDTLP):
    """  WMD distance: Req as sentence list, Class as method with signature, comm, classname
        Calculate wmd distance between req sentence and method
        aggregate wmd method to all req sentences of a req with req_wmd_reduce_func
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = []
            else:
                req_dict[req_emb.file_name_without_extension] = []
            for req_sentence in req_emb.vector.grouped_token_list:
                if self._dataset.keys_with_extension():
                    req_dict[req_emb.file_name].append(req_sentence)
                else:
                    req_dict[req_emb.file_name_without_extension].append(req_sentence)
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for meth in cls.methods:
                    method_words = [] + cls.get_name_words() + meth.get_name_words() + meth.get_comment_tokens() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(method_words)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(method_words)
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos):
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            # Also using ital for code side (it is actual mixed with english identifiers and ital comments)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=True)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def _choose_req_words(self, req_emb):
        return [sentence_words for sentence_words in req_emb.vector.grouped_token_list]
    
    def _choose_method_words(self, meth):
        return meth.get_name_words() + meth.get_param_plain_list() + meth.get_returntype_words() + meth.get_comment_tokens()
    
    def output_prefix(self):
        return "ft_comm_Identifier_sentence_wmd"
    
class FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP(FastTextCommentIdentifierSentenceWMDTLP):
    def cls_name_voter(self, m_dict):
        return not m_dict
        
    def output_prefix(self):
        return "ft_comm_Identifier_sentence_classname_voter_optional_wmd"
    
class FastTextUCNameDescFlowCommentIdentifierSentenceWMDTLP(FastTextCommentIdentifierSentenceWMDTLP):
    
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words, [word for group in req_emb.vector.flow_of_events_words for word in group]] 
    
    def output_prefix(self):
        return "ft_uc_name_desc_flow_comm_identifier_sentence_wmd"
    
class FastTextUCNameDescFlowCommentIdentifierSentenceSpecificNoClassNameVoterWMDTLP(FastTextCommentIdentifierSentenceWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]
    
    def output_prefix(self):
        return "ft_uc_name_desc_flow_comm_identifier_sentence_specific_no_classname_voter_wmd"
    
    def cls_name_voter(self, m_dict):
        return False
    
class FastTextUCNameDescFlowCommentIdentifierSentenceSpeecificWMDTLP(FastTextUCNameDescFlowCommentIdentifierSentenceWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]
    def output_prefix(self):
        return "ft_uc_name_desc_flow_comm_identifier_sentencespecific_wmd"
    
class FastTextUCNameDescFlowCommentIdentifierSentenceClassNameVoterOptionalWMDTLP(FastTextUCNameDescFlowCommentIdentifierSentenceWMDTLP):
    def output_prefix(self):
        return "ft_UC_namedescflow_comm_identifier_sentence_classname_voter_optional_wmd"
    def cls_name_voter(self, m_dict):
        return not m_dict
    
class FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP(FastTextUCNameDescFlowCommentIdentifierSentenceClassNameVoterOptionalWMDTLP):
    def _choose_req_words(self, req_emb):
        return [req_emb.vector.name_words, req_emb.vector.description_words] + [sentence for sentence in req_emb.vector.flow_of_events_words]

    def output_prefix(self):
        return "ft_UC_namedescflow_comm_identifier_sentencespecific_classname_voter_optional_wmd"
    
    
class FastTextCommentIdentifierWMDTLP(FastTextCodeElementLevelWMDTLP):
    """  WMD distance: Req as word list, Class as method with signature, comm, classname
        Calculate wmd distance between req and method
        majority decision
    """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, code_reduce_func, rule_applier): 
        #req reduce func has no effect here
        return super(FastTextCommentIdentifierWMDTLP, cls).create(dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, max, code_reduce_func, rule_applier)
    
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = [req_emb.vector.token_list]
            else:
                req_dict[req_emb.file_name_without_extension] = [req_emb.vector.token_list]
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for meth in cls.methods:
                    method_words = [] + cls.get_name_words() + meth.get_name_words() + meth.get_comment_tokens() + meth.get_param_plain_list() + meth.get_returntype_words()
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(method_words)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(method_words)
        wmd_func = self._word_emb_creator.word_movers_distance
        if isinstance(self._dataset, Smos):
            assert isinstance(self._word_emb_creator, FastTextAlignedEngItalEmbeddingCreator)
            # Also using ital for code side (it is actual mixed with english identifiers and ital comments)
            wmd_func = partial(self._word_emb_creator.word_movers_distance, ital1=True, ital2=True)
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            wmd_func, 
            output_precalculated_filename,
             WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
        
    def output_prefix(self):
        return "ft_comm_Identifier_wmd"
    
class FastTextCommentLevelWMDTLP(FastTextCodeElementLevelWMDTLP):
    """ WMD distance: Req as word list, Class as list  of comment word lists
        Compare req with each comment
      """
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, None, WordTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MockEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR)
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, code_reduce_func, rule_applier): 
        #req reduce func has no effect here
        return super(FastTextCommentLevelWMDTLP, cls).create(dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, max, code_reduce_func, rule_applier)
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None, output_name_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(output_name_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        assert isinstance(req_embeddings[0], MockEmbedding)
        assert isinstance(code_embeddings[0], MockEmbedding)
        req_dict = dict()
        for req_emb in req_embeddings:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = [req_emb.vector.token_list]
            else:
                req_dict[req_emb.file_name_without_extension] = [req_emb.vector.token_list]
                
        code_dict = dict()
        for code_emb in code_embeddings:
            if self._dataset.keys_with_extension():
                code_dict[code_emb.file_name] = []
            else:
                code_dict[code_emb.file_name_without_extension] = []
            for cls in code_emb.vector.classifiers:
                for comm in cls.get_all_comment_tokens():
                    if self._dataset.keys_with_extension():
                        code_dict[code_emb.file_name].append(comm)
                    else:
                        code_dict[code_emb.file_name_without_extension].append(comm)
        
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict,
            self._word_emb_creator.word_movers_distance, 
            output_precalculated_filename,
            WMD_VALUE_MAP_FUNC)
        self.load_from_precalculated(output_precalculated_filename)
    
    def output_prefix(self):
        return "ft_commentlevel_wmd"
    
