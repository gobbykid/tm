import re, csv, spacy, nltk as nltk, syntok.segmenter as segmenter



nlp = spacy.load("en_core_web_md", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
#since the aim here is to find entities, the other processes incuded in the default pipeline are disabled in order to execute a much faster performance


nlp.max_length = 2000000 #this is needed in order to avoid the error "ValueError: [E088] Text of length 2000001 exceeds maximum of 1000000. The v2.x parser and NER models require roughly 1GB of temporary memory per 100,000 characters in the input. This means long texts may cause memory allocation errors. If you're not using the parser or NER, it's probably safe to increase the `nlp.max_length` limit. For more info, see the documentation: https://spacy.io/usage/processing-pipelines#config"

#If not already downloaded, it may be necessary to execute the download of the following:
#nltk.download('maxent_ne_chunker')
#nltk.download('words')




#Our regex-based word tokenizer
clean_tokenizer = nltk.RegexpTokenizer(pattern = "[a-zA-Z'’]+") #we want to keep the apostrophe and the right single quotation mark

#Useful lists in order to check the nature of the names
with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/nationalities.csv') as f:
    reader = csv.reader(f)
    nationalities = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/UK_counties.csv') as f:
    reader = csv.reader(f)
    countries = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/countries.csv') as f:
    reader = csv.reader(f)
    uk_counties = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/UK_cities.csv') as f:
    reader = csv.reader(f)
    uk_cities = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/religious_words.csv') as f:
    reader = csv.reader(f)
    religious_words = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/common_geographical_names.csv') as f:
    reader = csv.reader(f)
    geo_names = [row[0].lower() for row in reader]

with open('C:/Users/media/Desktop/gobbykid/tm/gobbykid-text-analysis/characters_extraction_and_gender_recognition/non_characters_csv/exclamations.csv') as f:
    reader = csv.reader(f)
    exclamations = [row[0].lower() for row in reader]




def get_characters(book):
    book = re.sub('\w+\n', '. ', book) #we replace the newlines with a dot and a space, so that the syntok segmenter can work properly
    book = re.sub('\n', ' ', book) #and so on...
    book = re.sub('--', ' ', book)
    book = re.sub('-', ' ', book)
    book = re.sub('_', ' ', book)
    book = re.sub('- -', ' ', book)
    book = re.sub('\*', ' ', book)
    book = re.sub('\s+', ' ', book)
    book = re.sub('\[[Ii]llustration(.+)?\]|\[[Pp]icture(.+)?\]', '', book)

    nltk_characters_set = get_charaters_nltk(book) #we get the characters with nltk
    spacy_characters_set = get_characters_spacy(book) #we get the characters with spacy

    proper_nouns_dict = get_proper_nouns(book) #we get the characters with our own extraction method (syntok and regexTokenizer)
    proper_nouns_set = set([word for word in proper_nouns_dict if proper_nouns_dict[word].get('upper', 0) / (proper_nouns_dict[word].get('upper', 0) + proper_nouns_dict[word].get('lower', 0)) == 1 and proper_nouns_dict[word]["upper"] > 1 and proper_nouns_dict[word]["not_first"] > 0]) #set a threshold: consider only words occuring more than once and at least once not at the beginning of a sentence (in order to avoid the recognition of exclamations and other words that are not names)
    proper_nouns_set = check_names(proper_nouns_set) #check if the names are not nationalities, countries, etc. (see the function below)
    #The returned result is the intersection between the set obtained from our simple extraction (acting as a filter) and the union between the one coming from the extraction with NLTK and the Spacy's one
    return (nltk_characters_set | spacy_characters_set) & proper_nouns_set




#we make nltk work with its word_tokenizer while spacy works with its own. Our extraction, on the other hand, will work with the syntok segmenter and with a regexTokenizer (from NLTK) 
def get_charaters_nltk(book):
    nltk_name_set = set()
    tokenized_sentences = nltk.sent_tokenize(book) #we tokenize the book into sentences with nltk (we could have used syntok, but we want to use the same tokenizer as the one used by spacy)
    for sent in tokenized_sentences:
        chunked = nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))) #the ne_chunk default value for "binary" attribute is "False", so it returns named entities with their own Class (PERSON, ORGANIZATION, etc.)
        for item in chunked:
            if type(item) == nltk.Tree and item.label() == "PERSON": #we check if the item is a named entity and if it is a person
                nltk_name_set.add(" ".join([token for token, pos in item.leaves()]).lower())  #we add the name to the set (we make it lowercase in order to avoid duplicates)
    return check_names(nltk_name_set) #we check if the names are not nationalities, countries, etc. (see the function below)



