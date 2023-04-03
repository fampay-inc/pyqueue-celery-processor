from celery import Celery

app = Celery('test')

@app.task(name="sample test task")
def sample_test_task(*args, **kwargs):
    return {"args": args, "kwargs": kwargs}