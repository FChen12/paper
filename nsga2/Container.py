import logging, random
import collections

log = logging.getLogger(__name__)

class Container:
    """
    A data structure that encapsulates treatment of duplicates
    """
    def __init__(self, duplicate_allowed):
        self._duplicate_allowed = duplicate_allowed
        self.empty()
            
    def add(self, element):
        """
        Add an element.
        Returns true if addition is successful.
        """
        size_before_add = self.size()
        if self._duplicate_allowed:
            self._datastructure.append(element)
        else:
            self._datastructure.add(element)
        size_after_add = self.size()
        
        return size_before_add < size_after_add
    
    def add_all(self, element_list):
        return sum([self.add(elem) for elem in element_list]) # sum counts number of true booleans
            
    def get_all_elems_as_list(self):
        return list(self._datastructure)
    
    def empty(self):
        if self._duplicate_allowed :
            self._datastructure = []
        else:
            self._datastructure = set()
            
    def remove(self, element):
        self._datastructure.remove(element)
        
    def remove_duplicates(self):
        """
        Removes all duplicates in the container.
        Returns true if at least one duplicate was found and removed
        """
        if self._duplicate_allowed:
            size_before_remove = self.size()
            self._datastructure = list(set(self._datastructure))
            size_after_remove = self.size()
            return size_before_remove > size_after_remove
        # otherwise: it's already a set -> nothing to do
        return False
        
    def merge(self, other_container):
        self.add_all(other_container._datastructure)
        
    def size(self):
        return len(self._datastructure)
    
    def remove_random_element(self):
        removed_elem = self.get_random_element()
        self._datastructure.remove(removed_elem)
        return removed_elem
        
    def get_random_element(self):
        if self.size() > 0:
            return random.choice(list(self._datastructure)) # list conversion needed for sets
        else:
            log.error(f"Can't choose random element from empty data structure")
            
    def get_two_random_elements(self):
        if self.size() > 1:
            return random.sample(list(self._datastructure), 2)
        else:
            log.error(f"Not enough elements to choose from")
        
    def allows_duplicates(self):
        return self._duplicate_allowed
    
    def difference_ignoring_duplicates(self, other_container):
        """
        Returns the unique elements that are contained in this container but not in the other
        This operation may NOT be symmetric if the containers have different sizes
        """
        return set(self._datastructure) - set(other_container._datastructure)
    
    def __eq__(self, other_container):
        if not self._duplicate_allowed == other_container._duplicate_allowed:
            return False
        return collections.Counter(self._datastructure) == collections.Counter(other_container._datastructure)
    
    def __repr__(self):
        return str(self._datastructure)

        