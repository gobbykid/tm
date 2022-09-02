from charEx import *
from genderRec import *
import os
from tqdm import tqdm #for progress bar

#--------------
import pickle
#----------------------


directory_paths = ["C:/Users/media/Desktop/gobbykid/corpus/gobbykidCorpus/male-writers/", "C:/Users/media/Desktop/gobbykid/corpus/gobbykidCorpus/female-writers/"]
file_paths = []

for path in directory_paths:
    for root, directories, files in os.walk(path):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)



#run the code in this way:

characters = dict()

for file_path in tqdm(file_paths): #tqdm just displays a progress bar in the terminal
    characters["book-"+file_path] = gender_recognition(get_characters(open(file_path, encoding="utf8").read()))


# to print a dictionary with characters divided by book and by gender, run:
"""
for key in characters:
    print(key, '-->', characters[key])
"""

# to return one unique list of all characters in the whole corpus, NOT divided by gender
all_characters_list= []
for entry in characters:
    for list in characters[entry]:
        all_characters_list.extend(list)

print(all_characters_list)

#-------------------------------------------------------------------

import pickle
characters_to_discard = all_characters_list
all_characters_file = open("C:/Users/media/Desktop/gobbykid/tm/all_characters_file.txt", "wb") 
pickle.dump(characters_to_discard, all_characters_file)
all_characters_file.close

with open('C:/Users/media/Desktop/gobbykid/tm/all_characters_file.txt', 'rb') as f:
    retrieved_characters = pickle.load(f)
