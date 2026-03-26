import json

def update_latest_file(host, token, base_path, file_type, filename):
    latest_path = f"{base_path}/{file_type}/latest.json"

    url = f"{host}/api/2.0/fs/files{latest_path}?overwrite=true"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "current_file": filename
    }

    response = requests.put(
        url,
        headers=headers,
        data=json.dumps(payload)
    )

    if not response.ok:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update latest.json: {response.text}"
        )



# Update latest.json
update_latest_file(
    host=host,
    token=token,
    base_path=BASE_PATH,
    file_type=file_type,
    filename=new_filename
    )
