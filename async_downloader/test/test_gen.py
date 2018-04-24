# -*- coding:utf-8 -*-


abc = []

def gen():

    a = yield 1
    try:
        abc[0].throw(StopIteration)
    except Exception:
        print("Error")
    b = yield 2
    c = yield 3



g = gen()
abc.append(g)
for i in g:
    print(i)
