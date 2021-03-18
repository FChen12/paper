from SolutionTraceMatrix import SolutionTraceMatrix
from logging import getLogger
import Util
import Paths
import random
from Dataset import Dataset
import FileUtil
from TraceLink import TraceLink
from Embedding import MockEmbedding

log = getLogger(__name__)

PRINT_FALSE_NEGATIVES = False
PRINT_FALSE_POSITIVES = False
    
def evaluate(trace_link_candidates, solution_trace_matrix: SolutionTraceMatrix, keys_with_extension=False):
    """
    keys_with_extension: Set to True if solution trace matrix contains file names with extension
    """
    if not trace_link_candidates:
        text = "No Trace Link candidates!"
        log.debug(text)
        return []
    valid_trace_links = []
    sol_matrix_copy = Util.deep_copy(solution_trace_matrix)
    false_positives_matrix = SolutionTraceMatrix()
    for trace_link in trace_link_candidates:
        if sol_matrix_copy.contains_req_code_pair(trace_link.get_req_key(keys_with_extension), 
                                                          trace_link.get_code_key(keys_with_extension)):
            # Remove correct trace links on copy to avoid duplicate true positive count
            sol_matrix_copy.remove_trace_pair(trace_link.get_req_key(keys_with_extension), trace_link.get_code_key(keys_with_extension))
            valid_trace_links.append(trace_link)
        elif PRINT_FALSE_POSITIVES:
            false_positives_matrix.add_trace_pair(trace_link.get_req_key(keys_with_extension), trace_link.get_code_key(keys_with_extension))
    if PRINT_FALSE_NEGATIVES:
        _print_false_negatives(sol_matrix_copy)
    if PRINT_FALSE_POSITIVES:
        log.info("\n\nFalse Positives: {} Links, {} unique Reqs, {} unique Code".format(false_positives_matrix._number_of_trace_links,
                                                                    false_positives_matrix.num_unique_reqs(), false_positives_matrix.num_unique_code()))
        log.info("\n" + false_positives_matrix.print_str())
        
    return valid_trace_links


    
def evaluateQueryAP(trace_link_candidates, solution_trace_matrix: SolutionTraceMatrix, keys_with_extension=False, reverse_compare=False):
    """
    trace_link_candidates: List of TraceLink-objects
    """
    if not trace_link_candidates:
        text = "No Trace Link candidates!"
        log.info(text)
        return 0
    trace_link_candidates = list(dict.fromkeys(trace_link_candidates)) # Deterministic duplicate removal (set is not stable)
    sol_matrix_copy = Util.deep_copy(solution_trace_matrix)# Use copy to track false negatives and avoid duplicate trace links
    similarity_relevance_list = []
    for trace_link in trace_link_candidates:
        req_name = trace_link.get_req_key(keys_with_extension)
        code_name = trace_link.get_code_key(keys_with_extension)
        if sol_matrix_copy.contains_req_code_pair(req_name, code_name):
            similarity_relevance_list.append((trace_link.similarity, True))
            # Remove to track down False Negatives (Remaining entries in sol_matrix_copy are false negatives)
            sol_matrix_copy.remove_trace_pair(req_name, code_name)
        else:
            similarity_relevance_list.append((trace_link.similarity, False))
        
    ap, prec_k_print_str = Util.calculate_query_average_precision(similarity_relevance_list, reverse_compare)
    print_str = f"average_precision={ap}{prec_k_print_str}"
    text_file = open(Paths.OUTPUT_DIR / "precision_at_k.txt", "w")
    text_file.write(print_str)
    text_file.close()

    log.info(print_str)
    if PRINT_FALSE_NEGATIVES:
        _print_false_negatives(sol_matrix_copy)
    return ap

def evaluateMAP(trace_link_candidates, k, dataset: Dataset, reverse_compare=False):
    """
    trace_link_candidates: List of TraceLink-objects
    """
    if not trace_link_candidates:
        text = "No Trace Link candidates!"
        log.info(text)
        return 0, 0
    
    req_dict = _build_req_dict_for_map(trace_link_candidates, dataset, reverse_compare)
    map =  Util.calculate_mean_average_precision(req_dict, k, dataset.num_reqs(), reverse_compare)
        
    return map, len(trace_link_candidates)

def evaluateMAPRecall(trace_link_candidates, dataset: Dataset, reverse_compare=False):
    """
    trace_link_candidates: List of TraceLink-objects
    """
    if not trace_link_candidates:
        text = "No Trace Link candidates!"
        log.info(text)
        return 0, 0
    
    req_dict = _build_req_dict_for_map(trace_link_candidates, dataset, reverse_compare)
    
    recall_map_dict = {}
    for k in range(1, len(dataset.all_original_code_file_names()) + 1):
        map_k, rec_k = Util.calculate_mean_average_precision_and_recall(req_dict, k, dataset.num_reqs(), dataset.solution_matrix()._number_of_trace_links, reverse_compare)
        recall_map_dict[rec_k] = map_k
        print(f"{k}: {rec_k}, {map_k}")
    return recall_map_dict

