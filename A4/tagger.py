import os
import sys
import argparse

ENDING_PUNCTUATIONS = {'.', '!', '?', ')', ']', '"'}
POS_TAGS = ['AJ0', 'AJC', 'AJS', 'AT0', 'AV0', 'AVP', 'AVQ', 'CJC', 'CJS', 'CJT', 'CRD', 'DPS', 'DT0', 'DTQ', 'EX0', 'ITJ', 'NN0', 'NN1', 'NN2', 'NP0', 'ORD', 'PNI', 'PNP', 'PNQ', 'PNX', 'POS', 'PRF', 'PRP', 'PUL', 'PUN', 'PUQ', 'PUR', 'TO0', 'UNC', 'VBB', 'VBD', 'VBG', 'VBI', 'VBN', 'VBZ', 'VDB', 'VDD', 'VDG', 'VDI', 'VDN', 'VDZ', 'VHB', 'VHD', 'VHG', 'VHI', 'VHN', 'VHZ', 'VM0', 'VVB', 'VVD', 'VVG', 'VVI', 'VVN', 'VVZ', 'XX0', 'ZZ0', 'AJ0-AV0', 'AJ0-VVN', 'AJ0-VVD', 'AJ0-NN1', 'AJ0-VVG', 'AVP-PRP', 'AVQ-CJS', 'CJS-PRP', 'CJT-DT0', 'CRD-PNI', 'NN1-NP0', 'NN1-VVB', 'NN1-VVG', 'NN2-VVZ', 'VVD-VVN']
AMBIGUITY_TAGS = {'AJ0-AV0', 'AJ0-VVN', 'AJ0-VVD', 'AJ0-NN1', 'AJ0-VVG', 'AVP-PRP', 'AVQ-CJS', 'CJS-PRP', 'CJT-DT0', 'CRD-PNI', 'NN1-NP0', 'NN1-VVB', 'NN1-VVG', 'NN2-VVZ', 'VVD-VVN'}
# P(S_0)
init_prob_table = {}
# transition probability P(S_k | S_k-1)
# key: pos, value: dict{pos, probability}
trans_prob_table = {}
# observation probability P(E | S)
observe_prob_table = {}


def read_test_file(file: str):
    test_file = open(file, "r")
    sentence = []
    prev = ' '
    for line in test_file:
        new_parts = line.strip()
        if prev in ENDING_PUNCTUATIONS and new_parts not in ENDING_PUNCTUATIONS:
            print(sentence)
            viterbi(sentence)
            sentence = []
        sentence.append(new_parts)
        prev = new_parts[0]


# def write_solution_file(file, sol):
#     # TODO
#
def pos_tag_indexing():
    ret = {}
    for i in range(len(POS_TAGS)):
        ret[POS_TAGS[i]] = i
    return ret


def viterbi(sentence: list):
    prob = [[0 for j in range(len(POS_TAGS))] for i in range(len(sentence))]
    prev = [[0 for j in range(len(POS_TAGS))] for i in range(len(sentence))]
    for i in range(len(POS_TAGS)):
        prev[0][i] = "N"
        if POS_TAGS[i] in init_prob_table:
            prob[0][i] = init_prob_table[POS_TAGS[i]]
            if POS_TAGS[i] in observe_prob_table:
                if sentence[0] in observe_prob_table[POS_TAGS[i]]:
                    prob[0][i] *= observe_prob_table[POS_TAGS[i]][sentence[0]]
        else:
            prob[0][i] = 0
    print(prob)



def translate_ambiguity(pos: str):
    if '-' in pos:
        parts = pos.split('-')
        return parts[1] + '-' + parts[0]


def read_files(training_list: list):
    init_occurrence = {}
    transition = {}
    observation = {}
    prev_word = ' '
    prev_pos = ' '
    total_sentences = 0
    total_transitions = 0
    for file in training_list:
        training_file = open(file, "r")
        for line in training_file:
            parts = line.split(':')
            new_parts = []
            for part in parts:
                new_parts.append(part.strip())
            # appears at the beginning of a sentence
            if '-' in new_parts[1] and new_parts[1] not in AMBIGUITY_TAGS:
                new_parts[1] = translate_ambiguity(new_parts[1])
            if prev_word == ' ' or prev_word == '.' and new_parts[1] not in ['PUL', 'PUQ', 'PUR', 'PUN']:
                total_sentences += 1
                if new_parts[1] not in init_occurrence:
                    init_occurrence[new_parts[1]] = 1
                else:
                    init_occurrence[new_parts[1]] += 1
            # check previous pos
            if prev_pos != ' ':
                if prev_pos not in transition:
                    transition[prev_pos] = {new_parts[1]: 1}
                else:
                    if new_parts[1] not in transition[prev_pos]:
                        transition[prev_pos][new_parts[1]] = 1
                    else:
                        transition[prev_pos][new_parts[1]] += 1
            # check words
            if new_parts[1] not in observation:
                observation[new_parts[1]] = {new_parts[0]: 1}
            else:
                if new_parts[0] not in observation[new_parts[1]]:
                    observation[new_parts[1]][new_parts[0]] = 1
                else:
                    observation[new_parts[1]][new_parts[0]] += 1
            total_transitions += 1
            if new_parts[1] not in ['PUL', 'PUQ', 'PUR']:
                prev_word = new_parts[0]
                print(prev_word)
            prev_pos = new_parts[1]
    # calculate initial probability
    for pos in init_occurrence:
        init_prob_table[pos] = init_occurrence[pos] / total_sentences
    # calculate transition probability
    for pos in transition:
        trans_prob_table[pos] = {}
        for pos2 in transition[pos]:
            trans_prob_table[pos][pos2] = transition[pos][pos2] / (total_transitions - 1)
    # calculate observation probability
    # number of word occurrence base on POS / number of total occurrence base on that POS TODO
    for pos in observation:
        observe_prob_table[pos] = {}
        sample_size = 0
        for word in observation[pos]:
            sample_size += observation[pos][word]
        for word in observation[pos]:
            observe_prob_table[pos][word] = observation[pos][word] / sample_size

    print(transition)
    return init_occurrence

def read_all_tags():
    tag_file = open('postags.txt', "r")
    ret = []
    for line in tag_file:
        if len(line) > 2:
            parts = line.split()
            ret.append(parts[0])
    return ret


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--trainingfiles",
    #     action="append",
    #     nargs="+",
    #     required=True,
    #     help="The training files."
    # )
    # parser.add_argument(
    #     "--testfile",
    #     type=str,
    #     required=True,
    #     help="One test file."
    # )
    # parser.add_argument(
    #     "--outputfile",
    #     type=str,
    #     required=True,
    #     help="The output file."
    # )
    # args = parser.parse_args()
    #
    # training_list = args.trainingfiles[0]
    # print("training files are {}".format(training_list))
    #
    # print("test file is {}".format(args.testfile))
    #
    # print("output file is {}".format(args.outputfile))
    #
    #
    # print("Starting the tagging process.")
    read_files(['training_simple.txt'])
    print(init_prob_table)
    # print(len(POS_TAGS))
    # print(read_all_tags())
    print(trans_prob_table)
    print(observe_prob_table)
    read_test_file('test1_simple.txt')
