def format_file_tree(files):
    """将文件列表格式化为树形结构"""
    tree = {}
    for file in files:
        date = file.uploaded_at.strftime('%Y-%m-%d')
        if date not in tree:
            tree[date] = []
        tree[date].append({
            'id': file.id,
            'name': file.name,
            'type': file.file_type,
            'status': file.status,
            'progress': file.progress,
            'annotation_count': file.annotation_count
        })
    return [{'date': k, 'files': v} for k, v in tree.items()] 