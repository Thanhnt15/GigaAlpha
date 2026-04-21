import pandas as pd
from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from gigaalpha.core.simulator import Simulator
from gigaalpha.core.metrics import AlphaDomains
import gigaalpha.strategies


class MegaSimulator:
    def __init__(self, data, alpha_name, gen_name, strategy_ids, fee=0.175):
        self.data = data.copy(deep=False)
        self.fee = fee

        self.alpha_name = alpha_name
        self.gen_name = gen_name
        self.strategy_ids = strategy_ids if isinstance(strategy_ids, list) else [strategy_ids]

        self.all_positions = []
        self.mega_position = None

        self.report = {
            'alpha_name': alpha_name,
            'gen_name':   gen_name,
        }

    @staticmethod
    def _parse_id(strategy_id, alpha_name, gen_name):
        parts = strategy_id.split("_")
        frequency = int(parts[0])

        alpha_keys = sorted(ALPHA_REGISTRY[alpha_name]['param_range'].keys())
        gen_keys = sorted(GEN_REGISTRY[gen_name]['param_range'].keys())

        params = {}
        idx = 1
        for keys in [alpha_keys, gen_keys]:
            for key in keys:
                val = parts[idx]
                if '(' in val and ')' in val:
                    val = tuple(float(x) for x in val.replace('(', '').replace(')', '').split(','))
                else:
                    val = float(val) if '.' in val else int(val)
                params[key] = val
                idx += 1
        return frequency, {k: params[k] for k in alpha_keys}, {k: params[k] for k in gen_keys}

    def compute_component_position(self):
        self.all_positions = []
        for sid in self.strategy_ids:
            freq, a_p, g_p = MegaSimulator._parse_id(sid, self.alpha_name, self.gen_name)
            sim = Simulator(self.data.copy(), freq, self.alpha_name, a_p, self.gen_name, g_p, self.fee)
            sim.compute_signal()
            sim.compute_position()
            self.all_positions.append(sim.data['position'].copy())
        return self.all_positions

    def compute_mega_position(self, positions_list=None):
        target = positions_list if positions_list is not None else self.all_positions
        if target:
            self.mega_position = pd.concat(target, axis=1).sum(axis=1)
            self.data['position'] = self.mega_position
            self.data['position'] = AlphaDomains.adjust_positions(self.data)
        return self.data['position']

    def compute_tvr_and_fee(self):
        AlphaDomains.compute_action_tvr_and_fee(self.data, self.fee)

    def compute_profits(self):
        AlphaDomains.compute_profits(self.data)

    def compute_performance(self, df_1d, start, end):
        perf = AlphaDomains.compute_performance(df_1d, start=start, end=end)
        return {**self.report, **perf}