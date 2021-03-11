from SolutionTraceMatrix import SolutionTraceMatrixWithDuplicates
import collections
import random, abc
from Preprocessing import CodeASTTokenizer
from Preprocessing.CodeASTTokenizer import JavaCodeASTTokenizer
import Paths
import pandas
from Dataset import Etour308, ROOT
from Preprocessing.Tokenizer import WordTokenizer

import it_core_news_lg

# keeping only tagger component needed for lemmatization


my_str = "inserisce"
nlp = it_core_news_lg.load(disable=["parser", "ner"])
doc = nlp(my_str)
words_lemmas_list = [token.lemma_ for token in doc]
print(words_lemmas_list)