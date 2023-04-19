import os

file_path = ["iwslt14.prompt1.de-en-ckpt/result.gen.ref", "iwslt14.prompt1.de-en-ckpt/result.gen.sys"]
new_file_path = ["iwslt14.prompt1.de-en-ckpt/processed.gen.ref", "iwslt14.prompt1.de-en-ckpt/processed.gen.sys"]
ori_file_path = ["/home/algodev/PythonProgram/R-Drop-main/fairseq_src/iwslt14.rdrop.de-en-ckpt/result.gen.ref",
                 "/home/algodev/PythonProgram/R-Drop-main/fairseq_src/iwslt14.rdrop.de-en-ckpt/result.gen.sys"]
test_en_path = "/home/algodev/PythonProgram/R-Drop-Prompt/fairseq_src/examples/translation_rdrop/" \
          "iwslt14.tokenized.de-en/tmp/test.en"
test_de_path = "/home/algodev/PythonProgram/R-Drop-Prompt/fairseq_src/examples/translation_rdrop/" \
          "iwslt14.tokenized.de-en/tmp/test.de"
new_path = "/home/algodev/PythonProgram/R-Drop-Prompt/fairseq_src/wrong_sentence_pairs"

# for i in range(2):
#     f_org = open(file_path[i], 'r+').read().split('\n')
#     data_org = f_org[:-1]
#
#     new_file = open(new_file_path[i], 'a+')
#
#     for index, text in enumerate(data_org):
#         print(text)
#         new_text = ""
#         for word in text:
#             if word == "[":
#                 break
#             else:
#                 new_text += word
#         print(new_text)
#         new_file.write(new_text)
#         new_file.write("\n")
#         print()
#
#     new_file.close()


f_ref = open(new_file_path[0], 'r+').read().split('\n')
data_ref = f_ref[:-1]
f_sys = open(new_file_path[1], 'r+').read().split('\n')
data_sys = f_sys[:-1]
test_en = open(test_en_path, 'r+').read().split('\n')[:-1]
test_de = open(test_de_path, 'r+').read().split('\n')[:-1]

new_file = open(new_path, 'a+')

i_list = []
count = 0
for index, text in enumerate(data_ref):
    len_min = min(len(text), len(data_sys[index]))
    len_dif = abs(len(text) - len(data_sys[index]))
    if len_dif > len_min:
        print(text)
        print(data_sys[index])

        for i, test_sent in enumerate(test_en):
            word_test = test_sent.split()
            word_ref = text.split()
            if word_ref[0] == word_test[0] and word_ref[1] == word_test[1] \
                    and word_ref[-2] == word_test[-2] and word_ref[-1] == word_test[-1]:
                print(i, test_sent)
                print(i, test_de[i])
                i_list.append(i)
                # new_file.write("generate_en:")
                # new_file.write(data_sys[index])
                # new_file.write("\n")
                # new_file.write("reference_en:")
                # new_file.write(test_sent)
                # new_file.write("\n")
                # new_file.write("reference_de:")
                # new_file.write(test_de[i])
                # new_file.write("\n")
                # new_file.write("\n")
                # break
        print(index, len(text), len(data_sys[index]))
        count += 1

new_file.close()
print('total differences:', count)
print(sorted(i_list))



