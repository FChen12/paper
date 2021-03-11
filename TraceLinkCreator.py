import abc, logging, statistics
import TraceLink
import Util
from Embedding import MethodCallGraphEmbedding
from Preprocessing.CallGraphUtil import build_method_param_dict_key, build_class_method_param_dict_key2
from Preprocessing import CallGraphUtil
from enum import Enum
    
log = logging.getLogger(__name__)

PRINT_MAJORITY_VOTE_STATISTIC = False
PRINT_DETAILED_MAJORITY_VOTE_STATISTIC = False
class TraceLinkCreator(abc.ABC):
    """
    reverse_compare=True: Smaller sim value == better;
                    else: Bigger sim value == better;
        
    """
    def __init__(self):
        self.data_adapter = None
        self.req_reduce_func = None
        self.code_reduce_func = None
        self.reverse_compare = None
    
    @abc.abstractmethod
    def create_tracelinks(self, elem_level_drop_thresh, majority_drop_thresh):
        """
        Returns a dict: eval_results[majority_thresh] = list_of_trace_link_candidates
        """
        pass
    
    def comp_func(self, a, b):
        return a < b if self.reverse_compare else a > b
    
    
class FileLevelTraceLinkCreator(TraceLinkCreator):
        
    def create_tracelinks(self, elem_level_drop_thresh, majority_drop_thresh): # Dont need these threshold on file level
        trace_link_candidates = []
        for class_emb in self.data_adapter.code_file_list():
            candidate_link = self.data_adapter.init_candidate_tracelink(class_emb)
            for req_emb in self.data_adapter.req_file_list(code_elem=self.data_adapter.code_element_list(class_emb)[0]):
                candidate_link = self.add_candidates(req_emb, class_emb, candidate_link)
            if candidate_link.has_tracelinks():
                    trace_link_candidates.append(candidate_link)
        return trace_link_candidates
    
    @abc.abstractmethod
    def add_candidates(self, req_emb, class_emb, candidate_link):
        pass
    
    @abc.abstractmethod
    def description(self):
        pass
    
class FileLevelCosSimTraceLinkCreator(FileLevelTraceLinkCreator):
        
    def add_candidates(self, req_emb, code_emb, candidate_link):
        cos_sim = self.data_adapter.calculate_similarity(req_emb, code_emb, Util.calculate_cos_sim)
        candidate_link.add_req_candidate(cos_sim, self.data_adapter.req_emb(req_emb))
        return candidate_link
    
    def description(self):
        return "File Level Cos Sim"
    
