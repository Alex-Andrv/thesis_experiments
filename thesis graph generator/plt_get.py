import matplotlib.pyplot as plt

arr = [100.0, 100.0, 100.0, 100.0, 87.47252747252747, 86.81318681318682, 81.71828171828172, 81.11888111888112, 81.27428127428128, 84.61538461538461, 89.01098901098901, 92.3076923076923, 97.8021978021978, 100.0, 100.0, 100.0, 100.0]
# arr = [100.0, 100.0, 100.0, 62.857142857142854, 55.824175824175825, 40.65934065934066, 39.960039960039964, 35.94405594405594, 43.04584304584304, 47.13286713286713, 65.03496503496503, 75.45787545787546, 97.8021978021978, 100.0, 100.0, 100.0, 100.0]
# arr = [100.0, 100.0, 100.0, 85.71428571428571, 97.14285714285714, 100.0, 100.0, 100.0, 100.0]
# arr = [100.0, 100.0, 26.666666666666668, 17.142857142857142, 4.835164835164836, 4.761904761904762, 2.3976023976023977, 2.237762237762238, 0.8080808080808081, 2.237762237762238, 2.3976023976023977, 4.761904761904762, 4.835164835164836, 17.142857142857142, 26.666666666666668, 100.0, 100.0]
# arr = [100.0, 100.0, 42.857142857142854, 42.857142857142854, 20.0, 42.857142857142854, 42.857142857142854, 100.0, 100.0]

fig, ax = plt.subplots(figsize=(20, 8))
ax.set_xlabel("k", fontsize=30)
ax.set_ylabel(r',', fontsize=30)
ax.grid(which="major", linewidth=1)
ax.plot(range(17), arr, c="red", label=r'$cnt * \binom{n}{k}^{-1} * 100$' + ", где cnt - количество успешно транслированных таблиц истинности")
plt.legend(loc='upper center', fontsize=15)
plt.savefig("С_4_k_3.jpg")
plt.show()