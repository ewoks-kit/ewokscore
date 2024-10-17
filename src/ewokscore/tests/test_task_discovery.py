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
            "description": "Test 1",
        },
        {
            "task_type": "class",
            "task_identifier": "ewokscore.tests.discover_module.MyTask2",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["result"],
            "category": "ewokscore",
            "description": None,
        },
    ]

    tasks = task_discovery.discover_tasks_from_modules()
    for task in expected:
        assert task not in tasks

    tasks = task_discovery.discover_tasks_from_modules(
        "ewokscore.tests.discover_module"
    )
    assert_tasks(tasks, expected)
    assert len(tasks) == len(expected)

    tasks = task_discovery.discover_tasks_from_modules()
    assert_tasks(tasks, expected)


def test_task_method_discovery():
    expected = [
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover_module.run",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test 2",
        },
        {
            "task_type": "method",
            "task_identifier": "ewokscore.tests.discover_module.myfunc",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": None,
        },
    ]
    tasks = task_discovery.discover_tasks_from_modules(
        "ewokscore.tests.discover_module", task_type="method"
    )
    assert_tasks(tasks, expected)
    assert len(tasks) == len(expected)


def test_task_ppfmethod_discovery():
    expected = [
        {
            "task_type": "ppfmethod",
            "task_identifier": "ewokscore.tests.discover_module.run",
            "required_input_names": ["a"],
            "optional_input_names": ["b"],
            "output_names": ["return_value"],
            "category": "ewokscore",
            "description": "Test 2",
        }
    ]
    tasks = task_discovery.discover_tasks_from_modules(
        "ewokscore.tests.discover_module", task_type="ppfmethod"
    )
    assert_tasks(tasks, expected)
    assert len(tasks) == len(expected)


def test_task_discovery():
    expected = [
        {
            "category": "ewokscore",
            "optional_input_names": ["b", "delay"],
            "output_names": ["too_small", "result"],
            "required_input_names": ["a"],
            "task_identifier": "ewokscore.tests.examples.tasks.condsumtask.CondSumTask",
            "task_type": "class",
            "description": "Check whether a value is too small",
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["a", "b", "raise_error"],
            "output_names": ["result"],
            "required_input_names": [],
            "task_identifier": "ewokscore.tests.examples.tasks.errorsumtask.ErrorSumTask",
            "task_type": "class",
            "description": "Add two number with intentional exception",
        },
        {
            "category": "ewokscore",
            "optional_input_names": [],
            "output_names": [],
            "required_input_names": [],
            "task_identifier": "ewokscore.tests.examples.tasks.nooutputtask.NoOutputTask",
            "task_type": "class",
            "description": "A task without outputs",
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["delay"],
            "output_names": ["sum"],
            "required_input_names": ["list"],
            "task_identifier": "ewokscore.tests.examples.tasks.sumlist.SumList",
            "task_type": "class",
            "description": "Add items from a list",
        },
        {
            "category": "ewokscore",
            "optional_input_names": ["b", "delay"],
            "output_names": ["result"],
            "required_input_names": ["a"],
            "task_identifier": "ewokscore.tests.examples.tasks.sumtask.SumTask",
            "task_type": "class",
            "description": "Add two numbers with a delay",
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.addfunc.addfunc",
            "task_type": "method",
            "required_input_names": ["arg"],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Add 1 to the first argument",
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.add",
            "task_type": "method",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Sum objects and add 1",
        },
        {
            "category": "ewokscore",
            "task_identifier": "ewokscore.tests.examples.tasks.simplemethods.append",
            "task_type": "method",
            "required_input_names": [],
            "optional_input_names": [],
            "output_names": ["return_value"],
            "description": "Return positional arguments as a tuple",
        },
    ]

    tasks = task_discovery.discover_all_tasks()
    assert_tasks(tasks, expected)


def assert_tasks(tasks, expected):
    listnames = ["output_names", "required_input_names", "optional_input_names"]
    for task in tasks:
        for listname in listnames:
            task[listname] = set(task[listname])

    for task in expected:
        for listname in listnames:
            task[listname] = set(task[listname])
        assert task in tasks
