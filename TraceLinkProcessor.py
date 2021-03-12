import abc, logging
from Paths import *
from Preprocessing.Preprocessor import JavaCodeStopWordRemover, StopWordRemover,\
 CamelCaseSplitter, LowerCaseTransformer, NonLetterFilter, WordLengthFilter,\
    Separator, UrlRemover, Lemmatizer, DuplicateWhiteSpaceFilter, AddFullStop, JavaDocFilter
from CodeEmbeddingCreator.CodeEmbeddingCreator import *
from WordEmbeddingCreator.WordEmbeddingCreator import FastTextEmbeddingCreator, \
    BertSentenceEmbeddingCreator
from RequirementEmbeddingCreator.RequirementEmbeddingCreator import AverageWordEmbeddingCreator, AverageBERTSentenceEmbeddingCreator
import Evaluator
from Embedding import RequirementEmbedding,\
    MethodCallGraphEmbedding, Embedding, MethodCallGraphEmbeddingMultipleSims
from TraceLink import normalize_value_range
from DataAdapter import EmbeddingsDataAdapter, \
    PrecalculatedTracePairProcessor,\
    EmbeddingsProcessor, DualPrecalculatedTracePairProcessor,\
    PrecalculatedEmbeddingsProcessor
from BertPredictor import BertPredictor
from EmbeddingCreator import MockEmbeddingCreator
from TracePairPrecalculator import TracePairPrecalculator
from CodeEmbeddingCreator.MethodCallGraphEmbeddingCreator import MethodSignatureCallGraphEmbeddingCreator
import FileUtil
from TraceLinkCreator import TopNTraceLinkCreator, CombinationTLC, CallGraphTLC,\
    FileLevelTraceLinkCreator
from EvalMatrix import EvalMatrix
from Dataset import Dataset
log = logging.getLogger(__name__)

DEFAULT_REQ_PREPROCESSOR = Preprocessor([UrlRemover(), Separator(), NonLetterFilter(), 
        CamelCaseSplitter(), LowerCaseTransformer(), Lemmatizer(), StopWordRemover(), WordLengthFilter(2)])

DEFAULT_CODE_PREPROCESSOR = Preprocessor([UrlRemover(), Separator(), NonLetterFilter(), 
        CamelCaseSplitter(), JavaCodeStopWordRemover(), LowerCaseTransformer(), Lemmatizer(), 
        StopWordRemover(), WordLengthFilter(2)])

SAVE_TRACE_LINKS = False

