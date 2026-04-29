from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from gigaalpha.core.metrics import AlphaDomains

class Simulator:
    def __init__(self, data, frequency, alpha_name, alpha_params, gen_name, gen_params, fee=0.175):
        self.data = data.copy(deep=False)
        self.fee = fee
        self.frequency = frequency

        self.alpha_fn     = ALPHA_REGISTRY[alpha_name]['function']
        self.alpha_params = alpha_params
        self.gen_fn       = GEN_REGISTRY[gen_name]['function']
        self.gen_params   = gen_params

        strategy_id = [str(frequency)]
        for k in sorted(gen_params.keys()):
            v = gen_params[k]
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
        for k in sorted(alpha_params.keys()):
            v = alpha_params[k]
            strategy_id.append(str(round(v, 4)) if isinstance(v, (float, int)) else str(v))
            
        self.report = {
            'alpha_name': alpha_name,
            'gen_name':   gen_name,
            'fee':        fee,
            'strategy':   "_".join(strategy_id),
            'frequency':  frequency,
            **{f'gen_{k}':   v for k, v in gen_params.items()},
            **{f'alpha_{k}': v for k, v in alpha_params.items()},
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

    def compute_performance(self, df_1d, start, end):
        perf = AlphaDomains.compute_performance(df_1d, start=start, end=end)
        return {**self.report, **perf}

    def execute_pipeline(self, segments):
        try:
            self.compute_signal()
            self.compute_position()
            self.compute_tvr_and_fee()
            self.compute_profits()
            df_1d_master = AlphaDomains.aggregate_to_1d(self.data)
            
            reports = []
            for segment in segments:
                start, end = segment[0], segment[1]
                report = self.compute_performance(df_1d_master, start, end)
                report['segment'] = f'{start}_{end}'
                reports.append(report)
            return reports
            
        except Exception as e:
            strategy_id = self.report.get('strategy', 'Unknown')
            raise RuntimeError(f"Pipeline failure for strategy {strategy_id}: {e}") from e
