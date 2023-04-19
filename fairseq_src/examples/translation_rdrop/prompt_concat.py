import nltk
import re
import os
from nltk import data
data.path.append(r"/home/algodev/PythonProgram/nltk_data")

data_type = ['test', 'train', 'valid']
file_path = []
prompt_file_path = []
for types in data_type:
    file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".de"))
    prompt_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".de_pmt"))

prompt_list = ["< translate into en >", "< output pos tagging of translation >"]

print(file_path)
print(prompt_file_path)

for i in range(3):
    f_org = open(file_path[i], 'r+').read().split('\n')
    data_org = f_org[:-1]

    new_file = open(prompt_file_path[i], 'a+')

    for text in data_org:
        for index, prompt in enumerate(prompt_list):
            text = text + " " + prompt_list[index]

        print(text)
        new_file.write(text)
        new_file.write("\n")

    new_file.close()