class MajorityTraceLinkCreator(TraceLinkCreator):
    def __init__(self):
        super(MajorityTraceLinkCreator, self).__init__()
        self._statistic = dict() # code_file -> (num(winner requirements), num(total election candidates))
        
    def create_tracelinks(self, elem_level_drop_thresh, majority_drop_thresh):
        trace_link_candidates = self.iterate_code_files(elem_level_drop_thresh, majority_drop_thresh)
        if trace_link_candidates and (PRINT_MAJORITY_VOTE_STATISTIC or PRINT_DETAILED_MAJORITY_VOTE_STATISTIC):
            winners = []
            total = []
            max_vote_counts = []
            for codefile in self._statistic:
                winners.append(self._statistic[codefile][0])
                total.append(self._statistic[codefile][1])
                max_vote_counts.append(self._statistic[codefile][2])
                if PRINT_DETAILED_MAJORITY_VOTE_STATISTIC:
                    log.info("{} of {} for {}".format(self._statistic[codefile][0], self._statistic[codefile][1], codefile))
            
            log.info("---------------")
            log.info("average #winners: {}".format(Util.create_averaged_vector(winners)))
            log.info("median #winners: {}".format(statistics.median(winners)))
            log.info("average #total req candidates: {}".format(Util.create_averaged_vector(total)))
            log.info("median #total req candidates: {}".format(statistics.median(total)))
            log.info(f"max vote counts: {max_vote_counts}")
            log.info("---------------")
            
        return trace_link_candidates
    
    def iterate_code_files(self, elem_level_drop_thresh, maj_drop_thresh):
        
        trace_link_candidates = []
        for code_file in self.data_adapter.code_file_list(): 
            candidate_link = self.data_adapter.init_candidate_tracelink(code_file)
            link_dict, vote_array = self.get_votes_from_code_entries(code_file,
                                        self.req_reduce_func, elem_level_drop_thresh, maj_drop_thresh)
            if vote_array:
                majority_ranked_dict, max_vote_count = Util.majority_count(vote_array)
                
                """
                majority_ranked_dict = sorted(majority_ranked_dict.items(), key=lambda x:x[1], reverse=True)
                for entry in majority_ranked_dict[:6]:
                    req_filename = entry[0]
                    sim = self.code_reduce_func(link_dict.get_all_sims(req_filename))
                    candidate_link.add_req_candidate(sim, link_dict.get_req_emb(req_filename))
                """
                for req_filename in majority_ranked_dict:
                    
                    
                    if majority_ranked_dict[req_filename] == max_vote_count:
                        sim = self.code_reduce_func(link_dict.get_all_sims(req_filename))
                        candidate_link.add_req_candidate(sim, link_dict.get_req_emb(req_filename))
                    
                if candidate_link.has_tracelinks():
                    trace_link_candidates.append(candidate_link)
                self._statistic[candidate_link.get_codefile_name()] = (len(candidate_link.get_all_candidates()), len(majority_ranked_dict), max_vote_count)
        return trace_link_candidates
    
    
    def get_votes_from_code_entries(self, code_file, req_reduce_func, elem_level_drop_thresh, maj_drop_thresh):
        link_dict = ReqLinkRegister() # {req_filename: (req_emb, [sim1, sim2, ...])}
        vote_array = [] # contains the votes (requirement file names)
        for code_elem in self.data_adapter.code_element_list(code_file):
            all_code_elem_to_req_links = [] #[(sim, req_file)] contains sims to all reqs for this code elem
            for req_file in self.data_adapter.req_file_list(code_elem=code_elem): 
                req_filename = self.data_adapter.req_filename(req_file)
                all_code_elem_to_req_elem_sims = [] # list contains all similarities to sentences of a requirement above drop_thresh
                for req_elem in self.data_adapter.req_element_list(req_file):
                    sim = self.data_adapter.calculate_similarity(req_elem, code_elem, Util.calculate_cos_sim)
                    if sim == float("inf"):# Can happen if calculating wm distance with a completely oov document/element
                        continue
                    all_code_elem_to_req_elem_sims += [sim]
                all_code_elem_to_req_elem_sims = self.code_elem_to_req_elem_filter(all_code_elem_to_req_elem_sims, elem_level_drop_thresh)
                if not all_code_elem_to_req_elem_sims:
                    continue #No similarities to requirement sentences above threshold
                code_elem_to_req_sim = req_reduce_func(all_code_elem_to_req_elem_sims) # calculate a single sim value for the requirement
                all_code_elem_to_req_links.append((code_elem_to_req_sim, req_file))
            all_code_elem_to_req_links = self.code_elem_to_req_filter(all_code_elem_to_req_links, maj_drop_thresh)
            for link in all_code_elem_to_req_links:
                req_filename = self.data_adapter.req_filename(link[1])
                vote_array.append(req_filename)
                link_dict.add(req_filename, self.data_adapter.req_emb(link[1]), link[0])

        return link_dict, vote_array
    
    def code_elem_to_req_elem_filter(self, all_similarities_to_req, drop_thresh):
        return [sim for sim in all_similarities_to_req if self.comp_func(sim, drop_thresh)]
    
    def code_elem_to_req_filter(self, all_code_elem_to_req_links, drop_thresh):
        return [elem for elem in all_code_elem_to_req_links if self.comp_func(elem[0], drop_thresh)]
    
        
