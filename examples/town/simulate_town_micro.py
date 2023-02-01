import sys
import os
import libsumo as traci
import random
import time
import pickle


def main():

    # Establish connection
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    sumo_cmd = ["sumo", "-c", script_dir + "/town_scenario/town.sumocfg", "--start"]
    traci.start(sumo_cmd)
    edges = traci.edge.getIDList()

    # Initialize ego vehicle
    route_edges = []
    while not route_edges:
        start = random.choice(edges)
        destination = random.choice(edges)
        route_edges = list(traci.simulation.findRoute(start, destination).edges)
    traci.route.add('ego_route', route_edges)
    traci.vehicle.add('ego', 'ego_route')

    log_veh_count = []
    log_ego_speed = []
    log_num_lane_changes = 0
    log_headway = []
    log_step_time = []

    t1 = time.time()
    for i in range(3600):

        t1_step = time.time()
        # Step simulator
        traci.simulationStep()

        # Get every vehicle speed (to interact with the simulation)
        vehs = traci.vehicle.getIDList()
        speeds = []
        for veh in vehs:
            speeds.append(traci.vehicle.getSpeed(veh))

        # Reroute ego vehicle on a random route
        try:
            current_route = traci.vehicle.getRoute('ego')
            current_edge = traci.vehicle.getRoadID('ego')
        except traci.TraCIException as e:
            traci.vehicle.add('ego', 'ego_route')
            st_exception = True
            while st_exception:
                try:
                    target_edge = random.choice(edges)
                    traci.vehicle.changeTarget('ego', target_edge)
                    current_route = traci.vehicle.getRoute('ego')
                    if len(current_route) > 2:
                        st_exception = False
                        current_route = traci.vehicle.getRoute('ego')
                        current_edge = traci.vehicle.getRoadID('ego')
                except traci.TraCIException:
                    pass
        if current_edge == current_route[-2]:
            st_exception = True
            while st_exception:
                try:
                    target_edge = random.choice(edges)
                    traci.vehicle.changeTarget('ego', target_edge)
                    current_route = traci.vehicle.getRoute('ego')
                    if len(current_route) > 2:
                        st_exception = False
                except traci.TraCIException:
                    break
        t2_step = time.time()

        # logging
        log_veh_count.append(len(vehs))
        log_ego_speed.append(traci.vehicle.getSpeed('ego'))
        if traci.vehicle.couldChangeLane('ego', 1) or traci.vehicle.couldChangeLane('ego', -1):
            log_num_lane_changes += 1
        log_headway.append(traci.vehicle.getLeader('ego', 150))
        log_step_time.append(t2_step - t1_step)

    t2 = time.time()
    print(f"Simulation time: {t2 - t1} seconds")

    log_time = t2 - t1

    with open(script_dir + '/results/town_micro_results', 'wb') as f:
        pickle.dump([log_time, log_veh_count, log_ego_speed, log_num_lane_changes, log_headway, log_step_time], f)

    traci.close()


if __name__ == "__main__":
    main()
