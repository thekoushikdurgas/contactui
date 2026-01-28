"""JSON Store views."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def list_json_view(request):
    """List all JSON store entries."""
    from apps.documentation.repositories.s3_json_storage import S3JSONStorage
    from django.conf import settings
    
    storage = S3JSONStorage()
    
    try:
        # List JSON files from json_store prefix
        json_prefix = f"{settings.S3_DATA_PREFIX}json_store/"
        files = storage.list_json_files(json_prefix, max_keys=100)
        
        entries = []
        for file_key in files:
            entry_data = storage.read_json(file_key)
            if entry_data:
                entries.append({
                    'key': file_key.split('/')[-1].replace('.json', ''),
                    'data': entry_data,
                    'size': len(str(entry_data))
                })
    except Exception:
        entries = []
    
    context = {
        'entries': entries,
        'total': len(entries)
    }
    return render(request, 'json_store/list.html', context)