def get_characters_spacy(book):
    doc = nlp(book) #we process the book with spacy (we could have used syntok, but we want to use the same tokenizer as the one used by nltk)
    spacy_name_set = set([ent.text.lower() for ent in doc.ents if ent.label_ == "PERSON"]) #we add the names to the set (we make it lowercase in order to avoid duplicates)
    return check_names(spacy_name_set) #we check if the names are not nationalities, countries, etc. (see the function below)


#The following function's aim is to extract words that have an high probability of being a character's name or surname
def get_proper_nouns(book):
    proper_nouns = {}
    list_of_sentences = syntok_list_of_sentences(book) #we use syntok's segmenter in order to avoid the splitting of words like "Mr." or "Mrs." into "Mr" and "." (which would be the case if we used nltk's sent_tokenize)
    for sentence in list_of_sentences:
        next_words = []  #list of words that follow a capitalized word
        tokenized_sent = clean_tokenizer.tokenize(sentence) #we use the regex-based tokenizer in order to avoid the splitting of words like "Mr." or "Mrs." into "Mr" and "." (which would be the case if we used nltk's word_tokenize)
        for word in tokenized_sent: 
            if len(word) > 1:
                if word[-1] == "’":
                    clean_word = word[:-1]
                elif word[-2:] == "’s":
                    clean_word = word[:-2] 
                else:
                    clean_word = word
            else:
                clean_word = word
                
            full_name = [] #list of words that form a full name (e.g. ["Mr.", "John", "Smith"])
            if word in next_words or len(clean_word) <= 1: #if the word is in the list of words that follow a capitalized word, or if it is a single letter, we skip it (we don't want to consider it as a name)
                continue
            else:
                if clean_word[0].isupper() and not re.match("(I’.+)|I", clean_word): #We want to avoid including I, I'm, I'll
                    case = 'upper'
                    full_name.append(clean_word) #We add the first word to the list
                    upper = True
                    idx = tokenized_sent.index(word) #We get the index of the word in the sentence
                    while upper:
                        if idx < len(tokenized_sent)-1: #We check if we are not at the end of the sentence
                            idx += 1
                        else:
                            break       #We break the loop if we are at the end of the sentence
                        if tokenized_sent[idx][0].isupper() and len(tokenized_sent[idx]) > 1: #We check if the next word is capitalized and if it is longer than 1 character
                            full_name.append(tokenized_sent[idx]) #We add the next word to the list of words that make up the name
                            next_words.append(tokenized_sent[idx]) #We add the next word to the list of words to avoid in the next iteration of the loop (we don't want to consider the same word twice)
                        else:
                            upper = False
                else:
                    case = 'lower'

            if full_name: 
                name_lower = " ".join(full_name).lower()
                case = 'upper'
            else:
                name_lower = clean_word.lower()
                case = 'lower'

            if name_lower not in proper_nouns:
                proper_nouns[name_lower] = {} #We create a dictionary for the name with the corresponding case, the number of times it appears with that case, and the number of times it appears at the first position of a sentence
                proper_nouns[name_lower]['upper'] = 0 
                proper_nouns[name_lower]['lower'] = 0
                proper_nouns[name_lower]["not_first"] = 0
            proper_nouns[name_lower][case]+= 1 #We update the number of times the name appears with the corresponding case
            if re.match("\w+(\s\w+)+", name_lower) or (not re.match("\w+(\s\w+)+", name_lower) and tokenized_sent.index(word) != 0): #We check if the name is a full name (e.g. "Mr. John Smith") and not a single word (e.g. "Mr.") or a surname (e.g. "Smith") or if it is a single word and it is not at the beginning of the sentence
                proper_nouns[name_lower]["not_first"] += 1
 
    return proper_nouns