class TraceLinkProcessor(abc.ABC):
    def __init__(self, dataset, word_emb_creator, trace_link_creator, run_config, rule_applier):
        self._dataset = dataset
        self._word_emb_creator = word_emb_creator # needed for wmd_function
        self._trace_link_creator = trace_link_creator
        self._run_config = run_config
        self._rule_applier = rule_applier
        self._other_constructor_init()
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, req_reduce_func, code_reduce_func, rule_applier): 
        run_config = RunConfiguration(dataset, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, req_reduce_func, code_reduce_func, cls.is_reverse_compare(), isinstance(trace_link_creator, TopNTraceLinkCreator))
        return cls(dataset, word_emb_creator, trace_link_creator, run_config, rule_applier)
    
    def change_thresholds(self, new_elem_threshs, new_maj_threshs, new_file_threshs):
        self._run_config = RunConfiguration(self._dataset, new_elem_threshs, new_maj_threshs, new_file_threshs,
                                            self._run_config.normalize, self._run_config.req_reduce_func, self._run_config.code_reduce_func,
                                             self._run_config.reverse_compare, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        
    def _other_constructor_init(self):
        """
        Other initializations in subclasses
        """
        pass
    
    @classmethod
    def is_reverse_compare(cls):
        return False
    
    def _init_trace_link_creator(self):
        self._trace_link_creator.data_adapter = self._get_data_adapter()
        self._trace_link_creator.req_reduce_func = self._run_config.req_reduce_func
        self._trace_link_creator.code_reduce_func = self._run_config.code_reduce_func
        self._trace_link_creator.reverse_compare = self._run_config.reverse_compare
        self._other_trace_link_init()
    
    @abc.abstractmethod
    def _get_data_adapter(self):
        pass
    
    @abc.abstractmethod
    def reload_with_dataset(self, dataset):
        pass
    def _other_trace_link_init(self):
        """
        Other initializations in subclasses
        """
        pass
    
    def default_req_emb_creator(self, word_emb_creator):
        log.error("default_req_emb_creator for {} not supported".format(self.__class__.__name))
        
    def default_code_emb_creator(self, word_emb_creator):
        log.error("default_code_emb_creator for {} not supported".format(self.__class__.__name))
    
    def run(self):
        self._init_trace_link_creator()
        eval_result_matrix = EvalMatrix(self._run_config.elem_thresholds, self._run_config.majority_thresholds, self._run_config.file_level_thresholds,
                                               self._dataset.solution_matrix()._number_of_trace_links)
        for elem_thresh in self._run_config.elem_thresholds:
            for maj_thresh in self._run_config.majority_thresholds:
                # Skip eval if elem_thresh is more similar ("bigger") than maj_thresh. Dont Skip when doing TopN
                if isinstance(self._trace_link_creator, TopNTraceLinkCreator) or not self._run_config.comp_func(elem_thresh, maj_thresh):
                    for thresh in self._run_config.file_level_thresholds:
                        # Skip eval if elem_thresh is more similar ("bigger") than maj_thresh. Dont Skip when doing TopN or when normalizing value range
                        if isinstance(self._trace_link_creator, TopNTraceLinkCreator) or not self._run_config.comp_func(maj_thresh, thresh) or self._run_config.normalize:
                            trace_links = self._trace_link_creator.create_tracelinks(elem_thresh, maj_thresh)
                            
                            if self._run_config.normalize:
                                trace_links = normalize_value_range(trace_links)
                            if SAVE_TRACE_LINKS:
                                all_trace_pairs = []
                                req_names = set()
                                code_names = set()
                                for candidate in trace_links:
                                    for link in candidate.get_all_candidates():
                                        req_names.add(link.get_req_key())
                                        code_names.add(link.get_code_key())
                                        all_trace_pairs.append((link.get_req_key(), link.get_code_key(), link.similarity))
                            
                                df = pandas.DataFrame(None, index=req_names, columns=code_names)
                                for pair in all_trace_pairs:
                                    df.at[pair[0], pair[1]] = pair[2]
                                FileUtil.write_dataframe_to_csv(df, precalculated_all_filelevel_sims_csv_filename(self._dataset, self.__class__.__name__))
                            trace_links = self._flatten_trace_link_list(trace_links)
                            trace_links = self._apply_file_level_threshold(trace_links, thresh)
                            if self._rule_applier:
                                trace_links = self._rule_applier.apply(trace_links)
                            valid_trace_links = self._evaluate_tracelinks(trace_links)
                            eval_result_matrix.add_eval_result(elem_thresh, maj_thresh, thresh, valid_trace_links, trace_links)
                        else:
                            eval_result_matrix.add_eval_result(elem_thresh, maj_thresh, thresh, [], [])
                            
        return eval_result_matrix    
        
    def _apply_file_level_threshold(self, trace_links, drop_thresh):
        if self.is_reverse_compare():
            return [trace_link for trace_link in trace_links if trace_link.similarity <= drop_thresh]
        else:
            return [trace_link for trace_link in trace_links if trace_link.similarity > drop_thresh]
    
    def _flatten_trace_link_list(self, trace_links):
        return [trace_link for trace_candidate in trace_links for trace_link in trace_candidate.get_all_candidates()]
        
    def _create_req_embeddings(self, req_embedding_creator):
        req_dir = self._dataset.req_folder()
        req_output_file = req_emb_output_file(self._dataset, req_embedding_creator.__class__.__name__)
        return req_embedding_creator.create_all_embeddings(req_dir, req_output_file)
        
    def _create_code_embeddings(self, code_embedding_creator):
        code_dir = self._dataset.code_folder()
        code_output_file = code_emb_output_file(self._dataset, code_embedding_creator.__class__.__name__)
        return code_embedding_creator.create_all_embeddings(code_dir, code_output_file)
        
    def _evaluate_tracelinks(self, trace_link_candidates):
        return Evaluator.evaluate(trace_link_candidates, self._dataset.solution_matrix(), self._dataset.keys_with_extension())
    
    @abc.abstractmethod
    def output_prefix(self):
        pass
    
class FastTextFileLevelTLP(TraceLinkProcessor, EmbeddingsProcessor):
    
    def _other_constructor_init(self):
        assert isinstance(self._trace_link_creator, FileLevelTraceLinkCreator), "FastTextFileLevelTLP needs a (subclass of) FileLevelTraceLinkCreator"
        EmbeddingsProcessor.__init__(self)
        self._req_emb_creator = None #Need these two variables to permit reloading dataset without changing the current emb_creators
        self._code_emb_creator = None
        
    def _get_data_adapter(self):
        return self._data_adapter
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, file_level_drop_thresholds, normalize, rule_applier): 
        # elem thresh, maj thresh, req and code req func have no effect here
        return super(FastTextFileLevelTLP, cls).create(dataset, word_emb_creator, trace_link_creator, [0], [0], file_level_drop_thresholds,
                                            normalize, None, None, rule_applier)
    
    def load_from_embeddings(self, req_embedding_creator, code_embedding_creator, dataset=None):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        self._req_emb_creator = req_embedding_creator
        self._code_emb_creator = code_embedding_creator
        if dataset:
            self._dataset = dataset
        self._data_adapter =  EmbeddingsDataAdapter(self._create_req_embeddings(req_embedding_creator),
                                         self._create_code_embeddings(code_embedding_creator))
    
    def reload_with_dataset(self, dataset):
        self._dataset = dataset
        self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        self._data_adapter =  EmbeddingsDataAdapter(self._create_req_embeddings(self._req_emb_creator),
                                         self._create_code_embeddings(self._code_emb_creator))
        
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return AverageWordEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, word_emb_creator)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return IdentifierEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, word_emb_creator)
    
    def output_prefix(self):
        return type(self._req_emb_creator).__name__ + "_" + type(self._code_emb_creator).__name__
    
