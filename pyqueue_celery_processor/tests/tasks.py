from celery import Celery

app = Celery('tests')


@app.task(name="sample tests task")
def sample_test_task(*args, **kwargs):
    return {"args": args, "kwargs": kwargs}
