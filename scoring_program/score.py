#!/usr/bin/env python

# Scoring program for the AutoML challenge
# Isabelle Guyon and Arthur Pesah, ChaLearn, August 2014-November 2016

# ALL INFORMATION, SOFTWARE, DOCUMENTATION, AND DATA ARE PROVIDED "AS-IS".
# ISABELLE GUYON, CHALEARN, AND/OR OTHER ORGANIZERS OR CODE AUTHORS DISCLAIM
# ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY PARTICULAR PURPOSE, AND THE
# WARRANTY OF NON-INFRINGEMENT OF ANY THIRD PARTY'S INTELLECTUAL PROPERTY RIGHTS.
# IN NO EVENT SHALL ISABELLE GUYON AND/OR OTHER ORGANIZERS BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF SOFTWARE, DOCUMENTS, MATERIALS,
# PUBLICATIONS, OR INFORMATION MADE AVAILABLE FOR THE CHALLENGE.

# Some libraries and options
import os
import errno
from sys import argv

import libscores
import my_metric
import yaml
from libscores import *

# Default I/O directories:
root_dir = "../"
default_solution_dir = root_dir + "sample_data"
default_prediction_dir = root_dir + "sample_result_submission"
default_score_dir = root_dir + "scoring_output"

# Debug flag 0: no debug, 1: show all scores, 2: also show version amd listing of dir
debug_mode = 0

# Constant used for a missing score
missing_score = -0.999999

# Version number
scoring_version = 1.0

def _HERE(*args):
    h = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(h, *args)


def _load_scoring_function(n=1):
    with open(_HERE('metric_'+str(n)+'.txt'), 'r') as f:
        metric_name = f.readline().strip()
        try:
            score_func = getattr(libscores, metric_name)
        except:
            score_func = getattr(my_metric, metric_name)
        return metric_name, score_func

# =============================== MAIN ========================================
if __name__ == "__main__":

    #### INPUT/OUTPUT: Get input and output directory names
    if len(argv) == 1:  # Use the default data directories if no arguments are provided
        solution_dir = default_solution_dir
        prediction_dir = default_prediction_dir
        score_dir = default_score_dir
    elif len(argv) == 3: # The current default configuration of Codalab
        solution_dir = os.path.join(argv[1], 'ref')
        prediction_dir = os.path.join(argv[1], 'res')
        score_dir = argv[2]
    elif len(argv) == 4:
        solution_dir = argv[1]
        prediction_dir = argv[2]
        score_dir = argv[3]
    else:
        swrite('\n*** WRONG NUMBER OF ARGUMENTS ***\n\n')
        exit(1)

    # Create the output directory, if it does not already exist and open output files
    mkdir(score_dir)
    score_file = open(os.path.join(score_dir, 'scores.txt'), 'wb')

    # Get the metric
    metric_name_1, scoring_function_1 = _load_scoring_function(1)
    metric_name_2, scoring_function_2 = _load_scoring_function(2)
    metric_name_3, scoring_function_3 = _load_scoring_function(3)

    # Get all the solution files from the solution directory
    solution_names = sorted(ls(os.path.join(solution_dir, '*.solution')))
    print(solution_names)

    # Loop over files in solution directory and search for predictions with extension .predict having the same basename
    for solution_file in solution_names:
        score = missing_score # default score value
        # Extract the dataset name from the file name
        basename = solution_file[-solution_file[::-1].index(filesep):-solution_file[::-1].index('.')-1]
        try:
            # Get the last prediction from the res subdirectory (must contains basename)
            predict_files = ls(os.path.join(prediction_dir, basename + '*'))
            predict_files = predict_files + ls(os.path.join(prediction_dir, '*', basename + '*')) # robust to sub-directory

            if (predict_files == []):
                print('File not found: {}'.format(basename))
                prediction = None
            else:
                predict_file = predict_files[-1]
                # Read the solution and prediction values into numpy arrays
                solution = read_array(solution_file)
                prediction = read_array(predict_file)
                if(solution.shape!=prediction.shape):
                    print('Bad prediction shape: {} != {}'.format(prediction.shape, solution.shape))

            # Chose metric regarding task (ad-hoc)
            if basename=='classification':
                scoring_function, metric_name = scoring_function_1, metric_name_1
            elif basename=='selection':
                scoring_function, metric_name = scoring_function_2, metric_name_2
            elif basename=='causal':
                scoring_function, metric_name = scoring_function_2, metric_name_2
            else:
                raise Exception('Unknown solution file basename: {}'.format(basename))

            try:
                # Compute the score prescribed by the metric file
                score = scoring_function(solution, prediction)
            except:
                print('Could not compute {} score'.format(basename))

            print("======= " + basename.capitalize() + ": score(" + metric_name + ")=%0.12f =======" % score)
            # Write score corresponding to selected task and metric to the output file
            score_file.write(metric_name + ": %0.12f\n" % score) # classification

            if debug_mode>0:
                scores = compute_all_scores(solution, prediction)

        except Exception as e:
            print e

    # End loop for solution_file in solution_names

    # Read the execution time and add it to the scores:
    #try:
    #    metadata = yaml.load(open(os.path.join(prediction_dir, 'metadata'), 'r'))
    #    score_file.write("Duration: %0.6f\n" % metadata['elapsedTime'])
    #except:
    #    score_file.write("Duration: 0\n")

    score_file.close()

    # Lots of debug stuff
    if debug_mode>1:
        swrite('\n*** SCORING PROGRAM: PLATFORM SPECIFICATIONS ***\n\n')
        show_platform()
        show_io(input_dir, output_dir)
        show_version(scoring_version)

    #exit(0)
