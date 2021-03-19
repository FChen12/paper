import abc, logging
from EvalMatrix import EvalMatrix
from Paths import excel_eval_filename, RECALL_PREC_CSV_HEADER,\
    csv_recall_precision_filename, resulting_valid_tracelinks_csv_filename, all_resulting_tracelinks_csv_filename,\
    csv_recall_map_filename
import FileUtil
from Dataset import Dataset
import Util
from SolutionTraceMatrix import SolutionTraceMatrix
import Evaluator
import Paths

log = logging.getLogger(__name__)

class EvalStrategy(abc.ABC):
    """
    Determines the evaluation result by its sub classes.
    The thresholds are set in the given trace link processor.
    Even if using precalculated files, the threshold in the trace link processor must be set and match the thresholds in
    the precalculated file
    """
    def __init__(self, precalculated_eval_result_matrix_path=None):
        self._trace_link_processor = None
        self._run_config = None
        self._precalculated_eval_result_matrix_path = precalculated_eval_result_matrix_path
    
    def set_trace_link_processor(self, trace_link_processor):
        self._trace_link_processor = trace_link_processor
        self._run_config = trace_link_processor._run_config
        
    def run(self, output_file_suffix=""):
        if self._precalculated_eval_result_matrix_path:
            log.info("Loading precalculated eval result matrix from " + str(self._precalculated_eval_result_matrix_path))
            return self._process_eval_results(EvalMatrix.load_eval_result_matrix_from_file(self._precalculated_eval_result_matrix_path))
        else:
            log.info(Util.curr_time())
            log.info("Running TraceLinkProcessor: " + type(self._trace_link_processor).__name__ + " ... ")
            return self._process_eval_results(self._trace_link_processor.run(), output_file_suffix)
        
    @abc.abstractmethod
    def _process_eval_results(self, eval_result_matrix: EvalMatrix,output_file_suffix):
        pass
    
    
    
