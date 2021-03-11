import FileUtil, pandas
from sklearn.feature_extraction.text import TfidfVectorizer
import Paths
import Util

class TFIDFData:
    
    def __init__(self, precalculated_file_path):
        self._file_path = precalculated_file_path
        self._tfidf_dataframe = FileUtil.read_csv_to_dataframe(precalculated_file_path)
    
    def contains_file_name(self, file_name):
        return file_name in self._tfidf_dataframe.index
    
    def get_weight(self, file_name, word):
        return self._tfidf_dataframe.loc[file_name, word]
    
    def get_vector(self, file_name):
        return self._tfidf_dataframe.loc[file_name].tolist()
        
    
    
class TFIDFPrecalculator:
    
    def __init__(self):
        self._tfIdfVectorizer = TfidfVectorizer()
        
    def precalculate_and_write(self, file_contents: [str], file_names: [str], output_filename):
        """
        file_contents = list of content strings of all files
        file_names = list of all file names
        output_filename = name of the file with the precalculated weights
        
        The file content and its corresponding file name must have the same index in both lists
        """
        assert len(file_contents) == len(file_names)
        table = self._tfIdfVectorizer.fit_transform(file_contents)
        df = pandas.DataFrame(table.todense(), index=file_names, columns=self._tfIdfVectorizer.get_feature_names())
        FileUtil.write_dataframe_to_csv(df, output_filename)
        
class TFIDFCosSimPrecalculator:
    
    @classmethod
    def precalculate(cls, dataset, req_word_chooser, code_word_chooser, output_vector_file=None, output_sim_file=None, output_suffix=""):
        if not output_vector_file:
            output_vector_file = Paths.precalculated_req_code_tfidf_vectors_filename(dataset, type(req_word_chooser).__name__, type(code_word_chooser).__name__, output_suffix)
        
        if not output_sim_file:
            output_sim_file = Paths.precalculated_req_code_tfidf_cos_sim_filename(dataset, type(req_word_chooser).__name__, type(code_word_chooser).__name__, output_suffix)
        file_contents, req_file_names, code_file_names = [], [], []
        
        for file in FileUtil.get_files_in_directory(dataset.req_folder()):
            file_contents.append(" ".join(req_word_chooser.get_words(file)))
            req_file_names.append(FileUtil.get_filename_from_path(file))
        for file in FileUtil.get_files_in_directory(dataset.code_folder()):
            file_contents.append(" ".join(code_word_chooser.get_words(file)))
            code_file_names.append(FileUtil.get_filename_from_path(file))
            
        TFIDFPrecalculator().precalculate_and_write(file_contents, req_file_names + code_file_names, output_vector_file)
        t = TFIDFData(output_vector_file)
        df = pandas.DataFrame(None, index=req_file_names, columns=code_file_names)
        for req_file_name in req_file_names:
            for code_file_name in code_file_names:
                df.at[req_file_name, code_file_name] = Util.calculate_cos_sim(t.get_vector(req_file_name), t.get_vector(code_file_name))
        FileUtil.write_dataframe_to_csv(df, output_sim_file)

