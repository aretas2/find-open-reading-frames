#!/usr/bin/env python

#Author: Aretas Gaspariunas

###PLEASE READ!###
##Detects ORFs in a DNA sequence provided as input FASTA file
##Assumes that the starting codon is ATG, accounts all 6 reading frames
##Ignores ORFs containing ambigious calls indicated by mark 'N'
##Please use the help flag for further information and options
###PLEASE READ!###

import argparse
import re
from Bio.Seq import Seq  # Biopython module; install with pip via CLI

class DNAsequence:
    def __init__(self, sequence, full_tag):
        self.sequence = sequence
        self.full_tag = full_tag
        self.tag = full_tag.split(' ')[0]

    find_codon_len = lambda self, codon: len(re.findall(codon, self.sequence))

    rev_comp = lambda self: str(Seq(self.sequence).reverse_complement())

    def count_GC(self):
        g_count = self.sequence.count('G')
        c_count = self.sequence.count('C')
        gc_count = float((g_count + c_count)) / float(len(self.sequence)) * 100

        return gc_count

    def find_ORF_regex(self, seq, min_nt_len, translate, table, nan, start_codon, strand_sense):
        # modify the regex to include the stop codon?
        # list comprehension, numpy

        pattern = re.compile(r'(?=({0}(?:...)*?)(?=TAG|TGA|TAA))'.format(start_codon))

        orf_list = []
        for m in pattern.finditer(seq):
            orf = m.group(1)
            if len(orf) >= min_nt_len:
                if nan is False and re.search('N', orf):
                    print ("Ignoring ORF starting at {0}; contains an ambigious NT call: 'N'".format(m.start()+1))
                elif m.start() % 3 == 0:
                    # print m.start(), m_end, 1, m.groups()[0]
                    orf_list.append((m.start(), strand_sense, 1, orf))
                elif (m.start() - 1) % 3 == 0:
                    # print m.start(), m_end, 2, m.groups()[0]
                    orf_list.append((m.start(), strand_sense, 2, orf))
                else:
                    # print m.start(), m_end, 3, m.groups()[0]
                    orf_list.append((m.start(), strand_sense, 3, orf))

        refine_orf_list = []
        longest = None
        for orf in orf_list:
            if longest is None:
                longest = orf
            elif len(longest[3]) + longest[0] == len(orf[3]) + orf[0] and len(orf[3]) > len(longest[3]):
                longest = orf
            elif len(longest[3]) + longest[0] != len(orf[3]) + orf[0]:
                refine_orf_list.append(longest)
                longest = orf
        refine_orf_list.append(longest)

        # formating and writting output
        final_orf_list = []
        if refine_orf_list == [None]:
            return ''
        else:
            for orf in refine_orf_list:
                if translate is False:
                    output = '{0}|STRAND_{1}_FRAME_{2}_LENGTH_{3}_START_{4}\n{5}\n'\
                        .format(self.tag.upper(), strand_sense, orf[2], len(orf[3]), orf[0] + 1, orf[3])
                    print (output)
                    final_orf_list.append(output)
                elif translate is True:
                    trans_seq = Seq(orf[3]).translate(table)
                    output = '{0}|STRAND_{1}_FRAME_{2}_LENGTH_{3}_START_{4}\n{5}\n'\
                        .format(self.tag.upper(), strand_sense, orf[2], len(trans_seq), orf[0] + 1, trans_seq)
                    print (output)
                    final_orf_list.append(output)

            final_string = ''.join(final_orf_list)
            return final_string

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--fasta',
        help='Specify the FASTA file with nucleotide sequence for ORF detection', required=True)
    parser.add_argument('-l', '--min_ORF_len',
        help='Specify the minimum nucleotide length for ORF detection; default = 300 NT', default=300, type=int)
    parser.add_argument('-p', '--protein',
        help='Include the flag if you wish to translate ORFs to peptide sequences', action='store_true')
    parser.add_argument('-t', '--table',
        help='Specify the translation table. Please see BioPython documentation', default=1, type=int)
    parser.add_argument('-s', '--stdout',
        help='Specify the flag for an output in a text file in FASTA format', action='store_true')
    parser.add_argument('-n', '--ignore_ambigious',
        help='Specify if ORFs with ambigious calls (marked by N) to be included in the output', action='store_true')
    parser.add_argument('-c', '--start_codon',
        help='Specify if you want to use a different start codon', default='ATG', type=str)
    args = parser.parse_args()

    try:
        with open(args.fasta, 'r') as f:
            first_line = f.readline().strip('\n')
            if first_line.startswith('>'):
                print ('The input file format seems to match FASTA! Proceeding...')
                second_line = f.readline().strip('\n').upper()
                if re.match(r'^A|^T|^C|^G', second_line):
                    sequence = second_line + f.read().replace('\n', '')
                    new_object = DNAsequence(sequence.upper(), first_line)

                    if args.stdout:
                        with open(args.fasta.split(".")[0] + '_ORF.fasta', 'w') as out_file:
                            out_file.write(new_object.find_ORF_regex(new_object.sequence,\
                                args.min_ORF_len, args.protein, args.table, args.ignore_ambigious, args.start_codon, '+1'))
                            out_file.write(new_object.find_ORF_regex(new_object.rev_comp(),\
                                args.min_ORF_len, args.protein, args.table, args.ignore_ambigious, args.start_codon, '-1'))
                    else:
                        new_object.find_ORF_regex(new_object.sequence, args.min_ORF_len, \
                            args.protein, args.table, args.ignore_ambigious, args.start_codon, '+1')
                        new_object.find_ORF_regex(new_object.rev_comp(), args.min_ORF_len, \
                            args.protein, args.table, args.ignore_ambigious, args.start_codon, '-1')
                        print (new_object.count_GC())
                else:
                    print ('The FASTA file does not contain a nucleotide sequence')
            else:
                print ('Wrong file format! The input file must be in FASTA format')
                exit()
    except IOError:
        print ('Could not open the file!', args.fasta)