class FastTextWordCosSimTLP(TraceLinkProcessor, PrecalculatedTracePairProcessor):
    
    def _other_constructor_init(self):
        PrecalculatedTracePairProcessor.__init__(self)
        self._req_emb_creator_name = None
        self._code_emb_creator_name = None # Need this attribute to permit dataset reloading without changing the code_emb_creator
        
    def _get_data_adapter(self):
        return self._data_adapter
    
    def build_precalculated_name_and_load(self, req_emb_creator_name, code_emb_creator_name, dataset = None):
        self._req_emb_creator_name = req_emb_creator_name
        self._code_emb_creator_name = code_emb_creator_name
        self.reload_with_dataset(dataset)
    
    def reload_with_dataset(self, dataset):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        precalculated_filename = self.default_precalculated_filename(self._dataset, self._req_emb_creator_name, self._code_emb_creator_name)
        self.load_from_precalculated(precalculated_filename)
        
        
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_filename:
            output_precalculated_filename = self.default_precalculated_filename(self._dataset, req_embedding_creator.__class__.__name__,
                                                                                 code_embedding_creator.__class__.__name__)
        
        req_list = self._create_req_embeddings(req_embedding_creator) # List of all req embeddings
        code_list = self._create_code_embeddings(code_embedding_creator) # List of all code embeddings
        if not code_list:
            log.info("No code embeddings for {} with {}, skip.".format(self._dataset.name(), code_embedding_creator.__class__.__name__))
            return
        assert isinstance(req_list[0], RequirementEmbedding)
        assert isinstance(code_list[0], CodeEmbedding)
        
        # convert embedding list into dictionary form (needed input format for TracePairPrecalculator)
        req_dict = dict()
        for req_emb in req_list:
            if self._dataset.keys_with_extension():
                req_dict[req_emb.file_name] = [req_emb.vector]
            else:
                req_dict[req_emb.file_name_without_extension] = [req_emb.vector]
                
        code_dict = dict()
        for code_emb in code_list:
            if code_emb.sub_vectors:
                if self._dataset.keys_with_extension():
                    code_dict[code_emb.file_name] = code_emb.sub_vectors
                else:
                    code_dict[code_emb.file_name_without_extension] = code_emb.sub_vectors
        
        # precalculates all req/code embedding combinations with cos sim and writes it to output_precalculated_filename
        TracePairPrecalculator().calculate_trace_pairs(req_dict, code_dict, Util.calculate_cos_sim, output_precalculated_filename)
        
        super(FastTextWordCosSimTLP, self).load_from_precalculated(output_precalculated_filename)
    
    def default_precalculated_filename(self, dataset: Dataset, req_emb_creator_name: str, code_emb_creator_name: str):        
        return precalculated_json_filename(dataset, code_emb_creator_name, req_emb_creator_name + "_" + code_emb_creator_name)
    
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return AverageWordEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, word_emb_creator)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return IdentifierEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, word_emb_creator)
    
    def output_prefix(self):
        return self._req_emb_creator_name + "_" + self._code_emb_creator_name

