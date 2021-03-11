from pathlib import Path
from abc import ABC, abstractmethod
from gensim.models.keyedvectors import KeyedVectors, WordEmbeddingsKeyedVectors
import torch, random, zipfile
from transformers import BertTokenizer, BertModel
import gensim.models.wrappers
from pyemd import emd
import numpy, logging
import FileUtil
import Util

CURRENT_DIR = Path(__file__).parent
DEFAULT_FASTTEXT_MODEL_PATH = str(CURRENT_DIR / "resources/cc.en.300.bin")
DEFAULT_FASTTEXT_VEC_FILE = CURRENT_DIR / "resources/wiki-news-300d-1M-subword.vec"
BERT_MODEL_DEFAULT = "bert-base-uncased"
COLAB_MODEL_PATH = "/content/drive/My Drive/models/cc.en.300.bin"
COLAB_ALIGNED_MODEL_PATH_IT = "/content/drive/My Drive/muse_it/wiki.multi.it.vec"
COLAB_ALIGNED_MODEL_PATH_ENG = "/content/drive/My Drive/muse_en/wiki.multi.en.vec"
COLAB_FINETUNED_MODEL_ZIP_1 = "/content/drive/My Drive/domAdaptiert/domAdaptiert.zip" # Containing whole words
COLAB_FINETUNED_MODEL_ZIP_2 = "/content/drive/My Drive/domAdaptiertSub/domAdaptiertSub.zip" # only n-grams
FOLDER_A = "a" # need extra folders to avoid timeout on colab when reading large files
FOLDER_B = "b"
COLAB_FINETUNED_MODEL_1 = FOLDER_A + "/avg3.vec"
COLAB_FINETUNED_MODEL_2 = FOLDER_B + "/avg4.vec"

log = logging.getLogger(__file__)

class WordEmbeddingCreator(ABC) :
    
    @abstractmethod
    def create_word_embedding(self, word, ital=False):
        """
        Use ital option to indicate if a second language model should be used
        """
        pass
    
    @abstractmethod
    def word_movers_distance(self, str_list_1, str_list_2):
        pass
    
class FastTextEmbeddingCreator(WordEmbeddingCreator):
    """
    Use this for monolingual fasttext models that uses .bin models
    """
    def __init__(self, model_path=COLAB_MODEL_PATH):
        self._model = gensim.models.wrappers.FastText.load_fasttext_format(model_path)
        self._model.init_sims(replace=True) # normalizes vectors

    def create_word_embedding(self, word, ital=None):
        try:
            return self._model[word]
        except KeyError as k:
            log.info(k)
            return None
    
    def word_movers_distance(self, str_list_1, str_list_2):
        return self._model.wmdistance(str_list_1, str_list_2)
        
