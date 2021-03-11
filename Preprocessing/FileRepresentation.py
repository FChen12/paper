from Preprocessing.Preprocessor import Preprocessable
import abc
import FileUtil

class FileRepresentation(Preprocessable):
    """
    Tokenized requirement or code files are put in a file representation.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = FileUtil.get_filename_from_path(file_path)
        
    @abc.abstractmethod
    def get_printable_string(self) -> str:
        pass
    
    
    
class TextFileRepresentation(FileRepresentation):
    """
    For requirements.
    token list is a plain list of words or sentences, depending on the tokenizer
    """
    def __init__(self, token_list, file_path):
        self.token_list = token_list
        super(TextFileRepresentation, self).__init__(file_path)
    
    def preprocess(self, preprocessor):
        self.token_list = preprocessor.run_preprocessing(self.token_list, self.file_name)
        self.__clean_up_strings()
    
    def get_printable_string(self):
        return "\n".join(self.token_list)
    
    def __clean_up_strings(self): # Delete any empty strings in the word list
        self.token_list = [word for word in self.token_list if word and not word == ""]
        
class TextFileGroupedRepresentation(FileRepresentation):
    """
    For requirements.
    grouped_token_list is a nested list, e.g. [[sentence1_word1, sentence1_word2], [sentence2_word1, sentence2_word2]}
    """
    def __init__(self, grouped_token_list, file_path):
        self.grouped_token_list = grouped_token_list
        super(TextFileGroupedRepresentation, self).__init__(file_path)
        
    def preprocess(self, preprocessor):
        processed_groups = []
        for group in self.grouped_token_list:
            processed_groups.append(preprocessor.run_preprocessing(group, self.file_name))
        self.grouped_token_list = processed_groups
        self.__clean_up_strings()
    
    def get_printable_string(self):
        return "\n".join([" ".join(g) for g in self.grouped_token_list])
    
    def __clean_up_strings(self): # Delete any empty strings in the word list
        cleaned_groups = []
        for group in self.grouped_token_list:
            cleaned_groups.append([word for word in group if word and not word == ""])
        self.grouped_token_list = [group for group in cleaned_groups if group]
        
class UseCaseFileRepresentation(FileRepresentation):
    
    def __init__(self, file_path, name_words=[], description_words=[], actor_words=[], precondition_words=[],
                  postcondition_words=[], flow_of_events_words=[], quality_requirement_words=[], user_words=[], system_words=[]):
        assert isinstance(name_words, list) and isinstance(description_words, list) and \
                isinstance(actor_words, list) and isinstance(precondition_words, list) and \
                isinstance(postcondition_words, list) and isinstance(flow_of_events_words, list) and \
                isinstance(flow_of_events_words, list) # Needs to be lists to do preprocessing correctly
        self.name_words = name_words
        self.description_words = description_words
        self.actor_words = actor_words
        self.precondition_words = precondition_words
        self.postcondition_words = postcondition_words
        self.flow_of_events_words = flow_of_events_words
        self.quality_requirement_words = quality_requirement_words
        super(UseCaseFileRepresentation, self).__init__(file_path)
        
    def preprocess(self, preprocessor):
        self.name_words = preprocessor.run_preprocessing(self.name_words, self.file_name)
        self.description_words = preprocessor.run_preprocessing(self.description_words, self.file_name)
        self.actor_words = preprocessor.run_preprocessing(self.actor_words, self.file_name)
        self.precondition_words = preprocessor.run_preprocessing(self.precondition_words, self.file_name)
        self.postcondition_words = preprocessor.run_preprocessing(self.postcondition_words, self.file_name)
        self.flow_of_events_words = [preprocessor.run_preprocessing(sentence_words, self.file_name) for sentence_words in self.flow_of_events_words]
        self.quality_requirement_words = preprocessor.run_preprocessing(self.quality_requirement_words, self.file_name)
        self.__clean_up_strings()
    
    def get_printable_string(self):
        print_str = ["UC_NAME || " + "|".join(self.name_words)]
        print_str.append("DESCRIPTION || " + "|".join(self.description_words))
        print_str.append("ACTOR || " + "|".join(self.actor_words))
        print_str.append("PRECOND || " + "|".join(self.precondition_words))
        print_str.append("EVENTFLOW || " + ", ".join(["|".join(sent_group) for sent_group in self.flow_of_events_words]))
        print_str.append("POSTCOND || " + "|".join(self.postcondition_words))
        print_str.append("QUALIREQ || " + "|".join(self.quality_requirement_words))
        return "\n".join(print_str)
        
    
    def __clean_up_strings(self): # Delete any empty strings in the word list
        self.name_words = [word for word in self.name_words if word and not word == ""]
        self.description_words = [word for word in self.description_words if word and not word == ""]
        self.actor_words = [word for word in self.actor_words if word and not word == ""]
        self.precondition_words = [word for word in self.precondition_words if word and not word == ""]
        self.postcondition_words = [word for word in self.postcondition_words if word and not word == ""]
        cleaned_foe = []
        for sent_group in self.flow_of_events_words:
            cleaned_foe.append([word for word in sent_group if word and not word == "" ])
        self.flow_of_events_words = [group for group in cleaned_foe if group]
        self.quality_requirement_words = [word for word in self.quality_requirement_words if word and not word == ""]
