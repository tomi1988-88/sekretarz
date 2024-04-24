
def log_it(func):
    def wrapper(*args, **kwargs):
        if TheBrain.LOG_IT:
            try:
                log_path = TheBrain.PROJECT_PATH.joinpath("log.log")
                with open(log_path, "a") as log_file:
                    line_to_save = f"{dt.datetime.now(): }, {func.__name__}, {args}, {kwargs}\n"
                    log_file.write(line_to_save)
            except AttributeError as e:
                print(e)

        return func(*args, **kwargs)
    return wrapper


# def _log_it(project_path):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             try:
#                 log_path = TheBrain.PROJECT_PATH.joinpath("log.log")
#                 with open(log_path, "a") as log_file:
#                     line_to_save = f"{func.__name__}, {args}, {kwargs}\n"
#                     log_file.write(line_to_save)
#             except AttributeError as e:
#                 print(e)
#
#             return func(*args, **kwargs)
#         return wrapper
#     return decorator