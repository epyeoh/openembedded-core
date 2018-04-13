from configparser import ConfigParser

class TestResultLogConfigParser(object):

    def __init__(self, config):
        self.parser = ConfigParser()
        # Persist content cases (eg. Uppercase & Lowercase)
        self.parser.optionxform = str
        self.parser.read(config)

    def get_config_items(self, section):
        items = []
        if self.parser.has_section(section):
            items = self.parser.items(section)
        return [i[1] for i in items]