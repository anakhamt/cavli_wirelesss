import uuid
from datetime import datetime

from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException
import boto3
from pymongo import MongoClient
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from app.file_schema import files_serializer

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_s3_client():
    s3_client = boto3.client(
        's3',
        aws_access_key_id="AKIAZ67RLARH3UNYUIGB",
        aws_secret_access_key="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",
        region_name='us-east-2')
    return s3_client


def presigned_url(s3_client, filename):
    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': 'cavli',
            'Key': filename
        },
        ExpiresIn=3600,
        HttpMethod='GET'
    )
    return url

# client = MongoClient("mongodb+srv://test_user:wBplqrwY1c8Bmwsq@calve.xtvnerw.mongodb.net/?retryWrites=true&w=majority")
#

@app.get("/")
def hello_world():
    return {"message": "OK"}


@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient("mongodb+srv://root_user:06uDhlAhbxg79DSA@files.qwlyxgn.mongodb.net/?retryWrites=true&w=majority")
    app.database = app.mongodb_client["file_metadata"]
    app.collection = app.database["file"]
    print("Connected to the MongoDB database!")


@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()


@app.get("/files/all")
async def find_all_files():
    print(app.collection.find())
    files = files_serializer(app.collection.find())
    return {"status": "Ok", "data": files}


@app.get("/files/{id}")
async def get_one_file(id: str):
    file = files_serializer(app.collection.find({"_id": ObjectId(id)}))
    return {"status": "Ok", "data": file}


@app.post("/files/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    print(file.filename)
    try:
        contents = file.file.read()
        file.file.seek(0)
        s3_client = get_s3_client()
        # Upload the file to your S3 service
        s3_client.upload_fileobj(file.file, 'cavli', file.filename)
    except Exception as e:
        print(e)
    finally:
        url = presigned_url(s3_client, file.filename)
        meta = {"name": file.filename, "url": url, "date": datetime.now()}
        x = app.collection.insert_one(meta)
        file.file.close()
    print(contents)  # Handle file contents as desired
    return {"Filename": file.filename}


@app.get("/view/{id}")
async def view(id: str):
    try:
        s3_client = get_s3_client()
        result = s3_client.get_object(Bucket="cavli", Key=id)
        text = result["Body"].read().decode()
        print('s3 testing')
        # print(text)
        # return StreamingResponse(content=result["Body"].iter_chunks())
        json_content = json.loads(text)
        return json_content
    except Exception as e:
        if hasattr(e, "message"):
            raise HTTPException(
                status_code=e.message["response"]["Error"]["Code"],
                detail=e.message["response"]["Error"]["Message"],
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))
