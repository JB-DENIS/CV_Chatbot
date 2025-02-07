import multiprocessing
import subprocess
import os


def start_backend():
    os.chdir("./backend")
    # subprocess.run(["uv", "sync"])
    subprocess.run(
        [
            "uv",
            "run",
            "fastapi",
            "run",
            "app/main.py",
            "--host",
            "0.0.0.0",
            "--port",
            "8088",
        ]
    )


def start_frontend():
    os.chdir("./frontend")
    # subprocess.run(["uv", "sync"])
    subprocess.run(
        [
            "uv",
            "run",
            "streamlit",
            "run",
            "app/main.py",
            "--server.port",
            "8888",
            "--server.address",
            "0.0.0.0",
        ]
    )


def main():
    backend_process = multiprocessing.Process(target=start_backend)
    frontend_process = multiprocessing.Process(target=start_frontend)

    backend_process.start()
    frontend_process.start()

    backend_process.join()
    frontend_process.join()


if __name__ == "__main__":
    main()
