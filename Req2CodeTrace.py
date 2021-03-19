from Paths import *
import logging
import random


logging.basicConfig(level=logging.INFO, 
                    handlers=[logging.FileHandler("log_output.log", mode='w'), logging.StreamHandler()])


from Preprocessing.Preprocessor import Preprocessor, CamelCaseSplitter, WordLengthFilter, JavaCodeStopWordRemover, JavaDocFilter, \
Separator, LowerCaseTransformer, Lemmatizer
from Preprocessing.Tokenizer import SentenceTokenizer, UCTokenizer,\
    WordAndSentenceTokenizer, JavaDocDescriptionOnlyTokenizer
from TFIDFData import TFIDFCosSimPrecalculator
from Preprocessing.JaccardSimilarityCalculator import UCNameChooser,\
    CodeClassNameMethodSignatureChooser, UCNameDescChooser,\
    UCNameDescFlowChooser, RodriguezCodeChooser
from BertPredictor import BertPredictor
from CodeEmbeddingCreator.CodeEmbeddingCreator import *
import Evaluator
from nsga2.NSGA2Factory import StandardNSGA2Factory

from Preprocessing.CodeASTTokenizer import JavaCodeASTTokenizer, CCodeASTTokenizer
from RequirementEmbeddingCreator.RequirementEmbeddingCreator import AverageWordEmbeddingCreator, \
    AverageSentenceEmbeddingCreator, UCAverageWordEmbeddingCreator,\
    UCAverageWordEmbeddingCreatorWithNameDescFlow,\
    UCAverageWordEmbeddingCreatorWithNameDesc, UCTFIDFWordEmbeddingCreator,\
    UCTFIDFWordEmbeddingCreatorWithNameDesc,\
    UCTFIDFWordEmbeddingCreatorWithNameDescFlow
import TraceLink, numpy, Util
from WordEmbeddingCreator.WordEmbeddingCreator import FastTextEmbeddingCreator, \
    MockWordEmbeddingCreator, BertSentenceEmbeddingCreator, FastTextAlignedEngItalEmbeddingCreator, FineTunedFastTextEmbeddingCreator,\
    DEFAULT_FASTTEXT_MODEL_PATH
import pathlib, gensim
from TraceLinkProcessor import *
from FastTextWMDTLP import *
from TraceLinkCreator import FileLevelCosSimTraceLinkCreator,\
    SeparateMajorityCombinationTLC, UnionMajorityCombinationTLC,\
    ReturnAllMajorityCombinationTLC, CallGraphDoubleMajorityTLC, AllCallMajorityTLC,\
    WeightedSimilaritySumCallMajorityTLC, WeightedVectorSumCallMajorityTLC,\
    MajorityTraceLinkCreator, TopNTraceLinkCreator,\
    WeightedSimilaritySumCallElementLevelMajorityTLC
from CodeEmbeddingCreator.MethodCallGraphEmbeddingCreator import MethodSignatureCallGraphEmbeddingCreator,\
    MethodCommentSignatureCallGraphEmbeddingCreator
from Dataset import *
from EvalStrategy import WritePrecRecallF1Excel, TotalAveragePrecision,\
    SeparateAveragePrecision, BestCrossProjectConfig, WritePrecisionRecallCSV,\
    BestCrossProjectTechnique, SaveEvalResultMatrix, SaveValidTraceLinks,\
    SaveAllTraceLinks, MeanAveragePrecision, WriteMAPRecallCSV
from geneticAlgoritm.Req2CodeGeneticAlgorithm import Req2CodeGeneticAlgorithm,\
    Req2CodeGeneticAlgorithmWithDuplicates
from RuleApplier import RuleApplier, ExtendsRule, RelationDirection,\
    ImplementsRule, CallGraphRule

gensim.logger.setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, filename="log_output.txt", filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S',)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def run_fasttext_filelevel_cos_sim(dataset, eval_strategy, req_emb_creator, code_emb_creator, normalize=False, output_filename_suffix=""):
    """
    One req embedding per req, one class embedding per class, cos sim as metric, without call graphs
    req_emb_creator: Determines the way the req embedding is created
    code_emb_creator: Determines the way the code embedding is created (which class elements are involved?)
    
    The file level cos sim with fastText is the only technique that does not uses precalculated files.
    -> You have to set the WORD_EMB_CREATOR to an actual fastText model
    """
    log.info("\n#####  FastText file level cos sim on {}: \n######################################".format(dataset.name()))
    log.info(type(req_emb_creator).__name__ +  "/" + type(code_emb_creator).__name__ +  ": ")
    f = FastTextFileLevelTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize, None)
    f.load_from_embeddings(req_emb_creator, code_emb_creator)
    eval_strategy.set_trace_link_processor(f)
    eval_strategy.run(output_filename_suffix)
    
def run_all_fasttext_filelevel_cos_sim(dataset, eval_strategy, req_emb_creator, code_preprocessor, code_tokenizer, normalize=False, output_filename_suffix=""):
    """
    Runs all implemented cos sim file level mappings with all code element combinations without call graphs
    List of all code element combinations: see array MAJORITY_IDENTIFIEREMBEDDING_CLASSES
    
    The file level cos sim with fastText is the only technique that does not uses precalculated files.
    -> You have to set the WORD_EMB_CREATOR to an actual fastText model
    """
    log.info("\n#####  All FastText file level cos sim on {}: \n######################################".format(dataset.name()))
    tlp = FastTextFileLevelTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize)
    for creator in IDENTIFIEREMBEDDING_CLASSES:
        log.info(type(req_emb_creator).__name__ + "/" + creator.__name__ +  ": ")
        tlp.load_from_embeddings(req_emb_creator, creator(code_preprocessor, WORD_EMBD_CREATOR, tokenizer=code_tokenizer))
        eval_strategy.set_trace_link_processor(tlp)
        eval_strategy.run(output_filename_suffix)