class WritePrecRecallF1Excel(EvalStrategy):
    """
    Writes the precision/recall/f1 values into an excel file.
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        excel_array = []
        best_f1 = 0
        best_elem_thresh = None
        best_maj_thresh = None
        best_file_thresh = None
        f_thresh_header = [self._run_config.file_thresh_text + str(dt) for dt in self._run_config.file_level_thresholds]
        for elem_thresh in eval_result_matrix.elem_threshs:
            start_row = [self._run_config.elem_thresh_text + str(elem_thresh)] + f_thresh_header
            excel_array.append(start_row)
            for m_thresh in eval_result_matrix.maj_threshs:
                next_row = [self._run_config.maj_thresh_text + self._run_config.majority_print[m_thresh]]
                for f_thresh in eval_result_matrix.file_level_threshs:
                    if eval_result_matrix.is_none_entry(elem_thresh, m_thresh, f_thresh):
                        next_row.append("")
                    else:
                        log.info("e{}/m{}/f{}:".format(elem_thresh,  self._run_config.majority_print[m_thresh], f_thresh))
                        f_1 = eval_result_matrix.f_1(elem_thresh, m_thresh, f_thresh)
                        if f_1 > best_f1:
                            best_f1 = f_1
                            best_elem_thresh = elem_thresh
                            best_maj_thresh = m_thresh
                            best_file_thresh = f_thresh
                        print_str = eval_result_matrix.print_str(elem_thresh, m_thresh, f_thresh)
                        log.info("\n" + print_str +"\n")
                        next_row.append(print_str)
                excel_array.append(next_row)
            excel_array.append([""])
        best_thresh_cell_str = ""
        if best_f1 > 0:
            best_tresh_str = f"e{best_elem_thresh} m{self._run_config.majority_print[best_maj_thresh]} f{best_file_thresh}"
            best_f1_str = f"Best f1: {best_f1} at " + best_tresh_str
            excel_array.append([best_f1_str])
            
            # if possible, append a 3x3 matrix with file level/maj thresh as columns/rows where the center cell contains the best f1 value
            best_m_tresh_limits = []
            if len(eval_result_matrix.maj_threshs) > 1:
                best_idx = eval_result_matrix.maj_threshs.index(best_maj_thresh)
                if best_idx - 1 >= 0:
                    best_m_tresh_limits.append(eval_result_matrix.maj_threshs[best_idx - 1])
                best_m_tresh_limits.append(best_maj_thresh)
                if best_idx + 1 < len(eval_result_matrix.maj_threshs):
                    best_m_tresh_limits.append(eval_result_matrix.maj_threshs[best_idx + 1])
            else:
                best_m_tresh_limits.append(best_maj_thresh)
            best_f_tresh_limits = []
            if len(eval_result_matrix.file_level_threshs) > 1:
                best_idx = eval_result_matrix.file_level_threshs.index(best_file_thresh)
                if best_idx - 1 >= 0:
                    best_f_tresh_limits.append(eval_result_matrix.file_level_threshs[best_idx - 1])
                best_f_tresh_limits.append(best_file_thresh)
                if best_idx + 1 < len(eval_result_matrix.file_level_threshs):
                    best_f_tresh_limits.append(eval_result_matrix.file_level_threshs[best_idx + 1])
            else:
                best_f_tresh_limits.append(best_file_thresh)
            
            
            excel_array.append([f"elem_level_drop_thresh: {best_elem_thresh}"] + [f"file_level_drop_thresh: {dt}" for dt in best_f_tresh_limits])
            for m_thr_limit in best_m_tresh_limits:
                next_excel_row = [f"majority_drop_thresh: {m_thr_limit}"]
                for f_thresh in best_f_tresh_limits:
                    if m_thr_limit == best_maj_thresh and f_thresh == best_file_thresh:
                        best_thresh_cell_str = best_tresh_str + "\n" + eval_result_matrix.print_str(best_elem_thresh, m_thr_limit, f_thresh)
                        next_excel_row.append(best_thresh_cell_str)
                    else:
                        next_excel_row.append(eval_result_matrix.print_str(best_elem_thresh, m_thr_limit, f_thresh))
                excel_array.append(next_excel_row)

        else:
            best_f1_str = "No trace links"
            excel_array.append([best_f1_str])
        
        log.info(best_f1_str + "\n" + best_thresh_cell_str)
        FileUtil.write_eval_to_excel(excel_array, excel_eval_filename(self._trace_link_processor._dataset, self._trace_link_processor.output_prefix() + "_" + output_file_suffix))
        return (best_f1, best_elem_thresh, best_maj_thresh, best_file_thresh)
        


class TotalAveragePrecision(EvalStrategy):
    """
        Calculates the total average precision (vary all three thresholds)
        Does not create an output file, the result is printed in log.info()
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        log.info("Calculating total average precision ... ")
        rec_prec_dict = {} # rec_prec_dict[recall] = precision
        for elem_thresh in self._run_config.elem_thresholds:
            for m_thresh in self._run_config.majority_thresholds:
                for f_thresh in self._run_config.file_level_thresholds:
                    if not eval_result_matrix.is_none_entry(elem_thresh, m_thresh, f_thresh):
                        recall = eval_result_matrix.recall(elem_thresh, m_thresh, f_thresh)
                        prec = eval_result_matrix.precision(elem_thresh, m_thresh, f_thresh)
                        if recall in rec_prec_dict: # only update prec if new value is better
                            if rec_prec_dict[recall] < prec:
                                rec_prec_dict[recall] = prec  
                        else:
                            rec_prec_dict[recall] = prec  
        
        log.info("Average precision: " + str(Util.calculate_discrete_integral_average_precision(rec_prec_dict)))
        first_three_threshs = str(eval_result_matrix.elem_threshs[:3]) + " ..." if len(eval_result_matrix.elem_threshs) >= 3 else str(eval_result_matrix.elem_threshs)
        log.info("elem_thresh= " + first_three_threshs)
        first_three_threshs = str(eval_result_matrix.maj_threshs[:3]) + " ..."  if len(eval_result_matrix.maj_threshs) >= 3 else str(eval_result_matrix.maj_threshs)
        log.info("majority_thresh= " + first_three_threshs)
        first_three_threshs = str(eval_result_matrix.file_level_threshs[:3]) + " ..."  if len(eval_result_matrix.file_level_threshs) >= 3 else str(eval_result_matrix.file_level_threshs)
        log.info("file_level_thresh= " + first_three_threshs)
        
