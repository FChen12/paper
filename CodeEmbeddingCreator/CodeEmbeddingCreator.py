import logging, Util
from EmbeddingCreator import EmbeddingCreator
from WordEmbeddingCreator.WordEmbeddingCreator import MockWordEmbeddingCreator,\
    FastTextAlignedEngItalEmbeddingCreator
from Preprocessing.CodeASTTokenizer import JavaCodeASTTokenizer
from Preprocessing.Preprocessor import Preprocessor, CamelCaseSplitter,\
    LowerCaseTransformer, NonLetterFilter, UrlRemover, Separator,\
    JavaCodeStopWordRemover, StopWordRemover, Lemmatizer, WordLengthFilter
from Embedding import CodeEmbedding
from Paths import *
from Preprocessing.CodeFileRepresentation import Enum_
import FileUtil
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas
import Paths
from Dataset import Etour308
from builtins import isinstance
from pandas.core.arrays import integer
import numpy
from TFIDFData import TFIDFData, TFIDFPrecalculator

log = logging.getLogger(__name__ )
logging.basicConfig(level=logging.INFO)
class CodeEmbeddingCreator(EmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
                  tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(CodeEmbeddingCreator, self).__init__(preprocessor, wordemb_creator,
                                                    tokenizer, preprocessed_token_output_directory)
        self._is_ital_identifier = False
        self._is_ital_comm = False
        if isinstance(wordemb_creator, FastTextAlignedEngItalEmbeddingCreator):
            self._is_ital_comm = True
            
    
class IdentifierEmbeddingCreator(CodeEmbeddingCreator):
    """
    Super class for the combinations of different class elements for cos sim class embeddings or majority decision
    Modify boolean attributes in sub classes to create new combinations
    """
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = False
        self._with_attribute = False
        self._with_attribute_comment_to_attr = False
        self._with_attribute_comment_to_class = False
        self._with_method = True
        self._with_method_comment_to_method = False
        self._with_method_comment_to_class= False
        self._with_method_body_to_method = False
        self._with_method_body_to_class = False
        self._with_class_name_to_method = True
        self._with_inner_classifier = False
        self._average_function = Util.create_averaged_vector # function that maps multiple vectors to one
        
        super(IdentifierEmbeddingCreator, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
    def _embedd_and_average(self, word_list, ital):
        word_embd = self._map_to_emb(word_list, ital)
        return [self._average_function(word_embd)] if word_embd else []
    
    def _map_to_emb(self, word_list, ital):
        return self._create_word_embeddings_from_word_list(word_list, ital)
    
    def _create_embeddings(self, file_representation):
        code_embeddings = []
        for classifier in file_representation.classifiers:
            partial_class_embeddings = []
            if self._with_class_name:
                class_name = classifier.get_name_words()
                if class_name:
                    partial_class_embeddings = self._embedd_and_average(class_name, self._is_ital_identifier)
            if self._with_super_classifier:
                super_cls = classifier.get_super_classifiers_plain_list()
                if super_cls:
                    partial_class_embeddings += self._embedd_and_average(super_cls, self._is_ital_identifier)
            if self._with_class_comment:
                class_comment = classifier.get_comment_tokens()
                if class_comment:
                    partial_class_embeddings += self._embedd_and_average(class_comment, self._is_ital_comm)
            if self._with_attribute_comment_to_class:
                for attr in classifier.attributes:
                    attr_comment = attr.get_comment_tokens()
                    if attr_comment:
                        partial_class_embeddings += self._embedd_and_average(attr_comment, self._is_ital_comm)
            if self._with_method_comment_to_class:
                for method in classifier.methods:
                    method_comment = method.get_comment_tokens()
                    if method_comment:
                        partial_class_embeddings += self._embedd_and_average(method_comment, self._is_ital_comm)
            if self._with_method_body_to_class:
                for method in classifier.methods:
                    method_body = method.get_body_words()
                    if method_body:
                        partial_class_embeddings += self._embedd_and_average(method_body, self._is_ital_identifier)
            if self._with_attribute:
                for attr in classifier.attributes:
                    attr_words = attr.get_attribute_plain_list()
                    attr_comm_emb = []
                    if self._with_attribute_comment_to_attr:
                        attr_comm = attr.get_comment_tokens()
                        attr_comm_emb = self._map_to_emb(attr_comm, self._is_ital_comm)
                        
                    if isinstance(classifier, Enum_): #Treat enum constants as attributes
                        attr_words += classifier.get_constant_words()
                    attr_all_emb = self._map_to_emb(attr_words, self._is_ital_identifier) + attr_comm_emb
                    partial_class_embeddings += [self._average_function(attr_all_emb)] if attr_all_emb else []
            if self._with_method:
                for method in classifier.methods:
                    method_words = []
                    if self._with_class_name_to_method:
                        method_words = classifier.get_name_words()
                    method_words += method.get_name_words()
                    method_words += method.get_returntype_words()
                    method_words += method.get_param_plain_list()
                    
                    method_comment_word_emb = []
                    if self._with_method_comment_to_method:
                        method_comment_words = method.get_comment_tokens()
                        method_comment_word_emb = self._map_to_emb(method_comment_words, self._is_ital_comm)
                    if self._with_method_body_to_method:
                        method_words += method.get_body_words()
                    
                    method_all_emb = self._map_to_emb(method_words, self._is_ital_identifier) + method_comment_word_emb
                    
                    partial_class_embeddings += [self._average_function(method_all_emb)] if method_all_emb else []
                    
            if self._with_inner_classifier:
                for i_classif in classifier.inner_classifiers:
                    inner_classif_words = i_classif.get_name_words()
                    inner_classif_comm_words = i_classif.get_comment_tokens()
                    for attr in i_classif.attributes:
                        inner_classif_words += attr.get_attribute_plain_list()
                        inner_classif_comm_words += attr.get_comment_tokens()
                    for method in i_classif.methods:
                        inner_classif_words += method.get_name_words()
                        inner_classif_words += method.get_returntype_words()
                        inner_classif_words += method.get_param_plain_list()
                        #Ignore method bodies
                        inner_classif_comm_words += method.get_comment_tokens()
                    if isinstance(i_classif, Enum_):
                        inner_classif_words += i_classif.get_constant_words()
                    # Ignore potential inner classifiers of inner classifiers
                    i_classif_word_emb = self._map_to_emb(inner_classif_words, self._is_ital_identifier)
                    comment_word_emb = self._map_to_emb(inner_classif_comm_words, self._is_ital_comm)
                    all_i_classif_emb = comment_word_emb + i_classif_word_emb
                    partial_class_embeddings += [self._average_function(all_i_classif_emb)] if all_i_classif_emb else []
                            
            if partial_class_embeddings:
                code_emb = CodeEmbedding(file_representation.file_path, 
                                        self._average_function(partial_class_embeddings), partial_class_embeddings)
                code_emb.class_name = classifier.name
                code_embeddings.append(code_emb)
        
        return code_embeddings


class IdentifierEmbeddingCreatorWithMethodBody(IdentifierEmbeddingCreator):
    
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodBody, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
        self._with_class_name = True
        self._with_method = True
        self._with_method_body_to_method = True
        self._with_class_name_to_method = True
    

            

class IdentifierEmbeddingCreatorWithMethodComment(IdentifierEmbeddingCreator):
    
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodComment, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_class_name_to_method = True
      
class IdentifierEmbeddingCreatorWithMethodCommentAndBody(IdentifierEmbeddingCreator):
    
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodCommentAndBody, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_method_body_to_method = True
        self._with_class_name_to_method = True
    
class IdentifierEmbeddingCreatorWithSuperClassifier(IdentifierEmbeddingCreator):
    
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithSuperClassifier, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
        self._with_class_name = True
        self._with_method = True
        self._with_super_classifier = True
        self._with_class_name_to_method = True
         
class IdentifierEmbeddingCreatorWithClassComment(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithClassComment, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = True
        self._with_method = True
        self._with_class_name_to_method = True
        
        
class IdentifierEmbeddingCreatorCommentToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorCommentToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = True
        self._with_method = True
        self._with_method_comment_to_class= True
        self._with_class_name_to_method = True
        

class IdentifierEmbeddingCreatorOnlyCommentsAndClassName(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorOnlyCommentsAndClassName, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = True
        self._with_method = False
        self._with_method_comment_to_method = False
        self._with_method_comment_to_class= True
        self._with_method_body_to_method = False
        self._with_method_body_to_class = False
        self._with_class_name_to_method = False
        
class IdentifierEmbeddingCreatorEverything(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorEverything, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = True
        self._with_class_comment = True
        self._with_attribute = True
        self._with_attribute_comment_to_attr = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_method_comment_to_class= True
        self._with_method_body_to_method = True
        self._with_method_body_to_class = True
        self._with_class_name_to_method = True
        self._with_inner_classifier = True
        
class IdentifierEmbeddingCreatorWithMethodBodyToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodBodyToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_body_to_class = True
        self._with_class_name_to_method = True
        
class IdentifierEmbeddingCreatorWithMethodCommentToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodCommentToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_comment_to_class= True
        self._with_class_name_to_method = True
        
class IdentifierEmbeddingCreatorWithMethodBodyAndCommentToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorWithMethodBodyAndCommentToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_comment_to_class= True
        self._with_method_body_to_class = True
        self._with_class_name_to_method = True
        
class IdentifierEmbeddingCreatorEverythingToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorEverythingToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = True
        self._with_class_comment = True
        self._with_attribute = True
        self._with_attribute_comment_to_class = True
        self._with_method = True
        self._with_method_comment_to_class= True
        self._with_method_body_to_class = True
        self._with_class_name_to_method = True
        self._with_inner_classifier = True
        
class IdentifierEmbeddingCreatorCommentBodyToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorCommentBodyToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = True
        self._with_method = True
        self._with_method_comment_to_class= True
        self._with_method_body_to_class = True
        self._with_class_name_to_method = True
        
class IdentifierEmbeddingOnlyMethods(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingOnlyMethods, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = False
        
class IdentifierEmbeddingOnlyClassNameAndComment(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingOnlyClassNameAndComment, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_comment = True
        self._with_method = False
        self._with_class_name_to_method = False
        
        self._with_attribute = False
        self._with_attribute_comment_to_attr = False
        self._with_attribute_comment_to_class = False
        
        
class IdentifierEmbeddingWithAttribute(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingWithAttribute, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
        self._with_attribute = True
        
        
class IdentifierEmbeddingWithAttributeComment(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingWithAttributeComment, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
        self._with_attribute = True
        self._with_attribute_comment_to_attr = True
        
class IdentifierEmbeddingWithAttributeCommentToClass(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingWithAttributeCommentToClass, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
        self._with_attribute = True
        self._with_attribute_comment_to_class = True
        
class ClassIdentifierEmbeddingCreator(CodeEmbeddingCreator):
    """
    Take all words in a code file and average (flat average)
    """
    def _create_embeddings(self, file_representation):
        
        class_embeddings = []
        for classifier in file_representation.classifiers:
            identif_words, comm_words = self._get_all_words_in_classifiers(classifier)
            identif_vectors = self._create_word_embeddings_from_word_list(identif_words, self._is_ital_identifier)
            comm_vectors = self._create_word_embeddings_from_word_list(comm_words, self._is_ital_comm)
            all_vectors = identif_vectors + comm_vectors
            code_emb = CodeEmbedding(file_representation.file_path, 
                                     Util.create_averaged_vector(all_vectors), all_vectors)
            code_emb.class_name = classifier.name
            class_embeddings.append(code_emb)
        return class_embeddings
    
    def _get_all_words_in_classifiers(self, classifier):
        all_identifiers_in_class = set()
        all_comm_in_class = set()
        all_identifiers_in_class.update(classifier.get_name_words())
        all_identifiers_in_class.update(classifier.get_super_classifiers_plain_list())
        all_comm_in_class.update(classifier.get_comment_tokens())
        for attr in classifier.attributes:
            all_comm_in_class.update(attr.get_comment_tokens())
            all_identifiers_in_class.update(attr.get_attribute_plain_list())
        for meth in classifier.methods:
            all_identifiers_in_class.update(meth.get_name_words())
            all_identifiers_in_class.update(meth.get_param_plain_list())
            all_identifiers_in_class.update(meth.get_returntype_words())
            all_comm_in_class.update(meth.get_comment_tokens())
            all_identifiers_in_class.update(meth.get_body_words())
        if isinstance(classifier, Enum_):
            all_identifiers_in_class.update(classifier.get_constant_words())
        for i_classif in classifier.inner_classifiers:
            i_word, i_comm = self._get_all_words_in_classifiers(i_classif)
            all_identifiers_in_class.update(i_word)
            all_comm_in_class.update(i_comm)
        return all_identifiers_in_class, all_comm_in_class
    
class IdentifierEmbeddingCreatorMethodAndComments(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorMethodAndComments, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = False
        self._with_class_comment = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_method_comment_to_class= False
        self._with_method_body_to_method = False
        self._with_method_body_to_class = False
        self._with_class_name_to_method = True
        
class IdentifierEmbeddingCreatorMethodCommentsSuperclassifier(IdentifierEmbeddingCreator):
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(IdentifierEmbeddingCreatorMethodCommentsSuperclassifier, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_super_classifier = True
        self._with_class_comment = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_method_comment_to_class= False
        self._with_method_body_to_method = False
        self._with_method_body_to_class = False
        self._with_class_name_to_method = True
        
class MethodNameSentenceEmbeddingCreator(CodeEmbeddingCreator):
    """
    Use this for BERT embeddings (creates sentences out of method signatures and class names)
    """
    def __init__(self, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
       
        super(MethodNameSentenceEmbeddingCreator, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        
    def _create_embeddings(self, file_representation):
        code_embeddings = []   
        for classifier in file_representation.classifiers:
            partial_class_embeddings = []
            for method in classifier.methods:
                    method_words = classifier.get_name_words() + method.get_name_words()
                    if method_words:
                        method_words = " ".join(method_words) + "." # create artificial sentence
                        partial_class_embeddings.append(self._create_word_embedding(method_words))
            if partial_class_embeddings:
                code_emb = CodeEmbedding(file_representation.file_path, 
                                        Util.create_averaged_vector(partial_class_embeddings), partial_class_embeddings)
                code_embeddings.append(code_emb)
        return code_embeddings


class TFIDFIdentifierEmbeddingCreator(IdentifierEmbeddingCreator):
    """
    Super class for the combinations of different class elements for cos sim class embeddings or majority decision
    Modify boolean attributes in sub classes to create new combinations
    """
    def __init__(self, precalculated_weights_file, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        
        super(TFIDFIdentifierEmbeddingCreator, self).__init__(preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
                
        if not precalculated_weights_file:
            log.info("No precalculated weights file read")
        else:
            self._tf_idf_data = TFIDFData(precalculated_weights_file)
        

    def _create_embeddings(self, file_representation):
        code_embeddings = []
        for classifier in file_representation.classifiers:
            class_embedding = 0 # used for file level mapping
            total_class_embeddings_weights = 0
            sub_vectors = [] # used for majority decision
            if self._with_class_name:
                class_name = classifier.get_name_words()
                sub_vector = 0
                total_sub_vector_weight = 0
                for word in class_name:
                    weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                    weighted_emb = weight * self._create_word_embedding_2(word, False)
                    class_embedding += weighted_emb
                    sub_vector += weighted_emb
                    total_sub_vector_weight += weight
                sub_vector /= total_sub_vector_weight # normalize
                sub_vectors.append(sub_vector)
                total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_super_classifier:
                super_cls = classifier.get_super_classifiers_plain_list()
                sub_vector = 0
                total_sub_vector_weight = 0
                for word in super_cls:
                    weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                    weighted_emb = weight * self._create_word_embedding_2(word, False)
                    class_embedding += weighted_emb
                    sub_vector += weighted_emb
                    total_sub_vector_weight += weight
                sub_vector /= total_sub_vector_weight # normalize
                sub_vectors.append(sub_vector)
                total_class_embeddings_weights += total_sub_vector_weight
                
            if self._with_class_comment:
                class_comment = classifier.get_comment_tokens()
                sub_vector = 0
                total_sub_vector_weight = 0
                for word in class_comment:
                    weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                    weighted_emb = weight * self._create_word_embedding_2(word, False)
                    class_embedding += weighted_emb
                    sub_vector += weighted_emb
                    total_sub_vector_weight += weight
                sub_vector /= total_sub_vector_weight # normalize
                sub_vectors.append(sub_vector)
                total_class_embeddings_weights += total_sub_vector_weight
                
            if self._with_attribute_comment_to_class:
                for attr in classifier.attributes:
                    attr_comment = attr.get_comment_tokens()
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in attr_comment:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_method_comment_to_class:
                for method in classifier.methods:
                    method_comment = method.get_comment_tokens()
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in method_comment:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_method_body_to_class:
                for method in classifier.methods:
                    method_body = method.get_body_words()
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in method_body:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_attribute:
                for attr in classifier.attributes:
                    attr_words = attr.get_attribute_plain_list()
                    if self._with_attribute_comment_to_attr:
                        attr_words += attr.get_comment_tokens()
                        
                    if isinstance(classifier, Enum_): #Treat enum constants as attributes
                        attr_words += classifier.get_constant_words()
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in attr_words:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_method:
                for method in classifier.methods:
                    method_words = []
                    if self._with_class_name_to_method:
                        method_words = classifier.get_name_words()
                    method_words += method.get_name_words()
                    method_words += method.get_returntype_words()
                    method_words += method.get_param_plain_list()
                    
                    if self._with_method_comment_to_method:
                        method_words += method.get_comment_tokens()
                    if self._with_method_body_to_method:
                        method_words += method.get_body_words()
                    
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in method_words:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                    
            if self._with_inner_classifier:
                for i_classif in classifier.inner_classifiers:
                    inner_classif_words = i_classif.get_name_words()
                    inner_classif_words += i_classif.get_comment_tokens()
                    for attr in i_classif.attributes:
                        inner_classif_words += attr.get_attribute_plain_list()
                        inner_classif_words += attr.get_comment_tokens()
                    for method in i_classif.methods:
                        inner_classif_words += method.get_name_words()
                        inner_classif_words += method.get_returntype_words()
                        inner_classif_words += method.get_param_plain_list()
                        #Ignore method bodies
                        inner_classif_words += method.get_comment_tokens()
                    if isinstance(i_classif, Enum_):
                        inner_classif_words += i_classif.get_constant_words()
                    # Ignore potential inner classifiers of inner classifiers
                    
                    sub_vector = 0
                    total_sub_vector_weight = 0
                    for word in inner_classif_words:
                        weight = self._tf_idf_data.get_weight(FileUtil.get_filename_from_path(file_representation.file_path), word)
                        weighted_emb = weight * self._create_word_embedding_2(word, False)
                        class_embedding += weighted_emb
                        sub_vector += weighted_emb
                        total_sub_vector_weight += weight
                    sub_vector /= total_sub_vector_weight # normalize
                    sub_vectors.append(sub_vector)
                    total_class_embeddings_weights += total_sub_vector_weight
                            
            if isinstance(class_embedding, numpy.ndarray) and numpy.any(class_embedding):# class_embedding is a nonzero vector
                class_embedding /= total_class_embeddings_weights # normalize
                code_emb = CodeEmbedding(file_representation.file_path, class_embedding, sub_vectors)
                code_emb.class_name = classifier.name
                code_embeddings.append(code_emb)
        
        return code_embeddings
    
    def precalculate_weights(self, dataset, output_filename=None):
        all_files = FileUtil.get_files_in_directory(dataset.code_folder())
        file_names = []
        file_contents = []
        for file in all_files:
            content = []
            file_representation = self._tokenize_and_preprocess(file)
            for classifier in file_representation.classifiers:
                if self._with_class_name or self._with_class_name_to_method:
                    content += classifier.get_name_words()
                if self._with_super_classifier:
                    content += classifier.get_super_classifiers_plain_list()
                if self._with_class_comment:
                    content += classifier.get_comment_tokens()
                if self._with_attribute_comment_to_class or self._with_attribute_comment_to_attr:
                    for attr in classifier.attributes:
                        content += attr.get_comment_tokens()
                if self._with_method_comment_to_class or self._with_method_comment_to_method:
                    for method in classifier.methods:
                        content += method.get_comment_tokens()
                if self._with_method_body_to_class or self._with_method_body_to_method:
                    for method in classifier.methods:
                        content += method.get_body_words()
                if self._with_attribute:
                    for attr in classifier.attributes:
                        content += attr.get_attribute_plain_list()
                    if isinstance(classifier, Enum_): #Treat enum constants as attributes
                        content += classifier.get_constant_words()
                if self._with_method:
                    for method in classifier.methods:
                        content += method.get_name_words()
                        content += method.get_returntype_words()
                        content += method.get_param_plain_list()
                        
                if self._with_inner_classifier:
                    for i_classif in classifier.inner_classifiers:
                        content += i_classif.get_name_words()
                        content += i_classif.get_comment_tokens()
                        for attr in i_classif.attributes:
                            content += attr.get_attribute_plain_list()
                            content += attr.get_comment_tokens()
                        for method in i_classif.methods:
                            content += method.get_name_words()
                            content += method.get_returntype_words()
                            content += method.get_param_plain_list()
                            #Ignore method bodies
                            content += method.get_comment_tokens()
                        if isinstance(i_classif, Enum_):
                            content += i_classif.get_constant_words()
                        # Ignore potential inner classifiers of inner classifiers
            content = " ".join(content)
            if content and not content.isspace():
                file_contents.append(content)
                file_names.append(FileUtil.get_filename_from_path(file_representation.file_path))
            
        if not output_filename:
            output_filename = Paths.precalculated_tfidf_weights_filename(dataset, self.__class__.__name__)
        TFIDFPrecalculator().precalculate_and_write(file_contents, file_names, output_filename)
        
    @classmethod
    def default_precalculated_weights_file(cls, dataset):
        return Paths.precalculated_tfidf_weights_filename(dataset, cls.__name__)
        
        
class TFIDFIdentifierEmbeddingCreatorWithMethodComment(TFIDFIdentifierEmbeddingCreator):
    
    def __init__(self, precalculated_weights_file, preprocessor=Preprocessor(), wordemb_creator=MockWordEmbeddingCreator(),
              tokenizer=JavaCodeASTTokenizer(None, None), preprocessed_token_output_directory=PREPROCESSED_CODE_OUTPUT_DIR): 
        super(TFIDFIdentifierEmbeddingCreatorWithMethodComment, self).__init__(precalculated_weights_file, preprocessor, wordemb_creator,
                                                tokenizer, preprocessed_token_output_directory)
        self._with_class_name = True
        self._with_method = True
        self._with_method_comment_to_method = True
        self._with_class_name_to_method = True
        
CAMEL = CamelCaseSplitter()
LOWER = LowerCaseTransformer()
LETTER = NonLetterFilter()
URL = UrlRemover()
SEP = Separator()
JAVASTOP = JavaCodeStopWordRemover()
STOP = StopWordRemover()
LEMMA = Lemmatizer()
W_LENGTH = WordLengthFilter(2) # Remove everthing that is smaller equal length 2
CODE_PREPROCESSOR = Preprocessor([URL, SEP, LETTER, CAMEL, JAVASTOP, LOWER, LEMMA, STOP, W_LENGTH])

#TFIDFIdentifierEmbeddingCreator(None, CODE_PREPROCESSOR).precalculate_weights(Etour308())
#TFIDFIdentifierEmbeddingCreatorWithMethodComment(None, CODE_PREPROCESSOR).precalculate_weights(Etour308())