class BertSelfTrainedTraceLinkProcessor(TraceLinkProcessor, PrecalculatedTracePairProcessor):
    """
    Majority decision with self trained Bert models
    """
    
    def _other_constructor_init(self):
        PrecalculatedTracePairProcessor.__init__(self)
        self._trace_link_type = None
        self._percent = None
        
    def _get_data_adapter(self):
        return self._data_adapter
    
    @classmethod
    def create(cls, dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds,
                                            normalize, req_reduce_func, code_reduce_func, trace_link_type, percent, rule_applier):
        instance = super(BertSelfTrainedTraceLinkProcessor, cls).create(dataset, word_emb_creator, trace_link_creator, elem_drop_thresholds, majority_drop_threshs, file_level_drop_thresholds, normalize, req_reduce_func, code_reduce_func, rule_applier)
        instance._trace_link_type = trace_link_type
        instance._percent = percent
        return instance
    
    def build_precalculated_name_and_load(self, percent=None, trace_link_type=None, dataset=None):
        if percent:
            self._percent = percent
        if trace_link_type:
            self._trace_link_type = trace_link_type
        
        self.reload_with_dataset(dataset)
        
    def reload_with_dataset(self, dataset):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        self._set_remaining_solution_matrix()
        precalculated_filename = self._default_precalculated_filename()
        self.load_from_precalculated(precalculated_filename)
        
    def _set_remaining_solution_matrix(self):
        """
        Since the data for self trained bert models are split into train:test we don't use the complete solution matrix
        We only need the remaining solution links that are contained in the test set
        """
        self._dataset._solution_matrix = FileUtil.read_txt_format_solution_matrix(remaining_trace_matrix_filename(self._percent, self._dataset, self._trace_link_type))
    
    def _default_precalculated_filename(self):        
        return bert_trace_pair_json_filename(self._percent, self._dataset, self._trace_link_type)
    
    def output_prefix(self):
        return self._trace_link_type.name
  
    def precalculate_tracelinks(self, output_precalculated_filename=None, req_embedding_creator=None, code_embedding_creator=None):
        if req_embedding_creator:
            log.info("req_embedding_creator for BertSelfTrainedTraceLinkProcessor not needed")
        if code_embedding_creator:
            log.info("code_embedding_creator for BertSelfTrainedTraceLinkProcessor not needed")
        if not output_precalculated_filename:
            output_precalculated_filename = self._default_precalculated_filename()
        predictor = self._word_emb_creator
        if not predictor:
            predictor = BertPredictor(bert_predictor_path(self._run_config.trace_link_type))
        req_csv = req_csv_filename(self._run_config.percent, self._dataset, self._run_config.trace_link_type)
        code_csv = code_csv_filename(self._run_config.percent, self._dataset, self._run_config.trace_link_type)
        
        # convert csv list into dictionary form (needed input format for TracePairPrecalculator)
        req_dict = Util.get_grouped_dict_list(FileUtil.read_csv_to_dataframe_with_header(req_csv, REQ_FILE_CSV_HEADER), REQ_FILE_COLUMN_NAME, REQ_COLUMN_NAME)
        code_dict = Util.get_grouped_dict_list(FileUtil.read_csv_to_dataframe_with_header(code_csv, CODE_FILE_CSV_HEADER), CODE_FILE_COLUMN_NAME, CODE_COLUMN_NAME)
        log.info("Precalculating ....")
        TracePairPrecalculator().precalculate_trace_pairs(req_dict, code_dict, predictor.calculate_trace_link_probability,
                                                     output_precalculated_filename)
        log.info("... Done")
        self.load_from_precalculated(output_precalculated_filename)
        