def run_fasttext_majority(dataset, eval_strategy, req_emb_creator, code_emb_creator, req_reduce_func=max, code_reduc_func=max, finetuned=False, normalize=False, precalculate=False, output_filename_suffix=""):
    """
    Majority decision with cosine similarity, without call graphs
    
    req_reduce_func = requirement similarity reduction function for the majority decision. Use max or Util.create_averaged_vector
    code_reduc_func = code similarity reduction function for the majority decision. Use max or Util.create_averaged_vector
    Majority decision with cos sim
    precalculate=True: do precalculation
    precalculate=False: load precalculated file; precalculated file name is inferred from the name of the code embedding creator
    finetuned=True: it uses a finetuned model -> uses the finetuned precalculated filename
    output_filename_suffix: an optional suffix added to the output file to make results of multiple runs with the same code_emb_creator differentiable
    normalize=True: normalize value range to [0,1] before applying the last threshold (== file level threshold)
    """
    log.info("\n#####  FastText majority ({}) on {}: \n######################################".format(type(code_emb_creator).__name__, dataset.name()))
    f = FastTextWordCosSimTLP.create(dataset, WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS,
                                 normalize, req_reduce_func, code_reduc_func)
    if precalculate:
        precalculated_file = None
        if finetuned:
            precalculated_file = precalculated_finetuned_json_filename(dataset, type(code_emb_creator).__name__)
        f.precalculate_tracelinks(precalculated_file, req_emb_creator, code_emb_creator) # Using the default req_emb_creator if None
    if finetuned:
        precalculated_file = precalculated_finetuned_json_filename(dataset, type(req_emb_creator).__name__, type(code_emb_creator).__name__)
        f.load_from_precalculated(precalculated_file)
    else:
        f.build_precalculated_name_and_load(type(req_emb_creator).__name__, type(code_emb_creator).__name__, dataset)
    eval_strategy.set_trace_link_processor(f)
    eval_strategy.run(output_filename_suffix)
       
def run_fasttext_majority2(dataset, eval_strategy, req_emb_creator, code_emb_creator, req_reduce_func=max, code_reduc_func=max, normalize=False, precalculate=False, output_filename_suffix=""):
    """
    Majority decision with cosine similarity, without call graphs
    
    req_reduce_func = requirement similarity reduction function for the majority decision. Use max or Util.create_averaged_vector
    code_reduc_func = code similarity reduction function for the majority decision. Use max or Util.create_averaged_vector
    Majority decision with cos sim
    precalculate=True: do precalculation
    precalculate=False: load precalculated file; precalculated file name is inferred from the name of the code embedding creator
    finetuned=True: it uses a finetuned model -> uses the finetuned precalculated filename
    output_filename_suffix: an optional suffix added to the output file to make results of multiple runs with the same code_emb_creator differentiable
    normalize=True: normalize value range to [0,1] before applying the last threshold (== file level threshold)
    """
    log.info("\n#####  FastText majority ({}) on {}: \n######################################".format(type(code_emb_creator).__name__, dataset.name()))
    f = FastTextWordCosSimTLP2.create(dataset, WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS,
                                 normalize, req_reduce_func, code_reduc_func)
    if precalculate:
        f.precalculate_tracelinks(None, None, req_emb_creator, code_emb_creator) # None = Using default precalculated file names
    f.build_precalculated_name_and_load(type(req_emb_creator).__name__, type(code_emb_creator).__name__, dataset)
    eval_strategy.set_trace_link_processor(f)
    eval_strategy.run(output_filename_suffix)
                              
        
def run_all_fasttext_majority(dataset, eval_strategy, code_preprocessor, code_tokenizer, req_reduce_func=max, code_reduc_func=max, output_filename_suffix="", finetuned=False, normalize=False, precalculate=False):
    """
    Runs all implemented cos sim majority decision code element combinations, without call graphs
    List of all code element combinations: see array MAJORITY_IDENTIFIEREMBEDDING_CLASSES
    """
    
    log.info("\n#####  All FastText majority on {}: \n######################################".format(dataset.name()))
    f = FastTextWordCosSimTLP.create(dataset, WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS,
                                 normalize, req_reduce_func, code_reduc_func)
    
    for creator in MAJORITY_IDENTIFIEREMBEDDING_CLASSES:
        log.info(creator.__name__ +  ": ")
        if precalculate:
            precalculated_file = None
            if finetuned:
                precalculated_file = precalculated_finetuned_json_filename(dataset, creator.__name__)
            # Using the default req_emb_creator if None
            f.precalculate_tracelinks(precalculated_file, None, creator(code_preprocessor, WORD_EMBD_CREATOR, tokenizer=code_tokenizer)) 
        try:
            if finetuned:
                precalculated_file = precalculated_finetuned_json_filename(dataset, creator.__name__)
                f.load_from_precalculated(precalculated_file)
            else:
                f.build_precalculated_name_and_load(creator.__name__, dataset)
        except FileNotFoundError as f:
            # if the precalculated file could not be found. 
            # Can happen if file was not precalculated 
            # e.g. libest has no class comments -> No precalculated file if code_emb only includes class comments
            log.info("Skipping {}: {}".format(creator.__name__, f))
            continue
        
        eval_strategy.set_trace_link_processor(f)
        eval_strategy.run(output_filename_suffix)
            

def run_bertmodel_identifier_cos_sim(dataset, eval_strategy, normalize=False, output_filename_suffix=""):
    """
    runs the original bert model, not the self trained
    """
    log.info("\n#####  BertModel cos sim on {}: \n######################################".format(dataset.name()))
    tlp = BertModelTraceLinkProcessor.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator, DROP_THRESHOLDS, normalize)
    tlp.load_from_embeddings(None, None) # Using default emb creators if None
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
        
