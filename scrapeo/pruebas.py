def progress_hook(d, progress, task_id):
    if d['status'] == 'downloading':
        progress.update(task_id, advance=d['downloaded_bytes'])
    elif d['status'] == 'finished':
        progress.stop()
