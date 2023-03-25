from prometheus_client import Counter

TASKS_SENT_TOTAL = Counter(
    "tasks_sent_total",
    "Total number of tasks produced by the source code",
    ["task_name"],
)

TASKS_ENQUEUE_TOTAL = Counter(
    "tasks_enqueue_total",
    "Total number of taskes enqueued in in-memory queue",
    ["task_name"],
)

TASKS_ENQUEUE_FAILED_TOTAL = Counter(
    "tasks_enqueue_failed_total",
    "Total number of tasks failed to be enqueued in in-memory queue",
    ["task_name"],
)

TASKS_PROCESS_SUCCESS = Counter(
    "tasks_processed_success",
    "Total number of tasks sent from the in-memory queue to broker",
    ["task_name"],
)

TASKS_PROCESS_FAILED = Counter(
    "tasks_processed_failed",
    "Total number of tasks failed to go from the in-memory queue to broker",
    ["task_name"],
)