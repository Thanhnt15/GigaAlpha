import pandas as pd
from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from gigaalpha.core.simulator import Simulator
from gigaalpha.core.metrics import AlphaDomains
import gigaalpha.strategies


class MegaSimulator:
    def __init__(self, dic_data, alpha_name, gen_name, strategy_ids, fee=0.175):
        self.dic_data = dic_data
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
        frequency = float(parts[0]) if "." in parts[0] else int(parts[0])

        gen_keys = sorted(GEN_REGISTRY[gen_name]['param_range'].keys())
        alpha_keys = sorted(ALPHA_REGISTRY[alpha_name]['param_range'].keys())

        params = {}
        idx = 1
        for keys in [gen_keys, alpha_keys]:
            for key in keys:
                val = parts[idx]
                if '(' in val and ')' in val:
                    val = tuple(float(x) for x in val.replace('(', '').replace(')', '').split(','))
                else:
                    val = float(val) if '.' in val else int(val)
                params[key] = val
                idx += 1
        
        g_p = {k: params[k] for k in gen_keys}
        a_p = {k: params[k] for k in alpha_keys}
        return frequency, g_p, a_p

    def compute_component_position(self):
        self.all_positions = []
        ref_idx = self.dic_data[1].index
        
        for sid in self.strategy_ids:
            freq, g_p, a_p = MegaSimulator._parse_id(sid, self.alpha_name, self.gen_name)
            sim = Simulator(self.dic_data[freq], freq, self.alpha_name, a_p, self.gen_name, g_p, self.fee)
            sim.compute_signal()
            sim.compute_position()
            pos = sim.data['position'].reindex(ref_idx).ffill().fillna(0)
            self.all_positions.append(pos)
        return self.all_positions

    def compute_mega_position(self, lst_positions=None):
        lst_positions = lst_positions if lst_positions is not None else self.all_positions
        if lst_positions:
            pos_sum = pd.concat(lst_positions, axis=1).sum(axis=1)
            self.mega_position = (pos_sum / len(lst_positions)).round(6).astype(int)
            self.dic_data[1]['position'] = self.mega_position
            self.dic_data[1]['position'] = AlphaDomains.adjust_positions(self.dic_data[1])
        return self.dic_data[1]

    def compute_tvr_and_fee(self):
        AlphaDomains.compute_action_tvr_and_fee(self.dic_data[1], self.fee)

    def compute_profits(self):
        AlphaDomains.compute_profits(self.dic_data[1])

    def compute_performance(self,df_1d, start, end):
        perf = AlphaDomains.compute_performance(df_1d, start=start, end=end)
        return {**self.report, **perf}

if __name__ == "__main__":
    dic_data = pd.read_pickle('/home/ubuntu/GigaAlpha/data/dic_freqs.pickle')
    segments = [["2018_01_01", "2020_01_01"]]
    LST_STRATEGY = [
        '10_0.0_0.1_5'
    ]
    mega = MegaSimulator(dic_data, '064', '1_1', LST_STRATEGY)
    mega.compute_component_position()
    mega.compute_mega_position()
    mega.compute_tvr_and_fee()
    mega.compute_profits()
    df_1d = AlphaDomains.aggregate_to_1d(mega.dic_data[1])
    
    for segment in segments:
        start, end = segment[0], segment[1]
        report = mega.compute_performance(df_1d, start=start, end=end)
        print(report)
    
    