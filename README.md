# universal-partial-words

Code and data supporting the identification of upwords as described in [The Existence and Structure of Universal Partial Cycles](https://arxiv.org/abs/2310.13067). Motivated by the definition of upwords, this script searches the solution space for upwords of a given alphabet and subword length.

## Data

This folder contains a partial list of the upwords for the binary alphabet with subword length 8. Each line of the text file contains one upword.

## Code

This folder contains a python script that implements an algorithm developed by Daniel McGinnis that searches for upwords by randomly traversing a n-ary (mostly; every level corresponding to a wildcard character is unary) tree and pruning sections of the tree that cannot contain upwords for the alphabet with n characters of a given word length.