class BertCombinedSelfTrainedTLP(TraceLinkProcessor, DualPrecalculatedTracePairProcessor):
    """
    Combines two types of trace links, e.g. req-sentence <> code_identifer and req_sentence <> code_comment
    the req source have to be the same for both link types
    """
    def _other_constructor_init(self):
        DualPrecalculatedTracePairProcessor.__init__(self)
        assert isinstance(self._trace_link_creator, CombinationTLC), "BertCombinedSelfTrainedTLP requires a (subclass of) CombinationTLC as TracelinkProcessor"
        self._trace_link_type_1 = None
        self._trace_link_type_2 = None
        self._percent = None
    
    def build_precalculated_name_and_load(self, trace_link_type_1, trace_link_type_2, percent, dataset):
        
        if percent:
            self._percent = percent
        if trace_link_type_1:
            self._trace_link_type_1 = trace_link_type_1
        if trace_link_type_2:
            self._trace_link_type_2 = trace_link_type_2
        self.reload_with_dataset(dataset)
    
    def reload_with_dataset(self, dataset):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        self._set_remaining_solution_matrix()
        precalculated_filename = self._default_precalculated_filename()
        precalculated_filename_2 = self._default_precalculated_filename_2()
        self.load_from_precalculated(precalculated_filename, precalculated_filename_2)
        
    def _other_trace_link_init(self):
        self._trace_link_creator.data_adapter_2 = self._data_adapter_2
        
    def _get_data_adapter(self):
        return self._data_adapter
    
    def _set_remaining_solution_matrix(self):
        """
        Since the data for self trained bert models are split into train:test we don't use the complete solution matrix
        We only need the remaining solution links that are contained in the test set
        """
        self._dataset._solution_matrix = FileUtil.read_txt_format_solution_matrix(remaining_trace_matrix_filename(self._percent, self._dataset, self._trace_link_type_1))
            
    def _default_precalculated_filename(self):        
        return bert_trace_pair_json_filename(self._percent, self._dataset, self._trace_link_type_1)
    
    def _default_precalculated_filename_2(self):        
        return bert_trace_pair_json_filename(self._percent, self._dataset, self._trace_link_type_2)

    def output_prefix(self):
        return self._trace_link_type_1.name + "_and_" + self._trace_link_type_2.name
    
    def precalculate_tracelinks(self, output_precalculated_filename, req_embedding_creator=None, code_embedding_creator=None):
        log.error("Please use BertSelfTrainedTLP.precalculate_tracelinks to precalculate the files separately")
    
class BertModelTraceLinkProcessor(FastTextFileLevelTLP):
    """
    TraceLinkProcessor to use with existing bert model on file level
    """
    DEFAULT_REQ_PREPROCESSOR = Preprocessor([UrlRemover(), Separator(True), CamelCaseSplitter(True), NonLetterFilter(), DuplicateWhiteSpaceFilter(), AddFullStop()])
    DEFAULT_CODE_PREPROCESSOR = Preprocessor([JavaDocFilter(), Separator(True), CamelCaseSplitter(True), NonLetterFilter(), DuplicateWhiteSpaceFilter()])
       
    def output_prefix(self):
        return "bertmodel_identifier"
    
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = BertSentenceEmbeddingCreator()
        return AverageBERTSentenceEmbeddingCreator(BertModelTraceLinkProcessor.DEFAULT_REQ_PREPROCESSOR, word_emb_creator)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = BertSentenceEmbeddingCreator()
        return MethodNameSentenceEmbeddingCreator(BertModelTraceLinkProcessor.DEFAULT_CODE_PREPROCESSOR, word_emb_creator)
    
