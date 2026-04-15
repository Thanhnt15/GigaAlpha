from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from gigaalpha.core.metrics import AlphaDomains

class Simulator:
    def __init__(self, data, frequency, alpha_name, alpha_params, gen_name, gen_params, fee=0.175):
        self.data = data.copy()
        self.fee = fee
        self.frequency = frequency

        self.alpha_fn     = ALPHA_REGISTRY[alpha_name]['function']
        self.alpha_params = alpha_params
        self.gen_fn       = GEN_REGISTRY[gen_name]['function']
        self.gen_params   = gen_params

        strategy_id = [str(frequency)] if frequency else []
        for v in alpha_params.values():
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
        for v in gen_params.values():
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
            
        self.report = {
            'alpha_name': alpha_name,
            'gen_name':   gen_name,
            'fee':        fee,
            'frequency':  frequency,
            'strategy':   "_".join(strategy_id),
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
        try:
            self.compute_signal()
        except Exception as e:
            raise RuntimeError(f"Failed at compute_signal for strategy dict {self.report['strategy']}: {e}") from e

        try:
            self.compute_position()
        except Exception as e:
            raise RuntimeError(f"Failed at compute_position for strategy {self.report['strategy']}: {e}") from e

        try:
            self.compute_tvr_and_fee()
        except Exception as e:
            raise RuntimeError(f"Failed at compute_tvr_and_fee for strategy {self.report['strategy']}: {e}") from e

        try:
            self.compute_profits()
        except Exception as e:
            raise RuntimeError(f"Failed at compute_profits for strategy {self.report['strategy']}: {e}") from e

        reports = []
        for segment in segments:
            start, end = segment[0], segment[1]
            try:
                report = self.compute_performance(start, end)
                report['segment'] = f'{start}_{end}'
                reports.append(report)
            except Exception as e:
                raise RuntimeError(f"Failed at compute_performance for segment {start}_{end} (strategy {self.report['strategy']}): {e}") from e
        return reports