def _build_req_dict_for_map(trace_link_candidates, dataset: Dataset, reverse_compare=False):
    trace_link_candidates = list(dict.fromkeys(trace_link_candidates)) # Deterministic duplicate removal (set is not stable)
    
    if len(trace_link_candidates) < dataset.num_original_links():
        # trace_link_candidates does not contain all possible link between reqs and code
        # -> Add missing links as dummy links with 0 similarity 
        code_filenames = dataset.all_original_code_file_names(True)
        req_filenames = dataset.all_original_req_file_names(True)
        for req_name in req_filenames:
            for code_name in code_filenames:
                no_similarity = 1 if reverse_compare else 0
                dummy_trace_link = TraceLink(MockEmbedding(req_name), MockEmbedding(code_name), no_similarity)
                if not dummy_trace_link in trace_link_candidates:
                    trace_link_candidates.append(dummy_trace_link)
    assert len(trace_link_candidates) == dataset.num_original_links(), f"{len(trace_link_candidates)} != {dataset.num_original_links()}"
    
    req_dict = {} # req_dict["req_name"] = [(sim_to_code_1: float, relevant: bool), (sim_to_code_2, relevant), ...]
    sol_matrix_copy = Util.deep_copy(dataset.solution_matrix()) # Use copy to track false negatives and avoid duplicate trace links
    for trace_link in trace_link_candidates:
        req_name = trace_link.get_req_key(dataset.keys_with_extension())
        code_name = trace_link.get_code_key(dataset.keys_with_extension())
        sim_rel_tuple_to_add = (trace_link.similarity, False)
        if sol_matrix_copy.contains_req_code_pair(req_name, code_name):
            sim_rel_tuple_to_add = (trace_link.similarity, True)
            sol_matrix_copy.remove_trace_pair(req_name, code_name)
        if req_name in req_dict:
            req_dict[req_name].append(sim_rel_tuple_to_add)
        else:
            req_dict[req_name] = [sim_rel_tuple_to_add]
            
    if PRINT_FALSE_NEGATIVES:
        _print_false_negatives(sol_matrix_copy)
        
    return req_dict
            
def _print_false_negatives(sol_matrix_with_false_negatives):
    log.info(f"\nFalse Negatives: {sol_matrix_with_false_negatives._number_of_trace_links} Links, {sol_matrix_with_false_negatives.num_unique_reqs()} unique Reqs, {sol_matrix_with_false_negatives.num_unique_code()} unique Code")
    log.info("\n" + sol_matrix_with_false_negatives.print_str())
        
def evaluate_and_calc_metrics(trace_link_candidates, solution_trace_matrix: SolutionTraceMatrix, keys_with_extension=False):
    valid_trace_links = evaluate(trace_link_candidates, solution_trace_matrix, keys_with_extension)
    if valid_trace_links:
        true_positives = len(valid_trace_links)
        total_num_found_links = len(trace_link_candidates)
        precision, recall, f_1 = Util.calc_prec_recall_f1(true_positives, total_num_found_links, solution_trace_matrix._number_of_trace_links)
        print_str = Util.build_prec_recall_f1_print_str(precision, recall, f_1, true_positives, total_num_found_links, solution_trace_matrix._number_of_trace_links)
        return precision, recall, f_1, print_str
    else:
        return 0, 0, 0, "No valid trace links"
    
def evaluate_tuple_list(trace_link_candidates, solution_trace_matrix: SolutionTraceMatrix):
    """
    trace_link_candidates as list of tuples: [(req, code, sim)]
    """
    if not trace_link_candidates:
        text = "No Trace Link candidates!"
        log.debug(text)
        return None, None
    total_num_found_links = 0
    valid_trace_links = []
    sol_matrix_copy = Util.deep_copy(solution_trace_matrix)
    false_positives_matrix = SolutionTraceMatrix()
    for req, code, sim in trace_link_candidates:
            total_num_found_links += 1
            if sol_matrix_copy.contains_req_code_pair(req, code):
                # Remove correct trace links on copy to avoid duplicate true positive count
                sol_matrix_copy.remove_trace_pair(req, code)
                valid_trace_links.append((req, code, sim))
            elif PRINT_FALSE_POSITIVES:
                false_positives_matrix.add_trace_pair(req, code)
    if PRINT_FALSE_NEGATIVES:
        _print_false_negatives(sol_matrix_copy)
    if PRINT_FALSE_POSITIVES:
        log.info("\n\nFalse Positives: {} Links, {} unique Reqs, {} unique Code".format(false_positives_matrix._number_of_trace_links,
                                                                    false_positives_matrix.num_unique_reqs(), false_positives_matrix.num_unique_code()))
        log.info("\n" + false_positives_matrix.print_str())
        
    precision, recall, f_1 = Util.calc_prec_recall_f1(len(valid_trace_links), total_num_found_links, solution_trace_matrix._number_of_trace_links)
    print_str = Util.build_prec_recall_f1_print_str(precision, recall, f_1, len(valid_trace_links), total_num_found_links, solution_trace_matrix._number_of_trace_links)
    return precision, recall, f_1, print_str
