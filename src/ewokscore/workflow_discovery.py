import sys
from fnmatch import fnmatch
from typing import Generator
from typing import List
from typing import Optional

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources


from .entry_points import entry_points


def discover_all_workflows(
    workflow_extension: Optional[str] = None,
    raise_import_failure: bool = True,
) -> List[str]:
    """
    Generates the full python qualifier names of the workflows
    as defined by entry-point group "ewoks.workflows".
    """
    return list(
        _iter_discover_all_workflows(
            workflow_extension=workflow_extension,
            raise_import_failure=raise_import_failure,
        )
    )


def discover_tasks_from_modules(
    *fq_names_or_patterns: str,
    workflow_extension: Optional[str] = None,
    raise_import_failure: bool = True,
) -> List[str]:
    """
    Generates the full python qualifier names of the workflows
    as defined by the module names/patterns.
    """
    if workflow_extension is None:
        workflow_extensions = ("json", "yaml")
    else:
        workflow_extensions = (workflow_extension,)

    result = list()
    for fq_name_or_pattern in fq_names_or_patterns:
        for workflow_extension in workflow_extensions:
            result.extend(
                _iter_fqns_from_pattern(
                    fq_name_or_pattern,
                    file_extension=workflow_extension,
                    raise_import_failure=raise_import_failure,
                )
            )
    return result


def _iter_discover_all_workflows(
    workflow_extension: Optional[str] = None,
    raise_import_failure: bool = True,
) -> Generator[str, None, None]:
    visited = set()
    for entrypoint in entry_points("ewoks.workflows"):
        module_pattern = entrypoint.name
        if module_pattern in visited:
            continue
        visited.add(module_pattern)
        yield from discover_tasks_from_modules(
            module_pattern,
            workflow_extension=workflow_extension,
            raise_import_failure=raise_import_failure,
        )


def _iter_fqns_from_pattern(
    fq_name_or_pattern: str,
    file_extension: str,
    raise_import_failure: bool = True,
) -> Generator[str, None, None]:
    if not fq_name_or_pattern:
        return

    parts = fq_name_or_pattern.split(".")
    first = parts[0]
    rest = parts[1:]

    yield from _iter_module_pattern_parts(
        current_package=first,
        remaining_parts=rest,
        file_extension=file_extension,
        raise_import_failure=raise_import_failure,
    )


def _iter_module_pattern_parts(
    current_package: str,
    remaining_parts: List[str],
    file_extension: str,
    raise_import_failure: bool = True,
) -> Generator[str, None, None]:
    if not remaining_parts:
        return

    part = remaining_parts[0]
    tail = remaining_parts[1:]

    try:
        files = importlib_resources.files(current_package)
    except Exception:
        if raise_import_failure:
            raise
        return

    # Last component: match workflow resource files
    if not tail:
        pattern = f"{part}.{file_extension}"

        for resource in files.iterdir():
            if not resource.is_file():
                continue

            if fnmatch(resource.name, pattern):
                stem = resource.name[: -(len(file_extension) + 1)]
                yield f"{current_package}.{stem}"

        return

    # Intermediate package matching
    for resource in files.iterdir():
        if not resource.is_dir():
            continue

        if not fnmatch(resource.name, part):
            continue

        subpackage = f"{current_package}.{resource.name}"

        # Ensure it is importable as a package
        try:
            importlib_resources.files(subpackage)
        except Exception:
            if raise_import_failure:
                raise
            continue

        yield from _iter_module_pattern_parts(
            current_package=subpackage,
            remaining_parts=tail,
            file_extension=file_extension,
            raise_import_failure=raise_import_failure,
        )
