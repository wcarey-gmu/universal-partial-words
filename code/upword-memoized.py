#!/usr/bin/env python3
###############################################################################
#
#  Project:  {Upcycle Project Name}
#  Authors:  William Carey <wcarey1@gmu.edu>
#            
#  Acknowledgements: The algorithm that underlies this program was developed
#                    by Daniel McGinnis <{e-mail goes here}>.
# 
#  Copyright (c) 2023-2025, William Carey
#  SPDX-License-Identifier: MIT
#

import math
import random

# --- Configurable Parameters -------------------------------------------------

# The elements of @alphabet strings because you can't hash lists in Python, so
# you can't memoize functions whose arguments include a list, so if we want to
# use the current state of the upword as a key for our cache, we have to make 
# it a string.
alphabet = ["0","1"]
window_length = 8

randomize_walk = False
verbose_output = True

output_filename = "upwords.txt"

# --- Class to Check for Repeated Subwords ------------------------------------

class SubwordCache(object):
    def __init__(self, alphabet, window_length):
        self.mem_seenWords = {}
        self.alphabet = alphabet
        self.window_length = window_length
        self.max_entries = 9000
        
    def coveredSubwords(self, word):
        """For a given word, returns a set containing all the subwords that
           appear in the word. Relies on global variables @window_length and
           @alphabet and treats "w" as the wildcard character. Memoized by 
           @mem_seenWords.
        """
        if len(word) < window_length:
            return set()

        if word not in self.mem_seenWords:
            new_words = set()
            last_word = word[-window_length:]
            for a in alphabet:
                new_words.add(last_word.replace("w", a))
            self.mem_seenWords[word] = self.coveredSubwords(word[:-1]).union(new_words)

        return self.mem_seenWords[word]

    def size(self):
        """Returns the number of entries in the cache.
        """
        return len(self.mem_seenWords)
        
    def setMaxEntries(self, entries):
        """Sets the maximum number of entries in the cache. Each thousand 
           entries use about 1GB of memory for the binary alphabet, n=8 
           case.
        """
        self.max_entries = entries

    # The memoization blows up the ram usage, so we'll prune the cache every
    # so often. This is dark magic, so it'll take some profiling to determine
    # whether intelligently pruning the cache is more expensive than just 
    # blowing it away when it gets too big (for some value of too big).
    def expire(self, current_stack):
        """If the cache is too big, removes elements (but not the ones we still
           need) until it's smaller.
        """
        if len(self.mem_seenWords) < self.max_entries:
            return
    
        # We want to retain cache for the elements of the current processing
        # stack *less their last character*.
        truncated_keys = []
        for key in current_stack:
            truncated_keys.append(key[:-1])
    
        # You can't modify a dictionary while iterating over its keys, so we
        # have to build a list of bad keys, and then iterate over those, which
        # is slow, but better than making a copy of the cache, I think, because
        # the list of bad keys will be shorter?
        bad_keys = []
        for key in self.mem_seenWords:
            if not key in truncated_keys:
                bad_keys.append(key)
    
        for key in bad_keys:
            del self.mem_seenWords[key]

    # This is recursive, so might blow the stack on *really* long upwords.
    def hasRepeatedSubword(self, word):
        """ Returns true if word covers a subword of size @window_length
            for @alphabet more than once. Returns false otherwise. Recursive
            and memoized.
        """
        words = self.coveredSubwords(word[:-1])
        for a in alphabet:
            # Because we're pruning branches that duplicate words, we only
            # have to look at the *last* position and see if any of the words
            # created by the most recently added character appear more than
            # once.
            if word[-window_length:].replace("w", a) in words:
                return True
        return False

# --- Main Program Starts Here ------------------------------------------------

cache = SubwordCache(alphabet, window_length)

# We can start the upword with the first symbol in @alphabet without loss of 
# generality because alphabet rotations (bit flips in the binary case) produce
# elements of an equivalence class of upwords. So for the binary alphabet, this
# will find the half of the possible upwords that start with 0.
first_candidate = alphabet[0]

# An upword for $\A^n$ is $|\A|^n + (n-1)$ characters long. 
target_length = len(alphabet)**(window_length-1) + (window_length-1)

if verbose_output:
    print("Searching for universal partial words of length ", target_length)

# Rather than a random walk down the tree, this is going to use a stack to
# do a depth first search of the tree, favoring the lexicographically least 
# available branch (as given by the order of the elements of @alphabet).
# Note that if @randomize_walk is True, then this will take a random walk
# down the tree instead.
processing_stack = []
processing_stack.append(first_candidate)

upwords = []
longest = len(first_candidate)

# For some points in the parameter space, there are lots of upwords,
# so let's write them down in a file.
upword_list = open(output_filename, 'w')

while len(processing_stack) > 0:
    # Grab the top element of the stack and process it.
    word = processing_stack.pop()

    if (len(word) >= longest):
        longest = len(word)
        if verbose_output:
            print(len(processing_stack), cache.size(), longest)

    # If we're on a wildcard node, add that. Otherwise, add a speculative node
    # for each character in the alphabet. This bakes in a diamondicity of 1, 
    # with the wildcard appearing as the last character of each frame. If we 
    # want a bigger diamondicity, we could turn this into a function that 
    # returns the next set of symbols based on that logic.    
    if len(word) % window_length == window_length - 1:
        next_symbols = ['w']
    else:
        # This turns out to be rather expensive, but mixes up the order 
        # we traverse the tree. If we want the program to be strictly 
        # deterministic, we can comment out this line.
        # Are there probabilistic things that could help order this?
        if randomize_walk:
            random.shuffle(alphabet) 
        
        next_symbols = alphabet

    # A node is a leaf node is it has not children that could potentially
    # be upwords. (i.e. if every one of its potential children has a repeated
    # subword. Leaf nodes don't add any elements to the processing queue.)
    isLeafNode = True
    for c in next_symbols:
        candidate = word + c

        # We don't need to add the children of @word if they repeat seen
        # windows, because they will never have a child that is an upword.
        if cache.hasRepeatedSubword(candidate):
            continue

        isLeafNode = False
        if len(candidate) == target_length:
            # We found one! Actually this just means that we've found a 
            # word that's the right length and doesn't *double* cover anything.
            # We need to check the results to make sure they cover all the
            # possible words, which they might not if our wildcard rules are
            # too restrictive.
            upwords.append(candidate)
            if verbose_output:
                print("Found upword #", len(words),": ", candidate)
            upword_list.write(candidate)
            upword_list.write("\n")
        else:
            # Not long enough yet, so we'll put it on the stack to add
            # children and process more.
            processing_stack.append(candidate)

    # When we hit a leaf node, we'll prune the cache. In practice, this hits
    # enough to keep the cache from blowing up.
    if isLeafNode:
        cache.expire(processing_stack)

upword_list.close()