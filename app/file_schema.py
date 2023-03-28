
def file_serializer(file) -> dict:
    return {
        'id': str(file["_id"]),
        'name': file["name"],
        'url': file["url"],
        'date': file["date"]
    }


def files_serializer(files) -> list:
    return [file_serializer(file) for file in files]
