import re


class PatternNotSpecified(Exception):
    pass


class Search(object):

    def __init__(self, label, patterns, flags=0, store_actions=None, output_map=lambda self: (self.label,) + self.groups):

        self.__label = label
        self.__patterns = patterns
        self.__flags = flags
        self.__output_map = output_map
        self.__store_actions = store_actions

    def search(self, text, context={}):
        """ executes .search on the compiled regex, raises PatternNotSpecified if __pattern is Falsy  """
        if not self.__patterns:
            raise PatternNotSpecified
        if not hasattr(self, '_Search__regexs'):
            self.__regexs = [re.compile(p, flags=self.__flags)
                             for p in self.__patterns]
        self.__context = context
        # self.__results = [regex.search(text) for regex in self.__regexs]
        self.__results = []
        for regex in self.__regexs:
            match = regex.search(text)
            self.__results.append(match)
            if not match:
                break
        # if not len(self.__results) == len(self.__patterns):
        #     self.__results = [None]
        return self.__results

    def __str__(self):
        return ','.join(self.output_map())

    def __repr__(self):
        return f'<Search {self.__label!r} {self.__patterns!r} {self.__flags!r} {self.output_map()!r}>'

    @property
    def groups(self):
        if hasattr(self, '_Search__results') and all(self.__results):
            return [r.groups() for r in self.__results]

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
        for k, v in self.store_actions.items():
            try:
                kv = k(self.groups) if hasattr(k, '__call__') else k
                vv = v(self.groups) if hasattr(v, '__call__') else v
                store[kv] = vv
            except Exception as e:
                store[self.label] = str(e)
        return store
