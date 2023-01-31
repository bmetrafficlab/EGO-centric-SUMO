import math
import pickle
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({'font.size': 16})


def create_cdf(data, bins):
    count = [0] * bins
    bins = list(range(bins))
    for d in data:
        for b in bins:
            if d < b:
                count[b - 1] += 1
                break
    sum_count = sum(count)
    count_norm = []
    for c in count:
        count_norm.append(c / sum_count)
    return np.cumsum(count_norm)


def create_headway(data):
    headway = []
    no_leader_ctr = 0
    for d in data:
        if d is None:
            no_leader_ctr += 1
        else:
            headway.append(d[1])
    return headway, no_leader_ctr

def eval_all(cosim_0_path, cosim_1_path, cosim_2_path, cosim_3_path, cosim_4_path,
             micro_0_path, micro_1_path, micro_2_path, micro_3_path, micro_4_path,
             SAVE):
    cosim_0 = pickle.load(open(cosim_0_path, 'rb'))
    cosim_1 = pickle.load(open(cosim_1_path, 'rb'))
    cosim_2 = pickle.load(open(cosim_2_path, 'rb'))
    cosim_3 = pickle.load(open(cosim_3_path, 'rb'))
    cosim_4 = pickle.load(open(cosim_4_path, 'rb'))

    micro_0 = pickle.load(open(micro_0_path, 'rb'))
    micro_1 = pickle.load(open(micro_1_path, 'rb'))
    micro_2 = pickle.load(open(micro_2_path, 'rb'))
    micro_3 = pickle.load(open(micro_3_path, 'rb'))
    micro_4 = pickle.load(open(micro_4_path, 'rb'))

    # Simulation time:
    mean_sim_time_cosim = np.mean([cosim_0[0], cosim_1[0], cosim_2[0], cosim_3[0], cosim_4[0]])
    mean_sim_time_micro = np.mean([micro_0[0], micro_1[0], micro_2[0], micro_3[0], micro_4[0]])

    std_sim_time_cosim = np.std([cosim_0[0], cosim_1[0], cosim_2[0], cosim_3[0], cosim_4[0]])
    std_sim_time_micro = np.std([micro_0[0], micro_1[0], micro_2[0], micro_3[0], micro_4[0]])

    print(f'Mean simulation time - cosim = {mean_sim_time_cosim} s, with std = {std_sim_time_cosim} s.')
    print(f'Mean simulation time - micro = {mean_sim_time_micro} s, with std = {std_sim_time_micro} s.')

    # Vehicle counts
    veh_count_cosim_0 = cosim_0[1]
    veh_count_cosim_1 = cosim_1[1]
    veh_count_cosim_2 = cosim_2[1]
    veh_count_cosim_3 = cosim_3[1]
    veh_count_cosim_4 = cosim_4[1]

    veh_count_micro_0 = micro_0[1]
    veh_count_micro_1 = micro_1[1]
    veh_count_micro_2 = micro_2[1]
    veh_count_micro_3 = micro_3[1]
    veh_count_micro_4 = micro_4[1]

    cdf_limit_cosim = max(veh_count_cosim_0)
    cdf_limit_micro = max(veh_count_micro_0)

    cdf_veh_count_cosim_0 = create_cdf(veh_count_cosim_0, cdf_limit_cosim)
    cdf_veh_count_cosim_1 = create_cdf(veh_count_cosim_1, cdf_limit_cosim)
    cdf_veh_count_cosim_2 = create_cdf(veh_count_cosim_2, cdf_limit_cosim)
    cdf_veh_count_cosim_3 = create_cdf(veh_count_cosim_3, cdf_limit_cosim)
    cdf_veh_count_cosim_4 = create_cdf(veh_count_cosim_4, cdf_limit_cosim)

    cdf_veh_count_micro_0 = create_cdf(veh_count_micro_0, cdf_limit_micro)
    cdf_veh_count_micro_1 = create_cdf(veh_count_micro_1, cdf_limit_micro)
    cdf_veh_count_micro_2 = create_cdf(veh_count_micro_2, cdf_limit_micro)
    cdf_veh_count_micro_3 = create_cdf(veh_count_micro_3, cdf_limit_micro)
    cdf_veh_count_micro_4 = create_cdf(veh_count_micro_4, cdf_limit_micro)

    cdf_veh_count_cosim_aggregated = np.array([cdf_veh_count_cosim_0, cdf_veh_count_cosim_1, cdf_veh_count_cosim_2, cdf_veh_count_cosim_3, cdf_veh_count_cosim_4])
    cdf_veh_count_micro_aggregated = np.array([cdf_veh_count_micro_0, cdf_veh_count_micro_1, cdf_veh_count_micro_2, cdf_veh_count_micro_3, cdf_veh_count_micro_4])

    cdf_mean_veh_count_cosim = np.mean(cdf_veh_count_cosim_aggregated, axis=0)
    cdf_mean_veh_count_micro = np.mean(cdf_veh_count_micro_aggregated, axis=0)

    cdf_std_veh_count_cosim = np.std(cdf_veh_count_cosim_aggregated, axis=0)
    cdf_std_veh_count_micro = np.std(cdf_veh_count_micro_aggregated, axis=0)

    # Plot CDFs
    ax = plt.axes()
    ax.plot(range(cdf_limit_cosim), cdf_mean_veh_count_cosim, lw=2, color='blue')
    ax.fill_between(range(cdf_limit_cosim), cdf_mean_veh_count_cosim + cdf_std_veh_count_cosim, cdf_mean_veh_count_cosim - cdf_std_veh_count_cosim, facecolor='blue', alpha=0.3)
    ax.set_xlabel('Vehicles in the simulation')
    ax.set_ylabel('CDF of vehicle counts')
    ax.set_xlim(0, cdf_limit_cosim)
    ax.set_ylim(0, 1)
    if SAVE:
        plt.savefig('veh_num_cosim.pdf')
        plt.close()
    else:
        plt.show()

    ax = plt.axes()
    ax.plot(range(cdf_limit_micro), cdf_mean_veh_count_micro, lw=2, color='red')
    ax.fill_between(range(cdf_limit_micro), cdf_mean_veh_count_micro + cdf_std_veh_count_micro, cdf_mean_veh_count_micro - cdf_std_veh_count_micro, facecolor='red', alpha=0.3)
    ax.set_xlabel('Vehicles in the simulation')
    ax.set_ylabel('CDF of vehicle counts')
    ax.set_xlim(0, cdf_limit_micro)
    ax.set_ylim(0, 1)
    if SAVE:
        plt.savefig('veh_num_micro.pdf')
        plt.close()
    else:
        plt.show()

    # EGO speed
    ego_speed_cosim_0 = cosim_0[2]
    ego_speed_cosim_1 = cosim_1[2]
    ego_speed_cosim_2 = cosim_2[2]
    ego_speed_cosim_3 = cosim_3[2]
    ego_speed_cosim_4 = cosim_4[2]

    ego_speed_micro_0 = micro_0[2]
    ego_speed_micro_1 = micro_1[2]
    ego_speed_micro_2 = micro_2[2]
    ego_speed_micro_3 = micro_3[2]
    ego_speed_micro_4 = micro_4[2]

    cdf_ego_speed_cosim_0 = create_cdf(ego_speed_cosim_0, 30)
    cdf_ego_speed_cosim_1 = create_cdf(ego_speed_cosim_1, 30)
    cdf_ego_speed_cosim_2 = create_cdf(ego_speed_cosim_2, 30)
    cdf_ego_speed_cosim_3 = create_cdf(ego_speed_cosim_3, 30)
    cdf_ego_speed_cosim_4 = create_cdf(ego_speed_cosim_4, 30)

    cdf_ego_speed_micro_0 = create_cdf(ego_speed_micro_0, 30)
    cdf_ego_speed_micro_1 = create_cdf(ego_speed_micro_1, 30)
    cdf_ego_speed_micro_2 = create_cdf(ego_speed_micro_2, 30)
    cdf_ego_speed_micro_3 = create_cdf(ego_speed_micro_3, 30)
    cdf_ego_speed_micro_4 = create_cdf(ego_speed_micro_4, 30)

    cdf_ego_speed_cosim_aggregated = np.array([cdf_ego_speed_cosim_0, cdf_ego_speed_cosim_1, cdf_ego_speed_cosim_2, cdf_ego_speed_cosim_3, cdf_ego_speed_cosim_4])
    cdf_ego_speed_micro_aggregated = np.array([cdf_ego_speed_micro_0, cdf_ego_speed_micro_1, cdf_ego_speed_micro_2, cdf_ego_speed_micro_3, cdf_ego_speed_micro_4])

    cdf_mean_ego_speed_cosim = np.mean(cdf_ego_speed_cosim_aggregated, axis=0)
    cdf_mean_ego_speed_micro = np.mean(cdf_ego_speed_micro_aggregated, axis=0)

    cdf_std_ego_speed_cosim = np.std(cdf_ego_speed_cosim_aggregated, axis=0)
    cdf_std_ego_speed_micro = np.std(cdf_ego_speed_micro_aggregated, axis=0)

    ax = plt.axes()
    ax.plot(range(30), cdf_mean_ego_speed_cosim, lw=2, color='blue', label='co-simulation')
    ax.fill_between(range(30), cdf_mean_ego_speed_cosim + cdf_std_ego_speed_cosim, cdf_mean_ego_speed_cosim - cdf_std_ego_speed_cosim, facecolor='blue', alpha=0.3)
    ax.plot(range(30), cdf_mean_ego_speed_micro, lw=2, color='red', label='microscopic')
    ax.fill_between(range(30), cdf_mean_ego_speed_micro + cdf_std_ego_speed_micro, cdf_mean_ego_speed_micro - cdf_std_ego_speed_micro, facecolor='red', alpha=0.3)
    ax.set_xlabel('Vehicle speed (m/s)')
    ax.set_ylabel('CDF of EGO vehicle speed')
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1)
    ax.legend()
    if SAVE:
        plt.savefig('speed.pdf')
        plt.close()
    else:
        plt.show()

    # Lane changes:
    mean_lane_changes_cosim = np.mean([cosim_0[3], cosim_1[3], cosim_2[3], cosim_3[3], cosim_4[3]])
    mean_lane_changes_micro = np.mean([micro_0[3], micro_1[3], micro_2[3], micro_3[3], micro_4[3]])

    std_lane_changes_cosim = np.std([cosim_0[3], cosim_1[3], cosim_2[3], cosim_3[3], cosim_4[3]])
    std_lane_changes_micro = np.std([micro_0[3], micro_1[3], micro_2[3], micro_3[3], micro_4[3]])

    print(f'Mean number of lane changes by the EGO vehicle - cosim = {mean_lane_changes_cosim}, with std = {std_lane_changes_cosim}.')
    print(f'Mean number of lane changes by the EGO vehicle - micro = {mean_lane_changes_micro}, with std = {std_lane_changes_micro}.')

    # Headways
    headway_cosim_0, no_leader_cosim_0 = create_headway(cosim_0[4])
    headway_cosim_1, no_leader_cosim_1 = create_headway(cosim_1[4])
    headway_cosim_2, no_leader_cosim_2 = create_headway(cosim_2[4])
    headway_cosim_3, no_leader_cosim_3 = create_headway(cosim_3[4])
    headway_cosim_4, no_leader_cosim_4 = create_headway(cosim_4[4])

    headway_micro_0, no_leader_micro_0 = create_headway(micro_0[4])
    headway_micro_1, no_leader_micro_1 = create_headway(micro_1[4])
    headway_micro_2, no_leader_micro_2 = create_headway(micro_2[4])
    headway_micro_3, no_leader_micro_3 = create_headway(micro_3[4])
    headway_micro_4, no_leader_micro_4 = create_headway(micro_4[4])

    # No leader
    mean_no_leader_cosim = np.mean([no_leader_cosim_0, no_leader_cosim_1, no_leader_cosim_2, no_leader_cosim_3, no_leader_cosim_4])
    mean_no_leader_micro = np.mean([no_leader_micro_0, no_leader_micro_1, no_leader_micro_2, no_leader_micro_3, no_leader_micro_4])

    std_no_leader_cosim = np.std([no_leader_cosim_0, no_leader_cosim_1, no_leader_cosim_2, no_leader_cosim_3, no_leader_cosim_4])
    std_no_leader_micro = np.std([no_leader_micro_0, no_leader_micro_1, no_leader_micro_2, no_leader_micro_3, no_leader_micro_4])

    print(f'Mean time of no leader - cosim = {mean_no_leader_cosim} s, with std = {std_no_leader_cosim} s.')
    print(f'Mean time of no leader - micro = {mean_no_leader_micro} s, with std = {std_no_leader_micro} s.')

    # Headway CDF

    cdf_headway_cosim_0 = create_cdf(headway_cosim_0, 150)
    cdf_headway_cosim_1 = create_cdf(headway_cosim_1, 150)
    cdf_headway_cosim_2 = create_cdf(headway_cosim_2, 150)
    cdf_headway_cosim_3 = create_cdf(headway_cosim_3, 150)
    cdf_headway_cosim_4 = create_cdf(headway_cosim_4, 150)

    cdf_headway_micro_0 = create_cdf(headway_micro_0, 150)
    cdf_headway_micro_1 = create_cdf(headway_micro_1, 150)
    cdf_headway_micro_2 = create_cdf(headway_micro_2, 150)
    cdf_headway_micro_3 = create_cdf(headway_micro_3, 150)
    cdf_headway_micro_4 = create_cdf(headway_micro_4, 150)

    cdf_headway_cosim_aggregated = np.array([cdf_headway_cosim_0, cdf_headway_cosim_1, cdf_headway_cosim_2, cdf_headway_cosim_3, cdf_headway_cosim_4])
    cdf_headway_micro_aggregated = np.array([cdf_headway_micro_0, cdf_headway_micro_1, cdf_headway_micro_2, cdf_headway_micro_3, cdf_headway_micro_4])

    cdf_mean_headway_cosim = np.mean(cdf_headway_cosim_aggregated, axis=0)
    cdf_mean_headway_micro = np.mean(cdf_headway_micro_aggregated, axis=0)

    cdf_std_headway_cosim = np.std(cdf_headway_cosim_aggregated, axis=0)
    cdf_std_headway_micro = np.std(cdf_headway_micro_aggregated, axis=0)

    ax = plt.axes()
    ax.plot(range(150), cdf_mean_headway_cosim, lw=2, color='blue', label='co-simulation')
    ax.fill_between(range(150), cdf_mean_headway_cosim + cdf_std_headway_cosim, cdf_mean_headway_cosim - cdf_std_headway_cosim, facecolor='blue', alpha=0.3)
    ax.plot(range(150), cdf_mean_headway_micro, lw=2, color='red', label='microscopic')
    ax.fill_between(range(150), cdf_mean_headway_micro + cdf_std_headway_micro, cdf_mean_headway_micro - cdf_std_headway_micro, facecolor='red', alpha=0.3)
    ax.legend()
    ax.set_xlabel('Headway (m)')
    ax.set_ylabel('CDF of headway')
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 1)
    if SAVE:
        plt.savefig('headway.pdf')
        plt.close()
    else:
        plt.show()


