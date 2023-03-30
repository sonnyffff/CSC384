import math
import os
import sys
import argparse
import time

ENDING_PUNCTUATIONS = {'.', '!', '?', ')', ']', '"'}
POS_TAGS = ['AJ0', 'AJC', 'AJS', 'AT0', 'AV0', 'AVP', 'AVQ', 'CJC', 'CJS', 'CJT', 'CRD', 'DPS', 'DT0', 'DTQ', 'EX0',
            'ITJ', 'NN0', 'NN1', 'NN2', 'NP0', 'ORD', 'PNI', 'PNP', 'PNQ', 'PNX', 'POS', 'PRF', 'PRP', 'PUL', 'PUN',
            'PUQ', 'PUR', 'TO0', 'UNC', 'VBB', 'VBD', 'VBG', 'VBI', 'VBN', 'VBZ', 'VDB', 'VDD', 'VDG', 'VDI', 'VDN',
            'VDZ', 'VHB', 'VHD', 'VHG', 'VHI', 'VHN', 'VHZ', 'VM0', 'VVB', 'VVD', 'VVG', 'VVI', 'VVN', 'VVZ', 'XX0',
            'ZZ0', 'AJ0-AV0', 'AJ0-VVN', 'AJ0-VVD', 'AJ0-NN1', 'AJ0-VVG', 'AVP-PRP', 'AVQ-CJS', 'CJS-PRP', 'CJT-DT0',
            'CRD-PNI', 'NN1-NP0', 'NN1-VVB', 'NN1-VVG', 'NN2-VVZ', 'VVD-VVN']
AMBIGUITY_TAGS = {'AJ0-AV0', 'AJ0-VVN', 'AJ0-VVD', 'AJ0-NN1', 'AJ0-VVG', 'AVP-PRP', 'AVQ-CJS', 'CJS-PRP', 'CJT-DT0',
                  'CRD-PNI', 'NN1-NP0', 'NN1-VVB', 'NN1-VVG', 'NN2-VVZ', 'VVD-VVN'}
# P(S_0)
init_prob_table = {}
# transition probability P(S_k | S_k-1)
# key: pos, value: dict{pos, probability}
trans_prob_table = {}
# observation probability P(E | S)
observe_prob_table = {}
# observation probability P(S | E)
reverse_prb_table = {}
occurrence_table = {}


def read_test_file(file_read: str, file_write: str):
    test_file = open(file_read, "r")
    sentences = []
    sols = []
    sentence = []
    prev = ' '
    for line in test_file:
        new_parts = line.strip()
        # TODO separate sentences
        if (prev in ENDING_PUNCTUATIONS and new_parts not in ENDING_PUNCTUATIONS):
            prob, prev = viterbi(sentence)
            largest_indexes = []
            largest_index = prob[len(sentence) - 1].index(max(prob[len(sentence) - 1]))
            largest_indexes.append(largest_index)
            for i in range(len(sentence) - 1, 0, -1):
                largest_index = prev[i][largest_index]
                largest_indexes.append(largest_index)
            largest_indexes.reverse()
            sol = [POS_TAGS[i] for i in largest_indexes]
            sentences.append(sentence)
            sols.append(sol)
            sentence = []
        sentence.append(new_parts)
        prev = new_parts[0]
    else:
        prob, prev = viterbi(sentence)
        largest_indexes = []
        largest_index = prob[len(sentence) - 1].index(max(prob[len(sentence) - 1]))
        largest_indexes.append(largest_index)
        for i in range(len(sentence) - 1, 0, -1):
            largest_index = prev[i][largest_index]
            largest_indexes.append(largest_index)
        largest_indexes.reverse()
        sol = [POS_TAGS[i] for i in largest_indexes]
        sentences.append(sentence)
        sols.append(sol)
    write_solution_file(file_write, sols, sentences)


def write_solution_file(file, sols, sentences):
    sol_file = open(file, "w+")
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
            sol_file.write(sentences[i][j] + ' ' + ':' + ' ' + sols[i][j])
            sol_file.write('\n')


def pos_tag_indexing():
    ret = {}
    for i in range(len(POS_TAGS)):
        ret[POS_TAGS[i]] = i
    return ret


