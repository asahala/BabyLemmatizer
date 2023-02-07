
gold = []
pred = []
with open('target-lemma-test.txt', 'r', encoding='utf-8') as f:
    for l in f.read().splitlines():
        gold.append(l)

with open('lemma-output.txt', 'r', encoding='utf-8') as f:
    for l in f.read().splitlines():
        pred.append(l)

tot = 0
right = 0
for p, g in zip(pred, gold):
    tot += 1
    if p == g:
        right += 1


print(right/tot)
    
