from TraceLink import TraceLink
import abc, logging
import FileUtil
import Paths
from enum import Enum
from Embedding import MockEmbedding

log = logging.getLogger(__name__)

class RuleApplier:
    def __init__(self, rules=[]):
        self._rules = rules
    
    def apply(self, trace_links: [TraceLink]):
        new_trace_links = []
        for tl in trace_links:
            for rule in self._rules:
                new_trace_links += rule.apply(tl)
        return trace_links + new_trace_links
    
    
class RelationDirection(Enum):
    up = 1 # super classifier
    down = 2 # sub classifier
    both = 3
    
class Rule(abc.ABC):
    @abc.abstractmethod
    def apply(self, trace_link):
        pass
    
class ExtendsRule(Rule):
    def __init__(self, dataset, direction: RelationDirection, inheritance_graph_path=None):
        if not inheritance_graph_path:
            inheritance_graph_path = Paths.inheritance_graph_filename(dataset)
        self._implements_inheritance_dict = FileUtil.read_dict_from_json(inheritance_graph_path)
        self._direction = direction
        self._class2file_map = FileUtil.read_dict_from_json(Paths.classifier_to_file_map_filename(dataset))
        
    def apply(self, trace_link):
        new_trace_links = []
        trace_link_file_name = trace_link.get_code_key(True)
        if not trace_link_file_name.endswith(".java"):
            if trace_link_file_name in self._class2file_map:
                trace_link_file_name = self._class2file_map[trace_link_file_name]
            else:
                log.error(f"Can't resolve {trace_link_file_name} to its containing java file")
        req_embedding = trace_link.req_embedding
        if not trace_link_file_name in self._implements_inheritance_dict:
            log.info(f"{trace_link_file_name} is not in the inheritance graph")
            return []
        if self._direction == RelationDirection.up or self._direction == RelationDirection.both:
            for super_classifier in self._implements_inheritance_dict[trace_link_file_name][0]:
                new_trace_links.append(TraceLink(req_embedding, MockEmbedding(super_classifier, None, None)))
        if self._direction == RelationDirection.down or self._direction == RelationDirection.both:
            for super_classifier in self._implements_inheritance_dict[trace_link_file_name][1]:
                new_trace_links.append(TraceLink(req_embedding, MockEmbedding(super_classifier, None, None)))
        return new_trace_links
            
class ImplementsRule(ExtendsRule):
    def __init__(self, dataset, direction: RelationDirection, implements_graph_path=None):
        if not implements_graph_path:
            implements_graph_path = Paths.implements_graph_filename(dataset)
        super(ImplementsRule, self).__init__(dataset, direction, implements_graph_path)
        

class CallGraphRule(Rule):

    def __init__(self, dataset, direction: RelationDirection):
        self._call_graph = dataset.class_callgraph()
        self._direction = direction
        self._class2file_map = FileUtil.read_dict_from_json(Paths.classifier_to_file_map_filename(dataset))
        
    def apply(self, trace_link):
        new_trace_links = []
        trace_link_file_name = trace_link.get_code_key()
        req_embedding = trace_link.req_embedding
        if not trace_link_file_name in self._call_graph:
            log.info(f"{trace_link_file_name} is not in the call graph")
            return []
        if self._direction == RelationDirection.up or self._direction == RelationDirection.both:
            for class_that_called_me in self._call_graph[trace_link_file_name]["called_by"]:
                new_trace_links.append(TraceLink(req_embedding, MockEmbedding(class_that_called_me, None, None)))
        if self._direction == RelationDirection.down or self._direction == RelationDirection.both:
            for called_class in self._call_graph[trace_link_file_name]["calls"]:
                new_trace_links.append(TraceLink(req_embedding, MockEmbedding(called_class, None, None)))
        return new_trace_links