def pos_tag_hard_coded_check(time_stamp, word: str):
    if time_stamp != 0:
        if word[0].isupper():
            return 'NP0'
    if word in {'an', 'the', 'An', 'a', 'A', 'The'}:
        return 'AT0'
    elif word in {'How', 'Why', 'Where'}:
        return 'AVQ'
    elif word in {'Or', 'and', 'or', 'nor', 'Nor', 'And', 'but'}:
        return 'CJC'
    elif word in {'if', 'Because', 'If', 'because', 'whether', 'Whether', 'although', 'Although'}:
        return 'CJS'
    elif word.isnumeric():
        return 'CRD'
    elif word in {'their', 'My', 'Your', 'your', 'our', 'Our', 'Their', 'my'}:
        return 'DPS'
    elif word == 'this':
        return 'DT0'
    elif word in {'you', 'we', 'me', 'us', 'yours', 'he', 'I', 'they', 'them', 'she', 'him', 'his'}:
        return 'PNP'
    elif word in {'himself', 'myself', 'oneself', 'itself', 'yourself', 'themselves', 'herself'}:
        return 'PNX'
    elif word in {'of'}:
        return 'PRF'
    elif word in {"'"}:
        return 'POS'
    elif word in {'(', '['}:
        return 'PUL'
    elif word in {'.', '!', ':', ';', ',', '-', '?'}:
        return 'PUN'
    elif word in {'"'}:
        return 'PUQ'
    elif word in {')', ']'}:
        return 'PUR'
    elif word == 'be' or word == 'Be':
        return 'VBI'
    elif word == 'is':
        return 'VBZ'
    elif word in {'not', 'Not', "n't"}:
        return 'XX0'
    elif len(word) == 1 and word.isalpha():
        return 'ZZ0'
    elif word in {'for', 'with'}:
        return 'PRP'
    elif word in {'yes', 'Oh'}:
        return 'ITJ'
    elif word == 'people':
        return 'NN0'
    elif word in {'last', 'first', 'next'}:
        return 'ORD'
    elif word in {'who'}:
        return 'PNQ'
    elif word in {"'m", 'are', 'am', "'re"}:
        return 'VBB'
    elif word in {'doing'}:
        return 'VDG'
    elif word in {'does'}:
        return 'VDZ'
    elif word in {'has'}:
        return 'VHZ'
    elif word in {'was'}:
        return 'VBD'
    elif word in {'being'}:
        return 'VBG'
    elif word in {'been'}:
        return 'VBN'
    elif word in {'did'}:
        return 'VDD'
    return 0


def pos_tag_defensive_check(time_stamp, word: str):
    if word in reverse_prb_table:
        return max(reverse_prb_table[word], key=reverse_prb_table[word].get)
    elif word == 'to':
        return 'PRP'
    elif word in {'back', 'out', 'up'}:
        return 'AVP'
    elif word == 'all':
        return 'DT0'
    elif word in {'what', 'which'}:
        return 'DTQ'
    return 0


def viterbi(sentence: list):
    pos_pos = pos_tag_indexing()
    pos_with_max_value = max(occurrence_table, key=occurrence_table.get)
    position_of_max = pos_pos[pos_with_max_value]
    prob = [[0 for j in range(len(POS_TAGS))] for i in range(len(sentence))]
    prev = [[0 for j in range(len(POS_TAGS))] for i in range(len(sentence))]
    # make guess by P(S|E)
    if sentence[0] in reverse_prb_table:
        max_tag = max(reverse_prb_table[sentence[0]], key=reverse_prb_table[sentence[0]].get)
        pos_max_tag = pos_pos[max_tag]
        for i in range(len(POS_TAGS)):
            prev[0][i] = "N"
            if i == pos_max_tag:
                prob[0][i] = 1
            else:
                prob[0][i] = 0
    # if the word never appears in the training file, choose the POS tag that occurs at initial most often
    else:
        for i in range(len(POS_TAGS)):
            prev[0][i] = "N"
            if POS_TAGS[i] in init_prob_table:
                prob[0][i] = init_prob_table[POS_TAGS[i]]
                if POS_TAGS[i] in observe_prob_table:
                    if sentence[0] in observe_prob_table[POS_TAGS[i]]:
                        prob[0][i] *= observe_prob_table[POS_TAGS[i]][sentence[0]]
            else:
                prob[0][i] = 0
    for t in range(1, len(sentence)):
        if pos_tag_hard_coded_check(t, sentence[t]) != 0:
            index = pos_pos[pos_tag_hard_coded_check(t, sentence[t])]
            for i in range(len(POS_TAGS)):
                if i == index:
                    prob[t][i] = 1
                else:
                    prob[t][i] = 0
                prev[t][i] = prob[t - 1].index(max(prob[t - 1]))
        else:
            for i in range(len(POS_TAGS)):
                x = -100
                max_val = -math.inf
                for j in range(len(POS_TAGS)):
                    if POS_TAGS[j] in trans_prob_table and POS_TAGS[i] in trans_prob_table[POS_TAGS[j]]:
                        temp_x = prob[t - 1][j] * trans_prob_table[POS_TAGS[j]][POS_TAGS[i]]
                        if POS_TAGS[i] in observe_prob_table and sentence[t] in observe_prob_table[POS_TAGS[i]]:
                            temp_x *= observe_prob_table[POS_TAGS[i]][sentence[t]]
                            if temp_x > max_val:
                                x = j
                                max_val = temp_x
                # if one of transition/observation probability is not found
                if x == -100:
                    flag = 0
                    if pos_tag_defensive_check(t, sentence[t]) != 0:
                        flag = 1
                        index = pos_pos[pos_tag_defensive_check(t, sentence[t])]
                        if index == i:
                            prob[t][i] = 1
                    elif i == position_of_max and flag == 0:
                        prob[t][i] = -math.inf
                    prev[t][i] = prob[t - 1].index(max(prob[t - 1]))
                else:
                    prob[t][i] = prob[t - 1][x] * trans_prob_table[POS_TAGS[x]][POS_TAGS[i]] * \
                                 observe_prob_table[POS_TAGS[i]][sentence[t]]
                    prev[t][i] = x
    return prob, prev


