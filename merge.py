
src = []
pred = []
with open('source-lemma-test.txt', 'r', encoding='utf-8') as f:
    for l in f.read().splitlines():
        src.append(l)

with open('source-output.txt', 'r', encoding='utf-8') as f:
    for l in f.read().splitlines():
        pred.append(l)

tot = 0
right = 0
with open('lemma-test.txt', 'w', encoding='utf-8') as f:
        
    for p, s in zip(pred, src):
        s = s.split('=')[0]
        s = s + '=' + p
    
        f.write(s + '\n')
    
