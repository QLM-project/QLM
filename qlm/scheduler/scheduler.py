from qlm.queue.group import Group
from qlm.queue.virtual_queue import VirtualQueue
from qlm.config import Config
from qlm.scheduler.rwt_estimator import RWTEstimator
import gurobipy as gp
from gurobipy import GRB
from gurobipy import quicksum
from gurobipy import LinExpr
from bidict import bidict
import time
from collections import deque


class Scheduler:
    """
    Scheduler class is responsible for managing the scheduling of the queue.
    It is responsible for checking for SLO violations and reordering the queue based on the scheduling policy.
    """

    def __init__(self, policy="edf"):
        """
        Initializes the scheduler with a scheduling policy and a RWTEstimator object.
        :param policy: The scheduling policy for the scheduler.
        """
        self.policy = policy
        self.rwt_estimator = RWTEstimator()
        self.config = Config()

    def _update_all_slos(self, vqs):
        """
        Updates the SLOs for all requests in the virtual queues based on current time.
        :param vqs: The list of virtual queues.
        """
        for vq in vqs:
            for group in vq.groups:
                for request in group.requests:
                    curr_time = time.time()
                    request.slo -= curr_time - request.insertion_time
                    request.slo = (
                        request.slo
                        // self.config.slo_granularity
                        * self.config.slo_granularity
                    )
                    request.insertion_time = curr_time

    def check_violation(self, vqs):
        """
        Checks for SLO violations in the virtual queues.
        :param vqs: The list of virtual queues.
        :return: True if there is a violation, False otherwise.
        """
        self._update_all_slos(vqs)

        for vq in vqs:
            est_time = 0
            curr_model = None

            for group in vq.groups:
                prev_model = curr_model
                curr_model = group.model

                if prev_model != None and prev_model != curr_model:
                    est_time += config.swap_time

                waiting_time = self.rwt_estimator.get_waiting_time(group)

                est_time += waiting_time

                if est_time > group.slo:
                    return True

        return False

    def reorder(self, vqs):
        """
        Reorders the virtual queues based on the scheduling policy.
        :param vqs: The list of virtual queues.
        :return: The reordered list of virtual queues.
        """
        if self.policy == "edf":
            return self._reorder_edf(vqs)
        elif self.policy == "lp":
            return self._reorder_lp_solver(vqs)

    def _reorder_edf(self, vqs):
        """
        Reorders the virtual queues based on the Earliest Deadline First (EDF) policy.
        :param vqs: The list of virtual queues.
        :return: The reordered list of virtual queues.
        """
        for vq in vqs:
            groups = list(vq.groups)
            groups.sort(key=lambda x: x.slo)
            vq.groups = deque(groups)

        return vqs

    def _reorder_lp_solver(self, vqs):
        """
        Reorders the virtual queues based on the Linear Programming (LP) solver.
        :param vqs: The list of virtual queues.
        :return: The reordered list of virtual queues.
        """

        options = {
            "WLSACCESSID": self.config.gurobi["access_id"],
            "WLSSECRET": self.config.gurobi["secret_key"],
            "LICENSEID": self.config.gurobi["license"],
        }

        groups = []
        slos = []
        models = []

        model_idx_bimap = bidict({})
        group_idx_bimap = bidict({})
        last_model_idx = 0
        last_group_idx = 0

        vqs_fail_case = vq.copy()

        for vq in vqs:
            while len(vq.groups) > 0:
                group = vq.groups.popleft()
                groups.append(self.rwt_estimator.get_waiting_time(group))
                group_idx_bidict[group] = last_group_idx
                last_group_idx += 1
                slos.append(group.slo)
                if group.model in model_idx_bidict:
                    models.append(model_idx_bidict[group.model])
                else:
                    model_idx_bimap[group.model] = last_model_idx
                    models.append(last_model_idx)
                    last_model_idx += 1

        N = len(groups)  # nunber of request groups
        WORKERs = len(vqs)  # number of GPUs
        SLOTs = len(groups)  # number of slots per GPU
        MODELs = len(
            models
        )  # number of models being served (assume serially labeled from 0 to MODELs-1)
        MODEL_SWAP_TIME = (
            self.config.model_swap_time
        )  # Time required to swap two models

        with gp.Env(params=options) as env, gp.Model(env=env) as model:

            # Model initialization
            x = model.addVars(WORKERs, N, N, vtype=GRB.BINARY, name="x")
            completion_slot = model.addVars(WORKERs, N, vtype=GRB.INTEGER, name="ct")
            model_slot = model.addVars(WORKERs, N, vtype=GRB.INTEGER, name="model")
            transition_slot = model.addVars(WORKERs, N, vtype=GRB.INTEGER, name="trans")
            slo_slot = model.addVars(WORKERs, N, vtype=GRB.INTEGER, name="slo")
            penalty_slot = model.addVars(
                WORKERs, N, vtype=GRB.INTEGER, name="penalty", lb=-100000
            )

            # Group assignment to GPU slot
            for i in range(N):
                model.addConstr(
                    quicksum(
                        x[g, i, slot] for g in range(WORKERs) for slot in range(SLOTs)
                    )
                    == 1
                )

            # GPU slot assignment to group
            for g in range(WORKERs):
                for slot in range(SLOTs):
                    model.addConstr(quicksum(x[g, i, slot] for i in range(N)) == 1)

            # Calculating model type and SLO for all GPU slots
            for g in range(WORKERs):
                for slot in range(SLOTs):
                    model.addConstr(
                        model_slot[g, slot]
                        == quicksum(models[i] * x[g, i, slot] for i in range(N))
                    )
                    model.addConstr(
                        slo_slot[g, slot]
                        == quicksum(slos[i] * x[g, i, slot] for i in range(N))
                    )

            # Initializing model swap time for first GPU slot to 0
            for g in range(WORKERs):
                model.addConstr(transition_slot[g, 0] == 0)

            # Calculating model swap times based on adjacent GPU slots
            for g in range(WORKERs):
                for slot in range(1, SLOTs):
                    model.addConstr(
                        model_slot[g, slot] - model_slot[g, slot - 1]
                        <= 1 + MODELs - MODELs * transition_slot[g, slot]
                    )
                    model.addConstr(
                        model_slot[g, slot] - model_slot[g, slot - 1]
                        >= MODELs * transition_slot[g, slot] - MODELs - 1
                    )
                    model.addConstr(
                        model_slot[g, slot] - model_slot[g, slot - 1]
                        <= MODELs * transition_slot[g, slot] - 1
                    )
                    model.addConstr(
                        model_slot[g, slot] - model_slot[g, slot - 1]
                        >= 1 - MODELs * transition_slot[g, slot]
                    )

            # Estimating cumulative completion time per GPU slot
            for g in range(WORKERs):
                for slot in range(SLOTs):
                    model.addConstr(
                        completion_slot[g, slot]
                        == quicksum(
                            groups[i] * x[g, i, j]
                            for i in range(N)
                            for j in range(slot + 1)
                        )
                    )

            # Estimating penalty for violating SLOs
            for g in range(WORKERs):
                for slot in range(SLOTs):
                    model.addConstr(
                        penalty_slot[g, slot]
                        == completion_slot[g, slot]
                        + MODEL_SWAP_TIME * transition_slot[g, slot]
                        - slo_slot[g, slot]
                    )

            # Constraining no SLO violation
            for g in range(WORKERs):
                for slot in range(SLOTs):
                    model.addConstr(penalty_slot[g, slot] <= 0)

            # Minimize total penalty
            model.setObjective(
                quicksum(
                    penalty_slot[g, slot]
                    for g in range(WORKERs)
                    for slot in range(SLOTs)
                ),
                GRB.MINIMIZE,
            )

            model.optimize()

            if model.Status == GRB.OPTIMAL:
                print("Optimal solution found for LP!")
                for g in range(WORKERs):
                    for i in range(N):
                        for slot in range(SLOTs):
                            var_name = f"x[{g},{i},{slot}]"
                            var = model.getVarByName(var_name)
                            if var and abs(var.X) > 0:  # Only display non-zero values
                                vqs[g].groups.append(group_idx_bimap.inv[i])
                return vqs
            else:
                print("No optimal solution found for LP, reverting to EDF")
                vqs = vqs_fail_case
                self._reorder_edf(vqs)
