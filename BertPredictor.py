import torch
from transformers import BertTokenizer
from torch import nn
from transformers import BertForSequenceClassification
import Util
import FileUtil

TRAINING_PARAM_FILE_NAME = "training_param.json"

class BertPredictor:
    """
    This is the BERT classificator that predicts a probability of a trace link relation between
    a requirement element and a code element
    """
    def __init__(self, bert_model_dir, toGPU=True):
        self.training_param = FileUtil.read_dict_from_json(bert_model_dir / TRAINING_PARAM_FILE_NAME)
        self.model = BertForSequenceClassification.from_pretrained(str(bert_model_dir))
        self.tokenizer = BertTokenizer.from_pretrained(str(bert_model_dir))
        self.toGPU = toGPU
        self.activation = nn.Softmax(dim=1)
        if toGPU:
            self.device = Util._init_colab_gpu()
            self.model.cuda()
        self.model.eval()
            
    def calculate_trace_link_probability(self, req_element, code_element):
        bert_input = self._encode_data(req_element, code_element)
        b_input_ids = bert_input[0]
        b_input_mask = bert_input[1]
        if self.toGPU:
            b_input_ids = bert_input[0].to(self.device)
            b_input_mask = bert_input[1].to(self.device)
        
        with torch.no_grad():        
            logits = self.model(b_input_ids, attention_mask=b_input_mask)[0]
            if self.toGPU:
                logits = logits.cpu()
            probabilities = self.activation(logits)
            return self._unpack_tensor(probabilities)
    
    def _encode_data(self, req_element, code_element):
        encoded_dict = self.tokenizer.encode_plus(req_element, code_element, add_special_tokens=True, 
                            max_length=self.training_param["max_seq_len"],
                            pad_to_max_length = True, return_attention_mask = True, do_lower_case=True)

        return torch.tensor(encoded_dict['input_ids']).unsqueeze(0), torch.tensor(encoded_dict['attention_mask']).unsqueeze(0)

    def _unpack_tensor(self, tens):
        return tens.data[0].tolist()[1]