class FastTextWordCosSimTLP2(TraceLinkProcessor, PrecalculatedEmbeddingsProcessor):
    DEFAULT_REQ_EMB_CREATOR_NAME = "UCAverageWordEmbeddingCreator"
    DEFAULT_CODE_EMB_CREATOR_NAME = "IdentifierEmbeddingCreator"
    
    def _other_constructor_init(self):
        PrecalculatedEmbeddingsProcessor.__init__(self)
        #assert isinstance(self._trace_link_creator, CallGraphTLC)
        self._req_emb_creator_name = None
        self._code_emb_creator_name = None
        
    def default_req_emb_creator(self, word_emb_creator):
        """
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return AverageWordEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, word_emb_creator)"""
    
    def default_code_emb_creator(self, word_emb_creator):
        """
        if not word_emb_creator:
            word_emb_creator = FastTextEmbeddingCreator()
        return MethodSignatureCallGraphEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, word_emb_creator)"""
    
    def _get_data_adapter(self):
        return self._data_adapter
    
    """
    def _other_trace_link_init(self):
        self._trace_link_creator.method_call_graph_dict = self._dataset.method_callgraph()"""
        
    def precalculate_tracelinks(self, output_precalculated_req_filename, output_precalculated_code_filename, req_embedding_creator, code_embedding_creator):
        """
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)"""
        if not output_precalculated_req_filename:
            output_precalculated_req_filename = self.default_precalculated_filename(req_embedding_creator.__class__.__name__)
        if not output_precalculated_code_filename:
            output_precalculated_code_filename = self.default_precalculated_filename(code_embedding_creator.__class__.__name__)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        
      
        FileUtil.write_dict_to_json(output_precalculated_req_filename, [req_emb.to_json() for req_emb in req_embeddings])
        FileUtil.write_dict_to_json(output_precalculated_code_filename, [code_emb.to_json() for code_emb in code_embeddings])
        
        self.build_precalculated_name_and_load(req_embedding_creator.__class__.__name__, code_embedding_creator.__class__.__name__)
        
    def default_precalculated_filename(self, emb_creator_name):
        return precalculated_vectors_json_filename(self._dataset, emb_creator_name)
    
    def load_from_precalculated(self, precalculated_req_filename, precalculated_code_filename):
        req_json = FileUtil.read_dict_from_json(precalculated_req_filename)
        code_json = FileUtil.read_dict_from_json(precalculated_code_filename)
        req_embeddings = [Embedding.from_json(req_dict) for req_dict in req_json]
        code_embeddings = [Embedding.from_json(code_dict) for code_dict in code_json]
        self._data_adapter = EmbeddingsDataAdapter(req_embeddings, code_embeddings)
        
    def build_precalculated_name_and_load(self, req_emb_creator_name="", code_emb_creator_name="", dataset=None):
        """
        req_emb_creator_name = class name of the req_emb_creator
        code_emb_creator_name = class name of the code_emb_creator
        """
        if not req_emb_creator_name:
            req_emb_creator_name = self.DEFAULT_REQ_EMB_CREATOR_NAME
        if not code_emb_creator_name:
            code_emb_creator_name = self.DEFAULT_CODE_EMB_CREATOR_NAME
        self._req_emb_creator_name = req_emb_creator_name
        self._code_emb_creator_name = code_emb_creator_name
        self.reload_with_dataset(dataset)
    
    def reload_with_dataset(self, dataset):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        precalculated_req_filename = self.default_precalculated_filename(self._req_emb_creator_name)
        precalculated_code_filename = self.default_precalculated_filename(self._code_emb_creator_name)
        self.load_from_precalculated(precalculated_req_filename, precalculated_code_filename)
        
    def output_prefix(self):
        return self._req_emb_creator_name + "_" + self._code_emb_creator_name
    
