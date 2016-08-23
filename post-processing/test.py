def ngrams(input_str, n):
	words = input_str.split()
	results = []
	for word in words:
		if len(word) >= n:
			results += [word[i:i+n] for i in range(len(word) - (n - 1))]
		elif n > 0:
			results += ngrams(word, n - 1)

	return results


if __name__ == '__main__':
	print ngrams("sony experia z3+", 2)