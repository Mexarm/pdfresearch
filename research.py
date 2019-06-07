import re


class PatternNotSpecified(Exception):
    pass


class Search(object):

    def __init__(self, label, pattern, flags=0, store_actions=None, output_map=lambda self: (self.label,) + self.groups):

        self.__label = label
        self.__pattern = pattern
        self.__flags = flags
        self.__output_map = output_map
        self.__store_actions = store_actions

    def search(self, text, context={}):
        """ executes .search on the compiled regex, raises PatternNotSpecified if __pattern is Falsy  """
        if not self.__pattern:
            raise PatternNotSpecified
        if not hasattr(self, '_Search__regex'):
            self.__regex = re.compile(self.__pattern, flags=self.__flags)
        self.__context = context
        self.__result = self.__regex.search(text)
        return self.__result

    def __str__(self):
        return ','.join(self.output_map())

    def __repr__(self):
        return f'<Search {self.__label!r} {self.__pattern!r} {self.__flags!r} {self.output_map()!r}>'

    @property
    def groups(self):
        if hasattr(self, '_Search__result') and self.__result:
            return self.__result.groups()

    @property
    def context(self):
        return self.__context

    @property
    def store_actions(self):
        return self.__store_actions

    @store_actions.setter
    def store_actions(self, value):
        self.__store_actions = value

    @property
    def label(self):
        return self.__label

    @label.setter
    def label(self, value):
        self.__label = value

    def output_map(self):
        if self.groups is None:
            return
        return self.__output_map(self)

    def get_store_values(self):
        store = dict()
        for k, fn in self.store_actions.items():
            try:
                store[k] = fn(self.groups)
            except Exception as e:
                store[k] = str(e)
        return store