if __name__ == "__main__":

    # Choose one:
    TOWN = True
    INGOLSTADT = False
    LUXEMBOURG = False
    TURIN = False

    SAVE = False

    if TOWN:
        cosim_0_path = 'examples/town/results/town_cosim_results_0'
        cosim_1_path = 'examples/town/results/town_cosim_results_1'
        cosim_2_path = 'examples/town/results/town_cosim_results_2'
        cosim_3_path = 'examples/town/results/town_cosim_results_3'
        cosim_4_path = 'examples/town/results/town_cosim_results_4'

        micro_0_path = 'examples/town/results/town_micro_results_0'
        micro_1_path = 'examples/town/results/town_micro_results_1'
        micro_2_path = 'examples/town/results/town_micro_results_4'
        micro_3_path = 'examples/town/results/town_micro_results_3'
        micro_4_path = 'examples/town/results/town_micro_results_4'

    if INGOLSTADT:
        cosim_0_path = 'examples/ingolstadt/results/ingolstadt_cosim_results_0'
        cosim_1_path = 'examples/ingolstadt/results/ingolstadt_cosim_results_1'
        cosim_2_path = 'examples/ingolstadt/results/ingolstadt_cosim_results_2'
        cosim_3_path = 'examples/ingolstadt/results/ingolstadt_cosim_results_3'
        cosim_4_path = 'examples/ingolstadt/results/ingolstadt_cosim_results_4'

        micro_0_path = 'examples/ingolstadt/results/ingolstadt_micro_results_0'
        micro_1_path = 'examples/ingolstadt/results/ingolstadt_micro_results_1'
        micro_2_path = 'examples/ingolstadt/results/ingolstadt_micro_results_2'
        micro_3_path = 'examples/ingolstadt/results/ingolstadt_micro_results_3'
        micro_4_path = 'examples/ingolstadt/results/ingolstadt_micro_results_4'

    if LUXEMBOURG:
        cosim_0_path = 'examples/luxembourg/results/luxembourg_cosim_results_0'
        cosim_1_path = 'examples/luxembourg/results/luxembourg_cosim_results_1'
        cosim_2_path = 'examples/luxembourg/results/luxembourg_cosim_results_2'
        cosim_3_path = 'examples/luxembourg/results/luxembourg_cosim_results_3'
        cosim_4_path = 'examples/luxembourg/results/luxembourg_cosim_results_4'

        micro_0_path = 'examples/luxembourg/results/luxembourg_micro_results_0'
        micro_1_path = 'examples/luxembourg/results/luxembourg_micro_results_1'
        micro_2_path = 'examples/luxembourg/results/luxembourg_micro_results_2'
        micro_3_path = 'examples/luxembourg/results/luxembourg_micro_results_3'
        micro_4_path = 'examples/luxembourg/results/luxembourg_micro_results_4'

    if TURIN:  # Note: cosim is run once only (too long)
        cosim_0_path = 'examples/turin/results/turin_cosim_results_0'
        cosim_1_path = 'examples/turin/results/turin_cosim_results_0'
        cosim_2_path = 'examples/turin/results/turin_cosim_results_0'
        cosim_3_path = 'examples/turin/results/turin_cosim_results_0'
        cosim_4_path = 'examples/turin/results/turin_cosim_results_0'

        micro_0_path = 'examples/turin/results/turin_meso_results_0'
        micro_1_path = 'examples/turin/results/turin_meso_results_0'
        micro_2_path = 'examples/turin/results/turin_meso_results_0'
        micro_3_path = 'examples/turin/results/turin_meso_results_0'
        micro_4_path = 'examples/turin/results/turin_meso_results_0'

    eval_all(cosim_0_path, cosim_1_path, cosim_2_path, cosim_3_path, cosim_4_path,
             micro_0_path, micro_1_path, micro_2_path, micro_3_path, micro_4_path,
             SAVE)
