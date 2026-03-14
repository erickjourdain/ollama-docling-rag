from fastapi import Request

def get_job_ws_manager(request: Request):
    return request.app.state.ws_manager