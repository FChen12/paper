import logging, FileUtil, Util, numpy
from Paths import *

log = logging.getLogger(__name__)
class TracePairPrecalculator:
    CODE_FILE_LIST = "code_file_list"
    CODE_FILENAME = "code_filename"
    CODE_ELEMENT_LIST = "code_element_list"
    CODE_ELEMENT = "code_element"
    REQUIREMENT_LIST = "requirement_list"
    REQUIREMENT_FILENAME = "requirement_filename"
    REQUIREMENT_ELEMENT = "requirement_element"
    REQUIREMENT_ELEMENT_LIST = "requirement_element_list"
    SIMILARITY = "similarity"
    
    """
    Class to pre calculate req-element/code-element trace pair similarities and persists it as json file
    to speed up trace link methods with expensive similarity calculations
    """
    
    def calculate_trace_pairs(self, req_dict, code_dict, sim_calculator, output_json_file=None, sim_map_func=None):
        """
        Compares all code elements with all requirement elements, builds a dict from it and persists it as json file.
        
        req_dict: dict whose keys are requirement file names and the entries are their corresponding list of req elements
        code_dict: dict whose keys are code file names and the entries are their corresponding list of code elements 
        sim_calculator: function to calculate the similarity between a req elem and code elem
                        sim_calculator(req_elem, code_elem) -> float
        sim_map_func: function to map the calculated sim value by sim_calculator to a new value, e.g. for normalizing with wmd distances
        
        resulting json file:                
        dict{
        "code_file_list"=
                [dict{
                    code_filename=str,
                    code_element_list=
                            [dict{
                                code_element=str,
                                requirement_list=[
                                    dict{
                                        requirement_filename=str
                                        requirement_element_list=[
                                                dict{
                                                    requirement_element=str
                                                    similarity=float
                                                }
                                        ]
                                    }
                                 ]
                               }
                             ]
                     }
                ]
        }
        """
        
        all_code_files = []
        curr_code_files = []
        total_len = len(code_dict.keys())
        for i, code_file_name in enumerate(code_dict): 
            log.info("code_filename {} of {}".format(i, total_len))
            code_file_entry = dict()
            code_file_entry[self.CODE_FILENAME] = code_file_name
            code_elem_list = code_dict[code_file_name]
            code_elem_entry_list = []
            num_elems = len(code_elem_list)
            for j, code_elem in enumerate(code_elem_list):
                log.info("code element {} of {}".format(j, num_elems))
                code_elem_entry = dict()
                if isinstance(code_elem, numpy.ndarray):
                    # We're working with calculated embeddings -> no need to save the code elem itself
                    code_elem_entry[self.CODE_ELEMENT] =  "N/A"
                else: 
                    code_elem_entry[self.CODE_ELEMENT] =  code_elem
                requirements_entry_list = []
                for req_file_name in req_dict: 
                    requirement_entry = dict()
                    requirement_entry[self.REQUIREMENT_FILENAME] = req_file_name
                    req_elem_list = req_dict[req_file_name]
                    requirement_elem_entry_list = []
                    for req_elem in req_elem_list:
                        requirement_elem_entry = dict()
                        if isinstance(req_elem, numpy.ndarray):
                            # We're working with calculated embeddings -> no need to save the Req elem itself
                            requirement_elem_entry[self.REQUIREMENT_ELEMENT] =  "N/A"
                        else:
                            requirement_elem_entry[self.REQUIREMENT_ELEMENT] = req_elem
                        sim = sim_calculator(req_elem, code_elem)
                        if sim_map_func:
                            sim = sim_map_func(sim)
                        requirement_elem_entry[self.SIMILARITY] = sim
                        requirement_elem_entry_list.append(requirement_elem_entry)
                    requirement_entry[self.REQUIREMENT_ELEMENT_LIST] = requirement_elem_entry_list
                    requirements_entry_list.append(requirement_entry)
                code_elem_entry[self.REQUIREMENT_LIST] = requirements_entry_list
                code_elem_entry_list.append(code_elem_entry)
            code_file_entry[self.CODE_ELEMENT_LIST] = code_elem_entry_list
            all_code_files.append(code_file_entry)
            curr_code_files.append(code_file_entry)
        json_dict = dict()
        json_dict[self.CODE_FILE_LIST] = all_code_files
        if output_json_file:
            FileUtil.write_dict_to_json(output_json_file, json_dict)
        return json_dict
        