def run_fasttext_identifier_wmd(dataset, eval_strategy, output_filename_suffix="", normalize=True, precalculate=False):
    """
    WMD mapping, file level
    Req: Bag of Embeddings of its words
    Code: Bag of Embeddings of its class names and method signatures
    """
    log.info("\n#####  FastText Identifier WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize)
    _run_eval_strategy_wmd(tlp, eval_strategy, output_filename_suffix)
    
def run_fasttext_uc_name_identifier_wmd(dataset, eval_strategy, output_filename_suffix="", normalize=True, rule_applier=None):
    """
    WMD mapping, file level
    Req: Bag of Embeddings of its words
    Code: Bag of Embeddings of its class names and method signatures
    """
    log.info("\n#####  FastText UC Name Identifier WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextUCNameIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize, rule_applier)
    _run_eval_strategy_wmd(tlp, eval_strategy, output_filename_suffix)
    
def run_fasttext_uc_namedesc_identifier_wmd(dataset, eval_strategy, output_filename_suffix="", normalize=True):
    """
    WMD mapping, file level
    Req: Bag of Embeddings of its words
    Code: Bag of Embeddings of its class names and method signatures
    """
    log.info("\n#####  FastText UC Name Desc Identifier WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextUCNameDescIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize)
    _run_eval_strategy_wmd(tlp, eval_strategy, output_filename_suffix)
    
def run_fasttext_uc_namedescflow_identifier_wmd(dataset, eval_strategy, output_filename_suffix="", normalize=True):
    """
    WMD mapping, file level
    Req: Bag of Embeddings of its words
    Code: Bag of Embeddings of its class names and method signatures
    """
    log.info("\n#####  FastText UC Name Desc Flow Identifier WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextUCNameDescFlowIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize)
  
    _run_eval_strategy_wmd(tlp, eval_strategy, output_filename_suffix)

def _run_eval_strategy_wmd(tlp, eval_strategy, output_filename_suffix, precalculated_suffix=""):
    tlp.build_precalculated_name_and_load(output_suffix=precalculated_suffix)
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
    
def run_fasttext_comment_wmd(dataset, eval_strategy, output_filename_suffix="", normalize=True, precalculate=False):
    """
    WMD mapping, file level
    Req: Bag of Embeddings of its words
    Code: Bag of Embeddings of its class names and method signatures
    """
    log.info("\n#####  FastText Comment WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextCommentWMDTLP.create(dataset, WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, normalize)
    if precalculate:
        req_emb_creator = None # uses default (english/java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, IT_WORD_TOKENIZER)
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
    
def run_fasttext_sentence_level_identifier_wmd(dataset, eval_strategy, trace_link_creator, req_reduce_func, code_reduce_func,
                                                output_filename_suffix="", normalize=True, precalculate=False, rule_applier=None):
    log.info("\n#####  FastText Sentence level WMD on {}: \n######################################".format(dataset.name()))
    tlp = FastTextSentenceLevelIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, normalize, req_reduce_func, code_reduce_func, rule_applier)
    if precalculate:
        req_emb_creator = None # uses default (english/java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(True))
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)

def run_fasttext_comm_identifier_wmd(dataset, eval_strategy, trace_link_creator, code_reduce_func,
                                      output_filename_suffix="", normalize=True, precalculate=False):
    log.info("\n#####  FastText Comm identifier WMD ({}) on {}: \n######################################".format(type(trace_link_creator).__name__,dataset.name()))
    tlp = FastTextCommentIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, normalize, code_reduce_func)
    if precalculate:
        req_emb_creator = None # uses default (english(java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, WordTokenizer(True))
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
 
def run_fasttext_file_level_identifier_wmd(dataset, eval_strategy, trace_link_creator, code_reduce_func, 
                                                output_filename_suffix="", normalize=True, precalculate=False):
    log.info("\n#####  FastText File level identifier ({}) WMD on {}: \n######################################".format(type(trace_link_creator).__name__,dataset.name()))
    tlp = FastTextFileLevelIdentifierWMDTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, normalize, code_reduce_func)
    if precalculate:
        req_emb_creator = None # uses default (english(java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(True))
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)

def run_fasttext_comm_identifier_sentence_wmd(dataset, eval_strategy, trace_link_creator, req_reduce_func, code_reduce_func, 
                                                   output_filename_suffix="", normalize=True, precalculate=False):
    log.info("\n#####  FastText comm identifier sentence  ({}) WMD on {}: \n######################################".format(type(trace_link_creator).__name__,dataset.name()))
    tlp = FastTextCommentIdentifierSentenceWMDTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, normalize, req_reduce_func, code_reduce_func)
    if precalculate:
        req_emb_creator = None # uses default (english(java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(True))
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
    
def run_fasttext_comment_level_wmd(dataset, eval_strategy, trace_link_creator, code_reduce_func,
                                            output_filename_suffix="", normalize=True, precalculate=False):
    log.info("\n#####  FastText Comment Level ({}) WMD on {}: \n######################################".format(type(trace_link_creator).__name__,dataset.name()))
    tlp = FastTextCommentLevelWMDTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, normalize, code_reduce_func)
    if precalculate:
        req_emb_creator = None # uses default (english(java) embedding creator if None
        code_emb_creator = None
        if isinstance(dataset, Smos):
            req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, IT_WORD_TOKENIZER, PREPROCESSED_REQ_OUTPUT_DIR)
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER), PREPROCESSED_CODE_OUTPUT_DIR)
        if isinstance(dataset, Libest):
            code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
        tlp.precalculate_tracelinks(req_emb_creator, code_emb_creator)
    else:
        tlp.build_precalculated_name_and_load()
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(output_filename_suffix)
    
def run_bert_tracelinks_trace_pairs(dataset, eval_strategy, traceLinkType, req_reduce_func, code_reduce_func, output_filename_suffix="",
                                      normalize=False, precalculate=False):
    log.info("\n#####  Self-trained Bert trace link pairs ({}) on {}: \n######################################".format(traceLinkType.name, dataset.name()))
    b = BertSelfTrainedTraceLinkProcessor.create(dataset, PREDICTOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, 
            DROP_THRESHOLDS, normalize, req_reduce_func, code_reduce_func, traceLinkType, 0.2)
    if precalculate:
        b.precalculate_tracelinks()
    else:
        b.build_precalculated_name_and_load(0.2, traceLinkType, dataset)
    eval_strategy.set_trace_link_processor(b)
    eval_strategy.run(output_filename_suffix)
    
def run_bert_combined_tracelinks_trace_pairs(dataset, eval_strategy, trace_link_processor, trace_link_type_1, trace_link_type_2, req_reduce_func, code_reduce_func, output_filename_suffix="",
                                      normalize=False, precalculate=False):
    log.info("\n#####  Self-trained combined Bert trace link pairs ({}, {}) on {}: \n######################################".format(
        trace_link_type_1.name, trace_link_type_2.name, dataset.name()))
    b = BertCombinedSelfTrainedTLP.create(dataset, None, trace_link_processor, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, 
            DROP_THRESHOLDS, normalize, req_reduce_func, code_reduce_func)
    b.build_precalculated_name_and_load(trace_link_type_1, trace_link_type_2, 0.2, dataset)
    eval_strategy.set_trace_link_processor(b)
    eval_strategy.run(output_filename_suffix)
                                         
def run_call_graph_tracelinks(dataset, eval_strategy, trace_link_creator, req_reduce_func, code_reduce_func,
                               req_emb_creator=None, code_emb_creator=None, normalize=False, output_filename_suffix="", precalculate=False):
    log.info("\n#####  Callgraph Trace links ({}) on {}: \n######################################".format(type(trace_link_creator).__name__,dataset.name()))
    m = MethodCallGraphTLP.create(dataset, WORD_EMBD_CREATOR, trace_link_creator, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS,
                                   DROP_THRESHOLDS, normalize, req_reduce_func, code_reduce_func)
    if precalculate:
        m.precalculate_tracelinks(None, None, req_emb_creator, code_emb_creator) # None = Using default precalculated file names
    else:
        m.build_precalculated_name_and_load(type(req_emb_creator).__name__, type(code_emb_creator).__name__)
    eval_strategy.set_trace_link_processor(m)
    eval_strategy.run(output_filename_suffix)
    
