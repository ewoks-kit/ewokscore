from ewokscore import task_discovery


def test_task_class_discovery():
    expected = [
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover_module.MyTask1",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["result"],
            "category": "ewokscore",
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover_module.MyTask2",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["result"],
            "category": "ewokscore",
        },
    ]

    tasks = list(task_discovery.discover_tasks_from_modules())
    for task in expected:
        assert task not in tasks

    tasks = list(
        task_discovery.discover_tasks_from_modules("ewokscore.tests.discover_module")
    )
    for task in expected:
        assert task in tasks
    assert len(tasks) == len(expected)

    tasks = list(task_discovery.discover_tasks_from_modules())
    for task in expected:
        assert task in tasks


def test_task_method_discovery():
    expected = [
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover_module.run",
            "category": "ewokscore",
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover_module.myfunc",
            "category": "ewokscore",
        },
    ]
    tasks = list(
        task_discovery.discover_tasks_from_modules(
            "ewokscore.tests.discover_module", task_type="method"
        )
    )
    for task in expected:
        assert task in tasks
    assert len(tasks) == len(expected)


def test_task_ppfmethod_discovery():
    expected = [
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover_module.run",
            "category": "ewokscore",
        }
    ]
    tasks = list(
        task_discovery.discover_tasks_from_modules(
            "ewokscore.tests.discover_module", task_type="ppfmethod"
        )
    )
    for task in expected:
        assert task in tasks
    assert len(tasks) == len(expected)
