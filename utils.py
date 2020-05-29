
def get_v(obj,k):
    try:
        return obj[k]
    except KeyError as e:
        return None