class MeanAveragePrecision(EvalStrategy):
    """
    Calculates Mean Average Precision, sorted by Requirements
    For each Requirement, consider the list of linked code candidates
    Take the first k code candidates to calculate average precision
    """
    def __init__(self, k, precalculated_eval_result_matrix_path=None):
        super(MeanAveragePrecision, self).__init__(precalculated_eval_result_matrix_path)
        self.k = k
        
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        assert len(self._run_config.elem_thresholds) == 1, "Elem threshold needs to be a single threshold value"
        assert len(self._run_config.majority_thresholds) == 1, "majority threshold needs to be a single threshold value"
        assert len(self._run_config.file_level_thresholds) == 1, "file level threshold needs to be a single threshold value"
        
        e_thresh = self._run_config.elem_thresholds[0]
        m_thresh = self._run_config.majority_thresholds[0]
        f_thresh = self._run_config.file_level_thresholds[0]
        if not eval_result_matrix.is_none_entry(e_thresh, m_thresh, f_thresh):
            all_links = eval_result_matrix.all_trace_links(e_thresh, m_thresh, f_thresh)
            map, num_distinct_links = Evaluator.evaluateMAP(all_links, self.k, self._trace_link_processor._dataset, 
                                        self._trace_link_processor._run_config.reverse_compare)
            log.info(f"MAP @ {self.k}: {map}")
            
        else: 
            log.info(f"No trace links for Mean Average Precision")
     
class WriteMAPRecallCSV(EvalStrategy):
    """
    Create csv file containing recall;map pairs by varying k in map@k
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        log.info("Generationg csv...: ")
        assert len(self._run_config.elem_thresholds) == 1, "Elem threshold needs to be a single threshold value"
        assert len(self._run_config.majority_thresholds) == 1, "majority threshold needs to be a single threshold value"
        assert len(self._run_config.file_level_thresholds) == 1, "file level threshold needs to be a single threshold value"
        
        e_thresh = self._run_config.elem_thresholds[0]
        m_thresh = self._run_config.majority_thresholds[0]
        f_thresh = self._run_config.file_level_thresholds[0]
        if not eval_result_matrix.is_none_entry(e_thresh, m_thresh, f_thresh):
            all_links = eval_result_matrix.all_trace_links(e_thresh, m_thresh, f_thresh)
            recall_map_dict = Evaluator.evaluateMAPRecall(all_links, self._trace_link_processor._dataset, 
                                        self._trace_link_processor._run_config.reverse_compare)
                        
            output_file_name = csv_recall_map_filename(self._trace_link_processor._dataset, output_file_suffix)
            FileUtil.write_recall_precision_csv(recall_map_dict, output_file_name)
            
            log.info("... Done: ")     
        else:
            log.error(f"No trace links for e{e_thresh} m{m_thresh} f{f_thresh}")
            
class SeparateAveragePrecision(EvalStrategy):
    """
        Calculates the average precision for each majority/elem threshold-pair separately (only varying the file threshold)
        Does not create an output file, the result is printed in log.info()
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        highest_avg = 0
        highest_avg_elem_thresh = None
        highest_avg_maj_thresh = None
        avg_prec_dict = {} # avg_prec_dict[elem_thresh][maj_thresh] = avg prec
        for elem_thresh in self._run_config.elem_thresholds:
            inner_avg_prec_dict = {}
            for m_thresh in self._run_config.majority_thresholds:
                rec_prec_dict = {} # rec_prec_dict[recall] = precision
                for file_thresh in self._run_config.file_level_thresholds:
                    if not eval_result_matrix.is_none_entry(elem_thresh, m_thresh, file_thresh):
                        rec_prec_dict[eval_result_matrix.recall(elem_thresh, m_thresh, file_thresh)] = eval_result_matrix.precision(elem_thresh, m_thresh, file_thresh)
                avg_prec = Util.calculate_discrete_integral_average_precision(rec_prec_dict)
                if avg_prec > highest_avg:
                    highest_avg = avg_prec
                    highest_avg_elem_thresh = elem_thresh
                    highest_avg_maj_thresh = m_thresh
                inner_avg_prec_dict[m_thresh] = avg_prec
            avg_prec_dict[elem_thresh] = inner_avg_prec_dict
            
        excel_array = []
        elem_thresh_header = [self._run_config.elem_thresh_text +  str(dt) for dt in self._run_config.elem_thresholds]
        start_row = ["Max avg precision: {} at e{}m{}".format(highest_avg, highest_avg_elem_thresh, highest_avg_maj_thresh)] + elem_thresh_header
        excel_array.append(start_row)
        for m_thresh in eval_result_matrix.maj_threshs:
                next_row = [self._run_config.maj_thresh_text + self._run_config.majority_print[m_thresh]]
                for elem_thresh in eval_result_matrix.elem_threshs:
                    next_row.append("average_precision: " + str(avg_prec_dict[elem_thresh][m_thresh]))
                excel_array.append(next_row)
        FileUtil.write_eval_to_excel(excel_array, excel_eval_filename(self._trace_link_processor._dataset, self._trace_link_processor.output_prefix() + "_" + output_file_suffix))
        
