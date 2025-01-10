import abc

class baseClassUI(object, metaclass=abc.ABCMeta):
    """ Base class for UI handlers, specifies the two functions that need to be defined for every UIHandler class """
    @abc.abstractmethod
    def display_ui(self):
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_user_input(self):
        raise NotImplementedError