class FastTextAlignedEngItalEmbeddingCreator(WordEmbeddingCreator):
    """
    For eng/ital fasttext embedding aligned in a single vector space

    """
    def __init__(self, model_path_it=COLAB_ALIGNED_MODEL_PATH_IT, model_path_en=COLAB_ALIGNED_MODEL_PATH_ENG):
        self._model_it = KeyedVectors.load_word2vec_format(model_path_it)
        self._model_it.init_sims(replace=True)
        
        self._model_en = KeyedVectors.load_word2vec_format(model_path_en)
        self._model_en.init_sims(replace=True)
    
    def create_word_embedding(self, word, ital=True):
        """
        ital=True: use italian model, otherwise english
        Returns None if word is neither in italian nor in english model
        """
        if ital:
            try:
                return self._model_it[word]
            except KeyError as k:
                log.info("It_model: " + str(k))
        else:
            try:
                return self._model_en[word]
            except KeyError as l:
                log.info("Eng_model: " + str(l))
            
        return None
    
    def __wmdistance(self, document1, document2, ital1, ital2):
        """
        See gensim.models.WordEmbeddingKeyedVectors.wmdistance
        
        Modifies the original method to work with two vec models with potential oov
        Returns infinity if at least one of the documents is empty or completely oov
        """
        # Remove out-of-vocabulary words.
        len_pre_oov1 = len(document1)
        len_pre_oov2 = len(document2)
        document1 = [token for token in document1 if self.create_word_embedding(token, ital1) is not None]
        document2 = [token for token in document2 if self.create_word_embedding(token, ital2) is not None]
        diff1 = len_pre_oov1 - len(document1)
        diff2 = len_pre_oov2 - len(document2)
        if diff1 > 0 or diff2 > 0:
            log.info('Removed %d and %d OOV words from document 1 and 2 (respectively).', diff1, diff2)

        if not document1 or not document2:
            log.info(
                "At least one of the documents had no words that were in the vocabulary. "
                "Aborting (returning inf)."
            )
            return float('inf')
        
        dictionary = gensim.corpora.dictionary.Dictionary(documents=[document1, document2])
        vocab_len = len(dictionary)

        if vocab_len == 1:
            # Both documents are composed by a single unique token
            return 0.0

        # Sets for faster look-up.
        docset1 = set(document1)
        docset2 = set(document2)

        # Compute distance matrix.
        distance_matrix = numpy.zeros((vocab_len, vocab_len), dtype= numpy.core.numerictypes.double)
        for i, t1 in dictionary.items():
            if t1 not in docset1:
                continue

            for j, t2 in dictionary.items():
                if t2 not in docset2 or distance_matrix[i, j] != 0.0:
                    continue

                # Compute Euclidean distance between word vectors.
                distance_matrix[i, j] = distance_matrix[j, i] = numpy.sqrt(numpy.sum((self.create_word_embedding(t1, ital1) - self.create_word_embedding(t2, ital2))**2))

        if numpy.sum(distance_matrix) == 0.0:
            # `emd` gets stuck if the distance matrix contains only zeros.
            log.info('The distance matrix is all zeros. Aborting (returning inf).')
            return float('inf')

        def nbow(document):
            d = numpy.zeros(vocab_len, dtype=numpy.core.numerictypes.double)
            nbow = dictionary.doc2bow(document)  # Word frequencies.
            doc_len = len(document)
            for idx, freq in nbow:
                d[idx] = freq / float(doc_len)  # Normalized word frequencies.
            return d

        # Compute nBOW representation of documents.
        d1 = nbow(document1)
        d2 = nbow(document2)

        # Compute WMD.
        return emd(d1, d2, distance_matrix)
    
    def word_movers_distance(self, str_list_1, str_list_2, ital1, ital2):
        return self.__wmdistance(str_list_1, str_list_2, ital1, ital2)
        
    