def precalculate(tlp, req_emb_creator=None, code_emb_creator=None, output_name_suffix=""):
    """
    if isinstance(dataset, Smos):
        req_emb_creator = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(True))
        code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(IT_WORD_TOKENIZER))
    if isinstance(dataset, Libest):
        code_emb_creator = MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, CCodeASTTokenizer(), PREPROCESSED_CODE_OUTPUT_DIR)
    """
    Util.log_curr_time()
    log.info("\n#####  Precalculation for {} ... \n######################################".format(type(tlp).__name__,))
    tlp.precalculate_tracelinks(None, req_emb_creator, code_emb_creator, output_name_suffix)
    log.info("   ... Precalculation done.")
    Util.log_curr_time()
    
def precalculate_wmd_callgraph_files(tlp, req_embedding_creator, output_name_suffix=""):
    tlp.precalculate_for_callgraph_files(req_embedding_creator=req_embedding_creator, output_name_suffix=output_name_suffix)
    
def best_f1_finder(trace_link_processor, output_suffix = ""):
    if isinstance(trace_link_processor._trace_link_creator, TopNTraceLinkCreator):
        log.error("best_f1_finder() does not support TopNTraceLinkCreators")
        return
    trace_link_processor.build_precalculated_name_and_load(output_suffix = output_suffix)
    eval_strategy = WritePrecRecallF1Excel()
    eval_strategy.set_trace_link_processor(trace_link_processor)
    best_f1, best_elem_thresh, best_maj_thresh, best_file_thresh = eval_strategy.run()
    if len(ELEM_THRESHOLDS) > 1:
        if best_elem_thresh <= 0.02:
            new_elem_thresh = Util.get_range_array(0, best_elem_thresh + 0.06, 0.01)
        elif best_elem_thresh >= 0.98:
            new_elem_thresh = Util.get_range_array(best_elem_thresh - 0.06, best_elem_thresh, 0.01)
        else:
            new_elem_thresh = Util.get_range_array(best_elem_thresh - 0.03, best_elem_thresh + 0.03, 0.01)
    else:
        new_elem_thresh = ELEM_THRESHOLDS
    if len(MAJORITY_THRESHOLDS) > 1:
        if best_maj_thresh <= 0.02:
            new_maj_thresh = Util.get_range_array(0, best_maj_thresh + 0.06, 0.01)
        elif best_elem_thresh >= 0.98:
            new_maj_thresh = Util.get_range_array(best_maj_thresh - 0.06, best_maj_thresh, 0.01)
        else:
            new_maj_thresh = Util.get_range_array(best_maj_thresh - 0.03, best_maj_thresh + 0.03, 0.01)
    else:
        new_maj_thresh = MAJORITY_THRESHOLDS
    if len(DROP_THRESHOLDS) > 1:
        if best_file_thresh <= 0.02:
            new_file_thresh = Util.get_range_array(0, best_elem_thresh + 0.06, 0.01)
        elif best_file_thresh >= 0.98:
            new_file_thresh = Util.get_range_array(best_file_thresh - 0.06, best_file_thresh, 0.01)
        else:
            new_file_thresh = Util.get_range_array(best_file_thresh - 0.03, best_file_thresh + 0.03, 0.01)
    else:
        new_file_thresh = DROP_THRESHOLDS
        
    trace_link_processor.change_thresholds(new_elem_thresh, new_maj_thresh, new_file_thresh)
    eval_strategy.set_trace_link_processor(trace_link_processor)
    new_best_f1, new_best_elem_thresh, new_best_maj_thresh, new_best_file_thresh = eval_strategy.run()
    while new_best_f1 > best_f1:
        best_f1 = new_best_f1
        if len(ELEM_THRESHOLDS) > 1:
            if new_best_elem_thresh <= 0 or new_best_elem_thresh >= 1:
                break
            new_elem_thresh = Util.get_range_array(new_best_elem_thresh - 0.03, new_best_elem_thresh + 0.03, 0.01)
        if len(MAJORITY_THRESHOLDS) > 1:
            if new_best_maj_thresh <= 0 or new_best_maj_thresh >= 1:
                break
            new_maj_thresh = Util.get_range_array(new_best_maj_thresh - 0.03, new_best_maj_thresh + 0.03, 0.01)
        if len(DROP_THRESHOLDS) > 1:
            if new_best_file_thresh <= 0 or new_best_file_thresh >= 1:
                break
            new_file_thresh = Util.get_range_array(new_best_file_thresh - 0.03, new_best_file_thresh + 0.03, 0.01)
        trace_link_processor.change_thresholds(new_elem_thresh, new_maj_thresh, new_file_thresh)
        eval_strategy.set_trace_link_processor(trace_link_processor)
        new_best_f1, new_best_elem_thresh, new_best_maj_thresh, new_best_file_thresh = eval_strategy.run()
    
    
    new_elem_thresh = Util.get_range_array(new_best_elem_thresh - 0.01, new_best_elem_thresh + 0.01, 0.01)
    new_elem_thresh = [x for x in new_elem_thresh if 0 <= x <= 1]
    new_maj_thresh = Util.get_range_array(new_best_maj_thresh - 0.01, new_best_maj_thresh + 0.01, 0.01)
    new_maj_thresh = [x for x in new_maj_thresh if 0 <= x <= 1]
    new_file_thresh = Util.get_range_array(new_best_file_thresh - 0.01, new_best_file_thresh + 0.01, 0.01)
    new_file_thresh = [x for x in new_file_thresh if 0 <= x <= 1]
    
    trace_link_processor.change_thresholds(new_elem_thresh, new_maj_thresh, new_file_thresh)
    eval_strategy.set_trace_link_processor(trace_link_processor)
    new_best_f1, new_best_elem_thresh, new_best_maj_thresh, new_best_file_thresh = eval_strategy.run()
    
    
# preprocessing steps
CAMEL = CamelCaseSplitter()
LOWER = LowerCaseTransformer()
LETTER = NonLetterFilter()
URL = UrlRemover()
SEP = Separator()
JAVASTOP = JavaCodeStopWordRemover()
JAVASTOP_IT = JavaCodeStopWordRemover(True)
STOP_IT = StopWordRemover(True) # Italian stop word remover
STOP = StopWordRemover()
LEMMA_IT = Lemmatizer(Lemmatizer.LemmatizerType.italian_spacy)
LEMMA = Lemmatizer(Lemmatizer.LemmatizerType.english_spacy)
JAVADOC = JavaDocFilter()
W_LENGTH = WordLengthFilter(2) # Remove everthing that is smaller equal length 2