class CallGraphTLC(MajorityTraceLinkCreator):
    
    class NeighborStrategy(Enum):
        both = 1 
        up = 2   # Only neighbors that call this method
        down = 3 # Only neighbors that are called by this method
    
    def __init__(self, method_weight=None, neighbor_strategy: NeighborStrategy=NeighborStrategy.both):
        super(CallGraphTLC, self).__init__()
        self.method_call_graph_dict = None
        self.no_classname_in_cg_key = False
        self.method_weight = method_weight
        self.neighbor_strategy = neighbor_strategy
        if method_weight is not None:
            assert method_weight >= 0 and method_weight <= 1
            self.method_multiplier = method_weight / (1 - method_weight)
        
        
    def get_votes_from_code_entries(self, code_file, req_reduce_func, elem_level_drop_thresh, maj_drop_thresh):
        link_dict = ReqLinkRegister() # {req_filename: (req_emb, [sim1, sim2, ...])}
        vote_array = [] # contains the votes (requirement file names)
        assert isinstance(code_file, MethodCallGraphEmbedding)
        for method_name_key in code_file.methods_dict:
            # method_vote_array: contains the votes ( == requirement file names)
            # method_link_dict: {req_filename: (req_emb, [sim1, sim2, ...])}
            method_link_dict, method_vote_array = self.init_method_dict_and_vote_array() 
            
            current_sims = self.get_method_property(code_file, method_name_key, req_reduce_func, elem_level_drop_thresh)
            method_link_dict, method_vote_array = self.handle_current_method(current_sims, method_link_dict, method_vote_array, elem_level_drop_thresh)
            method_callgraph_key = build_class_method_param_dict_key2(code_file.class_name, method_name_key)
            if self.no_classname_in_cg_key:
                method_callgraph_key = method_name_key
            if not method_callgraph_key in self.method_call_graph_dict:
                log.debug("Method not in method call graph:" + method_callgraph_key)
            else:
                method_callgraph_entry = self.method_call_graph_dict[method_callgraph_key]
                all_neighbors = None
                if self.neighbor_strategy == self.NeighborStrategy.both:
                    all_neighbors = method_callgraph_entry[CallGraphUtil.CALLED_BY] + method_callgraph_entry[CallGraphUtil.CALLS]
                elif self.neighbor_strategy == self.NeighborStrategy.up:
                    all_neighbors = method_callgraph_entry[CallGraphUtil.CALLED_BY]
                elif self.neighbor_strategy == self.NeighborStrategy.down:
                    all_neighbors = method_callgraph_entry[CallGraphUtil.CALLS]
                else:
                    log.error("Unknown neighbor strategy: " + str(self.neighbor_strategy))
                for neighbor_method_tuple in all_neighbors:
                    neighbor_method = self.method_call_graph_dict[neighbor_method_tuple[0]]
                    for code_emb in self.data_adapter.code_file_list():
                        assert isinstance(code_emb, MethodCallGraphEmbedding)
                        # Determine class of the neighbor method to build the emb_method_key
                        if self.is_in_same_class(code_emb, neighbor_method[CallGraphUtil.CLASS_NAME]):
                            emb_method_key = build_method_param_dict_key(neighbor_method[CallGraphUtil.METHOD_NAME], 
                                                             neighbor_method[CallGraphUtil.PARAMS])
                
                            sims = self.get_method_property(code_emb, emb_method_key, req_reduce_func, elem_level_drop_thresh)
                            if not sims:
                                continue
                            method_link_dict, method_vote_array = self.process_neighbor_method(sims, method_link_dict,
                                                                                             method_vote_array, elem_level_drop_thresh)
                    
                if self.method_weight is not None:
                    method_vote_array = self.apply_weighting(method_vote_array)
            link_dict, vote_array = self.eval_method_links(link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh)    
        
        for non_cg_key in code_file.non_cg_dict:
            # add class elements with no cg property (e.g. class name) as potential voters
            similarity_tuple_list = code_file.get_non_cg_sim(non_cg_key)
            for sim_list, req_name in similarity_tuple_list:
                filtered_sims = [sim for sim in sim_list if self.comp_func(sim, elem_level_drop_thresh)]
                if not filtered_sims:
                    continue  #this code elem has no similarities to req elements above threshold 
                aggregated_sim_to_req = req_reduce_func(filtered_sims)
                if  self.comp_func(aggregated_sim_to_req, maj_drop_thresh):
                    # Add req as vote
                    vote_array.append(req_name)
                    link_dict.add(req_name, self.data_adapter.get_req_file(req_name), aggregated_sim_to_req)
        
        return link_dict, vote_array
                    
    def apply_weighting(self, method_vote_array):
        current_method_votes = method_vote_array[0]
        neighbor_votes = method_vote_array[1]
        additional_votes_for_curr_method = round(self.method_multiplier * len(neighbor_votes)) - len(current_method_votes)
        method_vote_array[0] += current_method_votes * additional_votes_for_curr_method
        return method_vote_array
    
    def is_in_same_class(self, cg_emb, neighbor_class):
        if self.no_classname_in_cg_key:# Libest: check for filename instead of class name
            return cg_emb.file_name == neighbor_class
        else:
            return cg_emb.check_class_name(neighbor_class)
    @abc.abstractmethod
    def handle_current_method(self, current_sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        pass
    
    @abc.abstractmethod
    def process_neighbor_method(self, neighbor_method_tuple, method_link_dict, method_vote_array, elem_level_drop_thresh):
        pass
    
    @abc.abstractmethod
    def eval_method_links(self, link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh):
        pass
    @abc.abstractmethod
    def get_method_property(self, code_file, method_name_key, req_reduce_func, elem_level_drop_thresh):
        pass
    
    
    def init_method_dict_and_vote_array(self):
        return ReqLinkRegister(), [[],[]] #First inner list for current method votes, second for neighbor votes
                
class CallGraphSimBasedTLC(CallGraphTLC):
    """
    Superclass for trace links creators who create trace links by the
    pre-calculated similarity values without using the vectors
    """
                
    def get_method_property(self, code_file, method_name_key, req_reduce_func, elem_level_drop_thresh):
        return code_file.get_method_sims(method_name_key) # Returns list of tuples: [(sim, req_emb_1), (sim, req_emb_2), ...]
    
       
class CallGraphDoubleMajorityTLC(CallGraphSimBasedTLC):
    def get_vote_with_max_sim(self, vote_tuple_list):# list of [(sim, req), (sim, req), ...]
        return sorted(vote_tuple_list, key=lambda x: x[0], reverse=True)[0]
        
    def handle_current_method(self, current_sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        # We dont need elem_level_drop_thresh because me always take the maximum
        vote_of_current_method = self.get_vote_with_max_sim(current_sims) #req with max sim
        req_filename = vote_of_current_method[1]
        req_emb = self.data_adapter.get_req_file(req_filename)
        method_vote_array[0].append(req_filename)
        method_link_dict.add(req_filename, req_emb, vote_of_current_method[0])
        return method_link_dict, method_vote_array
    
    def apply_weighting(self, method_vote_array):
        assert len(method_vote_array[0]) == 1
        return super(CallGraphDoubleMajorityTLC, self).apply_weighting(method_vote_array)
    
    def eval_method_links(self, link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh):
        method_vote_array = method_vote_array[0] + method_vote_array[1]
        majority_ranked_list, max_vote_count = Util.majority_count(method_vote_array)
        for req_filename in majority_ranked_list:
            if majority_ranked_list[req_filename] == max_vote_count:
                sim = self.code_reduce_func(method_link_dict.get_all_sims(req_filename))
                if self.comp_func(sim, maj_drop_thresh):
                    vote_array.append(req_filename)
                    link_dict.add(req_filename, method_link_dict.get_req_emb(req_filename), sim)
        return link_dict, vote_array
    
    def process_neighbor_method(self, sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        # We dont need elem_level_drop_thresh because me always take the maximum
        neighbor_vote = self.get_vote_with_max_sim(sims)
        req_filename = neighbor_vote[1]
        req_emb = self.data_adapter.get_req_file(req_filename)
        method_vote_array[1].append(req_filename)
        method_link_dict.add(req_filename, req_emb, neighbor_vote[0])
        return method_link_dict, method_vote_array
    
class AllCallMajorityTLC(CallGraphSimBasedTLC):
    
    def handle_current_method(self, current_sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        current_sims = self.code_elem_to_req_elem_filter(current_sims, elem_level_drop_thresh)
        for curr_vote in current_sims:
            req_filename = curr_vote[1]
            req_emb = self.data_adapter.get_req_file(req_filename)
            method_vote_array[0].append(req_filename)
            method_link_dict.add(req_filename, req_emb, curr_vote[0])
        return method_link_dict, method_vote_array
    
    def process_neighbor_method(self, sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        filtered_neighbor_votes = self.code_elem_to_req_elem_filter(sims, elem_level_drop_thresh)
        for neighbor_vote in filtered_neighbor_votes:
            req_filename = neighbor_vote[1]
            req_emb = self.data_adapter.get_req_file(req_filename)
            method_vote_array[1].append(req_filename)
            method_link_dict.add(req_filename, req_emb, neighbor_vote[0])
        return method_link_dict, method_vote_array
    
    def eval_method_links(self, link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh):
        # We dont need maj_drop_thresh, since its already filtered by elem_drop_thresh
        method_vote_array = method_vote_array[0] + method_vote_array[1]
        vote_array += method_vote_array
        for req_filename in method_link_dict:
            link_dict.add(req_filename, method_link_dict.get_req_emb(req_filename), method_link_dict.get_all_sims(req_filename))
        return link_dict, vote_array
    
    def code_elem_to_req_elem_filter(self, all_similarities_to_req, drop_thresh):
        return [sim for sim in all_similarities_to_req if self.comp_func(sim[0], drop_thresh)]
    
class WeightedSimilaritySumCallMajorityTLC(CallGraphSimBasedTLC):
    def init_method_dict_and_vote_array(self):
        return DualReqLinkRegister(), []
    
    def handle_current_method(self, current_sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        all_links_of_current_method = self.code_elem_to_req_filter(current_sims, elem_level_drop_thresh)
        for req_link in all_links_of_current_method:
            req_filename = req_link[1]
            req_emb = self.data_adapter.get_req_file(req_filename)
            method_link_dict.add(req_filename, req_emb, req_link[0], [])
        return method_link_dict, method_vote_array
    
    def process_neighbor_method(self, sims, method_link_dict, method_vote_array, elem_level_drop_thresh):
        filtered_neighbor_links = self.code_elem_to_req_elem_filter(sims, elem_level_drop_thresh)
        for neighbor_link in filtered_neighbor_links:
            req_filename = neighbor_link[1]
            req_emb = self.data_adapter.get_req_file(req_filename)
            method_link_dict.add(req_filename, req_emb, [], neighbor_link[0])
        return method_link_dict, method_vote_array
    
    def eval_method_links(self, link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh):
        averaged_link_dict = ReqLinkRegister()
        for req_filename in method_link_dict:
            neighbor_sims = method_link_dict.get_all_neighbor_sims(req_filename)
            current_sim = None
            if len(method_link_dict.get_all_sims(req_filename)) == 1:# The current method has sims to the req
                current_sim = method_link_dict.get_all_sims(req_filename)[0]
            req_emb = method_link_dict.get_req_emb(req_filename)
            if len(neighbor_sims) == 0: # No neighbor sims, method, only sims from current 
                sim = current_sim
            elif not method_link_dict.get_all_sims(req_filename): # No sims from current method, only neighbor sims
                sim = sum(neighbor_sims) / len(neighbor_sims) # average
            else:# There are both current sim and neighbor sims
                if self.method_weight is not None:
                    neighbor_weight = (1 - self.method_weight) / len(neighbor_sims)
                    sim = self.method_weight * current_sim + neighbor_weight * sum(neighbor_sims)
                else:
                    #sim = (current_sim + sum(neighbor_sims)) / (len(neighbor_sims) + 1)
                    sim = current_sim
            averaged_link_dict.add(req_filename, req_emb, sim)
            # The case where there are neither a current sim nor neighbor sims can not happen
            # since this wouldn't have been added to the method_link_dict in the first place
        
        for req_filename in averaged_link_dict:
            assert len(averaged_link_dict.get_all_sims(req_filename)) == 1
            averaged_sim = averaged_link_dict.get_all_sims(req_filename)[0]
            if self.comp_func(averaged_sim, maj_drop_thresh):
                vote_array.append(req_filename)
                link_dict.add(req_filename, averaged_link_dict.get_req_emb(req_filename), averaged_sim)
        return link_dict, vote_array
    
    def apply_weighting(self, method_vote_array):
        # Weighting occurs in eval_method_links() 
        return method_vote_array
    
    def code_elem_to_req_elem_filter(self, all_similarities_to_req, drop_thresh):
        return [sim for sim in all_similarities_to_req if self.comp_func(sim[0], drop_thresh)]
    
class WeightedSimilaritySumCallElementLevelMajorityTLC(WeightedSimilaritySumCallMajorityTLC):
    """
    The requirements can have multiple elements (similarities) that are aggregated with the req_reduce_func
    """
    def get_method_property(self, code_file, method_name_key, req_reduce_func, elem_level_drop_thresh):
        sims_tuple_list = code_file.get_method_sims(method_name_key)
        if not sims_tuple_list:
            log.debug(f"Skip: No similarity for {code_file.class_name}.{method_name_key}")
            return None
        filtered_tuple_list = []
        for tup in sims_tuple_list:
            filtered_sims = [sim for sim in tup[0] if self.comp_func(sim, elem_level_drop_thresh)]
            if filtered_sims:
                filtered_tuple_list.append((filtered_sims, tup[1]))
        # Returns list of tuples: [(aggregated_sim, req_name_1), (aggregated_sim, req_name_2), ...]
        return [(req_reduce_func(sims_tuple[0]), sims_tuple[1]) for sims_tuple in filtered_tuple_list]
         
    
    
class WeightedVectorSumCallMajorityTLC(CallGraphTLC):
    """
    Use the method_vote_array to store vectors of the current method and its neighbors
    """
    def init_method_dict_and_vote_array(self):
        return None, [[], []] # List of vectors of current method and neighbors
        
    def get_method_property(self, code_file, method_name_key, req_reduce_func, elem_level_drop_thresh):
        return code_file.get_method_vector(method_name_key)
    
    def apply_weighting(self, method_vote_array):
        return method_vote_array
    
    def handle_current_method(self, current_vector, method_link_dict, method_vote_array, elem_level_drop_thresh):
        method_vote_array[0] += [current_vector]
        return method_link_dict, method_vote_array
    
    def process_neighbor_method(self, vector, method_link_dict, method_vote_array, elem_level_drop_thresh):
        method_vote_array[1].append(vector)
        return method_link_dict, method_vote_array
    
    def eval_method_links(self, link_dict, vote_array, method_link_dict, method_vote_array, maj_drop_thresh):
        weighted_vector = None
        if method_vote_array[1] and self.method_weight: # There are neighbors -> apply weight
            current_method_vector = method_vote_array[0][0]
            neighbor_vectors = sum(method_vote_array[1]) / len(method_vote_array[1])
            weighted_vector = self.method_weight * current_method_vector + (1 - self.method_weight) * neighbor_vectors
        else:
            weighted_vector = method_vote_array[0][0]
        
        sims_to_all_reqs = [] #()
        for req_emb in self.data_adapter.req_file_list():
            sim = Util.calculate_cos_sim(req_emb.vector, weighted_vector)
            sims_to_all_reqs.append((sim, req_emb))
        sims_to_all_reqs = self.code_elem_to_req_filter(sims_to_all_reqs, maj_drop_thresh)
        for entry in sims_to_all_reqs:
            req_filename = entry[1].file_name
            vote_array.append(req_filename)
            link_dict.add(req_filename, entry[1], entry[0])
        return link_dict, vote_array
        
    
class TopNTraceLinkCreator(MajorityTraceLinkCreator):
    """
    Majority decision votes are filtered by top N instead of majority drop thresh
    """
    
    def code_elem_to_req_filter(self, all_code_elem_to_req_links, drop_thresh):
        if self.reverse_compare:
            all_code_elem_to_req_links.sort(key=lambda x: x[0]) # Smallest similarity first
        else:
            all_code_elem_to_req_links.sort(key=lambda x: x[0], reverse=True) # Biggest similarity first
        return all_code_elem_to_req_links[:drop_thresh]

class CombinationTLC(MajorityTraceLinkCreator):
    """
    Combines TraceLinks from one req source with two code sources e.g. identifier and comments
    req source is taken from the first data_adapter
    """
    def __init__(self):
        super(CombinationTLC, self).__init__()
        self.data_adapter_2 = None
        
    def __get_corresponding_code_file_from_data_adapter_2(self, code_file_data_1):
        code_file_name = self.data_adapter.code_filename(code_file_data_1)
        for code_file in self.data_adapter_2.code_file_list():
            if self.data_adapter_2.code_filename(code_file) == code_file_name:
                return code_file
        return None
            
    def iterate_code_files(self, elem_level_drop_thresh, maj_drop_thresh):
        trace_link_candidates = []
        for code_file_data_1 in self.data_adapter.code_file_list(): 
            candidate_link = self.data_adapter.init_candidate_tracelink(code_file_data_1)
            link_dict_data_1, vote_array_data_1 = self.get_votes_from_code_entries(code_file_data_1,
                                        self.req_reduce_func, elem_level_drop_thresh, maj_drop_thresh)
            
            code_file_data_2 = self.__get_corresponding_code_file_from_data_adapter_2(code_file_data_1)
            link_dict_data_2, vote_array_data_2 = self.get_votes_from_code_entries(code_file_data_2,
                                        self.req_reduce_func, elem_level_drop_thresh, maj_drop_thresh)
            candidate_link = self._apply_combination_strategy(link_dict_data_1, vote_array_data_1, link_dict_data_2, vote_array_data_2, candidate_link)
            if candidate_link.has_tracelinks():
                trace_link_candidates.append(candidate_link)
        return trace_link_candidates
    
    @abc.abstractmethod
    def _apply_combination_strategy(self, link_dict_data_1, vote_array_data_1, link_dict_data_2, vote_array_data_2, candidate_link):
        pass
    
class SeparateMajorityCombinationTLC(CombinationTLC):
    def _apply_combination_strategy(self, link_dict_data_1, vote_array_data_1, link_dict_data_2, vote_array_data_2, candidate_link):
        # majority vote on both data separately
        link_dict = dict() # (sim, req_emb) Needed to avoid duplicate trace links if code entry map to the same req
        if vote_array_data_1:
            id_majority_ranked_list, max_vote_count = Util.majority_count(vote_array_data_1)
            for req_filename in id_majority_ranked_list:
                if id_majority_ranked_list[req_filename] == max_vote_count:
                    sim = self.code_reduce_func(link_dict_data_1.get_all_sims(req_filename))
                    if req_filename not in link_dict or link_dict[req_filename][0] < sim:
                        link_dict[req_filename] = (sim, link_dict_data_1.get_req_emb(req_filename))
        if vote_array_data_2:
            comm_sent_majority_ranked_list, max_vote_count = Util.majority_count(vote_array_data_2)
            for req_filename in comm_sent_majority_ranked_list:
                if comm_sent_majority_ranked_list[req_filename] == max_vote_count:
                    sim = self.code_reduce_func(link_dict_data_2.get_all_sims(req_filename))
                    if req_filename not in link_dict or link_dict[req_filename][0] < sim:
                        link_dict[req_filename] = (sim, link_dict_data_2.get_req_emb(req_filename))
        for req_filename in link_dict:
            candidate_link.add_req_candidate(link_dict[req_filename][0], link_dict[req_filename][1])  
        return candidate_link
        
class UnionMajorityCombinationTLC(CombinationTLC):
    def _apply_combination_strategy(self, link_dict_data_1, vote_array_data_1, link_dict_data_2, vote_array_data_2, candidate_link):
        # majoritiy decision on union of both data
        all_votes = (vote_array_data_1 if vote_array_data_1 else []) + (vote_array_data_2 if vote_array_data_2 else [])
        if all_votes:
            majority_ranked_list, max_vote_count = Util.majority_count(all_votes)
            for req_filename in majority_ranked_list:
                if majority_ranked_list[req_filename] == max_vote_count:
                    all_sims_for_req = [] # accumulate all similarities to this req from both data
                    req_emb = None
                    if link_dict_data_1 and req_filename in link_dict_data_1:
                        all_sims_for_req += link_dict_data_1.get_all_sims(req_filename)
                        req_emb = link_dict_data_1.get_req_emb(req_filename)
                    if link_dict_data_2 and req_filename in link_dict_data_2:
                        all_sims_for_req += link_dict_data_2.get_all_sims(req_filename)
                        req_emb = link_dict_data_2.get_req_emb(req_filename) # req_emb from data 1 or data 2 should be the same
                    candidate_link.add_req_candidate(self.code_reduce_func(all_sims_for_req), req_emb)
        return candidate_link
        
    
class ReturnAllMajorityCombinationTLC(CombinationTLC):
    def _apply_combination_strategy(self, link_dict_data_1, vote_array_data_1, link_dict_data_2, vote_array_data_2, candidate_link):
        # Just return all previous trace links, ignoring votes
        link_dict = dict() # (sim, req_emb) Needed to avoid duplicate trace links
        for req_filename in link_dict_data_1:
            sim = self.code_reduce_func(link_dict_data_1.get_all_sims(req_filename))
            if req_filename not in link_dict or link_dict[req_filename][0] < sim:
                link_dict[req_filename] = (sim, link_dict_data_1.get_req_emb(req_filename))
        if link_dict_data_2:
            for req_filename in link_dict_data_2:
                sim = self.code_reduce_func(link_dict_data_2.get_all_sims(req_filename))
                if req_filename not in link_dict or link_dict[req_filename][0] < sim:
                    link_dict[req_filename] = (sim, link_dict_data_2.get_req_emb(req_filename))
        for req_filename in link_dict:
            candidate_link.add_req_candidate(link_dict[req_filename][0], link_dict[req_filename][1])   
        return candidate_link
    

        
        
class ReqLinkRegister:
    def __init__(self):
        # _link_dict[req_filename] = (req_emb, [sim1, sim2, ...])
        self._link_dict = {}
        
    def __iter__(self):
        return self._link_dict.__iter__()
           
    def get_all_sims(self, req_filename):
        return self._link_dict[req_filename][1]

    def get_req_emb(self, req_filename):
        return self._link_dict[req_filename][0]
      
    def add(self, req_filename, req_emb, sim):
        if not isinstance(sim, list):
            sim = [sim]
        if req_filename not in self._link_dict:
            self._link_dict[req_filename] = (req_emb, sim)
        else:
            self._link_dict[req_filename][1].extend(sim)
            
class DualReqLinkRegister(ReqLinkRegister):
    # _link_dict[req_filename] = (req_emb, [sim], [neighborSim1,  neighborSim2, ...])
    def get_all_neighbor_sims(self, req_filename):
        return self._link_dict[req_filename][2]
    
    def add(self, req_filename, req_emb, sim=[], neighbor_sim=[]):
        if not isinstance(sim, list):
            sim = [sim]
        if not isinstance(neighbor_sim, list):
            neighbor_sim = [neighbor_sim]
            
        if req_filename not in self._link_dict:
            self._link_dict[req_filename] = (req_emb, sim, neighbor_sim)
        else:
            
            self._link_dict[req_filename][1].extend(sim)
            self._link_dict[req_filename][2].extend(neighbor_sim)
        