def translate_ambiguity(pos: str):
    if '-' in pos:
        parts = pos.split('-')
        return parts[1] + '-' + parts[0]


def read_files(training_list: list):
    init_occurrence = {}
    transition = {}
    observation = {}
    reverse = {}
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
            # check SE
            if new_parts[0] not in reverse:
                reverse[new_parts[0]] = {new_parts[1]: 1}
            else:
                if new_parts[1] not in reverse[new_parts[0]]:
                    reverse[new_parts[0]][new_parts[1]] = 1
                else:
                    reverse[new_parts[0]][new_parts[1]] += 1
            # check occurrence
            if new_parts[1] not in occurrence_table:
                occurrence_table[new_parts[1]] = 1
            else:
                occurrence_table[new_parts[1]] += 1
            total_transitions += 1
            if new_parts[1] not in ['PUL', 'PUQ', 'PUR']:
                prev_word = new_parts[0]
                # print(prev_word)
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
    # calculate SE
    for pos in reverse:
        reverse_prb_table[pos] = {}
        sample_size = 0
        for word in reverse[pos]:
            sample_size += reverse[pos][word]
        for word in reverse[pos]:
            reverse_prb_table[pos][word] = reverse[pos][word] / sample_size
    # print(transition)
    return init_occurrence


def read_all_tags():
    tag_file = open('postags.txt', "r")
    ret = []
    for line in tag_file:
        if len(line) > 2:
            parts = line.split()
            ret.append(parts[0])
    return ret


def generate_test(file, out):
    tag_file = open(file, "r")
    out_file = open(out, "w")
    for line in tag_file:
        parts = line.split()
        out_file.write(parts[0].strip())
        out_file.write('\n')


def check_matches(test_file, answer_file):
    test_file = open(test_file, 'r')
    answer_file = open(answer_file, 'r')
    matches = 0
    total = 0
    while 1:
        line1 = test_file.readline()
        line2 = answer_file.readline()
        if not line1:
            break
        if line1 == line2:
            matches += 1
        # else:
        #     print(total)
        total += 1
    print("accuracy: " + str(matches / total))


def check_hard_code_pos(pos):
    keys = set()
    print(observe_prob_table[pos])
    for key in observe_prob_table[pos]:
        if observe_prob_table[pos][key] > 0.5:
            print(key)
            print(reverse_prb_table[key])
    for key in observe_prob_table[pos]:
        if observe_prob_table[pos][key] > 0.5 and reverse_prb_table[key][pos] > 0.85:
            keys.add(key)
    if len(keys) != 0:
        print("elif word in ")
        print(keys)
        print("return " + "'" + pos + "'")


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

    # training_list = args.trainingfiles[0]
    # read_files(training_list)
    # read_test_file(args.testfile, args.outputfile)

    start = time.time()
    read_files(['training2.txt'])
    read_test_file('test1.txt', 'solution.txt')
    check_matches('solution.txt', 'answer1.txt')
    end = time.time()
    print("runtime: " + str(end - start))

    # generate_test('training2.txt', 'test2.txt')
    # print(init_prob_table)
    # print(len(POS_TAGS))
    # print(read_all_tags())
    # print(trans_prob_table)
    # for pos in POS_TAGS:
    #     check_hard_code_pos(pos)
    # print(reverse_prb_table)