# Classes with different combinations for class embeddings
# used in run_all_fasttext_filelevel_cos_sim and 
MAJORITY_IDENTIFIEREMBEDDING_CLASSES = [IdentifierEmbeddingCreator, IdentifierEmbeddingCreatorWithMethodBody, IdentifierEmbeddingCreatorWithMethodComment,
IdentifierEmbeddingCreatorWithMethodCommentAndBody, IdentifierEmbeddingCreatorWithSuperClassifier,
IdentifierEmbeddingCreatorWithClassComment, IdentifierEmbeddingCreatorCommentToClass, IdentifierEmbeddingCreatorOnlyCommentsAndClassName,
IdentifierEmbeddingCreatorEverything, IdentifierEmbeddingCreatorWithMethodBodyToClass, IdentifierEmbeddingCreatorWithMethodCommentToClass,
IdentifierEmbeddingCreatorWithMethodBodyAndCommentToClass, IdentifierEmbeddingCreatorEverythingToClass, IdentifierEmbeddingCreatorCommentBodyToClass,
IdentifierEmbeddingOnlyMethods, IdentifierEmbeddingOnlyClassNameAndComment, IdentifierEmbeddingWithAttribute, IdentifierEmbeddingWithAttributeComment, 
IdentifierEmbeddingWithAttributeCommentToClass, IdentifierEmbeddingCreatorMethodAndComments, IdentifierEmbeddingCreatorMethodCommentsSuperclassifier]

IDENTIFIEREMBEDDING_CLASSES = MAJORITY_IDENTIFIEREMBEDDING_CLASSES + [ClassIdentifierEmbeddingCreator]

# Code AST Tokenizer / Parser
C_TOKENIZER = CCodeASTTokenizer(Libest())
JAVA_TOKENIZER = JavaCodeASTTokenizer(None, None)
JAVA_TOKENIZER_WORD_AND_SENTENCE = JavaCodeASTTokenizer(None, SentenceTokenizer(None, False))

# Tokenizer for natural language in english or italian
IT_WORD_TOKENIZER = WordTokenizer(None, True)
EN_WORD_TOKENIZER = WordTokenizer(None)
ETOUR308_UC_TOKENIZER = UCTokenizer(Etour308())
# Preprocessor for english artefacts. Tokens = word strings
CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, WordLengthFilter(2)])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, WordLengthFilter(2)])

"""
_oldpre: 
CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, W_LENGTH])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, W_LENGTH])

_newpre:
CODE_PREPROCESSOR = Preprocessor([JAVADOC, URL, SEP, LETTER, CAMEL, LOWER, JAVASTOP, LEMMA, STOP, W_LENGTH])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, W_LENGTH])

-preplus:
CODE_PREPROCESSOR = Preprocessor([JAVADOC, URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, W_LENGTH])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, W_LENGTH])
"""

# Preprocessor for BERT: Tokens = sentences; no lemmatizer or stop word remover needed
BERT_REQ_SENTENCE_PREPROCESSOR = Preprocessor([Separator(True), CamelCaseSplitter(True), NonLetterFilter(), DuplicateWhiteSpaceFilter(), AddFullStop()])


# Preprocessor for italian artefacts
CODE_PREPROCESSOR_IT = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP_IT, LOWER, LEMMA_IT, STOP_IT, W_LENGTH])
REQ_PREPROCESSOR_IT = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA_IT, STOP_IT, W_LENGTH])


# Chose the word embedding creator here. This does not have to be set if you are using precalculated files.
WORD_EMBD_CREATOR = MockWordEmbeddingCreator() # MockWordEmbeddingCreator creates random embeddings
#WORD_EMBD_CREATOR = FastTextEmbeddingCreator() # Use this for monolingual embeddings. Path to model as constructor argument.
#WORD_EMBD_CREATOR = FastTextAlignedEngItalEmbeddingCreator() # Use this for smos. Path to models as constructor argument.
#WORD_EMBD_CREATOR = FineTunedFastTextEmbeddingCreator() # Use this for the software requirement specific fasttext model by telge.
#WORD_EMBD_CREATOR = FastTextEmbeddingCreator() # Use this for monolingual embeddings
#WORD_EMBD_CREATOR = BertSentenceEmbeddingCreator() # Use this for bert sentence embeddings

PREDICTOR = None
# Use this for the self trained bert models 
#PREDICTOR = BertPredictor(pathlib.Path("/content/drive/My Drive/models/bert_models/sentence_bert_model"), True) 

FileUtil.setup_clear_dir(OUTPUT_DIR)
FileUtil.setup_clear_dir(PREPROCESSED_REQ_OUTPUT_DIR)
FileUtil.setup_clear_dir(PREPROCESSED_CODE_OUTPUT_DIR)


# Set ranges for the eval run
# Remember: 0 is highest similarity for wmd, 1 for cosine similarity
DROP_THRESHOLDS = Util.get_range_array(0.2, 0.8, 0.1)
MAJORITY_THRESHOLDS = Util.get_range_array(0.2, 0.8, 0.1) # can be majority thresholds or top n percentage depending on the trace link creator
ELEM_THRESHOLDS = Util.get_range_array(0.2, 0.8, 0.1)

# examples of requirement embedding creators
avg_sen_req_en = AverageSentenceEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR)
avg_req_en = AverageWordEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, EN_WORD_TOKENIZER)
avg_req_it = AverageWordEmbeddingCreator(REQ_PREPROCESSOR_IT, WORD_EMBD_CREATOR, IT_WORD_TOKENIZER) # italian

# examples of code embedding creators
id_code_en_java = IdentifierEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JAVA_TOKENIZER)
id_code_en_c = IdentifierEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, C_TOKENIZER)

# english identifiers, italian comments
id_code_it_comments_java = IdentifierEmbeddingCreator(CODE_PREPROCESSOR_IT, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(None, IT_WORD_TOKENIZER))

#req_name_tfidf_etour308 = UCTFIDFWordEmbeddingCreator(UCTokenizer(Etour308()), UCTFIDFWordEmbeddingCreator.default_precalculated_weights_file(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR)
#req__namedesc_tfidf_etour308 = UCTFIDFWordEmbeddingCreatorWithNameDesc(UCTokenizer(Etour308()), UCTFIDFWordEmbeddingCreatorWithNameDesc.default_precalculated_weights_file(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR)
#req__namedescflow_tfidf_etour308 = UCTFIDFWordEmbeddingCreatorWithNameDescFlow(UCTokenizer(Etour308()), UCTFIDFWordEmbeddingCreatorWithNameDescFlow.default_precalculated_weights_file(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR)

#code_tfidf_etour308 = TFIDFIdentifierEmbeddingCreator(TFIDFIdentifierEmbeddingCreator.default_precalculated_weights_file(Etour308()), CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JAVA_TOKENIZER)

