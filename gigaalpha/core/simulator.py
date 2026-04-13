from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from gigaalpha.core.metrics import AlphaDomains

class Simulator:
    def __init__(self, data, bar_size, alpha_name, alpha_params, gen_name, gen_params, fee=0.175):
        self.data = data.copy()
        self.fee = fee
        self.bar_size = bar_size

        self.alpha_fn     = ALPHA_REGISTRY[alpha_name]['function']
        self.alpha_params = alpha_params
        self.gen_fn       = GEN_REGISTRY[gen_name]['function']
        self.gen_params   = gen_params

        strategy_id = [str(bar_size)] if bar_size else []
        for v in alpha_params.values():
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
        for v in gen_params.values():
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
            
        self.report = {
            'strategy':   "_".join(strategy_id),
            'bar_size':   bar_size,
            'fee':        fee,
            'alpha_name': alpha_name,
            'gen_name':   gen_name,
            **{f'alpha_{k}': v for k, v in alpha_params.items()},
            **{f'gen_{k}':   v for k, v in gen_params.items()},
        }

    def compute_signal(self):
        self.data['signal'] = self.alpha_fn(self.data, **self.alpha_params)

    def compute_position(self):
        self.data['position'] = self.gen_fn(self.data['signal'], **self.gen_params)
        self.data['position'] = AlphaDomains.adjust_positions(self.data)

    def compute_tvr_and_fee(self):
        AlphaDomains.compute_action_tvr_and_fee(self.data, self.fee)

    def compute_profits(self):
        AlphaDomains.compute_profits(self.data)

    def compute_performance(self, start, end):
        perf = AlphaDomains.compute_performance(self.data, start=start, end=end)
        return {**self.report, **perf}

    def execute_pipeline(self, segments):
        self.compute_signal()
        self.compute_position()
        self.compute_tvr_and_fee()
        self.compute_profits()

        reports = []
        for segment in segments:
            start, end = segment[0], segment[1]
            report = self.compute_performance(start, end)
            report['segment'] = f'{start}_{end}'
            reports.append(report)
        return reports
