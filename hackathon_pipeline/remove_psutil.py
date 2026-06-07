import os

with open("run_retraining.py", "r") as f:
    code = f.read()

code = code.replace("import psutil\n", "")
code = code.replace("process = psutil.Process(os.getpid())\nstart_mem = process.memory_info().rss / (1024 * 1024)\n", "start_mem = 0\n")
code = code.replace("end_mem = process.memory_info().rss / (1024 * 1024)\n", "end_mem = 0\n")

with open("run_retraining.py", "w") as f:
    f.write(code)
