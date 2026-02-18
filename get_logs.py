import subprocess
with open("logs.txt", "w") as f:
    subprocess.run(["docker", "logs", "factu-backend-1"], stdout=f, stderr=f)
