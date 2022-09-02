from genderize import Genderize
from genderComputer import GenderComputer
import re

male_words = {"sir", "duke", "lord", "king", "prince",  "mister", "mr", "father", "uncle", "son", "brother", "boy", "widower", "master"}
female_words = {"lady", "duchess", "queen", "princess", "dame", "missis", "miss", "mrs", "ms", "aunt", "mother", "sister", "daughter", "girl", "widow", "mistress"}


def filter_surnames(names_set):
    single_word_names = []
    filtered_swn = []
    multiple_words_names = []
    for name in names_set:
        if re.match("\w+(\s\w+)+", name):
            multiple_words_names.append((name.split(" "))) #The names are splitted in order to be able to check each word composing the name and to be able to add the name to the right list
        else:
            single_word_names.append(name)
    
    for s_name in single_word_names:   
        remove = False
        for mwn in multiple_words_names:
            if s_name[-1] == "s":             #Here the family names are removed: e.g. If we find "John Doe", "Lisa Doe", "Does" and "Doe", we remove "Does" and "Doe"
                if mwn[-1] == s_name[:-1]:   #The family names are removed by checking the last word of the name and the last word of the surname
                    remove = True
            
            if mwn[-1] == s_name:      #Here we just check if the last word of the name is the same of the surname
                remove = True
        if not remove:
            filtered_swn.append(s_name)  #If the name is not a surname, it is added to the list of names composed by a single word
        else:
            continue

    return filtered_swn, multiple_words_names






def gender_recognition(names_set):
    gc = GenderComputer()
    single_word_names, multiple_words_names = filter_surnames(names_set) #This function aims at removing the names that are composed by a single word but are present in the list of names composed by multiple words

    male_characters = []
    female_characters = []
    unknown_gender = []

    for name in single_word_names:                   #First check by means of genderComputer on the list of names composed by a single word
        gender = gc.resolveGender(name, None)       #If the name is not found, it returns None
        if gender == "male": 
            male_characters.append(name)
        elif gender == "female":
            female_characters.append(name)
        else:
            try:                                      #If genderComputer is not able to guess the gender, Genderize is used
                char_info = Genderize().get([name])   #Genderize returns a list of dictionaries, so we need to access the first element of the list
                if char_info[0]["gender"] == "male":
                    male_characters.append(name)
                elif char_info[0]["gender"] == "female":
                    female_characters.append(name)
                else:
                    unknown_gender.append(name)
            except:
                unknown_gender.append(name)

    
    for full_name in multiple_words_names:                        #The first block of checks aims at guessing the gender on the basis of genderdized words present in the strings without using any additional library
        joined_name = " ".join(full_name)

        if len(set(full_name) & male_words) > 0:                #By checking the presence of genderdized words in the name we can directly append the name in the right list
            do_not_add = False
            for masculine_name in male_characters:
                if re.match(".+\s.+", masculine_name):
                    mnw_list = masculine_name.split(" ")
                    if full_name[1:] == mnw_list[1:] or full_name[1:] == mnw_list:
                        do_not_add = True
                        break
                else:
                    continue
            if do_not_add == False:
                male_characters.append(joined_name)


        elif len(set(full_name) & female_words) > 0:
                do_not_add = False
                for feminine_name in female_characters:
                    if re.match(".+\s.+", feminine_name):
                        mnw_list = feminine_name.split(" ")
                        if full_name[1:] == mnw_list[1:] or full_name[1:] == mnw_list:
                            do_not_add = True
                            break
                    else:
                        continue                   
                if do_not_add == False:
                    female_characters.append(joined_name)


        else:                                                       #Now, it is used the same process as before: first we check the gender by meand of genderComputer
            gender = gc.resolveGender(joined_name, None)           #If the name is not found, it returns None
            if gender == "male":
                male_characters = check_list_mwn(male_characters, full_name)

            elif gender == "female":
                female_characters = check_list_mwn(female_characters, full_name)
            else:                                       #In the following block the detection is based on each word composing the names
                already_added = False                  
                for single_name in full_name:
                    if already_added:
                        break
                    else:
                        if single_name in male_characters:
                            male_characters = check_list_mwn(male_characters, full_name)
                            already_added = True
                        elif single_name in female_characters:
                            female_characters = check_list_mwn(female_characters, full_name)
                            already_added = True
                        elif single_name in unknown_gender:
                            continue
                        else:
                            name_gender = gc.resolveGender(single_name, None) 
                            if name_gender == "male":
                                male_characters = check_list_mwn(male_characters, full_name)
                                already_added = True
                            elif name_gender == "female":
                                female_characters = check_list_mwn(female_characters, full_name)
                                already_added = True
                            else:
                                if full_name.index(single_name) == len(full_name) -1:
                                    unknown_gender.append(joined_name)
                                else:
                                    try:                                                #This try except block is necessary since Genderize has a daily request limit
                                        name_gender = Genderize().get([single_name])
                                        if name_gender[0]["gender"] == "male":
                                            male_characters = check_list_mwn(male_characters, full_name)
                                            already_added = True
                                        elif name_gender[0]["gender"] == "female":
                                            female_characters = check_list_mwn(female_characters, full_name)
                                            already_added = True
                                        else:
                                            continue
                                    except:
                                        continue
                                


    return male_characters, female_characters, unknown_gender



def check_list_mwn(character_list, name_to_check):
    dupl_list = character_list

    for name in dupl_list:
        spl_name = name.split(" ")
        if (spl_name[1:] == name_to_check[1:] or spl_name[1:] == name_to_check) and spl_name[0] in (male_words or female_words):
            character_list.remove(name)
            
    character_list.append(" ".join(name_to_check))
    return character_list



