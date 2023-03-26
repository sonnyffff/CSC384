import os
import sys
import argparse

init_prob_table = {}


def read_files(training_list: list):
    init_occurrence = {}
    prev_word = ' '
    total_sentences = 0
    for file in training_list:
        training_file = open(file, "r")
        for line in training_file:
            parts = line.split(':')
            new_parts = []
            for part in parts:
                new_parts.append(part.strip())
            #  appears at the beginning of a sentence
            if prev_word == ' ' or prev_word == '.':
                total_sentences += 1
                if new_parts[1] not in init_occurrence:
                    init_occurrence[new_parts[1]] = 1
                else:
                    init_occurrence[new_parts[1]] += 1
            prev_word = new_parts[0]
    # calculate initial probability for pos
    for pos in init_occurrence:
        init_prob_table[pos] = init_occurrence[pos] / total_sentences
    print(total_sentences)
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
    print(read_files(['training1.txt']))
    print(init_prob_table)