"""
tlp = FastTextUCNameSentenceLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, TopNTraceLinkCreator(), ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True,  min, min)

#best_f1_finder(tlp)

tlp.precalculate_tracelinks(None, MockEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, ETOUR308_UC_TOKENIZER))
tlp.build_precalculated_name_and_load()
eval_strategy = WritePrecRecallF1Excel()
eval_strategy.set_trace_link_processor(tlp)
eval_strategy.run()

"""
DROP_THRESHOLDS = [1]#Util.get_range_array(0.47, 0.49, 0.01)
MAJORITY_THRESHOLDS = [1]#Util.get_range_array(0.59, 0.6, 0.01)
ELEM_THRESHOLDS = [1]#Util.get_range_array(0.67, 0.69, 0.01)
###eval_strategy = MeanAveragePrecision(1)
eval_strategy = WritePrecRecallF1Excel()

w = 0.88
CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, WordLengthFilter(2)])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, WordLengthFilter(2)])

tlc = WeightedSimilaritySumCallElementLevelMajorityTLC(w, CallGraphTLC.NeighborStrategy.both)#

"""
# B + methkomm Etour
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

# Etour B + UC 
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, UCTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")



r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(Itrust(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(SmosTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(SmosTrans(), JavaDocDescriptionOnlyTokenizer(SmosTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP.create(SmosTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(EANCI(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(EANCI(), JavaDocDescriptionOnlyTokenizer(EANCI(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP.create(EANCI(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")


r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(Itrust(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, UCTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")


#Itrust Filelevel
tlp = FastTextCommentIdentifierFilelevelClassNameOptionalWMDTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, DROP_THRESHOLDS, False, None)
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordTokenizer(Itrust(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, r, c, "_javadoc_spacy")

#Etour Filelevel
tlp = FastTextCommentIdentifierFilelevelClassNameOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, DROP_THRESHOLDS, False, None)
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, r, c, "_javadoc_spacy")



# Etour best verfahren cossim
tlp = MethodCallGraphTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
r = UCAverageWordEmbeddingCreatorWithNameDescFlow(UCTokenizer(Etour308(), False), REQ_PREPROCESSOR, WORD_EMBD_CREATOR, PREPROCESSED_REQ_OUTPUT_DIR)
c = MethodCommentSignatureCallGraphEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, None, r, c, "_javadoc_best")

#Etour cossim satzweise Req
tlp = MethodCallGraphTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
r = AverageSentenceEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(Etour308(), False),  PREPROCESSED_REQ_OUTPUT_DIR)
c = MethodCommentSignatureCallGraphEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, None, r, c, "_javadoc_satz")

#Etour cossim fliess Req
tlp = MethodCallGraphTLPWholeReq.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
r = AverageWordEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, WordTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MethodCommentSignatureCallGraphEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, None, r, c, "_javadoc_flies")
"""

"""
#itrust cossim satzweise Req / best verfahren
tlp = MethodCallGraphTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
r = AverageSentenceEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, WordAndSentenceTokenizer(Itrust(), False),  PREPROCESSED_REQ_OUTPUT_DIR)
c = MethodCommentSignatureCallGraphEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, None, r, c, "_javadoc_best")

#itrust cossim fliess Req
tlp = MethodCallGraphTLPWholeReq.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
r = AverageWordEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, WordTokenizer(Itrust(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MethodCommentSignatureCallGraphEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_tracelinks(None, None, r, c, "_javadoc_flies")



#Itrust ohne UC Struktur, Fliestext
tlp = FastTextCommentIdentifierClassNameVoterOptionalWMDTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, None)
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordTokenizer(Itrust(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Itrust(), JavaDocDescriptionOnlyTokenizer(Itrust(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#Etour308 ohne UC Struktur, Fliestext
tlp = FastTextCommentIdentifierClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, None)
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

"""
"""
#EANCI best
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, UCTokenizer(EANCINoTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(EANCINoTrans(), JavaDocDescriptionOnlyTokenizer(EANCINoTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP.create(EANCINoTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#EANCI ohne Methkomm
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, UCTokenizer(EANCINoTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(EANCINoTrans(), JavaDocDescriptionOnlyTokenizer(EANCINoTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP.create(EANCINoTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#EANCI ohne UC Stuktur, satzweise
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, WordAndSentenceTokenizer(EANCINoTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(EANCINoTrans(), JavaDocDescriptionOnlyTokenizer(EANCINoTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP.create(EANCINoTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#EANCI ohne UC Struktur, Fliesstext
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, WordTokenizer(EANCINoTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(EANCINoTrans(), JavaDocDescriptionOnlyTokenizer(EANCINoTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierClassNameVoterOptionalWMDTLP.create(EANCINoTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")


#Smos ohne Methkomm
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, UCTokenizer(SmosTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(SmosTrans(), JavaDocDescriptionOnlyTokenizer(SmosTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP.create(SmosTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#SmosTrans ohne UC Stuktur, satzweise
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, WordAndSentenceTokenizer(SmosTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(SmosTrans(), JavaDocDescriptionOnlyTokenizer(SmosTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP.create(SmosTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

#SmosTrans ohne UC Struktur, Fliesstext
r = MockEmbeddingCreator(REQ_PREPROCESSOR_IT, None, WordTokenizer(SmosTrans(), True), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR_IT, None, JavaCodeASTTokenizer(SmosTrans(), JavaDocDescriptionOnlyTokenizer(SmosTrans(), True)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextCommentIdentifierClassNameVoterOptionalWMDTLP.create(SmosTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc_spacy")

# Etour ohne CG
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, UCTokenizer(Etour308(), False), PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(Etour308(), JavaDocDescriptionOnlyTokenizer(Etour308(), False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
tlp.precalculate_tracelinks(None, r, c, "_javadoc")




CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, WordLengthFilter(2)])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, WordLengthFilter(2)])
r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, ETOUR308_UC_TOKENIZER, PREPROCESSED_REQ_OUTPUT_DIR)
c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(JavaDocDescriptionOnlyTokenizer(False)), PREPROCESSED_CODE_OUTPUT_DIR) 
tlp = FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc")

tlp = FastTextUCNameDescFlowAllCommentSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_javadoc")



tlp = FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP.create(SmosTrans(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_preplus")


r = MockEmbeddingCreator(REQ_PREPROCESSOR, None, WordAndSentenceTokenizer(), PREPROCESSED_REQ_OUTPUT_DIR)

tlp = FastTextAllCommentSentenceIdentifierClassNameVoterOptionalWMDTLP.create(Itrust(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_preplus")


c = MockEmbeddingCreator(CODE_PREPROCESSOR, None, CCodeASTTokenizer, PREPROCESSED_CODE_OUTPUT_DIR) 

tlp = FastTextUCNameDescFlowSentenceLevelIdentifierClassNameVoterOptionalWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, None)
tlp.precalculate_for_callgraph_files(None, None, r, c, "_preplus")

TFIDFCosSimPrecalculator().precalculate(Etour308(), UCNameDescFlowChooser(ETOUR308_UC_TOKENIZER, REQ_PREPROCESSOR), RodriguezCodeChooser(JAVA_TOKENIZER, CODE_PREPROCESSOR))

tlp = FastTextUCNameDescFlowRodriguezIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, True, None)
tlp.build_precalculated_name_and_load(Etour308())
eval_strategy.set_trace_link_processor(tlp)
eval_strategy.run()

FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP
FastTextUCNameDescFlowAllCommentSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP
FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP
FastTextUCNameDescFlowCommentIdentifierSentenceSpecificNoClassNameVoterWMDTLP
"""

