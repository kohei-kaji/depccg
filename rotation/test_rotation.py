from rotation.find_verb import VerbListCreator

class Test(object):
    def __init__(self):
        self.verblist = {}
    
    def _getverblist(self):
        with open('./test_sentence', 'r') as f:
            for line in f:
                self.verblist = VerbListCreator.create_verblist(line)
    
t = Test()
for key, value in t.verblist.items():
    print(f'{key} # {str(value)}')
