import nltk
import re
import os
from nltk import data
data.path.append(r"/home/algodev/PythonProgram/nltk_data")

data_type = ['test', 'train', 'valid']
file_path = []
pos_file_path = []
new_file_path = []
for types in data_type:
    file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".en"))
    pos_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".postag.en"))
    new_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".en_pos"))

print(file_path)
print(pos_file_path)
print(new_file_path)

for i in range(3):
    f_org = open(file_path[i], 'r+').read().split('\n')
    data_org = f_org[:-1]
    f_pos = open(pos_file_path[i], 'r+').read().split('\n')
    data_pos = f_pos[:-1]

    new_file = open(new_file_path[i], 'a+')

    if len(data_pos) == len(data_org):
        for index, text in enumerate(data_org):
            text_cat = text + ' [ pos tagging ] ' + data_pos[index]
            new_file.write(text_cat)
            new_file.write("\n")
            print(text_cat)

    new_file.close()


# count = 0
# with open(file_path, 'r') as f:
#     data = f.read().split('\n')
#     for sentence in data:
#         if "&apos;" in sentence:
#             count += 1
#             sentence = re.sub("&apos;", "'", sentence)
#         if "&quot;" in sentence:
#             count += 1
#             sentence = re.sub("&quot;", "\"", sentence)
#
#         print(sentence)
#         text = nltk.word_tokenize(sentence)
#         print(text)
#         text_postag = nltk.pos_tag(text)
#         tag_list = []
#         for tags in text_postag:
#             tag_list.append(tags[1])
#         pos_text = " ".join(tag_list)
#         print(pos_text)
#
#         new_file = open(new_file_path, 'a+')
#         new_file.write(pos_text)
#         new_file.write("\n")
#
# print(count)


# text1 = "It's a vehicle through which the soul of each particular culture comes into the material world."
# text2 = "it &apos;s a vehicle through which the soul of each particular culture comes into the material world ."
# flag = 1
#
# if flag:
#     text = nltk.word_tokenize(text1)
# else:
#     text = nltk.word_tokenize(text2)
#
# print(text)
# text_postag = nltk.pos_tag(text)
# tag_list = []
# for tags in text_postag:
#     tag_list.append(tags[1])
# pos_text = " ".join(tag_list)
# print(pos_text)


