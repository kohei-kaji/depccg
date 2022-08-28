from reader import read_parsedtree

tokens = [token for _, token, _ in read_parsedtree("/Users/kako/depccg/rotation/test_sentence")]
print(tokens)