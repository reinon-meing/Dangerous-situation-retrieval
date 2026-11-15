"""Read /tmp/cs.csv (ros2 topic echo --csv) and print the message rate."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cs.csv"
ts = []
for line in open(path, encoding="utf-8", errors="replace"):
    p = line.strip().split(",")
    if len(p) < 9 or not p[0].isdigit() or not p[1].isdigit():
        continue
    ts.append(int(p[0]) + int(p[1]) / 1e9)

if len(ts) < 2:
    print("fewer than 2 messages in", path)
    sys.exit(1)

d = [b - a for a, b in zip(ts, ts[1:])]
T = ts[-1] - ts[0]
print("messages:", len(ts))
print("span: %.2f s" % T)
print("mean rate: %.0f Hz" % (len(d) / T))
print("gap min %.1f ms, max %.1f ms" % (min(d) * 1e3, max(d) * 1e3))
big = [x for x in d if x > 0.05]
print("gaps over 50 ms:", len(big))
