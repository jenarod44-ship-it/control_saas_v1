import os

for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            try:
                data = open(path, "r", encoding="latin-1").read()
                open(path, "w", encoding="utf-8").write(data)
                print("Convertido:", path)
            except:
                pass
