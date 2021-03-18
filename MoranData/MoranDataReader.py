import FileUtil, logging
logging.basicConfig(level=logging.INFO, 
                    handlers=[logging.FileHandler("log_output.log", mode='w'), logging.StreamHandler()])
from TraceLink import TraceLink
from Embedding import MockEmbedding
import Evaluator
import Paths
from Dataset import Etour308, Libest, Smos, Itrust
import Util

log = logging.getLogger(__name__)

def eval_moran_data(file_path, dataset, drop_threshs):
    trace_links = extract_moran_trace_links(file_path)
    eval_result_list = eval_moran_data_multiple_thresh(trace_links, dataset, drop_threshs)
    best_f1 = 0
    best_print_str = "No best"
    best_thresh = None
    for precision, recall, f_1, print_str, thresh in eval_result_list:
        log.info(f"\n drop_thresh={thresh}:\n" + print_str + "\n")
        if f_1 > best_f1:
            best_f1 = f_1
            best_print_str = print_str
            best_thresh = thresh
    log.info(f"\nBest f1 at {best_thresh}: \n{best_print_str}")
    
def eval_moran_data_multiple_thresh(trace_links, dataset, drop_threshs):
    return [(*eval_moran_data_at_thresh(trace_links, dataset, thresh), thresh)  for thresh in drop_threshs]
        
def eval_moran_data_at_thresh(trace_links, dataset, drop_thresh):
    trace_links = [link for link in trace_links if link.similarity > drop_thresh]
    precision, recall, f_1, print_str = Evaluator.evaluate_and_calc_metrics(trace_links, dataset.solution_matrix())
    return precision, recall, f_1, print_str

def extract_moran_trace_links(file_path):
    lines = FileUtil.read_textfile_into_lines_list(file_path)
    lines = lines[6:] # first 6 lines contain no similarity data
    trace_links = []
    for line in lines:
        req, code, sim = line.split(" ")
        code = _remove_package(code)
        if code.endswith(".jsp") or  code.endswith(".txt"):
            continue
        sim = float(sim)
        trace_links.append(TraceLink(MockEmbedding(_lowercase_extension(req)), MockEmbedding(_lowercase_extension(code)), sim))
    return trace_links
            
def _remove_package(name):
    if name.count(".") > 1:
        parts = name.split(".")
        name = parts[-2] + "." + parts[-1]
    return name
def _lowercase_extension(file_name):
    name, ext = file_name.split(".")
    return name + "." + ext.lower()

def convert_moran_to_recall_prec_csv(file_path, dataset, drop_threshs, output_file_name):
    trace_links = extract_moran_trace_links(file_path)
    eval_result_list = eval_moran_data_multiple_thresh(trace_links, dataset, drop_threshs, dataset.keys_with_extension())
    recall_prec_dict = {}
    for precision, recall, f_1, print_str, thresh in eval_result_list:
        recall_prec_dict[recall] = precision
    
    FileUtil.write_recall_precision_csv(recall_prec_dict, output_file_name)
    log.info(f"Integral Average Precision: {Util.calculate_discrete_integral_average_precision(recall_prec_dict)}")
    
def calculate_moran_mean_avg_prec(file_path, dataset, k):
    """
    MAP@k
    """
    trace_links = extract_moran_trace_links(file_path)
    map, num_distinct_links = Evaluator.evaluateMAP(trace_links, k, dataset, False)
    log.info(f"Mean Average Precision @ {k}: {map} with {num_distinct_links} distinct links")
   
   
#calculate_moran_mean_avg_prec(Paths.ROOT / "MoranData/results_RQ1_eTour_MAP.tm", Etour308(True), None) 
#calculate_moran_mean_avg_prec(Paths.ROOT / "MoranData/results_RQ1_SMOS_VI.tm", Smos(), 1) 



#eval_moran_data(Paths.ROOT / "MoranData/results_RQ1_iTrust_MAP.tm", Itrust(), Util.get_range_array(0, 1, 0.01))
#convert_moran_to_recall_prec_csv(Paths.ROOT / "MoranData/results_RQ1_SMOS_MAP.tm", Smos(), Util.get_range_array(0, 1, 0.01), "moran_libest_vi.csv")
#convert_moran_to_recall_prec_csv(Paths.ROOT / "MoranData/results_RQ1_SMOS_VI.tm", Smos(), Util.get_range_array(0, 1, 0.01), "moran_libest_map.csv")
#convert_moran_to_recall_prec_csv(Paths.ROOT / "MoranData/results_RQ1_SMOS_NUTS.tm", Smos(), Util.get_range_array(0, 1, 0.01), "moran_libest_nuts.csv")

     
    