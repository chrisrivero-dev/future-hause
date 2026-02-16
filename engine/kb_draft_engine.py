import uuid
from datetime import datetime

def create_kb_scaffold(project):
    return {
        "id": str(uuid.uuid4()),
        "linked_project_id": project["id"],
        "source_signal_id": project["source_signal_id"],
        "title": project["summary"],
        "sections": [
            "Issue Description",
            "Impact",
            "Root Cause",
            "Resolution / Workaround",
            "Next Steps"
        ],
        "status": "draft_scaffold",
        "created_at": datetime.utcnow().isoformat()
    }
