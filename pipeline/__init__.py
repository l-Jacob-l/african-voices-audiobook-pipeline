def run_pipeline(*args, **kwargs):
    from pipeline.pipeline import run_pipeline as _run
    return _run(*args, **kwargs)


def run_history_pipeline(*args, **kwargs):
    from pipeline.pipeline import run_history_pipeline as _run
    return _run(*args, **kwargs)
