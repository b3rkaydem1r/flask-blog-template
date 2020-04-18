from datetime import datetime


def time(post_time):
    time = datetime.strptime(str(post_time), "%Y-%m-%d %H:%M:%S")
    return time.strftime("%d %B %Y")