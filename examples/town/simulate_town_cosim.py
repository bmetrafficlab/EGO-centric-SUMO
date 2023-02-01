import sys, os
import random
import time
import pickle
from libsumo_parallel import *

sys.setrecursionlimit(25000)


def micro_callback(ego_id, init, edges):

    if init:
        # Initialize ego vehicle
        route_edges = ['-74725439#1', '-74725439#0', '-74725447', '-467182459', '325782603#0', '325782603#1',
                       '325782603#2', '325782603#4', '765276434', '-300832373#5', '-765276438#1', '-765276438#0']
        libsumo.route.add('ego_route', route_edges)
        libsumo.vehicle.add(ego_id, 'ego_route')

    # Reroute ego vehicle on a random route
    try:
        current_route = libsumo.vehicle.getRoute(ego_id)
        current_edge = libsumo.vehicle.getRoadID(ego_id)
    except libsumo.TraCIException as e:
        libsumo.vehicle.add(ego_id, 'ego_route')
        st_exception = True
        while st_exception:
            try:
                target_edge = random.choice(edges)
                libsumo.vehicle.changeTarget(ego_id, target_edge)
                current_route = libsumo.vehicle.getRoute(ego_id)
                if len(current_route) > 2:
                    st_exception = False
                    current_route = libsumo.vehicle.getRoute(ego_id)
                    current_edge = libsumo.vehicle.getRoadID(ego_id)
            except libsumo.TraCIException:
                pass
    if current_edge == current_route[-2]:
        st_exception = True
        while st_exception:
            try:
                target_edge = random.choice(edges)
                libsumo.vehicle.changeTarget(ego_id, target_edge)
                current_route = libsumo.vehicle.getRoute(ego_id)
                if len(current_route) > 2:
                    st_exception = False
            except libsumo.TraCIException:
                break

    # Get every vehicle speed (to interact with the simulation)
    vehs = libsumo.vehicle.getIDList()
    speeds = []
    for veh in vehs:
        speeds.append(libsumo.vehicle.getSpeed(veh))

    # logging
    headway_thd = 150  # m
    veh_count = len(vehs)
    try:
        ego_speed = libsumo.vehicle.getSpeed(ego_id)
        if libsumo.vehicle.couldChangeLane(ego_id, 1) or libsumo.vehicle.couldChangeLane(ego_id, -1):
            changed_lane = 1
        else:
            changed_lane = 0
        headway = libsumo.vehicle.getLeader(ego_id, headway_thd)
    except libsumo.TraCIException:
        ego_speed = 0
        changed_lane = 0
        headway = None

    return veh_count, ego_speed, changed_lane, headway


def main():

    micro = True
    init = True
    ego_id = 'ego'

    # Get the road network as graph
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    sumo_cmd = ["sumo", "-c", script_dir + "/town_scenario/town.sumocfg", "--start"]
    network_path = script_dir + "/town_scenario/town.net.xml"
    parallel_conn = LibsumoParallelConnection(micro_callback, None)
    network = parallel_conn.parse_network(network_path)
    edge_objs = network.getEdges()
    edges = []
    for e in edge_objs:
        edges.append(e.getID())
    micro_cmd, meso_cmd = parallel_conn.create_meso(sumo_cmd)
    parallel_conn.start(micro_cmd, meso_cmd, ego_id, 250)

    log_veh_count = []
    log_ego_speed = []
    log_num_lane_changes = 0
    log_headway = []
    log_step_time = []

    t1 = time.time()
    for i in range(3600):

        t1_step = time.time()
        # Step both simulators
        if i == 0:
            parallel_conn.set_callback_arguments((ego_id, init, edges), micro)
        else:
            parallel_conn.set_callback_arguments((ego_id, not init, edges), micro)

        parallel_conn.simulation_step(network)

        veh_count, ego_speed, changed_lane, headway = parallel_conn.get_callback_returns(micro)
        t2_step = time.time()

        # logging
        log_veh_count.append(veh_count)
        log_ego_speed.append(ego_speed)
        log_num_lane_changes += changed_lane
        log_headway.append(headway)
        log_step_time.append(t2_step - t1_step)

    t2 = time.time()
    print(f"Simulation time: {t2 - t1} seconds")

    log_time = t2-t1

    with open(script_dir + "/results/town_cosim_results", 'wb') as f:
        pickle.dump([log_time, log_veh_count, log_ego_speed, log_num_lane_changes, log_headway, log_step_time], f)

    parallel_conn.close()


if __name__ == "__main__":
    main()
