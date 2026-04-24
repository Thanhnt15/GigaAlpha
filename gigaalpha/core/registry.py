import logging

logger = logging.getLogger(__name__)

ALPHA_REGISTRY = {}
GEN_REGISTRY   = {}

def register_alpha(param_range):
    """
    Decorator to register an alpha function into the registry.
    """
    def decorator(func):
        # Get short name: "alpha_001" -> "001"
        name = func.__name__.replace("alpha_", "")

        if name in ALPHA_REGISTRY:
            existing_func = ALPHA_REGISTRY[name]["function"]
            logger.warning(
                f"[DUPLICATE ALPHA] Name '{name}' is already registered!\n"
                f"Existing: {existing_func.__name__} (from {existing_func.__module__})\n"
                f"New:      {func.__name__} (from {func.__module__})\n"
                f"The new function will OVERWRITE the old one."
            )

        ALPHA_REGISTRY[name] = {
            "function":     func,
            "param_range": param_range,
        }
        return func

    return decorator


def register_gen(param_range):
    """
    Decorator to register a gen function into the registry.
    """
    def decorator(func):
        # Get short name: "gen_1_1" -> "1_1"
        name = func.__name__.replace("gen_", "")

        if name in GEN_REGISTRY:
            existing_func = GEN_REGISTRY[name]["function"]
            logger.warning(
                f"[DUPLICATE GEN] Name '{name}' is already registered!\n"
                f"Existing: {existing_func.__name__} (from {existing_func.__module__})\n"
                f"New:      {func.__name__} (from {func.__module__})\n"
                f"The new function will OVERWRITE the old one."
            )

        GEN_REGISTRY[name] = {
            "function":     func,
            "param_range": param_range,
        }
        return func

    return decorator
