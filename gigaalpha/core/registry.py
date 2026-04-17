ALPHA_REGISTRY = {}
GEN_REGISTRY   = {}

def register_alpha(param_range):
    """
    Gắn lên trên hàm alpha để đăng ký vào sổ cái.
    """
    def decorator(func):
        # Lấy tên ngắn: "alpha_001" -> "001"
        name = func.__name__.replace("alpha_", "")

        ALPHA_REGISTRY[name] = {
            "function":     func,
            "param_range": param_range,
        }
        return func

    return decorator


def register_gen(param_range):
    """
    Gắn lên trên hàm gen để đăng ký vào sổ cái.
    """
    def decorator(func):
        # Lấy tên ngắn: "gen_1_1" -> "1_1"
        name = func.__name__.replace("gen_", "")

        GEN_REGISTRY[name] = {
            "function":     func,
            "param_range": param_range,
        }
        return func

    return decorator