DROP_THRESHOLDS = Util.get_range_array(0, 1, 0.01)
MAJORITY_THRESHOLDS = Util.get_range_array(0, 0.1 , 0.01)
ELEM_THRESHOLDS = [1]#Util.get_range_array(0.67, 0.69, 0.01)
###eval_strategy = MeanAveragePrecision(1)
eval_strategy = WritePrecisionRecallCSV()

def abc(w, clazz, dataset, r, c, o="_javadoc_spacy"):
    tlc = WeightedSimilaritySumCallElementLevelMajorityTLC(w, CallGraphTLC.NeighborStrategy.both)
    #tlc = FileLevelCosSimTraceLinkCreator()
    tlp = clazz.create(dataset, WORD_EMBD_CREATOR, tlc, ELEM_THRESHOLDS, MAJORITY_THRESHOLDS, DROP_THRESHOLDS, False, min, min, None)
    tlp.build_precalculated_name_and_load_callgraph_wmd(dataset, output_suffix=o)
    ##tlp.build_precalculated_name_and_load(r, c, dataset, output_suffix=o)
    #tlp.build_precalculated_name_and_load(dataset, output_suffix=o)
    eval_strategy.set_trace_link_processor(tlp)
    eval_strategy.run(str(w))
    """
    tlp = clazz.create(dataset, WORD_EMBD_CREATOR, tlc, [1], [1], [1], False, min, min, None)
    #tlp.build_precalculated_name_and_load(r, c, dataset, output_suffix=o)
    tlp.build_precalculated_name_and_load_callgraph_wmd(dataset, output_suffix=o)
    #tlp.build_precalculated_name_and_load(dataset, output_suffix=o)
    
    eval_strateg2y = MeanAveragePrecision(1)
    eval_strateg2y.set_trace_link_processor(tlp)
    eval_strateg2y.run(str(w))
    
    eval_strateg2y = MeanAveragePrecision(2)
    eval_strateg2y.set_trace_link_processor(tlp)
    eval_strateg2y.run(str(w))
    
    eval_strateg2y = MeanAveragePrecision(3)
    eval_strateg2y.set_trace_link_processor(tlp)
    eval_strateg2y.run(str(w))
    
    eval_strateg2y = MeanAveragePrecision(None)
    eval_strateg2y.set_trace_link_processor(tlp)
    eval_strateg2y.run(str(w))
    """
abc(0.9, FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP, Itrust(), "AverageSentenceEmbeddingCreator", "MethodCommentSignatureCallGraphEmbeddingCreator")
####FastTextCommentIdentifierClassNameVoterOptionalWMDTLP
#abc(0.9, FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP, Etour308())
Util.log_curr_time()
"""
Best                        FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP / FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP
Ohne MethCom                FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP / FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP
Ohne UC-Strukur, Satzweise / baseline+Methkomm CG=None  FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP
Ohne UC-Struktur, Fliess    FastTextCommentIdentifierClassNameVoterOptionalWMDTLP
WMD Filelevel               FastTextCommentIdentifierFilelevelClassNameOptionalWMDTLP
Baseline CG=None            FastTextSentenceLevelIdentifierClassNameOptionalWMDTLP
Baseline + UC CG=None       FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP
Baseline + Methcomm + CG    FastTextCommentIdentifierSentenceClassNameVoterOptionalWMDTLP
Baseline + UC +CG           FastTextUCNameDescFlowSentenceSpecificIdentifierClassNameVoterOptionalWMDTLP
Baseline + Methcomm + UC CG=None FastTextUCNameDescFlowCommentIdentifierSentenceSpecificClassNameVoterOptionalWMDTLP

MethodCallGraphTLPWholeReq
UCAverageWordEmbeddingCreatorWithNameDescFlow
AverageWordEmbeddingCreator
AverageSentenceEmbeddingCreator
MethodCommentSignatureCallGraphEmbeddingCreator
for i in Util.get_range_array(0.5, 0.8, 0.1):
    abc(i)





random.seed(43)
pre = Paths.all_resulting_tracelinks_csv_filename(Etour308(), "FastTextUCNameIdentifierWMDTLP", 1, 1, 0.56)

f = StandardNSGA2Factory(300, 348, Etour308(), duplicate_individuals_allowed=False, duplicate_genes_allowed=False, max_generations=120, 
                         crossover_probability=0.8, max_crossover_size=50, mutation_probability=0.5, max_mutation_size=50, 
                         precalculated_genes_files=[], child_population_size=300)

nsga2 = f.create_nsga2_instance()
nsga2.run()

CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, JAVASTOP, LEMMA, STOP, W_LENGTH])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, W_LENGTH])

"""
"""
a = SaveAllTraceLinks.load_resulting_trace_link_csv_into_solutionmatrix(Etour308(), FastTextUCNameIdentifierWMDTLP, 1, 1, 0.56)

s = Util.get_range_array(116, 348, 1)
r = Req2CodeGeneticAlgorithm(precalculated_all_filelevel_sims_csv_filename(Etour308(), "FastTextUCNameIdentifierWMDTLP"), 
         [], elitism_mode=Req2CodeGeneticAlgorithm.ElitismMode.merge, max_mutation_size=50, max_crossover_size=50, 
         duplicate_individuals=False, constant_population_size=True, maximise_fitness=False, crossover_probability=0.5, 
         mutation_probability=0.3, constant_individual_size=True, start_individual_sizes=s, individual_size = 348, 
         population_size=120, generations=300)
r.start(Etour308())"""
"""
fh = logging.FileHandler(Paths.OUTPUT_DIR / "log_output.txt")
fh.setLevel(logging.INFO)
log.addHandler(fh)
"""
#tlp = FastTextUCNameIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, True, None)
#_run_eval_strategy_wmd(tlp, SaveAllTraceLinks(1, 1, 0.56), "")
#best_f1_finder(tlp)
"""
rule_applier = RuleApplier([ImplementsRule(Etour308(), RelationDirection.down)])
tlp = FastTextUCNameDescFlowSentenceLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, Util.create_averaged_vector, min, rule_applier= None)



tlp.precalculate_tracelinks(None, MockEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, ETOUR308_UC_TOKENIZER),
                            MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(EN_WORD_TOKENIZER)), "_cname_extra")
"""

