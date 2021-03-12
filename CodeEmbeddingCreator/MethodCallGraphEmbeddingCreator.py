from CodeEmbeddingCreator.CodeEmbeddingCreator import CodeEmbeddingCreator
import abc, Util
from Embedding import MethodCallGraphEmbedding,\
    MethodCallGraphEmbeddingMultipleSims
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
                code_embeddings.append(MethodCallGraphEmbeddingMultipleSims(file_representation.file_path, classifier.get_original_name(),
                                                             methods_dict))
            elif classifier.get_name_words():
                class_name_vectors = self._create_word_embeddings_from_word_list(classifier.get_name_words(), False)
                if class_name_vectors:
                    aggregated_cls_name_vector = Util.create_averaged_vector(class_name_vectors)
                    
                    meth_embedding = MethodCallGraphEmbeddingMultipleSims(file_representation.file_path, classifier.get_original_name(), {})
                    meth_embedding.non_cg_dict = {MethodCallGraphEmbedding.CLASS_NAME_VOTER: aggregated_cls_name_vector}
                    
                    code_embeddings.append(meth_embedding)
                
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
        return Util.create_averaged_vector(self._create_word_embeddings_from_word_list(method_words, False))
    
class MethodCommentSignatureCallGraphEmbeddingCreator(MethodCallGraphEmbeddingCreator):
    
    def _calculate_method_vector(self, classifier, method):
        method_words = classifier.get_name_words()
        method_words += method.get_name_words()
        method_words += method.get_returntype_words()
        method_words += method.get_param_plain_list()
        method_words += method.get_comment_tokens()
        method_subvectors = self._create_word_embeddings_from_word_list(method_words, False)
        return Util.create_averaged_vector(method_subvectors)