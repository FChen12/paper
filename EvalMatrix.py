import FileUtil

"""
Represents the output object of an trace link processor.
Contains the precision/recall/f1 values for all threshold combinations.
An EvalStrategy can take this object to do further evaluation, e.g. average precision calculation
"""
import Util

class EvalMatrix:
    # Keys for json persisting
    EVAL_DATA = "eval_data"
    SOL_MATRIX_SIZE = "sol_matrix_size"
    ELEM_THRESHS = "elem_threshs"
    MAJ_TRHESHS = "maj_threshs"
    FILE_LEVEL_TRHESHS = "file_level_threshs"
    
    def __init__(self, elem_threshs, maj_threshs, file_level_threshs, sol_matrix_size):
        eval_dict = {}
        for elem_thresh in elem_threshs:
            m_thresh_dict = {}
            for m_thresh in maj_threshs:
                drop_thresh_dict = {}
                for d_thresh in file_level_threshs:
                    drop_thresh_dict[d_thresh] = None
                m_thresh_dict[m_thresh] = drop_thresh_dict
            eval_dict[elem_thresh] = m_thresh_dict
        self._eval_data = eval_dict
        self._sol_matrix_size = sol_matrix_size
        self.elem_threshs = elem_threshs
        self.maj_threshs = maj_threshs # Normal maj thresh or absolute top n values
        self.file_level_threshs = file_level_threshs
        
    def add_eval_result(self, elem_th, maj_th, file_th, valid_trace_links, all_trace_links):
        """
        Calculates the precision/recall/f1 value automatically
        """
        if not valid_trace_links:
            self._eval_data[elem_th][maj_th][file_th] = None
        else:
            true_positives = len(valid_trace_links)
            total_num_found_links = len(all_trace_links)
            precision, recall, f_1 = Util.calc_prec_recall_f1(true_positives, total_num_found_links, self._sol_matrix_size)
            print_str = Util.build_prec_recall_f1_print_str(precision, recall, f_1, true_positives, total_num_found_links, self._sol_matrix_size)
            self._eval_data[elem_th][maj_th][file_th] = (recall, precision, f_1, print_str, valid_trace_links, all_trace_links)
        
    def is_none_entry(self, elem_th, maj_th, file_th):
        return self._eval_data[elem_th][maj_th][file_th] is None
    
    def precision(self, elem_th, maj_th, file_th):
        """
        Returns precision of the threshold combi
        """
        return self._eval_data[elem_th][maj_th][file_th][1]
    
    def recall(self, elem_th, maj_th, file_th):
        """
        Returns recall of the threshold combi
        """
        return self._eval_data[elem_th][maj_th][file_th][0]
    
    def f_1(self, elem_th, maj_th, file_th):
        """
        Returns f1 of the threshold combi
        """
        return self._eval_data[elem_th][maj_th][file_th][2]
    
    def print_str(self, elem_th, maj_th, file_th):
        """
        Returns the printable string of the threshold combi
        """
        if self.is_none_entry(elem_th, maj_th, file_th):
            return "No trace links"
        return self._eval_data[elem_th][maj_th][file_th][3]
    
    
    def valid_trace_links(self, elem_th, maj_th, file_th):
        """
        Returns the valid (resulting) tracelinks of the threshold combi
        """
        return self._eval_data[elem_th][maj_th][file_th][4]
    
    def all_trace_links(self, elem_th, maj_th, file_th):
        """
        Returns all tracelinks of the threshold combi
        """
        return self._eval_data[elem_th][maj_th][file_th][5]
    
    def _set_data(self, elem_th, maj_th, file_th, data):
        self._eval_data[elem_th][maj_th][file_th] = data
        
    def write_eval_result_matrix_to_file(self, file_path):
        """
        Writes this object to a json file
        """
        complete_dict = {}
        json_compatible_eval_data = {}
        for elem_thresh in self.elem_threshs:
            m_thresh_dict = {}
            for m_thresh in self.maj_threshs:
                drop_thresh_dict = {}
                for d_thresh in self.file_level_threshs:
                    if self.is_none_entry(elem_thresh, m_thresh, d_thresh):
                        drop_thresh_dict[d_thresh] = "None"
                    else:
                        drop_thresh_dict[d_thresh] = self._eval_data[elem_thresh][m_thresh][d_thresh]
                m_thresh_dict[m_thresh] = drop_thresh_dict
            json_compatible_eval_data[elem_thresh] = m_thresh_dict
            
        complete_dict[self.EVAL_DATA] = json_compatible_eval_data
        complete_dict[self.SOL_MATRIX_SIZE] = self._sol_matrix_size
        complete_dict[self.ELEM_THRESHS] = self.elem_threshs
        complete_dict[self.MAJ_TRHESHS] = self.maj_threshs
        complete_dict[self.FILE_LEVEL_TRHESHS] = self.file_level_threshs
        
        FileUtil.write_dict_to_json(file_path, complete_dict)
        
    @classmethod
    def load_eval_result_matrix_from_file(cls, file_path):
        """
        loads an evalMatrix from an json file
        """
        complete_dict = FileUtil.read_dict_from_json(file_path)
        instance = cls(complete_dict[cls.ELEM_THRESHS], complete_dict[cls.MAJ_TRHESHS], complete_dict[cls.FILE_LEVEL_TRHESHS], complete_dict[cls.SOL_MATRIX_SIZE])
        eval_data = complete_dict[cls.EVAL_DATA]
        for elem_thresh in instance.elem_threshs:
            for m_thresh in instance.maj_threshs:
                for d_thresh in instance.file_level_threshs:
                    if eval_data[str(elem_thresh)][str(m_thresh)][str(d_thresh)] == "None":
                        instance._set_data(elem_thresh, m_thresh, d_thresh, None)
                    else:
                        instance._set_data(elem_thresh, m_thresh, d_thresh, eval_data[str(elem_thresh)][str(m_thresh)][str(d_thresh)])
        return instance