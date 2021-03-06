import subprocess
from svmutil import *
import sys

_DEBUG = False

#import sklearn.covariance

# In order to run this, you must install LIBSVM, add the LIBSVM
# python file to your PYTHONPATH and have LIBSVM in your PATH
# You also need scikit-learn installed (it's on pip)

#This is arbitrary
THRESHOLD_COEFF = 0.15

def get_two_class_model_file_name(input_file_name):
	return input_file_name + ".model"

def get_one_class_model_file_name(input_file_name):
	return input_file_name+ ".one_class_model"


def get_scale_param_file_name(input_file_name):
	return input_file_name +".scaling_params"

#Returns name of file to which scaled data is written
def scale(input_file_name, param_file_name=None):
	scaled_name = input_file_name + '.scaled'
	flag = "-r"
	params_path = param_file_name
	if(param_file_name is None):
		flag = "-s"
		params_path = get_scale_param_file_name(input_file_name)
	cmd = "svm-scale " + flag + " "+ params_path + " " + input_file_name + " > " + scaled_name
	print cmd
	subprocess.call(cmd, shell=True)
	print "Scaled data written to {0}".format(scaled_name)
	return scaled_name


# Assumes that scaled_input_file_name already scaled, and the parameters
# file has been created and has name get_scale_param_file_name(orig_file_name)
# Use one-class for novelty detection
def get_rbf_model(scaled_input_file_name, orig_file_name, is_one_class=False):
	labels, x = svm_read_problem(scaled_input_file_name)
	#-s 2 means one-class -t 2 means do RBF
	options = None
	if is_one_class:
		options = "-t 2"
	else:
		options = "-s 2 -t 2"
	model = svm_train(labels, x, options)
	model_file_name = None
	if is_one_class:
		model_file_name = get_two_class_model_file_name(orig_file_name)
	else:
		model_file_name = get_one_class_model_file_name(orig_file_name)
	print "Saved rbf model to {0}".format(model_file_name)
	svm_save_model(model_file_name, model)
	
	return model

def scale_and_train(input_file_name):
	scaled_name = None
	model = None
	scaled_name = scale(input_file_name)

	two_class_model = get_rbf_model(scaled_name, input_file_name, is_one_class = False)
	one_class_model = get_rbf_model(scaled_name, input_file_name, is_one_class = True)
	return (one_class_model, model)


def get_w_and_unimportant_dims(model):
		support_vectors = model.get_SV()
		coefs = model.get_sv_coef()

		SV_list = sv_to_list_of_lists(support_vectors)
		
		sgn = 1
		#get the first element of label (which is a ctype)
		if(model.label.contents.value < 0):
			sgn = -1

		w = get_w(coefs, labels, SV_list, sgn)

		#get the largest component (element) of the w vector
		largest_comp = 0
		for wi in w:
			if abs(wi) > largest_comp:
				largest_comp = abs(wi)

		unimportant_dim_nums = []
		for i in xrange(len(w)):
			if abs(w[i]) < THRESHOLD_COEFF * largest_comp:
				unimportant_dim_nums.append(i)

		return (w, unimportant_dim_nums)

#Get the vector for the hyperplane
def get_w(coefs, labels, SV_list, sgn):
	if len(coefs) == 0:
		return []

	w = [0 for i in xrange(len(SV_list[0]))]
	for i in xrange(len(coefs)):
		for j in xrange(len(w)):
			#coefs is stored as a list of tuples, where only the first elem matters
			w[j] += sgn * coefs[i][0] * SV_list[i][j]
	return w

def transpose(M):
	return zip(*M)

def get_num_features(SVs):
	highest_num = 0
	for SV in SVs:
		for key in SV.keys():
			if(key > highest_num):
				highest_num = key
	return highest_num

def sv_to_list_of_lists(SVs):
	num_features = get_num_features(SVs)
	outer_list = []
	for SV in SVs:
		result = [0 for key in xrange(num_features)]
		for feature_number in SV.keys():
			if feature_number > 0:
				result[feature_number - 1] = SV[feature_number]
		outer_list.append(result)
	return outer_list

#This is really just for testing
def main():
	if len(sys.argv) != 2:
		print "Usage : python train.py <name of input data file>"
		return
	(one_class_model, two_class_model) = scale_and_train(sys.argv[1])
	# test_file_name = 'data/test'

	# scaled_name = scale(test_file_name,get_scale_param_file_name(sys.argv[1]))
	# labels, x = svm_read_problem(scaled_name)

	# labels,accs,vals = svm_predict(labels, x, one_class_model)
	# print "labels: {0}\t vals:{1}\r\n".format(repr(labels), repr(vals))

if __name__ == "__main__":
	main()