class MethodCallGraphTLP(TraceLinkProcessor, PrecalculatedEmbeddingsProcessor):
    DEFAULT_REQ_EMB_CREATOR_NAME = "AverageWordEmbeddingCreator"
    DEFAULT_CODE_EMB_CREATOR_NAME = "MethodSignatureCallGraphEmbeddingCreator"
    
    def _other_constructor_init(self):
        PrecalculatedEmbeddingsProcessor.__init__(self)
        assert isinstance(self._trace_link_creator, CallGraphTLC)
        self._req_emb_creator_name = None
        self._code_emb_creator_name = None
        
    def default_req_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = BertSentenceEmbeddingCreator()
        return AverageWordEmbeddingCreator(DEFAULT_REQ_PREPROCESSOR, word_emb_creator)
    
    def default_code_emb_creator(self, word_emb_creator):
        if not word_emb_creator:
            word_emb_creator = BertSentenceEmbeddingCreator()
        return MethodSignatureCallGraphEmbeddingCreator(DEFAULT_CODE_PREPROCESSOR, word_emb_creator)
    
    def _get_data_adapter(self):
        return self._data_adapter
    
    def _other_trace_link_init(self):
        self._trace_link_creator.method_call_graph_dict = self._dataset.method_callgraph()
        
    def precalculate_tracelinks(self, output_precalculated_req_filename, output_precalculated_code_filename, req_embedding_creator=None, code_embedding_creator=None, output_suffix=""):
        if not req_embedding_creator:
            req_embedding_creator = self.default_req_emb_creator(self._word_emb_creator)
        if not code_embedding_creator:
            code_embedding_creator = self.default_code_emb_creator(self._word_emb_creator)
        if not output_precalculated_req_filename:
            output_precalculated_req_filename = self.default_precalculated_filename(req_embedding_creator.__class__.__name__, output_suffix)
        if not output_precalculated_code_filename:
            output_precalculated_code_filename = self.default_precalculated_filename(code_embedding_creator.__class__.__name__, output_suffix)
            
        req_embeddings = self._create_req_embeddings(req_embedding_creator)
        code_embeddings = self._create_code_embeddings(code_embedding_creator)
        
        for cg_emb in code_embeddings: 
            assert isinstance(cg_emb, MethodCallGraphEmbeddingMultipleSims)
            for method_name_key in cg_emb.methods_dict:
                for req_file in req_embeddings: 
                    assert isinstance(req_file, RequirementEmbedding)
                    req_parts = self._choose_req_part(req_file) # choose if using partial vectors or whole vector
                    sims_of_all_parts = [Util.calculate_cos_sim(req_vector, cg_emb.get_method_vector(method_name_key)) for req_vector in req_parts]
                    cg_emb.add_method_sim(method_name_key, sims_of_all_parts, req_file.file_name)
            for other_key in cg_emb.non_cg_dict:
                for req_file in req_embeddings: 
                    assert isinstance(req_file, RequirementEmbedding)
                    req_parts = self._choose_req_part(req_file) # choose if using partial vectors or whole vector
                    sims_of_all_parts = [Util.calculate_cos_sim(req_vector, cg_emb.get_non_cg_vector(other_key)) for req_vector in req_parts]
                    cg_emb.add_non_cg_sim(other_key, sims_of_all_parts, req_file.file_name)
        
        FileUtil.write_dict_to_json(output_precalculated_req_filename, [req_emb.to_json() for req_emb in req_embeddings])
        FileUtil.write_dict_to_json(output_precalculated_code_filename, [code_emb.to_json() for code_emb in code_embeddings])
        
        ######self.build_precalculated_name_and_load(req_embedding_creator.__class__.__name__, code_embedding_creator.__class__.__name__)
        
    def _choose_req_part(self, req_file):
        return req_file.sub_vectors
    
    def default_precalculated_filename(self, emb_creator_name, output_name_suffix=""):
        return precalculated_json_filename(self._dataset, emb_creator_name, emb_creator_name + output_name_suffix)
    
    def load_from_precalculated(self, precalculated_req_filename, precalculated_code_filename):
        req_json = FileUtil.read_dict_from_json(precalculated_req_filename)
        code_json = FileUtil.read_dict_from_json(precalculated_code_filename)
        req_embeddings = [Embedding.from_json(req_dict) for req_dict in req_json]
        code_embeddings = [MethodCallGraphEmbedding.from_json(code_dict) for code_dict in code_json]
        self._data_adapter = EmbeddingsDataAdapter(req_embeddings, code_embeddings)
        
    def build_precalculated_name_and_load(self, req_emb_creator_name="", code_emb_creator_name="", dataset=None):
        """
        req_emb_creator_name = class name of the req_emb_creator
        code_emb_creator_name = class name of the code_emb_creator
        """
        if not req_emb_creator_name:
            req_emb_creator_name = self.DEFAULT_REQ_EMB_CREATOR_NAME
        if not code_emb_creator_name:
            code_emb_creator_name = self.DEFAULT_CODE_EMB_CREATOR_NAME
        self._req_emb_creator_name = req_emb_creator_name
        self._code_emb_creator_name = code_emb_creator_name
        self.reload_with_dataset(dataset)
    
    def reload_with_dataset(self, dataset):
        if dataset:
            self._dataset = dataset
            self._run_config.reload_dataset(dataset, isinstance(self._trace_link_creator, TopNTraceLinkCreator))
        precalculated_req_filename = self.default_precalculated_filename(self._req_emb_creator_name)
        precalculated_code_filename = self.default_precalculated_filename(self._code_emb_creator_name)
        self.load_from_precalculated(precalculated_req_filename, precalculated_code_filename)
        
    def output_prefix(self):
        return type(self._trace_link_creator).__name__ + "." + self._code_emb_creator_name + "." + self._trace_link_creator.neighbor_strategy.name + "."+ str(self._trace_link_creator.method_weight)
    