class BestCrossProjectConfig(EvalStrategy):
    def __init__(self, datasets: [(Dataset, str)]):
        """
        Parameter dataset:
            [Dataset, precalculated_eval_matrix_file_name]
        precalculated_eval_matrix_file_name can be None of no precalculated file exists.
        Uses thresholds of run_config in trace_link_proceessor even if precalculated
        Does not create an output file, the result is printed in log.info()
        """
        super(BestCrossProjectConfig, self).__init__()
        self._datasets = datasets
        
    def run(self, output_file_suffix=""):
        eval_matrix_dict = {} # eval_matrix_dict[dataset_name] = eval_matrix_of_dataset
        dataset_majority_percentages_to_absolute = {}
        log.info("Running best cross project f 1")
        for d_tuple in self._datasets:
            dataset_obj = None
            if not isinstance(d_tuple, Dataset) and len(d_tuple) == 2 and d_tuple[1] is not None:
                dataset_obj = d_tuple[0]
                log.info("Loading precalculated eval result matrix for {} from {} ...".format(dataset_obj.name(), str(d_tuple[1])))
                eval_matrix_dict[dataset_obj.name()] = EvalMatrix.load_eval_result_matrix_from_file(d_tuple[1])
                self._trace_link_processor.reload_with_dataset(dataset_obj) # renew absolute top n values
            else:
                dataset_obj = d_tuple
                if isinstance(d_tuple, list) or isinstance(d_tuple, tuple):
                    dataset_obj = d_tuple[0]
                self._trace_link_processor.reload_with_dataset(dataset_obj)
                log.info(Util.curr_time())
                log.info("Running TraceLinkProcessor on dataset {} ...".format(dataset_obj.name()))
                eval_matrix_dict[dataset_obj.name()] = self._trace_link_processor.run()
            dataset_majority_percentages_to_absolute[dataset_obj.name()] = self._trace_link_processor._run_config.majority_percentage_to_absolute
        
        log.info(Util.curr_time())
        log.info("Calculate best avg f_1...")
        best_avg_f_1 = 0
        best_dataset_f_1 = {} # best_dataset_f_1[dataset_name] = best_f_1
        best_elem_thresh = None
        best_maj_thresh = None
        best_file_thresh = None
        for elem_thresh in self._run_config.elem_thresholds:
            for m_thresh in self._run_config.original_maj_threshs:
                for f_thresh in self._run_config.file_level_thresholds:
                    dataset_f_1 = {} #dataset_f_1[dataset_name] = f_1
                    for dataset_name in eval_matrix_dict:
                        # Maps top_n_percentage to top n absolute or identity function if not top n
                        m_absolute = dataset_majority_percentages_to_absolute[dataset_name][m_thresh] 
                        if eval_matrix_dict[dataset_name].is_none_entry(elem_thresh, m_absolute, f_thresh):
                            dataset_f_1[dataset_name] = None
                        else:
                            dataset_f_1[dataset_name] = eval_matrix_dict[dataset_name].f_1(elem_thresh, m_absolute, f_thresh)
                    if None in dataset_f_1.values():
                        continue
                    avg_f_1 = Util.create_averaged_vector(dataset_f_1.values())
                    if avg_f_1 > best_avg_f_1:
                        best_avg_f_1 = avg_f_1
                        best_dataset_f_1 = dataset_f_1
                        best_elem_thresh = elem_thresh
                        best_maj_thresh = m_thresh
                        best_file_thresh = f_thresh
                        
        log.info("Best cross project avg_f_1: {} at e{} m{} f{}".format(best_avg_f_1, best_elem_thresh, best_maj_thresh, best_file_thresh))
        log.info("Individual f_1_values: " + str(best_dataset_f_1))
                    
    def _process_eval_results(self, eval_result_matrix:EvalMatrix, output_file_suffix):
        pass
                            

