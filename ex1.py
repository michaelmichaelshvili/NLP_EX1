from collections import defaultdict
import re
import math
from random import choices


class Ngram_Language_Model:
    """The class implements a Markov Language Model that learns a language model
        from a given text.
        It supoprts language generation and the evaluation of a given string.
        The class can be applied on both word level and character level.
    """

    def __init__(self, n=3, chars=False):
        """Initializing a language model object.
        Args:
            n (int): the length of the markov unit (the n of the n-gram). Defaults to 3.
            chars (bool): True iff the model consists of ngrams of characters rather then word tokens.
                          Defaults to False
        """
        self.n = n
        self.model_dict = defaultdict(
            int)  # a dictionary of the form {ngram:count}, holding counts of all ngrams in the specified text.
        self.use_chars = chars
        self.V = None  # size of vocabulary
        self.context_by_n = None  # dict from context size to all contexts in this size
        self.contexts_prob = []

    def build_model(self, text):
        """populates the instance variable model_dict.

            Args:
                text (str): the text to construct the model from.
        """
        splitted = self.split(text)
        self.context_by_n = {i: defaultdict(int) for i in range(0, self.n)}

        for n in range(1, self.n + 1):
            for idx in range(len(splitted) - 1, n - 2, -1):
                ngram = self.get_ngram_by_last_index(splitted, idx, n)
                context, last_gram = self.split_context_gram(ngram)
                n_size_context = self.context_by_n[len(self.split(context))]
                if context in n_size_context:
                    if last_gram in n_size_context[context]:
                        n_size_context[context][last_gram] += 1
                    else:
                        n_size_context[context][last_gram] = 1
                else:
                    n_size_context[context] = {last_gram: 1}
                if n == self.n:
                    self.model_dict[ngram] += 1
        self.V = len(self.model_dict)
        sum_per_context = [sum(self.context_by_n[self.n - 1][context].values()) for context in
                           self.context_by_n[self.n - 1]]
        sum_all_context = sum(sum_per_context)
        self.contexts_prob = [context_sum / sum_all_context for context_sum in sum_per_context]

    def get_ngram_by_last_index(self, s, idx, n_size):
        """
        Return ngram of size self.n ends at index idx

            Args:
                s (list): list of tokens from which the ngram is extracted
                idx (int): the index from which to start build (reversed) the ngram
                n_size (int) the size of the ngram
            Retutns:
                ngram (str). the ngram was extracted

        """
        if n_size is None:
            n_size = self.n
        if self.use_chars:
            return "".join(s[max(idx - n_size + 1, 0): idx + 1])
        else:
            return " ".join(s[max(idx - n_size + 1, 0): idx + 1])

    def split_context_gram(self, ngram):
        """Return context and last gram from given ngram.

            Args:
                ngram (str): text to split

            Returns:
                context (str): all tokens except the last
                last_gram (str): last token
        """
        if self.use_chars:
            context, last_gram = ngram[:-1], ngram[-1]
        else:
            ngram_split = ngram.split(" ")
            context, last_gram = self.join(ngram_split[:-1]), ngram_split[-1]
        return context, last_gram

    def get_model_dictionary(self):
        """Returns the dictionary class object
        """
        return self.model_dict

    def get_model_window_size(self):
        """Returning the size of the context window (the n in "n-gram")
        """
        return self.n

    def join(self, tokens):
        """
        Returns tokens joined into one string. join according to self.use_chars

            Args:
                tokens (list): tokens to join

            Return:
                str. join text.
        """
        if self.use_chars:
            return ''.join(tokens)
        else:
            return ' '.join(tokens)

    def split(self, text):
        """
        Returns tokens from text. the text is splitted according self.use_chars

            Args:
                text (str): string to split to tokens

            Return:
                List. Token list.
        """
        if self.use_chars:
            return list(text)
        else:
            if text == '':
                return []
            else:
                return text.split(' ')

    def generate(self, context=None, n=20):
        """Returns a string of the specified length, generated by applying the language model
        to the specified seed context. If no context is specified the context should be sampled
        from the models' contexts distribution. Generation should stop before the n'th word if the
        contexts are exhausted. If the length of the specified context exceeds (or equal to)
        the specified n, the method should return the a prefix of length n of the specified context.

            Args:
                context (str): a seed context to start the generated string from. Defaults to None
                n (int): the length of the string to be generated.

            Return:
                String. The generated text.

        """
        context_len = 0 if context is None else len(self.split(context))
        if context_len > n:  # context is longer than n - return the first n tokens
            return self.join(self.split(context)[:n])
        if context_len < self.n - 1:  # The context needs to be completed
            new_context = self.get_initial_context(context)
            if new_context is None:  # context is exhausted
                return context
            context = new_context

        final_text = self.split(context)
        if len(final_text) > n:
            return self.join(self.split(context)[:n])
        while len(final_text) < n:
            next_gram = self.get_next_gram(final_text)
            if next_gram is None:  # context is exhausted
                return self.join(final_text)
            final_text.append(next_gram)
        return self.join(final_text)

    def get_initial_context(self, init_context):
        """
            Sample the models' context distribution to get an initial context.
            If the initial context is exists, complete with the next grams we have see in the text.

            Args:
                init_context (str). The context that we got and need to evaluate from it
            Returns:
                String. An initial context

        """
        if init_context is None:
            return choices(list(self.context_by_n[self.n - 1].keys()), self.contexts_prob)[0]
        else:
            optional_context = [context for context in self.context_by_n[self.n - 1] if
                                context.startswith(init_context)]
            if len(optional_context) == 0:
                return None
            else:
                return choices(optional_context)[0]

    def get_next_gram(self, context):
        """
        Get the next gram according to context. the gram is chosen by weighted choice. The weight is number of apperance
        of the gram after the context.

        Returns:
            String. the chosen gram to be appropriate to the context.

        """
        if self.n == 1:
            last_context = ''
        else:
            last_context = self.join(context[-(self.n - 1):])
        last_context_len = len(self.split(last_context))
        if last_context not in self.context_by_n[self.n - 1]:
            return None
        possible_gram = self.context_by_n[self.n - 1][last_context].keys()
        possible_gram_probs_sum = sum(self.context_by_n[self.n - 1][last_context].values())
        possible_gram_probs = [self.context_by_n[self.n - 1][last_context][gram] / possible_gram_probs_sum for
                               gram in
                               possible_gram]
        return choices(list(self.context_by_n[self.n - 1][last_context].keys()), possible_gram_probs)[0]

    def evaluate(self, text):
        """Returns the log-likelihood of the specified text to be a product of the model.
           Laplace smoothing should be applied if necessary.
           I chose to use stupid backoff. i.e calculate also kgrams where k<n, so their context is not of size n-1.
           I think that is more accurate method because the first grams are also important to understand the prob
           of the text to be evaluate by the model.
           Args:
               text (str): Text to evaluate.

           Returns:
               Float. The float should reflect the (log) probability.
        """
        splitted = self.split(text)
        prob = 0

        for i in range(len(splitted) - 1, -1, -1):
            ngram = self.get_ngram_by_last_index(splitted, i, None)
            context, last_gram = self.split_context_gram(ngram)
            context_len = len(self.split(context))
            if context in self.context_by_n[context_len] and last_gram in self.context_by_n[context_len][context]:
                prob += math.log(self.get_prob(context, last_gram))
            else:
                prob += math.log(self.smooth(context))
        return prob

    def get_prob(self, context, last_gram):
        """
        Calculate the probability to ngram. The probability the the last gram will be after the context.
        The calculation is the (number of occurrences of the ngram) / (number of occurrences of the context)

            Args:
                context (str): the context of the ngram we want to calculate its prob
                last_gram (str): the last_gram of the ngram we want to calculate its prob

            Returns:
                prob (float): the probability of the ngram to be evaluate.
        """
        context_len = len(self.split(context))
        c_ngram = self.context_by_n[context_len][context][last_gram]
        c_context = sum(self.context_by_n[context_len][context].values())
        return c_ngram / c_context

    def smooth(self, context):
        """Returns the smoothed (Laplace) probability of the specified ngram.

            Args:
                context (str): the context of the ngram we want to calculate its prob

            Returns:
                float. The smoothed probability.
        """
        c_context = 0
        context_len = len(self.split(context))
        if context in self.context_by_n[context_len]:
            c_context = sum(self.context_by_n[context_len][context].values())
        return 1 / (c_context + self.V)


def normalize_text(text, lower=True, pad_punc=True):
    """Returns a normalized version of the specified string.
      You can add default parameters as you like (they should have default values!)
      You should explain your decisions in the header of the function.

      Args:
        text (str): the text to normalize
        lower (bool): if we want the model to learn only lower case tokens. Defaults to True.
        I chose to use this, because in English the first word in sentence is capital but has same meaning like th word
        without capital.
        pad_punc (bool): if treat punctuation like grams and padding them with white space. Defaults to True.
        I chose to use this because a dot or comma not supposed to influence the meaning.
      Returns:
        string. the normalized text.
    """
    normalized_text = text
    if lower:
        normalized_text = normalized_text.lower()
    if pad_punc:
        normalized_text = re.sub('(?<! )(?=[.,!?()!@#$%^&*\n\"])|(?<=[.,!?()!@#$%^&*\n\"])(?! )', r' ',
                                 normalized_text).strip()
    return normalized_text


def who_am_i():  # this is not a class method
    """Returns a ductionary with your name, id number and email. keys=['name', 'id','email']
        Make sure you return your own info!
    """
    return {'name': 'Michael Michaelshvili', 'id': '318949443', 'email': 'michmich@post.bgu.ac.il'}
