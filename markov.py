from sudachipy import tokenizer, dictionary
from collections import deque
import random
import re
import string
import os


class Markov:
    def __init__(self, file, order, sentence_num):
        self.file = file
        self.text = None
        self.order = order
        self.model = None
        self.sentence_num = sentence_num

    def load_file(self):
        print(f"load file: {self.file}")
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                self.text = f.read().strip()
        except UnicodeDecodeError:
            with open(self.file, "r", encoding="shift_jis") as f:
                self.text = f.read().strip()

    def wakati(self):
        tokenizer_obj = dictionary.Dictionary().create()
        mode = tokenizer.Tokenizer.SplitMode.C
        words = list()
        for line in self.bos_gen():
            parsed_text = [m.surface()
                           for m in tokenizer_obj.tokenize(line.rstrip("\n"), mode)]
            words.extend(parsed_text)
        return words

    def bos_gen(self):
        self.text = re.sub(r"\｜|《.*?》|［.*?］|　", "", self.text)
        bos = re.findall(r".*?。", self.text)
        for bos_ in bos:
            yield bos_

    def make_model(self):
        self.model = {}
        words = self.wakati()
        queue = deque([], self.order)
        queue.append("[BOS]")
        for markov_value in words:
            if len(queue) < self.order:
                queue.append(markov_value)
                continue

            if queue[-1] == "。":
                markov_key = tuple(queue)
                if markov_key not in self.model:
                    self.model[markov_key] = []
                self.model.setdefault(markov_key, []).append("[BOS]")
                queue.append("[BOS]")
            markov_key = tuple(queue)
            self.model.setdefault(markov_key, []).append(markov_value)
            queue.append(markov_value)

    def make_sentence(self, seed="[BOS]", max_words=5000):
        sentence_count = 0
        sentence_count_ = 0
        key_candidates = [key for key in self.model if key[0] == seed]
        if not key_candidates:
            print("Not find Keyword")
            return
        markov_key = random.choice(key_candidates)
        queue = deque(list(markov_key), len(list(self.model.keys())[0]))
        sentence = "".join(markov_key)
        for _ in range(max_words):
            markov_key = tuple(queue)
            next_word = random.choice(self.model[markov_key])
            sentence += next_word
            queue.append(next_word)

            if next_word == "。":
                sentence_count += 1
                if sentence_count == self.sentence_num:
                    break
        return sentence.replace(seed, "")

    def main(self):
        self.load_file()
        self.make_model()
        print("モデル生成完了。")


def prefix(data, count):
    if "!random" in data:
        for i in range(count):
            randstr = "".join(random.choices(
                string.ascii_letters + string.digits, k=10))
            data_ = data.replace("!random", randstr)
            yield data_
    elif "!markov" in data:
        file = "wagahaiwa_nekodearu.txt"
        markov = Markov(file, 50, 2)
        markov.main()
        for i in range(count):
            sentence = markov.make_sentence()
            data_ = data.replace("!markov", sentence)
            yield data_
    else:
        for i in range(count):
            yield data


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sentence_list = list()
    count = 5000
    data = "!markov"
    data2 = "!markov"
    for data_, data2_ in zip(prefix(data, count), prefix(data2, count)):
        print(f"{data_}\n{data2_}")
#    with open("./test.txt", "w", encoding="utf-8") as f:
#        f.write("\n".join(sentence_list))