class FineTunedFastTextEmbeddingCreator(WordEmbeddingCreator):
    """Using fine tuned fasttext model"""
    
    def __wmdistance(self, document1, document2):
        """
        See gensim.models.WordEmbeddingKeyedVectors.wmdistance
        
        Modifies the original method to work with two fine tuned models
        """
        dictionary = gensim.corpora.dictionary.Dictionary(documents=[document1, document2])
        vocab_len = len(dictionary)

        if vocab_len == 1:
            # Both documents are composed by a single unique token
            return 0.0

        # Sets for faster look-up.
        docset1 = set(document1)
        docset2 = set(document2)

        # Compute distance matrix.
        distance_matrix = numpy.zeros((vocab_len, vocab_len), dtype= numpy.core.numerictypes.double)
        for i, t1 in dictionary.items():
            if t1 not in docset1:
                continue

            for j, t2 in dictionary.items():
                if t2 not in docset2 or distance_matrix[i, j] != 0.0:
                    continue

                # Compute Euclidean distance between word vectors.
                distance_matrix[i, j] = distance_matrix[j, i] = numpy.sqrt(numpy.sum((self.create_word_embedding(t1) - self.create_word_embedding(t2))**2))

        if numpy.sum(distance_matrix) == 0.0:
            # `emd` gets stuck if the distance matrix contains only zeros.
            log.info('The distance matrix is all zeros. Aborting (returning inf).')
            return float('inf')

        def nbow(document):
            d = numpy.zeros(vocab_len, dtype=numpy.core.numerictypes.double)
            nbow = dictionary.doc2bow(document)  # Word frequencies.
            doc_len = len(document)
            for idx, freq in nbow:
                d[idx] = freq / float(doc_len)  # Normalized word frequencies.
            return d

        # Compute nBOW representation of documents.
        d1 = nbow(document1)
        d2 = nbow(document2)

        # Compute WMD.
        return emd(d1, d2, distance_matrix)
    
    def __init__(self):
        if not FileUtil.file_exists(COLAB_FINETUNED_MODEL_1):
            with zipfile.ZipFile(COLAB_FINETUNED_MODEL_ZIP_1, 'r') as zip_ref:
                zip_ref.extractall(FOLDER_A)
        if not FileUtil.file_exists(COLAB_FINETUNED_MODEL_2):
            with zipfile.ZipFile(COLAB_FINETUNED_MODEL_ZIP_2, 'r') as zip_ref:
                zip_ref.extractall(FOLDER_B)
          
        self._model = gensim.models.KeyedVectors.load_word2vec_format(COLAB_FINETUNED_MODEL_1)
        self._modelSub = gensim.models.KeyedVectors.load_word2vec_format(COLAB_FINETUNED_MODEL_2)
        self._model.init_sims(replace=True) # normalizes vectors
        self._modelSub.init_sims(replace=True)
    
    def create_word_embedding(self, word, ital=None):
        if word in self._model.wv.vocab:
            return self._model[word]
        else:
            extendedWord='<'+word+'>'
            subwords=[]
            minn=3
            maxn=6
            for n in range(minn, maxn+1):
                subwords=subwords+[extendedWord[i:i+n] for i in range(len(extendedWord)-n+1)]
            vecsSubwords=[]
            numsub=0
            for subword in subwords:
                if subword in self._modelSub.wv.vocab:
                    vecsSubwords.append(self._modelSub[subword])
                    numsub=numsub+1
            dim = 300
            vector = [0] * dim
            if numsub==0:
                return numpy.array(vector)
            else:
                for vecSubword in vecsSubwords:
                    for i in range(dim):
                        vector[i] = vector[i] + vecSubword[i]
                if len(vecsSubwords) > 0:
                    for j in range(dim):
                        vector[j] = vector[j] / len(vecsSubwords)
                return numpy.array(vector)
        
    def word_movers_distance(self, str_list_1, str_list_2):
        return self.__wmdistance(str_list_1, str_list_2)
        
class MockWordEmbeddingCreator(WordEmbeddingCreator):
    def __init__(self, seed = None):
        if seed:
            random.seed(seed)
    
    def create_word_embedding(self, word, sentence = None, ital=None):
        return Util.random_numpy_array(-1, 1, 300)
    
    def word_movers_distance(self, str_list_1, str_list_2, ital1=None, ital2=None):
        assert isinstance(str_list_1, list)
        assert isinstance(str_list_2, list)
        return random.uniform(0, 10)
    
class BertSentenceEmbeddingCreator(WordEmbeddingCreator):
    """
    Creates a sentence embedding with BERT. This is not the BERT classificator.
    """
    def __init__(self, model_path=BERT_MODEL_DEFAULT, toGPU=True):
        self._toGPU = toGPU
        self._tokenizer = BertTokenizer.from_pretrained(model_path, do_lower_case=True)
        self._model = BertModel.from_pretrained(model_path, output_attentions = False)
        if toGPU:
            self._device = Util._init_colab_gpu()
            self._model.cuda()
        self._model.eval()
 
    def create_word_embedding(self, sentence_string, ital=None):
        input_ids = self._tokenizer.encode(sentence_string, add_special_tokens=True)
        segments_ids = [1] * len(input_ids)
        tokens_tensor = torch.tensor(input_ids).unsqueeze(0) # create batch size = 1
        segments_tensors = torch.tensor(segments_ids).unsqueeze(0)
        if self._toGPU:
            cuda_tokens_tensor = tokens_tensor.to(self._device)
            cuda_segments_tensors = segments_tensors.to(self._device)
            with torch.no_grad():
                #output = (([batch][token][last_layer_weights]), ([batch][last_layer_weight_with_tanh_combine]))
                output = self._model(cuda_tokens_tensor, cuda_segments_tensors)
            return output[0][0][0].cpu().numpy() # Corresponds to the embedding for the [CLS] token
        else:
            with torch.no_grad():
                #output = (([batch][token][last_layer_weights]), ([batch][last_layer_weight_with_tanh_combine]))
                output = self._model(tokens_tensor, segments_tensors)
            return output[0][0][0].numpy()    



