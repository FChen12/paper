from CodeEmbeddingCreator.CodeEmbeddingCreator import CodeEmbeddingCreator
import abc, Util
from Embedding import MethodCallGraphEmbedding
from Preprocessing.CallGraphUtil import build_method_param_dict_key

"""
CodeEmbeddingCreators for embeddings with call dependencies

"""

class MethodCallGraphEmbeddingCreator(CodeEmbeddingCreator):
    
    def _create_embeddings(self, file_representation):
        code_embeddings = []
        for classifier in file_representation.classifiers:
            methods_dict = {}
            for method in classifier.methods:
                method_vector = self._calculate_method_vector(classifier, method)
                if method_vector is None:
                    continue
                methods_dict[build_method_param_dict_key(method.get_original_name(),
                                                          method.get_original_param_type_list())] = method_vector
            if methods_dict:
                code_embeddings.append(MethodCallGraphEmbedding(file_representation.file_path, classifier.get_original_name(),
                                                             methods_dict))
        return code_embeddings
               
                
    @abc.abstractmethod
    def _calculate_method_vector(self, classifier, method):
        pass
    
    
class MethodSignatureCallGraphEmbeddingCreator(MethodCallGraphEmbeddingCreator):
    
    def _calculate_method_vector(self, classifier, method):
        method_words = classifier.get_name_words()
        method_words += method.get_name_words()
        method_words += method.get_returntype_words()
        method_words += method.get_param_plain_list()
        return Util.create_averaged_vector(self._create_word_embeddings_from_word_list(method_words, self._is_ital_identifier))
    
class MethodCommentSignatureCallGraphEmbeddingCreator(MethodCallGraphEmbeddingCreator):
    
    def _calculate_method_vector(self, classifier, method):
        method_words = classifier.get_name_words()
        method_words += method.get_name_words()
        method_words += method.get_returntype_words()
        method_words += method.get_param_plain_list()
        method_subvectors = self._create_word_embeddings_from_word_list(method_words, self._is_ital_identifier)
        method_subvectors += self._create_word_embeddings_from_word_list(method.get_comment_tokens(), self._is_ital_comm)
        return Util.create_averaged_vector(method_subvectors)