import math, time
t = time.time()
pulse = (math.sin(t * 3.0) + 1.0) / 2.0
scale = 0.85 + pulse * 0.35
print("scale:", scale)