class BestCrossProjectTechnique(EvalStrategy):
    """
        Parameter dataset:
            [Dataset, precalculated_eval_matrix_file_name]
        precalculated_eval_matrix_file_name can be None of no precalculated file exists.
        Uses thresholds of run_config in trace_link_proceessor even if precalculated
        Does not create an output file, the result is printed in log.info()
        """
    def __init__(self, datasets: [Dataset], precalculated_eval_result_matrix_path=None):
        super(BestCrossProjectTechnique, self).__init__(precalculated_eval_result_matrix_path)
        self._datasets = datasets
        
    def run(self, output_file_suffix=""):
        eval_matrix_dict = {} # eval_matrix_dict[dataset_name] = eval_matrix_of_dataset
        dataset_majority_percentages_to_absolute = {}
        log.info("Running best cross project independent threshold f 1")
        for d_tuple in self._datasets:
            dataset_obj = None
            if not isinstance(d_tuple, Dataset) and len(d_tuple) == 2 and d_tuple[1] is not None:
                dataset_obj = d_tuple[0]
                log.info("Loading precalculated eval result matrix for {} from {} ...".format(dataset_obj.name(), str(d_tuple[1])))
                eval_matrix_dict[dataset_obj.name()] = EvalMatrix.load_eval_result_matrix_from_file(d_tuple[1])
                self._trace_link_processor.reload_with_dataset(dataset_obj) # renew absolute top n values
            else:
                dataset_obj = d_tuple
                if isinstance(d_tuple, list) or isinstance(d_tuple, tuple):
                    dataset_obj = d_tuple[0]
                log.info(Util.curr_time())
                log.info("Running TraceLinkProcessor on dataset {} ...".format(dataset_obj.name()))
                self._trace_link_processor.reload_with_dataset(dataset_obj)
                eval_matrix_dict[dataset_obj.name()] = self._trace_link_processor.run()
            dataset_majority_percentages_to_absolute[dataset_obj.name()] = self._trace_link_processor._run_config.majority_percentage_to_absolute
        
        log.info(Util.curr_time())
        log.info("Calculate best avg f_1...")
        
        best_dataset_f_1 = {} # best_dataset_f_1[dataset_name] = (best_f_1, elem_thresh, maj_thresh, file_thresh)
        for dataset_name in eval_matrix_dict:
            best_f_1 = 0
            for elem_thresh in self._run_config.elem_thresholds:
                for m_thresh in self._run_config.original_maj_threshs:
                    for f_thresh in self._run_config.file_level_thresholds:
                        m_absolute = dataset_majority_percentages_to_absolute[dataset_name][m_thresh] 
                        if not eval_matrix_dict[dataset_name].is_none_entry(elem_thresh, m_absolute, f_thresh):
                            f_1 = eval_matrix_dict[dataset_name].f_1(elem_thresh, m_absolute, f_thresh)
                            if f_1 > best_f_1:
                                best_f_1 = f_1
                                best_dataset_f_1[dataset_name] = (f_1, elem_thresh, m_thresh, f_thresh)
        
        avg_f_1 = Util.create_averaged_vector(list(map(lambda x: x[0], best_dataset_f_1.values())))
                       
                        
        log.info("Best cross project independent avg_f_1: {}".format(avg_f_1))
        log.info("Individual f_1_values: " + str(list(map(lambda x: x + " f1={}: e{} m{} f{}".format(
            best_dataset_f_1[x][0], best_dataset_f_1[x][1], best_dataset_f_1[x][2], best_dataset_f_1[x][3]), best_dataset_f_1.keys()))))
                    
    def _process_eval_results(self, eval_result_matrix:EvalMatrix, output_file_suffix):
        pass
            
