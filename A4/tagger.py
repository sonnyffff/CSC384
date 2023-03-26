import os
import sys
import argparse

init_prob_table = {}
# key: pos, value: dict{pos, probability}
trans_prob_table = {}
# observation probability P(E | S)
observe_prob_table = {}


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
            if prev_word == ' ' or prev_word == '.' and new_parts[1] not in ['PUL', 'PUQ', 'PUR', 'PUN']:
                total_sentences += 1
                if new_parts[1] and translate_ambiguity(new_parts[1]) not in init_occurrence:
                    init_occurrence[new_parts[1]] = 1
                elif new_parts[1] in init_occurrence:
                    init_occurrence[new_parts[1]] += 1
                else:
                    init_occurrence[translate_ambiguity(new_parts[1])] += 1
            # check previous pos
            if prev_pos != ' ':
                if prev_pos and translate_ambiguity(prev_pos) not in transition:
                    transition[prev_pos] = {new_parts[1]: 1}
                if prev_pos in transition:
                    if new_parts[1] and translate_ambiguity(new_parts[1]) not in transition[prev_pos]:
                        transition[prev_pos][new_parts[1]] = 1
                    elif new_parts[1] in transition[prev_pos]:
                        transition[prev_pos][new_parts[1]] += 1
                    else:
                        transition[prev_pos][translate_ambiguity(new_parts[1])] += 1
                else:
                    if new_parts[1] and translate_ambiguity(new_parts[1]) not in transition[translate_ambiguity(prev_pos)]:
                        transition[translate_ambiguity(prev_pos)][new_parts[1]] = 1
                    elif new_parts[1] in transition[prev_pos]:
                        transition[translate_ambiguity(prev_pos)][new_parts[1]] += 1
                    else:
                        transition[translate_ambiguity(prev_pos)][translate_ambiguity(new_parts[1])] += 1
            # check words
            if new_parts[1] and translate_ambiguity(new_parts[1]) not in observation:
                observation[new_parts[1]] = {new_parts[0]: 1}
            if new_parts[1] in observation:
                if new_parts[0] not in observation[new_parts[1]]:
                    observation[new_parts[1]][new_parts[0]] = 1
                else:
                    observation[new_parts[1]][new_parts[0]] += 1
            else:
                if new_parts[0] not in observation[translate_ambiguity(new_parts[1])]:
                    observation[translate_ambiguity(new_parts[1])][new_parts[0]] = 1
                else:
                    observation[translate_ambiguity(new_parts[1])][new_parts[0]] += 1
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
    read_files(['training_simple2.txt'])
    print(init_prob_table)
    print(trans_prob_table)
    print(observe_prob_table)

