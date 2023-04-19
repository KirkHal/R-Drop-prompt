import os

data_type = ['test', 'train', 'valid']
file_path = []
pos_file_path = []
new_file_path = []
prompt_file_path = []
for types in data_type:
    file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".en"))
    pos_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".postag.en"))
    new_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".en_pos"))
    prompt_file_path.append(os.path.join("iwslt14.tokenized.de-en", types + ".de_pmt"))

print(file_path)
print(pos_file_path)
print(new_file_path)

for i in range(3):
    f_new = open(new_file_path[i], 'r+').read().split('\n')
    data_new = f_new[:-1]

    print("EN sentence num:", len(data_new))
    count = 0
    data_part = data_new
    for sentence in data_part:
        # print(sentence)
        # print(len(sentence.split()))
        for word in sentence:
            if word == ";":
                count += 2
        count += len(sentence.split())
    print(count*2)

for i in range(3):
    f_prompt = open(prompt_file_path[i], 'r+').read().split('\n')
    data_prompt = f_prompt[:-1]

    print("DE sentence num:", len(data_prompt))
    count = 0
    for sentence in data_prompt:
        for word in sentence:
            if word == ";":
                count += 2
        count += len(sentence.split())
    print(count*2)
