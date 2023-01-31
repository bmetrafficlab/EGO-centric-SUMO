import subprocess
import os

N_RUNS = 5

TOWN = True
INGOLSTADT = False
LUXEMBOURG = False
TURIN = False

MICRO = False

if TOWN:
    for i in range(N_RUNS):
        subprocess.run(["python", "examples/town/simulate_town_cosim.py"])
        if os.path.exists("examples/town/results/town_cosim_results_" + str(i)):
            os.remove("examples/town/results/town_cosim_results_" + str(i))
        os.rename("examples/town/results/town_cosim_results", "examples/town/results/town_cosim_results_" + str(i))

    if MICRO:
        for i in range(N_RUNS):
            subprocess.run(["python", "examples/town/simulate_town_micro.py"])
            if os.path.exists("examples/town/results/town_micro_results_" + str(i)):
                os.remove("examples/town/results/town_micro_results_" + str(i))
            os.rename("examples/town/results/town_micro_results", "examples/town/results/town_micro_results_" + str(i))

if INGOLSTADT:
    for i in range(N_RUNS):
        subprocess.run(["python", "examples/ingolstadt/simulate_ingolstadt_cosim.py"])
        if os.path.exists("examples/ingolstadt/results/ingolstadt_cosim_results_" + str(i)):
            os.remove("examples/ingolstadt/results/ingolstadt_cosim_results_" + str(i))
        os.rename("examples/ingolstadt/results/ingolstadt_cosim_results", "examples/ingolstadt/results/ingolstadt_cosim_results_" + str(i))

    if MICRO:
        for i in range(N_RUNS):
            subprocess.run(["python", "examples/ingolstadt/simulate_ingolstadt_micro.py"])
            if os.path.exists("examples/ingolstadt/results/ingolstadt_micro_results_" + str(i)):
                os.remove("examples/ingolstadt/results/ingolstadt_micro_results_" + str(i))
            os.rename("examples/ingolstadt/results/ingolstadt_micro_results", "examples/ingolstadt/results/ingolstadt_micro_results_" + str(i))

if LUXEMBOURG:
    for i in range(N_RUNS):
        subprocess.run(["python", "examples/luxembourg/simulate_luxembourg_cosim.py"])
        if os.path.exists("examples/luxembourg/results/luxembourg_cosim_results_" + str(i)):
            os.remove("examples/luxembourg/results/luxembourg_cosim_results_" + str(i))
        os.rename("examples/luxembourg/results/luxembourg_cosim_results", "examples/luxembourg/results/luxembourg_cosim_results_" + str(i))

    if MICRO:
        for i in range(N_RUNS):
            subprocess.run(["python", "examples/luxembourg/simulate_luxembourg_micro.py"])
            if os.path.exists("examples/luxembourg/results/luxembourg_micro_results_" + str(i)):
                os.remove("examples/luxembourg/results/luxembourg_micro_results_" + str(i))
            os.rename("examples/luxembourg/results/luxembourg_micro_results", "examples/luxembourg/results/luxembourg_micro_results_" + str(i))

if TURIN:
    for i in range(N_RUNS):
        subprocess.run(["python", "examples/turin/simulate_turin_cosim.py"])
        if os.path.exists("examples/turin/results/turin_cosim_results_" + str(i)):
            os.remove("examples/turin/results/turin_cosim_results_" + str(i))
        os.rename("examples/turin/results/turin_cosim_results", "examples/turin/results/turin_cosim_results_" + str(i))

    if MICRO:
        for i in range(N_RUNS):
            subprocess.run(["python", "examples/turin/simulate_turin_micro.py"])
            if os.path.exists("examples/turin/results/turin_micro_results_" + str(i)):
                os.remove("examples/turin/results/turin_micro_results_" + str(i))
            os.rename("examples/turin/results/turin_micro_results", "examples/turin/results/turin_micro_results_" + str(i))