"""
tlp = FastTextUCNameDescSentenceLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, rule_applier= None)

tlp.precalculate_tracelinks(None, MockEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, ETOUR308_UC_TOKENIZER),
                            MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(EN_WORD_TOKENIZER)), "_cname_extra")


tlp = FastTextUCNameSentenceLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min, rule_applier= None)

tlp.precalculate_tracelinks(None, MockEmbeddingCreator(REQ_PREPROCESSOR, WORD_EMBD_CREATOR, ETOUR308_UC_TOKENIZER),
                            MockEmbeddingCreator(CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JavaCodeASTTokenizer(EN_WORD_TOKENIZER)), "_cname_extra")
"""
#best_f1_finder(tlp, "_cname_extra")
#_run_eval_strategy_wmd(tlp, WritePrecRecallF1Excel(), "", precalculated_suffix="_cname_extra")
#run_fasttext_uc_name_identifier_wmd(Etour308(), SaveValidTraceLinks(1, 1, 0.56), output_filename_suffix ="")
"""
tlp = FastTextUCNameDescFlowIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, FileLevelCosSimTraceLinkCreator(), DROP_THRESHOLDS, True)
best_f1_finder(tlp)
#run_fasttext_uc_namedescflow_identifier_wmd(Etour308(), WritePrecRecallF1Excel(), output_filename_suffix ="_descflow")


MAJORITY_THRESHOLDS = Util.get_range_array(0.3, 0.8, 0.1)

tlp = FastTextUCNameDescFileLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                                         MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min)
precalculate(tlp, 
             MockEmbeddingCreator(REQ_PREPROCESSOR, None, ETOUR308_UC_TOKENIZER, PREPROCESSED_REQ_OUTPUT_DIR),
             MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR))

_run_eval_strategy_wmd(tlp, WritePrecRecallF1Excel(), output_filename_suffix = "f_desc")

tlp = FastTextUCNameDescFlowFileLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                                         MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min)
precalculate(tlp, 
             MockEmbeddingCreator(REQ_PREPROCESSOR, None, ETOUR308_UC_TOKENIZER, PREPROCESSED_REQ_OUTPUT_DIR),
             MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR))
_run_eval_strategy_wmd(tlp, WritePrecRecallF1Excel(), output_filename_suffix = "f_descflow")


TFIDF_STOP_REQ = TFIDFStopWordRemover(0.2, UCTFIDFWordEmbeddingCreatorWithNameDescFlow.default_precalculated_weights_file(Etour308()))
TFIDF_STOP_CODE = TFIDFStopWordRemover(0.2, TFIDFIdentifierEmbeddingCreator.default_precalculated_weights_file(Etour308()))
CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, TFIDF_STOP_CODE, W_LENGTH])
REQ_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, LOWER, LEMMA, STOP, TFIDF_STOP_REQ, W_LENGTH])

tlp = FastTextUCNameDescFlowSentenceLevelIdentifierWMDTLP.create(Etour308(), WORD_EMBD_CREATOR, MajorityTraceLinkCreator(), ELEM_THRESHOLDS,
                                    MAJORITY_THRESHOLDS, DROP_THRESHOLDS, True, min, min)

best_f1_finder(tlp, output_suffix="_tfidf_stop_0r-0c")

tlp.precalculate_tracelinks(None, MockEmbeddingCreator(REQ_PREPROCESSOR, None, ETOUR308_UC_TOKENIZER, PREPROCESSED_REQ_OUTPUT_DIR), 
                            MockEmbeddingCreator(CODE_PREPROCESSOR, None, JavaCodeASTTokenizer(WordTokenizer()), PREPROCESSED_CODE_OUTPUT_DIR),
                            "_tfidf_stop_0.15r-0.15c")
tlp.build_precalculated_name_and_load()
eval_strategy = WritePrecRecallF1Excel()
eval_strategy.set_trace_link_processor(tlp)
eval_strategy.run()"""


    
    







#run_fasttext_filelevel_cos_sim(Etour308(), WritePrecRecallF1Excel(), req_name_tfidf_etour308, code_tfidf_etour308)
##run_fasttext_filelevel_cos_sim(Etour308(), WritePrecRecallF1Excel(), req_name_tfidf_etour308, code_tfidf_etour308)
# use the run function above to start the eval
#run_fasttext_majority2(Etour308(), WritePrecRecallF1Excel(), UCAverageWordEmbeddingCreatorWithNameDesc(UCTokenizer(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR), id_code_en_java, output_filename_suffix="2")
#run_fasttext_majority2(Etour308(), WritePrecRecallF1Excel(), UCAverageWordEmbeddingCreatorWithNameDescFlow(UCTokenizer(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR), id_code_en_java, output_filename_suffix="3")

##run_fasttext_majority(Etour308(), WritePrecRecallF1Excel(), UCTFIDFWordEmbeddingCreator(UCTokenizer(Etour308()), 
"""
run_fasttext_majority(Etour308(), WritePrecRecallF1Excel(), UCTFIDFWordEmbeddingCreatorWithNameDesc(UCTokenizer(Etour308()), UCTFIDFWordEmbeddingCreatorWithNameDesc.default_precalculated_weights_file(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR), TFIDFIdentifierEmbeddingCreator(TFIDFIdentifierEmbeddingCreator.default_precalculated_weights_file(Etour308()),CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JAVA_TOKENIZER))


run_fasttext_majority(Etour308(), WritePrecRecallF1Excel(), UCTFIDFWordEmbeddingCreatorWithNameDescFlow(UCTokenizer(Etour308()), UCTFIDFWordEmbeddingCreatorWithNameDescFlow.default_precalculated_weights_file(Etour308()), REQ_PREPROCESSOR, WORD_EMBD_CREATOR), TFIDFIdentifierEmbeddingCreator(TFIDFIdentifierEmbeddingCreator.default_precalculated_weights_file(Etour308()),CODE_PREPROCESSOR, WORD_EMBD_CREATOR, JAVA_TOKENIZER))

"""