class MethodCallGraphTLPWholeReq(MethodCallGraphTLP):
    def _choose_req_part(self, req_file):
        return [req_file.vector]
    
class RunConfiguration:
    FILE_THRESH_TEXT = "file_level_drop_thresh: "
    MAJ_THRESH_TEXT = "majority_drop_thresh: "
    TOPN_TEXT = "top_n: "
    ELEM_THRESH_TEXT = "elem_level_drop_thresh: "
    
    def __init__(self, dataset, elem_threshs, maj_threshs, file_threshs, normalize, req_reduce_func, code_reduce_func, reverse_compare, 
                 is_top_n=False):
        self.elem_thresholds = elem_threshs
        self.original_maj_threshs = maj_threshs # Normal majority threshs or top n percentages that remain unchanged on reload with new dataset
        self.majority_thresholds = maj_threshs # Normal majority threshs or top n absolute values
        self.majority_print = dict((x, str(x)) for x in maj_threshs)
        self.majority_percentage_to_absolute = dict((x, x) for x in maj_threshs)
        self.file_thresh_text = self.FILE_THRESH_TEXT
        self.maj_thresh_text = self.MAJ_THRESH_TEXT
        self.elem_thresh_text = self.ELEM_THRESH_TEXT
        
        self.file_level_thresholds = file_threshs
        self.normalize = normalize
        self.req_reduce_func = req_reduce_func
        self.code_reduce_func = code_reduce_func
        self.reverse_compare = reverse_compare

        if is_top_n:
            self.reload_dataset(dataset, True) # Convert percent top n values to absolute values
        
    def comp_func(self, a, b):
        """
        True if a is more similar than b
        """
        return a < b if self.reverse_compare else a > b
    
    def reload_dataset(self, dataset, is_top_n = False):
        if is_top_n:
            self.majority_thresholds = [] 
            self.majority_print = {}
            self.majority_percentage_to_absolute = {}
            self.maj_thresh_text = self.TOPN_TEXT
            for top_n_percent in self.original_maj_threshs:
                top_n_absolute = Util.top_percent(dataset.num_reqs(), top_n_percent)
                if top_n_absolute in self.majority_thresholds: # two percentages map to the same absolute value
                    self.majority_print[top_n_absolute] = str(top_n_percent) + ", " + self.majority_print[top_n_absolute]
                else:
                    self.majority_thresholds += [top_n_absolute]
                    self.majority_print[top_n_absolute] = "{} ({})".format(top_n_percent, top_n_absolute)
                self.majority_percentage_to_absolute[top_n_percent] = top_n_absolute
            