def syntok_list_of_sentences(book):
    list_of_sentences = [] 
    for paragraph in segmenter.process(book): #we use syntok's segmenter
        for sent in paragraph:
            temp = []
            token_list = []
            for token in sent:
                token_list.append(token.spacing) #we get the spacing of the token (e.g. " ") and we add it to the list
                token_list.append(token.value) #we get the value of the token (e.g. "Hello") and we add it to the list
            if token_list[0] == ' ':
                token_list.remove(token_list[0]) #we remove the first element of the list if it is a space
            temp = ''.join(token_list)
            list_of_sentences.append(temp)

    return list_of_sentences




def check_names(names_set):
    characters_set = set()
    substitutions_dict = {".+['’]s$": ("['’]s", ""), ".+’":("’", ""), ".+!":("!", ""), "[Tt]he\s.+":("[Tt]he\s", ""), "[oO]\s.+": ("[Oo]\s", ""), ".+['’]s\s.+": ("['’]s\s", " "),".+\s['’]s": ("\s['’]s", ""), ".+['’,.]": ("['’,.]", ""), "[Dd]oes\s.+": ("[Dd]oes\s", "")} #we create a dictionary of substitutions to be applied to the names
    not_names_regex = ["(.+)?christmas(.+)?", ".+hall","(.+)?land", "mechlin(\s\w+)?", ".+\sislet?", ".+\sisland", ".+\slake", "lake\s.+", ".+\spark", ".+\schurch", ".+\sstation", "(.+\s)?mine", ".+\sstreet", ".+\sriver", "river\s.+", ".+\sbrook", "(.+\s)?ocean", ".+\sbeach", ".+\sbay", "mount.+", "part\s.+", "chapter\s.+", ".+\sbridge", ".+\sdock", ".+\shead", ".+\slane", ".+(\s)?hill", ".+\srepublic", ".+\sroad", ".+\scastle", "(.+\s?)?court(\s.+)?", ".+\sfarm", ".+\slodge", ".+\scab", "(.+\s)?school", "(.+\s)?prison", ".+\sday", "injuns?", ".+\stowers?", "first\s.+", "second\s.+", "third\s.+", "fourth\s.+", "fifth\s.+", "sixth\s.+", "seventh\s.+", "(\.+\s)?majesty", ".+\sprince(ss)?", "\w+chnic", "\.+\slaw", "\.+\swords?", "\.+\speople", "st\s\w+", "(.+\s)?gang", "(.+\s)book", "(.+\s)?crew", "(.+\s)?memorial", "(.+\s)?house", "(.+\s)?port(\s.+)?", "(.+\s)?garden", ".+\sgod", ".+\sheaven", ".+\shell", "(.+\s)?terrace", "(.+\s)?town", "dear(\s.+)", "(.+\s)?abbey"] 
    not_names_words = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "christmas", "maecenas", "baby", "sir", "lord", "king", "prince", "duke", "mister", "master", "mr", "father", "uncle", "son", "brother", "lady", "queen", "princess", "duchess", "dame", "miss", "mrs", "ms", "aunt", "mother", "sister", "daughter", "mamma", "captain", "doctor", "treasure", "cap", "i", "me", "you", "yrs", "destiny", "virtue", "vicar", "englishman", "englishwoman", "quis", "editor", "project gutenberg", "where", "who", "why", "what", "how", "wont", "mystery", "fruit", "vegetables", "none", "perfessor", "professor", "teacher", "dearest", "lillibullero", "gradus", "latitude", "longitude", "north", "south", "east", "west", "latin"] #we create a list of words that are not names

    for name in names_set:
        s_name = name.strip()
        for regex in substitutions_dict:
            if re.match(regex, s_name):
                s_name = re.sub(substitutions_dict[regex][0], substitutions_dict[regex][1], s_name) #This line makes use of a dictionary containing tuples useful for the substitutions. The first element of the tuple is the regex and the second element is the substitution
        person_name = True
        for nnr in not_names_regex:
            if re.match(nnr, s_name): #we check if the name is a regex that is not a name (e.g. "Mr. John Smith" is not a regex that is not a name)
                person_name = False
                break
        if person_name and (s_name not in countries and s_name not in nationalities and s_name not in not_names_words and s_name not in uk_cities and s_name not in uk_counties and s_name not in geo_names and s_name not in religious_words and s_name not in exclamations): #we check if the name is a word that is not a name on the basis of the lists we have created before from the csv files
            characters_set.add(s_name.strip())
            
    return characters_set