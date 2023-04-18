import random
import sys
import os
from copy import deepcopy
import math
import multiprocessing as mp
import libsumo
from sumolib.net import readNet


class LibsumoParallelConnection:
    """
        An object to that handles a microscopic and a mesoscopic SUMO connection simultaneously.

        Args:
            callback_micro (function): function that is executed periodically during the simulation accessing the
                                       states of the microsimulation.
            callback_meso (function): function that is executed periodically during the simulation accessing the states
                                      of the meso simulation.
    """

    def __init__(self, callback_micro, callback_meso):

        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("Please declare environment variable 'SUMO_HOME'")

        self.multi_ego = False

        self._events = dict()
        self._events['start_micro'] = mp.Event()
        self._events['start_micro_DONE'] = mp.Event()
        self._events['step_micro'] = mp.Event()
        self._events['step_micro_DONE'] = mp.Event()
        self._events['set_callback_micro_args'] = mp.Event()
        self._events['set_callback_micro_args_DONE'] = mp.Event()
        self._events['get_callback_micro_resturn'] = mp.Event()
        self._events['get_callback_micro_resturn_DONE'] = mp.Event()

        self._events['start_meso'] = mp.Event()
        self._events['start_meso_DONE'] = mp.Event()
        self._events['step_meso'] = mp.Event()
        self._events['step_meso_DONE'] = mp.Event()
        self._events['set_callback_meso_args'] = mp.Event()
        self._events['set_callback_meso_args_DONE'] = mp.Event()
        self._events['get_callback_meso_resturn'] = mp.Event()
        self._events['get_callback_meso_resturn_DONE'] = mp.Event()
        self._events['step_meso_first_part_DONE'] = mp.Event()

        self._events['stop'] = mp.Event()

        manager = mp.Manager()
        self._set_values = manager.dict()
        self._set_values['start_micro_cmd'] = manager.list()
        self._set_values['start_meso_cmd'] = manager.list()
        self._set_values['callback_micro_arguments'] = ()
        self._set_values['callback_meso_arguments'] = ()

        self._set_values['ego_id'] = ''
        self._set_values['ego_pos'] = (0.0, 0.0)
        self._set_values['multi_ego_id'] = ()
        self._set_values['multi_ego_pos'] = ()
        self._set_values['distance'] = 0.0
        self._set_values['subgraph'] = ()
        self._set_values['inflow'] = ()
        self._set_values['new_links'] = ()
        self._set_values['prev_subgraph'] = ()
        self._set_values['prev_inflow_ids'] = ()

        self._set_values['meso_routes'] = ()
        self._set_values['meso_vehs'] = ()

        self._set_values['callback_micro_return'] = ()
        self._set_values['callback_meso_return'] = ()

        self._sumo_micro = mp.Process(target=self._control_sumo_micro_instance, args=(callback_micro,))
        self._sumo_meso = mp.Process(target=self._control_sumo_meso_instance, args=(callback_meso,))

    def set_callback_arguments(self, arguments, micro):
        """
            Passes the arguments of the optianal callback function as a tuple. It writes the data to a shared memory
            where the other process can access it.

            Args:
                micro (bool): if set, the arguments in the microsimulator's process is set. If false, the mesoscopic
                              simulator's callback arguments are set.
                arguments (tuple): arguments of the callback function
        """
        if micro:
            self._set_values['callback_micro_arguments'] = arguments
        else:
            self._set_values['callback_meso_arguments'] = arguments

    def get_callback_returns(self, micro):
        """
            Gets the return values of the callback function as a tuple. It reads the shared memory.

            Args:
                micro (bool): if set, the return values in the microsimulator's process returned. If false, the
                              mesoscopic simulator's callback return values are returned.
            Returns:
                values (tuple): return value of the callback function
        """
        if micro:
            return self._set_values['callback_micro_return']
        else:
            return self._set_values['callback_meso_return']

    def start(self, cmd_micro, cmd_meso, ego_id, distance):
        """
            Starts both processes and the SUMO instances as well.

            Args:
                cmd_micro (list): SUMO command to start the microscopic simulation
                cmd_meso (list): SUMO command to start the mesoscopic simulation
                ego_id (string or list): name(s) of the ego vehicle(s)
                distance (float): road distance in which microsimulation is used wrt the EGO coordinates. Only edges
                                  within the range is simulated with car following dynamics
        """

        if type(ego_id) is str:
            self.multi_ego = False
            self._set_values['ego_id'] = ego_id
        elif type(ego_id) is list:
            self.multi_ego = True
            self._set_values['multi_ego_id'] = tuple(ego_id)
        else:
            raise TypeError("ego_id must be a string or a list of strings")
        self._set_values['distance'] = distance

        self._sumo_meso.start()
        self._set_values['start_meso_cmd'][:] = cmd_meso
        self._events['start_meso'].set()
        self._events['start_meso_DONE'].wait()
        self._events['start_meso_DONE'].clear()

        self._sumo_meso = None  # remove from pickle

        self._sumo_micro.start()
        self._set_values['start_micro_cmd'][:] = cmd_micro
        self._events['start_micro'].set()
        self._events['start_micro_DONE'].wait()
        self._events['start_micro_DONE'].clear()

        self._sumo_micro = None  # remove from pickle

    def close(self):
        """
            Stops sumo and kills the process
        """
        self._events['stop'].set()
        try:
            self._sumo_micro.join()
        except AttributeError:
            pass
        try:
            self._sumo_meso.join()
        except AttributeError:
            pass

    def simulation_step(self, network):
        """
            Steps the SUMO instance within the process.
            
            Args:
                network (object): network object
        """
        self._get_microsimulation_subgraph_simplified(network)
        self._events['step_meso'].set()
        self._events['step_micro'].set()
        self._events['step_meso_DONE'].wait()
        self._events['step_meso_DONE'].clear()
        self._events['step_micro_DONE'].wait()
        self._events['step_micro_DONE'].clear()

    def create_meso(self, sumocmd, meso_gui=False, meso_limited_jc=True, meso_overtaking=True):
        """
            Takes the SUMO simulation configuration command and clones the SUMO config files (.sumocfg) with the mesosim
            flag enabled (<simulation>_meso.sumocfg) and with the routes removed (<simulation>_noRoutes.sumocfg).
            Returns  SUMO start commands for the two simulations.

            Args:
                sumocmd (list: string): Sumo start configuration, e.g., ["sumo-gui", "-c", "test.sumocfg", "--start"]
                meso_gui (bool): Start the meso simulation with a GUI. Optional. Default: False.
                meso_limited_jc (bool): Limited junction control. See SUMO documentation for further description.
                                        Optional. Default: True.
                meso_overtaking (bool): Mesoscopic overtaking. See SUMO documentation for further description. Optional.
                                        Default: True.
            Returns:
                micro_cmd (list: string): Sumo command to start the microscopic simulation
                meso_cmd (list: string): Sumo command to start the mesoscopic simulation
        """
        config_name = ''
        index = 0
        for i, arg in enumerate(sumocmd):
            if '.sumocfg' in arg:
                config_name = arg
                index = i
        if not config_name:
            sys.exit("Please provide a .sumocfg file in the arguments")

        meso_config_name = self._create_meso_net(config_name, dump_enabled=False, meso_limited_jc=meso_limited_jc,
                                                 meso_overtaking=meso_overtaking)
        micro_config_name = self._create_noflow_net(config_name)

        meso_cmd = deepcopy(sumocmd)
        if meso_gui is False:
            meso_cmd[0] = "sumo"
        else:
            meso_cmd[0] = "sumo-gui"
        meso_cmd[index] = meso_config_name

        micro_cmd = deepcopy(sumocmd)
        micro_cmd[index] = micro_config_name

        return micro_cmd, meso_cmd

    @staticmethod
    def _create_meso_net(config_name, dump_enabled=False, meso_limited_jc=True, meso_overtaking=True):
        """
            Creates a mesoscopic simulation from the given sumo file.

            Args:
                config_name (string): Sumo confilg file
                meso_limited_jc (bool): Limited junction control. See SUMO documentation for further description.
                                        Optional. Default: True.
                meso_overtaking (bool): Mesoscopic overtaking. See SUMO documentation for further description.
                                        Optional. Default: True.
            Returns:
                meso_config_name (string): Name of the sumocfg file with meso simulation.
        """
        with open(config_name, 'r') as f:
            contents = f.read()
        contents_lines = contents.splitlines()
        for line in contents_lines:
            line = line.replace(" ", "")
            if "mesosimvalue=\"true\"" in line:
                sys.exit("Mesoscopic simulation already enabled")

        meso_config_name = "{}{}{}".format(config_name[:-8], "_meso", config_name[-8:])
        st_outputs = False
        with open(meso_config_name, 'w') as f:
            for line in contents_lines:
                if "</input>" in line:
                    f.write("\n\t<mesoscopic>\n")
                    f.write("\t\t<mesosim value = \"true\"/>\n")
                    if meso_limited_jc:
                        f.write("\t\t<meso-junction-control.limited value = \"true\"/>\n")
                    else:
                        f.write("\t\t<meso-junction-control.limited value = \"false\"/>\n")
                    if meso_overtaking:
                        f.write("\t\t<meso-overtaking value = \"true\"/>\n")
                    else:
                        f.write("\t\t<meso-overtaking value = \"false\"/>\n")
                    f.write("\t</mesoscopic>\n\n")
                if dump_enabled:
                    if "</output>" in line:
                        f.write("\t\t<netstate-dump value = \"meso_vehicle_dump.xml\"/>\n")
                        st_outputs = True

                    if "</configuration>" in line and st_outputs is False:
                        f.write("\t<output>\n")
                        f.write("\t\t<netstate-dump value = \"meso_vehicle_dump.xml\"/>\n")
                        f.write("\t</output>\n")
                f.write(line + "\n")

        return meso_config_name

    @staticmethod
    def _create_noflow_net(config_name):
        """
            Creates a microscpoic simulation without route files

            Args:
                config_name (string): Sumo confilg file
            Returns:
                micro_config_name (string): Name of the sumocfg file with meso simulation.
        """
        with open(config_name, 'r') as f:
            contents = f.read()
        contents_lines = contents.splitlines()

        micro_config_name = "{}{}{}".format(config_name[:-8], "_noRoutes", config_name[-8:])
        with open(micro_config_name, 'w') as f:
            for line in contents_lines:
                if "route-files" in line:
                    continue
                f.write(line + "\n")

        return micro_config_name

    @staticmethod
    def parse_network(network_file):
        """
            Parses the .net file to get a list of edge start/end locations in the scenario.

            Args:
                network_file (string): the network file
            Returns:
                network (object): network object
        """
        return readNet(network_file)

    def _get_microsimulation_subgraph_simplified(self, network):
        """
            Gets subgraph where microsimulation takes place - uses a circle of given radius instead of graph search.

            Args:
                network (object): network object
            Returns:
                subgraph (list: string): List of microsimulaed edges
        """

        # Init
        distance = self._set_values['distance']
        subgraph = []

        if self.multi_ego:
            for pos in self._set_values['multi_ego_pos']:
                x, y = pos
                edges = network.getNeighboringEdges(x, y, distance, includeJunctions=True)
                for edge in edges:
                    subgraph.append(edge[0].getID())
            subgraph = list(set(subgraph))
        else:
            x, y = self._set_values['ego_pos']
            edges = network.getNeighboringEdges(x, y, distance, includeJunctions=True)
            for edge in edges:
                subgraph.append(edge[0].getID())

        self._set_values['subgraph_prev'] = self._set_values['subgraph']
        self._set_values['subgraph'] = subgraph
        self._set_values['inflow'] = self._get_inflow_edges(network)
        self._set_values['new_links'] = list(set(subgraph) - set(self._set_values['subgraph_prev']))

    def _get_inflow_edges(self, network):
        """
            Get inflow edges (which have no predecessor in the subgraph)
            
            Args:
                network (object): network object
            Returns:
                inflow_edges (list: string): List of inflow edges of the subgraph
        """
        subgraph = self._set_values['subgraph']
        inflow_edges = []
        for edge in subgraph:
            inflow = True
            edge_obj = network.getEdge(edge)
            from_node = edge_obj.getFromNode()
            to_node = edge_obj.getToNode()
            upstream_edges = from_node.getIncoming()
            for upstream_edge in upstream_edges:
                upstream_id = upstream_edge.getID()
                upstream_from_node = upstream_edge.getFromNode()
                if upstream_id in subgraph and upstream_from_node != to_node:
                    inflow = False
            if inflow:
                inflow_edges.append(edge)
        return inflow_edges

    def _control_sumo_meso_instance(self, callback):
        while True:
            # Interrupts
            if self._events['start_meso'].is_set():
                libsumo.start(self._set_values['start_meso_cmd'])
                self._events['start_meso'].clear()
                self._events['start_meso_DONE'].set()
            if self._events['stop'].is_set():
                libsumo.close()
                break
            
            if self._events['step_meso'].is_set():
                inflows = list(self._set_values['inflow'])
                renders = list(self._set_values['new_links'])
                micro_veh_ids = self._set_values['prev_inflow_ids']

                # To be rendered:
                route_to_add = []
                veh_to_add = []
                for edge in renders:
                    meso_vehicles = libsumo.edge.getLastStepVehicleIDs(edge)
                    if not meso_vehicles:
                        pass
                    else:
                        for meso_veh in meso_vehicles:
                            meso_route = libsumo.vehicle.getRouteID(meso_veh)

                            route_edges = libsumo.route.getEdges(meso_route)
                            try:
                                index = route_edges.index(edge)
                            except ValueError:
                                pass
                            else:
                                route_edges = route_edges[index:]
                            route_to_add.append((meso_veh, route_edges))
                            veh_to_add.append(meso_veh)
                # Inflows
                for edge in inflows:
                    meso_vehicles = libsumo.edge.getLastStepVehicleIDs(edge)
                    if not meso_vehicles:
                        pass
                    else:
                        try:
                            new_vehs = list(set(meso_vehicles) - set(micro_veh_ids[edge]))
                        except KeyError:
                            new_vehs = meso_vehicles
                        for meso_veh in new_vehs:
                            try:
                                meso_route = libsumo.vehicle.getRouteID(meso_veh)

                                route_edges = libsumo.route.getEdges(meso_route)
                            except libsumo.TraCIException:
                                continue
                            try:
                                index = route_edges.index(edge)
                            except ValueError:
                                pass
                            else:
                                route_edges = route_edges[index:]
                            route_to_add.append((meso_veh, route_edges))
                            veh_to_add.append(meso_veh)

                self._set_values['meso_routes'] = route_to_add
                self._set_values['meso_vehs'] = veh_to_add

                # Data is passed to the micro process here. Now the two run in parallel
                self._events['step_meso_first_part_DONE'].set()

                # Callback function
                if callback is not None:
                    callback_args = self._set_values['callback_meso_arguments'] = ()
                    callback_return = callback(*callback_args)
                    self._set_values['callback_meso_return'] = callback_return

                # Step the simulation
                libsumo.simulationStep()
                self._events['step_meso'].clear()
                self._events['step_meso_DONE'].set()

    def _control_sumo_micro_instance(self, callback):
        while True:
            # Interrupts
            if self._events['start_micro'].is_set():
                libsumo.start(self._set_values['start_micro_cmd'])
                self._events['start_micro'].clear()
                self._events['start_micro_DONE'].set()
            if self._events['stop'].is_set():
                libsumo.close()
                break
            if self._events['step_micro'].is_set():
                self._events['step_meso_first_part_DONE'].wait()
                self._events['step_meso_first_part_DONE'].clear()

                inflows = list(self._set_values['inflow'])
                subgraph = list(self._set_values['subgraph'])
                distance = self._set_values['distance']
                new_vehs = self._set_values['meso_vehs']
                new_routes = self._set_values['meso_routes']

                # Add vehicles
                for route, veh in zip(new_routes, new_vehs):
                    try:
                        if len(route[1]) < 2:
                            continue
                        libsumo.route.add(route[0], route[1])
                    except libsumo.TraCIException:
                        pass
                    try:
                        libsumo.vehicle.add(veh, veh, depart='now', departLane='best',
                                            departPos='free', departSpeed='max')
                    except libsumo.TraCIException:
                        r = random.randint(0, 1e7)
                        try:
                            libsumo.vehicle.add(veh + str(r), veh, depart='now', departLane='best',
                                                departPos='free', departSpeed='max')
                        except libsumo.TraCIException:
                            sys.stdout.write(f"Could not insert {veh}\n", )
                        # pass
                # Clear links
                micro_veh_ids = libsumo.vehicle.getIDList()
                if self.multi_ego:
                    ego_ids = self._set_values['multi_ego_id']
                    ego_pos_tuples = self._set_values['multi_ego_pos']
                else:
                    ego_id = self._set_values['ego_id']
                    x, y = self._set_values['ego_pos']

                for veh in micro_veh_ids:
                    if self.multi_ego:
                        if veh in ego_ids:
                            continue
                        else:
                            edge_id = libsumo.vehicle.getRoadID(veh)
                            if edge_id in subgraph:
                                continue
                            else:
                                try:
                                    x2, y2 = libsumo.vehicle.getPosition(veh)
                                    out_of_range = []
                                    for pos in ego_pos_tuples:
                                        x, y = pos
                                        if math.sqrt((x2 - x) ** 2 + (y2 - y) ** 2) > distance * 1.5:
                                            out_of_range.append(True)
                                        else:
                                            out_of_range.append(False)
                                    if all(out_of_range):
                                        libsumo.vehicle.remove(veh, reason=2)
                                except libsumo.TraCIException:
                                    pass  # vehicle was already removed from another link.
                    else:
                        if veh == ego_id:
                            continue
                        else:
                            edge_id = libsumo.vehicle.getRoadID(veh)
                            if edge_id in subgraph:
                                continue
                            else:
                                try:
                                    x2, y2 = libsumo.vehicle.getPosition(veh)
                                    if math.sqrt((x2 - x) ** 2 + (y2 - y) ** 2) > distance * 1.5:
                                        libsumo.vehicle.remove(veh, reason=2)
                                except libsumo.TraCIException:
                                    pass  # vehicle was already removed from another link.

                # Callback function
                if callback is not None:
                    callback_args = self._set_values['callback_micro_arguments']
                    callback_return = callback(*callback_args)
                    self._set_values['callback_micro_return'] = callback_return

                # Step the simulation
                libsumo.simulationStep()

                # Data from the microsimulator needed by the meso sim in the next step
                # (to avoid loss of synchronization)
                tmp_inflow_ids = dict()
                for edge in inflows:
                    tmp_inflow_ids[edge] = libsumo.edge.getLastStepVehicleIDs(edge)
                self._set_values['prev_inflow_ids'] = tmp_inflow_ids

                if self.multi_ego:
                    tmp_ego_pos_list = []
                    for ego_id in ego_ids:
                        try:
                            tmp_ego_pos_list.append(libsumo.vehicle.getPosition(ego_id))
                        except libsumo.TraCIException:
                            tmp_ego_pos_list.append((0, 0))
                            sys.stdout.write("EGO is not in the simulation\n")
                    self._set_values['multi_ego_pos'] = tmp_ego_pos_list
                else:
                    try:
                        self._set_values['ego_pos'] = libsumo.vehicle.getPosition(self._set_values['ego_id'])
                    except libsumo.TraCIException:
                        sys.stdout.write("EGO is not in the simulation\n")

                self._events['step_micro'].clear()
                self._events['step_micro_DONE'].set()