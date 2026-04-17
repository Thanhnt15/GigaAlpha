import itertools
from gigaalpha.core.registry import ALPHA_REGISTRY, GEN_REGISTRY
from typing import List, Dict, Any

class ScanParams:
    @staticmethod
    def gen_all_params(alpha_name, gen_name, lst_frequency, lst_fee) -> List[Dict[str, Any]]:
        alpha_params = ALPHA_REGISTRY[alpha_name]['param_range'] 
        gen_params   = GEN_REGISTRY[gen_name]['param_range']     

        all_params = {
            'alpha_name': [alpha_name],   
            'gen_name':   [gen_name],
            'frequency':  lst_frequency,
            'fee':        lst_fee,
            **alpha_params,               
            **gen_params,                 
        }

        return [dict(zip(all_params, combo)) for combo in itertools.product(*all_params.values())]