class WritePrecisionRecallCSV(EvalStrategy):
    """
    Create csv file containing recall;precision pairs
    Only varies the file threshold.
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_suffix=""):
        log.info("Generationg csv...: ")
        for elem_thresh in eval_result_matrix.elem_threshs:
            recall_prec_dict = {} # use this to override duplicate recall values
            for m_thresh in eval_result_matrix.maj_threshs:
                for f_thresh in eval_result_matrix.file_level_threshs:
                    if not eval_result_matrix.is_none_entry(elem_thresh, m_thresh, f_thresh):
                        recall = eval_result_matrix.recall(elem_thresh, m_thresh, f_thresh)
                        prec = eval_result_matrix.precision(elem_thresh, m_thresh, f_thresh)
                        if recall == 0 and prec == 0:
                            continue
                        recall_prec_dict[recall] = prec
                        
            #threshold_name = "_e{}m{}_".format(elem_thresh, self._run_config.majority_print[m_thresh])
        threshold_name = ""
        output_file_name = csv_recall_precision_filename(self._trace_link_processor._dataset, self._trace_link_processor.output_prefix() \
                                                                           + threshold_name + output_file_suffix) 
        FileUtil.write_recall_precision_csv(recall_prec_dict, output_file_name)
        FileUtil.write_dict_to_json(str(Paths.ROOT / output_file_suffix) + ".json", recall_prec_dict)
        log.info("... Done: ")
        
class SaveEvalResultMatrix(EvalStrategy):
    """
    saves the result of an trace link processor to a json file
    """
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_file_path):
        eval_result_matrix.write_eval_result_matrix_to_file(output_file_path)
        
class SaveAllTraceLinks(EvalStrategy):
    HEADER_REQ = "req"
    HEADER_CODE = "code"
    def __init__(self, elem_thresh, maj_thresh, file_thresh, precalculated_eval_result_matrix_path=None):
        """
        Saves the resulting trace links of the given threshold combi
        """
        super(SaveAllTraceLinks, self).__init__(precalculated_eval_result_matrix_path)
        self._elem_thresh = elem_thresh
        self._maj_thresh = maj_thresh
        self._file_thresh = file_thresh
        
    def _process_eval_results(self, eval_result_matrix: EvalMatrix, output_suffix=""):
        rows = [[self.HEADER_REQ, self.HEADER_CODE]]
        trace_links = self._choose_trace_links(eval_result_matrix)
        for trace_link in trace_links:
            rows.append([trace_link.get_req_key(), trace_link.get_code_key()])
        FileUtil.write_rows_to_csv_file(self._default_resulting_tracelinks_csv_filename(self._trace_link_processor._dataset, 
                type(self._trace_link_processor).__name__, self._elem_thresh, self._maj_thresh, self._file_thresh, output_suffix), rows)
        
    def _choose_trace_links(self, eval_result_matrix):
        return eval_result_matrix.all_trace_links(self._elem_thresh, self._maj_thresh, self._file_thresh)
    
    @classmethod
    def _default_resulting_tracelinks_csv_filename(cls, dataset, tlp_name, elem_thresh, maj_thresh, file_thresh, output_suffix):
        return all_resulting_tracelinks_csv_filename(dataset, tlp_name, elem_thresh, maj_thresh, file_thresh, output_suffix)

    @classmethod
    def load_resulting_trace_link_csv_into_solutionmatrix(cls, dataset, trace_link_processor_class, elem_thresh, maj_thresh, file_thresh, output_suffix=""):
        trace_link_list = FileUtil.read_csv_to_list(cls._default_resulting_tracelinks_csv_filename(dataset, 
                trace_link_processor_class.__name__, elem_thresh, maj_thresh, file_thresh, output_suffix))
        
        assert trace_link_list[0][0] == cls.HEADER_REQ and trace_link_list[0][1] == cls.HEADER_CODE, "unexpected header"
        sm = SolutionTraceMatrix()
        for req_name, code_name in trace_link_list[1:]:
            sm.add_trace_pair(req_name, code_name)
        return sm
    
class SaveValidTraceLinks(SaveAllTraceLinks):
    def __init__(self, elem_thresh, maj_thresh, file_thresh, precalculated_eval_result_matrix_path=None):
        super(SaveValidTraceLinks, self).__init__(elem_thresh, maj_thresh, file_thresh, precalculated_eval_result_matrix_path)

    def _choose_trace_links(self, eval_result_matrix):
        return eval_result_matrix.valid_trace_links(self._elem_thresh, self._maj_thresh, self._file_thresh)
    
    @classmethod
    def _default_resulting_tracelinks_csv_filename(cls, dataset, tlp_name, elem_thresh, maj_thresh, file_thresh, output_suffix):
        return resulting_valid_tracelinks_csv_filename(dataset, tlp_name, elem_thresh, maj_thresh, file_thresh, output_suffix)
        

            